"""Rutas de sincronización: el libro XLSX de la cuenta, sincronizar ya, estado y fuentes (administración)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError
from app.core import db
from app.core.deps import admin_user, bad, current_user
from app.sync import service, workbook

router = APIRouter()


@router.get("/api/workbook/meta")
def workbook_meta(u: User = Depends(current_user)):
    return workbook.meta(u.id)


@router.get("/api/workbook.xlsx")
def workbook_file(request: Request, u: User = Depends(current_user)):
    m = workbook.meta(u.id)
    p = workbook.path_for(u.id)
    if not m["etag"] or not p.exists():
        raise HTTPException(404, "Todavía no hay datos.")
    etag = f'"{m["etag"]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(p, media_type=workbook.XLSX_MIME, headers={"ETag": etag, "Cache-Control": "no-cache"})


@router.post("/api/sync")
async def sync_now(u: User = Depends(current_user)):
    return await service.sync_user(u)


@router.get("/api/status")
def status(u: User = Depends(current_user)):
    return {"sources": {"sheet": bool(u.sheet_id), "appsScript": bool(u.apps_script_url)}, **workbook.meta(u.id)}


class BridgeIn(BaseModel):
    sheetId: str = ""
    appsScriptUrl: str = ""


@router.put("/api/admin/users/{user_id}/bridge")
def admin_bridge(user_id: int, body: BridgeIn, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            if not users.get_user(con, user_id):
                raise HTTPException(404, "No existe esa cuenta.")
            users.update_bridge(con, user_id, body.sheetId, body.appsScriptUrl)
    except UserError as e:
        bad(e)
    return {"ok": True}
