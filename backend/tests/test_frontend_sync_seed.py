import io
import json
import zipfile

import httpx
import pytest
import respx


def _xlsx(marker: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.txt", marker)
    return b.getvalue()


def test_page_is_served_with_shim(client, make_user, login):
    make_user("laura", "Laura Romero")
    c = login("laura")
    html = c.get("/").text
    assert html.startswith("<!doctype html>")
    assert '<script src="/claude-shim.js"></script>' in html
    assert '"name": "Laura Romero"' in html
    assert "cdnjs.cloudflare.com/ajax/libs/xlsx" not in html
    assert "script.google.com" not in html
    assert "1aUMgruI3VycOCjbqH4" not in html
    assert "BL.profDef()" in html and "BL.pull()" in html
    assert c.get("/claude-shim.js").status_code == 200
    assert c.get("/manifest.webmanifest").json()["name"] == "BodyLens"
    assert c.get("/icon-192.png").status_code == 200
    assert c.get("/healthz").json() == {"ok": True}


def test_assembly_detects_changes(env, monkeypatch):
    from app import frontend
    monkeypatch.setattr(frontend, "REPLACEMENTS", frontend.REPLACEMENTS + [("no existe en la app", "x")])
    with pytest.raises(frontend.AssemblyError):
        frontend.assemble_fragment()


@respx.mock
def test_sync_bridge(client, make_user, login, monkeypatch):
    from app import db, google_bridge, users
    u = make_user("jaime", admin=True)
    with db.tx() as con:
        users.update_bridge(con, u.id, "A" * 44, "https://script.google.com/macros/s/xyz/exec")

    async def fake_token():
        return "tok"
    monkeypatch.setattr(google_bridge, "drive_token", fake_token)
    script = respx.get("https://script.google.com/macros/s/xyz/exec?accion=sincronizar").mock(return_value=httpx.Response(200, text="ok"))
    export = respx.get(url__startswith=f"https://www.googleapis.com/drive/v3/files/{'A' * 44}/export").mock(
        return_value=httpx.Response(200, content=_xlsx("v1")))

    c = login("jaime")
    assert c.get("/api/workbook.xlsx").status_code == 404
    r = c.post("/api/sync").json()
    assert r["ok"] and r["workbook"]["changed"] and script.called and export.called
    assert export.calls.last.request.headers["authorization"] == "Bearer tok"
    meta = c.get("/api/workbook/meta").json()
    wb = c.get("/api/workbook.xlsx")
    assert wb.status_code == 200 and wb.content == _xlsx("v1") and wb.headers["etag"] == f'"{meta["etag"]}"'
    assert c.get("/api/workbook.xlsx", headers={"If-None-Match": wb.headers["etag"]}).status_code == 304
    # sin cambios: mismo ETag
    r = c.post("/api/sync").json()
    assert r["workbook"]["changed"] is False and "al día" in r["message"]
    # cambio en la hoja: ETag nuevo
    export.mock(return_value=httpx.Response(200, content=_xlsx("v2")))
    assert c.post("/api/sync").json()["workbook"]["changed"] is True
    assert c.get("/api/workbook/meta").json()["etag"] != meta["etag"]


@respx.mock
def test_sync_reports_errors(client, make_user, login, monkeypatch):
    from app import db, google_bridge, users
    u = make_user("jaime")
    with db.tx() as con:
        users.update_bridge(con, u.id, "B" * 44, None)

    async def fake_token():
        return "tok"
    monkeypatch.setattr(google_bridge, "drive_token", fake_token)
    respx.get(url__startswith="https://www.googleapis.com/drive/v3/files/").mock(return_value=httpx.Response(404))
    r = login("jaime").post("/api/sync").json()
    assert r["ok"] is False and "compártela" in r["message"]


def test_sync_without_sources(client, make_user, login):
    make_user("laura")
    r = login("laura").post("/api/sync").json()
    assert r["ok"] is False and "fuentes" in r["message"]


def test_bridge_only_by_admin(client, make_user, login):
    make_user("jaime", admin=True)
    l = make_user("laura")
    a = login("jaime")
    assert a.put(f"/api/admin/users/{l.id}/bridge", json={"sheetId": "corto"}).status_code == 400
    assert a.put(f"/api/admin/users/{l.id}/bridge", json={"sheetId": "C" * 44, "appsScriptUrl": ""}).status_code == 200
    assert login("laura").put(f"/api/admin/users/{l.id}/bridge", json={"sheetId": "D" * 44}).status_code == 403


def test_seed(env, make_user, tmp_path):
    from app import db, docstore, seed, users
    make_user("jaime"); make_user("laura")
    snap = {
        "at": 1, "doc": {"cfg": {"goal": 80}, "manual": {}},
        "hist": {"2025": {"y": 2025, "d": {"2025-01-01": [100, 30, 30, 40, 50, 3, "w"]}}},
        "act": {"2026": {"y": 2026}}, "food": {"2026": {"y": 2026, "d": {}}}, "med": {"v": 1, "e": {}},
        "hklog": {"v": 1, "e": [["mood", "2026-01-01", "2026-01-01", "{}", "app"]]},
        "prof": {"laura": {"doc": {"cfg": {}}, "hklog": {"v": 1, "e": [["menstrual", "2026-01-02", "2026-01-02", "1", "x"]]}}},
        "profs": [{"id": "", "name": "Jaime"}, {"id": "laura", "name": "Laura", "cycle": 1}],
    }
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    assert seed.seed(str(p), "jaime")["documentos"] == 6
    seed.seed(str(p), "jaime")  # idempotente
    seed.seed(str(p), "laura", profile="laura")
    with db.ro() as con:
        j = users.get_by_username(con, "jaime"); l = users.get_by_username(con, "laura")
        jd = {d["id"]: d["data"] for d in docstore.list_docs(con, j, "bascula")["docs"]}
        ld = {d["id"]: d["data"] for d in docstore.list_docs(con, l, "bascula")["docs"]}
    assert set(jd) == {"peso", "hist-2025", "act-2026", "com-2026", "medidas", "hklog"}
    assert len(jd["hklog"]["e"]) == 1 and "perfiles" not in jd
    assert set(ld) == {"peso", "hklog"} and ld["hklog"]["e"][0][0] == "menstrual"
    with pytest.raises(SystemExit):
        seed.seed(str(p), "nadie")


def test_import_from_web(client, make_user, login):
    make_user("laura")
    c = login("laura")
    snap = {"doc": {"cfg": {}}, "hklog": {"v": 1, "e": [["mood", "a", "a", "{}", "x"]]},
            "prof": {"laura": {"doc": {"cfg": {"goal": 60}}, "hist": {"2026": {"y": 2026, "d": {}}}}},
            "profs": [{"id": "", "name": "Jaime"}, {"id": "laura", "name": "Laura"}]}
    assert c.post("/api/import", json={"copy": {"nada": 1}}).status_code == 400
    assert c.post("/api/import", json={"copy": snap, "profile": "otro"}).status_code == 400
    r = c.post("/api/import", json={"copy": snap, "profile": "laura"})
    assert r.status_code == 200 and r.json()["documents"] == 2
    ids = {d["id"] for d in c.get("/api/docs/bascula").json()["docs"]}
    assert ids == {"peso", "hist-2026"}
    assert c.get("/api/docs/bascula/peso").json()["data"]["cfg"]["goal"] == 60
