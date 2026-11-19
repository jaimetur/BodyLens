"""Rutas del panel de Administración (/admin): cuentas y configuración del correo.
Las invitaciones, peticiones de acceso, fuentes y correo de prueba tienen sus rutas en sus módulos."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError, clean_email
from app.core import db
from app.core.deps import admin_user, bad, base_url
from app.data import docstore
from app.mail import mailer
from app.sync import workbook
from app.web.page import esc

router = APIRouter()


def _user_row(con, x: User) -> dict:
    r = con.execute("SELECT created_at, requested_at FROM users WHERE id=?", (x.id,)).fetchone()
    partner = users.get_user(con, x.partner_id) if x.partner_id else None
    return {**x.public(), "active": x.active, "createdAt": r["created_at"], "requestedAt": r["requested_at"],
            "partner": partner.username if partner else None, "sheetId": x.sheet_id or "",
            "appsScriptUrl": x.apps_script_url or "", "sync": workbook.meta(x.id)}


@router.get("/api/admin/accounts")
def accounts(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"users": [_user_row(con, x) for x in users.list_users(con, active=None)], "me": u.id}


class AccountIn(BaseModel):
    name: str | None = None
    email: str | None = None
    isAdmin: bool | None = None
    active: bool | None = None


@router.patch("/api/admin/accounts/{user_id}")
def edit_account(user_id: int, body: AccountIn, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            x = users.get_user(con, user_id)
            if not x:
                raise HTTPException(404, "No existe esa cuenta.")
            if user_id == u.id and (body.isAdmin is False or body.active is False):
                raise UserError("No puedes quitarte a ti mismo la administración ni desactivar tu cuenta.")
            if body.name is not None:
                name = body.name.strip()
                if not name or len(name) > 80:
                    raise UserError("El nombre tiene que tener de 1 a 80 caracteres.")
                con.execute("UPDATE users SET name=? WHERE id=?", (name, user_id))
            if body.email is not None:
                users.set_email(con, user_id, body.email)
            if body.isAdmin is not None:
                con.execute("UPDATE users SET is_admin=? WHERE id=?", (int(body.isAdmin), user_id))
            if body.active is not None:
                con.execute("UPDATE users SET active=?, requested_at=CASE WHEN ?=1 THEN NULL ELSE requested_at END WHERE id=?",
                            (int(body.active), int(body.active), user_id))
                if not body.active:
                    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    except UserError as e:
        bad(e)
    return {"ok": True}


class ResetIn(BaseModel):
    email: bool = True


@router.post("/api/admin/accounts/{user_id}/password")
def reset_password(user_id: int, body: ResetIn, request: Request, u: User = Depends(admin_user)):
    """Pone una contraseña provisional (se pide cambiarla al entrar) y la devuelve una sola vez."""
    temp = secrets.token_urlsafe(6)
    with db.tx() as con:
        x = users.get_user(con, user_id)
        if not x:
            raise HTTPException(404, "No existe esa cuenta.")
        users.set_password(con, user_id, temp)
        con.execute("UPDATE users SET must_change=1 WHERE id=?", (user_id,))
    sent = False
    if body.email and x.email and mailer.settings()["configured"]:
        mailer.send_later([x.email], "Tu contraseña provisional", mailer.page("Tu contraseña provisional", [
            f"Hola {esc(x.name.split()[0])},",
            f"{esc(u.name)} ha restablecido la contraseña de tu cuenta <b>{esc(x.username)}</b>. "
            f"Entra con esta contraseña provisional y elige la tuya: <b>{esc(temp)}</b>",
        ], link=("Entrar en BodyLens", f"{base_url(request)}/login")))
        sent = True
    return {"ok": True, "password": temp, "emailed": sent}


@router.delete("/api/admin/accounts/{user_id}")
def delete_account(user_id: int, u: User = Depends(admin_user)):
    """Borra la cuenta y todos sus datos (si tenía pareja, se separan antes: la pareja conserva su copia)."""
    if user_id == u.id:
        raise HTTPException(400, "No puedes borrar tu propia cuenta.")
    with db.tx() as con:
        x = users.get_user(con, user_id)
        if not x:
            raise HTTPException(404, "No existe esa cuenta.")
        if x.partner_id:
            docstore.unlink_partner(con, x)
        con.execute("DELETE FROM invites WHERE used_by=?", (user_id,))
        con.execute("UPDATE invites SET created_by=NULL WHERE created_by=?", (user_id,))
        con.execute("DELETE FROM users WHERE id=?", (user_id,))
    try:
        p = workbook.path_for(user_id)
        if p.exists():
            p.unlink()
    except OSError:
        pass
    return {"ok": True}


# ---------- correo ----------

class MailIn(BaseModel):
    host: str = ""
    port: int | None = None
    security: str = "ssl"
    username: str = ""
    password: str = ""          # vacío = conservar la guardada
    from_address: str = ""
    from_name: str = "BodyLens"


@router.get("/api/admin/mail")
def get_mail(u: User = Depends(admin_user)):
    return mailer.public_settings()


@router.put("/api/admin/mail")
def put_mail(body: MailIn, u: User = Depends(admin_user)):
    if body.security not in ("ssl", "starttls", "none"):
        raise HTTPException(400, "Seguridad: ssl, starttls o none.")
    try:
        if body.from_address:
            clean_email(body.from_address)
    except UserError:
        raise HTTPException(400, "El remitente no es un correo válido.")
    stored = db.get_setting("mail", {}) or {}
    new = {"host": body.host.strip(), "port": body.port, "security": body.security, "username": body.username.strip(),
           "from_address": body.from_address.strip(), "from_name": body.from_name.strip() or "BodyLens",
           "password": body.password if body.password else stored.get("password", "")}
    with db.tx() as con:
        db.set_setting(con, "mail", new)
    return mailer.public_settings()
