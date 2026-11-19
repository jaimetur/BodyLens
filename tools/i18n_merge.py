#!/usr/bin/env python3
"""Junta las partes traducidas (<carpeta>/<lang>/partN.json) en src/frontend/i18n/locales/<lang>.json, ordenado como
source.json. Uso: python3 tools/i18n_merge.py <carpeta> <lang> [lang…]   (añade a lo que ya hubiera)"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "src" / "frontend" / "i18n"

src, langs = Path(sys.argv[1]), sys.argv[2:]
keys = json.loads((DIR / "source.json").read_text())
for lang in langs:
    out = DIR / "locales" / f"{lang}.json"
    d = json.loads(out.read_text()) if out.exists() else {}
    for p in sorted((src / lang).glob("part*.json")):
        d.update(json.loads(p.read_text()))
    d = {k: d[k] for k in keys if k in d}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"{lang}: {len(d)}/{len(keys)}")
