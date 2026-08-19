from fastapi import FastAPI
from fastapi.testclient import TestClient

from codevar_client.config import CodevarConfig
from codevar_client.middleware import CodevarMiddleware
from codevar_client.reporter import EventReporter


def _build_client():
    app = FastAPI()
    config = CodevarConfig(server_url="http://localhost:8000", api_key="abc123")
    app.add_middleware(CodevarMiddleware, config=config)

    @app.get("/boom")
    def boom():
        raise ValueError("kaboom")

    return TestClient(app, raise_server_exceptions=False)


def test_middleware_captures_user_agent_and_query_params(monkeypatch):
    reported = {}

    def fake_send(self, info, request_path=None, request_method=None, extra_context=None):
        reported["request_path"] = request_path
        reported["request_method"] = request_method
        reported["extra_context"] = extra_context

    monkeypatch.setattr(EventReporter, "send", fake_send)

    client = _build_client()
    client.get("/boom?limit=10", headers={"user-agent": "pytest-agent/1.0"})

    assert reported["request_path"] == "/boom"
    assert reported["request_method"] == "GET"
    assert reported["extra_context"]["user_agent"] == "pytest-agent/1.0"
    assert reported["extra_context"]["query_params"] == {"limit": "10"}


def test_middleware_omits_query_params_when_there_are_none(monkeypatch):
    reported = {}

    def fake_send(self, info, request_path=None, request_method=None, extra_context=None):
        reported["extra_context"] = extra_context

    monkeypatch.setattr(EventReporter, "send", fake_send)

    client = _build_client()
    client.get("/boom")

    assert "query_params" not in reported["extra_context"]
