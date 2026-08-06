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
        # Contextual de-escalation (docs/de-escalation-rules.md, backlog D14)
        deployment_context: Optional[str] = None,
        apply_de_escalation: bool = False,
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

        # Deterministic de-escalation, applied to the model's output and never
        # to its input: the deployed weights were trained on a corpus with no
        # deployment context, so feeding one into the token stream would be
        # out-of-distribution input a model cannot use. Off by default — it
        # changes the answer for every out-of-scope entity, and every figure
        # measured so far sits between 34 % and 49 % on four classes, which is
        # an improvement over the model and not a working system.
        de_escalated = 0
        if apply_de_escalation:
            de_escalated = self._de_escalation_steps(
                sector=sector, entity_type=entity_type,
                deployment_context=deployment_context)
            if de_escalated:
                severity = self._apply_de_escalation(severity, de_escalated)
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

        # A downgrade in a regulatory tool must say so. Never silent.
        if de_escalated:
            key_factors.append(
                f"contextual de-escalation: -{de_escalated} level(s) "
                "(NIS2 scope / non-essential deployment, "
                "see docs/de-escalation-rules.md)")

        return ContextualResult(
            severity=severity, confidence=confidence, key_factors=key_factors
        )

    # ------------------------------------------------------------------
    # Contextual de-escalation (docs/de-escalation-rules.md)
    # ------------------------------------------------------------------

    # Wording taken from the expert's own threshold_matched formulas in the
    # external validation set. Each marks a deployment that is not the entity's
    # essential service. Share of scenarios containing the term that the expert
    # down-graded: home 96.6 %, personal 91.1 %, single 89.2 %,
    # workstations 71.2 %, office 70.0 %, department 75.9 %.
    _NON_ESSENTIAL_TERMS = (
        "home", "personal", "single user", "single-user", "single ",
        "workstation", "desktop", "laptop", "office", "employee",
        "department", "individual", "consumer",
    )

    @staticmethod
    def _entity_annex(entity_type: Optional[str]) -> Optional[str]:
        """Annex of a canonical entity type, or None when it carries none."""
        import json
        from cyberscale.config import _REF_DIR

        path = _REF_DIR / "nis2_entity_types.json"
        if not path.exists():
            # Never guess scope from a file we could not read: returning None
            # here would silently de-escalate every entity.
            raise FileNotFoundError(
                f"{path} missing — cannot establish NIS2 scope, and guessing it "
                "would lower severity for entities that are in scope")
        data = json.loads(path.read_text())
        for et in data["entity_types"]:
            if et["id"] == entity_type:
                return et.get("annex")
        return None

    def _de_escalation_steps(
        self,
        *,
        sector: Optional[str],
        entity_type: Optional[str],
        deployment_context: Optional[str],
    ) -> int:
        """Levels to lower, 0-2. See docs/de-escalation-rules.md for derivation.

        R1 — outside NIS2 Annex I/II: no notification obligation, so regulatory
             severity cannot stand at the technical one.
        R2 — the affected system is not the essential service: a desktop, office
             tool or single-user install cannot meet the significant-incident
             threshold whatever the CVSS score.

        Capped at 2; the expert lowered by 3 in only 20 of 378 cases.
        """
        steps = 0
        if sector == "non_nis2" or (
            entity_type is not None and self._entity_annex(entity_type) is None
        ):
            steps += 1
        if deployment_context:
            ctx = deployment_context.lower()
            if any(t in ctx for t in self._NON_ESSENTIAL_TERMS):
                steps += 1
        return min(steps, 2)

    @staticmethod
    def _apply_de_escalation(severity: str, steps: int) -> str:
        order = ["Low", "Medium", "High", "Critical"]
        return order[max(order.index(severity) - steps, 0)]

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
