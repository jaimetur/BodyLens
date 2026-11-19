"""Almacén de documentos por usuario (sustituye al «db» del artefacto) y datos compartidos en pareja.

Cada usuario tiene su propia colección «bascula» con los mismos documentos que el artefacto (peso, hist-AAAA, hklog…).
Si dos cuentas están unidas como pareja, los registros de ciclo e intimidad del documento «hklog» viven en un documento
común de la pareja: al leer «hklog» cada uno recibe sus registros propios más los comunes, y al guardarlo los de esos
tipos van al documento común (así los ven y los editan los dos).
"""
from __future__ import annotations

import json
import re
import sqlite3

from app import db
from app.users import User

COL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
MAX_DOC_BYTES = 16 * 1024 * 1024

MAIN_COLLECTION = "bascula"
SHARED_DOC = "hklog"
# mismos tipos que CYC_T e INT_T de app_c.html: ciclo + actividad sexual
SHARED_TYPES = frozenset(
    ["menstrual", "intermenstrual", "ovulation", "bbt", "cervical", "contraceptive", "pregnancy", "sexual"]
)


class DocError(ValueError):
    pass


def check_names(collection: str, doc_id: str | None = None) -> None:
    if not COL_RE.match(collection or ""):
        raise DocError("Nombre de colección no válido.")
    if doc_id is not None and not ID_RE.match(doc_id or ""):
        raise DocError("Nombre de documento no válido.")


def couple_key(a: int, b: int) -> str:
    lo, hi = sorted((int(a), int(b)))
    return f"{lo}-{hi}"


# ---------- eventos de hklog ----------

def _ev_key(e) -> str:
    return "|".join("" if x is None else str(x) for x in e)


def merge_events(*logs) -> dict:
    """Unión sin duplicados ordenada por inicio (igual que mergeEv del frontend)."""
    seen: set[str] = set()
    out = []
    for log in logs:
        for e in (log or {}).get("e") or []:
            if not isinstance(e, list) or not e:
                continue
            k = _ev_key(e)
            if k not in seen:
                seen.add(k)
                out.append(e)
    out.sort(key=lambda e: str(e[1]) if len(e) > 1 and e[1] is not None else "")
    return {"v": 1, "e": out}


def split_events(log: dict | None) -> tuple[dict, dict]:
    """(propios, compartidos) de un hklog; conserva el resto de campos del documento en el propio."""
    log = log if isinstance(log, dict) else {}
    own = {k: v for k, v in log.items() if k != "e"}
    own.setdefault("v", 1)
    own_e, shared_e = [], []
    for e in log.get("e") or []:
        (shared_e if isinstance(e, list) and e and e[0] in SHARED_TYPES else own_e).append(e)
    own["e"] = own_e
    return own, {"v": 1, "e": shared_e}


# ---------- lectura y escritura de bajo nivel ----------

def _row(con: sqlite3.Connection, user_id: int, collection: str, doc_id: str):
    return con.execute("SELECT * FROM docs WHERE user_id=? AND collection=? AND id=?",
                       (user_id, collection, doc_id)).fetchone()


def _write(con: sqlite3.Connection, user_id: int, collection: str, doc_id: str, data) -> int:
    rev = db.next_rev(con)
    payload = None if data is None else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    con.execute(
        "INSERT INTO docs(user_id, collection, id, data, rev, updated_at) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(user_id, collection, id) DO UPDATE SET data=excluded.data, rev=excluded.rev, updated_at=excluded.updated_at",
        (user_id, collection, doc_id, payload, rev, db.now_iso()),
    )
    return rev


def _touch(con: sqlite3.Connection, user_id: int, collection: str, doc_id: str) -> int:
    """Nueva revisión sin cambiar el contenido (para que el sondeo de la pareja vea el cambio)."""
    r = _row(con, user_id, collection, doc_id)
    data = json.loads(r["data"]) if r and r["data"] is not None else {"v": 1, "e": []}
    return _write(con, user_id, collection, doc_id, data)


def _shared_get(con: sqlite3.Connection, couple: str) -> dict:
    r = con.execute("SELECT data FROM shared_docs WHERE couple=? AND id=?", (couple, SHARED_DOC)).fetchone()
    return json.loads(r["data"]) if r else {"v": 1, "e": []}


def _shared_set(con: sqlite3.Connection, couple: str, data: dict) -> None:
    con.execute(
        "INSERT INTO shared_docs(couple, id, data, rev, updated_at) VALUES(?,?,?,?,?) "
        "ON CONFLICT(couple, id) DO UPDATE SET data=excluded.data, rev=excluded.rev, updated_at=excluded.updated_at",
        (couple, SHARED_DOC, json.dumps(data, ensure_ascii=False, separators=(",", ":")), db.next_rev(con), db.now_iso()),
    )


def _view(con: sqlite3.Connection, user: User, collection: str, doc_id: str, raw: str | None):
    """Contenido que ve el usuario (hklog con los registros comunes de la pareja)."""
    data = None if raw is None else json.loads(raw)
    if data is not None and user.partner_id and collection == MAIN_COLLECTION and doc_id == SHARED_DOC:
        own, _ = split_events(data)
        merged = merge_events(own, _shared_get(con, couple_key(user.id, user.partner_id)))
        data = {**own, "e": merged["e"]}
    return data


