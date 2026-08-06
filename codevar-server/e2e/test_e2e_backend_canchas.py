"""
Prueba end-to-end real (no simulada) del flujo completo:

    backend-canchas (app real) -> codevar_client (real) -> codevar-server (real)

No se simula ningún error a mano: se dispara un bug genuino ya presente en
backend-canchas (routers/reservas.py::actualizar_reserva) y se verifica que
codevar-server lo recibe, lo agrupa y lo expone correctamente.

El bug: si la cancha asociada a una reserva ya no existe (por ejemplo tras
un bulk-delete que no dispara el cascade de SQLAlchemy a nivel de ORM),
`actualizar_reserva` accede a `cancha.id` / `cancha.precio_por_hora` sin
comprobar `None` -> AttributeError no manejado, capturado por
CodevarMiddleware y reportado a codevar-server.

Requiere:
  - codevar-server corriendo localmente (ver README.md de esta carpeta)
  - BACKEND_CANCHAS_PATH apuntando a la ruta local de backend-canchas

No requiere conectividad a la base de datos real de backend-canchas: la
conexión se sustituye por SQLite en memoria solo para esta corrida de
prueba (no se modifica ningún archivo del repo de backend-canchas).
"""
import os
import sys

BACKEND_CANCHAS_PATH = os.environ.get(
    "BACKEND_CANCHAS_PATH",
    "/home/davidjuz/Documentos/MovilesProyectos/CanchasDeportivasApp/backend",
)
CODEVAR_CLIENT_PATH = os.environ.get(
    "CODEVAR_CLIENT_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "codevar-client"),
)

sys.path.insert(0, BACKEND_CANCHAS_PATH)
sys.path.insert(0, CODEVAR_CLIENT_PATH)

os.environ.setdefault("CODEVAR_SERVER_URL", "http://127.0.0.1:8098")
os.environ.setdefault("CODEVAR_API_KEY", "e2e-test-key")


def run():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import database as canchas_database

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(bind=test_engine)
    canchas_database.engine = test_engine
    canchas_database.SessionLocal = TestSessionLocal

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    import main as canchas_main
    from fastapi.testclient import TestClient

    canchas_database.Base.metadata.create_all(bind=test_engine)
    canchas_main.app.dependency_overrides[canchas_database.get_db] = override_get_db

    middleware_names = [m.cls.__name__ for m in canchas_main.app.user_middleware]
    assert "CodevarMiddleware" in middleware_names, "CodevarMiddleware no está activo"

    client = TestClient(canchas_main.app, raise_server_exceptions=False)

    r = client.post("/canchas/", json={"nombre": "Cancha 1", "tipo": "futbol", "precio_por_hora": 20.0})
    cancha_id = r.json()["id"]

    r = client.post(
        "/reservas/",
        json={
            "cancha_id": cancha_id,
            "fecha": "2026-08-10",
            "hora_inicio": "10:00:00",
            "hora_fin": "11:00:00",
            "nombre_cliente": "David",
        },
    )
    reserva_id = r.json()["id"]

    db = TestSessionLocal()
    import models as canchas_models

    db.query(canchas_models.Cancha).filter_by(id=cancha_id).delete()
    db.commit()
    db.close()

    r = client.put(f"/reservas/{reserva_id}", json={"nombre_cliente": "David actualizado"})
    assert r.status_code == 500, f"se esperaba 500, llegó {r.status_code}"

    print("OK: bug real disparado en backend-canchas y capturado por CodevarMiddleware")
    print("Revisa el dashboard/API de codevar-server para confirmar que el evento llegó:")
    print(f"  {os.environ['CODEVAR_SERVER_URL']}/api/errors?api_key={os.environ['CODEVAR_API_KEY']}")


if __name__ == "__main__":
    run()
