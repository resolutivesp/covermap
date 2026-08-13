#!/usr/bin/env python3
"""verify_kenya.py — checks the Kenya build against its own inputs and rules."""
import os, sys, json, re
import numpy as np, pandas as pd, geopandas as gpd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{BASE}/data/ke"); import parameters_ke as P
OUT = f"{BASE}/out_ke"
FAIL = []
def chk(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   {detail}" if detail else ""))
    if not ok: FAIL.append(name)

S = json.load(open(f"{OUT}/impact_summary_ke.json"))
sub = pd.read_csv(f"{OUT}/subcounty_ke.csv")
plan = pd.read_csv(f"{OUT}/pre_positioning_plan_ke.csv")
curve = pd.read_csv(f"{OUT}/coverage_curve_ke.csv")
src = open(f"{BASE}/code/kenya_build.py").read()

print("\n=== A. FRAME: the v0.4 rule holds ===")
import tokenize, io
toks = [t.string.lower() for t in tokenize.generate_tokens(io.StringIO(src).readline)
        if t.type == tokenize.NAME]   # identifiers only: no comments, no strings, no docstrings
chk("no care-seeking identifier in the build's executable code (tokenizer-level)",
    not any("care" in t for t in toks))
chk("demand chain is exactly the two canonical lines (no extra multiplier)",
    'adm2["treated_yr"] = adm2["attendances_yr"] * P.ANTIVENOM_TREATED_FRACTION' in src and
    'adm2["vials_yr"] = adm2["treated_yr"] * P.VIALS_PER_TREATED * (1 + P.SAFETY_BUFFER)' in src)
chk("summary declares facility frame", "facility" in S["frame"] and "NO care-seeking" in S["frame"])

print("\n=== B. INPUTS: single source of truth ===")
lit = re.findall(r"(?<![\w.])(?:47564296|47_564_296|0\.252|0\.182|1\.40?|151\.0|20\.0|15\.0|4\.6|2\.0)(?![\w.])", src)
chk("no load-bearing literals retyped in kenya_build.py (all via P.*)", len(lit)==0, f"found {lit[:5]}")
chk("census total in summary equals parameters_ke", S["census_total_2019"]==P.CENSUS_TOTAL_2019)
chk("population pinned to census (within rounding)", abs(S["population_total"]-P.CENSUS_TOTAL_2019)<=1)

print("\n=== B2. COUNTY PINNING (rc2 - the check that would have caught finding 1) ===")
census = pd.read_csv(f"{BASE}/data/ke/{P.COUNTY_CENSUS_CSV}")
chk("47 county census rows summing EXACTLY to national total",
    len(census)==47 and census["pop_census_2019"].sum()==P.CENSUS_TOTAL_2019)
bycty = sub.groupby("county")["pop"].sum().round(0)
merged = census.set_index("county")["pop_census_2019"]
dev = (bycty - merged).abs().max()
chk("every county's modelled population equals its census figure (<=1 person)", dev<=1, f"max dev {dev}")
chk("treated fraction citation carries the paper's own numbers (119, 25.2%)",
    "119" in open(f"{BASE}/data/ke/parameters_ke.py").read() and "25.2" in open(f"{BASE}/data/ke/parameters_ke.py").read())

print("\n=== C. ARITHMETIC reproduces from inputs ===")
att = (sub["pop"]*sub["att_rate"]/1e5)
chk("attendances = pop x zone rate / 1e5 (per unit)", np.allclose(att, sub["attendances_yr"]))
chk("summary attendances = sum of units", abs(att.sum()-S["attendances_yr"])<1)
vials_chain = att*P.ANTIVENOM_TREATED_FRACTION*P.VIALS_PER_TREATED*(1+P.SAFETY_BUFFER)
chk("vials chain reproduces (treated x vials x buffer)", np.allclose(vials_chain, sub["vials_yr"]))
# independent allocation recomputation (rc3: no longer JSON-vs-its-own-sum)
import geopandas as gpd, numpy as np
_adm2 = gpd.read_file(f"{BASE}/data/ke/ken_ADM2.json").rename(columns={"shapeName":"subcounty"})
_adm2 = _adm2.merge(sub[["subcounty","vials_yr"]], on="subcounty")
_fac = pd.read_csv(f"{BASE}/data/ke/kenya_facilities_who_raw.csv").dropna(subset=["Lat","Long"])
_fac = _fac[_fac["Facility name"].isin(plan["Facility name"])]
_c = _adm2.to_crs(32637).geometry.representative_point()
_h = gpd.GeoDataFrame(_fac, geometry=gpd.points_from_xy(_fac["Long"],_fac["Lat"]), crs=4326).to_crs(32637)
_Dp = np.sqrt((_c.x.values[:,None]-_h.geometry.x.values[None,:])**2+(_c.y.values[:,None]-_h.geometry.y.values[None,:])**2)/1000
_covered = (_Dp<=50).any(axis=1)
_alloc = np.zeros(len(_h))
for _i in np.where(_covered)[0]: _alloc[int(np.argmin(_Dp[_i]))]+=_adm2["vials_yr"].iloc[_i]
_byname = dict(zip(_fac["Facility name"], np.round(_alloc).astype(int)))
_match = all(abs(_byname.get(r["Facility name"],-9)-r["vials_yr"])<=1 for _,r in plan.iterrows())
chk("per-facility allocation reproduces from raw geometry (independent recompute)", _match)
chk("procurement = vials x price", S["optimized"]["procure_usd_yr"]==int(S["optimized"]["vials_yr"]*P.PRICE_PER_VIAL_USD))

print("\n=== D. EXTERNAL ANCHORS are bounds, honestly stated ===")
r = S["burden_anchor"]["implied_national_attendance_per_100k"]
chk("implied national rate inside Coombs published range", 1.9<=r<=67.9, f"{r}")
chk("community bracket documented (Snow/Samburu)", "Snow" in S["burden_anchor"]["note"] and "Samburu" in S["burden_anchor"]["note"])

print("\n=== E. ZONES and coverage ===")
chk("47 counties, 290 subcounty units", S["n_counties"]==47 and S["n_subcounty_units"]==290)
chk("every subcounty has a zone", sub["zone"].notna().all())
chk("all five zones present", set(sub["zone"].unique())==set(P.ZONES.keys()))
chk("coverage curve monotonic", (curve["pct_covered"].diff().dropna()>=0).all())
kept = curve["pct_exact"].diff().dropna().iloc[:len(plan)-1]
nxt = curve["pct_exact"].diff().dropna().iloc[len(plan)-1] if len(curve) > len(plan) else 0.0
chk("stop rule two-sided: kept gains >= 0.5 AND first excluded < 0.5",
    (kept >= 0.5).all() and nxt < 0.5, f"min kept {kept.min():.3f}, next {nxt:.3f}")
chk("summary pct matches curve at chosen n", abs(curve.iloc[len(plan)-1]["pct_covered"]-S["optimized"]["pct_covered"])<0.11)

print("\n=== F. PRODUCT RULE: label never promoted; failure never recommended ===")
chk("Inoserp appears in NO recommendation", not plan["recommended_product"].str.contains("Inoserp").any())
er = plan[plan["serves_echis_county"]==True]
chk("facilities serving Echis counties: PANAF-only (no alternatives)",
    (er["recommended_product"]=="PANAF-Premium").all(), f"{len(er)} facilities")
chk("non-Echis facilities get alternatives listed",
    plan[plan["serves_echis_county"]==False]["recommended_product"].str.contains("alt:").all())
chk("AFRIVEN appears NOWHERE (not commercialised in Kenya - rc3)",
    not plan["recommended_product"].str.contains("AFRIVEN").any())
chk("only kenya_market products are ever recommended",
    all(all(P.PRODUCTS[n].get("kenya_market") for n in P.PRODUCTS
        if n.split(" (")[0] in r) for r in plan["recommended_product"]))

print("\n=== G. ROBUSTNESS declared ===")
chk("highlands-halved robustness reported", "placement_robustness" in S,
    str(S.get("placement_robustness")))
chk("provenance note declares CONSTRUCTION and NOT_CONFIRMED zones",
    "construction" in S["provenance_note"].lower() and "not_confirmed" in S["provenance_note"].lower())

print("\n" + "="*64)
if FAIL:
    print(f"RESULT: {len(FAIL)} CHECK(S) FAILED"); [print("   !", f) for f in FAIL]; sys.exit(1)
n = len([l for l in open(__file__).read().split(chr(10)) if "chk(" in l and "def chk" not in l])
print(f"RESULT: ALL {n} KENYA CHECKS PASSED")
