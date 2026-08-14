from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from api import main as api_main
from api.edpol_language import evaluate_social_copy
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
        lifecycle="rolling" if deadline is None else "open",
        eligibility=["Команды и организации из Казахстана"],
        score=score,
        raw={
            "deadline_policy": "rolling" if deadline is None else None,
            "provenance": {"evidence_state": "sourced"},
            "decision_readiness": {"status": "partial"},
            "i18n": {
                "ru": {
                    "title": "Поддержка технологических проектов",
                    "summary": (
                        "Финансирование для команд, которые развивают "
                        "технологические продукты."
                    ),
                    "eligibility": ["Команды и организации из Казахстана"],
                    "application_steps": [
                        "Проверить отраслевые критерии конкурса",
                        "Подготовить описание продукта и бюджет",
                        "Подать заявку через портал организатора",
                    ],
                    "social_title": "Технологические проекты: грант до 5 млн KZT",
                    "amount": "До 5 000 000 KZT",
                    "deadline_display": (
                        deadline.strftime("%d.%m.%Y")
                        if deadline is not None
                        else "Постоянный приём"
                    ),
                }
            },
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
    assert item["title"] == "Технологические проекты: грант до ₸5 млн"
    assert item["title"] not in item["body_text"]
    assert "https://qaz.fund/" not in item["body_text"]
    assert "Проверка:" not in item["body_text"]
    assert "utm_source=telegram" in item["canonical_url"]
    source = item["source_items"][0]
    assert source["id"] == "11111111-1111-1111-1111-111111111111"
    assert len(source["application_steps"]) == 3
    assert source["safety"]["status"] == "source_grounded_review_required"
    assert source["safety"]["human_review_required"] is True
    assert item["edpol"]["decision"] == "pass"
    assert payload["edpol_policy"]["version"] == "1.1.0"
    assert payload["audience_focus"] == "kazakhstan"
    assert payload["currency_display"] == "symbols"


def test_non_editorial_record_is_not_exported_to_qpost() -> None:
    opportunity = _opportunity(
        item_id="88888888-8888-8888-8888-888888888888", deadline=None
    )
    opportunity.raw.pop("i18n")

    payload = build_qpost_draft_feed(
        [opportunity],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 13),
    )

    assert payload["state"] == "no_candidates"
    assert payload["items"] == []
    assert payload["rejected_count"] == 1


def test_edpol_blocks_paraphrased_slop_in_all_supported_languages() -> None:
    cases = [
        ("Данная программа", "Она открывает новые горизонты."),
        ("Бұл бағдарлама", "Жоба жаңа мүмкіндіктер ашады."),
        ("This programme", "It opens new horizons."),
    ]

    for title, body in cases:
        report = evaluate_social_copy(title=title, body_text=body)
        assert report["decision"] == "blocked"
        assert "generic-opportunity-framing" in report["finding_ids"]


def test_russian_feed_does_not_leak_english_only_audience_text() -> None:
    opportunity = _opportunity(
        item_id="66666666-6666-6666-6666-666666666666",
        deadline=date(2026, 8, 17),
    )
    opportunity.eligibility = ["Startup teams from Kazakhstan and Central Asia"]
    opportunity.raw["i18n"]["ru"]["eligibility"] = [
        "Команды из Казахстана и Центральной Азии"
    ]

    payload = build_qpost_draft_feed(
        [opportunity],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 13),
    )

    audience = payload["items"][0]["source_items"][0]["audience"]
    assert audience == "Команды из Казахстана и Центральной Азии"


def test_grant_day_uses_source_grounded_editorial_fields() -> None:
    opportunity = _opportunity(
        item_id="77777777-7777-7777-7777-777777777777",
        deadline=date(2026, 8, 17),
    )
    opportunity.raw["amount_raw"] = "Бесплатно · офлайн в Астане · 14 недель"
    opportunity.raw["i18n"] = {
        "ru": {
            "title": "Технологические гранты для Казахстана",
            "summary": "Финансирование для команд с действующим продуктом.",
            "eligibility": ["Специалисты и предприниматели от 18 лет"],
            "application_steps": [
                "Заполнить заявку",
                "Пройти интервью",
                "Подтвердить участие",
            ],
            "highlights": ["Founder Lab", "Доступ к GPU"],
            "social_title": "AI'Preneurs – программа для AI-основателей",
            "audience_label": "Для кого",
            "highlights_label": "Что получите",
            "amount": "Грант до 5 000 000 KZT",
            "amount_label": "Участие",
            "deadline_display": "17 августа · 18:00",
            "deadline_label": "Последний день",
            "steps_title": "Как пройти отбор",
        }
    }

    payload = build_qpost_draft_feed(
        [opportunity],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 13),
    )

    item = payload["items"][0]
    assert item["title"] == "AI'Preneurs – программа для AI-основателей"
    assert item["title"] not in item["body_text"]
    assert item["body_text"].startswith(
        "Финансирование для команд с действующим продуктом."
    )
    assert item["source_items"][0]["title"] == ("Технологические гранты для Казахстана")
    assert "Для кого:\nСпециалисты и предприниматели от 18 лет" in item["body_text"]
    assert "Что получите:\n• Founder Lab\n• Доступ к GPU" in item["body_text"]
    assert "Участие: Грант до ₸5 000 000" in item["body_text"]
    assert "Последний день: 17 августа · 18:00" in item["body_text"]
    assert (
        "Как пройти отбор:\n1. Заполнить заявку\n2. Пройти интервью\n3. Подтвердить участие"
        in item["body_text"]
    )
    assert "https://qaz.fund/" not in item["body_text"]


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
    assert payload["items"][0]["body_text"].startswith(
        "Для заявителей из Казахстана:"
    )


