"""The landing page for visitors, and the sign-in for the Android app."""


def test_visitors_see_the_landing_page(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 200 and 'id="precios"' in r.text and "/alta?plan=yearly" in r.text


def test_the_android_app_goes_to_sign_in(client):
    r = client.get("/", follow_redirects=False, headers={"user-agent": "Mozilla/5.0 (Linux; Android 14) BodyLensApp/0.1.7"})
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_landing_path_moves_to_the_root(client):
    for path in ("/landing", "/landing/"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/"
    assert client.get("/landing?lang=es", follow_redirects=False).headers["location"] == "/?lang=es"


def test_landing_media_only_serves_media(client):
    assert client.get("/landing/media/../../backend/app/main.py").status_code == 404
    assert client.get("/landing/media/nothing.webp").status_code == 404


def test_landing_language_english_by_default_and_menu(client):
    assert '<html lang="en"' in client.get("/", headers={"accept-language": "es-ES,es;q=0.9"}).text   # English by default
    r = client.get("/?lang=de", headers={"accept-language": "en-US"})
    assert '<html lang="de"' in r.text and "bl_lang=de" in r.headers.get("set-cookie", "")
    assert '<html lang="de"' in client.get("/").text   # remembered
    assert '<html lang="es"' in client.get("/?lang=es").text
    client.cookies.clear()
    assert '<html lang="en"' in client.get("/?lang=xx").text   # unknown language: English
    assert 'id="langSel"' in r.text and '<option value="ja">' in r.text
