"""Rutas de páginas y ficheros estáticos: la app, las páginas de cuentas, la capa de compatibilidad, librerías e iconos."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response

from app.core import config, i18n
from app.core.deps import optional_user
from app.web import page

router = APIRouter()

VENDOR = {"xlsx.full.min.js", "html2canvas-pro.min.js", "jspdf.umd.min.js"}
BRANDING = {"icon.svg", "wordmark.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"}


def i18n_tags(lang: str) -> str:
    """Los scripts del idioma (diccionario y traductor), en la cabecera para que nada se vea antes en español."""
    from app.core import version
    v = version.current()["build"]
    d = i18n.stamp(lang)   # dictionary version in the URL: the browser fetches it again when it changes
    return f'<script src="/i18n/{lang}.js?v={v}-{d}"></script><script src="/i18n.js?v={v}"></script>'


def display_css(user) -> str:
    """Text size of the account (CSS zoom of the whole page); phones get half the increase so nothing overflows.
    Embedded pages (Your account, Administration, Help) cancel the zoom of their frame and apply it inside, so their
    content is laid out at the real width of the frame."""
    from app.accounts.users import FONT_SIZES, THEMES
    out = ""
    theme = getattr(user, "theme", None) or "auto"
    if theme in THEMES and theme != "auto":   # colour theme: its variables and the attribute that selects them
        css = config.settings.frontend_dir.joinpath("common", "themes.css").read_text(encoding="utf-8")
        out += f"<style>{css}</style><script>document.documentElement.setAttribute('data-theme','{theme}')</script>"
    z = FONT_SIZES.get(getattr(user, "font_size", None) or "md", FONT_SIZES["md"])
    if z == 1:
        return out
    zp = round(1 + (z - 1) / 2, 3)
    rule = lambda k: f"html{{zoom:{k}}}.srvframe{{zoom:{round(1 / k, 5)}}}"   # noqa: E731
    return out + f"<style>{rule(z)}@media (max-width:700px){{{rule(zp)}}}</style>"


def _page(*parts: str, request: Request | None = None, lang: str | None = None) -> HTMLResponse:
    """Página del servidor con sus estilos y scripts marcados con la versión (el navegador no usa copias viejas)
    y con el idioma de quien la ve."""
    from app.core import version
    v = version.current()["build"]
    html = config.settings.frontend_dir.joinpath(*parts).read_text(encoding="utf-8")
    html = html.replace('href="/pages.css"', f'href="/pages.css?v={v}"').replace('src="/pages.js"', f'src="/pages.js?v={v}"')
    u = optional_user(request) if request is not None else None
    lang = lang or (i18n.request_lang(request, u) if request is not None else i18n.DEFAULT)
    css = display_css(u)
    html = html.replace("<meta charset=\"utf-8\">", "<meta charset=\"utf-8\">" + i18n_tags(lang) + css
                        + f'<script src="/native.js?v={v}"></script>', 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@router.get("/i18n.js")
def i18n_runtime():
    return _front("i18n", "i18n.js", media_type="text/javascript")


@router.get("/i18n/{name}.js")
def i18n_dictionary(name: str):
    lang = i18n.clean(name)
    if not lang:
        raise HTTPException(404)
    # la URL lleva la versión (?v=): puede guardarse en caché
    return Response(i18n.script(lang), media_type="text/javascript",
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})


def _front(*parts: str, **kw) -> FileResponse:
    # las páginas y sus estilos cambian con cada despliegue: el navegador las revalida siempre (ETag → 304 si no cambian)
    kw.setdefault("headers", {"Cache-Control": "no-cache"})
    return FileResponse(config.settings.frontend_dir.joinpath(*parts), **kw)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    u = optional_user(request)
    if not u:
        # visitors see the landing page; the Android app goes straight to signing in
        if "BodyLensApp/" in request.headers.get("user-agent", ""):
            return RedirectResponse("/login", status_code=303)
        return landing(request)
    if u.must_change:
        return RedirectResponse("/cuenta?cambiar=1", status_code=303)
    from app.billing.routes import expired
    if expired(u.id):   # the Google Play subscription is over: the renewal page
        return RedirectResponse("/alta", status_code=303)
    return HTMLResponse(page.page(u.public(), i18n_tags(u.lang) + display_css(u)), headers={"Cache-Control": "no-store"})


LANDING_LANGS = ("en", "es")


def landing(request: Request) -> HTMLResponse:
    """The landing page in English or Spanish: the one chosen with its EN | ES switch (remembered in the language
    cookie), else the one of the visitor's browser (Spanish for Spanish and the languages of Spain, English otherwise)."""
    asked = request.query_params.get("lang")
    lang = asked if asked in LANDING_LANGS else None
    if not lang:
        c = request.cookies.get(i18n.COOKIE)
        lang = c if c in LANDING_LANGS else None
    if not lang:
        first = (request.headers.get("accept-language", "").split(",")[0].strip().lower()[:2])
        lang = "es" if first in ("es", "ca", "gl", "eu") else "en"
    r = _page("landing", "index.html", request=request, lang=lang)
    r.body = r.body.replace(b'<html lang="es">', f'<html lang="{lang}">'.encode(), 1)
    r.headers["content-length"] = str(len(r.body))
    r.headers["vary"] = "accept-language,cookie"
    if lang == "en":   # the description for search engines (the page's texts are translated in the browser)
        import re
        m = re.search(rb'<meta name="description-en" content="([^"]*)">', r.body)
        if m:
            r.body = re.sub(rb'<meta name="description" content="[^"]*">', b'<meta name="description" content="' + m.group(1) + b'">', r.body, count=1)
            r.headers["content-length"] = str(len(r.body))
    if asked in LANDING_LANGS:
        r.set_cookie(i18n.COOKIE, lang, max_age=5 * 365 * 86400, samesite="lax")
    return r


