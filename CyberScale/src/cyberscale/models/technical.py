"""Phase 3 -- Technical severity classifier (T1-T4).

Assesses observable technical impact from a CSIRT perspective.
Uses structured incident fields encoded as all-as-text input.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_CASCADING = {"none", "limited", "cross_sector", "uncontrolled"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}

T_LABEL_MAP = {0: "T1", 1: "T2", 2: "T3", 3: "T4"}


@dataclass
class TechnicalResult:
    """Result of a T-level classification."""

    level: str        # T1 / T2 / T3 / T4
    confidence: str   # high / medium / low
    key_factors: list[str]

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "confidence": self.confidence,
            "key_factors": self.key_factors,
        }


class TechnicalClassifier:
    """ModernBERT classifier for technical incident severity (T1-T4)."""

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
        service_impact: str = "partial",
        affected_entities: int = 1,
        sectors_affected: int = 1,
        cascading: str = "none",
        data_impact: str = "none",
    ) -> str:
        """Format input fields as all-as-text for the model."""
        return (
            f"{description} [SEP] "
            f"service_impact: {service_impact} "
            f"entities: {affected_entities} "
            f"sectors: {sectors_affected} "
            f"cascading: {cascading} "
            f"data_impact: {data_impact}"
        )

    def predict(
        self,
        description: str,
        service_impact: str = "partial",
        affected_entities: int = 1,
        sectors_affected: int = 1,
        cascading: str = "none",
        data_impact: str = "none",
    ) -> TechnicalResult:
        """Classify incident technical severity with MC dropout."""
        text = self.format_input(
            description, service_impact, affected_entities,
            sectors_affected, cascading, data_impact,
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
        level = T_LABEL_MAP[mean_probs.index(max(mean_probs))]
        max_prob = max(mean_probs)
        confidence = "high" if max_prob > 0.7 else "medium" if max_prob > 0.4 else "low"

        key_factors = self._extract_key_factors(
            service_impact, affected_entities, sectors_affected,
            cascading, data_impact,
        )

        return TechnicalResult(level=level, confidence=confidence, key_factors=key_factors)

    def _enable_dropout(self) -> None:
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()

    @staticmethod
    def _extract_key_factors(
        service_impact: str,
        affected_entities: int,
        sectors_affected: int,
        cascading: str,
        data_impact: str,
    ) -> list[str]:
        """Extract human-readable key factors from structured fields."""
        factors = []
        if service_impact in ("unavailable", "sustained"):
            factors.append(f"{service_impact} service impact")
        if affected_entities > 10:
            factors.append(f"{affected_entities} entities affected")
        if sectors_affected > 1:
            factors.append(f"{sectors_affected} sectors affected")
        if cascading in ("cross_sector", "uncontrolled"):
            factors.append(f"{cascading} cascading")
        if data_impact in ("exfiltrated", "systemic"):
            factors.append(f"{data_impact} data impact")
        return factors
