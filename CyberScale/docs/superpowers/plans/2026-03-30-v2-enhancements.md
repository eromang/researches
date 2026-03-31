# v2 Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deployment scale + entity type features to Phase 2 (addresses non_nis2 65.3% weakness), promote CWE to a first-class Phase 1 feature (addresses 60.5% accuracy), and wire the composable Phase 1 → 2 → 3 pipeline.

**Architecture:** Three low-effort enhancements to the existing CyberScale pipeline. (1) Phase 2's `ContextualClassifier` gains two new input fields (`deployment_scale`, `entity_type`) appended to its text format; the generation script produces scenarios with these fields; existing training infrastructure handles the rest. (2) Phase 1's scorer already accepts CWE as optional input but training data rarely includes it — we make the training script load CWE from the NVD bulk CSV and always include it in the input format so the model learns CWE-specific severity patterns. (3) A new `pipeline.py` module wires Phase 1 → Phase 2 → Phase 3 with a single `assess_full` entry point that chains scorer output into contextual input, and contextual context into incident classification.

**Tech Stack:** Python 3.12, pytest, existing ModernBERT classifiers, existing training scripts, FastMCP tool registration.

---

### Task 1: Add `deployment_scale` and `entity_type` to Phase 2 model input format

**Files:**
- Modify: `src/cyberscale/models/contextual.py`
- Test: `src/tests/models/test_contextual.py`

The `ContextualClassifier._format_input()` method currently builds:
```
{description} [SEP] sector: {sector} cross_border: {cross_border_str} [score: {score}]
```

We add two new optional fields so the model can learn deployment-context patterns.

- [ ] **Step 1: Write failing tests for new input fields**

Add to `src/tests/models/test_contextual.py`:

```python
class TestFormatInputV2:
    def test_with_deployment_scale(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=True,
            score=8.5, deployment_scale="enterprise",
        )
        assert "deployment_scale: enterprise" in text

    def test_with_entity_type(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=True,
            score=8.5, entity_type="hospital",
        )
        assert "entity_type: hospital" in text

    def test_with_both_new_fields(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=False,
            score=7.0, deployment_scale="critical_operator", entity_type="hospital",
        )
        assert "deployment_scale: critical_operator" in text
        assert "entity_type: hospital" in text

    def test_without_new_fields_unchanged(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="energy", cross_border=False, score=None,
        )
        assert "deployment_scale:" not in text
        assert "entity_type:" not in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/models/test_contextual.py::TestFormatInputV2 -v`
Expected: FAIL — `_format_input()` does not accept `deployment_scale` or `entity_type` kwargs.

- [ ] **Step 3: Add `deployment_scale` and `entity_type` to `_format_input`**

In `src/cyberscale/models/contextual.py`, update the `_format_input` method signature and body:

```python
def _format_input(
    self,
    description: str,
    sector: str,
    cross_border: bool,
    score: Optional[float] = None,
    deployment_scale: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> str:
    """Format input text for the model.

    Raises ValueError if sector is not in VALID_SECTORS.
    """
    if sector not in VALID_SECTORS:
        raise ValueError(f"Unknown sector: {sector}")

    cross_border_str = "true" if cross_border else "false"
    parts = [
        description,
        f"[SEP] sector: {sector}",
        f"cross_border: {cross_border_str}",
    ]
    if score is not None:
        parts.append(f"score: {score}")
    if deployment_scale is not None:
        parts.append(f"deployment_scale: {deployment_scale}")
    if entity_type is not None:
        parts.append(f"entity_type: {entity_type}")
    return " ".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/models/test_contextual.py -v`
