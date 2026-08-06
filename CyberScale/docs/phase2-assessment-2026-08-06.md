# Phase 2 contextual severity — assessment and options

**Date:** 2026-08-06 · **Status:** decision required, no action taken

The day began with a narrow request: three entity types under-performed, top up
their training data and retrain. The retrain was run and refuted its own premise,
and pulling that thread ended somewhere else entirely. This is the whole picture
in one place, because the individual findings are spread across backlog D3, D10,
D11, D12, D13, D14 and three documents, and separately none of them is
decidable.

## The one-line finding

**Phase 2 performs worse than ignoring context altogether.** On the only ground
truth it has never been trained to reproduce, returning the raw CVSS band scores
**36.95 %**; the deployed contextual model scores **34.2–34.6 %**.

## What was measured

The external validation set is 842 expert-labelled scenarios over 140 CVEs,
authored by a separate project before CyberScale existed, recovered on
2026-08-06 from vault git history after being deleted on 2026-03-30 as a "closed
predecessor project". 820 are usable. It is now tracked at
`evaluation/benchmarks/cve-severity-context/` with per-file hashes and five
integrity tests.

| approach | synthetic corpus | expert scenarios |
|---|---|---|
| ignore context, report the CVSS band | — | **36.95 %** |
| deployed contextual model (v4) | 81.71 % | 34.2–34.6 % |
| deterministic rule reproducing the generator | 87.65 % | 34.02 % |
| **de-escalation rules R1 (scope only)** | — | **41.95 %** * |
| **de-escalation rules R1+R2 (with deployment context)** | — | **48.63 %** * |

\* held-out split of 329 scenarios, where the passthrough baseline is 34.04 %.
Four balanced classes put chance at 25 %.

## Why it fails — three structural causes, in order of size

**1. The rules can only escalate.** Sector triggers, cross-border, CER status
and impact all raise severity; nothing lowers it. The expert lowers severity in
**378 of 842 scenarios (44.9 %)** and raises it in 157. The most common
contextual judgement in the real data is not expressible by the system and was
absent from every row the model trained on.

**2. The input the expert judges on never arrives.** The strongest predictors of
a downgrade live in the deployment description — *home* 96.6 %, *personal*
91.1 %, *single* 89.2 %, *workstations* 71.2 % of scenarios containing the term
are downgraded. Until today `predict()` had no parameter for it, while the MCP
docstring already promised one. No retraining closes a gap of this kind.

**3. The model does not learn the rules it was given.** On the synthetic corpus,
where the label is fully determined by the input, a ~60-line rule scores
**100.00 %** and the model **92.64 %** — 234 wrong answers whose value was
computable from what the model was shown. The remaining third of that corpus is
decided by a cross-border coin flip the generator never records, so no predictor
can recover it.

## Two figures that must stop being quoted

`metrics.json`'s **81.71 %** measures how well the model rehearses the rules that
generated its training data. It says nothing about correctness.

`evaluation/predecessor_benchmark.md`'s **88.0 %** is not reproducible. On the
278 scenarios whose counts are identical between that run and this data, today's
model scores 32.0 %. The report claims 100 % on six separate sector categories,
which a four-class model does not do. The circularity hypothesis was tested and
refuted — v1 did not train on this data — but the mechanism cannot be pinned
because v1's weights no longer exist. Treat the report as void.

## What exists now that did not this morning

- The external validation set, tracked and hash-verified, with a test that
  **fails rather than skips** when it is missing — it disappeared once already.
- `deployment_context` and `apply_de_escalation` on `predict()` and on the MCP
  tool. The context never enters the model's token stream; it drives a
  deterministic step on the output, because the weights never saw such a field.
  Off by default. A downgrade is always recorded in `key_factors`.
- De-escalation rules derived from the expert's own `threshold_matched`
  formulas, thresholds fixed on a 60 % split and reported on the untouched 40 %.
- A known reproducibility defect: the model returns different answers run to run
  even at `mc_passes=1` (D13).

## Options

### A — Turn on de-escalation, ship at ~49 %

Set `apply_de_escalation=True` and supply `deployment_context` from the calling
system.

*Buys:* the first configuration that beats the CVSS passthrough, by 8 points
with scope alone and 15 with context. Fully explainable, no model involved in
the correction.
*Costs:* a day of integration to source the deployment context per assessment.
*Risk:* 48.63 % on four classes is still wrong more often than right, and this
output feeds a regulatory qualification. Shipping it asserts a confidence the
measurement does not support.

### B — Rebuild the corpus so it can de-escalate, then retrain

Extend the generator to emit deployment contexts and downward moves, regenerate,
retrain, re-measure against the external set.

*Buys:* the only route to a model that can represent what an expert does.
*Costs:* the generator work is substantial, and the de-escalation semantics have
to be authored as regulation, not inferred — the 378 worked examples are the
material but not the decision.
*Risk:* everything measured today says model capacity is not the binding
constraint. This could reproduce D3's outcome at ten times the cost, and D3 cost
two hours of GPU to learn that more data changes nothing.

### C — Retire Phase 2's model, keep CVSS plus explicit scope rules

Replace the contextual model with the CVSS band and R1/R2 as deterministic
rules.

*Buys:* better accuracy than today, a 1.7 GB artifact and a GPU dependency
removed, an output that can be explained line by line — which matters more for
a regulatory instrument than a few points of accuracy. It applies the project's
own Lesson 18, already applied to the T-model and O-model, both removed.
*Costs:* small. The rules exist and are tested.
*Risk:* it concedes that Phase 2 as conceived does not work, and forecloses the
learned approach without a second independent dataset confirming the verdict.

### D — Stop and reconsider what Phase 2 is for

*Buys:* the honest option if contextual severity cannot be assessed from the
inputs available at assessment time. Nothing measured today distinguishes "we
built it wrong" from "this is not knowable from a CVE plus a sector".
*Costs:* none technically; it is a product decision.

## Recommendation

**C, with a deliberate pause before B.** The evidence for retiring the model is
now stronger than the evidence that was ever offered for keeping it: it loses to
its own input, it loses to a rule that reimplements its training labels, and the
one report claiming otherwise does not reproduce. C is cheap, reversible, and
makes the system explainable.

B remains the only path to something better than rules, but it should not start
until the de-escalation semantics are authored as a regulatory question. Building
the corpus first would encode whatever I inferred from 378 examples, and that is
exactly the mistake that produced the current corpus.

A is defensible only as an interim while B or C is decided, and only with the
accuracy stated to whoever consumes the output.

## What is not established

- Whether **any** predictor can do better from the inputs available. Nothing
  here separates a fixable design from an unanswerable question.
- Why the March benchmark reported 88 %. Refuted as circular; mechanism unknown;
  v1's weights are gone.
- Whether the external set is representative. It is one dataset, 140 CVEs, one
  author's judgement. Every conclusion above rests on it, and a second
  independent set would be the cheapest way to test the conclusions themselves.
- The larger version of that dataset — March ran against 1,833 scenarios, the
  recovered copy holds 842 — has not been found.
