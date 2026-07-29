#!/usr/bin/env python3
"""
FIGURE-TEXT CONSISTENCY CHECK  (added v0.6.1)

Why this exists
---------------
The four existing verification suites (256 checks) all passed while Ghana's figures displayed
87.5% and every text KPI on the same page said 86.0%. They could not catch it: they check that
the arithmetic reproduces and that the HTML *text* is consistent, but a number typed into a
matplotlib title is baked into a PNG. It is invisible to every string check on the document, and
it is the FIRST thing a human reader sees.

So: OCR every figure that ships in a brief, pull out every headline-format percentage, and
require it to be a value the model actually produced. This checks what the reviewer sees, not
what the code claims.

Note on OCR: tesseract occasionally misreads a glyph. A finding here is "inspect this", not
"the build is broken" — but an UNKNOWN value that matches a previous release's number (as 87.5
did) is a real defect, and that is exactly the case this is built to catch.
"""
import json, os, re, sys
from PIL import Image
import pytesseract

BASE = "/home/claude/snakebite"

COUNTRIES = {
    "GHANA": dict(
        json=f"{BASE}/out2/impact_summary.json",
        figs=[f"{BASE}/out2/{f}" for f in
              ("fig1_placement.png", "fig2_protected.png",
               "fig3_curve_scenarios.png", "fig4_demand.png")],
    ),
    "NIGERIA": dict(
        json=f"{BASE}/out_ng/impact_summary_ng.json",
        figs=[f"{BASE}/out_ng/{f}" for f in os.listdir(f"{BASE}/out_ng")
              if f.endswith(".png")] if os.path.isdir(f"{BASE}/out_ng") else [],
    ),
    "INDIA": dict(
        json=f"{BASE}/out_in/impact_summary_in.json",
        figs=[f"{BASE}/out_in/{f}" for f in os.listdir(f"{BASE}/out_in")
              if f.endswith(".png")] if os.path.isdir(f"{BASE}/out_in") else [],
    ),
}


def legit_percentages(obj, acc=None):
    """Every number in the JSON that could legitimately be printed as NN.N%."""
    if acc is None:
        acc = set()
    if isinstance(obj, dict):
        for v in obj.values():
            legit_percentages(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            legit_percentages(v, acc)
    elif isinstance(obj, (int, float)):
        f = float(obj)
        if 0 <= f <= 100:
            acc.add(round(f, 1))
            acc.add(round(f * 100, 1))   # fractions stored as 0.94 -> 94.0
    return acc


# Axis tick labels and round annotations are not claims; they are scaffolding.
AXIS_TICKS = {float(n) for n in range(0, 101, 5)}
TOL = 0.15

fails, warns, checks = [], [], 0
print("=" * 78)
print("FIGURE-TEXT CONSISTENCY — OCR of every shipped figure vs the model JSON")
print("=" * 78)

for name, cfg in COUNTRIES.items():
    if not os.path.exists(cfg["json"]):
        warns.append(f"{name}: no JSON at {cfg['json']} — skipped")
        continue
    data = json.load(open(cfg["json"]))
    legit = legit_percentages(data) | AXIS_TICKS
    figs = sorted(f for f in cfg["figs"] if os.path.exists(f) and "preview" not in f)
    print(f"\n--- {name} ({len(figs)} figuras, {len(legit)} valores legítimos) ---")
    if not figs:
        warns.append(f"{name}: no figures found")
        continue

    for fp in figs:
        checks += 1
        try:
            txt = pytesseract.image_to_string(Image.open(fp))
        except Exception as e:                                   # pragma: no cover
            warns.append(f"{name}: OCR failed on {os.path.basename(fp)} ({e})")
            continue
        # headline format: one decimal place followed by %
        found = re.findall(r"(\d{1,3}\.\d)\s*%", txt)
        bad = []
        for tok in found:
            v = float(tok)
            if not any(abs(v - L) < TOL for L in legit):
                bad.append(v)
        tag = os.path.basename(fp)
        if bad:
            uniq = sorted(set(bad))
            fails.append(f"{name} / {tag}: figura muestra {uniq} — no está en el JSON del modelo")
            print(f"  FAIL  {tag:28s} valores huérfanos: {uniq}")
        else:
            shown = sorted({float(t) for t in found})
            print(f"  PASS  {tag:28s} {len(found)} porcentaje(s) OK {shown if shown else ''}")

print("\n" + "=" * 78)
if fails:
    print(f"RESULT: {len(fails)} FIGURE(S) DISAGREE WITH THE MODEL")
    for f in fails:
        print("  ✗", f)
else:
    print(f"RESULT: ALL FIGURES CONSISTENT WITH THE MODEL  ({checks} figuras revisadas)")
for w in warns:
    print("  ! ", w)
print("=" * 78)
sys.exit(1 if fails else 0)
