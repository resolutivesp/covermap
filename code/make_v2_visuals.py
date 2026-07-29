#!/usr/bin/env python3
"""Ghana v0.2 figures — unified CoverMap design system (viz_common)."""
import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, pandas as pd, numpy as np, json, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from viz_common import PAL, mpl_theme, heat_cmap, blue_cmap
mpl_theme(); WARM=heat_cmap()
from _paths import BASE, SRC; DATA=f"{BASE}/data"; OUT=f"{BASE}/out2"
INK,SEC,MUT,GRID,BLUE,GOOD,CRIT,WARN,BLUED=PAL['ink'],PAL['sec'],PAL['mut'],PAL['grid'],PAL['blue'],PAL['good'],PAL['critical'],PAL['warning'],PAL['blue_d']
g=gpd.read_file(f"{OUT}/district_v2.geojson"); adm1=gpd.read_file(f"{DATA}/gha_ADM1.json")
allh=pd.read_csv(f"{DATA}/facilities_hospitals.csv"); plan=pd.read_csv(f"{OUT}/pre_positioning_plan.csv")
curve=pd.read_csv(f"{OUT}/coverage_curve.csv"); S=json.load(open(f"{OUT}/impact_summary.json"))
TITLE=dict(fontsize=12,weight='bold',color=INK,loc='left')
# Headline figures come from the JSON, never from a literal typed into a title.
# (v0.6.1: three figure titles still carried 87.5% -- the pre-v0.4 value, from before the
#  care-seeking double discount was removed -- while every text KPI said 86.0%. Nigeria and
#  India already read from their JSON; Ghana was written first and did not. Fixed here so the
#  figures cannot drift from the numbers again.)
PCT=S['optimized']['pct_protected']; K=S['optimized']['hospitals']; NH=len(allh)
_cv=curve.loc[curve.n_hospitals==K,'pct']
assert len(_cv)==1 and abs(PCT-float(_cv.iloc[0]))<0.15, \
    f"headline {PCT}% disagrees with the coverage curve at k={K} ({_cv.tolist()})"

# FIG1 — burden + placement (semantic-heat choropleth + blue stocking markers)
fig,ax=plt.subplots(figsize=(9,10)); ax.grid(False)
g.plot(column='echis_yr',ax=ax,cmap=WARM,legend=True,edgecolor='white',linewidth=0.25,
       legend_kwds={'shrink':0.48,'label':'Expected carpet-viper envenomings / year (district)'})
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.6)
ax.scatter(allh.lon,allh.lat,s=7,c=MUT,alpha=0.5,label=f'All hospitals ({NH})')
sz=45+plan['vials_year']/plan['vials_year'].max()*320
ax.scatter(plan.lon,plan.lat,s=sz,marker='o',c=BLUE,edgecolor='white',linewidth=0.9,label='Pre-position here (marker size = vials/yr)',zorder=5)
ax.legend(loc='lower left',fontsize=9,framealpha=.96,edgecolor=GRID); ax.axis('off')
ax.set_title(f"The pre-positioning plan: place PANAF-Premium where the burden is\n{K} hospitals — {PCT}% of the carpet-viper burden brought within reach",**TITLE)
plt.savefig(f"{OUT}/fig1_placement.png",dpi=135,bbox_inches='tight'); plt.close()

# FIG2 — within reach vs not (diverging blue<->red poles: CVD-safe, reads as opposite)
fig,ax=plt.subplots(figsize=(9,10)); ax.grid(False)
g[g.protected_opt].plot(ax=ax,color=BLUE,edgecolor='white',linewidth=0.25)
g[~g.protected_opt].plot(ax=ax,color=CRIT,edgecolor='white',linewidth=0.25)
adm1.boundary.plot(ax=ax,color=SEC,linewidth=0.6)
ax.scatter(plan.lon,plan.lat,s=78,marker='o',c=INK,edgecolor='white',linewidth=1.0,zorder=5)
ax.legend(handles=[Patch(color=BLUE,label='Within reach — ≤50 km of a stocking hospital'),
                   Patch(color=CRIT,label=f"Not within reach — incl. {S['pct_unreachable']}% beyond ANY hospital"),
                   plt.Line2D([],[],marker='o',color=INK,ls='',markersize=9,label='Stocking hospital')],
          loc='lower left',fontsize=9,framealpha=.96,edgecolor=GRID)
