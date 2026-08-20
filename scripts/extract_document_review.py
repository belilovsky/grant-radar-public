"""Create a review-only QAZ.FUND draft from one locally supplied document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.document_review import convert_document_to_review_draft


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract only review candidates from an official local document."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    draft = convert_document_to_review_draft(args.input, source_url=args.source_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote review draft: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
