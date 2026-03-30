"""Tests for ChromaDB vector store client."""

import pytest

from cyberscale.store.client import VulnStore


@pytest.fixture
def store(tmp_path):
    """Create a temporary VulnStore for testing."""
    return VulnStore(persist_dir=str(tmp_path / "chromadb"))


def test_add_and_get_by_cve_id(store):
    store.add(
        cve_id="CVE-2024-1234",
        description="A buffer overflow in ExampleProduct.",
        cvss_score=7.5,
        cvss_version="3.1",
        cwe="CWE-120",
        source="nvd",
    )

    result = store.get_by_cve_id("CVE-2024-1234")
    assert result is not None
    assert result["cve_id"] == "CVE-2024-1234"
    assert result["cvss_score"] == 7.5


def test_get_nonexistent_returns_none(store):
    result = store.get_by_cve_id("CVE-9999-0000")
    assert result is None


def test_search_similar(store):
    store.add(
        cve_id="CVE-2024-1111",
        description="SQL injection vulnerability in login form allows authentication bypass.",
        cvss_score=9.8,
        source="nvd",
    )
    store.add(
        cve_id="CVE-2024-2222",
        description="Buffer overflow in image parsing library causes crash.",
        cvss_score=5.5,
        source="nvd",
    )

    results = store.search_similar(
        "SQL injection in web application authentication",
        top_k=2,
    )
    assert len(results) >= 1
    assert results[0]["cve_id"] == "CVE-2024-1111"


def test_update_existing_entry(store):
    store.add(
        cve_id="CVE-2024-1234",
        description="A vulnerability.",
        cvss_score=None,
        source="circl",
    )
    store.add(
        cve_id="CVE-2024-1234",
        description="A buffer overflow vulnerability with updated details.",
        cvss_score=7.5,
        source="nvd",
    )

    result = store.get_by_cve_id("CVE-2024-1234")
    assert result["cvss_score"] == 7.5
    assert result["source"] == "nvd"
