"""Phase 1 -- Vulnerability severity scorer (4-class classification with confidence).

Loads a fine-tuned ModernBERT model with a 4-class classification head.
Provides Monte Carlo dropout for confidence estimation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


@dataclass
class ScorerResult:
    """Result of a severity scoring prediction."""

    score: float       # 0-10
    confidence: str    # high / medium / low
    band: str          # Critical / High / Medium / Low

    def to_dict(self) -> dict:
        return {"score": self.score, "confidence": self.confidence, "band": self.band}


class SeverityScorer:
    """ModernBERT classification model for vulnerability severity scoring."""

    LABEL_MAP = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
    BAND_CENTRES = {"Low": 2.0, "Medium": 5.5, "High": 8.0, "Critical": 9.5}
    CONFIDENCE_THRESHOLDS = {"high": 0.3, "medium": 1.0}

    def __init__(
        self,
        model_path: str | Path,
        mc_passes: int = 5,
        max_length: int = 192,
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

    def predict(self, description: str, cwe: Optional[str] = None) -> ScorerResult:
        """Score a vulnerability description with MC dropout confidence."""
        text = self._format_input(description, cwe=cwe)
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
        mean_probs = [sum(p[i] for p in all_probs) / len(all_probs) for i in range(4)]

        band = self.probs_to_band(mean_probs)
        score = self.probs_to_score(mean_probs)
        confidence = self.max_prob_to_confidence(max(mean_probs))

        return ScorerResult(score=round(score, 1), confidence=confidence, band=band)

    def _format_input(self, description: str, cwe: Optional[str] = None) -> str:
        """Format input text for the model."""
        if cwe:
            return f"{description} [SEP] cwe: {cwe}"
        return description

    def _enable_dropout(self) -> None:
        """Enable dropout layers for MC dropout at inference time."""
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()

    @staticmethod
    def probs_to_band(probs: list[float]) -> str:
        """Map class probabilities to a severity band via argmax."""
        idx = probs.index(max(probs))
        return SeverityScorer.LABEL_MAP[idx]

    @staticmethod
    def probs_to_score(probs: list[float]) -> float:
        """Compute weighted sum of band centres from class probabilities."""
        centres = [
            SeverityScorer.BAND_CENTRES[SeverityScorer.LABEL_MAP[i]]
            for i in range(4)
        ]
        return sum(p * c for p, c in zip(probs, centres))

    @staticmethod
    def max_prob_to_confidence(max_prob: float) -> str:
        """Map maximum class probability to a confidence label."""
        if max_prob > 0.7:
            return "high"
        if max_prob > 0.4:
            return "medium"
        return "low"

    @staticmethod
    def score_to_band(score: float) -> str:
        """Map a numeric score to a severity band."""
        if score >= 9.0:
            return "Critical"
        if score >= 7.0:
            return "High"
        if score >= 4.0:
            return "Medium"
        return "Low"

    @staticmethod
    def variance_to_confidence(variance: float) -> str:
        """Map MC dropout variance to a confidence label (backward compat)."""
        if variance < SeverityScorer.CONFIDENCE_THRESHOLDS["high"]:
            return "high"
        if variance < SeverityScorer.CONFIDENCE_THRESHOLDS["medium"]:
            return "medium"
        return "low"
