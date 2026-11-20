#!/usr/bin/env python3
"""Screenshots and short videos of the app for the marketing landing page, taken with the demo account.

    DATA_DIR=<demo dir> .venv/bin/python tools/demo_data.py          # demo account (prints its password)
    (start a server on that DATA_DIR, e.g. on port 8765)
    DEMO_PASSWORD=... .venv/bin/python tools/landing_capture.py [--url http://localhost:8765] [--out DIR] [--lang en|es]

Needs Playwright and Pillow (`pip install playwright pillow && python -m playwright install chromium`; they are not
project dependencies) and ffmpeg, to trim and encode the videos. Everything goes to src/frontend/landing/media/:
screenshots as WebP, videos as MP4 (H.264) and the first frame of each video (<video>-1.webp) as its poster.
Phone videos are 780x1688; desktop ones (video-desk-*, wide layout) 1440x900. --only desktop takes just the desktop
screenshots and videos. --tabs records instead one phone video per tab of each module of the app (read from the page:
tab-<module>-<tab>.mp4 and its poster tab-<module>-<tab>.webp, scrolling the whole tab) and writes manifest.json, the
list of modules, tabs and desktop media the landing page shows (run it for es and en: each run adds its names).
video-temas and video-desk-temas show the Summary going through every colour theme (switched in
the page, without saving the setting of the account).
--lang en switches the demo account to English for the capture (and back to Spanish at the end) and names every file
with the suffix -en (resumen-en.webp, video-sueno-en.mp4, video-sueno-en-1.webp); Spanish files have no suffix.
The browser clock is set to 20:35 of today (Madrid), the time the demo data stops (tools/demo_data.py).
"""
from __future__ import annotations

import argparse
import io
import json
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
DESKTOP_REC = {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 1}   # recorded at CSS size: 1x fills it
COMMON = {"locale": "es-ES", "timezone_id": "Europe/Madrid"}
LOCALES = {"es": "es-ES", "en": "en-GB"}
SFX = ""   # file name suffix of the language ("-en"; none for Spanish)
# texts the tours look for, in each language (the page translates them in the browser)
TEXTS = {"es": {"prev": "Anterior", "daily": "Pesada diaria"}, "en": {"prev": "Previous", "daily": "Daily weigh-in"}}
TXT = TEXTS["es"]
VIDEO_SIZE = {"width": 780, "height": 1688}
DESK_VIDEO_SIZE = {"width": 1440, "height": 900}
PHONE_VF = "fps=30,crop=390:844:0:0,scale=780:1688:flags=lanczos"   # the page sits in the top-left 390x844 of the recording
DESK_VF = "fps=24,crop=1440:900:0:0"

# (file name, view, tab or None): phone screenshots, the top of the screen as a user sees it
# phone screenshots the landing page still uses (the hero's back phones); the modules show a video per tab (--tabs)
SHOTS = [("actividad-evolucion", "actividad", "evo"), ("sueno-noche", "sueno", "hoy")]


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


def new_page(browser, state: Path, profile: dict, scheme: str = "light", video_dir: str | None = None,
             video_size: dict = VIDEO_SIZE) -> Page:
    extra = {"record_video_dir": video_dir, "record_video_size": video_size} if video_dir else {}
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
    page.context.close()
    desktop_shots(browser, url, state, out)


def desktop_shots(browser, url: str, state: Path, out: Path) -> None:
    page = new_page(browser, state, DESKTOP)
    page.goto(url + "/#resumen")
    translated(page)
    settle(page, 2500)
    for name, view, tab in (("desktop-resumen", "resumen", "gen"), ("desktop-peso", "peso", "evo"),
                            ("desktop-sueno", "sueno", "hoy"), ("desktop-actividad", "actividad", "evo"),
                            ("desktop-cuerpo", "composicion", None)):
        go(page, view, tab, 1800)
        save_webp(page.screenshot(), out / f"{name}{SFX}.webp", 1600)
        print("  ", name)
    go(page, "resumen", "gen", 1500)   # the export to PDF dialog, over the Summary
    page.click("#pdfBtn")
    page.wait_for_timeout(1200)
    save_webp(page.screenshot(), out / f"desktop-pdf{SFX}.webp", 1600)
    print("   desktop-pdf")
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


# ---------- desktop tours (wide layout, with the mouse) ----------

