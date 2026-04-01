"""Bulk-fetch CVEs from cvelistV5 (CVE.org) for Phase 1 training data.

Downloads all CVE records from the CVE Program's GitHub repository,
parses CVSS v3.1 scores, descriptions, and CWE locally — zero API calls.
Then caps per-score clustering and balances across CVSS bands.

Source: https://github.com/CVEProject/cvelistV5 (~2GB, ~340k CVEs)
Format: CVE JSON 5.0 (description, CVSS metrics, CWE in each file)

ChromaDB is populated by default, skipping entries that already exist
(safe to run after fetch_training_cves.py — no duplicates). Use
--no-store to skip.

Usage:
    cd CyberScale
    poetry run python training/scripts/fetch_bulk_cves.py \
        --output training/data/training_cves_bulk.csv \
        --config training/configs/scorer.json

    # Keep cvelistV5 clone for re-runs (skip download):
    poetry run python training/scripts/fetch_bulk_cves.py \
        --output training/data/training_cves_bulk.csv \
        --config training/configs/scorer.json \
        --cache-dir training/data/cvelistV5

    # CSV only, no ChromaDB:
    poetry run python training/scripts/fetch_bulk_cves.py \
        --output training/data/training_cves_bulk.csv \
        --config training/configs/scorer.json \
        --no-store
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

# Allow importing from src/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# ---------------------------------------------------------------------------
# Quality filters
# ---------------------------------------------------------------------------

# Reject descriptions that are stubs, reserved, or rejected
REJECT_PATTERNS = [
    re.compile(r"\*\*\s*RESERVED\s*\*\*", re.IGNORECASE),
    re.compile(r"\*\*\s*REJECT(ED)?\s*\*\*", re.IGNORECASE),
    re.compile(r"^\s*This candidate has been reserved", re.IGNORECASE),
    re.compile(r"^\s*DO NOT USE THIS CANDIDATE", re.IGNORECASE),
    re.compile(r"^\s*This CVE ID has been rejected", re.IGNORECASE),
    re.compile(r"^\s*N/A\s*$", re.IGNORECASE),
]


def passes_quality_filters(cve: dict, min_tokens: int = 10) -> tuple[bool, str]:
    """Check a parsed CVE against quality filters.

    Returns (passes, reason) — reason is empty if passes.
    """
    desc = cve["description"]

    # Reject stub/reserved/rejected descriptions
    for pattern in REJECT_PATTERNS:
        if pattern.search(desc):
            return False, "reserved/rejected"

    # Min token count (words, not chars — catches short but wide-char descriptions)
    tokens = desc.split()
    if len(tokens) < min_tokens:
        return False, f"too_few_tokens ({len(tokens)})"

    # Reject if CVSS score is exactly 0.0 (likely placeholder)
    if cve["cvss_score"] == 0.0:
        return False, "score_zero"

    return True, ""


def deduplicate_descriptions(cves: list[dict]) -> tuple[list[dict], int]:
    """Remove CVEs with duplicate descriptions (same text, different CVE ID).

    Uses SHA-256 of normalised description to detect duplicates.
    Keeps the first occurrence (lowest CVE ID lexicographically).
    """
    seen_hashes: dict[str, str] = {}  # hash -> cve_id
    unique = []
    dupes = 0

    # Sort by CVE ID for deterministic first-occurrence selection
    sorted_cves = sorted(cves, key=lambda c: c["cve_id"])

    for cve in sorted_cves:
        # Normalise: lowercase, collapse whitespace
        normalised = " ".join(cve["description"].lower().split())
        desc_hash = hashlib.sha256(normalised.encode()).hexdigest()

        if desc_hash in seen_hashes:
            dupes += 1
            continue

        seen_hashes[desc_hash] = cve["cve_id"]
        unique.append(cve)

    return unique, dupes


# ---------------------------------------------------------------------------
# Parsing CVE JSON 5.0
# ---------------------------------------------------------------------------

INVALID_CWES = {"CWE-noinfo", "CWE-Other"}


def extract_cwe(record: dict) -> str | None:
    """Extract first valid CWE ID from a cvelistV5 record.

    Looks in containers.cna.problemTypes[].descriptions[].cweId,
    skipping CWE-noinfo and CWE-Other.
    """
    try:
        problem_types = record["containers"]["cna"]["problemTypes"]
    except (KeyError, TypeError):
        return None

    for pt in problem_types:
        for desc in pt.get("descriptions", []):
            cwe_id = desc.get("cweId", "")
            if cwe_id and cwe_id not in INVALID_CWES:
                return cwe_id
    return None


def parse_cve_file(path: Path) -> dict | None:
    """Parse a single CVE JSON 5.0 file. Returns dict or None if unusable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    # Must be published
    state = data.get("cveMetadata", {}).get("state", "")
    if state != "PUBLISHED":
        return None

    cve_id = data.get("cveMetadata", {}).get("cveId", "")
    if not cve_id:
        return None

    cna = data.get("containers", {}).get("cna", {})

    # Description (English)
    description = None
    for desc in cna.get("descriptions", []):
        if desc.get("lang", "").startswith("en"):
            description = desc.get("value", "").strip()
            break
    if not description:
        return None

    # CVSS v3.1 score (prefer v3.1, fall back to v3.0)
    cvss_score = None
    cvss_version = None
    cvss_vector = None
    for metric_block in cna.get("metrics", []):
        # Try v3.1 first
        for key in ("cvssV3_1", "cvssV31", "cvssV3_0", "cvssV30"):
            if key in metric_block:
                m = metric_block[key]
                score = m.get("baseScore")
                version = m.get("version")
                if score is not None and version is not None:
                    cvss_score = float(score)
                    cvss_version = str(version)
                    cvss_vector = m.get("vectorString")
                    break
        if cvss_score is not None:
            break

    # Also check adp containers (NVD often scores via ADP)
    if cvss_score is None:
        for adp in data.get("containers", {}).get("adp", []):
            for metric_block in adp.get("metrics", []):
                for key in ("cvssV3_1", "cvssV31", "cvssV3_0", "cvssV30"):
                    if key in metric_block:
                        m = metric_block[key]
                        score = m.get("baseScore")
                        version = m.get("version")
                        if score is not None and version is not None:
                            cvss_score = float(score)
                            cvss_version = str(version)
                            cvss_vector = m.get("vectorString")
                            break
                if cvss_score is not None:
                    break

    if cvss_score is None:
        return None

    # CWE
    cwe = extract_cwe(data)

    # CPE vendor/product from first affected entry
    cpe_vendor = None
    cpe_product = None
    for affected in cna.get("affected", []):
        v = affected.get("vendor", "").strip()
        p = affected.get("product", "").strip()
        if v and v.lower() not in ("n/a", ""):
            cpe_vendor = v.lower()
        if p and p.lower() not in ("n/a", ""):
            cpe_product = p.lower()
        if cpe_vendor or cpe_product:
            break

    return {
        "cve_id": cve_id,
        "description": description,
        "cvss_score": cvss_score,
        "cvss_version": cvss_version,
        "cvss_vector": cvss_vector,
        "cwe": cwe,
        "cpe_vendor": cpe_vendor,
        "cpe_product": cpe_product,
        "source": "cvelistV5",
    }


