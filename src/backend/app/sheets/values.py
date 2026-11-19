"""Valores de celda como los de la hoja de Google: fechas (en hora de Madrid, sin zona), números, textos y vacíos.

En la base se guardan como JSON; las fechas como {"d": "AAAA-MM-DDTHH:MM:SS"}."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Madrid")


def enc(v):
    if isinstance(v, datetime):
        return {"d": v.replace(tzinfo=None, microsecond=0).isoformat()}
    if isinstance(v, date):
        return {"d": datetime(v.year, v.month, v.day).isoformat()}
    return v


def dec(v):
    if isinstance(v, dict) and "d" in v:
        return datetime.fromisoformat(v["d"])
    return v


def empty(v) -> bool:
    """vacio_ del Apps Script: '' o nada."""
    return v is None or v == ""


def js_str(v) -> str:
    """String(v) de JavaScript para las claves (12.0 → «12»)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def day_key(v) -> str:
    """Clave de leerFilas_: una fecha da «AAAA-MM-DD»; lo demás, su texto."""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    return js_str(v)


def sort_value(v):
    """val() de guardarFilas_: fechas por instante; lo demás como texto."""
    if isinstance(v, datetime):
        return (0, v.timestamp(), "")
    return (1, 0.0, js_str(v))


# ---------- fechas en la zona de la hoja (Europe/Madrid) ----------

def from_epoch(ts: float) -> datetime:
    """Segundos Unix → fecha y hora de Madrid sin zona (como la muestra la hoja)."""
    return datetime.fromtimestamp(float(ts), TZ).replace(tzinfo=None)


def to_epoch(d: datetime) -> float:
    return d.replace(tzinfo=TZ).timestamp()


def day_as_date(k: str) -> datetime:
    """fechaComoDia_: el día a las 12:00 de Madrid."""
    return datetime.strptime(k + " 12:00", "%Y-%m-%d %H:%M")


def add_days(k: str, n: int) -> str:
    return (datetime.strptime(k, "%Y-%m-%d") + timedelta(days=n)).strftime("%Y-%m-%d")


def today_key() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def local(d: datetime) -> datetime:
    """Cualquier fecha con zona → hora de Madrid sin zona."""
    if d.tzinfo is None:
        return d
    return d.astimezone(TZ).replace(tzinfo=None)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
