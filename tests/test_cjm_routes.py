from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from api import main as api_main
from core.models import Opportunity, OpportunityType


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def _reset_api_state(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DATABASE_URL",
        "GRANT_RADAR_ADMIN_TOKEN",
        "GRANT_RADAR_ALLOWED_HOSTS",
        "GRANT_RADAR_DB_URL",
        "PUBLIC_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def _opportunity(
    *,
    title: str,
    external_id: str,
    deadline: date | None,
    status: str = "open",
    application_url: str | None = "https://example.org/apply",
    eligibility: list[str] | None = None,
    amount: int | None = 5_000_000,
) -> Opportunity:
    raw = {
        "external_id": external_id,
        "status": status,
        "source_checked_at": "2026-07-27T10:00:00+00:00",
    }
    if application_url:
        raw["application_url"] = application_url
    return Opportunity(
        source="cjm_fixture",
        source_url=f"https://example.org/programmes/{external_id.lower()}",
        type=OpportunityType.GRANT,
        title=title,
        summary=(
            "Финансирование проектов из Казахстана с прямой ссылкой на "
            "условия организатора."
        ),
        funder="Фонд развития Казахстана",
        amount_max=amount,
        currency="KZT",
        deadline=deadline,
        eligibility=(
            ["Организации и команды из Казахстана"]
            if eligibility is None
            else eligibility
        ),
        tags=["kazakhstan", "business", "grant"],
        score=0.91,
        discovered_at=datetime.now(timezone.utc),
        opportunity_status=status,
        raw=raw,
    )


def _seed_journey_states() -> dict[str, Opportunity]:
    today = date.today()
    items = {
        "open": _opportunity(
            title="Открытый грант для цифрового проекта",
            external_id="CJM-OPEN",
            deadline=today + timedelta(days=45),
        ),
        "forecast": _opportunity(
            title="Предстоящий конкурс для исследователей",
            external_id="CJM-FORECAST",
            deadline=today + timedelta(days=90),
            status="upcoming",
        ),
        "closed": _opportunity(
            title="Завершённая программа поддержки",
            external_id="CJM-CLOSED",
            deadline=today - timedelta(days=20),
            status="closed",
        ),
        "missing": _opportunity(
            title="Программа с неполными условиями",
            external_id="CJM-MISSING",
            deadline=None,
            application_url=None,
            eligibility=[],
            amount=None,
        ),
    }
    api_main._cache.extend(items.values())
    api_main._clear_public_items_cache()
    return items


def _internal_links(html: str) -> list[str]:
    parser = _LinkParser()
    parser.feed(html)
    links: list[str] = []
    for raw_href in parser.links:
        href = raw_href.strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        parsed = urlsplit(href)
        if parsed.scheme in {"http", "https"} and parsed.netloc != "testserver":
            continue
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            continue
        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        links.append(f"{path}{query}")
    return sorted(set(links))


def test_human_route_graph_is_connected_in_both_languages(monkeypatch):
    _reset_api_state(monkeypatch)
    items = _seed_journey_states()
    funder_slug = next(iter(api_main._funder_index("ru")))
    client = TestClient(api_main.app)

    dynamic_paths = (
        f"/opportunity/{items['open'].id}",
        f"/opportunity/{items['open'].id}/prepare",
        f"/funder/{funder_slug}",
    )
    static_paths = (
        "/",
        "/insights",
        "/docs",
        "/status",
        "/terms",
        "/data-policy",
        "/data-routes",
        "/attribution",
        "/operator",
    )
    crawl_paths = (
        "/",
        "/insights",
        "/status",
        "/terms",
        "/data-policy",
        "/data-routes",
        "/attribution",
        *dynamic_paths,
    )

    for lang in ("ru", "en"):
        for path in (*static_paths, *dynamic_paths):
            response = client.get(path, params={"lang": lang})
            assert response.status_code == 200, path
            assert response.headers["content-type"].startswith("text/html"), path
            assert f'<html lang="{lang}"' in response.text, path
            assert "QAZ.FUND" in response.text, path
            assert "\u2014" not in response.text, path

            head = client.head(path, params={"lang": lang})
            assert head.status_code == 200, path
            assert not head.content, path

        for path in crawl_paths:
            response = client.get(path, params={"lang": lang})
            for href in _internal_links(response.text):
                linked = client.get(href)
                assert linked.status_code < 400, f"{path} -> {href}"