# ---------------------------------------------------------------------------
# CVSS vector parsing
# ---------------------------------------------------------------------------

# Maps CVSS v3.x vector abbreviations to output column names
_VECTOR_KEY_MAP = {
    "AV": "av",
    "AC": "ac",
    "PR": "pr",
    "UI": "ui",
    "S": "scope",
    "C": "conf",
    "I": "integ",
    "A": "avail",
}

CVSS_COMPONENT_COLS = list(_VECTOR_KEY_MAP.values())


def parse_cvss_vector(vector: str | None) -> dict[str, str | None]:
    """Parse a CVSS v3.x vector string into 8 component columns.

    Example input:  "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    Example output: {"av": "N", "ac": "L", "pr": "N", "ui": "N",
                     "scope": "U", "conf": "H", "integ": "H", "avail": "H"}

    Returns dict with None values for all components if vector is None or
    cannot be parsed.
    """
    empty = {col: None for col in CVSS_COMPONENT_COLS}
    if not vector:
        return empty

    # Strip the "CVSS:x.y/" prefix and split on "/"
    parts = vector.split("/")
    # Skip the first part if it starts with "CVSS:" (version prefix)
    if parts and parts[0].upper().startswith("CVSS:"):
        parts = parts[1:]

    parsed = dict(empty)
    for part in parts:
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        col = _VECTOR_KEY_MAP.get(key.upper())
        if col:
            parsed[col] = value.upper()

    return parsed


