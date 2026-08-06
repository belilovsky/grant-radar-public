from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from api import main as api_main
from api.embed_page import render_coverage_embed, render_opportunities_embed
from core.models import Opportunity, OpportunityType


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ALLOWED_HOSTS", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_public_items_cache()


def _opportunity() -> Opportunity:
    return Opportunity(
        source="official_source",
        source_url="https://official.example.org/program",
        type=OpportunityType.GRANT,
        title="Kazakhstan public-interest programme",
        summary="A public support programme for organisations in Kazakhstan.",
        deadline=date.today() + timedelta(days=21),
        tags=["kazakhstan", "support"],
        score=0.8,
        discovered_at=datetime(2026, 8, 1, 10, 0),
        raw={"source_html": "must never appear in an embed", "private_note": "hidden"},
    )


def test_opportunity_embed_is_localized_and_public_fields_only() -> None:
    html = render_opportunities_embed(items=[_opportunity()], lang="kk")

    assert '<html lang="kk"' in html
    assert "Өзекті мүмкіндіктер" in html
    assert "Kazakhstan public-interest programme" in html
    assert "source_html" not in html
    assert "private_note" not in html
    assert "<script" not in html
    assert 'data-avds-pattern="ListItem"' in html


def test_coverage_embed_renders_only_explicit_coverage_fields() -> None:
    html = render_coverage_embed(
        coverage={
            "enabled_sources": 2,
            "fresh_sources": 1,
            "stale_sources": 1,
            "unknown_freshness_sources": 0,
            "sources": [
                {
                    "slug": "official_source",
                    "name": "Official source",
                    "base_url": "https://official.example.org",
                    "enabled": True,
                    "items": 8,
                    "relevant_open_items": 3,
                    "freshness_status": "fresh",
                    "raw": "must never appear",
                }
            ],
        },
        lang="en",
    )

    assert '<html lang="en"' in html
    assert "Source coverage" in html
    assert "Official source" in html
    assert "3 relevant / 8" in html
    assert "must never appear" not in html
    assert 'data-avds-pattern="StatGroup"' in html


def test_embed_routes_allow_qaz_support_frames_and_keep_regular_pages_same_origin(
    monkeypatch,
) -> None:
    _reset_api_state(monkeypatch)
    api_main._cache.append(_opportunity())
    client = TestClient(api_main.app)

    widget = client.get("/embed/opportunities", params={"lang": "en"})
    regular = client.get("/status", params={"lang": "en"})

    assert widget.status_code == 200
    assert widget.headers.get("x-frame-options") is None
    assert (
        "frame-ancestors https://qaz.support"
        in widget.headers["content-security-policy"]
    )
    assert widget.headers["x-robots-tag"] == "noindex, nofollow"
    assert widget.headers["cache-control"].startswith("public, max-age=300")
    assert "source_html" not in widget.text
    assert "X-Frame-Options" not in widget.text

    assert regular.status_code == 200
    assert regular.headers["x-frame-options"] == "SAMEORIGIN"
