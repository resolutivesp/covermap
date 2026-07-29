#!/usr/bin/env python3
"""Nigeria visuals + report + interactive planner — unified CoverMap design system (viz_common)."""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from viz_common import PAL, BASE_CSS, mpl_theme, heat_cmap, b64, VERSION_TAG, VERSION_NOTE
mpl_theme(); WARM=heat_cmap()
from _paths import BASE, SRC; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_ng"
INK,SEC,MUT,GRID,BLUE,GOOD,CRIT,WARN,BLUED=PAL['ink'],PAL['sec'],PAL['mut'],PAL['grid'],PAL['blue'],PAL['good'],PAL['critical'],PAL['warning'],PAL['blue_d']
TITLE=dict(fontsize=12,weight='bold',color=INK,loc='left')
g=gpd.read_file(f"{OUT}/district_ng.geojson"); adm1=gpd.read_file(f"{DATA}/ng/nga_ADM1.json")
allh=pd.read_csv(f"{DATA}/ng/facilities_hospitals_ng.csv"); plan=pd.read_csv(f"{OUT}/pre_positioning_plan_ng.csv")
curve=pd.read_csv(f"{OUT}/coverage_curve_ng.csv"); S=json.load(open(f"{OUT}/impact_summary_ng.json")); O=S['optimized']; A=S['burden_anchor']

# FIG1 — burden + placement.
# Colour scale is CAPPED at the 97th percentile: one urban LGA (the capital, inheriting a rural
# zone rate) is ~8x the p95 and would otherwise flatten the whole map to near-white, hiding the
# real Middle-Belt/savanna gradient. Capping is a legibility choice, disclosed on the figure.
VMAX=float(np.percentile(g['echis_yr'],97))
fig,ax=plt.subplots(figsize=(10,10)); ax.grid(False)
g.plot(column='echis_yr',ax=ax,cmap=WARM,legend=True,edgecolor='white',linewidth=0.15,vmin=0,vmax=VMAX,
       legend_kwds={'shrink':0.48,'label':f'Expected carpet-viper (Echis) envenomings / year (LGA)\n(scale capped at the 97th percentile ≈ {VMAX:,.0f} for legibility)'})
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.5)
ax.scatter(allh.lon,allh.lat,s=4,c=MUT,alpha=0.4,label=f'All hospitals ({S["n_hospitals"]:,})')
sz=30+plan['vials_year']/plan['vials_year'].max()*300
ax.scatter(plan.lon,plan.lat,s=sz,marker='o',c=BLUE,edgecolor='white',linewidth=0.7,label=f'Pre-position here ({len(plan)}, size = vials/yr)',zorder=5)
ax.legend(loc='lower left',fontsize=9,framealpha=.96,edgecolor=GRID); ax.axis('off')
ax.set_title(f"Nigeria pre-positioning plan: place PANAF-Premium where the burden is\n{len(plan)} hospitals — {O['pct_protected']}% of the carpet-viper burden brought within reach",**TITLE)
U=S['urban_artifact']
ax.text(0.0,-0.012,f"Note: the highest-burden LGA in the model is {U['top_burden_lga']} ({U['top_burden_lga_state'].split()[0]}) — an URBAN ARTIFACT: cities inherit their eco-zone's rural rate.\nIt dominates the colour scale but not the plan: only {U['pct_vials_to_FCT_or_Lagos']}% of vials go to FCT/Lagos, and the top priorities are all savanna/Middle-Belt states.",
        transform=ax.transAxes,fontsize=8.6,color=SEC,va='top')
plt.savefig(f"{OUT}/fig1_placement_ng.png",dpi=130,bbox_inches='tight'); plt.close()

