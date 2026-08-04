"""Export a reproducible local editorial workbench from public NDJSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.workbench import (
    DEFAULT_INPUT_URL,
    WorkbenchError,
    build_workbench,
    read_ndjson_path,
    read_ndjson_text,
    read_ndjson_url,
    write_workbench,
)


def _read_input(value: str, *, timeout: float) -> list[dict[str, object]]:
    if value == "-":
        return read_ndjson_text(sys.stdin.read(), input_label="stdin")
    if value.startswith(("https://", "http://")):
        return read_ndjson_url(value, timeout=timeout)
    return read_ndjson_path(Path(value))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a safe JSON/CSV/README editorial workbench from public NDJSON."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_URL,
        help="NDJSON URL, local file, or '-' for stdin.",
    )
    parser.add_argument("--output", required=True, help="Output directory.")
    parser.add_argument(
        "--query",
        "--q",
        default="",
        help="Search title, summary, funder, source, or tags.",
    )
    parser.add_argument("--tag", default="", help="Exact case-insensitive tag.")
    parser.add_argument(
        "--source", default="", help="Exact case-insensitive source slug."
    )
    parser.add_argument(
        "--deadline-after",
        default="",
        help="Keep records with a known deadline on or after YYYY-MM-DD.",
    )
    parser.add_argument(
        "--lifecycle",
        choices=("open", "closing_soon", "rolling", "forecast", "closed", "awarded"),
        default="",
    )
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--force", action="store_true", help="Replace existing output files."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        rows = _read_input(args.input, timeout=args.timeout)
        payload, selected = build_workbench(
            rows,
            input_label=args.input,
            query=args.query,
            tag=args.tag,
            source=args.source,
            deadline_after=args.deadline_after,
            lifecycle=args.lifecycle,
            limit=args.limit,
        )
        paths = write_workbench(Path(args.output), payload, selected, force=args.force)
    except WorkbenchError as exc:
        print(f"workbench export failed: {exc}", file=sys.stderr)
        return 2
    selection = payload["selection"]
    print(
        json.dumps(
            {
                "status": "ok",
                "input_rows": len(rows),
                "selected_rows": len(selected),
                "selection_hash": selection["hash"],
                "files": [str(path) for path in paths],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
