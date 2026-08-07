# Backlog — CNVD Dataset Validation

Living list. Updated at every working checkpoint, not at the end.

**Status vocabulary:** `OPEN` · `IN PROGRESS` · `BLOCKED` · `DONE` · `DROPPED` (with reason)
**Priority:** `P1` acts on something time-sensitive · `P2` substantive · `P3` depth/nice-to-have

Last updated: **2026-08-07** — written retroactively. The project ran 2026-03-23/24 and was
declared complete on 2026-03-24, before this convention existed; this file reconstructs the
trail from [VALIDATION.md](VALIDATION.md) and the findings reports rather than from live notes.

> [!warning] Retroactive, and therefore weaker than a live backlog
> The point of a live backlog is to capture items *as they emerge*, because those are the
> ones nobody planned. This one cannot do that — it is assembled after the fact from the
> execution log. Items marked *emerged during work* below are identifiable because the log
> recorded them (R1 correcting V3, R8 finding the leakage); anything that emerged and was
> resolved without reaching the log is **not recoverable** and is not represented here.

**Project status: COMPLETE, then DORMANT since 2026-03-24.** No work in 4½ months. The
notes match that state — this is a closed project, not a stale one.

---

## Time-sensitive

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| T1 | File the drafted GitHub issue with CIRCL | P2 | **OPEN — live, not moot** | [GitHub-Issue-CIRCL.md](GitHub-Issue-CIRCL.md) is a **draft**. No record of it having been filed on `vulnerability-lookup/vulnerability-lookup` or the Hugging Face discussions. Q2 resolved 2026-08-07: the no-communication decision does **not** extend here, so this remains a real option. ⚠️ Before filing, re-check the findings against the current dataset — they were measured on the 2026-03-23 snapshot and the corpus has been updated since (HF shows `Vulnerability-CNVD` at 129k entries, updated Jul 6, against the 127,562 measured). **The leakage may already be fixed**, in which case filing an uncorrected issue would report a defect that no longer exists. See Q4. |

---

## V — Validation tracks

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| V1 | NVD overlap analysis | P1 | **DONE** | 81.0% CVE-mapped / 19.0% CNVD-only (n=10,457, 99% CI ±1.0%). Severity skew χ²=69.94, p=6.5e-16 |
| V2 | Model quality evaluation | P1 | **DONE** | 78.29% reproduced on the published split; corrected to **76.6%** by R11 once leakage was removed. Low recall 38.4% |
| V3 | Systematic bias detection | P2 | **DONE (corrected by R1/R2)** | Original verdict "functionally equivalent to a lookup table" was **overstated** and was corrected in place rather than quietly dropped |
| V4 | Dataset provenance | P1 | **DONE** | Dataset is a complete mirror of *published* CNVD entries. Missing IDs probed (n=100) are empty stubs — filtering is upstream at CNVD, not CIRCL |
| V5 | Vulnerability-Lookup integration audit | P2 | **DONE** | Model is **not** in the ingestion pipeline — a client-side JS badge that disappears silently if ML-Gateway is down. Zero severity mismatches (n=50) |
| V6 | Reproducibility — independent model rebuild | P3 | **DROPPED** 2026-03-24 | 8.5 h compute for a confirmatory result. R1/R2 already establish that keyword dependency is inherent to the data. See Q3 for what this costs |

---

## R — Evidence reinforcement

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| R1 | Keyword-heuristic baseline | P1 | **DONE** | *Emerged during work.* **Corrected V3.** A 15-line heuristic reaches 64.4%; the model beats it by 12.2pp, so it is not a lookup table |
| R2 | Typical vs atypical severity accuracy | P1 | **DONE** | *Emerged during work.* 89.4% vs 55.4% (χ²=1607, p≈0, n=10,787). The keyword dependency proven at scale |
| R3 | VLAI endpoint liveness | P3 | **DONE** | All 3 models responding. V5 updated |
| R4 | 10,457-sample reverse lookup | P1 | **DONE** | Tightened V1 from 95% CI ±2.2% to 99% CI ±1.0%. Confirmed the 1,232-sample estimate rather than moving it |
| R7 | Characterise the CNVD-only tail | P2 | **DONE** | Chinese-domestic PHP CMS/ERP; Hikvision, Kingsoft, UFIDA, Panwei present, Western vendors **absent** |
| R8 | Train/test duplicate-description scan | P1 | **DONE** | *Emerged during work.* **Data leakage found**: 1,587 duplicate descriptions, 15.6% of the test set. The single most consequential finding of the project |
| R9 | CNVD↔CVE links in the VL API | P3 | **DONE** | Stored internally, **not** exposed (404 on `/links`) |
| R10 | Why Low recall collapses | P2 | **DONE** | The model never predicts Low unless the *type* is typically Low — 87–100% miss rate on Low entries of typically-High types |
| R11 | Leakage-corrected accuracy | P1 | **DONE** | *Emerged during work.* **76.6%**, not 78.3%. This is the number the report leads with |
| R12 | Confirm the leakage mechanism | P2 | **DONE** | 94.1% of shared descriptions carry the same severity in both splits — CNVD boilerplate reuse across product IDs |
| R13 | Prefix-overlap control | P2 | **DONE** | 71.7% share a 50-char prefix, but these are legitimately similar entries, **not** leakage. Cleanest accuracy 76.69% — consistent with R11 |
| R14 | Out-of-distribution accuracy | P2 | **DONE (inconclusive)** | 80.56% on **n=36** — insufficient, and reported as insufficient. Most non-dataset CNVD IDs are empty stubs. R11's 76.6% remains the corrected metric |
| R5, R6 | *(not present in the execution log)* | — | — | The log jumps R4 → R7. Whether these were planned and dropped, or renumbered, is **not recoverable** from the record |

