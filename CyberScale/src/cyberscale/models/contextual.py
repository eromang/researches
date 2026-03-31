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
        ms_established: str = "EU",
        ms_affected: Optional[list[str]] = None,
        score: Optional[float] = None,
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> ContextualResult:
        """Classify contextual severity with MC dropout confidence."""
        cross_border = bool(
            ms_affected
            and any(ms != ms_established for ms in ms_affected)
        )
        text = self._format_input(
            description, sector, cross_border,
            ms_established=ms_established, ms_affected=ms_affected,
            score=score, entity_type=entity_type,
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
            ms_established=ms_established, ms_affected=ms_affected,
            entity_type=entity_type, cer_critical_entity=cer_critical_entity,
        )

        return ContextualResult(
            severity=severity, confidence=confidence, key_factors=key_factors
        )

    def _format_input(
        self,
        description: str,
        sector: str,
        cross_border: bool,
        ms_established: str = "EU",
        ms_affected: Optional[list[str]] = None,
        score: Optional[float] = None,
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> str:
        """Format input text for the model.

        Raises ValueError if sector is not in VALID_SECTORS or entity_type is
        not in VALID_ENTITY_TYPES.

        The model still sees cross_border: true/false as a derived feature,
        plus the new ms_established and ms_affected fields.
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
            f"ms_established: {ms_established}",
        ]
        if ms_affected:
            parts.append(f"ms_affected: {','.join(ms_affected)}")
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
        ms_established: str = "EU",
        ms_affected: Optional[list[str]] = None,
        entity_type: Optional[str] = None,
        cer_critical_entity: Optional[bool] = None,
    ) -> list[str]:
        """Extract key contextual factors for explainability."""
        factors = [f"{sector} sector"]
        if cross_border:
            n_ms = len(ms_affected) if ms_affected else 0
            factors.append(f"cross-border exposure ({n_ms} MS affected)")
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
