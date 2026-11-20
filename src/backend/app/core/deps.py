"""Dependencias y utilidades comunes de las rutas: sesión, administración, cookie y errores."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, Response

from app.accounts import users
from app.accounts.users import User
from app.core import config, db

COOKIE = "bl_session"
CSRF_HEADER = "x-bodylens"


def session_token(request: Request) -> str | None:
    return request.cookies.get(COOKIE)


def optional_user(request: Request) -> User | None:
    with db.ro() as con:
        return users.session_user(con, session_token(request))


def signed_in_user(request: Request) -> User:
    """Whoever is signed in, even if their subscription is over (to renew it, download their data or delete it)."""
    u = optional_user(request)
    if not u:
        raise HTTPException(401, "Inicia sesión.")
    return u


# what an account whose subscription is over can still do besides reading (it is read-only for 30 days, then deleted)
EXPIRED_OK = ("/api/me", "/api/logout", "/api/me/delete", "/api/play/", "/api/web/")


def current_user(request: Request) -> User:
    u = signed_in_user(request)
    path = request.url.path
    if path == "/api/me" or path.startswith(EXPIRED_OK[1:]) or request.method in ("GET", "HEAD"):
        return u
    from app.billing.routes import expired   # here: billing's routes use these dependencies
    if expired(u.id):
        raise HTTPException(402, "Tu cuenta es de solo lectura porque tu suscripción ha terminado: renuévala para añadir datos o sincronizar.")
    return u


def admin_user(u: User = Depends(current_user)) -> User:
    if not u.is_admin:
        raise HTTPException(403, "Solo para administradores.")
    return u


def set_session_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(COOKIE, token, max_age=config.settings.session_days * 86400, httponly=True,
                    secure=config.settings.cookie_secure, samesite="lax", path="/")


def bad(e: Exception, code: int = 400):
    raise HTTPException(code, str(e))


async def json_body(request: Request):
    try:
        return await request.json()
    except ValueError:
        raise HTTPException(400, "El cuerpo no es JSON.")


def client_ip(request: Request) -> str:
    return request.headers.get("x-forwarded-for", request.client.host if request.client else "?").split(",")[0].strip()


def base_url(request: Request) -> str:
    return config.settings.public_url or str(request.base_url).rstrip("/")
