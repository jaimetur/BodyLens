"""Leer la hoja de Google exportada (XLSX) a las tablas, y generar desde las tablas el libro XLSX que lee la página,
con las mismas pestañas, cabeceras y valores (las fechas como fechas de Excel)."""
from __future__ import annotations

import io
from datetime import datetime

from openpyxl import Workbook, load_workbook

from app.sheets import store
from app.sheets import values as V
from app.sheets.tabs import DYNAMIC

DATE_FMT = "yyyy-mm-dd hh:mm"


def _clean(v):
    if isinstance(v, datetime):
        return v.replace(microsecond=0)
    if isinstance(v, str) and v == "":
        return ""
    return v


def import_xlsx(con, user_id: int, content: bytes) -> dict:
    """Pasa la hoja entera a las tablas de la cuenta: las pestañas que escribe el servidor fila a fila (por su clave) y
    las demás tal cual. Devuelve {pestaña: filas}."""
    wb = load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    out = {}
    con.execute("DELETE FROM sheet_tabs WHERE user_id=?", (user_id,))
    for pos, ws in enumerate(wb.worksheets):
        rows = [[_clean(c) for c in r] for r in ws.iter_rows(values_only=True)]
        # sin las filas vacías del principio y del final (la exportación de Google empieza en la primera con datos)
        while rows and all(V.empty(c) for c in rows[-1]):
            rows.pop()
        while rows and all(V.empty(c) for c in rows[0]):
            rows.pop(0)
        tab = DYNAMIC.get(ws.title)
        if tab:
            store.set_position(con, user_id, tab.name, pos)
            data = [[("" if c is None else c) for c in r[:len(tab.headers)]] for r in rows[1:]]
            data = [r for r in data if not all(V.empty(c) for c in r)]
            out[tab.name] = store.replace_tab(con, user_id, tab, data)
        else:
            store.set_static(con, user_id, ws.title, [[("" if c is None else c) for c in r] for r in rows], pos)
            out[ws.title] = len(rows)
    store.mark_dirty(con, user_id)
    return out


def build_xlsx(con, user_id: int) -> bytes:
    wb = Workbook(write_only=True)
    for name, static in store.layout(con, user_id):
        ws = wb.create_sheet(title=name[:31])
        if static is not None:
            for r in static:
                ws.append([None if V.empty(c) else c for c in r] or [None])
            continue
        tab = DYNAMIC[name]
        ws.append(list(tab.headers))
        for r in store.sorted_rows(con, user_id, tab):
            ws.append([None if V.empty(c) else c for c in r])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()
