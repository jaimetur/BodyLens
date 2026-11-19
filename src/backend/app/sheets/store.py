"""Las pestañas del libro de datos de cada cuenta, en SQLite. Port de guardarFilas_ / leerFilas_ del Apps Script.

- Pestañas que escribe el servidor (tabs.DYNAMIC): una fila por clave en sheet_rows.
- Pestañas fijas de la hoja (Control Diario, Notas históricas, Pesos históricos…): se guardan tal cual en sheet_tabs.
- sheet_tabs también guarda el orden de las pestañas, para generar el libro igual que la hoja.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Callable

from app.core import db
from app.sheets import values as V
from app.sheets.tabs import DYNAMIC, Tab

SCHEMA = """
CREATE TABLE IF NOT EXISTS sheet_rows (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tab TEXT NOT NULL,
  key TEXT NOT NULL,
  data TEXT NOT NULL,
  PRIMARY KEY (user_id, tab, key)
);
CREATE TABLE IF NOT EXISTS sheet_tabs (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tab TEXT NOT NULL,
  position INTEGER NOT NULL,
  static_rows TEXT,
  PRIMARY KEY (user_id, tab)
);
"""

Row = list
Merge = Callable[[Row | None, Row, str], Row | None]
Remove = Callable[[Row], bool]


def ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)


def _pad(row: Row, n: int) -> Row:
    row = list(row)
    if len(row) < n:
        row += [""] * (n - len(row))
    return row[:n]


def read_rows(con: sqlite3.Connection, user_id: int, tab: Tab) -> dict[str, Row]:
    out = {}
    for r in con.execute("SELECT key, data FROM sheet_rows WHERE user_id=? AND tab=?", (user_id, tab.name)):
        out[r["key"]] = [V.dec(x) for x in json.loads(r["data"])]
    return out


def sorted_rows(con: sqlite3.Connection, user_id: int, tab: Tab) -> list[Row]:
    rows = list(read_rows(con, user_id, tab).values())
    rows.sort(key=lambda r: V.sort_value(r[tab.sort] if len(r) > tab.sort else ""))
    return rows


def _ensure_tab(con: sqlite3.Connection, user_id: int, name: str) -> None:
    if not con.execute("SELECT 1 FROM sheet_tabs WHERE user_id=? AND tab=?", (user_id, name)).fetchone():
        pos = con.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM sheet_tabs WHERE user_id=?", (user_id,)).fetchone()[0]
        con.execute("INSERT INTO sheet_tabs(user_id, tab, position) VALUES(?,?,?)", (user_id, name, pos))


def save_rows(con: sqlite3.Connection, user_id: int, tab: Tab, new: dict[str, Row], merge: Merge | None = None,
              remove: Remove | None = None) -> int:
    """guardarFilas_: mezcla las filas nuevas con las que hay (por clave) y quita las que `remove` diga que sobran
    (de entre las que no vienen en `new`). Devuelve cuántas filas tiene la pestaña."""
    _ensure_tab(con, user_id, tab.name)
    n = len(tab.headers)
    rows = read_rows(con, user_id, tab)
    changed: dict[str, Row | None] = {}
    for k, row in new.items():
        v = merge(rows.get(k), row, k) if merge else row
        if v:
            v = _pad(v, n)
            if rows.get(k) != v:
                changed[k] = v
            rows[k] = v
    if remove:
        for k in list(rows):
            if k not in new and remove(rows[k]):
                changed[k] = None
                del rows[k]
    for k, v in changed.items():
        if v is None:
            con.execute("DELETE FROM sheet_rows WHERE user_id=? AND tab=? AND key=?", (user_id, tab.name, k))
        else:
            con.execute(
                "INSERT INTO sheet_rows(user_id, tab, key, data) VALUES(?,?,?,?) "
                "ON CONFLICT(user_id, tab, key) DO UPDATE SET data=excluded.data",
                (user_id, tab.name, k, json.dumps([V.enc(x) for x in v], ensure_ascii=False, separators=(",", ":"))))
    if changed:
        mark_dirty(con, user_id)
    return len(rows)


def replace_tab(con: sqlite3.Connection, user_id: int, tab: Tab, rows: list[Row]) -> int:
    """Reescribe la pestaña entera (importación): la clave de cada fila es la de leerFilas_ (la última gana)."""
    _ensure_tab(con, user_id, tab.name)
    con.execute("DELETE FROM sheet_rows WHERE user_id=? AND tab=?", (user_id, tab.name))
    keyed: dict[str, Row] = {}
    for r in rows:
        r = _pad(r, len(tab.headers))
        k = V.day_key(r[tab.key])
        if k:
            keyed[k] = r
    con.executemany(
        "INSERT INTO sheet_rows(user_id, tab, key, data) VALUES(?,?,?,?)",
        [(user_id, tab.name, k, json.dumps([V.enc(x) for x in r], ensure_ascii=False, separators=(",", ":")))
         for k, r in keyed.items()])
    mark_dirty(con, user_id)
    return len(keyed)


def set_static(con: sqlite3.Connection, user_id: int, name: str, rows: list[list], position: int) -> None:
    con.execute(
        "INSERT INTO sheet_tabs(user_id, tab, position, static_rows) VALUES(?,?,?,?) "
        "ON CONFLICT(user_id, tab) DO UPDATE SET position=excluded.position, static_rows=excluded.static_rows",
        (user_id, name, position, json.dumps([[V.enc(x) for x in r] for r in rows], ensure_ascii=False)))


def set_position(con: sqlite3.Connection, user_id: int, name: str, position: int) -> None:
    con.execute(
        "INSERT INTO sheet_tabs(user_id, tab, position) VALUES(?,?,?) "
        "ON CONFLICT(user_id, tab) DO UPDATE SET position=excluded.position", (user_id, name, position))


def layout(con: sqlite3.Connection, user_id: int) -> list[tuple[str, list | None]]:
    """[(pestaña, filas fijas o None si es dinámica)] en el orden de la hoja; las dinámicas que falten, al final."""
    out, seen = [], set()
    for r in con.execute("SELECT tab, static_rows FROM sheet_tabs WHERE user_id=? ORDER BY position", (user_id,)):
        seen.add(r["tab"])
        st = r["static_rows"]
        out.append((r["tab"], [[V.dec(x) for x in row] for row in json.loads(st)] if st is not None else None))
    for name in DYNAMIC:
        if name not in seen:
            out.append((name, None))
    return out


def has_tables(con: sqlite3.Connection, user_id: int) -> bool:
    return bool(con.execute("SELECT 1 FROM sheet_tabs WHERE user_id=? LIMIT 1", (user_id,)).fetchone())


def mark_dirty(con: sqlite3.Connection, user_id: int) -> None:
    con.execute("INSERT INTO counters(name, value) VALUES(?, 1) ON CONFLICT(name) DO UPDATE SET value=1",
                (f"wb_dirty:{user_id}",))


def take_dirty(user_id: int) -> bool:
    with db.tx() as con:
        r = con.execute("SELECT value FROM counters WHERE name=?", (f"wb_dirty:{user_id}",)).fetchone()
        if r and r["value"]:
            con.execute("UPDATE counters SET value=0 WHERE name=?", (f"wb_dirty:{user_id}",))
            return True
    return False
