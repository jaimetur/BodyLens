import pytest


def test_page_is_served_with_shim(client, make_user, login):
    make_user("laura", "Laura Romero")
    c = login("laura")
    html = c.get("/").text
    assert html.startswith("<!doctype html>")
    assert '<script src="/claude-shim.js"></script>' in html
    assert '"name": "Laura Romero"' in html
    assert "cdnjs.cloudflare.com/ajax/libs/xlsx" not in html
    assert "script.google.com" not in html
    assert "1aUMgruI3VycOCjbqH4" not in html
    assert "BL.profDef()" in html and "BL.pull()" in html
    assert c.get("/claude-shim.js").status_code == 200
    assert c.get("/manifest.webmanifest").json()["name"] == "BodyLens"
    assert c.get("/icon-192.png").status_code == 200
    assert c.get("/healthz").json() == {"ok": True}


def test_assembly_detects_changes(env, monkeypatch):
    from app.web import page as frontend
    monkeypatch.setattr(frontend, "REPLACEMENTS", frontend.REPLACEMENTS + [("no existe en la app", "x")])
    with pytest.raises(frontend.AssemblyError):
        frontend.assemble_fragment()


def test_version_and_update_notice(client, make_user, login, tmp_path, monkeypatch):
    from app.core import version
    f = tmp_path / "REVISION"
    monkeypatch.setattr(version, "REVISION_FILE", f)
    monkeypatch.setenv("BODYLENS_REVISION", "imagen123")
    assert client.get("/api/version").json()["build"] == "imagen123"
    f.write_text("abc1234 2026-11-19T15:00:00Z\n")
    assert client.get("/api/version").json() == {"build": "abc1234", "deployedAt": "2026-11-19T15:00:00Z"}
    make_user("jaimetur")
    html = login("jaimetur").get("/").text
    assert 'window.BODYLENS_BUILD="abc1234"' in html
