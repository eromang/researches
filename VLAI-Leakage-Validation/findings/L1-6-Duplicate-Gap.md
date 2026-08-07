# L1-6 — Duplicated-vs-unique accuracy gap

**Executed:** 2026-08-07 · **Dataset:** `CIRCL/vulnerability-scores@5c017b72` ·
**Model:** `…roberta-base@accca22d` · Both pinned before the run.

Designed as the decisive test of whether VLAI's 90/10 split is grouped or random,
without needing CIRCL's unpublished seed. **It is not decisive. The design is weaker
than intended, and the reason is stated below rather than buried.**

---

## 1. Result

Scored 626,053 of 745,736 rows — the CVSS-labelable population established in L0.
119,683 skipped (no CVSS in any version, or no text). **496,445 rows (79.3%) carry a
description that repeats somewhere in the corpus.**

| Arm | Accuracy | 95% Wilson | n |
|---|---:|---|---:|
| Overall | 0.8899 | — | 626,053 |
| Duplicated description | **0.8947** | [0.8939, 0.8956] | 496,445 |
| Unique description | **0.8713** | [0.8695, 0.8731] | 129,608 |
| **Gap** | **+2.34 pp** | intervals disjoint | |

Per class, the gap is not uniform:

| Class | Duplicated | Unique | Gap | n (dup / uniq) |
|---|---:|---:|---:|---|
| Low | 0.6595 | 0.6195 | +4.00 pp | 21,749 / 5,335 |
| Medium | 0.9235 | 0.9081 | +1.54 pp | 227,450 / 60,817 |
| High | 0.8970 | 0.8726 | +2.44 pp | 184,665 / 50,381 |
| **Critical** | 0.8653 | 0.7982 | **+6.71 pp** | 62,581 / 13,075 |

Label provenance: `cvss_v3_1` 381,235 · `cvss_v3_0` 108,759 · `cvss_v2_0` 72,406 ·
`cvss_v4_0` 63,653.

## 2. The design flaw, stated plainly

**The test assumed the two arms differ in whether the model saw the text. They barely do.**

Whatever the split method, **~90% of every scored row is training data** — the population
is the whole labelable corpus and the model trained on 90% of it. So:

| | P(text seen in training) | |
|---|---|---|
| **Random 90/10** | unique ≈ 0.90 · duplicated ≈ 0.99 | contrast ≈ **9 points** |
| **Grouped 90/10** | unique ≈ 0.90 · duplicated ≈ 0.90 | contrast ≈ **0** |

A random split therefore predicts a gap of roughly `0.09 × (memorisation advantage)`.
Taking CNVD's measured leaked-vs-unleaked advantage of ~11 pp as the scale, that is a
predicted gap of **~1 pp** — not the "large gap" the L0 write-up anticipated. The design
diluted its own contrast by a factor of ten, and I did not notice before running it.

## 3. What can and cannot be concluded

**Can:** the gap is real. 2.34 pp with disjoint intervals at n=626k is not noise, and it
is directionally consistent with a random split rather than a grouped one — it sits above
the ~1 pp a random split predicts and well above the ~0 a grouped split predicts.

**Cannot:** that duplication *causes* it. A competing explanation survives untested —
**duplicated descriptions may simply be easier**. Boilerplate text is formulaic and
repetitive, so a model would score it better than bespoke text under a *perfectly grouped*
split. Nothing here separates "seen before" from "intrinsically easier", and the two
predict the same sign.

> [!caution] Not enough to state that VLAI's reported 0.8186 is inflated
> That claim requires knowing the split method, and this test does not establish it.
> Asserting it would repeat the CNVD error of the same morning — where a leakage
> correction was computed against a split the model had never been trained on.

**The Critical class is the one live lead.** Its +6.71 pp gap is nearly three times the
overall figure on 75,656 rows. If duplication were merely "easier text", there is no
obvious reason the effect would concentrate in the highest-severity band. Worth chasing;
not evidence on its own.

## 4. What would actually decide it

Ranked by discriminating power, not by cost:

1. **Ask CIRCL.** One sentence on the model card — the split method, or the seed — closes
   this outright. The English card documents neither; the Chinese one documents both.
   Communication is not excluded (T1), which makes this the cheapest decisive option.
2. **Isolate the confound.** Compare duplicated against unique rows *matched on description
   length, source and CVSS band*. If the gap survives matching, "easier text" weakens.
3. **Multiplicity response.** Under a grouped split, a description appearing 2 times and
   one appearing 50 times are seen with identical probability. Under a random split, both
   are ~certainly seen, so this also discriminates poorly — recorded so it is not
   mistaken for a good idea later.
4. **Reconstruct the split by exhaustion.** Search seeds for a 90/10 partition of the
   626,324 labelable rows reproducing 563,840 training examples. Cheap per seed, but the
   partition function is unknown, so a negative result would prove nothing.

## 5. Status

L1-6 is **DONE and inconclusive**, which is a result and is recorded as one. L0-4 —
grouped or random — remains **OPEN**, and is now known to be harder than the project
assumed at scoping.
