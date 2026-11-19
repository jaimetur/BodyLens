"""Rutas de cuentas: entrar y salir, registro por invitación, «Tu cuenta» y administración de cuentas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError
from app.core import config, db, i18n
from app.core.deps import (COOKIE, admin_user, bad, base_url, client_ip, current_user, session_token,
                           set_session_cookie)
from app.core.security import login_throttle
from app.sync import workbook

router = APIRouter()


# ---------- entrar y salir ----------

class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/api/login")
def login(body: LoginIn, request: Request, response: Response):
    keys = (f"ip:{client_ip(request)}", f"user:{body.username.strip().lower()}")
    if any(login_throttle.blocked(k) for k in keys):
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    with db.tx() as con:
        u = users.authenticate(con, body.username, body.password)
        if not u:
            for k in keys:
                login_throttle.fail(k)
            raise HTTPException(401, "Usuario o contraseña incorrectos.")
        if not u.active:
            raise HTTPException(403, "Tu petición de acceso todavía no está aprobada. Te llegará un correo cuando lo esté.")
        token = users.create_session(con, u.id)
    login_throttle.reset(keys[1])
    set_session_cookie(response, token)
    return {"ok": True, "user": u.public(), "mustChange": u.must_change}


@router.post("/api/logout")
def logout(request: Request, response: Response):
    with db.tx() as con:
        users.delete_session(con, session_token(request))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/api/login-hint")
def login_hint():
    """Cuentas que aún tienen su contraseña por defecto (referencia para un despliegue nuevo)."""
    with db.ro() as con:
        return {"accounts": users.default_accounts(con)}


# ---------- registro por invitación ----------

class RegisterIn(BaseModel):
    code: str
    username: str
    name: str
    password: str
    email: str = ""
    lang: str = ""   # language of the interface chosen in the form (else the one of the page)


@router.get("/api/invite/{code}")
def invite_info(code: str):
    with db.ro() as con:
        return {"valid": users.invite_valid(con, code)}


@router.post("/api/register")
def register(body: RegisterIn, request: Request, response: Response):
    ip = request.client.host if request.client else "?"
    if login_throttle.blocked(f"reg:{ip}"):
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    try:
        with db.tx() as con:
            u = users.redeem_invite(con, body.code, body.username, body.name, body.password, body.email)
            u.lang = users.set_lang(con, u.id, i18n.clean(body.lang) or i18n.request_lang(request))
            token = users.create_session(con, u.id)
    except UserError as e:
        login_throttle.fail(f"reg:{ip}")
        bad(e)
    set_session_cookie(response, token)
    return {"ok": True, "user": u.public()}


# ---------- «Tu cuenta» ----------

def _me(con, u: User) -> dict:
    partner = users.get_user(con, u.partner_id) if u.partner_id else None
    inc = con.execute("SELECT u.username, u.name FROM partner_requests r JOIN users u ON u.id=r.from_id WHERE r.to_id=?",
                      (u.id,)).fetchall()
    out = con.execute("SELECT u.username, u.name FROM partner_requests r JOIN users u ON u.id=r.to_id WHERE r.from_id=?",
                      (u.id,)).fetchall()
    pw = con.execute("SELECT pw_hash FROM users WHERE id=?", (u.id,)).fetchone()[0]
    return {
        "user": u.public(),
        "defaultPassword": users.has_default_password(u, pw),
        "partner": {"username": partner.username, "name": partner.name, "since": u.partner_since} if partner else None,
        "requests": {"incoming": [dict(r) for r in inc], "outgoing": [dict(r) for r in out]},
        "sources": {"sheet": bool(u.sheet_id), "appsScript": bool(u.apps_script_url)},
        "sync": workbook.meta(u.id),
        "syncIntervalMin": config.settings.sync_interval_min,
        "pendingRequests": con.execute("SELECT COUNT(*) FROM users WHERE active=0").fetchone()[0] if u.is_admin else 0,
    }


@router.get("/api/me")
def me(u: User = Depends(current_user)):
    with db.ro() as con:
        return _me(con, u)


class PasswordIn(BaseModel):
    current: str
    new: str


@router.post("/api/me/password")
def change_password(body: PasswordIn, response: Response, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            if not users.authenticate(con, u.username, body.current):
                raise UserError("La contraseña actual no es correcta.")
            users.set_password(con, u.id, body.new)
            token = users.create_session(con, u.id)
    except UserError as e:
        bad(e)
    set_session_cookie(response, token)
    return {"ok": True}


class FirstIn(BaseModel):
    username: str
    name: str
    password: str


@router.post("/api/me/first")
def first_login(body: FirstIn, response: Response, u: User = Depends(current_user)):
    """Primera entrada con la contraseña provisional: usuario, nombre y contraseña propios."""
    if not u.must_change:
        raise HTTPException(409, "Tu contraseña ya es la tuya; cámbiala en «Contraseña».")
    try:
        with db.tx() as con:
            users.rename(con, u.id, body.username, body.name)
            users.set_password(con, u.id, body.password)
            token = users.create_session(con, u.id)
    except UserError as e:
        bad(e)
    set_session_cookie(response, token)
    return {"ok": True}


class EmailIn(BaseModel):
    email: str


@router.post("/api/me/email")
def change_email(body: EmailIn, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            users.set_email(con, u.id, body.email)
    except UserError as e:
        bad(e)
    return {"ok": True}


class NameIn(BaseModel):
    name: str


@router.post("/api/me/name")
def change_name(body: NameIn, u: User = Depends(current_user)):
    name = body.name.strip()
    if not name or len(name) > 80:
        raise HTTPException(400, "Escribe tu nombre (hasta 80 caracteres).")
    with db.tx() as con:
        con.execute("UPDATE users SET name=? WHERE id=?", (name, u.id))
    return {"ok": True}


class LangIn(BaseModel):
    lang: str


@router.post("/api/me/lang")
def change_lang(body: LangIn, response: Response, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            lang = users.set_lang(con, u.id, body.lang)
    except UserError as e:
        bad(e)
    response.set_cookie(i18n.COOKIE, lang, max_age=5 * 365 * 86400, samesite="lax")
    from app.help import translate
    translate.prewarm([lang])   # the help in the new language, ready when it is opened
    return {"ok": True, "lang": lang}


# ---------- administración de cuentas ----------

class InviteIn(BaseModel):
    note: str = ""


@router.post("/api/admin/invites")
def admin_invite(body: InviteIn, request: Request, u: User = Depends(admin_user)):
    with db.tx() as con:
        code = users.create_invite(con, u.id, body.note)
    return {"code": code, "url": f"{base_url(request)}/registro?c={code}", "days": config.settings.invite_days}


@router.get("/api/admin/invites")
def admin_invites(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"invites": users.list_invites(con)}


@router.get("/api/admin/users")
def admin_users(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"users": [{**x.public(), "sheetId": x.sheet_id or "", "appsScriptUrl": x.apps_script_url or "",
                           "partnerId": x.partner_id, "sync": workbook.meta(x.id)} for x in users.list_users(con)]}
