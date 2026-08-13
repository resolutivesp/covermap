#!/usr/bin/env python3
"""CoverMap system index — presents the three country demonstrators as ONE tool, with the
method, the honesty guardrails and the verification record. Self-contained HTML."""
import json, os
from viz_common import BASE_CSS, b64, VERSION, VERSION_TAG, VERSION_NOTE
from _paths import BASE, SRC
GH=json.load(open(f"{BASE}/out2/impact_summary.json"))
NG=json.load(open(f"{BASE}/out_ng/impact_summary_ng.json"))
IN=json.load(open(f"{BASE}/out_in/impact_summary_in.json"))

SUPP="""
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:18px 0}
.cty{background:var(--surface);border:1px solid var(--grid);border-radius:13px;padding:18px;display:flex;flex-direction:column}
.cty h3{margin:0 0 2px;color:var(--brand1);font-size:12px;letter-spacing:.6px}
.cty .big{font-size:30px;font-weight:700;color:var(--blue-d);line-height:1.05;margin:6px 0 2px}
.cty .lab{font-size:12.5px;color:var(--sec);min-height:56px}
.cty ul{margin:10px 0 0;padding-left:18px;font-size:12.5px;color:var(--sec)}
.cty .tag{margin-top:12px;font-size:11.5px;color:var(--mut);border-top:1px solid var(--grid);padding-top:9px}
.steps{counter-reset:s;list-style:none;padding:0;margin:12px 0}
.steps li{counter-increment:s;position:relative;padding-left:40px;margin:12px 0}
.steps li::before{content:counter(s);position:absolute;left:0;top:0;width:26px;height:26px;border-radius:50%;
 background:var(--brand1);color:#fff;display:grid;place-items:center;font-size:13px;font-weight:700}
.vtable td{font-variant-numeric:tabular-nums}
.ok{color:var(--good-txt);font-weight:700}
.nav{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}
.nav a{display:block;background:var(--surface);border:1px solid var(--grid);border-radius:12px;
 padding:18px 20px;text-decoration:none;color:var(--ink);transition:border-color .15s,box-shadow .15s}
.nav a:hover{border-color:var(--blue);box-shadow:0 2px 10px rgba(42,120,214,.10)}
.nav a b{display:block;font-size:16px;margin-bottom:3px;color:var(--blue-d)}
.nav a span{display:block;font-size:12.5px;color:var(--sec);line-height:1.5}
.nav a .go{display:inline-block;margin-top:9px;font-size:12px;color:var(--blue);font-weight:600}
.subnav{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 4px}
.subnav a{font-size:12.5px;color:var(--blue);text-decoration:none;border:1px solid var(--grid);
 border-radius:20px;padding:5px 13px;background:var(--surface)}
.subnav a:hover{border-color:var(--blue)}
@media(max-width:820px){.nav{grid-template-columns:1fr}}
@media(max-width:820px){.grid3{grid-template-columns:1fr}}
"""

