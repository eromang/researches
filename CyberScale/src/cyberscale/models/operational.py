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
VALID_COORDINATION = {"national", "eu_info", "eu_active", "full_ipcr"}

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
        mc_passes: int = 20,
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
        sectors_affected: str = "",
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        coordination_needs: str = "national",
        capacity_exceeded: bool = False,
    ) -> str:
        """Format input fields as all-as-text for the model."""
        return (
            f"{description} [SEP] "
            f"sectors: {sectors_affected} "
            f"relevance: {entity_relevance} "
            f"ms_affected: {ms_affected} "
            f"cross_border: {cross_border_pattern} "
            f"coordination: {coordination_needs} "
            f"capacity_exceeded: {str(capacity_exceeded).lower()}"
        )

    def predict(
        self,
        description: str,
        sectors_affected: str = "",
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        coordination_needs: str = "national",
        capacity_exceeded: bool = False,
    ) -> OperationalResult:
        """Classify incident operational severity with MC dropout."""
        text = self.format_input(
            description, sectors_affected, entity_relevance,
            ms_affected, cross_border_pattern, coordination_needs,
            capacity_exceeded,
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
            cross_border_pattern, coordination_needs, capacity_exceeded,
        )

        return OperationalResult(level=level, confidence=confidence, key_factors=key_factors)

    def _enable_dropout(self) -> None:
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()

    @staticmethod
    def _extract_key_factors(
        sectors_affected: str,
        entity_relevance: str,
        ms_affected: int,
        cross_border_pattern: str,
        coordination_needs: str,
        capacity_exceeded: bool,
    ) -> list[str]:
        """Extract human-readable key factors from structured fields."""
        factors = []
        if entity_relevance in ("high_relevance", "systemic"):
            factors.append(f"{entity_relevance} entity")
        if ms_affected > 2:
            factors.append(f"{ms_affected} member states affected")
        if cross_border_pattern in ("significant", "systemic"):
            factors.append(f"{cross_border_pattern} cross-border pattern")
        if coordination_needs in ("eu_active", "full_ipcr"):
            factors.append(f"{coordination_needs} coordination")
        if capacity_exceeded:
            factors.append("national capacity exceeded")
        n_sectors = len([s for s in sectors_affected.split(",") if s.strip()])
        if n_sectors > 1:
            factors.append(f"{n_sectors} sectors affected")
        return factors
