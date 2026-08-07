# Backlog — VLAI Leakage Validation

Living list. Updated at every working checkpoint, not at the end.

**Status vocabulary:** `OPEN` · `IN PROGRESS` · `BLOCKED` · `DONE` · `DROPPED` (with reason)
**Priority:** `P1` acts on something time-sensitive · `P2` substantive · `P3` depth/nice-to-have

Last updated: **2026-08-07** — project created. Nothing measured yet.

> [!note] This one is live from checkpoint zero
> Unlike the retroactive backlogs in `CNVD-Dataset-Validation` and `LLM-Benchmark`, this
> file starts with the project. Items that emerge during work get added **immediately** and
> labelled *emerged during work* — those are the ones that turn out to matter, and they are
> exactly what a reconstructed backlog cannot recover.

---

## Time-sensitive

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| T1 | Decide whether findings have a recipient | P1 | **RESOLVED (open door)** 2026-08-07 | The 2026-08-06 no-communication decision was scoped to `Exploit-Hazard-Validation` and **does not extend here**. User: a communication *could* be made — not that one will be. Treat the outcome as undecided but the channel as available. **Consequence: this project is not record-only, so timing matters** — see T2 and T3 |
| T2 | Snapshot the dataset and model cards | P1 | **OPEN** | `vulnerability-scores` was updated 16 days before project start and the org publishes ~monthly. **The claim under test can change under the project.** Pin the revision hash for both repo and model before L1 runs, or the corrected accuracy will be computed against a moving target — the failure mode `Exploit-Hazard-Validation` hit with PR 530. Now also the evidentiary basis of any communication: a finding quoted against an unpinned card cannot be checked by its recipient |
| T3 | Keep the findings communicable as work proceeds | P2 | **OPEN** | *Emerged from T1.* Since a communication is possible, the reports must stay quotable by someone who has to act on them: claim → measurement → sample size, no dependency on internal context, and the reproduction path runnable from public data alone. Cheap if done throughout, expensive as a retrofit — `CNVD-Dataset-Validation` shows the shape (`GitHub-Issue-CIRCL.md` was drafted straight from the findings reports) |

---

## L1 — Exact-duplicate description scan

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| L1-1 | Pull `vulnerability-scores` at a pinned revision | P1 | OPEN | 745,736 rows, split 671,162 / 74,574. Record the revision hash in `data/` |
| L1-2 | Normalise descriptions (whitespace, case, zero-width) | P1 | OPEN | Zero-width characters bit the vault's clipping pipeline; `\s` does not match `U+200B`. Strip explicitly rather than relying on `.strip()` |
| L1-3 | Hash and intersect train ∩ test | P1 | OPEN | The single measurement that decides whether the project continues |
| L1-4 | Per-class breakdown of any duplicates found | P2 | OPEN | CNVD's leaked entries scored 87.6% against 76.6% unleaked. Per-class matters because Low is the weak class |
| L1-5 | Report "no leakage" as a result if that is what is found | P1 | OPEN | Stated as a task so it cannot quietly become a non-deliverable. A clean split would mean the CNVD defect was **fixed**, which is worth publishing |

---

## L2 — Mechanism

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| L2-1 | Cross-tabulate duplicate pairs by `source` | P1 | OPEN | Tests the GHSA↔CVE hypothesis directly. 47.0% GHSA + 47.2% CVE Program |
| L2-2 | Cross-tabulate by `id` prefix (CVE / GHSA / PYSEC) | P1 | OPEN | Aliasing shows up here even if `source` is coarse |
| L2-3 | Separate boilerplate reuse from aliasing | P2 | OPEN | The CNVD mechanism was within-source boilerplate. If both are present here they must be reported separately, not summed |

---

## L3 — Leakage-corrected accuracy

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| L3-1 | Reproduce 0.8186 on the full test split | P1 | **BLOCKED** on L1-1 | Without a reproduction, a corrected figure is uninterpretable. CNVD reproduced 78.29% against a reported 77.83% before correcting anything |
| L3-2 | Recompute on the unleaked subset | P1 | **BLOCKED** on L1-3 | The deliverable |
| L3-3 | Per-class table, corrected | P2 | BLOCKED | Low is 0.5058 recall as published |
| L3-4 | Lead with the corrected number, not the delta | P2 | OPEN | Decision, recorded now so it is not relitigated under a nice-looking delta |

