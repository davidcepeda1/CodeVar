# Registro de excepciones de seguridad

Una excepción permite que el pipeline apruebe aunque un riesgo conocido siga
abierto. Solo es válida si tiene todos los campos, una fecha de expiración y
una prueba marcada con `xfail(strict=True)` o una entrada en
`sca_excepciones.txt`. Al vencer la fecha, la excepción se elimina o se
renueva con nueva justificación.

| ID | Riesgo | Prueba | Justificación | Control compensatorio | Responsable | Expira |
|----|--------|--------|---------------|-----------------------|-------------|--------|
| EXC-01 | R1 Inicio expone api_key | CP-11 | Requiere autenticación de usuarios, cambio de arquitectura planificado para el Parcial 2 | Instancia pública sin datos reales; claves rotadas | David Cepeda | 2026-12-15 |
| EXC-02 | R3 Formularios sin token CSRF | CP-12 | Depende de las sesiones introducidas con EXC-01 | Borrado exige escribir el nombre exacto del proyecto | David Cepeda | 2026-12-15 |
