#!/usr/bin/env python3
"""Generate parametric incident training data for CyberScale Phase 3.

Produces balanced T-level and O-level classification datasets by:
1. Enumerating all valid combinations of structured incident fields
2. Applying deterministic T/O-level assignment rules
3. Generating parametrized description text with paraphrase variants
4. Balancing classes to target_per_class via undersampling

Critical design choice: includes non-trigger scenarios where structured
fields suggest escalation but the description is mundane, and vice versa.
This prevents the model from learning spurious field-to-label shortcuts.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
from collections import Counter
from functools import partial
from pathlib import Path

print = partial(print, flush=True)

# ---------------------------------------------------------------------------
# Structured field value sets
# ---------------------------------------------------------------------------

SERVICE_IMPACTS = ["none", "partial", "degraded", "unavailable", "sustained"]
CASCADING = ["none", "limited", "cross_sector", "uncontrolled"]
DATA_IMPACTS = ["none", "accessed", "exfiltrated", "compromised", "systemic"]
ENTITIES_RANGE = [1, 1, 2, 2, 3, 3, 5, 8, 10, 12, 25, 55, 150]

ENTITY_RELEVANCE = ["non_essential", "essential", "high_relevance", "systemic"]
CROSS_BORDER = ["none", "limited", "significant", "systemic"]
MS_AFFECTED_RANGE = [1, 1, 1, 1, 1, 2, 3, 5, 8]  # Weight toward 1 MS for O1 coverage
CAPACITY_EXCEEDED = [False, True]
FINANCIAL_IMPACTS = ["none", "none", "minor", "significant", "severe"]
SAFETY_IMPACTS = ["none", "none", "none", "health_risk", "health_damage", "death"]
PERSONS_COUNT_RANGE = [0, 0, 0, 100, 1000, 10000, 100000]
O_ENTITIES_RANGE = [1, 1, 2, 3, 5, 10, 25, 50]

SECTORS = [
    "energy", "transport", "banking", "financial_market",
    "health", "drinking_water", "waste_water", "digital_infrastructure",
    "ict_service_management", "public_administration", "space",
    "postal_courier", "waste_management", "chemicals",
    "food_production", "manufacturing", "digital_providers",
    "research", "education",
]

SECTORS_AFFECTED_RANGE = [1, 1, 1, 1, 2, 2, 3, 5]  # Weight toward 1-2 for T1/O1 coverage

# ---------------------------------------------------------------------------
# Description templates (50 base templates)
# ---------------------------------------------------------------------------

BASE_TEMPLATES = [
    "Ransomware attack on {sector} provider causing {disruption} disruption to core services affecting {entities} entities across {n_sectors} sectors.",
    "DDoS campaign targeting {sector} infrastructure resulting in {disruption} service degradation for {entities} downstream organizations.",
    "Supply chain compromise through {sector} software vendor leading to {data_comp} data exposure across {entities} client organizations.",
    "Phishing campaign against {sector} operators with {data_comp} credential theft impacting {entities} entities.",
    "Advanced persistent threat targeting {sector} networks with {cascading} cascading effects across {n_sectors} sectors.",
    "Zero-day exploitation in {sector} control systems causing {disruption} operational disruption.",
    "Insider threat at {sector} facility resulting in {data_comp} data compromise affecting {entities} connected entities.",
    "Wiper malware deployed against {sector} systems causing {disruption} destruction of operational data.",
    "Man-in-the-middle attack intercepting {sector} communications with {data_comp} data exposure.",
    "Brute force attack on {sector} authentication systems leading to {disruption} access disruption for {entities} users.",
    "SQL injection against {sector} databases resulting in {data_comp} data breach across {entities} records systems.",
    "Firmware tampering in {sector} IoT devices causing {cascading} cascading failures in {n_sectors} sectors.",
    "Watering hole attack targeting {sector} personnel websites with {data_comp} credential harvesting.",
    "DNS hijacking affecting {sector} domain resolution causing {disruption} service disruption for {entities} organizations.",
    "BGP route leak impacting {sector} network connectivity with {disruption} disruption across {n_sectors} sectors.",
    "Cryptojacking malware on {sector} cloud infrastructure causing {disruption} performance degradation.",
    "Social engineering attack on {sector} help desk leading to {data_comp} data access for {entities} accounts.",
    "Vulnerability in {sector} VPN gateway exploited for {data_comp} data exfiltration from {entities} endpoints.",
    "Privilege escalation in {sector} active directory causing {cascading} lateral movement across {n_sectors} network segments.",
    "Botnet infection across {sector} endpoints with {disruption} service degradation affecting {entities} sites.",
    "Business email compromise targeting {sector} financial operations with {data_comp} transaction data exposure.",
    "Malicious update pushed to {sector} monitoring software affecting {entities} installations with {cascading} cascading impact.",
    "Credential stuffing attack on {sector} customer portals resulting in {data_comp} account compromise for {entities} users.",
    "API abuse targeting {sector} cloud services causing {disruption} rate limiting and outages.",
    "Configuration error in {sector} firewall rules exposing {data_comp} data to unauthorized access.",
    "Certificate authority compromise affecting {sector} trust chains with {cascading} cascading trust failures across {n_sectors} domains.",
    "Typosquatting campaign targeting {sector} supply chain with trojanized packages affecting {entities} developers.",
    "Memory corruption exploit in {sector} SCADA systems causing {disruption} process control disruption.",
    "Data poisoning attack on {sector} machine learning models with {data_comp} integrity compromise.",
    "SIM swapping attack targeting {sector} executives leading to {data_comp} two-factor bypass for {entities} accounts.",
    "Container escape in {sector} Kubernetes clusters causing {cascading} lateral movement across {n_sectors} namespaces.",
    "Power grid cyber-physical attack on {sector} SCADA causing {disruption} disruption with {cascading} cascading effects.",
    "Bluetooth vulnerability exploited in {sector} medical devices affecting {entities} hospital systems.",
    "Satellite communication jamming targeting {sector} ground stations causing {disruption} connectivity loss.",
    "Ransomware-as-a-service targeting {sector} SMEs causing {disruption} disruption across {entities} businesses.",
    "Cloud misconfiguration exposing {sector} storage buckets with {data_comp} data of {entities} customers.",
    "USB-based malware introduced into {sector} air-gapped systems causing {data_comp} data bridge.",
    "Deepfake-assisted social engineering targeting {sector} leadership with {data_comp} access to {entities} strategic systems.",
    "SSH key compromise in {sector} jump servers enabling {cascading} lateral access across {n_sectors} network zones.",
    "Log4j-style vulnerability in {sector} Java applications affecting {entities} instances with {disruption} service impact.",
    "Side-channel attack on {sector} cryptographic hardware with {data_comp} key material exposure.",
    "WebSocket injection in {sector} real-time systems causing {disruption} session disruption for {entities} active connections.",
    "OAuth token theft from {sector} identity providers affecting {entities} federated services.",
    "Hardware implant discovered in {sector} network equipment with {data_comp} persistent surveillance capability.",
    "Automated exploit chain targeting {sector} web applications with {cascading} cascading compromise across {n_sectors} sites.",
    "Operational technology network bridge exploit in {sector} causing {disruption} safety system degradation.",
    "Mass scanning and exploitation campaign against {sector} exposed services affecting {entities} unpatched systems.",
    "Encrypted channel abuse by malware in {sector} networks evading detection with {data_comp} data exfiltration.",
    "GPS spoofing targeting {sector} navigation systems causing {disruption} operational confusion for {entities} vehicles.",
    "Third-party cloud provider outage affecting {sector} hosted services with {disruption} disruption across {n_sectors} dependent sectors.",
]

LOW_SEVERITY_TEMPLATES = [
    "Automated port scan detected on {sector} external-facing web server. No exploitation attempted. Standard reconnaissance activity logged by IDS.",
    "Failed phishing email campaign targeting {sector} employees. All emails caught by spam filter. No credentials compromised. Security awareness team notified.",
    "Routine vulnerability scan found unpatched {sector} test server with {data_comp} exposure risk. Server is isolated from production networks.",
    "Single failed SSH brute force attempt against {sector} bastion host. Account locked after 5 attempts. No successful authentication.",
    "Expired SSL certificate on {sector} internal documentation portal caused browser warnings for {entities} users. No data exposure, certificate renewed within hours.",
    "Minor configuration drift detected in {sector} firewall rules. One non-critical port briefly exposed. No evidence of exploitation. Remediated same day.",
    "Commodity adware found on single {sector} employee workstation during routine scan. No lateral movement. Workstation reimaged per standard procedure.",
    "Low-confidence threat intelligence alert for {sector} IP range. Investigation found no indicators of compromise. Alert classified as false positive.",
    "Unauthorized USB device connected to {sector} workstation. Device contained no malware. Policy violation documented and employee counseled.",
    "Brief DNS resolution delay affecting {sector} internal services for {entities} users. Root cause was upstream provider maintenance, not an attack.",
    "Outdated {sector} web application flagged by automated scanner. Application is public-facing but read-only with no sensitive data.",
    "Test credentials found in {sector} code repository. Credentials were for development environment only with no production access.",
    "Minor defacement of low-traffic {sector} informational website. Content restored from backup within one hour. No data access.",
    "Suspicious login attempt on {sector} VPN from unusual geography. Multi-factor authentication prevented access. User confirmed no compromise.",
    "Scheduled penetration test triggered {sector} IDS alerts. All activity was authorized and within scope. No actual security incident.",
]

# Synonym substitution pools for paraphrasing
SYNONYMS = {
    "attack": ["incident", "breach", "intrusion", "compromise"],
    "targeting": ["affecting", "impacting", "directed at", "hitting"],
    "causing": ["resulting in", "leading to", "producing", "triggering"],
    "impact": ["outage", "degradation", "interruption", "impairment"],
    "affecting": ["impacting", "involving", "touching", "reaching"],
    "organizations": ["entities", "institutions", "operators", "providers"],
    "systems": ["infrastructure", "platforms", "services", "networks"],
    "deployed": ["launched", "executed", "activated", "introduced"],
    "resulting": ["leading", "culminating", "ending", "concluding"],
    "exposure": ["leak", "breach", "disclosure", "compromise"],
}


def _paraphrase(text: str, variant: int, rng: random.Random) -> str:
    """Generate a paraphrase variant via synonym substitution and reordering."""
    words = text.split()
    result = []
    for w in words:
        w_lower = w.lower().rstrip(".,;:")
        punct = w[len(w_lower):] if len(w) > len(w_lower) else ""
        if w_lower in SYNONYMS and rng.random() < 0.3 + variant * 0.1:
            replacement = rng.choice(SYNONYMS[w_lower])
            if w[0].isupper():
                replacement = replacement.capitalize()
            result.append(replacement + punct)
        else:
            result.append(w)
    # For variant 2+, sometimes swap adjacent clause fragments
    if variant >= 2 and " with " in " ".join(result):
        text_out = " ".join(result)
        parts = text_out.split(" with ", 1)
        if len(parts) == 2 and rng.random() < 0.4:
            # Restructure: "X with Y" -> "With Y, X"
            text_out = f"With {parts[1].rstrip('.')}, {parts[0].lower()}."
            return text_out
    return " ".join(result)


def _fill_template(
    template: str,
    sector: str,
    service_impact: str,
    entities: int,
    n_sectors: int,
    cascading: str,
    data_impact: str,
) -> str:
    """Fill a base template with field values."""
    return template.format(
        sector=sector.replace("_", " "),
        disruption=service_impact,
        entities=entities,
        n_sectors=n_sectors,
        cascading=cascading.replace("_", " "),
        data_comp=data_impact.replace("_", " "),
    )


# ---------------------------------------------------------------------------
# T-level assignment (deterministic)
# ---------------------------------------------------------------------------

def assign_t_level(
    service_impact: str,
    data_impact: str,
    cascading: str,
    entities: int,
) -> str:
    """Deterministic T-level based on structured fields."""
    # T4: sustained OR systemic data OR (unavailable + uncontrolled)
    if service_impact == "sustained":
        return "T4"
    if data_impact == "systemic":
        return "T4"
    if service_impact == "unavailable" and cascading == "uncontrolled":
        return "T4"

    # T3: unavailable OR exfiltrated data OR cross_sector cascading OR entities > 50
    if service_impact == "unavailable":
        return "T3"
    if data_impact == "exfiltrated":
        return "T3"
    if cascading == "cross_sector":
        return "T3"
    if entities > 50:
        return "T3"

    # T2: degraded OR accessed data OR compromised data OR limited cascading OR entities > 10
    if service_impact == "degraded":
        return "T2"
    if data_impact == "accessed":
        return "T2"
    if data_impact == "compromised":
        return "T2"
    if cascading == "limited":
        return "T2"
    if entities > 10:
        return "T2"

    # T1: everything else (none, partial service_impact + none data_impact)
    return "T1"


# ---------------------------------------------------------------------------
# O-level assignment (deterministic)
# ---------------------------------------------------------------------------

def assign_o_level(
    cross_border: str,
    capacity_exceeded: bool,
    entity_relevance: str,
    ms_affected: int,
    n_sectors: int,
) -> str:
    """Deterministic O-level based on structured fields.

    coordination_needs was removed in v4 — O-level is derived from
    observable cross-border pattern, entity relevance, and capacity.
    """
    # O4: (systemic cross-border + capacity_exceeded)
    #     OR (systemic entity + 6+ MS)
    #     OR (systemic cross-border + systemic entity)
    if cross_border == "systemic" and capacity_exceeded:
        return "O4"
    if entity_relevance == "systemic" and ms_affected >= 6:
        return "O4"
    if cross_border == "systemic" and entity_relevance == "systemic":
        return "O4"

    # O3: significant cross-border
    #     OR (high_relevance + 3+ MS) OR capacity_exceeded
    #     OR (systemic entity + 3+ MS)
    if cross_border == "significant":
        return "O3"
    if entity_relevance == "high_relevance" and ms_affected >= 3:
        return "O3"
    if capacity_exceeded:
        return "O3"
    if entity_relevance == "systemic" and ms_affected >= 3:
        return "O3"

    # O2: limited cross-border
    #     OR (essential + 2+ MS) OR 3+ sectors
    #     OR (high_relevance + 2+ MS)
    if cross_border == "limited":
        return "O2"
    if entity_relevance == "essential" and ms_affected >= 2:
        return "O2"
    if n_sectors >= 3:
        return "O2"
    if entity_relevance == "high_relevance" and ms_affected >= 2:
        return "O2"

    # O1: everything else
    return "O1"


# ---------------------------------------------------------------------------
# Invalid combination filters
# ---------------------------------------------------------------------------

def is_valid_t_combination(
    service_impact: str,
    cascading: str,
    data_impact: str,
    entities: int,
    n_sectors: int,
) -> bool:
    """Filter obviously inconsistent T-level field combinations."""
    # No cascading but many sectors makes little sense
    if cascading == "none" and n_sectors > 3:
        return False
    # None/partial service impact with uncontrolled cascading is unlikely
    if service_impact in ("none", "partial") and cascading == "uncontrolled":
        return False
    # Single entity with cross-sector or uncontrolled cascading
    if entities == 1 and cascading in ("cross_sector", "uncontrolled"):
        return False
    return True


def is_valid_o_combination(
    ms_affected: int,
    cross_border: str,
    entity_relevance: str,
    n_sectors: int,
) -> bool:
    """Filter invalid O-level field combinations per spec."""
    # non_essential + systemic cross-border -> skip
    if entity_relevance == "non_essential" and cross_border == "systemic":
        return False
    # 1 MS + significant/systemic cross-border -> skip
    if ms_affected == 1 and cross_border in ("significant", "systemic"):
        return False
    return True


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_t_samples(
    target_per_class: int,
    paraphrase_variants: int,
    seed: int,
) -> list[dict]:
    """Generate all T-level training samples."""
    rng = random.Random(seed)
    all_samples: list[dict] = []
    template_count = len(BASE_TEMPLATES)

    # Iterate over a sampled subset of combinations to keep generation tractable
    combos = list(itertools.product(
        SERVICE_IMPACTS, CASCADING, DATA_IMPACTS, ENTITIES_RANGE, SECTORS_AFFECTED_RANGE,
    ))
    rng.shuffle(combos)

    for svc_impact, cascading, data_impact, entities, n_sectors in combos:
        if not is_valid_t_combination(svc_impact, cascading, data_impact, entities, n_sectors):
            continue

        t_level = assign_t_level(svc_impact, data_impact, cascading, entities)
        sector = rng.choice(SECTORS)

        # Pick a template deterministically from combo hash
        # For T1 scenarios, use low-severity templates 50% of the time
        all_templates = BASE_TEMPLATES
        if t_level == "T1" and rng.random() < 0.5:
            all_templates = LOW_SEVERITY_TEMPLATES
        tmpl_idx = hash((svc_impact, cascading, data_impact, entities, n_sectors)) % len(all_templates)
        base_desc = _fill_template(
            all_templates[tmpl_idx], sector, svc_impact, entities, n_sectors, cascading, data_impact,
        )

        # Original + paraphrase variants
        descriptions = [base_desc]
        for v in range(1, paraphrase_variants + 1):
            descriptions.append(_paraphrase(base_desc, v, rng))

        # For T1 scenarios, also emit descriptions from the complementary template set
        # to ensure sufficient raw sample count (T1 combos are naturally sparse)
        if t_level == "T1":
            complement_templates = LOW_SEVERITY_TEMPLATES if all_templates is BASE_TEMPLATES else BASE_TEMPLATES
            c_tmpl_idx = hash((svc_impact, cascading, data_impact, entities, n_sectors, "complement")) % len(complement_templates)
            c_desc = _fill_template(
                complement_templates[c_tmpl_idx], sector, svc_impact, entities, n_sectors, cascading, data_impact,
            )
            descriptions.append(c_desc)
            for v in range(1, paraphrase_variants + 1):
                descriptions.append(_paraphrase(c_desc, v, rng))

        for desc in descriptions:
            text = (
                f"{desc} [SEP] "
                f"service_impact: {svc_impact} "
                f"entities: {entities} "
                f"sectors: {n_sectors} "
                f"cascading: {cascading} "
                f"data_impact: {data_impact}"
            )
            all_samples.append({"text": text, "label": t_level})

    return all_samples


def generate_o_samples(
    target_per_class: int,
    paraphrase_variants: int,
    seed: int,
) -> list[dict]:
    """Generate all O-level training samples."""
    rng = random.Random(seed + 1)  # Different seed for variety
    all_samples: list[dict] = []
    template_count = len(BASE_TEMPLATES)

    combos = list(itertools.product(
        ENTITY_RELEVANCE, CROSS_BORDER,
        MS_AFFECTED_RANGE, CAPACITY_EXCEEDED, SECTORS_AFFECTED_RANGE,
    ))
    rng.shuffle(combos)

    for relevance, cross_border, ms_affected, cap_exceeded, n_sectors in combos:
        if not is_valid_o_combination(ms_affected, cross_border, relevance, n_sectors):
            continue

        o_level = assign_o_level(
            cross_border, cap_exceeded, relevance, ms_affected, n_sectors,
        )

        sector = rng.choice(SECTORS)

        # Pick template
        tmpl_idx = hash((relevance, cross_border, ms_affected, cap_exceeded)) % template_count
        # Use a generic service_impact/entities for the description (non-trigger scenarios)
        svc_impact_word = rng.choice(["partial", "degraded", "unavailable", "sustained"])
        entities_count = rng.choice([1, 5, 12, 25, 55])
        cascading_word = rng.choice(["none", "limited", "cross sector"])
        data_impact_word = rng.choice(["none", "accessed", "exfiltrated"])

        base_desc = _fill_template(
            BASE_TEMPLATES[tmpl_idx],
            sector, svc_impact_word, entities_count, n_sectors, cascading_word, data_impact_word,
        )

        descriptions = [base_desc]
        for v in range(1, paraphrase_variants + 1):
            descriptions.append(_paraphrase(base_desc, v, rng))

        # For O1 scenarios, also emit descriptions from low-severity templates
        # to ensure sufficient raw sample count (O1 combos are naturally sparse)
        if o_level == "O1":
            ls_tmpl_idx = hash((relevance, cross_border, ms_affected, cap_exceeded, "low")) % len(LOW_SEVERITY_TEMPLATES)
            ls_desc = _fill_template(
                LOW_SEVERITY_TEMPLATES[ls_tmpl_idx],
                sector, svc_impact_word, entities_count, n_sectors, cascading_word, data_impact_word,
            )
            descriptions.append(ls_desc)
            for v in range(1, paraphrase_variants + 1):
                descriptions.append(_paraphrase(ls_desc, v, rng))

        # Generate consequence fields for this combo
        fin_impact = rng.choice(FINANCIAL_IMPACTS)
        safe_impact = rng.choice(SAFETY_IMPACTS)
        persons = rng.choice(PERSONS_COUNT_RANGE)
        n_entities = rng.choice(O_ENTITIES_RANGE)

        for desc in descriptions:
            text = (
                f"{desc} [SEP] "
                f"sectors: {n_sectors} "
                f"relevance: {relevance} "
                f"ms_affected: {ms_affected} "
                f"cross_border: {cross_border} "
                f"capacity_exceeded: {str(cap_exceeded).lower()}"
            )
            if fin_impact != "none":
                text += f" financial: {fin_impact}"
            if safe_impact != "none":
                text += f" safety: {safe_impact}"
            if persons > 0:
                text += f" persons: {persons}"
            if n_entities > 1:
                text += f" entities: {n_entities}"
            all_samples.append({"text": text, "label": o_level})

    return all_samples


# ---------------------------------------------------------------------------
# Balancing
# ---------------------------------------------------------------------------

def balance_classes(
    samples: list[dict],
    target_per_class: int,
    seed: int,
) -> list[dict]:
    """Balance dataset by undersampling majority and oversampling minority."""
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = {}
    for s in samples:
        by_label.setdefault(s["label"], []).append(s)

    balanced: list[dict] = []
    for label, items in sorted(by_label.items()):
        if len(items) >= target_per_class:
            balanced.extend(rng.sample(items, target_per_class))
        else:
            # Oversample with replacement to reach target
            balanced.extend(items)
            extra_needed = target_per_class - len(items)
            balanced.extend(rng.choices(items, k=extra_needed))

    rng.shuffle(balanced)
    return balanced


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(samples: list[dict], path: Path) -> None:
    """Write samples to CSV with text,label columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(samples)


