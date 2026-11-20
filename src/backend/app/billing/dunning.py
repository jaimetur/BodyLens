"""Accounts that stop paying: three warnings by email, a week apart, and then the account and its data are deleted.

Every few hours the server looks at each paid account (Google Play or the website). When its subscription is over it
counts as lapsed: the first warning goes at once, the second a week later and the third a week after that; if seven
days after the third warning the subscription has not been renewed, the account is deleted with all its data (the
partner keeps their own copy of what was shared). Renewing at any moment clears the warnings."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.accounts import deletion, users
from app.billing import routes as billing
from app.core import config, db
from app.mail import mailer

log = logging.getLogger("bodylens")
WARNINGS = 3
GAP = timedelta(days=7)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _when(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def _warn(u, n: int, delete_on: datetime) -> None:
    base = config.settings.public_url or ""
    mailer.send_later([u.email], f"Tu suscripción de BodyLens ha terminado ({n} de {WARNINGS})", mailer.page(
        "Renueva tu suscripción", [
            f"Hola, {u.name}. Tu suscripción de BodyLens ha terminado y no se ha renovado.",
            f"Si no la renuevas, tu cuenta y todos tus datos se borrarán del servidor el {_when(delete_on)}.",
            "Antes, si quieres, puedes descargar una copia de tus datos en Tu cuenta → Datos y copias.",
        ], link=("Renovar la suscripción", f"{base}/alta")))


def run_once(now: datetime | None = None) -> dict:
    now = now or _now()
    out = {"warned": 0, "deleted": 0, "renewed": 0}
    with db.ro() as con:
        ids = [r[0] for r in con.execute("SELECT user_id FROM subscriptions UNION SELECT user_id FROM stripe_subs UNION SELECT user_id FROM grants")]
    for uid in ids:
        try:
            lapsed = billing.expired(uid)
            gone = False
        except Exception:   # noqa: BLE001 — a provider down must not delete anybody
            log.exception("Could not check the subscription of account %s", uid)
            continue
        with db.tx() as con:
            row = con.execute("SELECT * FROM lapses WHERE user_id=?", (uid,)).fetchone()
            u = users.get_user(con, uid)
            if u is None:
                continue
            if not lapsed:
                if row:
                    con.execute("DELETE FROM lapses WHERE user_id=?", (uid,))
                    out["renewed"] += 1
                continue
            if row is None:
                con.execute("INSERT INTO lapses(user_id, lapsed_at, warnings) VALUES(?,?,0)", (uid, now.isoformat()))
                row = {"warnings": 0, "last_warning_at": None}
            last = datetime.fromisoformat(row["last_warning_at"]) if row["last_warning_at"] else None
            if row["warnings"] < WARNINGS and (last is None or now - last >= GAP):
                n = row["warnings"] + 1
                con.execute("UPDATE lapses SET warnings=?, last_warning_at=? WHERE user_id=?", (n, now.isoformat(), uid))
                _warn(u, n, now + GAP * (WARNINGS - n + 1))
                out["warned"] += 1
            elif row["warnings"] >= WARNINGS and last is not None and now - last >= GAP:
                try:
                    deletion.delete_account(con, u)
                except users.UserError:
                    continue   # the last administrator is never deleted
                mailer.send_later([u.email], "Tu cuenta de BodyLens se ha borrado", mailer.page(
                    "Cuenta borrada", [f"Hola, {u.name}. Como tu suscripción no se ha renovado tras tres avisos, tu cuenta "
                                       "y todos tus datos se han borrado del servidor."]))
                out["deleted"] += 1
                gone = True
                log.warning("Deleted account %s: subscription not renewed after %s warnings", uid, WARNINGS)
        if gone:
            deletion.delete_files(uid)
    return out


async def loop() -> None:
    while True:
        try:
            r = await asyncio.to_thread(run_once)
            if any(r.values()):
                log.info("Subscriptions: %s", r)
        except Exception:   # noqa: BLE001
            log.exception("Subscription check failed")
        await asyncio.sleep(6 * 3600)