def enrich_cvss_components(cves: list[dict]) -> None:
    """Add the 8 CVSS vector component columns to each CVE dict in-place."""
    for cve in cves:
        components = parse_cvss_vector(cve.get("cvss_vector"))
        cve.update(components)


# ---------------------------------------------------------------------------
# Download / cache
# ---------------------------------------------------------------------------

def download_cvelistv5(cache_dir: Path | None) -> Path:
    """Clone cvelistV5 repo (shallow, sparse — cves/ only)."""
    if cache_dir and cache_dir.exists() and (cache_dir / "cves").exists():
        print(f"Using cached cvelistV5 at {cache_dir}")
        return cache_dir

    target = cache_dir or Path(tempfile.mkdtemp(prefix="cvelistV5_"))
    target.mkdir(parents=True, exist_ok=True)

    print(f"Cloning cvelistV5 (shallow, sparse) to {target}...")
    print("  This may take a few minutes (~2GB)...")

    subprocess.run(
        ["git", "clone", "--depth=1", "--filter=blob:none", "--sparse",
         "https://github.com/CVEProject/cvelistV5.git", str(target)],
        check=True,
    )
    # Enable sparse checkout for cves/ directory only
    subprocess.run(
        ["git", "-C", str(target), "sparse-checkout", "set", "cves"],
        check=True,
    )
    # Checkout to actually fetch the blobs
    subprocess.run(
        ["git", "-C", str(target), "checkout"],
        check=True,
    )

    print(f"  Clone complete: {target}")
    return target


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def collect_all_cves(
    repo_dir: Path,
    min_desc_len: int = 50,
    min_tokens: int = 10,
) -> list[dict]:
    """Walk all CVE JSON files, parse them, apply quality filters, deduplicate."""
    cves_dir = repo_dir / "cves"
    if not cves_dir.exists():
        raise FileNotFoundError(f"cves/ directory not found in {repo_dir}")

    raw_cves = []
    file_count = 0
    skip_reasons: Counter = Counter()

    print("Parsing CVE files...")
    for json_file in cves_dir.rglob("CVE-*.json"):
        file_count += 1
        if file_count % 50000 == 0:
            print(f"  Parsed {file_count} files, {len(raw_cves)} candidates...")

        result = parse_cve_file(json_file)
        if result is None:
            skip_reasons["no_cvss_or_desc"] += 1
            continue
        if len(result["description"]) < min_desc_len:
            skip_reasons["desc_too_short"] += 1
            continue

        # Quality filters
        passes, reason = passes_quality_filters(result, min_tokens=min_tokens)
        if not passes:
            skip_reasons[reason] += 1
            continue

        raw_cves.append(result)

    print(f"  Total files: {file_count}")
    print(f"  After quality filters: {len(raw_cves)}")
    print(f"  Skip reasons: {dict(skip_reasons.most_common())}")

    # Deduplicate by description
    unique_cves, dupes = deduplicate_descriptions(raw_cves)
    print(f"  After dedup: {len(unique_cves)} (-{dupes} duplicate descriptions)")

    # Parse CVSS vector strings into individual component columns
    enrich_cvss_components(unique_cves)

    return unique_cves


BAND_DEFS = [
    ("Low", 0.0, 3.9),
    ("Medium", 4.0, 6.9),
    ("High", 7.0, 8.9),
    ("Critical", 9.0, 10.0),
]

BOUNDARIES = [4.0, 7.0, 9.0]


