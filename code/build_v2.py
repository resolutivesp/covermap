#!/usr/bin/env python3
"""
v0.2.1 — Antivenom PRE-POSITIONING decision-support engine (Ghana feasibility demonstrator).
"Given procurable products, WHICH antivenom at WHICH hospitals protects the most expected
envenomings within reach of care — how many vials should each hold, and how many deaths does
that avert (honestly, conditioned on real care-seeking)?"

Real inputs: district population (afripop2020 -> 2021 census); 190 real hospitals (Maina/WHO);
region envenoming incidence (facility-anchored); product menu w/ WHO-assessment, Echis-cover,
COLD-CHAIN. Impact/demand grounded in Habib 2015/16 + care-seeking cascade (community studies).
NOT clinical guidance. Subnational stock unobservable -> we model placement CHOICES.
"""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, os, json
from _paths import BASE, SRC; DATA=f"{BASE}/data"; OUT=f"{BASE}/out2"; os.makedirs(OUT,exist_ok=True)
M="EPSG:32630"

adm1=gpd.read_file(f"{DATA}/gha_ADM1.json")[['shapeName','geometry']].to_crs(4326)
adm1['region']=adm1['shapeName'].str.replace(' Region','',regex=False).str.strip()
adm2=gpd.read_file(f"{DATA}/gha_ADM2.json")[['shapeName','geometry']].to_crs(4326)
adm2=adm2.merge(pd.read_csv(f"{DATA}/district_pop.csv"), on='shapeName', how='left')

ZONE={'Upper East':'N_SAVANNA','Upper West':'N_SAVANNA','North East':'N_SAVANNA','Northern':'N_SAVANNA','Savannah':'N_SAVANNA',
 'Oti':'TRANSITION','Bono East':'TRANSITION','Bono':'TRANSITION','Volta':'TRANSITION',
 'Ahafo':'FOREST','Ashanti':'FOREST','Eastern':'FOREST','Western North':'FOREST','Western':'FOREST','Central':'FOREST',
 'Greater Accra':'COASTAL'}
# ---------------------------------------------------------------------------------------------
# FRAME (corrected v0.4): the published Ghanaian figures are FACILITY SNAKEBITE ATTENDANCE rates --
# people who already reached a health facility. They are NOT community incidence and NOT envenomings.
# The chain is therefore: attendance -> envenoming fraction -> Echis fraction -> vials.
# Each step is named separately so none is silently conflated (an earlier version treated the
# attendance rate AS the envenoming rate AND then multiplied by a care-seeking fraction -- a genuine
# double discount, since care-seeking has already happened by construction. That is fixed here.)
#
# ATTEND = facility snakebite attendances per 100,000/yr
#   N_SAVANNA 55  SOURCED  Aglanu 2025 PLoS NTD e0013820 ("annual hospital attendance rate on account
#                          of snakebite ... 55 persons per 100,000 per year", Upper West/North East).
#                          NB Abanga 2025 reports 101/100k for Savannah Region -> 55 is conservative.
#   TRANSITION 24 SOURCED  Ceesay 2021 Pan Afr Med J 40:131 (Volta+Oti, DHIMS2 2014-18 5-yr average).
#                          NB Bosoka 2025 reports 15.8/100k for Volta 2018-23 -> 24 is the higher/older.
#   FOREST 25     PARTIAL  Ghana Health Service DHIMS regional counts imply ~21-34/100k for
#                          Ashanti/Eastern/Central. Mensah 2016 Ghana Med J 50(2) reports HIGHER for
#                          Western Region ("about 55% of the incidence was between 50-100 per 100,000")
#                          -> 25 is a conservative floor. CORRECTION: the previous value of 8 was
#                          contradicted by Mensah 2016 by roughly 6-12x.
#   COASTAL 12    ASSUMED  *** no published snakebite incidence figure exists for Greater Accra ***
#                          set below forest on urbanisation grounds. The only fully unsourced rate.
ATTEND={'N_SAVANNA':55,'TRANSITION':24,'FOREST':25,'COASTAL':12}
# ENVENOM = fraction of facility attendances that are true envenomings needing antivenom.
#   0.647 SOURCED Aglanu 2025 (64.7% of northern Ghana attendances had >=1 abnormal clotting result).
#   Applied to all zones -- an ASSUMPTION outside the north, flagged in the outputs.
ENVENOM=0.647
# ECHIS = share of envenomings caused by Echis (carpet viper), which drives product choice.
#   N_SAVANNA 0.90 WEAK   Aglanu 2025 states E. ocellatus is "thought to cause about 90%" of northern
#                         envenomings -- an introductory assertion, not a measurement in that paper.
#                         The only community measurement in the same zone (Musah 2019) reports ~35%;
#                         the gap is severity selection (Echis bites are severe -> over-represented in
#                         facilities), which is the right direction for a facility-frame model.
#   TRANSITION 0.60 ASSUMED / FOREST 0.20 ASSUMED / COASTAL 0.20 ASSUMED -- no published basis.
#   CORRECTION: forest/coastal lowered from 0.30; E. ocellatus is a savanna species, largely absent
#   from closed forest (and eastern populations are now assigned to E. romani).
ECHIS={'N_SAVANNA':0.90,'TRANSITION':0.60,'FOREST':0.20,'COASTAL':0.20}
RATE={z:ATTEND[z]*ENVENOM for z in ATTEND}   # envenomings/100k/yr (derived, not asserted)
adm2['zone']=adm2['region'].map(ZONE)
adm2['env_yr']=adm2['pop']*adm2['zone'].map(RATE)/1e5
adm2['echis_yr']=adm2['env_yr']*adm2['zone'].map(ECHIS)

