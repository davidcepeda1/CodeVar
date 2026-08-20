<p align="center">
  <img src="codevar-server/app/static/CodeVar.png" alt="CodeVAR" width="220">
</p>

<h1 align="center">CodeVAR</h1>

<p align="center">
  Mini error-tracker inspirado en Sentry, con SDKs para Python/FastAPI y Node/Express.
</p>

<p align="center">
  <strong><a href="https://codevar.onrender.com">codevar.onrender.com</a></strong> — demo en vivo
</p>

---

## Qué es

CodeVAR captura excepciones no manejadas en tu app (FastAPI o Express), las agrupa por huella (mismo tipo de excepción + mismo archivo + misma línea) y las expone en un dashboard web con búsqueda/filtros, gráfico de frecuencia, stack trace completo y alertas por webhook cuando aparece un error nuevo — todo sin depender de una herramienta cerrada como Sentry.

El nombre hace referencia al VAR (Video Assistant Referee) del fútbol: así como el VAR revisa jugadas en busca de faltas, CodeVAR revisa el código en producción en busca de errores.

Es un proyecto personal de **David Cepeda**, estudiante de Ingeniería de Software (Universidad de las Fuerzas Armadas ESPE), construido para entender de primera mano cómo funciona la observabilidad en producción — captura de excepciones, deduplicación de eventos, diseño de una API de ingesta, alertas — y como pieza de portafolio. No busca competir con Sentry: es deliberadamente mínimo, sin autenticación de usuarios ni agrupación semántica avanzada de errores.

## Cómo funciona

```
Tu app (FastAPI o Express)
      │  excepción no manejada
      ▼
codevar-client / codevar-client-node
                 →  middleware que captura la excepción, extrae
                     tipo/archivo/línea y contexto de la request
      │  POST /api/events  (mismo protocolo, agnóstico de lenguaje)
      ▼
codevar-server   →  API de ingesta + agrupación por fingerprint
      │                + alerta por webhook si el grupo es nuevo
      ▼
  PostgreSQL      →  proyectos, grupos de error, eventos individuales
      │
      ▼
  Dashboard web    →  overview de proyectos, lista de errores con
                       filtros, detalle con gráfico y stack trace,
                       marcar resuelto/ignorado
```

## Demo

Recorrido por el dashboard: overview de proyectos, panel de conexión con pestañas por lenguaje (Python/Node), alertas por webhook, búsqueda/filtro de errores, y el detalle de un error con su gráfico de frecuencia y `extra_context`.

![Demo de CodeVAR: overview de proyectos, conexión multi-lenguaje, filtros, alertas por webhook y detalle de error con gráfico de frecuencia](demo.gif)

## Prueba tu propia app

1. Entra a [codevar.onrender.com](https://codevar.onrender.com) y crea un proyecto (**+ Nuevo proyecto**) — te muestra la `api_key` generada. El panel "Cómo conectar este proyecto" tiene una pestaña por lenguaje con el snippet ya completado.

**Python / FastAPI:**
```bash
pip install -e /ruta/a/codevar-client
```
```python
from fastapi import FastAPI
from codevar_client.middleware import CodevarMiddleware
from codevar_client.config import CodevarConfig

app = FastAPI()

app.add_middleware(
    CodevarMiddleware,
    config=CodevarConfig(
        server_url="https://codevar.onrender.com",
        api_key="la-api-key-de-tu-proyecto",
    ),
)
```

**Node / Express:**
```bash
npm install /ruta/a/codevar-client-node
```
```js
const { createConfig, codevarErrorHandler } = require("codevar-client");

app.use(codevarErrorHandler(createConfig({
    serverUrl: "https://codevar.onrender.com",
    apiKey: "la-api-key-de-tu-proyecto",
})));
```

Cualquier excepción no manejada en un endpoint aparece sola en tu dashboard, agrupada por tipo/archivo/línea — y si configuraste un webhook para el proyecto, te llega un aviso apenas ocurre por primera vez.

## Repositorios de este monorepo

| Carpeta | Qué es |
|---|---|
| [`codevar-server`](codevar-server/) | API de ingesta + dashboard (FastAPI + PostgreSQL + Jinja2) |
| [`codevar-client`](codevar-client/) | Middleware/SDK instalable vía pip para apps FastAPI |
| [`codevar-client-node`](codevar-client-node/) | Middleware/SDK instalable vía npm para apps Express |

## Documentación

- [`Contexto.md`](Contexto.md) — contexto completo del proyecto, decisiones de alcance ya tomadas
- [`Planning.md`](Planning.md) — plan de desarrollo original por fases y convención de commits
- [`codevar-server/README.md`](codevar-server/README.md) — setup, endpoints y stack del servidor
- [`codevar-client/README.md`](codevar-client/README.md) — instalación y uso del SDK de Python
- [`codevar-client-node/README.md`](codevar-client-node/README.md) — instalación y uso del SDK de Node

## Stack técnico

| Capa | Tecnología |
|---|---|
| Backend / API | FastAPI |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy |
| Dashboard | Jinja2 (server-rendered, sin frontend framework) |
| SDK Python | Paquete instalable vía pip (`pip install -e`) |
| SDK Node | Paquete instalable vía npm, sin dependencias de runtime (usa `fetch` nativo) |
| Alertas | Webhooks salientes (Discord/Slack) |
| Despliegue | Render |

## Alcance (a propósito limitado)

- Fingerprinting simple: `hash(tipo_excepción + archivo + línea)`. Sin análisis semántico avanzado.
- Sin autenticación de usuarios — cada proyecto se identifica por una `api_key` opaca, no hay cuentas ni permisos.
- Dos lenguajes soportados (Python/FastAPI y Node/Express) para demostrar que el protocolo de ingesta es agnóstico — no busca cubrir todos los frameworks existentes.

Ver [`Contexto.md`](Contexto.md) para el detalle completo de las decisiones de alcance del MVP original.
