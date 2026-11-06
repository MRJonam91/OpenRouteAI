"""Minimal adapters for two loopback model server protocols."""

import asyncio
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class Route:
    provider: str
    model: str

    @property
    def id(self) -> str:
        return f"{self.provider}/{self.model}"


@dataclass(frozen=True)
class Completion:
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int


class OllamaProvider:
    def __init__(self, client: httpx.AsyncClient, origin: str) -> None:
        self.client = client
        self.origin = origin.rstrip("/")

    async def models(self) -> list[Route]:
        response = await self.client.get(f"{self.origin}/api/tags")
        response.raise_for_status()
        models = response.json().get("models")
        if not isinstance(models, list):
            raise ValueError("Invalid Ollama model list")
        names = {item.get("name") for item in models if isinstance(item, dict) and isinstance(item.get("name"), str)}
        candidates = [name for name in sorted(names) if name and not name.lower().endswith(":cloud")]
        limit = asyncio.Semaphore(8)

        async def supports_chat(name: str) -> bool:
            try:
                async with limit:
                    details = await self.client.post(f"{self.origin}/api/show", json={"model": name})
                details.raise_for_status()
                capabilities = details.json().get("capabilities")
                return isinstance(capabilities, list) and "completion" in capabilities
            except (httpx.HTTPError, ValueError):
                return False

        supported = await asyncio.gather(*(supports_chat(name) for name in candidates))
        return [Route("ollama", name) for name, ok in zip(candidates, supported) if ok]

    async def chat(self, model: str, messages: list[dict], options: dict) -> Completion:
        body: dict = {"model": model, "messages": messages, "stream": False}
        if options:
            body["options"] = options
        response = await self.client.post(f"{self.origin}/api/chat", json=body)
        response.raise_for_status()
        data = response.json()
        message = data.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("Invalid Ollama chat response")
        return Completion(
            content=message["content"],
            finish_reason=data.get("done_reason") or "stop",
            prompt_tokens=data.get("prompt_eval_count") or 0,
            completion_tokens=data.get("eval_count") or 0,
        )


class LocalOpenAIProvider:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def models(self) -> list[Route]:
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        models = response.json().get("data")
        if not isinstance(models, list):
            raise ValueError("Invalid OpenAI-compatible model list")
        names = {item.get("id") for item in models if isinstance(item, dict) and isinstance(item.get("id"), str)}
        return [Route("local", name) for name in sorted(names) if name and not name.lower().endswith(":cloud")]

    async def chat(self, model: str, messages: list[dict], options: dict) -> Completion:
        body = {"model": model, "messages": messages, "stream": False, **options}
        response = await self.client.post(f"{self.base_url}/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Invalid OpenAI-compatible chat response")
        choice = choices[0]
        message = choice.get("message") if isinstance(choice, dict) else None
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("Invalid OpenAI-compatible chat response")
        usage = data.get("usage") or {}
        return Completion(
            content=message["content"],
            finish_reason=choice.get("finish_reason") or "stop",
            prompt_tokens=usage.get("prompt_tokens") or 0,
            completion_tokens=usage.get("completion_tokens") or 0,
        )
