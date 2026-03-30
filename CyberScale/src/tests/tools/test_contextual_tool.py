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
            key_factors=["health sector", "cross-border exposure"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in clinical system",
            sector="health",
            cross_border=True,
            score=8.5,
        )
        assert result["severity"] == "Critical"
        assert result["confidence"] == "high"
        assert "health sector" in result["key_factors"]
        assert result["sector"] == "health"
        assert result["cross_border"] is True

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
            cross_border=False,
        )
        assert result["severity"] == "Medium"
        assert result["cross_border"] is False

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
            cross_border=True,
            score=9.5,
        )
        mock_clf.predict.assert_called_once_with(
            "Buffer overflow in SCADA", "transport", True, 9.5,
            deployment_scale=None, entity_type=None,
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
            cross_border=False,
        )
        mock_clf.predict.assert_called_once_with(
            "Info disclosure", "non_nis2", False, None,
            deployment_scale=None, entity_type=None,
        )

    def test_deployment_scale_and_entity_type_passed_to_model(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical",
            confidence="high",
            key_factors=["critical_operator", "hospital"],
        )
        result = _assess_with_model(
            mock_clf,
            description="RCE in medical device firmware",
            sector="health",
            cross_border=True,
            score=9.1,
            deployment_scale="critical_operator",
            entity_type="hospital",
        )
        mock_clf.predict.assert_called_once_with(
            "RCE in medical device firmware", "health", True, 9.1,
            deployment_scale="critical_operator", entity_type="hospital",
        )
        assert result["deployment_scale"] == "critical_operator"
        assert result["entity_type"] == "hospital"

    def test_deployment_scale_and_entity_type_in_output_when_provided(self):
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
            cross_border=False,
            deployment_scale="enterprise",
            entity_type="utility",
        )
        assert result["deployment_scale"] == "enterprise"
        assert result["entity_type"] == "utility"

    def test_deployment_scale_and_entity_type_absent_from_output_when_none(self):
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
            cross_border=False,
        )
        assert "deployment_scale" not in result
        assert "entity_type" not in result

    def test_deployment_scale_only_in_output_when_entity_type_none(self):
        from cyberscale.tools.contextual import _assess_with_model

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High",
            confidence="high",
            key_factors=["banking sector"],
        )
        result = _assess_with_model(
            mock_clf,
            description="SQL injection in banking portal",
            sector="banking",
            cross_border=False,
            deployment_scale="enterprise",
        )
        assert result["deployment_scale"] == "enterprise"
        assert "entity_type" not in result
