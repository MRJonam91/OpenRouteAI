"""OpenAI-compatible HTTP surface for local text chat."""

import asyncio
from time import time
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .config import Settings
from .providers import LocalOpenAIProvider, OllamaProvider, Route


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(min_length=1)
    messages: list[Message] = Field(min_length=1)
    stream: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=1)


def error(status: int, code: str, message: str, kind: str = "server_error") -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {
        "message": message, "type": kind, "code": code, "param": None,
    }})


async def _discover(providers: dict) -> list[Route]:
    results = await asyncio.gather(*(provider.models() for provider in providers.values()), return_exceptions=True)
    routes = []
    for result in results:
        if isinstance(result, list):
            routes.extend(result)
    return routes


def create_app(settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="OpenRouteAI", version="0.1.0a1", docs_url=None, redoc_url=None)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return error(400, "invalid_request", "Invalid or unsupported request field", "invalid_request_error")

    def providers(client: httpx.AsyncClient) -> dict:
        found = {"ollama": OllamaProvider(client, settings.ollama_base_url)}
        if settings.local_base_url:
            found["local"] = LocalOpenAIProvider(client, settings.local_base_url)
        return found

    def client() -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=httpx.Timeout(60, connect=2), trust_env=False, transport=transport)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/models")
    async def models():
        async with client() as session:
            routes = await _discover(providers(session))
        if not routes:
            return error(503, "no_local_models", "No local models are available")
        return {"object": "list", "data": [{"id": route.id, "object": "model", "owned_by": route.provider} for route in routes]}

    @app.post("/v1/chat/completions")
    async def chat(request: ChatRequest):
        if request.stream:
            return error(400, "unsupported_parameter", "Streaming is not supported in this alpha", "invalid_request_error")
        async with client() as session:
            active = providers(session)
            routes = await _discover(active)
            if request.model == "auto":
                if settings.preferred_model:
                    preferred = next((route for route in routes if route.id == settings.preferred_model), None)
                    if preferred is None:
                        return error(404, "model_not_found", "Configured local model is unavailable", "invalid_request_error")
                    routes.remove(preferred)
                    routes.insert(0, preferred)
                attempts = routes[:2]
            else:
                chosen = next((route for route in routes if route.id == request.model), None)
                if chosen is None:
                    return error(404, "model_not_found", "Requested local model is unavailable", "invalid_request_error")
                attempts = [chosen]
            if not attempts:
                return error(503, "no_local_models", "No local models are available")

            common = {key: value for key, value in (
                ("temperature", request.temperature), ("top_p", request.top_p),
                ("max_tokens", request.max_tokens),
            ) if value is not None}
            messages = [item.model_dump() for item in request.messages]
            for route in attempts:
                options = dict(common)
                if route.provider == "ollama" and "max_tokens" in options:
                    options["num_predict"] = options.pop("max_tokens")
                try:
                    completion = await active[route.provider].chat(route.model, messages, options)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code < 500:
                        return error(502, "provider_rejected", "Local model rejected the request")
                    continue
                except (httpx.RequestError, ValueError, TypeError, KeyError):
                    continue
                return {
                    "id": f"chatcmpl-{uuid4().hex}", "object": "chat.completion",
                    "created": int(time()), "model": route.id,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": completion.content}, "finish_reason": completion.finish_reason}],
                    "usage": {"prompt_tokens": completion.prompt_tokens, "completion_tokens": completion.completion_tokens,
                              "total_tokens": completion.prompt_tokens + completion.completion_tokens},
                }
            return error(503, "provider_unavailable", "Local model is unavailable")

    return app
