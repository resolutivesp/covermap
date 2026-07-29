#!/usr/bin/env python3
"""India visuals + report — unified CoverMap design system (viz_common).
Headline = ASV coverage-gap; burden anchored to the Million Death Study and rural-weighted per MDS."""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from viz_common import PAL, BASE_CSS, mpl_theme, heat_cmap, b64, VERSION_TAG, VERSION_NOTE
mpl_theme(); WARM=heat_cmap()
from _paths import BASE, SRC; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_in"
INK,SEC,MUT,GRID,BLUE,BLUED=PAL['ink'],PAL['sec'],PAL['mut'],PAL['grid'],PAL['blue'],PAL['blue_d']
TITLE=dict(fontsize=12,weight='bold',color=INK,loc='left')
g=gpd.read_file(f"{OUT}/district_in.geojson"); adm1=gpd.read_file(f"{DATA}/in/ind_ADM1.json")
S=json.load(open(f"{OUT}/impact_summary_in.json")); pri=pd.read_csv(f"{OUT}/priority_districts_in.csv")
A=S['burden_anchor']

# FIG1 — ASV coverage gap (regional pattern)
fig,ax=plt.subplots(figsize=(9,10)); ax.grid(False)
g.plot(column='gap',ax=ax,cmap=WARM,legend=True,edgecolor='white',linewidth=0.15,vmin=0.2,vmax=0.7,
       legend_kwds={'shrink':0.48,'label':'Share of local burden the standard ASV likely does NOT cover'})
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.5); ax.axis('off')
ax.set_title("Where the standard (southern-sourced) ASV likely underperforms\nRegional venom variation (NW desert, NE) + non-Big-Four species — evidence-informed",**TITLE)
ax.text(0.0,-0.012,"Zone-level approximation from antivenomics (Senji Laxme/Sunagar; TRSTMH 2025) — it flags where the standard\nproduct is LIKELY to underperform. It is not a per-patient prediction and not clinical guidance.",
        transform=ax.transAxes,fontsize=8.6,color=SEC,va='top')
plt.savefig(f"{OUT}/fig1_gap_in.png",dpi=130,bbox_inches='tight'); plt.close()

# FIG2 — priority: deaths inside the coverage gap
fig,ax=plt.subplots(figsize=(9,10)); ax.grid(False)
g.plot(column='gap_deaths',ax=ax,cmap=WARM,legend=True,edgecolor='white',linewidth=0.15,
       legend_kwds={'shrink':0.48,'label':'Snakebite deaths/yr inside the ASV coverage-gap (burden × gap)'})
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.5); ax.axis('off')
ax.set_title("Priority districts: real snakebite mortality (Million Death Study) where the\nstandard antivenom likely fails the local snakes",**TITLE)
ax.text(0.0,-0.012,"Mortality is distributed within each state 94% rural / 6% urban, per the Million Death Study's own finding that\n~94% of India's snakebite deaths occur in rural areas — so this reflects rural burden, not city population.",
        transform=ax.transAxes,fontsize=8.6,color=SEC,va='top')
plt.savefig(f"{OUT}/fig2_priority_in.png",dpi=130,bbox_inches='tight'); plt.close()

# FIG3 — top states by gap-deaths
st=g.groupby('cstate')['gap_deaths'].sum().sort_values(ascending=False).head(12).iloc[::-1]
fig,ax=plt.subplots(figsize=(10,6.5)); ax.grid(axis='x')
ax.barh(range(len(st)),st.values,color=BLUE,height=0.72)
ax.set_yticks(range(len(st))); ax.set_yticklabels([s.title() for s in st.index],fontsize=9)
for i,v in enumerate(st.values): ax.text(v+st.max()*0.01,i,f'{v:,.0f}',va='center',fontsize=9,weight='bold',color=INK)
ax.set_xlabel('Snakebite deaths/yr inside the ASV coverage-gap (MDS-anchored)')
ax.set_title('States where region-specific antivenom would help most',**TITLE)
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_states_in.png",dpi=130,bbox_inches='tight'); plt.close()

# ---- REPORT
SC=S['targeting_scenarios']; CONC=S['gap_concentration']
_sr="".join(f"<tr><td class=l>{x['label']}</td><td>{x['districts'] if x['districts'] else '—'}</td>"
            f"<td><b>{x['pct_of_gap']}%</b></td><td>{x['gap_deaths']:,}</td>"
            f"<td>{x['population']/1e6:,.0f}M</td><td class=l>{x['note']}</td></tr>" for x in SC)
