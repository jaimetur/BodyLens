"""Rutas de correo: correo de prueba para comprobar la configuración SMTP."""
from __future__ import annotations

import asyncio
from html import escape as esc

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.accounts.users import User, UserError, clean_email
from app.core.deps import admin_user, bad, base_url
from app.mail import mailer

router = APIRouter()


class TestMailIn(BaseModel):
    to: str = ""


@router.post("/api/admin/test-email")
async def admin_test_email(body: TestMailIn, request: Request, u: User = Depends(admin_user)):
    try:
        to = clean_email(body.to) or u.email
    except UserError as e:
        bad(e)
    if not to:
        raise HTTPException(400, "Pon tu correo en «Tu cuenta» o escribe a quién enviarlo.")
    try:
        # a real-looking notice (a one-line "if you read this, it works" message is what spam filters distrust)
        first = esc((u.name or u.username).split()[0])
        await asyncio.to_thread(mailer.send, [to], "Comprobación del correo", mailer.page("Comprobación del correo", [
            f"Hola {first},",
            "este es el correo de comprobación que has pedido desde Administración → Correo. Si te ha llegado, BodyLens "
            "ya puede enviarte los avisos de tu cuenta: peticiones de acceso, invitaciones, contraseñas e invitaciones "
            "de pareja.",
            "Si lo encuentras en la carpeta de spam, márcalo como «No es spam» y añade esta dirección a tus contactos: "
            "así los próximos avisos llegarán a la bandeja de entrada.",
        ], link=("Abrir BodyLens", f"{base_url(request)}/")))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    return {"ok": True, "to": to}
