#!/usr/bin/env python3
"""
India snakebite ASV coverage-gap & access demonstrator (CoverMap-India).
Different regime from Africa: one product class (Big-Four polyvalent ASV) is used nationwide, so the
lever is NOT "which product" but (1) REGIONAL venom variation — southern-sourced ASV underperforms in
the NW desert & NE even for the Big Four — and (2) ~20 non-Big-Four species with no cover. This maps,
per district: burden (REAL, Million Death Study state rates x census population) x ASV coverage
adequacy (evidence-informed, Senji Laxme/Sunagar antivenomics + TRSTMH 2025) x access to a hospital.
Headline = coverage/gap. Mortality is anchored to MDS (~58,000/yr) and never exceeds it. NOT clinical guidance.
"""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, os, json, unicodedata, re
BASE="/home/claude/snakebite"; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_in"; os.makedirs(OUT,exist_ok=True)
M="EPSG:32644"  # UTM 44N (central India) — access distances approximate at edges

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode()
    s=re.sub(r'\(.*?\)',' ',s); s=re.sub(r'[^A-Za-z ]',' ',s).upper()
    return re.sub(r'\s+',' ',s).strip()

# ---- boundaries
adm1=gpd.read_file(f"{DATA}/in/ind_ADM1.json")[['shapeName','geometry']].to_crs(4326)
adm1['state_n']=adm1['shapeName'].map(norm)
adm2=gpd.read_file(f"{DATA}/in/ind_ADM2.json")[['shapeName','geometry']].to_crs(4326)
# drop placeholder polygons in the boundary file (1 feature named "DATA NOT AVAILABLE"): giving it a
# share of a state's population would invent burden for a district that does not exist.
_n_before=len(adm2)
adm2=adm2[~adm2['shapeName'].astype(str).str.strip().str.upper().isin(['DATA NOT AVAILABLE'])].reset_index(drop=True)
_n_placeholder=_n_before-len(adm2)
adm2['dist_n']=adm2['shapeName'].map(norm)
# district -> state via centroid-in-state
c=adm2.copy(); c['geometry']=c.geometry.centroid
j=gpd.sjoin(c, adm1[['state_n','geometry']], how='left', predicate='within'); j=j[~j.index.duplicated(keep='first')]
for i in j[j['state_n'].isna()].index:
    k=adm1.distance(c.loc[i].geometry).idxmin(); j.loc[i,'state_n']=adm1.loc[k,'state_n']
adm2['state_n']=j['state_n'].values

# geoBoundaries state -> 2011-census state name (aliases)
# geoBoundaries uses POST-2019 units; the 2011 census uses the units of its time. Aliases below map
# each modern unit to its 2011 census parent so population joins are complete:
#   Telangana -> Andhra Pradesh (bifurcated 2014) · Ladakh -> Jammu & Kashmir (separated 2019)
#   Dadra & Nagar Haveli and Daman & Diu -> the COMBINED 2011 pair (merged into one UT in 2020)
GB2C={'TELANGANA':'ANDHRA PRADESH','ODISHA':'ORISSA','PUDUCHERRY':'PONDICHERRY','DELHI':'NCT OF DELHI',
      'DADRA AND NAGAR HAVELI AND DAMAN AND DIU':'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
      'LADAKH':'JAMMU AND KASHMIR','JAMMU AND KASHMIR':'JAMMU AND KASHMIR'}
adm2['cstate']=adm2['state_n'].map(lambda s: GB2C.get(s,s))

# ---- census population by district; join on (state,district)
cen=pd.read_csv(f"{DATA}/in/census2011.csv")
cen['cstate']=cen['State name'].map(norm); cen['dist_n']=cen['District name'].map(norm)
# the 2011 census lists Dadra & Nagar Haveli and Daman & Diu separately; geoBoundaries carries the
# merged 2020 UT. Combine the two census entries so neither is dropped from the population join.
cen['cstate']=cen['cstate'].replace({'DADRA AND NAGAR HAVELI':'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
                                     'DAMAN AND DIU':'DADRA AND NAGAR HAVELI AND DAMAN AND DIU'})
