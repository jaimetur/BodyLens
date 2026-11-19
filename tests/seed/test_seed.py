import json

import pytest


def test_seed(env, make_user, tmp_path):
    from app.accounts import users
    from app.core import db
    from app.data import docstore, importer as seed
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
