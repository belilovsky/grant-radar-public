"""Focused regression coverage for the public source-status page."""

from api.status_page import render_status_page


def test_status_page_keeps_last_check_visible_in_mobile_rows() -> None:
    html = render_status_page(
        coverage={
            "sources": [
                {
                    "enabled": True,
                    "name": "Example source",
                    "slug": "kazakhstan_domestic_support",
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
    assert 'href="mailto:contact@qaz.fund"' in html
    assert "Поддержка РК" in html
    assert "tbody tr:nth-child(even)" in html


def test_status_page_labels_partial_source_check() -> None:
    html = render_status_page(
        coverage={
            "sources": [
                {
                    "enabled": True,
                    "name": "Kazakhstan domestic support",
                    "slug": "kazakhstan_domestic_support",
                    "items": 56,
                    "relevant_open_items": 50,
                    "freshness_status": "watch",
                }
            ],
            "enabled_sources": 1,
            "fresh_sources": 0,
            "stale_sources": 0,
            "watch_sources": 1,
            "unknown_freshness_sources": 0,
        },
        lang="ru",
    )

    assert "Проверен частично" in html
    assert 'class="state state--watch"' in html
    assert "<strong>1</strong>" in html


def test_status_page_has_editorial_kazakh_shell_and_three_language_switch() -> None:
    html = render_status_page(
        coverage={"sources": [], "enabled_sources": 0},
        lang="kk",
    )

    assert '<html lang="kk"' in html
    assert "Дереккөздер мәртебесі" in html
    assert 'href="/status?lang=kk" lang="kk" aria-current="page"' in html
    assert 'href="/status?lang=ru" lang="ru"' in html
    assert 'href="/status?lang=en" lang="en"' in html


def test_status_page_has_share_preview_metadata() -> None:
    html = render_status_page(
        coverage={"sources": [], "enabled_sources": 0},
        lang="en",
        site_origin="https://qaz.fund",
    )

    assert 'property="og:type" content="website"' in html
    assert 'property="og:url" content="https://qaz.fund/status?lang=en"' in html
    assert 'property="og:image" content="https://qaz.fund/og-image.png?lang=en"' in html
    assert (
        'property="og:image:alt" content="QAZ.FUND: find, verify, compare and '
        'prepare a support programme"' in html
    )
    assert 'name="twitter:card" content="summary_large_image"' in html
    assert (
        'name="twitter:image" content="https://qaz.fund/og-image.png?lang=en"' in html
    )


def test_status_page_localizes_source_names_in_kazakh() -> None:
    html = render_status_page(
        coverage={
            "sources": [
                {
                    "enabled": True,
                    "name": "Kazakhstan domestic support",
                    "slug": "kazakhstan_domestic_support",
                    "base_url": "https://example.org/programs",
                    "items": 2,
                    "relevant_open_items": 1,
                    "freshness_status": "fresh",
                }
            ],
            "enabled_sources": 1,
            "fresh_sources": 1,
        },
        lang="kk",
    )

    assert "Қазақстандағы қолдау бағдарламалары" in html
    assert "Kazakhstan domestic support" not in html


def test_status_page_keeps_official_name_when_slug_has_no_curated_label() -> None:
    html = render_status_page(
        coverage={
            "sources": [
                {
                    "enabled": True,
                    "name": "Grants.gov (US Federal)",
                    "slug": "grants_gov",
                    "base_url": "https://grants.gov",
                    "items": 1,
                    "relevant_open_items": 1,
                    "freshness_status": "fresh",
                }
            ],
            "enabled_sources": 1,
            "fresh_sources": 1,
        },
        lang="en",
    )

    assert "Grants.gov (US Federal)" in html
    assert "grants gov" not in html
