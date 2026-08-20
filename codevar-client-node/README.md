# codevar-client (Node)

SDK/middleware instalable para capturar excepciones no manejadas en apps Express y reportarlas a [`codevar-server`](../codevar-server).

## Contexto

CodeVAR nació limitado a un solo lenguaje (Python + FastAPI). Este paquete demuestra que el protocolo de ingesta (`POST /api/events` con `project_api_key` + payload JSON) es agnóstico de lenguaje — `codevar-server` no necesita ningún cambio para aceptar eventos que vienen de Node en vez de Python. Es el equivalente en Node/Express de [`codevar-client`](../codevar-client).

Cuando ocurre un error no manejado en una ruta Express, el middleware lo captura, extrae de dónde vino (tipo de error, archivo y línea del primer frame del stack) y lo envía a `codevar-server` por HTTP — sin interrumpir el flujo normal de la app.

## Arquitectura

```
Tu app Express
      │  error no manejado en una ruta (o pasado a next(err))
      ▼
codevarErrorHandler()          →  error middleware de Express
      │  captura, reporta, y hace next(err) para no cambiar
      │  el manejo de errores normal de tu app
      ▼
extractExceptionInfo()         →  parsea err.stack, toma el primer frame
                                   (dónde se hizo el `throw`)
      ▼
reporter.send()                →  POST {serverUrl}/api/events
                                   si falla (servidor caído, timeout, etc.),
                                   loguea un warning y sigue — nunca re-lanza
```

| Módulo | Responsabilidad |
|---|---|
| `src/config.js` | `createConfig`: `serverUrl`, `apiKey` del proyecto, `timeout` (default 2000ms) |
| `src/middleware.js` | `codevarErrorHandler`: error middleware de Express, captura + arma `extra_context` (user-agent, query params) |
| `src/stackUtils.js` | `extractExceptionInfo`: parsea `err.stack` y arma la info a reportar |
| `src/reporter.js` | `send`: hace el `POST /api/events` con `fetch` nativo, absorbe cualquier error de red |

## Instalación

Desde el proyecto Express donde se quiere usar:

```bash
npm install /ruta/a/codevar-client-node
```

Requiere Node ≥ 18 (usa el `fetch` global, sin dependencias externas de HTTP) y Express ≥ 4 como peer dependency.

## Uso

```js
const express = require("express");
const { createConfig, codevarErrorHandler } = require("codevar-client");

const app = express();

const config = createConfig({
  serverUrl: "http://localhost:8000", // la URL de TU codevar-server, no la de esta app
  apiKey: "la-api-key-del-proyecto",  // la que te muestra el dashboard al crear el proyecto
});

// ... tus rutas normales ...

// el error handler de CodeVAR va DESPUÉS de tus rutas
app.use(codevarErrorHandler(config));

// tu propio error handler (opcional) va después del de CodeVAR
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.message });
});
```

`server_url` y `api_key` se obtienen creando un proyecto desde el dashboard de `codevar-server` — igual que para el SDK de Python.

**Importante — límite de Express 4:** Express 4 solo captura automáticamente los errores lanzados de forma **síncrona** dentro de una ruta. Si tu handler es `async`, tienes que atrapar el error y pasarlo tú mismo:

```js
app.get("/ruta", async (req, res, next) => {
  try {
    await algoQuePuedeFallar();
  } catch (err) {
    next(err); // sin esto, codevarErrorHandler nunca se entera
  }
});
```

(Express 5 sí reenvía automáticamente los rechazos de promesas — si migras, este paso deja de ser necesario.)

## Qué captura y qué no

- **Sí captura**: cualquier `Error` que llegue al error middleware de Express — ya sea lanzado sincrónicamente en una ruta, o pasado explícitamente con `next(err)`.
- **No captura** (a propósito): errores en callbacks fuera del ciclo request/response de Express (timers, listeners de eventos, colas), ni rechazos de promesas no atrapados en handlers `async` (ver limitación de Express 4 arriba).

## Test end-to-end

`test/e2e.test.js` levanta un `codevar-server` real (SQLite temporal), monta la app Express de ejemplo (`examples/demo-app.js`), dispara errores reales (uno síncrono repetido y uno async) y verifica contra la API de `codevar-server` que se agruparon correctamente y que `extra_context` llegó completo:

```bash
npm install
npm test
```

## Stack

- Node ≥ 18
- `express` (peer dependency — el middleware se registra con `app.use`)
- Sin dependencias de runtime: usa `fetch` nativo

Ver [`../Planning.md`](../Planning.md) para el plan de desarrollo original por fases, y el plan de v0.2.0 para el contexto de esta fase.
