"""The external validation set must not be lost or altered without noticing.

This data has already been deleted once. It sat in the Obsidian vault at
`01_Projects/CVE-Severity-Context/`, was removed on 2026-03-30 as a "closed
predecessor project", and was recovered on 2026-08-06 only because a filesystem
path survived in a session log — a first search for it failed.

It is the only ground truth for Phase 2 that CyberScale's own rules did not
generate, which makes its absence particularly costly: without it, every
contextual-severity figure measures how well a model rehearses the rules it was
trained on, and nothing checks whether those rules match expert judgement. The
answer, when it was finally checked, was that they largely do not — the expert
lowers severity in 44.9 % of scenarios and the rule chain cannot lower anything.

So the failure this guards is not corruption, it is quiet disappearance. A
missing directory would otherwise surface as a skipped test, and a skipped test
reads like a passing one.
"""
import hashlib
import os
import subprocess

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BENCH = os.path.join(REPO, "evaluation", "benchmarks", "cve-severity-context")
SCENARIOS = os.path.join(BENCH, "scenarios")
MANIFEST = os.path.join(BENCH, "MANIFEST.sha256")

EXPECTED_SCENARIOS = 842
EXPECTED_MANIFEST_SHA256 = "d61f0df7aea719ed1c9dffcc1f3f0d4b0a3b1ac0e6f0bb882c0c4b9790dd0ccd"


def test_the_benchmark_directory_exists():
    """Deliberately not skipped when absent — a skip reads as a pass."""
    assert os.path.isdir(SCENARIOS), (
        f"{SCENARIOS} is missing. This is the only external validation set for "
        "Phase 2 and it has been deleted once before; recover it from git "
        "history rather than regenerating anything.")
    assert os.path.isfile(MANIFEST), f"{MANIFEST} is missing"


def test_the_scenario_count_is_unchanged():
    n = sum(1 for root, _d, files in os.walk(SCENARIOS)
            for f in files if f.endswith(".md"))
    assert n == EXPECTED_SCENARIOS, (
        f"{n} scenarios found, expected {EXPECTED_SCENARIOS}. If this is a "
        "deliberate addition, update EXPECTED_SCENARIOS and re-measure the "
        "published baselines — they are not comparable across a changed set.")


def test_the_manifest_itself_has_not_been_rewritten():
    """Guards the guard: regenerating MANIFEST.sha256 would make any content
    change verify cleanly against itself."""
    digest = hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest()
    assert digest == EXPECTED_MANIFEST_SHA256, (
        "MANIFEST.sha256 has changed. Verifying content against a rewritten "
        "manifest proves nothing.")


def test_every_scenario_matches_its_recorded_hash():
    proc = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
                          cwd=BENCH, capture_output=True, text=True)
    assert proc.returncode == 0, (
        "scenario content has drifted from the manifest:\n"
        + "\n".join(l for l in proc.stdout.splitlines() if "OK" not in l)[:2000])


def test_the_downward_divergence_that_the_rules_cannot_express_is_still_there():
    """The property that makes this set worth keeping, asserted rather than
    described: if it ever stops holding, the reason to keep the data changed."""
    import re
    directions = {"downward": 0, "upward": 0, "none": 0}
    for root, _d, files in os.walk(SCENARIOS):
        for f in files:
            if not f.endswith(".md"):
                continue
            text = open(os.path.join(root, f), encoding="utf-8",
                        errors="replace").read()
            m = re.search(r'^divergence_direction:\s*"?(\w+)"?', text, re.M)
            if m and m.group(1) in directions:
                directions[m.group(1)] += 1
    assert directions["downward"] == 378, directions
    assert directions["downward"] > directions["upward"] * 2, (
        "downward divergence is no longer dominant — the argument that "
        "CyberScale's escalate-only rule chain cannot represent expert "
        "judgement rests on this")
