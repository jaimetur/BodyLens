#!/usr/bin/env python3
"""Google Play screenshots of the app in every language of the app, taken with the SYNTHETIC demo account.

    DATA_DIR=<demo dir> .venv/bin/python tools/demo_data.py          # demo account (prints its password)
    (start a server on that DATA_DIR, e.g. on port 8765)
    DEMO_PASSWORD=... .venv/bin/python tools/store_capture.py [--url http://localhost:8765] [--out DIR] [--lang en,es]

For each language (all of them by default) it takes 7 screenshots of the same screens (Summary, Weight, Sleep,
Activity, Heart, Meals, History) on three devices, the sizes Google Play asks for:

    <out>/<lang>/phone/1-resumen.png …        1080×1920 (9:16)
    <out>/<lang>/tablet/1-resumen.png …       1620×2880 (9:16; the same images for 7-inch and 10-inch tablets)
    <out>/<lang>/chromebook/1-resumen.png …   2880×1620 (16:9)

and <out>/manifest.json (build and languages). The default output is assets/play-store/screenshots, which git ignores:
GitHub Actions makes them whenever the app's layout changes (.github/workflows/play-store.yml) and leaves them in the
"play-store-media" release; tools/play-store-media.sh downloads them there and tools/play_publish.py uploads them to
Play Console. Same requirements as tools/landing_capture.py (Playwright, Pillow), whose helpers it uses.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import landing_capture as lc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# language of the app → browser locale
LANGS = {"en": "en-GB", "es": "es-ES", "ca": "ca-ES", "de": "de-DE", "fr": "fr-FR", "it": "it-IT", "ja": "ja-JP",
         "nl": "nl-NL", "pt": "pt-PT", "zh": "zh-CN"}
SHOTS = [("1-resumen", "resumen", "gen"), ("2-peso", "peso", "evo"), ("3-sueno", "sueno", "hoy"),
         ("4-actividad", "actividad", "evo"), ("5-corazon", "corazon", None), ("6-comidas", "comidas", None),
         ("7-historial", "historial", None)]
DEVICES = {
    "phone": {"viewport": {"width": 360, "height": 640}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True},
    "tablet": {"viewport": {"width": 810, "height": 1440}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True},
    "chromebook": {"viewport": {"width": 1440, "height": 810}, "device_scale_factor": 2},
}


def capture(browser, url: str, password: str, lang: str, out: Path) -> None:
    lc.SFX = "" if lang == "es" else "-" + lang   # lc.translated() waits for the translation unless Spanish
    lc.COMMON["locale"] = LANGS[lang]
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state.json"
        lc.login(browser, url, password, state, lang)
        for device, profile in DEVICES.items():
            d = out / lang / device
            d.mkdir(parents=True, exist_ok=True)
            page = lc.new_page(browser, state, profile)
            page.goto(url + "/#resumen")
            lc.translated(page)
            lc.settle(page, 2500)
            for name, view, tab in SHOTS:
                lc.go(page, view, tab, 1800)
                page.screenshot(path=str(d / f"{name}.png"))
            page.context.close()
            print(f"   {lang} {device}: {len(SHOTS)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default="http://localhost:8765")
    ap.add_argument("--out", default=str(ROOT / "assets" / "play-store" / "screenshots"))
    ap.add_argument("--lang", default=",".join(LANGS), help="comma-separated languages (default: all)")
    a = ap.parse_args()
    langs = [x for x in a.lang.split(",") if x]
    bad = [x for x in langs if x not in LANGS]
    if bad:
        sys.exit(f"Unknown languages: {', '.join(bad)} (known: {', '.join(LANGS)})")
    password = os.environ.get("DEMO_PASSWORD") or sys.exit("Set DEMO_PASSWORD (printed by tools/demo_data.py).")
    out, url = Path(a.out), a.url.rstrip("/")
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for lang in langs:
                capture(browser, url, password, lang, out)
        finally:   # the demo account goes back to Spanish
            with tempfile.TemporaryDirectory() as tmp:
                lc.login(browser, url, password, Path(tmp) / "state.json", "es")
        browser.close()
    build = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    (out / "manifest.json").write_text(json.dumps({"build": build, "languages": langs, "devices": list(DEVICES),
                                                   "shots": [s[0] for s in SHOTS]}, indent=1) + "\n")
    print(f"{out}: {len(langs)} languages")


if __name__ == "__main__":
    main()
