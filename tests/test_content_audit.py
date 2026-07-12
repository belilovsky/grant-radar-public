"""Tests for live content audit analysis helpers."""

from __future__ import annotations

from datetime import datetime, timezone

try:
    UTC = timezone.utc
except AttributeError:  # pragma: no cover - Python < 3.11 compatibility
    from datetime import UTC

from scripts.content_audit import analyze_content


def test_content_audit_flags_forbidden_and_missing_summary():
    result = analyze_content(
        coverage={
            "enabled_sources": 19,
            "relevant_open_items": 2,
            "sources": [
                {
                    "slug": "active_source",
                    "enabled": True,
                    "items": 2,
                    "last_discovered_at": "2099-01-01T00:00:00+00:00",
                },
                {
                    "slug": "empty_source",
                    "enabled": True,
                    "items": 0,
                    "last_discovered_at": None,
                },
            ],
        },
        opportunities=[
            {
                "title": "AI3 Action Institute - Artificial Intelligence for American Indians",
                "summary": "",
                "tags": ["grant"],
            },
            {
                "title": "Rolling startup credits",
                "summary": "Cloud credits for startups.",
                "tags": ["rolling"],
            },
        ],
        forbidden_terms=["AI3 Action Institute"],
        min_sources=19,
        min_opportunities=2,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "needs_attention"
    assert result.zero_item_sources == ["empty_source"]
    assert result.missing_summary_titles == [
        "AI3 Action Institute - Artificial Intelligence for American Indians"
    ]
    assert result.short_summary_titles == ["Rolling startup credits"]
    assert result.missing_deadline_titles == [
        "AI3 Action Institute - Artificial Intelligence for American Indians"
    ]
    assert result.rootish_source_urls == ["", ""]
    assert result.forbidden_hits == {
        "AI3 Action Institute": [
            "AI3 Action Institute - Artificial Intelligence for American Indians"
        ]
    }


def test_content_audit_accepts_clean_rolling_items():
    result = analyze_content(
        coverage={
            "enabled_sources": 19,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "startup",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "title": "Global startup support",
                "summary": (
                    "Open rolling support for Central Asia startups with a direct "
                    "application route and clear eligibility notes."
                ),
                "tags": ["rolling", "central_asia_eligible"],
                "source_url": "https://example.org/programs/global-startup-support",
            }
        ],
        forbidden_terms=["AI3 Action Institute"],
        min_sources=19,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.issues == []
    assert result.missing_deadline_titles == []
    assert result.rootish_source_urls == []


def test_content_audit_allows_closed_seasonal_source_without_items():
    result = analyze_content(
        coverage={
            "enabled_sources": 2,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "active_source",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-07-13T00:00:00+00:00",
                },
                {
                    "slug": "canada_cfli_ca",
                    "enabled": True,
                    "items": 0,
                    "last_discovered_at": None,
                },
            ],
        },
        opportunities=[
            {
                "title": "Central Asia innovation support",
                "summary": (
                    "Current support opportunity with a verified official source, "
                    "clear regional scope and an explicit rolling deadline policy."
                ),
                "tags": ["rolling", "central_asia"],
                "source_url": "https://example.org/opportunities/current-call",
            }
        ],
        forbidden_terms=[],
        min_sources=2,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.zero_item_sources == []


def test_content_audit_flags_tags_without_public_localization():
    result = analyze_content(
        coverage={
            "enabled_sources": 1,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "startup",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "title": "Capacity building program",
                "summary": (
                    "A detailed public program summary with enough context for teams "
                    "to understand the opportunity and verify the official source."
                ),
                "tags": ["rolling", "capacity_building"],
                "source_url": "https://example.org/programs/capacity-building",
            }
        ],
        forbidden_terms=[],
        min_sources=1,
        min_opportunities=1,
        stale_after_days=7,
        label_maps={
            "ru": {"rolling": "Бессрочно"},
            "en": {
                "rolling": "Rolling",
                "capacity_building": "Capacity building",
            },
        },
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "needs_attention"
    assert result.unlocalized_tags == {"ru": ["capacity_building"]}
    assert "public tags are missing localized display labels" in result.issues


def test_content_audit_ignores_html_entities_inside_raw_source_snippets():
    result = analyze_content(
        coverage={
            "enabled_sources": 19,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "adb",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "title": "Kazakhstan project financing",
                "summary": (
                    "Clear public summary for a Kazakhstan infrastructure and "
                    "business-support opportunity with a direct source page."
                ),
                "tags": ["rolling", "kazakhstan"],
                "source_url": "https://example.org/projects/123/main",
                "raw": {"snippet": "Original upstream HTML has &nbsp; and &amp;."},
            }
        ],
        forbidden_terms=["AI3 Action Institute"],
        min_sources=19,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.html_entity_titles == []


def test_content_audit_flags_domestic_items_without_detail_contract():
    result = analyze_content(
        coverage={
            "enabled_sources": 23,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "kazakhstan_domestic_support",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "source": "kazakhstan_domestic_support",
                "title": "State grant for startup business development",
                "summary": (
                    "Official Enbek page for grants issued free of charge for "
                    "startup-business development."
                ),
                "tags": ["rolling", "kazakhstan", "domestic_support"],
                "source_url": "https://www.enbek.kz/ru/node/3481",
                "raw": {},
            }
        ],
        forbidden_terms=["AI3 Action Institute"],
        min_sources=23,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "needs_attention"
    assert result.missing_detail_status_titles == [
        "State grant for startup business development"
    ]
