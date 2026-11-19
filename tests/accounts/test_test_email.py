"""The test email of Administration → Mail reads like a real notice (greeting, what it is for, a link)."""


def test_test_email_content(client, make_user, login, monkeypatch):
    from app.mail import mailer
    sent = []
    monkeypatch.setattr(mailer, "send", lambda to, subject, body, reply_to=None: sent.append((to, subject, body)))
    make_user("root", name="Ana Pérez", admin=True)
    c = login("root")
    r = c.post("/api/admin/test-email", json={"to": "ana@example.test"})
    assert r.status_code == 200, r.text
    to, subject, body = sent[0]
    assert to == ["ana@example.test"] and subject == "Comprobación del correo"
    assert "Hola Ana," in body and "Abrir BodyLens" in body and "spam" not in body   # the word itself scores as spam
