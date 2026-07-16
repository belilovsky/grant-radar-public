"""Focused regression coverage for the public source-status page."""

from api.status_page import render_status_page


def test_status_page_keeps_last_check_visible_in_mobile_rows() -> None:
    html = render_status_page(
        coverage={
            "sources": [
                {
                    "enabled": True,
                    "name": "Example source",
                    "base_url": "https://example.org/programs",
                    "items": 4,
                    "relevant_open_items": 2,
                    "last_checked_at": "2026-07-17T08:30:00Z",
                    "freshness_status": "fresh",
                }
            ],
            "enabled_sources": 1,
            "fresh_sources": 1,
            "stale_sources": 0,
            "unknown_freshness_sources": 0,
        },
        lang="ru",
    )

    assert 'class="mobile-updated"' in html
    assert "Последняя проверка: 17.07.2026 08:30 UTC" in html
    assert ".mobile-updated { display:block; }" in html
