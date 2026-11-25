"""What Administration → Business reads from outside, with a cache so the panel does not ask on every visit:
- Stripe: charges, refunds and subscriptions (its API, with the saved secret key);
- Google Play: the published version on each track (Play Developer API) and, from the Cloud Storage bucket of the
  developer account's reports, the monthly earnings reports and the daily installs statistics. Both are read with the
  same service account the server uses for the subscriptions (Administration → Business → Google Play)."""
from __future__ import annotations

import csv
import io
import re
import time
import zipfile
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from app.billing import play, stripe

STORAGE = "https://storage.googleapis.com/storage/v1/b"
STORAGE_SCOPE = "https://www.googleapis.com/auth/devstorage.read_only"
TTL = {"stripe": 600, "tracks": 900, "earnings": 3600, "installs": 3600}
_cache: dict[str, tuple[float, object, str]] = {}


class Unconfigured(Exception):
    pass


def cached(key: str, refresh: bool, fetch):
    """(value, when it was taken) of a fetch, kept TTL seconds (refresh: ask again now)."""
    hit = _cache.get(key)
    if hit and not refresh and time.time() - hit[0] < TTL[key.split(":")[0]]:
        return hit[1], hit[2]
    value = fetch()
    taken = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _cache[key] = (time.time(), value, taken)
    return value, taken


def clear() -> None:
    _cache.clear()


# ---------- Stripe ----------

def _all(path: str, params: dict | None = None, pages: int = 50) -> list[dict]:
    out, after = [], None
    for _ in range(pages):
        p = {"limit": 100, **(params or {}), **({"starting_after": after} if after else {})}
        j = stripe.call("GET", path, p)
        out += j.get("data", [])
        if not j.get("has_more") or not j.get("data"):
            break
        after = j["data"][-1]["id"]
    return out


def stripe_raw(refresh: bool = False):
    if not stripe.settings()["secret"]:
        raise Unconfigured()
    return cached("stripe", refresh, lambda: {
        "charges": _all("/charges"), "refunds": _all("/refunds"),
        "subscriptions": _all("/subscriptions", {"status": "all"})})


def stripe_test() -> str:
    if not stripe.settings()["secret"]:
        raise Unconfigured()
    stripe.call("GET", "/prices", {"limit": 1})
    s = stripe.settings()["secret"]
    return "live" if s.startswith(("sk_live", "rk_live")) else "test"


# ---------- Google Play: tracks ----------

def _play_get(method: str, url: str, scope: str = play.SCOPE, **kw) -> requests.Response:
    if not play.configured():
        raise Unconfigured()
    r = requests.request(method, url, headers={"Authorization": f"Bearer {play._access_token(scope)}"}, timeout=30, **kw)
    if r.status_code == 403:
        raise RuntimeError("Google no da permiso a la cuenta de servicio (403).")
    if r.status_code >= 400:
        raise RuntimeError(f"Google Play: error {r.status_code}.")
    return r


def play_tracks(refresh: bool = False):
    """The release on each track (internal test, closed test, production…): its name and state."""
    def fetch():
        base = f"{play.API}/{play.settings()['package']}/edits"
        edit = _play_get("POST", base).json()["id"]
        try:
            tracks = _play_get("GET", f"{base}/{edit}/tracks").json().get("tracks", [])
        finally:
            try:
                _play_get("DELETE", f"{base}/{edit}")
            except Exception:   # noqa: BLE001 — an unused edit expires by itself
                pass
        out = []
        for t in tracks:
            rel = [r for r in t.get("releases", []) if r.get("status") in ("completed", "inProgress", "halted")] or t.get("releases", [])
            if rel:
                r = rel[0]
                out.append({"track": t.get("track"), "name": r.get("name") or ", ".join(r.get("versionCodes", [])),
                            "status": r.get("status"), "versionCodes": r.get("versionCodes", [])})
        return {"tracks": out}
    return cached("tracks", refresh, fetch)


def play_test() -> str:
    s = play.settings()
    _play_get("GET", f"{play.API}/{s['package']}/subscriptions", params={"pageSize": 1})
    return s["package"]


# ---------- Google Play: reports in Cloud Storage ----------

def bucket_name(value: str) -> str:
    """The bucket of the reports from what is pasted: gs://pubsite_prod_…, its name, or its Google Cloud console URL."""
    v = (value or "").strip()
    m = re.search(r"(pubsite_prod_[A-Za-z0-9_-]+)", v)
    if m:
        return m.group(1)
    v = re.sub(r"^gs://", "", v)
    return v.split("/")[0]