def select_training_set(
    cves: list[dict],
    target_per_band: int = 3000,
    max_per_score: int = 500,
    boundary_margin: float = 1.0,
    boundary_ratio: float = 0.33,
    seed: int = 42,
) -> list[dict]:
    """Select training set with boundary-enriched sampling.

    Two-phase selection per band:
      1. Core samples: capped at max_per_score per unique score value
      2. Boundary samples: extra samples drawn from ±boundary_margin of
         band edges to boost model accuracy near classification boundaries

    Args:
        cves: Full quality-filtered CVE pool
        target_per_band: Target samples per band (total = 4 × target)
        max_per_score: Max samples per unique score value (anti-clustering)
        boundary_margin: Distance from band edge for boundary enrichment
        boundary_ratio: Fraction of target_per_band reserved for boundaries
        seed: Random seed
    """
    rng = random.Random(seed)

    # --- Phase 1: Pool assignment per band ---
    band_pools: dict[str, list[dict]] = defaultdict(list)
    for cve in cves:
        for name, lo, hi in BAND_DEFS:
            if lo <= cve["cvss_score"] <= hi:
                band_pools[name].append(cve)
                break

    print(f"\n--- Selection Strategy ---")
    print(f"Target: {target_per_band}/band = {target_per_band * 4} total")
    print(f"Boundary enrichment: {boundary_ratio:.0%} of band from ±{boundary_margin} of edges")
    print(f"Per-score cap: {max_per_score}")

    for name, _, _ in BAND_DEFS:
        print(f"  {name:10s}: {len(band_pools[name]):6d} in pool")

    # --- Phase 2: Per-band selection ---
    boundary_target = int(target_per_band * boundary_ratio)
    core_target = target_per_band - boundary_target

    selected: list[dict] = []

    for name, lo, hi in BAND_DEFS:
        pool = band_pools[name]
        rng.shuffle(pool)

        # Identify boundary samples (within margin of band edges)
        boundary_samples = []
        core_samples = []
        for cve in pool:
            score = cve["cvss_score"]
            near_boundary = any(abs(score - b) <= boundary_margin for b in BOUNDARIES)
            if near_boundary:
                boundary_samples.append(cve)
            else:
                core_samples.append(cve)

        # Cap per-score within each subset
        def cap_per_score(samples: list[dict], cap: int) -> list[dict]:
            by_score: dict[float, list[dict]] = defaultdict(list)
            for s in samples:
                by_score[s["cvss_score"]].append(s)
            result = []
            for score in sorted(by_score.keys()):
                group = by_score[score]
                rng.shuffle(group)
                result.extend(group[:cap])
            return result

        capped_boundary = cap_per_score(boundary_samples, max_per_score)
        capped_core = cap_per_score(core_samples, max_per_score)

        # Select boundary samples first, then fill with core
        actual_boundary = min(boundary_target, len(capped_boundary))
        rng.shuffle(capped_boundary)
        band_selected = capped_boundary[:actual_boundary]

        remaining = target_per_band - len(band_selected)
        rng.shuffle(capped_core)
        band_selected.extend(capped_core[:remaining])

        # If still short (small band), take more from boundary overflow
        if len(band_selected) < target_per_band:
            overflow = capped_boundary[actual_boundary:]
            band_selected.extend(overflow[:target_per_band - len(band_selected)])

        actual = len(band_selected)
        actual_bnd = min(actual_boundary, actual)
        print(f"  {name:10s}: selected {actual} "
              f"(core={actual - actual_bnd}, boundary={actual_bnd}, "
              f"pool={len(pool)})")

        selected.extend(band_selected)

    rng.shuffle(selected)

    # Actual band counts (may be less than target if pool is small)
    final_counts = Counter()
    for cve in selected:
        for name, lo, hi in BAND_DEFS:
            if lo <= cve["cvss_score"] <= hi:
                final_counts[name] += 1
                break

    # Balance to smallest actual band
    min_actual = min(final_counts.values())
    if min_actual < target_per_band:
        print(f"\n  Rebalancing to smallest band: {min_actual}")
        by_band: dict[str, list[dict]] = defaultdict(list)
        for cve in selected:
            for name, lo, hi in BAND_DEFS:
                if lo <= cve["cvss_score"] <= hi:
                    by_band[name].append(cve)
                    break
        selected = []
        for name in by_band:
            rng.shuffle(by_band[name])
            selected.extend(by_band[name][:min_actual])
        rng.shuffle(selected)

    print(f"\nFinal: {len(selected)} CVEs")
    return selected


