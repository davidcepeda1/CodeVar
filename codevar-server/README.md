<p align="center">
  <img src="app/static/CodeVarIco.png" alt="CodeVAR" width="90">
</p>

# codevar-server

API de ingesta y dashboard de **CodeVAR**, un mini error-tracker para aplicaciones Python/FastAPI inspirado en Sentry. Recibe eventos de error enviados por [`codevar-client`](../codevar-client), los agrupa por huella (fingerprint) y los expone en un dashboard web con frecuencia, último visto y stack trace completo.

## Contexto

CodeVAR captura excepciones no manejadas en tiempo de ejecución y las agrupa por `hash(tipo_excepción + archivo + línea)`, en vez de guardar cada ocurrencia como un evento aislado. `codevar-server` es la mitad "backend" del sistema: recibe esos eventos vía HTTP, decide si pertenecen a un grupo existente o crean uno nuevo, y sirve tanto una API JSON como un dashboard HTML server-rendered (sin frontend framework) para revisarlos.

Es deliberadamente mínimo: un solo lenguaje soportado (los eventos vienen de `codevar-client`, que solo existe para FastAPI), sin autenticación de usuarios (cada proyecto se identifica por una `api_key` opaca) y sin alertas externas. Ver [`../Contexto.md`](../Contexto.md) para el detalle completo de estas decisiones de alcance.

## Arquitectura

```
codevar-client (en tu app)
      │  POST /api/events
      ▼
┌─────────────────────────────────────────────┐
│ codevar-server                                │
│                                                │
│  fingerprint.py   → hash(tipo+archivo+línea)  │
│  main.py          → rutas API + dashboard     │
│  models.py        → Project / ErrorGroup /    │
│                      ErrorEvent (SQLAlchemy)  │
│  schemas.py        → validación Pydantic      │
│  templates/         → dashboard Jinja2         │
└─────────────────────────────────────────────┘
      │
      ▼
  PostgreSQL
```

**Modelo de datos** (ver `app/models.py`):

| Tabla | Qué guarda |
|---|---|
| `projects` | Un proyecto instrumentado: `name` único + `api_key` opaca (identifica y autentica al proyecto) |
| `error_groups` | Un tipo de error deduplicado por `fingerprint` único por proyecto, con `event_count` y `status` (`unresolved`/`resolved`/`ignored`) |
| `error_events` | Cada ocurrencia individual: stack trace, request path/method, contexto extra (JSON) |

Las tablas se crean automáticamente al arrancar el servidor (`Base.metadata.create_all` en un evento de `startup`) — no hace falta correr migraciones a mano.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate        # source .venv/bin/activate.fish en fish
pip install -r requirements.txt
cp .env.example .env             # completar DATABASE_URL con tu Postgres
```

```bash
DATABASE_URL="postgresql://user:password@localhost:5432/codevar" uvicorn app.main:app --reload
```

Para probar rápido sin levantar Postgres, `DATABASE_URL` acepta SQLite (usado en desarrollo/pruebas a lo largo de este proyecto):

```bash
DATABASE_URL="sqlite:///./codevar.db" uvicorn app.main:app --reload
```

## Uso

### 1. Crear un proyecto

Entra a `http://localhost:8000/` (el overview) y usa **"+ Nuevo proyecto"**. Al crearlo, el dashboard te muestra la `api_key` generada y un snippet listo para copiar en la app que quieras instrumentar (ver [`codevar-client`](../codevar-client)).

### 2. Dashboard (HTML)

| Página | Qué hace |
|---|---|
| `GET /` | Overview: lista de proyectos con contador de errores y última actividad |
| `GET /dashboard?api_key=...` | Lista de errores de un proyecto, con panel de conexión (api_key + snippet) y zona de peligro para eliminar el proyecto |
| `GET /dashboard/errors/{id}?api_key=...` | Detalle de un grupo de error: metadata, controles de estado, eventos individuales con stack trace expandible |
| `POST /projects` | Crea un proyecto (form: `name`) |
| `POST /dashboard/projects/rename?api_key=...` | Renombra el proyecto actual (form: `name`) |
| `POST /dashboard/projects/delete?api_key=...` | Elimina el proyecto y todos sus grupos/eventos en cascada (form: `confirm_name`, debe coincidir exacto con el nombre) |
| `POST /dashboard/errors/{id}/status?api_key=...` | Marca un error como resuelto/ignorado/reabierto (form: `status`) |

### 3. API (JSON)

| Endpoint | Descripción |
|---|---|
| `POST /api/events` | Ingesta un evento de error. Body: `project_api_key`, `exception_type`, `file_path`, `line_number`, y opcionalmente `stack_trace`, `request_path`, `request_method`, `extra_context`. Devuelve `{"error_group_id": ...}`. Lo usa `codevar-client`, no se llama a mano normalmente |
| `GET /api/errors?api_key=...` | Lista los grupos de error de un proyecto, ordenados por `last_seen` descendente |
| `GET /api/errors/{id}?api_key=...` | Detalle de un grupo, incluyendo sus eventos |
| `PATCH /api/errors/{id}?api_key=...` | Cambia el estado de un grupo. Body: `{"status": "resolved" \| "ignored" \| "unresolved"}` |

Todos los endpoints (API y dashboard) devuelven `401` si la `api_key` no corresponde a ningún proyecto. Ver `postman/` para una colección lista para importar con casos de prueba (incluyendo agrupación por fingerprint y condiciones de carrera).

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Jinja2 (dashboard, sin frontend framework)

## Pruebas

- `postman/` — colección de Postman para probar la ingesta manualmente
- `e2e/` — prueba end-to-end real contra `backend-canchas` (dispara un bug genuino, no simulado, y verifica que llega al dashboard)

Ver [`../Planning.md`](../Planning.md) para el plan de desarrollo completo por fases.
