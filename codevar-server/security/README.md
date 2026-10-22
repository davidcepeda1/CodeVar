# Pipeline de seguridad de CodeVAR

Procedimiento repetible para detectar fallas y comprobar su corrección.
Todo se ejecuta en local con datos sintéticos; no contacta la instancia pública.

## Requisitos

- Python 3.13 y Git
- Desde `codevar-server`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-security.txt
```

## Ejecución

```bash
bash security/run_security_checks.sh <etiqueta>
```

Etapas, en orden:

| Etapa | Herramienta | Falla cuando |
|-------|-------------|--------------|
| SAST | bandit 1.9.4 sobre `app/` | hay un hallazgo de severidad y confianza media o mayor |
| SCA | pip-audit 2.10.1 sobre `requirements.txt` | hay una vulnerabilidad conocida no registrada en `sca_excepciones.txt` |
| Pruebas | pytest sobre `tests/` | falla una prueba o una prueba `xfail(strict=True)` empieza a pasar |
| DAST | Schemathesis 4.32.3 en proceso | alguna petición generada produce un error 500 |

El script sale con código 1 si alguna etapa falla.

## Evidencia

Cada ejecución crea `evidencias/<fecha>_<etiqueta>_<commit>/` con el entorno,
los reportes JSON y JUnit, las salidas de pytest y un `SHA256SUMS` para
comprobar que no fueron alterados. En GitHub Actions la carpeta se publica como
artefacto durante 90 días.

## Repetir la comparación antes y después

```bash
git checkout cb154e2   # pruebas y pipeline sobre el código original
bash security/run_security_checks.sh antes
git checkout d5e9514   # mismas pruebas, código corregido
bash security/run_security_checks.sh despues
```

`git diff cb154e2 d5e9514 -- tests tests_dast security` sale vacío: las pruebas
son idénticas en ambas ejecuciones.

## Excepciones

Ver `excepciones.md`. Toda excepción requiere justificación, control
compensatorio, responsable y fecha de expiración.
