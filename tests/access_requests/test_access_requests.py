import smtplib

import pytest


@pytest.fixture()
def sent(monkeypatch):
    """Correos «enviados» (sin red ni hilos)."""
    from app.mail import mailer
    out = []
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "bodylens@example.test")
    monkeypatch.setattr(mailer, "send_later", lambda to, subject, html_body, reply_to=None: out.append(
        {"to": [t for t in to if t], "subject": subject, "html": html_body, "reply_to": reply_to}))
    return out


def test_request_approve_flow(client, make_user, login, sent):
    from app.accounts import users
    from app.core import db
    admin = make_user("jaimetur", "Jaime Tur", admin=True)
    with db.tx() as con:
        users.set_email(con, admin.id, "admin@example.test")
    body = {"name": "Laura Romero", "email": "laura@example.test", "username": "laura", "password": "1234", "note": "Soy Laura"}
    assert client.post("/api/access-requests", json={**body, "email": "mal"}).status_code == 400
    assert client.post("/api/access-requests", json=body).status_code == 201
    assert [m["to"] for m in sent] == [["admin@example.test"], ["laura@example.test"]]
    assert "Soy Laura" in sent[0]["html"] and sent[0]["reply_to"] == "laura@example.test"
    # mismo correo otra vez: no
    assert client.post("/api/access-requests", json={**body, "username": "laura2"}).status_code == 400
    # pendiente: no puede entrar
    r = client.post("/api/login", json={"username": "laura", "password": "1234"})
    assert r.status_code == 403 and "aprobada" in r.json()["detail"]
    a = login("jaimetur")
    assert a.get("/api/me").json()["pendingRequests"] == 1
    rq = a.get("/api/admin/access-requests").json()
    assert rq["mail"]["configured"] is True and rq["requests"][0]["note"] == "Soy Laura"
    # otra cuenta no puede unirse en pareja con una pendiente
    assert a.post("/api/partner/request", json={"username": "laura"}).status_code == 404
    rid = rq["requests"][0]["id"]
    assert a.post(f"/api/admin/access-requests/{rid}/approve").status_code == 200
    assert sent[-1]["to"] == ["laura@example.test"] and "activa" in sent[-1]["subject"]
    assert a.post(f"/api/admin/access-requests/{rid}/approve").status_code == 409
    l = login("laura", "1234")
    assert l.get("/api/me").json()["user"]["email"] == "laura@example.test"
    # el correo no se puede repetir ni quitar
    assert l.post("/api/me/email", json={"email": "admin@example.test"}).status_code == 400
    assert l.post("/api/me/email", json={"email": ""}).status_code == 400


def test_reject_and_honeypot(client, make_user, login, sent):
    make_user("jaimetur", admin=True)
    a = login("jaimetur")
    client.post("/api/access-requests", json={"name": "Bot", "email": "b@example.test", "username": "bot", "password": "1234", "website": "x"})
    assert a.get("/api/admin/access-requests").json()["requests"] == []
    client.post("/api/access-requests", json={"name": "Otra", "email": "o@example.test", "username": "otra", "password": "1234"})
    rid = a.get("/api/admin/access-requests").json()["requests"][0]["id"]
    assert client.post(f"/api/admin/access-requests/{rid}/reject").status_code in (401, 403)
    assert a.post(f"/api/admin/access-requests/{rid}/reject").status_code == 200
    assert sent[-1]["to"] == ["o@example.test"]
    assert client.post("/api/login", json={"username": "otra", "password": "1234"}).status_code == 401


def test_request_throttle(client, sent):
    for i in range(5):
        client.post("/api/access-requests", json={"name": "X", "email": f"x{i}@example.test", "username": f"x{i}", "password": "1234"})
    r = client.post("/api/access-requests", json={"name": "X", "email": "x9@example.test", "username": "x9", "password": "1234"})
    assert r.status_code == 429


def test_mailer_smtp_ssl(monkeypatch):
    from app.mail import mailer
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port, local_hostname=None, timeout=None, context=None):
            calls["conn"] = (host, port)
            calls["helo"] = local_hostname
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def ehlo(self): pass
        def login(self, u, p): calls["login"] = (u, p)
        def send_message(self, m): calls["msg"] = m
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    for k, v in {"SMTP_HOST": "mail.jtgcloud.com", "SMTP_PORT": "465", "SMTP_SECURITY": "ssl",
                 "SMTP_USERNAME": "bodylens@jtgcloud.com", "SMTP_PASSWORD": "secreto", "SMTP_FROM": "bodylens@jtgcloud.com"}.items():
        monkeypatch.setenv(k, v)
    mailer.send(["a@example.test"], "Hola", mailer.page("Hola", ["texto <b>x</b>"], link=("Entrar", "https://x/login")))
    assert calls["conn"] == ("mail.jtgcloud.com", 465) and calls["login"] == ("bodylens@jtgcloud.com", "secreto")
    assert calls["helo"] and not calls["helo"].startswith("[")  # a public name, never the container address
    m = calls["msg"]
    assert m["Subject"] == "BodyLens - Hola" and "bodylens@jtgcloud.com" in m["From"]
    assert "https://x/login" in m.get_body(("plain",)).get_content()   # el texto va en el idioma del destinatario
    assert "secreto" not in str(mailer.public_settings())


