#!/usr/bin/env python3
"""INDEPENDENT verification of India — reproducibility, MDS anchoring, rural weighting,
state-total invariance, and honesty guardrails."""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, json, re, sys, os
from _paths import BASE, SRC; DATA=f"{BASE}/data"; OUT=f"{BASE}/out_in"
FAIL=[]
def chk(n, ok, d=""):
    print(("  PASS  " if ok else "  FAIL  ")+n+(f"   {d}" if d else ""))
    if not ok: FAIL.append(n)

S=json.load(open(f"{OUT}/impact_summary_in.json")); A=S['burden_anchor']
d=pd.read_csv(f"{OUT}/district_in.csv"); pri=pd.read_csv(f"{OUT}/priority_districts_in.csv")
cen=pd.read_csv(f"{DATA}/in/census2011.csv")

print("\n=== A. REPRODUCIBILITY ===")
chk("canonical facility input persisted in repo", os.path.exists(f"{DATA}/in/facilities_hospitals_in.csv"))
chk("census persisted", os.path.exists(f"{DATA}/in/census2011.csv"))
chk("boundaries persisted", os.path.exists(f"{DATA}/in/ind_ADM1.json") and os.path.exists(f"{DATA}/in/ind_ADM2.json"))
src=open(f"{SRC}/india_build.py").read()
chk("build falls back to the persisted CSV (no hard dependency on the raw geojson)",
    "FAC_CSV" in src and "os.path.exists(FAC_RAW)" in src)
chk("build de-duplicates facilities", "drop_duplicates" in src)

print("\n=== B. POPULATION: state totals must be EXACT ===")
import unicodedata
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode()
    s=re.sub(r'\(.*?\)',' ',s); s=re.sub(r'[^A-Za-z ]',' ',s).upper()
    return re.sub(r'\s+',' ',s).strip()
cen['cstate']=cen['State name'].map(norm).replace(
    {'DADRA AND NAGAR HAVELI':'DADRA AND NAGAR HAVELI AND DAMAN AND DIU',
     'DAMAN AND DIU':'DADRA AND NAGAR HAVELI AND DAMAN AND DIU'})
cst=cen.groupby('cstate')['Population'].sum().to_dict()
bad=[]
for cs,sub in d.groupby('cstate'):
    if cs in cst and abs(sub['pop'].sum()-cst[cs])>2: bad.append((cs,round(sub['pop'].sum()),cst[cs]))
chk("every census-state population is reproduced EXACTLY", not bad, str(bad[:3]))
chk("national population == 2011 census total", abs(d['pop'].sum()-cen['Population'].sum())<50,
    f"{d['pop'].sum():,.0f} vs {cen['Population'].sum():,.0f}")
for nm,exp in [('UTTAR PRADESH',199_812_341),('BIHAR',104_099_452),('MAHARASHTRA',112_374_333)]:
    got=d.loc[d.cstate==nm,'pop'].sum(); chk(f"{nm} population exact", abs(got-exp)<2, f"{got:,.0f} vs {exp:,}")
chk("no NaN anywhere in the district table", d.isna().sum().sum()==0, str(int(d.isna().sum().sum())))

print("\n=== C0. RATE PROVENANCE: state rates must MATCH the published MDS table verbatim ===")
# Suraweera 2020 eLife 9:e54076, Table 3, column 2010-2014 (verified against two independent readings).
# This check exists because an earlier version used approximated rates (Kerala 4x, Chhattisgarh 2.4x off)
# while claiming them as MDS values. It locks the numbers to the source.
MDS_T3_2010_14={'UTTAR PRADESH':6.0,'BIHAR':8.9,'ANDHRA PRADESH':5.6,'MADHYA PRADESH':6.0,'RAJASTHAN':5.0,
 'ORISSA':5.9,'GUJARAT':5.1,'JHARKHAND':7.1,'CHHATTISGARH':2.5,'WEST BENGAL':2.9,'MAHARASHTRA':2.6,
 'KARNATAKA':2.9,'TAMIL NADU':3.0,'KERALA':0.5,'ASSAM':2.1,'HARYANA':1.8,'PUNJAB':4.0,'JAMMU AND KASHMIR':0.9}
