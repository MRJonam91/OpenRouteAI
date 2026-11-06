"""Contract test with the official OpenAI Python client."""

import httpx
import pytest
from openai import AsyncOpenAI

from openrouteai.app import create_app
from openrouteai.config import Settings


@pytest.mark.asyncio
async def test_official_sdk_can_call_gateway():
    def upstream(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "tiny:latest"}]})
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"]})
        if request.url.path == "/api/chat":
            return httpx.Response(200, json={"message": {"role": "assistant", "content": "Ciao"}, "prompt_eval_count": 2, "eval_count": 1})
        raise AssertionError(request.url.path)

    app = create_app(Settings(), httpx.MockTransport(upstream))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:4000") as http_client:
        client = AsyncOpenAI(base_url="http://127.0.0.1:4000/v1", api_key="local", http_client=http_client)
        reply = await client.chat.completions.create(model="auto", messages=[{"role": "user", "content": "Ciao"}])
    assert reply.model == "ollama/tiny:latest"
    assert reply.choices[0].message.content == "Ciao"
    assert reply.usage.total_tokens == 3
