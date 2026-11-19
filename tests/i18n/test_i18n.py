import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOCALES = ROOT / "src" / "frontend" / "i18n" / "locales"


@pytest.fixture()
def fake_locale(tmp_path, monkeypatch):
    """A tiny catalog: English messages, es.json bridging to the Spanish texts of the page, and a French file."""
    from app.core import i18n
    d = tmp_path / "loc"
    d.mkdir()
    (d / "es.json").write_text(json.dumps({"Hi {0}": "Hola {0}", "Your temporary password": "Tu contraseña provisional",
                                           "{1} days, {0} logged": "{0} de {1} días", "Sign in": "Entrar",
                                           "High": ["Alta", "Alto"]}))
    (d / "fr.json").write_text(json.dumps({"Sign in": "Se connecter", "High": "Haut"}))
    monkeypatch.setattr(i18n, "locale_file", lambda lang: d / f"{lang}.json")
    return d


def test_tr_y_patrones(env, fake_locale):
    from app.core import i18n
    assert i18n.tr("en", "  Entrar: ") == " Sign in: "   # los espacios se juntan, como en HTML
    assert i18n.tr("en", "3 de 7 días") == "7 days, 3 logged"
    assert i18n.tr("en", "Sin traducción") == "Sin traducción"
    assert i18n.tr("es", "Entrar") == "Entrar"
    assert i18n.tr("en", "Alto") == "High" and i18n.tr("fr", "Alta") == "Haut"
    assert i18n.tr("fr", "Tu contraseña provisional") == "Your temporary password"   # sin traducir: en inglés
    assert i18n.tr_html("en", '<html lang="es"><p>Hola Ana,</p><a>Entrar</a>') == '<html lang="en"><p>Hi Ana,</p><a>Sign in</a>'


def test_idioma_de_la_cuenta(client, make_user, login):
    from app.accounts import users
    from app.core import db
    make_user("ana")
    c = login("ana")
    assert c.get("/api/me").json()["user"]["lang"] == "en"            # las cuentas nuevas, en inglés
    assert c.post("/api/me/lang", json={"lang": "xx"}).status_code == 400
    r = c.post("/api/me/lang", json={"lang": "fr"})
    assert r.status_code == 200 and r.cookies.get("bl_lang") == "fr"
    with db.ro() as con:
        assert users.get_by_username(con, "ana").lang == "fr"
    page = c.get("/").text
    assert '<html lang="fr">' in page and "/i18n/fr.js?v=" in page and "/i18n.js?v=" in page
    assert "/i18n/fr.js" in c.get("/cuenta").text


def test_sin_sesion_cookie_o_ingles(client):
    assert "/i18n/en.js?v=" in client.get("/login").text
    client.cookies.set("bl_lang", "de")
    assert "/i18n/de.js?v=" in client.get("/login").text
    js = client.get("/i18n/de.js").text
    assert js.startswith('window.BL_LANG="de";') and "BL_LANGS" in js and "BL_I18N=" in js
    assert client.get("/i18n/xx.js").status_code == 404
    assert client.get("/i18n.js").status_code == 200


def test_peticion_de_cuenta_con_el_idioma_de_la_cookie(client):
    from app.accounts import users
    from app.core import db
    client.cookies.set("bl_lang", "it")
    r = client.post("/api/access-requests", json={"username": "gio", "name": "Gio Rossi", "email": "g@example.test",
                                                 "password": "1234"})
    assert r.status_code == 201, r.text
    with db.ro() as con:
        assert users.get_by_username(con, "gio").lang == "it"


def test_correo_en_el_idioma_de_cada_cuenta(env, make_user, fake_locale, monkeypatch):
    from app.accounts import users
    from app.core import db
    from app.mail import mailer
    a, b = make_user("ana"), make_user("bea")
    with db.tx() as con:
        users.set_email(con, a.id, "ana@example.test")
        users.set_email(con, b.id, "bea@example.test")
        users.set_lang(con, b.id, "es")
    monkeypatch.setattr(mailer, "settings", lambda: {"configured": True})
    got = []
    monkeypatch.setattr(mailer, "_deliver", lambda s, to, subj, html, rt: got.append((to, subj, html)))
    mailer.send(["ana@example.test", "bea@example.test", "otro@example.test"], "Tu contraseña provisional",
                mailer.page("Tu contraseña provisional", ["Hola Ana,"]))
    by = {tuple(t): (s, h) for t, s, h in got}
    assert by[("ana@example.test", "otro@example.test")][0] == "Your temporary password"
    assert "Hi Ana," in by[("ana@example.test", "otro@example.test")][1]
    assert by[("bea@example.test",)][0] == "Tu contraseña provisional"


def test_las_cuentas_de_antes_siguen_en_espanol(tmp_path, monkeypatch):
    """Una base de antes del multi-idioma: al migrar, sus cuentas quedan en español."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.core import config, db
    config.reload_settings()
    con = sqlite3.connect(config.settings.db_path)
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, name TEXT, pw_hash TEXT, is_admin INTEGER,"
                " partner_id INTEGER, partner_since TEXT, sheet_id TEXT, apps_script_url TEXT, created_at TEXT)")
    con.execute("INSERT INTO users VALUES (1,'jaime','Jaime','x',1,NULL,NULL,NULL,NULL,'2026-01-01')")
    con.commit()
    con.close()
    db.init_db()
    with db.ro() as c:
        assert c.execute("SELECT lang FROM users WHERE id=1").fetchone()[0] == "es"


def test_diccionarios_completos():
    """Every language translates the whole English catalog, with the same placeholders."""
    import subprocess
    import sys
    if not any(LOCALES.glob("*.json")):
        pytest.skip("todavía no hay diccionarios")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "i18n_check.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_access_request_with_chosen_language(client):
    """The language picked in the form wins over the one of the page."""
    from app.accounts import users
    from app.core import db
    client.cookies.set("bl_lang", "it")
    r = client.post("/api/access-requests", json={"username": "pia", "name": "Pia Rossi", "email": "p@example.test",
                                                  "password": "1234", "lang": "ja"})
    assert r.status_code == 201, r.text
    with db.ro() as con:
        assert users.get_by_username(con, "pia").lang == "ja"
