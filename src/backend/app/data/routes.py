"""Rutas de datos: la colección de documentos de cada cuenta (el «db» de window.claude) e importar copias."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.accounts.users import User
from app.core import db
from app.core.deps import bad, current_user, json_body
from app.data import docstore, importer

router = APIRouter()


@router.get("/api/docs/{collection}")
def docs_list(collection: str, since: int | None = None, u: User = Depends(current_user)):
    try:
        with db.ro() as con:
            return docstore.list_docs(con, u, collection, since)
    except docstore.DocError as e:
        bad(e)


@router.get("/api/docs/{collection}/{doc_id}")
def docs_get(collection: str, doc_id: str, u: User = Depends(current_user)):
    try:
        with db.ro() as con:
            d = docstore.get_doc(con, u, collection, doc_id)
    except docstore.DocError as e:
        bad(e)
    if d is None:
        raise HTTPException(404, "No existe.")
    return d


@router.put("/api/docs/{collection}/{doc_id}")
async def docs_put(collection: str, doc_id: str, request: Request, u: User = Depends(current_user)):
    data = await json_body(request)
    try:
        with db.tx() as con:
            return {"rev": docstore.put_doc(con, u, collection, doc_id, data)}
    except docstore.DocError as e:
        bad(e)


@router.patch("/api/docs/{collection}/{doc_id}")
async def docs_patch(collection: str, doc_id: str, request: Request, u: User = Depends(current_user)):
    patch = await json_body(request)
    try:
        with db.tx() as con:
            rev = docstore.update_doc(con, u, collection, doc_id, patch)
            return {"rev": rev, "data": docstore.get_doc(con, u, collection, doc_id)["data"]}
    except docstore.DocError as e:
        bad(e)


@router.delete("/api/docs/{collection}/{doc_id}")
def docs_delete(collection: str, doc_id: str, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            return {"rev": docstore.delete_doc(con, u, collection, doc_id)}
    except docstore.DocError as e:
        bad(e)


@router.post("/api/import")
async def import_copy(request: Request, u: User = Depends(current_user)):
    """Importa en la cuenta una copia de BodyLens: snap.json o la «Copia completa (JSON)» de Ajustes.
    Cuerpo: {copy: <contenido del fichero>, profile: null | "<id del perfil de la copia>", withProfiles: bool}"""
    body = await json_body(request)
    if not isinstance(body, dict):
        raise HTTPException(400, "Petición no válida.")
    try:
        with db.tx() as con:
            n = importer.import_copy(con, u, body.get("copy"), body.get("profile") or None, bool(body.get("withProfiles")))
    except (importer.ImportError_, docstore.DocError) as e:
        bad(e)
    return {"ok": True, "documents": n}
