#!/bin/sh
# Despliega en el NAS el commit actual de la rama de la versión (lo usa el agente tras cada push).
#   - Si desde lo desplegado solo cambia código (src/, assets/): copia en caliente (tar por SSH) a la carpeta code/ del stack
#     y reinicia el contenedor si cambia el backend. Tarda unos segundos.
#   - Si cambian dependencias, Dockerfile o librerías de la página: espera a la imagen nueva de GitHub Actions y la baja.
# Uso: tools/deploy.sh [--imagen]      (--imagen fuerza el camino de la imagen)
set -eu
HOST=${BODYLENS_HOST:-nas}
STACK=${BODYLENS_STACK:-/volume1/docker/stacks/bodylens}
DOCKER="sudo -n /usr/local/bin/docker"
cd "$(git rev-parse --show-toplevel)"
# solo se despliega el commit: lo que esté sin commit se queda en local (se avisa para que no sorprenda)
[ -z "$(git status --porcelain --untracked-files=no -- src assets docker pyproject.toml)" ] || echo "Aviso: hay cambios sin commit; se despliega solo el commit $(git rev-parse --short=7 HEAD)." >&2
SHA=$(git rev-parse --short=7 HEAD)
PREV=$(ssh -o BatchMode=yes "$HOST" "cut -d' ' -f1 $STACK/code/REVISION 2>/dev/null || true")
IMAGE=0
[ "${1:-}" = "--imagen" ] && IMAGE=1
if [ -z "$PREV" ] || ! git cat-file -e "$PREV^{commit}" 2>/dev/null; then IMAGE_CHANGES="(primer despliegue en caliente)"; else
  IMAGE_CHANGES=$(git diff --name-only "$PREV" HEAD -- docker/Dockerfile docker/entrypoint.sh pyproject.toml src/frontend/package.json src/frontend/package-lock.json)
fi
[ -n "$PREV" ] && [ -n "$IMAGE_CHANGES" ] && [ "$IMAGE_CHANGES" != "(primer despliegue en caliente)" ] && IMAGE=1
BACKEND=1
if [ -n "$PREV" ] && git cat-file -e "$PREV^{commit}" 2>/dev/null && [ -z "$(git diff --name-only "$PREV" HEAD -- src/backend)" ]; then BACKEND=0; fi

if [ "$IMAGE" = 1 ]; then
  echo "Cambian dependencias o la imagen: espero al build de GitHub Actions del commit $SHA…"
  RID=""
  for i in $(seq 1 30); do RID=$(gh run list --workflow docker.yml --commit "$(git rev-parse HEAD)" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || true); [ -n "$RID" ] && break; sleep 5; done
  [ -n "$RID" ] || { echo "No encuentro el build del commit $SHA (¿has hecho push?)." >&2; exit 1; }
  gh run watch "$RID" --exit-status >/dev/null || { echo "El build $RID ha fallado." >&2; exit 1; }
fi

# código: export limpio del commit (solo lo que está en git). En el NAS se borran los ficheros (no las carpetas, que el
# contenedor tiene montadas) y se extrae encima; el NAS no permite rsync por SSH.
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
git archive HEAD src assets | tar -x -C "$TMP"
echo "$SHA $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$TMP/REVISION"
COPYFILE_DISABLE=1 tar --no-xattrs -c -C "$TMP" src assets REVISION | ssh -o BatchMode=yes "$HOST" \
  "mkdir -p $STACK/code && find $STACK/code -type f -delete && tar -x -C $STACK/code && find $STACK/code -depth -type d -empty -delete; mkdir -p $STACK/code"

if [ "$IMAGE" = 1 ]; then
  ssh -o BatchMode=yes "$HOST" "cd $STACK && $DOCKER compose -p bodylens pull -q && $DOCKER compose -p bodylens up -d"
elif [ "$BACKEND" = 1 ]; then
  ssh -o BatchMode=yes "$HOST" "$DOCKER restart bodylens >/dev/null"
fi
for i in $(seq 1 30); do
  S=$(ssh -o BatchMode=yes "$HOST" "$DOCKER inspect --format '{{.State.Health.Status}}' bodylens" 2>/dev/null || true)
  [ "$S" = healthy ] && break; sleep 4
done
echo "Desplegado $SHA en $HOST ($([ "$IMAGE" = 1 ] && echo 'imagen nueva' || ([ "$BACKEND" = 1 ] && echo 'en caliente, con reinicio' || echo 'en caliente, sin reinicio'))): $S"
[ "$S" = healthy ]
