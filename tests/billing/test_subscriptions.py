"""Accounts paid with a Google Play subscription (Google's answers are simulated)."""
import time

import pytest

NOW = lambda: int(time.time() * 1000)   # noqa: E731


@pytest.fixture()
def google(monkeypatch):
    from app.billing import play
    state = {"tok-1": {"active": True, "state": "SUBSCRIPTION_STATE_ACTIVE", "product": "bodylens", "basePlan": "monthly",
                       "expiry": NOW() + 7 * 86400_000, "acknowledged": False}}
    acks = []
    monkeypatch.setattr(play, "configured", lambda: True)
    monkeypatch.setattr(play, "check", lambda t: dict(state[t]) if t in state else (_ for _ in ()).throw(play.PlayError("Google Play no reconoce esa compra.")))
    monkeypatch.setattr(play, "acknowledge", lambda t, p: acks.append(t))
    return state, acks


def _signup(client, token="tok-1", username="nuria"):
    return client.post("/api/play/signup", json={"token": token, "username": username, "name": "Nuria",
                                                 "email": f"{username}@example.com", "password": "contraseña-larga"})


def test_signup_with_a_subscription(client, google):
    state, acks = google
    assert client.get("/api/play/config").json()["enabled"] is True
    r = _signup(client)
    assert r.status_code == 200, r.text
    assert acks == ["tok-1"]                                    # acknowledged, or Google would refund it
    assert client.get("/api/me").status_code == 200             # signed in
    st = client.get("/api/play/status").json()
    assert st["plan"] == "play" and st["active"] and st["basePlan"] == "monthly"
    assert _signup(client, username="otra").status_code == 400  # one account per purchase
    assert _signup(client, token="unknown", username="otra").status_code == 400


def test_an_inactive_purchase_is_refused(client, google):
    state, _ = google
    state["tok-1"].update(active=False, state="SUBSCRIPTION_STATE_EXPIRED")
    assert _signup(client).status_code == 400


def test_expired_subscription_leaves_the_app_read_only_until_renewed(client, google, monkeypatch):
    state, _ = google
    assert _signup(client).status_code == 200
    from app.core import db
    with db.tx() as con:   # the paid period ended a while ago, and Google says so
        con.execute("UPDATE subscriptions SET expiry_ms=?, checked_at=0", (NOW() - 1000,))
    state["tok-1"].update(active=False, state="SUBSCRIPTION_STATE_EXPIRED", expiry=NOW() - 1000)
    assert client.get("/api/me").status_code == 200              # still allowed
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 402   # read-only
    assert client.post("/api/sync").status_code == 402
    assert client.get("/api/sources").status_code == 200                              # reading still works
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 200 and 'id="roDay"' in r.text                            # the app with the banner
    st = client.get("/api/play/status").json()
    assert st["active"] is False and st["readOnly"] and 29 < (st["deleteOn"] - NOW()) / 86400_000 <= 30
    # renewed in the app: a new purchase token linked to the account
    state["tok-2"] = {"active": True, "state": "SUBSCRIPTION_STATE_ACTIVE", "product": "bodylens", "basePlan": "yearly",
                      "expiry": NOW() + 365 * 86400_000, "acknowledged": True}
    r = client.post("/api/play/link", json={"token": "tok-2"})
    assert r.status_code == 200 and r.json()["active"] and r.json()["basePlan"] == "yearly"
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200
    assert "readOnly" not in client.get("/api/play/status").json() and 'id="roDay"' not in client.get("/").text


def test_accounts_without_a_subscription_never_expire(client, make_user, login):
    make_user("ana")
    c = login("ana")
    assert c.get("/api/play/status").json() == {"plan": "free"}
    assert c.post("/api/me/theme", json={"theme": "ocean"}).status_code == 200


def test_play_settings_in_administration(client, make_user, login):
    make_user("root", admin=True)
    c = login("root")
    assert c.put("/api/admin/play", json={"serviceAccount": "not json"}).status_code == 400
    sa = '{"client_email": "x@y.iam.gserviceaccount.com", "private_key": "-----BEGIN PRIVATE KEY-----", "type": "service_account"}'
    r = c.put("/api/admin/play", json={"serviceAccount": sa})
    assert r.status_code == 200 and r.json()["configured"] and r.json()["serviceAccount"].startswith("x@")
    assert "private_key" not in r.text