def test_lifecycle_changes_the_application_route(monkeypatch):
    _reset_api_state(monkeypatch)
    items = _seed_journey_states()
    client = TestClient(api_main.app)

    closed = client.get(f"/opportunity/{items['closed'].id}?lang=ru")
    assert closed.status_code == 200
    assert "Приём завершён" in closed.text
    assert f"/opportunity/{items['closed'].id}/prepare" not in closed.text
    assert "Открыть подачу" not in closed.text

    closed_workspace = client.get(f"/opportunity/{items['closed'].id}/prepare?lang=ru")
    assert closed_workspace.status_code == 200
    assert "Приём по этой программе завершён" in closed_workspace.text

    forecast = client.get(f"/opportunity/{items['forecast'].id}?lang=ru")
    assert forecast.status_code == 200
    assert "Приём ещё не открыт" in forecast.text
    assert f"/opportunity/{items['forecast'].id}/prepare?lang=ru" in forecast.text

    forecast_workspace = client.get(
        f"/opportunity/{items['forecast'].id}/prepare?lang=ru"
    )
    assert forecast_workspace.status_code == 200
    assert "Заполняйте черновик предварительно" in forecast_workspace.text


def test_missing_empty_and_broken_link_states_have_recovery(monkeypatch):
    _reset_api_state(monkeypatch)
    items = _seed_journey_states()
    client = TestClient(api_main.app)

    incomplete = client.get(f"/opportunity/{items['missing'].id}?lang=ru")
    assert incomplete.status_code == 200
    assert "Что уточнить" in incomplete.text
    assert "сумму" in incomplete.text
    assert "требования к заявителю" in incomplete.text
    assert "путь подачи" in incomplete.text

    browser_404 = client.get(
        "/opportunity/not-a-uuid",
        params={"lang": "ru"},
        headers={"Accept": "text/html"},
    )
    assert browser_404.status_code == 404
    assert "Вернуться в каталог" in browser_404.text
    assert 'href="/insights?lang=ru"' in browser_404.text
    assert 'href="/status?lang=ru"' in browser_404.text

    machine_422 = client.get(
        "/api/v1/opportunities/not-a-uuid",
        headers={"Accept": "application/json"},
    )
    assert machine_422.status_code == 422
    assert machine_422.headers["content-type"].startswith("application/json")

    api_main._cache.clear()
    api_main._clear_public_items_cache()
    empty_api = client.get("/api/v1/opportunities")
    empty_insights = client.get("/insights?lang=ru")
    empty_status = client.get("/status?lang=ru")
    empty_home = client.get("/?lang=ru")
    assert empty_api.json()["total_count"] == 0
    assert "Данных пока недостаточно" in empty_insights.text
    assert "Статус источников" in empty_status.text
    assert "Записей / актуально" in empty_status.text
    assert "Каталог временно не содержит доступных карточек" in empty_home.text
    assert "emptyStateActions" in empty_home.text


def test_machine_and_operator_routes_have_explicit_boundaries(monkeypatch):
    _reset_api_state(monkeypatch)
    _seed_journey_states()
    client = TestClient(api_main.app)

    json_routes = (
        "/health",
        "/ready",
        "/sources",
        "/coverage",
        "/funders",
        "/api/v1",
        "/api/v1/schema",
        "/api/v1/opportunities",
        "/api/v1/insights",
        "/api/v1/changes",
        "/media/v1/feed.json",
        "/media/v1/digest/daily.json",
        "/.well-known/qdev-ecosystem.json",
        "/.well-known/avds-ui-contract.json",
    )
    for path in json_routes:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "json" in response.headers["content-type"], path

    head_routes = (
        "/sources",
        "/funders",
        "/api/v1",
        "/api/v1/schema",
        "/api/v1/opportunities",
        "/api/v1/opportunities.ndjson",
        "/api/v1/insights",
        "/api/v1/changes",
        "/opportunities.ndjson",
    )
    for path in head_routes:
        response = client.head(path)
        assert response.status_code == 200, path
        assert response.content == b"", path

    api_index = client.get("/api/v1").json()["routes"]
    assert api_index["daily_digest_json"].endswith("/media/v1/digest/daily.json")
    assert api_index["daily_digest_text"].endswith("/media/v1/digest/daily.txt")

    operator = client.get("/operator?lang=ru")
    assert operator.status_code == 200
    assert operator.headers["x-robots-tag"] == "noindex, nofollow"
    assert client.get("/operator/health").status_code in {401, 404}
    assert client.post("/refresh").status_code in {401, 404}
