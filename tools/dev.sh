#!/bin/sh
# Servidor de desarrollo en caliente (sin Docker): http://localhost:8000
# Lee los ficheros del repositorio tal cual (la página al recargar, el backend se reinicia solo al guardar) y usa los
# datos de data-dev/ (tools/dev-data.sh copia ahí los del NAS; lo que se cambie aquí no vuelve al NAS).
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
if [ ! -f src/frontend/vendor/xlsx.full.min.js ]; then
  mkdir -p src/frontend/vendor
  for f in xlsx/dist/xlsx.full.min.js jspdf/dist/jspdf.umd.min.js html2canvas-pro/dist/html2canvas-pro.min.js; do
    cp "src/frontend/node_modules/$f" src/frontend/vendor/
  done
fi
export DATA_DIR="$ROOT/data-dev" COOKIE_SECURE=0 SCHEDULER_ENABLED=0 PUBLIC_URL=http://localhost:${PORT:-8000} \
       BODYLENS_REVISION=desarrollo BODYLENS_REVISION_FILE="$ROOT/data-dev/REVISION" TZ=Europe/Madrid
cd src/backend
exec "$ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}" --reload --reload-dir app
