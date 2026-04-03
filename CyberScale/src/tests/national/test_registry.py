"""Tests for the pluggable national module registry."""

from cyberscale.national.registry import get_national_module, get_available_ms


class TestNationalRegistry:
    def test_lu_module_available(self):
        module = get_national_module("LU")
        assert module is not None
        is_covered_fn, assess_fn = module
        assert callable(is_covered_fn)
        assert callable(assess_fn)

    def test_unknown_ms_returns_none(self):
        assert get_national_module("XX") is None
        assert get_national_module("DE") is None
        assert get_national_module("FR") is None

    def test_eu_returns_none(self):
        """EU-wide has no national module."""
        assert get_national_module("EU") is None

    def test_available_ms(self):
        ms_list = get_available_ms()
        assert "LU" in ms_list
        assert isinstance(ms_list, list)

    def test_lu_is_covered_fn_works(self):
        module = get_national_module("LU")
        is_covered_fn, _ = module
        assert is_covered_fn("energy", "electricity_undertaking") is True
        assert is_covered_fn("digital_infrastructure", "cloud_computing_provider") is False

    def test_lu_assess_fn_works(self):
        module = get_national_module("LU")
        _, assess_fn = module
        result = assess_fn(
            sector="energy",
            entity_type="electricity_undertaking",
            sector_specific={"voltage_level": "hv_ehv"},
        )
        assert result.significant_incident is True
        assert result.ilr_reference == "ILR/N22/4"

    def test_lazy_loading_caches(self):
        """Second call returns same module (cached)."""
        m1 = get_national_module("LU")
        m2 = get_national_module("LU")
        assert m1 is m2

    def test_be_module_available(self):
        assert "BE" in get_available_ms()

    def test_be_module_loads(self):
        module = get_national_module("BE")
        assert module is not None
        is_covered_fn, assess_fn = module
        assert callable(is_covered_fn)
        assert callable(assess_fn)