def test_currency_codes_are_compacted_to_symbols_across_visible_copy() -> None:
    opportunity = _opportunity(
        item_id="99999999-9999-9999-9999-999999999999",
        deadline=date(2026, 9, 1),
    )
    opportunity.raw["i18n"]["ru"].update(
        {
            "social_title": "Премия: 5 млн KZT победителю",
            "summary": "Фонд 35 000 000 KZT, дополнительная выплата EUR 460.",
            "amount": "USD 2,000 или 5 млн KZT",
        }
    )

    payload = build_qpost_draft_feed(
        [opportunity],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 15),
    )

    item = payload["items"][0]
    visible = f"{item['title']}\n{item['body_text']}"
    assert "KZT" not in visible
    assert "USD" not in visible
    assert "EUR" not in visible
    assert "₸5 млн" in visible
    assert "₸35 000 000" in visible
    assert "$2,000" in visible
    assert "€460" in visible


def test_kazakhstan_cards_rank_before_global_and_unscoped_cards_are_excluded() -> None:
    local = _opportunity(
        item_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        deadline=date(2026, 9, 1),
        score=0.5,
    )
    global_item = _opportunity(
        item_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        deadline=date(2026, 8, 20),
        score=0.9,
    )
    global_item.eligibility = ["Applicants worldwide"]
    global_item.raw["i18n"]["ru"]["eligibility"] = ["Заявители из любой страны"]
    global_item.raw["i18n"]["ru"]["summary"] = "Приём заявок из любой страны."
    unscoped = _opportunity(
        item_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        deadline=date(2026, 8, 18),
        score=1.0,
    )
    unscoped.eligibility = ["Selected organisations"]
    unscoped.raw["i18n"]["ru"]["eligibility"] = ["Отдельные организации"]
    unscoped.raw["i18n"]["ru"]["summary"] = "Конкурс для отдельных организаций."

    payload = build_qpost_draft_feed(
        [global_item, unscoped, local],
        base_url="https://qaz.fund",
        lang="ru",
        template="weekly",
        today=date(2026, 8, 15),
        limit=5,
    )

    sources = payload["items"][0]["source_items"]
    assert [source["id"] for source in sources] == [str(local.id), str(global_item.id)]
    assert [source["focus_rank"] for source in sources] == [0, 1]
    assert payload["rejected_count"] == 1


def test_education_admission_cannot_enter_grant_or_main_opportunity_stream() -> None:
    admission = _opportunity(
        item_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
        deadline=date(2026, 9, 20),
    )
    admission.tags = ["education_admission", "state_funded_seat", "education"]
    admission.raw["opportunity_taxonomy"] = {
        "instrument": "education_admission",
        "application_mode": "admission",
        "deadline_model": "multiple",
    }
    admission.raw["application_windows"] = [
        {"route": "working_qualifications", "deadline": "2026-08-27"}
    ]

    grant_payload = build_qpost_draft_feed(
        [admission],
        base_url="https://qaz.fund",
        lang="ru",
        template="grant_day",
        today=date(2026, 8, 15),
    )
    main_payload = build_qpost_draft_feed(
        [admission],
        base_url="https://qaz.fund",
        lang="ru",
        template="opportunity_day",
        today=date(2026, 8, 15),
    )
    education_payload = build_qpost_draft_feed(
        [admission],
        base_url="https://qaz.fund",
        lang="ru",
        template="education_day",
        today=date(2026, 8, 15),
    )

    assert grant_payload["state"] == "no_candidates"
    assert main_payload["state"] == "no_candidates"
    assert education_payload["items"][0]["source_items"][0]["taxonomy"] == {
        "version": "1.0.0",
        "instrument": "education_admission",
        "benefit_type": "tuition_coverage",
        "application_mode": "admission",
        "deadline_model": "multiple",
        "content_track": "education",
        "publication_scope": "dedicated",
        "decision": "pass",
        "finding_ids": [],
    }


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
    assert payload["schema_version"] == "qazfund-qpost-drafts.v3"
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
