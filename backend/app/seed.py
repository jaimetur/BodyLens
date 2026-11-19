"""Importa los datos del artefacto en la cuenta de un usuario.

Acepta los dos formatos:
  - snap.json (copia que llevaba la página: incluye otros perfiles en «prof» y la lista en «profs»)
  - la «Copia completa (JSON)» de Ajustes → Copia de seguridad ({app:'bascula', v:1, doc, hist, …})

Uso:
  python -m app.seed FICHERO --usuario jaime                 # datos del perfil principal
  python -m app.seed FICHERO --usuario laura --perfil laura   # datos de otro perfil de la copia a su propia cuenta
  python -m app.seed FICHERO --usuario jaime --con-perfiles   # además, los demás perfiles dentro de la misma cuenta

Es idempotente: vuelve a escribir los mismos documentos (los registros de «hklog» y «hkev» se suman sin duplicar).
"""
from __future__ import annotations

import argparse
import json
import sys

from app import db, docstore
from app.users import get_by_username

COL = docstore.MAIN_COLLECTION
# clave en la copia → prefijo del documento por años
YEARLY = {"hist": "hist", "act": "act", "slp": "slp", "wo": "wo", "food": "com", "hk": "hk", "ecg": "ecg", "nap": "nap"}


def docs_from_copy(c: dict) -> dict[str, dict]:
    """Documentos de la colección a partir de una copia (snap o copia de seguridad)."""
    out: dict[str, dict] = {}
    if isinstance(c.get("doc"), dict):
        out["peso"] = c["doc"]
    if isinstance(c.get("med"), dict) and c["med"]:
        out["medidas"] = c["med"]
    for key, prefix in YEARLY.items():
        for y, v in (c.get(key) or {}).items():
            if isinstance(v, dict) and str(y).isdigit():
                out[f"{prefix}-{y}"] = v
    for key in ("hkev", "hklog"):
        if isinstance(c.get(key), dict):
            out[key] = c[key]
    return out


class ImportError_(ValueError):
    """Error de importación con mensaje para el usuario."""


def check_copy(c) -> dict:
    if not isinstance(c, dict) or not ("doc" in c or "hist" in c):
        raise ImportError_("El fichero no parece una copia de BodyLens (snap.json o copia completa JSON).")
    return c


def load_copy(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return check_copy(json.load(f))


def profiles_in(c: dict) -> list[dict]:
    """Perfiles que trae la copia además del principal: [{id, name}]."""
    names = {p.get("id"): p.get("name") for p in (c.get("profs") or []) if isinstance(p, dict)}
    return [{"id": pid, "name": names.get(pid) or pid} for pid, v in (c.get("prof") or {}).items() if isinstance(v, dict)]


def import_copy(con, user, c: dict, profile: str | None = None, with_profiles: bool = False) -> int:
    """Escribe en la cuenta los documentos de la copia (dentro de una transacción abierta). Devuelve cuántos."""
    check_copy(c)
    if profile:
        src = (c.get("prof") or {}).get(profile)
        if not isinstance(src, dict):
            have = ", ".join(p["id"] for p in profiles_in(c)) or "ninguno"
            raise ImportError_(f"La copia no tiene el perfil «{profile}». Perfiles: {have}.")
    else:
        src = c
    docs = docs_from_copy(src)
    if with_profiles and not profile:
        for pid, pc in (c.get("prof") or {}).items():
            if isinstance(pc, dict):
                for k, v in docs_from_copy(pc).items():
                    docs[f"pf-{pid}-{k}"] = v
        if isinstance(c.get("profs"), list):
            docs["perfiles"] = {"v": 1, "list": c["profs"]}
    if not docs:
        raise ImportError_("La copia no trae datos.")
    for doc_id, data in docs.items():
        if doc_id in ("hklog", "hkev"):
            cur = docstore.get_doc(con, user, COL, doc_id)
            if cur:
                data = {**cur["data"], **data, "e": docstore.merge_events(cur["data"], data)["e"]}
        docstore.put_doc(con, user, COL, doc_id, data)
    return len(docs)


def seed(path: str, username: str, profile: str | None = None, with_profiles: bool = False) -> dict:
    try:
        c = load_copy(path)
    except ImportError_ as e:
        raise SystemExit(str(e))
    db.init_db()
    with db.tx() as con:
        user = get_by_username(con, username)
        if not user:
            raise SystemExit(f"No existe la cuenta «{username}». Créala antes (invitación o python -m app.admin).")
        try:
            n = import_copy(con, user, c, profile, with_profiles)
        except ImportError_ as e:
            raise SystemExit(str(e))
    return {"usuario": username, "documentos": n}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m app.seed", description="Importa una copia de BodyLens en una cuenta.")
    ap.add_argument("fichero")
    ap.add_argument("--usuario", required=True, help="cuenta de destino")
    ap.add_argument("--perfil", help="importar este perfil de la copia (p. ej. laura) en vez del principal")
    ap.add_argument("--con-perfiles", action="store_true", help="importar también los demás perfiles en la misma cuenta")
    a = ap.parse_args(argv)
    try:
        r = seed(a.fichero, a.usuario, a.perfil, a.con_perfiles)
    finally:
        db.fix_ownership()
    print(f"Importados {r['documentos']} documentos en la cuenta «{r['usuario']}».")


if __name__ == "__main__":
    main(sys.argv[1:])
