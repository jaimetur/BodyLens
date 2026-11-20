"""Help documents: the help of each module, the README and the changelog.

English is the only source (under settings.docs_dir):
  help/en/README.md        help index, shown as the Help home
  help/en/<module>.md      help of each module
  help/en/legal/<doc>.md   privacy policy, terms of use and account deletion (public pages, not in the help index)
  README.md, CHANGELOG.md  project README and changelog
Other languages are translated automatically from these files (app.help.translate).
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from app.core import config

NAME = re.compile(r"^[a-z0-9_-]{1,40}$")
LEGAL = ("privacy", "terms", "delete-account")   # public legal pages (help/en/legal/), not in the help index


def root() -> Path:
    return config.settings.docs_dir


def resolve(doc: str) -> Path | None:
    """The English file of ``doc``: 'home', 'readme', 'changelog' or a module name."""
    if doc == "home":
        p = root() / "help" / "en" / "README.md"
    elif doc == "readme":
        p = root() / "README.md"
    elif doc == "changelog":
        p = root() / "CHANGELOG.md"
    elif doc in LEGAL:
        p = root() / "help" / "en" / "legal" / f"{doc}.md"
    elif NAME.match(doc) and doc.upper() not in ("README", "CHANGELOG"):
        p = root() / "help" / "en" / f"{doc}.md"
    else:
        return None
    return p if p.is_file() else None


def source(doc: str) -> str | None:
    """The English Markdown of ``doc`` as it is translated and shown (README without its GitHub language bar)."""
    p = resolve(doc)
    if not p:
        return None
    md = p.read_text(encoding="utf-8")
    if doc == "readme":
        md = re.sub(r"^\*\*[^\n]*README_[A-Z]{2}\.md[^\n]*(\n[^\n#][^\n]*)*\n", "", md, count=1, flags=re.M)
    return md


def module_names() -> list[str]:
    """Module help files, in the order of the help index."""
    names = sorted(p.stem for p in (root() / "help" / "en").glob("*.md") if p.stem not in ("README", "CHANGELOG"))
    home = source("home") or ""
    order = re.findall(r"\(([a-z0-9_-]+)\.md\)", home)
    return sorted(names, key=lambda n: (order.index(n) if n in order else len(order), n))


def all_docs() -> list[str]:
    return ["home", *module_names(), "readme", "changelog", *(d for d in LEGAL if resolve(d))]


def title_of(md: str) -> str:
    m = re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else ""


# ---------- a small Markdown renderer (headings, lists, tables, code, quotes, links, emphasis) ----------

def _link(m: re.Match) -> str:
    text, url = m.group(1), m.group(2)
    if re.match(r"^https?://", url):
        return f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'
    if re.match(r"^/[a-z0-9-]+$", url):   # a page of this server (e.g. /privacy)
        return f'<a href="{url}" target="_top">{text}</a>'
    name = url.split("#")[0].split("/")[-1]
    if re.match(r"^README(_[A-Z]{2})?\.md$", name):
        return f'<a href="#" data-doc="readme">{text}</a>'
    if name == "CHANGELOG.md":
        return f'<a href="#" data-doc="changelog">{text}</a>'
    if url.endswith(".md") and "/" not in url.strip("./") and NAME.match(name[:-3]):
        return f'<a href="#" data-doc="{name[:-3]}">{text}</a>'
    return text   # files of the repository are not reachable from the app


def inline(s: str) -> str:
    codes: list[str] = []
    s = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes) - 1}\x00", s)
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))])}</code>", s)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def render(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(x.strip() for x in para)) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            flush()
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            lv = len(m.group(1))
            out.append(f"<h{lv}>{inline(m.group(2).strip())}</h{lv}>")
            i += 1
            continue
        if re.match(r"^\s*(---+|\*\*\*+)\s*$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush()
            head = _cells(line)
            rows = []
            i += 2
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append("<div class=\"tbl\"><table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r)
                                                          + "</tr>" for r in rows) + "</tbody></table></div>")
            continue
        if line.startswith(">"):
            flush()
            q = []
            while i < n and lines[i].startswith(">"):
                q.append(lines[i][1:].lstrip())
                i += 1
            out.append("<blockquote>" + render("\n".join(q)) + "</blockquote>")
            continue
        if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            flush()
            block = []
            while i < n and (re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i])
                             or (lines[i].startswith("  ") and lines[i].strip() and block)):
                block.append(lines[i])
                i += 1
            out.append(_list(block))
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)


def _list(block: list[str]) -> str:
    """A list, nested by indentation; continuation lines join the previous item."""
    items: list[tuple[int, bool, str]] = []
    for ln in block:
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", ln)
        if m:
            items.append((len(m.group(1)), m.group(2)[0].isdigit(), m.group(3)))
        elif items:
            ind, ordered, text = items[-1]
            items[-1] = (ind, ordered, text + " " + ln.strip())
    html_out: list[str] = []
    stack: list[tuple[int, str]] = []
    for ind, ordered, text in items:
        tag = "ol" if ordered else "ul"
        while stack and ind < stack[-1][0]:
            html_out.append(f"</li></{stack.pop()[1]}>")
        if stack and ind == stack[-1][0]:
            html_out.append("</li>")
        elif not stack or ind > stack[-1][0]:
            html_out.append(f"<{tag}>")
            stack.append((ind, tag))
        html_out.append(f"<li>{inline(text)}")
    while stack:
        html_out.append(f"</li></{stack.pop()[1]}>")
    return "".join(html_out)
