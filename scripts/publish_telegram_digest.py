#!/usr/bin/env python3
"""Preview or explicitly publish the QAZ.FUND daily digest to Telegram.

This is intentionally a one-shot command. It does not create a timer, cron
entry, daemon or background process. Sending requires both ``--send`` and an
idempotency state file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def _digest_hash(payload: dict[str, Any]) -> str:
    stable = {
        "state": payload.get("state"),
        "period_from": payload.get("period_from"),
        "period_to": payload.get("period_to"),
        "created": payload.get("created"),
        "changed": payload.get("changed"),
        "items": [
            {
                "id": item.get("id"),
                "change_type": item.get("change_type"),
                "content_hash": item.get("content_hash"),
            }
            for item in payload.get("items") or []
        ],
    }
    raw = json.dumps(
        stable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview the QAZ.FUND daily change digest. Add --send plus an "
            "idempotency state file for an explicit Telegram publication."
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("QAZFUND_PUBLIC_URL", "https://qaz.fund"),
    )
    parser.add_argument("--lang", choices=("ru", "en"), default="ru")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send once to Telegram. Without this flag the command only previews.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        help="Required with --send; prevents repeat delivery of the same digest.",
    )
    parser.add_argument(
        "--send-empty",
        action="store_true",
        help="Also send collecting/no-change editions.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send even when the state file already records this digest.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    endpoint = (
        f"{args.base_url.rstrip('/')}/media/v1/digest/daily.json"
        f"?lang={args.lang}&limit={max(1, min(args.limit, 30))}"
    )
    try:
        response = httpx.get(endpoint, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        print(f"error: could not load daily digest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("error: daily digest did not return an object", file=sys.stderr)
        return 2

    text = str(payload.get("text") or "").strip()
    if not text:
        print("error: daily digest text is empty", file=sys.stderr)
        return 2
    digest_hash = _digest_hash(payload)
    print(text)
    print(f"\nDigest: {digest_hash}")
    print(f"State: {payload.get('state')}")
    if not args.send:
        print("Delivery: preview only")
        return 0

    if args.state_file is None:
        print("error: --state-file is required with --send", file=sys.stderr)
        return 2
    if payload.get("state") != "ready" and not args.send_empty:
        print("Delivery: skipped because the edition has no publishable changes")
        return 0
    previous = _read_state(args.state_file)
    if previous.get("digest_hash") == digest_hash and not args.force:
        print("Delivery: already sent; idempotency state matched")
        return 0

    token = os.environ.get("QAZFUND_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("QAZFUND_TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print(
            "error: QAZFUND_TELEGRAM_BOT_TOKEN and "
            "QAZFUND_TELEGRAM_CHAT_ID are required",
            file=sys.stderr,
        )
        return 2
    try:
        telegram = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text[:4096],
                "link_preview_options": {"is_disabled": True},
            },
            timeout=30.0,
        )
        telegram.raise_for_status()
        result = telegram.json()
    except (httpx.HTTPError, ValueError) as exc:
        print(f"error: Telegram delivery failed: {exc}", file=sys.stderr)
        return 3
    if not isinstance(result, dict) or not result.get("ok"):
        print("error: Telegram rejected the message", file=sys.stderr)
        return 3

    message = result.get("result")
    message_id = message.get("message_id") if isinstance(message, dict) else None
    _write_state(
        args.state_file,
        {
            "schema_version": "qazfund-telegram-delivery-state.v1",
            "digest_hash": digest_hash,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "message_id": message_id,
        },
    )
    print(f"Delivery: sent (message_id={message_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
