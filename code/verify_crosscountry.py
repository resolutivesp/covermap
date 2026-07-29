#!/usr/bin/env python3
"""Cross-country consistency: shared parameters must be IDENTICAL where the method is shared,
and every country must satisfy the same honesty invariants."""
import json, sys, os, re
BASE="/home/claude/snakebite"
FAIL=[]
def chk(n, ok, d=""):
    print(("  PASS  " if ok else "  FAIL  ")+n+(f"   {d}" if d else ""))
    if not ok: FAIL.append(n)

GH=json.load(open(f"{BASE}/out2/impact_summary.json"))
NG=json.load(open(f"{BASE}/out_ng/impact_summary_ng.json"))
IN=json.load(open(f"{BASE}/out_in/impact_summary_in.json"))

print("\n=== A. SHARED MODEL PARAMETERS (Ghana vs Nigeria: same West-African regime) ===")
for k in ['reach_km','vials_per_patient','usd_per_vial','buffer','recommended_product',
          'CFR_right_product','CFR_wrong_product','CFR_delta','envenoming_fraction']:
    chk(f"'{k}' identical across Ghana and Nigeria", GH['model_params'][k]==NG['model_params'][k],
        f"{GH['model_params'][k]} vs {NG['model_params'][k]}")
print("\n=== A2. THE DOUBLE-DISCOUNT FIX must hold in BOTH West-African models ===")
for nm,M in (('Ghana',GH),('Nigeria',NG)):
    P=M['model_params']
    chk(f"{nm}: declares the facility frame", 'facility' in str(P.get('frame','')).lower())
    chk(f"{nm}: care-seeking multiplier is GONE", 'care_seeking' not in P and 'care_range' not in P)
    chk(f"{nm}: attendance is separated from the envenoming fraction",
        'attendance_per_100k' in P and 'envenoming_fraction' in P)
    chk(f"{nm}: mortality uses the OBSERVED Visser differential (0.103)", abs(P['CFR_delta']-0.103)<1e-6)

print("\n=== B. HONESTY INVARIANTS (must hold for every country) ===")
# 1. no impact figure may exceed the published national mortality ceiling
ngworst=max(v['deaths_hi'] for v in NG['scenarios'].values())
chk("Nigeria: worst-case upper deaths <= published ceiling", ngworst<=NG['burden_anchor']['deaths_ceiling_used'],
    f"{ngworst:,} <= {NG['burden_anchor']['deaths_ceiling_used']:,}")
ghworst=max(v['deaths_hi'] for v in GH['scenarios'].values())
chk("Ghana: worst-case upper deaths <= generous national ceiling (9,900 bites x 5% CFR)", ghworst<=9900*0.05,
    f"{ghworst:,} <= {int(9900*0.05):,}")
chk("India: modelled mortality inside the GBD uncertainty interval", IN['burden_anchor']['inside_GBD_ui'])
chk("India: gap deaths are a strict subset of total", IN['gap_deaths_yr']<IN['burden_anchor']['modelled_deaths_yr'])

# 2. every country's modelled burden must be anchored to a published figure
chk("Ghana carries a burden anchor", 'burden_anchor' in GH and bool(GH['burden_anchor'].get('source')))
chk("Nigeria carries a burden anchor", 'burden_anchor' in NG and bool(NG['burden_anchor'].get('published_rate_source')))
chk("Nigeria admits its rates are a CONSTRUCTION (no per-zone published figure)",
    'no published per-eco-zone snakebite rate exists' in open(f"{BASE}/nigeria_build.py").read())
chk("Nigeria surfaces the mortality-gap tension rather than tuning it",
    'mortality_gap_exceeds_published_central' in NG['burden_anchor'])
chk("India admits no published national gap anchor exists",
    IN['burden_anchor'].get('no_published_national_gap_anchor') is True)
chk("India carries published sub-national anchors instead",
    len(IN['burden_anchor'].get('published_subnational_anchors',[]))>=3)
chk("India carries a burden anchor", 'burden_anchor' in IN and bool(IN['burden_anchor'].get('MDS_source')))