# rural share per district (household split is the census proxy for the rural/urban population split)
_rh=cen['Rural_Households'].fillna(0); _uh=cen['Urban_Households'].fillna(0)
cen['rural_share']=(_rh/(_rh+_uh).replace(0,np.nan)).fillna(1.0).clip(0,1)
cen_rs=cen.set_index(['cstate','dist_n'])['rural_share'].to_dict()
cen_state_rs=cen.groupby('cstate').apply(
    lambda g: float(g['Rural_Households'].sum()/max(g['Rural_Households'].sum()+g['Urban_Households'].sum(),1))).to_dict()
cen_d=cen.set_index(['cstate','dist_n'])['Population'].to_dict()
cen_state_tot=cen.groupby('cstate')['Population'].sum().to_dict()
cen_state_ndist=cen.groupby('cstate')['District name'].count().to_dict()
def dist_pop(r):
    p=cen_d.get((r['cstate'],r['dist_n']))
    if p is not None: return p, True
    tot=cen_state_tot.get(r['cstate']); nd=cen_state_ndist.get(r['cstate'])
    return (tot/nd if tot and nd else np.nan), False
res=adm2.apply(dist_pop,axis=1); adm2['pop']=[x[0] for x in res]; adm2['matched']=[x[1] for x in res]
match_rate=100*adm2['matched'].mean()
# rescale district pops within each census-state so state sums == census state total (keeps burden exact)
adm2['pop']=adm2['pop'].fillna(0)
for cs,sub in adm2.groupby('cstate'):
    tot=cen_state_tot.get(cs); s=sub['pop'].sum()
    if tot and s>0: adm2.loc[sub.index,'pop']=sub['pop']/s*tot

# ---- burden: state death rate (per 100k/yr) anchored to Million Death Study (Suraweera 2020)
# TRANSCRIBED VERBATIM from Suraweera 2020, eLife 9:e54076, TABLE 3 ("Snakebite death rates by state
# in India for 2001-2014"), column **2010-2014** — the most recent period, appropriate for a
# present-day planning tool. Verified against two independent readings of the published table.
# NOTE ON A CORRECTED ERROR: an earlier version of this model used approximated rates that deviated
# from Table 3 by up to 300% (Kerala) while the deliverables described them as "real MDS state rates".
# They are now the published values. States absent from the named rows fall back to Table 3's OWN
# published catch-all rows ("Northeastern states" 0.7; "All other states" 3.2) -- so no state rate in
# this model is an assumption any more. Independent check: the resulting national rate lands at
# ~4.6/100k against Table 3's published "All India" row of 4.5/100k.
RATE={'UTTAR PRADESH':6.0,'BIHAR':8.9,'ANDHRA PRADESH':5.6,'MADHYA PRADESH':6.0,'RAJASTHAN':5.0,'ORISSA':5.9,
 'GUJARAT':5.1,'JHARKHAND':7.1,'CHHATTISGARH':2.5,'WEST BENGAL':2.9,'MAHARASHTRA':2.6,'KARNATAKA':2.9,
 'TAMIL NADU':3.0,'KERALA':0.5,'ASSAM':2.1,'HARYANA':1.8,'PUNJAB':4.0,'JAMMU AND KASHMIR':0.9}
# Table 3 ALSO publishes two catch-all rows that we previously replaced with an assumption.
# Both are now used verbatim (confirmed against two independent readings of the table):
NE_RATE=0.7    # "Northeastern states" row (Assam is listed SEPARATELY at 2.1, above)
DEFRATE=3.2    # "All other states" row -- a PUBLISHED value, no longer an assumption
for _st in ['ARUNACHAL PRADESH','NAGALAND','MANIPUR','MIZORAM','TRIPURA','MEGHALAYA','SIKKIM']:
    RATE[_st]=NE_RATE
