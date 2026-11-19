#!/usr/bin/env python3
"""Translations of the help kept in the repository (help/i18n/<lang>/<doc>.md).

The help, the README and the changelog are written in English; the app translates them automatically. For the most
used languages a careful translation can be kept in the repository instead: its first line records the English it
was made from (<!-- en: <hash> -->), so the app uses it only while that English has not changed.

Usage:
  python3 tools/help_i18n.py check            lists, for each language folder, the documents missing or stale
  python3 tools/help_i18n.py stamp <lang> [doc…]   marks the files as made from the current English
                                                  (run it after translating or updating them)
Document names: home (help/en/README.md), readme (README.md), changelog (CHANGELOG.md) and each help/en/<module>.md.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))
os.environ.setdefault("DOCS_DIR", str(ROOT))

from app.core import config  # noqa: E402

config.reload_settings()
from app.help import docs, translate  # noqa: E402

I18N = ROOT / "help" / "i18n"


def check() -> int:
    bad = 0
    for d in sorted(p for p in I18N.glob("*") if p.is_dir()):
        lang = d.name
        for doc in docs.all_docs():
            src = docs.source(doc)
            p = d / f"{doc}.md"
            if not p.exists():
                print(f"{lang}/{doc}: missing")
                bad += 1
            elif translate.bundled(lang, doc, src) is None:
                print(f"{lang}/{doc}: stale (the English changed) or not stamped")
                bad += 1
    print("OK" if not bad else f"{bad} to update")
    return 1 if bad else 0


def stamp(lang: str, names: list[str]) -> int:
    for doc in names or docs.all_docs():
        p = I18N / lang / f"{doc}.md"
        if not p.exists():
            print(f"{lang}/{doc}: missing, skipped")
            continue
        text = translate.BUNDLE_HEAD.sub("", p.read_text(encoding="utf-8"), count=1)
        p.write_text(f"<!-- en: {translate.source_hash(docs.source(doc))} -->\n" + text, encoding="utf-8")
        print(f"{lang}/{doc}: stamped")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"]:
        sys.exit(check())
    if a[:1] == ["stamp"] and len(a) >= 2:
        sys.exit(stamp(a[1], a[2:]))
    print(__doc__)
    sys.exit(2)
