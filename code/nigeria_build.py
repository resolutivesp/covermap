#!/usr/bin/env python3
"""
Nigeria pre-positioning demonstrator (CoverMap) — mirrors the Ghana model with Nigeria data.
Nigeria: highest West-African snakebite burden; the Middle Belt (Kaltungo/Gombe/Benue) is the
Echis ocellatus epicentre; Habib's cost-effectiveness anchors are Nigerian. Same West-African
coverage matrix and product menu (PANAF-Premium recommended). NOT clinical guidance.
"""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, os, json, subprocess
BASE="/home/claude/snakebite"; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_ng"; os.makedirs(OUT,exist_ok=True); os.makedirs(f"{DATA}/ng",exist_ok=True)
M="EPSG:32632"  # UTM 32N covers Nigeria

# ---- 1. boundaries (geoBoundaries via Git LFS host)
mb="https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/NGA"
for lvl in ["ADM1","ADM2"]:
    f=f"{DATA}/ng/nga_{lvl}.json"
    if not os.path.exists(f) or os.path.getsize(f)<5000:
        subprocess.run(["curl","-sL","--max-time","120","-o",f,f"{mb}/{lvl}/geoBoundaries-NGA-{lvl}_simplified.geojson"])
adm1=gpd.read_file(f"{DATA}/ng/nga_ADM1.json")[['shapeName','geometry']].to_crs(4326); adm1['state']=adm1['shapeName'].str.strip()
adm2=gpd.read_file(f"{DATA}/ng/nga_ADM2.json")[['shapeName','geometry']].to_crs(4326)

# ---- 2. state -> ecological zone
NORTH=['Sokoto','Kebbi','Zamfara','Katsina','Kano','Jigawa','Yobe','Borno']
MIDDLE=['Kaduna','Bauchi','Gombe','Adamawa','Taraba','Niger','Kwara','Kogi','Benue','Plateau','Nasarawa',
        'Federal Capital Territory','Abuja']
def zone_of(state):
    s=str(state)
    if any(n.lower() in s.lower() for n in NORTH): return 'SUDAN_SAVANNA'
    if any(n.lower() in s.lower() for n in MIDDLE): return 'MIDDLE_BELT'
    return 'SOUTH_FOREST'
adm1['zone']=adm1['state'].map(zone_of)
# assign each LGA to its state (centroid within), then zone
c=adm2.copy(); c['geometry']=c.geometry.centroid
j=gpd.sjoin(c, adm1[['state','zone','geometry']], how='left', predicate='within'); j=j[~j.index.duplicated(keep='first')]
for i in j[j['state'].isna()].index:
    k=adm1.distance(c.loc[i].geometry).idxmin(); j.loc[i,['state','zone']]=adm1.loc[k,['state','zone']].values
adm2['state']=j['state'].values; adm2['zone']=j['zone'].values

# ---- 3. population (afripop2020 gives the within-country DISTRIBUTION only; scaled to national total)
from rasterstats import zonal_stats
RASTER=f"{DATA}/ng/afripop2020.tif"
if not os.path.exists(RASTER): RASTER="/tmp/afrilearndata/inst/extdata/afripop2020.tif"  # fallback
zs=zonal_stats(adm2, RASTER, stats="sum")
raw=np.array([max(z['sum'] or 0,0) for z in zs],float)
NG_POP_2020=206_139_589   # World Bank 2020 estimate; afripop gives the within-country distribution only
adm2['pop']=raw/raw.sum()*NG_POP_2020