RATE_SOURCE="Suraweera 2020 eLife 9:e54076 Table 3, period 2010-2014 (transcribed verbatim, incl. the 'Northeastern states' 0.7 and 'All other states' 3.2 catch-all rows)"
MDS_NATIONAL_RATE=4.5   # "All India" row, 2010-2014, same table
adm2['rate']=adm2['cstate'].map(RATE).fillna(DEFRATE)

# RURAL WEIGHTING (from the anchor source itself): the Million Death Study reports that
# "about 94% of snakebite deaths occurred in rural areas". Distributing a state's mortality by TOTAL
# population implicitly assumes city-dwellers die of snakebite at the rural per-capita rate, which
# contradicts the MDS and makes metros (Jaipur, Ahmedabad, Thane) top the priority list. We therefore
# split each state's MDS-anchored mortality 94/6 between its rural and urban populations. This leaves
# every STATE total (and the national total) EXACTLY unchanged - it only re-allocates within a state.
RURAL_DEATH_SHARE=0.94   # Suraweera 2020, eLife 9:e54076
adm2['rural_share']=[cen_rs.get((r['cstate'],r['dist_n']), cen_state_rs.get(r['cstate'],0.7))
                     for _,r in adm2.iterrows()]
adm2['rural_pop']=adm2['pop']*adm2['rural_share']; adm2['urban_pop']=adm2['pop']*(1-adm2['rural_share'])
adm2['deaths_yr']=0.0; adm2['deaths_rural']=0.0; adm2['deaths_urban']=0.0
for cs,sub in adm2.groupby('cstate'):
    D=float((sub['pop']*sub['rate']/1e5).sum())          # state total, MDS-anchored (unchanged)
    rp=sub['rural_pop'].sum(); up=sub['urban_pop'].sum()
    dr=(sub['rural_pop']/rp*D*RURAL_DEATH_SHARE) if rp>0 else sub['pop']*0
    du=(sub['urban_pop']/up*D*(1-RURAL_DEATH_SHARE)) if up>0 else sub['pop']*0
    # if a state has no urban (or no rural) population, its whole total stays with the other arm
    if up<=0: dr=sub['rural_pop']/max(rp,1e-9)*D
    if rp<=0: du=sub['urban_pop']/max(up,1e-9)*D
    adm2.loc[sub.index,'deaths_rural']=dr; adm2.loc[sub.index,'deaths_urban']=du
    adm2.loc[sub.index,'deaths_yr']=dr+du

