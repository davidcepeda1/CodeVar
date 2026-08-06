# codevar-server

API de ingesta y dashboard de CodeVAR, un mini error-tracker para aplicaciones Python/FastAPI.

Recibe eventos de error enviados por `codevar-client`, los agrupa por huella (fingerprint) y los expone en un dashboard web.

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Jinja2 (dashboard)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar DATABASE_URL
```

Ver `Planning.md` y `Contexto.md` en la raíz del proyecto para el plan de desarrollo y el contexto completo.
