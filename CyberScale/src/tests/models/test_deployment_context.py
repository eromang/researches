"""`deployment_context` reaches Phase 2, and de-escalation stays opt-in.

Measured 2026-08-06 against the external validation set: the expert lowers
severity below the CVSS base score in 378 of 842 scenarios, and the strongest
predictors of that live in the deployment context — *home* appears in scenarios
down-graded 96.6 % of the time, *personal* 91.1 %, *single* 89.2 %,
*workstations* 71.2 %. `predict()` had no parameter for any of it, so the field
the expert actually judges on never reached the model. On the held-out split,
adding it takes the rules from 41.95 % to 48.63 %, and on down-graded scenarios
from 24.83 % to 55.70 %.

Two design decisions are pinned here because both are easy to get wrong.

**The context is never fed to the model.** It is applied as a deterministic
step on the model's output. The deployed weights were trained on a corpus that
contains no deployment context, so putting one in the token stream would be
out-of-distribution input to a model that cannot use it — measurable harm for no
gain. `test_the_model_input_is_untouched_by_deployment_context` is the guard.

**De-escalation is off by default.** Turning it on changes the severity returned
for every out-of-scope entity, and every figure measured so far sits between
34 % and 49 % on four classes. That is an improvement over the model and not a
working system, so it is offered rather than imposed.
"""
import pytest

from cyberscale.models.contextual import ContextualClassifier


class _Stub(ContextualClassifier):
    """Exercises the de-escalation logic without loading 600 MB of weights."""

    def __init__(self, severity="High"):
        self._severity = severity
        self.max_length = 256
        self.mc_passes = 1


def _steps(**kw):
    return _Stub()._de_escalation_steps(**kw)


# --- R1: entity outside NIS2 scope -----------------------------------------

def test_an_out_of_scope_entity_is_lowered_one_level():
    assert _steps(sector="non_nis2", entity_type=None, deployment_context=None) == 1


def test_an_annex_entity_is_not_lowered_for_scope():
    assert _steps(sector="energy", entity_type="electricity_undertaking",
                  deployment_context=None) == 0


# --- R2: the affected system is not the essential service -------------------

@pytest.mark.parametrize("context", [
    "Home user running the application on a personal laptop",
    "Single-user install on one finance workstation",
    "Departmental office tool used by 12 employees",
])
def test_a_non_essential_deployment_is_lowered(context):
    assert _steps(sector="energy", entity_type="electricity_undertaking",
                  deployment_context=context) == 1


def test_an_operational_deployment_is_not_lowered():
    assert _steps(sector="energy", entity_type="electricity_undertaking",
                  deployment_context="SCADA historian on the plant control "
                                     "network serving 400,000 customers") == 0


def test_the_two_rules_compose_and_cap_at_two():
    assert _steps(sector="non_nis2", entity_type=None,
                  deployment_context="personal home laptop, single user") == 2


# --- application ------------------------------------------------------------

def test_severity_never_falls_below_low():
    assert _Stub()._apply_de_escalation("Low", 2) == "Low"


def test_two_steps_from_critical_lands_on_medium():
    assert _Stub()._apply_de_escalation("Critical", 2) == "Medium"


def test_the_model_input_is_untouched_by_deployment_context():
    """The weights never saw this field; injecting it would be OOD input."""
    clf = _Stub()
    common = dict(description="Remote code execution in the web console",
                  sector="energy", cross_border=False, score=9.1)
    without = clf._format_input(**common)
    with_ctx = clf._format_input(**common)
    assert without == with_ctx
    assert "deployment_context" not in without
    assert "workstation" not in without.lower()