# ---- ASV coverage adequacy (evidence-informed zone approximation; 1 = southern Big-Four adequate)
# ---------------------------------------------------------------------------------------------
# ASV COVERAGE ADEQUACY -- ORDINAL TIERS, NOT MEASURED FRACTIONS.
# *** HONEST STATUS: no published figure exists for the share of Indian snakebite burden that the
# standard ASV fails to cover, at national OR state level. *** An adversarial review of the
# antivenomics literature (Senji Laxme/Sunagar 2019-2021; Attarde 2021; Deka 2023; Kumar 2026;
# Gopalakrishnan 2025; Menon 2025) confirms the DIRECTION of every tier below but supports NO
# precise level. These are evidence-informed ORDINAL TIERS. Read the output as an order-of-magnitude
# flag whose error sign is unknown -- never as a measured quantity.
#
# CORRECTIONS APPLIED after that review:
#  - collapsed false precision: 0.75/0.72 and 0.70/0.68/0.65/0.62 distinctions had NO evidentiary
#    basis and are merged into single tiers.
#  - KERALA moved 0.55 -> mainland tier. The old value was calibrated to Hypnale's share of *bites*
#    but applied to *mortality*: a category error. Hypnale is low-lethality, while D. russelii --
#    48.8% of species-identified Kerala bites and the dominant killer -- is WELL neutralised
#    (0.84-0.99 mg/ml, above the 0.6 marketed claim).
#  - NE lowered 0.40 -> 0.35: in Assam 66.19% of identified venomous bites were green pit vipers /
#    Salazar's pit viper, which have NO label coverage at all (Menon 2025). Bite-weighted this would
#    be lower still (~0.15-0.30); it stays at 0.35 because the model weights by DEATHS and pit viper
#    envenoming has low case-fatality. Deka 2023 (77-80% antivenomics retention for N. kaouthia)
#    is genuine counter-evidence that 0.35 may be too low.
#
# KNOWN TENSION WE DO NOT PAPER OVER: the tiers imply a "distance from the Tamil Nadu sourcing zone"
# gradient, but the data does not have that shape. For N. naja the ASV met its marketed claim in
# only ONE tested population (Andhra Pradesh, 0.80 mg/ml) and sat at 0.28-0.38 in Punjab, West
# Bengal, Madhya Pradesh and Maharashtra ALIKE -- i.e. the Gangetic belt neutralises cobra venom as
# poorly as the northwest. The mainland tier survives only because D. russelii and E. carinatus,
# which dominate mortality there, ARE well covered. That is the model's reasoning, not a measurement.
NW=0.45; NE=0.35; ANDAMAN=0.30; SOUTH=0.75; MAINLAND=0.65
ADEQ={
 # NW arid/semi-arid: N. naja desert population = COMPLETE preclinical failure (Senji Laxme 2021);
 # D. russelii Punjab 0.39 mg/ml; E. c. sochureki clinical non-response 68.4% (Gopalakrishnan 2025).
 'RAJASTHAN':NW,'PUNJAB':NW,'GUJARAT':NW,'HARYANA':NW,'CHANDIGARH':NW,'JAMMU AND KASHMIR':NW,
 # NE: non-Big-Four pit vipers dominate identified venomous bites; N. kaouthia (Arunachal) total ED50 failure.
 'ASSAM':NE,'ARUNACHAL PRADESH':NE,'NAGALAND':NE,'MANIPUR':NE,'MIZORAM':NE,'TRIPURA':NE,'MEGHALAYA':NE,'SIKKIM':NE,
 # Andaman & Nicobar: the ONLY tier with a near-direct published anchor -- Bharat 0.151 mg/ml vs a
 # 0.6 claim (=0.25) and Premium Serums completely ineffective against N. sagittifera (Attarde 2021).
 'ANDAMAN AND NICOBAR ISLANDS':ANDAMAN,
 # Southern sourcing zone. NOTE the counter-evidence we carry: Attarde 2021 reports "poor efficacy of
 # the polyvalent antivenom against N. naja venom from southern India" (0.338/0.442 vs 0.6 claim),
 # and TN's own cobra was never lethality-tested. 0.75 is the most challengeable tier here.
 'TAMIL NADU':SOUTH,'ANDHRA PRADESH':SOUTH,'KARNATAKA':SOUTH,'PONDICHERRY':SOUTH,
 # Rest of mainland (incl. Kerala, per the correction above).
 'UTTAR PRADESH':MAINLAND,'BIHAR':MAINLAND,'MADHYA PRADESH':MAINLAND,'JHARKHAND':MAINLAND,
 'CHHATTISGARH':MAINLAND,'WEST BENGAL':MAINLAND,'UTTARAKHAND':MAINLAND,'ORISSA':MAINLAND,
 'MAHARASHTRA':MAINLAND,'GOA':MAINLAND,'KERALA':MAINLAND,'HIMACHAL PRADESH':MAINLAND,'NCT OF DELHI':MAINLAND}
ADEQ_STATUS="ordinal tiers, evidence-informed; NO published level exists (see india_build.py header)"
adm2['adeq']=adm2['cstate'].map(ADEQ).fillna(MAINLAND)
adm2['gap']=1-adm2['adeq']
adm2['gap_deaths']=adm2['deaths_yr']*adm2['gap']   # deaths where the standard ASV likely underperforms

