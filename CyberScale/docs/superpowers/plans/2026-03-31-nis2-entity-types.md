# NIS2-Aligned Entity Types for Phase 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 8 generic entity types and 4 generic deployment scales with ~60 NIS2-specific entity types from Annex I and II. Entity type now encodes both identity and scale — `deployment_scale` is removed as redundant. Add `cer_critical_entity` boolean for CER Directive essential-override.

**Architecture:** A new reference JSON (`nis2_entity_types.json`) defines all entity types with sector mappings. The generation script draws entity types from this reference, constrained to the correct sector. The model/tools gain `cer_critical_entity` as an optional boolean that escalates Annex II entities to essential status. `deployment_scale` is removed from model input, tools, pipeline, and generation — the entity type implicitly encodes deployment scale (a `transmission_system_operator` is inherently critical-scale).

**Tech Stack:** Python, ModernBERT, PyTorch, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `data/reference/nis2_entity_types.json` | Create | Reference data: all NIS2 entity types with sector/annex/CER metadata |
| `training/scripts/generate_contextual.py` | Modify | Use new entity types, sector-constrained selection, `cer_critical_entity`, remove `deployment_scale` |
| `src/cyberscale/models/contextual.py` | Modify | Add `VALID_ENTITY_TYPES`, `cer_critical_entity`; remove `deployment_scale` from predict/format_input/key_factors |
| `src/cyberscale/tools/contextual.py` | Modify | Add `cer_critical_entity`; remove `deployment_scale` from MCP tool |
| `src/cyberscale/tools/vulnerability.py` | Modify | Add `cer_critical_entity`; remove `deployment_scale` from `assess_full_pipeline` + `_assess_pipeline` |
| `src/cyberscale/pipeline.py` | Modify | Add `cer_critical_entity`; remove `deployment_scale` passthrough |
| `src/tests/models/test_contextual.py` | Modify | Tests for new entity types, `cer_critical_entity`; remove `deployment_scale` tests |
| `src/tests/tools/test_contextual_tool.py` | Modify | Tests for MCP tool with `cer_critical_entity`; remove `deployment_scale` tests |
| `src/tests/tools/test_vulnerability_scoring.py` | Modify | Pipeline tool tests with `cer_critical_entity`; remove `deployment_scale` |
| `src/tests/test_pipeline.py` | Modify | Pipeline passthrough tests for `cer_critical_entity`; remove `deployment_scale` |

---

### Task 1: Create NIS2 Entity Types Reference JSON

**Files:**
- Create: `data/reference/nis2_entity_types.json`

- [ ] **Step 1: Create the reference file**

```json
{
  "version": "1.0",
  "source": "NIS2 Directive (EU) 2022/2555 Annex I & II, CER Directive (EU) 2022/2557",
  "entity_types": [
    {"id": "electricity_undertaking", "label": "Electricity undertaking", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "distribution_system_operator", "label": "Distribution system operator", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "transmission_system_operator", "label": "Transmission system operator", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "oil_undertaking", "label": "Oil undertaking", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "gas_undertaking", "label": "Gas undertaking", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "hydrogen_operator", "label": "Hydrogen operator", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "district_heating_operator", "label": "District heating/cooling operator", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "electricity_market_operator", "label": "Electricity market operator (NEMO)", "sector": "energy", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "air_carrier", "label": "Air carrier", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "airport_operator", "label": "Airport managing body", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "traffic_management_operator", "label": "Traffic management control operator", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "rail_infrastructure_manager", "label": "Railway infrastructure manager", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "railway_undertaking", "label": "Railway undertaking", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "shipping_company", "label": "Shipping company", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "port_operator", "label": "Port managing body", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "inland_waterway_operator", "label": "Inland waterway transport operator", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "road_authority", "label": "Road authority", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "its_operator", "label": "Intelligent transport systems operator", "sector": "transport", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "credit_institution", "label": "Credit institution", "sector": "banking", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "trading_venue_operator", "label": "Trading venue operator", "sector": "financial_market", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "central_counterparty", "label": "Central counterparty (CCP)", "sector": "financial_market", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "healthcare_provider", "label": "Healthcare provider", "sector": "health", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "eu_reference_laboratory", "label": "EU reference laboratory", "sector": "health", "annex": "I", "nis2_status": "essential", "cer_eligible": false},
    {"id": "pharma_rd_manufacturer", "label": "Pharmaceutical R&D/manufacturer", "sector": "health", "annex": "I", "nis2_status": "essential", "cer_eligible": false},
    {"id": "medical_device_manufacturer", "label": "Medical device manufacturer (critical)", "sector": "health", "annex": "I", "nis2_status": "essential", "cer_eligible": false},

    {"id": "drinking_water_supplier", "label": "Drinking water supplier/distributor", "sector": "drinking_water", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "waste_water_operator", "label": "Waste water collection/treatment operator", "sector": "waste_water", "annex": "I", "nis2_status": "essential", "cer_eligible": false},

    {"id": "ixp_operator", "label": "Internet exchange point operator", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "dns_service_provider", "label": "DNS service provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "tld_registry", "label": "TLD name registry", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "cloud_computing_provider", "label": "Cloud computing service provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "data_centre_operator", "label": "Data centre service provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "cdn_provider", "label": "Content delivery network provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "trust_service_provider", "label": "Trust service provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "public_ecn_provider", "label": "Public electronic communications network provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "public_ecs_provider", "label": "Public electronic communications service provider", "sector": "digital_infrastructure", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "managed_service_provider", "label": "Managed service provider (MSP)", "sector": "ict_service_management", "annex": "I", "nis2_status": "essential", "cer_eligible": false},
    {"id": "managed_security_service_provider", "label": "Managed security service provider (MSSP)", "sector": "ict_service_management", "annex": "I", "nis2_status": "essential", "cer_eligible": false},

    {"id": "central_government_entity", "label": "Central government entity", "sector": "public_administration", "annex": "I", "nis2_status": "essential", "cer_eligible": true},
    {"id": "regional_government_entity", "label": "Regional government entity", "sector": "public_administration", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "space_operator", "label": "Operator of ground-based infrastructure (space)", "sector": "space", "annex": "I", "nis2_status": "essential", "cer_eligible": true},

    {"id": "postal_service_provider", "label": "Postal service provider", "sector": "postal", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "courier_service_provider", "label": "Courier service provider", "sector": "postal", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "waste_management_operator", "label": "Waste management undertaking", "sector": "waste_management", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "medical_device_manufacturer_ii", "label": "Medical device manufacturer (non-critical, Annex II)", "sector": "manufacturing", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "machinery_manufacturer", "label": "Machinery & equipment manufacturer", "sector": "manufacturing", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "motor_vehicle_manufacturer", "label": "Motor vehicle manufacturer", "sector": "manufacturing", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "electrical_equipment_manufacturer", "label": "Electrical equipment manufacturer", "sector": "manufacturing", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "chemicals_manufacturer", "label": "Chemicals manufacturer", "sector": "chemicals", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "chemicals_distributor", "label": "Chemicals distributor", "sector": "chemicals", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "food_producer", "label": "Food production undertaking", "sector": "food", "annex": "II", "nis2_status": "important", "cer_eligible": true},
    {"id": "food_distributor", "label": "Food distribution undertaking", "sector": "food", "annex": "II", "nis2_status": "important", "cer_eligible": true},

    {"id": "online_marketplace_provider", "label": "Online marketplace provider", "sector": "digital_providers", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "search_engine_provider", "label": "Online search engine provider", "sector": "digital_providers", "annex": "II", "nis2_status": "important", "cer_eligible": false},
    {"id": "social_network_provider", "label": "Social networking service provider", "sector": "digital_providers", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "research_organisation", "label": "Research organisation", "sector": "research", "annex": "II", "nis2_status": "important", "cer_eligible": false},

    {"id": "generic_enterprise", "label": "Generic enterprise (non-NIS2)", "sector": "non_nis2", "annex": null, "nis2_status": "not_applicable", "cer_eligible": false},
    {"id": "generic_sme", "label": "Generic SME (non-NIS2)", "sector": "non_nis2", "annex": null, "nis2_status": "not_applicable", "cer_eligible": false},
    {"id": "generic_individual", "label": "Individual (non-NIS2)", "sector": "non_nis2", "annex": null, "nis2_status": "not_applicable", "cer_eligible": false}
  ]
}
```

