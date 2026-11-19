"""Automatic translation of the English documents (help, README, changelog) into the reader's language.

English is the only source. A translation is made the first time a document is asked for in a language and kept in
<DATA_DIR>/translations/<lang>/<doc>-<hash>.html, where the hash is the one of the English text: when the English
changes, a new translation is made. Until it is ready, and when no translator is available, the English is shown.

Translators, in order:
  1. LibreTranslate (free, self-hosted next to BodyLens): LIBRETRANSLATE_URL, e.g. http://libretranslate:5000.
  2. The Claude API (paid, better quality), only if an Anthropic API key is set (ANTHROPIC_API_KEY or
     Administration, stored encrypted).
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
from pathlib import Path

from app.core import config, crypto, db, i18n

log = logging.getLogger("bodylens.translate")

MODEL = "claude-opus-5-5"
SETTING = "translator"
CHUNK = 12000   # characters of Markdown per request (split at headings)

_busy: set[tuple[str, str]] = set()
_lock = threading.Lock()
_slots = threading.Semaphore(2)   # at most two translations at a time


# ---------- settings ----------

def api_key() -> str:
    env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env:
        return env
    s = db.get_setting(SETTING) or {}
    return crypto.decrypt(s.get("key")) or "" if s.get("key") else ""


LIBRE_TTL = 60.0
_libre: dict = {"at": 0.0, "codes": None}


def libre_url() -> str:
    return os.environ.get("LIBRETRANSLATE_URL", "").strip().rstrip("/")


def libre_codes() -> set[str] | None:
    """Languages LibreTranslate can translate into (None when it is not reachable); checked at most once a minute."""
    import time
    if not libre_url():
        return None
    if time.time() - _libre["at"] < LIBRE_TTL:
        return _libre["codes"]
    import httpx
    try:
        r = httpx.get(libre_url() + "/languages", timeout=4)
        r.raise_for_status()
        codes = {x["code"] for x in r.json()}
    except Exception:  # noqa: BLE001 — not reachable yet (e.g. still downloading its models)
        codes = None
    _libre.update(at=time.time(), codes=codes)
    return codes


def libre_code(lang: str) -> str | None:
    codes = libre_codes() or set()
    if lang in codes:
        return lang
    return next((c for c in sorted(codes) if c.startswith(lang + "-") or (lang == "zh" and c in ("zh-Hans", "zh"))), None)


def provider(lang: str | None = None) -> str | None:
    """'libre', 'claude' or None (no translator for ``lang``)."""
    if libre_codes() is not None and (lang is None or libre_code(lang)):
        return "libre"
    if api_key():
        return "claude"
    return None


def configured() -> bool:
    return provider() is not None


def save_key(con, key: str | None) -> None:
    """Store the key encrypted; an empty key removes it."""
    cur = db.get_setting(SETTING) or {}
    cur["key"] = crypto.encrypt(key.strip()) if key and key.strip() else None
    db.set_setting(con, SETTING, cur)


def status() -> dict:
    s = db.get_setting(SETTING) or {}
    codes = libre_codes()
    return {"configured": configured(), "provider": provider(), "libreUrl": libre_url(), "libreOk": codes is not None,
            "libreLanguages": sorted(codes or []), "claudeKey": bool(api_key()),
            "fromEnv": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
            "model": MODEL, "lastError": s.get("lastError"), "lastOk": s.get("lastOk")}


def _note(**kv) -> None:
    with db.tx() as con:
        cur = db.get_setting(SETTING) or {}
        cur.update(kv)
        db.set_setting(con, SETTING, cur)


# ---------- cache ----------

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def cache_path(lang: str, doc: str, source: str) -> Path:
    return config.settings.data_dir / "translations" / lang / f"{doc}-{_hash(source)}.html"


def cached(lang: str, doc: str, source: str) -> str | None:
    p = cache_path(lang, doc, source)
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


# translations kept in the repository (help/i18n/<lang>/<doc>.md), made carefully for the most used languages; the
# first line records the English they were made from: <!-- en: <hash> -->. A stale one (the English changed since)
# is not used, and the automatic translator takes over until it is updated (tools/help_i18n.py lists them).
BUNDLE_HEAD = re.compile(r"^<!--\s*en:\s*([0-9a-f]{16})\s*-->[ \t]*\n?")


def bundle_path(lang: str, doc: str) -> Path:
    return config.settings.docs_dir / "help" / "i18n" / lang / f"{doc}.md"


def source_hash(source: str) -> str:
    return _hash(source)


def bundled(lang: str, doc: str, source: str) -> str | None:
    """The HTML of the bundled translation of ``doc``, if there is one made from the current English."""
    try:
        text = bundle_path(lang, doc).read_text(encoding="utf-8")
    except OSError:
        return None
    m = BUNDLE_HEAD.match(text)
    if not m or m.group(1) != _hash(source):
        return None
    from app.help import docs
    return docs.render(text[m.end():])


def pending(lang: str, doc: str) -> bool:
    with _lock:
        return (lang, doc) in _busy


# ---------- translation ----------

SYSTEM = (
    "You translate the Markdown documentation of BodyLens, a personal health web app (weight and body composition, "
    "activity, sleep, heart, meals, cycle, mood), from English into {language}.\n"
    "Rules:\n"
    "- Return only the translated Markdown, with exactly the same structure: headings, lists, tables, emphasis, links, "
    "blank lines.\n"
    "- Do not translate code blocks, inline code, URLs, file names or link targets.\n"
    "- Keep product names as they are (BodyLens, Withings, Health Auto Export, Health Connect, AutoSleep, Apple Watch, "
    "Google, Claude, Docker). Apple Health is the iPhone app; use its official name in {language}.\n"
    "- Names of the app's screens and buttons are in bold or in quotes: translate them as the app shows them; this "
    "glossary has the app's own translations:\n{glossary}\n"
    "- Address the reader informally if {language} distinguishes, in a clear and concise style."
)


def _glossary(lang: str) -> str:
    """The short UI names of the app in ``lang`` (English -> translation), so the help uses the same words."""
    import json
    try:
        d = json.loads(i18n.locale_file(lang).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "(none)"
    pairs = [(k, v if isinstance(v, str) else v[0]) for k, v in d.items() if len(k) <= 32 and "{" not in k]
    return "\n".join(f"{k} = {v}" for k, v in pairs[:900])


def chunks(md: str) -> list[str]:
    """Split at level-1/2 headings into pieces of at most CHUNK characters (outside code blocks)."""
    parts, cur, in_code = [], [], False
    for line in md.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,2}\s", line) and sum(len(x) + 1 for x in cur) > CHUNK // 2:
            parts.append("\n".join(cur))
            cur = []
        cur.append(line)
    parts.append("\n".join(cur))
    out = []
    for p in parts:   # still too long (a huge section): split at blank lines
        while len(p) > CHUNK:
            cut = p.rfind("\n\n", 0, CHUNK)
            cut = cut if cut > 0 else CHUNK
            out.append(p[:cut])
            p = p[cut:]
        out.append(p)
    return [p for p in out if p.strip()]


def _translate_chunk(client, lang: str, text: str) -> str:
    language = i18n.LANGS.get(lang, lang)
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",   # if the model declines, the API retries on a fallback model in the same call
        output_config={"effort": "low"},
        system=SYSTEM.format(language=language, glossary=_glossary(lang)),
        messages=[{"role": "user", "content": text}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError("the model declined to translate this text")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("the translation was cut off (max_tokens)")
    return "".join(b.text for b in msg.content if b.type == "text").strip("\n")


def _translate_claude(lang: str, source: str) -> str:
    import anthropic
    from app.help import docs
    client = anthropic.Anthropic(api_key=api_key(), max_retries=3)
    md = "\n\n".join(_translate_chunk(client, lang, c) for c in chunks(source)) + "\n"
    return docs.render(md)


PROTECT = re.compile(r"<pre>.*?</pre>|<code>.*?</code>", re.S)


def _translate_libre(lang: str, source: str) -> str:
    """Translate the rendered HTML; code blocks and inline code are replaced by empty markers and put back after."""
    import httpx
    from app.help import docs
    code = libre_code(lang)
    if not code:
        raise RuntimeError(f"LibreTranslate cannot translate into {lang}")
    html = docs.render(source)
    kept: list[str] = []
    html = PROTECT.sub(lambda m: kept.append(m.group(0)) or f'<var data-k="{len(kept) - 1}"></var>', html)
    # one request per section, so a long document does not hit time limits
    parts = re.split(r"(?=<h[12]>)", html)
    out = []
    with httpx.Client(timeout=300) as c:
        for part in parts:
            if not re.search(r"[A-Za-z]", re.sub(r"<[^>]+>", "", part)):
                out.append(part)
                continue
            r = c.post(libre_url() + "/translate", json={"q": part, "source": "en", "target": code, "format": "html"})
            r.raise_for_status()
            out.append(r.json()["translatedText"])
    res = "".join(out)
    return re.sub(r'<var data-k="(\d+)">\s*</var>', lambda m: kept[int(m.group(1))], res)


def translate(lang: str, doc: str, source: str) -> str:
    """Translate ``source`` (English Markdown) into ``lang`` and keep the HTML in the cache."""
    prov = provider(lang)
    if prov == "libre":
        out = _translate_libre(lang, source)
    elif prov == "claude":
        out = _translate_claude(lang, source)
    else:
        raise RuntimeError("no translator available")
    p = cache_path(lang, doc, source)
    p.parent.mkdir(parents=True, exist_ok=True)
    for old in p.parent.glob(f"{doc}-*.*"):   # translations of older English versions
        old.unlink(missing_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(out, encoding="utf-8")
    os.replace(tmp, p)
    return out


def request(lang: str, doc: str, source: str) -> bool:
    """Start translating in the background (once). False when there is no translator configured."""
    if lang == "en" or not provider(lang):
        return False
    with _lock:
        if (lang, doc) in _busy:
            return True
        _busy.add((lang, doc))

    def run():
        try:
            with _slots:
                translate(lang, doc, source)
            _note(lastOk=db.now_iso(), lastError=None)
            log.info("translated %s into %s", doc, lang)
        except Exception as e:  # noqa: BLE001 — never break the Help page because of the translator
            log.warning("could not translate %s into %s: %s", doc, lang, type(e).__name__)
            _note(lastError={"at": db.now_iso(), "doc": doc, "lang": lang, "error": f"{type(e).__name__}: {e}"[:300]})
        finally:
            with _lock:
                _busy.discard((lang, doc))

    threading.Thread(target=run, name=f"bodylens-translate-{lang}-{doc}", daemon=True).start()
    return True


def prewarm(langs: list[str]) -> int:
    """Translate in the background every document into the given languages (those already done are skipped)."""
    from app.help import docs
    n = 0
    for lang in sorted(set(langs) - {"en"}):
        for doc in docs.all_docs():
            src = docs.source(doc)
            if src is not None and bundled(lang, doc, src) is None and cached(lang, doc, src) is None \
                    and request(lang, doc, src):
                n += 1
    return n
