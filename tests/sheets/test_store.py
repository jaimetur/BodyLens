import io
from datetime import datetime

from openpyxl import Workbook, load_workbook


def _user(make_user):
    return make_user("jaimetur").id


def test_save_rows_merge_remove_and_sort(env, make_user):
    from app.core import db
    from app.sheets import store
    from app.sheets.tabs import ACTIVIDAD, ENTRENOS
    uid = _user(make_user)
    d = lambda k: datetime.strptime(k + " 12:00", "%Y-%m-%d %H:%M")
    with db.tx() as c:
        n = store.save_rows(c, uid, ACTIVIDAD, {"2026-11-02": [d("2026-11-02"), 5000], "2026-11-01": [d("2026-11-01"), 3000]})
        assert n == 2
        # mezcla: lo nuevo rellena solo los huecos
        fill = lambda old, new, k: [n if (o in ("", None)) else o for o, n in zip(old, new)] if old else new
        store.save_rows(c, uid, ACTIVIDAD, {"2026-11-01": [d("2026-11-01"), 9999, 2200]}, merge=fill)
        rows = store.sorted_rows(c, uid, ACTIVIDAD)
    assert [r[1] for r in rows] == [3000, 5000] and rows[0][2] == 2200 and len(rows[0]) == len(ACTIVIDAD.headers)
    with db.tx() as c:
        store.save_rows(c, uid, ENTRENOS, {"a": ["a", d("2026-11-01"), datetime(2026, 11, 1, 9)], "b": ["b", d("2026-11-01"), datetime(2026, 11, 1, 8)]})
        # quitar: las que no vienen y cumplen la condición
        store.save_rows(c, uid, ENTRENOS, {"c": ["c", d("2026-11-02"), datetime(2026, 11, 2, 7)]}, remove=lambda r: r[0] == "a")
        rows = store.sorted_rows(c, uid, ENTRENOS)
    assert [r[0] for r in rows] == ["b", "c"]  # ordenadas por «Inicio»


def _sheet_bytes():
    wb = Workbook()
    ws = wb.active; ws.title = "Control Diario"
    ws.append([None, None]); ws.append([None, "CONTROL"]); ws.append(["Fecha", "Peso (kg)"]); ws.append([datetime(2026, 1, 1), 110.5])
    w = wb.create_sheet("Withings")
    w.append(["Fecha y hora", "Timestamp", "Peso (kg)", "Grasa (%)", "Masa grasa (kg)", "Músculo (kg)", "Agua (kg)", "Hueso (kg)", "grpid", "attrib"])
    w.append([datetime(2026, 11, 19, 7, 35), 1795000000, 108.8, 40.1, 43.6, 61.0, 45.0, 3.1, 123, 0])
    w.append([None] * 10)
    s = wb.create_sheet("Salud")
    s.append(["Fecha y hora", "Métrica", "Valor", "Mín", "Máx", "Unidad", "Origen", "Clave"])
    s.append([datetime(2026, 11, 18, 22), "heart_rate", 60, 55, 70, "count/min", "", "heart_rate|1"])
    b = io.BytesIO(); wb.save(b); return b.getvalue()


def test_import_and_build_roundtrip(env, make_user):
    from app.core import db
    from app.sheets import store, xlsx_io
    from app.sheets.tabs import WITHINGS
    uid = _user(make_user)
    with db.tx() as c:
        counts = xlsx_io.import_xlsx(c, uid, _sheet_bytes())
    assert counts["Withings"] == 1 and counts["Control Diario"] == 3
    with db.ro() as c:
        assert store.read_rows(c, uid, WITHINGS)["123"][2] == 108.8
        out = load_workbook(io.BytesIO(xlsx_io.build_xlsx(c, uid)), data_only=True)
    assert out.sheetnames[:3] == ["Control Diario", "Withings", "Salud"]
    assert [c.value for c in out["Withings"][2]][:3] == [datetime(2026, 11, 19, 7, 35), 1795000000, 108.8]
    rows = list(out["Control Diario"].iter_rows(values_only=True))
    assert rows[0][1] == "CONTROL" and rows[2][1] == 110.5   # sin la fila vacía del principio
    assert "Sueño" in out.sheetnames  # las pestañas que escribe el servidor siempre están


def test_rebuild_only_when_dirty(env, make_user):
    from app.sheets import service, store
    from app.core import db
    from app.sheets.tabs import SALUD
    from app.sync import workbook
    uid = _user(make_user)
    service.import_sheet(uid, _sheet_bytes())
    etag = workbook.meta(uid)["etag"]
    assert etag and service.rebuild(uid) is False
    with db.tx() as c:
        store.save_rows(c, uid, SALUD, {"x": [datetime(2026, 11, 19, 8), "step_count", 100, "", "", "count", "", "x"]})
    assert service.rebuild(uid) is True and workbook.meta(uid)["etag"] != etag
