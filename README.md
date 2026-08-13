# CoverMap

**Matching antivenom to the snakes that actually bite.**

Antivenom is species-specific: the wrong product does not save the patient. When a rural Ghanaian
hospital switched from an effective antivenom to an unsuitable one against the carpet viper,
case-fatality among treated patients rose **1.8% → 12.1%**
([Visser 2008](https://doi.org/10.1016/j.trstmh.2007.11.006)).

CoverMap joins **what bites where** → **what each product is actually proven to neutralise** →
**who can reach care**, and returns a named, costed pre-positioning plan: which facility should
stock which antivenom, how many vials, at what annual cost.

**→ [Read the demonstrators](https://resolutivesp.github.io/covermap/)**

---

## Four countries, three failure regimes

| | Headline | Demand forecast |
|---|---|---|
| **Ghana** | **86.0%** of the carpet-viper burden brought within reach via 25 hospitals | 4,654 vials/yr (~$371,114) |
| **Nigeria** | **85.5%** via 63 hospitals — the same method against the largest West-African burden | 36,671 vials/yr (~$2,931,101) |
| **India** | **36.8%** of burden where the standard ASV likely underperforms (~20,484 deaths/yr inside that gap) | targeting list, not placement |
| **Kenya** | **86.6%** of expected attendances via 45 hospitals — the failing products were already withdrawn (2022); the gap is availability and placement | 1,569 vials/yr (~$125,520) |

In West Africa the binding gap is **which product** is stocked and where. In India a single
southern-sourced polyvalent is used nationwide, so the gap is **regional venom variation and
non-Big-Four species**. In Kenya the product triage is already done — the failing brands were
withdrawn in 2022 after national QC testing — so the gap is **availability and placement**. The
same engine expresses all three.

---

## Honest by design

This is a **feasibility demonstrator (IML 2)**, not a validated system, and it is built to say so.

- **We headline coverage, not deaths.** Mortality is a bounded decision-gap versus a worst case —
  explicitly *not* "extra lives saved versus today". In West Africa it uses an **observed**
  measurement (Visser's 1.8% → 12.1%), not a chain of assumed parameters.
- **No impact figure may exceed total national mortality.** Enforced in code, not promised in prose.
- **A parameter provenance audit ships with the code.** [`parameter-audit.txt`](parameter-audit.txt)
  labels every load-bearing number **sourced**, **partial** or **NOT CONFIRMED**. Six remain
  unconfirmed in the West Africa and India models — including all of Nigeria's per-eco-zone
  incidence rates, because no published figure exists at any resolution. Kenya carries its own
  declared table in `data/ke/parameters_ke.py`. That is reported as a finding about the field, not
  buried.
- **Corrections are carried, not dropped.** See the changelog in [`methods.md`](methods.md).

**Not clinical guidance.** It informs procurement and placement, never individual treatment or
species identification.

---

## Reproduce

Every figure is re-derived from committed inputs; no network access required.

```bash
pip install -r requirements.txt

python3 code/build_v2.py      && python3 code/make_v2_visuals.py \
  && python3 code/make_report_v2.py && python3 code/make_planner.py   # Ghana
python3 code/nigeria_build.py && python3 code/nigeria_outputs.py      # Nigeria
python3 code/india_build.py   && python3 code/india_outputs.py        # India
python3 code/kenya_build.py   && python3 code/kenya_outputs.py        # Kenya
python3 code/make_index.py                                            # site
```

### Verification

Independent scripts re-derive every published number from raw inputs and fail loudly on mismatch.

```bash
python3 code/verify_ghana.py        # 54 checks
python3 code/verify_nigeria.py      # 62 checks
python3 code/verify_india.py        # 73 checks
python3 code/verify_crosscountry.py # 67 checks
python3 code/verify_figures.py      # OCRs all 11 shipped figures
python3 code/audit_parameters.py    # provenance audit (not pass/fail)
```

**285 checks across five country suites (Ghana 54 · Nigeria 62 · India 73 · Kenya 29 · cross-country 67), plus an OCR pass over every figure.** The OCR suite exists because the others
all passed while three Ghana charts displayed `87.5%` — a pre-v0.4 value — and every text KPI on
the same page said `86.0%`. String checks cannot see a number baked into a PNG, which is the first
thing a reader sees. `verify_figures.py` reads each chart back with OCR and requires every
percentage it displays to be a value the model actually produced.

Together they prove the arithmetic is consistent with the inputs, that the figures agree with the
text, and that specific past errors cannot recur. They do **not** prove the inputs are correct —
that is the audit's job, and the audit says 6 load-bearing numbers remain unconfirmed.

---

## Attribution

Code: MIT (see [`LICENSE`](LICENSE)). **Input data carry their own licences** — checked against
each publisher's own licence page and documented per file in [`data/README.md`](data/README.md):

- Boundaries — [geoBoundaries](https://www.geoboundaries.org/) (CC BY 4.0) · Runfola et al. 2020,
  *PLoS ONE* 15(4): e0231866
- Facilities — Maina et al. 2019, *Sci Data* 6:134 (article CC BY 4.0, metadata CC0 1.0) ·
  NIC HealthGIS (India)
- Population — Census of India 2011 · Ghana Statistical Service 2021 PHC ·
  [WorldPop](https://www.worldpop.org/)/afripop2020 (CC BY 4.0)
- Burden — Habib 2015 *PLoS NTD* 9(1):e0003381 · Suraweera 2020 *eLife* 9:e54076 ·
  GBD 2019 via *Nat Commun* 2022 13:6160 · Aglanu 2025 · Ceesay 2021
- Coverage matrix — WHO risk-benefit-assessment product overviews + peer-reviewed preclinical
  literature (Ainsworth, Khochare, Senji Laxme/Sunagar, Visser)

Full citations in [`methods.md`](methods.md).
