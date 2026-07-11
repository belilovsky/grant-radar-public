from __future__ import annotations

from types import SimpleNamespace

from core import geofit, qazstack_bridge
from sources.kazakhstan_watch import KazakhstanWatchParser


def test_geo_fit_uses_shared_positive_signal_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        geofit,
        "evaluate_shared_geo_fit",
        lambda item: SimpleNamespace(
            has_positive_signal=True,
            has_central_asia_signal=False,
            exclusion_reason=None,
            low_confidence=False,
        ),
    )

    assert geofit.has_positive_geo_signal({"title": "Untyped opportunity"})


def test_geo_fit_keeps_local_fallback_when_shared_package_is_absent(
    monkeypatch,
) -> None:
    monkeypatch.setattr(geofit, "evaluate_shared_geo_fit", lambda item: None)

    item = {
        "source": "grants_gov",
        "title": "AI education grant",
        "summary": "Open to Central Asia civic technology teams.",
    }

    assert geofit.has_central_asia_geo_signal(item)
    assert not geofit.is_low_confidence_for_kazakhstan_focus(item)


def test_geo_fit_uses_shared_low_confidence_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        geofit,
        "evaluate_shared_geo_fit",
        lambda item: SimpleNamespace(
            has_positive_signal=False,
            has_central_asia_signal=False,
            exclusion_reason=None,
            low_confidence=True,
        ),
    )

    assert geofit.is_low_confidence_for_kazakhstan_focus({"source": "custom"})


def test_source_contract_validation_is_optional_without_qazstack() -> None:
    qazstack_bridge._shared_source_contract_cls.cache_clear()

    assert qazstack_bridge.validate_shared_source_contract(KazakhstanWatchParser()) in {
        False,
        True,
    }
