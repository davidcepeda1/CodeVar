"""CP-11 y CP-12. Riesgos conocidos con excepción aprobada en
security/excepciones.md. strict=True hace fallar el pipeline cuando la prueba
empieza a pasar, obligando a cerrar la excepción."""
import pytest


@pytest.mark.xfail(strict=True, reason="EXC-01: R1 se corrige con autenticación en el Parcial 2")
def test_cp11_inicio_no_expone_api_keys(client, project):
    assert project["api_key"] not in client.get("/").text


@pytest.mark.xfail(strict=True, reason="EXC-02: R3 depende de sesiones; se corrige en el Parcial 2")
def test_cp12_borrado_exige_token_csrf(client, project):
    r = client.post("/dashboard/projects/delete", params={"api_key": project["api_key"]},
                    data={"confirm_name": project["name"]}, follow_redirects=False)
    assert r.status_code == 403