Expected: All PASS (including existing tests — backward compatible since new params default to None).

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/models/contextual.py src/tests/models/test_contextual.py
git commit -m "feat(v2): add deployment_scale and entity_type to Phase 2 input format"
```

---

### Task 2: Wire `deployment_scale` and `entity_type` through `predict()` and `_extract_key_factors()`

**Files:**
- Modify: `src/cyberscale/models/contextual.py`
- Test: `src/tests/models/test_contextual.py`

The `predict()` method and key factor extraction need the new fields.

- [ ] **Step 1: Write failing tests for predict signature and key factors**

Add to `src/tests/models/test_contextual.py`:

```python
class TestKeyFactorsV2:
    def test_deployment_scale_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, deployment_scale="critical_operator")
        assert "critical_operator deployment" in factors

    def test_entity_type_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, entity_type="hospital")
        assert "hospital entity" in factors

    def test_small_deployment_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("non_nis2", False, 5.0, deployment_scale="individual")
        assert "individual deployment" in factors

    def test_no_new_factors_when_none(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0)
        assert not any("deployment" in f for f in factors)
        assert not any("entity" in f for f in factors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/models/test_contextual.py::TestKeyFactorsV2 -v`
Expected: FAIL — `_extract_key_factors()` does not accept `deployment_scale` or `entity_type`.

- [ ] **Step 3: Update `predict()` and `_extract_key_factors()`**

In `src/cyberscale/models/contextual.py`:

Update `predict()` signature:
```python
def predict(
    self,
    description: str,
    sector: str,
    cross_border: bool,
    score: Optional[float] = None,
    deployment_scale: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> ContextualResult:
    """Classify contextual severity with MC dropout confidence."""
    text = self._format_input(
        description, sector, cross_border, score=score,
        deployment_scale=deployment_scale, entity_type=entity_type,
    )
    inputs = self.tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=self.max_length,
        padding="max_length",
    )
    inputs = {k: v.to(self.device) for k, v in inputs.items()}

    # MC dropout: average softmax probabilities across N passes
    self._enable_dropout()
    all_probs: list[list[float]] = []
    with torch.no_grad():
        for _ in range(self.mc_passes):
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().tolist()
            all_probs.append(probs)
    self.model.eval()

    # Average probabilities across MC passes
    mean_probs = [
        sum(p[i] for p in all_probs) / len(all_probs) for i in range(4)
    ]

    severity = self.probs_to_severity(mean_probs)
    confidence = self.max_prob_to_confidence(max(mean_probs))
    key_factors = self._extract_key_factors(
        sector, cross_border, score,
        deployment_scale=deployment_scale, entity_type=entity_type,
    )

    return ContextualResult(
        severity=severity, confidence=confidence, key_factors=key_factors
    )
```

Update `_extract_key_factors()`:
```python
def _extract_key_factors(
    self,
    sector: str,
    cross_border: bool,
    score: Optional[float],
    deployment_scale: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> list[str]:
    """Extract key contextual factors for explainability."""
    factors = [f"{sector} sector"]
    if cross_border:
        factors.append("cross-border exposure")
    if score is not None and score >= 9.0:
        factors.append("critical base score")
    if deployment_scale is not None:
        factors.append(f"{deployment_scale} deployment")
    if entity_type is not None:
        factors.append(f"{entity_type} entity")
    return factors
```

- [ ] **Step 4: Run all contextual tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/models/test_contextual.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/models/contextual.py src/tests/models/test_contextual.py
git commit -m "feat(v2): wire deployment_scale and entity_type through predict() and key_factors"
```

---

### Task 3: Update Phase 2 MCP tool and generation script for new fields

**Files:**
- Modify: `src/cyberscale/tools/contextual.py`
- Modify: `training/scripts/generate_contextual.py`
- Test: `src/tests/tools/test_contextual_tool.py`

- [ ] **Step 1: Write failing test for contextual tool with new fields**

Add to `src/tests/tools/test_contextual_tool.py`:

```python
class TestAssessWithModelV2:
    def test_passes_deployment_scale(self):
        mock_clf = type("MockClf", (), {
            "predict": lambda self, desc, sector, cb, score, deployment_scale=None, entity_type=None:
                type("R", (), {
                    "severity": "High", "confidence": "high",
                    "key_factors": [f"{deployment_scale} deployment"] if deployment_scale else [],
                })()
        })()
        result = _assess_with_model(
            mock_clf, "desc", "health", False,
            score=None, deployment_scale="enterprise",
        )
        assert result["deployment_scale"] == "enterprise"

    def test_passes_entity_type(self):
        mock_clf = type("MockClf", (), {
            "predict": lambda self, desc, sector, cb, score, deployment_scale=None, entity_type=None:
                type("R", (), {
                    "severity": "High", "confidence": "high",
                    "key_factors": [f"{entity_type} entity"] if entity_type else [],
                })()
        })()
        result = _assess_with_model(
            mock_clf, "desc", "health", False,
            score=None, entity_type="hospital",
        )
        assert result["entity_type"] == "hospital"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/tools/test_contextual_tool.py::TestAssessWithModelV2 -v`
Expected: FAIL — `_assess_with_model()` does not accept `deployment_scale`/`entity_type`.

- [ ] **Step 3: Update `_assess_with_model` and MCP tool registration**

In `src/cyberscale/tools/contextual.py`:

Update `_assess_with_model`:
```python
def _assess_with_model(
    clf,
    description: str,
    sector: str,
    cross_border: bool,
    score: float | None = None,
    deployment_scale: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Assess contextual severity using the classifier model."""
    result = clf.predict(
        description, sector, cross_border, score,
        deployment_scale=deployment_scale, entity_type=entity_type,
    )
    out = {
        "severity": result.severity,
        "confidence": result.confidence,
        "key_factors": result.key_factors,
        "sector": sector,
        "cross_border": cross_border,
    }
    if deployment_scale is not None:
        out["deployment_scale"] = deployment_scale
    if entity_type is not None:
        out["entity_type"] = entity_type
    return out
```

Update `assess_contextual_severity` tool signature:
```python
@mcp.tool(annotations={"readOnlyHint": True})
def assess_contextual_severity(
    description: str,
    sector: str,
    cross_border: bool,
    severity_score: float | None = None,
    deployment_scale: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Assess context-dependent severity for a vulnerability given NIS2 sector, cross-border exposure, and deployment context."""
    ok, err = _validate_sector(sector)
    if not ok:
        return {"error": err}
    clf = _get_classifier()
    if clf is None:
        return {"error": "No trained model available. Deploy a model to data/models/contextual/."}
    return _assess_with_model(
        clf, description, sector, cross_border,
        score=severity_score, deployment_scale=deployment_scale,
        entity_type=entity_type,
    )
```

- [ ] **Step 4: Update generation script to include new fields in input_text**

In `training/scripts/generate_contextual.py`, update the scenario generation to include `deployment_scale` and `entity_type` in the input text format. Add constants:

```python
DEPLOYMENT_SCALES = ["individual", "small_business", "enterprise", "critical_operator"]
ENTITY_TYPES = ["individual", "sme", "msp", "hospital", "cloud_provider", "utility", "government", "bank"]
```

In `generate_scenarios()`, after the cross-border/trigger logic, add random deployment context selection per scenario. Update the `input_text` format string at line ~234:

```python
# Pick deployment context
deployment_scale = rng.choice(DEPLOYMENT_SCALES)
entity_type = rng.choice(ENTITY_TYPES)

# Format input text
input_text = (
    f"{desc} [SEP] sector: {sector_id} "
    f"cross_border: {str(cross_border).lower()} "
    f"score: {score} "
    f"deployment_scale: {deployment_scale} "
    f"entity_type: {entity_type}"
)
```

Add `deployment_scale` and `entity_type` to the row dict and to `fieldnames`.

- [ ] **Step 5: Run all contextual tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/tools/test_contextual_tool.py src/tests/models/test_contextual.py -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add src/cyberscale/tools/contextual.py training/scripts/generate_contextual.py src/tests/tools/test_contextual_tool.py
git commit -m "feat(v2): wire deployment_scale and entity_type through MCP tool and generation script"
```

---

### Task 4: CWE as first-class Phase 1 feature — ensure training data always includes CWE

**Files:**
- Modify: `training/scripts/fetch_bulk_cves.py`
- Test: `src/tests/test_cwe_enrichment.py` (new)

The Phase 1 model already handles `cwe` in `_format_input` and the `CVEDataset` tokenizer. The gap is that training data CSV often has empty CWE columns because the bulk fetch script doesn't always extract CWE. We ensure CWE is reliably extracted and included.

- [ ] **Step 1: Write test for CWE extraction in bulk fetch**

Create `src/tests/test_cwe_enrichment.py`:

```python
"""Tests for CWE enrichment in Phase 1 training data."""

from __future__ import annotations

import pytest


class TestCweExtraction:
    """Verify that CWE IDs are extracted from cvelistV5 format."""

    def test_extract_cwe_from_problem_types(self):
        """cvelistV5 stores CWE in cna.problemTypes[].descriptions[].cweId."""
        from training.scripts.fetch_bulk_cves import extract_cwe

        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-79", "lang": "en"}
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) == "CWE-79"

    def test_extract_cwe_skips_noinfo(self):
        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-noinfo", "lang": "en"}
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) is None

    def test_extract_cwe_missing_field(self):
        record = {"containers": {"cna": {}}}
        assert extract_cwe(record) is None

    def test_extract_cwe_multiple_picks_first_valid(self):
        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-Other", "lang": "en"},
                                {"type": "CWE", "cweId": "CWE-787", "lang": "en"},
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) == "CWE-787"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/test_cwe_enrichment.py -v`
Expected: FAIL — `extract_cwe` function does not exist.

- [ ] **Step 3: Add `extract_cwe()` function to `fetch_bulk_cves.py`**

In `training/scripts/fetch_bulk_cves.py`, add:

```python
INVALID_CWES = {"CWE-noinfo", "CWE-Other"}


