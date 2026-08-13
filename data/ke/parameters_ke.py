# -----------------------------------------------------------------------------
# KENYA MODEL PARAMETERS — single source of truth.
# Every number here carries its provenance. kenya_build.py IMPORTS this file;
# nothing below may be retyped elsewhere (project lesson 5: a hand-typed number
# survives every correction).
#
# Provenance grades: SOURCED (verbatim from primary source) · DERIVED
# (arithmetic on published numbers, method stated) · CONSTRUCTION (ours,
# bracketed by published data, declared) · NOT_CONFIRMED (searched, not found).
#
# DESIGN DECISION — FRAME (documented 11 Aug 2026, supersedes the first draft
# of the provenance sheet):
#   The Kenya model runs in the FACILITY frame, same as Ghana and Nigeria.
#   Rationale: the usable area anchors (Coombs 1997 — records of 50 health
#   units; Ochola 2018 — hospital records; Abouyannis 2023 — admissions) are
#   facility-based rates, not community rates. Anchoring the model to them
#   keeps one frame across all four countries and means NO care-seeking
#   multiplier is applied anywhere (the v0.4 correction holds).
#   Community surveys (Snow 1994 coast 151/100k; Tianyi 2024 Samburu 2.2%/5yr)
#   serve as the COMMUNITY-SIDE BRACKET only, exactly like Nigeria's 497/100k
#   savanna surveys. verify_kenya.py enforces this frame.
# -----------------------------------------------------------------------------

CITATIONS = {
    "snow1994":      "Snow RW et al., Ann Trop Med Parasitol 1994;88(6):665-71. Community survey, rural coastal Kenya: 151 bites/100k/yr; 19% by potentially venomous species; mortality 6.7/100k/yr.",
    "coombs1997":    "Coombs MD et al., Trans R Soc Trop Med Hyg 1997;91(3):319-21. Records of 50 health units, four areas: 13.8/100k/yr (range 1.9-67.9); minimum mortality 0.45/100k/yr. Area-specific rates NOT extractable from abstract; full text not accessed - FLAG.",
    "ochola2018":    "Ochola FO et al., Pan Afr Med J 2018;29:217. Hospital-record incidence: Kabarnet (Baringo) 6.7, Kakamega 4.6, Kapenguria (W Pokot) 2.7, Makueni 5.4 per 100k/yr.",
    "tianyi2024":    "Tianyi F-L et al., PLOS NTD 2024;18(1):e0011678. Samburu community survey: 5-yr period prevalence 2.2% (CI 1.4-3.4); 5-yr mortality 138/100k.",
    "abouyannis2023":"Abouyannis M et al., PLOS NTD 2023;17(7):e0010987. Kilifi 2003-21, 584 paediatric snakebite admissions; admission incidence 11.3/100k-py (<=5y), 29.1 (6-12y); antivenom vials among treated: 1 vial 67.9%, 2 vials 24.5%, >=3 vials 7.5%.",
    "toxins2026":    "Kenya Snakebite Research & Intervention Centre (Kenya Institute of Primate Research) et al. - Establishing the Kenya National Antivenom QC Laboratory, Toxins 2026;18(2):106. Big Five = N. ashei, N. pallida, N. nigricollis, D. polylepis, B. arietans. Neutralisation grid (Figure 4) LD50/mL, challenge dose 5x (3x marked #, 2x marked +) - VERIFIED against full text 11 Aug. Inoserp failed N. ashei, N. pallida, D. polylepis at manufacturer-claimed doses AND was withdrawn from the Kenyan market in 2022 after these assays (paper, primary). PANAF-Premium approved by Kenya PPB after WHO risk-benefit assessment (paper, primary). SAIMR $315/vial in Kenya (paper).",
    "ooms2021":      "Ooms GI et al., PLOS NTD 2021;15(8):e0009702 + HAI field report 2019-2020. RESOLVED 11 Aug (both real, different denominators): PLOS paper = PUBLIC SECTOR most-stocked: VINS African IHS 66.7% of facilities, Inoserp 33.3% (verbatim); field report = all-sector brand shares 86/11/6. Availability 44.7% public / 19.4% private (p=0.009); 20.0% of public facilities stocked out over 12 months, mean 13.6 days; private median price 14.4 days' wage (LPGW). All verbatim-verified 11 Aug. NOTE: survey is 2019-20, PRE-withdrawal - stock picture is historical context, not current market.",
    "knbs2019":      "KNBS, 2019 Kenya Population and Housing Census, Vol I. National total 47,564,296; county totals as published.",
    "whopar_panaf":  "WHO risk-benefit assessment, PANAF-Premium (Premium Serums), Mar 2023. Schedule 2 lists sub-Saharan taxa incl. Echis pyramidum, B. arietans, N. nigricollis, N. haje complex, D. polylepis, D. angusticeps.",
    "wuster2007":    "Wuster & Broadley 2007 (N. ashei description): dry lowlands of northern and eastern Kenya. Conflicts with broader Bio-Ken range table (Ochola 2018 Table 1); taxonomic source preferred.",
}

