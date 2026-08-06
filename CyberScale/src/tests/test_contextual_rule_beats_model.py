"""The contextual label is computable; the model is not needed to compute it.

Lesson 18 set the project's own test — if the label assignment function is
deterministic from the inputs, skip the model — and applied it to the T-model and
the O-model, both since removed. It was never applied to Phase 2's contextual
severity, on the grounds that free text is where ML earns its place.

Measured on the frozen v4 test split, reading only `input_text`:

    subset                            n      rule      model
    determined by the input text   3,178   100.00%    92.64%
    decided by an unrecorded flip  1,622    63.44%    60.30%
    TOTAL                          4,800    87.65%    81.71%

Two facts pinned here. First, the rule reproduces the generator **exactly** on
every row that carries no randomness — if that ever stops holding, the
reimplementation has drifted from `generate_contextual.py` and every comparison
built on it is void. Second, the rule beats the deployed model overall; a change
that reverses that is a change worth noticing.

The 33.8 % it cannot resolve are not a modelling failure: the generator's
cross-border escalation is a coin flip whose outcome is never written into
`input_text`. No predictor seeing only that string can recover it. Both arms sit
near the base rate there (the flip fired 36.6 % of the time, not 50 %, because
class balancing drops escalated rows preferentially).
"""
import csv
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO, "evaluation", "derive_contextual_rule.py")
FROZEN = os.path.join(REPO, "evaluation", "frozen", "contextual_eval_v4split.csv")
PREDS = "/tmp/cyberscale-retrain/preds_v4model.csv"

pytestmark = pytest.mark.skipif(
    not os.path.exists(FROZEN),
    reason="frozen eval set absent — regenerate with evaluation/frozen/make_frozen_eval.py")


def _run(*extra):
    return subprocess.run([sys.executable, SCRIPT, *extra],
                          capture_output=True, text=True, cwd=REPO)


def test_rule_reproduces_the_generator_exactly_where_nothing_is_random(tmp_path):
    """The control the script refuses to skip. 100 % or the rest is meaningless."""
    out = tmp_path / "r.json"
    p = _run("--out", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    d = json.loads(out.read_text())
    assert d["control_exact"] == d["control_rows"], (
        "the rule no longer reproduces generate_contextual.py on deterministic "
        "rows — it has drifted from the generator")
    assert d["control_rows"] > 2000, "control subset unexpectedly small"


def test_the_unrecoverable_share_is_the_cross_border_coin_flip(tmp_path):
    out = tmp_path / "r.json"
    assert _run("--out", str(out)).returncode == 0
    d = json.loads(out.read_text())
    # every row is reachable by one of the two assumptions: the only missing
    # information is that single bit
    assert d["oracle"] == d["n"], (
        "some rows are unreachable under both cross-border assumptions, so "
        "something other than the coin flip is unmodelled")


@pytest.mark.skipif(not os.path.exists(PREDS),
                    reason="model predictions absent — run eval_contextual_vocabulary.py "
                           "--dump-predictions first")
def test_the_rule_outscores_the_deployed_model(tmp_path):
    out = tmp_path / "r.json"
    p = _run("--model-predictions", PREDS, "--out", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    d = json.loads(out.read_text())
    rule = max(d["cb_never"], d["cb_always"])
    assert rule > d["model"], (
        f"rule {rule} vs model {d['model']} — the rule no longer wins, which "
        "reopens the question of what the model contributes")
