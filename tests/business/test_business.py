"""Administration → Business: figures from synthetic data, outside services simulated, and no secret in any answer."""
import json
import time
from datetime import datetime, timedelta, timezone

import pytest

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
DAY = 86400


def _ts(days_ago: float) -> int:
    return int((NOW - timedelta(days=days_ago)).timestamp())


@pytest.fixture()
def data(make_user):
    """Five accounts: two paying on the website (monthly and yearly), one in trial, one on Google Play and one free."""
    from app.core import db
    ids = [make_user(n).id for n in ("ana", "bea", "carla", "dani", "eva")]
    now_ms = NOW.timestamp() * 1000
    with db.tx() as con:
        con.execute("UPDATE users SET created_at=?", ((NOW - timedelta(days=1)).isoformat(),))
        con.execute("UPDATE users SET created_at=? WHERE id=?", ((NOW - timedelta(days=200)).isoformat(), ids[0]))
        con.execute("UPDATE users SET created_at=?, last_seen=? WHERE id=?", ((NOW - timedelta(days=3)).isoformat(), (NOW - timedelta(days=1)).isoformat(), ids[1]))
        con.execute("UPDATE users SET last_seen=? WHERE id=?", ((NOW - timedelta(days=20)).isoformat(), ids[2]))
        for uid, plan, status in ((ids[0], "monthly", "active"), (ids[1], "yearly", "active"), (ids[2], "monthly", "trialing")):
            con.execute("INSERT INTO stripe_subs(user_id, customer_id, subscription_id, plan, status, period_end_ms, updated_at) "
                        "VALUES(?,?,?,?,?,?,?)", (uid, f"cus_{uid}", f"sub_{uid}", plan, status, now_ms + 9e8, NOW.isoformat()))
        con.execute("INSERT INTO subscriptions(user_id, token_hash, token_enc, product_id, base_plan, state, expiry_ms, created_at) "
                    "VALUES(?,?,?,?,?,?,?,?)", (ids[3], "h", "e", "bodylens", "monthly", "SUBSCRIPTION_STATE_ACTIVE", now_ms + 9e8, NOW.isoformat()))
        con.execute("INSERT INTO grants(user_id, code, until_ms, created_at) VALUES(?,?,?,datetime('now'))", (ids[4], "LANZAMIENTO", None))
        con.execute("INSERT INTO counters(name, value) VALUES('dl:android:2026-11-20', 4), ('dl:android:2026-01-02', 6), ('dl:bridge:2026-11-24', 1)")
    return ids


def test_figures_from_the_servers_own_tables(data):
    from app.business import stats
    o = stats.overview("30d", now=NOW)
    u = o["users"]
    assert u["accounts"] == 5 and u["new"] == 4 and u["active7"] == 1 and u["active30"] == 2   # ana was made 200 days ago
    assert u["chart"]["unit"] == "day" and len(u["chart"]["points"]) == 30
    s = o["subscriptions"]
    assert (s["paid"], s["trial"], s["ended"]) == (3, 1, 0)
    assert s["byChannel"] == {"stripe": 3, "play": 1} and s["byPlan"] == {"monthly": 3, "yearly": 1}
    assert s["free"] == 1 and s["freeLifetime"] == 1 and s["codesUsed"] == [{"code": "LANZAMIENTO", "used": 1}]
    # MRR: monthly 1.50 (web) + yearly 12/12 (web) + monthly 1.50 (Play); the account in trial does not count yet
    assert s["mrr"] == {"total": 400, "stripe": 250, "play": 150}
    d = o["downloads"]
    assert d["android"] == {"period": 4, "total": 10} and d["bridge"] == {"period": 1, "total": 1}
    assert stats.overview("all", now=NOW)["downloads"]["android"]["period"] == 10
    # nothing configured outside: those blocks say so, without failing
    assert o["stripe"]["state"] == "unconfigured" and o["playInstalls"]["state"] == "unconfigured"