def test_mailer_not_configured(monkeypatch):
    from app.mail import mailer
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with pytest.raises(RuntimeError, match="no está configurado"):
        mailer.send(["a@example.test"], "x", "<p>x</p>")


def test_admin_panel_accounts(client, make_user, login, sent):
    make_user("jaimetur", "Jaime Tur", admin=True)
    lau = make_user("laura", "Laura")
    a = login("jaimetur")
    assert a.get("/admin").status_code == 200
    assert login("laura").get("/admin", follow_redirects=False).headers["location"] == "/cuenta"
    users = {u["username"]: u for u in a.get("/api/admin/accounts").json()["users"]}
    assert {"jaimetur", "laura", "admin"} <= set(users)
    me = users["jaimetur"]["id"]
    assert a.patch(f"/api/admin/accounts/{me}", json={"isAdmin": False}).status_code == 400
    assert a.patch(f"/api/admin/accounts/{lau.id}", json={"name": "Laura Romero", "email": "l@example.test", "isAdmin": True}).status_code == 200
    # desactivar cierra sus sesiones y le impide entrar
    l = login("laura")
    assert a.patch(f"/api/admin/accounts/{lau.id}", json={"active": False}).status_code == 200
    assert l.get("/api/me").status_code == 401
    a.patch(f"/api/admin/accounts/{lau.id}", json={"active": True})
    r = a.post(f"/api/admin/accounts/{lau.id}/password", json={"email": True}).json()
    assert r["emailed"] is True and sent[-1]["to"] == ["l@example.test"] and r["password"] in sent[-1]["html"]
    l2 = login("laura", r["password"])
    assert l2.get("/api/me").json()["user"]["mustChange"] is True
    # el admin cambia el usuario y la contraseña: se cierran sus sesiones y entra con los nuevos
    assert a.patch(f"/api/admin/accounts/{lau.id}", json={"username": "admin"}).status_code == 400   # ya existe
    assert a.patch(f"/api/admin/accounts/{lau.id}", json={"password": "abc"}).status_code == 400     # muy corta
    assert a.patch(f"/api/admin/accounts/{lau.id}", json={"username": "Laura.R", "password": "nueva1"}).status_code == 200
    assert l2.get("/api/me").status_code == 401
    l3 = login("laura.r", "nueva1")
    assert l3.get("/api/me").json()["user"]["mustChange"] is False
    assert a.delete(f"/api/admin/accounts/{me}").status_code == 400
    assert a.delete(f"/api/admin/accounts/{lau.id}").status_code == 200
    assert "laura" not in {u["username"] for u in a.get("/api/admin/accounts").json()["users"]}


def test_admin_mail_settings(client, make_user, login, monkeypatch):
    from app.mail import mailer
    monkeypatch.delenv("SMTP_HOST", raising=False)
    make_user("jaimetur", admin=True)
    a = login("jaimetur")
    assert a.get("/api/admin/mail").json()["configured"] is False
    r = a.put("/api/admin/mail", json={"host": "smtp.example.test", "port": 465, "security": "ssl", "username": "u@example.test",
                                       "password": "secreto", "from_address": "u@example.test", "from_name": "BodyLens"}).json()
    assert r["configured"] and r["hasPassword"] and "secreto" not in str(r)
    # sin contraseña nueva se conserva la guardada
    a.put("/api/admin/mail", json={"host": "smtp2.example.test", "security": "ssl", "from_address": "u@example.test"})
    s = mailer.settings()
    assert s["host"] == "smtp2.example.test" and s["password"] == "secreto"
    assert a.put("/api/admin/mail", json={"security": "raro"}).status_code == 400



def test_nunca_sin_administracion(client, make_user, login):
    """No se puede quitar, desactivar ni borrar la última cuenta de administración activa."""
    from app.accounts import users
    from app.accounts.users import UserError
    from app.core import db
    me = make_user("jaimetur", admin=True)
    a = login("jaimetur")
    with db.ro() as con:
        adm = users.get_by_username(con, "admin")
    # con otra admin activa (yo), a la cuenta inicial se le puede quitar la administración y desactivar
    assert a.patch(f"/api/admin/accounts/{adm.id}", json={"isAdmin": False}).status_code == 200
    # a mí mismo no (soy la única que queda)
    assert a.patch(f"/api/admin/accounts/{me.id}", json={"isAdmin": False}).status_code == 400
    assert a.patch(f"/api/admin/accounts/{me.id}", json={"active": False}).status_code == 400
    assert a.delete(f"/api/admin/accounts/{me.id}").status_code == 400
    # la comprobación del servidor, por si cambia la regla de «a ti mismo no»
    with db.ro() as con:
        with pytest.raises(UserError, match="única cuenta de administración"):
            users.ensure_other_admin(con, me.id)
        users.ensure_other_admin(con, adm.id)   # quedo yo: vale
