"""Sincronización de un usuario (tarea periódica y botón «Actualizar») y el planificador."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

import httpx

from app import config, db, google_bridge, workbook
from app.users import User, get_user, list_users

log = logging.getLogger("bodylens.sync")
_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


def has_sources(user: User) -> bool:
    return bool(user.sheet_id or user.apps_script_url)


async def sync_user(user: User, client: httpx.AsyncClient | None = None) -> dict:
    """Fase 1: dispara el Apps Script y exporta la hoja. Devuelve un resumen para la app."""
    if not has_sources(user):
        return {"ok": False, "message": "Tu cuenta no tiene fuentes de datos configuradas todavía."}
    lock = _locks[user.id]
    if lock.locked():
        async with lock:  # ya había una en marcha: se espera a que acabe y se devuelve su resultado
            return workbook.meta(user.id).get("lastSyncResult") or {"ok": True, "message": "Sincronizado."}
    async with lock:
        own = client is None
        client = client or httpx.AsyncClient()
        result: dict = {"ok": True}
        try:
            if user.apps_script_url:
                result["appsScript"] = await google_bridge.trigger_apps_script(client, user.apps_script_url)
            if user.sheet_id:
                try:
                    content = await google_bridge.export_sheet(client, user.sheet_id)
                    changed, etag = workbook.save(user.id, content)
                    result["workbook"] = {"changed": changed, "etag": etag}
                except (google_bridge.BridgeError, httpx.HTTPError, ValueError) as e:
                    result["ok"] = False
                    result["error"] = str(e) if isinstance(e, (google_bridge.BridgeError, ValueError)) else \
                        f"No se pudo descargar la hoja ({type(e).__name__})."
            if result.get("appsScript") and not result["appsScript"]["ok"]:
                result["ok"] = False
                result.setdefault("error", result["appsScript"]["error"])
            result["message"] = _summary(result)
        finally:
            if own:
                await client.aclose()
        workbook.record_sync(user.id, result)
        return result


def _summary(r: dict) -> str:
    if not r["ok"]:
        return r.get("error") or "No se pudo sincronizar."
    wb = r.get("workbook")
    if wb is None:
        return "Sincronización pedida a la hoja."
    return "Datos nuevos de la báscula y Apple Salud." if wb["changed"] else "Sin datos nuevos: todo al día."


async def sync_all() -> None:
    with db.ro() as con:
        users = [u for u in list_users(con) if has_sources(u)]
    async with httpx.AsyncClient() as client:
        for u in users:
            try:
                r = await sync_user(u, client)
                log.info("sync usuario=%s ok=%s %s", u.id, r.get("ok"), r.get("message"))
            except Exception:  # una cuenta con problemas no para a las demás
                log.exception("sync usuario=%s falló", u.id)


async def scheduler_loop() -> None:
    interval = max(1, config.settings.sync_interval_min) * 60
    await asyncio.sleep(20)  # deja arrancar el servidor
    while True:
        try:
            await sync_all()
        except Exception:
            log.exception("la tarea periódica falló")
        await asyncio.sleep(interval)


def reload_user(user_id: int) -> User | None:
    with db.ro() as con:
        return get_user(con, user_id)
