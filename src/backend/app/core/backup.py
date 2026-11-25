"""Backups of BodyLens (Administration → Backups), as MeetGo's.

A backup is one ZIP in a folder of the data directory (DATA_DIR, the server's or the container's, not the browser's):
- manifest.json: when, full or light, made by hand, by the schedule or before a restore, and its content;
- database/bodylens.db: the whole SQLite database, copied with SQLite's backup API (consistent while the server writes);
- files/...: the files BodyLens keeps besides the database (each account's workbook in users/ and the imported sheets
  in import/), only in full backups. The secrets (secrets/: the encryption key and the Google key) never go in a ZIP,
  and neither do what the server makes again by itself (downloads/, landing-media/, translations/).
A light backup is the database alone. Full backups go to <folder>/full and light ones to <folder>/light.

The daily copies of earlier versions (<folder>/bodylens-YYYY-MM-DD.db and other .db files in the folder) are shown as
light backups "from an earlier version": they can be restored or downloaded, and the retention never deletes them.

Restoring replaces, in the parts chosen, what this server has: the whole database (columns added since the backup take
their defaults) and the files the backup has (others are kept). The backup settings and the open sessions of this server
are kept, and a light backup of the current database is made first, so a restore can be undone.

Scheduled backups: hourly, every 4 hours, daily, weekly or monthly, at a time of Madrid; with light backups (hourly,
every 4 hours, daily) the ones between the weekly full backup are light, and a missed full one is made at the next. After
each scheduled backup the retention keeps every scheduled backup of the last N days and, of the full ones, the newest
and the newest of each of the last weeks and months; backups made by hand, before a restore or by earlier versions are
never deleted.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import sqlite3
import tempfile
import threading
import time
import zipfile
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core import config, db

log = logging.getLogger("bodylens.backup")
TZ = ZoneInfo("Europe/Madrid")
FORMAT = 1
LOW_DISK = 5 * 1024 ** 3        # less free space than this shows the disk in red
KEEP_SECTIONS = ("backups", "backup_state")   # this server's backup settings survive a restore
COMPONENTS = ("database", "files")
RECURRENCES = ("hourly", "every_4_hours", "daily", "weekly", "monthly")
LEVELS = ("full", "light")
FILE_DIRS = ("users", "import")  # the files of a full backup, inside the data directory
DEFAULTS = {   # the same as MeetGo's server: daily at 03:30, light from Monday to Saturday and full on Sunday
    "enabled": True, "recurrence": "daily", "weekly_day": 0, "monthly_day": 1, "execution_time": "03:30",
    "light_backups": True, "full_backup_day": 6, "keep_days": 15, "keep_weeks": 12, "keep_months": 120,
    "components": list(COMPONENTS), "backup_path": "",
}


def root() -> Path:
    return Path(config.settings.data_dir).resolve()


def default_folder() -> Path:
    return root() / "backups"


# ---------- settings and paths ----------

def get_config() -> dict:
    cfg = {**DEFAULTS, **(db.get_setting("backups", {}) or {})}
    cfg["backup_path"] = cfg.get("backup_path") or str(default_folder())
    return cfg


def save_config(data: dict) -> None:
    with db.tx() as con:
        db.set_setting(con, "backups", data)


def get_state() -> dict:
    return db.get_setting("backup_state", {}) or {}


def save_state(**changes) -> None:
    with db.tx() as con:
        state = db.get_setting("backup_state", {}) or {}
        state.update(changes)
        db.set_setting(con, "backup_state", state)


def folder() -> Path:
    """The folder of the backups now set."""
    return inside(get_config()["backup_path"])


def inside(path: str | Path) -> Path:
    """A folder of the data directory (nothing outside it can be read or written)."""
    p = Path(path).expanduser()
    p = (p if p.is_absolute() else root() / p).resolve()
    if p != root() and root() not in p.parents:
        raise ValueError("outside")
    return p


def backup_file(where: str | Path, name: str) -> Path:
    """A backup of the folder (a ZIP of its full or light subfolder, or a .db of an earlier version)."""
    f = inside(where)
    p = inside(f / name)
    if p.suffix not in (".zip", ".db") or not p.is_file() or f not in p.parents:
        raise ValueError("no file")
    return p


def list_dirs(path: str | Path) -> dict:
    p = inside(path)
    p.mkdir(parents=True, exist_ok=True)
    dirs = sorted((d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")), key=str.lower)
    return {"path": str(p), "root": str(root()), "parent": str(p.parent) if p != root() else None, "dirs": dirs}


# ---------- what is in a folder ----------

def _origin(name: str) -> str:
    for o in ("manual", "scheduled", "prerestore"):
        if f"-{o}" in name:
            return o
    return "scheduled"


def _when(p: Path) -> datetime:
    # bodylens-<level>-YYYYmmdd-HHMMSS-<origin>.zip, bodylens-YYYY-MM-DD.db (made at 03:30), or the file's time
    parts = p.stem.split("-")
    try:
        if p.suffix == ".db" and len(parts) == 4:
            return datetime(int(parts[1]), int(parts[2]), int(parts[3]), 3, 30, tzinfo=TZ)
        return datetime.strptime(parts[2] + parts[3], "%Y%m%d%H%M%S").replace(tzinfo=TZ)
    except (IndexError, ValueError):
        return datetime.fromtimestamp(p.stat().st_mtime, TZ)


def list_backups(where: str | Path | None = None) -> list[dict]:
    """The ZIPs of <folder>/full and <folder>/light, and the .db copies of earlier versions in the folder, newest first."""
    f = inside(where) if where is not None else folder()
    out = []
    for level, d, pattern in (("full", f / "full", "*.zip"), ("light", f / "light", "*.zip"), ("full", f, "*.zip"),
                              ("light", f, "*.db")):
        if not d.is_dir():
            continue
        for p in d.glob(pattern):
            st = p.stat()
            out.append({"name": str(p.relative_to(f)), "level": level, "origin": "legacy" if p.suffix == ".db" else _origin(p.name),
                        "size": st.st_size, "created_at": _when(p).isoformat()})
    out.sort(key=lambda b: b["created_at"], reverse=True)
    return out


def listing() -> list[dict]:
    return list_backups()


def disk(where: str | Path) -> dict:
    p = inside(where)
    while not p.exists():
        p = p.parent
    u = shutil.disk_usage(p)
    return {"free": u.free, "total": u.total, "used": u.used, "low": u.free < LOW_DISK}


# ---------- the schedule ----------

def _hm(cfg: dict) -> tuple[int, int]:
    try:
        h, m = (int(x) for x in str(cfg.get("execution_time") or "03:30").split(":")[:2])
        return max(0, min(23, h)), max(0, min(59, m))
    except ValueError:
        return 3, 30


def next_run(cfg: dict, after: datetime) -> datetime | None:
    """The first scheduled time after `after` (Madrid time), or None when the schedule is off."""
    if not cfg.get("enabled"):
        return None
    after = after.astimezone(TZ)
    h, m = _hm(cfg)
    rec = cfg.get("recurrence")
    day = after.replace(second=0, microsecond=0)
    if rec == "hourly":
        c = day.replace(minute=m)
        return c if c > after else c + timedelta(hours=1)
    if rec == "every_4_hours":
        for i in range(0, 30):
            c = (day + timedelta(hours=i)).replace(minute=m)
            if c > after and (c.hour - h) % 4 == 0:
                return c
    for i in range(0, 400):
        d = (after + timedelta(days=i)).date()
        if rec == "weekly" and d.weekday() != int(cfg.get("weekly_day", 0)):
            continue
        if rec == "monthly" and d.day != min(int(cfg.get("monthly_day", 1)), monthrange(d.year, d.month)[1]):
            continue
        c = datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)
        if c > after:
            return c
    return None


def light_schedule(cfg: dict) -> bool:
    return bool(cfg.get("light_backups")) and cfg.get("recurrence") in ("hourly", "every_4_hours", "daily")


def scheduled_level(cfg: dict, backups: list[dict], now: datetime) -> str:
    """Full, unless light backups are on and this week's full backup (from its day) was already made."""
    if not light_schedule(cfg):
        return "full"
    today = now.astimezone(TZ).date()
    since = today - timedelta(days=(today.weekday() - int(cfg.get("full_backup_day", 0))) % 7)
    for b in backups:
        if b["level"] == "full" and b["origin"] == "scheduled" and datetime.fromisoformat(b["created_at"]).date() >= since:
            return "light"
    return "full"


