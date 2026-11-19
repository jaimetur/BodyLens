"""Cuentas, sesiones, invitaciones y parejas."""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core import config, db
from app.core.security import hash_password, new_token, password_problem, token_hash, verify_password

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
EMAIL_RE = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")


def clean_email(email: str | None, required: bool = False) -> str | None:
    email = (email or "").strip()
    if not email:
        if required:
            raise UserError("Escribe tu correo electrónico.")
        return None
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise UserError("El correo electrónico no es válido.")
    return email


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
    must_change: bool = False
    email: str | None = None
    active: bool = True
    requested_at: str | None = None
    request_note: str | None = None
    lang: str = "en"
    font_size: str = "md"
    theme: str = "auto"
    lock_min: int = 1
    nav: str = "{}"

    @classmethod
    def from_row(cls, r: sqlite3.Row) -> "User":
        return cls(r["id"], r["username"], r["name"], bool(r["is_admin"]), r["partner_id"], r["partner_since"],
                   r["sheet_id"], r["apps_script_url"], bool(r["must_change"]), r["email"], bool(r["active"]),
                   r["requested_at"], r["request_note"], r["lang"] if "lang" in r.keys() else "en",
                   r["font_size"] if "font_size" in r.keys() else "md",
                   r["theme"] if "theme" in r.keys() else "auto",
                   r["lock_min"] if "lock_min" in r.keys() else 1,
                   r["nav"] if "nav" in r.keys() else "{}")

    def public(self) -> dict:
        return {"id": self.id, "username": self.username, "name": self.name, "isAdmin": self.is_admin,
                "mustChange": self.must_change, "email": self.email or "", "lang": self.lang,
                "fontSize": self.font_size, "theme": self.theme, "lockMin": self.lock_min, "nav": _json_obj(self.nav)}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_user(con: sqlite3.Connection, user_id: int) -> User | None:
    r = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return User.from_row(r) if r else None


def get_by_username(con: sqlite3.Connection, username: str) -> User | None:
    r = con.execute("SELECT * FROM users WHERE username=?", ((username or "").strip().lower(),)).fetchone()
    return User.from_row(r) if r else None


def get_by_login(con: sqlite3.Connection, login: str) -> User | None:
    """The account with that username or, when it contains «@», with that email."""
    login = (login or "").strip().lower()
    if "@" not in login:
        return get_by_username(con, login)
    r = con.execute("SELECT * FROM users WHERE lower(email)=?", (login,)).fetchone()
    return User.from_row(r) if r else None


def list_users(con: sqlite3.Connection, active: bool | None = True) -> list[User]:
    """Cuentas activas (por defecto), pendientes de aprobar (False) o todas (None)."""
    if active is None:
        return [User.from_row(r) for r in con.execute("SELECT * FROM users ORDER BY id")]
    return [User.from_row(r) for r in con.execute("SELECT * FROM users WHERE active=? ORDER BY id", (int(active),))]


def ensure_other_admin(con: sqlite3.Connection, user_id: int) -> None:
    """Refuse to leave the server without an active admin (removing, deactivating or deleting the last one)."""
    n = con.execute("SELECT count(*) FROM users WHERE is_admin=1 AND active=1 AND id<>?", (user_id,)).fetchone()[0]
    if not n:
        raise UserError("Es la única cuenta de administración activa: haz antes administradora a otra cuenta.")


def admin_emails(con: sqlite3.Connection) -> list[str]:
    return [u.email for u in list_users(con) if u.is_admin and u.email]


def count_users(con: sqlite3.Connection) -> int:
    return con.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def create_user(con: sqlite3.Connection, username: str, name: str, password: str, is_admin: bool = False,
                must_change: bool = False, email: str | None = None, active: bool = True,
                request_note: str | None = None) -> User:
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
    email = clean_email(email)
    now = db.now_iso()
    cur = con.execute(
        "INSERT INTO users(username, name, pw_hash, is_admin, must_change, email, active, requested_at, request_note, "
        "created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (username, name, hash_password(password), int(is_admin), int(must_change), email, int(active),
         None if active else now, (request_note or "").strip()[:500] or None, now),
    )
    return get_user(con, cur.lastrowid)  # type: ignore[return-value]


