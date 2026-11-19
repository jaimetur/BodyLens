"""Servidor de BodyLens (FastAPI): arranque, seguridad común y rutas de cada módulo."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.accounts import access_requests, users
from app.admin import routes as admin_routes
from app.accounts import routes as accounts_routes
from app.accounts.users import UserError
from app.core import backup, config, db, version
from app.core.deps import CSRF_HEADER
from app.couples import routes as couples_routes
from app.data import routes as data_routes
from app.mail import routes as mail_routes
from app.help import routes as help_routes
from app.sources import routes as sources_routes
from app.sync import routes as sync_routes
from app.sync import service as sync_service
from app.web import routes as web_routes

log = logging.getLogger("bodylens")


class _HideSecrets(logging.Filter):
    """El registro de accesos nunca muestra secretos: la dirección de envío de Apple Salud (lleva el token) ni los
    códigos y tokens de las URL (OAuth de Withings, invitaciones)."""
    _RX = [(re.compile(r"(/api/ingest/hae/)[^\s?\"]+"), r"\1***"),
           (re.compile(r"([?&](?:code|token|state|c)=)[^&\s\"]+"), r"\1***")]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            args = []
            for a in record.args:
                if isinstance(a, str):
                    for rx, rep in self._RX:
                        a = rx.sub(rep, a)
                args.append(a)
            record.args = tuple(args)
        return True


logging.getLogger("uvicorn.access").addFilter(_HideSecrets())


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
    try:   # phases of the Apple Health nights saved before the «Fases» column existed
        from app.sources import hae
        with db.tx() as con:
            for (uid,) in con.execute("SELECT id FROM users").fetchall():
                hae.rellenar_fases(con, uid)
    except Exception:   # noqa: BLE001 — never block the start-up
        log.exception("Could not fill in the sleep phases")
    tasks = [asyncio.create_task(sync_service.scheduler_loop()), asyncio.create_task(backup.loop())] if s.scheduler_enabled else []
    if s.scheduler_enabled:
        from app.help import translate
        tasks.append(asyncio.create_task(translate.prewarm_loop()))
    yield
    for t in tasks:
        t.cancel()


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
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")  # solo la propia app puede incrustar sus páginas
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
          sync_routes.router, sources_routes.router, mail_routes.router, help_routes.router, web_routes.router):
    app.include_router(r)
