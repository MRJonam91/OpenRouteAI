import httpx

from openrouteai.cli import main


def test_doctor_reports_local_models_and_support_link(capsys, monkeypatch):
    monkeypatch.delenv("OPENROUTEAI_LOCAL_BASE_URL", raising=False)
    def upstream(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "tiny:latest"}, {"name": "huge:cloud"}]})
        return httpx.Response(200, json={"capabilities": ["completion"]})

    transport = httpx.MockTransport(upstream)
    assert main(["doctor"], transport=transport) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert "ollama/tiny:latest" in lines[0]
    assert "huge:cloud" not in "\n".join(lines)
    assert lines[-1] == "Support: https://ko-fi.com/mrjonam"


def test_doctor_offline_omits_connection_details(capsys, monkeypatch):
    monkeypatch.delenv("OPENROUTEAI_LOCAL_BASE_URL", raising=False)

    def offline(request):
        raise httpx.ConnectError("private provider detail", request=request)

    assert main(["doctor"], transport=httpx.MockTransport(offline)) == 1
    output = capsys.readouterr().out
    assert "No local models" in output
    assert "private provider detail" not in output
    assert output.strip().endswith("https://ko-fi.com/mrjonam")


def test_help_has_support_footer(capsys):
    assert main(["--help"]) == 0
    assert capsys.readouterr().out.strip().endswith("https://ko-fi.com/mrjonam")


def test_serve_binds_only_loopback(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTEAI_LOCAL_BASE_URL", raising=False)
    observed = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: observed.update(kwargs))
    assert main(["serve"]) == 0
    assert observed["host"] == "127.0.0.1"
    assert observed["port"] == 4000
    assert observed["access_log"] is False
    assert capsys.readouterr().out.strip().endswith("https://ko-fi.com/mrjonam")
