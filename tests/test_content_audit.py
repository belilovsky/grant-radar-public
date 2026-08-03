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


def test_content_audit_uses_recent_successful_check_for_unchanged_monitor():
    result = analyze_content(
        coverage={
            "enabled_sources": 1,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "unchanged_monitor",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-07-01T00:00:00+00:00",
                    "last_checked_at": "2026-08-03T00:00:00+00:00",
                    "freshness_basis": "source_check",
                }
            ],
        },
        opportunities=[
            {
                "title": "Monitored support program",
                "summary": (
                    "An unchanged official program page checked recently; verify "
                    "the current terms before taking action."
                ),
                "tags": ["rolling"],
                "source_url": "https://example.org/programs/monitor",
            }
        ],
        forbidden_terms=[],
        min_sources=1,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 8, 3, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.stale_sources == []


def test_content_audit_accepts_source_policy_and_archived_items_without_dates():
    result = analyze_content(
        coverage={
            "enabled_sources": 2,
            "relevant_open_items": 2,
            "sources": [
                {
                    "slug": "watch",
                    "enabled": True,
                    "items": 2,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "title": "Forecast call",
                "summary": (
                    "Forecast record with an explicit source policy; verify the next "
                    "official notice before preparing an application."
                ),
                "tags": ["grant"],
                "raw": {"deadline_policy": "verify_notice_no_search_close_date"},
                "source_url": "https://example.org/programs/forecast-call",
            },
            {
                "title": "Awarded cycle archive",
                "summary": (
                    "Archived results record for historical analysis; it is not an "
                    "open application and has no active submission window."
                ),
                "tags": ["results_archive"],
                "lifecycle": "awarded",
                "source_url": "https://example.org/archive/2020",
            },
        ],
        forbidden_terms=[],
        min_sources=2,
        min_opportunities=2,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.missing_deadline_titles == []


def test_content_audit_accepts_monitored_watch_records_without_dates():
    result = analyze_content(
        coverage={
            "enabled_sources": 1,
            "relevant_open_items": 1,
            "sources": [
                {
                    "slug": "watch",
                    "enabled": True,
                    "items": 1,
                    "last_discovered_at": "2026-05-25T00:00:00+00:00",
                }
            ],
        },
        opportunities=[
            {
                "title": "Monitored programme page",
                "summary": (
                    "A monitored official page whose current call window must be "
                    "verified before any submission is prepared."
                ),
                "tags": ["grant"],
                "source_url": "https://example.org/programmes/current",
                "raw": {
                    "source_watch": True,
                    "verification_note": "Verify the current call window on the source.",
                },
            }
        ],
        forbidden_terms=[],
        min_sources=1,
        min_opportunities=1,
        stale_after_days=7,
        now=datetime(2026, 5, 25, tzinfo=UTC),
    )

    assert result.status == "ok"
    assert result.missing_deadline_titles == []


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