ax.axis('off'); ax.set_title(f"Who the plan covers\n{K} northern hospitals bring {PCT}% of the carpet-viper burden within reach",**TITLE)
ax.text(0.0,-0.012,f"Note: coverage is measured by BURDEN, not land area — the red southern districts are large but carry little\ncarpet-viper burden, which is why {PCT}% of burden is covered even though much of the map's area is red.",
        transform=ax.transAxes,fontsize=8.6,color=SEC,va='top')
plt.savefig(f"{OUT}/fig2_protected.png",dpi=135,bbox_inches='tight'); plt.close()

# FIG3 — coverage curve (emphasis) + scenario coverage (ordered status semantics)
fig,(a1,a2)=plt.subplots(1,2,figsize=(15,6.2))
a1.plot(curve.n_hospitals,curve.pct,marker='o',ms=3.5,color=BLUE,lw=2.4)
a1.axvline(K,color=MUT,ls='-',lw=0.9,alpha=.6); a1.axhline(PCT,color=MUT,ls='-',lw=0.9,alpha=.6)
a1.annotate(f'{K} hospitals → {PCT}%',xy=(K,PCT),xytext=(19,54),fontsize=10.5,weight='bold',color=INK,
            arrowprops=dict(arrowstyle='->',color=SEC))
a1.set_xlabel('# hospitals stocking PANAF-Premium'); a1.set_ylabel('% of carpet-viper burden within reach'); a1.set_ylim(0,100)
a1.set_title('A few well-chosen hospitals do most of the work',**TITLE)
sc=S['scenarios']; labels=[k.split('—')[0].replace('.','').strip() for k in sc]
cen=[v['pct'] for v in sc.values()]; y=np.arange(len(labels))
a2.barh(y,cen,color=[CRIT,WARN,GOOD,BLUED],height=.66); a2.set_xlim(0,100)
a2.set_yticks(y); a2.set_yticklabels(labels); a2.invert_yaxis()
for i,v in enumerate(cen): a2.text(v+1.5,i,f'{v}%',va='center',fontsize=10,weight='bold',color=INK)
a2.set_xlabel('% of carpet-viper burden within reach of the right antivenom')
a2.set_title('Coverage by procurement / placement choice',**TITLE)
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_curve_scenarios.png",dpi=135,bbox_inches='tight'); plt.close()

# FIG4 — demand per hospital (single-hue bars)
fig,ax=plt.subplots(figsize=(10,7)); ax.grid(axis='x')
top=plan.sort_values('vials_year',ascending=False).head(15).iloc[::-1]
ax.barh(range(len(top)),top.vials_year,color=BLUE,height=0.7)
ax.set_yticks(range(len(top))); ax.set_yticklabels([f"{h}  ({r})" for h,r in zip(top.hospital,top.region)],fontsize=8.5)
for i,v in enumerate(top.vials_year): ax.text(v+5,i,f'{v:,}',va='center',fontsize=8.5,weight='bold',color=INK)
ax.set_xlabel('Vials / year to pre-position (demand forecast, incl. 25% buffer)')
ax.set_title(f'Demand forecast: how many vials each hospital should hold\nTop 15 of {K} — total '+f"{int(plan.vials_year.sum()):,} vials/yr (~${int(plan.procure_usd_yr.sum()):,}/yr)",**TITLE)
plt.tight_layout(); plt.savefig(f"{OUT}/fig4_demand.png",dpi=135,bbox_inches='tight'); plt.close()
print("Ghana visuals:", [f for f in os.listdir(OUT) if f.endswith('.png')])
