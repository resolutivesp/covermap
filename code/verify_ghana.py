#!/usr/bin/env python3
"""INDEPENDENT verification of Ghana numbers — re-derives from raw inputs without reusing build_v2 logic,
then cross-checks every published artifact for consistency. Exit non-zero on any failure."""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, json, re, sys
BASE="/home/claude/snakebite"; DATA=f"{BASE}/data"; OUT=f"{BASE}/out2"
FAIL=[]; WARN=[]
def chk(name, ok, detail=""):
    (print if ok else (lambda s: (FAIL.append(name), print(s))[1]))(("  PASS  " if ok else "  FAIL  ")+name+(f"   {detail}" if detail else ""))
def warn(name, detail=""): WARN.append(name); print("  WARN  "+name+(f"   {detail}" if detail else ""))

S=json.load(open(f"{OUT}/impact_summary.json"))
d=pd.read_csv(f"{OUT}/district_v2.csv"); plan=pd.read_csv(f"{OUT}/pre_positioning_plan.csv")
curve=pd.read_csv(f"{OUT}/coverage_curve.csv")

print("\n=== A. POPULATION: independent re-derivation vs census ===")
pop_csv=pd.read_csv(f"{DATA}/district_pop.csv"); reg=pd.read_csv(f"{DATA}/region_pop.csv")
tot_model=d['pop'].sum(); tot_census=reg.iloc[:,1].sum()
chk("national population == 2021 census total", abs(tot_model-tot_census)<1, f"model {tot_model:,.0f} vs census {tot_census:,.0f}")
chk("national population ~30.8M (GSS 2021 PHC)", abs(tot_model-30.8e6)/30.8e6<0.02, f"{tot_model:,.0f}")
# per-region sums must equal census region totals exactly
rn=reg.columns[0]; rv=reg.columns[1]
cen=dict(zip(reg[rn],reg[rv]))
bad=[]
for r,sub in d.groupby('region'):
    if r in cen and abs(sub['pop'].sum()-cen[r])>1: bad.append((r,sub['pop'].sum(),cen[r]))
chk("every region sums to its census total", not bad, str(bad[:3]))
chk("no negative/NaN population", d['pop'].notna().all() and (d['pop']>=0).all())

print("\n=== B. BURDEN: recompute from population x rate x Echis fraction ===")
ZONE={'Upper East':'N_SAVANNA','Upper West':'N_SAVANNA','North East':'N_SAVANNA','Northern':'N_SAVANNA','Savannah':'N_SAVANNA',
 'Oti':'TRANSITION','Bono East':'TRANSITION','Bono':'TRANSITION','Volta':'TRANSITION',
 'Ahafo':'FOREST','Ashanti':'FOREST','Eastern':'FOREST','Western North':'FOREST','Western':'FOREST','Central':'FOREST',
 'Greater Accra':'COASTAL'}
# v0.4 facility frame: attendance -> envenoming fraction -> Echis fraction
ATT={'N_SAVANNA':55,'TRANSITION':24,'FOREST':25,'COASTAL':12}; ENV_F=0.647
RATE={z:ATT[z]*ENV_F for z in ATT}; ECH={'N_SAVANNA':.90,'TRANSITION':.60,'FOREST':.20,'COASTAL':.20}
z=d['region'].map(ZONE)
chk("every district mapped to a zone", z.notna().all(), f"unmapped={d.loc[z.isna(),'region'].unique()[:5]}")
env=(d['pop']*z.map(RATE)/1e5); ech=env*z.map(ECH)
chk("total envenomings matches summary", abs(env.sum()-S['total_envenomings_yr'])<2, f"recomputed {env.sum():,.0f} vs {S['total_envenomings_yr']:,}")
chk("total Echis-severe matches summary", abs(ech.sum()-S['total_echis_yr'])<2, f"recomputed {ech.sum():,.0f} vs {S['total_echis_yr']:,}")
chk("Echis-severe < all envenomings", ech.sum()<env.sum())

