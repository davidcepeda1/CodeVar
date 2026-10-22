"""CP-05 a CP-08. Entradas inválidas: deben rechazarse con 4xx controlado,
nunca con un error 500 ni almacenarse."""
from .helpers import crear_grupo, crear_proyecto, evento

FUERA_DE_RANGO = 2**63


def test_cp05_identificador_fuera_de_rango_responde_422(client, project):
    clave = project["api_key"]
    client.raise_server_exceptions = False

    respuestas = [
        client.get(f"/api/errors/{FUERA_DE_RANGO}", params={"api_key": clave}),
        client.patch(f"/api/errors/{FUERA_DE_RANGO}", params={"api_key": clave},
                     json={"status": "resolved"}),
        client.get(f"/dashboard/errors/{FUERA_DE_RANGO}", params={"api_key": clave}),
    ]

    assert [r.status_code for r in respuestas] == [422, 422, 422]


def test_cp06_numero_de_linea_invalido_es_rechazado(client, project):
    clave = project["api_key"]

    assert client.post("/api/events", json=evento(clave, line_number="diez")).status_code == 422
    assert client.post("/api/events", json=evento(clave, line_number=-1)).status_code == 422
    assert client.post("/api/events", json=evento(clave, line_number=2**31)).status_code == 422


def test_cp07_campos_sobredimensionados_son_rechazados(client, project):
    clave = project["api_key"]

    traza = client.post("/api/events", json=evento(clave, stack_trace="x" * 70_000))
    tipo = client.post("/api/events", json=evento(clave, exception_type="E" * 201))

    assert traza.status_code == 422
    assert tipo.status_code == 422
    assert client.get("/api/errors", params={"api_key": clave}).json() == []


def test_cp08_estado_no_permitido_es_rechazado(client):
    clave = crear_proyecto(client, "equipo-a")
    grupo = crear_grupo(client, clave)

    api = client.patch(f"/api/errors/{grupo}", params={"api_key": clave},
                       json={"status": "borrado"})
    panel = client.post(f"/dashboard/errors/{grupo}/status", params={"api_key": clave},
                        data={"status": "borrado"}, follow_redirects=False)

    assert api.status_code == 422
    assert panel.status_code == 400


def test_cp05b_paginacion_sin_limites_es_rechazada(client, project):
    clave = project["api_key"]
    client.raise_server_exceptions = False

    enorme = client.get("/api/errors", params={"api_key": clave, "page_size": 10**12})
    negativa = client.get("/api/errors", params={"api_key": clave, "page": 2**63})

    assert [enorme.status_code, negativa.status_code] == [422, 422]
