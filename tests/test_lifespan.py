from __future__ import annotations

import asyncio

import pytest

from api import main as api_main


@pytest.mark.asyncio
async def test_lifespan_does_not_warm_public_caches_before_ready(monkeypatch) -> None:
    def unexpected_warmup() -> None:
        raise AssertionError("cold cache warmup must not hold application startup")

    monkeypatch.setattr(api_main, "_warm_public_sitemap_cache", unexpected_warmup)
    monkeypatch.setattr(api_main, "_warm_public_items_cache", unexpected_warmup)

    async with api_main._lifespan(api_main.app):
        await asyncio.sleep(0)
