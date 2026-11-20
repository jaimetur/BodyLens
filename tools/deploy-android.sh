#!/bin/sh
# Puts the latest APKs of the Android apps on the NAS (the rolling "android-latest" release, rebuilt by GitHub Actions),
# so the server serves BodyLens at /android.apk and BodyLens Bridge at /android-bridge.apk. Usage: tools/deploy-android.sh   (after a push that changes android/)
set -eu
HOST=${BODYLENS_HOST:-nas}
DATA=${BODYLENS_DATA:-/volume1/docker/data/bodylens}
cd "$(git rev-parse --show-toplevel)"
SHA=$(git rev-parse HEAD)
RID=""
for i in $(seq 1 30); do RID=$(gh run list --workflow android.yml --commit "$SHA" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || true); [ -n "$RID" ] && break; sleep 5; done
if [ -n "$RID" ]; then gh run watch "$RID" --exit-status >/dev/null || { echo "The Android build $RID failed." >&2; exit 1; }; fi
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
gh release download android-latest -p bodylens-android.apk -p bodylens-bridge.apk -p android-build.txt -D "$TMP"
for f in bodylens-android.apk bodylens-bridge.apk; do
  ssh -o BatchMode=yes "$HOST" "mkdir -p $DATA/downloads && cat > $DATA/downloads/$f.tmp && mv $DATA/downloads/$f.tmp $DATA/downloads/$f && chmod 644 $DATA/downloads/$f" < "$TMP/$f"
done
echo "APKs on the NAS (BodyLens and BodyLens Bridge): $(cat "$TMP/android-build.txt")"
