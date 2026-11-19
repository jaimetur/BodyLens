import io
from datetime import datetime

from openpyxl import load_workbook

AS, AW = "AutoSleep", "Apple Watch de Prueba"


def seg(start, end, value, source):
    return {"startDate": start + " +0100", "endDate": end + " +0100", "value": value, "source": source}


def sleep(*segs):
    return {"data": {"metrics": [{"name": "sleep_analysis", "units": "hr", "data": list(segs)}]}}


def _uid(make_user):
    return make_user("jaimetur").id


def _rows(uid, tab):
    from app.core import db
    from app.sheets import store
    with db.ro() as con:
        return store.read_rows(con, uid, tab)


def _ingest(uid, body):
    from app.core import db
    from app.sources import hae
    with db.tx() as con:
        return hae.ingest(con, uid, body)


def test_noche_solo_autosleep_con_desvelo(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    r = _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 02:00:00", "Asleep", AS),
                           seg("2026-11-19 02:30:00", "2026-11-19 07:00:00", "Asleep", AS)))
    assert r["noches"] == 1
    n = _rows(uid, SUENO)["2026-11-19"]
    assert n[1] == datetime(2026, 11, 18, 23) and n[2] == datetime(2026, 11, 19, 7)
    assert n[3] == 480 and n[4] == 450 and n[8] == 30 and n[13] == "Apple Salud"
    assert n[14] == "120~150"   # desvelo de 02:00 a 02:30


def test_autosleep_corto_frente_al_reloj(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-19 05:00:00", "2026-11-19 07:00:00", "Asleep", AS),
                       seg("2026-11-18 23:00:00", "2026-11-19 03:00:00", "Core", AW),
                       seg("2026-11-19 03:00:00", "2026-11-19 04:00:00", "Deep", AW),
                       seg("2026-11-19 04:00:00", "2026-11-19 07:00:00", "REM", AW)))
    n = _rows(uid, SUENO)["2026-11-19"]
    assert n[4] == 480 and n[6] == 60 and n[7] == 180   # manda el reloj: 8 h, profundo 1 h, REM 3 h


def test_autosleep_completo_con_fases_del_reloj(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AS),
                       seg("2026-11-18 23:30:00", "2026-11-19 00:30:00", "Deep", AW),
                       seg("2026-11-19 00:30:00", "2026-11-19 06:00:00", "Core", AW)))
    n = _rows(uid, SUENO)["2026-11-19"]
    assert n[4] == 480 and n[6] == 60   # horario de AutoSleep, profundo del reloj


def test_phases_of_the_night_from_the_watch(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AS),
                       seg("2026-11-18 23:30:00", "2026-11-19 00:30:00", "Deep", AW),
                       seg("2026-11-19 00:30:00", "2026-11-19 02:00:00", "Core", AW),
                       seg("2026-11-19 02:00:00", "2026-11-19 02:20:00", "Awake", AW),
                       seg("2026-11-19 02:20:00", "2026-11-19 03:00:00", "REM", AW)))
    n = _rows(uid, SUENO)["2026-11-19"]
    # AutoSleep rules the schedule, the phases come from the watch (minutes from midnight of the wake-up day)
    assert n[15] == "-30~30~d;30~120~l;120~140~w;140~180~r"


def test_no_phases_without_a_source_that_has_them(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AS)))
    assert _rows(uid, SUENO)["2026-11-19"][15] in ("", None)


def test_old_nights_get_their_phases(env, make_user):
    from app.core import db
    from app.sheets import store
    from app.sheets.tabs import SUENO
    from app.sources import hae
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 01:00:00", "Deep", AW),
                       seg("2026-11-19 01:00:00", "2026-11-19 07:00:00", "Core", AW)))
    with db.tx() as con:   # a night saved before the column existed
        r = store.read_rows(con, uid, SUENO)["2026-11-19"]
        store.save_rows(con, uid, SUENO, {"2026-11-19": r[:15]})
    assert _rows(uid, SUENO)["2026-11-19"][15] in ("", None)
    with db.tx() as con:
        assert hae.rellenar_fases(con, uid) == 1
        assert hae.rellenar_fases(con, uid) == 0
    assert _rows(uid, SUENO)["2026-11-19"][15] == "-60~60~d;60~420~l"


def test_siesta_de_la_tarde(env, make_user):
    from app.sheets.tabs import SIESTAS, SUENO
    uid = _uid(make_user)
    r = _ingest(uid, sleep(seg("2026-11-18 15:00:00", "2026-11-18 15:40:00", "Asleep", AS)))
    assert r["noches"] == 0 and "2026-11-18" not in _rows(uid, SUENO)
    s = list(_rows(uid, SIESTAS).values())
    assert len(s) == 1 and s[0][4] == 40 and s[0][2] == datetime(2026, 11, 18, 15)


def test_reenvio_corrige_tramos(env, make_user):
    from app.sheets.tabs import FASES, SUENO
    uid = _uid(make_user)
    _ingest(uid, sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AS)))
    assert _rows(uid, SUENO)["2026-11-19"][4] == 480
    # AutoSleep rehace la noche: el envío siguiente cubre desde las 22:00 y ya no trae el tramo de las 23:00
    # (lo que esa app tenía dentro del periodo que cubre el envío y ya no viene, se quita)
    _ingest(uid, sleep(seg("2026-11-18 22:00:00", "2026-11-18 22:05:00", "Awake", AS),
                       seg("2026-11-18 23:30:00", "2026-11-19 06:30:00", "Asleep", AS)))
    assert _rows(uid, SUENO)["2026-11-19"][4] == 420
    assert len(_rows(uid, FASES)) == 2


