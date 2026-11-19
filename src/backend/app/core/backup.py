"""Copia de seguridad diaria de la base de datos: <DATA_DIR>/backups/bodylens-AAAA-MM-DD.db, se conservan las últimas
BACKUP_KEEP (30). Se hace con la API de copia de SQLite, así que es coherente aunque el servidor esté escribiendo."""
from __future__ import annotations

import asyncio
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core import config

log = logging.getLogger("bodylens.backup")
TZ = ZoneInfo("Europe/Madrid")
NAME = re.compile(r"^bodylens-(\d{4}-\d{2}-\d{2})\.db$")


def folder() -> Path:
    return config.settings.data_dir / "backups"


def keep() -> int:
    try:
        return max(1, int(os.environ.get("BACKUP_KEEP", "30")))
    except ValueError:
        return 30


def make(day: str | None = None) -> Path:
    """Hace la copia del día (si ya existe, la rehace) y borra las que sobran."""
    day = day or datetime.now(TZ).strftime("%Y-%m-%d")
    d = folder()
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"bodylens-{day}.db"
    tmp = dest.with_suffix(".tmp")
    src = sqlite3.connect(config.settings.db_path)
    out = sqlite3.connect(tmp)
    try:
        src.backup(out)
    finally:
        out.close()
        src.close()
    os.replace(tmp, dest)
    prune()
    return dest


def prune() -> list[str]:
    files = sorted(p for p in folder().iterdir() if NAME.match(p.name))
    old = files[:-keep()] if len(files) > keep() else []
    for p in old:
        p.unlink(missing_ok=True)
    return [p.name for p in old]


def listing() -> list[dict]:
    if not folder().exists():
        return []
    return [{"name": p.name, "size": p.stat().st_size} for p in sorted(folder().iterdir(), reverse=True) if NAME.match(p.name)]


async def loop() -> None:
    """Una copia al arrancar si hoy no hay, y después cada día a las 03:30 (hora de Madrid)."""
    await asyncio.sleep(60)
    while True:
        try:
            today = datetime.now(TZ).strftime("%Y-%m-%d")
            if not (folder() / f"bodylens-{today}.db").exists():
                p = await asyncio.to_thread(make, today)
                log.info("copia de seguridad: %s", p.name)
        except Exception:
            log.exception("la copia de seguridad falló")
        now = datetime.now(TZ)
        nxt = now.replace(hour=3, minute=30, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(days=1)
        await asyncio.sleep((nxt - now).total_seconds())
