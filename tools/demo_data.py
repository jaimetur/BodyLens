#!/usr/bin/env python3
"""Creates a demo account with about two years of realistic SYNTHETIC data (for screenshots and demos).

    DATA_DIR=/path/to/empty/dir .venv/bin/python tools/demo_data.py

Never point DATA_DIR at real data: the tool refuses to run if the account «demo» already exists.
The account («demo», Alex García, Spanish) gets a random password, printed once.

The data is stored the same way the real sources store it, so the app shows it exactly as with real data:
- sheet tabs (src/backend/app/sheets/tabs.py) as Withings and Health Auto Export write them: weigh-ins with body
  composition, daily activity, workouts, nights with phases, naps, heart metrics and mood records;
- account documents for what only the app keeps: the plan and settings («peso») and the meals («com-YYYY»).
Every value comes from a seeded random generator, so two runs on the same day give the same data. The data stops at
20:30 of today (Madrid), as seen in the evening (tools/landing_capture.py sets the browser clock to that time).
"""
from __future__ import annotations

import json
import math
import os
import random
import secrets
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

from app.accounts import users  # noqa: E402
from app.core import db  # noqa: E402
from app.data import docstore  # noqa: E402
from app.sheets import service as sheets, store, values as V  # noqa: E402
from app.sheets.tabs import ACTIVIDAD, ENTRENOS, REGISTROS, SALUD, SIESTAS, SUENO, WITHINGS, ORIGEN_SALUD  # noqa: E402

DAYS = 730
HEIGHT, BIRTH, SEX = 178, "1988-04-12", "h"
PLAN_START_OFFSET, PLAN_START_KG, GOAL_KG = -256, 92.0, 80.0
WATCH = "Apple Watch de Alex"
CUTOFF_MIN = 20 * 60 + 30   # the data ends today at 20:30
rnd = random.Random(20241121)

# Weight trend: (days before today, kg). A first attempt, a slow regain and the current plan with plateaus.
WEIGHT_ANCHORS = [(-729, 89.6), (-700, 89.9), (-682, 90.4), (-669, 89.6), (-629, 87.2), (-605, 86.9), (-574, 85.1),
                  (-554, 84.7), (-523, 85.4), (-457, 87.9), (-415, 88.6), (-354, 90.4), (-316, 92.2), (-264, 92.4),
                  (-256, 92.0), (-219, 89.9), (-194, 89.3), (-153, 87.4), (-128, 87.1), (-87, 86.9), (-51, 85.3),
                  (-26, 84.6), (0, 84.0)]


