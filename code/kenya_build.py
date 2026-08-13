#!/usr/bin/env python3
"""
kenya_build.py — Kenya demonstrator, CoverMap.
Facility frame, same as Ghana/Nigeria: NO care-seeking multiplier (v0.4 rule).
Every parameter is imported from data/ke/parameters_ke.py — nothing retyped.
Outputs: out_ke/impact_summary_ke.json, out_ke/county_ke.csv,
         out_ke/pre_positioning_plan_ke.csv, out_ke/coverage_curve_ke.csv
"""
import os, sys, json
import numpy as np, pandas as pd, geopandas as gpd
from rasterstats import zonal_stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "data", "ke"))
import parameters_ke as P

OUT = os.path.join(BASE, "out_ke"); os.makedirs(OUT, exist_ok=True)

# ---- 1. Counties + zones ----------------------------------------------------
adm1 = gpd.read_file(f"{BASE}/data/ke/ken_ADM1.json")[["shapeName", "geometry"]]
adm1 = adm1.rename(columns={"shapeName": "county"})
zone_of = {c: z for z, cs in P.ZONES.items() for c in cs}
adm1["zone"] = adm1["county"].map(zone_of)
missing = adm1[adm1["zone"].isna()]["county"].tolist()
assert not missing, f"counties without zone: {missing}"
assert len(adm1) == 47, f"expected 47 counties, got {len(adm1)}"

# ---- 2. Units: ADM2 subcounties (290) -> zone via parent county -------------
adm2 = gpd.read_file(f"{BASE}/data/ke/ken_ADM2.json")[["shapeName", "geometry"]]
adm2 = adm2.rename(columns={"shapeName": "subcounty"})
c = adm2.copy(); c["geometry"] = c.geometry.representative_point()
c = gpd.sjoin(c, adm1[["county", "zone", "geometry"]], how="left", predicate="within")
adm2["county"], adm2["zone"] = c["county"].values, c["zone"].values
orph = adm2["zone"].isna().sum()
if orph:  # coastal slivers etc: nearest county
    for i in adm2[adm2["zone"].isna()].index:
        j = adm1.distance(adm2.geometry[i].representative_point()).idxmin()
        adm2.loc[i, ["county", "zone"]] = adm1.loc[j, ["county", "zone"]].values
print(f"ADM2 units: {len(adm2)} ({orph} assigned by nearest-county fallback)")

# ---- Population: county totals PINNED to KNBS census; raster only WITHIN county
census = pd.read_csv(f"{BASE}/data/ke/{P.COUNTY_CENSUS_CSV}")
assert len(census) == 47 and census["pop_census_2019"].sum() == P.CENSUS_TOTAL_2019, \
    "county census integrity check failed"
zs = zonal_stats(adm2, f"{BASE}/data/ng/afripop2020.tif", stats="sum", all_touched=True)
adm2["w_raw"] = [z["sum"] or 0 for z in zs]
adm2["pop"] = 0.0
for cty, grp in adm2.groupby("county"):
    tot = census.loc[census["county"] == cty, "pop_census_2019"]
    assert len(tot) == 1, f"county not in census table: {cty}"
    w = grp["w_raw"].values
    w = w / w.sum() if w.sum() > 0 else np.full(len(grp), 1.0 / len(grp))
    adm2.loc[grp.index, "pop"] = float(tot.iloc[0]) * w
# rc2: raster weights are normalised per county, so cross-county double counting
# cannot move population between counties; within-county split stays approximate
# (declared). County totals now exactly reproduce the KNBS census.

# ---- 3. Burden: expected snakebite attendances per subcounty ----------------
adm2["att_rate"] = adm2["zone"].map(P.ZONE_ATTENDANCE_PER_100K)
adm2["attendances_yr"] = adm2["pop"] * adm2["att_rate"] / 1e5

# ---- 4. Facilities ----------------------------------------------------------
fac_all = pd.read_csv(f"{BASE}/data/ke/kenya_facilities_who_raw.csv")
fac = fac_all.dropna(subset=["Lat", "Long"])
n_dropped_no_coords = len(fac_all) - len(fac)   # declared in summary, not silent
gfac = gpd.GeoDataFrame(fac, geometry=gpd.points_from_xy(fac["Long"], fac["Lat"]), crs=adm1.crs)
gj = gpd.sjoin(gfac, adm1[["county", "zone", "geometry"]], how="left", predicate="within")
lost = gj["county"].isna()
for i in gj[lost].index:   # island/coastline facilities (e.g. Faza, Pate Island)
    j = adm1.distance(gj.geometry[i]).idxmin()
    gj.loc[i, ["county", "zone"]] = adm1.loc[j, ["county", "zone"]].values
