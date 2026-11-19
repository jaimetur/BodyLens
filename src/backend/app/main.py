"""Servidor de BodyLens (FastAPI): arranque, seguridad común y rutas de cada módulo."""
from __future__ import annotations

import asyncio
import contextlib
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.accounts import access_requests, users
from app.admin import routes as admin_routes
from app.accounts import routes as accounts_routes
from app.accounts.users import UserError
from app.core import config, db, version
from app.core.deps import CSRF_HEADER
from app.couples import routes as couples_routes
from app.data import routes as data_routes
from app.mail import routes as mail_routes
from app.sync import routes as sync_routes
from app.sync import service as sync_service
from app.web import routes as web_routes

log = logging.getLogger("bodylens")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    s = config.settings
    with db.tx() as con:
        if users.bootstrap_admin(con, s.admin_username, s.admin_name, s.admin_password):
            log.warning("Creada la cuenta de administración «%s» con la contraseña provisional: cámbiala al entrar.",
                        s.admin_username)
        if users.bootstrap_default_admin(con):
            log.warning("Creada la cuenta «%s» con la contraseña por defecto «%s»: cámbiala cuanto antes.", *users.DEFAULT_ADMIN)
        try:
            users.bootstrap_email(con, s.admin_username, s.admin_email)
        except UserError:
            log.warning("BODYLENS_ADMIN_EMAIL no es un correo válido.")
    task = asyncio.create_task(sync_service.scheduler_loop()) if s.scheduler_enabled else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="BodyLens", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def guard(request: Request, call_next):
    path = request.url.path
    # contra CSRF: toda escritura en la API lleva una cabecera propia (un formulario de otra web no puede ponerla)
    if path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS") \
            and not path.startswith("/api/ingest/") and request.headers.get(CSRF_HEADER) != "1":
        return JSONResponse({"detail": "Falta la cabecera de la app."}, status_code=403)
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    if path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


@app.get("/api/version")
def api_version():
    """Versión del código servido: la página la compara con la suya para avisar de que hay una nueva."""
    return version.current()


@app.get("/healthz")
def healthz():
    with db.ro() as con:
        con.execute("SELECT 1").fetchone()
    return {"ok": True}


# el orden importa: las páginas y ficheros estáticos (con la ruta comodín /{name}) van al final
for r in (accounts_routes.router, access_requests.router, admin_routes.router, couples_routes.router, data_routes.router,
          sync_routes.router, mail_routes.router, web_routes.router):
    app.include_router(r)
