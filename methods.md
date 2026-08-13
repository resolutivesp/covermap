# CoverMap — Methods v0.7.0 (Ghana · Nigeria · India · Kenya)

**Version:** v0.7.0 · August 2026 · **NOT clinical guidance.** Feasibility demonstrator (IML 2). Several layers are deliberate, cited approximations, each disclosed below.

---

## 0. Changelog — what changed and why

| Version | Change | Why |
|---|---|---|
| **v0.7.0** | **Kenya added** — fourth demonstrator, third failure regime (availability & placement: VINS and Inoserp were withdrawn from the Kenyan market in 2022 after national QC testing, verbatim in Toxins 2026;18(2):106). Facility frame, same as Ghana/Nigeria (no care-seeking multiplier); county populations pinned to the KNBS 2019 census (47 figures summing exactly to 47,564,296); zone attendance rates anchored to published area studies (Ochola 2018, Abouyannis 2023) with construction declared; product rule enforces Kenyan market availability (AFRIVEN potent in QC but not commercialised - never recommended; Inoserp failed 3 of 5 - excluded). 29-check verification suite incl. tokenizer-level frame check and independent allocation recomputation | **Three review rounds, errors in all three** - a county-centroid coarseness rejection (self-caught), a failed adversarial review (population-distribution artifact inflating Nairobi +122% while starving Turkana -59%, 9 of 36 sites artifacts; treated fraction 0.182 contradicting its source's verbatim 25.2%), and a passing re-review with every number reproduced independently end-to-end. The corrections are carried here, not deleted |
| **v0.6.2** | The coverage matrix conflated **demonstrated failure** with **absence of data**. PANAF-Premium × *Naja katiensis* rendered as `~` partial cover while its own cell recorded a measured failure (Khochare 2024: 11.16 LD50/mL, below the ≥20 threshold); four untested *Atractaspis* cells rendered in the same red as documented failures. Split into `✗` failure · `–` no activity claimed · `·` no data, with failure overriding every higher grade. Corrected six stale figures in this methods page (Ghana anchor 3,760→**5,627**; India 55,649→**55,656**; robustness 23/25→**24/25** and 51/64→**52/63**; checks 245→**256**; deduplicated the parameter table). Added `code/publish.py` | **Both errors ran in opposite directions and both were wrong.** Showing a measured failure as partial cover understates risk in the unsafe direction for a stocking decision; showing untested as failed asserts something about a commercial product the evidence does not support. The methods page was also still publishing pre-v0.4 outputs, so the one externally-checkable number disagreed with the site |
| **v0.6.1** | Corrected **three Ghana figure titles** that still displayed **87.5%** — the pre-v0.4 coverage value — while every text KPI on the same page said **86.0%**. Headline numbers in figures are now read from the model JSON. Added a **fifth verification suite** (`verify_figures.py`) that OCRs every shipped figure and requires each percentage it displays to be a value the model actually produced | The four existing suites (256 checks) all passed with the wrong number on screen: they check arithmetic and HTML *text*, but a number typed into a chart title is baked into a PNG and invisible to every string check — while being the first thing a reader sees |
| **v0.6** | India gains a **targeting-scenario table** ("the decision it changes"); **all three** briefs gain a **parameter-provenance table**; version stamped inside every artifact | India lacked the decision table the other two had; only Ghana had the provenance table — an inconsistency, not a choice |
| **v0.5** | Took all 10 assumed parameters back to primary sources: **4 resolved, 6 labelled NOT CONFIRMED** | "Not confirmed" now means *searched hard, no published figure exists* — not *unchecked* |
| **v0.4** | Removed the **care-seeking double discount**; replaced the synthetic mortality chain with Visser's **observed** differential; corrected India's state death rates (deviated up to 300% from the published MDS table while being described as MDS values); corrected Ghana's forest rate (contradicted by Mensah 2016) | Six real errors, one of which v0.3 had explicitly denied existed |
| **v0.3** | Unified design system; reproducibility hardened; verification suites | — |

**Current figures:** Ghana 86.0% coverage · 4,654 vials/yr · $371,114 — Nigeria 85.5% · 36,671 vials/yr · $2,931,101 — India 36.8% coverage-gap · 20,484 gap-deaths/yr · 55,656 modelled mortality.

---

## 1. Objective

Tell an antivenom purchaser **which product to pre-position at which facilities, in what quantity** — by joining *what bites where* to *what each product is actually proven to neutralise* to *who can reach care* — and state the impact **honestly**.

## 2. One engine, three failure regimes

| | West Africa (Ghana, Nigeria) | India | Kenya (v0.7.0) |
|---|---|---|---|
| Binding gap | **Which product** is stocked, and where | **Regional venom variation** + non-Big-Four species | **Availability & placement** — the product triage is already done |
| Why | Several products with wildly different *Echis* cover; some fail outright | One southern-sourced polyvalent used nationwide | The failing brands were withdrawn in 2022 after national QC testing; what remains is adequate but scarce and unevenly placed |
| Output | Named, costed pre-positioning plan | Coverage-gap target list for region-specific antivenom | Named, costed pre-positioning plan with per-facility product rule |

That the same engine expresses all three regimes is the central evidence that the method generalises.

## 3. The novel core — an evidence-graded coverage matrix

Product × species, every cell graded and cited:

- **A** — WHO risk-benefit-assessed (product overview)
- **B** — peer-reviewed preclinical (ED50 / antivenomics)
- **C** — manufacturer claim or label only
- **D** — no data
- **~** — partial / paraspecific
- **✗** — **published evidence AGAINST neutralisation** (overrides every higher grade)
- **–** — no activity claimed / product out of scope for that species
- **?** — claimed in the indication, no in-vivo datum
- **·** — no data

Two rules are enforced in code: a manufacturer label is never promoted to "covered", and published
evidence of failure overrides every higher grade. **✗ and – are deliberately distinct**: "we tested
it and it failed" is a different statement about a product than "nobody claims it works here", and
conflating them would both overstate our knowledge and misrepresent a manufacturer.

A manufacturer label is **never** promoted to "covered". No public dataset provides this layer; it is the reusable asset.

## 4. Data inputs (all public; all persisted in the repository)

| Layer | Ghana | Nigeria | India |
|---|---|---|---|
| Boundaries | geoBoundaries ADM1/2 (CC BY) | geoBoundaries, 774 LGAs | geoBoundaries, 734 districts |
| Population | afripop → GSS 2021 PHC regions (30.8 M) | afripop distribution → 206.1 M (World Bank 2020) | Census of India 2011 (1,210,854,977 — exact) |
| Facilities | 190 hospitals (Maina 2019 *Sci Data* 6:134) | 1,309 hospitals (Maina/WHO) | 3,575 hospital-tier (NIC HealthGIS: DHO/THO/CHC) |
| Burden | zone incidence, facility-anchored | zone incidence, facility-anchored | MDS state death rates × district population |

**Reproducibility:** every input is committed. No pipeline depends on network access or on `/tmp`. `python3 build → outputs → verify` reruns end to end.

## 5. Burden anchoring — the first guardrail

No country's burden is asserted without checking it against a published national figure **before** anything downstream is computed.

| Country | Model | Published anchor | Status |
|---|---|---|---|
| Ghana | 5,627 envenomings/yr | Ghana Health Service ~9,900 **bites**/yr (avg 2015–20) | model sits **below** reported bites, as it must → conservative floor |
| Nigeria | implied **14.0**/100k envenomings | published West Africa **8.9–93.3**/100k (Habib 2013) | **inside** the published range — a *bound*, not a confirmation. Implied attendance (21.6/100k) is ~2.8× FMoH surveillance (7.6/100k), assuming substantial under-reporting |
| India | 55,656 deaths/yr | MDS ~58,000 (Suraweera 2020); GBD 2019 51,100 (UI 29,600–64,100) | within **4.0%** of MDS, **inside** the GBD interval, using state rates **transcribed verbatim** from MDS Table 3 |

**⚠️ Correction in v0.4 (India).** The v0.3 state death rates were *approximations* described in the deliverables as "real Million Death Study state death rates". They deviated from the published table by up to **300%** (Kerala) and **140%** (Chhattisgarh); 12 of 17 states were off by ≥20%. They are now transcribed verbatim from Table 3 (column 2010–2014) and **locked by a verification check**.

## 6. Model

1. **Burden** per unit = population × zone incidence × species-severe fraction (West Africa), or population × MDS state death rate (India).
2. **Rural weighting (India).** The MDS finds **~94% of India's snakebite deaths occur in rural areas**. Distributing state mortality by *total* population implies city-dwellers die of snakebite at rural per-capita rates — contradicting the anchor source and pushing metros to the top of the priority list. Each state's mortality is therefore split **94% rural / 6% urban** using the census rural/urban household split. This is a *within-state re-allocation*: every state total and the national total are unchanged.
3. **Reach.** A unit is within reach if ≤ **50 km** of a stocking facility (straight-line proxy for travel time).
4. **Optimiser.** Greedy maximal-coverage: iteratively add the facility bringing the most not-yet-covered burden within reach.
5. **Demand.** Each unit's burden is assigned to its nearest chosen facility; vials/yr = facility attendance × envenoming fraction (0.647, Aglanu 2025) × *Echis* fraction × vials/patient × (1 + buffer). **No care-seeking multiplier is applied** — in the facility frame these patients have already reached care (see the v0.4 correction).

## 7. Grounded parameters (shared across Ghana and Nigeria — identical by construction, verified)

| Parameter | Point | Range | Source |
|---|---|---|---|
| Reach radius | 50 km | 30–80 | **PROXY.** The published accessibility standard is travel time, not straight-line distance (Longbottom 2018 *Lancet* 392:673), clinically justified by Habib & Abubakar (+1.01% mortality per hour of delay). **The threshold and the distance→time conversion are ours.** Finalist fix: MAP friction surface. |
| ~~Care-seeking~~ | **REMOVED** | — | **deleted in v0.4 — it double-discounted; see the correction above** |
| Vials / patient | 1.5 | 1–3 | **WHO PANAF-Premium product overview: Echis initial dose "1–3 vials"**; observed mean 1.23 in Ghana's Oti region (Ketor 2024) |
| Price / vial | $80 | $18–200 | Brown 2012 — $80 is an assumption inside his range, **not** a Brown point estimate. No authoritative price exists; published quotes span $3.4–$315, and $120/course sits inside the $100–153/dose baseline used in supply modelling (Potet 2020). |
| Safety buffer | 25% | — | **NOT CONFIRMED** — WHO/EPI sets stock in *months of stock*, not a percentage. A planning assumption, declared as such. |
| Envenoming fraction | 0.647 | — | Aglanu 2025 (64.7% of attendances had abnormal clotting); assumed outside northern Ghana |
| Product-choice CFR differential | **0.103** | 0.062–0.120 | **Visser 2008 — observed** (1.8% → 12.1%). Replaces the synthetic chain. |
| Untreated CFR / effectiveness | 0.16 / 0.75 | — | Habib 2015 — retained for the sensitivity band only, no longer in headline figures |

### ⚠️ CORRECTION IN v0.4 — this section previously contained a false claim

The v0.3 text asserted: *"The chain is conservative at both steps; it is not a double discount of the same quantity."* **That was wrong.**

The published Ghanaian rates are **facility snakebite ATTENDANCE rates** — people who have already reached a hospital. Multiplying them by a care-seeking fraction discounted the same quantity twice, and **understated the vial forecast by roughly half**. The care-seeking parameter has been **removed entirely** from both West-African models.

**The corrected chain** (each step named separately so none is silently conflated):

`facility attendance rate → envenoming fraction (0.647, Aglanu 2025) → Echis fraction → vials × (1+buffer)`

Outputs are therefore **antivenom demand at facilities**, not total community burden — the model deliberately does not estimate the unreached (community incidence in northern Ghana is ~10× the facility rate, Musah 2019). For a pre-positioning tool this is the right frame: you stock for the patients who arrive.

**Mortality was also re-anchored.** The old formula multiplied three assumed parameters (care-seeking × untreated CFR × effectiveness). It is replaced by a single **directly observed** Ghanaian measurement: when an ineffective antivenom was substituted in rural Ghana, treated-patient case-fatality rose **1.8% → 12.1%** (Visser 2008). We apply that **10.3-point differential**. This removed three assumptions and replaced them with one measurement.

## 7b. What is NOT sourced — shipped as a first-class artifact

`audit_parameters.py` classifies every load-bearing number as **CITED**, **DERIVED** or **ASSUMED** and prints the three largest exposures. Verification scripts check *arithmetic*; this audit checks *provenance*. They are different questions, and conflating them is what allowed earlier errors to survive rounds of "verification".

**Confirmation pass (v0.5).** All ten previously-assumed parameters were taken back to primary sources. **Four resolved, six did not.** The six are now labelled **NOT CONFIRMED** — meaning *searched hard, no published figure exists*, not *unchecked*.

Resolved: vials/patient (inside the WHO-published Echis dose); India's catch-all state rates (MDS Table 3 publishes its own "Northeastern states" 0.7 and "All other states" 3.2 rows — **no assumed state rate remains in India**, and the implied national rate 4.6/100k now matches Table 3's published All-India row of 4.5/100k); the 50 km reach (re-labelled a proxy for the published 3-hour standard); the vial price (bracketed and cross-checked).

