from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api import main as api_main
from api.daily_digest import daily_digest_payload, daily_digest_text
from api.insights import build_insights_payload
from core.db import SqlRepository
from core.models import Opportunity, OpportunityType
from core.public_contract import to_opportunity_v1
from sources.kazakhstan_domestic import ACTIVE_DOMESTIC_URLS


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def _item(*, summary: str = "Поддержка внедрения цифрового решения.") -> Opportunity:
    return Opportunity(
        source="astana_hub",
        source_url="https://example.org/program",
        type=OpportunityType.GRANT,
        title="Грант на внедрение технологии",
        summary=summary,
        funder="Оператор программы",
        amount_max=5_000_000,
        currency="KZT",
        deadline=date.today() + timedelta(days=24),
        eligibility=["Малый и средний бизнес Казахстана"],
        tags=["kazakhstan", "business", "digital", "grant"],
        score=0.9,
        discovered_at=datetime.now(timezone.utc),
        raw={
            "external_id": "INSIGHT-1",
            "application_url": "https://example.org/apply",
            "source_checked_at": "2026-07-27T10:00:00+00:00",
        },
    )


def test_insights_api_and_page_are_data_backed(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.append(_item())
    client = TestClient(api_main.app)

    response = client.get("/api/v1/insights", params={"lang": "ru"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qazfund-insights.v1"
    assert payload["scope"]["active"] == 1
    assert payload["scope"]["current_catalog"] == 1
    assert payload["scope"]["sources"] == 1
    assert payload["quality"]["complete_core_share"] == 100.0
    assert payload["distribution"]["formats"][0]["label"] == "Гранты"

    page = client.get("/insights", params={"lang": "ru"})
    assert page.status_code == 200
    assert 'data-avds-component="data-centre"' in page.text
    assert 'data-avds-version="4.6.0"' in page.text
    assert 'data-avds-component="DataQualityScorecard"' in page.text
    assert 'data-avds-pattern="change-ledger"' in page.text
    assert 'data-avds-pattern="machine-entrypoints"' in page.text
    assert "--ink: var(--color-text)" in page.text
    assert "Данные о финансировании Казахстана" in page.text
    assert "Что известно до перехода к источнику" in page.text
    assert ".footer nav { display: flex; flex-wrap: wrap;" in page.text
    assert ".hero { grid-template-columns: minmax(0, 1fr); }" in page.text
    assert "/api/v1/changes?hours=24" in page.text
    assert "\u2014" not in page.text
    assert "QazCompute" not in page.text


def test_insights_snapshot_is_reused_by_api_and_page(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.append(_item())
    calls = {"count": 0}
    original = api_main.build_insights_payload

    def counted_build(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(api_main, "build_insights_payload", counted_build)
    client = TestClient(api_main.app)

    assert client.get("/api/v1/insights?lang=ru").status_code == 200
    assert client.get("/insights?lang=ru").status_code == 200
    assert calls["count"] == 1


def test_insights_head_skips_analytics_projection(monkeypatch):
    _reset_api_state(monkeypatch)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("HEAD must not build analytics")

    monkeypatch.setattr(api_main, "_cached_insights_payload", fail_if_called)

    response = TestClient(api_main.app).head("/insights?lang=ru")

    assert response.status_code == 200
    assert response.content == b""
    assert "public, max-age=60" in response.headers["cache-control"]


def test_insights_separates_current_catalog_from_full_index():
    current = _item().model_copy(update={"lifecycle": "closing_soon"})
    expired = _item().model_copy(
        update={
            "source_url": "https://example.org/expired",
            "deadline": date.today() - timedelta(days=1),
            "lifecycle": "closed",
            "raw": {"external_id": "INSIGHT-EXPIRED"},
        }
    )
    review = _item().model_copy(
        update={
            "source_url": "https://example.org/review",
            "lifecycle": "closing_soon",
            "raw": {"external_id": "INSIGHT-REVIEW"},
        }
    )
    current_v1 = to_opportunity_v1(current, source_name="Astana Hub")
    expired_v1 = to_opportunity_v1(expired, source_name="Astana Hub")
    review_v1 = to_opportunity_v1(review, source_name="Astana Hub")

    payload = build_insights_payload(
        [current_v1, expired_v1, review_v1],
        today=date.today(),
        catalog_items=[current_v1],
    )

    assert payload["scope"] == {
        "indexed_relevant": 3,
        "current_catalog": 1,
        "active": 1,
        "outside_current_catalog": 2,
        "closed_or_archival": 1,
        "review_queue": 1,
        "sources": 1,
        "indexed_sources": 1,
        "closing_within_30_days": 1,
        "kazakhstan_explicit": 1,
    }


def test_application_workspace_is_local_and_exportable(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _item()
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    detail = client.get(f"/opportunity/{item.id}", params={"lang": "ru"})
    assert detail.status_code == 200
    assert "Подготовить заявку" in detail.text
    assert f"/opportunity/{item.id}/prepare?lang=ru" in detail.text

    page = client.get(
        f"/opportunity/{item.id}/prepare",
        params={"lang": "ru"},
    )
    assert page.status_code == 200
    assert 'data-avds-component="application-workspace"' in page.text
    assert 'data-avds-pattern="application-workspace"' in page.text
    assert 'data-avds-component="FormField"' in page.text
    assert 'data-avds-component="Progress"' in page.text
    assert 'data-avds-component="Textarea"' in page.text
    assert "--ink: var(--color-text)" in page.text
    assert "Данные остаются в этом браузере" in page.text
    assert "localStorage.setItem" in page.text
    assert "qazfund-application-draft-v1" in page.text
    assert "Скачать .md" in page.text
    assert "navigator.clipboard.writeText" in page.text
    assert "fetch(" not in page.text
    assert 'method="post"' not in page.text.lower()
    assert "\u2014" not in page.text


def test_application_workspace_localizes_internal_source_slug(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _item().model_copy(
        update={
            "source": "kazakhstan_domestic_support",
            "source_url": sorted(ACTIVE_DOMESTIC_URLS)[0],
            "funder": None,
            "eligibility": ["startup", "global"],
        }
    )
    api_main._cache.append(item)

    page = TestClient(api_main.app).get(
        f"/opportunity/{item.id}/prepare",
        params={"lang": "ru"},
    )

    assert page.status_code == 200
    assert "kazakhstan_domestic_support" not in page.text
    assert "Поддержка РК" in page.text
    assert "Стартап; Глобально" in page.text


def test_application_workspace_head_skips_detail_projection(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _item()
    api_main._cache.append(item)

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("HEAD must not build the application workspace")

    monkeypatch.setattr(api_main, "build_opportunity_detail", fail_if_called)

    response = TestClient(api_main.app).head(f"/opportunity/{item.id}/prepare?lang=ru")

    assert response.status_code == 200
    assert response.content == b""


def test_change_ledger_and_daily_digest_distinguish_updates(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'changes.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)
    api_main._repository_for_url.cache_clear()
    repository = SqlRepository(db_url)
    assert repository.upsert(_item(summary="Первая версия.")) is True
    assert repository.upsert(_item(summary="Условия программы обновлены.")) is False
    api_main._clear_public_items_cache()
    client = TestClient(api_main.app)

    response = client.get(
        "/api/v1/changes",
        params={"hours": 24, "lang": "ru"},
    )
    assert response.status_code == 200
    history = response.json()
    assert history["available"] is True
    assert history["created"] == 1
    assert history["changed"] == 1
    assert history["items"][0]["changed_fields"] == ["summary"]

    digest = client.get("/media/v1/digest/daily.json", params={"lang": "ru"})
    assert digest.status_code == 200
    payload = digest.json()
    assert payload["state"] == "ready"
    assert payload["delivery"]["automatic"] is False
    assert "Новых: 1" in payload["text"]
    assert "Изменено: 1" in payload["text"]

    text = client.get("/media/v1/digest/daily.txt", params={"lang": "ru"})
    assert text.status_code == 200
    assert "QAZ.FUND – изменения за сутки" in text.text


def test_daily_digest_collecting_state_is_honest():
    payload = daily_digest_payload(
        {
            "available": False,
            "period_from": "2026-07-26T00:00:00+00:00",
            "period_to": "2026-07-27T00:00:00+00:00",
            "created": 0,
            "changed": 0,
            "items": [],
        },
        lang="ru",
    )
    assert payload["state"] == "collecting"
    assert payload["delivery"]["automatic"] is False
    assert "первый достоверный выпуск" in daily_digest_text(payload).lower()