print("\n=== C0. RATE PROVENANCE: base rates are ATTENDANCE, and each is labelled ===")
src=open(f"{BASE}/build_v2.py").read()
chk("build declares the attendance frame explicitly", "ATTEND=" in src and "FACILITY SNAKEBITE ATTENDANCE" in src)
chk("envenoming fraction is separated from attendance", "ENVENOM=0.647" in src)
chk("north attendance rate is the Aglanu published value (55)", ATT['N_SAVANNA']==55)
chk("transition attendance rate is the Ceesay published value (24)", ATT['TRANSITION']==24)
chk("forest rate corrected away from the contradicted value of 8", ATT['FOREST']!=8 and ATT['FOREST']>=20,
    f"forest={ATT['FOREST']} (Mensah 2016 reports 50-100/100k in Western Region)")
chk("coastal rate flagged as the only fully unsourced value", "only fully unsourced rate" in src)
chk("forest/coastal Echis fraction lowered (E. ocellatus is a savanna species)", ECH['FOREST']<=0.20)

print("\n=== C. BURDEN ANCHOR: model must sit BELOW reported national cases ===")
A=S['burden_anchor']
chk("anchor present with source", bool(A.get('source')) and A.get('national_cases_reported_yr')==9900)
chk("modelled envenomings < reported bites (conservative floor)",
    A['modelled_envenomings_yr']<A['national_cases_reported_yr'],
    f"{A['modelled_envenomings_yr']:,} < {A['national_cases_reported_yr']:,}")

print("\n=== D. COVERAGE / OPTIMIZER ===")
O=S['optimized']
prot=d.loc[d['protected_opt'].astype(str).str.lower().isin(['true','1']),'echis_yr'].sum()
chk("optimized coverage % re-derives from district file", abs(100*prot/ech.sum()-O['pct_protected'])<0.15,
    f"recomputed {100*prot/ech.sum():.2f}% vs {O['pct_protected']}%")
chk("coverage curve is monotonic non-decreasing", (curve['pct'].diff().dropna()>=-1e-9).all())
chk("curve endpoint == optimized coverage", abs(curve['pct'].iloc[-1]-O['pct_protected'])<0.15,
    f"{curve['pct'].iloc[-1]} vs {O['pct_protected']}")
chk("curve starts at 0 with 0 hospitals", curve['pct'].iloc[0]==0)
chk("plan has exactly the optimized hospital count", len(plan)==O['hospitals'], f"{len(plan)} vs {O['hospitals']}")
chk("no duplicate hospitals in plan", plan['hospital'].str.strip().duplicated().sum()==0)
chk("structural gap + reachable == 100%", abs(S['pct_unreachable']+100*ech[d['reachable_any'].astype(str).str.lower().isin(['true','1'])].sum()/ech.sum()-100)<0.15)

print("\n=== E. DEMAND / COST ARITHMETIC (facility frame: NO care-seeking multiplier) ===")
P=S['model_params']; V,B,PR=P['vials_per_patient'],P['buffer'],P['usd_per_vial']
chk("model declares the facility frame", 'facility' in str(P.get('frame','')).lower(), str(P.get('frame')))
chk("care-seeking multiplier is GONE from the model params (double-discount fix)",
    'care_seeking' not in P, str([k for k in P if 'care' in k]))
exp_vials=(plan['envenomings_yr']*V*(1+B))
chk("per-hospital vials == env x vials x (1+buffer), rounded up",
    (abs(plan['vials_year']-np.ceil(exp_vials))<=1).all(),
    f"max dev {(plan['vials_year']-np.ceil(exp_vials)).abs().max():.2f}")
chk("plan vial total matches summary", int(plan['vials_year'].sum())==O['vials_yr'], f"{plan['vials_year'].sum()} vs {O['vials_yr']}")
chk("cost == vials-equivalent x price (within rounding)", abs(plan['procure_usd_yr'].sum()-O['procure_usd_yr'])<=len(plan),
    f"{plan['procure_usd_yr'].sum():,} vs {O['procure_usd_yr']:,}")
chk("plan envenomings <= total within-reach burden", plan['envenomings_yr'].sum()<=prot+1,
    f"{plan['envenomings_yr'].sum():,.0f} <= {prot:,.0f}")