# ---- 4. incidence & Echis fraction (facility-anchored; Nigerian snakebite literature, conservative)
# ---------------------------------------------------------------------------------------------
# FRAME (corrected v0.4) -- same facility frame as Ghana: attendance -> envenoming -> Echis -> vials.
# HONEST STATUS OF THESE RATES: *** no published per-eco-zone snakebite rate exists for Nigeria. ***
# These are a CONSTRUCTION, not a transcription. An earlier version described them as
# "facility-anchored and calibrated", which overstated their provenance. They are bracketed by:
#   FLOOR   Nigeria FMoH surveillance: 45,834 cases + 1,793 deaths Jan2018-Dec2020 = ~15,278/yr
#           = ~7.6/100k ALL BITES nationally (certainly under-reported).
#   CEILING community studies in savanna foci: ~497-500/100k (Pugh & Theakston 1980; Habib 2013).
#   RANGE   published West Africa envenoming incidence 8.9-93.3/100k (Habib 2013) -- a BOUND on the
#           national implied rate, NOT a confirmation of any zone value.
# OPEN UNCERTAINTY (unresolved, disclosed): the strongest Nigerian community datum (497/100k) is
# attributed to the Benue valley by Habib 2013/2011 but the underlying 1980 Lancet study is generally
# sited at Malumfashi (Katsina) -- i.e. it may belong to SUDAN_SAVANNA, which we rate LOWER than
# MIDDLE_BELT. If so the north-south gradient between our two savanna zones could be inverted.
# We could not obtain the original paper to settle this. The placement conclusion is robust to it
# (both zones are high and both are prioritised), but the split between them is not established.
ATTEND={'MIDDLE_BELT':45,'SUDAN_SAVANNA':28,'SOUTH_FOREST':4}   # facility attendances/100k/yr (CONSTRUCTED)
ENVENOM=0.647   # envenoming fraction (Aglanu 2025, northern Ghana) -- transferred to Nigeria; ASSUMED
RATE={z:ATTEND[z]*ENVENOM for z in ATTEND}
# Echis share of envenomings. SAVANNA 0.85 is SUPPORTED for a facility/severe construct:
#   Habib & Abubakar 2011 (Kaltungo, 6,687 victims) ">90% of the bites were due to E. ocellatus";
#   Habib 2013 hospital series 75%; Pugh & Theakston >=66%.
# SOUTH_FOREST 0.30 is UNSUPPORTED and probably too high: E. ocellatus is a savanna species, largely
#   absent from closed forest, and eastern populations are now assigned to E. romani. Lowered to 0.20.
ECHIS={'MIDDLE_BELT':0.85,'SUDAN_SAVANNA':0.85,'SOUTH_FOREST':0.20}
adm2['env_yr']=adm2['pop']*adm2['zone'].map(RATE)/1e5
adm2['echis_yr']=adm2['env_yr']*adm2['zone'].map(ECHIS)

# ---- 5. hospitals (Maina/WHO, Nigeria hospital-tier)
import rdata, re as _re
RDA=f"{DATA}/ng/df_who_sites.rda"
if not os.path.exists(RDA): RDA="/tmp/afrihealthsites/data/df_who_sites.rda"  # fallback
conv=rdata.read_rda(RDA); df=conv[list(conv)[0]]
if not isinstance(df,pd.DataFrame): df=pd.DataFrame(df)
df=df[df['Country'].astype(str).str.contains('Nigeria',case=False,na=False)].copy()
df=df.rename(columns={'Facility name':'name','Facility type':'ftype','Lat':'lat','Long':'lon','Tier_name':'tier'})
df=df.dropna(subset=['lat','lon']); df=df[(df.lat.between(3.5,14.5))&(df.lon.between(2.0,15.5))]
H=df[df['tier'].astype(str).str.contains('hospital',case=False,na=False)].copy()
# UPSTREAM DATA FIX (documented): 2 facility names in the Maina/WHO source carry a duplicated
# suffix ("... General Hospitaltal"). Repair the obvious duplication only; never rename a facility.
def _fixname(s):
    s=str(s)
    s=_re.sub(r'(?i)\bHospital(?:tal|al)\b','Hospital',s)
    return _re.sub(r'\s{2,}',' ',s).strip()
_n_fixed=int((H['name'].astype(str).map(_fixname)!=H['name'].astype(str)).sum())
H['name']=H['name'].map(_fixname)
H[['name','ftype','tier','lat','lon']].to_csv(f"{DATA}/ng/facilities_hospitals_ng.csv",index=False)
hosp=gpd.GeoDataFrame(H, geometry=gpd.points_from_xy(H.lon,H.lat), crs=4326)
hj=gpd.sjoin(hosp, adm1[['state','geometry']], how='left', predicate='within'); hj=hj[~hj.index.duplicated(keep='first')]
for i in hj[hj['state'].isna()].index:
    k=adm1.distance(hosp.loc[i].geometry).idxmin(); hj.loc[i,'state']=adm1.loc[k,'state']
hosp['state']=hj['state'].values; hosp=hosp.to_crs(M)

# ---- 6. distances / reachability
dc=adm2.to_crs(M).geometry.centroid
dcoords=np.column_stack([dc.x.values,dc.y.values]); hcoords=np.column_stack([hosp.geometry.x.values,hosp.geometry.y.values])
DX=np.sqrt(((dcoords[:,None,:]-hcoords[None,:,:])**2).sum(-1))/1000.0
REACH=50.0; adm2['nearest_km']=DX.min(axis=1); Rmat=DX<=REACH
echis_w=adm2['echis_yr'].values; total_echis=float(echis_w.sum())

