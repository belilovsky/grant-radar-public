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
    assert 'href="#opportunities"' in html
    assert 'href="#sources"' in html
    assert "syncFilterDisclosureForViewport" in html
    assert 'data-avds-pattern="filter-state-summary"' in html
    assert 'data-avds-pattern="evidence-summary"' in html
    assert 'data-avds-pattern="decision-summary"' in html
    assert 'data-avds-component="trust-strip"' in html
    assert 'data-avds-version="4.6.0"' in html
    assert "const PUBLIC_TIME_ZONE" in html
    assert "function publicDateISO" in html
    assert "getTimezoneOffset" not in html
    assert "Глобальный рынок ООН" in html
    assert "Закупки ОБСЕ" in html
    assert "const label = sourceDisplayName(source)" in html
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in DASHBOARD_CSS
    assert ".hero-pick:last-child { grid-column: 1 / -1; }" in DASHBOARD_CSS
    assert "@media (min-width: 1440px)" in DASHBOARD_CSS
    assert ".hero-points {" in DASHBOARD_CSS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in DASHBOARD_CSS
    assert "--panel-wash-card: color-mix" in DASHBOARD_CSS
    assert "background: var(--panel-wash-list);" in DASHBOARD_CSS
    assert "border-radius: var(--av-radius-md);" in DASHBOARD_CSS
