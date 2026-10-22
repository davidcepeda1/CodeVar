"""CP-09. El webhook solo puede apuntar a destinos HTTPS públicos."""
import pytest


def _configurar(client, clave, url):
    return client.post("/dashboard/projects/webhook", params={"api_key": clave},
                       data={"webhook_url": url}, follow_redirects=False)


@pytest.mark.parametrize("url", [
    "https://127.0.0.1/alerta",
    "https://localhost/alerta",
    "https://10.0.0.5/alerta",
    "https://192.168.1.10/alerta",
    "https://interno.lab/alerta",
    "http://hooks.ejemplo-publico.com/alerta",
    "https://host-inexistente.lab/alerta",
])
def test_cp09_destinos_no_permitidos_son_rechazados(client, project, url):
    r = _configurar(client, project["api_key"], url)
    assert "error=invalid_webhook_url" in r.headers["location"]


def test_cp09_destino_publico_https_es_aceptado(client, project):
    r = _configurar(client, project["api_key"], "https://hooks.ejemplo-publico.com/alerta")
    assert "error=" not in r.headers["location"]
