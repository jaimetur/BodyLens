#!/usr/bin/env python3
"""Screenshots and short videos of the app for the marketing landing page, taken with the demo account.

    DATA_DIR=<demo dir> .venv/bin/python tools/demo_data.py          # demo account (prints its password)
    (start a server on that DATA_DIR, e.g. on port 8765)
    DEMO_PASSWORD=... .venv/bin/python tools/landing_capture.py [--url http://localhost:8765] [--out DIR] [--lang en|es]

Needs Playwright and Pillow (`pip install playwright pillow && python -m playwright install chromium`; they are not
project dependencies) and ffmpeg, to trim and encode the videos. Everything goes to src/frontend/landing/media/:
screenshots as WebP, videos as MP4 (H.264) and the first frame of each video (<video>-1.webp) as its poster.
--lang en switches the demo account to English for the capture (and back to Spanish at the end) and names every file
with the suffix -en (resumen-en.webp, video-sueno-en.mp4, video-sueno-en-1.webp); Spanish files have no suffix.
The browser clock is set to 20:35 of today (Madrid), the time the demo data stops (tools/demo_data.py).
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Europe/Madrid")
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True}
DESKTOP = {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 2}
COMMON = {"locale": "es-ES", "timezone_id": "Europe/Madrid"}
LOCALES = {"es": "es-ES", "en": "en-GB"}
SFX = ""   # file name suffix of the language ("-en"; none for Spanish)
# texts the tours look for, in each language (the page translates them in the browser)
TEXTS = {"es": {"prev": "Anterior", "daily": "Pesada diaria"}, "en": {"prev": "Previous", "daily": "Daily weigh-in"}}
TXT = TEXTS["es"]
VIDEO_SIZE = {"width": 780, "height": 1688}

# (file name, view, tab or None): phone screenshots, the top of the screen as a user sees it
SHOTS = [("resumen", "resumen", "gen"), ("peso-evolucion", "peso", "evo"), ("peso-calendario", "peso", "cal"),
         ("cuerpo-bascula", "composicion", None), ("cuerpo-corazon", "corazon", None), ("actividad-hoy", "actividad", "hoy"),
         ("actividad-evolucion", "actividad", "evo"), ("sueno-noche", "sueno", "hoy"), ("sueno-saldo", "sueno", "banco"),
         ("sueno-horario", "sueno", "hor"), ("comidas-hoy", "comidas", "hoy"), ("intimo-animo", "intimo", "animo"),
         ("historial-intentos", "historial", "int")]


def evening() -> datetime:
    now = datetime.now(TZ)
    return now.replace(hour=20, minute=35, second=0, microsecond=0)


def save_webp(png: bytes, path: Path, width: int, quality: int = 82) -> None:
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=quality, method=6)


def translated(page: Page) -> None:
    """Waits until the page texts are in the capture language (they are translated in the browser after load)."""
    if SFX:
        page.wait_for_function("""() => { const s = document.querySelector('nav.vtabs[data-view="peso"] a[data-tab="evo"] span');
                                          return s && s.textContent.trim() !== 'Evolución' }""", timeout=20000)


def settle(page: Page, ms: int = 1200) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:  # noqa: BLE001 — the page polls the server; a short pause is enough then
        pass
    page.wait_for_timeout(ms)


def go(page: Page, view: str, tab: str | None = None, ms: int = 1200) -> None:
    """Opens a view (and one of its tabs) the way a user does, and waits for the charts."""
    page.evaluate("v => { if (location.hash !== '#' + v) location.hash = '#' + v }", view)
    page.wait_for_timeout(400)
    if tab:
        page.click(f'nav.vtabs[data-view="{view}"] a[data-tab="{tab}"]')
    page.evaluate("window.scrollTo(0, 0)")
    settle(page, ms)


def scroll(page: Page, dy: int, ms: int = 900) -> None:
    page.evaluate("dy => window.scrollBy({top: dy, behavior: 'smooth'})", dy)
    page.wait_for_timeout(ms)


def top(page: Page, ms: int = 700) -> None:
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(ms)


def tap(page: Page, selector: str, ms: int = 1100) -> None:
    """A finger tap on the first visible match (scrolled into view if needed)."""
    page.locator(selector).locator("visible=true").first.tap()
    page.wait_for_timeout(ms)


def tab(page: Page, view: str, name: str, ms: int = 1100) -> None:
    """Taps one of the tabs at the top of a view (scrolling up first, as a user would)."""
    if page.evaluate("window.scrollY") > 0:
        top(page)
    tap(page, f'nav.vtabs[data-view="{view}"] a[data-tab="{name}"]', ms)


def swipe(page: Page, left: bool = True, y: int = 560, ms: int = 1100) -> None:
    """A horizontal finger swipe on the page (next tab or module to the left), with real touch events."""
    cdp = page.context.new_cdp_session(page)
    xs = [330, 290, 240, 190, 140, 90, 60] if left else [60, 100, 150, 200, 250, 300, 330]

    def touch(kind, x):
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y}]})
    touch("touchStart", xs[0])
    for x in xs[1:]:
        page.wait_for_timeout(30)
        touch("touchMove", x)
    touch("touchEnd", xs[-1])
    cdp.detach()
    page.wait_for_timeout(ms)


def close_sheet(page: Page, ms: int = 700) -> None:
    tap(page, "#sheet .shclose", ms)


def set_lang(page: Page, url: str, lang: str) -> None:
    res = page.request.post(url + "/api/me/lang", data={"lang": lang}, headers={"X-BodyLens": "1"})
    if not res.ok:
        sys.exit(f"Could not set the account language to {lang}: {res.status} {res.text()}")


def login(browser, url: str, password: str, out_state: Path, lang: str) -> None:
    ctx = browser.new_context(**PHONE, **COMMON, color_scheme="light")
    page = ctx.new_page()
    page.goto(url + "/login")
    page.fill("#u", "demo")
    page.fill("#p", password)
    page.click("#go")
    page.wait_for_url(url + "/", timeout=20000)
    set_lang(page, url, lang)
    page.reload()
    settle(page, 3000)   # first start: the page reads the workbook and saves its documents
    ctx.storage_state(path=str(out_state))
    ctx.close()


def new_page(browser, state: Path, profile: dict, scheme: str = "light", video_dir: str | None = None) -> Page:
    extra = {"record_video_dir": video_dir, "record_video_size": VIDEO_SIZE} if video_dir else {}
    ctx = browser.new_context(**profile, **COMMON, color_scheme=scheme, storage_state=str(state), **extra)
    page = ctx.new_page()
    page.clock.install(time=evening())
    return page


def screenshots(browser, url: str, state: Path, out: Path) -> None:
    page = new_page(browser, state, PHONE)
    page.goto(url + "/#resumen")
    translated(page)
    settle(page, 2500)
    for name, view, tab in SHOTS:
        go(page, view, tab)
        save_webp(page.screenshot(), out / f"{name}{SFX}.webp", 1170)
        print("  ", name)
    go(page, "sueno", "hoy")
    page.click("svg.dial")
    settle(page, 1200)
    save_webp(page.screenshot(), out / f"sueno-reloj{SFX}.webp", 1170)
    print("   sueno-reloj")
    page.context.close()
    for scheme, suffix in (("dark", "-dark"),):
        page = new_page(browser, state, PHONE, scheme)
        page.goto(url + "/#resumen")
        translated(page)
        settle(page, 2500)
        for name, view, tab in (("resumen", "resumen", "gen"), ("sueno-noche", "sueno", "hoy")):
            go(page, view, tab)
            save_webp(page.screenshot(), out / f"{name}{suffix}{SFX}.webp", 1170)
            print("  ", name + suffix)
        page.context.close()
    page = new_page(browser, state, DESKTOP)
    page.goto(url + "/#resumen")
    translated(page)
    settle(page, 2500)
    for name, view, tab in (("desktop-resumen", "resumen", "gen"), ("desktop-peso", "peso", "evo")):
        go(page, view, tab, 1800)
        save_webp(page.screenshot(), out / f"{name}{SFX}.webp", 1600)
        print("  ", name)
    page.context.close()


# ---------- videos ----------
# Each video is recorded first; its poster (the first frame) is then taken apart (screenshots spoil a recording).

def tour_resumen(page: Page, still) -> None:
    still()
    for _ in range(5):
        scroll(page, 260, 1000)
        still()


def tour_peso(page: Page, still) -> None:
    still()
    scroll(page, 520, 1200)
    still()
    for tab in ("sem", "cal"):
        go(page, "peso", tab, 1200)
        still()
    scroll(page, 480, 1200)
    still()
    go(page, "peso", "evo", 1200)
    still()


def tour_sueno(page: Page, still) -> None:
    still()
    scroll(page, 380, 1100)
    still()
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(700)
    page.click("svg.dial")
    page.wait_for_timeout(1300)
    still()
    for _ in range(3):
        page.click(f'#sheet .shnav button[aria-label="{TXT["prev"]}"]')
        page.wait_for_timeout(1100)
        still()


def tour_actividad(page: Page, still) -> None:
    still()
    go(page, "actividad", "evo", 1300)
    still()
    for _ in range(4):
        scroll(page, 300, 1100)
        still()


def tour_cuerpo(page: Page, still) -> None:   # Body → Scale (body fat panel and charts), then Measurements
    still()
    scroll(page, 330, 850)
    still()
    scroll(page, 520, 900)
    still()
    scroll(page, 560, 900)
    still()
    top(page)
    tap(page, 'nav.cuetabs a[href="#medidas"]', 1050)
    still()
    scroll(page, 420, 900)
    still()


def tour_corazon(page: Page, still) -> None:   # Body → Heart: the coloured tiles, one enlarged, the evolution charts
    still()
    tap(page, '[data-sheet="kpi"][data-k^="hk|rhr|"]', 1200)
    still()
    close_sheet(page)
    scroll(page, 380, 900)
    still()
    scroll(page, 560, 900)
    still()
    scroll(page, 560, 900)
    still()
    scroll(page, 560, 900)
    still()


def tour_sueno_saldo(page: Page, still) -> None:   # Sleep → Balance, then Schedule
    still()
    scroll(page, 420, 900)
    still()
    scroll(page, 520, 900)
    still()
    tab(page, "sueno", "hor", 1050)
    still()
    scroll(page, 380, 900)
    still()
    scroll(page, 420, 900)
    still()


def tour_comidas(page: Page, still) -> None:   # Meals → Today: another day and its scores, then Analysis
    still()
    tap(page, '#v-comidas button.fwd:has-text("18")', 1050)
    still()
    scroll(page, 420, 900)
    still()
    scroll(page, 480, 900)
    still()
    tab(page, "comidas", "ana", 1050)
    still()
    scroll(page, 380, 900)
    still()


def tour_intimo(page: Page, still) -> None:   # Intimate → Mood: the figures and charts
    still()
    for dy in (600, 650, 700, 700, 700):
        scroll(page, dy, 900)
        still()


def tour_historial(page: Page, still) -> None:   # History → Years, All, Attempts (swiping between them)
    still()
    swipe(page, y=600, ms=1200)
    still()
    tap(page, f'#v-historial button.lg:has-text("{TXT["daily"]}")', 850)
    still()
    tap(page, f'#v-historial button.lg:has-text("{TXT["daily"]}")', 850)
    still()
    swipe(page, y=600, ms=1200)
    still()
    scroll(page, 200, 850)
    still()


def tour_actividad_entrenos(page: Page, still) -> None:   # Activity → Workouts, then Analysis (swipe)
    still()
    scroll(page, 420, 900)
    still()
    scroll(page, 520, 900)
    still()
    top(page)
    swipe(page, y=640, ms=1150)
    still()
    scroll(page, 420, 900)
    still()
    scroll(page, 520, 900)
    still()


def tour_resumen_salud(page: Page, still) -> None:   # Summary → Body, Day to day and Health; one card enlarged
    still()
    scroll(page, 330, 850)
    still()
    top(page)
    swipe(page, y=640, ms=1050)
    still()
    swipe(page, y=640, ms=1050)
    still()
    tap(page, '[data-sheet="kpi"][data-k^="hk|hrv|"]', 1200)
    still()
    close_sheet(page)
    scroll(page, 300, 850)
    still()


VIDEOS = [("video-resumen", "resumen", "gen", tour_resumen), ("video-peso", "peso", "evo", tour_peso),
          ("video-sueno", "sueno", "hoy", tour_sueno), ("video-actividad", "actividad", "hoy", tour_actividad),
          ("video-cuerpo", "composicion", None, tour_cuerpo), ("video-corazon", "corazon", None, tour_corazon),
          ("video-sueno-saldo", "sueno", "banco", tour_sueno_saldo), ("video-comidas", "comidas", "hoy", tour_comidas),
          ("video-intimo", "intimo", "animo", tour_intimo), ("video-historial", "historial", "anios", tour_historial),
          ("video-actividad-entrenos", "actividad", "wo", tour_actividad_entrenos),
          ("video-resumen-salud", "resumen", "cue", tour_resumen_salud)]


def open_view(browser, url: str, state: Path, view: str, tab: str | None, video_dir: str | None = None) -> Page:
    page = new_page(browser, state, PHONE, video_dir=video_dir)
    page.goto(url + "/#" + view)
    translated(page)
    settle(page, 2000)
    go(page, view, tab, 1000)
    return page


def encode(raw: Path, mp4: Path, start: float, length: float) -> None:
    """Trims the loading part and writes the MP4 (H.264, no audio, ready to stream)."""
    ff = shutil.which("ffmpeg") or sys.exit("ffmpeg is needed to encode the videos.")
    cut = ["-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(raw), "-an", "-vf", "fps=30,crop=390:844:0:0,scale=780:1688:flags=lanczos"]   # the page sits in the top-left 390x844 of the recording
    subprocess.run([ff, "-y", "-loglevel", "error", *cut, "-c:v", "libx264", "-preset", "slow", "-crf", "27",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=True)


def videos(browser, url: str, state: Path, out: Path) -> None:
    for name, view, tab, tour in VIDEOS:
        # the video: the page loads off camera (trimmed), then the tour
        tmp = tempfile.mkdtemp(prefix="bl-video-")
        t0 = time.monotonic()
        page = open_view(browser, url, state, view, tab, tmp)
        start = time.monotonic() - t0
        tour(page, lambda: page.wait_for_timeout(120))
        page.wait_for_timeout(500)
        length = time.monotonic() - t0 - start
        video = page.video
        page.context.close()
        encode(Path(video.path()), out / f"{name}{SFX}.mp4", start, length)
        shutil.rmtree(tmp, ignore_errors=True)
        # the poster: the first frame of the tour, without recording
        page = open_view(browser, url, state, view, tab)
        page.wait_for_timeout(250)
        save_webp(page.screenshot(), out / f"{name}{SFX}-1.webp", 1170, 78)
        page.context.close()
        print(f"   {name}{SFX}: {length:.1f} s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default="http://localhost:8765")
    ap.add_argument("--out", default=str(ROOT / "src" / "frontend" / "landing" / "media"))
    ap.add_argument("--only", choices=["shots", "videos"])
    ap.add_argument("--lang", choices=sorted(LOCALES), default="es", help="language of the app (default es)")
    a = ap.parse_args()
    global SFX, TXT
    SFX, TXT = ("" if a.lang == "es" else "-" + a.lang), TEXTS[a.lang]
    COMMON["locale"] = LOCALES[a.lang]
    password = os.environ.get("DEMO_PASSWORD") or sys.exit("Set DEMO_PASSWORD (printed by tools/demo_data.py).")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        browser = p.chromium.launch(args=[f"--lang={LOCALES[a.lang]}"])
        state = Path(tmp) / "state.json"
        url = a.url.rstrip("/")
        login(browser, url, password, state, a.lang)
        try:
            if a.only != "videos":
                print("Screenshots:")
                screenshots(browser, url, state, out)
            if a.only != "shots":
                print("Videos:")
                videos(browser, url, state, out)
        finally:
            if a.lang != "es":   # the demo account goes back to Spanish
                page = new_page(browser, state, PHONE)
                set_lang(page, url, "es")
                page.context.close()
        browser.close()
    total = sum(f.stat().st_size for f in out.iterdir() if f.is_file())
    print(f"{out}: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
