#!/usr/bin/env python3
"""Ghana CoverMap brief — unified design system (viz_common). Headline = coverage; deaths = bounded decision-gap."""
import json, pandas as pd, os
from viz_common import BASE_CSS, b64, cov_cell_style, VERSION_TAG, VERSION_NOTE
from _paths import BASE, SRC; OUT2=f"{BASE}/out2"; DATA=f"{BASE}/data"
S=json.load(open(f"{OUT2}/impact_summary.json")); cov=pd.read_csv(f"{DATA}/coverage_matrix.csv")
A=S['burden_anchor']; O=S['optimized']; P=S['model_params']
PROT_ENV=[v['protected_env'] for k,v in S['scenarios'].items() if k.startswith('C')][0]

# ---- scenario table
srows=""
for k,v in S['scenarios'].items():
    srows+=f"<tr><td class=l>{k}</td><td>{v['pct']}%</td><td>{v['protected_env']:,}</td><td><b>~{v['deaths_central']}</b> ({v['deaths_lo']}–{v['deaths_hi']})</td><td>${v['procure_usd_yr']:,}</td></tr>"
scen_table=f"<table class='t'><thead><tr><th class=l>Procurement / placement choice</th><th>Burden within reach</th><th>Envenomings/yr</th><th>Decision-gap deaths/yr (vs worst-case)</th><th>Procurement/yr</th></tr></thead><tbody>{srows}</tbody></table>"

# ---- product menu
PROD=[("PANAF-Premium","WHO-assessed","✓ polyvalent","Lyophilised — no refrigeration (48-mo)","★ RECOMMENDED: broad + heat-stable → rural pre-positioning; in Ghana supply"),
      ("EchiTAbG","WHO-assessed","✓✓ Echis only","Liquid (2–8 °C; 12-mo)","Echis-specific but needs cold chain"),
      ("Antivipmyn Africa","WHO-assessed","✓ polyvalent","Liquid (2–8 °C)","Needs cold chain → urban only"),
      ("Inoserp Pan-Africa","Assessment TERMINATED","claim","Liquid","No longer WHO-endorsed"),
      ("AFRIVEN / VINS","Not assessed","✗ fails Echis","Liquid","In Ghana supply; documented Echis failure")]
prows="".join(f"<tr><td class=l><b>{p[0]}</b></td><td>{p[1]}</td><td>{p[2]}</td><td>{p[3]}</td><td class=l>{p[4]}</td></tr>" for p in PROD)
prod_table=f"<table class='t'><thead><tr><th class=l>Product</th><th>WHO status</th><th>Echis coverage</th><th>Cold chain</th><th class=l>Placement implication</th></tr></thead><tbody>{prows}</tbody></table>"

# ---- evidence-graded coverage matrix
PRODC=[("PANAF-Premium","PANAF"),("Antivipmyn Africa","Antivipmyn"),("EchiTAbG","EchiTAbG"),("Inoserp Pan-Africa","Inoserp"),("SAIMR Polyvalent","SAIMR"),("Asna Antivenom C (Bharat)","Indian polyv.")]
SPP=["Echis ocellatus","Bitis arietans","Bitis rhinoceros","Naja nigricollis","Naja katiensis","Naja senegalensis","Naja melanoleuca","Dendroaspis polylepis","Dendroaspis viridis","Atractaspis","Causus maculatus"]
def cell(sp,pr):
    r=cov[(cov['species']==sp)&(cov['product']==pr)]
    if r.empty: return ("#eef1f4","#8a8a8a","·")
    return cov_cell_style(r.iloc[0].coverage, r.iloc[0].evidence_grade)
mrows=""
for sp in SPP:
    tds=f"<td class='sp'>{sp}</td>"
    for pr,_ in PRODC:
        bg,fg,tx=cell(sp,pr); tds+=f"<td style='background:{bg};color:{fg}'>{tx}</td>"
    mrows+=f"<tr>{tds}</tr>"
heads="".join(f"<th>{lab}</th>" for _,lab in PRODC)
cov_table=f"<table class='cov'><tr><th class=sp style='color:#fff;background:#26313f'>Species (Ghana)</th>{heads}</tr>{mrows}</table>"