gfac = gj
print(f"facilities: {len(gfac)} ({int(lost.sum())} assigned by nearest-county fallback)")
# spatial join (not the file's Admin1 strings, which mix county spellings)

# ---- 5. Demand chain (facility frame) ---------------------------------------
adm2["treated_yr"] = adm2["attendances_yr"] * P.ANTIVENOM_TREATED_FRACTION
adm2["vials_yr"] = adm2["treated_yr"] * P.VIALS_PER_TREATED * (1 + P.SAFETY_BUFFER)

# ---- 6. Reach: subcounty units -> hospitals (50 km proxy) -------------------
cent = adm2.to_crs(32637).geometry.representative_point()   # UTM 37N, subcounty units
hosp = gfac.to_crs(32637)
D = np.sqrt((cent.x.values[:, None] - hosp.geometry.x.values[None, :]) ** 2 +
            (cent.y.values[:, None] - hosp.geometry.y.values[None, :]) ** 2) / 1000.0

# Reach is evaluated subcounty-representative-point -> facility (290 units),
# matching Nigeria's LGA-level granularity. County centroids were rejected as
# too coarse (47 units; caught in first-pass review, 11 Aug).

# ---- 7. Adequacy + greedy maximal coverage ----------------------------------
def adequate(product, needs_echis):
    p = P.PRODUCTS[product]
    if not p["big5"]:
        return False
    if needs_echis and p["echis"] is not True:  # None (unknown) never counts
        return False
    return True

burden = adm2["attendances_yr"].values
chosen, covered, curve = [], np.zeros(len(adm2), bool), []
order = None
for step in range(60):
    gains = []
    for j in range(D.shape[1]):
        if j in chosen:
            gains.append(-1); continue
        newly = (~covered) & (D[:, j] <= P.REACH_KM)
        gains.append(burden[newly].sum())
    j = int(np.argmax(gains))
    if gains[j] <= 0:
        break
    chosen.append(j)
    covered |= (D[:, j] <= P.REACH_KM)
    curve.append({"n_hospitals": len(chosen),
                  "pct_covered": round(100 * burden[covered].sum() / burden.sum(), 1),
                  "pct_exact": 100 * burden[covered].sum() / burden.sum()})

# stop rule: cut where UNROUNDED marginal gain < 0.5% of total (rc2: was applied
# to 1-decimal rounded values, which let a 0.454% gain survive as "0.5")
cut = len(curve)
for i in range(1, len(curve)):
    if curve[i]["pct_exact"] - curve[i - 1]["pct_exact"] < 0.5:
        cut = i; break
chosen = chosen[:cut]
covered = np.zeros(len(adm2), bool)
for j in chosen:
    covered |= (D[:, j] <= P.REACH_KM)

pct = 100 * burden[covered].sum() / burden.sum()
plan = gfac.iloc[chosen][["Facility name", "Facility type", "Ownership", "county", "zone"]].copy()
# assign each covered county to its nearest chosen facility for vial allocation
alloc = np.zeros(len(chosen))
for i in range(len(adm2)):
    if covered[i]:
        dists = [D[i, j] for j in chosen]
        alloc[int(np.argmin(dists))] += adm2["vials_yr"].iloc[i]
plan["vials_yr"] = np.round(alloc).astype(int)
tot_vials = int(plan["vials_yr"].sum())

# ---- 7b. Product recommendation per facility (adequacy rule, enforced) ------
# a facility needs Echis cover if ANY demand unit allocated to it lies in an
# Echis county (safe direction: allocation-based, not facility-location-based)
unit_alloc = np.full(len(adm2), -1)
for i in range(len(adm2)):
    if covered[i]:
        unit_alloc[i] = int(np.argmin([D[i, j] for j in chosen]))
needs_echis = [bool(adm2.loc[(unit_alloc == k), "county"].isin(P.ECHIS_COUNTIES).any())
               for k in range(len(chosen))]
def recommend(ne):
    # rc3: only products actually on the Kenyan market are recommendable
    ok = [n for n in P.PRODUCTS if P.PRODUCTS[n].get("kenya_market") and adequate(n, ne)]
    assert ok, "no adequate marketed product"
    ok.sort(key=lambda n: P.PRODUCTS[n]["status"] != "WHO risk-benefit assessed")
    return ok[0] + ("" if len(ok) == 1 else " (alt: " + ", ".join(ok[1:]) + ")")
plan["serves_echis_county"] = needs_echis
plan["recommended_product"] = [recommend(ne) for ne in needs_echis]
assert not plan["recommended_product"].str.contains("Inoserp").any(), "Inoserp must never be recommended"

