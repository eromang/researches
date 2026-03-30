# Low-Severity Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix T1/O1 over-escalation by expanding low-severity training data, mixing curated incidents, and adding confidence-weighted loss.

**Architecture:** Three changes to the existing pipeline: (1) expand generation rules for T1/O1 in `generate_incidents.py`, (2) new `mix_curated.py` script to convert curated JSON to training CSVs with weight column, (3) add per-sample weight support to both training scripts. Then retrain and re-benchmark.

**Tech Stack:** Python 3.12, PyTorch, ModernBERT-base, existing training pipeline.

---

### Task 1: Expand T1/O1 generation rules

**Files:**
- Modify: `training/scripts/generate_incidents.py`
- Test: `src/tests/test_generation_balance.py`

- [ ] **Step 1: Write a test that checks raw T1 count is at least 500**

Create `src/tests/test_generation_balance.py`:

```python
"""Tests for improved T1/O1 generation balance."""

import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from generate_incidents import generate_t_samples, generate_o_samples


def test_t1_raw_count_at_least_500():
    """T1 must have at least 500 raw samples (was 120)."""
    t_raw = generate_t_samples(2000, paraphrase_variants=3, seed=42)
    t1_count = sum(1 for s in t_raw if s["label"] == "T1")
    assert t1_count >= 500, f"T1 raw count {t1_count} < 500"


def test_o1_raw_count_at_least_800():
    """O1 must have at least 800 raw samples (was 384)."""
    o_raw = generate_o_samples(2000, paraphrase_variants=3, seed=42)
    o1_count = sum(1 for s in o_raw if s["label"] == "O1")
    assert o1_count >= 800, f"O1 raw count {o1_count} < 800"


def test_no_class_regression():
    """T3/T4 and O3/O4 must not drop below 1000 raw samples."""
    t_raw = generate_t_samples(2000, paraphrase_variants=3, seed=42)
    o_raw = generate_o_samples(2000, paraphrase_variants=3, seed=42)
    t_counts = Counter(s["label"] for s in t_raw)
    o_counts = Counter(s["label"] for s in o_raw)
    for level in ["T3", "T4"]:
        assert t_counts[level] >= 1000, f"{level} dropped to {t_counts[level]}"
    for level in ["O3", "O4"]:
        assert o_counts[level] >= 1000, f"{level} dropped to {o_counts[level]}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest src/tests/test_generation_balance.py -v`
Expected: `test_t1_raw_count_at_least_500` FAILS (T1=120), `test_o1_raw_count_at_least_800` FAILS (O1=384)

- [ ] **Step 3: Modify generate_incidents.py**

Apply these changes to `training/scripts/generate_incidents.py`:

**a) Add 15 low-severity description templates** — insert after line 109 (after `BASE_TEMPLATES` list closing bracket):

```python
# Additional templates biased toward low-severity (T1) scenarios
LOW_SEVERITY_TEMPLATES = [
    "Automated port scan detected on {sector} external-facing web server. No exploitation attempted. Standard reconnaissance activity logged by IDS.",
    "Failed phishing email campaign targeting {sector} employees. All emails caught by spam filter. No credentials compromised. Security awareness team notified.",
    "Routine vulnerability scan found unpatched {sector} test server with {data_comp} exposure risk. Server is isolated from production networks.",
    "Single failed SSH brute force attempt against {sector} bastion host. Account locked after 5 attempts. No successful authentication.",
    "Expired SSL certificate on {sector} internal documentation portal caused browser warnings for {entities} users. No data exposure, certificate renewed within hours.",
    "Minor configuration drift detected in {sector} firewall rules. One non-critical port briefly exposed. No evidence of exploitation. Remediated same day.",
    "Commodity adware found on single {sector} employee workstation during routine scan. No lateral movement. Workstation reimaged per standard procedure.",
    "Low-confidence threat intelligence alert for {sector} IP range. Investigation found no indicators of compromise. Alert classified as false positive.",
    "Unauthorized USB device connected to {sector} workstation. Device contained no malware. Policy violation documented and employee counseled.",
    "Brief DNS resolution delay affecting {sector} internal services for {entities} users. Root cause was upstream provider maintenance, not an attack.",
    "Outdated {sector} web application flagged by automated scanner. Application is public-facing but read-only with no sensitive data.",
    "Test credentials found in {sector} code repository. Credentials were for development environment only with no production access.",
    "Minor defacement of low-traffic {sector} informational website. Content restored from backup within one hour. No data access.",
    "Suspicious login attempt on {sector} VPN from unusual geography. Multi-factor authentication prevented access. User confirmed no compromise.",
    "Scheduled penetration test triggered {sector} IDS alerts. All activity was authorized and within scope. No actual security incident.",
]
```

