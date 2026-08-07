# VLAI Severity Model — Train/Test Leakage Validation

## Context

CIRCL publishes [`vulnerability-severity-classification-roberta-base`](https://huggingface.co/CIRCL/vulnerability-severity-classification-roberta-base) (VLAI), a four-class severity classifier trained on [`CIRCL/vulnerability-scores`](https://huggingface.co/datasets/CIRCL/vulnerability-scores). It is the English flagship of the VLAI family and is exposed through Vulnerability-Lookup's ML-Gateway.

This project tests one question: **is the reported accuracy inflated by train/test leakage?**

It exists because the same defect was found, measured, and quantified in the same team's Chinese model four months earlier. See [`../CNVD-Dataset-Validation/`](../CNVD-Dataset-Validation/), tracks R8 / R11 / R12 / R13.

### The claim under test

Published on the model card, verified 2026-08-07:

| Metric | Reported |
|--------|----------|
| Accuracy | **0.8186** |
| F1 macro | **0.7510** |
| Low — P / R / F1 | 0.6773 / 0.5058 / 0.5791 |
| Medium — P / R / F1 | 0.8501 / 0.8656 / 0.8578 |
| High — P / R / F1 | 0.8109 / 0.8214 / 0.8162 |
| Critical — P / R / F1 | 0.7575 / 0.7447 / 0.7510 |

Training hyperparameters: 5 epochs, lr 3e-05, batch 32, seed 42, AdamW (fused), linear schedule.

### Why the prior is strong

Three facts, all verified on the published cards, none inferred:

1. **The hyperparameters are identical to the CNVD MacBERT model** — 5 epochs, lr 3e-05, batch 32, seed 42. Same team, same recipe, same pipeline.
2. **Neither card documents deduplication or split methodology.** The CNVD card did not either, and that is exactly where its 15.6% leakage came from: the split was done on IDs, not on description text.
3. **Low recall is the weakest class in both.** 0.5058 here; 38.4% (leakage-corrected) in CNVD. The shape of the defect matches.

### Why the mechanism should be *larger* here

`vulnerability-scores` aggregates six sources: **CVE Program 47.2%, GitHub Security Advisories 47.0%**, Red Hat CSAF 3.6%, PySec 0.9%, CISA CSAF 0.8%, Cisco CSAF 0.5%. The `id` field mixes CVE, GHSA and PYSEC identifiers.

A GHSA advisory and the CVE it describes are frequently **the same vulnerability under two identifiers, with near-identical descriptions**. If the split was performed on `id`, both land in different splits and the model sees the test text during training.

> [!warning] This is a hypothesis, not a measurement
> Nothing above has been tested. The corpus composition and the missing split
> documentation are facts; **that GHSA and CVE descriptions actually duplicate is an
> assumption**, and it is the first thing L1/L2 must establish or refute. The project
> must be equally willing to report "no leakage found" — that would itself be a useful
> result, and would say the CNVD defect was fixed rather than propagated.

### Source materials

| Resource | Location |
|----------|----------|
| Model under test | `CIRCL/vulnerability-severity-classification-roberta-base` |
| Training corpus | `CIRCL/vulnerability-scores` — 745,736 entries, split 671,162 / 74,574 |
| Prior art (same defect, Chinese model) | `../CNVD-Dataset-Validation/` R8, R11, R12, R13 |
| Deployment context | Vulnerability-Lookup ML-Gateway |

---

## Design constraints

**Everything must run on public data.** No CIRCL cooperation is assumed or required — see the open question on communication in [BACKLOG.md](BACKLOG.md).

**The CNVD R13 lesson is built in from the start, not bolted on.** In CNVD, 71.7% of the test set shared a 50-character prefix with training data, and that was **not** leakage — those were legitimately similar entries. Reporting prefix overlap as leakage would have inflated the finding by a factor of four. This project therefore separates three distinct things from track L1 onward:

| | What it is | Is it leakage? |
|---|---|---|
| **Exact duplicate** | Identical description text across splits | Yes |
| **ID aliasing** | Same vulnerability under CVE and GHSA ids | Yes, if descriptions match |
| **Near duplicate / shared prefix** | Similar boilerplate, different vulnerability | **No** — control, not finding |

**Report the corrected number, not the delta.** CNVD's headline became 76.6%, not "1.7pp of inflation". If leakage is found here, the deliverable is the corrected accuracy on unleaked test entries.

---

## Validation Plan

### L1 — Exact-duplicate description scan

**Question:** How many test-split descriptions appear verbatim in the training split?

**Method:** Normalise whitespace and case, hash every description, intersect train and test. Report the count, the share of the test set, and the per-class breakdown.

**Status:** Not started

---

### L2 — Mechanism: is it GHSA↔CVE aliasing?

**Question:** If duplicates exist, what produces them?

**Method:** For each cross-split duplicate pair, compare the `source` and `id` prefix of both members. Three candidate mechanisms, to be separated rather than assumed:
- GHSA↔CVE aliasing (the hypothesis above)
- Within-source boilerplate reuse (the CNVD mechanism)
- Re-publication of the same advisory under multiple CSAF feeds

**Status:** Not started

---

### L3 — Leakage-corrected accuracy

**Question:** What is the accuracy on test entries the model has not seen?

**Method:** Reproduce the reported 0.8186 on the full test split first — without that, any corrected figure is uninterpretable. Then recompute on the unleaked subset. Report both, and the per-class table, since Low is the weak class in both models.

**Status:** Not started — **blocked on L1** (no correction to compute if no leakage exists)

---

### L4 — Near-duplicate control

**Question:** How much of any apparent leakage is legitimate similarity rather than leakage?

**Method:** The CNVD R13 procedure — 50-character prefix overlap, plus a similarity threshold sweep. Establish the accuracy on entries with **no** prefix match as the cleanest available figure.

**Status:** Not started

---

### L5 — Does the corpus contain the same vulnerability under multiple ids?

**Question:** Independent of the split, how much identifier aliasing does `vulnerability-scores` carry?

**Method:** Cluster by normalised description across the whole 745,736-entry corpus, regardless of split. This measures a property of the dataset that matters to any consumer, not only to the split.

**Status:** Not started

---

## Priority Order

| Priority | Track | Rationale |
|----------|-------|-----------|
| 1 | L1 — exact-duplicate scan | Cheapest, and decides whether the project continues at all |
| 2 | L2 — mechanism | Determines whether this is a new defect or the CNVD one propagated |
| 3 | L4 — near-duplicate control | Must land before L3 is reported, or the correction will overclaim |
| 4 | L3 — corrected accuracy | The deliverable, but only meaningful after L1/L4 |
| 5 | L5 — corpus-level aliasing | Useful to consumers independent of the leakage question |

---

## Log

| Date | Entry |
|------|-------|
| 2026-08-07 | Project created. Claim under test recorded from the published model card (accuracy 0.8186, F1 macro 0.7510). Corpus composition and split sizes recorded from the dataset card. Five tracks defined. **Nothing measured yet** — the leakage hypothesis is motivated by the CNVD precedent and the corpus composition, and is explicitly unverified. |
