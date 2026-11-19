"""Monta la página de la app a partir de src/frontend/app (a + b + c) con los cambios mínimos para el servidor.

Los ficheros de src/frontend/app no se tocan: siguen sirviendo para el artefacto. Aquí se aplican sustituciones
exactas (cada una debe aparecer una sola vez; si el código cambia, la prueba lo detecta) y se añade la capa
de compatibilidad con window.claude.
"""
from __future__ import annotations

import html
import json
import threading
from pathlib import Path

from app.core import config, version

APPS_SCRIPT_EXEC = "https://script.google.com/macros/s/AKfycbyq4X7M4IRxqFM7ez4BYQ9SelLUPo1Wauc9zm4YgCfD8wubBL-rVKe5rytquF4D-7Ac/exec"
LEGACY_SHEET = "1aUMgruI3VycOCjbqH4_UvL8nS8i-mt1QFNiz6xaQx2Q"

# (buscar, sustituir por) — cambios mínimos para funcionar fuera de claude.ai
REPLACEMENTS: list[tuple] = [
    # librerías servidas por el propio servidor (sin CDN)
    ('<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>',
     '<script src="/vendor/xlsx.full.min.js"></script>'),
    ("h2c:'https://cdn.jsdelivr.net/npm/html2canvas-pro@1.5.8/dist/html2canvas-pro.min.js'",
     "h2c:'/vendor/html2canvas-pro.min.js'"),
    ("pdf:'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'",
     "pdf:'/vendor/jspdf.umd.min.js'"),
    # botón «Actualizar»: sincroniza en el servidor en vez de abrir el Apps Script
    (f'id="pullBtn" href="{APPS_SCRIPT_EXEC}?accion=sincronizar" target="_blank" rel="noopener"',
     'id="pullBtn" href="#"'),
    ("$('pullBtn').addEventListener('click',()=>{pullAt=Date.now();",
     "$('pullBtn').addEventListener('click',e=>{if(window.BODYLENS_SERVER){e.preventDefault();BL.pull();return}pullAt=Date.now();"),
    ("const WITHINGS_NOW='" + APPS_SCRIPT_EXEC + "?accion=sincronizar';", "const WITHINGS_NOW='#';"),
    # cada cuenta empieza con su propio perfil; la hoja de Google la configura el servidor
    ("const PROF_DEF=", "const PROF_DEF=window.BODYLENS_SERVER?BL.profDef():"),
    (f"fileId:'{LEGACY_SHEET}'}};", "fileId:null};"),
    ('<p class="src" id="railSrc">Datos de tu báscula Withings, guardados en tu cuenta de Claude.</p>',
     '<p class="src" id="railSrc">Datos de tu báscula Withings y de Apple Salud, guardados en tu cuenta de BodyLens.</p>'),
    # menú de perfiles: acceso a la cuenta
    ('<a class="owner-only" href="#ajustes">Ajustes</a>',
     '<a class="owner-only" href="#ajustes">Ajustes</a><a href="#cuenta">Tu cuenta</a><a href="#admin" class="bl-admin">Administración</a>'),
    # textos que hablaban de claude.ai y de la hoja
    ("<p class=\"lead\">La app lee la pestaña «Withings» de tu hoja «Peso Jaime 2026», que el script de la hoja actualiza desde Withings cada 6 horas, o al momento con el botón de la nube de arriba.</p>",
     "<p class=\"lead\">Los datos de la báscula y de Apple Salud llegan solos al servidor cada pocos minutos; con el botón de la nube de arriba se piden al momento. Las fuentes se ven en <a href=\"#cuenta\">Tu cuenta</a>.</p>"),
    ("<p class=\"foot\">Tus datos se guardan en el espacio de datos de esta app en Claude y están disponibles en el iPhone y en el Mac. Quien abra el enlace con sesión iniciada en claude.ai los ve al momento; sin sesión, ve la copia que lleva la página. Solo tú puedes cambiarlos o sincronizarlos.</p>",
     "<p class=\"foot\">Tus datos se guardan en tu cuenta de este servidor y solo los ves tú (lo de Ciclo e intimidad, también tu pareja si habéis unido las cuentas).</p>"),
    # mensajes de descarga (aparecen dos veces)
    ("'Esta vista no permite descargar archivos. Abre la app en claude.ai.'", "'No se pudo preparar la descarga.'", 2),
]

# lo que no tiene sentido en el servidor (copia publicada en la página, ID de la hoja) se oculta
SERVER_CSS = (
    "section.card:has(#pubBtn),label[for=cfFile],#fileSave,#fileMsg{display:none!important}"
)


class AssemblyError(RuntimeError):
    pass


def _src_files() -> list[Path]:
    src = config.settings.frontend_dir / "app"
    return [src / "app_a.html", src / "app_b.html", src / "app_c.html"]


def assemble_fragment() -> str:
    t = "".join(p.read_text(encoding="utf-8") for p in _src_files())
    for old, new, *times in REPLACEMENTS:
        want = times[0] if times else 1
        n = t.count(old)
        if n != want:
            raise AssemblyError(f"Sustitución esperada {want} vez/veces y aparece {n}: {old[:80]!r}")
        t = t.replace(old, new)
    return t


_cache: dict = {"key": None, "fragment": None}
_lock = threading.Lock()


def fragment() -> str:
    """Página montada; se rehace si cambia algún fichero (recarga en desarrollo)."""
    key = tuple((p, p.stat().st_mtime_ns) for p in _src_files())
    with _lock:
        if _cache["key"] != key:
            _cache["fragment"] = assemble_fragment()
            _cache["key"] = key
        return _cache["fragment"]


def page(user_public: dict, lang_tags: str = "") -> str:
    boot = json.dumps(user_public, ensure_ascii=False).replace("</", "<\\/")
    admin_css = "" if user_public.get("isAdmin") else ".bl-admin{display:none!important}"
    head = (
        f'<!doctype html><html lang="{user_public.get("lang", "es")}"><head><meta charset="utf-8">{lang_tags}'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#3B7BF2">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="BodyLens">'
        '<link rel="manifest" href="/manifest.webmanifest">'
        '<link rel="icon" type="image/svg+xml" href="/icon.svg">'
        '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
        f"<style>{SERVER_CSS}{admin_css}</style>"
        f"<script>window.BODYLENS_SERVER=true;window.BODYLENS_USER={boot};"
        f"window.BODYLENS_BUILD={json.dumps(version.current()['build'])};</script>"
        '<script src="/claude-shim.js"></script>'
        "</head><body>"
    )
    return head + fragment() + "</body></html>"


MANIFEST = {
    "name": "BodyLens",
    "short_name": "BodyLens",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#eef1f5",
    "theme_color": "#3B7BF2",
    "lang": "es-ES",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
}


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)
