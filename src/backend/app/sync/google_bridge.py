"""Fase 1: puente con Google. Dispara el Apps Script y exporta la hoja a XLSX con una cuenta de servicio."""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import httpx

from app.core import config

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_creds = None
_creds_lock = threading.Lock()


class BridgeError(RuntimeError):
    pass


def _token_sync() -> str:
    """Token de acceso de la cuenta de servicio (se renueva solo cuando caduca)."""
    global _creds
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    path = config.settings.google_sa_json
    if not path or not Path(path).is_file():
        raise BridgeError("Falta la cuenta de servicio de Google (GOOGLE_SERVICE_ACCOUNT_JSON).")
    with _creds_lock:
        if _creds is None:
            _creds = service_account.Credentials.from_service_account_file(path, scopes=[DRIVE_SCOPE])
        if not _creds.valid:
            _creds.refresh(Request())
        return _creds.token


async def drive_token() -> str:
    return await asyncio.to_thread(_token_sync)


async def trigger_apps_script(client: httpx.AsyncClient, url: str) -> dict:
    """GET a la aplicación web del Apps Script (?accion=sincronizar): trae Withings y rehace las últimas noches."""
    if "accion=" not in url:
        url += ("&" if "?" in url else "?") + "accion=sincronizar"
    try:
        r = await client.get(url, follow_redirects=True, timeout=180)
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"El Apps Script no responde ({type(e).__name__})."}
    if r.status_code >= 400:
        return {"ok": False, "error": f"El Apps Script respondió {r.status_code}."}
    return {"ok": True}


async def export_sheet(client: httpx.AsyncClient, sheet_id: str) -> bytes:
    token = await drive_token()
    r = await client.get(
        f"https://www.googleapis.com/drive/v3/files/{sheet_id}/export",
        params={"mimeType": XLSX_MIME},
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    if r.status_code == 404:
        raise BridgeError("No encuentro la hoja: compártela (lector) con el correo de la cuenta de servicio.")
    if r.status_code >= 400:
        raise BridgeError(f"Google Drive respondió {r.status_code} al exportar la hoja.")
    return r.content
