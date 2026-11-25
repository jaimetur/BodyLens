"""The figures of Administration → Business, from the server's own tables (accounts, subscriptions, free access,
downloads) and from Stripe and Google Play (business/sources.py). Every block says where its figures come from and
when they were taken; a source that is not configured or fails only affects its own block."""
from __future__ import annotations

import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.billing import codes, play, stripe
from app.business import counters, sources
from app.core import config, db

TZ = ZoneInfo("Europe/Madrid")
PERIODS = {"7d": 7, "30d": 30, "12m": 365, "all": None}
# what one paying account brings each month, in cents (the yearly plan counts ÷ 12)
MONTHLY = {plan: cents if interval == "month" else round(cents / 12) for plan, (interval, cents, _) in stripe.PLANS.items()}
STRIPE_PAID = {"active", "past_due"}


def parse(ts) -> datetime | None:
    """A timestamp of the database (ISO text, or seconds / milliseconds since 1970) as an aware datetime."""
    if ts in (None, ""):
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000 if ts > 1e11 else ts, timezone.utc)
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00").replace(" ", "T"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def period_start(period: str, now: datetime) -> datetime | None:
    days = PERIODS[period]
    return None if days is None else now - timedelta(days=days)


def buckets(period: str, now: datetime, first: datetime | None = None) -> tuple[str, list[str]]:
    """The keys of the chart of a period: days ("YYYY-MM-DD") for 7 and 30 days, months ("YYYY-MM") otherwise."""
    today = now.astimezone(TZ).date()
    days = PERIODS[period]
    if days is not None and days <= 31:
        return "day", [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    start = (today.replace(day=1) - timedelta(days=330)).replace(day=1) if days else \
        (first.astimezone(TZ).date().replace(day=1) if first else today.replace(day=1))
    out, d = [], start
    while d <= today:
        out.append(d.isoformat()[:7])
        d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return "month", out


def key_of(d: datetime, unit: str) -> str:
    k = d.astimezone(TZ).date().isoformat()
    return k if unit == "day" else k[:7]


def series(stamps: list[datetime], period: str, now: datetime, first: datetime | None = None) -> dict:
    unit, keys = buckets(period, now, first)
    c = Counter(key_of(d, unit) for d in stamps)
    return {"unit": unit, "points": [[k, c.get(k, 0)] for k in keys]}


def in_period(d: datetime | None, start: datetime | None, now: datetime) -> bool:
    return d is not None and (start is None or d >= start) and d <= now


# ---------- accounts ----------

def users_block(con, period: str, now: datetime) -> dict:
    start = period_start(period, now)
    rows = con.execute("SELECT created_at, last_seen, partner_id, active, requested_at FROM users").fetchall()
    accounts = [r for r in rows if r["active"] or not r["requested_at"]]   # not the access requests still pending
    made = [d for d in (parse(r["created_at"]) for r in accounts) if d]
    seen = [parse(r["last_seen"]) for r in accounts]
    seen_since = min((parse(r["last_seen"]) for r in rows if r["last_seen"]), default=None)
    return {
        "source": "BodyLens", "updated": now.isoformat(), "state": "ok",
        "accounts": len(accounts), "activeAccounts": sum(1 for r in accounts if r["active"]),
        "couples": sum(1 for r in accounts if r["partner_id"]) // 2,
        "new": sum(1 for d in made if in_period(d, start, now)),
        "active7": sum(1 for d in seen if d and d >= now - timedelta(days=7)),
        "active30": sum(1 for d in seen if d and d >= now - timedelta(days=30)),
        "seenSince": seen_since.isoformat() if seen_since else None,
        "chart": series([d for d in made if in_period(d, start, now)], period, now, min(made, default=None)),
    }


# ---------- subscriptions (as the server knows them) ----------

def subscription_rows(con, now: datetime) -> list[dict]:
    """One row per subscription: channel, plan, and whether it is in trial, paid or over."""
    out = []
    for r in con.execute("SELECT status, plan, cancel_end FROM stripe_subs"):
        st = r["status"]
        state = "trial" if st == "trialing" else "paid" if st in STRIPE_PAID else "ended"
        out.append({"channel": "stripe", "plan": r["plan"], "state": state, "cancelling": bool(r["cancel_end"]) and state != "ended"})
    now_ms = now.timestamp() * 1000
    for r in con.execute("SELECT state, base_plan, expiry_ms FROM subscriptions"):
        on = r["state"] in play.ACTIVE or (r["state"] == "SUBSCRIPTION_STATE_CANCELED" and r["expiry_ms"] > now_ms)
        out.append({"channel": "play", "plan": r["base_plan"], "state": "paid" if on else "ended",
                    "cancelling": r["state"] == "SUBSCRIPTION_STATE_CANCELED" and on})
    return out


def mrr(rows: list[dict]) -> dict:
    """Monthly recurring revenue in cents of the paying subscriptions (not those in trial), with the list prices."""
    by = Counter()
    for r in rows:
        if r["state"] == "paid":
            by[r["channel"]] += MONTHLY.get(r["plan"] or "monthly", 0)
    return {"total": sum(by.values()), "stripe": by["stripe"], "play": by["play"]}


def subscriptions_block(con, now: datetime) -> dict:
    rows = subscription_rows(con, now)
    count = lambda **kv: sum(1 for r in rows if all(r[k] == v for k, v in kv.items()))   # noqa: E731
    now_ms = now.timestamp() * 1000
    grants = con.execute("SELECT code, until_ms FROM grants").fetchall()
    free = [g for g in grants if g["until_ms"] is None or g["until_ms"] > now_ms]
    used = Counter(g["code"] for g in grants if g["code"] and g["code"] != "admin")
    promos = [{"code": p["code"], "left": p["left"], "max": p["max"]} for p in codes.promos()]
    return {
        "source": "BodyLens", "updated": now.isoformat(), "state": "ok",
        "paid": count(state="paid"), "trial": count(state="trial"), "ended": count(state="ended"),
        "cancelling": sum(1 for r in rows if r["cancelling"]),
        "readOnly": con.execute("SELECT COUNT(*) FROM lapses").fetchone()[0],
        "byPlan": {p: sum(1 for r in rows if r["state"] != "ended" and (r["plan"] or "monthly") == p) for p in stripe.PLANS},
        "byChannel": {c: sum(1 for r in rows if r["state"] != "ended" and r["channel"] == c) for c in ("stripe", "play")},
        "free": len(free), "freeLifetime": sum(1 for g in free if g["until_ms"] is None),
        "freeByAdmin": sum(1 for g in free if g["code"] == "admin" or not g["code"]),
        "codesUsed": [{"code": c, "used": n} for c, n in used.most_common()],
        "promos": promos, "mrr": mrr(rows),
        "prices": {p: cents for p, (_, cents, _) in stripe.PLANS.items()}, "trialDays": stripe.TRIAL_DAYS,
    }


# ---------- revenue (Stripe and Google Play) ----------

def stripe_figures(raw: dict, period: str, now: datetime) -> dict:
    """Collected and refunded in the period, revenue per month, trial conversion and cancellations, from Stripe's
    charges, refunds and subscriptions."""
    start = period_start(period, now)
    at = lambda x: datetime.fromtimestamp(x, timezone.utc) if x else None   # noqa: E731
    charges = [c for c in raw["charges"] if c.get("paid") and c.get("status") == "succeeded"]
    refunds = [r for r in raw["refunds"] if r.get("status") in ("succeeded", "pending")]
    collected = sum(c.get("amount", 0) for c in charges if in_period(at(c.get("created")), start, now))
    refunded = sum(r.get("amount", 0) for r in refunds if in_period(at(r.get("created")), start, now))
    unit, keys = buckets("12m" if period != "all" else "all", now,
                         min((at(c.get("created")) for c in charges), default=None))
    month = Counter()
    for c in charges:
        month[key_of(at(c["created"]), "month")] += c.get("amount", 0)
    for r in refunds:
        month[key_of(at(r["created"]), "month")] -= r.get("amount", 0)
    trials = [s for s in raw["subscriptions"] if s.get("trial_end") and in_period(at(s["trial_end"]), start, now)]
    converted = [s for s in trials if s.get("status") in STRIPE_PAID
                 or (s.get("status") == "canceled" and (s.get("canceled_at") or 0) > s["trial_end"])]
    cancelled = [s for s in raw["subscriptions"] if in_period(at(s.get("canceled_at")), start, now)]
    return {
        "currency": (charges[0].get("currency") if charges else "eur").upper(),
        "collected": collected, "refunded": refunded, "net": collected - refunded,
        "trialsEnded": len(trials), "converted": len(converted),
        "conversion": round(100 * len(converted) / len(trials)) if trials else None,
        "cancelled": len(cancelled),
        "chart": {"unit": "month", "points": [[k, month.get(k, 0)] for k in keys]},
    }


def play_earnings_figures(raw: dict, period: str, now: datetime) -> dict:
    """Google Play's earnings reports (one per month, published at the start of the next): net revenue, sales and
    refunds of the months in the period."""
    start = period_start(period, now)
    first = (start.astimezone(TZ).date().isoformat()[:7]) if start else ""
    months = {m: v for m, v in raw["months"].items() if m >= first}
    return {
        "currency": raw.get("currency") or "EUR", "latest": raw.get("latest"),
        "net": sum(v["net"] for v in months.values()), "charged": sum(v["charged"] for v in months.values()),
        "refunded": sum(v["refunded"] for v in months.values()),
        "chart": {"unit": "month", "points": [[m, raw["months"][m]["net"]] for m in sorted(raw["months"])][-24:]},
    }


def play_installs_figures(raw: dict, period: str, now: datetime) -> dict:
    start = period_start(period, now)
    first = start.astimezone(TZ).date().isoformat() if start else ""
    days = [d for d in raw["days"] if d["date"] >= first]
    return {"installs": sum(d["installs"] for d in days), "total": raw.get("total"), "activeDevices": raw.get("active"),
            "latest": raw.get("latest")}


def downloads_block(con, period: str, now: datetime) -> dict:
    start = period_start(period, now)
    first = start.astimezone(TZ).date().isoformat() if start else ""
    out = {"source": "BodyLens", "updated": now.isoformat(), "state": "ok"}
    since = []
    for apk in counters.APKS:
        per_day = counters.downloads(con, apk)
        since += list(per_day)
        out[apk] = {"period": sum(n for d, n in per_day.items() if d >= first), "total": sum(per_day.values())}
    out["since"] = min(since) if since else None
    return out


# ---------- health ----------

def health_block(now: datetime) -> dict:
    from app.core import backup
    from app.mail import mailer
    copies = backup.listing()
    last = copies[0]["created_at"] if copies else None
    try:
        du = shutil.disk_usage(config.settings.data_dir)
        disk = {"free": du.free, "total": du.total}
    except OSError:
        disk = None
    return {"source": "BodyLens", "updated": now.isoformat(), "state": "ok", "lastBackup": last, "backups": len(copies),
            "mail": mailer.settings()["configured"], "disk": disk}


# ---------- all together ----------

def block(source: str, fn) -> dict:
    """A block that depends on an outside service: its figures, or "unconfigured", or the error, never an exception."""
    try:
        data, updated = fn()
        return {"source": source, "state": "ok", "updated": updated, **data}
    except sources.Unconfigured:
        return {"source": source, "state": "unconfigured"}
    except Exception as e:   # noqa: BLE001 — one service failing never breaks the panel
        return {"source": source, "state": "error", "error": str(e)[:300] or e.__class__.__name__}


def overview(period: str, refresh: bool = False, now: datetime | None = None) -> dict:
    if period not in PERIODS:
        period = "30d"
    now = now or datetime.now(timezone.utc)
    with db.ro() as con:
        out = {"period": period, "generatedAt": now.isoformat(), "users": users_block(con, period, now),
               "subscriptions": subscriptions_block(con, now), "downloads": downloads_block(con, period, now)}
    out["health"] = health_block(now)

    def with_raw(fetch, figures):
        def run():
            raw, updated = fetch(refresh)
            return figures(raw, period, now), updated
        return run
    out["stripe"] = block("Stripe", with_raw(sources.stripe_raw, stripe_figures))
    out["playEarnings"] = block("Google Play", with_raw(sources.play_earnings, play_earnings_figures))
    out["playInstalls"] = block("Google Play", with_raw(sources.play_installs, play_installs_figures))
    out["playTracks"] = block("Google Play", lambda: sources.play_tracks(refresh))
    return out