Still not confirmed: Nigeria's per-zone rates and southern Echis fraction · Ghana's coastal rate and non-northern Echis fractions · India's adequacy tiers · the 25% buffer.

The three largest remaining exposures, stated plainly:

1. **India's adequacy tiers** — the coverage-gap headline is a direct function of magnitudes we chose. **No published national or state figure exists** (confirmed by targeted search of the primary literature, TRSTMH reviews and NAPSE). An adversarial literature review confirmed the *direction* of every tier and **no precise level**. The error sign is unknown. The published sub-national anchors — **68.4%** clinical ASV non-response in NW India (Gopalakrishnan 2025) and **66.19%** non-Big-Four share of identified venomous bites in Assam (Menon 2025) — are the hard evidence and should carry the argument.
2. **Nigeria's zone rates** — a **construction**; no published per-eco-zone figure exists. The gradient between the two savanna zones may even be inverted (the strongest community datum may belong to Katsina, not Benue; the 1980 source could not be obtained). And the Nigerian mortality gap **exceeds the published central national mortality** — flagged in the brief rather than tuned away.
3. **Ghana's coastal rate** — no published figure of any kind; the northern Echis fraction (0.90) rests on a hedged assertion, not a measurement.

## 8. Honesty guardrails — enforced in code, not promised in prose

