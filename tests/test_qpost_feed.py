from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from api import main as api_main
from api.qpost_feed import build_qpost_draft_feed
from core.models import Opportunity, OpportunityType


def _opportunity(
    *, item_id: str, deadline: date | None, score: float = 0.9
) -> Opportunity:
    return Opportunity(
        id=UUID(item_id),
        source="official_source",
        source_url="https://example.org/programme",
        type=OpportunityType.GRANT,
        title="Поддержка технологических проектов",
        summary="Финансирование для команд, которые развивают технологические продукты.",
        amount_max=5_000_000,
        currency="KZT",
        deadline=deadline,
        eligibility=["Команды и организации из Казахстана"],
        score=score,
        raw={
            "provenance": {"evidence_state": "sourced"},
            "decision_readiness": {"status": "partial"},
        },
    )


def test_grant_day_contract_is_draft_only_and_complete() -> None:
    payload = build_qpost_draft_feed(
        [_opportunity(item_id="11111111-1111-1111-1111-111111111111", deadline=None)],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 13),
    )

    assert payload["publication_mode"] == "draft_only"
    assert payload["human_review_required"] is True
    item = payload["items"][0]
    assert item["idempotency_key"].startswith("qazfund:grant_day:ru:2026-08-13:")
    assert item["title"].startswith("Возможность дня:")
    assert "utm_source=telegram" in item["canonical_url"]
    source = item["source_items"][0]
    assert source["id"] == "11111111-1111-1111-1111-111111111111"
    assert len(source["application_steps"]) == 3
    assert source["safety"]["status"] == "source_grounded_review_required"
    assert source["safety"]["human_review_required"] is True


def test_russian_feed_does_not_leak_english_only_audience_text() -> None:
    opportunity = _opportunity(
        item_id="66666666-6666-6666-6666-666666666666",
        deadline=date(2026, 8, 17),
    )
    opportunity.eligibility = ["Startup teams from Kazakhstan and Central Asia"]

    payload = build_qpost_draft_feed(
        [opportunity],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 13),
    )

    audience = payload["items"][0]["source_items"][0]["audience"]
    assert (
        audience == "Критерии участия нужно сверить на официальной странице программы"
    )


def test_deadline_templates_only_select_exact_runway() -> None:
    opportunities = [
        _opportunity(
            item_id="22222222-2222-2222-2222-222222222222", deadline=date(2026, 8, 20)
        ),
        _opportunity(
            item_id="33333333-3333-3333-3333-333333333333", deadline=date(2026, 8, 15)
        ),
    ]

    seven = build_qpost_draft_feed(
        opportunities,
        base_url="https://qaz.fund",
        lang="ru",
        template="deadline_7d",
        today=date(2026, 8, 13),
    )
    two = build_qpost_draft_feed(
        opportunities,
        base_url="https://qaz.fund",
        lang="ru",
        template="deadline_2d",
        today=date(2026, 8, 13),
    )

    assert seven["items"][0]["source_items"][0]["deadline"] == "2026-08-20"
    assert two["items"][0]["source_items"][0]["deadline"] == "2026-08-15"


def test_weekly_digest_has_one_stable_candidate_with_multiple_sources() -> None:
    payload = build_qpost_draft_feed(
        [
            _opportunity(
                item_id="44444444-4444-4444-4444-444444444444", deadline=None, score=0.8
            ),
            _opportunity(
                item_id="55555555-5555-5555-5555-555555555555", deadline=None, score=0.7
            ),
        ],
        base_url="https://qaz.fund",
        lang="ru",
        template="weekly",
        today=date(2026, 8, 13),
        limit=5,
    )

    assert len(payload["items"]) == 1
    assert payload["items"][0]["idempotency_key"] == "qazfund:weekly:ru:2026-W33"
    assert len(payload["items"][0]["source_items"]) == 2
    assert payload["items"][0]["human_review_required"] is True


def test_public_qpost_route_exposes_review_only_contract(monkeypatch) -> None:
    opportunity = _opportunity(
        item_id="66666666-6666-6666-6666-666666666666",
        deadline=None,
    )
    monkeypatch.setattr(
        api_main,
        "_query_opportunities",
        lambda **_: ([opportunity], 1),
    )

    with TestClient(api_main.app) as client:
        response = client.get(
            "/media/v1/qpost/drafts.json?lang=ru&template=grant_day&limit=1"
        )

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    payload = response.json()
    assert payload["schema_version"] == "qazfund-qpost-drafts.v1"
    assert payload["publication_mode"] == "draft_only"
    assert payload["items"][0]["template"] == "grant_day"


def test_public_qpost_route_calls_real_catalog_query_without_fastapi_defaults(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_cached_prepared_scope_items",
        lambda **_: [
            _opportunity(
                item_id="77777777-7777-7777-7777-777777777777",
                deadline=None,
            )
        ],
    )
    api_main._clear_public_items_cache()

    with TestClient(api_main.app) as client:
        response = client.get(
            "/media/v1/qpost/drafts.json?lang=ru&template=grant_day&limit=1"
        )

    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["source_items"][0]["id"] == (
        "77777777-7777-7777-7777-777777777777"
    )
