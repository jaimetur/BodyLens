"""Reglas de mezcla entre fuentes (port de Codigo.gs): Apple Salud manda; Withings solo rellena huecos."""
from __future__ import annotations

from datetime import datetime

from app.sheets import store
from app.sheets import values as V
from app.sheets.tabs import ENTRENOS, ORIGEN_SALUD, SUENO


def es_salud(fila, col: int) -> bool:
    return bool(fila) and len(fila) > col and V.js_str(fila[col]) == ORIGEN_SALUD


def mezcla_withings(col_origen: int):
    """mezclaWithings_: si la fila que hay es de Salud, lo de Withings solo rellena sus huecos."""
    def f(viejo, nuevo, _k=None):
        if viejo and es_salud(viejo, col_origen):
            return [nuevo[i] if V.empty(v) and i < len(nuevo) else v for i, v in enumerate(viejo)]
        return nuevo
    return f


def rellena_huecos(viejo, nuevo, _k=None):
    """rellenaHuecos_: lo nuevo manda, pero sus huecos se quedan con lo que había."""
    if not viejo:
        return nuevo
    return [viejo[i] if V.empty(v) and i < len(viejo) else v for i, v in enumerate(nuevo)]


def lo_nuevo_rellena(viejo, nuevo, _k=None):
    """actividadDesdeSalud_: lo de Salud manda; los campos que Salud no tiene se quedan con lo de Withings."""
    if not viejo:
        return nuevo
    return [viejo[i] if V.empty(v) and i < len(viejo) else v for i, v in enumerate(nuevo)]


def siestas_sin_salud(con, user_id: int, siestas: dict) -> dict:
    """siestasSinSalud_: fuera las siestas de Withings de los días cuya noche ya viene de Salud."""
    salud = {V.day_key(r[0]) for r in store.read_rows(con, user_id, SUENO).values()
             if es_salud(r, 13) and isinstance(r[0], datetime)}
    if not salud:
        return siestas
    out = {}
    for k, r in siestas.items():
        dia = V.day_key(r[1])
        if dia not in salud and V.add_days(dia, 1) not in salud:
            out[k] = r
    return out


def sin_copias_de_salud(con, user_id: int, filas: dict) -> dict:
    """sinCopiasDeSalud_: fuera los entrenos de Withings que ya están desde Salud (empiezan a menos de 10 min)."""
    hk = [r[2] for r in store.read_rows(con, user_id, ENTRENOS).values()
          if V.js_str(r[0]).startswith("hk-") and isinstance(r[2], datetime)]
    if not hk:
        return filas
    out = {}
    for k, r in filas.items():
        ini = r[2] if isinstance(r[2], datetime) else None
        if not ini or not any(abs((t - ini).total_seconds()) < 600 for t in hk):
            out[k] = r
    return out
