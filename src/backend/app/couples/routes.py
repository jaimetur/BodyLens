"""Rutas de pareja: pedir, aceptar, rechazar y separar. Lo que se comparte lo resuelve app.data.docstore."""
from __future__ import annotations

from datetime import date

from html import escape as esc

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User
from app.core import db
from app.core.deps import bad, base_url, current_user
from app.data import docstore
from app.mail import mailer

router = APIRouter()


class PartnerIn(BaseModel):
    username: str
    since: str | None = None


def _valid_since(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        raise HTTPException(400, "La fecha no es válida.")


def _clear_requests(con, a: int, b: int) -> None:
    con.execute("DELETE FROM partner_requests WHERE from_id IN (?,?) OR to_id IN (?,?)", (a, b, a, b))


def _first(name: str) -> str:
    return esc((name or "").split()[0] if name else "")


def _mail_invite(request: Request, u: User, other: User) -> None:
    """Invitation to the other person: they accept it in Tu cuenta → Cuenta → Pareja."""
    if other.email:
        mailer.send_later([other.email], f"{u.name} quiere unir su cuenta con la tuya", mailer.page("Invitación de pareja", [
            f"Hola {_first(other.name)},",
            f"<b>{esc(u.name)}</b> ({esc(u.username)}) quiere unir su cuenta de BodyLens con la tuya como pareja. Si la "
            "aceptas, los registros de Ciclo e intimidad se comparten: los veis y los editáis los dos. El resto sigue "
            "siendo de cada uno.",
            "Acéptala o recházala en «Tu cuenta» → Cuenta → Pareja.",
        ], link=("Ver la invitación", f"{base_url(request)}/#cuenta")), reply_to=u.email or None)


def _mail_linked(request: Request, to: User, other: User) -> None:
    if to.email:
        mailer.send_later([to.email], "Vuestras cuentas están unidas", mailer.page("Vuestras cuentas están unidas", [
            f"Hola {_first(to.name)},",
            f"<b>{esc(other.name)}</b> ha aceptado unir vuestras cuentas de BodyLens. Desde ahora compartís los "
            "registros de Ciclo e intimidad.",
        ], link=("Abrir BodyLens", f"{base_url(request)}/")))


@router.post("/api/partner/request")
def partner_request(body: PartnerIn, request: Request, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_login(con, body.username)
        if not other or other.id == u.id or not other.active:
            raise HTTPException(404, "No hay ninguna otra cuenta con ese usuario o correo. Revísalo o pídele a tu "
                                     "pareja que se cree una cuenta.")
        if u.partner_id or other.partner_id:
            raise HTTPException(409, "Alguna de las dos cuentas ya está unida a otra.")
        # si la otra persona ya lo había pedido, se unen directamente
        prev = con.execute("SELECT since FROM partner_requests WHERE from_id=? AND to_id=?", (other.id, u.id)).fetchone()
        if prev:
            docstore.link_partners(con, u, other, _valid_since(body.since) or prev["since"])
            _clear_requests(con, u.id, other.id)
            linked = True
        else:
            linked = False
            con.execute("INSERT INTO partner_requests(from_id, to_id, since, created_at) VALUES(?,?,?,?) "
                        "ON CONFLICT(from_id, to_id) DO UPDATE SET since=excluded.since",
                        (u.id, other.id, _valid_since(body.since), db.now_iso()))
    if linked:
        _mail_linked(request, other, u)
    else:
        _mail_invite(request, u, other)
    return {"ok": True, "linked": linked, "mailed": bool(other.email) and mailer.settings()["configured"]}


@router.post("/api/partner/accept")
def partner_accept(body: PartnerIn, request: Request, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        req = other and con.execute("SELECT since FROM partner_requests WHERE from_id=? AND to_id=?",
                                    (other.id, u.id)).fetchone()
        if not req:
            raise HTTPException(404, "Esa petición ya no existe.")
        try:
            docstore.link_partners(con, u, other, _valid_since(body.since) or req["since"])
        except docstore.DocError as e:
            bad(e, 409)
        _clear_requests(con, u.id, other.id)
    _mail_linked(request, other, u)
    return {"ok": True}


@router.post("/api/partner/reject")
def partner_reject(body: PartnerIn, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        if other:
            con.execute("DELETE FROM partner_requests WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
                        (other.id, u.id, u.id, other.id))
    return {"ok": True}


@router.post("/api/partner/unlink")
def partner_unlink(u: User = Depends(current_user)):
    with db.tx() as con:
        docstore.unlink_partner(con, u)
    return {"ok": True}
