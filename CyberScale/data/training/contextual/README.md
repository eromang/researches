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

## The deployed model is v2-era

`data/models/contextual/` at HEAD is byte-identical to its state before the v3 retrain, because that retrain was reverted. It is trained on the 8-entity-type v2 corpus, while `src/cyberscale/models/contextual.py` validates against 59 entity types and emits `ms_established:` / `ms_affected:`, which appear in none of the 32,000 v2 training rows. The two entity vocabularies have **zero overlap**. Tracked as `BACKLOG.md` D8.