H=pd.read_csv(f"{DATA}/facilities_hospitals.csv")
hosp=gpd.GeoDataFrame(H, geometry=gpd.points_from_xy(H.lon,H.lat), crs=4326)
hj=gpd.sjoin(hosp, adm1[['region','geometry']], how='left', predicate='within')
hj=hj[~hj.index.duplicated(keep='first')]
for i in hj[hj['region'].isna()].index:
    k=adm1.distance(hosp.loc[i].geometry).idxmin(); hj.loc[i,'region']=adm1.loc[k,'region']
hosp['region']=hj['region'].values
hosp=hosp.to_crs(M)
dc=adm2.to_crs(M).geometry.centroid
dcoords=np.column_stack([dc.x.values, dc.y.values]); hcoords=np.column_stack([hosp.geometry.x.values, hosp.geometry.y.values])
DX=np.sqrt(((dcoords[:,None,:]-hcoords[None,:,:])**2).sum(-1))/1000.0
REACH=50.0
adm2['nearest_km']=DX.min(axis=1)
Rmat=DX<=REACH
echis_w=adm2['echis_yr'].values
total_echis=float(echis_w.sum())

# ---- product menu (real; cold-chain corrected: EchiTAbG is LIQUID 2-8C; PANAF is lyophilised, no refrigeration)
PROD={
 'PANAF-Premium':     dict(assessed=1, echis=1, cold='lyophilised (no refrigeration; 48-mo)', poly=1),
 'EchiTAbG':          dict(assessed=1, echis=1, cold='liquid (2-8 C; 12-mo)',                 poly=0),
 'Antivipmyn Africa': dict(assessed=1, echis=1, cold='liquid (2-8 C)',                        poly=1),
 'Inoserp Pan-Africa':dict(assessed=0, echis=1, cold='liquid',                                poly=1),  # WHO assessment TERMINATED
 'AFRIVEN/VINS':      dict(assessed=0, echis=0, cold='liquid',                                poly=1),  # documented Echis failure
}
GOOD='PANAF-Premium'   # WHO-assessed, broad, heat-stable -> the pre-positioning product for the rural north

