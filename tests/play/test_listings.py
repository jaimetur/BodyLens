"""Google Play listing texts (assets/play-store/listings): one per store language, within Play's limits."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _publish():
    spec = importlib.util.spec_from_file_location("play_publish", ROOT / "tools" / "play_publish.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_listings_within_limits_and_mapped():
    app_lang = _publish().APP_LANG
    files = sorted((ROOT / "assets" / "play-store" / "listings").glob("*.json"))
    assert {p.stem for p in files} == set(app_lang)
    for p in files:
        t = json.loads(p.read_text(encoding="utf-8"))
        assert set(t) == {"title", "shortDescription", "fullDescription"}, p.name
        assert 0 < len(t["title"]) <= 30 and 0 < len(t["shortDescription"]) <= 80 and 0 < len(t["fullDescription"]) <= 4000, p.name


def test_every_app_language_has_a_store_language():
    from app.core.i18n import LANGS
    assert set(_publish().APP_LANG.values()) == set(LANGS)
