#!/usr/bin/env python3
"""Comprueba los diccionarios de idiomas contra source.json: claves que faltan y marcadores {0}, {1}… que no cuadran.
Uso: python3 tools/i18n_check.py [lang…]        (sin argumentos: todos)
     python3 tools/i18n_check.py --part SRC.json TRAD.json   (una parte suelta, para quien traduce)"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "src" / "frontend" / "i18n"
PH = re.compile(r"\{\d\}")


def check(keys: list[str], tr: dict) -> list[str]:
    bad = [f"falta: {k!r}" for k in keys if k not in tr]
    for k in keys:
        v = tr.get(k)
        if v is None:
            continue
        if not isinstance(v, str) or not v.strip():
            bad.append(f"vacía: {k!r}")
        elif sorted(PH.findall(k)) != sorted(PH.findall(v)):
            bad.append(f"marcadores distintos: {k!r} → {v!r}")
    return bad


def main(argv: list[str]) -> int:
    if argv[:1] == ["--part"]:
        bad = check(json.loads(Path(argv[1]).read_text()), json.loads(Path(argv[2]).read_text()))
        print("\n".join(bad) or "OK")
        return 1 if bad else 0
    keys = json.loads((DIR / "source.json").read_text())
    langs = argv or sorted(p.stem for p in (DIR / "locales").glob("*.json"))
    rc = 0
    for lang in langs:
        tr = json.loads((DIR / "locales" / f"{lang}.json").read_text())
        bad = check(keys, tr)
        print(f"{lang}: {len(keys) - sum(b.startswith('falta') for b in bad)}/{len(keys)}" + (f" · {len(bad)} problemas" if bad else " OK"))
        for b in bad[:20]:
            print("   ", b)
        rc |= bool(bad)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
