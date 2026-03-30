"""Fetch CVEs with CVSS scores from NVD and EUVD for Phase 1 training data.

Also populates ChromaDB vector store with fetched CVEs (skip with --no-store).
This avoids redundant API calls — the same data trains the model and seeds
the store for search_similar / score_vulnerability similarity enrichment.

Usage:
    cd CyberScale
    poetry run python training/scripts/fetch_training_cves.py \
        --output training/data/training_cves.csv \
        --config training/configs/scorer.json

    # CSV only, no ChromaDB:
    poetry run python training/scripts/fetch_training_cves.py \
        --output training/data/training_cves.csv \
        --config training/configs/scorer.json \
        --no-store
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any

from cyberscale.api.euvd import EUVDClient
from cyberscale.api.nvd import NVDClient
from cyberscale.store.client import VulnStore


CSV_FIELDS = ["cve_id", "description", "cvss_score", "cvss_version", "cwe", "source"]


def load_config(config_path: str) -> dict[str, Any]:
    """Load scorer configuration from JSON."""
    with open(config_path) as f:
        return json.load(f)


def fetch_nvd_band(
    client: NVDClient,
    band_name: str,
    target: int,
    min_desc_len: int,
) -> list[dict[str, Any]]:
    """Fetch CVEs from NVD for a single severity band."""
    collected: list[dict[str, Any]] = []
    start_index = 0
    page_size = 100

    print(f"  NVD {band_name}: fetching up to {target} CVEs...")

    while True:
        batch = client.search(
            severity=band_name.upper(),
            start_index=start_index,
            results_per_page=page_size,
        )
        if not batch:
            break

        for cve in batch:
            if cve.get("cvss_score") is None:
                continue
            desc = cve.get("description", "")
            if len(desc) < min_desc_len:
                continue
            collected.append({
                "cve_id": cve["id"],
                "description": desc,
                "cvss_score": cve["cvss_score"],
                "cvss_version": cve.get("cvss_version", ""),
                "cwe": cve.get("cwe", ""),
                "source": "nvd",
            })

        band_count = len(collected)
        print(f"    ... {band_count} collected (start_index={start_index})")

        if band_count >= target:
            break
        if len(batch) < page_size:
            break

        start_index += page_size
        time.sleep(6)

    return collected


def fetch_euvd_band(
    client: EUVDClient,
    band_name: str,
    band_cfg: dict[str, Any],
    target: int,
    existing_ids: set[str],
    min_desc_len: int,
) -> list[dict[str, Any]]:
    """Supplement a band with EUVD CVEs not already in the NVD set."""
    collected: list[dict[str, Any]] = []
    page = 0
    page_size = 100

    print(f"  EUVD {band_name}: supplementing (need {target} more)...")

    while len(collected) < target:
        results = client.search(
            from_score=band_cfg["min"],
            to_score=band_cfg["max"],
            size=page_size,
            page=page,
        )
        if not results:
            break

        for item in results:
            # EUVD items may map to multiple CVE IDs
            cve_ids = item.get("cve_ids", [])
            if not cve_ids:
                continue

            cve_id = cve_ids[0]
            if cve_id in existing_ids:
                continue

            if item.get("cvss_score") is None:
                continue
            desc = item.get("description", "")
            if not desc or len(desc) < min_desc_len:
                continue

            collected.append({
                "cve_id": cve_id,
                "description": desc,
                "cvss_score": item["cvss_score"],
                "cvss_version": item.get("cvss_version", ""),
                "cwe": "",  # EUVD does not provide CWE
                "source": "euvd",
            })
            existing_ids.add(cve_id)

            if len(collected) >= target:
                break

        print(f"    ... {len(collected)} new CVEs from EUVD (page={page})")

        if len(results) < page_size:
            break
        page += 1
        time.sleep(1)

    return collected


def balance_bands(
    bands: dict[str, list[dict[str, Any]]],
    target_total: int,
    band_config: dict[str, Any],
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Balance CVEs across bands by undersampling to target percentages."""
    rng = random.Random(seed)
    balanced: list[dict[str, Any]] = []

    for band_name, band_cfg in band_config.items():
        cves = bands.get(band_name, [])
        band_target = int(target_total * band_cfg["target_pct"])

        if len(cves) > band_target:
            sampled = rng.sample(cves, band_target)
        else:
            sampled = cves

        balanced.extend(sampled)
        print(f"  {band_name}: {len(sampled)} / {len(cves)} available (target: {band_target})")

    return balanced


