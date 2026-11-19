"""Libro de datos generado en el servidor (fase 2) y paso de una cuenta de la hoja de Google al servidor.

Cada cuenta tiene un origen de datos:
- «sheet»: el libro es la hoja de Google exportada (fase 1, puente).
- «server»: las pestañas viven en las tablas del servidor (Withings y Apple Salud escriben ahí) y el libro se
  genera desde ellas cuando cambian.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core import db
from app.sheets import store, xlsx_io
from app.sync import google_bridge, workbook

log = logging.getLogger("bodylens.sheets")


def source_of(user_id: int) -> str:
    with db.ro() as con:
        r = con.execute("SELECT data_source FROM users WHERE id=?", (user_id,)).fetchone()
    return (r["data_source"] if r else None) or "server"


def set_source(con, user_id: int, source: str) -> None:
    con.execute("UPDATE users SET data_source=? WHERE id=?", (source, user_id))


def rebuild(user_id: int, force: bool = False) -> bool:
    """Genera el libro desde las tablas si han cambiado. Devuelve si el libro ha cambiado."""
    if not (store.take_dirty(user_id) or force):
        return False
    with db.ro() as con:
        content = xlsx_io.build_xlsx(con, user_id)
    changed, _ = workbook.save(user_id, content)
    return changed


async def rebuild_async(user_id: int, force: bool = False) -> bool:
    return await asyncio.to_thread(rebuild, user_id, force)


def import_sheet(user_id: int, content: bytes) -> dict:
    with db.tx() as con:
        counts = xlsx_io.import_xlsx(con, user_id, content)
    rebuild(user_id, force=True)
    return counts


async def switch_to_server(user, client: httpx.AsyncClient | None = None) -> dict:
    """Trae la última versión de la hoja de la cuenta a las tablas y pasa la cuenta a «server»."""
    if not user.sheet_id:
        raise RuntimeError("La cuenta no tiene hoja de Google configurada.")
    own = client is None
    client = client or httpx.AsyncClient()
    try:
        if user.apps_script_url:
            await google_bridge.trigger_apps_script(client, user.apps_script_url)
        content = await google_bridge.export_sheet(client, user.sheet_id)
    finally:
        if own:
            await client.aclose()
    counts = await asyncio.to_thread(import_sheet, user.id, content)
    with db.tx() as con:
        set_source(con, user.id, "server")
    log.info("cuenta %s pasa a datos en el servidor: %s", user.id, counts)
    return counts
