"""Regression coverage for the QazPipe JSONL adapter boundary."""

from __future__ import annotations

import asyncio
import json

from scripts import qazpipe_adapter
from sources import GrantRecord


class NoisyParser:
    """A concrete adapter fixture that writes legacy progress to stdout."""

    async def __aenter__(self) -> "NoisyParser":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def fetch(self):
        print("legacy parser progress")
        yield GrantRecord(
            source="fixture",
            external_id="fixture-1",
            title="Fixture opportunity",
            url="https://example.test/opportunities/fixture-1",
        )


def test_adapter_emits_jsonl_only_and_redirects_parser_stdout(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(qazpipe_adapter, "PARSERS", {"fixture": NoisyParser})

    assert asyncio.run(qazpipe_adapter.run({"fixture"})) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["source_id"] == "fixture"
    assert payload["external_id"] == "fixture-1"
    assert "legacy parser progress" not in captured.out
    assert "adapter source stdout redirected: fixture" in captured.err
