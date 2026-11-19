"""Theme and inactivity-lock minutes of each account (Your account → Profile)."""


def test_theme_and_lock_minutes(client, make_user, login):
    make_user("ana")
    c = login("ana")
    me = c.get("/api/me").json()["user"]
    assert me["theme"] == "auto" and me["lockMin"] == 1          # defaults
    assert 'data-theme' not in c.get("/").text.split("<body>")[0]   # auto: the device decides

    assert c.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200
    assert c.post("/api/me/theme", json={"theme": "pink"}).status_code == 400
    head = c.get("/").text.split("<body>")[0]
    assert "setAttribute('data-theme','ocean')" in head and 'html:root[data-theme="ocean"]' in head
    assert "setAttribute('data-theme','ocean')" in c.get("/cuenta").text   # server pages too

    assert c.post("/api/me/lock", json={"minutes": 5}).status_code == 200
    assert c.post("/api/me/lock", json={"minutes": 7}).status_code == 400
    me = c.get("/api/me").json()["user"]
    assert me["theme"] == "ocean" and me["lockMin"] == 5