def glide(page: Page, dy: int, ms: int = 1100) -> None:
    """A slow smooth scroll (the wheel of a desktop mouse, eased)."""
    page.evaluate("""dy => new Promise(done => { const y0 = scrollY, t0 = performance.now(), T = 900;
        const step = t => { const f = Math.min(1, (t - t0) / T), e = f < .5 ? 2 * f * f : 1 - (-2 * f + 2) ** 2 / 2;
                            scrollTo(0, y0 + dy * e); f < 1 ? requestAnimationFrame(step) : done() };
        requestAnimationFrame(step) })""", dy)
    page.wait_for_timeout(max(0, ms - 900))


def click(page: Page, selector: str, ms: int = 1100) -> None:
    """A mouse click on the first visible match: the pointer travels there first."""
    el = page.locator(selector).locator("visible=true").first
    el.scroll_into_view_if_needed()
    b = el.bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=12)
    page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(ms)


def dtour_resumen(page: Page, still) -> None:   # Summary → General, wide layout, scrolling down and up
    page.mouse.move(900, 500)
    still(1300)
    glide(page, 260, 1900)
    glide(page, 260, 2200)
    glide(page, -520, 1900)


def dtour_peso(page: Page, still) -> None:   # Weight → Evolution: a point of the chart with its tooltip; Weeks, Calendar
    still(700)
    chart = page.locator("#chMain svg").first
    box = chart.bounding_box()
    glide(page, round(box["y"] - 260), 1100)
    box = chart.bounding_box()
    y = box["y"] + box["height"] * .45
    page.mouse.move(box["x"] + box["width"] * .55, y, steps=10)
    for f in (.62, .7, .78, .84):
        page.mouse.move(box["x"] + box["width"] * f, y, steps=14)
        page.wait_for_timeout(350)
    page.wait_for_timeout(700)
    glide(page, -page.evaluate("scrollY"), 1000)
    click(page, 'nav.vtabs[data-view="peso"] a[data-tab="sem"]', 1500)
    click(page, 'nav.vtabs[data-view="peso"] a[data-tab="cal"]', 1400)


def dtour_sueno(page: Page, still) -> None:   # Sleep → Night: the big clock, changing night with the side arrows
    still(1000)
    click(page, '#v-sueno [data-sheet="dial"]', 1600)
    for _ in range(3):
        click(page, '.shside[data-side="0"]', 1300)
    click(page, '.shside[data-side="1"]', 1300)


def dtour_actividad(page: Page, still) -> None:   # Activity → Evolution (coloured tiles, steps chart), then Analysis
    page.mouse.move(900, 500)
    still(1100)
    glide(page, 330, 1600)
    glide(page, -330, 900)
    click(page, 'nav.vtabs[data-view="actividad"] a[data-tab="ana"]', 1700)
    glide(page, 360, 1600)


def theme_frame(page: Page):
    page.wait_for_function("""() => { const f = document.getElementById('emb-cuenta');
                                       const s = f && f.contentDocument && f.contentDocument.getElementById('ftheme');
                                       return s && s.options.length && f.contentDocument.getElementById('kName').textContent }""", timeout=20000)
    return page.frame_locator("#emb-cuenta")


def dtour_ajustes(page: Page, still) -> None:   # Your account: a couple of colour themes, then back to the default
    fr = theme_frame(page)
    still(900)
    for theme in ("ocean", "sunset", "auto"):
        fr.locator("#ftheme").scroll_into_view_if_needed()
        b = fr.locator("#ftheme").bounding_box()
        page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=12)
        page.wait_for_timeout(300)
        with page.expect_navigation(timeout=20000):
            fr.locator("#ftheme").select_option(theme)
        translated(page)
        fr = theme_frame(page)
        page.wait_for_timeout(1700)


# every colour theme of Your account, in its order; the videos switch them in the page (no reload, nothing saved)
THEMES = ["light", "dark", "sepia", "ocean", "forest", "contrast", "rose", "lavender", "mint", "sunset", "graphite"]


def prep_temas(page: Page, desk: bool) -> None:
    """The themes (the server only inlines them when the account uses one), the first one on and the Summary scrolled so
    the hero card and the charts below it are in view."""
    page.add_style_tag(content=(ROOT / "src" / "frontend" / "common" / "themes.css").read_text(encoding="utf-8"))
    page.evaluate("t => { const h = document.documentElement; h.dataset.themeWas = h.getAttribute('data-theme') || '';"
                  " h.setAttribute('data-theme', t) }", THEMES[0])
    page.evaluate("dy => window.scrollTo(0, dy)", 0 if desk else 60)
    page.wait_for_timeout(600)


def set_theme(page: Page, theme: str) -> None:
    page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)


