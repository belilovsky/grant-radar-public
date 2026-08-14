from __future__ import annotations

from datetime import date

from core.models import Opportunity, OpportunityType
from core.opportunity_taxonomy import (
    classify_opportunity,
    template_accepts_taxonomy,
)


def _item(*, item_type: OpportunityType, tags: list[str], raw: dict | None = None):
    return Opportunity(
        source="official",
        source_url="https://example.org/call",
        type=item_type,
        title="Проверенная программа для Казахстана",
        summary="Официальные условия",
        deadline=date(2026, 9, 1),
        eligibility=["Заявители из Казахстана"],
        tags=tags,
        raw=raw or {},
    )


def test_college_state_order_is_admission_not_grant() -> None:
    item = _item(
        item_type=OpportunityType.GRANT,
        tags=["education_admission", "state_funded_seat", "education"],
        raw={
            "opportunity_taxonomy": {
                "instrument": "education_admission",
                "application_mode": "admission",
                "deadline_model": "multiple",
            },
            "application_windows": [
                {"route": "working_qualifications", "deadline": "2026-08-27"}
            ],
        },
    )

    taxonomy = classify_opportunity(item)

    assert taxonomy["instrument"] == "education_admission"
    assert taxonomy["benefit_type"] == "tuition_coverage"
    assert taxonomy["application_mode"] == "admission"
    assert taxonomy["deadline_model"] == "multiple"
    assert taxonomy["content_track"] == "education"
    assert taxonomy["publication_scope"] == "dedicated"
    assert template_accepts_taxonomy("grant_day", taxonomy) is False
    assert template_accepts_taxonomy("opportunity_day", taxonomy) is False
    assert template_accepts_taxonomy("education_day", taxonomy) is True


def test_cash_grant_and_procurement_use_different_tracks() -> None:
    grant = classify_opportunity(
        _item(item_type=OpportunityType.GRANT, tags=["grant", "startup"])
    )
    procurement = classify_opportunity(
        _item(item_type=OpportunityType.TENDER, tags=["procurement", "business"])
    )

    assert grant["benefit_type"] == "cash_nonrepayable"
    assert grant["content_track"] == "grants"
    assert procurement["benefit_type"] == "commercial_contract"
    assert procurement["application_mode"] == "tender"
    assert procurement["content_track"] == "procurement"
    assert template_accepts_taxonomy("grant_day", procurement) is False
    assert template_accepts_taxonomy("procurement_day", procurement) is True


def test_unknown_instrument_is_blocked_before_social_ranking() -> None:
    item = _item(
        item_type=OpportunityType.GRANT,
        tags=["grant"],
        raw={"opportunity_taxonomy": {"instrument": "unknown"}},
    )

    taxonomy = classify_opportunity(item)

    assert taxonomy["decision"] == "blocked"
    assert "instrument_unknown" in taxonomy["finding_ids"]
    assert template_accepts_taxonomy("opportunity_day", taxonomy) is False
