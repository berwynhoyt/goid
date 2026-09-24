#!/usr/bin/env python3
"""Build a Go version x target test matrix from the test jobs' results files.

Usage: test-matrix.py <results_dir> <out_dir>
Reads results-*.jsonl, one {"go", "target", "result"} object per line, where result is pass or fail.
The GO_VERSIONS environment variable holds the JSON list of every Go version tested.
Writes matrix.md (for the run summary), matrix.svg, matrix.json and index.html into out_dir.
"""

import glob
import html
import json
import os
import sys
import time

results_dir, out_dir = sys.argv[1], sys.argv[2]
versions = json.loads(os.environ["GO_VERSIONS"])
commit = os.environ.get("GITHUB_SHA", "")[:7]
run_url = "{}/{}/actions/runs/{}".format(os.environ.get("GITHUB_SERVER_URL", ""),
                                          os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", ""))
date = time.strftime("%Y-%m-%d", time.gmtime())

# results[version][column] = "pass" or "fail".
results = {}
for path in glob.glob(os.path.join(results_dir, "results-*.jsonl")):
    with open(path) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                results.setdefault(r["go"], {})[r["target"]] = r["result"]

# Linux ports first, then wasm, then the purego build mode.
# The race check only runs on the latest Go, so a column for it would be mostly blank.
# It still fails its job if it breaks, so it is left out here.
columns = set(c for row in results.values() for c in row) - {"race"}
extras = [c for c in ("purego",) if c in columns]
linux = sorted(c for c in columns if c.startswith("linux/"))
others = sorted(columns - set(linux) - set(extras))
columns = linux + others + extras
rows = list(reversed(versions))  # Newest Go version first.


def cell(version, column):
    """Return one of ok, fail, none (target unsupported) or missing (job produced no results)."""
    if version not in results:
        return "missing"
    r = results[version].get(column)
    return "none" if r is None else "ok" if r == "pass" else "fail"


def short(column):
    return column[len("linux/"):] if column.startswith("linux/") else column


# The SVG colors its symbols with CSS. Markdown cannot, so it uses emoji that carry their own color.
# chr() keeps this source file ASCII. U+FE0E asks for the text form of the tick, so CSS can color it.
TICK, CROSS, TICK_EMOJI, CROSS_EMOJI = chr(0x2714) + chr(0xFE0E), chr(0x2718), chr(0x2705), chr(0x274C)
symbols = {"ok": TICK, "fail": CROSS, "missing": "?", "none": ""}
md_symbols = dict(symbols, ok=TICK_EMOJI, fail=CROSS_EMOJI)
legend = "Key: %s = pass     %s = fail     ? = no pipeline results     blank = CPU unsupported by Go"
md_legend = legend % (TICK_EMOJI, CROSS_EMOJI)
legend %= (TICK, CROSS)
notes = []

# Markdown table for the workflow run summary.
md = ["## Test matrix", "", "| Go Version | " + " | ".join(short(c) for c in columns) + " |",
      "|---|" + "---|" * len(columns)]
for v in rows:
    md.append("| " + v + " | " + " | ".join(md_symbols[cell(v, c)] for c in columns) + " |")
md += ["", md_legend] + notes + [""]

# SVG grid for the README. The background is transparent, so it sits on GitHub's light or dark theme.
# Text uses a grey with about 4.3:1 contrast on both, and cells use see-through tints.
cw, ch, label_w, top, pad = 26, 22, 76, 22, 12
SCALE = 1.25  # Display size relative to the drawing's own units.
# SVG cannot measure text, so estimate widths per character, erring slightly wide.
HEAD_CHAR_W, KEY_CHAR_W = 6.8, 5.0
# Headers slant up at 50 degrees from the middle of their column.
COS, SIN = 0.643, 0.766
head_h = max(SIN * HEAD_CHAR_W * len(short(c)) for c in columns) + 10
grid_bottom = top + head_h + ch * len(rows)
lines = [legend] + notes + ["Commit %s | tested %s" % (commit, date)]
height = grid_bottom + 26 + 16 * (len(lines) - 1)
# The right edge is whichever reaches furthest: a slanted header, or a footer line.
width = max([label_w + cw * (i + 0.5) + COS * HEAD_CHAR_W * len(short(c)) + 6 for i, c in enumerate(columns)]
            + [KEY_CHAR_W * len(line) for line in lines])
full_w, full_h = width + 2 * pad, height + 2 * pad
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
       'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="12">'
       % (full_w * SCALE, full_h * SCALE, full_w, full_h),
       '<style>',
       '.bg{fill:none;stroke:#787880;stroke-opacity:0.4} text{fill:#787880;white-space:pre}',
       '.ok{fill:none} .fail{fill:#da3633;fill-opacity:0.22}',
       '.none{fill:none} .missing{fill:none}',
       '.tok{fill:#238636;font-weight:bold} .tfail{fill:#da3633;font-weight:bold}',
       '.tnone{fill:#4c7fd8;font-weight:bold} .tmissing{fill:#a88400;font-weight:bold}',
       '</style>',
       '<rect class="bg" x="0.5" y="0.5" width="%d" height="%d" rx="6"/>' % (full_w - 1, full_h - 1),
       '<g transform="translate(%d %d)">' % (pad, pad),
       '<text x="0" y="16" font-size="14" font-weight="bold">goid test matrix</text>',
       '<text x="0" y="%g" font-weight="bold">Go Version</text>' % (top + head_h - 6)]
