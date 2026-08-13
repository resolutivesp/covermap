#!/usr/bin/env python3
"""
PARAMETER PROVENANCE AUDIT.

The verification suites check ARITHMETIC (does burden = pop x rate x fraction reproduce?).
They cannot tell whether `rate` is real. This audit answers the different question:
for every load-bearing magic number in the three models, is it TRACEABLE to a published
source, or is it an ASSUMPTION we chose?

It makes no claim that assumptions are wrong. It makes them VISIBLE, so no deliverable can
describe an assumption as if it were a published figure -- which is exactly the error that
occurred with India's state death rates.
"""
import json, sys

# tier: CITED   = transcribed from a named published source (verifiable)
#       DERIVED = computed from CITED inputs by a stated rule
#       ASSUMED = our own choice; defensible, but NOT a published number
P=[
 # ---- shared West-Africa impact chain (v0.4: three assumed parameters REMOVED) ---------------
 ("shared","product-choice CFR differential 0.103","CITED","Visser 2008 TRSTMH 102:445 -- OBSERVED in rural Ghana: treated-patient case-fatality 1.8% -> 12.1% when an ineffective antivenom was substituted. REPLACED the old synthetic chain (care-seeking x untreated-CFR x effectiveness).","mortality figure"),
 ("shared","envenoming fraction 0.647","CITED (Ghana) / ASSUMED (Nigeria)","Aglanu 2025: 64.7% of northern Ghana snakebite attendances had >=1 abnormal clotting result. Transferring it to Nigeria is an assumption.","LINEAR on burden, vials, cost"),
 ("shared","care-seeking multiplier","REMOVED","*** was 0.45 -- DELETED in v0.4. The base rates are facility ATTENDANCE, so applying care-seeking double-discounted. This was a genuine methodological error that understated the vial forecast by ~half. ***","-"),
 ("shared","untreated CFR 0.16 / effectiveness 0.75","CITED (retained for sensitivity only)","Habib 2015 PLoS NTD 9(1):e0003381 (verified verbatim). No longer used for headline figures.","sensitivity band only"),
 ("shared","reach radius 50 km","PARTIAL — proxy for a published standard","*** the published standard is TRAVEL TIME, not distance: Longbottom 2018 Lancet 392:673 defines vulnerability as '>3 h away from major urban centres', justified clinically by Habib & Abubakar ('each hour delay ... increased mortality outcome of 1.01%'). 50 km straight-line is our computable stand-in; at rural West-African road speeds with a 1.3-1.4x road correction it lands ~2-3.5 h. THE CONVERSION IS OURS. Finalist fix: use the MAP friction surface and 3 h directly.","shifts coverage % and reachability"),
 ("shared","vials/patient 1.5","CONFIRMED — inside a WHO-published range","WHO PANAF-Premium product overview: initial dose for 'African carpet vipers (Echis): 1-3 vials'. Observed mean 1.23 in Ghana's Oti region (Ketor 2024). 1.5 sits inside the published range, just above the one observed mean.","LINEAR on vials + cost"),
 ("shared","price/vial $80","PARTIAL — inside a wide published bracket","no single authoritative price exists. Brown 2012 $18-200/vial; Burkina Faso subsidised to US$3.4 (2015); SAVP US$315/vial (2020). Cross-check: 1.5 x $80 = $120/course, inside the US$100-153/dose baseline used in published sub-Saharan supply modelling (Potet 2020).","LINEAR on cost only"),
 ("shared","safety buffer 25%","NOT CONFIRMED","*** searched and not found. *** WHO/EPI supply-chain guidance sets min/max levels in MONTHS OF STOCK, not a flat percentage; its worked example happens to imply ~25%, but that is an example, not a standard. Retained as a planning assumption.","LINEAR on vials + cost"),
 # ---- Ghana ----------------------------------------------------------------------------------
 ("ghana","N-savanna attendance 55/100k","CITED","Aglanu 2025 PLoS NTD e0013820 -- verbatim 'hospital attendance rate ... 55 persons per 100,000 per year'. NB Abanga 2025 gives 101/100k for Savannah Region, so 55 is conservative.","drives northern burden"),
 ("ghana","transition attendance 24/100k","CITED","Ceesay 2021 Pan Afr Med J 40:131 (Volta+Oti). NB Bosoka 2025 gives 15.8/100k for Volta 2018-23.","-"),
 ("ghana","forest attendance 25/100k","PARTIAL (CORRECTED)","*** was 8/100k -- CONTRADICTED by Mensah 2016 Ghana Med J 50(2), Western Region: 'about 55% of the incidence was between 50-100 per 100,000'. Raised to 25, consistent with GHS DHIMS regional counts (~21-34/100k) and still conservative vs Mensah. ***","southern burden; shifted some placement south"),
 ("ghana","coastal attendance 12/100k","NOT CONFIRMED","*** searched repeatedly across two independent review passes; NO published snakebite incidence figure of any kind exists for Greater Accra or Ghana's coastal zone. *** Directionally sensible (highly urban) but wholly unsourced. The single most unsupported number in the Ghana model - low impact (lowest-burden zone).","low-burden zone; minor"),
 ("ghana","Echis fraction 0.90 north","WEAK","Aglanu 2025 says E. ocellatus is 'THOUGHT TO CAUSE about 90%' -- an introductory assertion, not a measurement; that paper recorded no species. The only community measurement in the zone (Musah 2019) says ~35%; the gap is severity selection.","scales Echis burden"),
 ("ghana","Echis 0.60 transition / 0.20 forest+coastal","NOT CONFIRMED","*** no published zone-level Echis fraction exists for Ghana outside the north. *** Forest/coastal lowered from 0.30 on species-range grounds (E. ocellatus is a savanna species, largely absent from closed forest; eastern populations are now E. romani) - a reasoned direction, not a measurement.","scales Echis burden by zone"),
 ("ghana","national anchor 9,900 bites/yr","CITED","Ghana Health Service NTD Programme, avg 2015-2020","upper sanity bound only"),
 # ---- Nigeria --------------------------------------------------------------------------------
 ("nigeria","zone attendance 45 / 28 / 4 per 100k","NOT CONFIRMED — confirmed UNCONFIRMABLE","*** two independent review passes confirm NO published per-eco-zone snakebite rate exists for Nigeria at any resolution. *** These are a CONSTRUCTION bracketed by FMoH surveillance (~7.6/100k all bites, under-reported) and community surveys (~497-500/100k in savanna foci). Not a transcription of anything.","drives ALL Nigerian absolute figures"),
 ("nigeria","the MIDDLE_BELT > SUDAN_SAVANNA gradient","UNRESOLVED","the strongest Nigerian community datum (497/100k) is attributed to the Benue valley by Habib 2013/2011, but the underlying 1980 Lancet study is generally sited at Malumfashi (Katsina) = Sudan savanna, which we rate LOWER. The original paper could not be obtained. If inverted, the split between the two savanna zones is wrong (both remain high and both are prioritised).","split between the two savanna zones"),
 ("nigeria","Echis fraction 0.85 savanna","SUPPORTED","Habib & Abubakar 2011 (Kaltungo, 6,687 victims): '>90% of the bites were due to E. ocellatus'; Habib 2013 hospital series 75%; Pugh & Theakston >=66%. Correctly matched to a facility/severe construct.","-"),
 ("nigeria","Echis fraction 0.20 south","NOT CONFIRMED","*** no species-attribution study exists for southern Nigeria. *** The only southern datum found (Benin City, 435 cases over 20 years, two tertiary hospitals) reports no species breakdown. Lowered from 0.30 on species-range grounds only.","low-burden zone; minor"),
 ("nigeria","death ceiling 2,640","CITED","GBD 2019 Nigeria UI upper (Nat Commun 2022) -- verified verbatim","hard cap on reported deaths"),
 ("nigeria","mortality-gap central 2,013","FLAGGED TENSION","*** exceeds the highest published CENTRAL estimate of Nigeria's TOTAL snakebite mortality (Habib 1,927; GBD 1,460). *** Stays under the published upper bound (2,640) and is a worst-case counterfactual, but should be read as an upper-bound signal, not a forecast. Surfaced in the brief, not tuned away.","credibility exposure"),
 # ---- India ----------------------------------------------------------------------------------
 ("india","state death rates (18 states)","CITED (CORRECTED)","Suraweera 2020 eLife Table 3, col 2010-2014 -- now TRANSCRIBED VERBATIM and locked by verify_india C0. *** Previously approximated, deviating up to 300% (Kerala) and 140% (Chhattisgarh) while being described as 'real MDS state rates'. ***","state burden + priority ranking"),
 ("india","state catch-all rates (NE 0.7 / other 3.2)","CONFIRMED — now a published value","*** RESOLVED: MDS Table 3 publishes its OWN catch-all rows, which we had been replacing with an assumption. 'All other states' = 3.2/100k and 'Northeastern states' = 0.7/100k (2010-2014), both now used verbatim (two independent readings). Independent check: the model's implied national rate is 4.6/100k against Table 3's published 'All India' row of 4.5/100k.","no assumed state rate remains in India"),
 ("india","rural death share 0.94","CITED","Suraweera 2020: 'about 94% of snakebite deaths occurred in rural areas'","redistributes within state; totals unchanged"),
 ("india","ADEQ ordinal tiers (0.45/0.35/0.30/0.65/0.75)","NOT CONFIRMED — confirmed UNCONFIRMABLE","*** targeted search across the primary antivenomics literature, TRSTMH reviews and India's national action plan (NAPSE) confirms NO published figure exists for the national or state ASV coverage gap. *** The review whose thesis is 'look beyond the Big Four' (Menon 2025) states none; NAPSE proposes Regional Venom Centres precisely because the data is absent. Direction of every tier is evidenced; NO precise level is. Error sign UNKNOWN.","HEADLINE"),
 ("india","the implied 'distance from Tamil Nadu' gradient","KNOWN CONTRADICTION","the tiers imply a distance decay; the data does not have that shape. For N. naja the ASV met its claim in only ONE tested population (Andhra Pradesh 0.80) and sat at 0.28-0.38 in Punjab, West Bengal, Madhya Pradesh and Maharashtra alike -- the Gangetic belt neutralises as poorly as the NW. The mainland tier survives only because D. russelii and E. carinatus dominate mortality there and ARE covered.","structural caveat, disclosed"),
 ("india","published sub-national anchors","CITED","68.4% clinical ASV non-response in NW India (Gopalakrishnan 2025, 63/92); 66.19% non-Big-Four share of identified venomous bites in Assam (Menon 2025); ~0.25 ASV potency vs claim in the Andamans (Attarde 2021); 32.6% Hypnale share of identified Kerala bites (Menon 2025).","the hard evidence the case rests on"),
 ("india","MDS ~58,000 / GBD UI 29,600-64,100","CITED","Suraweera 2020; Nat Commun 2022 (both verified verbatim)","anchor"),
]