1. **Headline is coverage**, not deaths. Coverage is what the tool controls.
2. **Deaths are a bounded decision-gap** versus a worst case (ineffective product everywhere) — explicitly *not* extra lives versus today, since effective antivenom already reaches some patients.
3. **No impact figure may exceed total national mortality.** Nigeria's upper bound is hard-capped at the highest published estimate (2,640; GBD 2019 UI upper) and the cap is disclosed wherever it binds. *This caught a real error:* the uncapped ceiling scenario produced 2,955 — an impossible number.
4. **Artifacts are quantified, not hidden.** Urban units inherit rural zone rates. Nigeria: disclosed, and shown not to drive the plan (only 1.9% of vials to FCT/Lagos). India: fixed at source via the 94/6 rural weighting.
5. **Stock is unobservable** subnationally → placement *choices* are modelled, never a false inventory.
6. **Corrections are carried, not dropped.** The brief states prominently that an earlier draft wrongly claimed no South-Asian products were WHO-assessed (seven are), and explains why the finding survives: assessment covers the Big-Four label, not regional variation or non-Big-Four species.

## 9. Sensitivity & robustness

- Coverage-% is **invariant to uniform incidence scaling** (it is a ratio); absolute demand scales linearly.
- **Placement is robust:** Ghana 24/25 and Nigeria 52/63 chosen facilities remain chosen when the north–south gradient is flattened.
- India's priority list is rural-dominated by construction (top-10 mean rural share 0.80) and contains no metro district.