---

## L4 — Near-duplicate control

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| L4-1 | 50-character prefix overlap | P1 | OPEN | **This control exists because CNVD R13 nearly produced a 4× overclaim**: 71.7% of its test set shared a prefix with train, and that was legitimate similarity, not leakage |
| L4-2 | Similarity threshold sweep | P2 | OPEN | Where does "duplicate" stop and "similar" start? Report the curve, not one cutoff |
| L4-3 | Cleanest-subset accuracy (no prefix match) | P2 | OPEN | CNVD's equivalent was 76.69%, consistent with its 76.6% exact-duplicate correction — the agreement is what made the finding credible |

---

## L5 — Corpus-level identifier aliasing

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| L5-1 | Cluster the full 745,736 corpus by normalised description | P3 | OPEN | A property of the dataset, independent of the split. Matters to anyone training on it |
| L5-2 | Report the aliasing rate per source pair | P3 | OPEN | Would tell a consumer how much of the 745k is distinct vulnerabilities |

---

## Open questions

| # | Question | Status | Note |
|---|----------|--------|------|
| Q1 | Do GHSA and CVE descriptions actually duplicate? | OPEN | **The project's central assumption, and entirely untested.** If they are independently written, the mechanism hypothesis collapses and L1 may still find CNVD-style boilerplate leakage instead — or nothing |
| Q2 | Which split did the reported metrics use? | OPEN | The card says "evaluation set" without defining it. If it is a validation slice rather than the 74,574 test split, reproduction targets a different population and L3-1 may not converge on 0.8186 |
| Q3 | Are severity labels derived from CVSS, and if so from which version? | OPEN | The corpus carries `cvss_v4_0`, `cvss_v3_1`, `cvss_v3_0`, `cvss_v2_0` as separate columns. If the four-class label is bucketed from whichever version is present, entries differ in **label provenance**, not just value — and a v2-derived "high" is not a v3.1-derived "high" |
| Q4 | ~~Does the 2026-08-06 no-communication decision extend here?~~ | **RESOLVED (no)** 2026-08-07 | It was scoped to `Exploit-Hazard-Validation`. A communication here is possible though not decided. A GitHub-issue draft is therefore worth writing — see T3 |
| Q6 | If a communication is made, is a GitHub issue the right channel? | OPEN | *Emerged from Q4.* CNVD drafted one against `vulnerability-lookup/vulnerability-lookup`, with Hugging Face discussions as the alternative. A **dataset** defect may belong on the dataset repo rather than the code repo, and a leakage finding is arguably a model-card correction rather than a bug report. Not decided |
| Q5 | Has the corpus changed since the model was trained? | OPEN | The dataset is updated ~monthly; the model card does not pin a dataset revision. Leakage measured on today's corpus may not be the leakage the model was trained under — **a real threat to the whole design**, and the reason T2 is P1 |

---

## Decisions taken

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-07 | Build the near-duplicate control into L1, not after it | CNVD R13 showed prefix overlap is not leakage. Adding the control late would have meant reporting a 4× overclaim first and retracting it |
| 2026-08-07 | Reproduce before correcting | A corrected accuracy without a reproduced baseline is not interpretable. This is the CNVD sequence and it is what made 76.6% defensible |
| 2026-08-07 | Treat "no leakage found" as a publishable result | Otherwise the project has an incentive to find something. Recorded as L1-5 so it is a deliverable, not a fallback |
| 2026-08-07 | Public data only; no CIRCL cooperation assumed | Keeps the project executable regardless of the answer to T1/Q4 |
| 2026-08-07 | A communication to CIRCL is possible, not excluded | User decision, narrowing the 2026-08-06 no-communication call to `Exploit-Hazard-Validation` alone. **The outcome is undecided — the channel is available.** Two consequences: pinning revisions (T2) becomes evidentiary and not just methodological, and the reports must stay quotable by an outside reader from the first track (T3) rather than be retrofitted at the end |

---

## Dropped

*(nothing yet)*