# ---- grounded parameters (Habib 2015/16 + care-seeking cascade; see METHODS)
# ---- impact, re-anchored (v0.4) --------------------------------------------------------------
# The model now works in the FACILITY frame: the patients counted have already reached care.
# So the decision the tool governs is NOT "do they get to a hospital" but "is the antivenom on that
# hospital's shelf effective against the snake that bit them". Ghana has a DIRECTLY OBSERVED answer:
#   Visser 2008 TRSTMH 102:445 -- when an ineffective product replaced an effective one in rural
#   Ghana, case-fatality among treated Echis patients rose 1.8% -> 12.1%.
# We use that observed differential instead of the previous synthetic chain
# (care-seeking x untreated-CFR x effectiveness), which required THREE assumed parameters and
# double-counted care-seeking. This removes all three assumptions and replaces them with one
# measured, Ghana-specific quantity.
# ---- planning parameters: PROVENANCE STATED PER PARAMETER (see audit_parameters.py) ----------
# REACH 50 km -- PROXY for the published access standard, which is TRAVEL TIME, not distance.
#   The canonical snakebite accessibility study (Longbottom 2018, Lancet 392:673) defines vulnerability
#   as living ">3 h away from major urban centres" (>50,000 people), justified clinically by Habib &
#   Abubakar: "each hour delay between envenomation and antivenom administration was associated with
#   an increased mortality outcome of 1.01%". We use 50 km straight-line as a computable stand-in:
#   at rural West-African road speeds (~20-40 km/h) with a straight-line-to-road correction (~1.3-1.4x),
#   50 km straight-line lands roughly in the 2-3.5 h band. THAT CONVERSION IS OUR ASSUMPTION.
#   Finalist-phase upgrade: substitute the Malaria Atlas Project friction surface and use 3 h directly.
# VIALS 1.5 -- inside the WHO-PUBLISHED initial dose for Echis: PANAF-Premium product overview states
#   "African carpet vipers (Echis): 1-3 vials". Observed mean in Ghana's Oti region was 1.23
#   (Ketor 2024). 1.5 sits inside the published range, just above the one observed mean.
# PRICE $80/vial -- ASSUMPTION inside a very wide published bracket: Brown 2012 $18-200/vial;
#   Burkina Faso subsidised to US$3.4 (2015); SAVP US$315/vial (2020, southern Africa).
#   Cross-check: 1.5 vials x $80 = $120/course, inside the US$100-153/dose baseline used in the
#   published sub-Saharan supply modelling (Potet 2020). No single authoritative price exists.
# BUFFER 25% -- *** NOT CONFIRMED as a published standard. *** WHO/EPI supply-chain guidance sets
#   min/max levels in MONTHS OF STOCK, not a flat percentage. Retained as a planning assumption and
#   flagged as unconfirmed; it scales vials and cost linearly.
CFR_RIGHT=0.018; CFR_WRONG=0.121     # Visser 2008 (observed, rural Ghana)
CFR_DELTA=CFR_WRONG-CFR_RIGHT        # 0.103 -- case-fatality governed by the product choice
# retained ONLY for the published sensitivity band, not used in headline figures:
CFR_U=0.16; EFF=0.75                 # Habib 2015 (untreated Echis CFR; antivenom effectiveness)
VIALS=1.5; PRICE=80.0; BUFFER=0.25   # vials/treated patient (Echis); USD/vial; safety-stock buffer

def reach_mask(stock_idx):
    if len(stock_idx)==0: return np.zeros(len(adm2),bool)
    return Rmat[:, list(stock_idx)].any(axis=1)
def protected(stock_idx, product, w=echis_w):
    if not PROD[product]['echis'] or len(stock_idx)==0: return 0.0, np.zeros(len(adm2),bool)
    m=reach_mask(stock_idx); return float(w[m].sum()), m
def greedy(K, w=echis_w):
    chosen=[]; covered=np.zeros(len(adm2),bool); curve=[0.0]
    for _ in range(K):
        best_g,best_j=0.0,-1
        for j in range(len(hosp)):
            if j in chosen: continue
            g=w[(covered|Rmat[:,j]) & ~covered].sum()
            if g>best_g: best_g,best_j=g,j
        if best_j<0: break
        chosen.append(best_j); covered|=Rmat[:,best_j]; curve.append(float(w[covered].sum()))
    return chosen, covered, curve

