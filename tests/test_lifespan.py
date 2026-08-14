from __future__ import annotations

import asyncio
from threading import Event

import pytest

from api import main as api_main


@pytest.mark.asyncio
async def test_lifespan_does_not_wait_for_public_cache_warmup(monkeypatch) -> None:
    warmup_started = Event()
    release_warmup = Event()
    entered = asyncio.Event()
    release_lifespan = asyncio.Event()

    def blocking_sitemap_warmup() -> None:
        warmup_started.set()
        release_warmup.wait(timeout=2)

    monkeypatch.setattr(api_main, "_warm_public_sitemap_cache", blocking_sitemap_warmup)
    monkeypatch.setattr(api_main, "_warm_public_items_cache", lambda: None)

    async def serve() -> None:
        async with api_main._lifespan(api_main.app):
            entered.set()
            await release_lifespan.wait()

    loop = asyncio.get_running_loop()
    deadline = loop.time() + 0.5
    task = asyncio.create_task(serve())
    await asyncio.to_thread(warmup_started.wait)
    await entered.wait()
    assert loop.time() < deadline

    release_warmup.set()
    release_lifespan.set()
    await task
