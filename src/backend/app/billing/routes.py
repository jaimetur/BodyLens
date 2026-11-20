"""Accounts with a Google Play subscription: sign-up from the Android app, renewing, status and the settings.

An account created by invitation or an approved request has no subscription and never expires. An account created with
a subscription can be used while Google Play says it is active (trial, paid, grace period, or cancelled but still in
the period paid); when it is over, only signing in, renewing, downloading data and deleting the account are allowed."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

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
    g = con.execute("SELECT until_ms, code FROM grants WHERE user_id=?", (user_id,)).fetchone()
    w = con.execute("SELECT status, period_end_ms, plan, method FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
    r = con.execute("SELECT state, expiry_ms, base_plan FROM subscriptions WHERE user_id=?", (user_id,)).fetchone()
    out = {"kind": "free"}
    if r is not None:
        out = {"kind": "play", "state": r["state"], "expiry": r["expiry_ms"], "plan": r["base_plan"]}
    if w is not None:
        out = {"kind": "web", "state": w["status"], "expiry": w["period_end_ms"], "plan": w["plan"], "method": w["method"]}
    if g is not None:       # the invitation code used ("admin" when an administrator gave the free access)
        gift = {"giftUntil": g["until_ms"], "code": g["code"]}
        out = {**out, "gift": True, **gift} if out["kind"] != "free" else {"kind": "gift", **gift}
    return out


GRACE_DAYS = 30   # an account whose subscription is over is read-only this long, then deleted (billing/dunning.py)


def read_only_until(user_id: int) -> int | None:
    """For an account whose subscription is over: when it will be deleted (ms) if it is not renewed; None otherwise.
    The lapse starts the first time it is seen (here or in the periodic check)."""
    if not expired(user_id):
        return None
    now = datetime.now(timezone.utc)
    with db.tx() as con:
        r = con.execute("SELECT lapsed_at FROM lapses WHERE user_id=?", (user_id,)).fetchone()
        if r is None:
            con.execute("INSERT INTO lapses(user_id, lapsed_at, warnings) VALUES(?,?,0)", (user_id, now.isoformat()))
            since = now
        else:
            since = datetime.fromisoformat(r["lapsed_at"])
    return int((since + timedelta(days=GRACE_DAYS)).timestamp() * 1000)


def status(user_id: int) -> dict:
    ro = read_only_until(user_id)
    with db.ro() as con:
        r = _row(con, user_id)
        w = con.execute("SELECT * FROM stripe_subs WHERE user_id=?", (user_id,)).fetchone()
        lapse = con.execute("SELECT * FROM lapses WHERE user_id=?", (user_id,)).fetchone()
        g = con.execute("SELECT * FROM grants WHERE user_id=?", (user_id,)).fetchone()
    extra = {"warnings": lapse["warnings"], "lapsedAt": lapse["lapsed_at"]} if lapse else {}
    if ro:
        extra["readOnly"] = True
        extra["deleteOn"] = ro
    if g is not None and (codes.active(g) or (w is None and r is None)):
        return {"plan": "gift", "active": codes.active(g), "expiry": g["until_ms"], **extra}
    if w is not None:
        return {"plan": "web", "active": web.active(user_id, w), "expiry": w["period_end_ms"], "basePlan": w["plan"],
                "state": w["status"], "cancelAtEnd": bool(w["cancel_end"]), **extra}
    if r is None:
        return {"plan": "free"}
    return {"plan": "play", "active": not expired(user_id), "expiry": r["expiry_ms"], "product": r["product_id"],
            "basePlan": r["base_plan"], "state": r["state"], "package": play.settings()["package"],
            "cancelAtEnd": r["state"] == "SUBSCRIPTION_STATE_CANCELED", **extra}


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
    return {"enabled": play.configured(), "package": s["package"], "product": s["product"],
            "storeUrl": (db.get_setting("play", {}) or {}).get("storeUrl", "")}


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


@router.post("/api/play/cancel")
def play_cancel(u: User = Depends(signed_in_user)):
    """Cancels the Google Play subscription: it stays active until the end of the paid period, then the account is
    read-only for 30 days and is deleted if it is not renewed."""
    with db.ro() as con:
        r = _row(con, u.id)
    if r is None:
        raise HTTPException(404, "No tienes una suscripción de Google Play.")
    if not play.configured():
        raise HTTPException(503, "Las suscripciones todavía no están disponibles en este servidor.")
    try:
        play.cancel(crypto.decrypt(r["token_enc"]), r["product_id"])
        info = play.check(crypto.decrypt(r["token_enc"]))
    except Exception as e:   # noqa: BLE001 — Google did not answer
        raise HTTPException(502, str(e) or "Google Play no responde. Inténtalo más tarde.")
    with db.tx() as con:
        con.execute("UPDATE subscriptions SET state=?, expiry_ms=? WHERE user_id=?", (info["state"], info["expiry"], u.id))
    return status(u.id)


# ---------- Administration ----------

class PlayIn(BaseModel):
    package: str = ""
    product: str = ""
    serviceAccount: str = ""   # the JSON key of the service account; empty = keep the stored one
    remove: bool = False
    storeUrl: str | None = None   # the app's page in Google Play, once published (the landing page links it)


class CodeIn(BaseModel):
    code: str
    duration: str = "life"   # 1m, 3m, 6m, 1y, life or a date YYYY-MM-DD (free until that day)
    expires: str = ""        # YYYY-MM-DD: the last day it can be used ("" = no end)
    max: int | None = None   # how many accounts can use it (None = no limit)
    public: bool = False     # shown on the landing page as a promotion
    aliases: list[str] = []  # other names for the same code (e.g. LAUNCH for LANZAMIENTO)


class CodesIn(BaseModel):
    codes: list[CodeIn | str]


@router.get("/api/promos")
def get_promos():
    """The promotions shown on the landing page (public codes and the places they have left)."""
    return {"promos": codes.promos()}


@router.get("/api/admin/codes")
def get_codes(u: User = Depends(admin_user)):
    return {"codes": codes.codes()}


@router.put("/api/admin/codes")
def put_codes(body: CodesIn, u: User = Depends(admin_user)):
    clean = []
    old = {codes.norm(c["code"]): c for c in codes.codes()}
    for c in body.codes:
        code, dur, exp, mx, pub, al = (c, "life", "", None, False, []) if isinstance(c, str) else \
            (c.code, c.duration, c.expires, c.max, c.public, c.aliases)
        code = code.strip()
        if not code or codes.norm(code) in {n for x in clean for n in codes.names(x)}:
            continue
        al = [a.strip() for a in al if a.strip() and len(a.strip()) <= 60]
        al = [a for i, a in enumerate(al) if codes.norm(a) != codes.norm(code) and codes.norm(a) not in {codes.norm(b) for b in al[:i]}]
        if any(codes.norm(a) in {n for x in clean for n in codes.names(x)} for a in al):
            raise HTTPException(400, "Un alias no puede coincidir con otro código.")
        if len(code) > 60:
            raise HTTPException(400, "Un código no puede tener más de 60 caracteres.")
        d = codes.clean_duration(dur)
        if not d:
            raise HTTPException(400, "La duración de un código no es válida.")
        if "-" in d and codes.expired({"expires": d}):
            raise HTTPException(400, "La fecha hasta la que es gratis un código no puede haber pasado ya.")
        e = codes.clean_expiry(exp)
        if e is None:
            raise HTTPException(400, "Esa fecha de caducidad no es válida.")
        if e and codes.expired({"expires": e}):
            raise HTTPException(400, "La fecha de caducidad de un código no puede haber pasado ya.")
        if mx is not None and not 1 <= mx <= 1_000_000:
            raise HTTPException(400, "El número máximo de cuentas de un código tiene que ser de 1 a 1 000 000.")
        used = (old.get(codes.norm(code)) or {}).get("used", 0)     # the accounts already made with it are kept
        if mx is not None and used >= mx:
            raise HTTPException(400, "Ese código ya se ha usado ese número de veces: pon un máximo mayor.")
        clean.append({"code": code, "aliases": al, "duration": d, "expires": e, "max": mx, "used": used, "public": pub})
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
            "serviceAccount": sa.get("client_email", ""), "subscriptions": n,
            "storeUrl": (db.get_setting("play", {}) or {}).get("storeUrl", "")}


@router.put("/api/admin/play")
def put_play(body: PlayIn, u: User = Depends(admin_user)):
    import json
    stored = db.get_setting("play", {}) or {}
    new = {"package": body.package.strip() or play.DEFAULT_PACKAGE, "product": body.product.strip() or play.DEFAULT_PRODUCT,
           "sa": stored.get("sa"), "storeUrl": stored.get("storeUrl", "")}
    if body.storeUrl is not None:
        url = body.storeUrl.strip()
        if url and not url.startswith("https://play.google.com/"):
            raise HTTPException(400, "El enlace tiene que ser de https://play.google.com/…")
        new["storeUrl"] = url
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