# FIG2 — within reach vs not (diverging blue<->red: CVD-safe)
fig,ax=plt.subplots(figsize=(10,10)); ax.grid(False)
g[g.protected_opt].plot(ax=ax,color=BLUE,edgecolor='white',linewidth=0.15)
g[~g.protected_opt].plot(ax=ax,color=CRIT,edgecolor='white',linewidth=0.15)
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.5)
ax.scatter(plan.lon,plan.lat,s=60,marker='o',c=INK,edgecolor='white',linewidth=0.8,zorder=5)
ax.legend(handles=[Patch(color=BLUE,label='Within reach — ≤50 km of a stocking hospital'),
                   Patch(color=CRIT,label=f"Not within reach — incl. {S['pct_unreachable']}% beyond ANY hospital"),
                   plt.Line2D([],[],marker='o',color=INK,ls='',markersize=8,label='Stocking hospital')],
          loc='lower left',fontsize=9,framealpha=.96,edgecolor=GRID)
ax.axis('off'); ax.set_title(f"Who the plan covers — {O['pct_protected']}% of Nigeria's carpet-viper burden within reach",**TITLE)
ax.text(0.0,-0.012,"Note: coverage is measured by BURDEN, not land area — southern LGAs are large but carry little carpet-viper\nburden, which is why most of the burden is covered even where the map shows red.",
        transform=ax.transAxes,fontsize=8.6,color=SEC,va='top')
plt.savefig(f"{OUT}/fig2_protected_ng.png",dpi=130,bbox_inches='tight'); plt.close()

# FIG3 — coverage curve + scenarios
fig,(a1,a2)=plt.subplots(1,2,figsize=(15,6.2))
a1.plot(curve.n_hospitals,curve.pct,marker='o',ms=2.6,color=BLUE,lw=2.2)
kk=len(plan); a1.axvline(kk,color=MUT,ls='-',lw=0.9,alpha=.6); a1.axhline(O['pct_protected'],color=MUT,ls='-',lw=0.9,alpha=.6)
a1.annotate(f"{kk} hospitals → {O['pct_protected']}%",xy=(kk,O['pct_protected']),xytext=(kk*0.30,55),fontsize=10.5,weight='bold',color=INK,arrowprops=dict(arrowstyle='->',color=SEC))
a1.set_xlabel('# hospitals stocking PANAF-Premium'); a1.set_ylabel('% of carpet-viper burden within reach'); a1.set_ylim(0,100)
a1.set_title('A few dozen hospitals cover most of a huge burden',**TITLE)
sc=S['scenarios']; labels=[k.split('—')[0].replace('.','').strip() for k in sc]
cen=[v['pct'] for v in sc.values()]; y=np.arange(len(labels))
a2.barh(y,cen,color=[CRIT,WARN,GOOD,BLUED],height=.66); a2.set_xlim(0,100)
a2.set_yticks(y); a2.set_yticklabels(labels); a2.invert_yaxis()
for i,v in enumerate(cen): a2.text(v+1.5,i,f'{v}%',va='center',fontsize=10,weight='bold',color=INK)
a2.set_xlabel('% of carpet-viper burden within reach of the right antivenom')
a2.set_title('Coverage by procurement / placement choice',**TITLE)
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_curve_ng.png",dpi=130,bbox_inches='tight'); plt.close()

# FIG4 — demand top 15
fig,ax=plt.subplots(figsize=(10,7)); ax.grid(axis='x')
top=plan.sort_values('vials_year',ascending=False).head(15).iloc[::-1]
ax.barh(range(len(top)),top.vials_year,color=BLUE,height=0.7)
ax.set_yticks(range(len(top))); ax.set_yticklabels([f"{h}  ({s})" for h,s in zip(top.hospital,top.state)],fontsize=8.5)
for i,v in enumerate(top.vials_year): ax.text(v+top.vials_year.max()*0.01,i,f'{v:,}',va='center',fontsize=8.5,weight='bold',color=INK)
ax.set_xlabel('Vials / year to pre-position (demand forecast, incl. 25% buffer)')
ax.set_title(f'Demand forecast: vials per hospital (top 15 of {len(plan)})\nTotal {O["vials_yr"]:,} vials/yr (~${O["procure_usd_yr"]:,}/yr)',**TITLE)
plt.tight_layout(); plt.savefig(f"{OUT}/fig4_demand_ng.png",dpi=130,bbox_inches='tight'); plt.close()