def extract_cwe(record: dict) -> str | None:
    """Extract first valid CWE ID from a cvelistV5 record.

    Looks in containers.cna.problemTypes[].descriptions[].cweId,
    skipping CWE-noinfo and CWE-Other.
    """
    try:
        problem_types = record["containers"]["cna"]["problemTypes"]
    except (KeyError, TypeError):
        return None

    for pt in problem_types:
        for desc in pt.get("descriptions", []):
            cwe_id = desc.get("cweId", "")
            if cwe_id and cwe_id not in INVALID_CWES:
                return cwe_id
    return None
```

Then update the main CSV writing loop to call `extract_cwe(record)` and include a `cwe` column in the output CSV.

- [ ] **Step 4: Run tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/test_cwe_enrichment.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add training/scripts/fetch_bulk_cves.py src/tests/test_cwe_enrichment.py
git commit -m "feat(v2): extract CWE from cvelistV5 records for Phase 1 training data"
```

---

### Task 5: Verify Phase 1 training script uses CWE when available

**Files:**
- Modify: `training/scripts/train_scorer.py` (verify, may need no change)
- Test: `src/tests/test_cwe_enrichment.py`

The training script at `train_scorer.py:157` already loads CWE:
```python
cwes = df["cwe"].tolist() if "cwe" in df.columns else [None] * len(df)
```

