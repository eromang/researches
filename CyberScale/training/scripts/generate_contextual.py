#!/usr/bin/env python3
"""Generate contextual severity training data for CyberScale Phase 2.

Combines CVEs x sectors x cross_border with deterministic NIS2 severity rules
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

EU_MEMBER_STATES = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
]

# Impact field value sets for incident-mode scenarios (Phase B)
SERVICE_IMPACTS = ["none", "partial", "degraded", "unavailable", "sustained"]
DATA_IMPACTS = ["none", "accessed", "exfiltrated", "compromised", "systemic"]
FINANCIAL_IMPACTS = ["none", "minor", "significant", "severe"]
SAFETY_IMPACTS = ["none", "health_risk", "health_damage", "death"]
PERSONS_COUNT_RANGE = [0, 0, 10, 100, 1000, 10000, 100000]
DURATION_HOURS_RANGE = [0, 1, 4, 12, 24, 72, 168]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_entity_types(reference_path: Path) -> dict[str, list[dict]]:
    """Load NIS2 entity types and build sector -> entity_type mapping."""
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
    incident_ratio: float = 0.3,
) -> list[dict]:
    """Generate contextual severity scenarios for all CVEs."""
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
        non_triggered_pool = [s for s in nis2_sectors if s not in triggered_sectors]
        n_non_triggered = max(1, int(len(triggered_sectors) * non_trigger_ratio))
        if non_triggered_pool:
            non_triggered_sectors = rng.sample(
                non_triggered_pool, min(n_non_triggered, len(non_triggered_pool))
            )
        else:
            non_triggered_sectors = []

        # --- Build candidate scenarios ---
        candidates: list[tuple[str, bool, bool]] = []

        for sector_id in triggered_sectors:
            candidates.append((sector_id, False, True))
            candidates.append((sector_id, True, True))

        for sector_id in non_triggered_sectors:
            candidates.append((sector_id, False, False))
            candidates.append((sector_id, True, False))

        candidates.append(("non_nis2", False, False))
        candidates.append(("non_nis2", True, False))

        if len(candidates) > max_scenarios_per_cve:
            candidates = rng.sample(candidates, max_scenarios_per_cve)

        for sector_id, cross_border, is_triggered in candidates:
            sector_cfg = escalation_cfg[sector_id]
            sector_esc = parse_escalation(sector_cfg["escalation"])

            ctx_sev = base_sev

            if is_triggered:
                ctx_sev = escalate(ctx_sev, sector_esc)

            if cross_border and rng.random() < cross_border_escalation_prob:
                ctx_sev = escalate(ctx_sev, cross_border_esc)

            # Select entity type constrained to sector
            if sector_entity_map:
                sector_entities = sector_entity_map.get(sector_id, [])
                if sector_entities:
                    entity_info = rng.choice(sector_entities)
                    entity_type = entity_info["id"]
                    cer_critical_entity = entity_info["cer_eligible"] and rng.random() < 0.1
                else:
                    entity_type = "generic_enterprise"
                    cer_critical_entity = False
            else:
                entity_type = "generic_enterprise"
                cer_critical_entity = False

            # CER critical entity escalation: treated as essential
            if cer_critical_entity and sector_id not in ["non_nis2"]:
                ctx_sev = escalate(ctx_sev, 1)

            # Generate MS geography
            ms_established = rng.choice(EU_MEMBER_STATES)
            if cross_border:
                n_ms = rng.randint(1, 5)
                ms_pool = [ms for ms in EU_MEMBER_STATES if ms != ms_established]
                ms_affected_list = rng.sample(ms_pool, min(n_ms, len(ms_pool)))
            else:
                ms_affected_list = []

            cross_border_str = "true" if cross_border else "false"
            input_text = (
                f"{desc} [SEP] sector: {sector_id} "
                f"cross_border: {cross_border_str} "
                f"ms_established: {ms_established}"
            )
            if ms_affected_list:
                input_text += f" ms_affected: {','.join(ms_affected_list)}"
            input_text += f" score: {score} entity_type: {entity_type}"
            if cer_critical_entity:
                input_text += " cer_critical_entity: true"

            # Incident-mode: add impact fields for a fraction of scenarios
            is_incident = rng.random() < incident_ratio
            impact_fields = {}
            if is_incident:
                impact_fields = generate_impact_scenario(rng, sector_id)
                ctx_sev = impact_escalation(ctx_sev, impact_fields)
                input_text += " " + format_impact_fields(impact_fields)

            label = SEVERITY_INDEX[ctx_sev]

            rows.append(
                {
                    "cve_id": cve["cve_id"],
                    "input_text": input_text,
                    "sector": sector_id,
                    "cross_border": cross_border,
                    "ms_established": ms_established,
                    "ms_affected": ",".join(ms_affected_list) if ms_affected_list else "",
                    "cvss_score": score,
                    "base_severity": base_sev,
                    "contextual_severity": ctx_sev,
                    "label": label,
                    "entity_type": entity_type,
                    "cer_critical_entity": cer_critical_entity,
                    "entity_affected": is_incident,
                }
            )

    return rows


def impact_escalation(base_severity: str, impact_fields: dict) -> str:
    """Determine additional escalation from incident impact fields.

    Escalation rules:
    - unavailable/sustained service_impact: +1
    - exfiltrated/compromised/systemic data_impact: +1
    - significant/severe financial_impact: +1 (only if not already escalated by service/data)
    - health_damage/death safety_impact: +1
    - affected_persons >= 10000: +1
    - suspected_malicious + duration >= 24h: +1
    Capped at +2 total impact escalation.
    """
    steps = 0
    si = impact_fields.get("service_impact", "none")
    di = impact_fields.get("data_impact", "none")
    fi = impact_fields.get("financial_impact", "none")
    sa = impact_fields.get("safety_impact", "none")
    persons = impact_fields.get("affected_persons_count", 0)
    malicious = impact_fields.get("suspected_malicious", False)
    duration = impact_fields.get("impact_duration_hours", 0)

    if si in ("unavailable", "sustained"):
        steps += 1
    if di in ("exfiltrated", "compromised", "systemic"):
        steps += 1
    if sa in ("health_damage", "death"):
        steps += 1
    if persons >= 10000:
        steps += 1
    if malicious and duration >= 24:
        steps += 1

    steps = min(steps, 2)
    return escalate(base_severity, steps)


def generate_impact_scenario(rng: random.Random, sector_id: str) -> dict:
    """Generate random impact fields for an incident-mode scenario."""
    # Weight toward lower severity for balance
    si = rng.choice(SERVICE_IMPACTS)
    di = rng.choice(DATA_IMPACTS)
    fi = rng.choice(FINANCIAL_IMPACTS)
    # Safety impact only for health/transport/energy sectors
    if sector_id in ("health", "transport", "energy", "drinking_water", "food", "chemicals"):
        sa = rng.choice(SAFETY_IMPACTS)
    else:
        sa = rng.choice(["none", "none", "none", "health_risk"])
    persons = rng.choice(PERSONS_COUNT_RANGE)
    malicious = rng.random() < 0.4
    duration = rng.choice(DURATION_HOURS_RANGE)

    return {
        "service_impact": si,
        "data_impact": di,
        "financial_impact": fi,
        "safety_impact": sa,
        "affected_persons_count": persons,
        "suspected_malicious": malicious,
        "impact_duration_hours": duration,
    }


def format_impact_fields(fields: dict) -> str:
    """Format impact fields as text tokens for the model input."""
    parts = ["entity_affected: true"]
    if fields["service_impact"] != "none":
        parts.append(f"service_impact: {fields['service_impact']}")
    if fields["data_impact"] != "none":
        parts.append(f"data_impact: {fields['data_impact']}")
    if fields["financial_impact"] != "none":
        parts.append(f"financial_impact: {fields['financial_impact']}")
    if fields["safety_impact"] != "none":
        parts.append(f"safety_impact: {fields['safety_impact']}")
    if fields["affected_persons_count"] > 0:
        parts.append(f"affected_persons: {fields['affected_persons_count']}")
    if fields["suspected_malicious"]:
        parts.append("suspected_malicious: true")
    if fields["impact_duration_hours"] > 0:
        parts.append(f"duration_hours: {fields['impact_duration_hours']}")
    return " ".join(parts)


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
        "ms_established",
        "ms_affected",
        "cvss_score",
        "base_severity",
        "contextual_severity",
        "label",
        "entity_type",
        "cer_critical_entity",
        "entity_affected",
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