def select_capped(
    cves: list[dict],
    cap_per_band: int = 30000,
    max_per_score: int = 500,
    seed: int = 42,
) -> list[dict]:
    """Select training set by capping each band at N samples (no hard balancing).

    Use with class weights in training to handle the remaining imbalance.
    This preserves maximum volume while preventing extreme imbalance.

    Args:
        cves: Full quality-filtered CVE pool
        cap_per_band: Max samples per band (smallest band keeps all)
        max_per_score: Max samples per unique score value (anti-clustering)
        seed: Random seed
    """
    rng = random.Random(seed)

    # Assign to bands
    band_pools: dict[str, list[dict]] = defaultdict(list)
    for cve in cves:
        for name, lo, hi in BAND_DEFS:
            if lo <= cve["cvss_score"] <= hi:
                band_pools[name].append(cve)
                break

    print(f"\n--- Capped Selection (cap={cap_per_band}/band, score_cap={max_per_score}) ---")
    for name, _, _ in BAND_DEFS:
        print(f"  {name:10s}: {len(band_pools[name]):6d} in pool")

    # Cap per-score within each band, then cap band total
    selected: list[dict] = []
    for name, _, _ in BAND_DEFS:
        pool = band_pools[name]

        # Cap per score value first
        by_score: dict[float, list[dict]] = defaultdict(list)
        for cve in pool:
            by_score[cve["cvss_score"]].append(cve)

        score_capped = []
        for score in sorted(by_score.keys()):
            group = by_score[score]
            rng.shuffle(group)
            score_capped.extend(group[:max_per_score])

        # Cap band total
        rng.shuffle(score_capped)
        band_selected = score_capped[:cap_per_band]

        print(f"  {name:10s}: selected {len(band_selected)} "
              f"(score_capped={len(score_capped)}, pool={len(pool)})")
        selected.extend(band_selected)

    rng.shuffle(selected)
    print(f"\nFinal: {len(selected)} CVEs")

    # Compute class weights for training
    band_counts = Counter()
    for cve in selected:
        for name, lo, hi in BAND_DEFS:
            if lo <= cve["cvss_score"] <= hi:
                band_counts[name] += 1
                break

    total = len(selected)
    print(f"\n  Recommended class weights (inverse frequency):")
    for name in ["Low", "Medium", "High", "Critical"]:
        weight = total / (4 * band_counts[name]) if band_counts[name] > 0 else 1.0
        print(f"    {name:10s}: {weight:.2f} (n={band_counts[name]})")

    return selected