def retention(cfg: dict, backups: list[dict], now: datetime) -> list[dict]:
    """The scheduled backups to delete: kept are those of the last keep_days days (today included) and, of the full ones,
    the newest and the newest of each of the last keep_weeks weeks and keep_months months."""
    today = now.astimezone(TZ).date()
    sched = [b for b in backups if b["origin"] == "scheduled"]
    keep: set[str] = set()
    first_day = today - timedelta(days=max(1, int(cfg.get("keep_days", 7))) - 1)
    for b in sched:
        if datetime.fromisoformat(b["created_at"]).date() >= first_day:
            keep.add(b["name"])
    full = sorted((b for b in sched if b["level"] == "full"), key=lambda b: b["created_at"], reverse=True)
    if full:
        keep.add(full[0]["name"])
    weeks = {(today - timedelta(weeks=i)).isocalendar()[:2] for i in range(int(cfg.get("keep_weeks", 4)))}
    months, y, mth = set(), today.year, today.month
    for _ in range(int(cfg.get("keep_months", 6))):
        months.add((y, mth))
        y, mth = (y, mth - 1) if mth > 1 else (y - 1, 12)
    seen_w, seen_m = set(), set()
    for b in full:   # newest first: the first of each week or month is its newest
        d = datetime.fromisoformat(b["created_at"]).date()
        w, mo = d.isocalendar()[:2], (d.year, d.month)
        if w in weeks and w not in seen_w:
            seen_w.add(w)
            keep.add(b["name"])
        if mo in months and mo not in seen_m:
            seen_m.add(mo)
            keep.add(b["name"])
    return [b for b in sched if b["name"] not in keep]


