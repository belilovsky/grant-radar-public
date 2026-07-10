from __future__ import annotations

from datetime import date

from core.geofit import (
    is_excluded_for_kazakhstan_focus,
    is_relevant_for_kazakhstan_focus,
)
from core.models import Opportunity, OpportunityType
from core.scoring import score


def _opp(
    title: str, *, summary: str = "", tags: list[str] | None = None
) -> Opportunity:
    return Opportunity(
        source="test",
        source_url="https://example.org/item",
        type=OpportunityType.GRANT,
        title=title,
        summary=summary,
        tags=tags or [],
    )


def test_short_ai_keyword_does_not_match_inside_words():
    opp = _opp("Submit applications for creative residencies")

    assert score(opp, today=date(2026, 5, 22)) == 0.0


def test_ai_and_central_asia_match_on_word_boundaries():
    opp = _opp(
        "AI education grant",
        summary="Open to Central Asia civic technology teams.",
        tags=["edtech"],
    )

    assert score(opp, today=date(2026, 5, 22)) >= 0.6


def test_multi_word_keywords_match_underscore_tags():
    opp = _opp("Teacher program", tags=["digital_skills", "startup_support"])

    assert score(opp, today=date(2026, 5, 22)) >= 0.2


def test_us_tribal_only_ai_grant_is_downranked_for_kazakhstan_focus():
    opp = _opp(
        "AI3 Action Institute - Artificial Intelligence for American Indians",
        tags=["us", "federal", "grant", "governance"],
    )
    opp.funder = "HHS-ACF-ANA"
    opp.raw = {
        "agencyCode": "HHS-2026-ACF-ANA-NAI-0035",
        "agency": "Administration for Children and Families - ANA",
    }

    assert score(opp, today=date(2026, 5, 22)) < 0.3
    assert is_excluded_for_kazakhstan_focus(opp) is not None


def test_ai3_action_institute_is_excluded_for_kazakhstan_focus():
    opp = _opp(
        "AI3 Action Institute - Artificial Intelligence for American Indians",
        summary="Training and small grant activity for tribal innovators.",
        tags=["startup_support", "governance"],
    )
    opp.raw = {
        "organization": "AI3 Action Institute",
        "title": "AI3 Action Institute",
    }

    assert is_excluded_for_kazakhstan_focus(opp)


