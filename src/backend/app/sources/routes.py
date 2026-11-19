"""Rutas de las fuentes directas: Withings (OAuth por cuenta), Apple Salud (dirección con token para Health Auto
Export) y estado de las fuentes en «Tu cuenta»."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.accounts.users import User, get_user
from app.core import crypto, db
from app.core.deps import base_url, current_user, optional_user
from app.sheets import service as sheets
from app.sources import hae, withings

router = APIRouter()
log = logging.getLogger("bodylens.sources")


def _h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def ensure_server(user: User) -> None:
    """Primera vez que llega algo directo: la cuenta pasa a tener sus datos en el servidor (con su historial de la hoja)."""
    if sheets.source_of(user.id) == "server":
        return
    if user.sheet_id:
        await sheets.switch_to_server(user)
    else:
        with db.tx() as con:
            sheets.set_source(con, user.id, "server")


def _note(user_id: int, key: str, value: dict) -> None:
    with db.tx() as con:
        db.set_setting(con, f"{key}:{user_id}", value)


# ---------- Withings ----------

@router.get("/oauth/withings/start")
def withings_start(request: Request):
    u = optional_user(request)
    if not u:
        return RedirectResponse("/login?next=/%23cuenta", status_code=303)
    if not withings.configured():
        raise HTTPException(503, "Withings no está configurado en el servidor (WITHINGS_CLIENT_ID y WITHINGS_CLIENT_SECRET).")
    state = crypto.new_token(18)
    with db.tx() as con:
        db.set_setting(con, f"oauth:{state}", {"user": u.id, "exp": time.time() + 900})
    return RedirectResponse(withings.authorize_url(state), status_code=303)


@router.get("/oauth/withings/callback")
async def withings_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    st = db.get_setting(f"oauth:{state}") if state else None
    with db.tx() as con:
        con.execute("DELETE FROM settings WHERE key=?", (f"oauth:{state}",))
    if error or not code or not st or st.get("exp", 0) < time.time():
        return RedirectResponse("/#cuenta", status_code=303)
    with db.ro() as con:
        u = get_user(con, st["user"])
    if not u:
        return RedirectResponse("/login", status_code=303)
    async with httpx.AsyncClient() as client:
        await withings.exchange_code(client, u.id, code)
    await ensure_server(u)
    asyncio.create_task(_withings_now(u.id))
    return RedirectResponse("/#cuenta", status_code=303)


@router.api_route("/oauth/withings/callback", methods=["POST", "HEAD"])
async def withings_notify(request: Request):
    """Withings llama a la dirección registrada con POST: para comprobarla («Test») y para avisar de datos nuevos
    (userid=…). Siempre se responde 200; si es un aviso de una cuenta conectada, se sincroniza al momento."""
    if request.method == "POST":
        try:
            form = await request.form()
            wuid = str(form.get("userid") or "")
        except Exception:  # noqa: BLE001 — la prueba de Withings puede venir sin cuerpo
            wuid = ""
        if wuid:
            with db.ro() as con:
                rows = con.execute("SELECT user_id FROM source_tokens WHERE source='withings'").fetchall()
            for r in rows:
                tok = withings.load_tokens(r["user_id"]) or {}
                if str(tok.get("userid")) == wuid:
                    asyncio.create_task(_withings_now(r["user_id"]))
    return {"ok": True}


async def _withings_now(user_id: int) -> None:
    try:
        r = await withings.sync(user_id)
        _note(user_id, "withings_last", {"at": db.now_iso(), **r})
        await sheets.rebuild_async(user_id)
    except Exception:
        log.exception("primera sincronización de Withings de %s", user_id)


@router.post("/api/sources/withings/disconnect")
def withings_disconnect(u: User = Depends(current_user)):
    withings.forget(u.id)
    return {"ok": True}


# ---------- Apple Salud (Health Auto Export) ----------

@router.post("/api/sources/hae/token")
def hae_token(request: Request, u: User = Depends(current_user)):
    """Crea (o cambia) la dirección de envío de la cuenta; la anterior deja de valer."""
    token = crypto.new_token(24)
    with db.tx() as con:
        con.execute("DELETE FROM ingest_tokens WHERE user_id=? AND source='hae'", (u.id,))
        con.execute("INSERT INTO ingest_tokens(token_hash, user_id, source) VALUES(?,?, 'hae')", (_h(token), u.id))
        con.execute("INSERT INTO source_tokens(user_id, source, data, updated_at) VALUES(?, 'hae', ?, ?) "
                    "ON CONFLICT(user_id, source) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
                    (u.id, crypto.encrypt({"token": token}), db.now_iso()))
    return {"url": f"{base_url(request)}/api/ingest/hae/{token}"}


def _user_for_token(token: str) -> User | None:
    with db.ro() as con:
        r = con.execute("SELECT user_id FROM ingest_tokens WHERE token_hash=? AND source='hae'", (_h(token or ""),)).fetchone()
        return get_user(con, r["user_id"]) if r else None


async def _ingest(request: Request, token: str):
    u = _user_for_token(token)
    if not u or not u.active:
        return {"ok": False, "error": "token"}
    try:
        body = json.loads(await request.body())
    except ValueError:
        return {"ok": False, "error": "json"}
    await ensure_server(u)

    def work():
        with db.tx() as con:
            return hae.ingest(con, u.id, body)
    res = await asyncio.to_thread(work)
    _note(u.id, "hae_last", {"at": db.now_iso(), **{k: v for k, v in res.items() if k != "ok"}})
    await sheets.rebuild_async(u.id)
    return res


@router.post("/api/ingest/hae/{token}")
async def ingest_hae(token: str, request: Request):
    return await _ingest(request, token)


@router.post("/api/ingest/hae")
async def ingest_hae_q(request: Request, token: str = ""):
    return await _ingest(request, token)


# ---------- estado ----------

@router.get("/api/sources")
def sources(request: Request, u: User = Depends(current_user)):
    tok = withings.load_tokens(u.id)
    with db.ro() as con:
        r = con.execute("SELECT data FROM source_tokens WHERE user_id=? AND source='hae'", (u.id,)).fetchone()
    hae_tok = crypto.decrypt(r["data"]) if r else None
    return {
        "dataSource": sheets.source_of(u.id),
        "withings": {"configured": withings.configured(), "connected": bool(tok),
                     "connectedAt": (tok or {}).get("connected_at"), "last": db.get_setting(f"withings_last:{u.id}"),
                     "callback": withings.redirect_uri()},
        "hae": {"url": f"{base_url(request)}/api/ingest/hae/{hae_tok['token']}" if hae_tok else None,
                "last": db.get_setting(f"hae_last:{u.id}")},
        "androidApk": _apk_exists(),
    }


def _apk_exists() -> bool:
    from app.web.routes import android_apk_path
    return android_apk_path().exists()
