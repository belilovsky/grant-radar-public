"""Publication safety boundary tests."""

from core.content_safety import blocked_publication_reason, is_publication_blocked


def test_blocks_confirmed_impersonation_destination_host():
    item = {
        "title": "Generic business grant",
        "source_url": "https://www.ifcgrants.org/apply",
    }

    assert blocked_publication_reason(item) == (
        "blocked_destination_host:ifcgrants.org"
    )
    assert is_publication_blocked(item)


def test_blocks_secondary_publication_for_confirmed_unsafe_program():
    item = {
        "title": "International Finance Corporation (IFC) Women-Led Business Grant 2026",
        "source_url": (
            "https://opportunitydesk.org/2026/06/30/"
            "ifc-women-led-business-grant-2026/"
        ),
    }

    assert blocked_publication_reason(item) == (
        "blocked_publication_marker:ifc-women-led-business-grant-2026"
    )


def test_allows_unrelated_official_ifc_material():
    item = {
        "title": "IFC climate finance report",
        "source_url": "https://www.ifc.org/en/insights-reports/2026/climate-finance",
    }

    assert blocked_publication_reason(item) is None
    assert not is_publication_blocked(item)
