# VLAI Severity Model — Train/Test Leakage Validation

Independent test of whether the reported accuracy of CIRCL's
[`vulnerability-severity-classification-roberta-base`](https://huggingface.co/CIRCL/vulnerability-severity-classification-roberta-base)
(VLAI) is inflated by train/test leakage in
[`CIRCL/vulnerability-scores`](https://huggingface.co/datasets/CIRCL/vulnerability-scores).

> See [VALIDATION.md](VALIDATION.md) for the project overview, design constraints and execution log.
> See [BACKLOG.md](BACKLOG.md) for live task state and open questions.
> See [findings/](findings/) for per-track findings reports.
> See [methodology/](methodology/) for reproducible step-by-step procedures.

**Status:** created 2026-08-07. **Nothing measured yet.** Five tracks defined, none started.

---

## The claim under test

| Metric | Reported on the model card (verified 2026-08-07) |
|--------|--------------------------------------------------|
| Accuracy | **0.8186** |
| F1 macro | **0.7510** |
| Low recall | 0.5058 — the weakest class |

Trained on `CIRCL/vulnerability-scores`: 745,736 entries, split 671,162 train / 74,574 test.

## Why this is worth testing

The same team's Chinese severity model was found four months earlier to carry **15.6% train/test leakage** through duplicated descriptions, because the split was done on identifiers rather than on description text. Its reported 78.3% accuracy was really 76.6%. See [`../CNVD-Dataset-Validation/`](../CNVD-Dataset-Validation/).

Three facts make the prior strong here, all read off the published cards:

1. **Identical training recipe** — 5 epochs, lr 3e-05, batch 32, seed 42. Same as the CNVD model.
2. **Neither card documents deduplication or split methodology.** That silence is where the CNVD defect lived.
3. **Low is the weakest class in both.** 0.5058 here; 38.4% corrected in CNVD.

And one reason the mechanism could be **larger** here: the corpus is 47.2% CVE Program and 47.0% GitHub Security Advisories, with `id` mixing CVE, GHSA and PYSEC. A GHSA advisory and its CVE are often the same vulnerability under two identifiers. Split on `id`, they separate — and the model sees test text during training.

## What is fact and what is not

**Fact:** the published metrics, the corpus composition, the split sizes, the absent split documentation.

**Assumption, and the first thing to test:** that GHSA and CVE descriptions actually duplicate. If they are written independently, the mechanism hypothesis collapses.

**A finding of "no leakage" is a deliverable, not a failure.** It would mean the CNVD defect was fixed rather than propagated, which is worth reporting. It is tracked as L1-5 in the backlog precisely so the project cannot quietly drop it.

## Tracks

| Track | Question |
|-------|----------|
| **L1** | How many test descriptions appear verbatim in training? |
| **L2** | If duplicates exist, is the mechanism GHSA↔CVE aliasing, boilerplate reuse, or CSAF re-publication? |
| **L3** | What is the accuracy on entries the model has not seen? |
| **L4** | How much apparent leakage is legitimate similarity? (control, built in from the start) |
| **L5** | Independent of the split, how much identifier aliasing does the corpus carry? |

L4 exists because the CNVD run nearly produced a fourfold overclaim: 71.7% of its test set shared a 50-character prefix with training data, and that was **not** leakage.

## Two things that could invalidate the design

Both recorded as P1 in the backlog rather than discovered late:

- **The corpus moves.** `vulnerability-scores` is updated roughly monthly and the model card pins no dataset revision. Leakage measured today may not be the leakage the model was trained under. Revisions must be pinned before any track runs.
- **The reported metric's population is undefined.** The card says "evaluation set" without saying whether that is the 74,574 test split. If it is not, reproduction targets a different population.

## Reproducing

Public data only. No CIRCL cooperation is assumed or required.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

*(scripts to follow — nothing has been run yet)*