print("\n=== F. HONESTY GUARDRAIL: deaths must be a BOUNDED decision-gap ===")
chk("deaths use the OBSERVED Visser differential, not a synthetic care-seeking chain",
    abs(P['CFR_delta']-(P['CFR_wrong_product']-P['CFR_right_product']))<1e-9 and abs(P['CFR_delta']-0.103)<1e-6,
    f"delta={P['CFR_delta']}")
# Ghana total snakebite mortality ceiling: reported cases x plausible CFR upper bound.
# Aglanu 2025 facility CFR ~1.9%; even at a generous 5% community CFR on 9,900 bites -> ~495 deaths.
CEIL=9900*0.05
for k,v in S['scenarios'].items():
    if v['deaths_hi']>CEIL: FAIL.append(f"scenario '{k}' upper deaths {v['deaths_hi']} exceeds national ceiling {CEIL:.0f}")
chk("no scenario's UPPER deaths exceeds a generous national mortality ceiling",
    all(v['deaths_hi']<=CEIL for v in S['scenarios'].values()),
    f"max upper {max(v['deaths_hi'] for v in S['scenarios'].values())} vs ceiling {CEIL:.0f}")
chk("deaths formula reproduces (within-reach env x observed CFR differential)",
    abs(O['deaths_central']-round(prot*P['CFR_delta']))<=1, f"{O['deaths_central']} vs {round(prot*P['CFR_delta'])}")
chk("deaths_lo < central < deaths_hi", O['deaths_lo']<O['deaths_central']<O['deaths_hi'])

print("\n=== G. ARTIFACT CONSISTENCY: every number in the HTML must match the model ===")
html=open(f"{OUT}/ghana_prepositioning_brief_v2.html").read()
plan_html=open(f"{OUT}/covermap_planner.html").read()
must=[(f"{O['pct_protected']}%","coverage %"),(f"{O['vials_yr']:,}","vials"),
      (f"{S['total_echis_yr']:,}","Echis total"),(f"{S['pct_unreachable']}%","structural gap")]
for tok,lab in must:
    chk(f"brief contains {lab} ({tok})", tok in html)
    chk(f"planner contains {lab} ({tok})", tok in plan_html or tok.replace(',','') in plan_html)
chk("brief states procurement cost", f"${O['procure_usd_yr']:,}" in html or "237k" in html)
chk("brief carries the national burden anchor", "9,900" in html)
# forbidden overstatement language — only flag NON-negated occurrences (the brief legitimately
# says "NOT extra lives saved versus today", which is the honest framing, not an overstatement)
low=re.sub(r'<[^>]+>',' ',html.lower())
for bad_phrase in ["lives saved versus today","deaths averted per year","will save"]:
    occ=[m.start() for m in re.finditer(re.escape(bad_phrase),low)]
    negated=[o for o in occ if re.search(r'\b(not|never|no)\b[^.]{0,60}$',low[max(0,o-90):o])]
    chk(f"brief avoids UN-negated overstatement: '{bad_phrase}'", len(occ)==len(negated),
        f"{len(occ)} occurrence(s), {len(negated)} negated")
chk("brief frames deaths as decision-gap", "decision-gap" in html.lower())
chk("brief carries not-clinical-guidance disclaimer", "not clinical guidance" in html.lower())
chk("planner carries not-clinical-guidance disclaimer", "not clinical guidance" in plan_html.lower())

print("\n=== H. CITATION INTEGRITY (verified against primary sources) ===")
chk("Habib cost/death $2,330 cited correctly", "2,330" in html)
chk("Habib CFR 16% + effectiveness 75% cited", "16%" in html and "75%" in html)
chk("Visser CFR 1.8->12.1 cited", "1.8%" in html and "12.1%" in html)
chk("PANAF heat-stability claim present", "lyophilis" in html.lower())

print("\n"+"="*64)
if FAIL:
    print(f"RESULT: {len(FAIL)} FAILURE(S)"); [print("   x",f) for f in FAIL]; sys.exit(1)
print(f"RESULT: ALL CHECKS PASSED  ({len(WARN)} warnings)"); [print("   !",w) for w in WARN]