def smooth(anchors, x: float) -> float:
    """Value at x of the curve through the anchors (cosine easing between them)."""
    if x <= anchors[0][0]:
        return anchors[0][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x <= x1:
            f = (1 - math.cos(math.pi * (x - x0) / (x1 - x0))) / 2
            return y0 + (y1 - y0) * f
    return anchors[-1][1]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def at(day: date, minutes: float) -> datetime:
    """Local (Madrid) date and time of `minutes` after midnight of `day` (may be negative)."""
    return datetime(day.year, day.month, day.day) + timedelta(minutes=round(minutes))


def ms(d: datetime) -> int:
    return int(V.to_epoch(d) * 1000)


def noon(day: date) -> datetime:
    return V.day_as_date(day.isoformat())


class Demo:
    def __init__(self, today: date):
        self.today = today
        self.days = [today - timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
        self.weight = {d: smooth(WEIGHT_ANCHORS, (d - today).days) for d in self.days}
        self.tabs: dict = {t: {} for t in (WITHINGS, ACTIVIDAD, ENTRENOS, SUENO, SIESTAS, SALUD, REGISTROS)}
        self.workouts: dict[date, list] = {}
        self.cutoff = at(today, CUTOFF_MIN)

    def offset(self, d: date) -> int:
        return (d - self.today).days

    def dieting(self, d: date) -> bool:
        """In one of the two weight-loss attempts (more steps, more workouts, better meals)."""
        o = self.offset(d)
        return -682 <= o <= -554 or o >= PLAN_START_OFFSET

    # ---------- weigh-ins (Withings) ----------
    def weigh_ins(self):
        grp = 5_000_000_000
        for d in self.days:
            if rnd.random() > (0.88 if self.dieting(d) else 0.55):
                continue
            weekend = 0.35 if d.weekday() in (0, 6) else 0.0   # Sunday and Monday weigh-ins come after the weekend
            kg = self.weight[d] + weekend + rnd.gauss(0, 0.32)
            fat = clamp(22.8 + (self.weight[d] - 84) * 0.78 + rnd.gauss(0, 0.45), 15, 35)   # the loss is mostly fat
            fat_kg = kg * fat / 100
            bone = 3.3 + rnd.gauss(0, 0.03)
            muscle = kg - fat_kg - bone
            water = (kg - fat_kg) * 0.725 + rnd.gauss(0, 0.2)
            when = at(d, rnd.gauss(7 * 60 + 25, 20) + (60 if d.weekday() >= 5 else 0))
            grp += rnd.randint(1, 999)
            self.tabs[WITHINGS][str(grp)] = [when, int(V.to_epoch(when)), round(kg, 2), round(fat, 2), round(fat_kg, 2),
                                             round(muscle, 2), round(water, 2), round(bone, 2), grp, 0]

    # ---------- workouts and daily activity ----------
    def plan_workouts(self):
        kinds = {0: ("Pesas", 18 * 60 + 30, 50), 2: ("Correr", 19 * 60 + 10, 35), 3: ("Pádel", 20 * 60, 75),
                 5: ("Bicicleta", 10 * 60, 80), 6: ("Senderismo", 10 * 60 + 30, 110)}
        for d in self.days:
            if d.weekday() not in kinds:
                continue
            p = 0.8 if self.dieting(d) else 0.3
            if rnd.random() > p:
                continue
            tipo, start, dur = kinds[d.weekday()]
            if d.weekday() == 6 and rnd.random() < 0.5:
                tipo, dur = "Caminar", 60
            dur = max(20, round(dur + rnd.gauss(0, dur * 0.12)))
            start += rnd.gauss(0, 15)
            fitness = clamp((92.5 - self.weight[d]) / 8, 0, 1)
            hr_avg = {"Pesas": 112, "Correr": 152, "Pádel": 138, "Bicicleta": 134, "Senderismo": 118, "Caminar": 104}[tipo]
            hr_avg = round(hr_avg - 4 * fitness + rnd.gauss(0, 4))
            kcal = round(dur * {"Pesas": 6.2, "Correr": 11.5, "Pádel": 8.5, "Bicicleta": 8.8, "Senderismo": 6.8,
                                "Caminar": 4.6}[tipo] * self.weight[d] / 88)
            steps = {"Correr": dur * 158, "Senderismo": dur * 105, "Caminar": dur * 112, "Pádel": dur * 60}.get(tipo, 0)
            steps = round(steps * rnd.uniform(0.9, 1.1)) if steps else ""
            dist = {"Correr": dur * (150 + 25 * fitness), "Senderismo": dur * 72, "Caminar": dur * 85,
                    "Bicicleta": dur * 340}.get(tipo, 0)
            dist = round(dist * rnd.uniform(0.92, 1.08)) if dist else ""
            ini, fin = at(d, start), at(d, start + dur)
            if fin > self.cutoff:
                continue
            wid = f"hk-{secrets.token_hex(4).upper()}-{d.strftime('%y%m%d')}"
            row = [wid, noon(d), ini, fin, dur, tipo, kcal, steps, dist, hr_avg, round(hr_avg * 0.68),
                   round(hr_avg * 1.18 + rnd.gauss(0, 3)), round(rnd.uniform(4.5, 9.5), 1)]
            self.tabs[ENTRENOS][wid] = row
            self.workouts.setdefault(d, []).append(row)

    def activity(self):
        for d in self.days:
            wos = self.workouts.get(d, [])
            base = 9800 if self.dieting(d) else 6600
            base *= 0.82 if d.weekday() >= 5 and not wos else 1.0
            steps = round(clamp(rnd.lognormvariate(math.log(base), 0.22), 2100, 19000) + sum(w[7] or 0 for w in wos))
            if d == self.today:
                steps = round(steps * 0.85)   # today is not over yet
            dist = round(steps * rnd.uniform(0.72, 0.78))
            exercise = round(sum(w[4] for w in wos) + clamp(rnd.gauss(14 if self.dieting(d) else 8, 7), 0, 45))
            active = round(steps * 0.034 + sum(w[6] for w in wos) * 0.85 + rnd.gauss(40, 25))
            basal = round(1640 + (self.weight[d] - 84) * 13 + rnd.gauss(0, 15))
            hr_max = max([w[11] for w in wos] or [round(rnd.gauss(118, 8))])
            self.tabs[ACTIVIDAD][d.isoformat()] = [noon(d), steps, dist, round(clamp(rnd.gauss(24, 12), 0, 90)), "",
                                                   exercise, "", active, active + basal, round(rnd.gauss(76, 3)),
                                                   round(rnd.gauss(52, 2)), hr_max, ORIGEN_SALUD]

    # ---------- sleep ----------
    def night(self, d: date):
        """One night ending on the morning of day d: its hypnogram as [(start, end, phase)] in minutes from midnight."""
        weekend = d.weekday() >= 5   # Friday and Saturday nights
        onset = rnd.gauss(-25 if not weekend else 20, 22)
        wake = rnd.gauss(7 * 60 + 2 if not weekend else 8 * 60 + 40, 18)
        if rnd.random() < 0.08:   # a short night now and then
            wake -= rnd.uniform(40, 90)
        segs, t, cycle = [], onset, 0
        while t < wake - 15:
            light1 = rnd.uniform(18, 32)
            deep = max(0.0, rnd.gauss(42 - cycle * 11, 6))
            light2 = rnd.uniform(8, 20)
            rem = clamp(rnd.gauss(9 + cycle * 7, 4), 4, 45)
            for phase, length in (("l", light1), ("d", deep), ("l", light2), ("r", rem)):
                if length < 2 or t >= wake:
                    continue
                end = min(wake, t + length)
                segs.append([round(t), round(end), phase])
                t = end
            if t < wake - 20:
                awake = rnd.uniform(11, 22) if rnd.random() < 0.18 else rnd.uniform(1, 5) if rnd.random() < 0.55 else 0
                if awake >= 1:
                    segs.append([round(t), round(t + awake), "w"])
                    t += awake
            cycle += 1
        out = []
        for a, b, c in segs:   # merge touching pieces of the same phase
            if b <= a:
                continue
            if out and out[-1][2] == c and a - out[-1][1] <= 1:
                out[-1][1] = b
            else:
                out.append([a, b, c])
        return out

    def sleep(self):
        for d in self.days[1:]:
            segs = self.night(d)
            mins = {c: sum(b - a for a, b, x in segs if x == c) for c in "ldrw"}
            in_bed = segs[-1][1] - segs[0][0]
            asleep = in_bed - mins["w"]
            wakeups = sum(1 for s in segs if s[2] == "w")
            gaps = ";".join(f"{a}~{b}" for a, b, c in segs if c == "w" and b - a >= 10)
            phases = ";".join(f"{a}~{b}~{c}" for a, b, c in segs)
            fit = clamp((92.5 - self.weight[d]) / 8, 0, 1)
            self.tabs[SUENO][d.isoformat()] = [noon(d), at(d, segs[0][0]), at(d, segs[-1][1]), in_bed, asleep, mins["l"],
                                               mins["d"], mins["r"], mins["w"], wakeups, round(asleep / in_bed * 100),
                                               round(rnd.gauss(58 - 4 * fit, 2)), round(rnd.gauss(50 - 4 * fit, 2)),
                                               ORIGEN_SALUD, gaps, phases]
            if d.weekday() >= 5 and rnd.random() < 0.35 or rnd.random() < 0.04:
                start = rnd.uniform(14 * 60 + 40, 16 * 60 + 20)
                dur = round(rnd.uniform(18, 48))
                ini, fin = at(d, start), at(d, start + dur + rnd.uniform(2, 6))
                nid = f"hk{int(V.to_epoch(ini))}"
                self.tabs[SIESTAS][nid] = [nid, noon(d), ini, fin, dur, round(rnd.uniform(0, 6)), 0,
                                           round(rnd.gauss(61, 3)), ORIGEN_SALUD]

    # ---------- heart and other Apple Health metrics («Salud» tab) ----------
    def metric(self, when: datetime, key: str, val, unit: str, lo="", hi=""):
        k = f"{key}|{ms(when)}"
        self.tabs[SALUD][k] = [when, key, val, lo, hi, unit, WATCH, k]

    def heart(self):
        for d in self.days:
            fit = clamp((92.5 - self.weight[d]) / 8, 0, 1)
            self.metric(at(d, 7 * 60 + 30), "rhr", round(rnd.gauss(63 - 8 * fit, 1.6)), "count/min")
            for h in (90, 210, 330):
                self.metric(at(d, h), "hrv", round(clamp(rnd.gauss(39 + 11 * fit, 6), 18, 90), 1), "ms")
            for h in (120, 270):
                v = clamp(rnd.gauss(96.6, 0.7), 93.5, 99.5)
                self.metric(at(d, h), "spo2", round(v, 1), "%", round(v - rnd.uniform(1, 3), 1), round(min(100, v + 1.2), 1))
            rr = rnd.gauss(14.6, 0.5)
            self.metric(at(d, 180), "rr", round(rr, 1), "count/min", round(rr - rnd.uniform(1.2, 2.2), 1),
                        round(rr + rnd.uniform(1.5, 3), 1))
            self.metric(at(d, 13 * 60), "whr", round(rnd.gauss(104 - 6 * fit, 2.5)), "count/min")
            self.metric(at(d, 19 * 60), "day", round(clamp(rnd.gauss(55, 25), 5, 180)), "min")
            if d.weekday() == 6:
                self.metric(at(d, 11 * 60), "vo2", round(37.6 + 5.2 * fit + rnd.gauss(0, 0.4), 1), "ml/(kg·min)")
            for w in self.workouts.get(d, []):
                if w[5] in ("Correr", "Bicicleta", "Pádel"):
                    self.metric(w[3], "hrr", round(rnd.gauss(24 + 6 * fit, 2)), "count/min")

    # ---------- mood (State of Mind in Apple Health, «Registros de salud» tab) ----------
    MOOD_CLS = ["Very Unpleasant", "Unpleasant", "Slightly Unpleasant", "Neutral", "Slightly Pleasant", "Pleasant",
                "Very Pleasant"]
    GOOD = ["Calm", "Grateful", "Happy", "Content", "Hopeful", "Proud", "Peaceful", "Confident", "Joyful", "Relieved"]
    BAD = ["Stressed", "Drained", "Worried", "Frustrated", "Irritated", "Overwhelmed"]
    ASSOC = ["Family", "Fitness", "Work", "Partner", "Friends", "Health", "Hobbies", "Selfcare", "Weather", "Travel"]

    def mood(self):
        for d in self.days[-150:]:
            for kind, minute, p in (("dailyMood", 22 * 60 + 40, 0.8), ("momentaryEmotion", 13 * 60 + 15, 0.3)):
                if rnd.random() > p:
                    continue
                v = clamp(rnd.gauss(0.32 + (0.15 if d.weekday() >= 5 else 0) + (0.1 if self.workouts.get(d) else 0), 0.33),
                          -1, 1)
                if (self.today - d).days < 4:   # a good week to end with
                    v = max(v, rnd.uniform(0.35, 0.8))
                cls = self.MOOD_CLS[min(6, int((v + 1) / 2 * 7))]
                pool = self.GOOD if v > 0.1 else self.BAD if v < -0.1 else ["Indifferent", "Calm", "Drained"]
                when = at(d, minute + rnd.gauss(0, 25))
                val = {"v": round(v, 3), "c": cls, "k": kind, "l": rnd.sample(pool, rnd.randint(1, 3)),
                       "a": rnd.sample(self.ASSOC, rnd.randint(1, 2))}
                k = f"stateofmind|{ms(when)}"
                self.tabs[REGISTROS][k] = [when, when, "stateofmind", json.dumps(val, ensure_ascii=False,
                                                                                    separators=(",", ":")), k]

    # ---------- meals (app documents «com-YYYY») ----------
    BREAKFAST = ["Café con leche y tostada integral con tomate", "Yogur natural con avena y fresas",
                 "Tostada con aguacate y huevo", "Café y fruta", "Kéfir con nueces y plátano"]
    LUNCH = ["Lentejas con verduras y ensalada", "Pollo a la plancha con arroz integral", "Merluza al horno con patata",
             "Ensalada de garbanzos con atún", "Pasta integral con verduras y pavo", "Crema de calabacín y tortilla"]
    DINNER = ["Tortilla francesa y ensalada", "Salmón con verduras al horno", "Crema de verduras y pechuga de pavo",
              "Revuelto de setas y pan integral", "Ensalada César ligera", "Sopa de pescado"]
    TREATS = ["Dos onzas de chocolate", "Un trozo de tarta", "Patatas fritas en el aperitivo", "Helado"]
    DRINKS = ["Una caña", "Dos copas de vino", "Una cerveza sin alcohol", "Un vermú"]

    def meals(self) -> dict:
        docs: dict = {}
        for d in self.days[-45:]:
            if rnd.random() < 0.06 and d != self.today:
                continue
            weekend = d.weekday() >= 4
            wos = self.workouts.get(d, [])
            s = [rnd.choice([4, 4, 5, 3]), rnd.choice([4, 5, 4, 3]), rnd.choice([4, 3, 5, 4, 2]), rnd.choice([3, 4, 5, 4]),
                 min(5, round(wos[0][4] / 15)) if wos else 0, 0, 0]
            t = [rnd.choice(self.BREAKFAST), rnd.choice(self.LUNCH), rnd.choice(self.DINNER), None,
                 f"{wos[0][5]} {wos[0][4]} min" if wos else None, None, None]
            if rnd.random() < (0.45 if weekend else 0.12):
                s[5] = -rnd.choice([1, 1, 2, 3])
                t[3] = rnd.choice(self.TREATS)
            if rnd.random() < (0.5 if weekend else 0.08):
                s[6] = -rnd.choice([1, 1, 2])
                t[6] = rnd.choice(self.DRINKS)
            if d == self.today:   # today: only breakfast and lunch so far
                s[2], t[2], s[5], s[6], t[3], t[6] = None, None, 0, 0, None, None
            y = docs.setdefault(f"com-{d.year}", {"y": d.year, "d": {}})
            y["d"][d.isoformat()] = {"t": t, "s": s, "app": 1}
        return docs

    def drop_future(self):
        """Removes whatever would happen after the cut-off time of today."""
        for tab, rows in self.tabs.items():
            for k in [k for k, r in rows.items() if any(isinstance(x, datetime) and x > self.cutoff for x in r[:4])]:
                del rows[k]

    def settings(self) -> dict:
        start = (self.today + timedelta(days=PLAN_START_OFFSET)).isoformat()
        cfg = {"start": PLAN_START_KG, "goal": GOAL_KG, "startDate": start, "rates": [1, 0.5, 0.2], "height": HEIGHT,
               "sex": SEX, "birth": BIRTH, "fileId": None, "stepGoal": 9000, "minGoal": 30, "kcalGoal": 450,
               "sleepGoal": 7.5}
        return {"v": 3, "cfg": cfg, "cfgEdited": True, "manual": {}, "notes": {start: "Empiezo el plan con la nutricionista"},
                "milestones": [{"date": None, "kg": 88}, {"date": None, "kg": 85}], "lastSync": None}


def main() -> None:
    if "DATA_DIR" not in os.environ:
        raise SystemExit("Set DATA_DIR to a new, empty data directory (never the real data).")
    Path(os.environ["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    db.init_db()
    today = datetime.now(V.TZ).date()
    demo = Demo(today)
    demo.weigh_ins()
    demo.plan_workouts()
    demo.activity()
    demo.sleep()
    demo.heart()
    demo.mood()
    demo.drop_future()
    password = secrets.token_urlsafe(12)
    with db.tx() as con:
        if users.get_by_username(con, "demo"):
            raise SystemExit("The account «demo» already exists in this DATA_DIR: use a new, empty directory.")
        u = users.create_user(con, "demo", "Alex García", password, email="demo@example.com")
        con.execute("UPDATE users SET lang='es', data_source='server' WHERE id=?", (u.id,))
        for tab, rows in demo.tabs.items():
            store.save_rows(con, u.id, tab, rows)
        docstore.put_doc(con, u, docstore.MAIN_COLLECTION, "peso", demo.settings())
        for doc_id, data in demo.meals().items():
            docstore.put_doc(con, u, docstore.MAIN_COLLECTION, doc_id, data)
        # as if Health Auto Export had just posted (the «Update» button and the sources status expect it)
        db.set_setting(con, f"hae_last:{u.id}", {"at": db.now_iso(), "metricas": len(demo.tabs[SALUD])})
        store.mark_dirty(con, u.id)
    sheets.rebuild(u.id, force=True)
    print("Demo account created: user «demo» (Alex García), " +
          ", ".join(f"{t.name}: {len(r)}" for t, r in demo.tabs.items()))
    print(f"Password (shown only once): {password}")


if __name__ == "__main__":
    main()