And the `CVEDataset.__getitem__` at line 87 already enriches:
```python
if cwe and str(cwe).strip() and str(cwe).lower() not in ("nan", "none", ""):
    text = f"{desc} [SEP] cwe: {cwe}"
```

No model or training code changes needed — Task 4's data change is sufficient. We just verify with a test.

- [ ] **Step 1: Write a test that verifies CVEDataset uses CWE**

Add to `src/tests/test_cwe_enrichment.py`:

```python
class TestCVEDatasetCWE:
    """Verify that the training dataset includes CWE in tokenized text."""

    def test_cwe_included_in_text(self):
        from transformers import AutoTokenizer
        from training.scripts.train_scorer import CVEDataset

        tokenizer = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
        ds = CVEDataset(
            descriptions=["Buffer overflow in libfoo"],
            cwes=["CWE-119"],
            labels=[2],
            tokenizer=tokenizer,
            max_length=64,
        )
        item = ds[0]
        decoded = tokenizer.decode(item["input_ids"], skip_special_tokens=True)
        assert "cwe: CWE-119" in decoded

    def test_cwe_none_omitted(self):
        from transformers import AutoTokenizer
        from training.scripts.train_scorer import CVEDataset

        tokenizer = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
        ds = CVEDataset(
            descriptions=["Buffer overflow in libfoo"],
            cwes=[None],
            labels=[2],
            tokenizer=tokenizer,
            max_length=64,
        )
        item = ds[0]
        decoded = tokenizer.decode(item["input_ids"], skip_special_tokens=True)
        assert "cwe:" not in decoded
```

