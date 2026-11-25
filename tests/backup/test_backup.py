"""Backups (core/backup.py): schedule, retention, copies of earlier versions, backing up and restoring in a test
database (the DATA_DIR of the env fixture, never a real one)."""
import sqlite3
import time
import zipfile
from datetime import datetime, timedelta

import pytest

from app.core import backup as bk

TZ = bk.TZ


def _b(name, when, level="full", origin="scheduled"):
    return {"name": name, "level": level, "origin": origin, "size": 1, "created_at": when.isoformat()}


def test_defaults_are_meetgos():
    assert {k: bk.DEFAULTS[k] for k in ("enabled", "recurrence", "execution_time", "light_backups", "full_backup_day",
                                         "keep_days", "keep_weeks", "keep_months", "components")} == {
        "enabled": True, "recurrence": "daily", "execution_time": "03:30", "light_backups": True, "full_backup_day": 6,
        "keep_days": 15, "keep_weeks": 12, "keep_months": 120, "components": ["database", "files"]}


def test_next_run():
    cfg = {**bk.DEFAULTS}
    wed = datetime(2026, 11, 25, 10, 0, tzinfo=TZ)
    assert bk.next_run(cfg, wed) == datetime(2026, 11, 26, 3, 30, tzinfo=TZ)
    assert bk.next_run(cfg, datetime(2026, 11, 25, 3, 0, tzinfo=TZ)) == datetime(2026, 11, 25, 3, 30, tzinfo=TZ)
    assert bk.next_run({**cfg, "recurrence": "hourly"}, wed) == datetime(2026, 11, 25, 10, 30, tzinfo=TZ)
    assert bk.next_run({**cfg, "recurrence": "every_4_hours"}, wed) == datetime(2026, 11, 25, 11, 30, tzinfo=TZ)
    assert bk.next_run({**cfg, "recurrence": "weekly", "weekly_day": 6}, wed) == datetime(2026, 11, 29, 3, 30, tzinfo=TZ)
    assert bk.next_run({**cfg, "recurrence": "monthly", "monthly_day": 31}, wed) == datetime(2026, 11, 30, 3, 30, tzinfo=TZ)
    assert bk.next_run({**cfg, "enabled": False}, wed) is None


def test_light_between_the_sunday_full_backups():
    cfg = {**bk.DEFAULTS}
    sun = datetime(2026, 11, 29, 3, 30, tzinfo=TZ)
    assert bk.scheduled_level(cfg, [], sun) == "full"
    made = [_b("full/a.zip", sun)]
    assert bk.scheduled_level(cfg, made, sun + timedelta(days=1)) == "light"           # Monday
    assert bk.scheduled_level(cfg, made, sun + timedelta(days=7)) == "full"            # next Sunday
    # a full backup missed on Sunday is made on the next day
    assert bk.scheduled_level(cfg, [_b("full/b.zip", sun - timedelta(days=7))], sun + timedelta(days=1)) == "full"
    assert bk.scheduled_level({**cfg, "recurrence": "weekly"}, made, sun + timedelta(days=1)) == "full"


def test_retention_keeps_days_weeks_and_months_and_never_hand_made_or_older_copies():
    cfg = {**bk.DEFAULTS, "keep_days": 3, "keep_weeks": 2, "keep_months": 3}
    now = datetime(2026, 11, 25, 4, 0, tzinfo=TZ)
    days = [_b(f"light/d{i}.zip", now - timedelta(days=i), "light") for i in range(10)]
    fulls = [_b(f"full/f{i}.zip", now - timedelta(days=7 * i)) for i in range(20)]
    manual = _b("full/m.zip", now - timedelta(days=400), origin="manual")
    pre = _b("light/p.zip", now - timedelta(days=400), "light", origin="prerestore")
    legacy = _b("bodylens-2025-01-01.db", now - timedelta(days=330), "light", origin="legacy")
    gone = {b["name"] for b in bk.retention(cfg, days + fulls + [manual, pre, legacy], now)}
    assert {"light/d0.zip", "light/d1.zip", "light/d2.zip"}.isdisjoint(gone)        # the last 3 days
    assert {f"light/d{i}.zip" for i in range(3, 10)} <= gone
    assert "full/f0.zip" not in gone and "full/f1.zip" not in gone                  # newest of the last 2 weeks
    assert "full/f4.zip" not in gone and "full/f8.zip" not in gone                  # newest of October and September
    assert "full/f2.zip" in gone and "full/f19.zip" in gone
    assert {"full/m.zip", "light/p.zip", "bodylens-2025-01-01.db"}.isdisjoint(gone)


