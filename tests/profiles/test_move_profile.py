import json


def _put(con, user, doc_id, data):
    from app.data import docstore
    docstore.put_doc(con, user, "bascula", doc_id, data)


def test_move_profile_to_partner_account(env, make_user):
    from app.accounts import users
    from app.core import db
    from app.data import docstore, profiles
    j = make_user("jaimetur", "Jaime Tur", admin=True)
    l = make_user("laura", "Laura Romero")
    sex = ["sexual", "2026-11-02T23:00", "2026-11-02T23:00", "1", "app"]
    mood = ["mood", "2026-11-01", "2026-11-01", "{}", "app"]
    cyc = ["menstrual", "2026-11-03", "2026-11-03", "2", "Salud"]
    with db.tx() as con:
        _put(con, j, "hklog", {"v": 1, "e": [mood, sex]})
        _put(con, j, "peso", {"cfg": {"goal": 80}})
        _put(con, j, "pf-laura-hklog", {"v": 1, "e": [cyc]})
        _put(con, j, "pf-laura-peso", {"cfg": {"goal": 60}})
        _put(con, j, "perfiles", {"v": 1, "list": [
            {"id": "", "name": "Jaime Tur", "partner": "laura", "partnerSince": "2026-03-08"},
            {"id": "laura", "name": "Laura Romero", "cycle": 1, "partner": "", "partnerSince": "2026-03-08"}]})
        r = profiles.move_profile_by_names(con, "jaimetur", "laura", "laura")
    assert r == {"documents": 2, "linked": True, "since": "2026-03-08"}
    with db.ro() as con:
        j2, l2 = users.get_user(con, j.id), users.get_user(con, l.id)
        assert j2.partner_id == l.id and j2.partner_since == "2026-03-08"
        jd = {d["id"]: d["data"] for d in docstore.list_docs(con, j2, "bascula")["docs"]}
        ld = {d["id"]: d["data"] for d in docstore.list_docs(con, l2, "bascula")["docs"]}
    assert not any(k.startswith("pf-") for k in jd)
    assert jd["perfiles"]["list"] == [{"id": "", "name": "Jaime Tur"}]
    assert ld["peso"] == {"cfg": {"goal": 60}}
    # el ciclo de Laura y la intimidad se ven desde las dos cuentas; el ánimo de Jaime sigue siendo suyo
    assert jd["hklog"]["e"] == [mood, sex, cyc]
    assert ld["hklog"]["e"] == [sex, cyc]


def test_move_profile_errors(env, make_user):
    import pytest
    from app.core import db
    from app.data import profiles
    make_user("ana"); make_user("bea")
    with db.tx() as con, pytest.raises(profiles.ProfileError):
        profiles.move_profile_by_names(con, "ana", "nadie", "bea")
    with db.tx() as con, pytest.raises(profiles.ProfileError):
        profiles.move_profile_by_names(con, "ana", "", "bea")
