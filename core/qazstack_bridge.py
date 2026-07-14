"""Optional QazStack integration points for shared opportunity primitives."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol


class SharedGeoFitResult(Protocol):
    has_positive_signal: bool
    has_central_asia_signal: bool
    exclusion_reason: str | None
    low_confidence: bool


class SharedSourceContract(Protocol):
    def validate(self) -> None: ...


@lru_cache(maxsize=1)
def _shared_geo_evaluator():
    try:
        from qazstack.opportunities import evaluate_geo_fit
    except Exception:  # noqa: BLE001
        return None
    return evaluate_geo_fit


@lru_cache(maxsize=1)
def _shared_source_contract_cls():
    try:
        from qazstack.opportunities import SourceContract
    except Exception:  # noqa: BLE001
        return None
    return SourceContract


@lru_cache(maxsize=1)
def _shared_lifecycle_functions():
    try:
        from qazstack.opportunities import (
            normalized_opportunity_status,
            public_lifecycle,
        )
    except Exception:  # noqa: BLE001
        return None
    return normalized_opportunity_status, public_lifecycle


def evaluate_shared_geo_fit(item: Any) -> SharedGeoFitResult | None:
    """Run shared QazStack geo-fit when the package is installed."""

    evaluator = _shared_geo_evaluator()
    if evaluator is None:
        return None
    return evaluator(item)


def validate_shared_source_contract(parser: Any) -> bool:
    """Validate parser metadata against QazStack's source contract if present."""

    source_contract_cls = _shared_source_contract_cls()
    if source_contract_cls is None:
        return False
    contract: SharedSourceContract = source_contract_cls(
        slug=str(getattr(parser, "slug", "") or getattr(parser, "name", "")),
        name=str(getattr(parser, "name", "")),
        base_url=str(getattr(parser, "base_url", "")),
        request_delay=float(getattr(parser, "request_delay", 0.0)),
        default_tags=tuple(getattr(parser, "default_tags", ()) or ()),
    )
    contract.validate()
    return True


def shared_normalized_status(item: Any, *, today: Any = None) -> str | None:
    """Return QazStack's normalized status when the snapshot is available."""

    functions = _shared_lifecycle_functions()
    if functions is None:
        return None
    normalized_status, _ = functions
    return str(normalized_status(item, today=today))


def shared_public_lifecycle(item: Any, *, today: Any = None) -> str | None:
    """Return QazStack's public lifecycle when the snapshot is available."""

    functions = _shared_lifecycle_functions()
    if functions is None:
        return None
    _, lifecycle = functions
    return str(lifecycle(item, today=today))