- [ ] **Step 2: Run the test**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/test_cwe_enrichment.py::TestCVEDatasetCWE -v`
Expected: All PASS (existing code already handles this).

- [ ] **Step 3: Commit**

```bash
git add src/tests/test_cwe_enrichment.py
git commit -m "test(v2): verify Phase 1 training dataset includes CWE enrichment"
```

---

### Task 6: Composable pipeline — Phase 1 → Phase 2 → Phase 3 wiring

**Files:**
- Create: `src/cyberscale/pipeline.py`
- Test: `src/tests/test_pipeline.py` (new)

A single module that chains the three phases. Phase 1 scorer output (score + band + confidence) feeds Phase 2 as the `score` parameter. Phase 2 severity feeds Phase 3 as additional context in the description.

- [ ] **Step 1: Write failing tests for the pipeline**

Create `src/tests/test_pipeline.py`:

```python
"""Tests for the composable Phase 1 → 2 → 3 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from cyberscale.pipeline import PipelineResult, run_pipeline


@dataclass
class FakeScorer:
    """Stub Phase 1 scorer."""
    def predict(self, description: str, cwe: Optional[str] = None):
        @dataclass
        class R:
            score: float = 7.5
            confidence: str = "high"
            band: str = "High"
            def to_dict(self):
                return {"score": self.score, "confidence": self.confidence, "band": self.band}
        return R()


@dataclass
class FakeContextual:
    """Stub Phase 2 classifier."""
    def predict(self, description, sector, cross_border, score=None, **kwargs):
        @dataclass
        class R:
            severity: str = "High"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or ["health sector"]
            def to_dict(self):
                return {"severity": self.severity, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


@dataclass
class FakeTechnical:
    """Stub Phase 3 T-model."""
    def predict(self, description, **kwargs):
        @dataclass
        class R:
            level: str = "T3"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or []
            def to_dict(self):
                return {"level": self.level, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


@dataclass
class FakeOperational:
    """Stub Phase 3 O-model."""
    def predict(self, description, **kwargs):
        @dataclass
        class R:
            level: str = "O3"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or []
            def to_dict(self):
                return {"level": self.level, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


class TestRunPipeline:
    def test_full_pipeline_returns_all_phases(self):
        result = run_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            technical=FakeTechnical(),
            operational=FakeOperational(),
            description="Critical RCE in hospital system",
            sector="health",
            cross_border=True,
            # Phase 3 fields
            service_disruption="complete",
            affected_entities=50,
            sectors_affected="health,digital_infrastructure",
            cascading="cross_sector",
            data_compromise="sensitive",
            entity_relevance="high_relevance",
            ms_affected=3,
            cross_border_pattern="significant",
            coordination_needs="eu_active",
            capacity_exceeded=False,
        )
        assert result.phase1_score == 7.5
        assert result.phase1_band == "High"
        assert result.phase2_severity == "High"
        assert result.phase3_t_level == "T3"
        assert result.phase3_o_level == "O3"
        assert result.classification in (
            "below_threshold", "significant", "large_scale", "cyber_crisis"
        )

    def test_pipeline_without_phase3(self):
        result = run_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            description="SQL injection in banking portal",
            sector="banking",
            cross_border=False,
        )
        assert result.phase1_score == 7.5
        assert result.phase2_severity == "High"
        assert result.phase3_t_level is None
        assert result.phase3_o_level is None
        assert result.classification is None

    def test_pipeline_passes_cwe_to_scorer(self):
        calls = []
        class TrackingScorer:
            def predict(self, description, cwe=None):
                calls.append(cwe)
                @dataclass
                class R:
                    score: float = 5.0
                    confidence: str = "medium"
                    band: str = "Medium"
                return R()

        run_pipeline(
            scorer=TrackingScorer(),
            contextual=FakeContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
            cwe="CWE-119",
        )
        assert calls == ["CWE-119"]

    def test_pipeline_passes_score_to_contextual(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(score)
                @dataclass
                class R:
                    severity: str = "Medium"
                    confidence: str = "medium"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),  # returns score=7.5
            contextual=TrackingContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
        )
        assert calls == [7.5]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/test_pipeline.py -v`
Expected: FAIL — `cyberscale.pipeline` module does not exist.

- [ ] **Step 3: Implement `pipeline.py`**

Create `src/cyberscale/pipeline.py`:

```python
"""Composable Phase 1 → Phase 2 → Phase 3 pipeline.