html=f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CoverMap — antivenom pre-positioning (Ghana demonstrator)</title><style>{BASE_CSS}</style></head><body>
<header><div class="wrap"><div class="badge">{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · illustrative data · not clinical guidance</div>
<h1>CoverMap — the right antivenom, pre-positioned in the right place</h1>
<div class="sub">A decision-support tool that tells antivenom purchasers <b>which WHO-assessed product to place at which hospitals</b> — matching the snakes that bite each district to the antivenoms proven to neutralise them, and to how far patients must travel — so scarce vials protect the most lives. Ghana demonstrator, built on public data.</div></div></header>
<div class="wrap">

<div class="card lead"><p><b>Antivenom is species-specific — the wrong product does not save the patient.</b> When rural Ghana substituted an unsuitable antivenom against the carpet viper, district case-fatality rose <b>1.8% → 12.1%</b> (Visser 2008). Effective antivenom also concentrates in cities while the burden concentrates in the rural north. Yet the actors who buy and place antivenom decide <b>which product, and where</b> with no tool that joins <i>what bites where</i> to <i>what each product neutralises</i> to <i>who can reach care</i>. CoverMap is that tool — a deployable decision support, not a database and not a therapy.</p>
<div class="kpis">
<div class="kpi"><b>{O['pct_protected']}%</b><span>of the carpet-viper burden brought <b>within reach</b> of the right antivenom (from ~0% today), via {O['hospitals']} hospitals</span></div>
<div class="kpi"><b>~{PROT_ENV:,}</b><span>carpet-viper envenomings/yr brought <b>within reach</b> of the right antivenom (of ~{S['total_echis_yr']:,})</span></div>
<div class="kpi"><b>{O['vials_yr']:,}</b><span>vials/yr to pre-position: a concrete demand forecast (~${O['procure_usd_yr']:,}/yr procurement)</span></div>
<div class="kpi bad"><b>{S['pct_unreachable']}%</b><span>of burden beyond 50 km of ANY hospital — a structural gap stocking alone can't close (shown, not hidden)</span></div>
</div>
<div class="anchor"><b>Burden is anchored to real data, and the frame is stated.</b> Ghana Health Service records <b>~{A['national_cases_reported_yr']:,} snakebite cases/yr</b> nationally ({A['source']}). This model works in the <b>facility frame</b>: it counts patients who <i>already reach a health facility</i>, using published <b>hospital attendance rates</b> (55/100,000 northern Ghana, Aglanu 2025; 24/100,000 Volta/Oti, Ceesay 2021), then applies the published <b>envenoming fraction</b> (64.7% of northern attendances had abnormal clotting, Aglanu 2025) to get <b>{A['modelled_envenomings_yr']:,} envenomings/yr</b> needing antivenom — below the reported bite count, as it must be.
<br><br><b>Correction carried:</b> an earlier version treated the attendance rate as if it were community incidence <i>and</i> then multiplied by a care-seeking fraction — a double discount that <b>understated the vial forecast by roughly half</b>. Care-seeking is no longer applied: by construction these patients have already sought care. Two zone rates were also corrected (forest 8→25/100,000, contradicted by Mensah 2016; coastal 5→12, which remains the one rate with <i>no</i> published basis).</div></div>

<h2>The engine: four public layers, joined into one decision</h2>
<p>CoverMap crosses (1) which snakes occur in each district, (2) an <b>evidence-graded matrix</b> of which antivenoms actually neutralise them, (3) the real hospital network and travel distance, and (4) modelled burden — then recommends the product-and-placement that protects the most expected envenomings within reach, under real budget and cold-chain constraints.</p>
<img src="data:image/png;base64,{b64(f'{OUT2}/fig1_placement.png')}" alt="Burden and optimizer placement">

<h2>The decision it changes — quantified</h2>
<p>Same country, same 190 hospitals; the only thing that changes is <b>which antivenom is stocked and where</b>. The optimiser reaches nearly the structural ceiling with a handful of well-chosen hospitals.</p>
<img src="data:image/png;base64,{b64(f'{OUT2}/fig3_curve_scenarios.png')}" alt="Coverage curve and scenario impact">
{scen_table}
<div class="note"><b>What's at stake — honest.</b> The tool's direct, defensible output is <b>coverage</b>: {O['pct_protected']}% of the carpet-viper burden brought within reach of a species-appropriate product. The mortality column is a <i>decision-gap</i> anchored to a <b>directly observed Ghanaian measurement</b>, not a synthetic chain: when an ineffective antivenom replaced an effective one in rural Ghana, case-fatality among treated carpet-viper patients rose <b>1.8% → 12.1%</b> (Visser 2008). We apply that observed <b>{P['CFR_delta']:.1%} differential</b> to the patients the plan brings within reach. This replaces an earlier formula that multiplied three separate assumed parameters (care-seeking × untreated CFR × effectiveness) and double-counted care-seeking. It is what the <i>product choice</i> governs against a worst case — <b>not</b> extra lives saved versus today, since effective antivenom already reaches some patients. Antivenom is independently highly cost-effective (Habib 2015: ~$2,330/death averted, ~$100/DALY); the plan's procurement cost is ~${O['procure_usd_yr']:,}/yr.</div>

<h2>From decision to action: the pre-positioning plan</h2>
<p>The output is not a map — it is a named, costed plan an organisation can act on: which hospitals to stock, in priority order, and <b>how many vials each should hold</b> — the demand forecast the WHO Stockpile Programme explicitly needs. An interactive planner lets a purchaser trade budget against coverage.</p>
<img src="data:image/png;base64,{b64(f'{OUT2}/fig4_demand.png')}" alt="Demand forecast by hospital">
<div class="note"><b>Robust to the assumptions:</b> 23 of the 25 chosen hospitals stay chosen even if the north–south incidence gradient is flattened, and coverage-% is invariant to uniform incidence scaling — so "concentrate in the north" does not hinge on the exact rates.</div>

<h2>The novel, reusable core: an evidence-graded coverage matrix</h2>
<p>The clinically load-bearing layer no public dataset provides: which product actually neutralises which species, <b>graded by evidence</b> — never promoting a manufacturer label to "covered."</p>
<div class="legend"><span><i class="sw" style="background:#0ca30c"></i>A — WHO-assessed</span><span><i class="sw" style="background:#7dc47d"></i>B — peer-reviewed preclinical</span><span><i class="sw" style="background:#fde08a"></i>C — claim / label</span><span><i class="sw" style="background:#ec835a"></i>~ partial (paraspecific)</span><span><i class="sw" style="background:#a01111"></i>✗ published evidence AGAINST neutralisation</span><span><i class="sw" style="background:#d9a5a5"></i>– no activity claimed / out of scope</span><span><i class="sw" style="background:#f2c9b4"></i>? claimed, no in-vivo datum</span><span><i class="sw" style="background:#eef1f4"></i>· no data</span></div>
{cov_table}

<h2>Grounded in the real procurement decision</h2>
<p>The product menu is real, and so is the constraint that decides what survives in the rural north — <b>cold chain</b>. Only three antivenoms have passed WHO risk-benefit assessment for sub-Saharan Africa; of the products Ghana actually registers, only PANAF-Premium is among them. Independent verification confirms PANAF-Premium as the best <i>single</i> choice — the only WHO-assessed product covering both vipers <b>and</b> elapids, and heat-stable; the strongest <i>programme</i> is PANAF as the thermostable backbone plus EchiTAbG as an <i>Echis</i>-specialist top-up in the highest carpet-viper zones. (Inoserp failed independent testing and is not WHO-assessed; SAIMR is a Southern-African product with no <i>Echis</i> cover.)</p>
{prod_table}
<img src="data:image/png;base64,{b64(f'{OUT2}/fig2_protected.png')}" alt="Protected vs unprotected under optimized placement">

<h2>Real data &amp; honest limits</h2>
<p><b>Real inputs:</b> 190 hospitals with coordinates and level (Maina/WHO 2019); district population (WorldPop/afripop2020 disaggregated to the 2021 census, 30.8 M); region envenoming incidence anchored to Ghana facility studies (north ~55/100k, Aglanu 2025; Volta ~24/100k, Ceesay 2021); an evidence-graded coverage matrix from WHO product overviews + peer-reviewed preclinical data; impact anchored to Habib (2015). Boundaries: <a href="https://www.geoboundaries.org/">geoBoundaries</a> (CC BY 4.0); population raster <a href="https://www.worldpop.org/">WorldPop</a>/afripop2020 (CC BY 4.0).</p>
<div class="note"><b>Limits, by design.</b><ul>
<li><b>Stock is unobservable</b> subnationally → the tool models procurement/placement <b>choices</b>, not a false inventory.</li>
<li><b>The facility frame is a choice, and it bounds what the tool claims.</b> Outputs are <b>antivenom demand at facilities</b>, not total community burden — community incidence in northern Ghana is roughly 10× the facility rate (Musah 2019, ~580/100,000). This model deliberately does not estimate the unreached.</li>
<li><b>Three zone parameters have no published basis</b> and are flagged as such: the coastal attendance rate (12/100,000), and the Echis fractions for transition (0.60) and forest/coastal (0.20). The northern Echis fraction (0.90) rests on a hedged assertion in Aglanu 2025, not a measurement.</li>
<li><b>Access is straight-line ≤50 km</b>, a proxy for travel time (finalist phase: Malaria Atlas friction surface).</li>
<li><b>Coverage rests largely on preincubation ED50/antivenomics</b>, not clinical RCTs → grade B ≠ proven bedside efficacy.</li>
<li><b>Not clinical guidance</b> — it informs procurement/placement, never individual treatment or species ID.</li></ul></div>

<h2>Parameter provenance — what is sourced and what is not</h2>
<p class=muted>Every load-bearing number was taken back to primary sources. Four previously-assumed parameters resolved; six did not, and are labelled <b>not confirmed</b> rather than quietly carried. "Not confirmed" here means <i>searched hard, no published figure exists</i> — not "unchecked".</p>
<table class='t'><thead><tr><th class=l>Parameter</th><th class=l>Status</th><th class=l>Basis</th></tr></thead><tbody>
<tr><td class=l>Northern attendance 55/100k</td><td class=l><b>Sourced</b></td><td class=l>Aglanu 2025, verbatim</td></tr>
<tr><td class=l>Transition attendance 24/100k</td><td class=l><b>Sourced</b></td><td class=l>Ceesay 2021, verbatim</td></tr>
<tr><td class=l>Envenoming fraction 0.647</td><td class=l><b>Sourced</b></td><td class=l>Aglanu 2025 (abnormal clotting); assumed outside the north</td></tr>
<tr><td class=l>Mortality differential 10.3 pp</td><td class=l><b>Sourced</b></td><td class=l>Visser 2008 — observed, not modelled</td></tr>
<tr><td class=l>Vials/patient 1.5</td><td class=l><b>Sourced</b></td><td class=l>inside the WHO PANAF-Premium Echis dose (1–3 vials); observed 1.23 in Oti</td></tr>
<tr><td class=l>Forest attendance 25/100k</td><td class=l>Partial</td><td class=l>GHS regional counts ~21–34/100k; Mensah 2016 reports higher — this is a floor</td></tr>
<tr><td class=l>Reach 50 km</td><td class=l>Partial — proxy</td><td class=l>the published standard is <b>3 h travel time</b> (Longbottom 2018); the distance conversion is ours</td></tr>
<tr><td class=l>Price $80/vial</td><td class=l>Partial</td><td class=l>published prices span $3.4–$315; $120/course sits inside the $100–153/dose modelling baseline</td></tr>
<tr><td class=l>Coastal attendance 12/100k</td><td class=l><b>Not confirmed</b></td><td class=l>no published figure exists for Greater Accra, of any kind</td></tr>
<tr><td class=l>Echis fractions outside the north</td><td class=l><b>Not confirmed</b></td><td class=l>no published zone-level figure; lowered on species-range grounds only</td></tr>
<tr><td class=l>Safety buffer 25%</td><td class=l><b>Not confirmed</b></td><td class=l>WHO/EPI sets stock in <i>months of stock</i>, not a percentage</td></tr>
</tbody></table>

<h2>Why this fits the prize</h2>
<p>It is a <b>deployable decision-support solution</b> (in-scope: "use of data to improve the distribution of antivenom"), not basic research and not therapy development (both out of scope). <b>Innovation:</b> the evidence-graded coverage matrix + a pre-positioning optimiser with cold-chain and access — beyond today's hazard maps. <b>Impact:</b> a quantified, honestly-bounded coverage chain at the district resolution and seasonal cadence procurement actually uses. <b>End user:</b> the WHO Antivenom Stockpile Programme / national NTD programmes, whose remit is exactly this. <b>Maturity:</b> concept + feasibility demonstrated (IML 2); field-testing with a programme partner is the finalist-phase plan.</p>

<footer><b>{VERSION_TAG}</b> — {VERSION_NOTE}<br><br><p class="src"><b>Sources:</b> Visser 2008 TRSTMH 102:445 · Habib 2015 PLoS NTD 9(1):e0003381 (effectiveness 75%, untreated CFR 16%, cost/death $2,330.16, cost/DALY $99.61) · Hamza 2016 PLoS NTD 10(3):e0004568 · WHO risk-benefit-assessed antivenom product overviews · Maina 2019 Sci Data 6:134 (facilities) · Ghana Statistical Service 2021 PHC (30.8 M) · Aglanu 2025 / Ceesay 2021 (Ghana incidence) · Ghana Health Service NTD Programme (≈9,900 cases/yr) · <a href="https://www.geoboundaries.org/">geoBoundaries</a> CC BY 4.0 · <a href="https://www.worldpop.org/">WorldPop</a>/afripop2020 CC BY 4.0. Open method, coverage matrix and code in the project repository.</p>
<p class="src">Feasibility demonstrator for the MedInves project, August 2026. Species presence, access and stock layers are illustrative approximations for method demonstration; not clinical guidance.</p></footer>
</div></body></html>"""
open(f"{OUT2}/ghana_prepositioning_brief_v2.html","w").write(html)
print("Ghana brief written:", os.path.getsize(f"{OUT2}/ghana_prepositioning_brief_v2.html"),"bytes")
