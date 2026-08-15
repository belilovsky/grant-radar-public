"""Regression tests for the dashboard module boundaries."""

from api import dashboard
from api.avds_visual import DASHBOARD_AVDS4_CSS
from api.dashboard_copy import dashboard_copy as canonical_dashboard_copy
from api.dashboard_style import DASHBOARD_CSS


def test_dashboard_reexports_canonical_copy_helper() -> None:
    assert dashboard.dashboard_copy is canonical_dashboard_copy
    assert dashboard.dashboard_copy("unsupported")["lang"] == "ru"
    assert dashboard.dashboard_copy("kk")["lang"] == "kk"
    assert dashboard.dashboard_copy("kk")["headline"] == "QAZ.FUND"
    assert dashboard.dashboard_copy("ru")["detail_readiness_title"] == (
        "Полнота данных"
    )


def test_dashboard_uses_extracted_static_styles() -> None:
    html = dashboard.render_dashboard(
        root_path="",
        items=0,
        relevant_items=0,
        source_count=0,
        lang="ru",
        site_origin="https://qaz.fund",
    )

    assert DASHBOARD_CSS in html
    assert DASHBOARD_AVDS4_CSS in html
    assert "--container-max: var(--av-container-dashboard)" in DASHBOARD_CSS
    assert 'class="site-footer-nav"' in html
    assert 'data-view="opportunities"' in html
    assert 'data-view="sources"' not in html
    assert "syncFilterDisclosureForViewport" in html
    assert 'data-avds-pattern="filter-state-summary"' in html
    assert 'data-avds-pattern="evidence-summary"' in html
    assert 'data-avds-pattern="catalog-card"' in html
    assert 'data-avds-component="trust-strip"' in html
    assert 'data-avds-version="4.6.0"' in html
    assert 'data-avds-component="quick-links-rail"' not in html
    assert 'data-avds-component="public-summary-strip"' not in html
    assert "qaz-fund-ornamental-background-1920x1080.webp" in html
    assert "radial-gradient(circle at 92% 6%" not in html
    assert "#F0C64D" not in html
    assert html.count("<h1>") == 1
    assert html.count('class="topbar"') == 1
    assert "const PUBLIC_TIME_ZONE" in html
    assert "function publicDateISO" in html
    assert "getTimezoneOffset" not in html
    assert "Глобальный рынок ООН" in html
    assert "Закупки ОБСЕ" in html
    assert "const label = sourceDisplayName(source)" in html
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in DASHBOARD_CSS
    assert "@media (min-width: 1440px)" in DASHBOARD_CSS
    assert "grid-template-columns: minmax(0, 1fr);" in DASHBOARD_AVDS4_CSS
    assert ".opportunity-facts {" in DASHBOARD_AVDS4_CSS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in DASHBOARD_CSS
    assert "--panel-wash-card: color-mix" in DASHBOARD_CSS
    assert "background: var(--panel-wash-list);" in DASHBOARD_CSS
    assert "border-radius: var(--av-radius-md);" in DASHBOARD_CSS
    assert ".hero-copy > .topbar {" in DASHBOARD_CSS
    assert '<section\n          class="hero-stage"' not in html

    preset_button_block = DASHBOARD_CSS.split(".preset-button {", 1)[1].split("}", 1)[0]
    assert "background: var(--brand-soft);" in preset_button_block
    assert (
        "border: 1px solid color-mix(in oklab, var(--brand), var(--line) 72%);"
        in preset_button_block
    )

    mobile_touch_block = DASHBOARD_AVDS4_CSS.split("@media (max-width: 820px) {", 1)[
        1
    ].split("@media (max-width: 560px)", 1)[0]
    for selector in (
        ".mobile-app-brand",
        ".mobile-lang-switch a",
        ".mobile-icon-button",
        ".hero-actions .button",
        ".preset-button",
        ".detail-link",
        ".advanced-filters > summary",
    ):
        assert selector in mobile_touch_block
    assert "min-height: var(--av-control-height-lg);" in mobile_touch_block
    assert "min-width: var(--av-control-height-lg);" in mobile_touch_block


def test_dashboard_secondary_mobile_links_keep_avds_touch_targets() -> None:
    mobile_block = DASHBOARD_CSS.split("@media (max-width: 820px) {", 1)[1]

    for selector in (
        ".more-link",
        ".opportunity h3 a",
        ".site-footer-nav a",
        ".site-footer > p a",
    ):
        assert selector in mobile_block
    assert "min-height: var(--av-control-height-lg);" in mobile_block