def print_distribution(samples: list[dict], name: str) -> None:
    """Print class distribution stats."""
    counts = Counter(s["label"] for s in samples)
    total = len(samples)
    print(f"\n{name}: {total} samples")
    for label in sorted(counts):
        pct = counts[label] / total * 100
        print(f"  {label}: {counts[label]:>6} ({pct:5.1f}%)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate parametric incident training data for CyberScale Phase 3"
    )
    parser.add_argument(
        "--output-t", type=Path,
        default=Path("training/data/technical_training.csv"),
        help="Output path for technical (T-level) training CSV",
    )
    parser.add_argument(
        "--output-o", type=Path,
        default=Path("training/data/operational_training.csv"),
        help="Output path for operational (O-level) training CSV",
    )
    parser.add_argument(
        "--config-t", type=Path,
        default=Path("training/configs/technical_cls.json"),
        help="Technical classifier config",
    )
    parser.add_argument(
        "--config-o", type=Path,
        default=Path("training/configs/operational_cls.json"),
        help="Operational classifier config",
    )
    args = parser.parse_args()

    # Load configs
    with open(args.config_t) as f:
        cfg_t = json.load(f)
    with open(args.config_o) as f:
        cfg_o = json.load(f)

    seed = cfg_t["model"]["seed"]
    t_target = cfg_t["data"]["target_per_class"]
    t_variants = cfg_t["data"]["paraphrase_variants"]
    o_target = cfg_o["data"]["target_per_class"]
    o_variants = cfg_o["data"]["paraphrase_variants"]

    # Generate T-level data
    print("Generating T-level samples...")
    t_raw = generate_t_samples(t_target, t_variants, seed)
    print_distribution(t_raw, "T-level (raw)")
    t_balanced = balance_classes(t_raw, t_target, seed)
    print_distribution(t_balanced, "T-level (balanced)")

    # Generate O-level data
    print("\nGenerating O-level samples...")
    o_raw = generate_o_samples(o_target, o_variants, seed)
    print_distribution(o_raw, "O-level (raw)")
    o_balanced = balance_classes(o_raw, o_target, seed)
    print_distribution(o_balanced, "O-level (balanced)")

    # Write outputs
    write_csv(t_balanced, args.output_t)
    print(f"\nWrote {len(t_balanced)} T-level samples to {args.output_t}")

    write_csv(o_balanced, args.output_o)
    print(f"Wrote {len(o_balanced)} O-level samples to {args.output_o}")


if __name__ == "__main__":
    main()