bad=[]
for st,exp in MDS_T3_2010_14.items():
    got=d.loc[d.cstate==st,'rate']
    if len(got) and abs(got.iloc[0]-exp)>1e-9: bad.append((st,float(got.iloc[0]),exp))
chk("every modelled state rate equals the published MDS Table 3 value", not bad, str(bad[:4]))
chk("build documents the rate source", "RATE_SOURCE" in src and "Table 3" in src)
chk("catch-all rates use Table 3's OWN published rows (no assumed default remains)",
    "NE_RATE=0.7" in src and "DEFRATE=3.2" in src)
chk("NE states carry the published 'Northeastern states' rate (0.7), not a default",
    all(abs(float(d.loc[d.cstate==st,'rate'].iloc[0])-0.7)<1e-9
        for st in ['NAGALAND','MANIPUR','MIZORAM','TRIPURA','MEGHALAYA','SIKKIM']
        if (d.cstate==st).any()))
chk("implied national rate matches the published All-India row within 5%",
    abs(A['implied_national_rate']-A['MDS_national_rate_2010_14'])/A['MDS_national_rate_2010_14']<0.05,
    f"{A['implied_national_rate']} vs published {A['MDS_national_rate_2010_14']}")

print("\n=== C. MDS ANCHORING (mortality must not be invented) ===")
chk("modelled deaths re-derive from the district file", abs(d['deaths_yr'].sum()-A['modelled_deaths_yr'])<2,
    f"{d['deaths_yr'].sum():,.0f} vs {A['modelled_deaths_yr']:,}")
chk("modelled mortality within 10% of the MDS point estimate", A['within_MDS_pct']<=10, f"{A['within_MDS_pct']}%")
chk("modelled mortality inside the GBD 2019 uncertainty interval", A['inside_GBD_ui'],
    f"{A['modelled_deaths_yr']:,} in [{A['GBD2019_ui'][0]:,},{A['GBD2019_ui'][1]:,}]")
chk("modelled mortality never exceeds the GBD upper bound", A['modelled_deaths_yr']<=A['deaths_ceiling_used'])
chk("gap deaths are a SUBSET of total deaths (never additive)", S['gap_deaths_yr']<A['modelled_deaths_yr'],
    f"{S['gap_deaths_yr']:,} < {A['modelled_deaths_yr']:,}")
chk("gap % re-derives", abs(100*d['gap_deaths'].sum()/d['deaths_yr'].sum()-S['pct_burden_in_asv_gap'])<0.15,
    f"{100*d['gap_deaths'].sum()/d['deaths_yr'].sum():.2f}% vs {S['pct_burden_in_asv_gap']}%")

print("\n=== D. RURAL WEIGHTING (per the MDS's own finding) ===")
chk("rural death share == 0.94 as specified", abs(A['rural_share_of_modelled_deaths']-0.94)<0.005,
    str(A['rural_share_of_modelled_deaths']))
chk("rural_share column exported for audit", 'rural_share' in d.columns)
chk("rural_share within [0,1]", d['rural_share'].between(0,1).all())
# the re-allocation MUST NOT change any state total
srcb=open(f"{SRC}/india_build.py").read()
chk("re-allocation is within-state by construction", "for cs,sub in adm2.groupby('cstate')" in srcb and "RURAL_DEATH_SHARE" in srcb)
# priority list must now be rural-dominated
top10=pri.head(10)
# district names repeat across states (Aurangabad, Balrampur, Bijapur...), so join on BOTH keys
mean_rs=top10.merge(d[['shapeName','cstate','rural_share']],on=['shapeName','cstate'],how='left')['rural_share'].mean()
chk("top-10 priority districts are predominantly rural (mean rural share > 0.6)", mean_rs>0.6, f"mean rural share {mean_rs:.2f}")
metros=['Mumbai','Chennai','Kolkata','Bangalore','Hyderabad','Delhi','Thane','Ahmadabad']
hit=[m for m in metros if m in set(top10['shapeName'])]
chk("no pure metro district in the top-10 priority list", not hit, str(hit))