**b) Add low-severity templates to generation** — modify `generate_t_samples` function. Replace line 336-338:

```python
        # Pick a template deterministically from combo hash
        tmpl_idx = hash((disruption, cascading, data_comp, entities, n_sectors)) % template_count
        base_desc = _fill_template(
```

With:

```python
        # For T1 scenarios, use low-severity templates 50% of the time
        all_templates = BASE_TEMPLATES
        if assign_t_level(disruption, data_comp, cascading, entities) == "T1" and rng.random() < 0.5:
            all_templates = LOW_SEVERITY_TEMPLATES
        tmpl_idx = hash((disruption, cascading, data_comp, entities, n_sectors)) % len(all_templates)
        base_desc = _fill_template(
```

**c) Expand ENTITIES_RANGE weighting toward small values** — replace line 35:

```python
ENTITIES_RANGE = [1, 1, 2, 2, 3, 3, 5, 8, 10, 12, 25, 55, 150]
```

**d) Expand MS_AFFECTED_RANGE weighting toward 1** — replace line 40:

```python
MS_AFFECTED_RANGE = [1, 1, 1, 1, 1, 2, 3, 5, 8]
```

**e) Expand SECTORS_AFFECTED_RANGE weighting toward 1** — replace line 52:

```python
SECTORS_AFFECTED_RANGE = [1, 1, 1, 1, 2, 2, 3, 5]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest src/tests/test_generation_balance.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Verify exact counts**

Run:
```bash
poetry run python -c "
from training.scripts.generate_incidents import generate_t_samples, generate_o_samples
from collections import Counter
t_raw = generate_t_samples(2000, paraphrase_variants=3, seed=42)
o_raw = generate_o_samples(2000, paraphrase_variants=3, seed=42)
t_counts = Counter(s['label'] for s in t_raw)
o_counts = Counter(s['label'] for s in o_raw)
print('T:', dict(sorted(t_counts.items())))
print('O:', dict(sorted(o_counts.items())))
"
```

- [ ] **Step 6: Commit**

```bash
git add training/scripts/generate_incidents.py src/tests/test_generation_balance.py
git commit -m "feat(v2): expand T1/O1 generation rules for better low-severity coverage"
```

---

### Task 2: Create curated mixing script

**Files:**
- Create: `training/scripts/mix_curated.py`
- Test: `src/tests/test_mix_curated.py`

- [ ] **Step 1: Write failing tests**

Create `src/tests/test_mix_curated.py`:

```python
"""Tests for curated incident mixing into training data."""

import csv
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from mix_curated import convert_to_t_csv, convert_to_o_csv, mix_into_training


@pytest.fixture
def sample_incident():
    return {
        "id": "INC-001",
        "name": "Test",
        "date": "2024-01-01",
        "sources": ["https://example.com"],
        "description": "A ransomware attack disrupted hospital systems causing complete shutdown of IT services for days",
        "t_fields": {
            "service_disruption": "complete",
            "affected_entities": 25,
            "sectors_affected": 2,
            "cascading": "cross_sector",
            "data_compromise": "sensitive",
        },
        "o_fields": {
            "sectors_affected": "health, digital infrastructure",
            "entity_relevance": "high_relevance",
            "ms_affected": 4,
            "cross_border_pattern": "significant",
            "coordination_needs": "eu_active",
            "capacity_exceeded": True,
        },
        "expected_t": "T3",
        "expected_o": "O3",
        "rationale": {
            "t_rationale": "Complete disruption plus sensitive data",
            "o_rationale": "EU active coordination needed",
        },
    }


