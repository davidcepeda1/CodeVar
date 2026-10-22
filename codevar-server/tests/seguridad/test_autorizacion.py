"""CP-01 a CP-04. Acceso entre proyectos: la clave de un proyecto nunca debe
permitir leer ni modificar datos de otro."""
from .helpers import crear_grupo, crear_proyecto


def test_cp01_api_no_entrega_grupo_de_otro_proyecto(client):
    clave_a = crear_proyecto(client, "equipo-a")
    clave_b = crear_proyecto(client, "equipo-b")
    grupo_a = crear_grupo(client, clave_a)

    r = client.get(f"/api/errors/{grupo_a}", params={"api_key": clave_b})

    assert r.status_code == 404


def test_cp02_api_no_modifica_estado_de_otro_proyecto(client):
    clave_a = crear_proyecto(client, "equipo-a")
    clave_b = crear_proyecto(client, "equipo-b")
    grupo_a = crear_grupo(client, clave_a)

    r = client.patch(f"/api/errors/{grupo_a}", params={"api_key": clave_b},
                     json={"status": "resolved"})

    assert r.status_code == 404
    detalle = client.get(f"/api/errors/{grupo_a}", params={"api_key": clave_a}).json()
    assert detalle["status"] == "unresolved"


def test_cp03_panel_no_muestra_detalle_de_otro_proyecto(client):
    clave_a = crear_proyecto(client, "equipo-a")
    clave_b = crear_proyecto(client, "equipo-b")
    grupo_a = crear_grupo(client, clave_a)

    r = client.get(f"/dashboard/errors/{grupo_a}", params={"api_key": clave_b})

    assert r.status_code == 404


def test_cp04_clave_ausente_o_invalida_es_rechazada(client):
    assert client.get("/api/errors").status_code == 422
    assert client.get("/api/errors", params={"api_key": "0" * 64}).status_code == 401
