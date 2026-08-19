def _event_payload(api_key, exception_type="ValueError", file_path="app/foo.py", line_number=10):
    return {
        "project_api_key": api_key,
        "exception_type": exception_type,
        "file_path": file_path,
        "line_number": line_number,
        "stack_trace": "Traceback ...",
    }


def test_invalid_api_key_returns_401(client):
    response = client.post("/api/events", json=_event_payload("does-not-exist"))
    assert response.status_code == 401


def test_first_event_creates_a_new_error_group(client, project):
    response = client.post("/api/events", json=_event_payload(project["api_key"]))
    assert response.status_code == 201

    groups = client.get(f"/api/errors?api_key={project['api_key']}").json()
    assert len(groups) == 1
    assert groups[0]["exception_type"] == "ValueError"
    assert groups[0]["event_count"] == 1


def test_repeated_event_regroups_instead_of_duplicating(client, project):
    for _ in range(3):
        client.post("/api/events", json=_event_payload(project["api_key"]))

    groups = client.get(f"/api/errors?api_key={project['api_key']}").json()
    assert len(groups) == 1
    assert groups[0]["event_count"] == 3


def test_different_fingerprint_creates_a_separate_group(client, project):
    client.post("/api/events", json=_event_payload(project["api_key"], exception_type="ValueError"))
    client.post("/api/events", json=_event_payload(project["api_key"], exception_type="KeyError"))

    groups = client.get(f"/api/errors?api_key={project['api_key']}").json()
    assert len(groups) == 2


def test_events_are_scoped_to_their_project(client, project):
    other = client.post("/projects", data={"name": "other-project"}, follow_redirects=False)
    other_api_key = other.headers["location"].split("api_key=")[1].split("&")[0]

    client.post("/api/events", json=_event_payload(project["api_key"]))

    groups = client.get(f"/api/errors?api_key={other_api_key}").json()
    assert groups == []
