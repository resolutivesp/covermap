# CoverMap

**Matching antivenom to the snakes that actually bite.**

Antivenom is species-specific: the wrong product does not save the patient. When rural Ghana
substituted an unsuitable antivenom against the carpet viper, district case-fatality rose
**1.8% → 12.1%** ([Visser 2008](https://doi.org/10.1016/j.trstmh.2007.11.006)).

CoverMap joins **what bites where** → **what each product is actually proven to neutralise** →
**who can reach care**, and returns a named, costed pre-positioning plan: which facility should
stock which antivenom, how many vials, at what annual cost.

**→ [Read the demonstrators](https://USUARIO.github.io/covermap/)**

---

## Three countries, two failure regimes

| | Headline | Demand forecast |
|---|---|---|
| **Ghana** | **86.0%** of the carpet-viper burden brought within reach via 25 hospitals | 4,654 vials/yr (~$371,114) |
| **Nigeria** | **85.5%** via 63 hospitals — the same method against the largest West-African burden | 36,671 vials/yr (~$2,931,101) |
| **India** | **36.8%** of burden where the standard ASV likely underperforms (~20,484 deaths/yr inside that gap) | targeting list, not placement |

In West Africa the binding gap is **which product** is stocked and where. In India a single
southern-sourced polyvalent is used nationwide, so the gap is **regional venom variation and
non-Big-Four species**. The same engine expresses both.

---

## Honest by design

This is a **feasibility demonstrator (IML 2)**, not a validated system, and it is built to say so.

- **We headline coverage, not deaths.** Mortality is a bounded decision-gap versus a worst case —
  explicitly *not* "extra lives saved versus today". In West Africa it uses an **observed**
  measurement (Visser's 1.8% → 12.1%), not a chain of assumed parameters.
- **No impact figure may exceed total national mortality.** Enforced in code, not promised in prose.
- **A parameter provenance audit ships with the code.** [`parameter-audit.txt`](parameter-audit.txt)
  labels every load-bearing number **sourced**, **partial** or **NOT CONFIRMED**. Six remain
  unconfirmed — including all of Nigeria's per-eco-zone incidence rates, because no published figure
  exists at any resolution. That is reported as a finding about the field, not buried.
- **Corrections are carried, not dropped.** See the changelog in [`methods.md`](methods.md).

**Not clinical guidance.** It informs procurement and placement, never individual treatment or
species identification.

---

## Reproduce

Every figure is re-derived from committed inputs; no network access required.

```bash
pip install geopandas rasterio rasterstats matplotlib pandas numpy rdata

python3 code/build_v2.py      && python3 code/make_v2_visuals.py \
  && python3 code/make_report_v2.py && python3 code/make_planner.py   # Ghana
python3 code/nigeria_build.py && python3 code/nigeria_outputs.py      # Nigeria
python3 code/india_build.py   && python3 code/india_outputs.py        # India
python3 code/make_index.py                                            # site
```

### Verification

Independent scripts re-derive every published number from raw inputs and fail loudly on mismatch.

```bash
python3 code/verify_ghana.py        # 54 checks
python3 code/verify_nigeria.py      # 62 checks
python3 code/verify_india.py        # 73 checks
python3 code/verify_crosscountry.py # 67 checks
python3 code/audit_parameters.py    # provenance audit (not pass/fail)
```

**256 checks pass.** They prove the arithmetic is consistent with the inputs and that specific past
errors cannot recur. They do **not** prove the inputs are correct — that is the audit's job, and the
audit says 6 load-bearing numbers remain unconfirmed.

---

## Attribution

Code: MIT (see [`LICENSE`](LICENSE)). **Input data carry their own licences:**

- Boundaries — [geoBoundaries](https://www.geoboundaries.org/) (CC BY)
- Facilities — Maina et al. 2019, *Sci Data* 6:134 · NIC HealthGIS (India)
- Population — Census of India 2011 · Ghana Statistical Service 2021 PHC · afripop2020
- Burden — Habib 2015 *PLoS NTD* 9(1):e0003381 · Suraweera 2020 *eLife* 9:e54076 ·
  GBD 2019 via *Nat Commun* 2022 13:6160 · Aglanu 2025 · Ceesay 2021
- Coverage matrix — WHO risk-benefit-assessment product overviews + peer-reviewed preclinical
  literature (Ainsworth, Khochare, Senji Laxme/Sunagar, Visser)

Full citations in [`methods.md`](methods.md).
