#!/usr/bin/env python3
"""Ghana interactive pre-positioning PLANNER — unified design system (viz_common), self-contained (no external JS)."""
import json, pandas as pd, os
from viz_common import BASE_CSS, b64, VERSION_TAG
BASE="/home/claude/snakebite"; OUT=f"{BASE}/out2"
S=json.load(open(f"{OUT}/impact_summary.json")); O=S['optimized']; P=S['model_params']
cur=pd.read_csv(f"{OUT}/coverage_curve.csv"); plan=pd.read_csv(f"{OUT}/pre_positioning_plan.csv")
DELTA=P['CFR_delta']
def dd(e): return round(e*DELTA)
curve=[dict(k=int(r.n_hospitals),pct=float(r.pct),env=int(r.echis_protected),vials=int(r.cum_vials),cost=int(r.cum_cost_usd),
            dc=dd(r.echis_protected)) for _,r in cur.iterrows()]
planj=[dict(pr=int(r.priority),h=r.hospital.strip(),reg=r.region,tier=r.tier.replace('Tier','T').replace(' hospital',''),
            v=int(r.vials_year),c=int(r.procure_usd_yr)) for _,r in plan.iterrows()]
img=b64(f"{OUT}/fig1_placement.png")
firstC=[v['protected_env'] for k,v in S['scenarios'].items() if k.startswith('C')][0]

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
html="<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
html+="<title>CoverMap — antivenom pre-positioning planner (Ghana)</title><style>"+BASE_CSS+SUPP+"</style></head><body>"
html+=f"<header><div class='wrap'><div class='badge'>{VERSION_TAG} · FEASIBILITY DEMONSTRATOR · IML 2 · illustrative data · not clinical guidance</div>"
html+="<h1>CoverMap — antivenom pre-positioning planner</h1><div class='sub'>For a national NTD programme or the WHO Antivenom Stockpile Programme: which WHO-assessed antivenom to place at which hospitals, how many vials each should hold, and how much of the burden it brings within reach. Ghana demonstrator.</div></div></header><div class='wrap'>"
html+="<div class='kpis'>"
html+=f"<div class='kpi'><b>{O['pct_protected']}%</b><span>of the carpet-viper burden brought <b>within reach</b> of the right antivenom (from ~0% today)</span></div>"
html+=f"<div class='kpi'><b>~{firstC:,}</b><span>carpet-viper envenomings/yr brought <b>within reach</b> of the right antivenom (of ~{S['total_echis_yr']:,} nationally)</span></div>"
html+=f"<div class='kpi'><b>{O['vials_yr']:,}</b><span>vials / year to pre-position — a concrete demand forecast</span></div>"
html+=f"<div class='kpi'><b>${O['procure_usd_yr']:,}</b><span>annual antivenom procurement cost for the plan</span></div>"
html+="</div>"
html+="<div class='card'><h2>The plan on the map</h2><p class='muted'>Districts shaded by expected carpet-viper burden; blue circles are the hospitals to stock, sized by the vials each should hold. The optimiser concentrates supply in the northern savanna, where the burden is.</p>"
html+=f"<img src='data:image/png;base64,{img}' alt='placement map'></div>"
html+="<div class='card'><h2>Budget planner — how far does the money go?</h2><p class='muted'>Antivenom is scarce and budgets are tight. Drag to choose how many hospitals you can stock; see the coverage, envenomings within reach, vials and cost. A few well-chosen hospitals do most of the work.</p>"
html+="<div class='sliderrow'><span class='muted'>Hospitals&nbsp;stocked</span><input id='sl' type='range' min='1' max='25' value='25'><b id='nh' style='min-width:2.4em;text-align:right;font-variant-numeric:tabular-nums'>25</b></div>"
html+="<div class='out'><div><b id='o_pct'></b><span>% burden within reach</span></div><div><b id='o_d'></b><span>envenomings within reach</span></div><div><b id='o_v'></b><span>vials / yr</span></div><div><b id='o_c'></b><span>procurement / yr</span></div></div></div>"
html+="<div class='card'><h2>Pre-positioning plan — stock in this priority order</h2><p class='muted'>The actionable output: named hospitals, in the order they add the most within-reach burden, with the vials each should hold. Rows above the budget line are highlighted.</p>"
html+="<div class='plantable'><table class='t'><thead><tr><th>#</th><th class='l'>Hospital</th><th class='l'>Region</th><th class='l'>Tier</th><th>Vials/yr</th><th>Cost/yr</th></tr></thead><tbody id='tb'></tbody></table></div></div>"
html+="<div class='note'><b>Honest by design.</b> The headline is <b>coverage</b> — envenomings within reach of the right antivenom — what the tool controls. Deaths are a decision-gap anchored to a <b>directly observed</b> Ghanaian measurement: case-fatality among treated carpet-viper patients rose <b>1.8% → 12.1%</b> when an ineffective product was substituted (Visser 2008). It is what the <b>product choice</b> governs — <b>not</b> extra lives versus today, since effective antivenom already reaches some patients. Subnational stock is unobservable, so this models a placement <b>choice</b>, not measured inventory. ~"+str(S['pct_unreachable'])+"% of burden sits beyond 50&nbsp;km of any hospital. Robust: "+str(S['placement_robustness']['flat_gradient_overlap_of_25'])+"/25 hospitals stay chosen even if the gradient is flattened.</div>"
html+="<footer>PANAF-Premium is the recommended product: WHO risk-benefit-assessed, broad sub-Saharan cover, and <b>heat-stable (lyophilised, no refrigeration)</b> — deployable in rural facilities without cold chain. Facility frame: patients counted have already reached care, so no care-seeking multiplier is applied (an earlier version double-counted it). Mortality differential from Visser 2008; facilities Maina/WHO 2019; population Ghana 2021 census. Illustrative feasibility demonstrator — not clinical guidance.</footer>"
html+="</div>"
html+="<script>const curve="+json.dumps(curve)+";const plan="+json.dumps(planj)+";"
html+="""
const $=id=>document.getElementById(id);const nf=n=>n.toLocaleString('en-US');
const tb=$('tb');plan.forEach(p=>{const tr=document.createElement('tr');tr.dataset.pr=p.pr;
tr.innerHTML=`<td>${p.pr}</td><td class='l'>${p.h}</td><td class='l'>${p.reg}</td><td class='l'>${p.tier}</td><td>${nf(p.v)}</td><td>$${nf(p.c)}</td>`;tb.appendChild(tr);});
function upd(k){const c=curve[k];$('nh').textContent=k;$('o_pct').textContent=c.pct+'%';
$('o_d').textContent=nf(c.env);$('o_v').textContent=nf(c.vials);$('o_c').textContent='$'+nf(c.cost);
document.querySelectorAll('#tb tr').forEach(tr=>{const on=+tr.dataset.pr<=k;tr.className=on?'on':'off';});}
$('sl').addEventListener('input',e=>upd(+e.target.value));upd(25);
</script></body></html>"""
open(f"{OUT}/covermap_planner.html","w").write(html)
print("Ghana planner:",os.path.getsize(f"{OUT}/covermap_planner.html"),"bytes")
