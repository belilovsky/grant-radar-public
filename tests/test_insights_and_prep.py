from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api import main as api_main
from api.daily_digest import daily_digest_payload, daily_digest_text
from core.db import SqlRepository
from core.models import Opportunity, OpportunityType


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
    assert "/api/v1/changes?hours=24" in page.text
    assert "\u2014" not in page.text
    assert "QazCompute" not in page.text


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
