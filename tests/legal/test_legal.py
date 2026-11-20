"""Public legal pages (privacy, terms, deleting an account) and the legal details set in Administration."""


def test_legal_pages_are_public(client):
    for path in ("/privacy", "/terms", "/delete-account"):
        r = client.get(path)
        assert r.status_code == 200 and "Responsable de los datos" in r.text
    for doc in ("privacy", "terms", "delete-account"):
        r = client.get(f"/api/help/{doc}?lang=en")
        assert r.status_code == 200 and "<h1>" in r.json()["html"]
        es = client.get(f"/api/help/{doc}?lang=es").json()
        assert es["shown"] == "es"                                   # bundled Spanish copy
    assert 'href="/delete-account"' in client.get("/api/help/privacy?lang=en").json()["html"]


def test_legal_pages_are_not_in_the_help_index(client):
    ids = [m["id"] for m in client.get("/api/help?lang=en").json()["modules"]]
    assert "privacy" not in ids and "terms" not in ids


def test_legal_details_from_administration(client, make_user, login):
    make_user("root", admin=True)
    make_user("ana")
    assert login("ana").put("/api/admin/legal", json={"controller": "X"}).status_code == 403
    c = login("root")
    assert c.put("/api/admin/legal", json={"controller": "Ana", "email": "bad"}).status_code == 400
    assert c.put("/api/admin/legal", json={"controller": "Ana Pérez", "email": "privacy@example.com"}).status_code == 200
    info = client.get("/api/legal").json()
    assert info["controller"] == "Ana Pérez" and info["email"] == "privacy@example.com"