# ---- 7. product menu + params (same West-African regime as Ghana; Habib is Nigerian)
GOOD='PANAF-Premium'; PROD_echis={'PANAF-Premium':1}
# Impact: same correction as Ghana -- the facility frame means care-seeking has already happened,
# so multiplying by it again was a double discount. Mortality uses the OBSERVED product-choice
# differential (Visser 2008, rural Ghana: treated-patient CFR 1.8% -> 12.1% under a failing product).
# Transferring a Ghanaian differential to Nigeria is an EXTRAPOLATION and is flagged as such.
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
CFR_RIGHT=0.018; CFR_WRONG=0.121; CFR_DELTA=CFR_WRONG-CFR_RIGHT
CFR_U=0.16; EFF=0.75; VIALS=1.5; PRICE=80.0; BUFFER=0.25

def greedy(K,w=echis_w):
    chosen=[]; covered=np.zeros(len(adm2),bool); curve=[0.0]
    for _ in range(K):
        best_g,best_j=0.0,-1
        for jx in range(len(hosp)):
            if jx in chosen: continue
            g=w[(covered|Rmat[:,jx]) & ~covered].sum()
            if g>best_g: best_g,best_j=g,jx
        if best_j<0: break
        chosen.append(best_j); covered|=Rmat[:,best_j]; curve.append(float(w[covered].sum()))
    return chosen,covered,curve

ceil_reach=Rmat.any(axis=1); ceil_b=float(echis_w[ceil_reach].sum())
gap_b=float(echis_w[~ceil_reach].sum())
MAXK=70; chosen_all,_,curve=greedy(MAXK)
pct=[100*c/total_echis for c in curve]
K85=next((k for k in range(len(pct)) if pct[k]>=85), len(pct)-1)   # hospitals to reach 85%
chosen=chosen_all[:K85]
cov_opt=np.zeros(len(adm2),bool)
for jx in chosen: cov_opt|=Rmat[:,jx]
opt_b=float(echis_w[cov_opt].sum()); adm2['protected_opt']=cov_opt; adm2['reachable_any']=ceil_reach

naive_idx=[i for i,t in enumerate(hosp['tier'].astype(str)) if 'central' in t.lower()]
naive_reach=Rmat[:,naive_idx].any(axis=1) if naive_idx else np.zeros(len(adm2),bool)
naive_b=float(echis_w[naive_reach].sum())

# HARD BOUND: the decision-gap is antivenom-preventable mortality. It CANNOT exceed total national
# snakebite mortality. We cap every reported deaths figure at the highest published upper estimate
# (GBD 2019 Nigeria UI upper = 2,640) and flag when the cap binds, rather than print an impossible number.
DEATH_CEIL=2640
def deaths_raw(pb,d=None): return pb*(CFR_DELTA if d is None else d)
def deaths(pb,d=None): return min(deaths_raw(pb,d), DEATH_CEIL)
def capped(pb,d=None): return deaths_raw(pb,d) > DEATH_CEIL
D_LO=0.062; D_HI=round(CFR_U*EFF,3)   # sensitivity band on the CFR differential
def row(pb): return dict(protected_env=round(pb),pct=round(100*pb/total_echis,1),deaths_central=round(deaths(pb)),
    deaths_lo=round(deaths(pb,D_LO)),deaths_hi=round(deaths(pb,D_HI)),
    deaths_hi_capped=bool(capped(pb,D_HI)),treated_yr=round(pb),
    vials_yr=round(pb*VIALS*(1+BUFFER)),procure_usd_yr=round(pb*VIALS*(1+BUFFER)*PRICE))
scen={'A. Status quo — product that FAILS Echis (Bharat/Indian polyvalent)':row(0.0),
      f'B. Naive — good product only at {len(naive_idx)} tertiary/central hospitals':row(naive_b),
      f'C. Optimized — {GOOD} at {len(chosen)} hospitals':row(opt_b),
      'D. Structural ceiling — good product at all hospitals':row(ceil_b)}

# demand per chosen hospital
sub=DX[:,np.array(chosen)]; nch=sub.argmin(axis=1); nd=sub.min(axis=1); served=np.where(nd<=REACH,nch,-1)
plan=[]
for ci,jx in enumerate(chosen):
    m=served==ci; env=float(echis_w[m].sum()); tr=env   # facility frame: no care-seeking multiplier
    plan.append(dict(priority=ci+1,hospital=str(hosp['name'].iloc[jx]),state=str(hosp['state'].iloc[jx]),
        tier=str(hosp['tier'].iloc[jx]),lat=float(hosp['lat'].iloc[jx]),lon=float(hosp['lon'].iloc[jx]),
        envenomings_yr=round(env,1),vials_year=int(np.ceil(tr*VIALS*(1+BUFFER))),procure_usd_yr=int(round(tr*VIALS*(1+BUFFER)*PRICE))))
