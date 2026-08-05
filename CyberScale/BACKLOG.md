# Backlog — CyberScale

Live task state. Updated at every working checkpoint, not at the end.

This is the working list: what is open, what was found mid-work, what was decided
and why. It is **not** the milestone plan — that is
[`docs/enhancement-roadmap.md`](docs/enhancement-roadmap.md), which tracks planned
version work. Items here are things discovered while doing something else, plus
decisions worth not relitigating.

**Status:** `OPEN` · `IN PROGRESS` · `BLOCKED` · `DONE` · `DROPPED` (with reason)
**Priority:** `P1` acts on something time-sensitive · `P2` substantive · `P3` depth

Last updated: **2026-08-05**

---

## Time-sensitive

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| T1 | ILR consultation CP/N26/2 | P1 | OPEN | The draft abrogates eleven NIS1-era ILR regulations; CyberScale implements nine. Impact analysis and an independent observations section: [`docs/lu-n26-consultation-impact.md`](docs/lu-n26-consultation-impact.md). Consultation window closes — check the ILR notice for the date. |
| T2 | PR 530 merge unblocks Phase 0 step 3d | P2 | BLOCKED | [vulnerability-lookup#530](https://github.com/vulnerability-lookup/vulnerability-lookup/pull/530) is OPEN at `c5ccb64`. Until it lands there is no `POST /api/exploit-hazard` to use as an optional single-CVE backend. |

---

## Data integrity

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| D1 | 27 invalid `entity_type` values in curated datasets | P2 | OPEN | Absent from `nis2_entity_types.json`. **4** in `curated_lu_incidents` (`road_transport_operator` ×2, `gas_distribution_operator`, `digital_service_provider`); **23** in `curated_multi_entity`, where sector names (`chemicals`, `space`, `postal`, `research`, `waste_management`, `financial_market`, `non_nis2`, `drinking_water`) sit in the `entity_type` field. Pre-existing. Each needs a per-entry judgement — `chemicals` plausibly maps to `chemicals_manufacturer`, `space` and `research` genuinely do not — and correcting them shifts benchmark semantics. |
| D2 | Decide the fate of `contextual_train.csv` | P3 | OPEN | 17 MB v3 snapshot, tracked, referenced by no code, superseded by `contextual_training.csv` (v4). Kept because `training/data/` is gitignored so this is the only version-controlled training set. Delete if the HuggingFace v4 dataset is sufficient provenance. Maintainer call, documented in [`data/training/contextual/README.md`](data/training/contextual/README.md). |
| D3 | Thin training coverage for three newly ML-routed entity types | P2 | OPEN | The IR scope fix moved `ixp_operator`, `public_ecn_provider` and `public_ecs_provider` from tier 1 (IR deterministic) to tier 3 (ML), so the model is now answerable for them. They carry 145 / 140 / 155 rows against a **299.5 median** across the 48 ML-routed types — roughly half, though above the 87 minimum. Labels are sound (they track `digital_infrastructure`, not IR logic). Top up at the next retrain; not a reason to retrain alone. |
| D4 | `evaluation/curated_benchmark.md` header figures are stale | P3 | OPEN | The 97.5% / 96.2% recorded there date from 2026-03-30, before the v4/v5/v8 changes that made T and O deterministic. Current: T 95.7%, O 82.6%, matrix 91.3% on 46 incidents. Verified that the six 2024-2026 additions score 6/6 on both axes and **raised** the averages; every failure is pre-existing. |
| D5 | `data/training/` vs `training/data/` is a confusing pair | P3 | OPEN | One is tracked and holds a single superseded file; the other is gitignored and holds the working corpus. A byte-identical duplicate survived in the gap until 2026-08-05. Consider renaming one. |

---

## Regulatory — Luxembourg

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| R1 | Switch LU to N26 on entry into force | P1 | BLOCKED | `lu_n26.py` is implemented and tested (14 tests) but **not wired into the router**. `lu.py` remains the default because the draft is not in force. Switching should be a deliberate act on the adoption date, not a side effect. |
| R2 | No implemented rule for electronic communications providers | P2 | OPEN | With IR correctly scoped, LU telecom falls to the general ML model. The applicable national text is **ILR/N23/3**, which CyberScale never implemented and which N26 also abrogates. Under N26 it would fall to the generic Art. 2(1) criteria. |
| R3 | Four N26 criteria need fields the impact taxonomy lacks | P2 | OPEN | Trade-secret exfiltration (d), physical access compromise (f), direct financial loss and turnover in euro (j), prejudice amounts (k). `lu_n26.py` accepts them as optional and reports them in `not_evaluable`. Adding them to `impact_taxonomy.json` is the real fix. |
| R4 | N26 Art. 2(4) recurrence needs incident history | P3 | OPEN | Two occurrences in six months sharing a root cause, collectively meeting criterion (j). CyberScale assesses one incident at a time and holds no such state. `assess_recurrence()` is exposed separately so the requirement stays visible rather than silently unmet. |
| R5 | N26 annexes are unpublished | P3 | BLOCKED | Art. 2(1)(l) and 2(5) let ILR reintroduce sector-, entity-type- or group-specific criteria by annex. None shipped with the consultation draft, so criterion (l) is permanently `not_evaluable`. This is the route by which the nine abrogated sector regulations could effectively return. |

---

## Exploit hazard integration

Design and evidence: [`docs/exploit-hazard-integration-design.md`](docs/exploit-hazard-integration-design.md).
Underlying validation: sibling project `../Exploit-Hazard-Validation/`.

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| E1 | Step 1 — fix EUVD exploited set | P1 | **DONE** | `get_exploited()` paginates `/search?exploited=1` (1,665) instead of the 4-record "latest" view |
| E2 | Step 2 — CIRCL KEV as exploitation source | P1 | **DONE** | EUVD's exploited flag is 99.7% CISA. CIRCL KEV holds 2,789 distinct CVEs with per-source provenance |
| E3 | Step 3a-3c — Phase 0 prioritisation | P2 | **DONE** | Ranking only. Benchmark reproduces the validation's AUC-ROC in 11/11 cells exactly |
| E4 | Step 3d — CIRCL endpoint as optional backend | P3 | BLOCKED | See T2. Right shape for single-CVE explain-this-one calls, wrong for ranking an inventory |
| E5 | Step 4 — dependency-graph correlation | P3 | OPEN | The paper defers correlated exposure to future work (§5.3, "a graph-based dependency structure"). `aggregation.py:53 propagate_cascading()` already walks the ENISA/CER sector graph for incident impact. Research track, no delivery date. |
| E6 | Never aggregate hazard with the independence product | P2 | OPEN (guard) | Not a task, a constraint. Measured overstatement reaches **247×** per component (Linux kernel: `EL_g` 0.79 when the most exploitable CVE scored 0.0032). Fleet-wide it is mild (1.14–1.30×). If a per-entity or per-sector hazard rollup is ever requested, this is the trap. |

---

## Testing and infrastructure

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| I1 | `be.py` evaluated only `thresholds[0]` | P2 | **DONE** | All three availability thresholds now evaluate, plus the maintenance exclusion. Surfaced two wiring gaps: the router never passed `affected_persons_pct`, and `0.0` was indistinguishable from "unmeasured" |
| I2 | Full suite needs `poetry install` | P3 | **DONE** | 545 pass. `src/tests/store` needs chromadb and the model tests need torch; a light venv skips them cleanly rather than failing |
| I3 | Validate ML inference for the three re-routed entity types | P2 | OPEN | Related to D3. The tests pass, but nothing has exercised actual model predictions for `ixp_operator` / `public_ecn_provider` / `public_ecs_provider` since they started routing to the ML path. |

---

## Open questions

| # | Question | Status | Note |
|---|----------|--------|------|
| Q1 | Are the 23 multi-entity `entity_type` values a mistake or a different convention? | OPEN | They are consistently sector names. If deliberate, the field is misnamed; if not, each needs mapping. Determines whether D1 is a rename or 23 judgements. |
| Q2 | When does N26 enter force, and does it change on consultation feedback? | OPEN | Gates R1. The criteria implemented in `lu_n26.py` are the *draft*; adoption may alter them. |
| Q3 | Will the annexes reintroduce sector-specific thresholds? | OPEN | Gates R5 and determines whether the nine abrogated regulations effectively survive in another form. |
| Q4 | Does the ML model perform adequately on the three re-routed entity types? | OPEN | Gates D3/I3. If not, the IR scope fix traded a wrong deterministic answer for an unreliable probabilistic one. |
| Q5 | Should Phase 0 default `k` track the validation as catalogues age? | OPEN | `k` drifts with observation date (0.684 Jan 2025 → 0.576 Aug 2026). The 0.55 default is a 2026-08 ranking choice, not a constant. Re-check when the validation re-runs. |

---

## Decisions taken

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-05 | Exploitation status comes from CIRCL KEV, not EUVD | EUVD's exploited set is 99.7% CISA with an identical median TTE. Reaching for EUVD looks like a sovereignty decision and does not function as one. |
| 2026-08-05 | IR scope follows Article 1, not our entity list | `ir_incident_thresholds.json` listed 14 entity types; IR (EU) 2024/2690 Art. 1 names 11 and Arts. 5–14 cover exactly those. Verified against the Official Journal text. |
| 2026-08-05 | `exploited` is three-valued | True and False are catalogue answers; None means the lookup failed. Collapsing the last into False reports "not exploited" on every network error. |
| 2026-08-05 | `time_to_exploit_days` stays signed | Exploitation before publication is a real category, not something to clamp away. |
| 2026-08-05 | Age is a function, not a record field | `age_days(record, as_of=)` — a value that changes between calls does not belong in something callers may cache. |
| 2026-08-05 | `affected_persons_pct` is `float \| None` | `None` means the entity could not determine the count, which is what BE's `unknown_scope` threshold exists for. `0.0` asserts no users were affected. The old `0.0` default collapsed the two. |
| 2026-08-05 | `lu_n26.py` sits alongside `lu.py` rather than replacing it | The draft is not in force. Replacing in-force rules with a consultation draft would be wrong; a parallel module makes adoption a configuration change. |
| 2026-08-05 | Phase 0 emits no rate, count or probability | The model's rate output is denominated in third-party sensor detections and runs ~55× above any observable feed. Not reportable. |
| 2026-08-05 | Phase 0 `k` defaults to 0.55, not the paper's 0.605 | 0.605 falls outside every properly-estimated interval (0.52 curated / 0.72 observational), and for ranking lower k performs better. Stated as a ranking choice, not a calibration claim. |
| 2026-08-05 | Unrankable and unresolvable entries are excluded, not sorted last | Placing an unrankable vulnerability at the bottom of a remediation queue asserts it is least urgent. |
| 2026-08-05 | Real incidents go to `real_incident_validation.json`; `curated_*` stay synthetic | Except `curated_incidents.json`, which was always real-world. Follows the project's own README. |
| 2026-08-05 | BE-12 kept as a negative case rather than made to pass | The AZ Monica reporting gives no duration, and every BE availability threshold needs one. Supplying a plausible figure would be inventing evidence. Assessing real incidents from open reporting routinely lacks the fields criteria are written around. |

---

## Dropped

| Item | Reason |
|------|--------|
| Consume CIRCL's `POST /api/exploit-hazard` for Phase 0 ranking | Right for single-CVE third-party lookups, wrong for ranking an inventory — one HTTP call per CVE, when the age term is four locally-validated lines. Retained as E4, an optional backend for single-CVE calls. |
| Adding EPSS as a Phase 1 feature | Would blur severity and likelihood together. Wrong on the modelling side, and wrong under NIS2 where Art. 23 significance is impact-based. Became the separate Phase 0 surface instead. |
| Proximus/Tango as an LU curated scenario | Its RETEX records `nis2_significant: false`, but under the IR criteria a 4-hour degradation would trigger. Resolving that needs an EECC-versus-NIS2 determination the vault does not make. |
