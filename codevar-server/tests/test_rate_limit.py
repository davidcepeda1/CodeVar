from app.rate_limit import RateLimiter, events_rate_limiter


def test_rate_limiter_allows_up_to_the_limit():
    limiter = RateLimiter(max_events=3, window_seconds=60)
    assert limiter.check("key") == 0.0
    assert limiter.check("key") == 0.0
    assert limiter.check("key") == 0.0


def test_rate_limiter_blocks_beyond_the_limit():
    limiter = RateLimiter(max_events=2, window_seconds=60)
    limiter.check("key")
    limiter.check("key")
    retry_after = limiter.check("key")
    assert retry_after > 0


def test_rate_limiter_keys_are_independent():
    limiter = RateLimiter(max_events=1, window_seconds=60)
    limiter.check("a")
    assert limiter.check("b") == 0.0


def test_events_endpoint_returns_429_once_project_hits_the_limit(client, project, monkeypatch):
    monkeypatch.setattr(events_rate_limiter, "max_events", 1)

    payload = {
        "project_api_key": project["api_key"],
        "exception_type": "ValueError",
        "file_path": "app/foo.py",
        "line_number": 10,
    }
    first = client.post("/api/events", json=payload)
    second = client.post("/api/events", json=payload)

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Retry-After" in second.headers
