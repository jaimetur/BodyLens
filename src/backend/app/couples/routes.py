"""Rutas de pareja: pedir, aceptar, rechazar y separar. Lo que se comparte lo resuelve app.data.docstore."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User
from app.core import db
from app.core.deps import bad, current_user
from app.data import docstore

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


@router.post("/api/partner/request")
def partner_request(body: PartnerIn, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        if not other or other.id == u.id or not other.active:
            raise HTTPException(404, "No hay ninguna otra cuenta con ese usuario.")
        if u.partner_id or other.partner_id:
            raise HTTPException(409, "Alguna de las dos cuentas ya está unida a otra.")
        # si la otra persona ya lo había pedido, se unen directamente
        prev = con.execute("SELECT since FROM partner_requests WHERE from_id=? AND to_id=?", (other.id, u.id)).fetchone()
        if prev:
            docstore.link_partners(con, u, other, _valid_since(body.since) or prev["since"])
            _clear_requests(con, u.id, other.id)
            return {"ok": True, "linked": True}
        con.execute("INSERT INTO partner_requests(from_id, to_id, since, created_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(from_id, to_id) DO UPDATE SET since=excluded.since",
                    (u.id, other.id, _valid_since(body.since), db.now_iso()))
    return {"ok": True, "linked": False}


@router.post("/api/partner/accept")
def partner_accept(body: PartnerIn, u: User = Depends(current_user)):
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
