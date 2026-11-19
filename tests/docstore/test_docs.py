def test_crud_and_polling(client, make_user, login):
    make_user("jaime")
    c = login("jaime")
    assert c.get("/api/docs/bascula").json()["docs"] == []
    r1 = c.put("/api/docs/bascula/peso", json={"cfg": {"goal": 80}}).json()["rev"]
    c.put("/api/docs/bascula/hist-2026", json={"y": 2026, "d": {}})
    full = c.get("/api/docs/bascula").json()
    assert {d["id"] for d in full["docs"]} == {"peso", "hist-2026"}
    since = full["rev"]
    assert c.get(f"/api/docs/bascula?since={since}").json()["docs"] == []
    r = c.patch("/api/docs/bascula/peso", json={"notes": {"2026-01-01": "x"}}).json()
    assert r["data"] == {"cfg": {"goal": 80}, "notes": {"2026-01-01": "x"}} and r["rev"] > r1
    c.delete("/api/docs/bascula/hist-2026")
    ch = c.get(f"/api/docs/bascula?since={since}").json()["docs"]
    assert {(d["id"], d.get("deleted", False)) for d in ch} == {("peso", False), ("hist-2026", True)}
    assert c.get("/api/docs/bascula/hist-2026").status_code == 404
    assert "hist-2026" not in {d["id"] for d in c.get("/api/docs/bascula").json()["docs"]}


def test_users_are_isolated(client, make_user, login):
    make_user("jaime"); make_user("laura")
    j = login("jaime"); l = login("laura")
    j.put("/api/docs/bascula/peso", json={"secreto": 1})
    assert l.get("/api/docs/bascula").json()["docs"] == []
    assert l.get("/api/docs/bascula/peso").status_code == 404


def test_bad_names(client, make_user, login):
    make_user("jaime")
    c = login("jaime")
    assert c.put("/api/docs/bascula/..%2Fx", json={}).status_code in (400, 404)
    assert c.put("/api/docs/bascula/ok", json=[1, 2]).status_code == 400


def _log(*events):
    return {"v": 1, "e": [list(e) for e in events]}


def test_couple_shares_cycle_and_intimacy(client, make_user, login):
    make_user("jaime"); make_user("laura")
    j = login("jaime"); l = login("laura")
    mood = ["mood", "2026-11-01T10:00", "2026-11-01T10:00", "{}", "app"]
    sex_j = ["sexual", "2026-11-02T23:00", "2026-11-02T23:00", "1", "app"]
    cyc_l = ["menstrual", "2026-11-03", "2026-11-03", "2", "Salud"]
    j.put("/api/docs/bascula/hklog", json=_log(mood, sex_j))
    l.put("/api/docs/bascula/hklog", json=_log(cyc_l))
    # antes de unirse, nada se comparte
    assert l.get("/api/docs/bascula/hklog").json()["data"]["e"] == [cyc_l]

    j.post("/api/partner/request", json={"username": "laura", "since": "2026-03-01"})
    assert l.get("/api/me").json()["requests"]["incoming"][0]["username"] == "jaime"
    assert l.post("/api/partner/accept", json={"username": "jaime"}).status_code == 200
    assert j.get("/api/me").json()["partner"] == {"username": "laura", "name": "Laura", "since": "2026-03-01"}

    since = l.get("/api/docs/bascula").json()["rev"]
    assert j.get("/api/docs/bascula/hklog").json()["data"]["e"] == [mood, sex_j, cyc_l]
    assert l.get("/api/docs/bascula/hklog").json()["data"]["e"] == [sex_j, cyc_l]  # el ánimo de Jaime no

    # Laura borra el registro de intimidad y añade uno de ciclo: Jaime lo ve (y su sondeo lo detecta)
    cyc2 = ["menstrual", "2026-11-04", "2026-11-04", "1", "app"]
    jsince = j.get("/api/docs/bascula").json()["rev"]
    l.put("/api/docs/bascula/hklog", json=_log(cyc_l, cyc2))
    changed = j.get(f"/api/docs/bascula?since={jsince}").json()["docs"]
    assert [d["id"] for d in changed] == ["hklog"]
    assert changed[0]["data"]["e"] == [mood, cyc_l, cyc2]

    # al separarse cada uno conserva una copia
    j.post("/api/partner/unlink")
    assert j.get("/api/docs/bascula/hklog").json()["data"]["e"] == [mood, cyc_l, cyc2]
    assert l.get("/api/docs/bascula/hklog").json()["data"]["e"] == [cyc_l, cyc2]
    j.put("/api/docs/bascula/hklog", json=_log(mood))
    assert l.get("/api/docs/bascula/hklog").json()["data"]["e"] == [cyc_l, cyc2]
    assert since  # (rev usado)


def test_mutual_request_links_directly(client, make_user, login):
    make_user("jaime"); make_user("laura"); make_user("otra")
    j = login("jaime"); l = login("laura"); o = login("otra")
    j.post("/api/partner/request", json={"username": "laura"})
    assert l.post("/api/partner/request", json={"username": "jaime"}).json()["linked"] is True
    assert o.post("/api/partner/request", json={"username": "jaime"}).status_code == 409
    assert j.post("/api/partner/request", json={"username": "nadie"}).status_code == 404
