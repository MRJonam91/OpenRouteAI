import json

import httpx
import pytest

from openrouteai.app import create_app
from openrouteai.config import Settings


def fake_upstream(request):
    if request.url.port == 11434 and request.url.path == "/api/tags":
        return httpx.Response(200, json={"models": [{"name": "tiny:latest"}, {"name": "huge:cloud"}]})
    if request.url.port == 11434 and request.url.path == "/api/show":
        return httpx.Response(200, json={"capabilities": ["completion"]})
    if request.url.port == 11434 and request.url.path == "/api/chat":
        body = json.loads(request.content)
        assert body["stream"] is False
        return httpx.Response(200, json={"model": body["model"], "message": {"role": "assistant", "content": "Ollama says hi"}, "done": True, "prompt_eval_count": 4, "eval_count": 3})
    if request.url.port == 1234 and request.url.path == "/v1/models":
        return httpx.Response(200, json={"data": [{"id": "small-local"}]})
    if request.url.port == 1234 and request.url.path == "/v1/chat/completions":
        return httpx.Response(200, json={"model": "small-local", "choices": [{"message": {"role": "assistant", "content": "Local says hi"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 2, "completion_tokens": 2}})
    raise AssertionError(f"Unexpected upstream path: {request.url.path}")


async def call(app, method, path, **kwargs):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:4000") as client:
        return await client.request(method, path, **kwargs)


def make_app(handler=fake_upstream):
    return create_app(Settings(local_base_url="http://127.0.0.1:1234/v1"), httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_auto_prefers_ollama_and_returns_openai_shape():
    response = await call(make_app(), "POST", "/v1/chat/completions", json={"model": "auto", "messages": [{"role": "user", "content": "Ciao"}]})
    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "ollama/tiny:latest"
    assert body["choices"][0]["message"] == {"role": "assistant", "content": "Ollama says hi"}
    assert body["usage"] == {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7}


@pytest.mark.asyncio
async def test_explicit_local_model_uses_compatible_server():
    response = await call(make_app(), "POST", "/v1/chat/completions", json={"model": "local/small-local", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 7})
    assert response.status_code == 200
    assert response.json()["model"] == "local/small-local"
    assert response.json()["choices"][0]["message"]["content"] == "Local says hi"


@pytest.mark.asyncio
async def test_auto_fallback_uses_second_local_provider_on_503():
    attempts = []

    def upstream(request):
        if request.url.path == "/api/chat":
            attempts.append("ollama")
            return httpx.Response(503, json={"error": "busy"})
        if request.url.path == "/v1/chat/completions":
            attempts.append("local")
        return fake_upstream(request)

    response = await call(make_app(upstream), "POST", "/v1/chat/completions", json={"model": "auto", "messages": [{"role": "user", "content": "Hi"}]})
    assert response.status_code == 200
    assert response.json()["model"] == "local/small-local"
    assert attempts == ["ollama", "local"]


@pytest.mark.asyncio
async def test_models_exclude_cloud_and_health_is_independent():
    models = await call(make_app(), "GET", "/v1/models")
    health = await call(make_app(), "GET", "/health")
    assert [item["id"] for item in models.json()["data"]] == ["ollama/tiny:latest", "local/small-local"]
    assert health.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_auto_excludes_embedding_only_ollama_model():
    def upstream(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "all-minilm:latest"}, {"name": "tiny:latest"}]})
        if request.url.path == "/api/show":
            model = json.loads(request.content)["model"]
            return httpx.Response(200, json={"capabilities": ["embedding"] if model == "all-minilm:latest" else ["completion"]})
        return fake_upstream(request)

    response = await call(make_app(upstream), "POST", "/v1/chat/completions", json={"model": "auto", "messages": [{"role": "user", "content": "Hi"}]})
    assert response.status_code == 200
    assert response.json()["model"] == "ollama/tiny:latest"


@pytest.mark.asyncio
async def test_unsupported_stream_and_fields_are_openai_errors():
    body = {"model": "auto", "messages": [{"role": "user", "content": "Hi"}]}
    stream = await call(make_app(), "POST", "/v1/chat/completions", json={**body, "stream": True})
    tools = await call(make_app(), "POST", "/v1/chat/completions", json={**body, "tools": []})
    assert stream.status_code == 400
    assert stream.json()["error"]["type"] == "invalid_request_error"
    assert tools.status_code == 400
    assert tools.json()["error"]["code"] == "invalid_request"


@pytest.mark.asyncio
async def test_cloud_or_missing_model_cannot_be_called():
    for model in ["ollama/huge:cloud", "local/missing"]:
        response = await call(make_app(), "POST", "/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": "Hi"}]})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_provider_failure_never_echoes_prompt_or_upstream_details():
    def offline(request):
        raise httpx.ConnectError("private connection detail", request=request)

    app = create_app(Settings(), httpx.MockTransport(offline))
    response = await call(app, "POST", "/v1/chat/completions", json={"model": "auto", "messages": [{"role": "user", "content": "top-secret-prompt"}]})
    assert response.status_code == 503
    assert response.json()["error"]["type"] == "server_error"
    assert "top-secret-prompt" not in response.text
    assert "private connection detail" not in response.text


@pytest.mark.asyncio
async def test_explicit_model_does_not_fallback_after_failure():
    attempted = []

    def upstream(request):
        if request.url.path == "/api/chat":
            attempted.append("ollama")
            return httpx.Response(503)
        if request.url.path == "/v1/chat/completions":
            attempted.append("local")
        return fake_upstream(request)

    response = await call(make_app(upstream), "POST", "/v1/chat/completions", json={"model": "ollama/tiny:latest", "messages": [{"role": "user", "content": "Hi"}]})
    assert response.status_code == 503
    assert attempted == ["ollama"]
