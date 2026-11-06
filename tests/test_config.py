import pytest

from openrouteai.config import Settings


def test_default_settings_use_loopback(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTEAI_LOCAL_BASE_URL", raising=False)
    settings = Settings.from_env()
    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.local_base_url is None
    assert settings.host == "127.0.0.1"


@pytest.mark.parametrize("url", [
    "https://api.example.com/v1", "http://192.168.0.5:1234/v1",
    "http://user:password@127.0.0.1:1234/v1", "http://localhost.evil.test:1234/v1",
    "http://127.0.0.1:1234/v1?token=secret", "http://127.0.0.1:1234/other",
])
def test_rejects_remote_or_ambiguous_provider_url(url):
    with pytest.raises(ValueError):
        Settings(local_base_url=url)


def test_rejects_non_loopback_bind_address():
    with pytest.raises(ValueError):
        Settings(host="0.0.0.0")


def test_accepts_local_compatible_server():
    settings = Settings(local_base_url="http://127.0.0.1:1234/v1")
    assert settings.local_base_url == "http://127.0.0.1:1234/v1"