Chains the three CyberScale phases:
  Phase 1 (scorer): vulnerability description + CWE → score, band, confidence
  Phase 2 (contextual): description + sector + cross_border + Phase 1 score → contextual severity
  Phase 3 (incident): T-model + O-model → Blueprint matrix classification
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineResult:
    """Combined result from all pipeline phases."""

    # Phase 1
    phase1_score: float
    phase1_band: str
    phase1_confidence: str

    # Phase 2
    phase2_severity: str
    phase2_confidence: str
    phase2_key_factors: list[str]

    # Phase 3 (optional — only when incident fields provided)
    phase3_t_level: Optional[str] = None
    phase3_o_level: Optional[str] = None
    classification: Optional[str] = None
    label: Optional[str] = None
    provision: Optional[str] = None


def run_pipeline(
    scorer,
    contextual,
    description: str,
    sector: str,
    cross_border: bool,
    cwe: Optional[str] = None,
    deployment_scale: Optional[str] = None,
    entity_type: Optional[str] = None,
    # Phase 3 fields (all optional — omit to skip Phase 3)
    technical=None,
    operational=None,
    service_disruption: Optional[str] = None,
    affected_entities: Optional[int] = None,
    sectors_affected: Optional[str] = None,
    cascading: Optional[str] = None,
    data_compromise: Optional[str] = None,
    entity_relevance: Optional[str] = None,
    ms_affected: Optional[int] = None,
    cross_border_pattern: Optional[str] = None,
    coordination_needs: Optional[str] = None,
    capacity_exceeded: Optional[bool] = None,
) -> PipelineResult:
    """Run the composable assessment pipeline.

    Phase 1 score is automatically fed into Phase 2 as context.
    Phase 3 runs only when technical/operational classifiers and
    incident fields are provided.
    """
    # --- Phase 1: Vulnerability scoring ---
    p1 = scorer.predict(description, cwe=cwe)

    # --- Phase 2: Contextual severity (receives Phase 1 score) ---
    p2 = contextual.predict(
        description, sector, cross_border,
        score=p1.score,
        deployment_scale=deployment_scale,
        entity_type=entity_type,
    )

    # --- Phase 3: Incident classification (optional) ---
    has_phase3 = (
        technical is not None
        and operational is not None
        and service_disruption is not None
    )

    if has_phase3:
        n_sectors = len([s for s in sectors_affected.split(",") if s.strip()])
        t_result = technical.predict(
            description,
            service_disruption=service_disruption,
            affected_entities=affected_entities,
            sectors_affected=n_sectors,
            cascading=cascading,
            data_compromise=data_compromise,
        )
        o_result = operational.predict(
            description,
            sectors_affected=sectors_affected,
            entity_relevance=entity_relevance,
            ms_affected=ms_affected,
            cross_border_pattern=cross_border_pattern,
            coordination_needs=coordination_needs,
            capacity_exceeded=capacity_exceeded,
        )

        from cyberscale.matrix.dual_scale import classify_incident
        matrix = classify_incident(t_result.level, o_result.level)

        return PipelineResult(
            phase1_score=p1.score,
            phase1_band=p1.band,
            phase1_confidence=p1.confidence,
            phase2_severity=p2.severity,
            phase2_confidence=p2.confidence,
            phase2_key_factors=p2.key_factors,
            phase3_t_level=t_result.level,
            phase3_o_level=o_result.level,
            classification=matrix.classification,
            label=matrix.label,
            provision=matrix.provision,
        )

    return PipelineResult(
        phase1_score=p1.score,
        phase1_band=p1.band,
        phase1_confidence=p1.confidence,
        phase2_severity=p2.severity,
        phase2_confidence=p2.confidence,
        phase2_key_factors=p2.key_factors,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/test_pipeline.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/pipeline.py src/tests/test_pipeline.py
git commit -m "feat(v2): composable Phase 1 → 2 → 3 pipeline with automatic score forwarding"
```

---

### Task 7: Pipeline MCP tool — `assess_full_pipeline` endpoint

**Files:**
- Modify: `src/cyberscale/tools/vulnerability.py`
- Test: `src/tests/tools/test_vulnerability_scoring.py`

Expose the pipeline as a single MCP tool that chains all three phases.

- [ ] **Step 1: Write failing test for the pipeline tool**

Add to `src/tests/tools/test_vulnerability_scoring.py`:

```python
class TestPipelineTool:
    def test_pipeline_tool_returns_all_phases(self):
        from cyberscale.tools.vulnerability import _assess_pipeline

        class FakeScorer:
            def predict(self, desc, cwe=None):
                from cyberscale.models.scorer import ScorerResult
                return ScorerResult(score=8.0, confidence="high", band="High")

        class FakeContextual:
            def predict(self, desc, sector, cb, score=None, **kw):
                from cyberscale.models.contextual import ContextualResult
                return ContextualResult(severity="High", confidence="high", key_factors=["health sector"])

        result = _assess_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            description="RCE in medical device",
            sector="health",
            cross_border=True,
        )
        assert result["phase1"]["score"] == 8.0
        assert result["phase2"]["severity"] == "High"
        assert "phase3" not in result  # no incident fields provided
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/tools/test_vulnerability_scoring.py::TestPipelineTool -v`
Expected: FAIL — `_assess_pipeline` does not exist.

- [ ] **Step 3: Add `_assess_pipeline` helper and MCP tool**

In `src/cyberscale/tools/vulnerability.py`, add after the existing lazy loaders:

```python
_contextual_instance = None
_contextual_model_path = Path("data/models/contextual")


