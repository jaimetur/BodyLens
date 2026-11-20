"""Invitation codes: a free account for life, unless an administrator sets an end date."""


def _signup(client, code, username="paco"):
    return client.post("/api/web/signup", json={"username": username, "name": "Paco", "email": f"{username}@example.com",
                                                "password": "contraseña-larga", "code": code})


def test_code_gives_a_free_account_at_once(client):
    assert _signup(client, "nope").status_code == 400
    r = _signup(client, "  invitación_Amigos ")             # no accents, case or spaces
    assert r.status_code == 200 and r.json()["signedIn"]
    st = client.get("/api/play/status").json()
    assert st["plan"] == "gift" and st["active"] and st["expiry"] is None
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200


def test_admin_sets_and_lifts_the_end_of_free_access(client, make_user, login):
    assert _signup(client, "INVITACION_AMIGOS").status_code == 200
    make_user("root", admin=True)
    admin = login("root")
    acc = {a["username"]: a for a in admin.get("/api/admin/accounts").json()["users"]}
    assert acc["paco"]["plan"] == {"kind": "gift", "giftUntil": None}
    pid = acc["paco"]["id"]
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "2020-01-31"}).status_code == 200
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 402      # over: blocked
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "lifetime"}).status_code == 200
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "31/01/2020"}).status_code == 400


def test_codes_are_set_in_administration(client, make_user, login):
    make_user("root", admin=True)
    admin = login("root")
    assert admin.get("/api/admin/codes").json()["codes"] == ["INVITACION_AMIGOS"]
    assert admin.put("/api/admin/codes", json={"codes": ["Familia2026", "familia2026", " "]}).json()["codes"] == ["Familia2026"]
    assert _signup(client, "INVITACION_AMIGOS").status_code == 400
    assert _signup(client, "FAMILIA2026").status_code == 200
