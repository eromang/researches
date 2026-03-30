"""Tests for store refresh mechanism."""

import pytest
from unittest.mock import MagicMock

from cyberscale.store.refresh import StoreRefresher


def test_refresh_adds_new_cves_to_store():
    lookup = MagicMock()
    store = MagicMock()

    lookup.lookup_cve.return_value = {
        "id": "CVE-2024-1234",
        "description": "Test vulnerability.",
        "cvss_score": 7.5,
        "cvss_version": "3.1",
        "cvss_vector": None,
        "cwe": "CWE-79",
        "sources": ["nvd"],
    }

    refresher = StoreRefresher(lookup=lookup, store=store)
    refresher.refresh_cve("CVE-2024-1234")

    store.add.assert_called_once_with(
        cve_id="CVE-2024-1234",
        description="Test vulnerability.",
        cvss_score=7.5,
        cvss_version="3.1",
        cwe="CWE-79",
        source="nvd",
    )


def test_refresh_skips_when_lookup_returns_none():
    lookup = MagicMock()
    store = MagicMock()

    lookup.lookup_cve.return_value = None

    refresher = StoreRefresher(lookup=lookup, store=store)
    refresher.refresh_cve("CVE-9999-0000")

    store.add.assert_not_called()
