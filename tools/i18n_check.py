#!/usr/bin/env python3
"""Checks the translation files against the English catalog.

- src/frontend/i18n/catalog.json must list exactly the keys of locales/es.json (es.json is the bridge to the
  Spanish texts in the code; run tools/i18n_catalog.py after editing it).
- Every locales/<lang>.json must translate every catalog message, keeping the same {0}, {1}… placeholders.

Usage: python3 tools/i18n_check.py [lang…]                 (all languages by default)
       python3 tools/i18n_check.py --part KEYS.json TRANS.json   (check a partial file: a list of messages and
                                                                its {message: translation} object)"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "src" / "frontend" / "i18n"
PH = re.compile(r"\{\d\}")


def placeholders(s: str) -> list[str]:
    return sorted(PH.findall(s))


def check(keys: list[str], tr: dict) -> list[str]:
    bad = [f"missing: {k!r}" for k in keys if k not in tr]
    for k in keys:
        v = tr.get(k)
        if v is None:
            continue
        for x in (v if isinstance(v, list) else [v]):
            if not isinstance(x, str) or not x.strip():
                bad.append(f"empty: {k!r}")
            elif placeholders(k) != placeholders(x):
                bad.append(f"placeholders differ: {k!r} -> {x!r}")
    bad += [f"not in the catalog: {k!r}" for k in tr if k not in set(keys)]
    return bad


def main(argv: list[str]) -> int:
    if argv[:1] == ["--part"]:
        bad = [b for b in check(json.loads(Path(argv[1]).read_text()), json.loads(Path(argv[2]).read_text()))]
        print("\n".join(bad) or "OK")
        return 1 if bad else 0
    catalog = json.loads((DIR / "catalog.json").read_text())
    es = json.loads((DIR / "locales" / "es.json").read_text())
    rc = 0
    if catalog != sorted(es):
        print("catalog.json is out of date: run python3 tools/i18n_catalog.py")
        rc = 1
    langs = argv or sorted(p.stem for p in (DIR / "locales").glob("*.json"))
    for lang in langs:
        tr = json.loads((DIR / "locales" / f"{lang}.json").read_text())
        bad = check(catalog, tr)
        done = len(catalog) - sum(b.startswith("missing") for b in bad)
        print(f"{lang}: {done}/{len(catalog)}" + (f" · {len(bad)} problems" if bad else " OK"))
        for b in bad[:20]:
            print("   ", b)
        rc |= bool(bad)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