# ---------- tasks (one backup or restore at a time) ----------

@dataclass
class Task:
    id: str
    kind: str                  # backup | restore
    state: str = "running"     # running | done | error
    step: str = ""
    progress: float = 0.0
    message: str = ""
    file: str = ""
    started: float = field(default_factory=time.time)

    def out(self) -> dict:
        return {"id": self.id, "kind": self.kind, "state": self.state, "step": self.step,
                "progress": round(self.progress, 3), "message": self.message, "file": self.file}


_lock = threading.Lock()
_tasks: dict[str, Task] = {}


def current_task() -> Task | None:
    live = [t for t in _tasks.values() if t.state == "running"]
    if live:
        return live[0]
    done = sorted(_tasks.values(), key=lambda t: t.started, reverse=True)
    return done[0] if done and time.time() - done[0].started < 600 else None


def get_task(task_id: str) -> Task | None:
    return _tasks.get(task_id)


def busy() -> bool:
    return _lock.locked()


def start(kind: str, work) -> Task:
    """Runs work(task) in a thread; one backup or restore at a time."""
    t = Task(id=os.urandom(6).hex(), kind=kind)
    _tasks[t.id] = t

    def run():
        with _lock:
            try:
                work(t)
                t.state, t.progress = "done", 1.0
            except Exception as e:   # noqa: BLE001
                log.exception("backup task %s failed", kind)
                t.state, t.message = "error", str(e) or e.__class__.__name__
    threading.Thread(target=run, daemon=True).start()
    return t


# ---------- making a backup ----------

def _files() -> list[Path]:
    out = []
    for d in FILE_DIRS:
        base = root() / d
        if base.is_dir():
            out += [p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".partial")]
    return out


def estimate(level: str, components: list[str], where: Path) -> int:
    """Bytes a backup needs: the latest one of the same level, else the database's size and the files'."""
    same = [b for b in list_backups(where) if b["level"] == level and b["origin"] != "legacy"]
    if same:
        return int(same[0]["size"] * 1.2) + 20 * 1024 ** 2
    total = config.settings.db_path.stat().st_size if "database" in components and config.settings.db_path.exists() else 0
    if level == "full" and "files" in components:
        total += sum(p.stat().st_size for p in _files())
    return total + 20 * 1024 ** 2


