# contextual_train.csv — superseded v3 snapshot

This file is a **v3-era snapshot** of the Phase 2 contextual severity training data, committed by `106ad93 data(v3): regenerate Phase 2 training data with NIS2 entity types`. It is not what the training pipeline reads.

Three similarly named files exist, and they are three different schema generations. Telling them apart by name alone is not possible, which is how a byte-identical copy of this one survived unnoticed in `training/data/contextual/` until 2026-08-05.

| File | Generation | Distinguishing column | Tracked? | Used by |
|---|---|---|---|---|
| `training/data/contextual_training_v2.csv` | v2 | `deployment_scale` | no — `training/data/` is gitignored | `mix_predecessor.py` input |
| **`data/training/contextual/contextual_train.csv`** (this file) | **v3** | `cer_critical_entity`, no MS geography | **yes** | **nothing** |
| `training/data/contextual_training.csv` | **v4, current** | `ms_established`, `ms_affected`, `entity_affected` | no | `train_contextual.py`, published to HF |

`deployment_scale` was replaced by `entity_type` in v3, and `cross_border` by the `ms_established` / `ms_affected` pair in v4, which is why the schemas differ rather than the rows.

## Why it is kept

It is the only version-controlled copy of a training set. `training/data/` is gitignored by design — that directory holds generated corpora, a `cvelistV5` clone and other large working data — so nothing else under it survives a fresh checkout.

Keep it as a historical record, or delete it if the v4 dataset on HuggingFace is considered sufficient provenance. It is 17 MB and referenced by no code, so deleting costs nothing operationally. That is a call for the maintainer, not a cleanup task.

## Contents

32,000 rows, 59 entity types. Note the row count: `wc -l` reports 47,470 because `input_text` contains embedded newlines. Anything sizing this dataset by line count overstates it by roughly 48%.

Columns: `cve_id, input_text, sector, cross_border, cvss_score, base_severity, contextual_severity, label, entity_type, cer_critical_entity`. `label` is a 0–3 integer encoding of `contextual_severity`.
