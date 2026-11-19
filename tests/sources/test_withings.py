import time
from datetime import datetime
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from app.sheets import values as V


@pytest.fixture()
def wenv(env, monkeypatch):
    monkeypatch.setenv("WITHINGS_CLIENT_ID", "cid")
    monkeypatch.setenv("WITHINGS_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("PUBLIC_URL", "https://bodylens.example.test")
    from app.core import config, crypto
    config.reload_settings()
    crypto.reset()
    return env


def ts(s):
    return int(V.to_epoch(datetime.strptime(s, "%Y-%m-%d %H:%M")))


def test_sueno_dia_noche_y_siesta():
    from app.sources.withings import sueno_dia
    series = [
        {"startdate": ts("2026-11-18 15:00"), "enddate": ts("2026-11-18 15:30"), "state": 1, "model": "Sleep Analyzer", "model_id": 63},
        {"startdate": ts("2026-11-18 23:30"), "enddate": ts("2026-11-19 03:00"), "state": 1, "model": "Sleep Analyzer", "model_id": 63, "hr": {"1": 60, "2": 50}},
        {"startdate": ts("2026-11-19 03:00"), "enddate": ts("2026-11-19 03:20"), "state": 0, "model": "Sleep Analyzer", "model_id": 63},
        {"startdate": ts("2026-11-19 03:20"), "enddate": ts("2026-11-19 05:00"), "state": 2, "model": "Sleep Analyzer", "model_id": 63},
        {"startdate": ts("2026-11-19 05:00"), "enddate": ts("2026-11-19 07:00"), "state": 3, "model": "Sleep Analyzer", "model_id": 63},
    ]
    r = sueno_dia(series, "2026-11-19")
    f = r["fila"]
    assert f[1] == datetime(2026, 11, 18, 23, 30) and f[2] == datetime(2026, 11, 19, 7)
    assert f[3] == 450 and f[4] == 430 and f[6] == 100 and f[7] == 120 and f[9] == 1 and f[11] == 55 and f[12] == 50
    assert len(r["siestas"]) == 1 and list(r["siestas"].values())[0][4] == 30


@respx.mock
def test_oauth_y_sincronizacion(wenv, make_user):
    import asyncio
    from app.core import db
    from app.sheets import store
    from app.sheets.tabs import ACTIVIDAD, WITHINGS
    from app.sources import withings
    uid = make_user("jaimetur").id
    tokens = iter([{"access_token": "a1", "refresh_token": "r1", "expires_in": 10800, "userid": 7},
                   {"access_token": "a2", "refresh_token": "r2", "expires_in": 10800, "userid": 7}])
    tok_route = respx.post(withings.TOKEN_URL).mock(side_effect=lambda req: httpx.Response(200, json={"status": 0, "body": next(tokens)}))
    respx.post(withings.MEASURE_URL).mock(side_effect=lambda req: httpx.Response(200, json={"status": 0, "body": (
        {"measuregrps": [{"grpid": 111, "attrib": 0, "date": ts("2026-11-19 07:35"),
                          "measures": [{"type": 1, "value": 108800, "unit": -3}, {"type": 6, "value": 401, "unit": -1}]}], "more": 0}
        if "meastypes=1%2C6" in req.content.decode() else {"measuregrps": [], "more": 0})}))
    respx.post(withings.V2_MEASURE_URL).mock(side_effect=lambda req: httpx.Response(200, json={"status": 0, "body": (
        {"activities": [{"date": "2026-11-18", "steps": 9000, "distance": 6500.4, "calories": 410.6, "totalcalories": 2800, "model": "Watch"}], "more": False}
        if "getactivity" in req.content.decode() else {"series": [], "more": False})}))
    respx.post(withings.V2_SLEEP_URL).mock(return_value=httpx.Response(200, json={"status": 0, "body": {"series": []}}))
    respx.post(withings.HEART_URL).mock(return_value=httpx.Response(200, json={"status": 0, "body": {"series": [], "more": False}}))
    u = withings.authorize_url("st")
    assert "client_id=cid" in u and "redirect_uri=https%3A%2F%2Fbodylens.example.test%2Foauth%2Fwithings%2Fcallback" in u

    async def run():
        async with httpx.AsyncClient() as c:
            await withings.exchange_code(c, uid, "CODE")
            assert parse_qs(tok_route.calls.last.request.content.decode())["grant_type"] == ["authorization_code"]
            # caducado: se renueva y se guarda el refresh token nuevo
            t = withings.load_tokens(uid); t["expires"] = time.time() - 1; withings.save_tokens(uid, t)
            return await withings.sync(uid, c)
    res = asyncio.run(run())
    assert res["errores"] == [] and res["pesadas"] == 1
    assert withings.load_tokens(uid)["refresh_token"] == "r2"
    with db.ro() as con:
        w = store.read_rows(con, uid, WITHINGS)["111"]
        a = store.read_rows(con, uid, ACTIVIDAD)["2026-11-18"]
    assert w[0] == datetime(2026, 11, 19, 7, 35) and w[2] == 108.8 and w[3] == 40.1
    assert a[1] == 9000 and a[2] == 6500 and a[7] == 411


def test_withings_no_pisa_salud(wenv, make_user):
    from app.core import db
    from app.sheets import rules, store
    from app.sheets.tabs import ACTIVIDAD
    uid = make_user("jaimetur").id
    with db.tx() as con:
        store.save_rows(con, uid, ACTIVIDAD, {"2026-11-18": [datetime(2026, 11, 18, 12), 12000, 8000, "", "", 30, "", 500, "", "", "", "", "Apple Salud"]})
        store.save_rows(con, uid, ACTIVIDAD, {"2026-11-18": [datetime(2026, 11, 18, 12), 9000, 6500, 10, 40, 20, 5, 410, 2800, 70, 50, 120, "Watch"]},
                        merge=rules.mezcla_withings(12))
        a = store.read_rows(con, uid, ACTIVIDAD)["2026-11-18"]
    assert a[1] == 12000 and a[3] == 10 and a[4] == 40 and a[12] == "Apple Salud"