# ---------- API ----------

def list_docs(con: sqlite3.Connection, user: User, collection: str, since: int | None = None) -> dict:
    check_names(collection)
    rev = db.current_rev(con)
    if since is None:
        rows = con.execute("SELECT * FROM docs WHERE user_id=? AND collection=? AND data IS NOT NULL ORDER BY id",
                           (user.id, collection)).fetchall()
    else:
        rows = con.execute("SELECT * FROM docs WHERE user_id=? AND collection=? AND rev>? ORDER BY id",
                           (user.id, collection, since)).fetchall()
    docs = []
    for r in rows:
        if r["data"] is None:
            docs.append({"id": r["id"], "deleted": True, "rev": r["rev"]})
        else:
            docs.append({"id": r["id"], "data": _view(con, user, collection, r["id"], r["data"]), "rev": r["rev"]})
    return {"rev": rev, "docs": docs}


def get_doc(con: sqlite3.Connection, user: User, collection: str, doc_id: str):
    check_names(collection, doc_id)
    r = _row(con, user.id, collection, doc_id)
    if not r or r["data"] is None:
        return None
    return {"id": doc_id, "data": _view(con, user, collection, doc_id, r["data"]), "rev": r["rev"]}


def put_doc(con: sqlite3.Connection, user: User, collection: str, doc_id: str, data) -> int:
    check_names(collection, doc_id)
    if not isinstance(data, dict):
        raise DocError("El documento tiene que ser un objeto JSON.")
    if len(json.dumps(data, separators=(",", ":"))) > MAX_DOC_BYTES:
        raise DocError("El documento es demasiado grande.")
    if user.partner_id and collection == MAIN_COLLECTION and doc_id == SHARED_DOC:
        own, shared = split_events(data)
        _shared_set(con, couple_key(user.id, user.partner_id), shared)
        _touch(con, user.partner_id, collection, doc_id)
        return _write(con, user.id, collection, doc_id, own)
    return _write(con, user.id, collection, doc_id, data)


def update_doc(con: sqlite3.Connection, user: User, collection: str, doc_id: str, patch) -> int:
    if not isinstance(patch, dict):
        raise DocError("El cambio tiene que ser un objeto JSON.")
    cur = get_doc(con, user, collection, doc_id)
    return put_doc(con, user, collection, doc_id, {**((cur or {}).get("data") or {}), **patch})


def delete_doc(con: sqlite3.Connection, user: User, collection: str, doc_id: str) -> int:
    check_names(collection, doc_id)
    if not _row(con, user.id, collection, doc_id):
        return db.current_rev(con)
    return _write(con, user.id, collection, doc_id, None)


# ---------- parejas ----------

def link_partners(con: sqlite3.Connection, a: User, b: User, since: str | None = None) -> None:
    """Une dos cuentas: los registros de ciclo e intimidad de ambas pasan al documento común."""
    if a.id == b.id:
        raise DocError("No puedes ser tu propia pareja.")
    if a.partner_id or b.partner_id:
        raise DocError("Alguna de las dos cuentas ya tiene pareja.")
    con.execute("UPDATE users SET partner_id=?, partner_since=? WHERE id=?", (b.id, since, a.id))
    con.execute("UPDATE users SET partner_id=?, partner_since=? WHERE id=?", (a.id, since, b.id))
    couple = couple_key(a.id, b.id)
    pieces = [_shared_get(con, couple)]
    for u in (a, b):
        r = _row(con, u.id, MAIN_COLLECTION, SHARED_DOC)
        if r and r["data"] is not None:
            own, shared = split_events(json.loads(r["data"]))
            pieces.append(shared)
            _write(con, u.id, MAIN_COLLECTION, SHARED_DOC, own)
        else:
            _write(con, u.id, MAIN_COLLECTION, SHARED_DOC, {"v": 1, "e": []})
    _shared_set(con, couple, merge_events(*pieces))


def unlink_partner(con: sqlite3.Connection, user: User) -> None:
    """Separa la pareja: cada uno se queda con una copia de los registros comunes."""
    if not user.partner_id:
        return
    couple = couple_key(user.id, user.partner_id)
    shared = _shared_get(con, couple)
    for uid in (user.id, user.partner_id):
        r = _row(con, uid, MAIN_COLLECTION, SHARED_DOC)
        own = json.loads(r["data"]) if r and r["data"] is not None else {"v": 1, "e": []}
        merged = merge_events(own, shared)
        _write(con, uid, MAIN_COLLECTION, SHARED_DOC, {**own, "e": merged["e"]})
    con.execute("DELETE FROM shared_docs WHERE couple=?", (couple,))
    con.execute("UPDATE users SET partner_id=NULL, partner_since=NULL WHERE id IN (?,?)", (user.id, user.partner_id))
    con.execute("DELETE FROM partner_requests WHERE from_id IN (?,?) OR to_id IN (?,?)",
                (user.id, user.partner_id, user.id, user.partner_id))
