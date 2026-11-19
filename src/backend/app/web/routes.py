"""Rutas de páginas y ficheros estáticos: la app, las páginas de cuentas, la capa de compatibilidad, librerías e iconos."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from app.core import config
from app.core.deps import optional_user
from app.web import page

router = APIRouter()

VENDOR = {"xlsx.full.min.js", "html2canvas-pro.min.js", "jspdf.umd.min.js"}
BRANDING = {"icon.svg", "wordmark.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"}


def _page(*parts: str) -> HTMLResponse:
    """Página del servidor con sus estilos y scripts marcados con la versión (el navegador no usa copias viejas)."""
    from app.core import version
    v = version.current()["build"]
    html = config.settings.frontend_dir.joinpath(*parts).read_text(encoding="utf-8")
    html = html.replace('href="/pages.css"', f'href="/pages.css?v={v}"').replace('src="/pages.js"', f'src="/pages.js?v={v}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


def _front(*parts: str, **kw) -> FileResponse:
    # las páginas y sus estilos cambian con cada despliegue: el navegador las revalida siempre (ETag → 304 si no cambian)
    kw.setdefault("headers", {"Cache-Control": "no-cache"})
    return FileResponse(config.settings.frontend_dir.joinpath(*parts), **kw)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    u = optional_user(request)
    if not u:
        return RedirectResponse("/login", status_code=303)
    if u.must_change:
        return RedirectResponse("/cuenta?cambiar=1", status_code=303)
    return HTMLResponse(page.page(u.public()), headers={"Cache-Control": "no-store"})


@router.get("/login", response_class=HTMLResponse)
def login_page():
    return _page("accounts", "login.html")


@router.get("/solicitar", response_class=HTMLResponse)
def request_page():
    return _page("accounts", "solicitar.html")


@router.get("/registro", response_class=HTMLResponse)
def register_page():
    return _page("accounts", "registro.html")


@router.get("/cuenta", response_class=HTMLResponse)
def account_page(request: Request):
    if not optional_user(request):
        return RedirectResponse("/login?next=/cuenta", status_code=303)
    return _page("accounts", "cuenta.html")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    u = optional_user(request)
    if not u:
        return RedirectResponse("/login?next=/admin", status_code=303)
    if not u.is_admin:
        return RedirectResponse("/cuenta", status_code=303)
    return _page("admin", "admin.html")


@router.get("/claude-shim.js")
def shim():
    return _front("compat", "claude-shim.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


@router.get("/pages.css")
def pages_css():
    return _front("common", "pages.css", media_type="text/css", headers={"Cache-Control": "no-cache"})


@router.get("/pages.js")
def pages_js():
    return _front("common", "pages.js", media_type="text/javascript", headers={"Cache-Control": "no-cache"})


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
