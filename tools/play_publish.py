#!/usr/bin/env python3
"""Publishes BodyLens to Google Play Console with the Google Play Developer API, without the web console.

    PLAY_SERVICE_ACCOUNT_JSON="$(cat key.json)" python tools/play_publish.py bundle app.aab [--track alpha] [--name "0.2.0 (45)"]
    PLAY_SERVICE_ACCOUNT_JSON="$(cat key.json)" python tools/play_publish.py listing [--images DIR] [--validate]

- bundle: uploads an Android App Bundle and releases it to a track (alpha, the closed test, by default; production
  needs Google's approval first), with --name as the release name and --notes as its English notes.
- listing: updates the store listing of every language in assets/play-store/listings/<locale>.json (title, short and
  full description) and, with --images, replaces its screenshots with those of tools/store_capture.py
  (<DIR>/<lang>/phone|tablet/*.png; Chromebook screenshots cannot be uploaded through the API) and its feature graphic
  (assets/play-store/feature-1024x500-<es|en>.png). --validate checks the changes and discards them.

The service account (its JSON key in PLAY_SERVICE_ACCOUNT_JSON, or a file with --key) needs, in Play Console → Users
and permissions, "Release apps to testing tracks" (and "Release to production" for production) and "Manage store
presence" for the listing. Changes go through Google's review as when they are made by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "app.bodylens.android"
API = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}"
UPLOAD = f"https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/{PACKAGE}"
LISTINGS = ROOT / "assets" / "play-store" / "listings"
# Play locale → language of the app whose screenshots it shows
APP_LANG = {"en-US": "en", "es-ES": "es", "es-419": "es", "ca": "ca", "de-DE": "de", "fr-FR": "fr", "it-IT": "it",
            "ja-JP": "ja", "nl-NL": "nl", "pt-PT": "pt", "pt-BR": "pt", "zh-CN": "zh"}
IMAGES = {"phoneScreenshots": "phone", "sevenInchScreenshots": "tablet", "tenInchScreenshots": "tablet"}


def session(key: str | None) -> AuthorizedSession:
    info = json.loads(Path(key).read_text() if key else os.environ.get("PLAY_SERVICE_ACCOUNT_JSON") or "null")
    if not info:
        sys.exit("No service account: set PLAY_SERVICE_ACCOUNT_JSON or pass --key.")
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/androidpublisher"])
    return AuthorizedSession(creds)


def ok(r):
    if r.status_code >= 400:
        sys.exit(f"Google Play: {r.status_code} {r.text[:600]}")
    return r.json() if r.content else {}


def finish(s: AuthorizedSession, edit: str, validate: bool) -> None:
    if validate:
        ok(s.post(f"{API}/edits/{edit}:validate"))
        s.delete(f"{API}/edits/{edit}")
        print("Valid; nothing was changed.")
    else:
        ok(s.post(f"{API}/edits/{edit}:commit"))
        print("Sent to Google Play.")


def bundle(s: AuthorizedSession, a) -> None:
    edit = ok(s.post(f"{API}/edits"))["id"]
    with open(a.aab, "rb") as f:
        b = ok(s.post(f"{UPLOAD}/edits/{edit}/bundles", params={"uploadType": "media"}, data=f,
                      headers={"Content-Type": "application/octet-stream"}, timeout=600))
    code = b["versionCode"]
    notes = [{"language": "en-US", "text": a.notes}] if a.notes else []
    release = {"versionCodes": [str(code)], "status": a.status, "releaseNotes": notes, **({"name": a.name} if a.name else {})}
    ok(s.put(f"{API}/edits/{edit}/tracks/{a.track}", json={"track": a.track, "releases": [release]}))
    print(f"Version {code} → {a.track} ({a.status}).")
    finish(s, edit, a.validate)


def listing(s: AuthorizedSession, a) -> None:
    edit = ok(s.post(f"{API}/edits"))["id"]
    for p in sorted(LISTINGS.glob("*.json")):
        loc = p.stem
        t = json.loads(p.read_text(encoding="utf-8"))
        ok(s.put(f"{API}/edits/{edit}/listings/{loc}", json={"language": loc, **t}))
        n = 0
        if a.images:
            lang = APP_LANG[loc]
            feat = ROOT / "assets" / "play-store" / f"feature-1024x500-{'es' if lang == 'es' else 'en'}.png"
            for kind, files in [("featureGraphic", [feat])] + [
                    (k, sorted((Path(a.images) / lang / d).glob("*.png"))) for k, d in IMAGES.items()]:
                if not files:
                    continue
                ok(s.delete(f"{API}/edits/{edit}/listings/{loc}/{kind}"))
                for f in files:
                    with open(f, "rb") as fh:
                        ok(s.post(f"{UPLOAD}/edits/{edit}/listings/{loc}/{kind}", params={"uploadType": "media"},
                                  data=fh, headers={"Content-Type": "image/png"}, timeout=300))
                    n += 1
        print(f"   {loc}: texts" + (f" and {n} images" if n else ""))
    finish(s, edit, a.validate)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--key", help="service account JSON key file (default: PLAY_SERVICE_ACCOUNT_JSON)")
    ap.add_argument("--validate", action="store_true", help="check the changes and discard them")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bundle", help="upload an AAB and release it to a track")
    b.add_argument("aab")
    b.add_argument("--track", default="alpha", help="alpha (closed test, default), internal, beta, production")
    b.add_argument("--status", default="completed", choices=["completed", "draft"])
    b.add_argument("--name", default="", help='release name shown in Play Console (e.g. "0.2.0 (45)")')
    b.add_argument("--notes", default="", help="release notes (English)")
    li = sub.add_parser("listing", help="update the store listing texts (and screenshots) of every language")
    li.add_argument("--images", help="folder of tools/store_capture.py (e.g. assets/play-store/screenshots)")
    a = ap.parse_args()
    s = session(a.key)
    bundle(s, a) if a.cmd == "bundle" else listing(s, a)


if __name__ == "__main__":
    main()