plan_df=pd.DataFrame(plan).sort_values('priority').reset_index(drop=True); plan_df.to_csv(f"{OUT}/pre_positioning_plan_ng.csv",index=False)

# robustness: flatter gradient
RATE_F={'MIDDLE_BELT':20,'SUDAN_SAVANNA':15,'SOUTH_FOREST':10}
w_flat=(adm2['pop']*adm2['zone'].map(RATE_F)/1e5*adm2['zone'].map(ECHIS)).values
chosen_flat,_,_=greedy(K85,w=w_flat); overlap=len(set(chosen)&set(chosen_flat))

summary=dict(country='Nigeria',model_params=dict(reach_km=REACH,frame='facility (attendance-anchored; NO care-seeking multiplier)',
    attendance_per_100k=ATTEND,envenoming_fraction=ENVENOM,echis_fraction=ECHIS,
    CFR_right_product=CFR_RIGHT,CFR_wrong_product=CFR_WRONG,CFR_delta=round(CFR_DELTA,4),
    param_provenance=dict(
      reach_km="PROXY for the published 3-hour travel-time standard (Longbottom 2018 Lancet 392:673); the distance-to-time conversion is our assumption",
      vials_per_patient="inside the WHO-published initial dose for Echis (PANAF-Premium overview: 1-3 vials); observed mean 1.23 in Ghana Oti (Ketor 2024)",
      usd_per_vial="ASSUMPTION inside a wide published bracket ($18-200 Brown 2012; $3.4 subsidised Burkina 2015; $315 SAVP 2020)",
      buffer="NOT CONFIRMED as a published standard - WHO/EPI sets min/max in MONTHS OF STOCK, not a percentage"),
    CFR_untreated=CFR_U,effectiveness=EFF,vials_per_patient=VIALS,usd_per_vial=PRICE,buffer=BUFFER,recommended_product=GOOD),
    population_total=round(adm2['pop'].sum()),total_envenomings_yr=round(adm2['env_yr'].sum()),total_echis_yr=round(total_echis),
    n_states=len(adm1),n_lgas=len(adm2),n_hospitals=len(hosp),structural_gap_env=round(gap_b),pct_unreachable=round(100*gap_b/total_echis,1),
    optimized=dict(hospitals=len(chosen),pct_protected=round(100*opt_b/total_echis,1),deaths_central=round(deaths(opt_b)),
        deaths_lo=round(deaths(opt_b,D_LO)),deaths_hi=round(deaths(opt_b,D_HI)),
        vials_yr=int(plan_df['vials_year'].sum()),procure_usd_yr=int(plan_df['procure_usd_yr'].sum())),
    scenarios=scen,placement_robustness=dict(flat_gradient_overlap=overlap,of=K85),
    facility_names_repaired=_n_fixed,
    # URBAN ARTIFACT CHECK: urban LGAs inherit their eco-zone rate, which overstates their snakebite
    # burden (envenoming is rural). We quantify whether that artifact actually distorts the DECISION.
    urban_artifact=dict(
      top_burden_lga=str(adm2.loc[adm2['echis_yr'].idxmax(),'shapeName']),
      top_burden_lga_state=str(adm2.loc[adm2['echis_yr'].idxmax(),'state']),
      top_burden_lga_env=round(float(adm2['echis_yr'].max())),
      max_over_p95_ratio=round(float(adm2['echis_yr'].max()/np.percentile(adm2['echis_yr'],95)),1),
      pct_vials_to_FCT_or_Lagos=round(100*float(plan_df.loc[plan_df['state'].astype(str).str.contains('Abuja|Federal Capital|Lagos',case=False,na=False),'vials_year'].sum())/float(plan_df['vials_year'].sum()),1),
      note="the single highest-burden LGA is an urban artifact (capital city inheriting a rural zone rate); it dominates the colour scale but NOT the plan - see pct_vials_to_FCT_or_Lagos"),
    burden_anchor=dict(
      implied_national_envenoming_rate_per_100k=round(adm2['env_yr'].sum()/adm2['pop'].sum()*1e5,1),
      published_west_africa_rate_range_per_100k=[8.9,93.3],
      published_rate_source="Habib 2013, J Venom Anim Toxins Trop Dis 19:27 (West Africa 8.9-93.3/100k/yr)",
      community_rate_benue_per_100k=497,
      community_rate_note="Benue valley community incidence ~497/100k (Habib 2013) and NE Nigeria ~500/100k (Pugh & Theakston 1980) are ~20x our facility-anchored zone rates -> our burden is a deliberate conservative FLOOR",
      national_deaths_GBD2019=1460, national_deaths_GBD2019_ui=[977,2640],
      national_deaths_Habib2015=1927, national_deaths_Habib2015_ui=[1529,2333],
      deaths_ceiling_used=DEATH_CEIL, deaths_ceiling_binds_in_scenarios=[k for k,v in scen.items() if v['deaths_hi_capped']],
      implied_facility_attendance_per_100k=round(adm2['pop'].mul(adm2['zone'].map(ATTEND)).sum()/adm2['pop'].sum()/1e5*1e5,1),
      FMoH_surveillance_bites_per_100k=7.6,
      FMoH_note="Nigeria FMoH surveillance recorded ~15,278 snakebite cases/yr (2018-2020) = ~7.6/100k. Our constructed attendance rate is ~2.8x that, which assumes substantial surveillance under-reporting (plausible, but ASSUMED).",
      # HONESTY FLAG: the product-choice mortality gap is a worst-case counterfactual. If it exceeds
      # the published CENTRAL national mortality, that is a signal the absolute figure is strained --
      # we surface it rather than tune it away.
      mortality_gap_exceeds_published_central=bool(round(deaths(opt_b))>1927),
      mortality_gap_tension_note="the central product-choice gap exceeds the highest published CENTRAL estimate of Nigeria's TOTAL annual snakebite mortality (Habib 2015: 1,927; GBD 2019: 1,460). It stays under the highest published UPPER bound (2,640) and is a worst-case counterfactual, not an expectation - but it should be read as an upper-bound signal, not a forecast. Nigeria's absolute figures are the least anchored in the project because no published per-eco-zone rate exists.",
      note="decision-gap deaths are bounded by TOTAL national snakebite mortality; the reported upper bound must not exceed the highest published upper estimate (GBD 2019 UI upper = 2,640)"))
