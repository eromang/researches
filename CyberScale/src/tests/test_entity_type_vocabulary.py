"""Every entity_type in the repository must exist in the canonical vocabulary.

`nis2_entity_types.json` is authoritative: the MCP boundary rejects anything
outside it (`VALID_ENTITY_TYPES`). A reference file or dataset carrying a name
that is not in it describes behaviour production cannot reach.

That is exactly what happened. Until 2026-08-05 eleven of the twenty-two entity
types in `lu_thresholds.json` used ILR-flavoured names — `road_transport_operator`,
`gas_distribution_operator`, `air_traffic_management` and others — so those LU
thresholds were unreachable through the tool, while the benchmarks passed because
they call the assessor directly and skip validation. Twenty-three multi-entity
scenarios separately carried their *sector* name in `entity_type`.

These tests exist so neither drift recurs silently.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REF = Path(__file__).parent.parent.parent / "data" / "reference"


def _valid() -> set[str]:
    return {e["id"] for e in json.loads((REF / "nis2_entity_types.json").read_text())["entity_types"]}


def _walk(obj, path=""):
    """Yield (path, value) for every entity_type / entity_types found."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "entity_type" and isinstance(v, str):
                yield f"{path}.{k}", v
            elif k == "entity_types" and isinstance(v, list):
                for e in v:
                    yield f"{path}.{k}", e
            else:
                yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from _walk(x, f"{path}[{i}]")


DATASETS = [
    "curated_incidents.json",
    "curated_lu_incidents.json",
    "curated_be_incidents.json",
    "curated_lu_crisis_scenarios.json",
    "curated_multi_entity_incidents.json",
    "real_incident_validation.json",
]


@pytest.mark.parametrize("name", DATASETS)
def test_dataset_entity_types_are_canonical(name):
    valid = _valid()
    data = json.loads((REF / name).read_text())
    bad = sorted({v for _, v in _walk(data) if v not in valid})
    assert not bad, f"{name} uses entity types absent from nis2_entity_types.json: {bad}"


def test_lu_threshold_mapping_uses_canonical_names():
    """Otherwise the LU thresholds behind those names are unreachable."""
    valid = _valid()
    lu = json.loads((REF / "lu_thresholds.json").read_text())
    bad = []
    for sector, mapping in lu["sector_mapping"].items():
        if sector == "description":
            continue
        bad += [f"{sector}:{et}" for et in mapping if et not in valid]
    assert not bad, f"lu_thresholds.json maps entity types the MCP boundary rejects: {bad}"


def test_ir_entity_types_are_canonical():
    valid = _valid()
    ir = json.loads((REF / "ir_incident_thresholds.json").read_text())
    bad = [e for e in ir["ir_entity_types"] if e not in valid]
    assert not bad, f"ir_incident_thresholds.json lists non-canonical entity types: {bad}"


def test_entity_type_is_never_a_bare_sector_name():
    """The failure mode that produced the 23 multi-entity errors: the generator
    filled entity_type with the sector when it had no specific type."""
    ets = json.loads((REF / "nis2_entity_types.json").read_text())["entity_types"]
    sectors = {e["sector"] for e in ets}
    valid = {e["id"] for e in ets}
    offenders = []
    for name in DATASETS:
        data = json.loads((REF / name).read_text())
        for path, v in _walk(data):
            if v in sectors and v not in valid:
                offenders.append(f"{name}{path}={v}")
    assert not offenders, f"sector names used as entity types: {offenders[:10]}"


def test_every_lu_mapped_type_resolves_to_a_sector_key_or_none():
    """A mapping that points at a sector key the thresholds file does not define
    would route to a lookup that cannot succeed."""
    lu = json.loads((REF / "lu_thresholds.json").read_text())
    keys = set(lu["sectors"].keys())
    bad = []
    for sector, mapping in lu["sector_mapping"].items():
        if sector == "description":
            continue
        for et, key in mapping.items():
            if key is not None and key not in keys:
                bad.append(f"{et} -> {key}")
    assert not bad, f"mappings point at undefined LU sector keys: {bad}"