# ---- 7c. Robustness: the top pick depends on the NOT_CONFIRMED highlands rate.
# Re-run placement with the CENTRAL_HIGHLANDS rate halved and report overlap.
alt_burden = adm2.apply(lambda r: r["pop"] * (r["att_rate"] / 2 if r["zone"] == "CENTRAL_HIGHLANDS" else r["att_rate"]) / 1e5, axis=1).values
alt_chosen, alt_cov = [], np.zeros(len(adm2), bool)
for step in range(len(chosen)):
    gains = [(-1 if j in alt_chosen else alt_burden[(~alt_cov) & (D[:, j] <= P.REACH_KM)].sum()) for j in range(D.shape[1])]
    j = int(np.argmax(gains))
    if gains[j] <= 0: break
    alt_chosen.append(j); alt_cov |= (D[:, j] <= P.REACH_KM)
overlap = len(set(chosen) & set(alt_chosen))

# ---- 8. External anchor checks (bounds, not confirmations) -------------------
implied_national_rate = 1e5 * adm2["attendances_yr"].sum() / adm2["pop"].sum()
anchors = {
    "implied_national_attendance_per_100k": round(implied_national_rate, 1),
    "coombs_multiarea_rate": 13.8,
    "coombs_range": [1.9, 67.9],
    "note": "implied national attendance must sit inside Coombs' published area range; "
            f"community rates run far higher (Snow coast {P.COMMUNITY_BRACKET['coast_bites_per_100k']:.0f}; "
            f"Samburu ~{P.COMMUNITY_BRACKET['samburu_annualised_per_100k']:.0f} derived) — same "
            "facility-vs-community gap Nigeria documents.",
}
assert 1.9 <= implied_national_rate <= 67.9, "implied rate outside published bracket"

summary = {
    "country": "Kenya",
    "frame": "facility (attendance-anchored; NO care-seeking multiplier)",
    "version_inputs": "parameters_ke.py — single source of truth; see CITATIONS",
    "population_total": int(adm2["pop"].sum()),
    "census_total_2019": P.CENSUS_TOTAL_2019,
    "n_counties": len(adm1), "n_subcounty_units": len(adm2),
    "n_hospital_tier": len(gfac),
    "facilities_dropped_no_coords": int(n_dropped_no_coords),
    "attendances_yr": int(adm2["attendances_yr"].sum()),
    "optimized": {
        "hospitals": len(chosen),
        "pct_covered": round(pct, 1),
        "vials_yr": tot_vials,
        "procure_usd_yr": int(tot_vials * P.PRICE_PER_VIAL_USD),
    },
    "burden_anchor": anchors,
    "placement_robustness": {"highlands_rate_halved_overlap": overlap, "of": len(chosen)},
    "product_rule": "PANAF-Premium required for facilities serving Echis pyramidum counties (only "
                    "marketed product whose E. pyramidum cover is WHO Schedule-2 listed - grade A "
                    "under our published scheme); SAIMR Polyvalent the marketed alternative "
                    "elsewhere (QC 2026: potent vs all Big Five; no Echis cover). AFRIVEN was "
                    "potent vs the Big Five in the QC panel but has yet to be commercialised in "
                    "Kenya - not recommendable. Inoserp excluded (failed 3 of 5; withdrawn 2022).",
    "provenance_note": ("zone rate status: " + "; ".join(f"{z} {st}" for z, st in P.ZONE_RATE_STATUS.items())
                       + f". Treated fraction {P.ANTIVENOM_TREATED_FRACTION} and vials/treated "
                       f"{P.VIALS_PER_TREATED}: fraction SOURCED (verbatim 25.2%), vials DERIVED - both Abouyannis 2023 (paediatric, coastal). "
                       "Zone rate values live only in parameters_ke.py."),
}
json.dump(summary, open(f"{OUT}/impact_summary_ke.json", "w"), indent=1)
adm2.drop(columns="geometry").to_csv(f"{OUT}/subcounty_ke.csv", index=False)
adm1.drop(columns="geometry").to_csv(f"{OUT}/county_ke.csv", index=False)
plan.to_csv(f"{OUT}/pre_positioning_plan_ke.csv", index=False)
pd.DataFrame(curve).to_csv(f"{OUT}/coverage_curve_ke.csv", index=False)

print(f"Kenya: {len(chosen)} hospitals -> {pct:.1f}% of attendances within {P.REACH_KM:.0f} km")
print(f"vials/yr {tot_vials:,} (~${tot_vials * P.PRICE_PER_VIAL_USD:,.0f})")
print(f"implied national attendance {implied_national_rate:.1f}/100k (Coombs bracket 1.9-67.9)")
print(plan.head(10).to_string(index=False))