def test_periods_and_charts():
    from app.business import stats
    assert stats.period_start("all", NOW) is None and stats.period_start("7d", NOW) == NOW - timedelta(days=7)
    unit, keys = stats.buckets("12m", NOW)
    assert unit == "month" and keys[-1] == "2026-11" and len(keys) == 12
    unit, keys = stats.buckets("all", NOW, NOW - timedelta(days=800))
    assert keys[0] == "2024-09" and keys[-1] == "2026-11"


def test_stripe_revenue_conversion_and_cancellations():
    from app.business import stats
    raw = {
        "charges": [{"amount": 150, "currency": "eur", "paid": True, "status": "succeeded", "created": _ts(2)},
                    {"amount": 1200, "currency": "eur", "paid": True, "status": "succeeded", "created": _ts(40)},
                    {"amount": 150, "currency": "eur", "paid": False, "status": "failed", "created": _ts(1)}],
        "refunds": [{"amount": 150, "status": "succeeded", "created": _ts(1)}],
        "subscriptions": [
            {"status": "active", "trial_end": _ts(5)},                                   # converted
            {"status": "canceled", "trial_end": _ts(6), "canceled_at": _ts(7)},        # left during the trial
            {"status": "canceled", "trial_end": _ts(50), "canceled_at": _ts(3)},       # paid, then left
        ]}
    f = stats.stripe_figures(raw, "30d", NOW)
    assert (f["collected"], f["refunded"], f["net"]) == (150, 150, 0)
    assert f["trialsEnded"] == 2 and f["converted"] == 1 and f["conversion"] == 50 and f["cancelled"] == 2
    assert dict(f["chart"]["points"])["2026-10"] == 1200
    assert stats.stripe_figures(raw, "12m", NOW)["collected"] == 1350


def test_play_reports_are_read():
    from app.business import sources, stats
    earnings = ("Transaction Date,Transaction Type,Product id,Merchant Currency,Amount (Merchant Currency)\n"
                "\"Oct 3, 2026\",Charge,app.bodylens.android,EUR,1.50\n"
                "\"Oct 3, 2026\",Google fee,app.bodylens.android,EUR,-0.23\n"
                "\"Oct 9, 2026\",Charge refund,app.bodylens.android,EUR,-1.50\n"
                "\"Oct 9, 2026\",Charge,app.other,EUR,9.99\n")
    assert sources.parse_earnings(earnings, "app.bodylens.android") == {"charged": 150, "refunded": 150, "net": -23, "currency": "EUR"}
    installs = ("Date,Package Name,Daily Device Installs,Daily User Installs,Total User Installs,Active Device Installs\n"
                "2026-11-20,app.bodylens.android,3,2,40,31\n2026-11-21,app.bodylens.android,5,4,44,33\n").encode("utf-16")
    days = sources.parse_installs(sources._text(installs))
    f = stats.play_installs_figures({"days": days, "latest": "2026-11-21", "total": 44, "active": 33}, "7d", NOW)
    assert f == {"installs": 6, "total": 44, "activeDevices": 33, "latest": "2026-11-21"}
    assert sources.bucket_name("gs://pubsite_prod_123456/") == "pubsite_prod_123456"
    assert sources.bucket_name("https://console.cloud.google.com/storage/browser/pubsite_prod_rev_0123?x=1") == "pubsite_prod_rev_0123"


def test_a_failing_source_only_breaks_its_block(data, monkeypatch):
    from app.business import sources, stats
    monkeypatch.setattr(sources, "stripe_raw", lambda refresh=False: (_ for _ in ()).throw(RuntimeError("Stripe no responde.")))
    o = stats.overview("30d", now=NOW)
    assert o["stripe"] == {"source": "Stripe", "state": "error", "error": "Stripe no responde."}
    assert o["users"]["state"] == "ok"