def deduplicate(cves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate CVEs by cve_id, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for cve in cves:
        cve_id = cve["cve_id"]
        if cve_id not in seen:
            seen.add(cve_id)
            unique.append(cve)
    return unique


def write_csv(cves: list[dict[str, Any]], output_path: str) -> None:
    """Write CVEs to CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(cves)

    print(f"\nWrote {len(cves)} CVEs to {path}")


def populate_store(cves: list[dict[str, Any]], store: VulnStore) -> int:
    """Add CVEs to ChromaDB vector store. Returns count of entries added."""
    added = 0
    for cve in cves:
        store.add(
            cve_id=cve["cve_id"],
            description=cve["description"],
            cvss_score=cve["cvss_score"],
            cvss_version=cve.get("cvss_version") or None,
            cwe=cve.get("cwe") or None,
            source=cve["source"],
        )
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch CVEs from NVD and EUVD for training data."
    )
    parser.add_argument(
        "--output",
        default="training/data/training_cves.csv",
        help="Output CSV path (default: training/data/training_cves.csv)",
    )
    parser.add_argument(
        "--config",
        default="training/configs/scorer.json",
        help="Scorer config JSON path (default: training/configs/scorer.json)",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="Skip ChromaDB population (CSV only)",
    )
    parser.add_argument(
        "--nvd-api-key",
        default=None,
        help="NVD API key for faster rate limits (optional)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    data_cfg = config["data"]
    target_total = data_cfg["target_total"]
    band_config = data_cfg["band_balance"]
    min_desc_len = data_cfg["min_description_length"]
    seed = config["model"].get("seed", 42)

    nvd = NVDClient(api_key=args.nvd_api_key)
    euvd = EUVDClient()

    # Phase 1: Fetch from NVD (primary source)
    print("=" * 60)
    print("Phase 1: Fetching from NVD (primary)")
    print("=" * 60)

    bands: dict[str, list[dict[str, Any]]] = {}
    all_ids: set[str] = set()

    for band_name, band_cfg in band_config.items():
        band_target = int(target_total * band_cfg["target_pct"])
        # Fetch extra to account for filtering
        fetch_target = int(band_target * 1.3)
        cves = fetch_nvd_band(nvd, band_name, fetch_target, min_desc_len)
        cves = deduplicate(cves)
        bands[band_name] = cves
        all_ids.update(c["cve_id"] for c in cves)
        print(f"  {band_name}: {len(cves)} unique CVEs from NVD\n")

    # Phase 2: Supplement from EUVD where NVD fell short
    print("=" * 60)
    print("Phase 2: Supplementing from EUVD")
    print("=" * 60)

    for band_name, band_cfg in band_config.items():
        band_target = int(target_total * band_cfg["target_pct"])
        nvd_count = len(bands.get(band_name, []))
        shortfall = band_target - nvd_count

        if shortfall > 0:
            euvd_cves = fetch_euvd_band(
                euvd, band_name, band_cfg, shortfall, all_ids, min_desc_len
            )
            bands[band_name].extend(euvd_cves)
            print(f"  {band_name}: +{len(euvd_cves)} from EUVD (total: {len(bands[band_name])})\n")
        else:
            print(f"  {band_name}: NVD sufficient ({nvd_count} >= {band_target}), skipping EUVD\n")

    # Phase 3: Balance and deduplicate
    print("=" * 60)
    print("Phase 3: Balancing across bands")
    print("=" * 60)

    balanced = balance_bands(bands, target_total, band_config, seed=seed)
    balanced = deduplicate(balanced)

    print(f"\nTotal balanced CVEs: {len(balanced)}")

    # Phase 4: Write CSV
    write_csv(balanced, args.output)

    # Phase 5: Populate ChromaDB
    if not args.no_store:
        print(f"\nPopulating ChromaDB with {len(balanced)} CVEs...")
        store = VulnStore()
        added = populate_store(balanced, store)
        print(f"ChromaDB: {added} entries added (total: {store.count()})")
    else:
        print("\nSkipping ChromaDB population (--no-store)")

    print("\nDone.")


if __name__ == "__main__":
    main()
