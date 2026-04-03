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

from cyberscale.config import (
    VALID_SECTORS,
    VALID_ENTITY_TYPES,
    VALID_SERVICE_IMPACT,
    VALID_DATA_IMPACT,
    VALID_FINANCIAL_IMPACT,
    VALID_SAFETY_IMPACT,
    max_prob_to_confidence,
)

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
        # Incident-mode impact fields (all optional, Phase B)
        entity_affected: Optional[bool] = None,
        service_impact: Optional[str] = None,
        data_impact: Optional[str] = None,
        financial_impact: Optional[str] = None,
        safety_impact: Optional[str] = None,
        affected_persons_count: Optional[int] = None,
        suspected_malicious: Optional[bool] = None,
        impact_duration_hours: Optional[int] = None,
    ) -> ContextualResult:
        """Classify contextual severity with MC dropout confidence.

        When entity_affected=True, the incident-mode impact fields are included
        in the model input for incident-aware severity assessment.
        """
        cross_border = bool(
            ms_affected
            and any(ms != ms_established for ms in ms_affected)
        )
        text = self._format_input(
            description, sector, cross_border,
            ms_established=ms_established, ms_affected=ms_affected,
            score=score, entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
            entity_affected=entity_affected,
            service_impact=service_impact, data_impact=data_impact,
            financial_impact=financial_impact, safety_impact=safety_impact,
            affected_persons_count=affected_persons_count,
            suspected_malicious=suspected_malicious,
            impact_duration_hours=impact_duration_hours,
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
            entity_affected=entity_affected,
            service_impact=service_impact, data_impact=data_impact,
            financial_impact=financial_impact, safety_impact=safety_impact,
            affected_persons_count=affected_persons_count,
            suspected_malicious=suspected_malicious,
            impact_duration_hours=impact_duration_hours,
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
        entity_affected: Optional[bool] = None,
        service_impact: Optional[str] = None,
        data_impact: Optional[str] = None,
        financial_impact: Optional[str] = None,
        safety_impact: Optional[str] = None,
        affected_persons_count: Optional[int] = None,
        suspected_malicious: Optional[bool] = None,
        impact_duration_hours: Optional[int] = None,
    ) -> str:
        """Format input text for the model.

        Raises ValueError if sector is not in VALID_SECTORS or entity_type is
        not in VALID_ENTITY_TYPES.

        When entity_affected is True, incident-mode impact fields are appended.
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
        # Incident-mode impact fields
        if entity_affected:
            parts.append("entity_affected: true")
            if service_impact and service_impact != "none":
                parts.append(f"service_impact: {service_impact}")
            if data_impact and data_impact != "none":
                parts.append(f"data_impact: {data_impact}")
            if financial_impact and financial_impact != "none":
                parts.append(f"financial_impact: {financial_impact}")
            if safety_impact and safety_impact != "none":
                parts.append(f"safety_impact: {safety_impact}")
            if affected_persons_count and affected_persons_count > 0:
                parts.append(f"affected_persons: {affected_persons_count}")
            if suspected_malicious:
                parts.append("suspected_malicious: true")
            if impact_duration_hours and impact_duration_hours > 0:
                parts.append(f"duration_hours: {impact_duration_hours}")
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
        entity_affected: Optional[bool] = None,
        service_impact: Optional[str] = None,
        data_impact: Optional[str] = None,
        financial_impact: Optional[str] = None,
        safety_impact: Optional[str] = None,
        affected_persons_count: Optional[int] = None,
        suspected_malicious: Optional[bool] = None,
        impact_duration_hours: Optional[int] = None,
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
        # Incident-mode factors
        if entity_affected:
            if service_impact in ("unavailable", "sustained"):
                factors.append(f"{service_impact} service impact")
            if data_impact in ("exfiltrated", "compromised", "systemic"):
                factors.append(f"{data_impact} data impact")
            if financial_impact in ("significant", "severe"):
                factors.append(f"{financial_impact} financial impact")
            if safety_impact in ("health_damage", "death"):
                factors.append(f"{safety_impact} safety impact")
            if affected_persons_count and affected_persons_count >= 10000:
                factors.append(f"{affected_persons_count} persons affected")
            if suspected_malicious:
                factors.append("suspected malicious activity")
            if impact_duration_hours and impact_duration_hours >= 24:
                factors.append(f"{impact_duration_hours}h impact duration")
        return factors

    @staticmethod
    def probs_to_severity(probs: list[float]) -> str:
        """Map class probabilities to a severity label via argmax."""
        idx = probs.index(max(probs))
        return LABEL_MAP[idx]

    @staticmethod
    def max_prob_to_confidence(max_prob: float) -> str:
        return max_prob_to_confidence(max_prob)
