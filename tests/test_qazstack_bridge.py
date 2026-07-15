from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import qazstack
from qazstack import __version__ as qazstack_version

from core import geofit, qazstack_bridge
from sources.kazakhstan_watch import KazakhstanWatchParser


def test_qazstack_release_dependency_is_imported_outside_the_worktree() -> None:
    """QAZ.FUND consumes the released package, not a copied source snapshot."""

    assert qazstack_version == "1.37.2"
    package_path = Path(qazstack.__file__).resolve()
    assert "site-packages" in package_path.parts
    assert not package_path.is_relative_to(Path.cwd() / "qazstack")


def test_docker_context_excludes_removed_qazstack_source_snapshot() -> None:
    """A non-destructive deploy cannot shadow the installed release wheel."""

    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "qazstack/" in dockerignore.splitlines()


def test_geo_fit_keeps_product_rules_local() -> None:
    """Kazakhstan relevance remains a QAZ.FUND editorial decision."""

    assert geofit.has_positive_geo_signal({"title": "Kazakhstan AI education grant"})


def test_geo_fit_keeps_local_kazakhstan_rules() -> None:
    item = {
        "source": "grants_gov",
        "title": "AI education grant",
        "summary": "Open to Central Asia civic technology teams.",
    }

    assert geofit.has_central_asia_geo_signal(item)
    assert not geofit.is_low_confidence_for_kazakhstan_focus(item)


def test_geo_fit_keeps_local_low_confidence_policy() -> None:
    """A global bridge without a regional signal remains low-confidence."""

    assert geofit.is_low_confidence_for_kazakhstan_focus({"source": "opportunity_desk"})


def test_source_contract_validation_uses_packaged_qazstack_release() -> None:
    qazstack_bridge._shared_source_contract_cls.cache_clear()

    assert qazstack_bridge.validate_shared_source_contract(KazakhstanWatchParser())


def test_packaged_release_falls_back_when_lifecycle_is_not_released() -> None:
    item = SimpleNamespace(
        opportunity_status=None,
        deadline=date(2026, 7, 20),
        tags=[],
        raw={},
    )

    qazstack_bridge._shared_lifecycle_functions.cache_clear()

    assert (
        qazstack_bridge.shared_normalized_status(item, today=date(2026, 7, 15)) is None
    )
    assert (
        qazstack_bridge.shared_public_lifecycle(item, today=date(2026, 7, 15)) is None
    )


def test_bridge_uses_lifecycle_after_a_compatible_release(monkeypatch) -> None:
    item = SimpleNamespace(deadline=date(2026, 7, 20), tags=[], raw={})

    monkeypatch.setattr(
        qazstack_bridge,
        "_shared_lifecycle_functions",
        lambda: (
            lambda _item, today=None: "closing_soon",
            lambda _item, today=None: "closing_soon",
        ),
    )

    assert (
        qazstack_bridge.shared_normalized_status(item, today=date(2026, 7, 15))
        == "closing_soon"
    )
    assert (
        qazstack_bridge.shared_public_lifecycle(item, today=date(2026, 7, 15))
        == "closing_soon"
    )
