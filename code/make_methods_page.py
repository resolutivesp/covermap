#!/usr/bin/env python3
"""Render METHODS as a real HTML page.

Why this exists: the repo ships .nojekyll (needed so GitHub Pages serves our hand-built HTML
untouched). A side-effect is that GitHub Pages then serves .md with Content-Type text/markdown,
which Chrome and Firefox DOWNLOAD rather than render. A reviewer clicking "Methods" got a file
download instead of a page. This renders methods.md into the same chrome as the three briefs.
"""
import re
import markdown
from viz_common import BASE_CSS, VERSION_TAG

BASE = "/home/claude/snakebite"
SRC = f"{BASE}/repo/methods.md"
OUT = f"{BASE}/repo/methods.html"

md = open(SRC, encoding="utf-8").read()

# Drop the leading H1 — it becomes the page header instead, so it isn't printed twice.
body_md = re.sub(r"^#\s+.*?\n", "", md, count=1)

body = markdown.markdown(
    body_md,
    extensions=["tables", "footnotes", "attr_list", "sane_lists", "toc"],
    extension_configs={"toc": {"permalink": False}},
)

SUPP = """
.doc{background:var(--surface);border:1px solid var(--grid);border-radius:13px;padding:26px 30px;margin:18px 0}
.doc h2{margin:30px 0 8px;font-size:19px;color:var(--brand1);border-bottom:1px solid var(--grid);padding-bottom:6px}
.doc h2:first-child{margin-top:0}
.doc h3{margin:22px 0 6px;font-size:15.5px;color:var(--blue-d)}
.doc h4{margin:16px 0 4px;font-size:13.5px;color:var(--sec);letter-spacing:.3px;text-transform:uppercase}
.doc p{margin:9px 0;font-size:14px;color:var(--ink)}
.doc li{font-size:14px;margin:5px 0}
.doc table{border-collapse:collapse;width:100%;margin:14px 0;font-size:12.8px}
.doc th{background:var(--plane);text-align:left;font-weight:600;color:var(--sec);
 border-bottom:2px solid var(--grid);padding:8px 10px;vertical-align:bottom}
.doc td{border-bottom:1px solid var(--grid);padding:8px 10px;vertical-align:top;
 font-variant-numeric:tabular-nums}
.doc tr:last-child td{border-bottom:none}
.doc code{background:var(--plane);border:1px solid var(--grid);border-radius:4px;
 padding:1px 5px;font-size:12.3px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.doc pre{background:var(--plane);border:1px solid var(--grid);border-radius:8px;
 padding:13px 15px;overflow-x:auto;font-size:12.3px;line-height:1.5}
.doc pre code{background:none;border:none;padding:0}
.doc blockquote{margin:13px 0;padding:2px 0 2px 15px;border-left:3px solid var(--blue);
 color:var(--sec);font-size:13.5px}
.doc a{color:var(--blue)}
.doc hr{border:none;border-top:1px solid var(--grid);margin:26px 0}
.doc strong{font-weight:650}
.back{display:inline-block;margin:2px 0 0;font-size:13px;color:var(--blue);text-decoration:none}
.back:hover{text-decoration:underline}
@media(max-width:820px){.doc{padding:18px 16px}.doc table{font-size:11.6px}}
"""

html = f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>CoverMap — Methods {VERSION_TAG.split(' · ')[0].replace('CoverMap ','')}</title>
<style>{BASE_CSS}{SUPP}</style></head><body>
<header><div class=wrap>
<div class=badge>{VERSION_TAG} · METHODS · what the model does and what it assumes</div>
<h1>Methods — Ghana · Nigeria · India</h1>
<div class=sub>The full method, every load-bearing parameter, and an explicit record of what is
sourced versus what we chose. Read alongside the
<a href="parameter-audit.txt" style="color:#fff;text-decoration:underline">parameter provenance audit</a>,
which labels each input SOURCED, DERIVED, PARTIAL or NOT CONFIRMED.</div>
</div></header><div class=wrap>
<p><a class=back href="index.html">← Back to CoverMap</a></p>
<div class=doc>
{body}
</div>
<p><a class=back href="index.html">← Back to CoverMap</a></p>
</div></body></html>"""

open(OUT, "w", encoding="utf-8").write(html)
print(f"wrote {OUT}  ({len(html):,} bytes)")

# Repoint the index link: .md downloads, .html renders.
idx_path = f"{BASE}/repo/index.html"
idx = open(idx_path, encoding="utf-8").read()
before = idx.count('href="methods.md"')
idx = idx.replace('href="methods.md"', 'href="methods.html"')
open(idx_path, "w", encoding="utf-8").write(idx)
print(f"index.html: repointed {before} methods link(s) .md -> .html")
