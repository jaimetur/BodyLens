"""Invitation codes: whoever signs up with one gets a free account, for life unless an administrator sets an end
date (Administration → Users). The codes are set in Administration; INVITACION_AMIGOS by default. They are compared
without accents, case or spaces."""
from __future__ import annotations

import time
import unicodedata

from app.core import db

DEFAULT = ["INVITACION_AMIGOS"]


def norm(code: str) -> str:
    s = unicodedata.normalize("NFKD", code or "")
    return "".join(c for c in s if not unicodedata.combining(c) and not c.isspace()).upper()


def codes() -> list[str]:
    s = db.get_setting("codes", None)
    return list(s) if isinstance(s, list) else list(DEFAULT)


def valid(code: str) -> bool:
    n = norm(code)
    return bool(n) and n in {norm(c) for c in codes()}


def grant(con, user_id: int, code: str | None, until_ms: int | None) -> None:
    con.execute("INSERT INTO grants(user_id, code, until_ms, created_at) VALUES(?,?,?,datetime('now')) "
                "ON CONFLICT(user_id) DO UPDATE SET until_ms=excluded.until_ms", (user_id, code, until_ms))


def active(row) -> bool:
    return row["until_ms"] is None or row["until_ms"] > time.time() * 1000
