"""Pasar un perfil de la app (los documentos «pf-<perfil>-…» de una cuenta) a la cuenta propia de esa persona.

Se usa cuando alguien que era un perfil dentro de otra cuenta (p. ej. la pareja) tiene ya su propia cuenta: sus datos
pasan a ser los documentos principales de su cuenta, el perfil desaparece de la cuenta de origen y, si los dos perfiles
estaban marcados como pareja, las dos cuentas se unen en pareja (comparten ciclo e intimidad).
"""
from __future__ import annotations

import json
import sqlite3

from app.accounts.users import User, get_user
from app.data import docstore

COL = docstore.MAIN_COLLECTION


class ProfileError(ValueError):
    pass


def _profiles(con: sqlite3.Connection, user: User) -> dict:
    d = docstore.get_doc(con, user, COL, "perfiles")
    return (d or {}).get("data") or {"v": 1, "list": []}


def move_profile(con: sqlite3.Connection, src: User, profile_id: str, dst: User, link_couple: bool = True) -> dict:
    """Mueve el perfil `profile_id` de la cuenta `src` a la cuenta `dst`. Devuelve un resumen."""
    if not profile_id:
        raise ProfileError("El perfil principal no se puede mover: elige otro perfil.")
    if src.id == dst.id:
        raise ProfileError("Las cuentas de origen y destino son la misma.")
    prefix = f"pf-{profile_id}-"
    rows = con.execute("SELECT id FROM docs WHERE user_id=? AND collection=? AND id LIKE ? AND data IS NOT NULL",
                       (src.id, COL, prefix.replace("_", "\\_") + "%")).fetchall()
    ids = [r["id"] for r in rows if r["id"].startswith(prefix)]
    plist = _profiles(con, src)
    entry = next((p for p in plist.get("list") or [] if p.get("id") == profile_id), None)
    if not ids and not entry:
        raise ProfileError(f"La cuenta «{src.username}» no tiene el perfil «{profile_id}».")
    moved = 0
    for doc_id in ids:
        target = doc_id[len(prefix):]
        data = docstore.get_doc(con, src, COL, doc_id)["data"]
        cur = docstore.get_doc(con, dst, COL, target)
        if cur and target in ("hklog", "hkev"):
            data = {**cur["data"], **data, "e": docstore.merge_events(cur["data"], data)["e"]}
        elif cur and target not in ("peso",):
            # los documentos por años o de medidas que ya existan en la cuenta de destino no se pisan
            continue
        docstore.put_doc(con, dst, COL, target, data)
        docstore.delete_doc(con, src, COL, doc_id)
        moved += 1
    # el perfil sale de la lista de la cuenta de origen (y de la pareja de los demás perfiles)
    since = None
    if entry:
        since = entry.get("partnerSince") or None
        new_list = []
        for p in plist.get("list") or []:
            if p.get("id") == profile_id:
                continue
            p = dict(p)
            if p.get("partner") == profile_id:
                since = since or p.get("partnerSince") or None
                p.pop("partner", None)
                p.pop("partnerSince", None)
            new_list.append(p)
        docstore.put_doc(con, src, COL, "perfiles", {**plist, "list": new_list})
    # pareja del perfil principal de la cuenta de origen (id «»): entonces las dos cuentas pasan a ser pareja
    main = next((p for p in plist.get("list") or [] if p.get("id") == ""), None)
    was_partner = bool(entry and (entry.get("partner") == "" or (main and main.get("partner") == profile_id)))
    linked = False
    if link_couple and was_partner:
        src_now, dst_now = get_user(con, src.id), get_user(con, dst.id)
        if not src_now.partner_id and not dst_now.partner_id:
            docstore.link_partners(con, src_now, dst_now, since)
            linked = True
    return {"documents": moved, "linked": linked, "since": since}


def move_profile_by_names(con: sqlite3.Connection, src_username: str, profile_id: str, dst_username: str,
                          link_couple: bool = True) -> dict:
    from app.accounts.users import get_by_username
    src, dst = get_by_username(con, src_username), get_by_username(con, dst_username)
    if not src or not dst:
        raise ProfileError("No existe alguna de las dos cuentas.")
    return move_profile(con, src, profile_id, dst, link_couple)


def dumps(r: dict) -> str:
    return json.dumps(r, ensure_ascii=False)
