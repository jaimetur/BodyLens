"""Public legal pages (/privacy, /terms, /delete-account) and the legal details of this server (Administration).

The texts are help documents (help/en/legal/<doc>.md, translated like the rest of the help); who is responsible for
the data and how to contact them are settings of each server, shown above the text."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.accounts.users import User, UserError, clean_email
from app.core import db
from app.core.deps import admin_user, base_url

router = APIRouter()

PAGES = ("privacy", "terms", "delete-account")


def info(request: Request | None = None) -> dict:
    s = db.get_setting("legal", {}) or {}
    return {"controller": s.get("controller", ""), "email": s.get("email", ""), "address": s.get("address", ""),
            "server": base_url(request) if request is not None else ""}


@router.get("/api/legal")
def public_info(request: Request):
    """Who is responsible for the data on this server and how to contact them (shown on the legal pages)."""
    return info(request)


class LegalIn(BaseModel):
    controller: str = ""
    email: str = ""
    address: str = ""


@router.get("/api/admin/legal")
def get_legal(request: Request, u: User = Depends(admin_user)):
    return info(request)


@router.put("/api/admin/legal")
def put_legal(body: LegalIn, request: Request, u: User = Depends(admin_user)):
    email = body.email.strip()
    if email:
        try:
            email = clean_email(email)
        except UserError:
            raise HTTPException(400, "El correo de contacto no es válido.")
    new = {"controller": body.controller.strip()[:120], "email": email, "address": body.address.strip()[:200]}
    with db.tx() as con:
        db.set_setting(con, "legal", new)
    return info(request)


def _page_route(doc: str):
    def page(request: Request) -> HTMLResponse:
        from app.web.routes import _page
        return _page("legal", "legal.html", request=request)
    page.__name__ = "legal_" + doc.replace("-", "_")
    return page


for _doc in PAGES:
    router.add_api_route("/" + _doc, _page_route(_doc), methods=["GET"], response_class=HTMLResponse)
