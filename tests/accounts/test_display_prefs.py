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


def test_navigation_is_kept_on_the_server(client, make_user, login):
    make_user("eva")
    c = login("eva")
    nav = {"": {"h": "#sueno", "vt": {"sueno": "hor"}, "t": 1}, "pa": {"h": "#comidas", "t": 2}}
    assert c.post("/api/me/nav", json={"nav": nav}).status_code == 200
    assert c.get("/api/me").json()["user"]["nav"] == nav
    assert '"h": "#sueno"' in c.get("/").text          # the app page gets it at start
    assert c.post("/api/me/nav", json={"nav": {"x": "y" * 40_000}}).status_code == 400
