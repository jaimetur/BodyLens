#!/bin/sh
# Copies the landing page's videos and screenshots to the NAS (<DATA_DIR>/landing-media), from the "landing-media"
# release that GitHub Actions records whenever the app's layout changes (.github/workflows/landing-media.yml).
# Only when they changed (their manifest's build differs). Run by tools/deploy.sh; usage: tools/deploy-landing-media.sh
# The previous copy may belong to the container's user (it seeds the folder at start), so it is removed through it if needed.
set -eu
HOST=${BODYLENS_HOST:-nas}
DATA=${BODYLENS_DATA:-/volume1/docker/data/bodylens}
cd "$(git rev-parse --show-toplevel)"
gh release view landing-media >/dev/null 2>&1 || { echo "No landing-media release yet: the landing page uses the media in the repository."; exit 0; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
gh release download landing-media -p manifest.json -D "$TMP" >/dev/null
NEW=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('build',''))" "$TMP/manifest.json")
OLD=$(ssh -o BatchMode=yes "$HOST" "cat $DATA/landing-media/manifest.json 2>/dev/null" | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('build',''))
except Exception: print('')")
if [ -n "$NEW" ] && [ "$NEW" = "$OLD" ]; then echo "Landing media already up to date ($NEW)."; exit 0; fi
gh release download landing-media -D "$TMP/media" >/dev/null
COPYFILE_DISABLE=1 tar --no-xattrs -c -C "$TMP/media" . | ssh -o BatchMode=yes "$HOST" \
  "rmold() { rm -rf $DATA/landing-media.old 2>/dev/null || sudo -n /usr/local/bin/docker exec -u 1034:65544 bodylens rm -rf /data/landing-media.old 2>/dev/null || true; };
   mkdir -p $DATA/landing-media.new && tar -x -C $DATA/landing-media.new && chmod -R a+rX $DATA/landing-media.new && rmold && { [ ! -d $DATA/landing-media.old ] || { echo 'Cannot remove landing-media.old' >&2; exit 1; }; } && { [ ! -d $DATA/landing-media ] || mv $DATA/landing-media $DATA/landing-media.old; } && mv $DATA/landing-media.new $DATA/landing-media && rmold"
echo "Landing media on the NAS: $NEW ($(ls "$TMP/media" | wc -l | tr -d ' ') files)."
