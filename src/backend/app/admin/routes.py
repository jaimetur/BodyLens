"""Rutas del panel de Administración (/admin): cuentas y configuración del correo.
Las invitaciones, peticiones de acceso, fuentes y correo de prueba tienen sus rutas en sus módulos."""
from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.accounts import deletion, users
from app.billing import codes
from app.billing import routes as billing
from app.accounts.users import User, UserError, clean_email
from app.core import crypto, db
from app.core.deps import admin_user, bad, base_url
from app.mail import mailer
from app.sync import workbook
from app.web.page import esc

router = APIRouter()


def _user_row(con, x: User) -> dict:
    r = con.execute("SELECT created_at, requested_at FROM users WHERE id=?", (x.id,)).fetchone()
    partner = users.get_user(con, x.partner_id) if x.partner_id else None
    return {**x.public(), "active": x.active, "createdAt": r["created_at"], "requestedAt": r["requested_at"],
            "partner": partner.username if partner else None, "sheetId": x.sheet_id or "",
            "appsScriptUrl": x.apps_script_url or "", "sync": workbook.meta(x.id), "plan": billing.summary(con, x.id)}


@router.get("/api/admin/accounts")
def accounts(u: User = Depends(admin_user)):
    with db.ro() as con:
        return {"users": [_user_row(con, x) for x in users.list_users(con, active=None)], "me": u.id}


class AccountIn(BaseModel):
    username: str | None = None
    name: str | None = None
    password: str | None = None   # vacío o ausente = no se cambia
    email: str | None = None
    isAdmin: bool | None = None
    active: bool | None = None
    freeUntil: str | None = None   # free access: "lifetime", "YYYY-MM-DD" (until the end of that day) or "none"


@router.patch("/api/admin/accounts/{user_id}")
def edit_account(user_id: int, body: AccountIn, u: User = Depends(admin_user)):
    try:
        with db.tx() as con:
            x = users.get_user(con, user_id)
            if not x:
                raise HTTPException(404, "No existe esa cuenta.")
            if user_id == u.id and (body.isAdmin is False or body.active is False):
                raise UserError("No puedes quitarte a ti mismo la administración ni desactivar tu cuenta.")
            if x.is_admin and x.active and (body.isAdmin is False or body.active is False):
                users.ensure_other_admin(con, user_id)
            if body.username is not None or body.name is not None:
                users.rename(con, user_id, x.username if body.username is None else body.username,
                             x.name if body.name is None else body.name)
            if body.password:
                users.set_password(con, user_id, body.password)   # cierra sus sesiones abiertas
            if body.email is not None:
                users.set_email(con, user_id, body.email)
            if body.isAdmin is not None:
                con.execute("UPDATE users SET is_admin=? WHERE id=?", (int(body.isAdmin), user_id))
            if body.freeUntil is not None:
                _free_until(con, user_id, body.freeUntil)
            if body.active is not None:
                con.execute("UPDATE users SET active=?, requested_at=CASE WHEN ?=1 THEN NULL ELSE requested_at END WHERE id=?",
                            (int(body.active), int(body.active), user_id))
                if not body.active:
                    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    except UserError as e:
        bad(e)
    return {"ok": True}


def _free_until(con, user_id: int, value: str) -> None:
    """Free access of an account: for life, until a day (Europe/Madrid, end of the day) or none."""
    from datetime import datetime, time as dtime
    from zoneinfo import ZoneInfo
    if value == "none":
        con.execute("DELETE FROM grants WHERE user_id=?", (user_id,))
        return
    if value == "lifetime":
        until = None
    else:
        try:
            day = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise UserError("La fecha de fin no es válida.")
        until = int(datetime.combine(day, dtime(23, 59, 59), ZoneInfo("Europe/Madrid")).timestamp() * 1000)
    codes.grant(con, user_id, "admin", until)
    con.execute("DELETE FROM lapses WHERE user_id=?", (user_id,))


class ResetIn(BaseModel):
    email: bool = True


