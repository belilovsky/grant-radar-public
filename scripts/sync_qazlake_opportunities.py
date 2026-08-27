#!/usr/bin/env python3
"""Idempotently consume the protected QazLake QAZ.FUND projection."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from core.db import SqlRepository


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _cursor(path: Path) -> int:
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("cursor", 0))
    except FileNotFoundError:
        return 0


def _store_cursor(path: Path, cursor: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"schema_version": "qazfund-qazlake-cursor/v1", "cursor": cursor})
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _record(item: dict) -> dict:
    result = {
        key: item.get(key)
        for key in (
            "source",
            "source_url",
            "type",
            "title",
            "summary",
            "funder",
            "amount_min",
            "amount_max",
            "currency",
            "eligibility",
            "tags",
            "languages",
            "score",
            "opportunity_status",
            "lifecycle",
        )
    }
    result["raw"] = {
        "external_id": item["external_id"],
        "qazlake_content_hash": item["content_hash_sha256"],
        "qazlake_ingested_at": item["ingested_at"],
    }
    if item.get("deadline"):
        result["deadline"] = date.fromisoformat(str(item["deadline"]))
    result["discovered_at"] = (
        datetime.fromisoformat(
            str(item["discovered_at"]).replace("Z", "+00:00")
        ).replace(tzinfo=None)
        if item.get("discovered_at")
        else datetime.utcnow()
    )
    return result


def sync_once() -> int:
    endpoint = _env("QAZLAKE_QAZFUND_FEED_URL").rstrip("/")
    token = _env("QAZLAKE_PRODUCT_FEED_TOKEN")
    database_url = _env("GRANT_RADAR_DB_URL")
    cursor_path = Path(
        os.getenv(
            "QAZFUND_QAZLAKE_CURSOR_PATH",
            "/var/lib/grant-radar/qazlake-opportunities.cursor.json",
        )
    )
    cursor = _cursor(cursor_path)
    repository = SqlRepository(database_url)
    while True:
        request = Request(
            f"{endpoint}?cursor={cursor}&limit=200",
            headers={"X-QazLake-Feed-Token": token, "Accept": "application/json"},
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("schema_version") != "qazlake.qazfund-opportunity-feed/v1":
            raise RuntimeError("unexpected QazLake opportunity feed contract")
        for item in payload.get("items", []):
            repository.upsert(_record(item))
            cursor = max(cursor, int(item["cursor"]))
        _store_cursor(cursor_path, cursor)
        if not payload.get("has_more"):
            break
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loop-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.loop_seconds < 0:
        raise RuntimeError("--loop-seconds must be non-negative")
    while True:
        sync_once()
        heartbeat = os.environ.get("GRANT_RADAR_WORKER_HEARTBEAT_PATH", "").strip()
        if heartbeat:
            Path(heartbeat).touch()
        if not args.loop_seconds:
            return 0
        time.sleep(args.loop_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
