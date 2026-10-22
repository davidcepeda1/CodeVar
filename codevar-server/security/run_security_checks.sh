#!/usr/bin/env bash
# Pipeline de seguridad de CodeVAR: SAST, SCA, pruebas y DAST en un solo paso.
# Uso, desde codevar-server:  bash security/run_security_checks.sh [etiqueta]
# Sale con código 1 si alguna etapa incumple su criterio de fallo.
set -uo pipefail
cd "$(dirname "$0")/.."

ETIQUETA="${1:-manual}"
COMMIT="$(git rev-parse --short HEAD)"
OUT="evidencias/$(date +%Y%m%d-%H%M%S)_${ETIQUETA}_${COMMIT}"
mkdir -p "$OUT"
export DATABASE_URL="sqlite:///$PWD/$OUT/laboratorio.db"
FALLOS=0

registrar() {  # etapa, código de salida
    if [ "$2" -eq 0 ]; then estado="APROBADO"; else estado="FALLIDO"; FALLOS=$((FALLOS + 1)); fi
    printf '%-28s %s\n' "$1" "$estado" | tee -a "$OUT/resumen.txt"
}

{
    echo "commit: $(git rev-parse HEAD)"
    echo "fecha:  $(date -Iseconds)"
    python --version
    pip freeze | grep -iE '^(fastapi|starlette|sqlalchemy|pydantic|pytest|bandit|pip.audit|schemathesis|hypothesis)=='
} > "$OUT/entorno.txt"

echo "== SAST: bandit"
bandit -r app -q --severity-level medium --confidence-level medium \
    -f json -o "$OUT/sast_bandit.json"
registrar "SAST bandit" $?

echo "== SCA: pip-audit"
IGNORAR=$(grep -vE '^\s*(#|$)' security/sca_excepciones.txt | awk '{print "--ignore-vuln " $1}')
# shellcheck disable=SC2086
pip-audit -r requirements.txt $IGNORAR -f json -o "$OUT/sca_pip_audit.json" \
    > "$OUT/sca_pip_audit.txt" 2>&1
registrar "SCA pip-audit" $?

echo "== Pruebas funcionales, de autorización y de entradas"
python -m pytest tests -p no:cacheprovider -rfxX --junitxml="$OUT/pruebas.xml" \
    > "$OUT/pruebas.txt" 2>&1
registrar "Pruebas pytest" $?

echo "== DAST: schemathesis"
python -m pytest tests_dast -p no:cacheprovider -rf --junitxml="$OUT/dast.xml" \
    > "$OUT/dast.txt" 2>&1
registrar "DAST schemathesis" $?

rm -f "$OUT/laboratorio.db"
(cd "$OUT" && sha256sum ./* > SHA256SUMS)
echo "Evidencia guardada en $OUT"
[ "$FALLOS" -eq 0 ] || { echo "Pipeline FALLIDO: $FALLOS etapa(s)"; exit 1; }
echo "Pipeline APROBADO"
