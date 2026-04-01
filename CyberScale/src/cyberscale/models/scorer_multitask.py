"""Phase 6 -- Multi-task vulnerability severity scorer.

Wraps a shared ModernBERT encoder with a primary band classification head
and eight auxiliary CVSS component heads.  Supports MC dropout inference
and checkpoint save/load via state_dict + JSON config.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class MultiTaskScorerResult:
    """Result of a multi-task severity scoring prediction."""

    score: float              # 0-10
    confidence: str           # high / medium / low
    band: str                 # Critical / High / Medium / Low
    predicted_vector: dict    # {"av": "N", "ac": "L", ...}

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Default component configs
# ---------------------------------------------------------------------------

DEFAULT_COMPONENT_CONFIGS: dict[str, dict] = {
    "av": {"num_labels": 4},    # N / A / L / P
    "ac": {"num_labels": 2},    # L / H
    "pr": {"num_labels": 3},    # N / L / H
    "ui": {"num_labels": 2},    # N / R
    "scope": {"num_labels": 2}, # U / C
    "conf": {"num_labels": 3},  # N / L / H
    "integ": {"num_labels": 3}, # N / L / H
    "avail": {"num_labels": 3}, # N / L / H
}

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class MultiTaskScorer(nn.Module):
    """ModernBERT encoder with a band head and eight CVSS component heads."""

    COMPONENT_LABEL_MAPS: dict[str, dict[str, int]] = {
        "av": {"N": 0, "A": 1, "L": 2, "P": 3},
        "ac": {"L": 0, "H": 1},
        "pr": {"N": 0, "L": 1, "H": 2},
        "ui": {"N": 0, "R": 1},
        "scope": {"U": 0, "C": 1},
        "conf": {"N": 0, "L": 1, "H": 2},
        "integ": {"N": 0, "L": 1, "H": 2},
        "avail": {"N": 0, "L": 1, "H": 2},
    }

    REVERSE_LABEL_MAPS: dict[str, dict[int, str]] = {
        comp: {v: k for k, v in mapping.items()}
        for comp, mapping in COMPONENT_LABEL_MAPS.items()
    }

    def __init__(
        self,
        base_model: str = "answerdotai/ModernBERT-base",
        num_band_labels: int = 4,
        component_configs: Optional[dict[str, dict]] = None,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.base_model = base_model
        self.num_band_labels = num_band_labels
        self.component_configs = component_configs or DEFAULT_COMPONENT_CONFIGS
        self.dropout_rate = dropout

        # Shared encoder
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size  # 768 for base

        self.dropout = nn.Dropout(dropout)

        # Band head (primary) -- 2-layer MLP with ReLU
        self.band_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_band_labels),
        )

        # 8 component heads (auxiliary) -- single linear layer each
        self.component_heads = nn.ModuleDict(
            {
                name: nn.Linear(hidden_size, cfg["num_labels"])
                for name, cfg in self.component_configs.items()
            }
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        """Return ``(band_logits, component_logits_dict)``."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # Use [CLS] token representation (first token)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)

        band_logits = self.band_head(cls_output)
        component_logits = {
            name: head(cls_output)
            for name, head in self.component_heads.items()
        }
        return band_logits, component_logits

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def get_config(self) -> dict:
        """Return a JSON-serialisable config dict."""
        return {
            "base_model": self.base_model,
            "num_band_labels": self.num_band_labels,
            "component_configs": self.component_configs,
            "dropout": self.dropout_rate,
        }

    def save_pretrained(self, path: str | Path) -> None:
        """Save model state_dict and config JSON to *path*."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path / "model.pt")
        (path / "config.json").write_text(json.dumps(self.get_config(), indent=2))

    @classmethod
    def from_pretrained(cls, path: str | Path) -> MultiTaskScorer:
        """Load a saved checkpoint from *path*."""
        path = Path(path)
        config = json.loads((path / "config.json").read_text())
        model = cls(
            base_model=config["base_model"],
            num_band_labels=config["num_band_labels"],
            component_configs=config["component_configs"],
            dropout=config["dropout"],
        )
        state = torch.load(path / "model.pt", map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        return model


# ---------------------------------------------------------------------------
# Inference wrapper (mirrors SeverityScorer API)
# ---------------------------------------------------------------------------


class MultiTaskSeverityScorer:
    """Inference wrapper around :class:`MultiTaskScorer`.

    Loads a saved checkpoint and provides MC-dropout prediction that returns
    both the band prediction and decoded CVSS vector components.
    """

    LABEL_MAP = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
    BAND_CENTRES = {"Low": 2.0, "Medium": 5.5, "High": 8.0, "Critical": 9.5}

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

        self.model = MultiTaskScorer.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model.base_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(
        self,
        description: str,
        cwe: Optional[str] = None,
        vendor: Optional[str] = None,
        product: Optional[str] = None,
    ) -> MultiTaskScorerResult:
        """Score a vulnerability description with MC dropout confidence."""
        text = self._format_input(description, cwe=cwe, vendor=vendor, product=product)
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # MC dropout passes
        self._enable_dropout()
        all_band_probs: list[list[float]] = []
        all_comp_probs: dict[str, list[list[float]]] = {
            name: [] for name in self.model.component_heads
        }

        with torch.no_grad():
            for _ in range(self.mc_passes):
                band_logits, comp_logits = self.model(
                    inputs["input_ids"], inputs["attention_mask"]
                )
                band_probs = (
                    torch.softmax(band_logits, dim=-1).squeeze(0).cpu().tolist()
                )
                all_band_probs.append(band_probs)
                for name, logits in comp_logits.items():
                    probs = (
                        torch.softmax(logits, dim=-1).squeeze(0).cpu().tolist()
                    )
                    all_comp_probs[name].append(probs)
        self.model.eval()

        # Average band probabilities
        num_bands = len(all_band_probs[0])
        mean_band_probs = [
            sum(p[i] for p in all_band_probs) / len(all_band_probs)
            for i in range(num_bands)
        ]

        band = self.probs_to_band(mean_band_probs)
        score = self.probs_to_score(mean_band_probs)
        confidence = self.max_prob_to_confidence(max(mean_band_probs))

        # Decode component predictions
        predicted_vector = self._decode_components(all_comp_probs)

        return MultiTaskScorerResult(
            score=round(score, 1),
            confidence=confidence,
            band=band,
            predicted_vector=predicted_vector,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_input(
        self,
        description: str,
        cwe: Optional[str] = None,
        vendor: Optional[str] = None,
        product: Optional[str] = None,
    ) -> str:
        suffixes = []
        if cwe:
            suffixes.append(f"cwe: {cwe}")
        if vendor:
            suffixes.append(f"vendor: {vendor}")
        if product:
            suffixes.append(f"product: {product}")
        if suffixes:
            return f"{description} [SEP] {' '.join(suffixes)}"
        return description

    def _enable_dropout(self) -> None:
        """Enable dropout layers for MC dropout at inference time."""
        for module in self.model.modules():
            if isinstance(module, nn.Dropout):
                module.train()

    def _decode_components(
        self,
        all_comp_probs: dict[str, list[list[float]]],
    ) -> dict[str, str]:
        """Average component probs across MC passes and argmax-decode."""
        result: dict[str, str] = {}
        for name, passes in all_comp_probs.items():
            num_labels = len(passes[0])
            mean_probs = [
                sum(p[i] for p in passes) / len(passes) for i in range(num_labels)
            ]
            idx = mean_probs.index(max(mean_probs))
            result[name] = MultiTaskScorer.REVERSE_LABEL_MAPS[name][idx]
        return result

    # ------------------------------------------------------------------
    # Static scoring helpers (same as SeverityScorer)
    # ------------------------------------------------------------------

    @staticmethod
    def probs_to_band(probs: list[float]) -> str:
        idx = probs.index(max(probs))
        return MultiTaskSeverityScorer.LABEL_MAP[idx]

    @staticmethod
    def probs_to_score(probs: list[float]) -> float:
        centres = [
            MultiTaskSeverityScorer.BAND_CENTRES[
                MultiTaskSeverityScorer.LABEL_MAP[i]
            ]
            for i in range(len(probs))
        ]
        return sum(p * c for p, c in zip(probs, centres))

    @staticmethod
    def max_prob_to_confidence(max_prob: float) -> str:
        if max_prob > 0.7:
            return "high"
        if max_prob > 0.4:
            return "medium"
        return "low"

    @staticmethod
    def score_to_band(score: float) -> str:
        if score >= 9.0:
            return "Critical"
        if score >= 7.0:
            return "High"
        if score >= 4.0:
            return "Medium"
        return "Low"
