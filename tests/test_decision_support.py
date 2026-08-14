from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api import main as api_main
from core.decision_support import assess_profile, program_truth, record_kind
from core.kazakhstan_data_routes import data_routes, data_routes_contract
from core.models import Opportunity, OpportunityType


def _item(
    *,
    title: str = "Конкурс на цифровые решения для бизнеса Алматы",
    item_type: OpportunityType = OpportunityType.GRANT,
    deadline: date | None = None,
    raw: dict | None = None,
    eligibility: list[str] | None = None,
    tags: list[str] | None = None,
) -> Opportunity:
    return Opportunity(
        source="decision_fixture",
        source_url="https://example.org/source",
        type=item_type,
        title=title,
        summary="Поддержка ТОО и технологических команд в Казахстане.",
        deadline=deadline,
        eligibility=eligibility or ["ТОО из Алматы"],
        tags=tags or ["kazakhstan", "business", "digital", "grant"],
        discovered_at=datetime.now(timezone.utc),
        raw=raw or {},
    )


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def test_program_truth_does_not_call_rules_an_open_grant():
    rules = _item(
        title="Критерии субсидирования производителей сельхозпродукции",
        raw={"region": "Казахстан"},
    )

    truth = program_truth(rules)

    assert record_kind(rules) == "regulatory_guidance"
    assert truth["kind"] == "regulatory_guidance"
    assert truth["actionability"] == "reference"


def test_program_truth_keeps_procurement_notice_distinct_from_plan_or_result():
    tender = _item(
        title="Открытый конкурс на поставку оборудования",
        item_type=OpportunityType.TENDER,
        deadline=date.today() + timedelta(days=10),
        raw={"application_url": "https://example.org/tender"},
    )
    plan = _item(
        title="Годовой план закупок на 2026 год",
        item_type=OpportunityType.TENDER,
    )

    assert program_truth(tender)["kind"] == "procurement_notice"
    assert program_truth(tender)["actionability"] == "apply"
    assert program_truth(plan)["kind"] == "procurement_plan"
    assert program_truth(plan)["actionability"] == "plan"


def test_profile_precheck_matches_kazakhstan_region_without_eligibility_claim():
    item = _item(
        deadline=date.today() + timedelta(days=10),
        raw={
            "application_url": "https://example.org/apply",
            "region": "город Алматы, Казахстан",
        },
    )

    result = assess_profile(
        item,
        {
            "applicant": "business",
            "legal_form": "too",
            "region": "almaty_city",
            "sector": "it",
            "support_need": "grant",
            "has_eds": "yes",
        },
    )

    assert result["status"] == "potential_fit"
    assert {"applicant_signal", "legal_form_signal", "region_signal"} <= set(
        result["positive_signals"]
    )
    assert "confirmation of eligibility" in result["legal_boundary"]


def test_profile_precheck_does_not_confuse_almaty_city_with_almaty_region():
    item = _item(raw={"region": "Алматинская область"})

    result = assess_profile(item, {"region": "almaty_city"})

    assert "region_signal" not in result["positive_signals"]
    assert "region_verify" in result["checks"]


def test_fit_endpoint_is_private_and_localizes_its_safety_boundary(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _item(
        deadline=date.today() + timedelta(days=10),
        raw={
            "application_url": "https://example.org/apply",
            "region": "Алматы",
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(
        f"/opportunities/{item.id}/fit.json",
        params={"lang": "ru", "applicant": "business", "region": "almaty_city"},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    payload = response.json()
    assert payload["truth"]["actionability"] == "apply"
    assert payload["legal_boundary"] == (
        "Это предчек по опубликованным данным, а не подтверждение права на участие."
    )


def test_data_routes_are_explicit_about_coverage_and_publicly_discoverable(
    monkeypatch,
):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    routes = data_routes("ru")
    assert len(routes) >= 7
    assert {route["id"] for route in routes} >= {
        "public_procurement",
        "agro_livestock",
        "ecology_hearings",
    }
    assert all(route["coverage"] in {"not_indexed", "partial"} for route in routes)
    assert data_routes_contract("https://qaz.fund")["human_page"] == (
        "https://qaz.fund/data-routes?lang=ru"
    )

    page = client.get("/data-routes", params={"lang": "ru"})
    assert page.status_code == 200
    assert 'data-avds-component="data-route-card"' in page.text
    assert "Государственные закупки" in page.text
    assert "Экологические слушания" in page.text
    assert "Покрывается частично" in page.text
    assert "\u2014" not in page.text
    assert not client.head("/data-routes?lang=ru").content

    contract = client.get("/.well-known/kazakhstan-data-routes.json")
    assert contract.status_code == 200
    assert contract.json()["schema_version"] == "kazakhstan-data-routes.v1"
    assert contract.json()["routes"][0]["id"] == "public_procurement"
