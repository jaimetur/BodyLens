"""SQLite: conexión, esquema y contador global de revisiones."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.core import config

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
  email TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  requested_at TEXT,
  request_note TEXT,
  data_source TEXT NOT NULL DEFAULT 'server',
  lang TEXT NOT NULL DEFAULT 'en',
  font_size TEXT NOT NULL DEFAULT 'md',
  theme TEXT NOT NULL DEFAULT 'auto',
  lock_min INTEGER NOT NULL DEFAULT 1,
  nav TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS subscriptions (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  token_enc TEXT NOT NULL,
  product_id TEXT NOT NULL,
  base_plan TEXT,
  state TEXT,
  expiry_ms INTEGER NOT NULL DEFAULT 0,
  checked_at INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stripe_subs (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  customer_id TEXT NOT NULL,
  subscription_id TEXT NOT NULL UNIQUE,
  plan TEXT,
  status TEXT NOT NULL,
  period_end_ms INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pending_signups (
  id TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lapses (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  lapsed_at TEXT NOT NULL,
  warnings INTEGER NOT NULL DEFAULT 0,
  last_warning_at TEXT
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
CREATE TABLE IF NOT EXISTS source_tokens (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  data TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (user_id, source)
);
CREATE TABLE IF NOT EXISTS ingest_tokens (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS counters (
  name TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);
"""


def get_setting(key: str, default=None):
    import json
    try:
        with ro() as con:
            r = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    except sqlite3.OperationalError:
        return default
    return json.loads(r["value"]) if r else default


def set_setting(con: sqlite3.Connection, key: str, value) -> None:
    import json
    con.execute("INSERT INTO settings(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)))


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
    for col, ddl in (("must_change", "INTEGER NOT NULL DEFAULT 0"), ("email", "TEXT"),
                     ("active", "INTEGER NOT NULL DEFAULT 1"), ("requested_at", "TEXT"), ("request_note", "TEXT"),
                     ("data_source", "TEXT NOT NULL DEFAULT 'server'")):
        if col not in cols:
            con.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
    # the Google Sheet bridge is retired for new accounts: every account without a sheet keeps its data on the server
    con.execute("UPDATE users SET data_source='server' WHERE data_source='sheet' AND coalesce(sheet_id, '')=''")
    if "font_size" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN font_size TEXT NOT NULL DEFAULT 'md'")
    if "theme" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'auto'")
    if "lock_min" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN lock_min INTEGER NOT NULL DEFAULT 1")
    if "nav" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN nav TEXT NOT NULL DEFAULT '{}'")
    if "lang" not in cols:
        # las cuentas de antes del multi-idioma usaban la app en español: lo conservan; las nuevas, inglés
        con.execute("ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'en'")
        con.execute("UPDATE users SET lang='es'")


def init_db() -> None:
    con = connect()
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
        _migrate(con)
        from app.sheets import store
        store.ensure_schema(con)
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