@router.post("/api/admin/accounts/{user_id}/password")
def reset_password(user_id: int, body: ResetIn, request: Request, u: User = Depends(admin_user)):
    """Pone una contraseña provisional (se pide cambiarla al entrar) y la devuelve una sola vez."""
    temp = secrets.token_urlsafe(6)
    with db.tx() as con:
        x = users.get_user(con, user_id)
        if not x:
            raise HTTPException(404, "No existe esa cuenta.")
        users.set_password(con, user_id, temp)
        con.execute("UPDATE users SET must_change=1 WHERE id=?", (user_id,))
    sent = False
    if body.email and x.email and mailer.settings()["configured"]:
        mailer.send_later([x.email], "Tu contraseña provisional", mailer.page("Tu contraseña provisional", [
            f"Hola {esc(x.name.split()[0])},",
            f"{esc(u.name)} ha restablecido la contraseña de tu cuenta <b>{esc(x.username)}</b>. "
            f"Entra con esta contraseña provisional y elige la tuya: <b>{esc(temp)}</b>",
        ], link=("Entrar en BodyLens", f"{base_url(request)}/login")))
        sent = True
    return {"ok": True, "password": temp, "emailed": sent}


@router.delete("/api/admin/accounts/{user_id}")
def delete_account(user_id: int, u: User = Depends(admin_user)):
    """Borra la cuenta y todos sus datos (si tenía pareja, se separan antes: la pareja conserva su copia)."""
    if user_id == u.id:
        raise HTTPException(400, "No puedes borrar tu propia cuenta.")
    with db.tx() as con:
        x = users.get_user(con, user_id)
        if not x:
            raise HTTPException(404, "No existe esa cuenta.")
        try:
            deletion.delete_account(con, x)
        except UserError as e:
            raise HTTPException(400, str(e))
    deletion.delete_files(user_id)
    return {"ok": True}


# ---------- Withings (aplicación de desarrollador) ----------

class WithingsAppIn(BaseModel):
    clientId: str = ""
    clientSecret: str = ""   # vacío = conservar el guardado


@router.get("/api/admin/withings")
def get_withings_app(u: User = Depends(admin_user)):
    from app.sources import withings
    return {"clientId": withings.client_id(), "hasSecret": bool(withings.client_secret()),
            "secretHint": crypto.hint(withings.client_secret()),
            "configured": withings.configured(), "callback": withings.redirect_uri()}


@router.put("/api/admin/withings")
def put_withings_app(body: WithingsAppIn, u: User = Depends(admin_user)):
    from app.sources import withings
    with db.tx() as con:
        withings.save_app(con, body.clientId, body.clientSecret or None)
    return get_withings_app(u)


# ---------- backups (core/backup.py) ----------

class BackupSettingsIn(BaseModel):
    enabled: bool = False
    recurrence: str = Field(default="daily", pattern="^(hourly|every_4_hours|daily|weekly|monthly)$")
    weekly_day: int = Field(default=0, ge=0, le=6)
    monthly_day: int = Field(default=1, ge=1, le=31)
    execution_time: str = Field(default="03:30", pattern=r"^\d{2}:\d{2}$")
    light_backups: bool = False
    full_backup_day: int = Field(default=0, ge=0, le=6)
    keep_days: int = Field(default=7, ge=1, le=3650)
    keep_weeks: int = Field(default=4, ge=0, le=520)
    keep_months: int = Field(default=6, ge=0, le=240)
    components: list[str] = Field(default_factory=lambda: ["database", "files"])
    backup_path: str = ""


class BackupRunIn(BaseModel):
    level: str = Field(pattern="^(full|light)$")


class BackupFileIn(BaseModel):
    path: str = ""
    name: str


class BackupRestoreIn(BackupFileIn):
    parts: list[str] = Field(default_factory=list)


class BackupDirIn(BaseModel):
    path: str = ""
    name: str = Field(min_length=1, max_length=80)


