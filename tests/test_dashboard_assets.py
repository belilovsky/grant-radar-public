"""Regression tests for the dashboard module boundaries."""

from api import dashboard
from api.dashboard_copy import dashboard_copy as canonical_dashboard_copy
from api.dashboard_style import DASHBOARD_CSS


def test_dashboard_reexports_canonical_copy_helper() -> None:
    assert dashboard.dashboard_copy is canonical_dashboard_copy
    assert dashboard.dashboard_copy("unsupported")["lang"] == "ru"


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
    assert "--container-max: var(--av-container-dashboard)" in DASHBOARD_CSS
    assert 'class="site-footer-nav"' in html
    assert 'href="#opportunities"' in html
    assert 'href="#sources"' in html
    assert "syncFilterDisclosureForViewport" in html
    assert 'data-avds-pattern="filter-state-summary"' in html
    assert 'data-avds-pattern="evidence-summary"' in html
    assert 'data-avds-pattern="decision-summary"' in html
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in DASHBOARD_CSS
    assert ".hero-pick:last-child { grid-column: 1 / -1; }" in DASHBOARD_CSS
