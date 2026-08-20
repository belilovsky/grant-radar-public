"""Run QAZ.FUND with deterministic, non-production browser-test records."""

from __future__ import annotations

import argparse
import os
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import uvicorn

from core.models import Opportunity, OpportunityType
from core.public_clock import public_today

PRIMARY_OPPORTUNITY_ID = UUID("11111111-1111-4111-8111-111111111111")
SECONDARY_OPPORTUNITY_ID = UUID("22222222-2222-4222-8222-222222222222")
FUNDER_SLUG = "astana-hub"


def _browser_opportunity(**fields: object) -> Opportunity:
    payload: dict[str, object] = {
        "currency": "KZT",
        "languages": ["ru", "kk", "en"],
        "eligibility": ["Команды из Казахстана", "Юридические лица и ИП"],
        "score": 0.92,
    }
    payload.update(fields)
    return Opportunity.model_validate(payload)


def browser_seed_items() -> list[Opportunity]:
    """Return representative lifecycle and information-density states."""

    today = public_today()
    return [
        _browser_opportunity(
            id=PRIMARY_OPPORTUNITY_ID,
            source="astana_hub",
            source_url="https://astanahub.com/programs/digital-product-grant",
            type=OpportunityType.GRANT,
            title="Грант на развитие цифрового продукта",
            summary=(
                "Финансирование пилотирования и вывода цифрового продукта на рынок "
                "для технологических команд Казахстана."
            ),
            funder="Astana Hub",
            amount_max=Decimal("25000000"),
            deadline=today + timedelta(days=21),
            tags=["kazakhstan", "startup", "ai", "grant"],
            lifecycle="open",
            raw={
                "application_url": "https://astanahub.com/programs/apply",
                "country": "Kazakhstan",
                "external_id": "browser-open",
                "detail_sections_ru": [
                    {
                        "heading": "Что поддерживает программа",
                        "text": "Пилот, проверку спроса и подготовку выхода на рынок.",
                    }
                ],
            },
        ),
        _browser_opportunity(
            id=SECONDARY_OPPORTUNITY_ID,
            source="astana_hub",
            source_url="https://astanahub.com/programs/closing-support",
            type=OpportunityType.GRANT,
            title="Поддержка малого бизнеса: ближайший срок",
            summary=(
                "Программа для предпринимателей, которым требуется софинансирование "
                "оборудования и запуска продаж."
            ),
            funder="Astana Hub",
            amount_max=Decimal("50000000"),
            deadline=today + timedelta(days=3),
            tags=["kazakhstan", "sme", "business_support", "grant"],
            lifecycle="closing_soon",
            raw={"country": "Kazakhstan", "external_id": "browser-closing"},
        ),
        _browser_opportunity(
            id=UUID("33333333-3333-4333-8333-333333333333"),
            source="astana_hub",
            source_url="https://astanahub.com/programs/accelerator",
            type=OpportunityType.ACCELERATOR,
            title="Постоянный набор в акселератор",
            summary="Акселерационная программа с бессрочной предварительной заявкой.",
            funder="Astana Hub",
            tags=["kazakhstan", "startup", "accelerator", "rolling"],
            lifecycle="rolling",
            opportunity_status="rolling",
            raw={"deadline_policy": "rolling", "external_id": "browser-rolling"},
        ),
        _browser_opportunity(
            id=UUID("44444444-4444-4444-8444-444444444444"),
            source="internews",
            source_url="https://internews.org/future-media-call",
            type=OpportunityType.GRANT,
            title="Планируемый конкурс для медиапроектов",
            summary="Анонс будущего конкурса: условия и точная дата ещё уточняются.",
            funder="Internews",
            deadline=today + timedelta(days=90),
            tags=["kazakhstan", "media", "forecast"],
            lifecycle="forecast",
            opportunity_status="forecast",
            raw={"country": "Kazakhstan", "external_id": "browser-forecast"},
        ),
        _browser_opportunity(
            id=UUID("55555555-5555-4555-8555-555555555555"),
            source="astana_hub",
            source_url="https://astanahub.com/programs/archive-2025",
            type=OpportunityType.CONTEST,
            title="Архивный конкурс технологических решений",
            summary="Завершённый набор сохранён для понимания профиля организатора.",
            funder="Astana Hub",
            deadline=today - timedelta(days=30),
            tags=["kazakhstan", "startup", "closed"],
            lifecycle="closed",
            opportunity_status="closed",
            raw={"country": "Kazakhstan", "external_id": "browser-closed"},
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ.setdefault("PUBLIC_BASE_URL", f"http://{args.host}:{args.port}")
    os.environ.setdefault("GRANT_RADAR_ALLOWED_HOSTS", f"{args.host},localhost")
    os.environ.setdefault("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", "0")
    os.environ.setdefault("PUBLIC_ANALYTICS_ENABLED", "0")

    from api import main as api_main

    api_main._cache[:] = browser_seed_items()
    api_main._refresh_public_items_cache()
    uvicorn.run(api_main.app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