def test_convert_to_t_csv_format(sample_incident):
    rows = convert_to_t_csv(sample_incident, paraphrase_variants=0)
    assert len(rows) == 1
    row = rows[0]
    assert "[SEP]" in row["text"]
    assert "disruption: complete" in row["text"]
    assert "entities: 25" in row["text"]
    assert "data_compromise: sensitive" in row["text"]
    assert row["label"] == "T3"
    assert row["weight"] == 1.0


def test_convert_to_o_csv_format(sample_incident):
    rows = convert_to_o_csv(sample_incident, paraphrase_variants=0)
    assert len(rows) == 1
    row = rows[0]
    assert "[SEP]" in row["text"]
    assert "relevance: high_relevance" in row["text"]
    assert "ms_affected: 4" in row["text"]
    assert "capacity_exceeded: true" in row["text"]
    assert row["label"] == "O3"
    assert row["weight"] == 1.0


def test_paraphrase_variants(sample_incident):
    rows = convert_to_t_csv(sample_incident, paraphrase_variants=3)
    assert len(rows) == 4  # original + 3 variants
    # All should have same label and weight
    assert all(r["label"] == "T3" for r in rows)
    assert all(r["weight"] == 1.0 for r in rows)
    # Texts should differ (paraphrased)
    texts = [r["text"] for r in rows]
    assert len(set(texts)) > 1


