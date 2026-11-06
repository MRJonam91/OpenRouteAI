"""Opt-in integration test requiring an installed Ollama chat model."""

import os

import httpx
import pytest

from openrouteai.app import create_app
from openrouteai.config import Settings


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("OPENROUTEAI_LIVE_MODEL"), reason="Set OPENROUTEAI_LIVE_MODEL for a real Ollama test")
async def test_chat_with_real_local_model():
    model = os.environ["OPENROUTEAI_LIVE_MODEL"]
    app = create_app(Settings(preferred_model=f"ollama/{model}"))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:4000", timeout=120) as client:
        response = await client.post("/v1/chat/completions", json={
            "model": "auto", "messages": [{"role": "user", "content": "Reply with one short greeting."}], "max_tokens": 12,
        })
    assert response.status_code == 200, response.text
    assert response.json()["model"] == f"ollama/{model}"
    assert response.json()["choices"][0]["message"]["content"]
