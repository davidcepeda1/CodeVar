def _report(client, api_key, exception_type, file_path, line_number=10):
    client.post(
        "/api/events",
        json={
            "project_api_key": api_key,
            "exception_type": exception_type,
            "file_path": file_path,
            "line_number": line_number,
        },
    )


def test_text_filter_matches_exception_type(client, project):
    _report(client, project["api_key"], "ValueError", "app/foo.py")
    _report(client, project["api_key"], "KeyError", "app/bar.py")

    response = client.get(f"/api/errors?api_key={project['api_key']}&q=Value")
    groups = response.json()

    assert len(groups) == 1
    assert groups[0]["exception_type"] == "ValueError"


def test_text_filter_matches_file_path(client, project):
    _report(client, project["api_key"], "ValueError", "app/payments.py")
    _report(client, project["api_key"], "KeyError", "app/users.py")

    response = client.get(f"/api/errors?api_key={project['api_key']}&q=payments")
    groups = response.json()

    assert len(groups) == 1
    assert groups[0]["file_path"] == "app/payments.py"


def test_status_filter(client, project):
    _report(client, project["api_key"], "ValueError", "app/foo.py")
    group_id = client.get(f"/api/errors?api_key={project['api_key']}").json()[0]["id"]
    client.patch(
        f"/api/errors/{group_id}?api_key={project['api_key']}",
        json={"status": "resolved"},
    )

    unresolved = client.get(f"/api/errors?api_key={project['api_key']}&status=unresolved").json()
    resolved = client.get(f"/api/errors?api_key={project['api_key']}&status=resolved").json()

    assert unresolved == []
    assert len(resolved) == 1


def test_pagination_limits_page_size(client, project):
    for i in range(5):
        _report(client, project["api_key"], f"Error{i}", f"app/mod{i}.py")

    first_page = client.get(
        f"/api/errors?api_key={project['api_key']}&page=1&page_size=2"
    ).json()
    second_page = client.get(
        f"/api/errors?api_key={project['api_key']}&page=2&page_size=2"
    ).json()

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert {g["id"] for g in first_page}.isdisjoint({g["id"] for g in second_page})


def test_dashboard_page_shows_empty_state_for_filter_with_no_matches(client, project):
    _report(client, project["api_key"], "ValueError", "app/foo.py")

    response = client.get(f"/dashboard?api_key={project['api_key']}&q=NoSuchThing")

    assert response.status_code == 200
    assert "No hay errores que coincidan con el filtro." in response.text
