def test_pages_need_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/docs/bascula").status_code == 401


def test_login_and_logout(client, make_user):
    make_user("jaime", "Jaime Tur", admin=True)
    assert client.post("/api/login", json={"username": "jaime", "password": "mala-contraseña"}).status_code == 401
    r = client.post("/api/login", json={"username": "JAIME", "password": "contraseña-larga"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert client.get("/api/me").json()["user"]["name"] == "Jaime Tur"
    client.post("/api/logout")
    assert client.get("/api/me").status_code == 401


def test_writes_need_app_header(client, make_user):
    make_user("jaime")
    client.post("/api/login", json={"username": "jaime", "password": "contraseña-larga"})
    r = client.put("/api/docs/bascula/peso", json={"a": 1}, headers={"X-BodyLens": ""})
    assert r.status_code == 403


def test_login_throttle(client, make_user):
    make_user("jaime")
    for _ in range(8):
        client.post("/api/login", json={"username": "jaime", "password": "nope-nope-nope"})
    r = client.post("/api/login", json={"username": "jaime", "password": "contraseña-larga"})
    assert r.status_code == 429


def test_invite_registration(client, make_user, login):
    make_user("jaime", admin=True)
    admin = login("jaime")
    inv = admin.post("/api/admin/invites", json={"note": "Laura"}).json()
    code = inv["code"]
    assert inv["url"].endswith(f"/registro?c={code}")
    assert client.get(f"/api/invite/{code}").json() == {"valid": True}
    r = client.post("/api/register", json={"code": code, "username": "laura", "name": "Laura", "password": "abc"})
    assert r.status_code == 400 and "4 caracteres" in r.json()["detail"]
    r = client.post("/api/register", json={"code": code, "username": "laura", "name": "Laura Romero",
                                           "password": "otra-contraseña-larga"})
    assert r.status_code == 200
    assert client.get("/api/me").json()["user"]["username"] == "laura"
    # de un solo uso
    assert client.get(f"/api/invite/{code}").json() == {"valid": False}
    r = client.post("/api/register", json={"code": code, "username": "otro", "name": "Otro", "password": "otra-contraseña-larga"})
    assert r.status_code == 400


def test_only_admin_invites(client, make_user, login):
    make_user("laura")
    c = login("laura")
    assert c.post("/api/admin/invites", json={}).status_code == 403
    assert c.get("/api/admin/users").status_code == 403


def test_change_password(client, make_user, login):
    make_user("jaime")
    c = login("jaime")
    assert c.post("/api/me/password", json={"current": "mal", "new": "nueva-contraseña-1"}).status_code == 400
    assert c.post("/api/me/password", json={"current": "contraseña-larga", "new": "nueva-contraseña-1"}).status_code == 200
    assert c.get("/api/me").status_code == 200  # la sesión actual sigue
    login("jaime", "nueva-contraseña-1")


def test_bootstrap_admin_must_change(env, monkeypatch):
    monkeypatch.setenv("BODYLENS_ADMIN_USER", "jaime")
    monkeypatch.setenv("BODYLENS_ADMIN_NAME", "Jaime Tur")
    monkeypatch.setenv("BODYLENS_ADMIN_PASSWORD", "inicio")
    from app import config
    config.reload_settings()
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        c.headers.update({"X-BodyLens": "1"})
        r = c.post("/api/login", json={"username": "jaime", "password": "inicio"}).json()
        assert r["mustChange"] is True and r["user"]["isAdmin"] is True
        assert c.get("/", follow_redirects=False).headers["location"] == "/cuenta?cambiar=1"
        assert c.post("/api/me/first", json={"username": "x", "name": "J", "password": "abcd"}).status_code == 400
        assert c.post("/api/me/first", json={"username": "jaimetur", "name": "Jaime", "password": "1234"}).status_code == 200
        assert c.get("/", follow_redirects=False).status_code == 200
        me = c.get("/api/me").json()["user"]
        assert me["username"] == "jaimetur" and me["mustChange"] is False
        assert c.post("/api/me/first", json={"username": "jaimetur", "name": "J", "password": "1234"}).status_code == 409
    # al volver a arrancar con usuarios ya creados no se crea otra
    with TestClient(app) as c:
        assert c.post("/api/login", json={"username": "jaime", "password": "inicio"}, headers={"X-BodyLens": "1"}).status_code == 401


def test_migrates_old_database(env):
    from app import db
    con = db.connect()
    con.execute("DROP TABLE users")
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                "name TEXT NOT NULL, pw_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0, partner_id INTEGER, "
                "partner_since TEXT, sheet_id TEXT, apps_script_url TEXT, created_at TEXT NOT NULL)")
    con.close()
    db.init_db()
    with db.ro() as c2:
        assert "must_change" in {r[1] for r in c2.execute("PRAGMA table_info(users)")}


def test_default_admin_and_login_hint(env):
    from fastapi.testclient import TestClient
    from app import db, users
    from app.main import app
    with TestClient(app) as c:
        c.headers.update({"X-BodyLens": "1"})
        assert c.get("/api/login-hint").json() == {"accounts": [{"username": "admin", "password": "admin123"}]}
        assert c.post("/api/login", json={"username": "admin", "password": "admin123"}).status_code == 200
        me = c.get("/api/me").json()
        assert me["user"]["isAdmin"] and me["defaultPassword"] is True
        assert c.post("/api/me/password", json={"current": "admin123", "new": "otra"}).status_code == 200
        assert c.get("/api/login-hint").json() == {"accounts": []}
        assert c.get("/api/me").json()["defaultPassword"] is False
    # borrada, no vuelve a crearse al reiniciar
    with db.tx() as con:
        con.execute("DELETE FROM users WHERE username='admin'")
    with TestClient(app) as c:
        assert c.get("/api/login-hint").json() == {"accounts": []}
        with db.ro() as con:
            assert users.get_by_username(con, "admin") is None


def test_default_admin_added_to_existing_deployment(env, make_user):
    make_user("jaimetur", admin=True)
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        assert c.get("/api/login-hint").json()["accounts"][0]["username"] == "admin"
