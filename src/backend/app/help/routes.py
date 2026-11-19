"""Routes of the Help module: the documents in the reader's language (translated automatically from English)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.accounts.users import User
from app.core import db, i18n
from app.core.deps import admin_user, bad, current_user
from app.help import docs, translate

router = APIRouter()


def _lang(request: Request, u: User) -> str:
    return i18n.clean(request.query_params.get("lang")) or i18n.request_lang(request, u)


def _doc(lang: str, doc: str) -> tuple[str, str, bool]:
    """(html, language actually shown, translation pending)."""
    src = docs.source(doc)
    if src is None:
        raise HTTPException(404, "That help document does not exist.")
    if lang != "en":
        done = translate.bundled(lang, doc, src) or translate.cached(lang, doc, src)
        if done is not None:
            return done, lang, False
        return docs.render(src), "en", translate.request(lang, doc, src)
    return docs.render(src), "en", False


def _title(html: str, doc: str) -> str:
    import re
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else doc


@router.get("/api/help")
def help_index(request: Request, u: User = Depends(current_user)):
    lang = _lang(request, u)
    mods = []
    for n in docs.module_names():
        html, _, _ = _doc(lang, n)
        mods.append({"id": n, "title": _title(html, n)})
    return {"lang": lang, "modules": mods, "translator": translate.configured()}


@router.get("/api/help/{doc}")
def help_doc(doc: str, request: Request, u: User = Depends(current_user)):
    lang = _lang(request, u)
    html, shown, pending = _doc(lang, doc)
    return {"doc": doc, "lang": lang, "shown": shown, "pending": pending, "translator": translate.configured(),
            "title": _title(html, doc), "html": html}


# ---------- Administration: the translator ----------

class TranslatorIn(BaseModel):
    apiKey: str = ""      # empty = keep the stored one
    remove: bool = False


@router.get("/api/admin/translator")
def get_translator(u: User = Depends(admin_user)):
    return translate.status()


@router.put("/api/admin/translator")
def put_translator(body: TranslatorIn, u: User = Depends(admin_user)):
    if body.apiKey.strip() and not body.apiKey.strip().startswith("sk-ant-"):
        bad("That does not look like an Anthropic API key (it starts with sk-ant-).")
    with db.tx() as con:
        if body.remove:
            translate.save_key(con, None)
        elif body.apiKey.strip():
            translate.save_key(con, body.apiKey)
    return translate.status()


@router.post("/api/admin/translator/prewarm")
def prewarm(u: User = Depends(admin_user)):
    """Translate now every document into the languages the accounts use."""
    if not translate.configured():
        bad("No translator is available: LibreTranslate is not reachable and there is no API key.")
    return {"started": translate.prewarm(translate.prewarm_languages())}
