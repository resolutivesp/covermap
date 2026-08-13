#!/usr/bin/env python3
"""
kenya_outputs.py — Kenya brief (HTML) + figures. All displayed numbers are read
from out_ke/impact_summary_ke.json and the CSVs — never typed (lesson 5).
Stamp: Kenya demonstrator rc2 — post-adversarial-review rebuild; pending re-review.
"""
import os, sys, json
import pandas as pd, geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{BASE}/data/ke"); import parameters_ke as P
sys.path.insert(0, f"{BASE}/code"); from viz_common import VERSION
OUT = f"{BASE}/out_ke"

S = json.load(open(f"{OUT}/impact_summary_ke.json"))
sub = pd.read_csv(f"{OUT}/subcounty_ke.csv")
plan = pd.read_csv(f"{OUT}/pre_positioning_plan_ke.csv")
curve = pd.read_csv(f"{OUT}/coverage_curve_ke.csv")
O = S["optimized"]

adm2 = gpd.read_file(f"{BASE}/data/ke/ken_ADM2.json").rename(columns={"shapeName": "subcounty"})
adm2 = adm2.merge(sub[["subcounty", "attendances_yr", "zone"]], on="subcounty", how="left")
fac = pd.read_csv(f"{BASE}/data/ke/kenya_facilities_who_raw.csv")
chosen = fac.merge(plan[["Facility name"]], on="Facility name")

# ---- fig 1: burden + placement ----------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 8))
adm2.plot(column="attendances_yr", cmap="YlOrRd", linewidth=0.15, edgecolor="#999", ax=ax, legend=True,
          legend_kwds={"label": "expected snakebite attendances / yr", "shrink": 0.6})
ax.scatter(chosen["Long"], chosen["Lat"], s=42, c="#0b57d0", marker="^", zorder=5,
           label=f"{O['hospitals']} selected hospitals")
ax.legend(loc="lower right"); ax.set_axis_off()
ax.set_title(f"Kenya — {O['hospitals']} hospitals bring {O['pct_covered']}% of expected "
             f"attendances within {P.REACH_KM:.0f} km", fontsize=11)
plt.tight_layout(); plt.savefig(f"{OUT}/fig1_placement_ke.png", dpi=130); plt.close()

# ---- fig 2: coverage curve --------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(curve["n_hospitals"], curve["pct_covered"], "-o", ms=3.5, color="#0b57d0")
ax.axhline(O["pct_covered"], ls="--", lw=0.8, color="#888")
ax.set_xlabel("hospitals selected (greedy)"); ax.set_ylabel("% of attendances within reach")
ax.set_title(f"Coverage saturates: {O['pct_covered']}% at {O['hospitals']} hospitals", fontsize=11)
ax.set_ylim(0, 100); ax.grid(alpha=0.25)
plt.tight_layout(); plt.savefig(f"{OUT}/fig2_curve_ke.png", dpi=130); plt.close()

# ---- brief ------------------------------------------------------------------
zone_rows = "".join(
    f"<tr><td>{z}</td><td style='text-align:right'>{P.ZONE_ATTENDANCE_PER_100K[z]}</td>"
    f"<td>{P.ZONE_RATE_STATUS[z]}</td></tr>" for z in P.ZONES)
plan_rows = "".join(
    f"<tr><td>{r['Facility name']}</td><td>{r['county']}</td><td>{r['zone']}</td>"
    f"<td style='text-align:right'>{r['vials_yr']}</td><td>{r['recommended_product']}</td></tr>"
    for _, r in plan.iterrows())