html=f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>CoverMap — matching antivenom to the snakes that actually bite</title><style>{BASE_CSS}{SUPP}</style></head><body>
<header><div class=wrap><div class=badge>{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · four countries · not clinical guidance</div>
<h1>CoverMap — matching antivenom to the snakes that actually bite</h1>
<div class=sub>Antivenom is species-specific: the wrong product does not save the patient. CoverMap joins <b>what bites where</b> to <b>what each product is actually proven to neutralise</b> to <b>who can reach care</b> — and turns it into a costed, named plan a procurement programme can act on. Demonstrated on four countries covering three different failure regimes.</div></div></header><div class=wrap>

<div class='card lead'><p><b>The problem is a decision, not a discovery.</b> When rural Ghana substituted an unsuitable antivenom against the carpet viper, district case-fatality rose <b>1.8% → 12.1%</b> (Visser 2008). The people who buy and place antivenom must choose <i>which product</i> and <i>where</i> — with no tool that joins species range to evidence-graded product coverage to access. CoverMap is that tool.</p>
<div class=anchor><b>One method, three regimes.</b> In West Africa the binding gap is <b>which product</b> is stocked and where (several products, wildly different <i>Echis</i> cover). In India a single southern-sourced polyvalent is used nationwide, so the gap is <b>regional venom variation and non-Big-Four species</b>. In Kenya the failing products were withdrawn in 2022 after national QC testing, so the gap is <b>availability and placement</b>. The same engine expresses all three — the strongest evidence that it generalises.</div></div>

<h2>Read the four demonstrators</h2>
<div class=nav>
 <a href="ghana.html"><b>Ghana →</b><span>Placement: 25 named hospitals, 4,654 vials/yr, ~$371k. The best-sourced demonstrator.</span><span class=go>Open the brief</span></a>
 <a href="nigeria.html"><b>Nigeria →</b><span>Scale: 63 hospitals, 36,671 vials/yr against the largest West-African burden.</span><span class=go>Open the brief</span></a>
 <a href="india.html"><b>India →</b><span>A different regime: where the standard antivenom underperforms, and where to target first.</span><span class=go>Open the brief</span></a>
 <a href="kenya.html"><b>Kenya →</b><span>The third regime: failing products already withdrawn; 45 hospitals reach 86.6% — where should adequate stock sit.</span><span class=go>Open the brief</span></a>
</div>
<div class=subnav>
 <a href="ghana-planner.html">Interactive budget planner — Ghana</a>
 <a href="nigeria-planner.html">Interactive budget planner — Nigeria</a>
 <a href="parameter-audit.txt">Parameter provenance audit</a>
 <a href="methods.html">Methods ({VERSION})</a>
</div>

<h2>Four demonstrators, one engine</h2>
<div class=grid3>
 <div class=cty><h3>GHANA · PLACEMENT</h3>
  <div class=big>{GH['optimized']['pct_protected']}%</div>
  <div class=lab>of the carpet-viper burden brought <b>within reach</b> of a species-appropriate antivenom, via {GH['optimized']['hospitals']} hospitals (from ~0% under a failing product)</div>
  <ul><li><b>{GH['optimized']['vials_yr']:,} vials/yr</b> demand forecast (~${GH['optimized']['procure_usd_yr']:,})</li>
      <li>{GH['pct_unreachable']}% of burden beyond ANY hospital — structural gap, shown</li>
      <li>{GH['placement_robustness']['flat_gradient_overlap_of_25']}/25 hospitals stay chosen under a flattened gradient</li></ul>
  <div class=tag>Anchor: Ghana Health Service ~{GH['burden_anchor']['national_cases_reported_yr']:,} bites/yr; model {GH['burden_anchor']['modelled_envenomings_yr']:,} envenomings = conservative floor</div></div>

 <div class=cty><h3>NIGERIA · SCALE</h3>
  <div class=big>{NG['optimized']['pct_protected']}%</div>
  <div class=lab>of the carpet-viper burden within reach via {NG['optimized']['hospitals']} hospitals — the same method against the largest West-African burden</div>
  <ul><li><b>{NG['optimized']['vials_yr']:,} vials/yr</b> (~${NG['optimized']['procure_usd_yr']:,})</li>
      <li>{NG['total_echis_yr']:,} Echis-severe envenomings/yr across {NG['n_lgas']} LGAs</li>
      <li>{NG['placement_robustness']['flat_gradient_overlap']}/{NG['placement_robustness']['of']} hospitals robust to a flattened gradient</li></ul>
  <div class=tag>Anchor: implied {NG['burden_anchor']['implied_national_envenoming_rate_per_100k']}/100k inside the published West-Africa range {NG['burden_anchor']['published_west_africa_rate_range_per_100k'][0]}–{NG['burden_anchor']['published_west_africa_rate_range_per_100k'][1]}/100k</div></div>

 <div class=cty><h3>INDIA · A DIFFERENT REGIME</h3>
  <div class=big>{IN['pct_burden_in_asv_gap']}%</div>
  <div class=lab>of India's snakebite burden sits where the standard ASV <b>likely underperforms</b> — ~{IN['gap_deaths_yr']:,} deaths/yr inside that gap. <b>An ordinal model output, not a measurement</b>: no published national figure exists.</div>
  <ul><li>Burden anchored to the Million Death Study (~{IN['MDS_deaths_yr']:,}/yr)</li>
      <li>Mortality weighted <b>94% rural</b>, per the MDS's own finding</li>
      <li>{IN['n_hospital_tier']:,} hospital-tier facilities; only {IN['pct_far']}% of burden &gt;50 km from one</li></ul>
  <div class=tag>Anchor: modelled {IN['burden_anchor']['modelled_deaths_yr']:,} within {IN['burden_anchor']['within_MDS_pct']}% of MDS, inside GBD UI {IN['burden_anchor']['GBD2019_ui'][0]:,}–{IN['burden_anchor']['GBD2019_ui'][1]:,}</div></div>
</div>

<h2>How it works</h2>
<ol class=steps>
<li><b>Species → district.</b> Which medically important snakes occur where, at eco-zone resolution.</li>
<li><b>The novel core: an evidence-graded coverage matrix.</b> Which product is actually proven to neutralise which species, graded <b>A</b> (WHO risk-benefit-assessed) · <b>B</b> (peer-reviewed preclinical) · <b>C</b> (manufacturer claim) · <b>~</b> (partial/paraspecific) · <b>✗</b> (published evidence AGAINST neutralisation) · <b>–</b> (no activity claimed) · <b>·</b> (no data). Two rules are enforced in code: a manufacturer label is never promoted to "covered", and published evidence of failure overrides every higher grade. Comparable evidence exists as literature; what did not is this cross-tabulation in machine-readable form, keyed to placement.</li>
<li><b>Access.</b> Real facility coordinates and distance to care, so coverage means <i>reachable</i> coverage.</li>
<li><b>Burden, anchored.</b> Population × published incidence/mortality — every country checked against a published national figure before anything else is computed.</li>
<li><b>The decision.</b> A greedy maximal-coverage optimiser returns a named, priority-ordered, costed pre-positioning plan: which hospital, how many vials, what it costs — the demand forecast a stockpile programme needs.</li>
</ol>

<h2>Honest by design — the guardrails, stated up front</h2>
<div class=note><b>We headline coverage, not deaths.</b> Coverage (% of burden within reach of an appropriate product) is what the tool actually controls. Mortality is reported as a <b>bounded decision-gap</b> versus a worst case (an ineffective product everywhere) — explicitly <b>not</b> "extra lives saved versus today", since effective antivenom already reaches some patients. In West Africa it is anchored to a <b>directly observed</b> measurement (case-fatality 1.8% → 12.1% when an ineffective product was substituted in rural Ghana, Visser 2008) rather than a synthetic chain of assumed parameters.</div>
<div class=note><b>We work in the facility frame, and say so.</b> The published incidence figures are <b>hospital attendance rates</b> — patients who already reached care. Outputs are therefore <b>antivenom demand at facilities</b>, not total community burden (which runs ~10× higher). An earlier version treated attendance as community incidence <i>and</i> then applied a care-seeking multiplier — a double discount that understated the vial forecast by roughly half. That is corrected; care-seeking is no longer applied anywhere.</div>
<div class=note><b>We publish what is <i>not</i> sourced.</b> A parameter provenance audit ships with the code (<code>audit_parameters.py</code>): of the load-bearing numbers, it labels each CITED, DERIVED or ASSUMED, and names the three largest exposures — India's ordinal adequacy tiers, Nigeria's constructed zone rates (no published per-zone figure exists), and Ghana's coastal rate (no published figure of any kind). Verification scripts check arithmetic; this audit checks provenance, because the two are different questions.</div>
<div class=note><b>No impact figure may exceed total national mortality.</b> This is enforced in code, not promised in prose: Nigeria's upper bound is capped at the highest published national estimate ({NG['burden_anchor']['deaths_ceiling_used']:,}, GBD 2019 UI upper) and the cap is disclosed wherever it binds. India's coverage-gap is a strict <i>subset</i> of MDS mortality, never an addition to it.</div>
<div class=note><b>Artifacts are disclosed and quantified, not hidden.</b> Urban units inherit their zone's rural incidence, which overstates city burden. In Nigeria we show the consequence and prove it doesn't drive the plan (only {NG['urban_artifact']['pct_vials_to_FCT_or_Lagos']}% of vials go to the FCT or Lagos). In India we fixed it at the source, weighting mortality 94% rural per the Million Death Study.</div>
<div class=note><b>Stock is unobservable subnationally</b> — so CoverMap models placement <b>choices</b>, never a false inventory. Access is straight-line ≤50 km, a documented proxy for travel time. Coverage rests largely on preincubation ED50/antivenomics, not clinical trials — grade B is not proven bedside efficacy. <b>Not clinical guidance.</b></div>

<h2>Verification record</h2>
<p class=muted>Every number in every artifact is re-derived from raw inputs by an independent script that fails loudly on any mismatch. All three pipelines reproduce from data committed in the repository — no network, no temporary files.</p>
<table class='t vtable'><thead><tr><th class=l>Suite</th><th>Checks</th><th>Result</th><th class=l>Covers</th></tr></thead><tbody>
<tr><td class=l>verify_ghana.py</td><td>54</td><td class=ok>PASS</td><td class=l>population vs census, burden re-derivation, optimiser, demand arithmetic, mortality ceiling, artifact consistency, citations</td></tr>
<tr><td class=l>verify_nigeria.py</td><td>62</td><td class=ok>PASS</td><td class=l>reproducibility, scaled population (guards the 550k regression), rates declared a construction, death ceiling, the flagged mortality-gap tension, urban artifact</td></tr>
<tr><td class=l>verify_india.py</td><td>62</td><td class=ok>PASS</td><td class=l>state rates locked to the published MDS table verbatim, exact state populations, 94/6 rural weighting, ordinal-tier disclosure, published sub-national anchors carried</td></tr>
<tr><td class=l>verify_crosscountry.py</td><td>34</td><td class=ok>PASS</td><td class=l>shared parameters identical, honesty invariants hold everywhere, no stale or contradictory numbers</td></tr>
</tbody></table>

<h2>Who it is for</h2>
<p>The <b>WHO Antivenom Stockpile Programme</b> and <b>national NTD programmes</b> — the actors whose remit is exactly "which product, how much, where". The output is deliberately the thing they already have to produce: a costed pre-positioning plan with a demand forecast.</p>

<footer><b>{VERSION_TAG}</b> — {VERSION_NOTE}<br><br>CoverMap · MedInves project · August 2026. Coverage matrix from WHO risk-benefit-assessment product overviews + peer-reviewed preclinical literature. Base layers: <a href="https://www.geoboundaries.org/">geoBoundaries</a> (CC BY 4.0); <a href="https://www.worldpop.org/">WorldPop</a>/afripop2020 (CC BY 4.0); Maina 2019 <i>Sci Data</i> 6:134 (CC BY 4.0 / metadata CC0); Census of India 2011; Ghana Statistical Service 2021 PHC; NIC HealthGIS. Impact anchors: Habib 2015 <i>PLoS NTD</i> 9(1):e0003381 · Habib 2015 <i>PLoS NTD</i> 9(9):e0004088 · Habib 2013 <i>J Venom Anim Toxins</i> 19:27 · Suraweera 2020 <i>eLife</i> 9:e54076 · GBD 2019 via <i>Nat Commun</i> 2022 13:6160 · Visser 2008 <i>TRSTMH</i> 102:445. Feasibility demonstrator — illustrative, not clinical guidance.</footer>
</div></body></html>"""
SITE=BASE if os.path.exists(f"{BASE}/ghana.html") else f"{BASE}/repo"
open(f"{SITE}/index.html","w").write(html)
print("index written:",f"{SITE}/index.html",os.path.getsize(f"{SITE}/index.html"),"bytes")
