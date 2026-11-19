"""Apple Salud vía Health Auto Export (automatización «API REST», JSON versión 2): port de doPost y de las reglas de
sueño, actividad y entrenos del Apps Script original (Codigo.gs). También sirve para Android (Health Connect) si la app
manda el mismo JSON.

Salud es la fuente principal: sueño, siestas, actividad diaria y entrenos; Withings solo rellena huecos."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone

from app.sheets import rules, store
from app.sheets import values as V
from app.sheets.tabs import ACTIVIDAD, AVISOS, ECG, ENTRENOS, FASES, ORIGEN_SALUD, REGISTROS, SALUD, SIESTAS, SUENO

LOG_RE = re.compile(r"sexual|menstrua|intermenstrual|ovulation|cervical|contracept|pregnan|lactation|basal_body|mindful|"
                    r"alcohol|headache|fatigue|pain|bloating|cramps|nausea|sweats|appetite|mood|symptom|toothbrush|handwashing")
HK_MAP = [(re.compile(r"^resting_heart_rate$"), "rhr"), (re.compile(r"^heart_rate_variability"), "hrv"),
          (re.compile(r"oxygen_saturation|^spo2"), "spo2"), (re.compile(r"^respiratory_rate$"), "rr"),
          (re.compile(r"^vo2_?max$"), "vo2"), (re.compile(r"wrist_temperature"), "temp"),
          (re.compile(r"breathing_disturbances"), "bdist"), (re.compile(r"time_in_daylight"), "day"),
          (re.compile(r"stand_hour"), "stand"), (re.compile(r"^flights_climbed$"), "flights"),
          (re.compile(r"walking_heart_rate"), "whr"), (re.compile(r"^walking_speed$"), "wspeed"),
          (re.compile(r"walking_steadiness"), "steady"), (re.compile(r"cardio_recovery|heart_rate_recovery"), "hrr")]
HK_HORARIAS = re.compile(r"^(step_count|walking_running_distance|active_energy|basal_energy_burned|apple_exercise_time|"
                         r"heart_rate|flights_climbed)$")
ECG_ES = {"sinus rhythm": "Ritmo sinusal", "atrial fibrillation": "Fibrilación auricular", "high heart rate": "Frec. cardiaca alta",
          "low heart rate": "Frec. cardiaca baja", "inconclusive": "No concluyente", "poor recording": "Registro deficiente",
          "unrecognized": "No reconocido"}
HK_WO_ES = {"walking": "Caminar", "outdoor walk": "Caminar", "indoor walk": "Caminar en interior", "running": "Correr",
            "outdoor run": "Correr", "indoor run": "Correr en interior", "cycling": "Bicicleta", "outdoor cycle": "Bicicleta",
            "indoor cycle": "Bicicleta en interior", "hiking": "Senderismo", "swimming": "Natación", "pool swim": "Natación",
            "open water swim": "Natación", "yoga": "Yoga", "pilates": "Pilates", "elliptical": "Elíptica", "rowing": "Remo",
            "traditional strength training": "Pesas", "functional strength training": "Fuerza funcional",
            "high intensity interval training": "HIIT", "core training": "Core", "dance": "Baile",
            "stair stepper": "Escaleras", "soccer": "Fútbol", "tennis": "Tenis", "padel": "Pádel", "paddle sports": "Pádel",
            "cooldown": "Enfriamiento", "mixed cardio": "Cardio", "other": "Otro"}
DORMIDO = ("core", "deep", "rem", "asleep")
MIN = 60000  # ms


# ---------- utilidades con la semántica de JavaScript ----------

def jr(x) -> int:
    """Math.round de JavaScript (los .5 hacia arriba)."""
    return math.floor(x + 0.5)


def r1(x):
    return "" if x is None else jr(x * 10) / 10


def r2(x):
    return jr(x * 100) / 100


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def nn(v) -> bool:
    """v != null de JavaScript."""
    return v is not None


def js_json(v) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def cell(v):
    return js_json(v) if isinstance(v, (dict, list)) else v


_HAE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?\s*([+-]\d{2}):?(\d{2})?")


def fecha(s):
    """fechaHAE_: «2026-11-18 23:15:00 +0100» → (hora de Madrid sin zona, milisegundos Unix)."""
    if not s:
        return None
    m = _HAE_RE.match(str(s))
    try:
        if m:
            off = int(m.group(7)) * 60 + (1 if m.group(7)[0] != "-" else -1) * int(m.group(8) or 0)
            aware = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)),
                             int(m.group(6) or 0), tzinfo=timezone(timedelta(minutes=off)))
        else:
            aware = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            if aware.tzinfo is None:
                aware = aware.replace(tzinfo=V.TZ)
    except ValueError:
        return None
    return Fecha(V.local(aware), int(round(aware.timestamp() * 1000)))


class Fecha:
    __slots__ = ("local", "ms")

    def __init__(self, local, ms):
        self.local, self.ms = local, ms


def ms_of(d) -> int | None:
    return int(round(V.to_epoch(d) * 1000)) if isinstance(d, datetime) else None


def dia_de(ms: int) -> str:
    return V.from_epoch(ms / 1000).strftime("%Y-%m-%d")


def hora_de(ms: int) -> int:
    return V.from_epoch(ms / 1000).hour


def ms_at(k: str, hhmm: str) -> int:
    return int(V.to_epoch(datetime.strptime(f"{k} {hhmm}", "%Y-%m-%d %H:%M")) * 1000)


def dia_de_noche(fin_ms: int) -> str:
    """La noche del día k acaba entre las 17:00 del día anterior y las 17:00 del día k."""
    k = dia_de(fin_ms)
    return V.add_days(k, 1) if hora_de(fin_ms) >= 17 else k


def a_kcal(v, u):
    return v / 4.184 if re.search(r"kj", u or "", re.I) else v


def a_metros(v, u):
    u = str(u or "").lower()
    return v * 1000 if u == "km" else v * 1609.34 if u == "mi" else v * 0.3048 if u == "ft" else v


# ---------- doPost ----------

def ingest(con, user_id: int, body) -> dict:
    """Procesa un envío de Health Auto Export y guarda en las pestañas. Devuelve el resumen (como doPost)."""
    d = body.get("data", body) if isinstance(body, dict) else {}
    if not isinstance(d, dict):
        d = {}
    filas, ecgs, avisos, registros = {}, {}, {}, {}
    sueno_mts, dias_act = [], {}
    # otras listas (síntomas, ciclo, estado de ánimo, medicamentos…): un registro por elemento
    for lista, items in d.items():
        if lista in ("metrics", "workouts", "ecg", "heartRateNotifications") or not isinstance(items, list):
            continue
        for x in items:
            if not isinstance(x, dict):
                continue
            ini = fecha(x.get("start") or x.get("date") or x.get("startDate"))
            if not ini:
                continue
            tipo = (lista + (":" + str(x["name"]) if x.get("name") else "")).lower()
            animo = bool(re.search(r"mind|mood", lista, re.I))
            if animo:
                val = {"v": x["valence"] if nn(x.get("valence")) else x.get("value"), "c": x.get("valenceClassification") or "",
                       "k": x.get("kind") or "", "l": x.get("labels") or [], "a": x.get("associations") or []}
            else:
                val = next((x[c] for c in ("severity", "value", "qty", "valence") if nn(x.get(c))), 1)
            k = f"{tipo}|{ini.ms}"
            fin = fecha(x.get("end") or x.get("endDate")) or ini
            registros[k] = [ini.local, fin.local, tipo, cell(val), k]
    for mt in d.get("metrics") or []:
        nombre = str(mt.get("name") or "").lower()
        clave = next((c for rx, c in HK_MAP if rx.search(nombre)), nombre)
        if nombre == "sleep_analysis":
            sueno_mts.append(mt)
            continue
        es_log, horaria = bool(LOG_RE.search(nombre)), bool(HK_HORARIAS.search(nombre))
        usada = clave != nombre or horaria
        unidad = mt.get("units") or ""
        if horaria:
            for x in mt.get("data") or []:
                f = fecha(x.get("date") or x.get("startDate"))
                if f:
                    dias_act[f.local.strftime("%Y-%m-%d")] = True
        diario: dict = {}
        for x in mt.get("data") or []:
            f = fecha(x.get("date") or x.get("startDate"))
            if not f:
                continue
            if es_log:   # actividad sexual, ciclo, síntomas…: uno por momento
                val = next((x[c] for c in ("qty", "value", "Avg") if nn(x.get(c))), 1)
                k = f"{nombre}|{f.ms}"
                fin = fecha(x.get("endDate") or x.get("end")) or f
                registros[k] = [f.local, fin.local, nombre, cell(val), k]
                continue
            val = next((x[c] for c in ("qty", "Avg", "avg") if nn(x.get(c))), None)
            mn = x["Min"] if nn(x.get("Min")) else (x["min"] if nn(x.get("min")) else "")
            mx = x["Max"] if nn(x.get("Max")) else (x["max"] if nn(x.get("max")) else "")
            if val is None and mn == "":
                continue
            if usada:
                k = f"{clave}|{f.ms}"
                filas[k] = [f.local, clave, "" if val is None else val, mn, mx, unidad, x.get("source") or "", k]
                continue
            # el resto se guarda resumido por día
            dia = f.local.strftime("%Y-%m-%d")
            a = diario.setdefault(dia, {"n": 0, "s": 0.0, "mn": math.inf, "mx": -math.inf})
            vv = num(mn) if val is None else num(val)
            a["n"] += 1
            a["s"] += vv
            a["mn"] = min(a["mn"], vv if mn == "" else num(mn))
            a["mx"] = max(a["mx"], vv if mx == "" else num(mx))
        for dia, a in diario.items():
            suma = bool(re.search(r"count|step|energy|distance|flights|time|minutes|stand|calories|kcal", nombre)
                        or re.fullmatch(r"count|kcal|km|m|min|kJ", unidad))
            k = f"{nombre}|{dia}"
            filas[k] = [V.day_as_date(dia), nombre, r2(a["s"]) if suma else r2(a["s"] / a["n"]), a["mn"], a["mx"],
                        unidad, "día", k]
    for g in d.get("ecg") or []:
        f = fecha(g.get("start") or g.get("date"))
        if not f:
            continue
        fs0 = num(g.get("samplingFrequency")) or 512
        if math.isnan(fs0):
            fs0 = 512
        sig = [x if isinstance(x, (int, float)) else (x or {}).get("voltage") for x in (g.get("voltageMeasurements") or [])]
        sig = [x for x in sig if isinstance(x, (int, float))]
        if sig and max(abs(x) for x in sig[:2000]) < 0.1:
            sig = [x * 1e6 for x in sig]   # voltios → µV
        paso = max(1, jr(fs0 / 128))
        out = [jr(sum(sig[i:i + paso]) / paso) for i in range(0, len(sig) - paso + 1, paso)]
        cls = str(g.get("classification") or "")
        sec = f.ms // 1000
        ecgs[str(sec)] = [f.local, sec, g.get("averageHeartRate") or "", ECG_ES.get(cls.lower(), cls), "hae",
                          jr(fs0 / paso), ",".join(str(x) for x in out)[:49000], g.get("source") or ""]
    for n in d.get("heartRateNotifications") or []:
        ini = fecha(n.get("start") or n.get("date"))
        if not ini:
            continue
        fin = fecha(n.get("end")) or ini
        txt = js_json(n).lower()
        tipo = "irreg" if "irregular" in txt else "lowhr" if re.search(r"low|baja", txt) else "highhr" if re.search(r"high|alta", txt) else ""
        if not tipo:
            hr = [h.get("hr") or h.get("qty") or h.get("Avg") for h in (n.get("heartRate") or [])]
            hr = [num(x) for x in hr if x]
            tipo = "lowhr" if hr and sum(hr) / len(hr) < 60 else "highhr"
        k = f"{tipo}|{ini.ms}"
        avisos[k] = [ini.local, fin.local, tipo, f"umbral {n['threshold']}" if nn(n.get("threshold")) else "", k]
    if filas:
        store.save_rows(con, user_id, SALUD, filas)
    if ecgs:
        store.save_rows(con, user_id, ECG, ecgs)
    if avisos:
        store.save_rows(con, user_id, AVISOS, avisos)
    if registros:
        store.save_rows(con, user_id, REGISTROS, registros)
    res = {"ok": True, "metricas": len(filas), "ecg": len(ecgs), "avisos": len(avisos), "registros": len(registros)}
    # Salud como fuente principal: actividad del día, noches y siestas, entrenamientos
    try:
        res["actividad"] = actividad_desde_salud(con, user_id, list(dias_act))
    except Exception as e:  # noqa: BLE001 — como el Apps Script: una parte que falla no impide las demás
        res["errorActividad"] = str(e)
    try:
        for mt in sueno_mts:
            r = sueno_desde_salud(con, user_id, mt)
            res["noches"] = res.get("noches", 0) + r["noches"]
            res["siestas"] = res.get("siestas", 0) + r["siestas"]
    except Exception as e:  # noqa: BLE001
        res["errorSueno"] = str(e)
    try:
        if d.get("workouts"):
            res["entrenos"] = entrenos_desde_salud(con, user_id, d["workouts"])
    except Exception as e:  # noqa: BLE001
        res["errorEntrenos"] = str(e)
    return res


# ---------- actividad del día a partir de las horas de «Salud» ----------

def actividad_desde_salud(con, user_id: int, dias: list) -> int:
    if not dias:
        return 0
    quiero = set(dias)
    A: dict = {}
    for r in store.sorted_rows(con, user_id, SALUD):
        if not isinstance(r[0], datetime) or r[6] == "día":
            continue
        k = r[0].strftime("%Y-%m-%d")
        if k not in quiero or V.empty(r[2]):
            continue
        m, v, u = V.js_str(r[1]), num(r[2]), V.js_str(r[5])
        if math.isnan(v):
            continue
        a = A.setdefault(k, {"pasos": 0, "dist": 0, "pisos": 0, "ejer": 0, "act": 0, "bas": 0, "fc": [], "fcMin": [],
                             "fcMax": [], "hay": False})
        if m == "step_count":
            a["pasos"] += v; a["hay"] = True
        elif m == "walking_running_distance":
            a["dist"] += a_metros(v, u)
        elif m in ("flights", "flights_climbed"):
            a["pisos"] += v
        elif m == "apple_exercise_time":
            a["ejer"] += v
        elif m == "active_energy":
            a["act"] += a_kcal(v, u); a["hay"] = True
        elif m == "basal_energy_burned":
            a["bas"] += a_kcal(v, u)
        elif m == "heart_rate":
            a["fc"].append(v)
            if not V.empty(r[3]):
                a["fcMin"].append(num(r[3]))
            if not V.empty(r[4]):
                a["fcMax"].append(num(r[4]))
    filas = {}
    for k, a in A.items():
        if not a["hay"]:
            continue
        media = jr(sum(a["fc"]) / len(a["fc"])) if a["fc"] else ""
        filas[k] = [V.day_as_date(k), jr(a["pasos"]), jr(a["dist"]), jr(a["pisos"] * 3) if a["pisos"] else "", "",
                    jr(a["ejer"]) or "", "", jr(a["act"]), jr(a["act"] + a["bas"]) if a["bas"] else "", media,
                    min(a["fcMin"]) if a["fcMin"] else "", max(a["fcMax"]) if a["fcMax"] else "", ORIGEN_SALUD]
    return store.save_rows(con, user_id, ACTIVIDAD, filas, merge=rules.lo_nuevo_rellena) if filas else 0


# ---------- sueño ----------

def sueno_desde_salud(con, user_id: int, mt: dict) -> dict:
    datos = mt.get("data") or []
    if not datos:
        return {"noches": 0, "siestas": 0}
    tramos, resumen = {}, []
    for x in datos:
        fase = str(x.get("value") or x.get("stage") or "").lower()
        ini, fin = fecha(x.get("startDate") or x.get("start")), fecha(x.get("endDate") or x.get("end"))
        if fase and ini and fin:   # sin resumir: un tramo por fase
            f = ("deep" if re.search(r"deep|profund", fase) else "rem" if "rem" in fase else
                 "core" if re.search(r"core|light|ligero", fase) else "awake" if re.search(r"awake|despiert", fase) else
                 "inbed" if re.search(r"in ?bed|en cama", fase) else "asleep")
            src = x.get("source") or ""
            k = f"{src}|{f}|{ini.ms}"
            tramos[k] = [ini.local, fin.local, f, src, k]
        elif x.get("sleepStart") or x.get("inBedStart") or nn(x.get("totalSleep")) or nn(x.get("asleep")):
            resumen.append(x)
    dias: dict = {}
    if tramos:
        # cada envío manda en el tramo de tiempo que cubre de cada app: lo que esa app ya no tiene ahí se quita
        cubre: dict = {}
        for t in tramos.values():
            c = cubre.setdefault(t[3], [math.inf, -math.inf])
            c[0] = min(c[0], ms_of(t[0]))
            c[1] = max(c[1], ms_of(t[1]))

        def quitar(r):
            c = cubre.get(V.js_str(r[3]))
            if not c or not isinstance(r[0], datetime):
                return False
            t0 = ms_of(r[0])
            if c[0] <= t0 < c[1]:
                dias[dia_de_noche(ms_of(r[1]) if isinstance(r[1], datetime) else t0)] = True
                return True
            return False
        store.save_rows(con, user_id, FASES, tramos, remove=quitar)
        for t in tramos.values():
            dias[dia_de_noche(ms_of(t[1]))] = True
        return guardar_noches_salud(con, user_id, list(dias))
    # resumido: cada noche tal cual (salvo los días hechos con tramos, que son más fieles)
    con_tramos = {dia_de_noche(ms_of(r[1])) for r in store.read_rows(con, user_id, FASES).values() if isinstance(r[1], datetime)}
    noches = {}
    for x in resumen:
        h = lambda v: 0 if v is None or v == "" else num(v) * 60   # noqa: E731 — vienen en horas
        ini, fin = fecha(x.get("sleepStart") or x.get("inBedStart")), fecha(x.get("sleepEnd") or x.get("inBedEnd"))
        if not ini or not fin:
            continue
        ini_c, fin_c = fecha(x.get("inBedStart")) or ini, fecha(x.get("inBedEnd")) or fin
        dormido = h(x["totalSleep"] if nn(x.get("totalSleep")) else x.get("asleep"))
        core, deep, rem, desp = h(x.get("core")), h(x.get("deep")), h(x.get("rem")), h(x.get("awake"))
        if dormido < 60:
            continue
        k = dia_de_noche(fin.ms)
        if k in con_tramos:
            continue
        en_cama = max(dormido, (max(fin.ms, fin_c.ms) - min(ini.ms, ini_c.ms)) / MIN)
        fc = pulso_entre(con, user_id, ini.ms, fin.ms)
        noches[k] = [V.day_as_date(k), ini.local, fin.local, jr(en_cama), jr(dormido), jr(core or max(0, dormido - deep - rem)),
                     jr(deep), jr(rem), jr(desp or en_cama - dormido), "", jr(dormido / en_cama * 100), fc["media"], fc["min"],
                     ORIGEN_SALUD]
    if noches:
        store.save_rows(con, user_id, SUENO, noches, merge=rules.rellena_huecos)
    return {"noches": len(noches), "siestas": 0}


def pulso_entre(con, user_id: int, ini_ms: int, fin_ms: int) -> dict:
    """Pulso medio y mínimo entre dos instantes, con las horas de «heart_rate» de «Salud» (últimas 6000 filas)."""
    rows = store.sorted_rows(con, user_id, SALUD)[-6000:]
    v, mn = [], []
    for r in rows:
        if r[1] != "heart_rate" or not isinstance(r[0], datetime):
            continue
        t = ms_of(r[0])
        if t < ini_ms - 3600000 or t >= fin_ms:
            continue
        if not V.empty(r[2]):
            v.append(num(r[2]))
        if not V.empty(r[3]):
            mn.append(num(r[3]))
    return {"media": jr(sum(v) / len(v)) if v else "", "min": min(mn) if mn else ""}


def desvelos(dormidos: list, e: dict, k: str) -> str:
    """Ratos despierto de 10 min o más dentro de la noche, en minutos desde la medianoche del día en que te levantas."""
    base = ms_at(k, "00:00")
    out, fin = [], None
    for a, b in sorted(((x0, x1) for x0, x1, *_ in dormidos if x0 >= e["ini"] and x1 <= e["fin"]), key=lambda t: t[0]):
        if fin is not None and a - fin >= 10 * MIN:
            out.append(f"{jr((fin - base) / MIN)}~{jr((a - base) / MIN)}")
        fin = b if fin is None else max(fin, b)
    return ";".join(out)


def guardar_noches_salud(con, user_id: int, dias: list) -> dict:
    """guardarNochesSalud_: rehace las noches y siestas de los días indicados con los tramos guardados."""
    if not dias:
        return {"noches": 0, "siestas": 0}
    todos = [(ms_of(r[0]), ms_of(r[1]), V.js_str(r[2]), V.js_str(r[3]))
             for r in store.sorted_rows(con, user_id, FASES) if isinstance(r[0], datetime) and isinstance(r[1], datetime)]
    if not todos:
        return {"noches": 0, "siestas": 0}
    noches, siestas, dias_hechos, ventanas = {}, {}, {}, []
    for k in dias:
        fin_v = ms_at(k, "17:00")
        ini_v = fin_v - 24 * 3600000
        dentro = [r for r in todos if ini_v < r[1] <= fin_v]
        if not dentro:
            continue
        por_fuente: dict = {}
        for r in dentro:
            por_fuente.setdefault(r[3], []).append(r)
        dormido_ = lambda rs: sum(r[1] - r[0] for r in rs if r[2] in DORMIDO)   # noqa: E731
        rango_ = lambda f: -1 if dormido_(por_fuente[f]) <= 0 else 2 if re.search("autosleep", f, re.I) else 1 if re.search("watch", f, re.I) else 0  # noqa: E731
        fuente = None
        for f in por_fuente:
            if (fuente is None or rango_(f) > rango_(fuente)
                    or (rango_(f) == rango_(fuente) and dormido_(por_fuente[f]) > dormido_(por_fuente[fuente]))):
                fuente = f
        # si AutoSleep se queda claramente corto frente al reloj (aún no ha cerrado la noche), manda el reloj
        if fuente and re.search("autosleep", fuente, re.I):
            for f in list(por_fuente):
                if re.search("watch", f, re.I) and dormido_(por_fuente[f]) > dormido_(por_fuente[fuente]) * 1.2 + 15 * MIN:
                    fuente = f
        rs = sorted(por_fuente[fuente], key=lambda r: r[0])
        dormidos = [r for r in rs if r[2] in DORMIDO]
        if not dormidos:
            continue
        eps, ep = [], None
        for r in dormidos:
            if not ep or r[0] - ep["fin"] > 90 * MIN:
                ep = {"ini": r[0], "fin": r[1], "sueno": 0}
                eps.append(ep)
            ep["fin"] = max(ep["fin"], r[1])
            ep["sueno"] += r[1] - r[0]

        def fases(e):
            t = {"core": 0, "deep": 0, "rem": 0, "asleep": 0, "awake": 0, "desp": 0}
            for r in rs:
                if r[0] < e["ini"] or r[1] > e["fin"]:
                    continue
                if r[2] in t:
                    t[r[2]] += (r[1] - r[0]) / MIN
                if r[2] == "awake":
                    t["desp"] += 1
            return t

        nocturna = lambda t: hora_de(t) >= 19 or hora_de(t) < 12   # noqa: E731
        # ratos de la misma noche separados por un desvelo (≤ 4 h, de 19:00 a 12:00): una sola noche
        for i in range(len(eps) - 1, 0, -1):
            a, b = eps[i - 1], eps[i]
            if b["ini"] - a["fin"] <= 4 * 3600000 and nocturna(a["fin"]) and nocturna(b["ini"]):
                a["fin"] = max(a["fin"], b["fin"])
                a["sueno"] += b["sueno"]
                a["cortes"] = a.get("cortes", 0) + 1 + b.get("cortes", 0)
                del eps[i]
        # la noche del día k tiene que acabar después de las 03:00 de ese día; si no, es siesta
        tres = ms_at(k, "03:00")
        candidatas = [e for e in eps if e["fin"] >= tres] or eps
        principal = candidatas[0]
        for e in candidatas:
            if e["sueno"] > principal["sueno"]:
                principal = e
        dias_hechos[k] = True
        ventanas.append((ini_v, fin_v))
        if principal["sueno"] >= 3600000 and principal["fin"] >= tres:
            f = fases(principal)
            en_cama = (principal["fin"] - principal["ini"]) / MIN
            dormido = min(en_cama, f["core"] + f["deep"] + f["rem"] + f["asleep"])
            f_deep, f_rem = f["deep"], f["rem"]
            # AutoSleep no distingue fases: el profundo y el REM los pone el reloj en ese mismo horario
            reloj = next((x for x in por_fuente if x != fuente and re.search("watch", x, re.I)), None)
            if reloj and not re.search("watch", fuente, re.I):
                t = {"deep": 0, "rem": 0}
                for r in por_fuente[reloj]:
                    a0, b0 = max(r[0], principal["ini"]), min(r[1], principal["fin"])
                    if b0 > a0 and r[2] in t:
                        t[r[2]] += (b0 - a0) / MIN
                f_deep = min(t["deep"], dormido)
                f_rem = min(t["rem"], max(0, dormido - f_deep))
            fc = pulso_entre(con, user_id, principal["ini"], principal["fin"])
            noches[k] = [V.day_as_date(k), V.from_epoch(principal["ini"] / 1000), V.from_epoch(principal["fin"] / 1000),
                         jr(en_cama), jr(dormido), jr(max(0, dormido - f_deep - f_rem)), jr(f_deep), jr(f_rem),
                         jr(en_cama - dormido), f["desp"] + principal.get("cortes", 0), jr(dormido / en_cama * 100),
                         fc["media"], fc["min"], ORIGEN_SALUD, desvelos(dormidos, principal, k)]
        for e in eps:
            if (k in noches and e is principal) or e["sueno"] < 10 * MIN:
                continue
            f = fases(e)
            dia = dia_de(e["ini"])
            fc = pulso_entre(con, user_id, e["ini"], e["fin"])
            sid = f"hk{e['ini'] // 1000}"
            siestas[sid] = [sid, V.day_as_date(dia), V.from_epoch(e["ini"] / 1000), V.from_epoch(e["fin"] / 1000),
                            jr(f["core"] + f["deep"] + f["rem"] + f["asleep"]), jr(f["deep"]), jr(f["rem"]), fc["media"], ORIGEN_SALUD]
        # siestas que solo detecta otra app: sus ratos de sueño que no se solapan con lo de la fuente elegida
        ocupado = [(e["ini"], e["fin"]) for e in eps]
        for f2 in por_fuente:
            if f2 == fuente:
                continue
            ds = sorted((r for r in por_fuente[f2] if r[2] in DORMIDO), key=lambda r: r[0])
            e2, p = [], None
            for r in ds:
                if not p or r[0] - p["fin"] > 30 * MIN:
                    p = {"ini": r[0], "fin": r[1], "sueno": 0}
                    e2.append(p)
                p["fin"] = max(p["fin"], r[1])
                p["sueno"] += r[1] - r[0]
            for e in e2:
                if e["sueno"] < 10 * MIN or any(e["ini"] < o1 + 30 * MIN and o0 - 30 * MIN < e["fin"] for o0, o1 in ocupado):
                    continue
                ocupado.append((e["ini"], e["fin"]))
                dia = dia_de(e["ini"])
                fc = pulso_entre(con, user_id, e["ini"], e["fin"])
                sid = f"hk{e['ini'] // 1000}"
                siestas[sid] = [sid, V.day_as_date(dia), V.from_epoch(e["ini"] / 1000), V.from_epoch(e["fin"] / 1000),
                                jr(e["sueno"] / MIN), 0, 0, fc["media"], f"{ORIGEN_SALUD} ({f2})"]
    if noches:
        store.save_rows(con, user_id, SUENO, noches, merge=rules.rellena_huecos)
    if dias_hechos:
        def quitar(r):   # las siestas de esos días se rehacen enteras (las de Withings incluidas)
            t0 = ms_of(r[2])
            return t0 is not None and any(v0 < t0 <= v1 for v0, v1 in ventanas)
        store.save_rows(con, user_id, SIESTAS, siestas, remove=quitar)
    return {"noches": len(noches), "siestas": len(siestas)}


# ---------- entrenamientos ----------

def entrenos_desde_salud(con, user_id: int, ws: list) -> int:
    if not ws:
        return 0

    def q(o):
        if o is None:
            return None
        if isinstance(o, (int, float)):
            return o
        if isinstance(o, dict) and nn(o.get("qty")):
            return num(o["qty"])
        return None

    def suma(a):
        return sum(q(x) or 0 for x in a) if isinstance(a, list) else q(a)

    filas, rangos = {}, []
    for w in ws:
        ini, fin = fecha(w.get("start")), fecha(w.get("end"))
        if not ini or not fin:
            continue
        wid = "hk-" + V.js_str(w.get("id") or ini.ms // 1000)
        dur = num(w["duration"]) / 60 if nn(w.get("duration")) else (fin.ms - ini.ms) / MIN
        en = w.get("activeEnergyBurned") or w.get("activeEnergy")
        kcal = a_kcal(q(en), en.get("units") if isinstance(en, dict) else "") if q(en) is not None else suma(w.get("activeEnergy"))
        dist = a_metros(q(w["distance"]), (w["distance"] or {}).get("units") if isinstance(w.get("distance"), dict) else "") if w.get("distance") else None
        hr = w.get("heartRate") or {}
        fc_med = q(w.get("avgHeartRate")) or q(hr.get("avg"))
        fc_max = q(w.get("maxHeartRate")) or q(hr.get("max"))
        fc_min = q(hr.get("min"))
        nombre = str(w.get("name") or "Otro")
        tipo = HK_WO_ES.get(nombre.lower(), nombre)
        filas[wid] = [wid, V.day_as_date(ini.local.strftime("%Y-%m-%d")), ini.local, fin.local, jr(dur), tipo,
                      jr(kcal) if kcal is not None else "", (jr(suma(w["stepCount"])) or "") if nn(w.get("stepCount")) else "",
                      jr(dist) if dist else "", jr(fc_med) if fc_med else "", jr(fc_min) if fc_min else "",
                      jr(fc_max) if fc_max else "", r1(q(w.get("intensity"))) if q(w.get("intensity")) is not None else ""]
        rangos.append(ini.ms)

    def quitar(r):   # fuera la copia de Withings del mismo entreno (empieza a menos de 10 minutos)
        if V.js_str(r[0]).startswith("hk-") or not isinstance(r[2], datetime):
            return False
        t = ms_of(r[2])
        return any(abs(t - x) < 10 * MIN for x in rangos)
    return store.save_rows(con, user_id, ENTRENOS, filas, remove=quitar) if filas else 0