Write this to `data/reference/nis2_entity_types.json`.

- [ ] **Step 2: Validate the reference file loads**

Run: `python -c "import json; d=json.load(open('data/reference/nis2_entity_types.json')); print(f'{len(d[\"entity_types\"])} entity types'); sectors=set(e['sector'] for e in d['entity_types']); print(f'Sectors: {sorted(sectors)}')"`

Expected: 59 entity types, covering all 19 sectors (18 NIS2 + non_nis2).

- [ ] **Step 3: Commit**

```bash
git add data/reference/nis2_entity_types.json
git commit -m "feat(v3): add NIS2-aligned entity types reference (Annex I+II, CER)"
```

---

### Task 2: Add VALID_ENTITY_TYPES, cer_critical_entity, remove deployment_scale from Contextual Model

**Files:**
- Modify: `src/cyberscale/models/contextual.py`
- Modify: `src/tests/models/test_contextual.py`

- [ ] **Step 1: Write failing tests**

Replace the entire test file `src/tests/models/test_contextual.py` with updated tests. Key changes: remove all `deployment_scale` tests, add `VALID_ENTITY_TYPES` and `cer_critical_entity` tests.

```python
"""Tests for Phase 2 — Contextual severity classifier."""

from __future__ import annotations

import pytest

from cyberscale.models.contextual import (
    ContextualClassifier, ContextualResult, VALID_ENTITY_TYPES,
)


class TestContextualResult:
    def test_result_fields(self):
        r = ContextualResult(severity="High", confidence="high", key_factors=["health sector", "RCE"])
        assert r.severity == "High"
        assert len(r.key_factors) == 2

    def test_to_dict(self):
        r = ContextualResult(severity="Critical", confidence="medium", key_factors=["cross-border"])
        d = r.to_dict()
        assert d["severity"] == "Critical"
        assert d["key_factors"] == ["cross-border"]


class TestValidEntityTypes:
    def test_entity_types_is_set(self):
        assert isinstance(VALID_ENTITY_TYPES, set)

    def test_contains_annex_i_entities(self):
        for et in ["healthcare_provider", "credit_institution", "cloud_computing_provider", "managed_service_provider"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_contains_annex_ii_entities(self):
        for et in ["postal_service_provider", "chemicals_manufacturer", "food_producer", "research_organisation"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_contains_non_nis2_entities(self):
        for et in ["generic_enterprise", "generic_sme", "generic_individual"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_old_entity_types_not_present(self):
        for old in ["individual", "sme", "msp", "hospital", "cloud_provider", "utility", "government", "bank"]:
            assert old not in VALID_ENTITY_TYPES, f"Old entity type {old} should not be in VALID_ENTITY_TYPES"

    def test_entity_type_count(self):
        assert len(VALID_ENTITY_TYPES) >= 55


class TestFormatInput:
    def test_with_all_fields(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input("Buffer overflow in X", sector="health", cross_border=True, score=8.5)
        assert "Buffer overflow in X" in text
        assert "sector: health" in text
        assert "cross_border: true" in text
        assert "score: 8.5" in text

    def test_without_score(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input("Buffer overflow in X", sector="energy", cross_border=False, score=None)
        assert "sector: energy" in text
        assert "cross_border: false" in text
        assert "score:" not in text

    def test_sector_validation(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(ValueError, match="Unknown sector"):
            clf._format_input("desc", sector="invalid_sector", cross_border=False)

    def test_deployment_scale_not_accepted(self):
        """deployment_scale was removed in v3 — entity_type encodes scale."""
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(TypeError):
            clf._format_input(
                "Buffer overflow", sector="health", cross_border=True,
                score=8.5, deployment_scale="enterprise",
            )

    def test_entity_type_validation_rejects_old_types(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(ValueError, match="Unknown entity_type"):
            clf._format_input(
                "Buffer overflow", sector="health", cross_border=True,
                score=8.5, entity_type="hospital",
            )

    def test_entity_type_validation_accepts_new_types(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="health", cross_border=True,
            score=8.5, entity_type="healthcare_provider",
        )
        assert "entity_type: healthcare_provider" in text

    def test_cer_critical_entity_true_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
            cer_critical_entity=True,
        )
        assert "cer_critical_entity: true" in text

    def test_cer_critical_entity_false_not_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert "cer_critical_entity:" not in text

    def test_cer_critical_entity_none_not_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
        )
        assert "cer_critical_entity:" not in text


class TestClassificationOutput:
    def test_probs_to_severity(self):
        assert ContextualClassifier.probs_to_severity([0.05, 0.10, 0.75, 0.10]) == "High"

    def test_probs_to_severity_critical(self):
        assert ContextualClassifier.probs_to_severity([0.0, 0.0, 0.1, 0.9]) == "Critical"

    def test_confidence_high(self):
        assert ContextualClassifier.max_prob_to_confidence(0.85) == "high"

    def test_confidence_medium(self):
        assert ContextualClassifier.max_prob_to_confidence(0.55) == "medium"

    def test_confidence_low(self):
        assert ContextualClassifier.max_prob_to_confidence(0.30) == "low"


class TestKeyFactors:
    def test_basic_factors(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5)
        assert "health sector" in factors
        assert "cross-border exposure" in factors
        assert "critical base score" in factors

    def test_no_cross_border(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0)
        assert "energy sector" in factors
        assert "cross-border exposure" not in factors
        assert "critical base score" not in factors

    def test_entity_type_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, entity_type="healthcare_provider")
        assert "healthcare_provider entity" in factors

    def test_cer_critical_entity_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors(
            "food", False, 6.0, entity_type="food_producer",
            cer_critical_entity=True,
        )
        assert "CER critical entity (essential override)" in factors

    def test_cer_critical_entity_false_no_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors(
            "food", False, 6.0, entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert not any("CER" in f for f in factors)

    def test_no_deployment_factor(self):
        """deployment_scale was removed in v3."""
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0, entity_type="electricity_undertaking")
        assert not any("deployment" in f for f in factors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd src && python -m pytest tests/models/test_contextual.py -v --tb=short 2>&1 | tail -30`