def test_copies_of_earlier_versions_are_listed_and_kept(env):
    f = bk.default_folder()
    f.mkdir(parents=True)
    sqlite3.connect(f / "bodylens-2026-11-24.db").close()
    sqlite3.connect(f / "antes-de-laura-20261119.db").close()
    found = {b["name"]: b for b in bk.list_backups()}
    assert found["bodylens-2026-11-24.db"]["origin"] == "legacy" and found["bodylens-2026-11-24.db"]["level"] == "light"
    assert found["bodylens-2026-11-24.db"]["created_at"].startswith("2026-11-24T03:30")
    assert not bk.retention(bk.get_config(), list(found.values()), datetime.now(TZ))


def _wait(client, tid):
    for _ in range(200):
        t = client.get(f"/api/admin/backups/task/{tid}").json()
        if t["state"] != "running":
            return t
        time.sleep(0.05)
    raise AssertionError("the task did not finish")


def test_back_up_and_restore_in_a_test_database(client, make_user, login, env):
    from app.core import config, db
    make_user("jefa", admin=True)
    make_user("laura")
    a = login("jefa")
    (config.settings.data_dir / "users" / "9").mkdir(parents=True)
    (config.settings.data_dir / "users" / "9" / "workbook.xlsx").write_bytes(b"before")
    assert a.get("/api/admin/backups").json()["settings"]["keep_days"] == 15            # the defaults, with nothing saved
    t = _wait(a, a.post("/api/admin/backups/run", json={"level": "full"}).json()["id"])
    assert t["state"] == "done", t
    full = t["file"]
    with zipfile.ZipFile(bk.default_folder() / full) as z:
        names = z.namelist()
    assert "database/bodylens.db" in names and "files/users/9/workbook.xlsx" in names and "manifest.json" in names
    assert not any(n.startswith("files/secrets") for n in names)
    # after the backup: one more account, a changed file and a changed backup setting
    make_user("pepa")
    (config.settings.data_dir / "users" / "9" / "workbook.xlsx").write_bytes(b"after")
    cfg = a.get("/api/admin/backups").json()["settings"]
    a.put("/api/admin/backups/settings", json={**cfg, "keep_days": 30})
    m = a.post("/api/admin/backups/inspect", json={"name": full}).json()
    assert m["has_database"] and m["has_files"] and m["file_count"] == 1
    t = _wait(a, a.post("/api/admin/backups/restore", json={"name": full, "parts": ["database", "files"]}).json()["id"])
    assert t["state"] == "done", t
    with db.ro() as con:
        assert not con.execute("SELECT 1 FROM users WHERE username='pepa'").fetchone()            # as in the backup
    assert (config.settings.data_dir / "users" / "9" / "workbook.xlsx").read_bytes() == b"before"
    st = a.get("/api/admin/backups").json()                 # still signed in: the open sessions are kept
    assert st["settings"]["keep_days"] == 30                                                      # kept
    assert {b["origin"] for b in st["backups"]} == {"manual", "prerestore"}                       # the undo copy
    r = a.get("/api/admin/backups/download", params={"name": full})
    assert r.status_code == 200 and r.content[:2] == b"PK"
    assert a.get("/api/admin/backups/download", params={"name": "../bodylens.db"}).status_code == 404
    assert a.get("/api/admin/backups/files", params={"path": "/etc"}).status_code == 400
    assert a.post("/api/admin/backups/delete", json={"name": full}).json()["ok"]
    assert login("laura").get("/api/admin/backups").status_code == 403


def test_restoring_a_copy_of_an_earlier_version(client, make_user, login, env):
    from app.core import config, db
    make_user("jefa", admin=True)
    f = bk.default_folder()
    f.mkdir(parents=True)
    src, out = sqlite3.connect(config.settings.db_path), sqlite3.connect(f / "bodylens-2026-11-24.db")
    src.backup(out)
    out.close()
    src.close()
    make_user("pepa")
    a = login("jefa")
    t = _wait(a, a.post("/api/admin/backups/restore", json={"name": "bodylens-2026-11-24.db", "parts": ["database"]}).json()["id"])
    assert t["state"] == "done", t
    with db.ro() as con:
        assert not con.execute("SELECT 1 FROM users WHERE username='pepa'").fetchone()


def test_the_scheduler_counts_from_its_first_round_and_applies_the_retention(env, make_user):
    make_user("jefa")
    start = datetime(2026, 11, 28, 12, 0, tzinfo=TZ)                    # a Saturday
    assert not bk.scheduled_once(start)                                  # the first round only notes the start
    assert not bk.scheduled_once(start + timedelta(hours=1))
    assert bk.scheduled_once(datetime(2026, 11, 29, 3, 31, tzinfo=TZ))   # Sunday: the full one
    assert bk.scheduled_once(datetime(2026, 11, 30, 3, 31, tzinfo=TZ))   # Monday: light
    levels = sorted(b["level"] for b in bk.list_backups())
    assert levels == ["full", "light"]
    assert not bk.scheduled_once(datetime(2026, 11, 30, 10, 0, tzinfo=TZ))
