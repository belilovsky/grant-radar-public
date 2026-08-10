import asyncio
from datetime import UTC, datetime

import semantic_service.app as semantic_app


def test_index_loop_retries_quickly_until_first_success(monkeypatch):
    state = semantic_app.ServiceState()
    delays: list[float] = []
    attempts = 0

    async def fake_reindex(current_state):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            current_state.indexed_at = datetime.now(UTC)

    async def fake_sleep(delay):
        delays.append(delay)
        if len(delays) == 2:
            raise asyncio.CancelledError

    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_REINDEX_INTERVAL_SECONDS", "600")
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_STARTUP_RETRY_SECONDS", "3")
    monkeypatch.setattr(semantic_app, "reindex", fake_reindex)
    monkeypatch.setattr(semantic_app.asyncio, "sleep", fake_sleep)

    try:
        asyncio.run(semantic_app._index_loop(state))
    except asyncio.CancelledError:
        pass

    assert attempts == 2
    assert delays == [3, 600]
