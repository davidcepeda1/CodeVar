# codevar-client

SDK/middleware instalable para capturar excepciones no manejadas en apps FastAPI y reportarlas a un servidor [`codevar-server`](../codevar-server).

## Instalación

Desde el proyecto donde se quiere usar (ej. `backend-canchas`):

```bash
pip install -e /ruta/a/codevar-client
```

## Uso

```python
from fastapi import FastAPI
from codevar_client.middleware import CodevarMiddleware
from codevar_client.config import CodevarConfig

app = FastAPI()

app.add_middleware(
    CodevarMiddleware,
    config=CodevarConfig(
        server_url="https://mi-codevar-server.onrender.com",
        api_key="la-api-key-del-proyecto",
    ),
)
```

Cualquier excepción no manejada que ocurra dentro de un endpoint se captura automáticamente, se extraen tipo de excepción/archivo/línea del traceback, y se envía como evento a `codevar-server`. La excepción original se sigue propagando normalmente (FastAPI responde su 500 como siempre).

## Componentes

| Módulo | Responsabilidad |
|---|---|
| `config.py` | `CodevarConfig`: URL del servidor, API key del proyecto, timeout |
| `middleware.py` | `CodevarMiddleware`: intercepta requests, captura excepciones |
| `traceback_utils.py` | `extract_exception_info`: parsea el traceback (frame donde ocurrió el `raise`) |
| `reporter.py` | `EventReporter`: hace `POST /api/events` al servidor |

Ver `Contexto.md` y `Planning.md` en la raíz del proyecto para el contexto y plan de desarrollo completos.