---

## Open questions

| # | Question | Status | Note |
|---|----------|--------|------|
| Q1 | Was the GitHub issue ever filed? | OPEN | The draft exists and is complete. Nothing in the repository records a submission, and absence of a record is **not** evidence it was not sent — this is "could not look", not "found nothing" |
| Q2 | ~~Does the 2026-08-06 "no communication with CIRCL" decision extend to this project?~~ | **RESOLVED (no)** 2026-08-07 | User answer: the decision was scoped to `Exploit-Hazard-Validation`; a communication here is possible though not decided. T1 therefore stays open rather than becoming `DROPPED`. The blocker on filing is no longer permission — it is **freshness**, see T1 and Q4 |
| Q3 | Is the keyword dependency inherent to the data, or to CIRCL's training run? | OPEN (accepted) | R1/R2 make it very likely inherent, which is why V6 was dropped. But that is the one thing an independent retrain would have *established* rather than inferred. Cost of the drop, stated plainly |
| Q4 | Has the leakage been fixed upstream since March 2026? | **OPEN — now blocks T1** | The dataset had ~monthly HF commits as of 2026-03-23. Observed 2026-08-07: `CIRCL/Vulnerability-CNVD` now shows **129k entries, updated Jul 6**, against the **127,562** these findings were measured on — so the corpus has moved and the model card was refreshed ~1 month ago. The 15.6% leakage may be fixed, unchanged, or worse; **not re-checked**. A single re-run of R8 answers it. This became load-bearing when Q2 resolved: filing an issue against a defect that has since been fixed would be the costliest possible outcome |
| Q5 | Does the RMSV attribution for the publication cliff hold causally? | OPEN (by design) | The coincidence between the 94%→4% coverage decline and RMSV (Sept 2021) is **measured**; the causal reading is inferred and is presented as such in the report. No counterfactual is available |
| Q6 | Is the 19.0% CNVD-only tail stable as the dataset grows? | OPEN | Measured once, at one snapshot. The tail is concentrated in 2020–2021, so continued ingestion of recent years should shrink it. Untested |

---

## Decisions taken

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-24 | Lead the report with **76.6%**, not the reproduced 78.29% | R11's leakage correction is the honest headline. Reporting the reproduced figure would have replicated CIRCL's own inflation while appearing to validate it |
| 2026-03-24 | Correct V3 in place rather than restate it | R1 showed the "lookup table" verdict overstated. The findings report was annotated with the correction so the original claim and its retraction both remain visible |
| 2026-03-24 | Report R14 as inconclusive rather than as an 80.6% result | n=36. Quoting it as a result would have been the exact overclaim the project was auditing |
| 2026-03-24 | Skip V6 | See Q3 — accepted cost, recorded rather than silently omitted |
| 2026-03-24 | Frame the review as characterisation, not critique | The dataset and model are useful; the question was what they actually are. Stated explicitly in the report so the tone is not mistaken for hostility |
| 2026-08-07 | A communication to CIRCL is possible, not excluded | User decision, narrowing the 2026-08-06 no-communication call to `Exploit-Hazard-Validation` alone. This reopens T1 — but the gate is now **freshness, not permission**: the findings are 4½ months old and the corpus has moved (Q4). Re-measure before filing |

---

## Dropped

| Item | Reason |
|------|--------|
| V6 — independent model rebuild | 8.5 h compute for a confirmatory result (Q3 records what this costs) |
| CVSS-based comparison | The dataset has no CVSS scores — severity is 3-class categorical. Not a gap in the work, a property of the source |
| Date-based cohort analysis | No date fields in the dataset. Year had to be derived from the CNVD ID pattern, which is why V4 reasons over sequence numbers instead |