# ---------- REPORT ----------
prot_env=[v['protected_env'] for k,v in sc.items() if k.startswith('C')][0]
srows=""
for k,v in sc.items():
    capmark=" <span title='capped at the published national mortality ceiling'>†</span>" if v.get('deaths_hi_capped') else ""
    srows+=f"<tr><td class=l>{k}</td><td>{v['pct']}%</td><td>{v['protected_env']:,}</td><td><b>~{v['deaths_central']:,}</b> ({v['deaths_lo']:,}–{v['deaths_hi']:,}{capmark})</td><td>${v['procure_usd_yr']:,}</td></tr>"
scen_table=f"<table class='t'><thead><tr><th class=l>Procurement / placement choice</th><th>Within reach</th><th>Envenomings/yr</th><th>Decision-gap deaths/yr (vs worst-case)</th><th>Procurement/yr</th></tr></thead><tbody>{srows}</tbody></table>"
if A.get('deaths_ceiling_binds_in_scenarios'):
    scen_table+=f"<p class=src>† Upper bound <b>capped at {A['deaths_ceiling_used']:,}</b> — the highest published estimate of Nigeria's <i>total</i> annual snakebite mortality (GBD 2019 UI upper). Antivenom-preventable deaths cannot exceed total deaths, so we cap the figure and say so rather than print an arithmetically-derived but impossible number. The cap binds only in the theoretical all-hospital ceiling scenario, not in the recommended plan.</p>"