def test_only_administrators_and_no_secret_in_any_answer(client, make_user, login, monkeypatch):
    from app.billing import stripe
    make_user("jefa", admin=True)
    make_user("pepa")
    assert login("pepa").get("/api/admin/business").status_code == 403
    a = login("jefa")
    monkeypatch.setattr(stripe, "ensure_prices", lambda secret: {"monthly": "price_m", "yearly": "price_y"})
    secrets = {"stripe": "sk_test_SECRETstripe1234", "hook": "whsec_SECREThook5678", "mail": "SECRETmail-pass-9012",
               "withings": "SECRETwithings3456", "claude": "sk-ant-SECRETclaude7890", "key": "SECRETprivatekey"}
    assert a.put("/api/admin/stripe", json={"secret": secrets["stripe"], "webhook": secrets["hook"]}).status_code == 200
    assert a.put("/api/admin/mail", json={"host": "smtp.example.com", "port": 465, "username": "x", "password": secrets["mail"],
                                          "from_address": "x@example.com"}).status_code == 200
    assert a.put("/api/admin/withings", json={"clientId": "cid", "clientSecret": secrets["withings"]}).status_code == 200
    assert a.put("/api/admin/translator", json={"apiKey": secrets["claude"]}).status_code == 200
    sa = json.dumps({"client_email": "sa@x.iam.gserviceaccount.com", "private_key": secrets["key"]})
    assert a.put("/api/admin/play", json={"serviceAccount": sa, "bucket": "gs://pubsite_prod_42"}).status_code == 200
    from app.core import db
    assert secrets["mail"] not in json.dumps(db.get_setting("mail"))        # saved encrypted
    from app.mail import mailer
    assert mailer.settings()["password"] == secrets["mail"]                # and still used to send
    answers = [a.get(p).text for p in ("/api/admin/business?period=all", "/api/admin/stripe", "/api/admin/mail", "/api/admin/withings",
                                       "/api/admin/translator", "/api/admin/play")]
    for text in answers:
        for s in secrets.values():
            assert s not in text
    assert a.get("/api/admin/stripe").json()["secretHint"] == "…1234"
    assert a.get("/api/admin/mail").json()["passwordHint"] == "…9012"
    assert a.get("/api/admin/play").json()["bucket"] == "pubsite_prod_42"
    r = a.post("/api/admin/business/test", json={"what": "reports"}).json()
    assert r["ok"] is False   # the key is not a real one: Google says no, and the message says why


def test_apk_downloads_are_counted(client, env):
    from app.core import config, db
    from app.business import counters
    d = config.settings.data_dir / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    (d / "bodylens-android.apk").write_bytes(b"apk" * 100)
    (d / "bodylens-bridge.apk").write_bytes(b"apk")
    assert client.get("/android.apk").status_code == 200
    assert client.get("/android.apk", headers={"Range": "bytes=0-99"}).status_code == 206
    client.get("/android.apk", headers={"Range": "bytes=100-"})            # a resumed download: not another one
    client.get("/android-bridge.apk")
    with db.ro() as con:
        assert sum(counters.downloads(con, "android").values()) == 2
        assert sum(counters.downloads(con, "bridge").values()) == 1


def test_last_seen_is_noted(client, make_user, login):
    from app.business import counters
    from app.core import db
    counters._seen.clear()
    make_user("pepa")
    login("pepa", c=client).get("/api/me")
    with db.ro() as con:
        assert con.execute("SELECT last_seen FROM users WHERE username='pepa'").fetchone()[0]


def test_installs_by_country_are_added_up():
    from app.business import sources
    csv_text = ("Date,Package Name,Country,Daily User Installs,Total User Installs,Current Device Installs\n"
                "2026-11-20,app.bodylens.android,ES,2,30,20\n2026-11-20,app.bodylens.android,PT,1,5,4\n")
    assert sources.parse_installs(csv_text) == [{"date": "2026-11-20", "installs": 3, "total": 35, "active": 24}]


def test_an_email_password_saved_by_older_versions_is_kept_and_encrypted(client, make_user, login):
    from app.core import db
    from app.mail import mailer
    with db.tx() as con:
        db.set_setting(con, "mail", {"host": "smtp.example.com", "from_address": "x@example.com", "password": "old-plain-password"})
    assert mailer.settings()["password"] == "old-plain-password"
    make_user("jefa", admin=True)
    a = login("jefa")
    assert a.put("/api/admin/mail", json={"host": "smtp.example.com", "from_address": "x@example.com"}).status_code == 200
    assert "old-plain-password" not in str(db.get_setting("mail")) and mailer.settings()["password"] == "old-plain-password"
