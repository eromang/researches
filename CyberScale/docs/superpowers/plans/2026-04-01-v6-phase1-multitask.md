# v6 Implementation Plan — Phase 1 CVSS Vector Multi-Task Learning

**Goal:** Break Phase 1 band accuracy past 60% by predicting individual CVSS vector components as auxiliary tasks. Target >70%.

**Rationale:** v2 proved that feature additions (CWE) don't help — the bottleneck is description quality. CVE descriptions are formulaic regardless of severity. Multi-task learning decomposes the hard problem (predict overall severity) into easier sub-problems (predict attack vector, complexity, impact) that descriptions contain more signal for.

**Tech Stack:** ModernBERT-base, PyTorch, transformers (same as all other models)

---

## Architecture

```
Input: "Buffer overflow in OpenSSL allows remote code execution via crafted certificate"
                                    │
                              ModernBERT-base
                              (shared encoder)
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
         Band Head           8 Vector Heads         (optional)
         (4-class)          (2-4 classes each)      CPE Head
              │                     │                     │
         Critical/High/      AV: Network              vendor:
         Medium/Low          AC: Low                  openssl
                             PR: None
                             UI: None
                             S: Unchanged
                             C: High
                             I: High
                             A: High
```

**Loss:** `total_loss = band_loss + lambda * sum(component_losses)`
- `lambda = 0.3` (start), tune if needed
- Each component loss is cross-entropy with class weights
- Band loss remains the primary objective

---

## Tasks

### Task 1: Extract CVSS vector components from training data

**Files:**
- Modify: `training/scripts/fetch_bulk_cves.py`

The cvelistV5 data already contains CVSS v3.1 vectors. Extract the 8 components into separate columns.

**CVSS v3.1 vector string format:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`

Parse into:
- `av`: N/A/L/P (Network/Adjacent/Local/Physical)
- `ac`: L/H (Low/High)
- `pr`: N/L/H (None/Low/High)
- `ui`: N/R (None/Required)
- `scope`: U/C (Unchanged/Changed)
- `conf`: N/L/H (None/Low/High) — confidentiality
- `integ`: N/L/H (None/Low/High) — integrity
- `avail`: N/L/H (None/Low/High) — availability

**Verification:**
```bash
poetry run python training/scripts/fetch_bulk_cves.py --output training/data/training_cves_v6.csv
# Check: CSV has 8 new columns, >90% non-null for CVEs with CVSS v3.1
```

**Commit:** `feat(cyberscale): v6 extract CVSS vector components from training data`

---

### Task 2: Multi-head scorer model

**Files:**
- Create: `src/cyberscale/models/scorer_multitask.py`
- Create: `src/tests/models/test_scorer_multitask.py`

**Model class: `MultiTaskScorer`**

```python
class MultiTaskScorer(nn.Module):
    def __init__(self, base_model, num_band_labels=4, component_configs=None):
        # Shared ModernBERT encoder
        self.encoder = AutoModel.from_pretrained(base_model)

        # Band classification head (primary)
        self.band_head = nn.Linear(hidden_size, num_band_labels)

        # 8 component heads (auxiliary)
        # AV: 4 classes, AC: 2, PR: 3, UI: 2, S: 2, C: 3, I: 3, A: 3
        self.component_heads = nn.ModuleDict({...})