## 10. Honest limits

1. **Per-zone facility attendance is the dominant uncertainty.** It is a construction bracketed by national surveillance below and community surveys above, not a transcription of any published per-zone figure — hence a range, not a point. (The old care-seeking multiplier, previously listed here, was removed in v0.4.)
2. **Access is straight-line**, not road travel time.
3. **Species presence is eco-zone-level**; coverage rests largely on preincubation ED50/antivenomics, not clinical RCTs — grade B ≠ proven bedside efficacy.
4. **India's facility layer covers 25 of 36 states** → the "far from care" figure is a floor, not a ceiling.
5. **India's district-name join matches 85.7%**; unmatched districts are filled to their state average, so *state totals stay exact*.
6. **India's ASV coverage-gap is a zone-level approximation**, not a per-patient prediction.
7. **Not clinical guidance** — informs procurement and placement only.

## 11. Verification

Independent scripts re-derive every published number from raw inputs and fail loudly on mismatch.

```
python3 verify_ghana.py        # 54 checks
python3 verify_nigeria.py      # 62 checks
python3 verify_india.py        # 62 checks
python3 verify_crosscountry.py # 67 checks — shared params, honesty invariants, no stale numbers
python3 audit_parameters.py    # provenance audit (not a pass/fail suite)
```

All **285** pass (Ghana 54 · Nigeria 62 · India 73 · Kenya 29 · cross-country 67). **They do not prove the model is correct** — they prove the arithmetic is consistent with the inputs and that specific past errors cannot recur. Input validity is the audit's job, and the audit says **6** of 28 load-bearing numbers remain NOT CONFIRMED. They also act as regression guards on the specific historical errors: the Nigeria 550k population bug, the "deaths averted" overstatement, the "Hospitaltal" upstream typo, and the false "zero South-Asia WHO-assessed products" claim.

