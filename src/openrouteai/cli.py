"""Human-facing commands; no request content is printed."""

import argparse
import asyncio

import httpx
import uvicorn

from .app import create_app
from .config import Settings
from .providers import LocalOpenAIProvider, OllamaProvider


SUPPORT_URL = "https://ko-fi.com/mrjonam"


async def _doctor(settings: Settings, transport: httpx.AsyncBaseTransport | None) -> int:
    async with httpx.AsyncClient(timeout=httpx.Timeout(5, connect=2), trust_env=False, transport=transport) as client:
        providers = [OllamaProvider(client, settings.ollama_base_url)]
        if settings.local_base_url:
            providers.append(LocalOpenAIProvider(client, settings.local_base_url))
        discovered = await asyncio.gather(*(provider.models() for provider in providers), return_exceptions=True)
    routes = [route.id for result in discovered if isinstance(result, list) for route in result]
    if not routes:
        print("No local models are available.")
        return 1
    print("Local models: " + ", ".join(routes))
    return 0


def main(argv: list[str] | None = None, transport: httpx.AsyncBaseTransport | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openrouteai", description="Local AI gateway")
    parser.add_argument("--version", action="version", version="OpenRouteAI 0.1.0a1")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Run the loopback API server")
    commands.add_parser("doctor", help="List available local models")
    try:
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:
            return int(exc.code)
        try:
            settings = Settings.from_env()
        except ValueError:
            print("Invalid local gateway configuration.")
            return 2
        if args.command == "doctor":
            return asyncio.run(_doctor(settings, transport))
        print(f"OpenRouteAI listening on http://{settings.host}:{settings.port}/v1")
        try:
            uvicorn.run(create_app(settings), host=settings.host, port=settings.port, access_log=False)
        except KeyboardInterrupt:
            pass
        return 0
    finally:
        print(f"Support: {SUPPORT_URL}")
