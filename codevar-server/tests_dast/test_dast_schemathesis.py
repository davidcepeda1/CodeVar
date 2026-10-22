"""CP-13. Prueba dinámica: Schemathesis genera peticiones a partir del esquema
OpenAPI y comprueba que ninguna produzca un error 500. Se ejecuta dentro del
proceso, contra la aplicación ASGI y una base SQLite temporal."""
import os
import secrets
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/codevar_dast.db")

import schemathesis  # noqa: E402
from hypothesis import settings  # noqa: E402
from schemathesis.checks import not_a_server_error  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Project  # noqa: E402

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
CLAVE = secrets.token_hex(32)
with SessionLocal() as db:
    db.add(Project(name="dast-laboratorio", api_key=CLAVE))
    db.commit()

schema = schemathesis.openapi.from_asgi("/openapi.json", app).exclude(
    path="/dashboard/projects/delete"
)


@schema.parametrize()
@settings(max_examples=int(os.environ.get("DAST_EJEMPLOS", "30")), deadline=None, derandomize=True)
def test_cp13_ninguna_peticion_produce_error_500(case):
    if any(p.name == "api_key" for p in case.operation.query):
        case.query = {**(case.query or {}), "api_key": CLAVE}
    if isinstance(case.body, dict) and "project_api_key" in case.body:
        case.body["project_api_key"] = CLAVE
    case.call_and_validate(checks=[not_a_server_error])