def _get_contextual():
    global _contextual_instance
    if _contextual_instance is None:
        if not _contextual_model_path.exists():
            return None
        from cyberscale.models.contextual import ContextualClassifier
        _contextual_instance = ContextualClassifier(model_path=_contextual_model_path)
    return _contextual_instance


def _assess_pipeline(
    scorer,
    contextual,
    description: str,
    sector: str,
    cross_border: bool,
    cwe: str | None = None,
    deployment_scale: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Run Phase 1 → Phase 2 pipeline and return structured result."""
    from cyberscale.pipeline import run_pipeline

    result = run_pipeline(
        scorer=scorer,
        contextual=contextual,
        description=description,
        sector=sector,
        cross_border=cross_border,
        cwe=cwe,
        deployment_scale=deployment_scale,
        entity_type=entity_type,
    )
    return {
        "phase1": {
            "score": result.phase1_score,
            "band": result.phase1_band,
            "confidence": result.phase1_confidence,
        },
        "phase2": {
            "severity": result.phase2_severity,
            "confidence": result.phase2_confidence,
            "key_factors": result.phase2_key_factors,
        },
    }
```

Then in the `register()` function, add the new MCP tool:

```python
@mcp.tool(annotations={"readOnlyHint": True})
def assess_full_pipeline(
    description: str,
    sector: str,
    cross_border: bool,
    cve_id: str | None = None,
    deployment_scale: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Full pipeline: Phase 1 scoring → Phase 2 contextual severity. Automatically chains Phase 1 score into Phase 2."""
    scorer = _get_scorer()
    if scorer is None:
        return {"error": "No trained scorer model. Deploy to data/models/scorer/."}
    contextual = _get_contextual()
    if contextual is None:
        return {"error": "No trained contextual model. Deploy to data/models/contextual/."}

    cwe = None
    if cve_id:
        from cyberscale.api.lookup import UnifiedLookup
        lookup = UnifiedLookup()
        result = lookup.lookup_cve(cve_id)
        if result:
            cwe = result.get("cwe")

    return _assess_pipeline(
        scorer, contextual, description, sector, cross_border,
        cwe=cwe, deployment_scale=deployment_scale, entity_type=entity_type,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/tools/test_vulnerability_scoring.py -v`
Expected: All PASS.

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && poetry run pytest src/tests/ -v`
Expected: All PASS — no regressions.

- [ ] **Step 6: Commit**

```bash
git add src/cyberscale/tools/vulnerability.py src/cyberscale/pipeline.py src/tests/tools/test_vulnerability_scoring.py
git commit -m "feat(v2): add assess_full_pipeline MCP tool for composable Phase 1 → 2 assessment"
```