def rename(con: sqlite3.Connection, user_id: int, username: str, name: str) -> None:
    username = (username or "").strip().lower()
    name = (name or "").strip()
    if not USERNAME_RE.match(username):
        raise UserError("El usuario tiene que tener de 2 a 32 caracteres: letras minúsculas, números, punto, guion o guion bajo.")
    if not name or len(name) > 80:
        raise UserError("Escribe tu nombre (hasta 80 caracteres).")
    other = get_by_username(con, username)
    if other and other.id != user_id:
        raise UserError("Ese nombre de usuario ya existe.")
    con.execute("UPDATE users SET username=?, name=? WHERE id=?", (username, name, user_id))


def set_lang(con: sqlite3.Connection, user_id: int, lang: str | None) -> str:
    from app.core import i18n
    lang = i18n.clean(lang)
    if not lang:
        raise UserError("Ese idioma no está disponible.")
    con.execute("UPDATE users SET lang=? WHERE id=?", (lang, user_id))
    return lang


# text size of the interface: CSS zoom of the page (phones get half the increase, see app.web.routes.display_css)
FONT_SIZES = {"sm": 1.0, "md": 1.1, "lg": 1.22, "xl": 1.36}


def set_font_size(con: sqlite3.Connection, user_id: int, size: str | None) -> str:
    if size not in FONT_SIZES:
        raise UserError("Ese tamaño de texto no está disponible.")
    con.execute("UPDATE users SET font_size=? WHERE id=?", (size, user_id))
    return size


def _json_obj(s: str | None) -> dict:
    try:
        v = json.loads(s or "{}")
    except ValueError:
        return {}
    return v if isinstance(v, dict) else {}


# what each profile of the account had open (section, tabs), so the app reopens it on any device
NAV_MAX_BYTES = 32_000


def set_nav(con: sqlite3.Connection, user_id: int, nav: dict) -> None:
    s = json.dumps(nav, ensure_ascii=False, separators=(",", ":"))
    if len(s.encode()) > NAV_MAX_BYTES:
        raise UserError("Demasiados datos de navegación.")
    con.execute("UPDATE users SET nav=? WHERE id=?", (s, user_id))


# colour themes of the interface (CSS in src/frontend/common/themes.css); "auto" follows the device
THEMES = ("auto", "light", "dark", "sepia", "ocean", "forest", "contrast")
# minutes without activity before a profile with a PIN locks itself
LOCK_MINUTES = (1, 2, 5, 10, 15, 30)


def set_theme(con: sqlite3.Connection, user_id: int, theme: str | None) -> str:
    if theme not in THEMES:
        raise UserError("Ese tema no está disponible.")
    con.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
    return theme


def set_lock_minutes(con: sqlite3.Connection, user_id: int, minutes: int | None) -> int:
    if minutes not in LOCK_MINUTES:
        raise UserError("Ese tiempo de bloqueo no está disponible.")
    con.execute("UPDATE users SET lock_min=? WHERE id=?", (minutes, user_id))
    return minutes


def set_email(con: sqlite3.Connection, user_id: int, email: str | None) -> None:
    email = clean_email(email, required=True)
    if email_taken(con, email, except_id=user_id):
        raise UserError("Ya hay otra cuenta con ese correo.")
    con.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))


def approve(con: sqlite3.Connection, user_id: int) -> User:
    u = get_user(con, user_id)
    if not u or u.active:
        raise UserError("Esa petición ya no está pendiente.")
    con.execute("UPDATE users SET active=1 WHERE id=?", (user_id,))
    return get_user(con, user_id)  # type: ignore[return-value]


def reject(con: sqlite3.Connection, user_id: int) -> User:
    u = get_user(con, user_id)
    if not u or u.active:
        raise UserError("Esa petición ya no está pendiente.")
    con.execute("DELETE FROM users WHERE id=?", (user_id,))
    return u


def set_password(con: sqlite3.Connection, user_id: int, password: str) -> None:
    if p := password_problem(password):
        raise UserError(p)
    con.execute("UPDATE users SET pw_hash=?, must_change=0 WHERE id=?", (hash_password(password), user_id))
    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def authenticate(con: sqlite3.Connection, username: str, password: str) -> User | None:
    """Sign in with the username or with the account's email (usernames never contain «@»)."""
    login = (username or "").strip().lower()
    if "@" in login:
        r = con.execute("SELECT * FROM users WHERE lower(email)=?", (login,)).fetchone()
    else:
        r = con.execute("SELECT * FROM users WHERE username=?", (login,)).fetchone()
    ok = verify_password(r["pw_hash"] if r else None, password or "")
    return User.from_row(r) if (r and ok) else None