def _bucket() -> str:
    b = bucket_name(play.settings()["bucket"])
    if not b or not play.configured():
        raise Unconfigured()
    return b


def _list(bucket: str, prefix: str) -> list[str]:
    names, token = [], None
    for _ in range(20):
        params = {"prefix": prefix, "fields": "items(name),nextPageToken", **({"pageToken": token} if token else {})}
        j = _play_get("GET", f"{STORAGE}/{bucket}/o", STORAGE_SCOPE, params=params).json()
        names += [i["name"] for i in j.get("items", [])]
        token = j.get("nextPageToken")
        if not token:
            break
    return names


def _download(bucket: str, name: str) -> bytes:
    return _play_get("GET", f"{STORAGE}/{bucket}/o/{quote(name, safe='')}", STORAGE_SCOPE, params={"alt": "media"}).content


def _text(b: bytes) -> str:
    """The reports' CSV are UTF-16 (installs) or UTF-8 (earnings)."""
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16")
    return b.decode("utf-8-sig")


def _num(s) -> float:
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def parse_earnings(csv_text: str, package: str) -> dict:
    """{charged, refunded, net, currency} in cents of one month's earnings report, for one app (the merchant account
    may sell other apps too). Google's fees and taxes are part of the net."""
    charged = refunded = net = 0.0
    currency = None
    for row in csv.DictReader(io.StringIO(csv_text)):
        if (row.get("Product id") or row.get("Product ID") or "").strip() != package:
            continue
        amount = _num(row.get("Amount (Merchant Currency)"))
        currency = currency or (row.get("Merchant Currency") or "").strip() or None
        kind = (row.get("Transaction Type") or "").strip().lower()
        if kind == "charge":
            charged += amount
        elif kind == "charge refund":
            refunded += -amount
        net += amount
    return {"charged": round(charged * 100), "refunded": round(refunded * 100), "net": round(net * 100), "currency": currency}


def play_earnings(refresh: bool = False):
    def fetch():
        bucket, pkg = _bucket(), play.settings()["package"]
        months, currency = {}, None
        for name in sorted(_list(bucket, "earnings/earnings_")):
            m = re.search(r"earnings_(\d{4})(\d{2})[_.]", name)   # earnings_YYYYMM.zip (and any later adjustment file)
            if not m or not name.endswith(".zip"):
                continue
            month = f"{m.group(1)}-{m.group(2)}"
            with zipfile.ZipFile(io.BytesIO(_download(bucket, name))) as z:
                for inner in z.namelist():
                    if inner.lower().endswith(".csv"):
                        f = parse_earnings(_text(z.read(inner)), pkg)
                        cur = months.setdefault(month, {"charged": 0, "refunded": 0, "net": 0})
                        for k in cur:
                            cur[k] += f[k]
                        currency = currency or f["currency"]
        return {"months": months, "latest": max(months) if months else None, "currency": currency}
    return cached("earnings", refresh, fetch)


def parse_installs(csv_text: str) -> list[dict]:
    """One row per day (the rows of a dimension, e.g. one per country, are added up)."""
    days: dict[str, dict] = {}
    for row in csv.DictReader(io.StringIO(csv_text)):
        d = (row.get("Date") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            continue
        pick = lambda *cols: next((row[c] for c in cols if row.get(c) not in (None, "")), 0)   # noqa: E731
        day = days.setdefault(d, {"date": d, "installs": 0, "total": 0, "active": 0})
        day["installs"] += int(_num(pick("Daily User Installs", "Daily Device Installs")))
        day["total"] += int(_num(pick("Total User Installs")))
        day["active"] += int(_num(pick("Current Device Installs", "Active Device Installs")))
    return list(days.values())


def play_installs(refresh: bool = False):
    def fetch():
        bucket, pkg = _bucket(), play.settings()["package"]
        # installs_<package>_YYYYMM_<dimension>.csv: the overview if there is one, else the one by country
        names = _list(bucket, f"stats/installs/installs_{pkg}_")
        months: dict[str, str] = {}
        for dim in ("_country.csv", "_overview.csv"):
            for name in names:
                m = re.search(r"_(\d{6})_[a-z_]+\.csv$", name)
                if m and name.endswith(dim):
                    months[m.group(1)] = name
        days = []
        for month in sorted(months):
            days += parse_installs(_text(_download(bucket, months[month])))
        days.sort(key=lambda d: d["date"])
        last = days[-1] if days else {}
        return {"days": days, "latest": last.get("date"), "total": last.get("total"), "active": last.get("active")}
    return cached("installs", refresh, fetch)


def reports_test() -> int:
    bucket = _bucket()
    return len(_list(bucket, "stats/installs/"))
