"""Which health source rules in an account when it gets data both from Apple Health (Health Auto Export) and from
Android (Health Connect, through the BodyLens app): the main source rules and the other one only fills the gaps, per
kind of data and day (sleep: per night; workouts: the same session, starting less than 10 minutes apart).

Each account chooses "apple", "android" or "auto" (the default): Android rules, unless most of the posts come from
Apple Health. Stored in the setting "health_primary:<user id>" with the posts counted from each source."""
from __future__ import annotations

from app.core import db

MODES = ("auto", "apple", "android")


def _key(user_id: int) -> str:
    return f"health_primary:{user_id}"


def state(user_id: int) -> dict:
    s = db.get_setting(_key(user_id), None)
    s = s if isinstance(s, dict) else {}
    mode = s.get("mode") if s.get("mode") in MODES else "auto"
    apple, android = int(s.get("apple") or 0), int(s.get("android") or 0)
    if mode == "auto":
        rules = "apple" if apple > android else "android"
    else:
        rules = mode
    return {"mode": mode, "rules": rules, "apple": apple, "android": android}


def set_mode(user_id: int, mode: str) -> dict:
    if mode not in MODES:
        raise ValueError(mode)
    s = state(user_id)
    with db.tx() as con:
        db.set_setting(con, _key(user_id), {"mode": mode, "apple": s["apple"], "android": s["android"]})
    return state(user_id)


def count_post(con, user_id: int, android: bool) -> bool:
    """Counts one more post from that source (for the "auto" choice), inside the post's transaction, and says whether
    Android rules in the account."""
    import json
    row = con.execute("SELECT value FROM settings WHERE key=?", (_key(user_id),)).fetchone()
    s = json.loads(row["value"]) if row else {}
    s = s if isinstance(s, dict) else {}
    k = "android" if android else "apple"
    s[k] = int(s.get(k) or 0) + 1
    db.set_setting(con, _key(user_id), s)
    mode = s.get("mode") if s.get("mode") in MODES else "auto"
    if mode == "auto":
        return not int(s.get("apple") or 0) > int(s.get("android") or 0)
    return mode == "android"