Expected: Multiple FAIL — `VALID_ENTITY_TYPES` not importable, `deployment_scale` still accepted, `cer_critical_entity` not accepted.

- [ ] **Step 3: Update contextual.py**

Replace the full `src/cyberscale/models/contextual.py` with:

```python
"""Phase 2 -- Contextual severity classifier.

Assesses context-dependent vulnerability severity based on NIS2 sector
and cross-border exposure. Works with or without a Phase 1 score.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


VALID_SECTORS = {
    "energy", "transport", "banking", "financial_market", "health",
    "drinking_water", "waste_water", "digital_infrastructure",
    "ict_service_management", "public_administration", "space",
    "postal", "waste_management", "manufacturing", "chemicals",
    "food", "digital_providers", "research", "non_nis2",
}

VALID_ENTITY_TYPES = {
    # Annex I — Essential
    "electricity_undertaking", "distribution_system_operator", "transmission_system_operator",
    "oil_undertaking", "gas_undertaking", "hydrogen_operator", "district_heating_operator",
    "electricity_market_operator",
    "air_carrier", "airport_operator", "traffic_management_operator", "rail_infrastructure_manager",
    "railway_undertaking", "shipping_company", "port_operator", "inland_waterway_operator",
    "road_authority", "its_operator",
    "credit_institution",
    "trading_venue_operator", "central_counterparty",
    "healthcare_provider", "eu_reference_laboratory", "pharma_rd_manufacturer", "medical_device_manufacturer",
    "drinking_water_supplier",
    "waste_water_operator",
    "ixp_operator", "dns_service_provider", "tld_registry", "cloud_computing_provider",
    "data_centre_operator", "cdn_provider", "trust_service_provider",
    "public_ecn_provider", "public_ecs_provider",
    "managed_service_provider", "managed_security_service_provider",
    "central_government_entity", "regional_government_entity",
    "space_operator",
    # Annex II — Important
    "postal_service_provider", "courier_service_provider",
    "waste_management_operator",
    "medical_device_manufacturer_ii", "machinery_manufacturer", "motor_vehicle_manufacturer",
    "electrical_equipment_manufacturer",
    "chemicals_manufacturer", "chemicals_distributor",
    "food_producer", "food_distributor",
    "online_marketplace_provider", "search_engine_provider", "social_network_provider",
    "research_organisation",
    # Non-NIS2
    "generic_enterprise", "generic_sme", "generic_individual",
}

LABEL_MAP = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}


@dataclass
class ContextualResult:
    """Result of a contextual severity classification."""

    severity: str       # Critical / High / Medium / Low
    confidence: str     # high / medium / low
    key_factors: list[str]

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "confidence": self.confidence,
            "key_factors": self.key_factors,
        }


class ContextualClassifier:
    """ModernBERT classification model for contextual vulnerability severity."""

    def __init__(
        self,
        model_path: str | Path,
        mc_passes: int = 5,
        max_length: int = 256,
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path)
        self.mc_passes = mc_passes
        self.max_length = max_length

        # Auto-detect device: MPS > CUDA > CPU
        if device is not None:
            self.device = torch.device(device)
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_path), num_labels=4
        )
        self.model.to(self.device)
        self.model.eval()

    def predict(
        self,
        description: str,
        sector: str,
        cross_border: bool,
        score: Optional[float] = None,
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> ContextualResult:
        """Classify contextual severity with MC dropout confidence."""
        text = self._format_input(
            description, sector, cross_border, score=score,
            entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
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
            entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
        )

        return ContextualResult(
            severity=severity, confidence=confidence, key_factors=key_factors
        )

    def _format_input(
        self,
        description: str,
        sector: str,
        cross_border: bool,
        score: Optional[float] = None,
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> str:
        """Format input text for the model.

        Raises ValueError if sector is not in VALID_SECTORS or
        entity_type is not in VALID_ENTITY_TYPES.
        """
        if sector not in VALID_SECTORS:
            raise ValueError(f"Unknown sector: {sector}")
        if entity_type is not None and entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(f"Unknown entity_type: {entity_type}")

        cross_border_str = "true" if cross_border else "false"
        parts = [
            description,
            f"[SEP] sector: {sector}",
            f"cross_border: {cross_border_str}",
        ]
        if score is not None:
            parts.append(f"score: {score}")
        if entity_type is not None:
            parts.append(f"entity_type: {entity_type}")
        if cer_critical_entity:
            parts.append("cer_critical_entity: true")
        return " ".join(parts)

    def _enable_dropout(self) -> None:
        """Enable dropout layers for MC dropout at inference time."""
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()

    def _extract_key_factors(
        self,
        sector: str,
        cross_border: bool,
        score: Optional[float],
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> list[str]:
        """Extract key contextual factors for explainability."""
        factors = [f"{sector} sector"]
        if cross_border:
            factors.append("cross-border exposure")
        if score is not None and score >= 9.0:
            factors.append("critical base score")
        if entity_type is not None:
            factors.append(f"{entity_type} entity")
        if cer_critical_entity:
            factors.append("CER critical entity (essential override)")
        return factors

    @staticmethod
    def probs_to_severity(probs: list[float]) -> str:
        """Map class probabilities to a severity label via argmax."""
        idx = probs.index(max(probs))
        return LABEL_MAP[idx]

    @staticmethod
    def max_prob_to_confidence(max_prob: float) -> str:
        """Map maximum class probability to a confidence label."""
        if max_prob > 0.7:
            return "high"
        if max_prob > 0.4:
            return "medium"
        return "low"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd src && python -m pytest tests/models/test_contextual.py -v --tb=short 2>&1 | tail -40`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/models/contextual.py src/tests/models/test_contextual.py
