"""Tests for Phase 2 contextual severity MCP tool helpers."""

from unittest.mock import MagicMock

from cyberscale.models.contextual import ContextualResult


class TestAssessContextualSeverity:
    def test_model_prediction_returned(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical",
            confidence="high",
            key_factors=["health sector", "cross-border exposure (2 MS affected)"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in clinical system",
            sector="health",
            ms_established="DE",
            ms_affected=["FR", "NL"],
            score=8.5,
        )
        assert result["severity"] == "Critical"
        assert result["confidence"] == "high"
        assert "health sector" in result["key_factors"]
        assert result["sector"] == "health"
        assert result["ms_established"] == "DE"
        assert result["cross_border"] is True
        assert result["ms_affected"] == ["FR", "NL"]

    def test_invalid_sector_returns_error(self):
        from cyberscale.tools.contextual import _validate_sector

        ok, err = _validate_sector("health")
        assert ok is True
        assert err == ""

        ok, err = _validate_sector("invalid")
        assert ok is False
        assert "Unknown sector" in err

    def test_no_cross_border(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium",
            confidence="medium",
            key_factors=["energy sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="DoS in web app",
            sector="energy",
            ms_established="FR",
        )
        assert result["severity"] == "Medium"
        assert result["cross_border"] is False
        assert "ms_affected" not in result

    def test_all_valid_sectors_accepted(self):
        from cyberscale.tools.contextual import VALID_SECTORS, _validate_sector

        for sector in VALID_SECTORS:
            ok, err = _validate_sector(sector)
            assert ok is True, f"Sector {sector} should be valid"

    def test_score_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High",
            confidence="high",
            key_factors=["transport sector", "critical base score"],
        )
        _assess_with_model(
            mock_clf,
            description="Buffer overflow in SCADA",
            sector="transport",
            ms_established="DE",
            ms_affected=["FR"],
            score=9.5,
        )
        mock_clf.predict.assert_called_once_with(
            "Buffer overflow in SCADA", "transport",
            ms_established="DE", ms_affected=["FR"],
            score=9.5, entity_type=None, cer_critical_entity=None,
        )

    def test_score_none_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
        )
        mock_clf.predict.assert_called_once_with(
            "Info disclosure", "non_nis2",
            ms_established="EU", ms_affected=None,
            score=None, entity_type=None, cer_critical_entity=None,
        )

    def test_entity_type_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical",
            confidence="high",
            key_factors=["healthcare_provider entity"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in medical device firmware",
            sector="health",
            ms_established="DE",
            ms_affected=["FR"],
            score=9.1,
            entity_type="healthcare_provider",
        )
        mock_clf.predict.assert_called_once_with(
            "RCE in medical device firmware", "health",
            ms_established="DE", ms_affected=["FR"],
            score=9.1, entity_type="healthcare_provider", cer_critical_entity=None,
        )
        assert result["entity_type"] == "healthcare_provider"

    def test_entity_type_absent_from_output_when_none(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
        )
        assert "entity_type" not in result

    def test_deployment_scale_not_accepted(self):
        """deployment_scale was removed in v3."""
        from cyberscale.tools.contextual import _assess_with_model
        import inspect
        sig = inspect.signature(_assess_with_model)
        assert "deployment_scale" not in sig.parameters

    def test_cross_border_not_direct_param(self):
        """cross_border is now derived, not a direct parameter."""
        from cyberscale.tools.contextual import _assess_with_model
        import inspect
        sig = inspect.signature(_assess_with_model)
        assert "cross_border" not in sig.parameters
        assert "ms_established" in sig.parameters
        assert "ms_affected" in sig.parameters


class TestCerCriticalEntity:
    def test_cer_critical_entity_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High",
            confidence="high",
            key_factors=["food sector", "CER critical entity (essential override)"],
        )
        result = _assess_with_model(
            mock_clf,
            description="DoS in food supply chain",
            sector="food",
            entity_type="food_producer",
            cer_critical_entity=True,
        )
        mock_clf.predict.assert_called_once_with(
            "DoS in food supply chain", "food",
            ms_established="EU", ms_affected=None,
            score=None, entity_type="food_producer", cer_critical_entity=True,
        )
        assert result["cer_critical_entity"] is True

    def test_cer_critical_entity_absent_when_none(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low",
            confidence="low",
            key_factors=["non_nis2 sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="Info disclosure",
            sector="non_nis2",
        )
        assert "cer_critical_entity" not in result

    def test_cer_critical_entity_false_absent(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium",
            confidence="medium",
            key_factors=["food sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="XSS in food portal",
            sector="food",
            entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert "cer_critical_entity" not in result
