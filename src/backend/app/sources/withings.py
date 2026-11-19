"""Withings directo desde el servidor (port de la parte de Withings de legacy/apps-script/Codigo.gs).

- OAuth por cuenta; el refresh token rota: se guarda siempre el nuevo (cifrado).
- Cada sincronización: pesadas y composición (desde la última menos 7 días), actividad (10 días), entrenos (14 días),
  sueño de las 3 últimas noches (siempre se vuelven a pedir) y la siesta de hoy, SpO2/VO2 (30 días) y ECG (60 días).
- Withings nunca pisa lo que viene de Apple Salud: solo rellena huecos.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from urllib.parse import urlencode

import httpx

from app.core import config, crypto, db
from app.sheets import rules, store
from app.sheets import values as V
from app.sheets.tabs import ACTIVIDAD, ECG, ENTRENOS, SIESTAS, SPO2_VO2, SUENO, WITHINGS

log = logging.getLogger("bodylens.withings")

AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
MEASURE_URL = "https://wbsapi.withings.net/measure"
V2_MEASURE_URL = "https://wbsapi.withings.net/v2/measure"
V2_SLEEP_URL = "https://wbsapi.withings.net/v2/sleep"
HEART_URL = "https://wbsapi.withings.net/v2/heart"
SCOPE = "user.metrics,user.activity"
HISTORY_START = 1199145600  # 1 ene 2008
RAW_TYPES = {1: 2, 6: 3, 8: 4, 76: 5, 77: 6, 88: 7}
ECG_CLASES = {0: "Ritmo sinusal normal", 1: "Fibrilación auricular", 2: "No concluyente"}
WO_TYPES = {1: "Caminar", 2: "Correr", 3: "Senderismo", 4: "Patinaje", 5: "BMX", 6: "Bicicleta", 7: "Natación", 8: "Surf",
            9: "Kitesurf", 10: "Windsurf", 11: "Bodyboard", 12: "Tenis", 13: "Pimpón", 14: "Squash", 15: "Bádminton",
            16: "Pesas", 17: "Calistenia", 18: "Elíptica", 19: "Pilates", 20: "Baloncesto", 21: "Fútbol",
            22: "Fútbol americano", 23: "Rugby", 24: "Voleibol", 25: "Waterpolo", 26: "Hípica", 27: "Golf", 28: "Yoga",
            29: "Baile", 30: "Boxeo", 31: "Esgrima", 32: "Lucha", 33: "Artes marciales", 34: "Esquí", 35: "Snowboard",
            36: "Otro", 187: "Remo", 188: "Zumba", 191: "Béisbol", 192: "Balonmano", 193: "Hockey",
            194: "Hockey sobre hielo", 195: "Escalada", 196: "Patinaje sobre hielo", 272: "Multideporte",
            306: "Caminar en interior", 307: "Correr en interior", 308: "Bicicleta en interior"}


class WithingsError(RuntimeError):
    pass


def _app() -> dict:
    """Aplicación de desarrollador de Withings: lo guardado en Administración manda sobre el .env."""
    s = db.get_setting("withings_app") or {}
    secret = crypto.decrypt(s.get("secret")) if s.get("secret") else None
    return {"id": s.get("id") or os.environ.get("WITHINGS_CLIENT_ID", "").strip(),
            "secret": secret or os.environ.get("WITHINGS_CLIENT_SECRET", "").strip()}


def client_id() -> str:
    return _app()["id"]


def client_secret() -> str:
    return _app()["secret"]


def save_app(con, cid: str, secret: str | None) -> None:
    cur = db.get_setting("withings_app") or {}
    db.set_setting(con, "withings_app", {"id": cid.strip(), "secret": crypto.encrypt(secret.strip()) if secret else cur.get("secret")})


def configured() -> bool:
    return bool(client_id() and client_secret())


def redirect_uri() -> str:
    return os.environ.get("WITHINGS_REDIRECT_URI") or f"{config.settings.public_url}/oauth/withings/callback"


# ---------- tokens (cifrados, por cuenta) ----------

def load_tokens(user_id: int) -> dict | None:
    with db.ro() as con:
        r = con.execute("SELECT data FROM source_tokens WHERE user_id=? AND source='withings'", (user_id,)).fetchone()
    return crypto.decrypt(r["data"]) if r else None


def save_tokens(user_id: int, tok: dict) -> None:
    with db.tx() as con:
        con.execute("INSERT INTO source_tokens(user_id, source, data, updated_at) VALUES(?, 'withings', ?, ?) "
                    "ON CONFLICT(user_id, source) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
                    (user_id, crypto.encrypt(tok), db.now_iso()))


def forget(user_id: int) -> None:
    with db.tx() as con:
        con.execute("DELETE FROM source_tokens WHERE user_id=? AND source='withings'", (user_id,))


def authorize_url(state: str) -> str:
    return AUTH_URL + "?" + urlencode({"response_type": "code", "client_id": client_id(), "scope": SCOPE,
                                       "redirect_uri": redirect_uri(), "state": state})


async def _token_request(client: httpx.AsyncClient, extra: dict) -> dict:
    r = await client.post(TOKEN_URL, data={"action": "requesttoken", "client_id": client_id(),
                                           "client_secret": client_secret(), **extra}, timeout=60)
    j = r.json()
    if j.get("status") != 0:
        raise WithingsError(f"Withings no dio el permiso (estado {j.get('status')}).")
    b = j["body"]
    return {"access_token": b["access_token"], "refresh_token": b["refresh_token"],
            "expires": time.time() + int(b.get("expires_in", 10800)) - 120, "userid": b.get("userid")}


async def exchange_code(client: httpx.AsyncClient, user_id: int, code: str) -> dict:
    tok = await _token_request(client, {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri()})
    tok["connected_at"] = db.now_iso()
    save_tokens(user_id, tok)
    return tok


async def access_token(client: httpx.AsyncClient, user_id: int) -> str:
    tok = load_tokens(user_id)
    if not tok:
        raise WithingsError("Withings no está conectado en esta cuenta.")
    if time.time() > tok.get("expires", 0):
        new = await _token_request(client, {"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]})
        tok.update(new)   # Withings rota el refresh token: se guarda siempre el nuevo
        save_tokens(user_id, tok)
    return tok["access_token"]


class Api:
    def __init__(self, client: httpx.AsyncClient, user_id: int):
        self.client, self.user_id = client, user_id

    async def call(self, url: str, payload: dict) -> dict:
        tok = await access_token(self.client, self.user_id)
        r = await self.client.post(url, data=payload, headers={"Authorization": f"Bearer {tok}"}, timeout=90)
        j = r.json()
        if j.get("status") != 0:
            raise WithingsError(f"Withings devolvió el estado {j.get('status')}.")
        return j.get("body") or {}

    async def pages(self, url: str, base: dict, key: str, max_pages: int = 100) -> list:
        out, offset = [], None
        for _ in range(max_pages):
            p = dict(base)
            if offset is not None:
                p["offset"] = offset
            b = await self.call(url, p)
            out += b.get(key) or []
            if not b.get("more"):
                break
            offset = b.get("offset")
        return out


# ---------- conversiones (filas con las mismas columnas que la hoja) ----------

def _val(m) -> float:
    return m["value"] * (10 ** m["unit"])


def filas_desde_grupos(grupos: list) -> dict:
    out = {}
    for g in grupos:
        fila = [V.from_epoch(g["date"]), g["date"], "", "", "", "", "", "", g.get("grpid"), g.get("attrib")]
        alguna = False
        for m in g.get("measures") or []:
            col = RAW_TYPES.get(m.get("type"))
            if col is None:
                continue
            fila[col] = round(_val(m), 2)
            alguna = True
        if alguna:
            out[V.js_str(g.get("grpid"))] = fila
    return out


def filas_actividad(acts: list) -> dict:
    por_dia = {}
    for a in acts:   # si un día llega de dos fuentes, se queda la de más pasos
        cur = por_dia.get(a.get("date"))
        if (not cur or (a.get("steps") or 0) > (cur.get("steps") or 0)
                or ((a.get("steps") or 0) == (cur.get("steps") or 0) and a.get("hr_average") and not cur.get("hr_average"))):
            por_dia[a.get("date")] = a
    out = {}
    for k, a in por_dia.items():
        out[k] = [V.day_as_date(k), a.get("steps") or 0, round(a.get("distance") or 0), round((a.get("elevation") or 0) * 10) / 10,
                  round((a.get("soft") or 0) / 60), round((a.get("moderate") or 0) / 60), round((a.get("intense") or 0) / 60),
                  round(a.get("calories") or 0), round(a.get("totalcalories") or 0), a.get("hr_average") or "",
                  a.get("hr_min") or "", a.get("hr_max") or "", a.get("model") or ""]
    return out


def filas_entrenamientos(ws: list) -> dict:
    out = {}
    for w in ws:
        d = w.get("data") or {}
        dur = max(0, (w["enddate"] - w["startdate"] - (d.get("pause_duration") or 0)) / 60)
        out[str(w["id"])] = [str(w["id"]), V.day_as_date(w["date"]), V.from_epoch(w["startdate"]), V.from_epoch(w["enddate"]),
                             round(dur), WO_TYPES.get(w.get("category"), f"Tipo {w.get('category')}"),
                             round(d.get("calories") or 0), d.get("steps") or "", round(d.get("distance") or 0) or "",
                             d.get("hr_average") or "", d.get("hr_min") or "", d.get("hr_max") or "", d.get("intensity") or ""]
    return out


def sueno_dia(series: list, k: str) -> dict | None:
    """suenoDia_: el día k son las 24 h que acaban a las 17:00 del día k; la fuente que más sueño registra; episodios
    separados por más de 90 min; el más largo (≥ 1 h) es la noche; los demás (≥ 10 min), siestas."""
    fin = V.to_epoch(datetime.strptime(k + " 17:00", "%Y-%m-%d %H:%M"))
    segs = [s for s in series if s["startdate"] >= fin - 24 * 3600 - 6 * 3600]
    if not segs:
        return None
    por_fuente: dict = {}
    for s in segs:
        por_fuente.setdefault(s.get("model_id") or s.get("model") or "x", []).append(s)
    mejor, mejor_sueno = None, -1
    for lst in por_fuente.values():
        t = sum(s["enddate"] - s["startdate"] for s in lst if s.get("state", 0) > 0)
        if t > mejor_sueno:
            mejor_sueno, mejor = t, lst
    mejor.sort(key=lambda s: s["startdate"])
    dormidos = [s for s in mejor if s.get("state", 0) > 0]
    if not dormidos:
        return None
    eps, ep = [], None
    for s in dormidos:
        if not ep or s["startdate"] - ep["fin"] > 90 * 60:
            ep = {"ini": s["startdate"], "fin": s["enddate"], "sueno": 0}
            eps.append(ep)
        ep["fin"] = max(ep["fin"], s["enddate"])
        ep["sueno"] += s["enddate"] - s["startdate"]
    principal = eps[0]   # el primero de los de más sueño (reduce con «>» del Apps Script)
    for e in eps:
        if e["sueno"] > principal["sueno"]:
            principal = e
    fuente = mejor[0].get("model") or ""

    def fases(e):
        ligero = profundo = rem = otro = 0
        desp = 0
        fc = []
        for s in mejor:
            if not (s["startdate"] >= e["ini"] and s["enddate"] <= e["fin"]):
                continue
            d = s["enddate"] - s["startdate"]
            st = s.get("state", 0)
            if st == 1:
                ligero += d
            elif st == 2:
                profundo += d
            elif st == 3:
                rem += d
            elif st > 3:
                otro += d
            else:
                desp += 1
            if st > 0 and s.get("hr"):
                fc += list(s["hr"].values())
        en_cama = e["fin"] - e["ini"]
        dormido = min(en_cama, ligero + profundo + rem + otro)
        return {"enCama": en_cama, "dormido": dormido, "ligero": ligero + otro, "profundo": profundo, "rem": rem,
                "desp": desp, "fcMedia": round(sum(fc) / len(fc)) if fc else "", "fcMin": min(fc) if fc else ""}

    fila = None
    if principal["sueno"] >= 3600:
        f = fases(principal)
        fila = [V.day_as_date(k), V.from_epoch(principal["ini"]), V.from_epoch(principal["fin"]), round(f["enCama"] / 60),
                round(f["dormido"] / 60), round(f["ligero"] / 60), round(f["profundo"] / 60), round(f["rem"] / 60),
                round((f["enCama"] - f["dormido"]) / 60), f["desp"], round(f["dormido"] / f["enCama"] * 100) if f["enCama"] else "",
                f["fcMedia"], f["fcMin"], fuente]
    siestas = {}
    for e in eps:
        if (fila and e is principal) or e["sueno"] < 10 * 60:
            continue
        f = fases(e)
        dia = V.from_epoch(e["ini"]).strftime("%Y-%m-%d")
        siestas[str(e["ini"])] = [str(e["ini"]), V.day_as_date(dia), V.from_epoch(e["ini"]), V.from_epoch(e["fin"]),
                                  round(f["dormido"] / 60), round(f["profundo"] / 60), round(f["rem"] / 60), f["fcMedia"], fuente]
    return {"fila": fila, "siestas": siestas}


# ---------- descargas ----------

async def _sueno_de(api: Api, k: str) -> dict | None:
    fin = int(V.to_epoch(datetime.strptime(k + " 17:00", "%Y-%m-%d %H:%M")))
    b = await api.call(V2_SLEEP_URL, {"action": "get", "startdate": fin - 24 * 3600, "enddate": fin, "data_fields": "hr"})
    return sueno_dia(b.get("series") or [], k)


async def _salud_corazon(api: Api, desde: int, hasta: int) -> dict:
    grupos = await api.pages(MEASURE_URL, {"action": "getmeas", "meastypes": "54,123", "category": 1, "startdate": desde,
                                           "enddate": hasta}, "measuregrps")
    out = {}
    for g in grupos:
        spo = vo = ""
        for m in g.get("measures") or []:
            x = _val(m)
            if m.get("type") == 54:
                spo = round(x * 10) / 10
            elif m.get("type") == 123:
                vo = round(x * 10) / 10
        if spo != "" or vo != "":
            out[V.js_str(g.get("grpid"))] = [V.from_epoch(g["date"]), g["date"], spo, vo, V.js_str(g.get("grpid"))]
    return out


async def _ecgs(api: Api, con_ya: dict, desde: int, hasta: int) -> dict:
    lista = await api.pages(HEART_URL, {"action": "list", "startdate": desde, "enddate": hasta}, "series")
    out = {}
    for s in lista:
        ecg = s.get("ecg") or {}
        if not ecg.get("signalid"):
            continue
        key = V.js_str(s.get("timestamp"))
        ya = con_ya.get(key)
        if ya and len(V.js_str(ya[6] if len(ya) > 6 else "")) > 100:
            continue  # ya guardado con su señal
        senal, fs = "", ""
        try:
            g = await api.call(HEART_URL, {"action": "get", "signalid": ecg["signalid"]})
            sig = g.get("signal") or []
            fs = g.get("sampling_frequency") or ""
            paso = round(fs / 150) if fs and fs > 200 else 1   # a unos 150 Hz
            if paso > 1:
                sig = sig[::paso]
                fs = round(fs / paso)
            senal = ",".join(str(x) for x in sig)
            if len(senal) > 49000:
                senal = senal[:49000].rsplit(",", 1)[0]
        except (WithingsError, httpx.HTTPError) as e:
            log.info("ECG %s: %s", key, e)
        out[key] = [V.from_epoch(s["timestamp"]), s["timestamp"], s.get("heart_rate") or "",
                    ECG_CLASES.get(ecg.get("afib"), "Desconocido"), str(ecg["signalid"]), fs, senal, s.get("model") or ""]
    return out


def _rellena_control_diario(con, user_id: int, pesadas: dict) -> int:
    """sincronizarPeso: en la pestaña «Control Diario», la primera pesada de cada día en las filas sin peso."""
    rows = con.execute("SELECT position, static_rows FROM sheet_tabs WHERE user_id=? AND tab='Control Diario'",
                       (user_id,)).fetchone()
    if not rows or rows["static_rows"] is None:
        return 0
    import json
    data = [[V.dec(x) for x in r] for r in json.loads(rows["static_rows"])]
    hoy, n = V.today_key(), 0
    for r in data:
        if len(r) < 3 or not isinstance(r[1], datetime):
            continue
        k = r[1].strftime("%Y-%m-%d")
        if k > hoy or not V.empty(r[2]) or k not in pesadas:
            continue
        r[2] = pesadas[k]
        n += 1
    if n:
        store.set_static(con, user_id, "Control Diario", data, rows["position"])
        store.mark_dirty(con, user_id)
    return n


async def sync(user_id: int, client: httpx.AsyncClient | None = None, full: bool = False) -> dict:
    """Una sincronización con Withings. Los errores de una parte no paran las demás."""
    own = client is None
    client = client or httpx.AsyncClient()
    api = Api(client, user_id)
    res: dict = {"errores": []}
    ahora = int(time.time())
    hoy = V.today_key()
    try:
        # pesadas y composición
        try:
            with db.ro() as con:
                ya = store.read_rows(con, user_id, WITHINGS)
            max_ts = max([int(r[1]) for r in ya.values() if isinstance(r[1], (int, float))] or [0])
            desde = HISTORY_START if (full or not max_ts) else max(HISTORY_START, max_ts - 7 * 86400)
            grupos = await api.pages(MEASURE_URL, {"action": "getmeas", "meastypes": ",".join(map(str, RAW_TYPES)),
                                                   "category": 1, "startdate": desde, "enddate": ahora}, "measuregrps", 200)
            nuevas = {k: v for k, v in filas_desde_grupos(grupos).items() if k not in ya}
            primeras: dict = {}
            for f in filas_desde_grupos(grupos).values():
                if f[2] == "":
                    continue
                k = f[0].strftime("%Y-%m-%d")
                if k not in primeras or f[1] < primeras[k][0]:
                    primeras[k] = (f[1], round(f[2] * 10) / 10)
            with db.tx() as con:
                if nuevas:
                    store.save_rows(con, user_id, WITHINGS, nuevas)
                res["controlDiario"] = _rellena_control_diario(con, user_id, {k: v[1] for k, v in primeras.items()})
            res["pesadas"] = len(nuevas)
        except (WithingsError, httpx.HTTPError, ValueError, KeyError) as e:
            res["errores"].append(f"Pesadas: {e}")
        # actividad y entrenos
        try:
            desde_k = "2008-01-01" if full else V.add_days(hoy, -10)
            acts = await api.pages(V2_MEASURE_URL, {"action": "getactivity", "startdateymd": desde_k, "enddateymd": hoy,
                                                    "data_fields": "steps,distance,elevation,soft,moderate,intense,active,"
                                                                   "calories,totalcalories,hr_average,hr_min,hr_max"}, "activities")
            ws = await api.pages(V2_MEASURE_URL, {"action": "getworkouts", "startdateymd": "2008-01-01" if full else V.add_days(hoy, -14),
                                                  "enddateymd": hoy}, "series")
            with db.tx() as con:
                store.save_rows(con, user_id, ACTIVIDAD, filas_actividad(acts), merge=rules.mezcla_withings(12))
                store.save_rows(con, user_id, ENTRENOS, rules.sin_copias_de_salud(con, user_id, filas_entrenamientos(ws)))
            res["actividad"] = len(acts)
        except (WithingsError, httpx.HTTPError, ValueError, KeyError) as e:
            res["errores"].append(f"Actividad: {e}")
        # sueño: las 3 últimas noches siempre (Withings a veces cierra la noche tarde) y la siesta de hoy
        try:
            nuevas, siestas = {}, {}
            for i in range(3):
                k = V.add_days(hoy, -i)
                r = await _sueno_de(api, k)
                if r:
                    if r["fila"]:
                        nuevas[k] = r["fila"]
                    siestas.update(r["siestas"])
            rm = await _sueno_de(api, V.add_days(hoy, 1))
            if rm:
                siestas.update(rm["siestas"])
            with db.tx() as con:
                store.save_rows(con, user_id, SUENO, nuevas, merge=rules.mezcla_withings(13))
                store.save_rows(con, user_id, SIESTAS, rules.siestas_sin_salud(con, user_id, siestas))
            res["noches"] = len(nuevas)
        except (WithingsError, httpx.HTTPError, ValueError, KeyError) as e:
            res["errores"].append(f"Sueño: {e}")
        # corazón
        try:
            spo = await _salud_corazon(api, HISTORY_START if full else ahora - 30 * 86400, ahora)
            with db.ro() as con:
                ya_ecg = store.read_rows(con, user_id, ECG)
            ecgs = await _ecgs(api, ya_ecg, HISTORY_START if full else ahora - 60 * 86400, ahora)
            with db.tx() as con:
                store.save_rows(con, user_id, SPO2_VO2, spo)
                store.save_rows(con, user_id, ECG, ecgs)
        except (WithingsError, httpx.HTTPError, ValueError, KeyError) as e:
            res["errores"].append(f"Corazón: {e}")
    finally:
        if own:
            await client.aclose()
    return res
