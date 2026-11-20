"""Lo que envía la app de Android (Health Connect con el formato de Health Auto Export) entra igual que desde el iPhone."""
from datetime import datetime

from tests.sources.test_hae import _ingest, _rows, _uid

PKG = "com.sec.android.app.shealth"


def d(s):
    return s + " +0100"


def payload():
    hourly = lambda name, units, vals: {"name": name, "units": units, "data": [
        {"date": d(f"2026-11-18 {h:02d}:00:00"), "qty": v} for h, v in vals]}
    seg = lambda a, b, v: {"startDate": d(a), "endDate": d(b), "value": v, "source": PKG}
    return {"data": {
        "metrics": [
            hourly("step_count", "count", [(9, 1200), (10, 3000)]),
            hourly("walking_running_distance", "km", [(9, 0.9), (10, 2.1)]),
            hourly("active_energy", "kcal", [(9, 60.4), (10, 140.2)]),
            {"name": "heart_rate", "units": "count/min", "data": [
                {"date": d("2026-11-18 09:00:00"), "Avg": 80, "Min": 60, "Max": 120},
                {"date": d("2026-11-18 10:00:00"), "Avg": 90, "Min": 70, "Max": 140}]},
            {"name": "resting_heart_rate", "units": "count/min", "data": [{"date": d("2026-11-18 08:00:00"), "qty": 55, "source": PKG}]},
            {"name": "menstrual_flow", "units": "", "data": [{"date": d("2026-11-18 08:00:00"), "value": "medium", "source": PKG}]},
            {"name": "sleep_analysis", "units": "hr", "data": [
                seg("2026-11-18 23:00:00", "2026-11-19 07:00:00", "In Bed"),
                seg("2026-11-18 23:10:00", "2026-11-19 02:00:00", "Core"),
                seg("2026-11-19 02:00:00", "2026-11-19 03:00:00", "Deep"),
                seg("2026-11-19 03:00:00", "2026-11-19 03:20:00", "Awake"),
                seg("2026-11-19 03:20:00", "2026-11-19 06:50:00", "REM")]},
        ],
        "workouts": [{"id": "abc-123", "name": "Running", "start": d("2026-11-18 18:00:00"), "end": d("2026-11-18 18:30:00"),
                      "duration": 1800, "source": PKG, "activeEnergyBurned": {"qty": 300.4, "units": "kcal"},
                      "distance": {"qty": 5.02, "units": "km"},
                      "heartRate": {"avg": {"qty": 150}, "min": {"qty": 100}, "max": {"qty": 175}}}],
    }}


def test_envio_de_android(env, make_user):
    from app.sheets.tabs import ACTIVIDAD, ENTRENOS, REGISTROS, SUENO
    uid = _uid(make_user)
    r = _ingest(uid, payload())
    assert r["noches"] == 1
    a = _rows(uid, ACTIVIDAD)["2026-11-18"]
    assert a[1] == 4200 and a[2] == 3000 and a[7] == 201 and a[9] == 85 and a[10] == 60 and a[11] == 140
    n = _rows(uid, SUENO)["2026-11-19"]
    assert n[1] == datetime(2026, 11, 18, 23, 10) and n[2] == datetime(2026, 11, 19, 6, 50)
    assert n[4] == 440 and n[5] == 170 and n[6] == 60 and n[7] == 210 and n[14] == "180~200"   # desvelo de 03:00 a 03:20
    w = next(iter(_rows(uid, ENTRENOS).values()))
    assert w[0] == "hk-abc-123"
    assert any(x[2] == "menstrual_flow" and x[3] == "medium" for x in _rows(uid, REGISTROS).values())


def test_descarga_del_apk(client, make_user, login, env):
    from app.core import config
    make_user("jaimetur")
    assert client.get("/android.apk").status_code == 404        # public (the landing page links it), but not there yet
    c = login("jaimetur")
    assert c.get("/android.apk").status_code == 404
    assert c.get("/api/sources").json()["androidApk"] is False
    p = config.settings.data_dir / "downloads"
    p.mkdir()
    (p / "bodylens-android.apk").write_bytes(b"PK\x03\x04apk")
    r = c.get("/android.apk")
    assert r.status_code == 200 and r.content == b"PK\x03\x04apk" and "android.package-archive" in r.headers["content-type"]
    assert client.get("/android.apk").status_code == 200        # without signing in too
    assert c.get("/api/sources").json()["androidApk"] is True
