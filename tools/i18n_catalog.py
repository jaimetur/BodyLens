#!/usr/bin/env python3
"""Rebuilds src/frontend/i18n/catalog.json (the English messages) from the keys of locales/es.json and sorts every
locale file the same way. Usage: python3 tools/i18n_catalog.py"""
import json
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / "src" / "frontend" / "i18n"


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


catalog = sorted(json.loads((DIR / "locales" / "es.json").read_text()))
dump(DIR / "catalog.json", catalog)
for p in sorted((DIR / "locales").glob("*.json")):
    d = json.loads(p.read_text())
    dump(p, {k: d[k] for k in catalog if k in d} | {k: v for k, v in d.items() if k not in set(catalog)})
print(f"{len(catalog)} messages")