print("\n=== D2. ADEQ PROVENANCE: must be declared ORDINAL, with published anchors carried ===")
chk("adeq status declares ordinal/no published level", 'ordinal' in A.get('adeq_status','').lower())
chk("summary states no national gap anchor exists", A.get('no_published_national_gap_anchor') is True)
chk("published sub-national anchors are carried", len(A.get('published_subnational_anchors',[]))>=3)
chk("anchors include the NW clinical non-response figure",
    any('68.4' in a['value'] for a in A['published_subnational_anchors']))
chk("anchors include the Assam non-Big-Four figure",
    any('66.19' in a['value'] for a in A['published_subnational_anchors']))
chk("false precision collapsed: at most 5 distinct adequacy tiers",
    d['adeq'].round(3).nunique()<=5, f"{d['adeq'].round(3).nunique()} distinct values")
chk("Kerala moved off the bite-weighted 0.55 (category-error fix)",
    abs(float(d.loc[d.cstate=='KERALA','adeq'].iloc[0])-0.55)>1e-6,
    f"Kerala adeq={float(d.loc[d.cstate=='KERALA','adeq'].iloc[0])}")
srcA=open(f"{SRC}/india_build.py").read()
chk("build documents the known gradient tension", "does not have that shape" in srcA)
chk("build documents the Kerala category-error correction", "category error" in srcA)

print("\n=== D3. TARGETING SCENARIOS: internally consistent and honestly framed ===")
SC=S['targeting_scenarios']; CONC=S['gap_concentration']
chk("scenario block present with a status-quo and a ceiling row", len(SC)>=5 and SC[0]['pct_of_gap']==0.0 and any(x['pct_of_gap']==100.0 for x in SC))
chk("every scenario's gap-share re-derives from the district file", all(
    abs(x['pct_of_gap']-100*x['gap_deaths']/d['gap_deaths'].sum())<0.15 for x in SC if x['districts']>0),
    "recomputed from district_in.csv")
chk("scenario gap-deaths never exceed the national gap total", all(x['gap_deaths']<=S['gap_deaths_yr']+1 for x in SC))
chk("scenario shares are monotonic in nothing spurious (ceiling is the max)",
    max(x['pct_of_gap'] for x in SC)==100.0)
top=d.sort_values('priority',ascending=False)
for n,v in CONC.items():
    got=100*top['gap_deaths'].head(int(n)).sum()/d['gap_deaths'].sum()
    if abs(got-v)>0.15: FAIL.append(f"concentration top-{n} mismatch {got:.1f} vs {v}")
chk("concentration curve re-derives at every point", not [f for f in FAIL if 'concentration' in f])
_d50=[x for x in SC if x['label'].startswith('D')][0]; _b=[x for x in SC if x['label'].startswith('B')][0]
chk("the 'targeting beats geography' claim is TRUE as stated",
    _d50['pct_of_gap']>=_b['pct_of_gap'] and _d50['districts']<_b['districts'],
    f"top-{_d50['districts']}={_d50['pct_of_gap']}% vs NW {_b['districts']} districts={_b['pct_of_gap']}%")
ihtml=open(f"{OUT}/india_coverage_gap_brief.html").read(); ilow=re.sub(r'<[^>]+>',' ',ihtml.lower())
chk("brief frames scenarios as REACH, not deaths averted", "reach" in ilow and "not</b> a claim that deploying there averts" in ihtml)
chk("brief admits India has NO small-set solution (does not oversell concentration)",
    "no small-set solution" in ilow and "will not move the national figure" in ilow)