git commit -m "feat(v3): add VALID_ENTITY_TYPES, cer_critical_entity; remove deployment_scale from contextual model"
```

---

### Task 3: Update MCP Contextual Tool — remove deployment_scale, add cer_critical_entity

**Files:**
- Modify: `src/cyberscale/tools/contextual.py`
- Modify: `src/tests/tools/test_contextual_tool.py`

- [ ] **Step 1: Write updated tests**

Replace `src/tests/tools/test_contextual_tool.py` with:

```python
"""Tests for Phase 2 contextual severity MCP tool helpers."""

from unittest.mock import MagicMock

from cyberscale.models.contextual import ContextualResult


class TestAssessContextualSeverity:
    def test_model_prediction_returned(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical",
            confidence="high",
            key_factors=["health sector", "cross-border exposure"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in clinical system",
            sector="health",
            cross_border=True,
            score=8.5,
        )
        assert result["severity"] == "Critical"
        assert result["confidence"] == "high"
        assert "health sector" in result["key_factors"]
        assert result["sector"] == "health"
        assert result["cross_border"] is True

    def test_invalid_sector_returns_error(self):
        from cyberscale.tools.contextual import _validate_sector

        ok, err = _validate_sector("health")
        assert ok is True
        assert err == ""

        ok, err = _validate_sector("invalid")
        assert ok is False
        assert "Unknown sector" in err

    def test_no_cross_border(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium",
            confidence="medium",
            key_factors=["energy sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="DoS in web app",
            sector="energy",
            cross_border=False,
        )
        assert result["severity"] == "Medium"
        assert result["cross_border"] is False

    def test_all_valid_sectors_accepted(self):
        from cyberscale.tools.contextual import VALID_SECTORS, _validate_sector

        for sector in VALID_SECTORS:
            ok, err = _validate_sector(sector)
            assert ok is True, f"Sector {sector} should be valid"

    def test_score_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High",
            confidence="high",
            key_factors=["transport sector", "critical base score"],
        )
        _assess_with_model(
            mock_clf,
            description="Buffer overflow in SCADA",
            sector="transport",
            cross_border=True,
            score=9.5,
        )
        mock_clf.predict.assert_called_once_with(
            "Buffer overflow in SCADA", "transport", True, 9.5,
            entity_type=None, cer_critical_entity=None,
        )

    def test_score_none_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
            cross_border=False,
        )
        mock_clf.predict.assert_called_once_with(
            "Info disclosure", "non_nis2", False, None,
            entity_type=None, cer_critical_entity=None,
        )

    def test_entity_type_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical",
            confidence="high",
            key_factors=["healthcare_provider entity"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in medical device firmware",
            sector="health",
            cross_border=True,
            score=9.1,
            entity_type="healthcare_provider",
        )
        mock_clf.predict.assert_called_once_with(
            "RCE in medical device firmware", "health", True, 9.1,
            entity_type="healthcare_provider", cer_critical_entity=None,
        )
        assert result["entity_type"] == "healthcare_provider"

    def test_entity_type_absent_from_output_when_none(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
            cross_border=False,
        )
        assert "entity_type" not in result

    def test_deployment_scale_not_accepted(self):
        """deployment_scale was removed in v3."""
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium", confidence="medium", key_factors=[],
        )
        import inspect
        sig = inspect.signature(_assess_with_model)
        assert "deployment_scale" not in sig.parameters


