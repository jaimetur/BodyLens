"""Help module: English documents, automatic translation (mocked) with a cache keyed by the English text."""
import time

import pytest


@pytest.fixture()
def docs_dir(tmp_path, monkeypatch, env):
    from app.core import config
    d = tmp_path / "docs"
    (d / "help" / "en").mkdir(parents=True)
    (d / "help" / "en" / "README.md").write_text("# Help\n\n- [Sleep](sleep.md)\n- [Weight](weight.md)\n")
    (d / "help" / "en" / "weight.md").write_text("# Weight\n\nYour **trend** weight.\n")
    (d / "help" / "en" / "sleep.md").write_text("# Sleep\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nSee [weight](weight.md).\n")
    (d / "README.md").write_text("# BodyLens\n\n**English** · [Español](README_ES.md)\n\nIntro text.\n")
    (d / "CHANGELOG.md").write_text("# CHANGELOG\n\n## Release: v1\n- **New:** things\n")
    monkeypatch.setenv("DOCS_DIR", str(d))
    config.reload_settings()
    return d


def test_render_markdown():
    from app.help import docs
    h = docs.render("# T\n\nText with `code` and [link](sleep.md) and [web](https://x.test).\n\n- a\n  - b\n- c\n\n"
                    "```\n<raw>\n```\n\n> quote\n")
    assert "<h1>T</h1>" in h and "<code>code</code>" in h and 'data-doc="sleep"' in h
    assert 'href="https://x.test" target="_blank"' in h and "<ul><li>a<ul><li>b</li></ul></li><li>c</li></ul>" in h
    assert "&lt;raw&gt;" in h and "<blockquote>" in h
    assert "<script>" not in docs.render("<script>alert(1)</script>")


def test_documents_in_english(client, make_user, login, docs_dir):
    make_user("ana")
    c = login("ana")
    idx = c.get("/api/help?lang=en").json()
    assert [m["id"] for m in idx["modules"]] == ["sleep", "weight"]   # order of the help index
    r = c.get("/api/help/sleep?lang=en").json()
    assert r["shown"] == "en" and "<table>" in r["html"] and 'data-doc="weight"' in r["html"]
    readme = c.get("/api/help/readme?lang=en").json()["html"]
    assert "Intro text" in readme and "README_ES" not in readme       # no GitHub language bar
    assert "Release: v1" in c.get("/api/help/changelog?lang=en").json()["html"]
    assert c.get("/api/help/../etc?lang=en").status_code == 404
    assert c.get("/api/help/nope?lang=en").status_code == 404
    assert client.get("/api/help").status_code == 200                 # public: no session needed
    assert "Intro text" in client.get("/api/help/readme?lang=en").json()["html"]