def test_noche_sin_datos(env, make_user):
    from app.sheets.tabs import SUENO
    uid = _uid(make_user)
    assert _ingest(uid, sleep()).get("noches", 0) == 0
    assert _rows(uid, SUENO) == {}


def test_actividad_registros_y_animo(env, make_user):
    from app.sheets.tabs import ACTIVIDAD, REGISTROS, SALUD
    uid = _uid(make_user)
    body = {"data": {"metrics": [
        {"name": "step_count", "units": "count", "data": [{"date": "2026-11-19 08:00:00 +0100", "qty": 1200, "source": "iPhone"},
                                                          {"date": "2026-11-19 09:00:00 +0100", "qty": 800.4}]},
        {"name": "active_energy", "units": "kJ", "data": [{"date": "2026-11-19 08:00:00 +0100", "qty": 418.4}]},
        {"name": "resting_heart_rate", "units": "count/min", "data": [{"date": "2026-11-19 07:00:00 +0100", "qty": 52}]},
        {"name": "sexual_activity", "units": "count", "data": [{"date": "2026-11-18 23:00:00 +0100", "qty": 1}]},
    ], "stateOfMind": [{"start": "2026-11-19 10:00:00 +0100", "valence": 0.5, "kind": "momentaryEmotion", "labels": ["Calm"]}]}}
    r = _ingest(uid, body)
    assert r["metricas"] == 4 and r["registros"] == 2
    a = _rows(uid, ACTIVIDAD)["2026-11-19"]
    assert a[1] == 2000 and a[7] == 100 and a[12] == "Apple Salud"   # 418,4 kJ = 100 kcal
    assert any(v[1] == "rhr" for v in _rows(uid, SALUD).values())
    regs = {v[2]: v[3] for v in _rows(uid, REGISTROS).values()}
    assert regs["sexual_activity"] == 1
    assert '"v":0.5' in regs["stateofmind"] and '"l":["Calm"]' in regs["stateofmind"]


def test_entrenos_quitan_copia_de_withings(env, make_user):
    from app.core import db
    from app.sheets import store
    from app.sheets.tabs import ENTRENOS
    uid = _uid(make_user)
    with db.tx() as con:
        store.save_rows(con, uid, ENTRENOS, {"999": ["999", datetime(2026, 11, 19, 12), datetime(2026, 11, 19, 18, 5),
                                                    datetime(2026, 11, 19, 19), 55, "Caminar"]})
    _ingest(uid, {"data": {"workouts": [{"id": "W1", "name": "Outdoor Walk", "start": "2026-11-19 18:00:00 +0100",
                                         "end": "2026-11-19 19:00:00 +0100", "duration": 3600,
                                         "activeEnergyBurned": {"qty": 250, "units": "kcal"}}]}})
    w = _rows(uid, ENTRENOS)
    assert list(w) == ["hk-W1"] and w["hk-W1"][5] == "Caminar" and w["hk-W1"][6] == 250 and w["hk-W1"][4] == 60


def test_endpoint_pasa_la_cuenta_al_servidor(client, make_user, login):
    make_user("jaimetur")
    c = login("jaimetur")
    url = c.post("/api/sources/hae/token").json()["url"]
    token = url.rsplit("/", 1)[1]
    assert c.get("/api/sources").json()["dataSource"] == "server"   # new accounts keep their data on the server
    anon = client.__class__(client.app)
    assert anon.post("/api/ingest/hae/malo", json={}).json() == {"ok": False, "error": "token"}
    r = anon.post(f"/api/ingest/hae/{token}", json=sleep(seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "Asleep", AS)))
    assert r.json()["noches"] == 1
    s = c.get("/api/sources").json()
    assert s["dataSource"] == "server" and s["hae"]["last"]["noches"] == 1 and s["hae"]["url"] == url
    wb = load_workbook(io.BytesIO(c.get("/api/workbook.xlsx").content), data_only=True)
    rows = list(wb["Sueño"].iter_rows(values_only=True))
    assert rows[0][0] == "Fecha" and rows[1][4] == 480
    # cambiar la dirección invalida la anterior
    c.post("/api/sources/hae/token")
    assert anon.post(f"/api/ingest/hae/{token}", json={}).json()["error"] == "token"


def test_el_registro_no_muestra_secretos():
    import logging
    from app.main import _HideSecrets
    rec = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d', (
        "1.2.3.4:0", "POST", "/api/ingest/hae/SECRETO123?x=1", "1.1", 200), None)
    rec2 = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d', (
        "1.2.3.4:0", "GET", "/oauth/withings/callback?code=ABC&state=XYZ", "1.1", 303), None)
    f = _HideSecrets()
    f.filter(rec); f.filter(rec2)
    assert "SECRETO123" not in rec.getMessage() and "/api/ingest/hae/***" in rec.getMessage()
    assert "ABC" not in rec2.getMessage() and "XYZ" not in rec2.getMessage()
