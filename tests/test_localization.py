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
