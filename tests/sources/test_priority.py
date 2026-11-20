"""Apple Health and Android (Health Connect) in the same account: the main source rules, the other fills gaps."""
from tests.sources.test_hae import AW, _rows, _uid, seg, sleep


def _post(uid, body, android, android_rules):
    from app.core import db
    from app.sources import hae
    with db.tx() as con:
        return hae.ingest(con, uid, body, android, android_rules)


def steps(day, qty, source=""):
    return {"data": {"metrics": [{"name": "step_count", "units": "count",
                                  "data": [{"date": f"{day} 10:00:00 +0100", "qty": qty, "source": source}]}]}}


def test_apple_rules_android_only_fills_gaps(env, make_user):
    from app.sheets.tabs import ACTIVIDAD
    uid = _uid(make_user)
    _post(uid, steps("2026-11-18", 5000, "iPhone"), False, False)
    assert _post(uid, steps("2026-11-18", 9000), True, False)["ignoradas"] == 1   # Apple has that day: ignored
    _post(uid, steps("2026-11-19", 7000), True, False)      # a day Apple has nothing: filled in
    a = _rows(uid, ACTIVIDAD)
    assert a["2026-11-18"][1] == 5000 and a["2026-11-19"][1] == 7000
    _post(uid, steps("2026-11-19", 6000, "iPhone"), False, False)   # Apple arrives later: Android's day goes away
    assert _rows(uid, ACTIVIDAD)["2026-11-19"][1] == 6000


def test_android_rules_apple_only_fills_gaps(env, make_user):
    from app.sheets.tabs import ACTIVIDAD, SALUD
    uid = _uid(make_user)
    _post(uid, steps("2026-11-18", 5000, "iPhone"), False, True)
    _post(uid, steps("2026-11-18", 9000), True, True)       # Android rules: Apple's day is replaced
    assert _rows(uid, ACTIVIDAD)["2026-11-18"][1] == 9000
    assert [r[6] for r in _rows(uid, SALUD).values()] == ["Health Connect"]


def test_sleep_and_workouts_of_the_main_source(env, make_user):
    from app.sheets.tabs import ENTRENOS, SUENO
    uid = _uid(make_user)
    _post(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AW)), False, False)
    _post(uid, sleep(seg("2026-11-18 22:00:00", "2026-11-19 08:00:00", "Asleep", "com.sec.android.app.shealth")), True, False)
    assert _rows(uid, SUENO)["2026-11-19"][4] == 480     # the Watch's night, not Android's 10 h
    wo = lambda i: {"data": {"workouts": [{"id": i, "name": "Running", "start": "2026-11-19 18:02:00 +0100",  # noqa: E731
                                           "end": "2026-11-19 19:00:00 +0100", "duration": 3480}]}}
    _post(uid, wo("A1"), False, False)
    _post(uid, wo("H1"), True, False)                        # the same session from Health Connect: not duplicated
    assert list(_rows(uid, ENTRENOS)) == ["hk-A1"]


def test_auto_follows_where_most_data_comes_from(client, make_user, login):
    make_user("jaimetur")
    c = login("jaimetur")
    assert c.get("/api/sources").json()["healthPrimary"]["rules"] == "android"   # new accounts: Android
    token = c.post("/api/sources/hae/token").json()["url"].rsplit("/", 1)[1]
    anon = client.__class__(client.app)
    for _ in range(2):
        anon.post(f"/api/ingest/hae/{token}", json=steps("2026-11-18", 100))
    anon.post(f"/api/ingest/hae/{token}", json=steps("2026-11-18", 100), headers={"User-Agent": "BodyLens-Android"})
    p = c.get("/api/sources").json()["healthPrimary"]
    assert p == {"mode": "auto", "rules": "apple", "apple": 2, "android": 1}
    h = c.get("/api/sources").json()["hae"]
    assert h["apple"]["metricas"] == 1 and h["android"]["ignoradas"] == 1 and "ignoradas" not in h["apple"]
    assert c.post("/api/sources/primary", json={"mode": "android"}).json()["rules"] == "android"
    assert c.post("/api/sources/primary", json={"mode": "nope"}).status_code == 400