def test_without_translator_english(client, make_user, login, docs_dir, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    make_user("ana")
    c = login("ana")
    r = c.get("/api/help/weight?lang=fr").json()
    assert r["shown"] == "en" and r["pending"] is False and r["translator"] is False


def _wait(translate, seconds=10.0):
    end = time.time() + seconds
    while translate.pending("fr", "weight") and time.time() < end:
        time.sleep(0.02)


def test_automatic_translation_and_cache(client, make_user, login, docs_dir, monkeypatch):
    from app.help import translate
    monkeypatch.delenv("LIBRETRANSLATE_URL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    calls = []

    def fake_chunk(client_, lang, text):
        calls.append((lang, text))
        return text.replace("Weight", "Poids").replace("Your", "Ton")
    monkeypatch.setattr(translate, "_translate_chunk", fake_chunk)
    make_user("ana")
    c = login("ana")
    r = c.get("/api/help/weight?lang=fr").json()
    assert r["shown"] == "en" and r["pending"] is True               # English while it is translated
    _wait(translate)
    r = c.get("/api/help/weight?lang=fr").json()
    assert r["shown"] == "fr" and r["title"] == "Poids" and "Ton" in r["html"]
    n = len(calls)
    c.get("/api/help/weight?lang=fr")
    assert len(calls) == n                                             # kept: not translated again
    (docs_dir / "help" / "en" / "weight.md").write_text("# Weight\n\nChanged.\n")
    assert c.get("/api/help/weight?lang=fr").json()["pending"] is True  # English changed: translated again
    _wait(translate)
    assert c.get("/api/help/weight?lang=fr").json()["html"].count("Changed") == 1
    assert len(list((translate.config.settings.data_dir / "translations" / "fr").glob("weight-*.html"))) == 1


def test_chunks_split_long_documents():
    from app.help import translate
    md = "# A\n\n" + "\n\n".join(f"## S{i}\n\n" + "x" * 3000 for i in range(10))
    parts = translate.chunks(md)
    assert len(parts) > 1 and all(len(p) <= translate.CHUNK for p in parts)
    assert "".join(p.replace("\n", "") for p in parts) == md.replace("\n", "")


def test_admin_translator_key(client, make_user, login, monkeypatch):
    from app.help import translate
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    make_user("jaimetur", admin=True)
    make_user("ana")
    a, u = login("jaimetur"), login("ana")
    assert u.get("/api/admin/translator").status_code == 403
    assert a.put("/api/admin/translator", json={"apiKey": "nope"}).status_code == 400
    assert a.post("/api/admin/translator/prewarm").status_code == 400
    r = a.put("/api/admin/translator", json={"apiKey": "sk-ant-secret"}).json()
    assert r["configured"] is True and "secret" not in str(r)
    assert translate.api_key() == "sk-ant-secret"
    assert a.put("/api/admin/translator", json={"remove": True}).json()["configured"] is False


def test_help_page(client, make_user, login):
    make_user("ana")
    c = login("ana")
    assert "/i18n.js" in c.get("/help").text
    assert client.get("/help", follow_redirects=False).status_code == 200   # public
    assert 'href="/help"' in client.get("/login").text


def test_libretranslate(client, make_user, login, docs_dir, monkeypatch):
    """LibreTranslate (free, self-hosted) translates the rendered HTML; code is never sent to it."""
    import httpx
    import respx
    from app.help import translate
    monkeypatch.setenv("LIBRETRANSLATE_URL", "http://lt.test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    translate._libre.update(at=0.0, codes=None)
    (docs_dir / "help" / "en" / "weight.md").write_text("# Weight\n\nUse `tools/x.sh` here.\n\n```\nWeight raw\n```\n")
    sent = []

    def fake(request):
        import json
        q = json.loads(request.content)["q"]
        sent.append(q)
        return httpx.Response(200, json={"translatedText": q.replace("Weight", "Poids").replace("Use", "Utilise")})
    with respx.mock:
        respx.get("http://lt.test/languages").mock(return_value=httpx.Response(200, json=[{"code": "en"}, {"code": "fr"}]))
        respx.post("http://lt.test/translate").mock(side_effect=fake)
        make_user("ana")
        c = login("ana")
        assert c.get("/api/help/weight?lang=fr").json()["pending"] is True
        _wait(translate)
        r = c.get("/api/help/weight?lang=fr").json()
    assert r["shown"] == "fr" and r["title"] == "Poids"
    assert "<code>tools/x.sh</code>" in r["html"] and "Weight raw" in r["html"]      # code kept as it was
    assert all("tools/x.sh" not in q and "Weight raw" not in q for q in sent)
    translate._libre.update(at=0.0, codes=None)


def test_bundled_translation(client, make_user, login, docs_dir, monkeypatch):
    """A translation kept in the repository is used while it matches the current English; then the translator."""
    from app.help import docs, translate
    monkeypatch.delenv("LIBRETRANSLATE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = docs_dir / "help" / "i18n" / "es"
    d.mkdir(parents=True)
    h = translate.source_hash(docs.source("weight"))
    (d / "weight.md").write_text(f"<!-- en: {h} -->\n# Peso\n\nTu peso de **tendencia**.\n")
    make_user("ana")
    c = login("ana")
    r = c.get("/api/help/weight?lang=es").json()
    assert r["shown"] == "es" and r["title"] == "Peso" and "<!--" not in r["html"]
    assert {m["id"]: m["title"] for m in c.get("/api/help?lang=es").json()["modules"]}["weight"] == "Peso"
    (docs_dir / "help" / "en" / "weight.md").write_text("# Weight\n\nChanged.\n")
    r = c.get("/api/help/weight?lang=es").json()
    assert r["shown"] == "en" and "Changed" in r["html"]               # stale: not used any more


def test_bundled_translations_up_to_date():
    """The translations kept in the repository (help/i18n/<lang>/) match the current English documents."""
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    r = subprocess.run([sys.executable, str(root / "tools" / "help_i18n.py"), "check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
