#!/bin/sh
# Arranca como root solo para dar la carpeta de datos al usuario PUID:PGID y sigue sin privilegios.
set -e
mkdir -p "${DATA_DIR:-/data}"
if [ "$(id -u)" = "0" ]; then
  chown -R "${PUID:-1000}:${PGID:-1000}" "${DATA_DIR:-/data}" 2>/dev/null || true
  exec setpriv --reuid="${PUID:-1000}" --regid="${PGID:-1000}" --clear-groups "$@"
fi
exec "$@"
