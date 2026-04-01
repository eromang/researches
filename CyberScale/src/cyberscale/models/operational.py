"""Phase 3 -- Operational severity classifier (O1-O4).

Assesses consequence and coordination needs from a crisis management perspective.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


VALID_ENTITY_RELEVANCE = {"non_essential", "essential", "high_relevance", "systemic"}
VALID_CROSS_BORDER = {"none", "limited", "significant", "systemic"}
VALID_FINANCIAL_IMPACT = {"none", "minor", "significant", "severe"}
VALID_SAFETY_IMPACT = {"none", "health_risk", "health_damage", "death"}

O_LABEL_MAP = {0: "O1", 1: "O2", 2: "O3", 3: "O4"}


@dataclass
class OperationalResult:
    """Result of an O-level classification."""

    level: str        # O1 / O2 / O3 / O4
    confidence: str   # high / medium / low
    key_factors: list[str]

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "confidence": self.confidence,
            "key_factors": self.key_factors,
        }


class OperationalClassifier:
    """ModernBERT classifier for operational incident severity (O1-O4)."""

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

    @staticmethod
    def format_input(
        description: str,
        sectors_affected: int = 1,
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        capacity_exceeded: bool = False,
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
        affected_entities: int = 1,
    ) -> str:
        """Format input fields as all-as-text for the model."""
        text = (
            f"{description} [SEP] "
            f"sectors: {sectors_affected} "
            f"relevance: {entity_relevance} "
            f"ms_affected: {ms_affected} "
            f"cross_border: {cross_border_pattern} "
            f"capacity_exceeded: {str(capacity_exceeded).lower()}"
        )
        if financial_impact != "none":
            text += f" financial: {financial_impact}"
        if safety_impact != "none":
            text += f" safety: {safety_impact}"
        if affected_persons_count > 0:
            text += f" persons: {affected_persons_count}"
        if affected_entities > 1:
            text += f" entities: {affected_entities}"
        return text

    def predict(
        self,
        description: str,
        sectors_affected: int = 1,
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        capacity_exceeded: bool = False,
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
        affected_entities: int = 1,
    ) -> OperationalResult:
        """Classify incident operational severity with MC dropout."""
        text = self.format_input(
            description, sectors_affected, entity_relevance,
            ms_affected, cross_border_pattern,
            capacity_exceeded, financial_impact, safety_impact,
            affected_persons_count, affected_entities,
        )
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True,
            max_length=self.max_length, padding="max_length",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        self._enable_dropout()
        all_probs = []
        with torch.no_grad():
            for _ in range(self.mc_passes):
                logits = self.model(**inputs).logits
                probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().tolist()
                all_probs.append(probs)
        self.model.eval()

        mean_probs = [sum(p[i] for p in all_probs) / len(all_probs) for i in range(4)]
        level = O_LABEL_MAP[mean_probs.index(max(mean_probs))]
        max_prob = max(mean_probs)
        confidence = "high" if max_prob > 0.7 else "medium" if max_prob > 0.4 else "low"

        key_factors = self._extract_key_factors(
            sectors_affected, entity_relevance, ms_affected,
            cross_border_pattern, capacity_exceeded,
            financial_impact, safety_impact, affected_persons_count,
            affected_entities,
        )

        return OperationalResult(level=level, confidence=confidence, key_factors=key_factors)

    def _enable_dropout(self) -> None:
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()

    @staticmethod
    def _extract_key_factors(
        sectors_affected: int,
        entity_relevance: str,
        ms_affected: int,
        cross_border_pattern: str,
        capacity_exceeded: bool,
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
        affected_entities: int = 1,
    ) -> list[str]:
        """Extract human-readable key factors from structured fields."""
        factors = []
        if entity_relevance in ("high_relevance", "systemic"):
            factors.append(f"{entity_relevance} entity")
        if ms_affected > 2:
            factors.append(f"{ms_affected} member states affected")
        if cross_border_pattern in ("significant", "systemic"):
            factors.append(f"{cross_border_pattern} cross-border pattern")
        if capacity_exceeded:
            factors.append("national capacity exceeded")
        if sectors_affected > 1:
            factors.append(f"{sectors_affected} sectors affected")
        if financial_impact in ("significant", "severe"):
            factors.append(f"{financial_impact} financial impact")
        if safety_impact in ("health_damage", "death"):
            factors.append(f"{safety_impact} safety impact")
        if affected_persons_count >= 10000:
            factors.append(f"{affected_persons_count} persons affected")
        if affected_entities > 10:
            factors.append(f"{affected_entities} entities affected")
        return factors
