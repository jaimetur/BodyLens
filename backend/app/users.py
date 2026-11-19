"""Cuentas, sesiones, invitaciones y parejas."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app import config, db
from app.security import hash_password, new_token, password_problem, token_hash, verify_password

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")


class UserError(ValueError):
    """Error con mensaje para mostrar al usuario."""


@dataclass
class User:
    id: int
    username: str
    name: str
    is_admin: bool
    partner_id: int | None
    partner_since: str | None
    sheet_id: str | None
    apps_script_url: str | None

    @classmethod
    def from_row(cls, r: sqlite3.Row) -> "User":
        return cls(r["id"], r["username"], r["name"], bool(r["is_admin"]), r["partner_id"], r["partner_since"],
                   r["sheet_id"], r["apps_script_url"])

    def public(self) -> dict:
        return {"id": self.id, "username": self.username, "name": self.name, "isAdmin": self.is_admin}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_user(con: sqlite3.Connection, user_id: int) -> User | None:
    r = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return User.from_row(r) if r else None


def get_by_username(con: sqlite3.Connection, username: str) -> User | None:
    r = con.execute("SELECT * FROM users WHERE username=?", ((username or "").strip().lower(),)).fetchone()
    return User.from_row(r) if r else None


def list_users(con: sqlite3.Connection) -> list[User]:
    return [User.from_row(r) for r in con.execute("SELECT * FROM users ORDER BY id")]


def count_users(con: sqlite3.Connection) -> int:
    return con.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def create_user(con: sqlite3.Connection, username: str, name: str, password: str, is_admin: bool = False) -> User:
    username = (username or "").strip().lower()
    name = (name or "").strip()
    if not USERNAME_RE.match(username):
        raise UserError("El usuario tiene que tener de 2 a 32 caracteres: letras minúsculas, números, punto, guion o guion bajo.")
    if not name or len(name) > 80:
        raise UserError("Escribe tu nombre (hasta 80 caracteres).")
    if p := password_problem(password):
        raise UserError(p)
    if get_by_username(con, username):
        raise UserError("Ese nombre de usuario ya existe.")
    cur = con.execute(
        "INSERT INTO users(username, name, pw_hash, is_admin, created_at) VALUES(?,?,?,?,?)",
        (username, name, hash_password(password), int(is_admin), db.now_iso()),
    )
    return get_user(con, cur.lastrowid)  # type: ignore[return-value]


def set_password(con: sqlite3.Connection, user_id: int, password: str) -> None:
    if p := password_problem(password):
        raise UserError(p)
    con.execute("UPDATE users SET pw_hash=? WHERE id=?", (hash_password(password), user_id))
    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def authenticate(con: sqlite3.Connection, username: str, password: str) -> User | None:
    r = con.execute("SELECT * FROM users WHERE username=?", ((username or "").strip().lower(),)).fetchone()
    ok = verify_password(r["pw_hash"] if r else None, password or "")
    return User.from_row(r) if (r and ok) else None


# ---------- sesiones ----------

def create_session(con: sqlite3.Connection, user_id: int) -> str:
    token = new_token()
    now = _utcnow()
    con.execute(
        "INSERT INTO sessions(token_hash, user_id, created_at, expires_at) VALUES(?,?,?,?)",
        (token_hash(token), user_id, now.isoformat(timespec="seconds"),
         (now + timedelta(days=config.settings.session_days)).isoformat(timespec="seconds")),
    )
    con.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(timespec="seconds"),))
    return token


def session_user(con: sqlite3.Connection, token: str | None) -> User | None:
    if not token:
        return None
    r = con.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at > ?",
        (token_hash(token), _utcnow().isoformat(timespec="seconds")),
    ).fetchone()
    return User.from_row(r) if r else None


def delete_session(con: sqlite3.Connection, token: str | None) -> None:
    if token:
        con.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(token),))


# ---------- invitaciones ----------

def create_invite(con: sqlite3.Connection, created_by: int | None, note: str = "") -> str:
    code = new_token(18)
    now = _utcnow()
    con.execute(
        "INSERT INTO invites(code_hash, created_by, note, created_at, expires_at) VALUES(?,?,?,?,?)",
        (token_hash(code), created_by, (note or "")[:120], now.isoformat(timespec="seconds"),
         (now + timedelta(days=config.settings.invite_days)).isoformat(timespec="seconds")),
    )
    return code


def invite_valid(con: sqlite3.Connection, code: str) -> bool:
    r = con.execute("SELECT used_by, expires_at FROM invites WHERE code_hash=?", (token_hash(code or ""),)).fetchone()
    return bool(r and r["used_by"] is None and r["expires_at"] > _utcnow().isoformat(timespec="seconds"))


def redeem_invite(con: sqlite3.Connection, code: str, username: str, name: str, password: str) -> User:
    if not invite_valid(con, code):
        raise UserError("La invitación no es válida o ha caducado. Pide otra.")
    user = create_user(con, username, name, password)
    con.execute("UPDATE invites SET used_by=?, used_at=? WHERE code_hash=?", (user.id, db.now_iso(), token_hash(code)))
    return user


def list_invites(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        "SELECT i.note, i.created_at, i.expires_at, i.used_at, u.username AS used_by_name "
        "FROM invites i LEFT JOIN users u ON u.id=i.used_by ORDER BY i.created_at DESC LIMIT 50"
    )
    return [dict(r) for r in rows]


def update_bridge(con: sqlite3.Connection, user_id: int, sheet_id: str | None, apps_script_url: str | None) -> None:
    sheet_id = (sheet_id or "").strip() or None
    apps_script_url = (apps_script_url or "").strip() or None
    if sheet_id and not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", sheet_id):
        raise UserError("El ID de la hoja no parece válido.")
    if apps_script_url and not apps_script_url.startswith("https://script.google.com/"):
        raise UserError("La URL del Apps Script tiene que empezar por https://script.google.com/.")
    con.execute("UPDATE users SET sheet_id=?, apps_script_url=? WHERE id=?", (sheet_id, apps_script_url, user_id))
