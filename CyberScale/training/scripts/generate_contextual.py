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

DEPLOYMENT_SCALES = ["individual", "small_business", "enterprise", "critical_operator"]
ENTITY_TYPES = ["individual", "sme", "msp", "hospital", "cloud_provider", "utility", "government", "bank"]

SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_INDEX = {name: idx for idx, name in enumerate(SEVERITY_LEVELS)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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

            # Format input text
            deployment_scale = rng.choice(DEPLOYMENT_SCALES)
            entity_type = rng.choice(ENTITY_TYPES)

            input_text = (
                f"{desc} [SEP] sector: {sector_id} "
                f"cross_border: {str(cross_border).lower()} "
                f"score: {score} "
                f"deployment_scale: {deployment_scale} "
                f"entity_type: {entity_type}"
            )

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
                    "deployment_scale": deployment_scale,
                    "entity_type": entity_type,
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
        "deployment_scale",
        "entity_type",
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
