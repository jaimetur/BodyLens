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
    r = client.post("/api/register", json={"code": code, "username": "laura", "name": "Laura", "password": "corta"})
    assert r.status_code == 400 and "10 caracteres" in r.json()["detail"]
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