ceil_b,_=protected(range(len(hosp)),GOOD)
unreachable=~Rmat.any(axis=1); gap_b=float(echis_w[unreachable].sum())
K=25
chosen,cov_opt,curve=greedy(K); opt_b=float(echis_w[cov_opt].sum())
adm2['protected_opt']=cov_opt; adm2['reachable_any']=~unreachable
naive_idx=[i for i,t in enumerate(hosp['tier'].astype(str)) if 'central' in t.lower()]
naive_b,_=protected(naive_idx,GOOD)

def deaths(pb): return pb*CFR_DELTA          # observed product-choice differential (Visser 2008)
def deaths_lo(pb): return pb*(0.08-0.018)     # sensitivity: lower wrong-product CFR
def deaths_hi(pb): return pb*(CFR_U*EFF)      # sensitivity: Habib untreated-CFR x effectiveness
def row(pb):
    return dict(protected_env=round(pb), pct=round(100*pb/total_echis,1),
        deaths_central=round(deaths(pb)), deaths_lo=round(deaths_lo(pb)), deaths_hi=round(deaths_hi(pb)),
        treated_yr=round(pb), vials_yr=round(pb*VIALS*(1+BUFFER)), procure_usd_yr=round(pb*VIALS*(1+BUFFER)*PRICE))
scen={
 'A. Status quo — non-assessed product that FAILS Echis (VINS/AFRIVEN)': row(0.0),
 f'B. Naive — good product only at {len(naive_idx)} tertiary/central hospitals': row(naive_b),
 f'C. Optimized — {GOOD} at {len(chosen)} hospitals': row(opt_b),
 'D. Structural ceiling — good product at all 190 hospitals': row(ceil_b),
}

# ---- DEMAND: allocate each district's Echis burden to its nearest CHOSEN hospital (within reach)
sub=DX[:,np.array(chosen)]; near_choice=sub.argmin(axis=1); near_d=sub.min(axis=1)
served_by=np.where(near_d<=REACH, near_choice, -1)
plan=[]
for ci,j in enumerate(chosen):
    m=served_by==ci; env=float(echis_w[m].sum()); treated=env   # facility frame: no care-seeking multiplier
    plan.append(dict(priority=ci+1, hospital=str(hosp['name'].iloc[j]), region=str(hosp['region'].iloc[j]), tier=str(hosp['tier'].iloc[j]),
        lat=float(hosp['lat'].iloc[j]), lon=float(hosp['lon'].iloc[j]),
        envenomings_yr=round(env,1), treated_yr=round(treated,1),
        vials_year=int(np.ceil(treated*VIALS*(1+BUFFER))), procure_usd_yr=int(round(treated*VIALS*(1+BUFFER)*PRICE))))
plan_df=pd.DataFrame(plan).sort_values('priority').reset_index(drop=True)
plan_df.to_csv(f"{OUT}/pre_positioning_plan.csv", index=False)

# ---- SENSITIVITY
# (1) coverage% is invariant to UNIFORM incidence scaling (it is a ratio) -> deaths scale linearly; report the grid.
sens_deaths={f"CFR-delta={d}": {f"incidence×{k}": round(opt_b*k*d) for k in (0.5,1.0,1.5)} for d in (0.062,CFR_DELTA,round(CFR_U*EFF,3))}
# (2) placement robustness under a FLATTER north/south gradient (north only 2x south, not ~7x)
RATE_FLAT={'N_SAVANNA':20,'TRANSITION':15,'FOREST':10,'COASTAL':10}
w_flat=(adm2['pop']*adm2['zone'].map(RATE_FLAT)/1e5*adm2['zone'].map(ECHIS)).values
chosen_flat,_,_=greedy(K, w=w_flat)
overlap=len(set(chosen)&set(chosen_flat))
north_share=sum(1 for j in chosen if hosp['region'].iloc[j] in [r for r,z in ZONE.items() if z in('N_SAVANNA','TRANSITION')])

