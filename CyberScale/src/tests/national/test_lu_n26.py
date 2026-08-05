"""Tests for the draft ILR/N26 important-incident criteria (CP/N26/2)."""

import pytest

from cyberscale.national.lu_n26 import (
    assess_lu_n26_significance,
    assess_recurrence,
    notification_deadlines,
)


def test_one_hour_disruption_triggers():
    """Art. 2(1)(a) — more than one hour, regardless of sector."""
    r = assess_lu_n26_significance(service_impact="degraded", impact_duration_hours=1.5)
    assert r.significant_incident
    assert any("2(1)(a)" in c for c in r.triggered_criteria)


def test_exactly_one_hour_does_not_trigger_on_duration():
    """'plus d'une heure' is strict: 1.0h is not more than one hour."""
    r = assess_lu_n26_significance(service_impact="unavailable", impact_duration_hours=1.0,
                                   users_affected_pct_lu=1.0)
    assert not any("2(1)(a)" in c for c in r.triggered_criteria)


def test_five_percent_users_triggers_without_duration():
    """The two limbs of (a) are alternatives: a short outage still triggers on reach."""
    r = assess_lu_n26_significance(service_impact="degraded", impact_duration_hours=0.25,
                                   users_affected_pct_lu=7.5)
    assert r.significant_incident


def test_fifty_users_cia_threshold():
    """Art. 2(1)(c) — strictly more than 50 users."""
    assert assess_lu_n26_significance(data_impact="accessed", affected_persons_count=51).significant_incident
    r = assess_lu_n26_significance(data_impact="accessed", affected_persons_count=50)
    assert not any("2(1)(c)" in c for c in r.triggered_criteria)


def test_cross_border_alone_triggers():
    """Art. 2(1)(e) has no magnitude qualifier at all."""
    r = assess_lu_n26_significance(cross_border=True)
    assert r.significant_incident
    assert any("2(1)(e)" in c for c in r.triggered_criteria)


def test_financial_threshold_is_the_lower_of_the_two():
    """Art. 2(1)(j) — 'le montant le plus faible étant retenu'.

    A small entity's 5% binds well below EUR 500 000.
    """
    r = assess_lu_n26_significance(direct_financial_loss_eur=60_000, annual_turnover_eur=1_000_000)
    assert r.significant_incident, "5% of 1M = 50k, so a 60k loss triggers"
    r2 = assess_lu_n26_significance(direct_financial_loss_eur=60_000, annual_turnover_eur=100_000_000)
    assert not any("2(1)(j)" in c for c in r2.triggered_criteria), "threshold stays at 500k for a large entity"


def test_scheduled_maintenance_is_excluded():
    """Art. 2(2) — planned interruptions are not important incidents."""
    r = assess_lu_n26_significance(service_impact="unavailable", impact_duration_hours=10,
                                   scheduled_maintenance=True)
    assert not r.significant_incident
    assert "2(2)" in r.excluded_reason


def test_ir_entities_are_out_of_scope():
    """Art. 2(6) — IR (EU) 2024/2690 entities are not displaced by this regulation."""
    r = assess_lu_n26_significance(entity_type="cloud_computing_provider",
                                   service_impact="unavailable", impact_duration_hours=48)
    assert not r.significant_incident
    assert "2(6)" in r.excluded_reason


def test_missing_inputs_are_not_evaluable_not_negative():
    """A field CyberScale does not carry must read as unknown, never as 'did not trigger'."""
    r = assess_lu_n26_significance(service_impact="degraded", impact_duration_hours=2)
    assert r.significant_incident
    joined = " ".join(r.not_evaluable)
    for art in ("2(1)(d)", "2(1)(f)", "2(1)(j)", "2(1)(k)", "2(1)(l)"):
        assert art in joined, f"{art} should be reported as not evaluable"


def test_annex_criteria_always_unknown():
    """Art. 2(1)(l) cannot be evaluated: the annexes were not published."""
    r = assess_lu_n26_significance(cross_border=True)
    assert any("2(1)(l)" in u for u in r.not_evaluable)


def test_recurrence_needs_all_three_conditions():
    """Art. 2(4) — two occurrences, six months, same root cause, and criterion (j)."""
    ok = assess_recurrence(occurrences=3, window_months=4, same_root_cause=True,
                           combined_direct_loss_eur=600_000)
    assert ok.significant_incident

    assert not assess_recurrence(occurrences=1, window_months=4, same_root_cause=True,
                                 combined_direct_loss_eur=600_000).significant_incident
    assert not assess_recurrence(occurrences=3, window_months=9, same_root_cause=True,
                                 combined_direct_loss_eur=600_000).significant_incident
    assert not assess_recurrence(occurrences=3, window_months=4, same_root_cause=False,
                                 combined_direct_loss_eur=600_000).significant_incident

    unknown = assess_recurrence(occurrences=3, window_months=4, same_root_cause=True)
    assert not unknown.significant_incident
    assert unknown.not_evaluable, "missing loss must be unknown, not a clean negative"


def test_trust_service_provider_has_24h_derogation():
    """Art. 3(5) — 24h rather than 72h for trust services."""
    assert notification_deadlines("trust_service_provider")["incident_notification_hours"] == 24
    assert notification_deadlines("healthcare_provider")["incident_notification_hours"] == 72
    assert notification_deadlines()["preliminary_hours"] == 24
    assert notification_deadlines()["final_report_days"] == 30


def test_result_flags_draft_status():
    """The result must never be mistaken for an in-force assessment."""
    r = assess_lu_n26_significance(cross_border=True)
    assert r.in_force is False
    assert "draft" in r.regulation.lower()


def test_ir_scope_follows_article_1_not_our_entity_list():
    """IR (EU) 2024/2690 Art. 1 names eleven entity types; telecom is not among them."""
    from cyberscale.national.lu_n26 import ir_scope, _IR_TITLE_ENTITY_TYPES

    assert len(_IR_TITLE_ENTITY_TYPES) == 11
    assert ir_scope("trust_service_provider") == "ir"
    assert ir_scope("cloud_computing_provider") == "ir"
    # Removed from ir_incident_thresholds.json on 2026-08-05 — verified against the OJ text
    for e in ("ixp_operator", "public_ecn_provider", "public_ecs_provider"):
        assert ir_scope(e) == "national", f"{e} is not in IR Art. 1 scope"

    r = assess_lu_n26_significance(entity_type="public_ecn_provider",
                                   service_impact="unavailable", impact_duration_hours=3.5)
    assert r.significant_incident and r.excluded_reason is None