def android_apk_path():
    return config.settings.data_dir / "downloads" / "bodylens-android.apk"


@router.get("/android.apk")
def android_apk(request: Request):
    """The Android app, for anyone (the landing page links it): tools/deploy-android.sh leaves it there."""
    p = android_apk_path()
    if not p.exists():
        raise HTTPException(404, "La app de Android todavía no está disponible en este servidor.")
    return FileResponse(p, media_type="application/vnd.android.package-archive", filename="BodyLens.apk",
                        headers={"Cache-Control": "no-cache"})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return _page("accounts", "login.html", request=request)


@router.get("/solicitar")
def request_page():
    """Accounts are no longer requested: they are made with a subscription or an invitation code (/alta)."""
    return RedirectResponse("/alta", status_code=303)


@router.get("/registro", response_class=HTMLResponse)
def register_page(request: Request):
    return _page("accounts", "registro.html", request=request)


@router.get("/cuenta", response_class=HTMLResponse)
def account_page(request: Request):
    if not optional_user(request):
        return RedirectResponse("/login?next=/cuenta", status_code=303)
    return _page("accounts", "cuenta.html", request=request)


@router.get("/alta", response_class=HTMLResponse)
def subscribe_page(request: Request):
    """New account with a Google Play subscription (in the Android app), or renewing one that is over."""
    return _page("accounts", "alta.html", request=request)


@router.get("/bienvenida", response_class=HTMLResponse)
def welcome_page(request: Request):
    """Back from Stripe's checkout page."""
    return _page("accounts", "bienvenida.html", request=request)


@router.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    """Public: the help can be read without signing in."""
    return _page("help", "help.html", request=request)


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    u = optional_user(request)
    if not u:
        return RedirectResponse("/login?next=/admin", status_code=303)
    if not u.is_admin:
        return RedirectResponse("/cuenta", status_code=303)
    return _page("admin", "admin.html", request=request)


@router.get("/claude-shim.js")
def shim():
    return _front("compat", "claude-shim.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


@router.get("/pages.css")
def pages_css():
    return _front("common", "pages.css", media_type="text/css", headers={"Cache-Control": "no-cache"})


@router.get("/pages.js")
def pages_js():
    return _front("common", "pages.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


@router.get("/landing/media/{name}")
def landing_media(name: str):
    """Screenshots and videos of the landing page (demo account, synthetic data)."""
    import re
    if not re.fullmatch(r"[a-z0-9-]+\.(webp|png|jpg|mp4|webm)", name):
        raise HTTPException(404)
    p = config.settings.frontend_dir / "landing" / "media" / name
    if not p.is_file():
        raise HTTPException(404)
    return FileResponse(p, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/native.js")
def native_js():
    return _front("common", "native.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


@router.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(page.MANIFEST, media_type="application/manifest+json")


@router.get("/vendor/{name}")
def vendor(name: str):
    if name not in VENDOR or not (config.settings.vendor_dir / name).exists():
        raise HTTPException(404)
    return FileResponse(config.settings.vendor_dir / name, media_type="text/javascript",
                        headers={"Cache-Control": "public, max-age=604800"})


@router.get("/{name}")
def branding(name: str):
    if name not in BRANDING:
        raise HTTPException(404)
    return FileResponse(config.settings.branding_dir / name, headers={"Cache-Control": "public, max-age=86400"})