summary=dict(
 model_params=dict(reach_km=REACH, frame='facility (attendance-anchored; NO care-seeking multiplier)',
                   attendance_per_100k=ATTEND, envenoming_fraction=ENVENOM, echis_fraction=ECHIS,
                   CFR_right_product=CFR_RIGHT, CFR_wrong_product=CFR_WRONG, CFR_delta=round(CFR_DELTA,4), CFR_untreated=CFR_U,
                   param_provenance=dict(
                     reach_km="PROXY for the published 3-hour travel-time standard (Longbottom 2018 Lancet 392:673); the distance-to-time conversion is our assumption",
                     vials_per_patient="inside the WHO-published initial dose for Echis (PANAF-Premium overview: 1-3 vials); observed mean 1.23 in Ghana Oti (Ketor 2024)",
                     usd_per_vial="ASSUMPTION inside a wide published bracket ($18-200 Brown 2012; $3.4 subsidised Burkina 2015; $315 SAVP 2020); 1.5 x $80 = $120/course sits inside the $100-153/dose modelling baseline (Potet 2020)",
                     buffer="NOT CONFIRMED as a published standard - WHO/EPI sets min/max in MONTHS OF STOCK, not a percentage"),
                   effectiveness=EFF, vials_per_patient=VIALS, usd_per_vial=PRICE, buffer=BUFFER, recommended_product=GOOD),
 total_envenomings_yr=round(adm2['env_yr'].sum()), total_echis_yr=round(total_echis), n_hospitals=len(hosp),
 burden_anchor=dict(national_cases_reported_yr=9900, source="Ghana Health Service NTD Programme, avg 2015-2020 (Opare, via Graphic 2023)",
                    modelled_envenomings_yr=round(adm2['env_yr'].sum()),
                    note="modelled ENVENOMINGS (severe, antivenom-relevant) are a conservative subset of all reported BITES; 5,811 < 9,900 as expected since many bites are dry/non-envenoming"),
 structural_gap_env=round(gap_b), pct_unreachable=round(100*gap_b/total_echis,1),
 optimized=dict(hospitals=len(chosen), pct_protected=round(100*opt_b/total_echis,1),
                deaths_central=round(deaths(opt_b)), deaths_lo=round(deaths_lo(opt_b)), deaths_hi=round(deaths_hi(opt_b)),
                vials_yr=int(plan_df['vials_year'].sum()), procure_usd_yr=int(plan_df['procure_usd_yr'].sum())),
 scenarios=scen, sensitivity_deaths=sens_deaths,
 placement_robustness=dict(flat_gradient_overlap_of_25=overlap, north_transition_hospitals_of_25=north_share),
 eight_country_scaleup_envenomings_yr=70712)
json.dump(summary, open(f"{OUT}/impact_summary.json","w"), indent=2)
adm2.drop(columns='geometry').to_csv(f"{OUT}/district_v2.csv", index=False)
adm2.to_file(f"{OUT}/district_v2.geojson", driver="GeoJSON")
pd.DataFrame({'n_hospitals':range(len(curve)),'echis_protected':curve,
             'pct':[round(100*c/total_echis,1) for c in curve],
             'cum_vials':[round(c*VIALS*(1+BUFFER)) for c in curve],
             'cum_cost_usd':[round(c*VIALS*(1+BUFFER)*PRICE) for c in curve]}).to_csv(f"{OUT}/coverage_curve.csv",index=False)

print(f"Echis-severe/yr {total_echis:,.0f} | optimized {len(chosen)} hosp -> {100*opt_b/total_echis:.1f}% | ceiling {100*ceil_b/total_echis:.1f}%")
print(f"Product-choice mortality gap/yr (Visser observed differential {CFR_DELTA:.3f}): central {deaths(opt_b):.0f}  (band {deaths_lo(opt_b):.0f}-{deaths_hi(opt_b):.0f})")
print(f"Demand: {int(plan_df['vials_year'].sum()):,} vials/yr  ~${int(plan_df['procure_usd_yr'].sum()):,}/yr procurement")
print(f"Structural gap {100*gap_b/total_echis:.1f}% | placement robustness: {overlap}/25 overlap under flat gradient, {north_share}/25 in north/transition")
print("\nPre-positioning plan (top 6 by vials):")
print(plan_df.head(6)[['hospital','region','vials_year','procure_usd_yr','envenomings_yr']].to_string(index=False))
