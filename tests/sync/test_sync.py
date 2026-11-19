import io
import zipfile

import httpx
import respx


def _xlsx(marker: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.txt", marker)
    return b.getvalue()


@respx.mock
def test_sync_bridge(client, make_user, login, monkeypatch):
    from app.accounts import users
    from app.core import db
    from app.sync import google_bridge
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
    from app.accounts import users
    from app.core import db
    from app.sync import google_bridge
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
