from __future__ import annotations

from core.nlp import (
    clean_source_summary,
    extract_rule_based_entities,
    text_quality_flags,
)
from scripts.deepseek_enrich_content import normalize_deepseek_payload
from scripts.nlp_quality_audit import analyze_nlp_quality


def test_rule_based_entities_extract_support_region_and_sector():
    entities = extract_rule_based_entities(
        title="Аграрная кредитная корпорация кредитование животноводства",
        summary=(
            "Официальная программа Казахстана по льготному кредитованию "
            "животноводов и производителей откормочных площадок."
        ),
        tags=["kazakhstan", "vettech", "preferential_financing"],
    )

    assert "preferential_financing" in entities["support_types"]
    assert "kazakhstan" in entities["regions"]
    assert "vettech" in entities["sectors"]
    assert "farmers" in entities["audiences"]


def test_rule_based_entities_extract_project_finance_and_tenders():
    finance = extract_rule_based_entities(
        title="Kazakhstan renewable energy grid expansion project",
        summary="The project will provide long-term financing for infrastructure.",
        tags=["Kazakhstan", "ecotech"],
    )
    tender = extract_rule_based_entities(
        title="Consulting Services: Project Management",
        summary="Active procurement notice for Kazakhstan: Expression of Interest.",
        tags=["Kazakhstan"],
    )

    assert "project_finance" in finance["support_types"]
    assert "tender" in tender["support_types"]


def test_clean_source_summary_removes_read_more_noise():
    assert (
        clean_source_summary("Описание программы. Читать далее Прием заявок")
        == "Описание программы."
    )
    assert clean_source_summary("Program details. Read more Call") == "Program details."


def test_text_quality_flags_repeated_phrase_and_latin_heavy_ru_text():
    flags = text_quality_flags(
        title="Субсидии на животноводство",
        summary=(
            "Official guide for livestock and livestock producers with Kazakhstan "
            "support details."
        ),
        lang="ru",
    )

    assert "latin_heavy_ru_text" in flags

    repeated = text_quality_flags(
        title="Субсидии на животноводство",
        summary="Субсидии на животноводство и животноводство для производителей.",
        lang="ru",
    )
    assert "repeated_phrase" in repeated


def test_nlp_quality_audit_flags_missing_entities_and_text_issues():
    result = analyze_nlp_quality(
        [
            {
                "title": "Generic update",
                "summary": "Generic English opportunity summary without Russian localization.",
                "source": "example",
                "tags": [],
            }
        ],
        lang="ru",
    )

    assert result.status == "needs_attention"
    assert result.flag_counts["latin_heavy_ru_text"] == 1
    assert result.flag_counts["missing_support_type_entity"] == 1
    assert result.flag_counts["missing_region_entity"] == 1


def test_deepseek_payload_normalization_keeps_known_entity_lists():
    payload = normalize_deepseek_payload(
        {
            "summary_ru": "Краткое описание программы поддержки.",
            "entities": {
                "funders": ["QazInnovations"],
                "regions": ["Kazakhstan"],
                "support_types": ["grant"],
                "unknown": ["ignored"],
            },
            "quality_flags": ["ok"],
        }
    )

    assert payload["summary_ru"] == "Краткое описание программы поддержки."
    assert payload["entities"] == {
        "funders": ["QazInnovations"],
        "regions": ["Kazakhstan"],
        "support_types": ["grant"],
    }
    assert payload["quality_flags"] == ["ok"]
