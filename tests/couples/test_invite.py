"""Partner invitation: by username or email, with a clear error when the account does not exist, and emails."""


def test_invite_by_email_and_mails(client, make_user, login, monkeypatch):
    from app.accounts import users
    from app.core import db
    from app.mail import mailer

    make_user("jaime"); make_user("laura")
    with db.tx() as con:
        con.execute("UPDATE users SET email=? WHERE username=?", ("Laura@Example.test", "laura"))
        con.execute("UPDATE users SET email=? WHERE username=?", ("jaime@example.test", "jaime"))
    sent = []
    monkeypatch.setattr(mailer, "send_later", lambda to, subject, body, reply_to=None: sent.append((to, subject)))
    monkeypatch.setattr(mailer, "settings", lambda: {"configured": True})
    j = login("jaime"); l = login("laura")

    r = j.post("/api/partner/request", json={"username": "nadie@example.test"})
    assert r.status_code == 404 and "usuario o correo" in r.json()["detail"]
    assert j.post("/api/partner/request", json={"username": "noexiste"}).status_code == 404

    r = j.post("/api/partner/request", json={"username": "laura@example.test"})
    assert r.status_code == 200 and r.json() == {"ok": True, "linked": False, "mailed": True}
    assert sent[-1][0] == ["Laura@Example.test"]          # the invitation goes to Laura

    assert l.post("/api/partner/accept", json={"username": "jaime"}).status_code == 200
    assert sent[-1][0] == ["jaime@example.test"]          # Jaime learns that it was accepted
    with db.ro() as con:
        assert users.get_by_username(con, "jaime").partner_id == users.get_by_username(con, "laura").id
