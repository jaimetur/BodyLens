"""Invitation codes: a free account for the code's time (or for life), unless an administrator changes the end date."""


def _signup(client, code, username="paco"):
    return client.post("/api/web/signup", json={"username": username, "name": "Paco", "email": f"{username}@example.com",
                                                "password": "contraseña-larga", "code": code})


def test_code_gives_a_free_account_at_once(client):
    assert _signup(client, "nope").status_code == 400
    r = _signup(client, "  invitación_Amigos ")             # no accents, case or spaces
    assert r.status_code == 200 and r.json()["signedIn"]
    st = client.get("/api/play/status").json()
    assert st["plan"] == "gift" and st["active"] and st["expiry"] is None
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200


def test_admin_sets_and_lifts_the_end_of_free_access(client, make_user, login):
    assert _signup(client, "INVITACION_AMIGOS").status_code == 200
    make_user("root", admin=True)
    admin = login("root")
    acc = {a["username"]: a for a in admin.get("/api/admin/accounts").json()["users"]}
    assert acc["paco"]["plan"] == {"kind": "gift", "giftUntil": None, "code": "INVITACION_AMIGOS"}
    pid = acc["paco"]["id"]
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "2020-01-31"}).status_code == 200
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 402      # over: blocked
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "lifetime"}).status_code == 200
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200
    assert admin.patch(f"/api/admin/accounts/{pid}", json={"freeUntil": "31/01/2020"}).status_code == 400


def test_codes_are_set_in_administration(client, make_user, login):
    make_user("root", admin=True)
    admin = login("root")
    assert admin.get("/api/admin/codes").json()["codes"] == [{"code": "INVITACION_AMIGOS", "duration": "life", "expires": "", "max": None, "used": 0, "public": False, "aliases": []}]
    r = admin.put("/api/admin/codes", json={"codes": ["Familia2026", {"code": "familia2026", "duration": "1m"}, " "]})
    assert r.json()["codes"] == [{"code": "Familia2026", "duration": "life", "expires": "", "max": None, "used": 0, "public": False, "aliases": []}]
    assert _signup(client, "INVITACION_AMIGOS").status_code == 400
    assert _signup(client, "FAMILIA2026").status_code == 200


def test_code_durations(client, make_user, login):
    import time
    from app.billing import codes
    make_user("root", admin=True)
    admin = login("root")
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "x", "duration": "2020-01-01"}]}).status_code == 400
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "x", "duration": "2w"}]}).status_code == 400
    r = admin.put("/api/admin/codes", json={"codes": [{"code": "TRES", "duration": "3m"}, {"code": "Fecha", "duration": "2099-03-15"}]})
    assert [(c["code"], c["duration"]) for c in r.json()["codes"]] == [("TRES", "3m"), ("Fecha", "2099-03-15")]
    assert _signup(client, "tres").status_code == 200
    st = client.get("/api/play/status").json()
    assert st["plan"] == "gift" and st["active"] and 88 < (st["expiry"] / 1000 - time.time()) / 86400 < 93
    # dates: the same day some months later (or the last one of a short month), to the end of that day in Madrid
    jan31 = 1769860800                       # 2026-01-31 12:00 UTC
    from datetime import datetime
    from zoneinfo import ZoneInfo
    end = lambda d: datetime.fromtimestamp(codes.until_ms(d, jan31) / 1000, ZoneInfo("Europe/Madrid"))   # noqa: E731
    assert end("1m").strftime("%Y-%m-%d %H:%M") == "2026-02-28 23:59"
    assert end("1y").strftime("%Y-%m-%d") == "2027-01-31" and end("6m").strftime("%Y-%m-%d") == "2026-07-31"
    assert end("2026-05-04").strftime("%Y-%m-%d %H:%M") == "2026-05-04 23:59" and codes.until_ms("life") is None


