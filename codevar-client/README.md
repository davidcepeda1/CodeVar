# codevar-client

SDK/middleware instalable para capturar excepciones no manejadas en apps FastAPI y reportarlas a [`codevar-server`](../codevar-server).

## Contexto

CodeVAR es un mini error-tracker inspirado en Sentry, deliberadamente limitado a un solo lenguaje: **Python + FastAPI**. `codevar-client` es la mitad que vive *dentro* de la app que quieres monitorear — no es un servicio aparte, es un middleware que se instala como cualquier paquete Python.

Cuando ocurre una excepción no manejada en un endpoint, el middleware la captura, extrae de dónde vino (tipo de excepción, archivo y línea exactos donde se hizo el `raise`) y la envía a `codevar-server` por HTTP — sin interrumpir el flujo normal de la app: la excepción se sigue propagando después, y si `codevar-server` no responde, el reporte falla en silencio (ver más abajo). Ver [`../Contexto.md`](../Contexto.md) para las decisiones de alcance completas.

## Arquitectura

```
Tu app FastAPI
      │  excepción no manejada dentro de un endpoint
      ▼
CodevarMiddleware.dispatch()
      │  atrapa la excepción, la vuelve a lanzar (no cambia el 500 normal)
      ▼
extract_exception_info()      →  usa el frame MÁS PROFUNDO del traceback
                                  (donde ocurrió el `raise`, no donde se atrapó)
      ▼
EventReporter.send()          →  POST {server_url}/api/events
                                  si falla (servidor caído, timeout, etc.),
                                  loguea un warning y sigue — nunca re-lanza
```

| Módulo | Responsabilidad |
|---|---|
| `config.py` | `CodevarConfig`: `server_url`, `api_key` del proyecto, `timeout` (default 2s) |
| `middleware.py` | `CodevarMiddleware`: intercepta cada request, captura excepciones no manejadas y arma `extra_context` (user-agent, query params) |
| `traceback_utils.py` | `extract_exception_info`: parsea el traceback y arma el `ExceptionInfo` a reportar |
| `reporter.py` | `EventReporter`: hace el `POST /api/events`, absorbe cualquier error de red |

## Instalación

Desde el proyecto FastAPI donde se quiere usar:

```bash
pip install -e /ruta/a/codevar-client
```

(Instala también sus dependencias: `starlette` y `requests`.)

## Uso

```python
from fastapi import FastAPI
from codevar_client.middleware import CodevarMiddleware
from codevar_client.config import CodevarConfig

app = FastAPI()

app.add_middleware(
    CodevarMiddleware,
    config=CodevarConfig(
        server_url="http://localhost:8000",  # la URL de TU codevar-server, no la de esta app
        api_key="la-api-key-del-proyecto",    # la que te muestra el dashboard al crear el proyecto
    ),
)
```

`server_url` y `api_key` se obtienen creando un proyecto desde el dashboard de `codevar-server` (`+ Nuevo proyecto`) — el panel "Cómo conectar este proyecto" te da este mismo snippet ya completado, listo para copiar.

Con eso agregado, cualquier excepción no manejada que ocurra dentro de un endpoint:

1. Se captura automáticamente (no hace falta envolver nada en `try/except`)
2. Se extrae tipo de excepción, archivo y línea del frame donde ocurrió el `raise`
3. Se captura también `extra_context` (JSON): el `user-agent` y los query params de la request que originó el error
4. Se envía como evento a `codevar-server`, que lo agrupa por fingerprint
5. La excepción original se sigue propagando normalmente — FastAPI responde su `500` como siempre, el middleware no cambia ese comportamiento

**Nota importante:** el reporter nunca lanza excepciones propias. Si `codevar-server` está caído o no responde, el intento de reportar falla en silencio (se loguea un warning) — CodeVAR nunca debe ser la razón por la que tu app se cae de forma distinta a como ya se caía.

## Qué captura y qué no

- **Sí captura**: cualquier `Exception` no manejada que se propague desde un endpoint — errores de lógica, de base de datos, excepciones de terceros, bugs propios.
- **No captura** (a propósito): `HTTPException` deliberados (404, 400, etc. — son respuestas intencionales, no bugs) ni errores de validación de Pydantic (422) — FastAPI los convierte en respuesta antes de que lleguen al middleware. Tampoco captura errores en `BackgroundTasks`, que corren después de que la respuesta ya se envió (limitación conocida, no una decisión de diseño).

## Stack

- Python ≥ 3.9
- `starlette` (el middleware se basa en `BaseHTTPMiddleware`)
- `requests` (envío del evento)

Ver [`../Planning.md`](../Planning.md) para el plan de desarrollo completo por fases.