def restore_theme(page: Page) -> None:
    page.evaluate("() => { const h = document.documentElement, t = h.dataset.themeWas; delete h.dataset.themeWas;"
                  " if (t) h.setAttribute('data-theme', t); else h.removeAttribute('data-theme') }")


def tour_temas(page: Page, still) -> None:   # Summary → General through every theme, with a slow scroll halfway
    still()
    for i, theme in enumerate(THEMES[1:]):
        set_theme(page, theme)
        if i in (3, 7):
            scroll(page, 170, 1300)
        else:
            page.wait_for_timeout(1300)
    page.wait_for_timeout(200)
    restore_theme(page)


def dtour_temas(page: Page, still) -> None:   # the same on the desktop layout
    page.mouse.move(900, 500)
    still(1300)
    for theme in THEMES[1:]:
        set_theme(page, theme)
        page.wait_for_timeout(1300)
    page.wait_for_timeout(200)
    restore_theme(page)


DESK_VIDEOS = [("video-desk-resumen", "resumen", "gen", dtour_resumen), ("video-desk-peso", "peso", "evo", dtour_peso),
               ("video-desk-sueno", "sueno", "hoy", dtour_sueno), ("video-desk-actividad", "actividad", "evo", dtour_actividad),
               ("video-desk-ajustes", "cuenta", None, dtour_ajustes), ("video-desk-temas", "resumen", "gen", dtour_temas)]

VIDEOS = [("video-resumen", "resumen", "gen", tour_resumen), ("video-peso", "peso", "evo", tour_peso),
          ("video-sueno", "sueno", "hoy", tour_sueno), ("video-actividad", "actividad", "hoy", tour_actividad),
          ("video-cuerpo", "composicion", None, tour_cuerpo), ("video-corazon", "corazon", None, tour_corazon),
          ("video-sueno-saldo", "sueno", "banco", tour_sueno_saldo), ("video-comidas", "comidas", "hoy", tour_comidas),
          ("video-intimo", "intimo", "animo", tour_intimo), ("video-historial", "historial", "anios", tour_historial),
          ("video-actividad-entrenos", "actividad", "wo", tour_actividad_entrenos),
          ("video-resumen-salud", "resumen", "cue", tour_resumen_salud), ("video-temas", "resumen", "gen", tour_temas)]
PREP = {"video-temas": prep_temas, "video-desk-temas": prep_temas}   # done off camera (trimmed) and for the poster


def open_view(browser, url: str, state: Path, view: str, tab: str | None, video_dir: str | None = None,
              desk: bool = False, prep=None) -> Page:
    page = new_page(browser, state, DESKTOP_REC if desk and video_dir else DESKTOP if desk else PHONE,
                    video_dir=video_dir, video_size=DESK_VIDEO_SIZE if desk else VIDEO_SIZE)
    page.goto(url + "/#" + view)
    translated(page)
    settle(page, 2000)
    go(page, view, tab, 1000)
    if prep:
        prep(page, desk)
    return page


