"""Accounts with a Google Play subscription: sign-up from the Android app, renewing, status and the settings.

An account created by invitation or an approved request has no subscription and never expires. An account created with
a subscription can be used while Google Play says it is active (trial, paid, grace period, or cancelled but still in
the period paid); when it is over, only signing in, renewing, downloading data and deleting the account are allowed."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError, clean_email
from app.billing import codes, play, web
from app.core import crypto, db
from app.core.deps import admin_user, bad, set_session_cookie, signed_in_user

router = APIRouter()
RECHECK_MS = 3600 * 1000        # an expired subscription is asked to Google again at most once an hour


def _row(con, user_id: int):
    return con.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()


def _save(con, user_id: int, token: str, info: dict) -> None:
    now = int(time.time() * 1000)
    con.execute(
        "INSERT INTO subscriptions(user_id, token_hash, token_enc, product_id, base_plan, state, expiry_ms, checked_at, "
        "created_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET token_hash=excluded.token_hash, "
        "token_enc=excluded.token_enc, product_id=excluded.product_id, base_plan=excluded.base_plan, "
        "state=excluded.state, expiry_ms=excluded.expiry_ms, checked_at=excluded.checked_at",
        (user_id, play.token_hash(token), crypto.encrypt(token), info["product"], info.get("basePlan"), info["state"],
         info["expiry"], now, datetime.now(timezone.utc).isoformat()))


def expired(user_id: int) -> bool:
    """True when the account has a subscription or a free access with an end date, and none of them is active.
    Accounts with none of them (created by invitation link or approved request) never expire."""
    with db.ro() as con:
        g = con.execute("SELECT * FROM grants WHERE user_id=?", (user_id,)).fetchone()
        w = con.execute("SELECT * FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
        r = _row(con, user_id)
    if g is not None and codes.active(g):
        return False
    if w is not None and web.active(user_id, w):
        return False
    if r is not None and not _play_expired(user_id):
        return False
    return g is not None or w is not None or r is not None


def _play_expired(user_id: int) -> bool:
    """The Google Play subscription is over (asking Google again once an hour)."""
    with db.ro() as con:
        r = _row(con, user_id)
    now = int(time.time() * 1000)
    if r is None or r["expiry_ms"] > now:
        return False
    if now - r["checked_at"] < RECHECK_MS or not play.configured():
        return True
    token = crypto.decrypt(r["token_enc"])
    try:
        info = play.check(token)
    except (play.PlayError, Exception):   # Google unreachable: keep what is known
        with db.tx() as con:
            con.execute("UPDATE subscriptions SET checked_at=? WHERE user_id=?", (now, user_id))
        return True
    with db.tx() as con:
        _save(con, user_id, token, info)
    return not info["active"]


def cancel_for(con, user_id: int) -> None:
    """Cancels the account's subscription (Stripe or Google Play) so nothing more is charged once it is deleted.
    Best effort: a provider that does not answer does not stop the deletion."""
    w = con.execute("SELECT subscription_id FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
    if w is not None:
        try:
            web.stripe.call("DELETE", f"/subscriptions/{w['subscription_id']}")
        except Exception:   # noqa: BLE001
            pass
    r = _row(con, user_id)
    if r is not None and play.configured():
        try:
            play.cancel(crypto.decrypt(r["token_enc"]), r["product_id"])
        except Exception:   # noqa: BLE001
            pass


def summary(con, user_id: int) -> dict:
    """What kind of account it is, without asking Google or Stripe (for the list in Administration): free with a code
    ("gift", with its end date or none for life), paid on the website ("web") or in the app ("play"), or neither."""
    g = con.execute("SELECT until_ms FROM grants WHERE user_id=?", (user_id,)).fetchone()
    w = con.execute("SELECT status, period_end_ms FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
    r = con.execute("SELECT state, expiry_ms FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()
    out = {"kind": "free"}
    if r is not None:
        out = {"kind": "play", "state": r["state"], "expiry": r["expiry_ms"]}
    if w is not None:
        out = {"kind": "web", "state": w["status"], "expiry": w["period_end_ms"]}
    if g is not None:
        out = {**out, "gift": True, "giftUntil": g["until_ms"]} if out["kind"] != "free" else {"kind": "gift", "giftUntil": g["until_ms"]}
    return out


def status(user_id: int) -> dict:
    with db.ro() as con:
        r = _row(con, user_id)
        w = con.execute("SELECT * FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
        lapse = con.execute("SELECT * FROM lapses WHERE user_id=?", (user_id,)).fetchone()
        g = con.execute("SELECT * FROM grants WHERE user_id=?", (user_id,)).fetchone()
    extra = {"warnings": lapse["warnings"], "lapsedAt": lapse["lapsed_at"]} if lapse else {}
    if g is not None and (codes.active(g) or (w is None and r is None)):
        return {"plan": "gift", "active": codes.active(g), "expiry": g["until_ms"], **extra}
    if w is not None:
        return {"plan": "web", "active": web.active(user_id, w), "expiry": w["period_end_ms"], "basePlan": w["plan"],
                "state": w["status"], **extra}
    if r is None:
        return {"plan": "free"}
    return {"plan": "play", "active": not expired(user_id), "expiry": r["expiry_ms"], "product": r["product_id"],
            "basePlan": r["base_plan"], "state": r["state"], "package": play.settings()["package"], **extra}


def _verified(token: str) -> dict:
    if not play.configured():
        raise HTTPException(503, "Las suscripciones todavía no están disponibles en este servidor.")
    try:
        info = play.check(token)
    except play.PlayError as e:
        raise HTTPException(400, str(e))
    if not info["active"]:
        raise HTTPException(400, "Esa suscripción no está activa.")
    return info


@router.get("/api/play/config")
def config():
    """Whether this server accepts accounts paid with a subscription (the app shows the option only then)."""
    s = play.settings()
    return {"enabled": play.configured(), "package": s["package"], "product": s["product"]}


class SignupIn(BaseModel):
    token: str
    username: str
    name: str
    email: str
    password: str


@router.post("/api/play/signup")
def signup(body: SignupIn, response: Response):
    """Creates an account paid with the subscription just bought in the app, and signs in."""
    info = _verified(body.token.strip())
    try:
        with db.tx() as con:
            if con.execute("SELECT 1 FROM subscriptions WHERE token_hash=?", (play.token_hash(body.token.strip()),)).fetchone():
                raise UserError("Esa suscripción ya tiene una cuenta: entra con su usuario y contraseña.")
            email = clean_email(body.email, required=True)
            u = users.create_user(con, body.username, body.name, body.password, email=email)
            _save(con, u.id, body.token.strip(), info)
            token = users.create_session(con, u.id)
    except UserError as e:
        bad(e)
    if not info["acknowledged"]:
        play.acknowledge(body.token.strip(), info["product"])
    set_session_cookie(response, token)
    return {"ok": True, "user": u.public()}


class LinkIn(BaseModel):
    token: str


@router.post("/api/play/link")
def link(body: LinkIn, u: User = Depends(signed_in_user)):
    """Links a subscription to the signed-in account: to renew one that is over, or to restore it."""
    info = _verified(body.token.strip())
    with db.tx() as con:
        other = con.execute("SELECT user_id FROM subscriptions WHERE token_hash=?",
                            (play.token_hash(body.token.strip()),)).fetchone()
        if other and other["user_id"] != u.id:
            raise HTTPException(400, "Esa suscripción es de otra cuenta.")
        _save(con, u.id, body.token.strip(), info)
    if not info["acknowledged"]:
        play.acknowledge(body.token.strip(), info["product"])
    return status(u.id)


@router.get("/api/play/status")
def my_status(u: User = Depends(signed_in_user)):
    return status(u.id)


# ---------- Administration ----------

class PlayIn(BaseModel):
    package: str = ""
    product: str = ""
    serviceAccount: str = ""   # the JSON key of the service account; empty = keep the stored one
    remove: bool = False


class CodesIn(BaseModel):
    codes: list[str]


@router.get("/api/admin/codes")
def get_codes(u: User = Depends(admin_user)):
    return {"codes": codes.codes()}


@router.put("/api/admin/codes")
def put_codes(body: CodesIn, u: User = Depends(admin_user)):
    clean = []
    for c in body.codes:
        c = c.strip()
        if c and codes.norm(c) not in {codes.norm(x) for x in clean}:
            if len(c) > 60:
                raise HTTPException(400, "Un código no puede tener más de 60 caracteres.")
            clean.append(c)
    with db.tx() as con:
        db.set_setting(con, "codes", clean)
    return {"codes": codes.codes()}


@router.get("/api/admin/play")
def get_play(u: User = Depends(admin_user)):
    s = play.settings()
    sa = s["sa"] or {}
    with db.ro() as con:
        n = con.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
    return {"package": s["package"], "product": s["product"], "configured": play.configured(),
            "serviceAccount": sa.get("client_email", ""), "subscriptions": n}


@router.put("/api/admin/play")
def put_play(body: PlayIn, u: User = Depends(admin_user)):
    import json
    stored = db.get_setting("play", {}) or {}
    new = {"package": body.package.strip() or play.DEFAULT_PACKAGE, "product": body.product.strip() or play.DEFAULT_PRODUCT,
           "sa": stored.get("sa")}
    if body.remove:
        new["sa"] = None
    elif body.serviceAccount.strip():
        try:
            sa = json.loads(body.serviceAccount)
            assert sa.get("client_email") and sa.get("private_key")
        except (ValueError, AssertionError, AttributeError):
            raise HTTPException(400, "Pega el fichero JSON de la clave de la cuenta de servicio.")
        new["sa"] = crypto.encrypt({k: sa[k] for k in ("client_email", "private_key", "token_uri") if k in sa})
    with db.tx() as con:
        db.set_setting(con, "play", new)
    play._access.clear()
    return get_play(u)