def make_backup(t: Task, *, level: str, origin: str, components: list[str], where: str | Path, by: str = "",
                when: datetime | None = None) -> Path:
    where = inside(where)
    if level == "light":
        components = [c for c in components if c != "files"]
    if not components:
        raise ValueError("Nada que copiar.")
    dest = where / level
    dest.mkdir(parents=True, exist_ok=True)
    for leftover in dest.glob("*.partial"):   # what an interrupted backup left
        leftover.unlink(missing_ok=True)
    need = estimate(level, components, where)
    if shutil.disk_usage(dest).free < need:
        raise OSError(f"No hay espacio libre suficiente en {dest}: hacen falta unos {need // 1024 ** 2} MB.")
    now = (when or datetime.now(TZ)).astimezone(TZ)
    name = f"bodylens-{level}-{now:%Y%m%d-%H%M%S}-{origin}.zip"
    partial = dest / (name + ".partial")
    manifest = {"app": "BodyLens", "format": FORMAT, "created_at": now.isoformat(), "level": level, "origin": origin,
                "by": by, "components": components, "files": 0}
    t.step, t.file = "database", str((dest / name).relative_to(where))
    try:
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            if "database" in components:
                with tempfile.TemporaryDirectory(dir=dest) as tmp:
                    copy = Path(tmp) / "bodylens.db"
                    src, out = sqlite3.connect(config.settings.db_path), sqlite3.connect(copy)
                    try:
                        src.backup(out)
                        manifest["tables"] = [r[0] for r in out.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                    finally:
                        out.close()
                        src.close()
                    z.write(copy, "database/bodylens.db")
                t.progress = 0.6 if "files" in components else 1.0
            if "files" in components:
                t.step = "files"
                files = _files()
                for i, p in enumerate(files):
                    z.write(p, "files/" + str(p.relative_to(root())))
                    t.progress = 0.6 + 0.4 * (i + 1) / max(1, len(files))
                manifest["files"] = len(files)
            z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
        final = dest / name
        partial.replace(final)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    save_state(last_success=now.isoformat(), last_level=level, last_size=final.stat().st_size, problem=None)
    t.message = final.name
    return final


# ---------- restoring ----------

def read_manifest(path: Path) -> dict:
    if path.suffix == ".db":   # a copy of an earlier version: the database alone
        return {"level": "light", "origin": "legacy", "created_at": _when(path).isoformat(), "has_database": True,
                "has_files": False, "file_count": 0, "table_count": _tables(path)}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        try:
            m = json.loads(z.read("manifest.json"))
        except KeyError:
            m = {"level": "full" if any(n.startswith("files/") for n in names) else "light"}
        m["has_database"] = "database/bodylens.db" in names
        m["has_files"] = any(n.startswith("files/") for n in names)
        m["file_count"] = sum(1 for n in names if n.startswith("files/") and not n.endswith("/"))
        m["table_count"] = len(m.get("tables") or [])
    return m


def _tables(path: Path) -> int:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        con.close()


def _restore_database(t: Task, source: Path) -> None:
    """Copies the backup's database over the live one with SQLite's backup API (the server keeps running), keeps this
    server's backup settings and open sessions (nobody is signed out) and brings the schema up to date."""
    kept = {k: db.get_setting(k, None) for k in KEEP_SECTIONS}
    with db.ro() as con:
        sessions = [tuple(r) for r in con.execute("SELECT token_hash, user_id, created_at, expires_at FROM sessions")]
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        src.close()
        raise ValueError("La base de datos de la copia está dañada.")
    live = sqlite3.connect(config.settings.db_path, timeout=60)
    try:
        src.backup(live)
    finally:
        live.close()
        src.close()
    t.progress = 0.7
    db.init_db()   # columns and tables added since the backup
    with db.tx() as con:
        for k, v in kept.items():
            if v is None:
                con.execute("DELETE FROM settings WHERE key=?", (k,))
            else:
                db.set_setting(con, k, v)
        con.execute("DELETE FROM sessions")
        con.executemany("INSERT OR IGNORE INTO sessions(token_hash, user_id, created_at, expires_at) SELECT ?,?,?,? "
                        "WHERE EXISTS (SELECT 1 FROM users WHERE id=?)", [(*r, r[1]) for r in sessions])


def _restore_files(t: Task, z: zipfile.ZipFile) -> int:
    names = [n for n in z.namelist() if n.startswith("files/") and not n.endswith("/")]
    base = root()
    for i, n in enumerate(names):
        target = (base / n[len("files/"):]).resolve()
        if base not in target.parents or target.relative_to(base).parts[0] not in FILE_DIRS:
            continue   # only into the folders a backup holds
        target.parent.mkdir(parents=True, exist_ok=True)
        with z.open(n) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
        t.progress = 0.8 + 0.2 * (i + 1) / max(1, len(names))
    return len(names)


def restore(t: Task, *, path: Path, parts: list[str], where: str | Path, by: str = "") -> None:
    # first, a light backup of what there is now: the restore can be undone
    t.step = "safety"
    if "database" in parts:
        make_backup(Task(id="pre", kind="backup"), level="light", origin="prerestore", components=["database"], where=where, by=by)
    if path.suffix == ".db":
        if "database" in parts:
            t.step = "database"
            _restore_database(t, path)
    else:
        with zipfile.ZipFile(path) as z:
            if "database" in parts:
                t.step = "database"
                with tempfile.TemporaryDirectory(dir=root()) as tmp:
                    z.extract("database/bodylens.db", tmp)
                    _restore_database(t, Path(tmp) / "database" / "bodylens.db")
            if "files" in parts:
                t.step = "files"
                _restore_files(t, z)
    t.message = path.name


# ---------- the scheduler ----------

def scheduled_once(now: datetime | None = None) -> bool:
    """Makes the scheduled backup when it is due (and then applies the retention). True when one was made."""
    now = now or datetime.now(TZ)
    cfg, state = get_config(), get_state()
    if not cfg.get("enabled") or busy():
        return False
    if not state.get("last_scheduled_at") and not state.get("enabled_at"):
        save_state(enabled_at=now.isoformat())   # the first time: the schedule counts from now
        return False
    since = datetime.fromisoformat(state.get("last_scheduled_at") or state["enabled_at"])
    due = next_run(cfg, since)
    if not due or now < due:
        return False
    where = cfg["backup_path"]
    save_state(last_scheduled_at=now.isoformat())
    level = scheduled_level(cfg, list_backups(where), now)
    components = list(cfg.get("components") or COMPONENTS)
    t = Task(id=os.urandom(6).hex(), kind="backup")
    _tasks[t.id] = t
    with _lock:
        try:
            try:
                make_backup(t, level=level, origin="scheduled", components=components, where=where, when=now)
            except OSError as e:
                if level == "full" and light_schedule(cfg):   # no room for the full one: a light one instead
                    make_backup(t, level="light", origin="scheduled", components=components, where=where, when=now)
                    save_state(problem=str(e))
                else:
                    raise
            t.state, t.progress = "done", 1.0
        except Exception as e:   # noqa: BLE001
            t.state, t.message = "error", str(e)
            log.exception("scheduled backup failed")
            save_state(problem=str(e))
            return False
    for b in retention(cfg, list_backups(where), now):
        try:
            (inside(where) / b["name"]).unlink(missing_ok=True)
            log.info("backup retention: deleted %s", b["name"])
        except OSError:
            log.warning("backup retention: could not delete %s", b["name"])
    return True


async def loop() -> None:
    """Every 30 seconds, the scheduled backup if it is due."""
    while True:
        await asyncio.sleep(30)
        try:
            await asyncio.to_thread(scheduled_once)
        except asyncio.CancelledError:
            raise
        except Exception:   # noqa: BLE001
            log.exception("backup scheduler round failed")
