from pydantic import HttpUrl

from core.localization import (
    localize_opportunity,
    localized_section_list,
    localized_text,
)
from core.models import Opportunity, OpportunityType


def test_russian_source_detail_beats_shorter_i18n_fallback():
    raw = {
        "detail_language": "ru",
        "detail_text": "Официальный текст источника с несколькими полезными условиями.",
        "detail_sections": [
            {
                "heading": "Условия",
                "text": "Официальный текст источника с несколькими полезными условиями.",
            }
        ],
        "i18n": {
            "ru": {
                "detail_text": "Короткий fallback.",
                "detail_sections": [
                    {"heading": "Описание", "text": "Короткий fallback."}
                ],
            }
        },
    }

    assert localized_text(raw, "ru", "detail_text") == raw["detail_text"]
    assert localized_section_list(raw, "ru") == raw["detail_sections"]


def test_localized_summary_removes_source_ui_noise():
    raw = {
        "i18n": {
            "ru": {
                "summary": "Описание программы. Читать далее Прием заявок",
            }
        }
    }

    assert localized_text(raw, "ru", "summary") == "Описание программы."


def test_localized_summary_fallback_uses_localized_title():
    item = Opportunity(
        source="kazakhstan_watch",
        source_url=HttpUrl("https://example.org/ebrd"),
        type=OpportunityType.GRANT,
        title="EBRD Kazakhstan SME advisory",
        summary="Short EBRD support route.",
        raw={
            "i18n": {
                "ru": {
                    "title": "ЕБРР Казахстан Консультирование МСП и доступ к финансированию",
                    "summary": (
                        "Пути поддержки ЕБРР для стартапов, МСП "
                        "и бизнес-консультационных услуг."
                    ),
                }
            }
        },
    )

    localized = localize_opportunity(item, "ru")

    assert "ЕБРР в Казахстане" in localized.summary
    assert len(localized.summary) >= 100


def test_russian_procurement_title_keeps_reference_for_distinction():
    item = Opportunity(
        source="undp_procurement",
        source_url=HttpUrl("https://example.org/undp/723"),
        type=OpportunityType.TENDER,
        title="Individual consultant for project support",
        summary="Consulting services for a Kazakhstan project.",
        raw={"reference": "UNDP-KAZ-00723"},
    )

    localized = localize_opportunity(item, "ru")

    assert localized.title == (
        "Закупка в Казахстане: консультационные услуги — UNDP-KAZ-00723"
    )


def test_russian_procurement_uses_compact_id_and_removes_summary_title_repeat():
    item = Opportunity(
        source="unicef_kazakhstan",
        source_url=HttpUrl("https://example.org/tender/webinars"),
        type=OpportunityType.TENDER,
        title="Individual consultant organizing two webinars",
        summary="Individual consultant organizing two webinars. Check requirements.",
        raw={
            "external_id": (
                "individual-consultant-organizing-two-webinars-for-open-badges"
            )
        },
    )

    localized = localize_opportunity(item, "ru")

    assert localized.title.endswith(f"№ {str(item.id).split('-')[0].upper()}")
    assert not localized.summary.startswith(localized.title)


def test_russian_localization_removes_doubled_public_title_prefix():
    title = "Закупочная возможность в Казахстане: консультационные услуги"
    item = Opportunity(
        source="unicef_kazakhstan",
        source_url=HttpUrl("https://example.org/tender/consulting"),
        type=OpportunityType.TENDER,
        title=title,
        summary=f"{title}: {title}. Проверьте требования и срок подачи.",
    )

    localized = localize_opportunity(item, "ru")

    assert localized.summary == "Проверьте требования и срок подачи."
