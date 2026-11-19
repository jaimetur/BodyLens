"""SQLite: conexión, esquema y contador global de revisiones."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  name TEXT NOT NULL,
  pw_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0,
  partner_id INTEGER REFERENCES users(id),
  partner_since TEXT,
  sheet_id TEXT,
  apps_script_url TEXT,
  must_change INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invites (
  code_hash TEXT PRIMARY KEY,
  created_by INTEGER REFERENCES users(id),
  note TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_by INTEGER REFERENCES users(id),
  used_at TEXT
);
CREATE TABLE IF NOT EXISTS partner_requests (
  from_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  to_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  since TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (from_id, to_id)
);
-- espejo de la colección del artefacto («bascula»), un espacio por usuario; data NULL = borrado (para el sondeo)
CREATE TABLE IF NOT EXISTS docs (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  collection TEXT NOT NULL,
  id TEXT NOT NULL,
  data TEXT,
  rev INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (user_id, collection, id)
);
CREATE INDEX IF NOT EXISTS docs_rev ON docs(user_id, collection, rev);
-- datos que comparte una pareja (ciclo e intimidad): clave «<id menor>-<id mayor>»
CREATE TABLE IF NOT EXISTS shared_docs (
  couple TEXT NOT NULL,
  id TEXT NOT NULL,
  data TEXT NOT NULL,
  rev INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (couple, id)
);
CREATE TABLE IF NOT EXISTS user_state (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  workbook_etag TEXT,
  workbook_updated_at TEXT,
  last_sync TEXT,
  last_sync_result TEXT
);
CREATE TABLE IF NOT EXISTS counters (
  name TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    path = config.settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=30000")
    return con


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """Transacción de escritura (BEGIN IMMEDIATE: una a la vez)."""
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        yield con
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


@contextmanager
def ro() -> Iterator[sqlite3.Connection]:
    con = connect()
    try:
        yield con
    finally:
        con.close()


def _migrate(con: sqlite3.Connection) -> None:
    """Columnas añadidas después de crear la base (las bases ya desplegadas no las tienen)."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
    if "must_change" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN must_change INTEGER NOT NULL DEFAULT 0")


def init_db() -> None:
    con = connect()
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
        _migrate(con)
    finally:
        con.close()


def fix_ownership() -> None:
    """Las órdenes de administración se lanzan con `docker exec` como root: la carpeta de datos vuelve al usuario
    con el que corre el servidor (PUID:PGID) para que pueda seguir escribiendo."""
    import os

    if not hasattr(os, "geteuid") or os.geteuid() != 0 or "PUID" not in os.environ:
        return
    uid, gid = int(os.environ["PUID"]), int(os.environ.get("PGID", os.environ["PUID"]))
    for root, dirs, files in os.walk(config.settings.data_dir):
        for name in [root, *(os.path.join(root, x) for x in dirs + files)]:
            try:
                os.chown(name, uid, gid)
            except OSError:
                pass


def next_rev(con: sqlite3.Connection) -> int:
    con.execute("INSERT INTO counters(name, value) VALUES('rev', 0) ON CONFLICT(name) DO NOTHING")
    con.execute("UPDATE counters SET value = value + 1 WHERE name='rev'")
    return con.execute("SELECT value FROM counters WHERE name='rev'").fetchone()[0]


def current_rev(con: sqlite3.Connection) -> int:
    row = con.execute("SELECT value FROM counters WHERE name='rev'").fetchone()
    return row[0] if row else 0