# --- Denominator (SOURCED) ---------------------------------------------------
CENSUS_TOTAL_2019 = 47_564_296          # knbs2019, verbatim
POP_SOURCE = "knbs2019"
COUNTY_CENSUS_CSV = "county_census_2019.csv"   # all 47 counties, KNBS 2019 via
# citypopulation.de transcription; INTEGRITY CHECK: the 47 figures sum EXACTLY
# to CENSUS_TOTAL_2019 (verified 11 Aug rc2). County totals are PINNED to these;
# the raster provides only WITHIN-county distribution (rc2 fix: the continental
# ~18.5 km raster with all_touched over small units double-counted cells ~4.9x,
# inflating Nairobi/Kiambu and starving the arid north (measured ~5.3x aggregate)
# - caught in adversarial review; 9 of 36 rc1 sites were artifacts of it).

# --- Zone definitions: county -> zone (design; species logic per zone below) -
# Zone membership follows published species ranges and the anchor studies'
# locations. County list = geoBoundaries ADM1 (47).
ZONES = {
    "ARID_NORTH":   ["Turkana","Marsabit","Mandera","Wajir","Garissa","Isiolo","Samburu"],
    "RIFT_SEMIARID":["Baringo","West Pokot","Elgeyo-Marakwet","Laikipia","Kajiado","Narok",
                     "Kitui","Makueni","Machakos","Embu","Tharaka","Meru"],
    "COAST":        ["Kilifi","Kwale","Tana River","Lamu","Mombasa","Taita Taveta"],
    "WEST":         ["Kakamega","Bungoma","Busia","Vihiga","Siaya","Kisumu","Homa Bay",
                     "Migori","Kisii","Nyamira","Trans Nzoia","Uasin Gishu","Nandi",
                     "Kericho","Bomet"],
    "CENTRAL_HIGHLANDS":["Nairobi","Kiambu","Murang'a","Nyeri","Kirinyaga","Nyandarua",
                     "Nakuru"],
}

# --- Facility snakebite ATTENDANCE rates per 100k/yr, by zone ---------------
# STATUS: CONSTRUCTION, bracketed. Two zones carry direct published anchors;
# the others are constructions between the published floor (Coombs range low
# 1.9) and ceiling (Coombs range high 67.9), with direction set by species
# ranges and the community-side bracket. This mirrors Nigeria's approach and
# is declared identically in the audit.
ZONE_ATTENDANCE_PER_100K = {
    "ARID_NORTH":    20.0,   # CONSTRUCTION. Community side very high (tianyi2024:
                             # 2.2%/5yr ~ 440/100k/yr DERIVED, uniform-rate assumption);
                             # sparse facilities imply large community->facility gap.
    "RIFT_SEMIARID": 15.0,   # CONSTRUCTION. Anchor: ochola2018 Kabarnet 6.7 (records,
                             # under-capture). NOTE rc2: coombs1997's top area (67.9) is NOT
                             # attributable to this zone - area-level rates were never extracted
                             # (see FLAG in citation); secondary attribution (tianyi2024) places
                             # the top Coombs area in Samburu (ARID_NORTH).
    "COAST":         15.0,   # PARTIAL ANCHOR: abouyannis2023 paediatric admissions
                             # 11.3-29.1/100k-py (children only; adult rate not published).
    "WEST":           4.6,   # SOURCED ANCHOR: ochola2018 Kakamega 4.6 (records-based).
    "CENTRAL_HIGHLANDS": 2.0,# NOT_CONFIRMED level; direction (lowest) from species
                             # ranges + coombs1997 range floor 1.9.
}
ZONE_RATE_STATUS = {
    "ARID_NORTH": "CONSTRUCTION", "RIFT_SEMIARID": "CONSTRUCTION",
    "COAST": "PARTIAL", "WEST": "SOURCED-ANCHORED", "CENTRAL_HIGHLANDS": "NOT_CONFIRMED",
}

# Community-side bracket (context, NOT model inputs) — mirrors Nigeria's 497:
COMMUNITY_BRACKET = {
    "coast_bites_per_100k": 151.0,        # snow1994, SOURCED
    "samburu_5yr_prevalence": 0.022,      # tianyi2024, SOURCED
    "samburu_annualised_per_100k": 440.0, # DERIVED: 2.2%/5yr, uniform-rate, no repeat bites
}

