"""El libro XLSX que lee la página, uno por usuario (fase 1: la hoja de Google exportada)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from app.core import config, db

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def path_for(user_id: int) -> Path:
    return config.settings.user_dir(user_id) / "workbook.xlsx"


def meta(user_id: int) -> dict:
    with db.ro() as con:
        r = con.execute("SELECT * FROM user_state WHERE user_id=?", (user_id,)).fetchone()
    if not r:
        return {"etag": None, "updatedAt": None, "lastSync": None, "lastSyncResult": None}
    return {
        "etag": r["workbook_etag"] if path_for(user_id).exists() else None,
        "updatedAt": r["workbook_updated_at"],
        "lastSync": r["last_sync"],
        "lastSyncResult": json.loads(r["last_sync_result"]) if r["last_sync_result"] else None,
    }


def _ensure_state(con, user_id: int) -> None:
    con.execute("INSERT INTO user_state(user_id) VALUES(?) ON CONFLICT(user_id) DO NOTHING", (user_id,))


def save(user_id: int, content: bytes) -> tuple[bool, str]:
    """Guarda el libro si ha cambiado. Devuelve (cambiado, etag)."""
    if not content.startswith(b"PK"):
        raise ValueError("La exportación no es un XLSX.")
    etag = hashlib.sha256(content).hexdigest()[:32]
    p = path_for(user_id)
    with db.tx() as con:
        _ensure_state(con, user_id)
        r = con.execute("SELECT workbook_etag FROM user_state WHERE user_id=?", (user_id,)).fetchone()
        if r["workbook_etag"] == etag and p.exists():
            return False, etag
        tmp = p.with_suffix(".tmp")
        tmp.write_bytes(content)
        os.replace(tmp, p)
        con.execute("UPDATE user_state SET workbook_etag=?, workbook_updated_at=? WHERE user_id=?",
                    (etag, db.now_iso(), user_id))
    return True, etag


def record_sync(user_id: int, result: dict) -> None:
    with db.tx() as con:
        _ensure_state(con, user_id)
        con.execute("UPDATE user_state SET last_sync=?, last_sync_result=? WHERE user_id=?",
                    (db.now_iso(), json.dumps(result, ensure_ascii=False), user_id))