SCEN_TABLE=("<table class='t'><thead><tr><th class=l>Targeting choice</th><th>Districts</th>"
  "<th>Coverage-gap reached</th><th>Gap deaths/yr in scope</th><th>Population</th><th class=l>Why this option</th>"
  "</tr></thead><tbody>"+_sr+"</tbody></table>")
_b=[x for x in SC if x['label'].startswith('B')][0]; _d50=[x for x in SC if x['label'].startswith('D')][0]
D50=_d50['pct_of_gap']; B_PCT=_b['pct_of_gap']; SAVED=_b['districts']-_d50['districts']; C100=CONC['100']

prows=""
for _,r in pri.head(20).iterrows():
    gappct=int(round((1-r['adeq'])*100))
    prows+=f"<tr><td class=l>{r['shapeName']}</td><td class=l>{str(r['cstate']).title()}</td><td>{r['deaths_yr']:.0f}</td><td>{gappct}%</td><td>{r['nearest_km']:.0f}</td><td><b>{r['gap_deaths']:.0f}</b></td></tr>"

H=f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>CoverMap India — ASV coverage gap</title><style>{BASE_CSS}</style></head><body>
<header><div class=wrap><div class=badge>{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · illustrative data · not clinical guidance</div>
<h1>CoverMap India — where the standard antivenom fails the local snakes</h1><div class=sub>India carries the world's largest snakebite burden (~58,000 deaths/yr, Million Death Study). Unlike West Africa, the lever is not "which product" — it is that the single southern-sourced polyvalent (ASV) <b>underperforms regionally</b> and misses ~20 non-Big-Four species. This maps where that gap is deadliest.</div></div></header><div class=wrap>

<div class='card'><div class=kpis>
<div class=kpi><b>{S['pct_burden_in_asv_gap']}%</b><span>of India's snakebite burden sits in districts where the standard ASV <b>likely underperforms</b> (regional variation or non-Big-Four species)</span></div>
<div class=kpi><b>~{S['gap_deaths_yr']:,}</b><span>deaths/yr inside that ASV coverage-gap — the target for <b>region-specific antivenom</b> (of ~{S['MDS_deaths_yr']:,} total, MDS)</span></div>
<div class=kpi><b>{S['n_hospital_tier']:,}</b><span>real hospital-tier facilities mapped; only {S['pct_far']}% of burden is &gt;50 km from one — in India, product quality (not access) is the binding gap</span></div>
<div class=kpi><b>{S['population_2011']//1000000:,}M</b><span>people across {len(g):,} districts — burden anchored to real Million Death Study state death rates</span></div></div>
<div class=anchor><b>Mortality is anchored to published national data.</b> Modelled mortality is <b>{A['modelled_deaths_yr']:,}/yr</b> — within <b>{A['within_MDS_pct']}%</b> of the Million Death Study point estimate (~{A['MDS_deaths_yr']:,}), using MDS state death rates <b>transcribed verbatim from the published table</b> (Table 3, 2010–2014) — including its own catch-all rows for the Northeastern states (0.7/100,000) and all other states (3.2/100,000), so <b>no assumed state rate remains</b>. Independent check: the model's implied national rate is {A['implied_national_rate']}/100,000 against Table 3's published All-India row of {A['MDS_national_rate_2010_14']}/100,000, and inside the GBD 2019 uncertainty interval ({A['GBD2019_ui'][0]:,}–{A['GBD2019_ui'][1]:,}). Mortality is distributed within each state <b>{int(A['rural_death_share']*100)}% rural / {int((1-A['rural_death_share'])*100)}% urban</b>, because the MDS itself finds ~94% of India's snakebite deaths occur in rural areas — this leaves every state total unchanged but stops metros from dominating the priority list.</div>

<div class=callout><b>The coverage-gap percentage is a model output, not a measurement — read it as an order of magnitude.</b> <b>No published figure exists</b> for the share of Indian snakebite burden the standard ASV fails to cover, at national or state level. We searched for one specifically; the review paper whose entire thesis is "look beyond the Big Four" (Menon 2025) does not state one, and the national action plan proposes Regional Venom Centres precisely because the data does not exist. Our adequacy values are therefore <b>evidence-informed ordinal tiers</b> ({int(A['adeq_tiers']['NW']*100)}% NW · {int(A['adeq_tiers']['NE']*100)}% NE · {int(A['adeq_tiers']['ANDAMAN']*100)}% Andamans · {int(A['adeq_tiers']['MAINLAND']*100)}% rest of mainland · {int(A['adeq_tiers']['SOUTH']*100)}% southern sourcing zone), not measured fractions. An adversarial review of the antivenomics literature confirmed the <b>direction</b> of every tier and supported <b>no precise level</b>; the error sign of the {S['pct_burden_in_asv_gap']}% is unknown. We report it because the ranking is decision-useful, and we refuse to imply precision it does not have.</div>

<div class=note><b>What IS published and hard — the anchors that carry this case:</b><ul>
{''.join(f"<li><b>{a['value']}</b> — {a['what']} <span class=src>({a['source']})</span></li>" for a in A['published_subnational_anchors'])}
</ul>These are attributable, sub-national and independent of our model. They are the strongest evidence that the gap is real; the map's job is to say <i>where</i> it concentrates, not to restate them.</div></div>

<h2>The regional pattern: a southern-sourced antivenom can't cover pan-India venom</h2>
<p class=muted>Indian ASV is raised on southern (Tamil Nadu/Irula) venoms. Published antivenomics shows: against the <b>Rajasthan desert cobra</b> the antivenom was <b>completely ineffective</b> — the highest dose tested failed to protect (Senji Laxme 2021); against <b>Punjab Russell's viper</b> it neutralised at <b>0.39 mg/ml versus 0.84–0.99 mg/ml for every other Indian population tested</b>, against a marketed claim of 0.60 (Senji Laxme 2021); and it has no label coverage at all for green pit vipers, <i>Hypnale</i>, sea snakes or <i>Bungarus niger</i>. Darker = larger uncovered share.</p>
<p class=muted><b>Correction:</b> an earlier draft compressed the Punjab result to "−35%", which is ambiguous — that is the shortfall against the <i>marketed claim</i>, whereas the shortfall against <i>other Indian populations</i> is 56–61%. The figures above are stated in full instead.</p>
<img src="data:image/png;base64,{b64(f'{OUT}/fig1_gap_in.png')}">

<h2>Where the gap is deadliest (real mortality × gap)</h2>
<img src="data:image/png;base64,{b64(f'{OUT}/fig2_priority_in.png')}">
<img src="data:image/png;base64,{b64(f'{OUT}/fig3_states_in.png')}">

<h2>Priority districts — where region-specific antivenom + stocking would help most</h2>
<table class='t'><thead><tr><th class=l>District</th><th class=l>State</th><th>Deaths/yr</th><th>ASV gap</th><th>km to hospital</th><th>Gap deaths/yr</th></tr></thead><tbody>{prows}</tbody></table>

<h2>The decision it changes — quantified</h2>
<p class=muted>India has no product-placement optimiser: access is not the binding gap here (under 1% of burden sits more than 50 km from a hospital). The decision this tool informs is different. Region-specific antivenom, and the Regional Venom Centres India's national action plan proposes, have to be rolled out <b>somewhere first</b>. This is what each choice reaches.</p>
{SCEN_TABLE}
<p class=src>Each row reports the share of the coverage-gap burden that <b>sits in</b> the districts targeted — a <b>reach</b> measure, exactly parallel to "within reach" in the West-African demonstrators. It is <b>not</b> a claim that deploying there averts those deaths, and it inherits the ordinal uncertainty of the adequacy tiers above.</p>

<div class=note><b>Two things this table says — one encouraging, one not.</b>
<br><br><b>Targeting beats geography.</b> The tool's top <b>50</b> districts reach {D50}% of the coverage-gap burden; targeting all <b>133</b> districts of the northwest reaches {B_PCT}%. Roughly the same reach for <b>{SAVED} fewer districts</b>, because the ranking crosses state lines to follow burden × gap rather than administrative boundaries. For a programme deciding where to site the first Regional Venom Centres, that is the practical output.
<br><br><b>But India has no small-set solution, and we will not pretend otherwise.</b> The top 100 of 734 districts reach only {C100}% of the gap; you need about <b>300 districts to pass three-quarters</b>. Compare Ghana, where 25 hospitals bring 86% of the carpet-viper burden within reach. India's burden is genuinely diffuse across a vast rural population, so a pilot in a handful of districts <b>will not move the national figure</b>. That points the strategy at the <b>product side</b> — getting region-appropriate antivenom into the national supply — with siting as the sequencing question, not the solution.</div>

<div class=note><b>What's at stake — honest.</b> This is a <b>coverage-gap map</b>, and we do <b>not</b> claim deaths averted. Burden is real (Million Death Study state death rates × 2011 census district population, rural-weighted; national {A['modelled_deaths_yr']:,} vs MDS ~{A['MDS_deaths_yr']:,}). The <b>ASV coverage-gap is an evidence-informed zone approximation</b> (Senji Laxme &amp; Sunagar antivenomics 2019/2021; TRSTMH 2025) — it flags where the standard antivenom is <i>likely</i> to underperform, not a per-patient prediction. The output is a target list for <b>region-specific antivenoms</b> and stocking, not a placement of one product.</div>

<div class=callout><b>Correction carried prominently.</b> An earlier draft of this work stated that no South-Asian antivenom products had been WHO risk-benefit-assessed. <b>That was wrong:</b> seven are (Bharat, Biological E ×2, Haffkine, Premium ×2, VINS). We correct it here rather than quietly drop it. The finding survives the correction, because it never depended on it: WHO assessment covers the <b>Big-Four label</b>, and does not certify performance against <b>regional venom variation</b> within those four species, nor against the ~20 medically important <b>non-Big-Four</b> species. That distinction is the whole point of this map.</div>

<div class=note><b>Limits, by design.</b> District population join matched {S['district_pop_match_rate_pct']}% by name (unmatched districts are filled to their state's average so <b>state totals stay exact</b>). The hospital layer (NIC HealthGIS, hospital-tier: district/taluka hospitals + CHCs) covers {S['states_with_hospitals']} of 36 states — access is <b>under-counted</b> where facilities are missing, so the {S['pct_far']}% "far from care" figure is a floor, not a ceiling. Coverage-gap fractions are <b>state-level ordinal tiers, not district-specific measurements</b>. A known tension we do not paper over: the tiers imply a "distance from the southern sourcing zone" gradient, but the underlying data does not have that shape — the antivenom met its marketed claim against the spectacled cobra in only one tested population (Andhra Pradesh), and performed as poorly in the Gangetic belt as in the northwest. The mainland tier survives only because Russell's viper and the saw-scaled viper, which dominate mortality there, <i>are</i> well covered. That is the model's reasoning, not a measurement. Rural weighting uses the census rural/urban household split as a proxy for the population split. Not clinical guidance.</div>

<h2>Parameter provenance — what is sourced and what is not</h2>
<p class=muted>"Not confirmed" below means <i>searched hard, no published figure exists</i> — not "unchecked".</p>
<table class='t'><thead><tr><th class=l>Parameter</th><th class=l>Status</th><th class=l>Basis</th></tr></thead><tbody>
<tr><td class=l>State death rates (18 states)</td><td class=l><b>Sourced</b></td><td class=l>MDS Table 3, column 2010–2014, <b>transcribed verbatim</b> and locked by a verification check</td></tr>
<tr><td class=l>Catch-all state rates</td><td class=l><b>Sourced</b></td><td class=l>Table 3's own rows: "Northeastern states" 0.7 · "All other states" 3.2 — <b>no assumed state rate remains</b></td></tr>
<tr><td class=l>Rural death share 94%</td><td class=l><b>Sourced</b></td><td class=l>Suraweera 2020: "about 94% of snakebite deaths occurred in rural areas"</td></tr>
<tr><td class=l>National cross-check</td><td class=l><b>Sourced</b></td><td class=l>model implies 4.6/100,000 against Table 3's published All-India row of 4.5/100,000</td></tr>
<tr><td class=l>Reach 50 km</td><td class=l>Partial — proxy</td><td class=l>published standard is <b>3 h travel time</b> (Longbottom 2018); the distance conversion is ours</td></tr>
<tr><td class=l><b>ASV adequacy tiers</b></td><td class=l><b>Not confirmed</b></td><td class=l><b>no published national or state coverage-gap figure exists.</b> Direction of every tier is evidenced; no precise level is. <b>The headline is a direct function of these — error sign unknown.</b></td></tr>
<tr><td class=l>Facility layer coverage</td><td class=l>Partial</td><td class=l>NIC HealthGIS covers 25 of 36 states → the "far from care" figure is a floor, not a ceiling</td></tr>
</tbody></table>

<footer><b>{VERSION_TAG}</b> — {VERSION_NOTE}<br><br>Boundaries <a href="https://www.geoboundaries.org/">geoBoundaries</a> (CC BY 4.0); population Census of India 2011; facilities NIC HealthGIS (hospital-tier {S['n_hospital_tier']:,}); burden Suraweera 2020 <i>eLife</i> 9:e54076 (Million Death Study, ~58,000/yr; ~94% rural; 77% out-of-hospital) + GBD 2019 via <i>Nat Commun</i> 2022 13:6160 (India 51,100; UI 29,600–64,100); coverage Senji Laxme/Sunagar antivenomics + TRSTMH 2025. Feasibility demonstrator — illustrative, not clinical guidance.</footer></div></body></html>"""
open(f"{OUT}/india_coverage_gap_brief.html","w").write(H)
print("India outputs:",[f for f in os.listdir(OUT) if f.endswith(('.png','.html'))])