rob = S["placement_robustness"]

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>CoverMap Kenya — the fourth demonstrator</title>
<style>
body{{font:15px/1.55 system-ui,sans-serif;color:#1c2733;margin:0}}
.wrap{{max-width:960px;margin:0 auto;padding:24px}}
header{{background:#0b3d2e;color:#fff;padding:26px 0}}
h1{{margin:0 0 6px;font-size:26px}} .sub{{opacity:.85}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}
.kpi{{background:#f4f7f6;border:1px solid #dde5e2;border-radius:10px;padding:12px}}
.kpi b{{font-size:24px;display:block}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0}}
td,th{{border:1px solid #d8dee3;padding:6px 8px;text-align:left}}
th{{background:#eef2f0}}
.note{{background:#fff8e6;border:1px solid #eadf9e;border-radius:8px;padding:10px 14px;margin:14px 0;font-size:14px}}
.warn{{background:#fdecec;border:1px solid #f3b8b8}}
footer{{margin:30px 0 10px;padding-top:14px;border-top:1px solid #ccc;font-size:12.5px;color:#555}}
img{{max-width:100%;border:1px solid #e3e6e9;border-radius:8px;margin:8px 0}}
</style></head><body>
<header><div class="wrap"><h1>CoverMap Kenya — the fourth demonstrator</h1>
<div class="sub">Which WHO-assessed antivenom at which hospitals, how many vials, at what cost —
replicated for Kenya with the host organisation whose fieldwork documented the problem.</div>
</div></header><div class="wrap">

<div class="note"><b>Review history — carried, not deleted.</b> This demonstrator went through
three review rounds before release: a county-centroid draft rejected in first-pass review as too
coarse; an rc1 that <b>failed</b> independent adversarial review on two critical findings (a
population-distribution artifact that inflated Nairobi by +122% while starving Turkana by −59% —
nine of its 36 sites were artifacts — and a treated fraction contradicting its source's verbatim
25.2%); and a re-review of the rebuilt rc2 in which every number was reproduced end-to-end by an
independent implementation. Five further minor findings were fixed in rc3, including removing a
recommended alternative that is not commercialised in Kenya. Not clinical guidance.</div>

<div class="kpis">
<div class="kpi"><b>{O['pct_covered']}%</b>of expected snakebite attendances within
{P.REACH_KM:.0f} km of a zone-adequate product</div>
<div class="kpi"><b>{O['hospitals']}</b>hospitals selected from {S['n_hospital_tier']}
hospital-tier facilities</div>
<div class="kpi"><b>{O['vials_yr']:,}</b>vials/yr demand forecast
(~${O['procure_usd_yr']:,}/yr at the ${P.PRICE_PER_VIAL_USD:.0f}/vial planning assumption)</div>
<div class="kpi"><b>{S['burden_anchor']['implied_national_attendance_per_100k']}</b>implied
national attendances/100k — inside the published multi-area range
({S['burden_anchor']['coombs_range'][0]}–{S['burden_anchor']['coombs_range'][1]}, Coombs 1997)</div>
</div>

<img src="fig1_placement_ke.png" alt="placement map">
<img src="fig2_curve_ke.png" alt="coverage curve">

<h2>Why Kenya is a different failure regime</h2>
<p>Ghana and Nigeria show a <i>product-selection</i> failure. Kenya has already run that triage:
the Kenya Snakebite Research &amp; Intervention Centre's preclinical assays — the work establishing
the National Antivenom Quality Control Laboratory — found the two dominant products wanting, and,
verbatim from that paper: <i>"Both products were withdrawn from the Kenyan market in 2022 after
performing poorly in our preclinical efficacy assays using Kenyan venoms [...] and failing to
achieve a positive review in the WHO's risk-benefit assessment process"</i> — the assays being the
same group's earlier published work, cited in the QC-lab paper. (The two: VINS Snake Venom
Antiserum African — 66.7% of stocking public facilities in the 2019–20 survey — and Inoserp,
33.3%.) What remains on the market: SAIMR Polyvalent — potent across the Big Five in the QC panel
but costly ($315 per vial, framed by the paper as "of potential use" regionally — and with no
<i>Echis</i> cover — and PANAF-Premium, WHO risk–benefit assessed and since approved by the
Pharmacy and Poisons Board. AFRIVEN, VINS's reformulation, was also potent across the Big Five in
the panel but <i>"has yet to be commercialised in Kenya"</i>, so this plan never recommends it.
Kenya's failure today is therefore <i>availability and placement</i>: antivenom in 44.7% of public
facilities and 20.0% stocked out in a year (13.6 days mean) — 2019–20 survey figures,
pre-withdrawal; today's picture is unlikely to be better. The product triage is done; CoverMap
answers what follows — where the adequate products should sit, and in what quantity.</p>

<h2>Product rule (enforced in code, verified)</h2>
<p>{S['product_rule']}</p>
<div class="note">Evidence: the Kenya QC-laboratory study (Toxins 2026;18(2):106) tested the four
products previously or currently available in Kenya against the Big Five venoms (challenge dose 5×;
3× and 2× where marked in its Figure 4). PANAF-Premium's <i>Echis pyramidum</i> cover is listed in
its WHO Schedule 2 — grade A under this project's published grading scheme; the WHO document itself
carries no grading. No other product has a Kenyan <i>Echis</i> datum — an unknown is never promoted
to coverage. Echis-county mapping follows the only Kenya-specific published range list (Ochola 2018
Table 1, a Bio-Ken compilation whose row is labelled <i>Echis carinatus</i> — the compilation's
name for the Kenyan carpet viper, <i>E. pyramidum</i> complex; the equation is ours). Place names
are mapped to counties by us: for listed places inclusion errs safe, but counties absent from the
compilation (Samburu, Isiolo, Marsabit — plausible range) default to unflagged, which for the
<i>alternative</i> recommendation is the unsafe direction. Declared; the WHO snake-distribution
database check is a named finalist-phase task.</div>

<h2>The plan</h2>
<table><tr><th>Facility</th><th>County</th><th>Zone</th><th>Vials/yr</th><th>Recommended product</th></tr>
<!-- serves_echis_county drives the recommendation; see product rule -->
{plan_rows}</table>

<h2>Zone attendance rates — provenance first</h2>
<table><tr><th>Zone</th><th>Rate /100k/yr</th><th>Status</th></tr>{zone_rows}</table>
<div class="note"><b>Honest limits.</b> Two zone rates carry direct published anchors (WEST:
Ochola 2018 Kakamega; COAST: Abouyannis 2023 paediatric admissions — children only). ARID_NORTH and
RIFT are constructions bracketed by Coombs 1997 (1.9–67.9) and the community-side surveys (Snow
1994 coast 151/100k; Samburu 2024 ≈440/100k derived). CENTRAL_HIGHLANDS is NOT CONFIRMED — no
published figure exists; the level is set low with direction from species ranges.
<b>Robustness:</b> halving that unconfirmed rate leaves {rob['highlands_rate_halved_overlap']} of
{rob['of']} selected hospitals unchanged. The treated fraction (25.2%) is the paper's own figure
(Abouyannis 2023); vials/patient (1.40) is derived from its published distribution and encodes
2003–21 paediatric practice with since-withdrawn products — likely a <i>floor</i> against current
dosing guidance for the products now advised. Both come from one coastal paediatric series and are
first on the list to replace with adult data. Reach is straight-line {P.REACH_KM:.0f} km, a declared
proxy for travel time. Facility coordinates inherit the WHO/KEMRI 2019 layer, including its known
geocoding imperfections — an upstream limitation we carry, not hide; one of 402 hospital-tier
facilities (Mother Solbritt, Migori) carries no coordinates and is dropped, declared here and in the
model output. Within-county population is split by a coarse raster and is approximate — county
totals are exact (census); the split inside each county is not.</div>

<footer>CoverMap {VERSION} · Kenya demonstrator · built {S['n_subcounty_units']} subcounty units,
{S['n_counties']} counties · population pinned to KNBS 2019 census ({S['census_total_2019']:,}) ·
facility layer WHO/KEMRI (Maina 2019) · FEASIBILITY DEMONSTRATOR · not clinical guidance ·
all figures read from impact_summary_ke.json — never typed</footer>
</div></body></html>"""
open(f"{OUT}/kenya_brief_rc2.html", "w").write(html)
print(f"brief written: {len(html):,} bytes; figs: fig1_placement_ke.png, fig2_curve_ke.png")
