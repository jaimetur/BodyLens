"""Small counters kept in the database: APK downloads per day and when each account was last seen."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core import db

TZ = ZoneInfo("Europe/Madrid")
APKS = ("android", "bridge")          # /android.apk (BodyLens) and /android-bridge.apk (BodyLens Bridge)
SEEN_EVERY = 600                      # seconds between two writes of the same account's last visit
_seen: dict[int, float] = {}


def count_download(apk: str, range_header: str | None = None) -> None:
    """One download of an APK, in the counter of its day (Europe/Madrid). A download manager that resumes a file asks
    for the rest of it with a Range header: only the request for its beginning counts."""
    if range_header and not range_header.replace(" ", "").startswith("bytes=0-"):
        return
    day = datetime.now(TZ).date().isoformat()
    with db.tx() as con:
        con.execute("INSERT INTO counters(name, value) VALUES(?, 1) ON CONFLICT(name) DO UPDATE SET value=value+1",
                    (f"dl:{apk}:{day}",))


def downloads(con, apk: str) -> dict[str, int]:
    """{day: downloads} of an APK."""
    rows = con.execute("SELECT name, value FROM counters WHERE name LIKE ?", (f"dl:{apk}:%",)).fetchall()
    return {r["name"].rsplit(":", 1)[1]: r["value"] for r in rows}


def seen(user_id: int) -> None:
    """Notes that the account is using the service (at most once every SEEN_EVERY seconds)."""
    now = time.time()
    if now - _seen.get(user_id, 0) < SEEN_EVERY:
        return
    _seen[user_id] = now
    try:
        with db.tx() as con:
            con.execute("UPDATE users SET last_seen=? WHERE id=?",
                        (datetime.now(timezone.utc).isoformat(timespec="seconds"), user_id))
    except Exception:   # noqa: BLE001 — never let a statistic break a request
        pass
