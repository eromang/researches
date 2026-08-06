# Phase 2 contextual training data — provenance

The 17 MB `contextual_train.csv` that sat here was removed on 2026-08-05. This note records what it was and why keeping it stopped being necessary. It remains in git history at `106ad93`, so it is recoverable — and note that `git rm` does not shrink a clone, since the blob stays in history either way. The saving is working-tree bytes only.

## The three generations

Three similarly named files exist and they are three schema generations. Name alone does not distinguish them, which is how a byte-identical copy of one survived unnoticed in `training/data/contextual/` until 2026-08-05.

| File | Gen | Distinguishing column | Entity types | Tracked | On HuggingFace |
|---|---|---|---:|---|---|
| `training/data/contextual_training_v2.csv` | v2 | `deployment_scale` | 8 | no | **yes** — served as `contextual_training.csv` |
| `data/training/contextual/contextual_train.csv` | v3 | `cer_critical_entity`, no MS geography | 59 | was; removed | no |
| `training/data/contextual_training.csv` | v4, current | `ms_established`, `ms_affected`, `entity_affected` | 59 | no | no |

`deployment_scale` was replaced by `entity_type` in v3, and `cross_border` by the `ms_established` / `ms_affected` pair in v4. All three hold 32,000 records — `wc -l` reports ~47,000 because `input_text` contains embedded newlines, overstating the size by about 48%.

An earlier version of this file claimed v4 was "published to HF". It is not. See below.

## Why removal costs nothing

v4 is **byte-reproducible from published and version-controlled inputs**. Verified 2026-08-05 by regenerating it and comparing hashes:

```
poetry run python training/scripts/generate_contextual.py \
  --cves training/data/training_cves.csv \
  --rules data/reference/sector_severity_rules.json \
  --config training/configs/contextual_cls.json \
  --output <out>.csv
# sha256 090bd96c2abe685affa5418f6881526c9d4773e01ad05cad7b26c9bc56f4ba6f
# identical to training/data/contextual_training.csv
```

Generation is seeded (`random.Random(seed)`, seed read from `contextual_cls.json`). Of the three inputs, the rules and the config are tracked, and `training_cves.csv` is published byte-for-byte at [`eromang/cyberscale-training-cves`](https://huggingface.co/datasets/eromang/cyberscale-training-cves) — sha256 verified, 12,719,939 bytes. So no training corpus depends on an untracked local file, which was the concern that kept v3 here.

v3, by contrast, was the input to a retrain that was **reverted** in `575c625`. It is provenance for an artifact that was never shipped.

## What the HuggingFace dataset actually contains

[`eromang/cyberscale-contextual-training`](https://huggingface.co/datasets/eromang/cyberscale-contextual-training) serves a file named `contextual_training.csv`, which reads as the current one. It is **v2** — sha256 `d3ff30f8…`, byte-identical to the local `contextual_training_v2.csv`, uploaded 2026-03-31T04:16Z, before v3 and v4 existed. The dataset card also declares `size_categories: 1K<n<10K` for a 32,000-record file and documents a two-column schema.

Anyone reaching for that dataset expecting the current training set gets the wrong generation. Correcting it means re-uploading to a public repository, so it is the maintainer's call and is tracked in `BACKLOG.md`.

## The deployed model is v4-trained

`data/models/contextual/` is trained on **v4** and has seen all 59 entity types. Three independent lines of evidence:

- **Dates.** v4 written 1 Apr 03:48 → `model.safetensors` 05:31 → `metrics.json` 06:59. The weights postdate v4 by 1 h 43.
- **Metrics.** Evaluating the deployed model on the v4 test split (stratified, seed 42) reproduces `metrics.json` to four decimals on five metrics: 81.71 % accuracy, macro F1 0.8148, per-class 0.9163 / 0.7770 / 0.7058 / 0.8601.
- **Behaviour.** On the 1,500 test rows whose `entity_type` does not exist in v2 at all, it scores 80.67 % — indistinguishable from its overall 81.71 %. A model blind to those tokens could not do that.

> **An earlier version of this file claimed the opposite**, on the strength of `git diff c51b3b6~1 HEAD -- data/models/contextual/` returning empty. **`data/models/` is gitignored**, so that diff compared nothing. An empty diff over untracked paths is the absence of evidence, not evidence of identity — and the two commits it named turn out to have touched only stray HuggingFace `.cache/` metadata, never any weights. Nothing was ever retrained-then-reverted.

What does survive: accuracy on the three entity types the IR scope fix re-routed to this model — `ixp_operator`, `public_ecn_provider`, `public_ecs_provider` — is **66.0 %** against 81.7 % overall. Wilson 95 % intervals [52.2, 77.6] and [80.6, 82.8] do not overlap, so the gap holds even at n = 50. Reproduce with `evaluation/eval_contextual_vocabulary.py --by-entity-type`. Tracked as `BACKLOG.md` D3/I3.