```

**Key design decisions:**
- Shared encoder, separate classification heads
- Each head has its own dropout for MC confidence
- Component heads are smaller (single linear layer) — they're auxiliary signals
- Band head gets more capacity (2-layer MLP with ReLU)

**Tests:**
- Test forward pass with all heads
- Test that band prediction works standalone (no components)
- Test MC dropout confidence per head
- Test component label maps

**Commit:** `feat(cyberscale): v6 multi-task scorer architecture (9 heads)`

---

### Task 3: Multi-task training script

**Files:**
- Create: `training/scripts/train_scorer_multitask.py`
- Create: `training/configs/scorer_multitask.json`

**Config:**
```json
{
  "model": {
    "base_model": "answerdotai/ModernBERT-base",
    "max_length": 256,
    "batch_size": 16,
    "learning_rate": 1e-5,
    "dropout": 0.3,
    "label_smoothing": 0.1,
    "weight_decay": 0.01,
    "mc_dropout_passes": 5,
    "warmup_ratio": 0.1,
    "gradient_clip": 1.0,
    "epochs": 20,
    "patience": 5,
    "seed": 42,
    "lambda_components": 0.3,
    "component_configs": {
      "av": {"num_labels": 4, "weight": 1.0},
      "ac": {"num_labels": 2, "weight": 0.8},
      "pr": {"num_labels": 3, "weight": 1.0},
      "ui": {"num_labels": 2, "weight": 0.8},
      "scope": {"num_labels": 2, "weight": 0.8},
      "conf": {"num_labels": 3, "weight": 1.0},
      "integ": {"num_labels": 3, "weight": 1.0},
      "avail": {"num_labels": 3, "weight": 1.0}
    }
  },
  "evaluation": {
    "test_split": 0.15,
    "val_split": 0.15
  }
}
```

**Training loop changes from `train_scorer.py`:**
- Multi-task loss: `band_loss + lambda * weighted_sum(component_losses)`
- Early stopping on val_acc (band head only — primary metric)
- Log per-component accuracy alongside band accuracy
- Save all heads in one model checkpoint

**Commit:** `feat(cyberscale): v6 multi-task training script + config`

---

### Task 4: Train and benchmark

**Steps:**
1. Generate training data with vector components
2. Train multi-task model
3. Compare against v1 baseline

**Run:**
```bash
# Generate data (if not done in Task 1)
poetry run python training/scripts/fetch_bulk_cves.py --output training/data/training_cves_v6.csv

# Train
poetry run python training/scripts/train_scorer_multitask.py \
    --data training/data/training_cves_v6.csv \
    --config training/configs/scorer_multitask.json \
    --output data/models/scorer_v6

# Benchmark
poetry run python training/scripts/evaluate_scorer.py \
    --model data/models/scorer_v6 \
    --data training/data/training_cves_v6.csv
```

**Success criteria:**

| Metric | v1 baseline | v6 target | Stretch |
|---|---|---|---|
| Band accuracy | 60.5% | >70% | >75% |
| Macro F1 | 56.4% | >65% | >70% |
| Per-component accuracy | N/A | >80% avg | >85% avg |

**If target not met:** Proceed to Task 5 (CPE/vendor signal).

**Commit:** `bench(cyberscale): v6 multi-task scorer results`

---

### Task 5: CPE product/vendor signal (conditional)

Only if Task 4 band accuracy <65%.

**Rationale:** "OpenSSL" or "Linux kernel" vulnerabilities are systematically higher severity than "WordPress plugin" at the same CWE. CPE vendor/product from cvelistV5 could add signal.

**Changes:**
- Extract CPE vendor/product from cvelistV5 data
- Add as input feature: `"{description} [SEP] cwe: {cwe} vendor: {vendor} product: {product}"`
- Retrain multi-task model with vendor/product
- Benchmark again

**Commit:** `feat(cyberscale): v6 add CPE vendor/product signal to scorer`

---

### Task 6: Integration + MCP tool update

**Files:**
- Modify: `src/cyberscale/models/scorer.py` or create wrapper
- Modify: `src/cyberscale/tools/vulnerability.py`

**Changes:**
- `score_vulnerability` MCP tool optionally returns predicted vector components
- Output includes: `score`, `band`, `confidence`, `predicted_vector` (dict of 8 components)
- Backwards compatible — existing callers get same output, new field is additive

**Commit:** `feat(cyberscale): v6 score_vulnerability returns predicted CVSS vector`

---

### Task 7: Publish + tag

- Publish scorer_v6 to HuggingFace (`eromang/cyberscale-scorer-v6`)
- Update README with v6 results
- Tag `cyberscale-v6`

**Commit:** `docs(cyberscale): v6 complete — Phase 1 multi-task scorer`

---

## Dependency graph

```
Task 1 (extract vectors) → Task 3 (training script) → Task 4 (train + benchmark)
Task 2 (model architecture) → Task 3
Task 4 → Task 5 (conditional: if <65%)
Task 4 or 5 → Task 6 (integration) → Task 7 (publish)
```

Tasks 1 and 2 can run in parallel.

## Success criteria

| Metric | Target |
|---|---|
| Band accuracy | >70% (vs 60.5% baseline) |
| Macro F1 | >65% (vs 56.4% baseline) |
| Per-component avg accuracy | >80% |
| No regressions | Phase 2/3 tests still pass |
| Full test suite | All pass |
