"""Servidor de BodyLens (FastAPI)."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app import config, db, docstore, frontend, seed, sync, users, workbook
from app.security import login_throttle
from app.users import User, UserError

log = logging.getLogger("bodylens")
COOKIE = "bl_session"
CSRF_HEADER = "x-bodylens"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    s = config.settings
    with db.tx() as con:
        if users.bootstrap_admin(con, s.admin_username, s.admin_name, s.admin_password):
            log.warning("Creada la cuenta de administración «%s» con la contraseña provisional: cámbiala al entrar.",
                        s.admin_username)
    task = None
    if config.settings.scheduler_enabled:
        task = asyncio.create_task(sync.scheduler_loop())
    yield
    if task:
        task.cancel()


app = FastAPI(title="BodyLens", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


# ---------- seguridad básica ----------

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


def _token(request: Request) -> str | None:
    return request.cookies.get(COOKIE)


def optional_user(request: Request) -> User | None:
    with db.ro() as con:
        return users.session_user(con, _token(request))


def current_user(request: Request) -> User:
    u = optional_user(request)
    if not u:
        raise HTTPException(401, "Inicia sesión.")
    return u


def admin_user(u: User = Depends(current_user)) -> User:
    if not u.is_admin:
        raise HTTPException(403, "Solo para administradores.")
    return u


def _set_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(COOKIE, token, max_age=config.settings.session_days * 86400, httponly=True,
                    secure=config.settings.cookie_secure, samesite="lax", path="/")


def _bad(e: Exception, code: int = 400):
    raise HTTPException(code, str(e))


# ---------- acceso ----------

class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(body: LoginIn, request: Request, response: Response):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "?").split(",")[0].strip()
    keys = (f"ip:{ip}", f"user:{body.username.strip().lower()}")
    if any(login_throttle.blocked(k) for k in keys):
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    with db.tx() as con:
        u = users.authenticate(con, body.username, body.password)
        if not u:
            for k in keys:
                login_throttle.fail(k)
            raise HTTPException(401, "Usuario o contraseña incorrectos.")
        token = users.create_session(con, u.id)
    login_throttle.reset(keys[1])
    _set_cookie(response, token)
    return {"ok": True, "user": u.public(), "mustChange": u.must_change}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    with db.tx() as con:
        users.delete_session(con, _token(request))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


class RegisterIn(BaseModel):
    code: str
    username: str
    name: str
    password: str


@app.get("/api/invite/{code}")
def invite_info(code: str):
    with db.ro() as con:
        return {"valid": users.invite_valid(con, code)}


@app.post("/api/register")
def register(body: RegisterIn, request: Request, response: Response):
    ip = request.client.host if request.client else "?"
    if login_throttle.blocked(f"reg:{ip}"):
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    try:
        with db.tx() as con:
            u = users.redeem_invite(con, body.code, body.username, body.name, body.password)
            token = users.create_session(con, u.id)
    except UserError as e:
        login_throttle.fail(f"reg:{ip}")
        _bad(e)
    _set_cookie(response, token)
    return {"ok": True, "user": u.public()}


# ---------- cuenta ----------

def _me(con, u: User) -> dict:
    partner = users.get_user(con, u.partner_id) if u.partner_id else None
    inc = con.execute("SELECT u.username, u.name FROM partner_requests r JOIN users u ON u.id=r.from_id WHERE r.to_id=?",
                      (u.id,)).fetchall()
    out = con.execute("SELECT u.username, u.name FROM partner_requests r JOIN users u ON u.id=r.to_id WHERE r.from_id=?",
                      (u.id,)).fetchall()
    return {
        "user": u.public(),
        "partner": {"username": partner.username, "name": partner.name, "since": u.partner_since} if partner else None,
        "requests": {"incoming": [dict(r) for r in inc], "outgoing": [dict(r) for r in out]},
        "sources": {"sheet": bool(u.sheet_id), "appsScript": bool(u.apps_script_url)},
        "sync": workbook.meta(u.id),
        "syncIntervalMin": config.settings.sync_interval_min,
    }


@app.get("/api/me")
def me(u: User = Depends(current_user)):
    with db.ro() as con:
        return _me(con, u)


class PasswordIn(BaseModel):
    current: str
    new: str


@app.post("/api/me/password")
def change_password(body: PasswordIn, request: Request, response: Response, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            if not users.authenticate(con, u.username, body.current):
                raise UserError("La contraseña actual no es correcta.")
            users.set_password(con, u.id, body.new)
            token = users.create_session(con, u.id)
    except UserError as e:
        _bad(e)
    _set_cookie(response, token)
    return {"ok": True}


class FirstIn(BaseModel):
    username: str
    name: str
    password: str


@app.post("/api/me/first")
def first_login(body: FirstIn, response: Response, u: User = Depends(current_user)):
    """Primera entrada con la contraseña provisional: usuario, nombre y contraseña propios."""
    if not u.must_change:
        raise HTTPException(409, "Tu contraseña ya es la tuya; cámbiala en «Contraseña».")
    try:
        with db.tx() as con:
            users.rename(con, u.id, body.username, body.name)
            users.set_password(con, u.id, body.password)
            token = users.create_session(con, u.id)
    except UserError as e:
        _bad(e)
    _set_cookie(response, token)
    return {"ok": True}


class NameIn(BaseModel):
    name: str


@app.post("/api/me/name")
def change_name(body: NameIn, u: User = Depends(current_user)):
    name = body.name.strip()
    if not name or len(name) > 80:
        raise HTTPException(400, "Escribe tu nombre (hasta 80 caracteres).")
    with db.tx() as con:
        con.execute("UPDATE users SET name=? WHERE id=?", (name, u.id))
    return {"ok": True}


# ---------- importar una copia del artefacto ----------

@app.post("/api/import")
async def import_copy(request: Request, u: User = Depends(current_user)):
    """Importa en la cuenta una copia de BodyLens: snap.json o la «Copia completa (JSON)» de Ajustes.
    Cuerpo: {copy: <contenido del fichero>, profile: null | "<id del perfil de la copia>", withProfiles: bool}"""
    body = await _json_body(request)
    if not isinstance(body, dict):
        raise HTTPException(400, "Petición no válida.")
    try:
        with db.tx() as con:
            n = seed.import_copy(con, u, body.get("copy"), body.get("profile") or None, bool(body.get("withProfiles")))
    except (seed.ImportError_, docstore.DocError) as e:
        _bad(e)
    return {"ok": True, "documents": n}


# ---------- pareja ----------

class PartnerIn(BaseModel):
    username: str
    since: str | None = None


def _valid_since(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        raise HTTPException(400, "La fecha no es válida.")


@app.post("/api/partner/request")
def partner_request(body: PartnerIn, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        if not other or other.id == u.id:
            raise HTTPException(404, "No hay ninguna otra cuenta con ese usuario.")
        if u.partner_id or other.partner_id:
            raise HTTPException(409, "Alguna de las dos cuentas ya está unida a otra.")
        # si la otra persona ya lo había pedido, se unen directamente
        prev = con.execute("SELECT since FROM partner_requests WHERE from_id=? AND to_id=?", (other.id, u.id)).fetchone()
        if prev:
            docstore.link_partners(con, u, other, _valid_since(body.since) or prev["since"])
            con.execute("DELETE FROM partner_requests WHERE from_id IN (?,?) OR to_id IN (?,?)", (u.id, other.id, u.id, other.id))
            return {"ok": True, "linked": True}
        con.execute("INSERT INTO partner_requests(from_id, to_id, since, created_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(from_id, to_id) DO UPDATE SET since=excluded.since",
                    (u.id, other.id, _valid_since(body.since), db.now_iso()))
    return {"ok": True, "linked": False}


@app.post("/api/partner/accept")
def partner_accept(body: PartnerIn, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        req = other and con.execute("SELECT since FROM partner_requests WHERE from_id=? AND to_id=?",
                                    (other.id, u.id)).fetchone()
        if not req:
            raise HTTPException(404, "Esa petición ya no existe.")
        try:
            docstore.link_partners(con, u, other, _valid_since(body.since) or req["since"])
        except docstore.DocError as e:
            _bad(e, 409)
        con.execute("DELETE FROM partner_requests WHERE from_id IN (?,?) OR to_id IN (?,?)", (u.id, other.id, u.id, other.id))
    return {"ok": True}


@app.post("/api/partner/reject")
def partner_reject(body: PartnerIn, u: User = Depends(current_user)):
    with db.tx() as con:
        other = users.get_by_username(con, body.username)
        if other:
            con.execute("DELETE FROM partner_requests WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
                        (other.id, u.id, u.id, other.id))
    return {"ok": True}


@app.post("/api/partner/unlink")
def partner_unlink(u: User = Depends(current_user)):
    with db.tx() as con:
        docstore.unlink_partner(con, u)
    return {"ok": True}


# ---------- administración ----------

class InviteIn(BaseModel):
    note: str = ""


@app.post("/api/admin/invites")
def admin_invite(body: InviteIn, request: Request, u: User = Depends(admin_user)):
    with db.tx() as con:
        code = users.create_invite(con, u.id, body.note)
    base = config.settings.public_url or str(request.base_url).rstrip("/")
    return {"code": code, "url": f"{base}/registro?c={code}", "days": config.settings.invite_days}


@app.get("/api/admin/invites")
def admin_invites(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"invites": users.list_invites(con)}


@app.get("/api/admin/users")
def admin_users(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"users": [{**x.public(), "sheetId": x.sheet_id or "", "appsScriptUrl": x.apps_script_url or "",
                           "partnerId": x.partner_id, "sync": workbook.meta(x.id)} for x in users.list_users(con)]}


class BridgeIn(BaseModel):
    sheetId: str = ""
    appsScriptUrl: str = ""


@app.put("/api/admin/users/{user_id}/bridge")
def admin_bridge(user_id: int, body: BridgeIn, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            if not users.get_user(con, user_id):
                raise HTTPException(404, "No existe esa cuenta.")
            users.update_bridge(con, user_id, body.sheetId, body.appsScriptUrl)
    except UserError as e:
        _bad(e)
    return {"ok": True}


# ---------- documentos (window.claude «db») ----------

@app.get("/api/docs/{collection}")
def docs_list(collection: str, since: int | None = None, u: User = Depends(current_user)):
    try:
        with db.ro() as con:
            return docstore.list_docs(con, u, collection, since)
    except docstore.DocError as e:
        _bad(e)


@app.get("/api/docs/{collection}/{doc_id}")
def docs_get(collection: str, doc_id: str, u: User = Depends(current_user)):
    try:
        with db.ro() as con:
            d = docstore.get_doc(con, u, collection, doc_id)
    except docstore.DocError as e:
        _bad(e)
    if d is None:
        raise HTTPException(404, "No existe.")
    return d


async def _json_body(request: Request):
    try:
        return await request.json()
    except ValueError:
        raise HTTPException(400, "El cuerpo no es JSON.")


@app.put("/api/docs/{collection}/{doc_id}")
async def docs_put(collection: str, doc_id: str, request: Request, u: User = Depends(current_user)):
    data = await _json_body(request)
    try:
        with db.tx() as con:
            return {"rev": docstore.put_doc(con, u, collection, doc_id, data)}
    except docstore.DocError as e:
        _bad(e)


@app.patch("/api/docs/{collection}/{doc_id}")
async def docs_patch(collection: str, doc_id: str, request: Request, u: User = Depends(current_user)):
    patch = await _json_body(request)
    try:
        with db.tx() as con:
            rev = docstore.update_doc(con, u, collection, doc_id, patch)
            return {"rev": rev, "data": docstore.get_doc(con, u, collection, doc_id)["data"]}
    except docstore.DocError as e:
        _bad(e)


@app.delete("/api/docs/{collection}/{doc_id}")
def docs_delete(collection: str, doc_id: str, u: User = Depends(current_user)):
    try:
        with db.tx() as con:
            return {"rev": docstore.delete_doc(con, u, collection, doc_id)}
    except docstore.DocError as e:
        _bad(e)


# ---------- libro de datos y sincronización ----------

@app.get("/api/workbook/meta")
def workbook_meta(u: User = Depends(current_user)):
    return workbook.meta(u.id)


@app.get("/api/workbook.xlsx")
def workbook_file(request: Request, u: User = Depends(current_user)):
    m = workbook.meta(u.id)
    p = workbook.path_for(u.id)
    if not m["etag"] or not p.exists():
        raise HTTPException(404, "Todavía no hay datos.")
    etag = f'"{m["etag"]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(p, media_type=workbook.XLSX_MIME, headers={"ETag": etag, "Cache-Control": "no-cache"})


@app.post("/api/sync")
async def sync_now(u: User = Depends(current_user)):
    return await sync.sync_user(u)


@app.get("/api/status")
def status(u: User = Depends(current_user)):
    return {"sources": {"sheet": bool(u.sheet_id), "appsScript": bool(u.apps_script_url)}, **workbook.meta(u.id)}


@app.get("/healthz")
def healthz():
    with db.ro() as con:
        con.execute("SELECT 1").fetchone()
    return {"ok": True}


# ---------- páginas y ficheros estáticos ----------

def _server_file(name: str):
    return FileResponse(config.settings.frontend_dir / "server" / name)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    u = optional_user(request)
    if not u:
        return RedirectResponse("/login", status_code=303)
    if u.must_change:
        return RedirectResponse("/cuenta?cambiar=1", status_code=303)
    return HTMLResponse(frontend.page(u.public()), headers={"Cache-Control": "no-store"})


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return _server_file("login.html")


@app.get("/registro", response_class=HTMLResponse)
def register_page():
    return _server_file("registro.html")


@app.get("/cuenta", response_class=HTMLResponse)
def account_page(request: Request):
    if not optional_user(request):
        return RedirectResponse("/login?next=/cuenta", status_code=303)
    return _server_file("cuenta.html")


@app.get("/claude-shim.js")
def shim():
    return FileResponse(config.settings.frontend_dir / "server" / "claude-shim.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/pages.css")
def pages_css():
    return FileResponse(config.settings.frontend_dir / "server" / "pages.css", media_type="text/css")


@app.get("/pages.js")
def pages_js():
    return FileResponse(config.settings.frontend_dir / "server" / "pages.js", media_type="text/javascript")


@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(frontend.MANIFEST, media_type="application/manifest+json")


VENDOR = {"xlsx.full.min.js", "html2canvas-pro.min.js", "jspdf.umd.min.js"}
BRANDING = {"icon.svg", "wordmark.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"}


@app.get("/vendor/{name}")
def vendor(name: str):
    if name not in VENDOR or not (config.settings.vendor_dir / name).exists():
        raise HTTPException(404)
    return FileResponse(config.settings.vendor_dir / name, media_type="text/javascript",
                        headers={"Cache-Control": "public, max-age=604800"})


@app.get("/{name}")
def branding(name: str):
    if name not in BRANDING:
        raise HTTPException(404)
    return FileResponse(config.settings.branding_dir / name, headers={"Cache-Control": "public, max-age=86400"})
