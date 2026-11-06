"""Validate the only network locations the alpha can use."""

from dataclasses import dataclass
import os
from urllib.parse import urlsplit


LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _loopback_url(value: str, allowed_paths: set[str]) -> None:
    url = urlsplit(value)
    if (
        url.scheme != "http"
        or url.hostname not in LOOPBACK
        or url.username is not None
        or url.password is not None
        or url.path not in allowed_paths
        or url.query
        or url.fragment
    ):
        raise ValueError("Provider URL must be a plain HTTP loopback URL")
    try:
        if url.port is None:
            raise ValueError("Port required")
    except ValueError as exc:
        raise ValueError("Provider URL must include a valid port") from exc


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = "http://127.0.0.1:11434"
    local_base_url: str | None = None
    host: str = "127.0.0.1"
    port: int = 4000
    preferred_model: str | None = None

    def __post_init__(self) -> None:
        _loopback_url(self.ollama_base_url, {"", "/"})
        if self.local_base_url is not None:
            _loopback_url(self.local_base_url, {"/v1", "/v1/"})
        if self.host not in LOOPBACK:
            raise ValueError("Gateway host must be loopback")
        if not 1 <= self.port <= 65535:
            raise ValueError("Gateway port is invalid")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            local_base_url=os.getenv("OPENROUTEAI_LOCAL_BASE_URL") or None,
            host=os.getenv("OPENROUTEAI_HOST", "127.0.0.1"),
            port=int(os.getenv("OPENROUTEAI_PORT", "4000")),
            preferred_model=os.getenv("OPENROUTEAI_MODEL") or None,
        )