json.dump(summary,open(f"{OUT}/impact_summary_ng.json","w"),indent=2)
adm2.drop(columns='geometry').to_csv(f"{OUT}/district_ng.csv",index=False)
adm2.to_file(f"{OUT}/district_ng.geojson",driver="GeoJSON")
pd.DataFrame({'n_hospitals':range(len(curve)),'echis_protected':curve,'pct':[round(p,1) for p in pct],
    'cum_vials':[round(c*VIALS*(1+BUFFER)) for c in curve],'cum_cost_usd':[round(c*VIALS*(1+BUFFER)*PRICE) for c in curve]}).to_csv(f"{OUT}/coverage_curve_ng.csv",index=False)

print("=== NIGERIA ===")
print("states:",len(adm1),"| LGAs:",len(adm2),"| hospitals:",len(hosp),"| pop: {:,.0f}".format(adm2['pop'].sum()))
print("zone LGA counts:",adm2['zone'].value_counts().to_dict())
print("zone pop (M):",{k:round(v/1e6,1) for k,v in adm2.groupby('zone')['pop'].sum().to_dict().items()})
print("envenomings/yr {:,.0f} | Echis-severe/yr {:,.0f}".format(adm2['env_yr'].sum(),total_echis))
print(f"optimized: {len(chosen)} hospitals -> {100*opt_b/total_echis:.1f}% | ceiling {100*ceil_b/total_echis:.1f}% | gap {100*gap_b/total_echis:.1f}%")
print(f"product-choice mortality gap/yr (Visser differential {CFR_DELTA:.3f}; capped at {DEATH_CEIL}) central {deaths(opt_b):.0f} (band {deaths(opt_b,D_LO):.0f}-{deaths(opt_b,D_HI):.0f})")
print(f"  anchor: implied national rate {adm2['env_yr'].sum()/adm2['pop'].sum()*1e5:.1f}/100k (published W-Africa 8.9-93.3) | deaths ceiling GBD-upper 2,640 -> upper {deaths(opt_b,D_HI):.0f} within ceiling: {deaths(opt_b,D_HI)<=2640}")
print(f"  facility names repaired (upstream duplicated suffix): {_n_fixed}")
print(f"demand {int(plan_df['vials_year'].sum()):,} vials/yr ~${int(plan_df['procure_usd_yr'].sum()):,} | robustness {overlap}/{K85}")
print("top plan:"); print(plan_df.head(6)[['hospital','state','vials_year','envenomings_yr']].to_string(index=False))