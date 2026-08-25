from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from api import main as api_main
from api.media import citation_text, render_opportunity_card_svg
from core.models import Opportunity, OpportunityType
from core.public_contract import to_opportunity_v1


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ALLOWED_HOSTS", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def _sample_opportunity() -> Opportunity:
    return Opportunity(
        source="astana_hub",
        source_url="https://example.org/astana-hub/program",
        type=OpportunityType.GRANT,
        title="AI infrastructure grant",
        summary="Cloud and implementation support for Kazakhstan teams.",
        funder="Astana Hub",
        tags=["kazakhstan", "ai", "startup", "grant"],
        eligibility=["Kazakhstan technology teams"],
        deadline=date(2026, 8, 31),
        discovered_at=datetime(2026, 7, 20, 9, 0, tzinfo=timezone.utc),
        score=0.9,
        raw={
            "i18n": {
                "ru": {
                    "title": "Грант на инфраструктуру ИИ",
                    "summary": "Облачная инфраструктура и внедрение для команд из Казахстана.",
                }
            },
            "application_url": "https://example.org/astana-hub/apply",
            "amount_raw": "до 5 000 000 тенге",
            "source_checked_at": "2026-07-21T10:00:00+00:00",
        },
    )


def test_media_projection_uses_kazakh_labels_for_source_and_deadline() -> None:
    item = to_opportunity_v1(_sample_opportunity())

    citation = citation_text(item, lang="kk")
    svg = render_opportunity_card_svg(item, lang="kk")

    assert "Дереккөз: Astana Hub." in citation
    assert "Ресми дереккөз" in citation
    assert "31.08.2026" in svg
    assert "Дереккөз: Astana Hub" in svg
    assert "грант беруші емес" in svg


def test_api_v1_exposes_versioned_public_contract(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _sample_opportunity()
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get("/api/v1/opportunities", params={"lang": "ru", "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "qazfund-dataset.v1"
    assert data["opportunity_schema_version"] == "opportunity.v1"
    assert data["total_count"] == 1
    row = data["items"][0]
    assert row["schema_version"] == "opportunity.v1"
    assert row["title"] == "Грант на инфраструктуру ИИ"
    assert row["source"]["name"] == "Astana Hub"
    assert row["links"]["official_source"] == "https://example.org/astana-hub/program"
    assert row["links"]["api"] == f"http://testserver/api/v1/opportunities/{item.id}"
    assert row["provenance"]["evidence_state"] == "sourced"
    assert row["quality"]["score_meaning"].startswith("record completeness")
    assert response.headers["x-dataset-schema-version"] == "qazfund-dataset.v1"

    detail = client.get(f"/api/v1/opportunities/{item.id}", params={"lang": "ru"})
    assert detail.status_code == 200
    assert detail.json()["funding_amount"]["display"] == "до 5 000 000 тенге"

    ndjson = client.get("/api/v1/opportunities.ndjson", params={"lang": "ru"})
    assert ndjson.status_code == 200
    assert ndjson.text.count("\n") == 1
    assert '"schema_version":"opportunity.v1"' in ndjson.text


def test_public_contract_does_not_call_admission_a_grant() -> None:
    item = _sample_opportunity()
    item.title = "Приём в колледжи по государственному заказу"
    item.tags = ["kazakhstan", "education", "education_admission"]
    item.raw["opportunity_taxonomy"] = {
        "instrument": "education_admission",
        "application_mode": "admission",
        "deadline_model": "multiple",
    }

    public = to_opportunity_v1(item)

    assert public.formats == ["education_admission"]
    assert "grant" not in public.formats


def test_media_v1_outputs_citation_cards_charts_and_feeds(monkeypatch):
    _reset_api_state(monkeypatch)
    item = _sample_opportunity()
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    citation = client.get(
        f"/media/v1/opportunities/{item.id}/citation.txt",
        params={"lang": "ru", "style": "citation"},
    )
    assert citation.status_code == 200
    assert "Грант на инфраструктуру ИИ" in citation.text
    assert "Источник: Astana Hub." in citation.text
    assert "https://example.org/astana-hub/program" in citation.text

    content = client.get(
        f"/media/v1/opportunities/{item.id}/content.json",
        params={"lang": "ru"},
    )
    assert content.status_code == 200
    assert content.json()["schema_version"] == "qazfund-media-content.v1"

    card = client.get(
        f"/media/v1/opportunities/{item.id}/card.svg",
        params={"lang": "ru", "format": "square"},
    )
    assert card.status_code == 200
    assert card.headers["content-type"].startswith("image/svg+xml")
    assert "QAZ.FUND" in card.text
    assert "\u2014" not in card.text

    portrait = client.get(
        f"/media/v1/opportunities/{item.id}/portrait.png",
        params={"lang": "ru"},
    )
    assert portrait.status_code == 200
    assert portrait.headers["content-type"].startswith("image/png")
    assert portrait.content[:8] == b"\x89PNG\r\n\x1a\n"

    chart = client.get("/media/v1/charts/active_by_theme.json", params={"lang": "ru"})
    assert chart.status_code == 200
    assert chart.json()["rows"][0]["label"] == "ИИ"

    chart_svg = client.get(
        "/media/v1/charts/active_by_theme.svg", params={"lang": "ru"}
    )
    assert chart_svg.status_code == 200
    assert "Активные возможности по темам" in chart_svg.text

    feed_json = client.get("/media/v1/feed.json", params={"lang": "ru"})
    assert feed_json.status_code == 200
    assert feed_json.json()["items"][0]["title"] == "Грант на инфраструктуру ИИ"

    feed_rss = client.get("/media/v1/feed.rss", params={"lang": "ru"})
    assert feed_rss.status_code == 200
    assert "<rss" in feed_rss.text
    assert "Грант на инфраструктуру ИИ" in feed_rss.text


def test_public_policy_pages_are_localized(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    ru_terms = client.get("/terms", params={"lang": "ru"})
    en_policy = client.get("/data-policy", params={"lang": "en"})
    attribution = client.get("/attribution", params={"lang": "ru"})

    assert ru_terms.status_code == 200
    assert "Условия использования" in ru_terms.text
    assert "Version dated" not in ru_terms.text
    assert en_policy.status_code == 200
    assert "Data policy" in en_policy.text
    assert "Browser-only draft" in en_policy.text
    assert "preparation-draft content is not sent to analytics" in en_policy.text
    assert attribution.status_code == 200
    assert "систем искусственного интеллекта" in attribution.text
    assert "Лицензия MIT относится к программному коду QAZ.FUND" in attribution.text
