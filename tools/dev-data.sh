#!/bin/sh
# Copia los datos del NAS (base de datos y libros de cada cuenta; nunca los secretos) a data-dev/, para el servidor de
# desarrollo en caliente (docker/compose.dev.yml). Lo que se cambie en desarrollo NO vuelve al NAS.
set -eu
HOST=${BODYLENS_HOST:-nas}
cd "$(git rev-parse --show-toplevel)"
mkdir -p data-dev
ssh -o BatchMode=yes "$HOST" 'sudo -n /usr/local/bin/docker exec bodylens python -c "
import sqlite3; s=sqlite3.connect(\"/data/bodylens.db\"); d=sqlite3.connect(\"/tmp/dev-copy.db\"); s.backup(d); d.close()
" && sudo -n /usr/local/bin/docker exec bodylens sh -c "cd /data && tar -c users -C /tmp dev-copy.db 2>/dev/null; rm -f /tmp/dev-copy.db"' \
  | tar -x -C data-dev
rm -f data-dev/bodylens.db data-dev/bodylens.db-wal data-dev/bodylens.db-shm
mv data-dev/dev-copy.db data-dev/bodylens.db
echo "Datos del NAS copiados a data-dev/ ($(du -sh data-dev | cut -f1))."
