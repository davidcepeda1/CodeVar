# CodeVAR — Plan de Desarrollo

> Leer junto a `contexto.md` antes de empezar a escribir código.

## Convención de commits

Se usa **Conventional Commits** en inglés, igual que en otros proyectos de David (consistencia entre repos). Formato:

```
<tipo>(<alcance opcional>): <descripción en presente, minúscula, sin punto final>
```

Tipos usados en este proyecto: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.

---

## Fase 0 — Setup

**Objetivo:** proyecto vacío pero corriendo, con la base de datos creada.

**Tareas:**

- Crear carpetas `codevar-server` y `codevar-client`
- Configurar entorno virtual, dependencias base (FastAPI, SQLAlchemy, psycopg2, uvicorn)
- Definir modelo de datos en PostgreSQL

**Modelo de datos:**

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE error_groups (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    fingerprint VARCHAR(64) NOT NULL,
    exception_type VARCHAR(200),
    file_path VARCHAR(300),
    line_number INTEGER,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    event_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'unresolved',
    UNIQUE(project_id, fingerprint)
);

CREATE TABLE error_events (
    id SERIAL PRIMARY KEY,
    error_group_id INTEGER REFERENCES error_groups(id),
    stack_trace TEXT,
    request_path VARCHAR(300),
    request_method VARCHAR(10),
    occurred_at TIMESTAMP DEFAULT NOW(),
    extra_context JSONB
);
```

**Commits sugeridos:**

```
chore: initialize codevar-server project structure
chore: add base dependencies (fastapi, sqlalchemy, psycopg2, uvicorn)
feat: define database models for projects, error_groups and error_events
chore: configure database connection and environment variables
docs: add initial README with project overview
```

---

## Fase 1 — Servidor de ingesta

**Objetivo:** enviar un evento simulado por Postman y verlo guardado y agrupado correctamente en la base de datos.

**Tareas:**

- Endpoint `POST /api/events`
- Lógica de fingerprint: `hash(exception_type + file_path + line_number)`
- Buscar grupo existente por fingerprint; si no existe, crearlo; si existe, incrementar `event_count` y actualizar `last_seen`
- Guardar el evento individual asociado al grupo

**Commits sugeridos:**

```
feat: implement fingerprint calculation for error grouping
feat: add POST /api/events endpoint for event ingestion
feat: implement error group lookup and creation logic
test: add manual test cases for event ingestion via Postman
fix: handle duplicate fingerprint edge cases
```

---

## Fase 2 — Cliente/SDK

**Objetivo:** un error real, sin simular, viaja desde una app FastAPI de prueba hasta la base de datos de CodeVAR.

**Tareas:**

- Middleware de FastAPI que captura excepciones no manejadas
- Extracción de tipo de excepción, archivo y línea desde el traceback
- Envío del evento al servidor vía HTTP (`reporter.py`)
- Empaquetar como instalable (`setup.py`) para poder hacer `pip install -e .` en otros proyectos

**Commits sugeridos:**

```
chore: initialize codevar-client package structure
feat: implement exception capture middleware for FastAPI
feat: add traceback parsing to extract exception metadata
feat: implement event reporter to send captured errors to server
chore: add setup.py for local pip installation
docs: add usage instructions to client README
```

---

## Fase 3 — API de consulta + Dashboard

**Objetivo:** ver los errores capturados en una interfaz web, no solo en la base de datos.

**Tareas:**

- Endpoint `GET /api/errors` (lista de grupos, ordenados por más reciente)
- Endpoint `GET /api/errors/{id}` (detalle de un grupo + sus eventos)
- Vista Jinja2 con tabla de errores: tipo, ubicación, frecuencia, último visto
- Vista de detalle con stack trace expandible

**Commits sugeridos:**

```
feat: add GET /api/errors endpoint for error group listing
feat: add GET /api/errors/{id} endpoint for error group detail
feat: implement dashboard base template with Jinja2
feat: add error list view to dashboard
feat: add error detail view with expandable stack trace
style: improve dashboard layout and readability
```

---

## Fase 4 — Integración real + pulido

**Objetivo:** demo convincente — un error real ocurre en `backend-canchas` y aparece en CodeVAR.

**Tareas:**

- Instalar `codevar-client` en `backend-canchas`
- Provocar errores de prueba reales y verificar el flujo completo end-to-end
- Endpoint `PATCH /api/errors/{id}` para marcar como resuelto/ignorado
- Manejo de errores propios de CodeVAR (que el propio tracker no se caiga si falla el envío del evento)

**Commits sugeridos:**

```
feat: integrate codevar-client into backend-canchas
feat: add PATCH /api/errors/{id} endpoint to update error status
feat: add resolved/ignored status controls to dashboard
fix: ensure reporter fails silently if server is unreachable
test: validate end-to-end flow with real errors from backend-canchas
```

---

## Fase 5 — Documentación + despliegue

**Objetivo:** proyecto listo para portafolio, con demo visual.

**Tareas:**

- README completo de ambos repositorios (contexto, arquitectura, instalación, uso)
- Desplegar `codevar-server` en Render
- Grabar GIF corto del flujo completo (error ocurre → aparece en dashboard)

**Commits sugeridos:**

```
docs: write full README for codevar-server
docs: write full README for codevar-client
chore: configure production environment variables for Render
chore: deploy codevar-server to Render
docs: add demo gif and usage example to README
```

---

## Notas para Claude Code

- Respetar el alcance definido en `contexto.md`: un solo lenguaje (Python/FastAPI), fingerprinting simple, dashboard server-rendered sin frontend framework.
- No agregar autenticación de usuarios, alertas por email/Slack, ni soporte multi-lenguaje salvo que se solicite explícitamente — no forma parte del MVP.
- Cada fase debe dejar el proyecto en un estado funcional y demostrable, incluso si el tiempo se acorta y no se llega a fases posteriores.
- Mantener los commits en inglés, formato Conventional Commits, uno por unidad de trabajo lógica (no combinar features distintas en un mismo commit).