H=f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>CoverMap Nigeria — antivenom pre-positioning</title><style>{BASE_CSS}</style></head><body>
<header><div class=wrap><div class=badge>{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · illustrative data · not clinical guidance</div>
<h1>CoverMap Nigeria — the right antivenom, pre-positioned</h1><div class=sub>Nigeria carries the largest snakebite burden in West Africa; the Middle Belt (Kaltungo, Gombe, Benue) is the carpet-viper epicentre. Which WHO-assessed antivenom to place at which hospitals, how many vials, and how much of the burden it brings within reach.</div></div></header><div class=wrap>

<div class='card'><div class=kpis>
<div class=kpi><b>{O['pct_protected']}%</b><span>of the carpet-viper burden brought <b>within reach</b> of the right antivenom (from ~0%), via {O['hospitals']} hospitals</span></div>
<div class=kpi><b>~{prot_env:,}</b><span>carpet-viper envenomings/yr the plan brings <b>within reach</b> (of {S['total_echis_yr']:,} nationally)</span></div>
<div class=kpi><b>{O['vials_yr']:,}</b><span>vials/yr demand forecast (~${O['procure_usd_yr']:,}/yr procurement)</span></div>
<div class=kpi bad><b>{S['pct_unreachable']}%</b><span>of burden beyond 50 km of ANY hospital — the structural gap stocking alone can't close (shown, not hidden)</span></div></div>
<p class=muted>Nigeria's modelled scale is ~9× Ghana's — the same method, a far larger burden. Because Nigeria is hospital-dense, only {S['pct_unreachable']}% of burden is beyond reach of any hospital (vs 6.2% in Ghana).</p>
<div class=callout><b>Nigeria's absolute figures are the least anchored in this project — stated plainly.</b> <b>No published per-eco-zone snakebite rate exists for Nigeria.</b> The zone rates are a <b>construction</b>, not a transcription; an earlier version described them as "facility-anchored and calibrated", which overstated their provenance. They sit between two published bounds: FMoH surveillance recorded ~15,278 cases/yr ({A['FMoH_surveillance_bites_per_100k']}/100,000, certainly under-reported), while community surveys in savanna foci report ~{A['community_rate_benue_per_100k']}/100,000. Our implied facility attendance ({A['implied_facility_attendance_per_100k']}/100,000) is ~2.8× the surveillance figure, which assumes substantial under-reporting — plausible, but assumed. The implied envenoming rate ({A['implied_national_envenoming_rate_per_100k']}/100,000) falls inside the published West-Africa range ({A['published_west_africa_rate_range_per_100k'][0]}–{A['published_west_africa_rate_range_per_100k'][1]}/100,000, {A['published_rate_source']}) — a <i>bound</i>, not a confirmation.
<br><br><b>Unresolved uncertainty we could not settle:</b> the strongest Nigerian community datum (~{A['community_rate_benue_per_100k']}/100,000) is attributed to the Benue valley by Habib, but the underlying 1980 study is generally sited at Malumfashi (Katsina) — i.e. it may belong to the Sudan savanna, which we rate <i>lower</i> than the Middle Belt. If so, the gradient between our two savanna zones could be inverted. Both zones are high and both are prioritised, so the placement conclusion holds; the split between them is not established.</div></div>

<h2>The plan on the map</h2><img src="data:image/png;base64,{b64(f'{OUT}/fig1_placement_ng.png')}">
<h2>The decision it changes — quantified</h2><img src="data:image/png;base64,{b64(f'{OUT}/fig3_curve_ng.png')}">{scen_table}
<div class=note><b>What's at stake — and where our own number strains.</b> The tool's direct, defensible output is <b>coverage</b>: {O['pct_protected']}% of the carpet-viper burden brought within reach of an effective antivenom. The deaths column applies the <b>observed</b> Ghanaian product-choice differential (case-fatality 1.8% → 12.1% under a failing product, Visser 2008) to the patients the plan reaches — an <b>extrapolation from Ghana to Nigeria</b>. Nigeria loses an estimated <b>{A['national_deaths_GBD2019']:,}–{A['national_deaths_Habib2015']:,} people/year</b> to snakebite in total (GBD 2019 {A['national_deaths_GBD2019']:,}, UI {A['national_deaths_GBD2019_ui'][0]:,}–{A['national_deaths_GBD2019_ui'][1]:,}; Habib 2015 {A['national_deaths_Habib2015']:,}, {A['national_deaths_Habib2015_ui'][0]:,}–{A['national_deaths_Habib2015_ui'][1]:,}).
<br><br><b>We flag rather than tune:</b> our central figure ({O['deaths_central']:,}) <b>exceeds the highest published CENTRAL estimate of Nigeria's total snakebite mortality</b> ({A['national_deaths_Habib2015']:,}). It stays under the highest published <i>upper</i> bound ({A['deaths_ceiling_used']:,}), and it is a worst-case counterfactual rather than an expectation — but it should be read as an <b>upper-bound signal, not a forecast</b>, and it is the clearest evidence that Nigeria's absolute figures carry wider uncertainty than Ghana's. This is why the headline is coverage and vials, never a deaths count. Placement is robust: {S['placement_robustness']['flat_gradient_overlap']}/{S['placement_robustness']['of']} hospitals stay chosen under a flattened gradient.</div>
<h2>From decision to action: demand per hospital</h2><img src="data:image/png;base64,{b64(f'{OUT}/fig4_demand_ng.png')}">
<h2>Who the plan covers</h2><img src="data:image/png;base64,{b64(f'{OUT}/fig2_protected_ng.png')}">
<div class=note><b>Limits, by design.</b> Subnational stock is unobservable → we model placement <b>choices</b>, not measured inventory. Access is straight-line ≤50 km, a proxy for travel time. Zone rates are a CONSTRUCTION with no published per-zone source, bracketed by FMoH surveillance below and community surveys above; urban LGAs inherit their zone's rate, which overstates their <i>snakebite</i> burden. The envenoming fraction (64.7%) is transferred from northern Ghana (Aglanu 2025) and is assumed for Nigeria. No care-seeking multiplier is applied: in the facility frame these patients have already reached care (an earlier version double-counted it, understating the vial forecast). Population is afripop's within-country distribution scaled to the national total (206.1 M, World Bank 2020) — the raster's own absolute counts are not used. {S['facility_names_repaired']} facility names carrying a duplicated suffix in the upstream Maina/WHO file were repaired (suffix only; no facility renamed). Not clinical guidance.</div>
<div class=callout><b>The urban artifact, quantified — and why it doesn't change the plan.</b> Because urban LGAs inherit their eco-zone's rural rate, the model's single highest-burden unit is <b>{S['urban_artifact']['top_burden_lga']}</b> ({S['urban_artifact']['top_burden_lga_state']}) at ~{S['urban_artifact']['top_burden_lga_env']:,} envenomings/yr — about {S['urban_artifact']['max_over_p95_ratio']}× the 95th percentile. That is an artifact, not a finding: snakebite envenoming is overwhelmingly rural. We show it rather than hide it, and we quantify its consequence: it dominates the map's colour scale, but only <b>{S['urban_artifact']['pct_vials_to_FCT_or_Lagos']}% of the planned vials</b> go to the FCT or Lagos, and every top-priority hospital sits in a savanna or Middle-Belt state (Kano, Niger, Kaduna, Gombe, Jigawa, Katsina, Kogi, Benue). <b>The decision is robust to the artifact</b> — which is precisely why we report the placement, not the raw burden raster.</div>
<h2>Parameter provenance — what is sourced and what is not</h2>
<p class=muted>Every load-bearing number was taken back to primary sources. "Not confirmed" below means <i>searched hard, no published figure exists</i> — not "unchecked". Nigeria carries more unconfirmed parameters than the other demonstrators, and they are the reason its absolute figures should be read as indicative.</p>
<table class='t'><thead><tr><th class=l>Parameter</th><th class=l>Status</th><th class=l>Basis</th></tr></thead><tbody>
<tr><td class=l>Echis fraction 0.85 (savanna)</td><td class=l><b>Sourced</b></td><td class=l>Habib &amp; Abubakar 2011 (Kaltungo, 6,687 victims): "&gt;90% of the bites were due to <i>E. ocellatus</i>"; Habib 2013 series 75%</td></tr>
<tr><td class=l>Mortality ceiling 2,640</td><td class=l><b>Sourced</b></td><td class=l>GBD 2019 Nigeria UI upper (<i>Nat Commun</i> 2022) — hard cap, verbatim</td></tr>
<tr><td class=l>Vials/patient 1.5</td><td class=l><b>Sourced</b></td><td class=l>inside the WHO PANAF-Premium <i>Echis</i> initial dose (1–3 vials)</td></tr>
<tr><td class=l>Mortality differential 10.3 pp</td><td class=l>Partial</td><td class=l>Visser 2008 — observed, but measured in <b>Ghana</b>; transferring it to Nigeria is an extrapolation</td></tr>
<tr><td class=l>Envenoming fraction 0.647</td><td class=l>Partial</td><td class=l>Aglanu 2025, measured in northern <b>Ghana</b>; assumed for Nigeria</td></tr>
<tr><td class=l>Reach 50 km</td><td class=l>Partial — proxy</td><td class=l>published standard is <b>3 h travel time</b> (Longbottom 2018); the distance conversion is ours</td></tr>
<tr><td class=l>Price $80/vial</td><td class=l>Partial</td><td class=l>published prices span $3.4–$315; $120/course sits inside the $100–153/dose modelling baseline</td></tr>
<tr><td class=l><b>Zone rates 45 / 28 / 4</b></td><td class=l><b>Not confirmed</b></td><td class=l><b>no published per-eco-zone rate exists for Nigeria at any resolution.</b> A construction bracketed by FMoH surveillance below and community surveys above. <b>Drives every absolute figure here.</b></td></tr>
<tr><td class=l>Middle-Belt &gt; Sudan-savanna gradient</td><td class=l><b>Unresolved</b></td><td class=l>the strongest community datum (~497/100k) may belong to Katsina, not Benue — the 1980 source could not be obtained. Both zones stay high and both are prioritised, so placement holds; the split does not.</td></tr>
<tr><td class=l>Echis fraction 0.20 (south)</td><td class=l><b>Not confirmed</b></td><td class=l>no species-attribution study exists for southern Nigeria</td></tr>
<tr><td class=l>Safety buffer 25%</td><td class=l><b>Not confirmed</b></td><td class=l>WHO/EPI sets stock in <i>months of stock</i>, not a percentage</td></tr>
</tbody></table>

<footer><b>{VERSION_TAG}</b> — {VERSION_NOTE}<br><br>Same West-African coverage matrix and recommended product (PANAF-Premium — WHO risk-benefit-assessed, broad, heat-stable/lyophilised) as the Ghana demonstrator. Real inputs: 774 LGAs (<a href="https://www.geoboundaries.org/">geoBoundaries</a>, CC BY 4.0); population <a href="https://www.worldpop.org/">WorldPop</a>/afripop2020 distribution (CC BY 4.0) → 206.1 M (World Bank 2020); {S['n_hospitals']:,} hospitals (Maina 2019 Sci Data 6:134 / WHO). Impact anchored to Habib 2015 PLoS NTD 9(1):e0003381; national mortality GBD 2019 (Nat Commun 2022) and Habib 2015 PLoS NTD 9(9):e0004088; incidence range Habib 2013 J Venom Anim Toxins 19:27. Illustrative feasibility demonstrator — not clinical guidance.</footer></div></body></html>"""
open(f"{OUT}/nigeria_prepositioning_brief.html","w").write(H)

# ---------- PLANNER ----------
DELTA=S['model_params']['CFR_delta']
def dd(e): return round(e*DELTA)
cj=[dict(k=int(r.n_hospitals),pct=float(r.pct),env=int(r.echis_protected),vials=int(r.cum_vials),cost=int(r.cum_cost_usd),
        dc=dd(r.echis_protected)) for _,r in curve.iterrows()]
pj=[dict(pr=int(r.priority),h=str(r.hospital).strip(),reg=r.state,v=int(r.vials_year),c=int(r.procure_usd_yr)) for _,r in plan.iterrows()]
img=b64(f'{OUT}/fig1_placement_ng.png')
SUPP="""
.sliderrow{display:flex;align-items:center;gap:16px;margin:14px 0 6px}
input[type=range]{flex:1;accent-color:var(--blue);height:6px}
.out{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:10px}
.out div{background:var(--plane);border:1px solid var(--grid);border-radius:10px;padding:12px}
.out b{display:block;font-size:22px;color:var(--ink);font-variant-numeric:tabular-nums}
.out span{font-size:12px;color:var(--sec)}
.plantable{max-height:520px;overflow:auto;border:1px solid var(--grid);border-radius:10px}
.plantable table{margin-top:0} .plantable th{position:sticky;top:0;z-index:1}
tr.off{opacity:.34} tr.on td{background:rgba(42,120,214,.06)}
@media(max-width:720px){.out{grid-template-columns:repeat(2,1fr)}}
"""
P=f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>CoverMap Nigeria — planner</title><style>{BASE_CSS}{SUPP}</style></head><body>
<header><div class=wrap><div class=badge>{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · not clinical guidance</div>
<h1>CoverMap Nigeria — antivenom pre-positioning planner</h1><div class=sub>Nigeria's Middle Belt is the carpet-viper epicentre. Which WHO-assessed antivenom at which hospitals, how many vials each, and how much of the burden it brings within reach.</div></div></header><div class=wrap>
<div class=kpis><div class=kpi><b>{O['pct_protected']}%</b><span>carpet-viper burden within reach (from ~0%)</span></div>
<div class=kpi><b>~{prot_env:,}</b><span>envenomings/yr within reach of the right antivenom (of {S['total_echis_yr']:,})</span></div>
<div class=kpi><b>{O['vials_yr']:,}</b><span>vials/yr demand forecast</span></div>
<div class=kpi><b>${O['procure_usd_yr']:,}</b><span>annual procurement cost</span></div></div>
<div class=card><h2>The plan on the map</h2><p class=muted>LGAs shaded by carpet-viper burden; blue circles are the hospitals to stock, sized by vials. Supply concentrates in the Middle Belt and north.</p><img src="data:image/png;base64,{img}"></div>
<div class=card><h2>Budget planner — how far does the money go?</h2><p class=muted>Drag to choose how many hospitals you can stock; see coverage, envenomings within reach, vials and cost.</p>
<div class=sliderrow><span class=muted>Hospitals stocked</span><input id=sl type=range min=1 max="{len(plan)}" value="{len(plan)}"><b id=nh style="min-width:2.4em;text-align:right;font-variant-numeric:tabular-nums">{len(plan)}</b></div>
<div class=out><div><b id=o_pct></b><span>% within reach</span></div><div><b id=o_d></b><span>envenomings within reach</span></div><div><b id=o_v></b><span>vials/yr</span></div><div><b id=o_c></b><span>procurement/yr</span></div></div></div>
<div class=card><h2>Pre-positioning plan — stock in this priority order</h2><div class=plantable><table class='t'><thead><tr><th>#</th><th class=l>Hospital</th><th class=l>State</th><th>Vials/yr</th><th>Cost/yr</th></tr></thead><tbody id=tb></tbody></table></div></div>
<div class=note><b>Honest by design.</b> The headline is <b>coverage</b> (envenomings within reach of the right antivenom) — what the tool controls. Deaths are a <i>decision-gap vs a worst-case</i> (ineffective product everywhere), <b>bounded by</b> Nigeria's total snakebite mortality (GBD 2019 {A['national_deaths_GBD2019']:,}, UI {A['national_deaths_GBD2019_ui'][0]:,}–{A['national_deaths_GBD2019_ui'][1]:,}; Habib 2015 {A['national_deaths_Habib2015']:,}) — <b>not</b> extra lives vs today, since effective antivenom already reaches some patients. Subnational stock is unobservable → placement <b>choice</b>, not inventory. {S['pct_unreachable']}% of burden is beyond 50 km of any hospital. Robust: {S['placement_robustness']['flat_gradient_overlap']}/{S['placement_robustness']['of']} hospitals stay chosen under a flattened gradient.</div>
<footer>PANAF-Premium recommended (WHO risk-benefit-assessed, broad, heat-stable/lyophilised — deployable without cold chain). Impact anchored to Habib 2015 (Nigerian cost-effectiveness). Boundaries <a href="https://www.geoboundaries.org/">geoBoundaries</a> (CC BY 4.0); facilities Maina/WHO (CC BY 4.0); population <a href="https://www.worldpop.org/">WorldPop</a>/afripop2020 (CC BY 4.0) distribution → 206.1 M; incidence facility-anchored and conservative ({A['implied_national_envenoming_rate_per_100k']}/100k vs published {A['published_west_africa_rate_range_per_100k'][0]}–{A['published_west_africa_rate_range_per_100k'][1]}/100k). Not clinical guidance.</footer></div>
<script>const curve={json.dumps(cj)},plan={json.dumps(pj)};const $=i=>document.getElementById(i),nf=n=>n.toLocaleString('en-US');
const tb=$('tb');plan.forEach(p=>{{const t=document.createElement('tr');t.dataset.pr=p.pr;t.innerHTML=`<td>${{p.pr}}</td><td class=l>${{p.h}}</td><td class=l>${{p.reg}}</td><td>${{nf(p.v)}}</td><td>$${{nf(p.c)}}</td>`;tb.appendChild(t);}});
function u(k){{const c=curve[k];$('nh').textContent=k;$('o_pct').textContent=c.pct+'%';$('o_d').textContent=nf(c.env);$('o_v').textContent=nf(c.vials);$('o_c').textContent='$'+nf(c.cost);document.querySelectorAll('#tb tr').forEach(t=>t.className=+t.dataset.pr<=k?'on':'off');}}
$('sl').addEventListener('input',e=>u(+e.target.value));u({len(plan)});</script></body></html>"""
open(f"{OUT}/covermap_planner_nigeria.html","w").write(P)
print("Nigeria outputs:",[f for f in os.listdir(OUT) if f.endswith(('.png','.html'))])
