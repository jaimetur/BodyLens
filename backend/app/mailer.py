"""Correo saliente por SMTP (peticiones de acceso y avisos). Se configura con variables de entorno, como en
DriveTest Analyzer: SMTP_HOST, SMTP_PORT, SMTP_SECURITY (ssl | starttls | none), SMTP_USERNAME, SMTP_PASSWORD,
SMTP_FROM y SMTP_FROM_NAME. La contraseña nunca se guarda en la base ni se muestra."""
from __future__ import annotations

import html
import logging
import os
import smtplib
import ssl
import threading
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

log = logging.getLogger("bodylens.mail")
TIMEOUT = 60
SUBJECT_PREFIX = "BodyLens - "


def settings() -> dict:
    security = (os.environ.get("SMTP_SECURITY") or "ssl").strip().lower()
    if security not in ("ssl", "starttls", "none"):
        security = "ssl"
    default_port = {"ssl": 465, "starttls": 587, "none": 25}[security]
    try:
        port = int(os.environ.get("SMTP_PORT") or default_port)
    except ValueError:
        port = default_port
    s = {
        "host": (os.environ.get("SMTP_HOST") or "").strip(),
        "port": port,
        "security": security,
        "username": (os.environ.get("SMTP_USERNAME") or "").strip(),
        "password": os.environ.get("SMTP_PASSWORD") or "",
        "from_address": (os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USERNAME") or "").strip(),
        "from_name": (os.environ.get("SMTP_FROM_NAME") or "BodyLens").strip(),
    }
    s["configured"] = bool(s["host"] and s["from_address"])
    return s


def public_settings() -> dict:
    s = settings()
    return {k: s[k] for k in ("configured", "host", "port", "security", "from_address")}


def page(title: str, paragraphs: list[str], link: tuple[str, str] | None = None) -> str:
    """HTML sencillo del correo, con los colores de la app. Los párrafos ya vienen escapados."""
    button = ""
    if link:
        button = (f'<p style="margin:22px 0 4px"><a href="{html.escape(link[1], quote=True)}" style="background:#3B7BF2;'
                  f'color:#fff;text-decoration:none;padding:11px 18px;border-radius:10px;font-weight:600;display:inline-block">'
                  f'{html.escape(link[0])}</a></p>')
    body = "".join(f'<p style="margin:0 0 12px">{p}</p>' for p in paragraphs)
    return (f'<!doctype html><html lang="es"><body style="margin:0;background:#eef1f5;padding:24px 12px;'
            f'font:15px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;color:#121a26">'
            f'<div style="max-width:520px;margin:0 auto;background:#fff;border:1px solid #dde3ea;border-radius:16px;padding:22px">'
            f'<div style="font-weight:700;font-size:18px;color:#3B7BF2;margin-bottom:14px">BodyLens</div>'
            f'<h1 style="font-size:19px;margin:0 0 12px">{html.escape(title)}</h1>{body}{button}</div></body></html>')


def _text_of(html_body: str) -> str:
    import re
    t = re.sub(r"<br\s*/?>|</p>|</h1>|</div>", "\n", html_body)
    t = re.sub(r"<a [^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"\2: \1", t)
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def build(s: dict, to: list[str], subject: str, html_body: str, reply_to: str | None = None) -> EmailMessage:
    m = EmailMessage()
    m["Subject"] = SUBJECT_PREFIX + subject
    m["From"] = formataddr((s["from_name"], s["from_address"]))
    m["To"] = ", ".join(to)
    if reply_to:
        m["Reply-To"] = reply_to
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain=s["from_address"].split("@")[-1] or None)
    m.set_content(_text_of(html_body))
    m.add_alternative(html_body, subtype="html")
    return m


def send(to: list[str], subject: str, html_body: str, reply_to: str | None = None) -> None:
    """Envía un correo; lanza RuntimeError con un mensaje en español si falla."""
    s = settings()
    to = [t for t in dict.fromkeys(x.strip() for x in to if x and x.strip())]
    if not s["configured"]:
        raise RuntimeError("El correo no está configurado (SMTP_HOST y SMTP_FROM en el .env).")
    if not to:
        raise RuntimeError("El correo no tiene destinatarios.")
    msg = build(s, to, subject, html_body, reply_to)
    ctx = ssl.create_default_context()
    try:
        server = smtplib.SMTP_SSL(s["host"], s["port"], timeout=TIMEOUT, context=ctx) if s["security"] == "ssl" \
            else smtplib.SMTP(s["host"], s["port"], timeout=TIMEOUT)
        with server:
            server.ehlo()
            if s["security"] == "starttls":
                server.starttls(context=ctx)
                server.ehlo()
            if s["username"]:
                server.login(s["username"], s["password"])
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError("El servidor de correo no acepta el usuario o la contraseña (SMTP_USERNAME / SMTP_PASSWORD).") from e
    except (smtplib.SMTPException, OSError) as e:
        raise RuntimeError(f"No se pudo enviar el correo: {type(e).__name__}.") from e


def send_later(to: list[str], subject: str, html_body: str, reply_to: str | None = None) -> None:
    """Envía en segundo plano (la petición web no espera); los fallos quedan en el log."""
    if not settings()["configured"] or not [t for t in to if t]:
        log.info("correo no enviado (sin configurar o sin destinatarios): %s", subject)
        return

    def run():
        try:
            send(to, subject, html_body, reply_to)
            log.info("correo enviado: %s", subject)
        except RuntimeError as e:
            log.warning("correo no enviado: %s — %s", subject, e)

    threading.Thread(target=run, name="bodylens-mail", daemon=True).start()