def test_unavailable_source_placeholder_is_downranked():
    opp = _opp(
        "U.S. Embassy Kazakhstan grants",
        summary="Small grants and public diplomacy opportunities for Kazakhstan.",
        tags=["kazakhstan", "education", "grant"],
    )
    opp.raw = {"page_title": "Technical Difficulties"}

    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_without_geo_signal_is_low_confidence():
    opp = _opp("AI education grant", summary="For schools", tags=["ai", "education"])
    opp.source = "grants_gov"

    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_tourism_storytelling_is_not_product_relevant():
    opp = _opp(
        "Storytelling to Safeguard Cultural Identity and Sovereignty",
        summary="Grant from the U.S. Mission to Uzbekistan for the tourism industry.",
        tags=["us", "federal", "grant", "media"],
    )
    opp.source = "grants_gov"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_counterterrorism_is_not_product_relevant():
    opp = _opp(
        "Countering Terrorist Financing Flows In and Through Tajikistan",
        summary="Security-only notice for counterterrorism programming.",
        tags=["us", "federal", "grant", "governance"],
    )
    opp.source = "grants_gov"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_inl_governance_notice_is_not_product_relevant_even_with_region_signal():
    opp = _opp(
        "Strengthening anti-corruption in Uzbekistan to improve the investment climate",
        summary="Notice from the Bureau of International Narcotics-Law Enforcement for Uzbekistan.",
        tags=["grant", "uzbekistan", "governance"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agency": "Bureau of International Narcotics-Law Enforcement"}

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_public_diplomacy_mission_is_not_product_relevant():
    opp = _opp(
        "Yemen Public Diplomacy Programs: English Language Education and Media Development",
        summary="Notice from the U.S. Mission in Saudi Arabia for public diplomacy programming.",
        tags=["us", "federal", "grant", "media"],
    )
    opp.source = "grants_gov"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_housing_demo_is_not_product_relevant():
    title = (
        "Mass Market Solutions for Leveraging Robotics and AI Technologies "
        "for Home Construction Demonstration"
    )
    opp = _opp(
        title,
        summary="Notice from the U.S. Department of Housing and Urban Development.",
        tags=["us", "federal", "grant", "artificial intelligence"],
    )
    opp.source = "grants_gov"

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_grants_gov_tribal_students_in_russian_is_not_product_relevant():
    opp = _opp(
        "Новое начало программы для студентов из племени",
        summary="Уведомление о возможности от федеральной программы США.",
        tags=["us", "federal", "grant", "artificial intelligence"],
    )
    opp.source = "grants_gov"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_grants_gov_nih_research_notice_is_not_product_relevant_without_region_signal():
    opp = _opp(
        "HeartShare 2.0 data translation center",
        summary="Notice from the National Institutes of Health for clinical research.",
        tags=["us", "federal", "grant", "artificial intelligence"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agency": "National Institutes of Health"}

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_grants_gov_usamraa_notice_is_not_product_relevant():
    opp = _opp(
        "DoD Epilepsy Research Program Award",
        summary="Clinical research opportunity from USAMRAA.",
        tags=["us", "federal", "grant", "artificial intelligence"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agencyName": "USAMRAA", "agencyCode": "DOD-AMRAA"}

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_grants_gov_postsecondary_office_notice_is_not_product_relevant_without_region_signal():
    opp = _opp(
        "Strengthening Institutions Program FY 2026 Competition",
        summary="Notice from the Office of Postsecondary Education.",
        tags=["us", "federal", "grant", "artificial intelligence"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agency": "Office of Postsecondary Education"}

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_grants_gov_eca_exchange_notice_is_not_product_relevant_without_region_signal():
    opp = _opp(
        "FY 2026 Young Leaders Exchange",
        summary="Notice from the Bureau of Educational and Cultural Affairs.",
        tags=["us", "federal", "grant", "education"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agency": "Bureau Of Educational and Cultural Affairs"}

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_grants_gov_cdc_domestic_health_notice_is_not_product_relevant_without_region_signal():
    opp = _opp(
        "World Trade Center Health Program research grants",
        summary="Notice from the Centers for Disease Control and Prevention.",
        tags=["us", "federal", "grant", "health"],
    )
    opp.source = "grants_gov"
    opp.raw = {"agency": "Centers for Disease Control and Prevention - ERA"}

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_out_of_region_only_notice_is_not_relevant_for_kazakhstan_feed():
    opp = _opp(
        "Impact Creators fellowship",
        summary=(
            "A six-month fellowship for digital journalists in the Middle East "
            "and North Africa with no local eligibility signal."
        ),
        tags=["media", "fellowship"],
    )
    opp.source = "internews"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_out_of_region_terms_keep_working_when_central_asia_is_explicit():
    opp = _opp(
        "Central Asia learning event in Brussels",
        summary=(
            "Partner meeting in Brussels for Kazakhstan and Central Asia media "
            "organizations preparing digital safety projects."
        ),
        tags=["media", "kazakhstan"],
    )
    opp.source = "internews"

    assert is_relevant_for_kazakhstan_focus(opp)


def test_astana_hub_kazakhstan_program_reaches_default_quality_threshold():
    opp = _opp('Программа "Tech Orda"', tags=["kz", "astana_hub", "program"])
    opp.source = "astana_hub"

    assert score(opp, today=date(2026, 5, 22)) >= 0.3


def test_agrotech_vettech_and_ecotech_keywords_raise_score():
    opp = _opp(
        "AgroTech and veterinary innovation challenge",
        summary=(
            "Open to Kazakhstan teams building animal health, irrigation, "
            "climate resilience and environmental monitoring solutions."
        ),
        tags=["kazakhstan", "agrotech", "vettech", "ecotech"],
    )

    assert score(opp, today=date(2026, 5, 22)) >= 0.6


def test_kazakhstan_innovation_grants_reach_quality_threshold():
    opp = _opp(
        "QazInnovations grants",
        summary=(
            "Kazakhstan innovation grant route for commercialization of "
            "technologies and SME startup support."
        ),
        tags=["kazakhstan", "innovation", "commercialization", "subsidy"],
    )

    assert score(opp, today=date(2026, 5, 22)) >= 0.5


def test_kazakhstan_domestic_support_reaches_quality_threshold():
    opp = _opp(
        "Kazakhstan export cost recovery",
        summary="Official state program for reimbursement of eligible export costs.",
        tags=[
            "kazakhstan",
            "domestic_support",
            "state_program",
            "reimbursement",
            "business_support",
        ],
    )

    assert score(opp, today=date(2026, 5, 22)) >= 0.3


def test_kazakhstan_preferential_finance_reaches_quality_threshold():
    opp = _opp(
        "Bgov unified business financial-support portal",
        summary=(
            "Kazakhstan preferential financing and leasing support for business "
            "through Baiterek group institutions."
        ),
        tags=[
            "kazakhstan",
            "domestic_support",
            "state_program",
            "preferential_financing",
            "leasing",
            "business_support",
        ],
    )

    assert score(opp, today=date(2026, 5, 22)) >= 0.3


def test_world_bank_state_borrower_pipeline_is_not_default_relevant():
    opp = _opp(
        "Advancing Learning, Entrepreneurship, and Markets for Artificial Intelligence",
        summary="World Bank project pipeline for Kazakhstan AI startup ecosystem.",
        tags=["kazakhstan", "central_asia", "world_bank", "project_pipeline", "ai"],
    )
    opp.source = "world_bank_kazakhstan"
    opp.type = OpportunityType.TENDER
    opp.raw = {
        "borrower": "Ministry of Finance of Republic of Kazakhstan",
        "lendinginstr": "Program-for-Results Financing",
    }

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.5


def test_global_bridge_excludes_out_of_region_accelerators():
    opp = _opp(
        "Africa Health-Tech Accelerator 2026",
        summary="Accelerator for African health-tech startups.",
        tags=["global", "startup", "accelerator", "technology"],
    )
    opp.source = "opportunity_desk"

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_global_bridge_excludes_event_only_conference_items():
    opp = _opp(
        "Democracy Fund Student Journalism Conference 2026",
        summary="Fully-funded trip for students to attend a conference.",
        tags=["global", "journalism", "media", "fellowship"],
    )
    opp.source = "opportunity_desk"

    assert not is_relevant_for_kazakhstan_focus(opp)


def test_undp_operational_service_notice_is_not_relevant():
    opp = _opp(
        "Долгосрочные соглашения на оказание услуг проживания в отеле и конференц-пакета",
        summary=(
            "UNDP Kazakhstan procurement notice for hotel accommodation "
            "and conference package services."
        ),
        tags=["undp", "procurement", "tender", "central_asia"],
    )
    opp.source = "undp_procurement"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3


def test_eeas_contracts_concluded_page_is_not_relevant():
    opp = _opp(
        "Перечень контрактов, заключенных в рамках конкурса заявок EuropeAid/176-656/DD/ACT/KZ",
        summary="EEAS Kazakhstan page with awarded contracts under a past call.",
        tags=["eu", "eeas", "grant", "kazakhstan"],
    )
    opp.source = "eeas_kazakhstan"

    assert not is_relevant_for_kazakhstan_focus(opp)
    assert score(opp, today=date(2026, 5, 22)) < 0.3