def _bk_folder(path: str) -> str:
    from app.core import backup
    try:
        return str(backup.inside(path or backup.get_config()["backup_path"]))
    except ValueError:
        raise HTTPException(400, "La carpeta tiene que estar dentro de la carpeta de datos.")


def _bk_file(path: str, name: str):
    from app.core import backup
    try:
        return backup.backup_file(_bk_folder(path), name)
    except ValueError:
        raise HTTPException(404, "No existe esa copia.")


def _bk_status() -> dict:
    from app.core import backup
    cfg, state = backup.get_config(), backup.get_state()
    backups = backup.list_backups(cfg["backup_path"])
    by = {lvl: [b for b in backups if b["level"] == lvl] for lvl in backup.LEVELS}
    since = state.get("last_scheduled_at") or state.get("enabled_at")
    nxt = backup.next_run(cfg, datetime.fromisoformat(since) if since else datetime.now(backup.TZ))
    if nxt and nxt < datetime.now(backup.TZ):
        nxt = backup.next_run(cfg, datetime.now(backup.TZ))
    task = backup.current_task()
    newest = lambda lvl: next((b["size"] for b in by[lvl] if b["origin"] != "legacy"), None)   # noqa: E731
    return {
        "settings": cfg, "root": str(backup.root()), "default_path": str(backup.default_folder()),
        "status": {
            "count": len(backups), "size": sum(b["size"] for b in backups),
            "count_full": len(by["full"]), "count_light": len(by["light"]),
            "size_full": sum(b["size"] for b in by["full"]), "size_light": sum(b["size"] for b in by["light"]),
            "latest_full": newest("full"), "latest_light": newest("light"),
            "disk": backup.disk(cfg["backup_path"]),
            "last_success": state.get("last_success") or (backups[0]["created_at"] if backups else None),
            "last_level": state.get("last_level") or (backups[0]["level"] if backups else None),
            "next_run": nxt.isoformat() if nxt else None,
            "next_level": backup.scheduled_level(cfg, backups, nxt) if nxt else None,
            "problem": state.get("problem"),
        },
        "backups": backups,
        "task": task.out() if task else None,
    }


@router.get("/api/admin/backups")
def backups_status(u: User = Depends(admin_user)):
    return _bk_status()


@router.put("/api/admin/backups/settings")
def backups_settings(body: BackupSettingsIn, u: User = Depends(admin_user)):
    """The schedule, the content and the folder of the next backups (scheduled ones included)."""
    from app.core import backup
    data = body.model_dump()
    data["components"] = [c for c in data["components"] if c in backup.COMPONENTS] or list(backup.COMPONENTS)
    data["backup_path"] = _bk_folder(data["backup_path"])
    before = backup.get_config()
    backup.save_config(data)
    if data["enabled"] and not before.get("enabled"):   # the schedule counts from now, not from the last backup made
        backup.save_state(enabled_at=datetime.now(backup.TZ).isoformat(), last_scheduled_at=None)
    return _bk_status()


@router.get("/api/admin/backups/files")
def backups_files(path: str = "", u: User = Depends(admin_user)):
    from app.core import backup
    return backup.list_backups(_bk_folder(path))


@router.get("/api/admin/backups/dirs")
def backups_dirs(path: str = "", u: User = Depends(admin_user)):
    from app.core import backup
    try:
        return backup.list_dirs(_bk_folder(path))
    except OSError as e:
        raise HTTPException(400, str(e))


@router.post("/api/admin/backups/dirs")
def backups_new_dir(body: BackupDirIn, u: User = Depends(admin_user)):
    from app.core import backup
    name = body.name.strip().replace("/", "").replace("\\", "")
    if not name or name.startswith("."):
        raise HTTPException(400, "Ese nombre de carpeta no vale.")
    target = backup.inside(_bk_folder(body.path)) / name
    target.mkdir(parents=True, exist_ok=True)
    return backup.list_dirs(target)


