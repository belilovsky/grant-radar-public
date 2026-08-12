from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from api import main as api_main
from api.media_page import build_media_snapshot
from core.models import Opportunity, OpportunityType


def _item(
    title: str, *, source: str = "official_source", days: int = 14
) -> Opportunity:
    return Opportunity(
        id=uuid4(),
        source=source,
        source_url="https://example.org/program",
        type=OpportunityType.GRANT,
        title=title,
        summary="Поддержка цифровых проектов и команд в Казахстане.",
        funder="Official source",
        deadline=date.today() + timedelta(days=days),
        tags=["digital", "Kazakhstan"],
        score=0.8,
        discovered_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


def test_media_snapshot_is_source_grounded_and_deterministic() -> None:
    items = [
        _item("Позднее обновление"),
        _item("Раннее обновление", source="another_source"),
    ]
    items[0].discovered_at = datetime(2026, 8, 5, 12, 0, 0)
    items[1].discovered_at = datetime(2026, 8, 4, 12, 0, 0)
    snapshot = build_media_snapshot(
        items=items, lang="ru", root_path="", as_of=date.today()
    )

    assert snapshot["schema_version"] == "media.v1"
    assert snapshot["count"] == 2
    assert snapshot["lead"]["title"] == "Позднее обновление"
    assert snapshot["cards"][0]["href"].startswith("/opportunity/")
    assert all("raw" not in card for card in snapshot["cards"])
    assert all("\u2014" not in str(card) for card in snapshot["cards"])


def test_media_pages_have_three_locales_and_machine_contract(monkeypatch) -> None:
    items = [_item("Медиаобновление"), _item("Второе обновление")]
    monkeypatch.setattr(
        api_main, "_cached_public_scope_items", lambda content_lang="ru": list(items)
    )
    client = TestClient(api_main.app)

    for lang in ("kk", "ru", "en"):
        response = client.get(f"/media?lang={lang}")
        assert response.status_code == 200
        assert f'<html lang="{lang}"' in response.text
        assert 'data-avds-component="media-lead"' in response.text
        assert 'data-avds-component="live-feed"' in response.text
        assert f'lang="{lang}" aria-current="page"' in response.text
        assert 'hreflang="kk"' in response.text
        assert 'hreflang="ru"' in response.text
        assert 'hreflang="en"' in response.text
        assert 'type="application/feed+json"' in response.text
        assert 'type="application/rss+xml"' in response.text
        assert 'datetime="' in response.text
        assert (
            ".back,.langs a,.section-head a,.media-card h3 a,.media-card-link,"
            ".media-card-source,.source-shelf-main,.footer a"
        ) in response.text
        assert ".live-feed-row a{min-height:44px}" in response.text
        assert (
            ".source-shelf-arrow{display:inline-grid;place-items:center;width:44px;height:44px}"
            in response.text
        )
        assert "topic=ai" in response.text
        assert "source=official_source" in response.text
        assert "\u2014" not in response.text

    payload = client.get("/media.json?lang=en").json()
    assert payload["schema_version"] == "media.v1"
    assert payload["language"] == "en"
    assert payload["links"]["human"].endswith("/media?lang=en")
    assert payload["sources"][0]["slug"] == "official_source"
    assert "raw" not in str(payload)

    feed_response = client.get("/media/feed.json?lang=en")
    assert feed_response.status_code == 200
    feed = feed_response.json()
    assert feed["version"] == "https://jsonfeed.org/version/1.1"
    assert feed["feed_url"].endswith("/media/feed.json?lang=en")
    assert feed["items"][0]["url"].startswith("http://testserver/opportunity/")
    assert feed["items"][0]["external_url"] == "https://example.org/program"
    assert "raw" not in str(feed)

    rss_response = client.get("/media/rss.xml?lang=en")
    assert rss_response.status_code == 200
    assert rss_response.headers["content-type"].startswith("application/rss+xml")
    assert '<rss version="2.0"' in rss_response.text
    assert "<link>http://testserver/opportunity/" in rss_response.text
    assert "https://example.org/program" in rss_response.text
    assert "raw" not in rss_response.text
