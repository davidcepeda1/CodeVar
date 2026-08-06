# Pruebas manuales — POST /api/events

Importar `codevar.postman_collection.json` en Postman. Requiere que el servidor esté corriendo (`uvicorn app.main:app --reload`) y que exista un `Project` en la base de datos con `api_key = abc123` (ajustar la variable `api_key` de la colección si se usa otra).

## Casos cubiertos

| # | Caso | Resultado esperado |
|---|------|---------------------|
| 1 | Evento válido, error nunca visto | `201`, se crea un `ErrorGroup` nuevo con `event_count = 1` |
| 2 | Mismo `exception_type` + `file_path` + `line_number` que el caso 1 | `201`, reutiliza el mismo `error_group_id`, `event_count` sube a 2 |
| 3 | Mismo tipo/archivo pero distinta `line_number` | `201`, crea un `ErrorGroup` distinto (fingerprint distinto) |
| 4 | `project_api_key` que no existe | `401 invalid project api key` |
| 5 | Payload sin campos requeridos (`file_path`, `line_number`) | `422` de validación de Pydantic |

Verificar en la base de datos (o en el siguiente endpoint de consulta, Fase 3) que `error_groups.event_count` y `last_seen` se actualizan como se espera en el caso 2.