chk("brief states the Ghana contrast honestly", "25 hospitals" in ihtml)

print("\n=== E. FACILITIES / ACCESS ===")
H=pd.read_csv(f"{DATA}/in/facilities_hospitals_in.csv")
chk("facility count matches summary", len(H)==S['n_hospital_tier'], f"{len(H)} vs {S['n_hospital_tier']}")
chk("no exact duplicate facilities remain", H.duplicated(subset=['name','type','lat','lon']).sum()==0)
chk("all facility coords inside India's bbox", H.lat.between(6,37).all() and H.lon.between(68,98).all())
chk("nearest_km non-negative and finite", (d['nearest_km']>=0).all() and np.isfinite(d['nearest_km']).all())
chk("facility state coverage disclosed", S['states_with_hospitals']==H['state'].nunique(),
    f"{S['states_with_hospitals']} vs {H['state'].nunique()}")

print("\n=== F. ARTIFACT CONSISTENCY + HONESTY ===")
html=open(f"{OUT}/india_coverage_gap_brief.html").read()
low=re.sub(r'<[^>]+>',' ',html.lower())
for tok,lab in [(f"{S['pct_burden_in_asv_gap']}%","gap %"),(f"{S['gap_deaths_yr']:,}","gap deaths"),
                (f"{S['n_hospital_tier']:,}","facilities"),(f"{A['modelled_deaths_yr']:,}","modelled deaths")]:
    chk(f"brief contains {lab} ({tok})", tok in html)
chk("brief states the MDS anchor", "58,000" in html and "Million Death Study" in html)
chk("brief states the GBD uncertainty interval", "29,600" in html and "64,100" in html)
chk("brief discloses the rural weighting", "94" in html and "rural" in low)
chk("brief states NO published national gap figure exists", "no published figure exists" in low)
chk("brief presents the gap as an order of magnitude, not a measurement",
    "order of magnitude" in low and "not a measurement" in low)
chk("brief carries the published sub-national anchors", "68.4%" in html and "66.19%" in html)
# the corrected brief states the full figures; if it still mentions "-35%" that is only allowed
# inside an explicit correction sentence (mention, not use)
_m35 = "\u221235%" in html or "-35%" in html
_corrected = ("0.39" in html and "0.84" in html)
_only_as_correction = (not _m35) or ("ambiguous" in low)
chk("brief states the Punjab figures in full (0.39 vs 0.84-0.99 vs claim 0.60)", _corrected)
chk("any residual '-35%' appears only as a flagged correction, never as a claim", _only_as_correction)
chk("brief admits the gradient tension", "does not have that shape" in low)
chk("brief carries the WHO-assessment CORRECTION prominently", "seven are" in low or "correction carried" in low)
chk("correction names the seven products", all(x in html for x in ["Bharat","Biological E","Haffkine","VINS"]))
chk("brief explicitly disclaims deaths-averted", "do <b>not</b> claim deaths averted" in html or "not</b> claim deaths averted" in html)
for bad in ["deaths averted per year","lives saved versus today","will save"]:
    occ=[m.start() for m in re.finditer(re.escape(bad),low)]
    neg=[o for o in occ if re.search(r'\b(not|never|no)\b[^.]{0,60}$',low[max(0,o-90):o])]
    chk(f"no UN-negated overstatement: '{bad}'", len(occ)==len(neg), f"{len(occ)} occ / {len(neg)} negated")
chk("brief carries the disclaimer", "not clinical guidance" in low)
chk("brief discloses the join match rate", f"{S['district_pop_match_rate_pct']}%" in html)
chk("brief discloses partial facility-state coverage", f"{S['states_with_hospitals']} of 36" in html)

print("\n"+"="*64)
if FAIL:
    print(f"RESULT: {len(FAIL)} FAILURE(S)"); [print("   x",f) for f in FAIL]; sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