def test_mix_into_training(sample_incident, tmp_path):
    # Create a synthetic CSV
    synth_path = tmp_path / "synthetic.csv"
    with open(synth_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerow({"text": "synthetic example [SEP] disruption: partial", "label": "T1"})

    output_path = tmp_path / "mixed.csv"
    mix_into_training(
        synthetic_csv=synth_path,
        curated_incidents=[sample_incident],
        output_csv=output_path,
        model_type="t",
        paraphrase_variants=0,
        synthetic_weight=0.8,
    )

    # Read output
    with open(output_path) as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 2  # 1 synthetic + 1 curated
    synth_row = [r for r in reader if "synthetic" in r["text"]][0]
    curated_row = [r for r in reader if "synthetic" not in r["text"]][0]
    assert float(synth_row["weight"]) == 0.8
    assert float(curated_row["weight"]) == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest src/tests/test_mix_curated.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mix_curated'`

- [ ] **Step 3: Write the implementation**

Create `training/scripts/mix_curated.py`:

```python
#!/usr/bin/env python3
"""Mix curated real-world incidents into synthetic training data.

Converts curated incidents from JSON to model-specific CSV format,
adds a weight column (curated=1.0, synthetic=0.8), and outputs
augmented training CSVs.

Usage:
    poetry run python training/scripts/mix_curated.py \
        --curated data/reference/curated_incidents.json \
        --synthetic-t training/data/technical_training.csv \
        --synthetic-o training/data/operational_training.csv \
        --output-t training/data/technical_training_v2.csv \
        --output-o training/data/operational_training_v2.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from generate_incidents import _paraphrase

print = partial(print, flush=True)


def convert_to_t_csv(
    incident: dict,
    paraphrase_variants: int = 3,
    seed: int = 42,
) -> list[dict]:
    """Convert a curated incident to T-model CSV rows."""
    tf = incident["t_fields"]
    desc = incident["description"]
    label = incident["expected_t"]

    base_text = (
        f"{desc} [SEP] "
        f"disruption: {tf['service_disruption']} "
        f"entities: {tf['affected_entities']} "
        f"sectors: {tf['sectors_affected']} "
        f"cascading: {tf['cascading']} "
        f"data_compromise: {tf['data_compromise']}"
    )

    rows = [{"text": base_text, "label": label, "weight": 1.0}]

    rng = random.Random(seed + hash(incident["id"]))
    for v in range(1, paraphrase_variants + 1):
        para_desc = _paraphrase(desc, v, rng)
        para_text = (
            f"{para_desc} [SEP] "
            f"disruption: {tf['service_disruption']} "
            f"entities: {tf['affected_entities']} "
            f"sectors: {tf['sectors_affected']} "
            f"cascading: {tf['cascading']} "
            f"data_compromise: {tf['data_compromise']}"
        )
        rows.append({"text": para_text, "label": label, "weight": 1.0})

    return rows


def convert_to_o_csv(
    incident: dict,
    paraphrase_variants: int = 3,
    seed: int = 42,
) -> list[dict]:
    """Convert a curated incident to O-model CSV rows."""
    of = incident["o_fields"]
    desc = incident["description"]
    label = incident["expected_o"]

    base_text = (
        f"{desc} [SEP] "
        f"sectors: {of['sectors_affected']} "
        f"relevance: {of['entity_relevance']} "
        f"ms_affected: {of['ms_affected']} "
        f"cross_border: {of['cross_border_pattern']} "
        f"coordination: {of['coordination_needs']} "
        f"capacity_exceeded: {str(of['capacity_exceeded']).lower()}"
    )

    rows = [{"text": base_text, "label": label, "weight": 1.0}]

    rng = random.Random(seed + hash(incident["id"]))
    for v in range(1, paraphrase_variants + 1):
        para_desc = _paraphrase(desc, v, rng)
        para_text = (
            f"{para_desc} [SEP] "
            f"sectors: {of['sectors_affected']} "
            f"relevance: {of['entity_relevance']} "
            f"ms_affected: {of['ms_affected']} "
            f"cross_border: {of['cross_border_pattern']} "
            f"coordination: {of['coordination_needs']} "
            f"capacity_exceeded: {str(of['capacity_exceeded']).lower()}"
        )
        rows.append({"text": para_text, "label": label, "weight": 1.0})

    return rows


def mix_into_training(
    synthetic_csv: Path,
    curated_incidents: list[dict],
    output_csv: Path,
    model_type: str,
    paraphrase_variants: int = 3,
    synthetic_weight: float = 0.8,
) -> int:
    """Mix curated incidents into synthetic training CSV with weight column.

    Returns total row count.
    """
    converter = convert_to_t_csv if model_type == "t" else convert_to_o_csv

    rows: list[dict] = []

    # Read synthetic data, add weight
    with open(synthetic_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["weight"] = synthetic_weight
            rows.append(row)

    # Convert and add curated incidents
    for inc in curated_incidents:
        rows.extend(converter(inc, paraphrase_variants=paraphrase_variants))

    # Write output
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "weight"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mix curated incidents into training data")
    parser.add_argument("--curated", type=Path, default=Path("data/reference/curated_incidents.json"))
    parser.add_argument("--synthetic-t", type=Path, default=Path("training/data/technical_training.csv"))
    parser.add_argument("--synthetic-o", type=Path, default=Path("training/data/operational_training.csv"))
    parser.add_argument("--output-t", type=Path, default=Path("training/data/technical_training_v2.csv"))
    parser.add_argument("--output-o", type=Path, default=Path("training/data/operational_training_v2.csv"))
    parser.add_argument("--paraphrase-variants", type=int, default=3)
    parser.add_argument("--synthetic-weight", type=float, default=0.8)
    args = parser.parse_args()

    # Load curated incidents
    data = json.loads(args.curated.read_text(encoding="utf-8"))
    incidents = data["incidents"]
    print(f"Loaded {len(incidents)} curated incidents")

    # Mix T-model data
    t_count = mix_into_training(
        synthetic_csv=args.synthetic_t,
        curated_incidents=incidents,
        output_csv=args.output_t,
        model_type="t",
        paraphrase_variants=args.paraphrase_variants,
        synthetic_weight=args.synthetic_weight,
    )
    print(f"T-model: {t_count} rows written to {args.output_t}")

    # Mix O-model data
    o_count = mix_into_training(
        synthetic_csv=args.synthetic_o,
        curated_incidents=incidents,
        output_csv=args.output_o,
        model_type="o",
        paraphrase_variants=args.paraphrase_variants,
        synthetic_weight=args.synthetic_weight,
    )
    print(f"O-model: {o_count} rows written to {args.output_o}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest src/tests/test_mix_curated.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add training/scripts/mix_curated.py src/tests/test_mix_curated.py
git commit -m "feat(v2): add curated incident mixing script with weight column"
```

---

### Task 3: Add per-sample weight support to training scripts

**Files:**
- Modify: `training/scripts/train_technical.py:48-79,123-134,209,267-278`
- Modify: `training/scripts/train_operational.py:48-79,123-134,209,267-278`
- Test: `src/tests/test_weighted_loss.py`

Both training scripts need identical changes. The CVEDataset class must return a weight per sample, and the training loop must apply it.

- [ ] **Step 1: Write failing tests**

Create `src/tests/test_weighted_loss.py`:

```python
"""Tests for per-sample weight support in training scripts."""

import csv
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from train_technical import CVEDataset as TCVEDataset
from train_operational import CVEDataset as OCVEDataset


@pytest.fixture
def sample_tokenizer():
    """Load the base tokenizer (lightweight, no GPU needed)."""
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")


def test_t_dataset_returns_weight_when_present(sample_tokenizer):
    texts = ["test text [SEP] disruption: partial entities: 1 sectors: 1 cascading: none data_compromise: none"]
    labels = [0]
    weights = [0.8]
    ds = TCVEDataset(texts, labels, sample_tokenizer, weights=weights)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(0.8)


def test_t_dataset_defaults_weight_to_1(sample_tokenizer):
    texts = ["test text [SEP] disruption: partial entities: 1 sectors: 1 cascading: none data_compromise: none"]
    labels = [0]
    ds = TCVEDataset(texts, labels, sample_tokenizer)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(1.0)


def test_o_dataset_returns_weight_when_present(sample_tokenizer):
    texts = ["test text [SEP] sectors: health relevance: essential ms_affected: 1 cross_border: none coordination: national capacity_exceeded: false"]
    labels = [0]
    weights = [0.8]
    ds = OCVEDataset(texts, labels, sample_tokenizer, weights=weights)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(0.8)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run pytest src/tests/test_weighted_loss.py -v`
Expected: FAIL — `TypeError: CVEDataset.__init__() got an unexpected keyword argument 'weights'`

- [ ] **Step 3: Modify train_technical.py**

In `training/scripts/train_technical.py`, modify the `CVEDataset` class:

Replace the `__init__` method (lines ~51-58):
```python
    def __init__(
        self,
        texts: list[str],
        labels: list[int],
        tokenizer: AutoTokenizer,
        max_length: int = 256,
        weights: list[float] | None = None,
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.weights = weights or [1.0] * len(texts)
```

Replace the `__getitem__` method (lines ~65-78):
```python
    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
            "weight": torch.tensor(self.weights[idx], dtype=torch.float32),
        }
```

In the `train()` function, after loading the CSV (around line 123), add weight column detection:

After `labels = df["label"]...` block (~line 143), add:
```python
    # Per-sample weights (optional column)
    if "weight" in df.columns:
        weights = df["weight"].astype(float).tolist()
        print(f"Per-sample weights detected: min={min(weights):.2f}, max={max(weights):.2f}")
    else:
        weights = [1.0] * len(texts)
```

Update the `make_dataset` helper (~line 174) to pass weights:
```python
    def make_dataset(idxs: list[int]) -> CVEDataset:
        return CVEDataset(
            texts=[texts[i] for i in idxs],
            labels=[labels[i] for i in idxs],
            tokenizer=tokenizer,
            max_length=max_length,
            weights=[weights[i] for i in idxs],
        )
```

Change the loss computation in the training loop. Replace line 209:
```python
    loss_fn = torch.nn.CrossEntropyLoss(weight=weight_tensor, label_smoothing=label_smoothing, reduction="none")
```

Replace the loss backward block (~lines 277-278):
```python
            raw_loss = loss_fn(outputs.logits, batch_labels)
            sample_weights = batch["weight"].to(device)
            loss = (raw_loss * sample_weights).mean()
            loss.backward()
```

And the validation loss (~lines 308):
```python
                raw_loss = loss_fn(outputs.logits, batch_labels)
                sample_weights = batch["weight"].to(device)
                loss = (raw_loss * sample_weights).mean()
```

- [ ] **Step 4: Apply identical changes to train_operational.py**

Make the exact same changes to `training/scripts/train_operational.py`:
- Same `CVEDataset.__init__` with `weights` parameter
- Same `__getitem__` returning `weight` tensor
- Same weight column detection after CSV loading
- Same `make_dataset` passing weights
- Same `reduction="none"` + manual weighting in training and validation loops

- [ ] **Step 5: Run tests to verify they pass**

Run: `poetry run pytest src/tests/test_weighted_loss.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add training/scripts/train_technical.py training/scripts/train_operational.py src/tests/test_weighted_loss.py
git commit -m "feat(v2): add per-sample confidence-weighted loss to training scripts"
```

---

### Task 4: Regenerate data, mix curated, retrain both models

**Files:**
- Output: `training/data/technical_training.csv` (regenerated)
- Output: `training/data/operational_training.csv` (regenerated)
- Output: `training/data/technical_training_v2.csv` (mixed)
- Output: `training/data/operational_training_v2.csv` (mixed)
- Output: `data/models/technical/` (retrained)
- Output: `data/models/operational/` (retrained)

This task requires GPU. Run commands in foreground with timeout management.

- [ ] **Step 1: Regenerate synthetic training data with expanded rules**

Run:
```bash
poetry run python training/scripts/generate_incidents.py \
    --output-t training/data/technical_training.csv \
    --output-o training/data/operational_training.csv
```

Verify T1 and O1 raw counts improved in the output.

- [ ] **Step 2: Mix curated incidents into training data**

Run:
```bash
poetry run python training/scripts/mix_curated.py \
    --curated data/reference/curated_incidents.json \
    --synthetic-t training/data/technical_training.csv \
    --synthetic-o training/data/operational_training.csv \
    --output-t training/data/technical_training_v2.csv \
    --output-o training/data/operational_training_v2.csv \
    --paraphrase-variants 3 \
    --synthetic-weight 0.8
```

- [ ] **Step 3: Retrain T-model**

Run:
```bash
poetry run python training/scripts/train_technical.py \
    --data training/data/technical_training_v2.csv \
    --config training/configs/technical_cls.json \
    --output data/models/technical
```

Expected: Training completes with early stopping. Check that test accuracy and macro F1 are printed.

- [ ] **Step 4: Retrain O-model**

Run:
```bash
poetry run python training/scripts/train_operational.py \
    --data training/data/operational_training_v2.csv \
    --config training/configs/operational_cls.json \
    --output data/models/operational
```

- [ ] **Step 5: Commit training data (not models — they're gitignored)**

```bash
git add training/data/technical_training_v2.csv training/data/operational_training_v2.csv
git commit -m "feat(v2): regenerate training data with expanded T1/O1 and curated mixing"
```

Note: the v2 CSVs may be large. If gitignored, skip this commit.

---

### Task 5: Re-run curated benchmark and compare

**Files:**
- Output: `evaluation/curated_benchmark.md` (updated)

- [ ] **Step 1: Run curated benchmark**

Run:
```bash
poetry run python evaluation/benchmark_curated.py \
    --t-model data/models/technical \
    --o-model data/models/operational \
    --dataset data/reference/curated_incidents.json \
    --output evaluation/curated_benchmark.md \
    --mc-passes 5
```

- [ ] **Step 2: Check results against success criteria**

Verify:
- T1 F1 > 0.50 (was 0.00)
- O1 F1 > 0.50 (was 0.095)
- O-model accuracy > 65% (was 40%)
- Matrix end-to-end > 75% (was 67.5%)
- T3/T4 F1 did not regress below 0.90
- O3/O4 F1 did not regress below 0.70

- [ ] **Step 3: Run synthetic benchmark to check for regression**

Run:
```bash
poetry run python evaluation/benchmark_incidents.py \
    --t-model data/models/technical \
    --o-model data/models/operational \
    --output evaluation/incident_benchmark.md \
    --mc-passes 5
```

Verify synthetic benchmark still passes (T macro F1 > 75%, O macro F1 > 75%, Matrix > 70%).

- [ ] **Step 4: Commit results**

```bash
git add evaluation/curated_benchmark.md evaluation/incident_benchmark.md
git commit -m "docs(v2): update benchmark results after low-severity calibration"
```
