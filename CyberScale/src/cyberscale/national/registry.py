"""Pluggable national module registry.

Maps member state codes to national assessment modules. The router in
entity_incident.py uses this registry to find national threshold logic.
"""

from __future__ import annotations

from typing import Callable


def _load_lu():
    from cyberscale.national.lu import is_lu_covered, assess_lu_significance
    return is_lu_covered, assess_lu_significance


def _load_be():
    from cyberscale.national.be import is_be_covered, assess_be_significance
    return is_be_covered, assess_be_significance


# Registry: MS code → lazy loader returning (is_covered_fn, assess_fn)
_NATIONAL_LOADERS: dict[str, Callable] = {
    "LU": _load_lu,
    "BE": _load_be,
    # Future: "DE": _load_de, "FR": _load_fr, etc.
}

_loaded_modules: dict[str, tuple] = {}


def get_national_module(ms: str) -> tuple | None:
    """Return (is_covered_fn, assess_fn) for a member state, or None.

    Lazy-loads the module on first access.
    """
    if ms not in _NATIONAL_LOADERS:
        return None

    if ms not in _loaded_modules:
        _loaded_modules[ms] = _NATIONAL_LOADERS[ms]()

    return _loaded_modules[ms]


def get_available_ms() -> list[str]:
    """Return list of member states with national modules."""
    return list(_NATIONAL_LOADERS.keys())
