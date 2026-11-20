"""Subscriptions paid on the website through Stripe: sign-up, coming back from the payment, renewing, Stripe's
webhook and the page to manage the card or cancel."""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.accounts import users
from app.accounts.users import User, UserError, clean_email
from app.billing import stripe
from app.core import crypto, db, i18n
from app.core.deps import admin_user, base_url, set_session_cookie, signed_in_user
from app.core.security import password_problem

router = APIRouter()
REFRESH_MS = 2 * 86400 * 1000      # a period over for 2 days without news from the webhook: ask Stripe


def _ms(sec) -> int:
    return int(sec or 0) * 1000


def _save(con, user_id: int, sub: dict) -> None:
    item = ((sub.get("items") or {}).get("data") or [{}])[0]
    price = (item.get("price") or {}).get("id")
    plan = next((p for p, pid in stripe.settings()["prices"].items() if pid == price), None)
    end = sub.get("current_period_end") or item.get("current_period_end")
    con.execute(
        "INSERT INTO stripe_subs(user_id, customer_id, subscription_id, plan, status, period_end_ms, updated_at) "
        "VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET customer_id=excluded.customer_id, "
        "subscription_id=excluded.subscription_id, plan=excluded.plan, status=excluded.status, "
        "period_end_ms=excluded.period_end_ms, updated_at=excluded.updated_at",
        (user_id, sub.get("customer"), sub["id"], plan, sub.get("status", ""), _ms(end), stripe.now_iso()))


def active(user_id: int, row) -> bool:
    """The website subscription lets the account in (asking Stripe if the webhook has been silent too long)."""
    if row["status"] in stripe.ACTIVE and row["period_end_ms"] + REFRESH_MS < time.time() * 1000 and stripe.configured():
        try:
            sub = stripe.call("GET", f"/subscriptions/{row['subscription_id']}")
            with db.tx() as con:
                _save(con, user_id, sub)
            return sub.get("status") in stripe.ACTIVE
        except stripe.StripeError:
            pass
    return row["status"] in stripe.ACTIVE


# ---------- plans and sign-up ----------

@router.get("/api/web/plans")
def plans():
    """The website's subscription plans (the landing page and the sign-up use them)."""
    return {"enabled": stripe.configured(), "trialDays": stripe.TRIAL_DAYS,
            "plans": [{"plan": p, "cents": c, "currency": "EUR", "interval": i} for p, (i, c, _) in stripe.PLANS.items()]}


class SignupIn(BaseModel):
    plan: str
    username: str
    name: str
    email: str
    password: str
    lang: str = ""


@router.post("/api/web/signup")
def signup(body: SignupIn, request: Request):
    """Checks the account's details and returns the address of Stripe's checkout page; the account is made when the
    subscription is confirmed."""
    if not stripe.configured():
        raise HTTPException(503, "Los pagos con tarjeta todavía no están disponibles en este servidor.")
    if body.plan not in stripe.PLANS:
        raise HTTPException(400, "Ese plan no existe.")
    username = body.username.strip().lower()
    try:
        if not users.USERNAME_RE.match(username):
            raise UserError("El usuario tiene que tener de 2 a 32 caracteres: letras minúsculas, números, punto, guion o guion bajo.")
        if not body.name.strip() or len(body.name.strip()) > 80:
            raise UserError("Escribe tu nombre (hasta 80 caracteres).")
        if p := password_problem(body.password):
            raise UserError(p)
        email = clean_email(body.email, required=True)
        with db.ro() as con:
            if users.get_by_username(con, username):
                raise UserError("Ese nombre de usuario ya existe.")
            if users.get_by_login(con, email):
                raise UserError("Ya hay una cuenta con ese correo: entra con ella.")
    except UserError as e:
        raise HTTPException(400, str(e))
    lang = i18n.clean(body.lang) or i18n.request_lang(request, None)
    pid = crypto.new_token(18)
    data = {"username": username, "name": body.name.strip(), "email": email, "pw": crypto.encrypt(body.password),
            "lang": lang, "plan": body.plan}
    with db.tx() as con:
        con.execute("DELETE FROM pending_signups WHERE created_at < datetime('now','-2 days')")
        con.execute("INSERT INTO pending_signups(id, data, created_at) VALUES(?,?,datetime('now'))", (pid, json.dumps(data)))
    try:
        return {"url": stripe.checkout(body.plan, pid, email, base_url(request), lang)}
    except stripe.StripeError as e:
        raise HTTPException(502, str(e))


def _account_for(session: dict) -> User | None:
    """Makes the account of a completed checkout (once), or links the renewal of an existing one."""
    sub = session.get("subscription")
    if isinstance(sub, str):
        sub = stripe.call("GET", f"/subscriptions/{sub}")
    if not sub or session.get("status") != "complete":
        return None
    meta = session.get("metadata") or {}
    with db.tx() as con:
        if meta.get("user"):                                   # renewal of an existing account
            u = users.get_user(con, int(meta["user"]))
            if u:
                _save(con, u.id, sub)
                con.execute("DELETE FROM lapses WHERE user_id=?", (u.id,))
            return u
        done = con.execute("SELECT user_id FROM stripe_subs WHERE subscription_id=?", (sub["id"],)).fetchone()
        if done:
            return users.get_user(con, done["user_id"])
        row = con.execute("SELECT data FROM pending_signups WHERE id=?", (meta.get("pending", ""),)).fetchone()
        if not row:
            return None
        d = json.loads(row["data"])
        u = users.create_user(con, d["username"], d["name"], crypto.decrypt(d["pw"]), email=d["email"])
        if d.get("lang"):
            users.set_lang(con, u.id, d["lang"])
        _save(con, u.id, sub)
        con.execute("DELETE FROM pending_signups WHERE id=?", (meta.get("pending", ""),))
        return u


