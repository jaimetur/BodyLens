#!/bin/sh
# Downloads the latest Google Play screenshots (phone, tablet and Chromebook, every language) that GitHub Actions takes
# whenever the app's layout changes (.github/workflows/play-store.yml, "play-store-media" release) to
# assets/play-store/screenshots/<lang>/<device>/, ready to upload to Play Console by hand or with
# tools/play_publish.py listing --images assets/play-store/screenshots.  Usage: tools/play-store-media.sh
set -eu
cd "$(git rev-parse --show-toplevel)"
OUT=assets/play-store/screenshots
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
gh release download play-store-media -D "$TMP" >/dev/null || { echo "No play-store-media release yet (run the 🛍️ Google Play screenshots workflow)."; exit 1; }
rm -rf "$OUT" && mkdir -p "$OUT"
for z in "$TMP"/screenshots-*.zip; do l=$(basename "$z" .zip); l=${l#screenshots-}; mkdir -p "$OUT/$l" && unzip -q "$z" -d "$OUT/$l"; done
cp "$TMP/manifest.json" "$OUT/"
echo "Screenshots of build $(python3 -c "import json;print(json.load(open('$OUT/manifest.json'))['build'])") in $OUT: $(ls "$OUT" | grep -v manifest | tr '\n' ' ')"
