<p align="center">
  <img src="app/static/CodeVarIco.png" alt="CodeVAR" width="90">
</p>

# codevar-server

API de ingesta y dashboard de **CodeVAR**, un mini error-tracker inspirado en Sentry. Recibe eventos de error enviados por [`codevar-client`](../codevar-client) (Python/FastAPI) o [`codevar-client-node`](../codevar-client-node) (Node/Express), los agrupa por huella (fingerprint) y los expone en un dashboard web con búsqueda/filtros, gráfico de frecuencia, alertas por webhook y stack trace completo.

## Contexto

CodeVAR captura excepciones no manejadas en tiempo de ejecución y las agrupa por `hash(tipo_excepción + archivo + línea)`, en vez de guardar cada ocurrencia como un evento aislado. `codevar-server` es la mitad "backend" del sistema: recibe esos eventos vía HTTP desde cualquier SDK que hable su protocolo de ingesta, decide si pertenecen a un grupo existente o crean uno nuevo, y sirve tanto una API JSON como un dashboard HTML server-rendered (sin frontend framework) para revisarlos.

Es deliberadamente mínimo: sin autenticación de usuarios (cada proyecto se identifica por una `api_key` opaca) y sin agrupación semántica avanzada de errores. Ver [`../Contexto.md`](../Contexto.md) para el detalle completo de las decisiones de alcance originales, y el plan de v0.2.0 para las fases agregadas después del MVP (filtros, tests, alertas, segundo SDK).

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
| `projects` | Un proyecto instrumentado: `name` único + `api_key` opaca (identifica y autentica al proyecto) + `webhook_url` opcional para alertas |
| `error_groups` | Un tipo de error deduplicado por `fingerprint` único por proyecto, con `event_count` y `status` (`unresolved`/`resolved`/`ignored`) |
| `error_events` | Cada ocurrencia individual: stack trace, request path/method, `extra_context` (JSON — headers y query params de la request que originó el error) |

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
| `GET /dashboard?api_key=...` | Lista de errores de un proyecto, con búsqueda/filtro por texto o estado (`q`, `status`), paginación (`page`), panel de conexión (api_key + snippet por lenguaje) y zona de peligro para eliminar el proyecto |
| `GET /dashboard/errors/{id}?api_key=...` | Detalle de un grupo de error: metadata, gráfico de frecuencia por día, controles de estado, eventos individuales con stack trace y `extra_context` expandibles |
| `POST /projects` | Crea un proyecto (form: `name`) |
| `POST /dashboard/projects/rename?api_key=...` | Renombra el proyecto actual (form: `name`) |
| `POST /dashboard/projects/webhook?api_key=...` | Configura o limpia la URL de webhook del proyecto (form: `webhook_url`, vacío para desactivar) |
| `POST /dashboard/projects/delete?api_key=...` | Elimina el proyecto y todos sus grupos/eventos en cascada (form: `confirm_name`, debe coincidir exacto con el nombre) |
| `POST /dashboard/errors/{id}/status?api_key=...` | Marca un error como resuelto/ignorado/reabierto (form: `status`) |

### 3. API (JSON)

| Endpoint | Descripción |
|---|---|
| `POST /api/events` | Ingesta un evento de error. Body: `project_api_key`, `exception_type`, `file_path`, `line_number`, y opcionalmente `stack_trace`, `request_path`, `request_method`, `extra_context`. Devuelve `{"error_group_id": ...}`. Lo usan `codevar-client` y `codevar-client-node`, no se llama a mano normalmente. Sujeto a rate limiting por proyecto (60 eventos/60s) — devuelve `429` con `Retry-After` si se excede |
| `GET /api/errors?api_key=...` | Lista los grupos de error de un proyecto. Acepta `q` (texto libre sobre tipo/archivo), `status`, `page` y `page_size` |
| `GET /api/errors/{id}?api_key=...` | Detalle de un grupo, incluyendo sus eventos |
| `PATCH /api/errors/{id}?api_key=...` | Cambia el estado de un grupo. Body: `{"status": "resolved" \| "ignored" \| "unresolved"}` |

Todos los endpoints (API y dashboard) devuelven `401` si la `api_key` no corresponde a ningún proyecto. Ver `postman/` para una colección lista para importar con casos de prueba (incluyendo agrupación por fingerprint y condiciones de carrera).

### 4. Alertas por webhook

Cada proyecto puede configurar una `webhook_url` (compatible con Discord/Slack) desde el panel del dashboard. Cuando `POST /api/events` crea un **error group nuevo** (no en reocurrencias del mismo error), `codevar-server` dispara un `POST` best-effort a esa URL con un mensaje corto (tipo de excepción, ubicación, link al detalle). Si el webhook falla o está caído, el intento se loguea y se descarta — nunca afecta la ingesta del evento.

Validado contra un webhook de Discord real:

<img src="../docs/img/discordWebhook.png" alt="Alerta de CodeVAR recibida en un canal de Discord" width="360">

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Jinja2 (dashboard, sin frontend framework)
- `requests` (envío de webhooks salientes)

## Pruebas

- `pytest tests/` — suite automatizada: fingerprinting, ingesta/agrupación, rate limiting, filtros/paginación, cambios de estado, webhooks (ver `requirements-dev.txt`)
- `postman/` — colección de Postman para probar la ingesta manualmente
- `e2e/` — prueba end-to-end real contra `backend-canchas` (dispara un bug genuino, no simulado, y verifica que llega al dashboard)

Ver [`../Planning.md`](../Planning.md) para el plan de desarrollo original por fases.