class CompleteIn(BaseModel):
    session_id: str


@router.post("/api/web/complete")
def complete(body: CompleteIn, response: Response):
    """Back from Stripe's checkout: the account (made now, or by the webhook a moment before) and a session."""
    try:
        session = stripe.call("GET", f"/checkout/sessions/{body.session_id}", {"expand": ["subscription"]})
    except stripe.StripeError as e:
        raise HTTPException(400, str(e))
    try:
        u = _account_for(session)
    except UserError as e:
        raise HTTPException(400, str(e))
    if not u:
        raise HTTPException(400, "El pago todavía no está confirmado. Espera un momento y vuelve a intentarlo.")
    created = (session.get("created") or 0) > time.time() - 3600     # only right after paying
    if created:
        with db.tx() as con:
            set_session_cookie(response, users.create_session(con, u.id))
    return {"ok": True, "signedIn": created, "username": u.username}


class RenewIn(BaseModel):
    plan: str


@router.post("/api/web/renew")
def renew(body: RenewIn, request: Request, u: User = Depends(signed_in_user)):
    """A new subscription for an account whose one is over (no free trial again)."""
    if not stripe.configured():
        raise HTTPException(503, "Los pagos con tarjeta todavía no están disponibles en este servidor.")
    price = stripe.settings()["prices"].get(body.plan)
    if not price:
        raise HTTPException(400, "Ese plan no existe.")
    with db.ro() as con:
        w = con.execute("SELECT customer_id FROM stripe_subs WHERE user_id=?", (u.id,)).fetchone()
    params = {"mode": "subscription", "line_items": [{"price": price, "quantity": 1}], "metadata": {"user": str(u.id)},
              "success_url": f"{base_url(request)}/bienvenida?session_id={{CHECKOUT_SESSION_ID}}",
              "cancel_url": f"{base_url(request)}/alta"}
    if w:
        params["customer"] = w["customer_id"]
    elif u.email:
        params["customer_email"] = u.email
    try:
        return {"url": stripe.call("POST", "/checkout/sessions", params)["url"]}
    except stripe.StripeError as e:
        raise HTTPException(502, str(e))


@router.post("/api/web/portal")
def manage(request: Request, u: User = Depends(signed_in_user)):
    """Stripe's page to change the card, see the invoices or cancel."""
    with db.ro() as con:
        w = con.execute("SELECT customer_id FROM stripe_subs WHERE user_id=?", (u.id,)).fetchone()
    if not w:
        raise HTTPException(404, "No tienes una suscripción de la web.")
    try:
        return {"url": stripe.portal(w["customer_id"], base_url(request))}
    except stripe.StripeError as e:
        raise HTTPException(502, str(e))


@router.post("/api/web/webhook")
async def webhook(request: Request):
    """Stripe tells what happens to each subscription (made, renewed, payment failed, cancelled)."""
    payload = await request.body()
    try:
        ev = stripe.verify_webhook(payload, request.headers.get("stripe-signature", ""))
    except stripe.StripeError as e:
        raise HTTPException(400, str(e))
    obj = (ev.get("data") or {}).get("object") or {}
    kind = ev.get("type", "")
    try:
        if kind == "checkout.session.completed":
            _account_for(obj)
        elif kind.startswith("customer.subscription."):
            with db.tx() as con:
                r = con.execute("SELECT user_id FROM stripe_subs WHERE subscription_id=?", (obj.get("id"),)).fetchone()
                if r:
                    _save(con, r["user_id"], obj)
                    if obj.get("status") in stripe.ACTIVE:
                        con.execute("DELETE FROM lapses WHERE user_id=?", (r["user_id"],))
    except (UserError, stripe.StripeError):
        pass   # answered 200 anyway: Stripe would retry a failure forever
    return {"ok": True}


# ---------- Administration ----------

class StripeIn(BaseModel):
    secret: str = ""     # empty = keep the stored one
    webhook: str = ""
    remove: bool = False


@router.get("/api/admin/stripe")
def get_stripe(request: Request, u: User = Depends(admin_user)):
    s = stripe.settings()
    with db.ro() as con:
        n = con.execute("SELECT COUNT(*) FROM stripe_subs").fetchone()[0]
    return {"configured": stripe.configured(), "webhookSet": bool(s["webhook"]), "prices": s["prices"],
            "live": bool(s["secret"] and s["secret"].startswith("sk_live")), "subscriptions": n,
            "webhookUrl": f"{base_url(request)}/api/web/webhook"}


@router.put("/api/admin/stripe")
def put_stripe(body: StripeIn, request: Request, u: User = Depends(admin_user)):
    stored = db.get_setting("stripe", {}) or {}
    new = dict(stored)
    if body.remove:
        new = {}
    else:
        if body.secret.strip():
            if not body.secret.strip().startswith(("sk_", "rk_")):
                raise HTTPException(400, "Pega la clave secreta de Stripe (empieza por sk_).")
            try:
                new["prices"] = stripe.ensure_prices(body.secret.strip())
            except stripe.StripeError as e:
                raise HTTPException(400, str(e))
            new["secret"] = crypto.encrypt(body.secret.strip())
        if body.webhook.strip():
            if not body.webhook.strip().startswith("whsec_"):
                raise HTTPException(400, "Pega el secreto de firma del webhook (empieza por whsec_).")
            new["webhook"] = crypto.encrypt(body.webhook.strip())
    with db.tx() as con:
        db.set_setting(con, "stripe", new)
    return get_stripe(request, u)