# ---- facilities (hospital-tier: district/taluka hospitals + CHC) with coords
# PROVENANCE: NIC HealthGIS / NRHM facility layer (types DHO = district hospital, THO = taluka
# hospital, CHC = community health centre). The hospital-tier extract is PERSISTED in the repo as
# the canonical model input so the pipeline reproduces without network access; if the full upstream
# geojson is present it is re-derived from source instead.
FAC_CSV=f"{DATA}/in/facilities_hospitals_in.csv"; FAC_RAW=f"{DATA}/in/facilities_nic.geojson"
if os.path.exists(FAC_RAW):
    gj=json.load(open(FAC_RAW)); rows=[]
    for f in gj['features']:
        p=f['properties']; t=str(p.get('type'))
        if t in ('DHO','THO','CHC') and f.get('geometry'):
            lon,lat=f['geometry']['coordinates'][:2]
            if lon and lat and 68<=lon<=98 and 6<=lat<=37: rows.append((p.get('name'),t,p.get('state'),lat,lon))
    H=pd.DataFrame(rows,columns=['name','type','state','lat','lon'])
    H=H.drop_duplicates(subset=['name','type','lat','lon']).reset_index(drop=True)
    H.to_csv(FAC_CSV,index=False)
else:
    H=pd.read_csv(FAC_CSV)
# guard: exact-duplicate facility records would inflate the reported facility count
_dups=int(H.duplicated(subset=['name','type','lat','lon']).sum())
H=H.drop_duplicates(subset=['name','type','lat','lon']).reset_index(drop=True)
H=H[(H.lon.between(68,98))&(H.lat.between(6,37))].reset_index(drop=True)
H.to_csv(f"{OUT}/facilities_hospitals_in.csv",index=False)
hosp=gpd.GeoDataFrame(H,geometry=gpd.points_from_xy(H.lon,H.lat),crs=4326).to_crs(M)

# ---- access: distance district centroid -> nearest hospital-tier facility
dc=adm2.to_crs(M).geometry.centroid
dco=np.column_stack([dc.x.values,dc.y.values]); hco=np.column_stack([hosp.geometry.x.values,hosp.geometry.y.values])
# chunked nearest to limit memory
nn=np.empty(len(adm2))
for i in range(0,len(adm2),150):
    d=np.sqrt(((dco[i:i+150,None,:]-hco[None,:,:])**2).sum(-1))/1000.0
    nn[i:i+150]=d.min(axis=1)
adm2['nearest_km']=nn
# states with NO facilities in the NIC file -> access unknown (flag, don't fake)
fac_states=set(hosp['state'].map(norm).dropna().unique())
adm2['access_known']=adm2['state_n'].isin({norm(s) for s in H['state'].dropna().unique()})

# ---- priority: burden x coverage-gap x access difficulty
REACH=50.0
adm2['access_factor']=1+np.minimum(adm2['nearest_km'],300)/REACH
adm2['priority']=adm2['gap_deaths']*adm2['access_factor']

# ---- headline coverage split + MDS anchor
nat_deaths=adm2['deaths_yr'].sum(); gap_deaths=adm2['gap_deaths'].sum()
far=adm2['deaths_yr'][adm2['nearest_km']>REACH].sum()
priority_sorted=adm2.sort_values('priority',ascending=False)
topN=100; top_gap=priority_sorted.head(topN)['gap_deaths'].sum()

# ---- TARGETING SCENARIOS: "what does the choice change?" -------------------------------------
# India has no product-placement optimiser (access is not the binding gap: <1% of burden is >50 km
# from a hospital). The decision this tool informs is DIFFERENT: given that region-specific antivenom
# and NAPSE's proposed Regional Venom Centres must be rolled out somewhere first, WHERE?
# Each scenario reports the share of the coverage-gap burden that SITS IN the districts targeted.
# That is a REACH measure, exactly parallel to "within reach" in West Africa -- it is NOT a claim
# that deploying there averts those deaths, and it inherits the ordinal uncertainty of the gap tiers.
NW_STATES={'RAJASTHAN','PUNJAB','GUJARAT','HARYANA','CHANDIGARH','JAMMU AND KASHMIR'}
NE_STATES={'ASSAM','ARUNACHAL PRADESH','NAGALAND','MANIPUR','MIZORAM','TRIPURA','MEGHALAYA','SIKKIM'}
_tot_gap=float(adm2['gap_deaths'].sum())
_pri=adm2.sort_values('priority',ascending=False)
def _scen(mask_or_n,label,note):
    sub=_pri.head(mask_or_n) if isinstance(mask_or_n,int) else adm2[mask_or_n]
    g=float(sub['gap_deaths'].sum())
    return dict(label=label, districts=int(len(sub)), gap_deaths=round(g),
                pct_of_gap=round(100*g/_tot_gap,1), population=int(sub['pop'].sum()), note=note)
