"""Subscriptions on the website (Stripe's answers are simulated) and the three warnings before deleting an account."""
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture()
def stripe_api(monkeypatch):
    from app.billing import stripe
    from app.core import crypto, db
    with db.tx() as con:
        db.set_setting(con, "stripe", {"secret": crypto.encrypt("sk_test_x"), "webhook": crypto.encrypt("whsec_test"),
                                       "prices": {"monthly": "price_m", "yearly": "price_y"}})
    subs = {"sub_1": {"id": "sub_1", "customer": "cus_1", "status": "trialing",
                      "current_period_end": int(time.time()) + 7 * 86400, "items": {"data": [{"price": {"id": "price_y"}}]}}}
    calls = []

    def call(method, path, params=None, secret=None):
        calls.append((method, path, params))
        if path == "/checkout/sessions" and method == "POST":
            return {"id": "cs_1", "url": "https://checkout.stripe.test/cs_1"}
        if path.startswith("/checkout/sessions/"):
            pending = calls[0][2]["metadata"]["pending"]
            return {"id": "cs_1", "status": "complete", "created": int(time.time()), "metadata": {"pending": pending},
                    "subscription": subs["sub_1"]}
        if path.startswith("/subscriptions/"):
            return subs[path.split("/")[-1]]
        raise AssertionError(path)
    monkeypatch.setattr(stripe, "call", call)
    return subs, calls


def _signup(client):
    return client.post("/api/web/signup", json={"plan": "yearly", "username": "lola", "name": "Lola", "email": "lola@example.com",
                                                "password": "contraseña-larga"})


def test_web_signup_makes_the_account_after_paying(client, stripe_api):
    subs, calls = stripe_api
    assert client.get("/api/web/plans").json()["enabled"] is True
    r = _signup(client)
    assert r.status_code == 200 and r.json()["url"].startswith("https://checkout.stripe.test")
    params = calls[0][2]
    assert params["subscription_data"]["trial_period_days"] == 7 and params["line_items"][0]["price"] == "price_y"
    assert client.get("/api/me").status_code == 401                 # no account until Stripe confirms
    r = client.post("/api/web/complete", json={"session_id": "cs_1"})
    assert r.status_code == 200 and r.json()["signedIn"]
    st = client.get("/api/play/status").json()
    assert st["plan"] == "web" and st["active"] and st["basePlan"] == "yearly"
    assert client.post("/api/web/complete", json={"session_id": "cs_1"}).status_code == 200   # idempotent
    assert _signup(client).status_code == 400                        # the username is taken now


def test_webhook_needs_stripe_signature(client, stripe_api):
    subs, _ = stripe_api
    assert _signup(client).status_code == 200
    assert client.post("/api/web/complete", json={"session_id": "cs_1"}).status_code == 200
    ev = json.dumps({"type": "customer.subscription.updated", "data": {"object": {**subs["sub_1"], "status": "canceled"}}}).encode()
    assert client.post("/api/web/webhook", content=ev, headers={"stripe-signature": "t=1,v1=bad"}).status_code == 400
    t = str(int(time.time()))
    sig = hmac.new(b"whsec_test", f"{t}.".encode() + ev, hashlib.sha256).hexdigest()
    assert client.post("/api/web/webhook", content=ev, headers={"stripe-signature": f"t={t},v1={sig}"}).status_code == 200
    assert client.post("/api/me/theme", json={"theme": "ocean"}).status_code == 402   # cancelled: blocked
    assert client.get("/api/play/status").json()["active"] is False


def test_three_warnings_then_the_account_is_deleted(client, stripe_api, monkeypatch):
    subs, _ = stripe_api
    from app.billing import dunning
    from app.core import db
    from app.mail import mailer
    sent = []
    monkeypatch.setattr(mailer, "send_later", lambda to, subject, body, reply_to=None: sent.append(subject))
    assert _signup(client).status_code == 200
    assert client.post("/api/web/complete", json={"session_id": "cs_1"}).status_code == 200
    with db.tx() as con:
        con.execute("UPDATE stripe_subs SET status='canceled'")
    t0 = datetime.now(timezone.utc)
    assert dunning.run_once(t0)["warned"] == 1
    assert dunning.run_once(t0 + timedelta(days=3))["warned"] == 0          # a week between warnings
    assert dunning.run_once(t0 + timedelta(days=7))["warned"] == 1
    assert dunning.run_once(t0 + timedelta(days=14))["warned"] == 1
    assert client.get("/api/play/status").json()["warnings"] == 3
    assert dunning.run_once(t0 + timedelta(days=18))["deleted"] == 0
    assert dunning.run_once(t0 + timedelta(days=21))["deleted"] == 1
    assert len([s for s in sent if "(" in s]) == 3 and any("borrado" in s for s in sent)
    with db.ro() as con:
        assert con.execute("SELECT COUNT(*) FROM users WHERE username='lola'").fetchone()[0] == 0


def test_renewing_clears_the_warnings(client, stripe_api, monkeypatch):
    subs, _ = stripe_api
    from app.billing import dunning
    from app.core import db
    from app.mail import mailer
    monkeypatch.setattr(mailer, "send_later", lambda *a, **k: None)
    assert _signup(client).status_code == 200
    assert client.post("/api/web/complete", json={"session_id": "cs_1"}).status_code == 200
    with db.tx() as con:
        con.execute("UPDATE stripe_subs SET status='canceled'")
    dunning.run_once()
    with db.tx() as con:
        con.execute("UPDATE stripe_subs SET status='active'")
    assert dunning.run_once()["renewed"] == 1
    assert "warnings" not in client.get("/api/play/status").json()