@router.post("/api/admin/backups/run")
def backups_run(body: BackupRunIn, u: User = Depends(admin_user)):
    """Back up now (full or light), with the content and folder saved in the settings."""
    from app.core import backup
    if backup.busy():
        raise HTTPException(409, "Ya hay una copia o una restauración en marcha.")
    cfg = backup.get_config()
    components = list(cfg.get("components") or backup.COMPONENTS)
    if body.level == "light" and components == ["files"]:
        raise HTTPException(400, "Una copia ligera no lleva los ficheros: elige también la base de datos.")
    t = backup.start("backup", lambda t: backup.make_backup(t, level=body.level, origin="manual", components=components,
                                                            where=cfg["backup_path"], by=u.name))
    return t.out()


@router.get("/api/admin/backups/task/{task_id}")
def backups_task(task_id: str, u: User = Depends(admin_user)):
    from app.core import backup
    t = backup.get_task(task_id)
    if not t:
        raise HTTPException(404, "No existe esa tarea.")
    return t.out()


@router.post("/api/admin/backups/inspect")
def backups_inspect(body: BackupFileIn, u: User = Depends(admin_user)):
    """What a backup holds, to choose the parts to restore."""
    from app.core import backup
    try:
        return backup.read_manifest(_bk_file(body.path, body.name))
    except HTTPException:
        raise
    except Exception:   # noqa: BLE001
        raise HTTPException(400, "No se puede leer esa copia.")


@router.post("/api/admin/backups/restore")
def backups_restore(body: BackupRestoreIn, u: User = Depends(admin_user)):
    from app.core import backup
    parts = [p for p in body.parts if p in backup.COMPONENTS]
    if not parts:
        raise HTTPException(400, "Elige qué restaurar.")
    if backup.busy():
        raise HTTPException(409, "Ya hay una copia o una restauración en marcha.")
    path, where = _bk_file(body.path, body.name), _bk_folder(body.path)
    t = backup.start("restore", lambda t: backup.restore(t, path=path, parts=parts, where=where, by=u.name))
    return t.out()


@router.get("/api/admin/backups/download")
def backups_download(name: str, path: str = "", u: User = Depends(admin_user)):
    from fastapi.responses import FileResponse
    p = _bk_file(path, name)
    return FileResponse(p, media_type="application/zip" if p.suffix == ".zip" else "application/octet-stream", filename=p.name)


@router.post("/api/admin/backups/delete")
def backups_delete(body: BackupFileIn, u: User = Depends(admin_user)):
    from app.core import backup
    if backup.busy():
        raise HTTPException(409, "Hay una copia o una restauración en marcha.")
    _bk_file(body.path, body.name).unlink()
    return {"ok": True}


# ---------- correo ----------

class MailIn(BaseModel):
    host: str = ""
    port: int | None = None
    security: str = "ssl"
    username: str = ""
    password: str = ""          # vacío = conservar la guardada
    from_address: str = ""
    from_name: str = "BodyLens"


@router.get("/api/admin/mail")
def get_mail(u: User = Depends(admin_user)):
    return mailer.public_settings()


@router.put("/api/admin/mail")
def put_mail(body: MailIn, u: User = Depends(admin_user)):
    if body.security not in ("ssl", "starttls", "none"):
        raise HTTPException(400, "Seguridad: ssl, starttls o none.")
    try:
        if body.from_address:
            clean_email(body.from_address)
    except UserError:
        raise HTTPException(400, "El remitente no es un correo válido.")
    stored = db.get_setting("mail", {}) or {}
    if body.password:
        password = body.password
    elif stored.get("password_enc"):
        password = crypto.decrypt(stored["password_enc"]) or ""
    else:
        password = stored.get("password", "")   # saved as plain text by older versions
    new = {"host": body.host.strip(), "port": body.port, "security": body.security, "username": body.username.strip(),
           "from_address": body.from_address.strip(), "from_name": body.from_name.strip() or "BodyLens",
           "password_enc": crypto.encrypt(password) if password else None}   # encrypted in the database
    with db.tx() as con:
        db.set_setting(con, "mail", new)
    return mailer.public_settings()