for i, c in enumerate(columns):
    x = label_w + cw * i + cw / 2
    y = top + head_h - 6
    svg.append('<text x="%g" y="%g" transform="rotate(-50 %g %g)">%s</text>' % (x, y, x, y, html.escape(short(c))))
for j, v in enumerate(rows):
    y = top + head_h + ch * j
    svg.append('<text x="0" y="%g">%s</text>' % (y + 15, html.escape(v)))
    for i, c in enumerate(columns):
        state = cell(v, c)
        x = label_w + cw * i
        # Inset each cell by 1px, leaving see-through gaps as grid lines.
        svg.append('<rect class="%s" x="%d" y="%d" width="%d" height="%d"/>' % (state, x + 1, y + 1, cw - 2, ch - 2))
        cls = "t" + state
        svg.append('<text class="%s" x="%g" y="%g" text-anchor="middle">%s</text>'
                   % (cls, x + cw / 2, y + 15, symbols[state]))
for k, text in enumerate(lines):
    text = html.escape(text)
    if text.startswith("Key:"):
        # Color the key's symbols like the cells.
        for state, symbol in symbols.items():
            if symbol:  # Replacing "" would insert a tspan between every character.
                text = text.replace(symbol, '<tspan class="t%s">%s</tspan>' % (state, symbol))
    svg.append('<text x="0" y="%d" font-size="11">%s</text>' % (grid_bottom + 18 + 16 * k, text))
svg.append('</g></svg>')

page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>goid test matrix</title>
<style>
:root{color-scheme:light dark} body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:16px;
background:#ffffff;color:#1f2328} a{color:#0969da} img{max-width:100%%;height:auto}
@media (prefers-color-scheme: dark){body{background:#0d1117;color:#e6edf3} a{color:#4493f8}}
</style></head><body>
<p><img src="matrix.svg" alt="goid test matrix"></p>
<p><a href="%s">Workflow run</a> - <a href="matrix.json">matrix.json</a></p>
</body></html>
""" % html.escape(run_url)

os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "matrix.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))
with open(os.path.join(out_dir, "matrix.svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(svg) + "\n")
with open(os.path.join(out_dir, "matrix.json"), "w", encoding="utf-8") as f:
    json.dump({"commit": commit, "date": date, "run": run_url, "columns": columns,
               "results": {v: {c: cell(v, c) for c in columns} for v in rows}}, f, indent=1)
with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
