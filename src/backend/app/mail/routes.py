"""Rutas de correo: correo de prueba para comprobar la configuración SMTP."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.accounts.users import User, UserError, clean_email
from app.core.deps import admin_user, bad
from app.mail import mailer

router = APIRouter()


class TestMailIn(BaseModel):
    to: str = ""


@router.post("/api/admin/test-email")
async def admin_test_email(body: TestMailIn, u: User = Depends(admin_user)):
    try:
        to = clean_email(body.to) or u.email
    except UserError as e:
        bad(e)
    if not to:
        raise HTTPException(400, "Pon tu correo en «Tu cuenta» o escribe a quién enviarlo.")
    try:
        await asyncio.to_thread(mailer.send, [to], "Correo de prueba", mailer.page("Correo de prueba", [
            "Si lees esto, el correo de BodyLens funciona."]))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    return {"ok": True, "to": to}