def test_code_expiry(client, make_user, login, monkeypatch):
    import time
    from app.billing import codes
    make_user("root", admin=True)
    admin = login("root")
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "x", "expires": "2020-01-01"}]}).status_code == 400
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "x", "expires": "31/12/2099"}]}).status_code == 400
    r = admin.put("/api/admin/codes", json={"codes": [{"code": "VERANO", "duration": "1y", "expires": "2099-08-31"},
                                                      {"code": "SIEMPRE", "duration": "life"}]})
    assert r.json()["codes"][0] == {"code": "VERANO", "duration": "1y", "expires": "2099-08-31", "max": None, "used": 0, "public": False, "aliases": []}
    assert _signup(client, "verano").status_code == 200
    # once the date has passed the code is deleted and no longer valid; the account keeps its free year
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + 80 * 365 * 86400)
    assert not codes.valid("VERANO") and codes.valid("siempre")
    monkeypatch.setattr(time, "time", real)
    assert [c["code"] for c in admin.get("/api/admin/codes").json()["codes"]] == ["SIEMPRE"]     # deleted
    st = client.get("/api/play/status").json()
    assert st["plan"] == "gift" and st["active"] and st["expiry"] > real() * 1000 + 360 * 86400 * 1000


def test_code_for_the_first_n_accounts(client, make_user, login):
    make_user("root", admin=True)
    admin = login("root")
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "x", "max": 0}]}).status_code == 400
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "PROMO", "duration": "3m", "max": 2}]}).status_code == 200
    from fastapi.testclient import TestClient
    from app.main import app
    for name in ("ana", "bea"):
        with TestClient(app) as c:
            c.headers.update({"X-BodyLens": "1"})
            assert _signup(c, "promo", name).status_code == 200
            if name == "ana":
                assert admin.get("/api/admin/codes").json()["codes"][0]["used"] == 1
                # lowering the maximum below the accounts already made is refused
                assert admin.put("/api/admin/codes", json={"codes": [{"code": "PROMO", "duration": "3m", "max": 1}]}).status_code == 400
    assert admin.get("/api/admin/codes").json()["codes"] == []          # full: deleted
    with TestClient(app) as c:
        c.headers.update({"X-BodyLens": "1"})
        r = _signup(c, "promo", "carla")
        assert r.status_code == 400 and "no es válido" in r.json()["detail"]


def test_public_promotion_for_the_landing_page(client, make_user, login):
    make_user("root", admin=True)
    admin = login("root")
    assert client.get("/api/promos").json() == {"promos": []}
    admin.put("/api/admin/codes", json={"codes": [{"code": "LANZAMIENTO", "duration": "1y", "max": 50, "public": True},
                                                  {"code": "SECRETO", "duration": "life"}]})
    assert _signup(client, "lanzamiento").status_code == 200
    assert client.get("/api/promos").json() == {"promos": [{"code": "LANZAMIENTO", "aliases": [], "duration": "1y", "expires": "", "max": 50, "left": 49}]}


def test_alias_shares_the_code(client, make_user, login):
    from fastapi.testclient import TestClient
    from app.main import app
    make_user("root", admin=True)
    admin = login("root")
    body = {"codes": [{"code": "LANZAMIENTO", "aliases": ["Launch", "lanzamiento", "launch"], "duration": "1y", "max": 2, "public": True}]}
    r = admin.put("/api/admin/codes", json=body).json()["codes"][0]
    assert r["aliases"] == ["Launch"]
    assert admin.put("/api/admin/codes", json={"codes": [{"code": "A"}, {"code": "B", "aliases": ["a"]}]}).status_code == 400
    assert client.get("/api/promos").json()["promos"][0]["aliases"] == ["Launch"]
    for name, code in (("ana", "launch"), ("bea", "LANZAMIENTO"), ("carla", "LAUNCH")):
        with TestClient(app) as c:
            c.headers.update({"X-BodyLens": "1"})
            assert _signup(c, code, name).status_code == (400 if name == "carla" else 200)    # 2 places shared
