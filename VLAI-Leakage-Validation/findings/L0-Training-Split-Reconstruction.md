# L0 — Reconstructing VLAI's training split

**Executed:** 2026-08-07 · **Dataset revision:** `5c017b72fba32aa8c700b512914935c2a385fd2c` (modified 2026-07-22)

L0 was not in the original plan. It was forced by a mistake made the same day in
`../CNVD-Dataset-Validation/`: a leakage correction was computed against the dataset's
**published** split when the model was trained on a different one, producing a spurious
result. Establishing which rows the model actually saw is therefore a **precondition**
for L1, not an optional refinement.

---

## 1. The published split is not the model's split

| | Rows |
|---|---:|
| Corpus | 745,736 |
| Published `train` | 671,162 |
| Published `test` | 74,574 |
| **Training examples the model actually saw** | **563,840** |

563,840 is derived from the model card's own training log: **17,620 optimizer steps per
epoch × batch size 32**. It matches neither the published train split nor any
deduplication of it (403,959 distinct train descriptions), nor an 80/20 or 90/10 of the
raw or deduplicated corpus.

## 2. What it does match

Severity labels must come from CVSS, and 119,412 rows carry **no CVSS score in any
version**, so they cannot be labelled.

| Candidate | Rows | vs 563,840 |
|---|---:|---:|
| 80/20 of raw corpus | 596,589 | +32,749 |
| 90/10 of raw corpus | 671,162 | +107,322 |
| 80/20 of deduplicated corpus | 336,531 | −227,309 |
| 80/20 of CVSS-labelable rows | 501,059 | −62,781 |
| **90/10 of CVSS-labelable rows (626,324)** | **563,692** | **−148 (0.026%)** |

**Conclusion:** the model is trained on a **90/10 split of the 626,324 rows that carry at
least one CVSS score.** The 148-row residual is consistent with the corpus having grown
slightly between the training run and this revision.

CVSS availability, for reference: `cvss_v3_1` 426,042 · `cvss_v2_0` 171,104 ·
`cvss_v3_0` 125,408 · `cvss_v4_0` 63,772.

## 3. What this does *not* establish

> [!CAUTION]
> **Matching the split's *size* does not identify its *method*.**
> Grouped splitting preserves row counts — CIRCL's Chinese model uses a grouped
> deduplicated split whose test half is 25,878 rows, still ≈20% of that corpus's raw rows.
> A 90/10 of 626,324 is therefore equally consistent with a plain random split and with a
> grouped one. **Assuming otherwise is the exact error L0 exists to prevent.**

## 4. The published split carries very large overlap — separately from the model

Measured on the same revision, on the dataset's own `train`/`test` split:

| | |
|---|---:|
| Distinct descriptions shared across splits | 52,780 |
| **Test entries carrying a train description** | **55,094 — 73.9% of the test split** |
| Distinct descriptions, whole corpus | 420,664 of 745,736 (**56.4%**) |

**43.6% of the corpus is descriptions that appear more than once.** For comparison, the
CNVD corpus showed 15.95% test-side overlap; this is **4.6× larger**.

This is a property of the **published split**, which the model does not use. It is
nonetheless a real trap for any third party who loads `vulnerability-scores` and uses its
built-in split — and the dataset card does not warn about it.

## 5. Where this leaves L1

The leakage question is now **open and precisely posed** rather than assumed:

- The Chinese model's card documents a grouped deduplicated split. **The English model's
  card says nothing** about split methodology, deduplication or evaluation-set size.
  Silence is "could not look", not "found nothing" — it is not evidence of absence.
- With 43.6% of rows carrying a repeated description, a *random* 90/10 would produce
  severe leakage; a *grouped* one would produce none.
- **Decisive test for L1:** score the model over the 626,324 labelable rows and compare
  accuracy on rows whose description is duplicated in the corpus against rows whose
  description is unique. A random split predicts a large gap; a grouped split predicts
  none. This tests the split's *method* through the model's behaviour, without needing
  CIRCL's seed — which is not published and cannot be recovered.
