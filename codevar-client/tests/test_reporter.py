import requests

from codevar_client.config import CodevarConfig
from codevar_client.reporter import EventReporter
from codevar_client.traceback_utils import ExceptionInfo


def _sample_info():
    return ExceptionInfo(
        exception_type="ValueError",
        file_path="app/foo.py",
        line_number=10,
        stack_trace="Traceback ...",
    )


def test_send_posts_the_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        class FakeResponse:
            status_code = 201

        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    config = CodevarConfig(server_url="http://localhost:8000", api_key="abc123")
    reporter = EventReporter(config)
    reporter.send(_sample_info(), request_path="/orders", request_method="POST")

    assert captured["url"] == "http://localhost:8000/api/events"
    assert captured["json"]["project_api_key"] == "abc123"
    assert captured["json"]["exception_type"] == "ValueError"
    assert captured["json"]["request_path"] == "/orders"
    assert captured["json"]["request_method"] == "POST"


def test_send_does_not_raise_when_server_is_unreachable(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)

    config = CodevarConfig(server_url="http://localhost:8000", api_key="abc123")
    reporter = EventReporter(config)

    # No debe lanzar: CodeVAR nunca debe romper la app que instrumenta.
    reporter.send(_sample_info())
