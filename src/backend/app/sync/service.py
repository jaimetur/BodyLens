"""Sincronización de un usuario (tarea periódica y botón «Actualizar») y el planificador."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

import httpx

from app.accounts.users import User, get_user, list_users
from app.core import config, db
from app.sync import google_bridge, workbook

log = logging.getLogger("bodylens.sync")
_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


def _server_mode(user: User) -> bool:
    from app.sheets import service as sheets
    return sheets.source_of(user.id) == "server"


def has_sources(user: User) -> bool:
    if _server_mode(user):
        from app.sources import withings
        return bool(withings.load_tokens(user.id))
    return bool(user.sheet_id or user.apps_script_url)


async def sync_server(user: User, client: httpx.AsyncClient | None = None) -> dict:
    """Fase 2: Withings directo (si está conectado) y libro regenerado desde las tablas."""
    from app.sheets import service as sheets
    from app.sources import withings
    if not withings.load_tokens(user.id) and not db.get_setting(f"hae_last:{user.id}"):
        return {"ok": False, "message": "You have not connected any data source yet: connect them in Your account → Data sources."}
    lock = _locks[user.id]
    async with lock:
        result: dict = {"ok": True}
        if withings.load_tokens(user.id):
            r = await withings.sync(user.id, client)
            with db.tx() as con:
                db.set_setting(con, f"withings_last:{user.id}", {"at": db.now_iso(), **r})
            result["withings"] = r
            if r.get("errores"):
                result["ok"] = False
                result["error"] = "; ".join(r["errores"])
        changed = await sheets.rebuild_async(user.id)
        result["workbook"] = {"changed": changed}
        n = (result.get("withings") or {}).get("pesadas", 0)
        result["message"] = result.get("error") or (
            (f"{n} {'pesada nueva' if n == 1 else 'pesadas nuevas'} de Withings. " if n else "") +
            ("Datos al día." if not changed else "Datos actualizados."))
        workbook.record_sync(user.id, result)
        return result


async def sync_user(user: User, client: httpx.AsyncClient | None = None) -> dict:
    """Sincroniza la cuenta: fase 2 (Withings directo) o fase 1 (Apps Script + hoja). Devuelve un resumen."""
    if _server_mode(user):
        return await sync_server(user, client)
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