def generate_pre_analysis(cves: list[dict], report_path: str | None = None) -> None:
    """Generate comprehensive pre-analysis report on dataset quality.

    Prints to stdout and optionally writes a markdown report.
    Covers: score distribution, CVSS version mix, CWE diversity,
    description length, year distribution, boundary density, top CWEs per band.
    """
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(cves)
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out(f"\n{'='*60}")
    out(f"DATASET PRE-ANALYSIS ({len(df)} CVEs)")
    out(f"{'='*60}")

    # --- 1. Overall stats ---
    out(f"\n## Overall")
    out(f"Total CVEs: {len(df)}")
    out(f"CVSS version: {df.cvss_version.value_counts().to_dict()}")
    v31_pct = (df.cvss_version == '3.1').mean() * 100
    out(f"v3.1 proportion: {v31_pct:.1f}%")
    out(f"CWE coverage: {df.cwe.notna().sum()}/{len(df)} ({df.cwe.notna().mean()*100:.0f}%)")
    out(f"Unique CWEs: {df.cwe.nunique()}")

    # --- 2. Per-band breakdown ---
    out(f"\n## Per-Band Breakdown")
    out(f"{'Band':10s} {'Count':>6s} {'Unique':>7s} {'Top1':>12s} {'Top1%':>6s} {'v3.1%':>6s} {'MeanLen':>8s}")
    band_defs = [("Low", 0, 3.9), ("Medium", 4.0, 6.9), ("High", 7.0, 8.9), ("Critical", 9.0, 10.0)]
    for name, lo, hi in band_defs:
        subset = df[(df.cvss_score >= lo) & (df.cvss_score <= hi)]
        if len(subset) == 0:
            continue
        top = subset.cvss_score.value_counts()
        top1_pct = top.iloc[0] / len(subset) * 100
        unique = subset.cvss_score.nunique()
        v31 = (subset.cvss_version == '3.1').mean() * 100
        mean_len = subset.description.str.len().mean()
        out(f"{name:10s} {len(subset):6d} {unique:7d} {top.index[0]:>12.1f} {top1_pct:5.0f}% {v31:5.0f}% {mean_len:7.0f}")

    # --- 3. Boundary density ---
    out(f"\n## Boundary Density")
    for b in [4.0, 7.0, 9.0]:
        near = df[(df.cvss_score >= b - 0.5) & (df.cvss_score <= b + 0.5)]
        below = near[near.cvss_score < b]
        above = near[near.cvss_score >= b]
        out(f"  ±0.5 of {b}: {len(near):5d} ({len(near)/len(df)*100:.1f}%)  "
            f"below={len(below)} above={len(above)}")

    # --- 4. Description length distribution ---
    out(f"\n## Description Length (chars)")
    desc_lens = df.description.str.len()
    out(f"  Min: {desc_lens.min():.0f}  Mean: {desc_lens.mean():.0f}  "
        f"Median: {desc_lens.median():.0f}  Max: {desc_lens.max():.0f}")
    for name, lo, hi in band_defs:
        subset = df[(df.cvss_score >= lo) & (df.cvss_score <= hi)]
        if len(subset) == 0:
            continue
        bl = subset.description.str.len()
        out(f"  {name:10s}: mean={bl.mean():.0f}  median={bl.median():.0f}")

    # --- 5. CWE diversity per band ---
    out(f"\n## Top 5 CWEs per Band")
    for name, lo, hi in band_defs:
        subset = df[(df.cvss_score >= lo) & (df.cvss_score <= hi)]
        if len(subset) == 0:
            continue
        top_cwes = subset.cwe.value_counts().head(5)
        cwe_str = ", ".join(f"{k}({v})" for k, v in top_cwes.items())
        out(f"  {name:10s}: {cwe_str}")

    # --- 6. Year distribution ---
    out(f"\n## CVE Year Distribution")
    df["year"] = df.cve_id.str.extract(r"CVE-(\d{4})-")[0].astype(int)
    year_counts = df.year.value_counts().sort_index()
    # Show ranges
    for decade_start in range(1999, 2030, 5):
        decade_end = decade_start + 4
        count = year_counts[(year_counts.index >= decade_start) & (year_counts.index <= decade_end)].sum()
        if count > 0:
            out(f"  {decade_start}-{decade_end}: {count:6d}")

    # --- 7. Clustering severity ---
    out(f"\n## Clustering Analysis")
    for name, lo, hi in band_defs:
        subset = df[(df.cvss_score >= lo) & (df.cvss_score <= hi)]
        if len(subset) == 0:
            continue
        top = subset.cvss_score.value_counts()
        # Gini-like: how concentrated is the distribution?
        props = top.values / top.values.sum()
        entropy = -sum(p * np.log2(p) for p in props if p > 0)
        max_entropy = np.log2(len(top))
        evenness = entropy / max_entropy if max_entropy > 0 else 0
        out(f"  {name:10s}: {len(top)} unique scores, "
            f"evenness={evenness:.2f} (1.0=perfectly even)")

    # --- 8. Quality flags ---
    out(f"\n## Quality Flags")
    flags = []
    for name, lo, hi in band_defs:
        subset = df[(df.cvss_score >= lo) & (df.cvss_score <= hi)]
        if len(subset) == 0:
            continue
        top_pct = subset.cvss_score.value_counts().iloc[0] / len(subset) * 100
        if top_pct > 30:
            flags.append(f"  WARNING: {name} band — top score is {top_pct:.0f}% of band")
        v31 = (subset.cvss_version == '3.1').mean() * 100
        if v31 < 50:
            flags.append(f"  WARNING: {name} band — only {v31:.0f}% v3.1 (majority v3.0)")
        mean_len = subset.description.str.len().mean()
        if mean_len < 100:
            flags.append(f"  WARNING: {name} band — short descriptions (mean {mean_len:.0f} chars)")
    if flags:
        for f in flags:
            out(f)
    else:
        out("  No quality warnings.")

    # Write report if path given
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text("\n".join(lines))
        out(f"\nReport saved to {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bulk-fetch CVEs from cvelistV5 for Phase 1 training"
    )
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--config", required=True, help="Config JSON path")
    parser.add_argument("--cache-dir", type=str, default=None,
                        help="Directory to cache/reuse cvelistV5 clone")
    parser.add_argument("--target-per-band", type=int, default=3000,
                        help="Target samples per band for balanced mode (total=4x, default: 3000)")
    parser.add_argument("--max-per-score", type=int, default=500,
                        help="Max samples per unique score value (default: 500)")
    parser.add_argument("--boundary-ratio", type=float, default=0.33,
                        help="Fraction of band reserved for boundary samples (default: 0.33)")
    parser.add_argument("--cap-per-band", type=int, default=None,
                        help="Cap each band at N samples without balancing (e.g., 30000). "
                             "Overrides --target-per-band. Use with class weights in training.")
    parser.add_argument("--min-tokens", type=int, default=10,
                        help="Min word count for descriptions (default: 10)")
    parser.add_argument("--no-store", action="store_true",
                        help="Skip ChromaDB population (default: populate, skipping duplicates)")
    parser.add_argument("--report", type=str, default=None,
                        help="Path to save pre-analysis markdown report")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text())
    seed = config.get("model", {}).get("seed", 42)
    min_desc_len = config.get("data", {}).get("min_description_length", 50)

    # Step 1: Download / cache
    cache_path = Path(args.cache_dir) if args.cache_dir else None
    repo_dir = download_cvelistv5(cache_path)

    # Step 2: Parse all CVEs, apply quality filters, deduplicate
    all_cves = collect_all_cves(
        repo_dir, min_desc_len=min_desc_len, min_tokens=args.min_tokens,
    )

    # Step 3: Select training set
    if args.cap_per_band:
        # Capped mode: take up to N per band, no hard balancing
        balanced = select_capped(
            all_cves,
            cap_per_band=args.cap_per_band,
            max_per_score=args.max_per_score,
            seed=seed,
        )
    else:
        # Balanced mode: boundary-enriched, hard-balanced
        balanced = select_training_set(
            all_cves,
            target_per_band=args.target_per_band,
            max_per_score=args.max_per_score,
            boundary_ratio=args.boundary_ratio,
            seed=seed,
        )

    # Step 4: Pre-analysis report
    report_path = args.report or str(Path(args.output).parent / "pre_analysis_report.md")
    generate_pre_analysis(balanced, report_path=report_path)

    # Step 5: Write CSV
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["cve_id", "description", "cvss_score", "cvss_version", "cvss_vector",
                   "cwe", "cpe_vendor", "cpe_product", "source",
                   "av", "ac", "pr", "ui", "scope", "conf", "integ", "avail"]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(balanced)
    print(f"\nWritten to {args.output}")

    # Step 6: Populate ChromaDB (skip duplicates)
    if not args.no_store:
        from cyberscale.store.client import VulnStore
        store = VulnStore()
        existing_count = store.count()
        print(f"\nPopulating ChromaDB ({existing_count} existing entries)...")

        # Batch-check which CVE IDs already exist to skip re-embedding
        all_ids = [cve["cve_id"] for cve in balanced]
        existing_ids = set()
        # Check in batches of 500 (ChromaDB get limit)
        for i in range(0, len(all_ids), 500):
            batch_ids = all_ids[i:i + 500]
            try:
                result = store._collection.get(ids=batch_ids, include=[])
                existing_ids.update(result["ids"])
            except Exception:
                pass

        new_cves = [cve for cve in balanced if cve["cve_id"] not in existing_ids]
        skipped = len(balanced) - len(new_cves)
        print(f"  Skipping {skipped} duplicates, adding {len(new_cves)} new entries...")

        added = 0
        for i, cve in enumerate(new_cves):
            try:
                store.add(
                    cve_id=cve["cve_id"],
                    description=cve["description"],
                    cvss_score=cve["cvss_score"],
                    cvss_version=cve.get("cvss_version"),
                    cwe=cve.get("cwe"),
                    source=cve["source"],
                )
                added += 1
            except Exception as e:
                print(f"  Store add failed for {cve['cve_id']}: {e}")
            if (i + 1) % 1000 == 0:
                print(f"  Added {added}/{len(new_cves)}...")

        print(f"ChromaDB: {added} new entries added (total: {store.count()})")
    else:
        print("\nSkipped ChromaDB (--no-store)")

    # Cleanup temp dir if no cache requested
    if cache_path is None:
        import shutil
        print(f"\nCleaning up temp clone at {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
