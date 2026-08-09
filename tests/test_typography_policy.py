from __future__ import annotations

from datetime import date

from core.history import public_snapshot
from core.localization import localize_opportunity
from core.models import (
    Opportunity,
    OpportunityDetail,
    OpportunityDetailSection,
    OpportunityMetadataField,
    OpportunityType,
)
from core.typography_policy import (
    POLICY_VERSION,
    normalize_public_detail,
    normalize_public_value,
    normalize_text,
    scan_text,
)


def _item() -> Opportunity:
    return Opportunity(
        source="test_source",
        source_url="https://example.test/source?a=one—two",
        type=OpportunityType.GRANT,
        title="Public title — source",
        summary="Public summary — source",
        funder="Funder — name",
        eligibility=["Teams — Kazakhstan"],
        tags=["tag — one"],
        deadline=date(2027, 1, 1),
        raw={
            "title_en": "Raw title — source",
            "summary_en": "Raw summary — source",
            "application_url": "https://example.test/apply?a=one—two",
        },
    )


def test_policy_normalizes_all_supported_entities_and_is_idempotent() -> None:
    assert POLICY_VERSION == "1.0.0"
    value = "A — B &mdash; C &#8212; D &#x2014; E"
    expected = "A – B &ndash; C &#8211; D &#x2013; E"
    assert normalize_text(value) == expected
    assert normalize_text(expected) == expected
    assert scan_text("Visible — https://example.test/a—b")
    assert len(scan_text("Visible — https://example.test/a—b")) == 1


def test_public_value_recursion_preserves_technical_urls() -> None:
    value = {
        "title": "Title — copy",
        "url": "https://example.test/a—b",
        "nested": ["One — item"],
    }
    assert normalize_public_value(value) == {
        "title": "Title – copy",
        "url": "https://example.test/a—b",
        "nested": ["One – item"],
    }


def test_localization_and_history_normalize_public_projection_only() -> None:
    item = _item()
    localized = localize_opportunity(item, "en")

    assert localized.title == "Raw title – source"
    assert localized.summary == "Raw summary – source"
    assert localized.eligibility == ["Teams – Kazakhstan"]
    assert localized.raw["title_en"] == "Raw title — source"
    assert str(localized.source_url) == "https://example.test/source?a=one%E2%80%94two"
    assert public_snapshot(item)["title"] == "Public title – source"


def test_detail_normalizes_public_fields_and_keeps_raw_payload() -> None:
    item = _item()
    detail = OpportunityDetail(
        **item.model_dump(),
        application_url="https://example.test/apply?a=one—two",
        detail_text="Detail — text",
        detail_sections=[
            OpportunityDetailSection(heading="Heading — one", text="Text — one")
        ],
        metadata=[OpportunityMetadataField(key="note", value="Value — one")],
    )
    normalized = normalize_public_detail(detail)

    assert normalized.detail_text == "Detail – text"
    assert normalized.detail_sections[0].heading == "Heading – one"
    assert normalized.detail_sections[0].text == "Text – one"
    assert normalized.metadata[0].value == "Value – one"
    assert normalized.raw["title_en"] == "Raw title — source"
    assert normalized.application_url == "https://example.test/apply?a=one—two"