class TestCerCriticalEntity:
    def test_cer_critical_entity_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High",
            confidence="high",
            key_factors=["food sector", "CER critical entity (essential override)"],
        )
        result = _assess_with_model(
            mock_clf,
            description="DoS in food supply chain",
            sector="food",
            cross_border=False,
            entity_type="food_producer",
            cer_critical_entity=True,
        )
        mock_clf.predict.assert_called_once_with(
            "DoS in food supply chain", "food", False, None,
            entity_type="food_producer", cer_critical_entity=True,
        )
        assert result["cer_critical_entity"] is True

    def test_cer_critical_entity_absent_when_none(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
            cross_border=False,
        )
        assert "cer_critical_entity" not in result

    def test_cer_critical_entity_false_absent(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium",
            confidence="medium",
            key_factors=["food sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="XSS in food portal",
            sector="food",
            cross_border=False,
            entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert "cer_critical_entity" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd src && python -m pytest tests/tools/test_contextual_tool.py -v --tb=short 2>&1 | tail -30`

Expected: FAIL — `_assess_with_model` still has `deployment_scale`, doesn't have `cer_critical_entity`.

- [ ] **Step 3: Update tools/contextual.py**

Replace `src/cyberscale/tools/contextual.py` with:

```python
"""Phase 2 MCP tools — Contextual severity with model integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_classifier_instance = None
_model_path = Path("data/models/contextual")


def _get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        if not _model_path.exists():
            return None
        from cyberscale.models.contextual import ContextualClassifier
        _classifier_instance = ContextualClassifier(model_path=_model_path)
    return _classifier_instance


# ---------------------------------------------------------------------------
# Sector validation
# ---------------------------------------------------------------------------

VALID_SECTORS = {
    "energy", "transport", "banking", "financial_market", "health",
    "drinking_water", "waste_water", "digital_infrastructure",
    "ict_service_management", "public_administration", "space",
    "postal", "waste_management", "manufacturing", "chemicals",
    "food", "digital_providers", "research", "non_nis2",
}


def _validate_sector(sector: str) -> tuple[bool, str]:
    """Validate that sector is in the allowed NIS2 sector list."""
    if sector not in VALID_SECTORS:
        return False, f"Unknown sector: {sector}. Valid sectors: {sorted(VALID_SECTORS)}"
    return True, ""


# ---------------------------------------------------------------------------
# Internal helper functions (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_with_model(
    clf,
    description: str,
    sector: str,
    cross_border: bool,
    score: float | None = None,
    entity_type: str | None = None,
    cer_critical_entity: bool | None = None,
) -> dict:
    """Assess contextual severity using the classifier model."""
    result = clf.predict(
        description, sector, cross_border, score,
        entity_type=entity_type, cer_critical_entity=cer_critical_entity,
    )
    out = {
        "severity": result.severity,
        "confidence": result.confidence,
        "key_factors": result.key_factors,
        "sector": sector,
        "cross_border": cross_border,
    }
    if entity_type is not None:
        out["entity_type"] = entity_type
    if cer_critical_entity:
        out["cer_critical_entity"] = True
    return out


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_contextual_severity(
        description: str,
        sector: str,
        cross_border: bool,
        severity_score: float | None = None,
        entity_type: str | None = None,
        cer_critical_entity: bool | None = None,
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
            score=severity_score, entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd src && python -m pytest tests/tools/test_contextual_tool.py -v --tb=short`

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/tools/contextual.py src/tests/tools/test_contextual_tool.py
git commit -m "feat(v3): remove deployment_scale, add cer_critical_entity to contextual MCP tool"
```

---

### Task 4: Update Pipeline and Full Pipeline MCP Tool — remove deployment_scale, add cer_critical_entity

**Files:**
- Modify: `src/cyberscale/pipeline.py`
- Modify: `src/cyberscale/tools/vulnerability.py`
- Modify: `src/tests/test_pipeline.py`
- Modify: `src/tests/tools/test_vulnerability_scoring.py`

- [ ] **Step 1: Write failing tests for pipeline**

Add to `src/tests/test_pipeline.py`:

```python
class TestCerCriticalEntityPassthrough:
    def test_pipeline_passes_cer_to_contextual(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(kwargs.get("cer_critical_entity"))
                @dataclass
                class R:
                    severity: str = "High"
                    confidence: str = "high"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),
            contextual=TrackingContextual(),
            description="DoS in food supply",
            sector="food",
            cross_border=False,
            cer_critical_entity=True,
        )
        assert calls == [True]

    def test_pipeline_cer_none_by_default(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(kwargs.get("cer_critical_entity"))
                @dataclass
                class R:
                    severity: str = "Medium"
                    confidence: str = "medium"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),
            contextual=TrackingContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
        )
        assert calls == [None]

    def test_pipeline_rejects_deployment_scale(self):
        """deployment_scale was removed in v3."""
        import inspect
        sig = inspect.signature(run_pipeline)
        assert "deployment_scale" not in sig.parameters
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd src && python -m pytest tests/test_pipeline.py::TestCerCriticalEntityPassthrough -v --tb=short`

Expected: FAIL.

- [ ] **Step 3: Update pipeline.py**

Replace `src/cyberscale/pipeline.py` with:

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
    entity_type: Optional[str] = None,
    cer_critical_entity: Optional[bool] = None,
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
        entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
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

- [ ] **Step 4: Update existing pipeline tests to remove deployment_scale**

In `src/tests/test_pipeline.py`, update `FakeContextual.predict` to use the new signature (no `deployment_scale`), and remove `deployment_scale` from any `run_pipeline()` calls that pass it. The existing tests don't pass `deployment_scale` explicitly, so they should work as-is. Verify:

Run: `cd src && python -m pytest tests/test_pipeline.py -v --tb=short`

Expected: All PASS.

- [ ] **Step 5: Write failing test for pipeline MCP tool**

Add to `src/tests/tools/test_vulnerability_scoring.py`:

```python
class TestPipelineToolCer:
    def test_pipeline_tool_passes_cer_critical_entity(self):
        from cyberscale.tools.vulnerability import _assess_pipeline

        calls = []
        class FakeScorer:
            def predict(self, desc, cwe=None):
                from cyberscale.models.scorer import ScorerResult
                return ScorerResult(score=6.0, confidence="medium", band="Medium")

        class FakeContextual:
            def predict(self, desc, sector, cb, score=None, **kw):
                calls.append(kw.get("cer_critical_entity"))
                from cyberscale.models.contextual import ContextualResult
                return ContextualResult(severity="High", confidence="high", key_factors=["food sector"])

        _assess_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            description="DoS in food chain",
            sector="food",
            cross_border=False,
            entity_type="food_producer",
            cer_critical_entity=True,
        )
        assert calls == [True]

    def test_pipeline_tool_rejects_deployment_scale(self):
        """deployment_scale was removed in v3."""
        from cyberscale.tools.vulnerability import _assess_pipeline
        import inspect
        sig = inspect.signature(_assess_pipeline)
        assert "deployment_scale" not in sig.parameters
```

- [ ] **Step 6: Run to verify it fails**

Run: `cd src && python -m pytest tests/tools/test_vulnerability_scoring.py::TestPipelineToolCer -v --tb=short`

Expected: FAIL.

- [ ] **Step 7: Update vulnerability.py**

In `src/cyberscale/tools/vulnerability.py`, update `_assess_pipeline` and `assess_full_pipeline` to remove `deployment_scale` and add `cer_critical_entity`:

Replace `_assess_pipeline` (lines 42-76):

```python
def _assess_pipeline(
    scorer,
    contextual,
    description: str,
    sector: str,
    cross_border: bool,
    cwe: str | None = None,
    entity_type: str | None = None,
    cer_critical_entity: bool | None = None,
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
        entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
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

Replace `assess_full_pipeline` (lines 182-210):

```python
    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_full_pipeline(
        description: str,
        sector: str,
        cross_border: bool,
        cve_id: str | None = None,
        entity_type: str | None = None,
        cer_critical_entity: bool | None = None,
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
            cwe=cwe, entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
        )
```

Also update the existing `TestPipelineTool.test_pipeline_tool_returns_all_phases` test in `src/tests/tools/test_vulnerability_scoring.py` — the `FakeContextual.predict` signature must match the new one (no `deployment_scale`). Since the existing fake uses `**kw`, it should work without changes.

- [ ] **Step 8: Run all tool tests**

Run: `cd src && python -m pytest tests/tools/test_vulnerability_scoring.py tests/test_pipeline.py -v --tb=short`

Expected: All PASS.

- [ ] **Step 9: Commit**

```bash
git add src/cyberscale/pipeline.py src/cyberscale/tools/vulnerability.py src/tests/test_pipeline.py src/tests/tools/test_vulnerability_scoring.py
git commit -m "feat(v3): remove deployment_scale, add cer_critical_entity to pipeline and MCP tools"
```

---

### Task 5: Update Training Data Generation Script

**Files:**
- Modify: `training/scripts/generate_contextual.py`

- [ ] **Step 1: Update generate_contextual.py**

Key changes:
- Remove `DEPLOYMENT_SCALES` and `ENTITY_TYPES` constants
- Add `load_entity_types()` function
- Update `generate_scenarios()` to use sector-constrained entity types
- Add `cer_critical_entity` to input text and escalation logic
- Remove `deployment_scale` from input text, rows, and fieldnames

Replace the full file with:

```python
#!/usr/bin/env python3
"""Generate contextual severity training data for CyberScale Phase 2.

Combines CVEs × sectors × cross_border with deterministic NIS2 severity rules
to produce labelled classification training data.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
from functools import partial
from pathlib import Path

print = partial(print, flush=True)

# ---------------------------------------------------------------------------
# Trigger detection patterns
# ---------------------------------------------------------------------------

TRIGGER_PATTERNS: dict[str, re.Pattern] = {
    "rce": re.compile(
        r"(?i)(remote code|code execution|arbitrary code|command injection)"
    ),
    "availability": re.compile(
        r"(?i)(denial of service|crash|hang|availability|disruption)"
    ),
    "data_compromise": re.compile(
        r"(?i)(data (leak|breach|exposure)|sensitive (data|information)|exfiltrat)"
    ),
    "authentication_bypass": re.compile(
        r"(?i)(authentication bypass|authorization bypass|privilege escalat)"
    ),
    "scada": re.compile(
        r"(?i)(scada|ics|industrial control|plc|hmi|modbus|dnp3)"
    ),
    "ot": re.compile(r"(?i)(operational technology|OT network|OT system)"),
    "supply_chain": re.compile(
        r"(?i)(supply chain|third.party|upstream|downstream|dependency)"
    ),
    "clinical_system": re.compile(
        r"(?i)(clinical|patient|medical device|hl7|dicom|fhir)"
    ),
    "safety_system": re.compile(
        r"(?i)(safety system|safety critical|sil|functional safety)"
    ),
    "integrity": re.compile(r"(?i)(integrity|tamper|modif|corrupt)"),
    "dns": re.compile(r"(?i)(dns|domain name|nameserver)"),
    "cloud": re.compile(r"(?i)(cloud|aws|azure|gcp|saas|iaas|paas)"),
    "cdn": re.compile(r"(?i)(cdn|content delivery|edge network)"),
    "trust_service": re.compile(
        r"(?i)(certificate|pki|trust service|digital signature)"
    ),
    "ip_theft": re.compile(
        r"(?i)(intellectual property|trade secret|proprietary|research data)"
    ),
    "command_injection": re.compile(
        r"(?i)(command injection|os command|shell injection)"
    ),
}

SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_INDEX = {name: idx for idx, name in enumerate(SEVERITY_LEVELS)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_entity_types(reference_path: Path) -> dict[str, list[dict]]:
    """Load NIS2 entity types and build sector → entity_type mapping."""
    with open(reference_path, encoding="utf-8") as fh:
        data = json.load(fh)
    sector_to_entities: dict[str, list[dict]] = {}
    for et in data["entity_types"]:
        sector_to_entities.setdefault(et["sector"], []).append(et)
    return sector_to_entities


def detect_triggers(description: str) -> set[str]:
    """Return the set of trigger keys that match the CVE description."""
    matched: set[str] = set()
    for key, pattern in TRIGGER_PATTERNS.items():
        if pattern.search(description):
            matched.add(key)
    return matched


def cvss_to_base_severity(score: float, bands: dict) -> str:
    """Map a CVSS score to a base severity label using the rules bands."""
    for label in SEVERITY_LEVELS:
        band = bands[label]
        if band["min"] <= score <= band["max"]:
            return label
    # Edge case: score == 0.0
    return "Low"


def escalate(severity: str, steps: int) -> str:
    """Escalate severity by *steps* levels, capped at Critical."""
    idx = SEVERITY_INDEX[severity]
    new_idx = min(idx + steps, SEVERITY_INDEX["Critical"])
    return SEVERITY_LEVELS[new_idx]


def parse_escalation(value: str) -> int:
    """Parse an escalation string like '+1' or '0' to an integer."""
    value = value.strip()
    if value.startswith("+"):
        return int(value[1:])
    return int(value)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------


def load_cves(path: Path) -> list[dict]:
    """Load CVEs from the Phase 1 CSV."""
    cves: list[dict] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                score = float(row["cvss_score"])
            except (ValueError, KeyError):
                continue
            if score <= 0:
                continue
            cves.append(
                {
                    "cve_id": row["cve_id"],
                    "description": row["description"],
                    "cvss_score": score,
                }
            )
    return cves


def generate_scenarios(
    cves: list[dict],
    rules: dict,
    max_scenarios_per_cve: int,
    cross_border_ratio: float,
    non_trigger_ratio: float,
    cross_border_escalation_prob: float,
    seed: int,
    sector_entity_map: dict[str, list[dict]] | None = None,
) -> list[dict]:
    """Generate contextual severity scenarios for all CVEs.

    Two types of scenarios per sector:
    1. Trigger-matched: CVE triggers overlap sector triggers → escalation applied
    2. Non-triggered: CVE is in sector but doesn't affect critical systems → base
       severity preserved (e.g., XSS in hospital admin portal, not clinical system)

    non_trigger_ratio controls what fraction of each NIS2 sector's scenarios are
    non-triggered (base severity). This prevents the model from learning that
    regulated sector = always escalate.

    cross_border_escalation_prob controls the probability that cross-border
    actually triggers escalation (real-world: not every cross-border scenario
    warrants escalation).
    """
    rng = random.Random(seed)

    escalation_cfg = rules["rules"]["escalation_triggers"]
    bands = rules["rules"]["base_severity_from_cvss"]
    cross_border_esc = parse_escalation(
        rules["rules"]["cross_border_rule"]["escalation"]
    )

    nis2_sectors = [s for s in escalation_cfg if s != "non_nis2"]
    rows: list[dict] = []

    for cve in cves:
        desc = cve["description"]
        score = cve["cvss_score"]
        base_sev = cvss_to_base_severity(score, bands)
        cve_triggers = detect_triggers(desc)

        # --- Trigger-matched sectors (escalation applies) ---
        triggered_sectors: list[str] = []
        for sector_id, sector_cfg in escalation_cfg.items():
            if sector_id == "non_nis2":
                continue
            sector_triggers = set(sector_cfg["triggers"])
            if cve_triggers & sector_triggers:
                triggered_sectors.append(sector_id)

        # --- Non-triggered sectors (base severity, no escalation) ---
        # Pick random NIS2 sectors that this CVE did NOT trigger
        non_triggered_pool = [s for s in nis2_sectors if s not in triggered_sectors]
        n_non_triggered = max(1, int(len(triggered_sectors) * non_trigger_ratio))
        if non_triggered_pool:
            non_triggered_sectors = rng.sample(
                non_triggered_pool, min(n_non_triggered, len(non_triggered_pool))
            )
        else:
            non_triggered_sectors = []

        # --- Build candidate scenarios ---
        candidates: list[tuple[str, bool, bool]] = []  # (sector, cross_border, is_triggered)

        # Triggered sectors
        for sector_id in triggered_sectors:
            candidates.append((sector_id, False, True))
            candidates.append((sector_id, True, True))

        # Non-triggered sectors (base severity)
        for sector_id in non_triggered_sectors:
            candidates.append((sector_id, False, False))
            candidates.append((sector_id, True, False))

        # Always include non_nis2 (never escalates)
        candidates.append(("non_nis2", False, False))
        candidates.append(("non_nis2", True, False))

        # Cap scenarios per CVE
        if len(candidates) > max_scenarios_per_cve:
            candidates = rng.sample(candidates, max_scenarios_per_cve)

        for sector_id, cross_border, is_triggered in candidates:
            sector_cfg = escalation_cfg[sector_id]
            sector_esc = parse_escalation(sector_cfg["escalation"])

            # Compute contextual severity
            ctx_sev = base_sev

            # Sector escalation: only if trigger-matched
            if is_triggered:
                ctx_sev = escalate(ctx_sev, sector_esc)

            # Cross-border escalation: probabilistic
            if cross_border and rng.random() < cross_border_escalation_prob:
                ctx_sev = escalate(ctx_sev, cross_border_esc)

            # Select entity type constrained to sector
            if sector_entity_map:
                sector_entities = sector_entity_map.get(sector_id, [])
                if sector_entities:
                    entity_info = rng.choice(sector_entities)
                    entity_type = entity_info["id"]
                    # CER critical entity: true only for CER-eligible entities (10% probability)
                    cer_critical_entity = entity_info["cer_eligible"] and rng.random() < 0.1
                else:
                    entity_type = "generic_enterprise"
                    cer_critical_entity = False
            else:
                entity_type = "generic_enterprise"
                cer_critical_entity = False

            # CER critical entity escalation: Annex II entity treated as essential
            if cer_critical_entity and sector_id not in ["non_nis2"]:
                ctx_sev = escalate(ctx_sev, 1)

            # Format input text
            input_text = (
                f"{desc} [SEP] sector: {sector_id} "
                f"cross_border: {str(cross_border).lower()} "
                f"score: {score} "
                f"entity_type: {entity_type}"
            )
            if cer_critical_entity:
                input_text += " cer_critical_entity: true"

            label = SEVERITY_INDEX[ctx_sev]

            rows.append(
                {
                    "cve_id": cve["cve_id"],
                    "input_text": input_text,
                    "sector": sector_id,
                    "cross_border": cross_border,
                    "cvss_score": score,
                    "base_severity": base_sev,
                    "contextual_severity": ctx_sev,
                    "label": label,
                    "entity_type": entity_type,
                    "cer_critical_entity": cer_critical_entity,
                }
            )

    return rows


def balance_classes(
    rows: list[dict], min_per_class: int, seed: int
) -> list[dict]:
    """Undersample majority classes to min_per_class."""
    rng = random.Random(seed)
    by_label: dict[int, list[dict]] = {}
    for row in rows:
        by_label.setdefault(row["label"], []).append(row)

    balanced: list[dict] = []
    for label_idx in sorted(by_label.keys()):
        class_rows = by_label[label_idx]
        if len(class_rows) > min_per_class:
            class_rows = rng.sample(class_rows, min_per_class)
        balanced.extend(class_rows)

    rng.shuffle(balanced)
    return balanced


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate contextual severity training data"
    )
    parser.add_argument(
        "--cves",
        type=Path,
        required=True,
        help="Path to Phase 1 CVE CSV (training_cves_80k.csv)",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        required=True,
        help="Path to sector_severity_rules.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to contextual_cls.json config",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output CSV path",
    )
    args = parser.parse_args()

    # Load config
    with open(args.config, encoding="utf-8") as fh:
        config = json.load(fh)

    data_cfg = config["data"]
    model_cfg = config["model"]
    seed = model_cfg["seed"]

    # Load rules
    with open(args.rules, encoding="utf-8") as fh:
        rules = json.load(fh)

    # Load entity types
    entity_types_path = Path(__file__).parent.parent.parent / "data" / "reference" / "nis2_entity_types.json"
    sector_entity_map = load_entity_types(entity_types_path)
    print(f"Loaded entity types for {len(sector_entity_map)} sectors")

    # Load CVEs
    print(f"Loading CVEs from {args.cves} ...")
    cves = load_cves(args.cves)
    print(f"  Loaded {len(cves)} CVEs with valid CVSS scores")

    # Generate scenarios
    print("Generating scenarios ...")
    rows = generate_scenarios(
        cves=cves,
        rules=rules,
        max_scenarios_per_cve=data_cfg["max_scenarios_per_cve"],
        cross_border_ratio=data_cfg["cross_border_ratio"],
        non_trigger_ratio=data_cfg.get("non_trigger_ratio", 1.0),
        cross_border_escalation_prob=data_cfg.get("cross_border_escalation_prob", 0.5),
        seed=seed,
        sector_entity_map=sector_entity_map,
    )
    print(f"  Generated {len(rows)} raw scenarios")

    # Print per-sector counts
    sector_counts = Counter(r["sector"] for r in rows)
    print("\nPer-sector counts (before balancing):")
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        print(f"  {sector}: {count}")

    # Print per-class distribution before balancing
    class_counts = Counter(r["label"] for r in rows)
    print("\nPer-class distribution (before balancing):")
    for label_idx in sorted(class_counts.keys()):
        label_name = SEVERITY_LEVELS[label_idx]
        print(f"  {label_name} ({label_idx}): {class_counts[label_idx]}")

    # Print entity type distribution
    et_counts = Counter(r["entity_type"] for r in rows)
    print(f"\nUnique entity types: {len(et_counts)}")
    cer_count = sum(1 for r in rows if r["cer_critical_entity"])
    print(f"CER critical entity scenarios: {cer_count} ({100*cer_count/len(rows):.1f}%)")

    # Balance if configured
    if data_cfg.get("target_balance", False):
        min_per_class = data_cfg["min_per_class"]
        print(f"\nBalancing: undersampling majority classes to {min_per_class} ...")
        rows = balance_classes(rows, min_per_class, seed)
        print(f"  Balanced to {len(rows)} scenarios")

        # Print per-class distribution after balancing
        class_counts = Counter(r["label"] for r in rows)
        print("\nPer-class distribution (after balancing):")
        for label_idx in sorted(class_counts.keys()):
            label_name = SEVERITY_LEVELS[label_idx]
            print(f"  {label_name} ({label_idx}): {class_counts[label_idx]}")

    # Write output
    print(f"\nWriting {len(rows)} scenarios to {args.output} ...")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "cve_id",
        "input_text",
        "sector",
        "cross_border",
        "cvss_score",
        "base_severity",
        "contextual_severity",
        "label",
        "entity_type",
        "cer_critical_entity",
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the script parses without errors**

Run: `python -c "import ast; ast.parse(open('training/scripts/generate_contextual.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add training/scripts/generate_contextual.py
git commit -m "feat(v3): use NIS2 entity types in generation, remove deployment_scale, add CER escalation"
```

---

### Task 6: Regenerate Training Data

**Files:**
- Output: `data/training/contextual/` (regenerated CSVs)

- [ ] **Step 1: Regenerate training data**

Run: `python training/scripts/generate_contextual.py --cves data/training/training_cves_80k.csv --rules data/reference/sector_severity_rules.json --config training/configs/contextual_cls.json --output data/training/contextual/contextual_train.csv`

Expected: Script completes, prints entity type counts per sector.

- [ ] **Step 2: Validate output**

Run: `python -c "import csv; rows=list(csv.DictReader(open('data/training/contextual/contextual_train.csv'))); ets=set(r['entity_type'] for r in rows); print(f'{len(ets)} unique entity types'); print('Has cer:', any(r.get('cer_critical_entity','')=='True' for r in rows)); print('Has deployment_scale:', 'deployment_scale' in rows[0])"`

Expected: 40+ unique entity types, CER present, no deployment_scale column.

- [ ] **Step 3: Commit**

```bash
git add data/training/contextual/contextual_train.csv
git commit -m "data(v3): regenerate Phase 2 training data with NIS2 entity types"
```

---

### Task 7: Retrain Phase 2 Model

**Files:**
- Output: `data/models/contextual/` (retrained model)

- [ ] **Step 1: Find and run the training command**

Run: `ls training/scripts/train_contextual*`

Run the training script (adjust based on what exists):

Run: `python training/scripts/train_contextual.py --config training/configs/contextual_cls.json --data data/training/contextual/contextual_train.csv --output data/models/contextual`

This is a long-running process. Run in foreground with explicit timeout management per lessons-learned.md lesson 15.

- [ ] **Step 2: Verify model outputs directory**

Run: `ls data/models/contextual/`

Expected: Model files present (config.json, model.safetensors, tokenizer files).

- [ ] **Step 3: Commit**

```bash
git add data/models/contextual/
git commit -m "model(v3): retrain Phase 2 contextual model with NIS2 entity types"
```

---

### Task 8: Run Full Test Suite and Benchmark

- [ ] **Step 1: Run all tests**

Run: `cd src && python -m pytest tests/ -v --tb=short 2>&1 | tail -50`

Expected: All tests PASS.

- [ ] **Step 2: Run Phase 2 benchmark if available**

Run: `ls evaluation/benchmark_predecessor* evaluation/evaluate_contextual* 2>/dev/null`

If benchmark exists, run it against the retrained model and verify accuracy >= 80%.

- [ ] **Step 3: Commit any benchmark results**

```bash
git add evaluation/
git commit -m "bench(v3): Phase 2 benchmark with NIS2 entity types"
```

---

## Dependency Graph

```
Task 1 (reference JSON) ──┬──> Task 2 (model code) ──> Task 3 (MCP contextual) ──┐
                           │                                                       │
                           └──> Task 5 (generation script) ──> Task 6 (regen data) │
                                                                    │              │
                                                                    v              v
                                                              Task 7 (retrain) ──> Task 8 (test)
                                                                    ^
                                Task 4 (pipeline + MCP) ────────────┘
```

Tasks 2 and 5 can run in parallel (no dependencies). Tasks 3 and 4 depend on Task 2. Task 6 depends on Tasks 1 and 5. Task 7 depends on Task 6. Task 8 depends on everything.