def main():
    n_c=sum(1 for r in P if r[2].startswith("CITED") or r[2].startswith("CONFIRMED")); n_a=sum(1 for r in P if r[2].startswith("ASSUMED") or r[2].startswith("NOT CONFIRMED"))
    n_d=len(P)-n_c-n_a
    print("="*100); print("PARAMETER PROVENANCE AUDIT — what is sourced vs what we chose"); print("="*100)
    for scope in ["shared","ghana","nigeria","india"]:
        print(f"\n--- {scope.upper()} ---")
        for s,name,tier,src,impact in P:
            if s!=scope: continue
            mark=("[SOURCED] " if tier.startswith("CITED") else
                  "[ASSUMED] " if tier.startswith("ASSUMED") else
                  "[SOURCED] " if tier.startswith("CONFIRMED") else
                  "[UNCONF!] " if tier.startswith("NOT CONFIRMED") else
                  "[REMOVED] " if tier=="REMOVED" else
                  "[!FLAG!!] " if "FLAG" in tier or "TENSION" in tier or "CONTRADICTION" in tier or tier=="UNRESOLVED" else
                  "[PARTIAL] ")
            print(f"  {mark}{name}")
            print(f"      source : {src}")
            if impact!="-": print(f"      impact : {impact}")
    print("\n" + "-"*100)
    print("KENYA (v0.7.0) - separate table; grades live in data/ke/parameters_ke.py")
    print("-"*100)
    KE = [
     ("kenya","zone attendance WEST 4.6/100k","CITED","Ochola 2018 PAMJ 29:217, Kakamega hospital-record rate","burden"),
     ("kenya","zone attendance COAST 15/100k","PARTIAL","Abouyannis 2023 paediatric admissions 11.3-29.1/100k-py; adult rate not published","burden"),
     ("kenya","zone attendance ARID_NORTH 20 & RIFT 15","ASSUMED","CONSTRUCTION bracketed by Coombs 1997 (1.9-67.9) and community surveys (Snow 151; Samburu ~440 derived)","burden"),
     ("kenya","zone attendance CENTRAL_HIGHLANDS 2.0","ASSUMED","NOT CONFIRMED - no published figure; direction from species ranges; placement robust 42/45 to halving","burden"),
     ("kenya","treated fraction 0.252","CITED","Abouyannis 2023 verbatim: 'Antivenom was administered to 119 (25.2%)'","vials"),
     ("kenya","vials/treated 1.40","DERIVED","Abouyannis 2023 distribution 72/26/8; paediatric 2003-21 practice - likely a floor","vials"),
     ("kenya","county populations","CITED","KNBS 2019 census, 47 county figures summing exactly to 47,564,296","denominator"),
     ("kenya","Echis county mapping","ASSUMED","DECLARED mapping of Ochola 2018 Table 1 place names (row labelled E. carinatus = Kenyan carpet viper); unlisted plausible-range counties unflagged - WHO snake-DB check is finalist work","product rule"),
     ("kenya","price $80/vial, buffer 25%, reach 50 km","ASSUMED","same planning assumptions as GH/NG, for comparability; Kenya patient prices (Ooms 2021) kept separate","cost"),
    ]
    for c,pname,st,note,impact in KE:
        print(f"  [{st:8}] {pname}")
        print(f"      source : {note}")
    print("\n"+"="*100)
    print(f"TOTAL {len(P)}   sourced/confirmed={n_c}   unconfirmed={n_a}   partial/flagged={n_d}")
    print("="*100)
    print("""
HONEST READING

  CONFIRMATION PASS (v0.5): all 10 previously-assumed parameters were taken back to primary
  sources. FOUR resolved, SIX did not and are now labelled NOT CONFIRMED rather than quietly
  carried. "Not confirmed" here means: searched hard, no published figure exists -- not "unchecked".

  RESOLVED:
    - vials/patient 1.5  -> inside the WHO-published Echis initial dose (1-3 vials, PANAF overview)
    - India catch-all rates -> MDS Table 3 publishes its own 'Northeastern states' (0.7) and
      'All other states' (3.2) rows; no assumed state rate remains in India, and the implied
      national rate (4.6/100k) now matches Table 3's published All-India row (4.5/100k)
    - reach 50 km -> re-labelled as a PROXY for the published 3-hour travel-time standard
      (Longbottom 2018), with the distance-to-time conversion declared as ours
    - price $80/vial -> bracketed by published prices and cross-checked against the $100-153/dose
      modelling baseline used in the sub-Saharan supply literature

  STILL NOT CONFIRMED (searched, does not exist in the literature):
    - Nigeria's per-zone rates and southern Echis fraction
    - Ghana's coastal rate and non-northern Echis fractions
    - India's adequacy tiers
    - the 25% safety buffer (supply-chain practice uses months-of-stock, not a percentage)
  * FIXED IN v0.4 (were errors, not just uncertainties):
      - the care-seeking double discount (understated the vial forecast by ~half)
      - Ghana's forest rate of 8/100k, contradicted by Mensah 2016 by 6-12x
      - India's state death rates, which deviated from the published MDS table by up to 300%
        while being described as MDS values
      - India's Kerala adequacy, a bite-vs-mortality category error
      - India's false precision (0.75 vs 0.72 etc.), collapsed to ordinal tiers
  * LARGEST REMAINING EXPOSURE -- India's ADEQ tiers. The coverage-gap headline is a direct
    function of magnitudes we chose. No published national or state figure exists; an adversarial
    literature review confirmed the DIRECTION of every tier and NO precise level. Read the
    headline as an order-of-magnitude flag whose error sign is UNKNOWN. The published
    sub-national anchors (68.4% NW clinical non-response; 66.19% Assam non-Big-Four bites) are
    the hard evidence -- they should carry the argument, not the modelled percentage.
  * SECOND EXPOSURE -- Nigeria's zone rates are a CONSTRUCTION; no published per-zone figure
    exists. Coverage % is a ratio and resists uniform scaling, but vials and cost scale LINEARLY.
    The gradient between the two savanna zones may even be inverted (unresolved: Malumfashi vs
    Benue). And the Nigerian mortality gap exceeds the published CENTRAL national mortality --
    flagged in the brief rather than tuned away.
  * THIRD -- Ghana's coastal rate has no published basis of any kind, and the northern Echis
    fraction (0.90) rests on a hedged assertion, not a measurement.
""")
    return 0

if __name__=="__main__":
    sys.exit(main())
