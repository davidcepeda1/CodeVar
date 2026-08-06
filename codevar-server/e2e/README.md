# Prueba end-to-end: backend-canchas → codevar-client → codevar-server

Valida el flujo completo con un error **real**, no simulado.

## Cómo correrla

Activar el entorno virtual antes de cualquier comando (`source .venv/bin/activate` en bash/zsh,
`source .venv/bin/activate.fish` en fish).

1. Crear la base de datos de prueba (SQLite) con un `Project` registrado:

    ```bash
    cd codevar-server
    DATABASE_URL="sqlite:////tmp/codevar_e2e.db" python e2e/setup_e2e_project.py
    ```

2. Levantar `codevar-server` apuntando a esa misma base de datos (dejar corriendo en su propia terminal):

    ```bash
    DATABASE_URL="sqlite:////tmp/codevar_e2e.db" uvicorn app.main:app --port 8098
    ```

3. En otra terminal, correr la prueba (ajustar `BACKEND_CANCHAS_PATH` si tu clon está en otra ruta):

    ```bash
    BACKEND_CANCHAS_PATH=/ruta/a/backend-canchas python e2e/test_e2e_backend_canchas.py
    ```

4. Ver el resultado en el navegador (con el servidor del paso 2 todavía corriendo):

    ```
    http://127.0.0.1:8098/dashboard?api_key=e2e-test-key
    ```

    Debería aparecer una fila `AttributeError` — al entrar al detalle, cada evento tiene un botón
    **Copiar** para llevar el stack trace completo al portapapeles.

## Qué hace

Dispara un bug real ya existente en `backend-canchas` (`routers/reservas.py::actualizar_reserva`):
si la cancha asociada a una reserva ya no existe, el código accede a `cancha.id` sin comprobar
`None`, lo cual lanza un `AttributeError` no manejado. La prueba reproduce ese escenario con datos
reales (crea cancha + reserva, borra la cancha con un bulk-delete que evita el cascade de
SQLAlchemy a nivel de ORM, y actualiza la reserva) para forzar la excepción de forma legítima —
no se lanza un error a mano en el código de prueba.

La conexión de `backend-canchas` a su base de datos real (Supabase) se sustituye por SQLite en
memoria solo para esta corrida; no se modifica ningún archivo del repo de `backend-canchas`.

## Resultado verificado (2026-08-06)

- `CodevarMiddleware` capturó el `AttributeError` en `routers/reservas.py:44`
- `codevar-server` recibió el evento (`POST /api/events` → `201`)
- `GET /api/errors` mostró el grupo con `exception_type`, `file_path` y `line_number` correctos
- `GET /api/errors/{id}` mostró el stack trace completo, `request_path=/reservas/1` y `request_method=PUT`

## Nota

Este bug de `backend-canchas` es real y sigue sin corregir — quedó identificado gracias a esta
prueba, pero corregirlo está fuera del alcance de CodeVAR (pertenece al otro repositorio).