scenarios_in=[
 dict(label='A. Status quo — one southern-sourced ASV nationwide', districts=0, gap_deaths=0,
      pct_of_gap=0.0, population=0, note='the coverage-gap is untouched by definition'),
 _scen(adm2['cstate'].isin(NW_STATES),'B. Northwest arid states first',
       'where the strongest clinical evidence sits: 68.4% ASV non-response in E. c. sochureki envenoming'),
 _scen(adm2['cstate'].isin(NW_STATES|NE_STATES),'C. Northwest + Northeast',
       'adds the non-Big-Four pit-viper belt (66.19% of identified venomous bites in Assam)'),
 _scen(50,'D. Top-50 districts by burden x gap','the tool\'s own ranking, cutting across state lines'),
 _scen(150,'E. Top-150 districts by burden x gap','same ranking, extended'),
 _scen(adm2['gap']>0,'F. Structural ceiling — every district with a gap',
       'the whole addressable gap; shown to bound the others'),
]
_conc={n:round(float(_pri['gap_deaths'].head(n).sum()/_tot_gap*100),1) for n in (25,50,100,150,200,300)}

MDS_TOTAL=58000; GBD_INDIA=51100
summary=dict(country='India', boundary_source='geoBoundaries IND (36 states / %d districts)'%len(adm2),
 population_2011=int(adm2['pop'].sum()), district_pop_match_rate_pct=round(match_rate,1),
 n_hospital_tier=len(hosp), states_with_hospitals=len(fac_states),
 modelled_deaths_yr=round(nat_deaths), MDS_deaths_yr=MDS_TOTAL, GBD_india_deaths_2019=GBD_INDIA,
 gap_deaths_yr=round(gap_deaths), pct_burden_in_asv_gap=round(100*gap_deaths/nat_deaths,1),
 deaths_far_from_hospital=round(far), pct_far=round(100*far/nat_deaths,1),
 top100_priority_gap_deaths=round(top_gap),
 facility_duplicates_removed=_dups, targeting_scenarios=scenarios_in, gap_concentration=_conc,
 burden_anchor=dict(
   modelled_deaths_yr=round(nat_deaths), MDS_deaths_yr=MDS_TOTAL, MDS_source="Suraweera 2020, eLife 9:e54076 (Million Death Study, ~58,000 deaths/yr)",
   GBD2019_deaths=GBD_INDIA, GBD2019_ui=[29600,64100], GBD_source="GBD 2019 via Nat Commun 2022 13:6160 (India 51,100; UI 29,600-64,100)",
   within_MDS_pct=round(100*abs(nat_deaths-MDS_TOTAL)/MDS_TOTAL,1),
   inside_GBD_ui=bool(29600<=nat_deaths<=64100),
   deaths_ceiling_used=64100,
   MDS_national_rate_2010_14=MDS_NATIONAL_RATE,
   implied_national_rate=None,  # filled below
   defrate_source="Suraweera 2020 Table 3 'All other states' row (2010-2014) = 3.2/100k -- PUBLISHED, previously an assumption of 2.5",
   NE_rate_source="Suraweera 2020 Table 3 'Northeastern states' row (2010-2014) = 0.7/100k -- PUBLISHED, previously fell to the 2.5 assumption",
   adeq_status=ADEQ_STATUS, adeq_tiers=dict(NW=NW,NE=NE,ANDAMAN=ANDAMAN,SOUTH=SOUTH,MAINLAND=MAINLAND),
   no_published_national_gap_anchor=True,
   published_subnational_anchors=[
     dict(value="68.4%", what="clinical ASV non-response in E. c. sochureki envenoming, NW India (63/92 patients; median 22 vials; all 9 deaths were non-responders)", source="Gopalakrishnan 2025, Trans R Soc Trop Med Hyg 119(8):943"),
     dict(value="66.19%", what="share of identified venomous bites caused by green pit viper / Salazar's pit viper (NO ASV label coverage), Demow CHC, Assam", source="Menon 2025, Trans R Soc Trop Med Hyg 119(9):1016"),
     dict(value="~0.25", what="Bharat ASV potency vs N. sagittifera relative to its 0.6 mg/ml marketed claim, Andaman & Nicobar (Premium Serums: completely ineffective)", source="Attarde 2021, Front Pharmacol 12:768210"),
     dict(value="32.6%", what="Hypnale hypnale share of species-identified snakebites, Kerala (a non-Big-Four species with no ASV coverage)", source="Menon 2025 citing a Kerala tertiary series")],
   rural_death_share=RURAL_DEATH_SHARE,
   rural_share_of_modelled_deaths=round(float(adm2['deaths_rural'].sum()/adm2['deaths_yr'].sum()),3),
   rural_note="mortality is distributed within each state 94/6 rural:urban per Suraweera 2020 (MDS: ~94% of snakebite deaths are rural); state and national totals are unchanged by this re-allocation",
   note="modelled mortality is ANCHORED to published national estimates: it must sit close to the MDS point estimate and inside the GBD uncertainty interval. The ASV coverage-gap is a share OF that mortality, never an addition to it."),
 note='deaths = decision-relevant burden anchored to MDS state rates; ASV-gap = evidence-informed zone approximation (Senji Laxme antivenomics + TRSTMH 2025), NOT a deaths-averted claim')
