#!/usr/bin/env python3
"""
CoverMap shared design system (single source of truth for all three country demonstrators).

Enforces ONE visual identity across Ghana / Nigeria / India:
  - exact dataviz-skill tokens for data ink, series, status and sequential ramps
  - a fixed brand-teal chrome (header) so the three briefs read as one product
  - a single injected stylesheet (BASE_CSS) shared by every HTML brief and planner
  - matplotlib theme + validated colormaps shared by every figure

Rationale (dataviz skill): light chart surface #fcfcfb; series-1 blue #2a78d6;
status tokens fixed (good/warning/serious/critical); sequential = one hue light->dark;
"semantic heat" (white->deep red) is the only multi-hue sequential we use, always with a
scale legend. Hero/stat-tile numbers use proportional figures; tabular-nums only in columns.
Briefs are LIGHT-mode by design (the figures render on the light surface, so a dark page
would clash with light images) — consistency over feature-count.
"""
import base64
from matplotlib.colors import LinearSegmentedColormap

# Single source of truth for the release stamp. Bump here; every brief picks it up.
VERSION = "v0.7.0"
VERSION_DATE = "July 2026"
VERSION_NOTE = ("v0.7.0 — adds KENYA, the fourth demonstrator and third failure regime "
                "(availability and placement: the failing products were withdrawn in 2022 after "
                "national QC testing). Built against a provenance sheet written before the code; "
                "county populations pinned to the KNBS 2019 census; product rule enforces market "
                "availability. Three review rounds: a self-caught coarseness rejection, a FAILED "
                "independent adversarial review (two critical errors - a population-distribution "
                "artifact and a treated fraction contradicting its source - both corrected), and a "
                "passing re-review with all numbers reproduced end-to-end independently. "
                "v0.6.2 — separates DEMONSTRATED FAILURE from ABSENCE OF DATA in the coverage "
                "matrix. PANAF-Premium x Naja katiensis was rendering as partial cover while its "
                "own cell recorded a measured failure (Khochare 2024, 11.16 LD50/mL, below the "
                "20 threshold); four untested Atractaspis cells were rendering in the same red as "
                "documented failures, asserting more than the evidence supports. Failure now "
                "overrides every higher grade and is visually distinct from no-claim and no-data. "
                "Also corrects six stale figures in the methods page and adds publish.py, which "
                "diffs generated output against the published site instead of copying by hand. "
                "v0.6.1 — corrects three Ghana figure titles that still displayed 87.5%, the "
                "pre-v0.4 coverage value, while every text KPI on the same page said 86.0%; the "
                "numbers are now read from the model JSON and a fifth verification suite OCRs "
                "every shipped figure to keep image and text in agreement. v0.6 added the "
                "targeting-scenario table for India and a parameter-provenance table to all three "
                "briefs. v0.5 confirmed 4 of 10 assumed parameters against primary sources and "
                "labelled the remaining 6 NOT CONFIRMED. v0.4 corrected the care-seeking double "
                "discount and India's state death rates.")
VERSION_TAG = f"CoverMap {VERSION} · {VERSION_DATE}"

# ---- palette tokens (dataviz skill, light surface) ------------------------------------
PAL = dict(
    surface="#fcfcfb", plane="#f6f7f9", ink="#0b0b0b", sec="#52514e", mut="#898781",
    grid="#e1e0d9", axis="#c3c2b7", ring="rgba(11,11,11,.10)",
    # data series (categorical slots 1..4)
    blue="#2a78d6", blue_d="#184f95", orange="#eb6834", aqua="#1baf7a", yellow="#eda100",
    # status (fixed, never themed)
    good="#0ca30c", good_txt="#006300", warning="#fab219", serious="#ec835a", critical="#d03b3b",
    # brand chrome (medical teal) — chrome only, never a data encoding
    brand1="#0b6b5b", brand2="#0d4f6b",
)

# sequential single-hue blue ramp (100->700) for ordered magnitude
SEQ_BLUE = ["#cde2fb","#9ec5f4","#6da7ec","#3987e5","#256abf","#184f95","#0d366b"]

def blue_cmap():
    """Sequential one-hue blue (light->dark) for ordered magnitude choropleths."""
    return LinearSegmentedColormap.from_list("seqblue", SEQ_BLUE)

def heat_cmap():
    """Semantic-heat ramp (near-zero recedes to surface -> deep red) for burden / gap.
    Allowed multi-hue sequential exception; ALWAYS paired with a scale legend."""
    return LinearSegmentedColormap.from_list(
        "heat", ["#fff5ec","#fdd9b5","#fca86b","#ef6c34","#c0392b","#7a0f0f"])