def encode(raw: Path, mp4: Path, start: float, length: float, vf: str = PHONE_VF, crf: int = 27) -> None:
    """Trims the loading part and writes the MP4 (H.264, no audio, ready to stream)."""
    ff = shutil.which("ffmpeg") or sys.exit("ffmpeg is needed to encode the videos.")
    cut = ["-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(raw), "-an", "-vf", vf]
    subprocess.run([ff, "-y", "-loglevel", "error", *cut, "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=True)


def debug(page: Page, name: str) -> None:
    """When a tour fails: a screenshot and the page's text in CAPTURE_DEBUG (the landing-media workflow keeps them)."""
    d = os.environ.get("CAPTURE_DEBUG")
    if not d:
        return
    Path(d).mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(Path(d) / f"{name}{SFX}.png"), full_page=True)
        (Path(d) / f"{name}{SFX}.txt").write_text(page.evaluate("document.body.innerText")[:20000], encoding="utf-8")
    except Exception:   # noqa: BLE001
        pass


def videos(browser, url: str, state: Path, out: Path) -> None:
    for name, view, tab, tour in VIDEOS:
        # the video: the page loads off camera (trimmed), then the tour
        tmp = tempfile.mkdtemp(prefix="bl-video-")
        t0 = time.monotonic()
        page = open_view(browser, url, state, view, tab, tmp, prep=PREP.get(name))
        start = time.monotonic() - t0
        try:
            tour(page, lambda: page.wait_for_timeout(120))
        except Exception:
            debug(page, name)
            raise
        page.wait_for_timeout(500)
        length = time.monotonic() - t0 - start
        video = page.video
        page.context.close()
        encode(Path(video.path()), out / f"{name}{SFX}.mp4", start, length)
        shutil.rmtree(tmp, ignore_errors=True)
        # the poster: the first frame of the tour, without recording
        page = open_view(browser, url, state, view, tab, prep=PREP.get(name))
        page.wait_for_timeout(250)
        save_webp(page.screenshot(), out / f"{name}{SFX}-1.webp", 1170, 78)
        page.context.close()
        print(f"   {name}{SFX}: {length:.1f} s")
    desktop_videos(browser, url, state, out)


def desktop_videos(browser, url: str, state: Path, out: Path) -> None:
    theme = new_page(browser, state, DESKTOP).request.get(url + "/api/me").json()["user"].get("theme") or "auto"
    try:
        for name, view, tab, tour in DESK_VIDEOS:
            tmp = tempfile.mkdtemp(prefix="bl-video-")
            t0 = time.monotonic()
            page = open_view(browser, url, state, view, tab, tmp, desk=True, prep=PREP.get(name))
            if view == "cuenta":
                theme_frame(page)
                page.wait_for_timeout(600)
            start = time.monotonic() - t0
            tour(page, lambda ms=120: page.wait_for_timeout(ms))
            page.wait_for_timeout(500)
            length = time.monotonic() - t0 - start
            video = page.video
            page.context.close()
            encode(Path(video.path()), out / f"{name}{SFX}.mp4", start, length, DESK_VF, 26)
            shutil.rmtree(tmp, ignore_errors=True)
            page = open_view(browser, url, state, view, tab, desk=True, prep=PREP.get(name))
            if view == "cuenta":
                theme_frame(page)
            page.wait_for_timeout(600)
            save_webp(page.screenshot(), out / f"{name}{SFX}-1.webp", 1600, 78)
            page.context.close()
            print(f"   {name}{SFX}: {length:.1f} s")
    finally:   # the demo account keeps its own theme
        page = new_page(browser, state, DESKTOP)
        page.request.post(url + "/api/me/theme", data={"theme": theme}, headers={"X-BodyLens": "1"})
        page.context.close()


# ---------- one video per tab of each module (--tabs) and the manifest the landing page reads ----------

TAB_VF = "fps=20,crop=390:844:0:0,scale=480:1038:flags=lanczos"   # smaller than the tours: there are many of them
TAB_PX_S = 380        # scrolling speed (CSS px per second), faster for long tabs so a video stays under ~20 s
TAB_MAX_S = 15      # longest scroll; plus the pauses at the top and at the bottom
# the desktop carousel of the landing page (the desktop videos and screenshots, in this order)
DESKTOP_SLIDES = [("video-desk-resumen", "Resumen", "Summary"), ("desktop-resumen", "Resumen", "Summary"),
                  ("video-desk-peso", "Peso", "Weight"), ("desktop-peso", "Peso", "Weight"),
                  ("video-desk-sueno", "Sueño", "Sleep"), ("desktop-sueno", "Sueño", "Sleep"),
                  ("video-desk-actividad", "Actividad", "Activity"), ("desktop-actividad", "Actividad", "Activity"),
                  ("desktop-cuerpo", "Cuerpo", "Body"), ("video-desk-temas", "Temas", "Themes")]


def app_tabs(page: Page) -> list[dict]:
    """The modules of the app's tab bar and the tabs of each one, read from the page (so new modules or tabs are
    picked up). A module's tabs are its «vtabs» (data-tab) or, for a group of views like Body, the views of its bar
    (its id is then the Spanish title of the view, «cuerpo», which the page does not translate)."""
    return page.evaluate("""() => [...document.querySelectorAll('#tabNav a[href^="#"]')].map(a => {
        const view = a.getAttribute('href').slice(1), v = document.getElementById('v-' + view);
        const nav = v && v.querySelector('nav.cuetabs');
        const id = nav && !nav.dataset.view ? ((v && v.dataset.title) || view).normalize('NFD')
                     .replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '') : view;
        const tabs = nav ? [...nav.querySelectorAll('a[href^="#"]')].map(t => ({
            view: t.getAttribute('href').slice(1), tab: t.dataset.tab || null,
            id: t.dataset.tab || t.getAttribute('href').slice(1), name: t.textContent.trim() })) : [{ view, tab: null, id: view, name: '' }];
        return { id, view, name: v && v.dataset.title ? (window.blT || String)(v.dataset.title) : a.textContent.trim(), tabs };
      })""")


def tour_tab(page: Page) -> None:
    """From the top of the tab to its bottom, smoothly, with a pause at each end."""
    page.wait_for_timeout(1200)
    h = page.evaluate("Math.max(0, document.scrollingElement.scrollHeight - innerHeight)")
    if h > 40:
        ms = round(1000 * min(TAB_MAX_S, max(1.5, h / TAB_PX_S)))
        page.evaluate("""([h, T]) => new Promise(done => { const t0 = performance.now();
            const step = t => { const f = Math.min(1, (t - t0) / T), e = f < .5 ? 2 * f * f : 1 - (-2 * f + 2) ** 2 / 2;
                                scrollTo(0, h * (.15 * f + .85 * e)); f < 1 ? requestAnimationFrame(step) : done() };
            requestAnimationFrame(step) })""", [h, ms])
    page.wait_for_timeout(1300)


def open_tab(browser, url: str, state: Path, mod: dict, t: dict, video_dir: str | None = None) -> Page:
    page = new_page(browser, state, PHONE, video_dir=video_dir)
    page.goto(url + "/#" + t["view"])
    translated(page)
    settle(page, 2000)
    go(page, t["view"], t["tab"] if t["tab"] and page.locator(f'nav.vtabs[data-view="{t["view"]}"] a[data-tab="{t["tab"]}"]').count() else None, 1200)
    return page


def tab_videos(browser, url: str, state: Path, out: Path, lang: str) -> None:
    probe = new_page(browser, state, PHONE)
    probe.goto(url + "/#resumen")
    translated(probe)
    settle(probe, 2500)
    mods = app_tabs(probe)
    probe.context.close()
    man_path = out / "manifest.json"
    try:
        old = json.loads(man_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    names = {m["id"]: m for m in old.get("modules", [])}
    modules = []
    for mod in mods:
        prev = names.get(mod["id"], {})
        ptabs = {t["id"]: t for t in prev.get("tabs", [])}
        tabs = []
        for t in mod["tabs"]:
            file = f"tab-{mod['id']}-{t['id']}"
            tmp = tempfile.mkdtemp(prefix="bl-video-")
            t0 = time.monotonic()
            page = open_tab(browser, url, state, mod, t, tmp)
            start = time.monotonic() - t0
            tour_tab(page)
            length = time.monotonic() - t0 - start
            video = page.video
            page.context.close()
            encode(Path(video.path()), out / f"{file}{SFX}.mp4", start, length, TAB_VF, 32)
            shutil.rmtree(tmp, ignore_errors=True)
            page = open_tab(browser, url, state, mod, t)   # the poster: the top of the tab, as the video starts
            page.wait_for_timeout(300)
            save_webp(page.screenshot(), out / f"{file}{SFX}.webp", 480, 72)
            page.context.close()
            print(f"   {file}{SFX}: {length:.1f} s")
            tabs.append({"id": t["id"], "file": file, "name": {**ptabs.get(t["id"], {}).get("name", {}), lang: t["name"] or mod["name"]}})
        modules.append({"id": mod["id"], "name": {**prev.get("name", {}), lang: mod["name"]}, "tabs": tabs})
    desktop = []
    for file, es, en in DESKTOP_SLIDES:
        kind = "video" if file.startswith("video-") else "image"
        for sfx in ("", "-en"):   # the landing page asks for <file>.webp as a video's poster
            src, dst = out / f"{file}{sfx}-1.webp", out / f"{file}{sfx}.webp"
            if kind == "video" and src.exists() and (not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime):
                shutil.copyfile(src, dst)
        desktop.append({"file": file, "kind": kind, "name": {"es": es, "en": en}})
    man = {"build": datetime.now(TZ).strftime("%Y%m%d%H%M"), "modules": modules, "desktop": desktop}
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"   {man_path.name}: {sum(len(m['tabs']) for m in modules)} tabs in {len(modules)} modules")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default="http://localhost:8765")
    ap.add_argument("--out", default=str(ROOT / "src" / "frontend" / "landing" / "media"))
    ap.add_argument("--only", choices=["shots", "videos", "desktop"])
    ap.add_argument("--tabs", action="store_true", help="only a video per tab of each module, and manifest.json")
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
            if a.tabs:
                print("Tabs:")
                tab_videos(browser, url, state, out, a.lang)
            elif a.only == "desktop":
                print("Desktop:")
                desktop_shots(browser, url, state, out)
                desktop_videos(browser, url, state, out)
            if not a.tabs and a.only in (None, "shots"):
                print("Screenshots:")
                screenshots(browser, url, state, out)
            if not a.tabs and a.only in (None, "videos"):
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
