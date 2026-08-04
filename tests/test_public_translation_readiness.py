from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qazfund_public_translation_readiness",
    ROOT / "scripts/check_public_translation_readiness.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_public_readiness_uses_aggregate_only_and_holds_without_approval() -> None:
    items = [
        {
            "raw": {
                "i18n": {"ru": {"title": "RU source"}, "en": {"title": "EN copy"}},
            }
        },
        {
            "raw": {
                "i18n": {"kk": {"title": "KK candidate"}},
            }
        },
    ]

    report = MODULE.summarize_items(items)

    assert report["item_count"] == 2
    assert report["locale_item_counts"] == {"kk": 1, "ru": 1, "en": 1}
    assert report["locale_field_counts"] == {"kk": 1, "ru": 1, "en": 1}
    assert report["kk_content_coverage_rate"] == 0.5
    assert report["source_language_metadata_count"] == 0
    assert report["reviewer_ref_count"] == 0
    assert report["quality_score_count"] == 0
    assert report["approved_only_ready_count"] == 0
    assert "RU source" not in str(report)
    assert "KK candidate" not in str(report)


def test_public_readiness_counts_detail_language_as_source_metadata() -> None:
    report = MODULE.summarize_items(
        [{"raw": {"detail_language": "ru"}}, {"raw": {"title": "No language"}}]
    )

    assert report["source_language_metadata_count"] == 1
