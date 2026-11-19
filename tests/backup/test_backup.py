import sqlite3


def test_backup_and_prune(env, make_user, monkeypatch):
    from app.core import backup
    make_user("jaimetur")
    monkeypatch.setenv("BACKUP_KEEP", "3")
    for d in ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"]:
        backup.make(d)
    names = [b["name"] for b in backup.listing()]
    assert names == ["bodylens-2026-11-04.db", "bodylens-2026-11-03.db", "bodylens-2026-11-02.db"]
    con = sqlite3.connect(backup.folder() / names[0])
    assert con.execute("SELECT username FROM users").fetchone()[0] == "jaimetur"


def test_backup_admin_routes(client, make_user, login):
    make_user("jaimetur", admin=True)
    make_user("laura")
    a = login("jaimetur")
    name = a.post("/api/admin/backups").json()["name"]
    assert name in [b["name"] for b in a.get("/api/admin/backups").json()["backups"]]
    r = a.get(f"/api/admin/backups/{name}")
    assert r.status_code == 200 and r.content[:15] == b"SQLite format 3"
    assert a.get("/api/admin/backups/../bodylens.db").status_code in (404, 400)
    assert login("laura").get("/api/admin/backups").status_code == 403
