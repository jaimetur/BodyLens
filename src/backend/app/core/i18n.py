"""Idiomas. La interfaz se escribe en español y se traduce con un diccionario por idioma
(src/frontend/i18n/locales/<lang>.json = {"texto en español": "traducción"}, con patrones «{0} pasos»).
En el navegador lo hace src/frontend/i18n/i18n.js; aquí, lo mismo para los correos.
Cada cuenta elige su idioma (users.lang); sin sesión, el de la cookie bl_lang; por defecto, inglés."""
from __future__ import annotations

import json
import re
from functools import lru_cache

from app.core import config

LANGS = {"en": "English", "es": "Español", "ca": "Català", "fr": "Français", "it": "Italiano", "de": "Deutsch",
         "pt": "Português", "nl": "Nederlands", "zh": "中文", "ja": "日本語"}
DEFAULT = "en"
COOKIE = "bl_lang"
EDGE = re.compile(r"^([\s ·—–\-:,;|.]*)(.*?)([\s ·—–\-:,;|]*)$", re.S)
LETTER = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")


def clean(lang: str | None) -> str | None:
    lang = (lang or "").strip().lower()[:5].split("-")[0]
    return lang if lang in LANGS else None


def request_lang(request, user=None) -> str:
    """Idioma de la petición: el de la cuenta, si no el de la cookie, si no el predeterminado."""
    if user is not None and getattr(user, "lang", None):
        return user.lang
    return clean(request.cookies.get(COOKIE)) or DEFAULT


def locale_file(lang: str):
    return config.settings.frontend_dir / "i18n" / "locales" / f"{lang}.json"


@lru_cache(maxsize=16)
def _load(lang: str, mtime: float) -> tuple[dict, list]:
    try:
        d = json.loads(locale_file(lang).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    pats = []
    for k, v in d.items():
        if "{0}" not in k:
            continue
        nums = re.findall(r"\{(\d)\}", k)
        rx = re.escape(k)
        rx = re.sub(r"\\\{(\d)\\\}", "(.*?)", rx)
        pats.append((re.compile("^" + rx + "$", re.S), v, nums, len(k)))
    pats.sort(key=lambda p: -p[3])
    return d, pats


def dictionary(lang: str) -> tuple[dict, list]:
    if lang == "es" or lang not in LANGS:
        return {}, []
    try:
        mtime = locale_file(lang).stat().st_mtime
    except OSError:
        return {}, []
    return _load(lang, mtime)


def tr(lang: str, text: str) -> str:
    """Traduce un texto (con la misma normalización que i18n.js)."""
    if not text or lang == "es" or not LETTER.search(text):
        return text
    d, pats = dictionary(lang)
    if not d:
        return text
    pre, core, suf = EDGE.match(re.sub(r"[\s ]+", " ", text)).groups()
    if core in d:
        return pre + d[core] + suf
    for rx, t, nums, _ in pats:
        m = rx.match(core)
        if m:
            return pre + re.sub(r"\{(\d)\}", lambda x: m.group(nums.index(x.group(1)) + 1) if x.group(1) in nums else "", t) + suf
    return text


def tr_html(lang: str, html_text: str) -> str:
    """Traduce los textos que hay entre etiquetas de un HTML (los correos)."""
    if lang == "es":
        return html_text
    out = re.sub(r">([^<>]+)<", lambda m: ">" + tr(lang, m.group(1)) + "<", html_text)
    return out.replace('<html lang="es">', f'<html lang="{lang}">')


def script(lang: str) -> str:
    """El /i18n/<lang>.js: idioma, lista de idiomas y diccionario."""
    d, _ = dictionary(lang)
    return (f"window.BL_LANG={json.dumps(lang)};window.BL_LANGS={json.dumps(LANGS, ensure_ascii=False)};"
            f"window.BL_I18N={json.dumps(d, ensure_ascii=False)};")
