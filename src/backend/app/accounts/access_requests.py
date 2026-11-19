"""Peticiones de acceso desde la pantalla de entrar: la cuenta se crea inactiva, la administración recibe un correo
y la aprueba o la rechaza; la persona recibe un correo en los dos casos."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError, clean_email
from app.core import db, i18n
from app.core.deps import admin_user, bad, base_url, client_ip
from app.core.security import Throttle
from app.mail import mailer
from app.web.page import esc

router = APIRouter()
request_throttle = Throttle(limit=5, window=3600)


class AccessRequestIn(BaseModel):
    name: str
    email: str
    username: str
    password: str
    note: str = ""
    website: str = ""
    lang: str = ""  # language of the interface chosen in the form (else the one of the page)  # campo trampa: las personas no lo ven ni lo rellenan


@router.post("/api/access-requests", status_code=201)
def access_request(body: AccessRequestIn, request: Request):
    """Crea la cuenta inactiva y avisa por correo a la administración, que la aprueba en «Tu cuenta»."""
    ip = client_ip(request)
    if request_throttle.blocked(f"ip:{ip}"):
        raise HTTPException(429, "Has enviado demasiadas peticiones. Prueba más tarde.")
    request_throttle.fail(f"ip:{ip}")
    if body.website:
        return {"ok": True}
    try:
        with db.tx() as con:
            email = clean_email(body.email, required=True)
            if users.email_taken(con, email):
                raise UserError("Ya hay una cuenta o una petición con ese correo.")
            u = users.create_user(con, body.username, body.name, body.password, email=email, active=False,
                                  request_note=body.note)
            u.lang = users.set_lang(con, u.id, i18n.clean(body.lang) or i18n.request_lang(request))
            admins = users.admin_emails(con)
    except UserError as e:
        bad(e)
    note = f"<br>Mensaje: <i>{esc(u.request_note)}</i>" if u.request_note else ""
    mailer.send_later(admins, f"Petición de acceso de {u.name}", mailer.page("Nueva petición de acceso", [
        f"<b>{esc(u.name)}</b> ({esc(u.email)}) pide una cuenta de BodyLens con el usuario <b>{esc(u.username)}</b>.{note}",
        "Apruébala o recházala en «Tu cuenta» → Administración → Peticiones de acceso.",
    ], link=("Revisar la petición", f"{base_url(request)}/cuenta#peticiones")), reply_to=u.email)
    mailer.send_later([u.email], "Hemos recibido tu petición", mailer.page("Hemos recibido tu petición", [
        f"Hola {esc(u.name.split()[0])},",
        f"tu petición de una cuenta de BodyLens con el usuario <b>{esc(u.username)}</b> está pendiente de aprobación. "
        "Te escribiremos cuando esté activa.",
    ]))
    return {"ok": True}


@router.get("/api/admin/access-requests")
def admin_access_requests(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"requests": [{"id": x.id, "username": x.username, "name": x.name, "email": x.email or "",
                              "note": x.request_note or "", "requestedAt": x.requested_at}
                             for x in users.list_users(con, active=False)],
                "mail": mailer.public_settings()}


@router.post("/api/admin/access-requests/{user_id}/approve")
def admin_approve(user_id: int, request: Request, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            x = users.approve(con, user_id)
    except UserError as e:
        bad(e, 409)
    if x.email:
        mailer.send_later([x.email], "Tu cuenta está activa", mailer.page("Tu cuenta está activa", [
            f"Hola {esc(x.name.split()[0])},",
            f"{esc(u.name)} ha aprobado tu cuenta de BodyLens. Entra con el usuario <b>{esc(x.username)}</b> y la "
            "contraseña que elegiste.",
            "Dentro, en «Tu cuenta» puedes importar tus datos y, si quieres, unir tu cuenta con la de tu pareja.",
        ], link=("Entrar en BodyLens", f"{base_url(request)}/login")))
    return {"ok": True}


@router.post("/api/admin/access-requests/{user_id}/reject")
def admin_reject(user_id: int, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            x = users.reject(con, user_id)
    except UserError as e:
        bad(e, 409)
    if x.email:
        mailer.send_later([x.email], "Tu petición de acceso", mailer.page("Tu petición de acceso", [
            f"Hola {esc(x.name.split()[0])},",
            "tu petición de una cuenta de BodyLens no se ha aprobado. Si crees que es un error, responde a este correo.",
        ]), reply_to=u.email)
    return {"ok": True}