def mpl_theme():
    """Apply the shared matplotlib theme. Call once per figure script."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'figure.facecolor':PAL['surface'],'axes.facecolor':PAL['surface'],'savefig.facecolor':PAL['surface'],
        'axes.edgecolor':PAL['axis'],'axes.labelcolor':PAL['sec'],'xtick.color':PAL['mut'],'ytick.color':PAL['mut'],
        'text.color':PAL['ink'],'axes.grid':True,'grid.color':PAL['grid'],'grid.linewidth':0.8,
        'axes.axisbelow':True,'font.family':'DejaVu Sans','axes.titlecolor':PAL['ink'],'figure.dpi':100})

def b64(path):
    with open(path,'rb') as f:
        return base64.b64encode(f.read()).decode()

# ---- unified stylesheet (shared by every brief + planner) -----------------------------
# Note: this is a plain string (no f-string) so it can be injected as {CSS} into report
# f-strings without brace-escaping. Values are the tokens above, inlined.
BASE_CSS = """
:root{
 --surface:#fcfcfb; --plane:#f6f7f9; --ink:#0b0b0b; --sec:#52514e; --mut:#898781;
 --grid:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,.10);
 --blue:#2a78d6; --blue-d:#184f95; --orange:#eb6834; --aqua:#1baf7a; --yellow:#eda100;
 --good:#0ca30c; --good-txt:#006300; --warning:#fab219; --serious:#ec835a; --crit:#d03b3b;
 --brand1:#0b6b5b; --brand2:#0d4f6b;
}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 color:var(--ink);background:var(--plane);line-height:1.58;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px 76px}
header{background:linear-gradient(135deg,var(--brand1),var(--brand2));color:#fff;padding:34px 22px}
header .wrap{padding:0}
.badge{display:inline-block;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.32);
 border-radius:20px;padding:3px 12px;font-size:12px;margin-bottom:12px;letter-spacing:.2px}
h1{font-size:30px;margin:.08em 0 .18em;letter-spacing:-.4px;line-height:1.15}
.sub{font-size:17px;opacity:.96;max-width:800px}
h2{font-size:21px;margin:34px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--grid);letter-spacing:-.2px}
h3{font-size:13px;margin:18px 0 6px;color:var(--brand1);text-transform:uppercase;letter-spacing:.5px}
p{margin:.6em 0} .lead{font-size:17px}
.card{background:var(--surface);border:1px solid var(--grid);border-radius:13px;padding:20px 22px;
 margin:16px 0;box-shadow:0 1px 3px rgba(20,30,50,.045)}
img{width:100%;border:1px solid var(--grid);border-radius:10px;margin-top:8px;background:var(--surface)}
/* stat tiles — hero numbers use PROPORTIONAL figures (no tabular-nums), per dataviz */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin:16px 0}
.kpi{background:var(--surface);border:1px solid var(--grid);border-radius:11px;padding:15px 16px}
.kpi>b{display:block;font-size:26px;line-height:1.1;color:var(--blue-d);font-weight:700}
.kpi.bad>b{color:var(--crit)} .kpi.warn>b{color:#9a6a00}
.kpi span{font-size:12.5px;color:var(--sec);display:block;margin-top:4px}
.kpi span b{display:inline;font-size:inherit;line-height:inherit;color:inherit;font-weight:700}
/* tables — tabular-nums only here, where digits align in columns */
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
.t td,.t th{border-bottom:1px solid var(--grid);padding:7px 9px;text-align:right;font-variant-numeric:tabular-nums}
.t th{background:#eef1f4;color:var(--sec);font-weight:600} .t td.l,.t th.l{text-align:left;font-variant-numeric:normal}
.cov td,.cov th{border:2px solid var(--surface);padding:6px 5px;text-align:center;font-weight:600;font-size:12px}
.cov th{background:#26313f;color:#fff;font-size:11px} .cov td.sp{background:#eef1f4;text-align:left;font-size:12px;font-style:italic}
.note{background:#f1f7f5;border-left:4px solid var(--brand1);padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:14px}
.callout{background:#fff5f2;border-left:4px solid var(--serious);padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:14px}
.anchor{background:#eef4fb;border-left:4px solid var(--blue);padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:14px}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin:9px 0;color:var(--sec)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.sw{width:14px;height:14px;border-radius:3px;display:inline-block;border:1px solid var(--ring)}
ul{margin:.3em 0;padding-left:20px} li{margin:4px 0}
small,.src{font-size:12px;color:var(--mut)} .src a{color:var(--brand1)}
.muted{color:var(--sec);font-size:14px}
footer{margin-top:30px;padding-top:16px;border-top:1px solid var(--grid);font-size:12px;color:var(--mut)}
@media(max-width:720px){.kpis{grid-template-columns:repeat(2,1fr)}}
"""

# evidence-grade -> cell style for the coverage matrix (aligned to status/sequential tokens)
def cov_cell_style(coverage, grade):
    c, g = str(coverage), str(grade)
    if c == "covered" and g == "A":   return ("#0ca30c","#ffffff","A")   # good, WHO-assessed
    if c == "covered" and g == "B":   return ("#7dc47d","#0a3d0a","B")   # good (lighter), preclinical
    if c == "covered" and g == "C":   return ("#fde08a","#5a4500","C")   # weak/claim
    if c == "paraspecific-partial":   return ("#ec835a","#3a1400","~")   # serious/partial
    if c == "failed":                 return ("#a01111","#ffffff","✗")   # PUBLISHED EVIDENCE AGAINST
    if c == "not-covered":            return ("#d9a5a5","#5a0000","–")   # no activity claimed / out of scope
    if c == "unknown":                return ("#f2c9b4","#5a1500","?")
    return ("#eef1f4","#8a8a8a","·")                                     # no data