# --- Treatment chain (facility frame; NO care-seeking multiplier) -----------
ANTIVENOM_TREATED_FRACTION = 0.252   # SOURCED abouyannis2023, verbatim: "Antivenom was
                                     # administered to 119 (25.2%) children with snakebite"
                                     # (denominator: 472 with clinical records). CORRECTED 11 Aug
                                     # rc2 - the earlier 0.182 (106/584) was a false derivation
                                     # caught in adversarial review: 106 is the vials-DOCUMENTED
                                     # subset, not the treated count. Paediatric, coastal - declared.
VIALS_PER_TREATED = 1.40             # DERIVED abouyannis2023 distribution (verbatim counts 72/26/8):
                                     # 1*0.679 + 2*0.245 + 3*0.075 = 1.394 (3+ taken as 3; floor).
                                     # DIRECTION CAVEAT (rc2): encodes 2003-21 paediatric practice
                                     # with since-withdrawn products - likely a FLOOR vs current
                                     # initial-dose recommendations for the products now advised.
SAFETY_BUFFER = 0.25                 # planning assumption, same as GH/NG (declared, not sourced)
PRICE_PER_VIAL_USD = 80.0            # planning assumption, same as GH/NG for comparability.
                                     # Kenya PATIENT prices exist (ooms2021: public 2.3 days-wage,
                                     # private median 14.4 days) but retail != procurement; kept separate.

REACH_KM = 50.0                      # same proxy as GH/NG; declared PROXY (travel-time is the standard)

# --- Species presence (for product adequacy) ---------------------------------
# Big Five present countrywide in varying mixes (toxins2026 tested all five).
# Echis pyramidum presence: ONLY Kenya-specific source found is ochola2018
# Table 1 (Bio-Ken compilation), whose row is labelled "Saw-scaled viper
# (Echis carinatus)" - the compilation's label for the Kenyan carpet viper
# (E. pyramidum complex); the equation is ours and declared (rc3). Places:
# "Lake Baringo, Kakuma, Mount Elgon, Makueni, Tsavo National Park, North
# Eastern Province". Place-name -> county mapping is OURS (declared). For
# LISTED places, inclusion errs safe (a flag forces the Echis product); but
# counties ABSENT from the compilation (Samburu, Isiolo, Marsabit - plausible
# range) default to unflagged, which for the ALTERNATIVE recommendation is the
# unsafe direction - declared, WHO snake-DB check is the finalist-phase fix:
#   Lake Baringo->Baringo | Kakuma->Turkana | Mount Elgon->Bungoma,Trans Nzoia
#   Makueni->Makueni | Tsavo NP->Taita Taveta,Kitui,Tana River
#   North Eastern Province->Garissa,Wajir,Mandera
# NOTE (rc2): the earlier ECHIS_ZONES cited wuster2007 - WRONG source (that is
# the N. ashei description, not E. pyramidum); caught in adversarial review.
# WHO venomous-snake distribution database check = finalist-phase task.
ECHIS_COUNTIES = {"Baringo","Turkana","Bungoma","Trans Nzoia","Makueni",
                  "Taita Taveta","Kitui","Tana River","Garissa","Wajir","Mandera"}

# --- Product adequacy for Kenya (from toxins2026 + whopar_panaf) -------------
# 'big5' = potent vs all Big Five per Kenya QC 2026; 'echis' = covers E. pyramidum.
PRODUCTS = {
    "PANAF-Premium":    {"big5": True,  "echis": True,  "kenya_market": True,
                         # QC potent all 5; E. pyramidum listed in WHO Schedule 2 (= grade A under
                         # OUR published grading scheme; the WHO document itself carries no grading).
                         # PPB-approved for Kenya after WHO assessment (toxins2026, primary).
                         "status": "WHO risk-benefit assessed"},
    "SAIMR Polyvalent": {"big5": True,  "echis": False, "kenya_market": True,
                         # QC potent all 5; SAIMR polyvalent does NOT cover Echis. $315/vial;
                         # described in toxins2026 as costly, "of potential use" regionally.
                         "status": "not WHO-assessed"},
    "AFRIVEN (VINS)":   {"big5": True,  "echis": None,  "kenya_market": False,
                         # QC potent all 5; E. pyramidum: no datum. rc3: NOT recommendable -
                         # toxins2026 verbatim: "has yet to be commercialised in Kenya".
                         "status": "not WHO-assessed; not yet commercialised in Kenya"},
    "Inoserp Pan-Africa":{"big5": False, "echis": None, "kenya_market": False,
                         # QC FAILED N. ashei, N. pallida, D. polylepis; withdrawn from Kenya 2022.
                         "status": "failed QC at claimed doses; withdrawn 2022"},
}
# Adequacy rule (enforced in build): a recommendable product must have
# kenya_market=True, big5=True,
# AND echis=True if ANY demand unit allocated to it lies in an ECHIS_COUNTIES
# county. None (unknown) never counts as coverage - label is never promoted.
