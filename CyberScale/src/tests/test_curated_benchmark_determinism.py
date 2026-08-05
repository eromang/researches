"""The curated Phase 3 benchmark must be reproducible.

Until 2026-08-05 it loaded the ML TechnicalClassifier, which retains MC dropout,
so three consecutive runs on identical data gave T 91.3 / 93.5 / 91.3 and matrix
89.1 / 91.3 / 89.1. A benchmark whose own figures move between runs cannot
support the statements made about it — including "these six additions raised the
average", which is the claim this repository actually made off it.

It now derives T and O with the same functions `tools/incident.py` calls, so the
result is fixed by the data. These tests pin that.
"""

from __future__ import annotations

import json
from pathlib import Path

from cyberscale.aggregation import derive_o_level, derive_t_level

REF = Path(__file__).parent.parent.parent / "data" / "reference"


def _derive_all():
    incidents = json.loads((REF / "curated_incidents.json").read_text())["incidents"]
    out = []
    for i in incidents:
        t, o = i["t_fields"], i["o_fields"]
        tl, _ = derive_t_level(t["service_impact"], t["data_impact"],
                               t["cascading"], t["affected_entities"])
        ol, _ = derive_o_level(o["cross_border_pattern"], o["capacity_exceeded"],
                               o["entity_relevance"], o["ms_affected"],
                               o["sectors_affected"],
                               affected_entities=t["affected_entities"])
        out.append((i["id"], tl, ol))
    return out


def test_derivation_is_stable_across_repeated_runs():
    runs = [_derive_all() for _ in range(5)]
    assert all(r == runs[0] for r in runs[1:]), "T/O derivation must not vary between runs"


def test_accuracy_is_pinned():
    """A change here is a real change in behaviour or in the dataset, not noise."""
    incidents = {i["id"]: i for i in
                 json.loads((REF / "curated_incidents.json").read_text())["incidents"]}
    derived = _derive_all()
    n = len(derived)
    t_ok = sum(1 for cid, tl, _ in derived if tl == incidents[cid]["expected_t"])
    o_ok = sum(1 for cid, _, ol in derived if ol == incidents[cid]["expected_o"])

    assert n == 46, f"dataset size changed to {n}; update the pinned figures below"
    assert t_ok == 43, f"T accuracy moved: {t_ok}/{n}"
    assert o_ok == 37, f"O accuracy moved: {o_ok}/{n}"


def test_matrix_classification_is_pinned():
    bm = json.loads((REF / "blueprint_matrix.json").read_text())["matrix"]
    incidents = {i["id"]: i for i in
                 json.loads((REF / "curated_incidents.json").read_text())["incidents"]}
    ok = sum(1 for cid, tl, ol in _derive_all()
             if bm[tl][ol] == bm[incidents[cid]["expected_t"]][incidents[cid]["expected_o"]])
    assert ok == 39, f"matrix classification accuracy moved: {ok}/46"


def test_benchmark_uses_the_production_derivation():
    """Guard against the benchmark drifting back to the deprecated ML models."""
    src = (Path(__file__).parent.parent.parent / "evaluation" /
           "benchmark_curated.py").read_text()
    main_body = src.split("def main(")[1]
    assert "evaluate_t_deterministic(incidents)" in main_body
    assert "evaluate_o_deterministic(incidents)" in main_body
    # The ML arm may exist, but only behind the flag.
    assert "if args.compare_ml:" in main_body