# 3. conservative-floor property
chk("Ghana modelled envenomings < reported national bites",
    GH['burden_anchor']['modelled_envenomings_yr']<GH['burden_anchor']['national_cases_reported_yr'])
lo,hi=NG['burden_anchor']['published_west_africa_rate_range_per_100k']
chk("Nigeria implied rate inside the published range (a BOUND, not a confirmation)",
    lo<=NG['burden_anchor']['implied_national_envenoming_rate_per_100k']<=hi)
chk("India mortality within 10% of the MDS point estimate", IN['burden_anchor']['within_MDS_pct']<=10)

print("\n=== C. EVERY PUBLISHED ARTIFACT: framing + disclaimer ===")
arts={
 'Ghana brief':f"{BASE}/out2/ghana_prepositioning_brief_v2.html",
 'Ghana planner':f"{BASE}/out2/covermap_planner.html",
 'Nigeria brief':f"{BASE}/out_ng/nigeria_prepositioning_brief.html",
 'Nigeria planner':f"{BASE}/out_ng/covermap_planner_nigeria.html",
 'India brief':f"{BASE}/out_in/india_coverage_gap_brief.html",
}
for name,p in arts.items():
    chk(f"{name}: exists", os.path.exists(p))
    if not os.path.exists(p): continue
    h=open(p).read(); low=re.sub(r'<[^>]+>',' ',h.lower())
    chk(f"{name}: carries the not-clinical-guidance disclaimer", "not clinical guidance" in low)
    chk(f"{name}: carries the IML/feasibility badge", "feasibility demonstrator" in low)
    # no un-negated overstatement anywhere
    bad_found=[]
    for bad in ["deaths averted per year","lives saved versus today","will save","guarantees"]:
        for m in re.finditer(re.escape(bad),low):
            if not re.search(r'\b(not|never|no)\b[^.]{0,60}$',low[max(0,m.start()-90):m.start()]): bad_found.append(bad)
    chk(f"{name}: no un-negated overstatement", not bad_found, str(set(bad_found)))
    chk(f"{name}: uses the unified design system", "--brand1:#0b6b5b" in h or "--brand1: #0b6b5b" in h)

print("\n=== D. NO STALE/CONTRADICTORY NUMBERS ACROSS ARTIFACTS ===")
gh=open(arts['Ghana brief']).read(); ng=open(arts['Nigeria brief']).read(); ind=open(arts['India brief']).read()
chk("Ghana coverage current", f"{GH['optimized']['pct_protected']}%" in gh)
chk("Ghana vial forecast current (post double-discount fix)", f"{GH['optimized']['vials_yr']:,}" in gh)
chk("Nigeria vial forecast current (post double-discount fix)", f"{NG['optimized']['vials_yr']:,}" in ng)
chk("no artifact still advertises a care-seeking multiplier as part of the impact chain",
    all('care-seeking (15' not in open(p2).read() for p2 in arts.values()))
chk("a parameter provenance audit ships alongside the verification suites",
    os.path.exists(f"{BASE}/audit_parameters.py") and os.path.exists(f"{BASE}/PARAMETER_AUDIT.txt"))
chk("Nigeria coverage current", f"{NG['optimized']['pct_protected']}%" in ng)
chk("India gap current", f"{IN['pct_burden_in_asv_gap']}%" in ind)
# guard against the specific historical regressions
chk("Nigeria brief does NOT contain the pre-fix population bug (550k)", "550,000" not in ng and "550k" not in ng)
chk("India brief does NOT claim zero South-Asia WHO-assessed products",
    "no south-asian" not in ind.lower() or "was wrong" in ind.lower())
chk("no artifact contains the old 'Hospitaltal' typo", all("Hospitaltal" not in open(p).read() for p in arts.values()))
chk("India brief reflects the corrected facility count", f"{IN['n_hospital_tier']:,}" in ind)

print("\n"+"="*64)
if FAIL:
    print(f"RESULT: {len(FAIL)} FAILURE(S)"); [print("   x",f) for f in FAIL]; sys.exit(1)
print("RESULT: ALL CROSS-COUNTRY CHECKS PASSED")