# cuenta inicial de todo despliegue, como en DriveTest Analyzer: se crea una sola vez (si luego se borra o se
# renombra, no vuelve) y la pantalla de entrar la muestra mientras conserve su contraseña por defecto
DEFAULT_ADMIN = ("admin", "admin123")
_hint_cache: dict = {}


def bootstrap_default_admin(con: sqlite3.Connection) -> User | None:
    if con.execute("SELECT 1 FROM counters WHERE name='bootstrap_default_admin'").fetchone():
        return None
    con.execute("INSERT INTO counters(name, value) VALUES('bootstrap_default_admin', 1)")
    if get_by_username(con, DEFAULT_ADMIN[0]):
        return None
    return create_user(con, DEFAULT_ADMIN[0], "Administración", DEFAULT_ADMIN[1], is_admin=True)


def has_default_password(u: User | None, pw_hash: str | None) -> bool:
    if not u or not pw_hash or u.username != DEFAULT_ADMIN[0]:
        return False
    if pw_hash not in _hint_cache:
        _hint_cache.clear()
        _hint_cache[pw_hash] = verify_password(pw_hash, DEFAULT_ADMIN[1])
    return _hint_cache[pw_hash]


def default_accounts(con: sqlite3.Connection) -> list[dict]:
    """Cuentas por defecto que todavía se pueden usar (para la referencia de la pantalla de entrar)."""
    r = con.execute("SELECT * FROM users WHERE username=? AND active=1", (DEFAULT_ADMIN[0],)).fetchone()
    if r and has_default_password(User.from_row(r), r["pw_hash"]):
        return [{"username": DEFAULT_ADMIN[0], "password": DEFAULT_ADMIN[1]}]
    return []


def bootstrap_admin(con: sqlite3.Connection, username: str, name: str, password: str) -> User | None:
    """Con la base vacía, crea la cuenta de administración inicial; hay que cambiar la contraseña al entrar."""
    if not username or count_users(con) or username.strip().lower() == DEFAULT_ADMIN[0]:
        return None
    return create_user(con, username, name, password, is_admin=True, must_change=True)


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
        "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at > ? AND u.active=1",
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


def email_taken(con: sqlite3.Connection, email: str, except_id: int | None = None) -> bool:
    r = con.execute("SELECT id FROM users WHERE email=? COLLATE NOCASE", (email,)).fetchone()
    return bool(r and r["id"] != except_id)


def redeem_invite(con: sqlite3.Connection, code: str, username: str, name: str, password: str, email: str) -> User:
    if not invite_valid(con, code):
        raise UserError("La invitación no es válida o ha caducado. Pide otra.")
    email = clean_email(email, required=True)
    if email_taken(con, email):
        raise UserError("Ya hay una cuenta con ese correo.")
    user = create_user(con, username, name, password, email=email)
    con.execute("UPDATE invites SET used_by=?, used_at=? WHERE code_hash=?", (user.id, db.now_iso(), token_hash(code)))
    return user


def list_invites(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        "SELECT i.note, i.created_at, i.expires_at, i.used_at, u.username AS used_by_name "
        "FROM invites i LEFT JOIN users u ON u.id=i.used_by ORDER BY i.created_at DESC LIMIT 50"
    )
    return [dict(r) for r in rows]


def bootstrap_email(con: sqlite3.Connection, username: str, email: str | None) -> None:
    """Correo de la cuenta inicial (BODYLENS_ADMIN_EMAIL) si todavía no tiene ninguno."""
    if email:
        con.execute("UPDATE users SET email=? WHERE username=? AND (email IS NULL OR email='')",
                    (clean_email(email), username.strip().lower()))


def update_bridge(con: sqlite3.Connection, user_id: int, sheet_id: str | None, apps_script_url: str | None) -> None:
    sheet_id = (sheet_id or "").strip() or None
    apps_script_url = (apps_script_url or "").strip() or None
    if sheet_id and not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", sheet_id):
        raise UserError("El ID de la hoja no parece válido.")
    if apps_script_url and not apps_script_url.startswith("https://script.google.com/"):
        raise UserError("La URL del Apps Script tiene que empezar por https://script.google.com/.")
    con.execute("UPDATE users SET sheet_id=?, apps_script_url=? WHERE id=?", (sheet_id, apps_script_url, user_id))
