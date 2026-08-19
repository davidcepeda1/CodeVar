def _create_group(client, project):
    client.post(
        "/api/events",
        json={
            "project_api_key": project["api_key"],
            "exception_type": "ValueError",
            "file_path": "app/foo.py",
            "line_number": 10,
        },
    )
    groups = client.get(f"/api/errors?api_key={project['api_key']}").json()
    return groups[0]["id"]


def test_valid_status_update(client, project):
    group_id = _create_group(client, project)

    response = client.patch(
        f"/api/errors/{group_id}?api_key={project['api_key']}",
        json={"status": "resolved"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_invalid_status_value_is_rejected(client, project):
    group_id = _create_group(client, project)

    response = client.patch(
        f"/api/errors/{group_id}?api_key={project['api_key']}",
        json={"status": "not-a-real-status"},
    )

    assert response.status_code == 422


def test_status_update_for_unknown_group_returns_404(client, project):
    response = client.patch(
        f"/api/errors/999999?api_key={project['api_key']}",
        json={"status": "resolved"},
    )

    assert response.status_code == 404
