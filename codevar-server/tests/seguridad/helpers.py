def crear_proyecto(client, nombre):
    r = client.post("/projects", data={"name": nombre}, follow_redirects=False)
    return r.headers["location"].split("api_key=")[1].split("&")[0]


def crear_grupo(client, api_key, linea=10):
    client.post("/api/events", json={
        "project_api_key": api_key,
        "exception_type": "ValueError",
        "file_path": "app/servicio.py",
        "line_number": linea,
    })
    return client.get("/api/errors", params={"api_key": api_key}).json()[0]["id"]


def evento(api_key, **cambios):
    datos = {
        "project_api_key": api_key,
        "exception_type": "ValueError",
        "file_path": "app/servicio.py",
        "line_number": 10,
    }
    datos.update(cambios)
    return datos
