import app.main as main_module


def _set_webhook(client, api_key, url):
    return client.post(
        "/dashboard/projects/webhook",
        params={"api_key": api_key},
        data={"webhook_url": url},
        follow_redirects=False,
    )


def _report_event(client, api_key, exception_type="ValueError", file_path="app/foo.py"):
    return client.post(
        "/api/events",
        json={
            "project_api_key": api_key,
            "exception_type": exception_type,
            "file_path": file_path,
            "line_number": 10,
        },
    )


def test_setting_a_valid_webhook_url_redirects_without_error(client, project):
    response = _set_webhook(client, project["api_key"], "https://discord.com/api/webhooks/abc")
    assert response.status_code == 303
    assert "error=" not in response.headers["location"]


def test_setting_an_invalid_webhook_url_is_rejected(client, project):
    response = _set_webhook(client, project["api_key"], "not-a-url")
    assert response.status_code == 303
    assert "error=invalid_webhook_url" in response.headers["location"]


def test_empty_webhook_url_clears_it(client, project):
    _set_webhook(client, project["api_key"], "https://discord.com/api/webhooks/abc")
    _set_webhook(client, project["api_key"], "")

    dashboard = client.get(f"/dashboard?api_key={project['api_key']}")
    assert "sin configurar" in dashboard.text


def test_new_error_group_triggers_a_webhook_call(client, project, monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json))

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr(main_module.requests, "post", fake_post)
    _set_webhook(client, project["api_key"], "https://discord.com/api/webhooks/abc")

    _report_event(client, project["api_key"])

    assert len(calls) == 1
    url, payload = calls[0]
    assert url == "https://discord.com/api/webhooks/abc"
    assert "ValueError" in payload["content"]


def test_repeated_events_do_not_retrigger_the_webhook(client, project, monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json))

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr(main_module.requests, "post", fake_post)
    _set_webhook(client, project["api_key"], "https://discord.com/api/webhooks/abc")

    _report_event(client, project["api_key"])
    _report_event(client, project["api_key"])
    _report_event(client, project["api_key"])

    assert len(calls) == 1


def test_no_webhook_call_when_none_configured(client, project, monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json))

        class FakeResponse:
            status_code = 200

        return FakeResponse()

    monkeypatch.setattr(main_module.requests, "post", fake_post)

    _report_event(client, project["api_key"])

    assert calls == []


def test_event_ingestion_survives_a_broken_webhook(client, project, monkeypatch):
    def fake_post(url, json, timeout):
        raise main_module.requests.ConnectionError("refused")

    monkeypatch.setattr(main_module.requests, "post", fake_post)
    _set_webhook(client, project["api_key"], "https://discord.com/api/webhooks/abc")

    response = _report_event(client, project["api_key"])
    assert response.status_code == 201
