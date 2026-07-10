from __future__ import annotations

from pydantic import HttpUrl

from core.models import Opportunity, OpportunityType
from core.russian_summary import (
    russian_opportunity_title_fallback,
    russian_summary_fallback,
    russian_title_fallback,
)


def _opp(
    *,
    source: str,
    title: str,
    summary: str,
    type_: OpportunityType = OpportunityType.GRANT,
    raw: dict | None = None,
) -> Opportunity:
    return Opportunity(
        source=source,
        source_url=HttpUrl("https://example.org/source"),
        type=type_,
        title=title,
        summary=summary,
        tags=["kazakhstan"],
        raw=raw or {},
    )


def test_russian_summary_fallback_for_startup_program():
    item = _opp(
        source="nvidia_inception",
        title="NVIDIA Inception Program",
        summary="Global program for AI and data-science startups with developer tools.",
        type_=OpportunityType.CLOUD_CREDIT,
    )

    summary = russian_summary_fallback(item, item.summary)

    assert "стартап" in summary.lower()
    assert "NVIDIA Inception" in summary
    assert "Global program" not in summary


def test_russian_summary_fallback_for_project_pipeline():
    item = _opp(
        source="adb_kazakhstan",
        title="KEGOC Renewable Energy Supporting Grid Expansion Project",
        summary="The loan will provide scarce long-term local currency financing.",
        type_=OpportunityType.TENDER,
    )

    summary = russian_summary_fallback(item, item.summary)

    assert "Азиатского банка развития" in summary
    assert "Казахстана" in summary


def test_russian_summary_fallback_for_procurement():
    item = _opp(
        source="undp_procurement",
        title="Supply of a field laboratory for water analysis",
        summary="UNDP procurement opportunity in UNDP-KAZ/KAZAKHSTAN.",
        type_=OpportunityType.TENDER,
        raw={"reference": "UNDP-KAZ-00706", "office": "UNDP-KAZ/KAZAKHSTAN"},
    )

    summary = russian_summary_fallback(item, item.summary)

    assert "Закупка ПРООН" in summary
    assert "UNDP-KAZ-00706" in summary
    assert "Supply of a field laboratory" not in summary
    assert len(summary) >= 100


def test_russian_summary_fallback_keeps_clean_ru_and_fixes_repetition():
    item = _opp(
        source="kazakhstan_domestic_support",
        title="Субсидии на животноводство",
        summary="Официальное руководство по субсидиям на животноводство и животноводство.",
    )

    assert russian_summary_fallback(item, item.summary) == (
        "Официальное руководство по субсидиям на животноводство."
    )


def test_russian_title_fallback_fixes_repetition():
    assert (
        russian_title_fallback("Поставка кухонного и кухонного оборудования")
        == "Поставка кухонного оборудования"
    )


def test_russian_opportunity_title_fallback_for_project_pipeline():
    item = _opp(
        source="world_bank_kazakhstan",
        title="Transport Resilience and Connectivity Enhancement Project",
        summary="The project supports resilient infrastructure.",
        type_=OpportunityType.TENDER,
    )

    title = russian_opportunity_title_fallback(item, item.title)

    assert title == "Проект Всемирного банка для Казахстана"
    assert "Transport Resilience" not in title


def test_russian_opportunity_title_fallback_prioritizes_water_procurement():
    item = _opp(
        source="ebrd_ecepp_procurement",
        title="Rehabilitation of water supply systems and facilities for irrigation",
        summary="Invitation for tenders.",
        type_=OpportunityType.TENDER,
    )

    title = russian_opportunity_title_fallback(item, item.title)
    summary = russian_summary_fallback(item, item.summary)

    expected_title = (
        "Закупка в Казахстане: " "экологические, водные или климатические задачи"
    )
    assert title.startswith(expected_title)
    assert title.endswith(f"№ {str(item.id).split('-')[0].upper()}")
    assert "водные или климатические задачи" in summary
    assert "цифровые системы" not in summary


def test_russian_summary_fallback_expands_short_kazakhstan_watch_summary():
    item = _opp(
        source="kazakhstan_watch",
        title="ЕБРР Казахстан Консультирование МСП и доступ к финансированию",
        summary="Пути поддержки ЕБРР для стартапов, МСП и бизнес-консультационных услуг.",
    )

    summary = russian_summary_fallback(item, item.summary)

    assert "ЕБРР в Казахстане" in summary
    assert len(summary) >= 100
