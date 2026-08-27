#!/usr/bin/env python3
"""Emit every QAZ.FUND source record for execution by the QazPipe owner.

This program has no scheduler, database writes or network policy of its own.
QazPipe invokes it through its locked runner and owns retries, delivery and
run evidence. Stdout is strictly JSONL so it is safe as an adapter boundary.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Any

from sources import PARSERS


def _jsonable(record: Any) -> dict[str, Any]:
    dump = record.model_dump(mode="json") if hasattr(record, "model_dump") else dict(record.__dict__)
    # Queue-oriented GrantRecord adapters and rich Opportunity adapters share
    # one transport contract without changing their product-local classes.
    dump.setdefault("source", str(getattr(record, "source", "")))
    dump.setdefault("source_url", str(getattr(record, "url", "")))
    dump.setdefault("summary", str(dump.get("description") or ""))
    dump.setdefault("type", "grant")
    dump.setdefault("currency", "USD")
    dump.setdefault("eligibility", [])
    dump.setdefault("tags", [])
    dump.setdefault("languages", [])
    raw = dump.get("raw") if isinstance(dump.get("raw"), dict) else {}
    external_id = str(raw.get("external_id") or raw.get("reference") or getattr(record, "external_id", "")).strip()
    if not external_id:
        external_id = str(getattr(record, "url", "")).strip()
    if not external_id:
        raise ValueError("source record has no stable external identity")
    return {"source_id": str(getattr(record, "source", "")).strip(), "external_id": external_id, "opportunity": dump}


async def run(selected: set[str] | None) -> int:
    emitted = 0
    for source_id, parser_type in PARSERS.items():
        if selected and source_id not in selected:
            continue
        parser = parser_type()
        try:
            async with parser:
                async for record in parser.fetch():
                    payload = _jsonable(record)
                    if not payload["source_id"]:
                        payload["source_id"] = source_id
                    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)
                    emitted += 1
        except Exception as exc:  # The owning QazPipe run must fail visibly.
            print(f"adapter source failed: {source_id}: {type(exc).__name__}", file=sys.stderr)
            return 1
    print(f"adapter emitted={emitted}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", dest="sources")
    args = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    return asyncio.run(run(set(args.sources or [])))


if __name__ == "__main__":
    raise SystemExit(main())
