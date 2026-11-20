"""Deleting your own account from "Your account" (required by Google Play for apps with accounts)."""


def test_delete_my_account(client, make_user, login):
    make_user("ana")
    c = login("ana")
    assert c.post("/api/me/delete", json={"password": "wrong-password"}).status_code == 400
    assert c.get("/api/me").status_code == 200                 # still there
    r = c.post("/api/me/delete", json={"password": "contraseña-larga"})
    assert r.status_code == 200
    assert c.get("/api/me").status_code == 401                  # signed out
    r = client.post("/api/login", json={"username": "ana", "password": "contraseña-larga"})
    assert r.status_code in (400, 401)                          # the account no longer exists
    from app.accounts import users
    from app.core import db
    with db.ro() as con:
        assert users.get_by_login(con, "ana") is None


def test_the_last_administrator_cannot_delete_themselves(client, make_user, login):
    from app.core import db
    with db.tx() as con:   # only one administrator left
        con.execute("UPDATE users SET is_admin=0")
    make_user("boss", admin=True)
    c = login("boss")
    assert c.post("/api/me/delete", json={"password": "contraseña-larga"}).status_code == 400
    assert c.get("/api/me").status_code == 200