## 12. Reproduce

```
python3 build_v2.py && python3 make_v2_visuals.py && python3 make_report_v2.py && python3 make_planner.py
python3 nigeria_build.py && python3 nigeria_outputs.py
python3 india_build.py && python3 india_outputs.py
python3 make_index.py
python3 verify_ghana.py && python3 verify_nigeria.py && python3 verify_india.py && python3 verify_crosscountry.py
```

## 13. Sources (verified against primary sources, July 2026)

- **Cost-effectiveness / impact:** Habib 2015, *PLoS NTD* 9(1):e0003381 — effectiveness **75%**, untreated CFR **16%**, cost/death **$2,330.16**, cost/DALY **$99.61** discounted / **$56.88** undiscounted *(all verified verbatim)* · Hamza 2016, *PLoS NTD* 10(3):e0004568 (16-country; $83–281/DALY). *Cite each for its own figure.*
- **National mortality:** GBD 2019 via *Nat Commun* 2022 13:6160 — Nigeria **1,460 (977–2,640)**, India **51,100 (29,600–64,100)**, global 63,400 *(verified verbatim)* · Habib 2015, *PLoS NTD* 9(9):e0004088 — Nigeria **1,927 (1,529–2,333)** · Suraweera 2020, *eLife* 9:e54076 — India **~58,000/yr**, **~94% rural**, **77% out-of-hospital**, 1.2 M deaths 2000–2019 *(verified verbatim)*.
- **Incidence:** Habib 2013, *J Venom Anim Toxins Trop Dis* 19:27 (West Africa 8.9–93.3/100k; Benue ~497/100k; only ~8.5% of Nigerian victims attend hospital) · Aglanu 2025, *PLoS NTD* (N Ghana ~55/100k facility) · Ceesay 2021, *Pan Afr Med J* 40:131 (Volta/Oti ~24/100k) · Musah 2019, *PLoS NTD* (community ~580/100k) · Ghana Health Service NTD Programme (~9,900 bites/yr).
- **Wrong-antivenom mortality:** Visser 2008, *TRSTMH* 102(5):445 — CFR **1.8% → 12.1%** ("sixfold").
- **Coverage matrix:** WHO risk-benefit-assessment product overviews (PANAF-Premium, EchiTAbG, Antivipmyn Africa) · Ainsworth 2018/2020 · Khochare 2024 *IJMS* 25:4213 · Edge 2025 *PLoS NTD* · Warrell 2008 · Senji Laxme/Sunagar antivenomics (India) · TRSTMH 2025.
- **Base layers:** geoBoundaries (CC BY) · Maina 2019 *Sci Data* 6:134 · Census of India 2011 · Ghana Statistical Service 2021 PHC · NIC HealthGIS · afripop2020 · GBIF.


## 12. Kenya (v0.7.0) — the fourth demonstrator

Kenya runs in the same facility frame as Ghana and Nigeria (no care-seeking multiplier). What is
different: **county populations are pinned to the KNBS 2019 census** (the 47 published county
figures, which sum exactly to the national 47,564,296; the coarse continental raster is used only
for within-county distribution, declared approximate) — and the **zone attendance rates carry
direct published area anchors** (Ochola 2018 hospital-record rates; Abouyannis 2023 paediatric
admissions), with the remaining zones a declared construction bracketed by Coombs 1997 (1.9–67.9
per 100k) and the community-side surveys (Snow 1994 coast 151/100k; Tianyi 2024 Samburu ≈440/100k
derived). The treated fraction (25.2%) is the verbatim figure of Abouyannis 2023; vials/treated
(1.40) is derived from its published distribution and is likely a floor. The product rule enforces
market availability: PANAF-Premium (WHO risk–benefit assessed; PPB-approved) is required for
facilities serving *Echis pyramidum* counties; SAIMR Polyvalent is the marketed alternative
elsewhere; AFRIVEN is potent in the QC panel but not commercialised in Kenya and is never
recommended; Inoserp failed three of five venoms and was withdrawn in 2022. Full parameter
provenance lives in `data/ke/parameters_ke.py`; the 29-check suite is `code/verify_kenya.py`;
the brief is `kenya.html`. Result: **45 hospitals → 86.6% of expected attendances within 50 km ·
1,569 vials/yr (~$125,520 at the $80/vial planning price)** · robustness 42/45 under halving of the
one NOT-CONFIRMED zone rate.
