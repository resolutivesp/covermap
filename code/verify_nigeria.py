#!/usr/bin/env python3
"""INDEPENDENT verification of Nigeria — re-derives from raw inputs, cross-checks artifacts,
and enforces the honesty guardrails (deaths bounded by published national mortality)."""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, json, re, sys, os
BASE="/home/claude/snakebite"; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_ng"
FAIL=[]
def chk(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ")+name+(f"   {detail}" if detail else ""))
    if not ok: FAIL.append(name)

S=json.load(open(f"{OUT}/impact_summary_ng.json")); O=S['optimized']; A=S['burden_anchor']; U=S['urban_artifact']
d=pd.read_csv(f"{OUT}/district_ng.csv"); plan=pd.read_csv(f"{OUT}/pre_positioning_plan_ng.csv")
curve=pd.read_csv(f"{OUT}/coverage_curve_ng.csv")

print("\n=== A. REPRODUCIBILITY (no /tmp dependency) ===")
chk("population raster persisted in repo", os.path.exists(f"{DATA}/ng/afripop2020.tif"))
chk("WHO facilities .rda persisted in repo", os.path.exists(f"{DATA}/ng/df_who_sites.rda"))
chk("boundaries persisted", os.path.exists(f"{DATA}/ng/nga_ADM1.json") and os.path.exists(f"{DATA}/ng/nga_ADM2.json"))
src=open(f"{BASE}/nigeria_build.py").read()
chk("build reads persisted raster first", 'RASTER=f"{DATA}/ng/afripop2020.tif"' in src)
chk("build reads persisted rda first", 'RDA=f"{DATA}/ng/df_who_sites.rda"' in src)

print("\n=== B. POPULATION ===")
NG=206_139_589
chk("national population == World Bank 2020 total", abs(d['pop'].sum()-NG)<1000, f"{d['pop'].sum():,.0f} vs {NG:,}")
chk("population is the SCALED distribution, not raw raster sums", d['pop'].sum()>1e8,
    "raw afripop sums were ~550k before the fix - this guards the regression")
chk("no NaN/negative population", d['pop'].notna().all() and (d['pop']>=0).all())
chk("LGA count == 774", len(d)==774, str(len(d)))
chk("state count == 37 (36 + FCT)", S['n_states']==37, str(S['n_states']))

print("\n=== C. BURDEN + published-rate anchor ===")
ATT={'MIDDLE_BELT':45,'SUDAN_SAVANNA':28,'SOUTH_FOREST':4}; ENV_F=0.647
RATE={z:ATT[z]*ENV_F for z in ATT}; ECH={'MIDDLE_BELT':.85,'SUDAN_SAVANNA':.85,'SOUTH_FOREST':.20}
env=(d['pop']*d['zone'].map(RATE)/1e5); ech=env*d['zone'].map(ECH)
chk("every LGA has a zone", d['zone'].notna().all())
chk("total envenomings re-derives", abs(env.sum()-S['total_envenomings_yr'])<2, f"{env.sum():,.0f} vs {S['total_envenomings_yr']:,}")
chk("total Echis-severe re-derives", abs(ech.sum()-S['total_echis_yr'])<2, f"{ech.sum():,.0f} vs {S['total_echis_yr']:,}")
rate=env.sum()/d['pop'].sum()*1e5
chk("implied national rate matches summary", abs(rate-A['implied_national_envenoming_rate_per_100k'])<0.15, f"{rate:.1f}")
lo,hi=A['published_west_africa_rate_range_per_100k']
chk("implied national rate INSIDE published West-Africa range", lo<=rate<=hi, f"{rate:.1f} in [{lo},{hi}]")
chk("our rate is well BELOW community surveys (conservative floor)", rate < A['community_rate_benue_per_100k']/5,
    f"{rate:.1f} vs Benue community {A['community_rate_benue_per_100k']}")

print("\n=== D. COVERAGE / OPTIMIZER ===")
prot=d.loc[d['protected_opt'].astype(str).str.lower().isin(['true','1']),'echis_yr'].sum()
chk("optimized coverage re-derives", abs(100*prot/ech.sum()-O['pct_protected'])<0.15, f"{100*prot/ech.sum():.2f}% vs {O['pct_protected']}%")
chk("coverage curve monotonic", (curve['pct'].diff().dropna()>=-1e-9).all())
chk("plan length == optimized hospitals", len(plan)==O['hospitals'], f"{len(plan)} vs {O['hospitals']}")
chk("no duplicate hospitals", plan['hospital'].str.strip().duplicated().sum()==0)
chk("coverage >= 85% target", O['pct_protected']>=85, f"{O['pct_protected']}%")

print("\n=== E. DEMAND / COST ===")
P=S['model_params']; V,B,PR=P['vials_per_patient'],P['buffer'],P['usd_per_vial']
chk("model declares the facility frame", 'facility' in str(P.get('frame','')).lower())
chk("care-seeking multiplier removed (double-discount fix)", 'care_seeking' not in P)
exp=(plan['envenomings_yr']*V*(1+B))
chk("per-hospital vials formula (no care multiplier)", (abs(plan['vials_year']-np.ceil(exp))<=1).all(), f"max dev {(plan['vials_year']-np.ceil(exp)).abs().max():.2f}")
chk("vial total matches summary", int(plan['vials_year'].sum())==O['vials_yr'])
chk("cost total matches summary", abs(plan['procure_usd_yr'].sum()-O['procure_usd_yr'])<=len(plan))
chk("implied cost/vial ~ $80", abs(O['procure_usd_yr']/O['vials_yr']-PR)<6, f"${O['procure_usd_yr']/O['vials_yr']:.1f}")

print("\n=== F. HONESTY GUARDRAIL: deaths bounded by PUBLISHED national mortality ===")
CEIL=A['deaths_ceiling_used']
chk("ceiling == highest published upper bound (GBD UI upper)", CEIL==A['national_deaths_GBD2019_ui'][1], str(CEIL))
worst=max(v['deaths_hi'] for v in S['scenarios'].values())
chk("NO scenario upper deaths exceeds the published ceiling", worst<=CEIL, f"max upper {worst:,} vs ceiling {CEIL:,}")
chk("central decision-gap is of the ORDER of national mortality (not above its range)",
    O['deaths_central']<=A['national_deaths_Habib2015_ui'][1],
    f"{O['deaths_central']:,} <= Habib upper {A['national_deaths_Habib2015_ui'][1]:,}")
chk("deaths use the OBSERVED Visser differential", abs(P['CFR_delta']-0.103)<1e-6, f"delta={P['CFR_delta']}")
chk("deaths formula reproduces (within-reach env x CFR differential, capped)",
    abs(O['deaths_central']-min(round(prot*P['CFR_delta']),A['deaths_ceiling_used']))<=1)
chk("deaths_lo < central < deaths_hi", O['deaths_lo']<O['deaths_central']<O['deaths_hi'])

print("\n=== F2. PROVENANCE HONESTY: rates must be declared a CONSTRUCTION, tension surfaced ===")
src2=open(f"{BASE}/nigeria_build.py").read()
chk("build states no per-zone published rate exists", "no published per-eco-zone snakebite rate exists" in src2)
chk("build discloses the possible gradient inversion (Malumfashi vs Benue)", "Malumfashi" in src2)
chk("summary records the FMoH surveillance comparison", 'FMoH_surveillance_bites_per_100k' in A)
chk("mortality-gap tension is FLAGGED, not hidden", 'mortality_gap_exceeds_published_central' in A)
ng_html=open(f"{OUT}/nigeria_prepositioning_brief.html").read()
if A.get('mortality_gap_exceeds_published_central'):
    chk("brief admits the central gap exceeds published central mortality",
        "exceeds the highest published CENTRAL" in ng_html)
chk("brief states the rates are a construction", "construction" in ng_html.lower())
chk("brief discloses the gradient-inversion uncertainty", "Malumfashi" in ng_html)

print("\n=== G. URBAN ARTIFACT: disclosed AND shown not to drive the decision ===")
chk("artifact block present", bool(U.get('top_burden_lga')))
chk("top-burden LGA is flagged as urban", 'Municipal' in U['top_burden_lga'] or 'Abuja' in U['top_burden_lga_state'])
share=100*plan.loc[plan['state'].astype(str).str.contains('Abuja|Federal Capital|Lagos',case=False,na=False),'vials_year'].sum()/plan['vials_year'].sum()
chk("FCT/Lagos vial share re-derives", abs(share-U['pct_vials_to_FCT_or_Lagos'])<0.15, f"{share:.1f}%")
chk("urban share is immaterial (<5% of vials)", share<5, f"{share:.1f}%")
top5=set(plan.nsmallest(5,'priority')['state'].astype(str))
chk("no top-5 priority hospital is in FCT/Lagos", not any(('Abuja' in s or 'Lagos' in s or 'Federal Capital' in s) for s in top5), str(top5))

print("\n=== H. ARTIFACT CONSISTENCY ===")
html=open(f"{OUT}/nigeria_prepositioning_brief.html").read()
pl=open(f"{OUT}/covermap_planner_nigeria.html").read()
for tok,lab in [(f"{O['pct_protected']}%","coverage"),(f"{O['vials_yr']:,}","vials"),(f"{S['total_echis_yr']:,}","Echis total")]:
    chk(f"brief has {lab} ({tok})", tok in html); chk(f"planner has {lab} ({tok})", tok in pl)
chk("brief states the published mortality anchor", "1,460" in html and "1,927" in html)
chk("brief states the published incidence range", "8.9" in html and "93.3" in html)
chk("brief states the FMoH surveillance floor", "15,278" in html or "7.6" in html)
chk("brief discloses the urban artifact", "URBAN ARTIFACT" in html.upper() or "urban artifact" in html.lower())
chk("brief discloses the facility-name repair", "duplicated suffix" in html.lower())
low=re.sub(r'<[^>]+>',' ',html.lower())
for bad in ["lives saved versus today","deaths averted per year","will save"]:
    occ=[m.start() for m in re.finditer(re.escape(bad),low)]
    neg=[o for o in occ if re.search(r'\b(not|never|no)\b[^.]{0,60}$',low[max(0,o-90):o])]
    chk(f"no UN-negated overstatement: '{bad}'", len(occ)==len(neg), f"{len(occ)} occ / {len(neg)} negated")
chk("brief frames deaths as decision-gap", "decision-gap" in low)
chk("brief + planner carry the disclaimer", "not clinical guidance" in html.lower() and "not clinical guidance" in pl.lower())
chk("no residual 'Hospitaltal' typo anywhere", "Hospitaltal" not in html and "Hospitaltal" not in pl and "Hospitaltal" not in plan.to_string())

print("\n"+"="*64)
if FAIL:
    print(f"RESULT: {len(FAIL)} FAILURE(S)"); [print("   x",f) for f in FAIL]; sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