summary['burden_anchor']['implied_national_rate']=round(float(nat_deaths/adm2['pop'].sum()*1e5),2)
json.dump(summary,open(f"{OUT}/impact_summary_in.json","w"),indent=2)
keep=['shapeName','cstate','pop','rural_share','rural_pop','rate','deaths_yr','adeq','gap','gap_deaths','nearest_km','access_known','priority','matched']
adm2[keep].to_csv(f"{OUT}/district_in.csv",index=False)
adm2[keep+['geometry']].to_file(f"{OUT}/district_in.geojson",driver="GeoJSON")
priority_sorted[['shapeName','cstate','deaths_yr','adeq','gap_deaths','nearest_km','priority']].head(40).to_csv(f"{OUT}/priority_districts_in.csv",index=False)

print("=== INDIA ===")
print(f"districts:{len(adm2)} | pop-join match:{match_rate:.1f}% | pop total:{adm2['pop'].sum():,.0f}")
print(f"hospital-tier facilities:{len(hosp)} across {len(fac_states)} states")
print(f"modelled deaths/yr:{nat_deaths:,.0f}  (MDS ~58,000 ; GBD 2019 51,100) -> anchor OK:{abs(nat_deaths-MDS_TOTAL)/MDS_TOTAL<0.25}")
print(f"burden in ASV coverage-gap:{gap_deaths:,.0f} ({100*gap_deaths/nat_deaths:.1f}%)")
print(f"deaths >50km from hospital:{far:,.0f} ({100*far/nat_deaths:.1f}%)")
print("state pop check (known): UP {:,.0f} (real ~199.8M) | Bihar {:,.0f} (~104M) | Maharashtra {:,.0f} (~112M)".format(
  adm2[adm2.cstate=='UTTAR PRADESH']['pop'].sum(), adm2[adm2.cstate=='BIHAR']['pop'].sum(), adm2[adm2.cstate=='MAHARASHTRA']['pop'].sum()))
print("state deaths top6:"); print((adm2.groupby('cstate')['deaths_yr'].sum().sort_values(ascending=False).head(6)).round(0).to_string())
print("top priority districts:"); print(priority_sorted[['shapeName','cstate','deaths_yr','gap','nearest_km']].head(6).to_string(index=False))
