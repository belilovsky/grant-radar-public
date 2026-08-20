#!/usr/bin/env python3
"""Fail when public QAZ.FUND source contains an editorial em dash."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.typography_policy import POLICY_VERSION, scan_text  # noqa: E402

PUBLIC_ROOTS = ("api", "core", "sources")
PUBLIC_SUFFIXES = {
    ".css",
    ".htm",
    ".html",
    ".js",
    ".json",
    ".jsonld",
    ".mjs",
    ".py",
    ".scss",
    ".svg",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".playwright-cli",
    "output",
    "generated",
    "snapshots",
    "node_modules",
}
IGNORED_FILES = {
    Path("core/typography_policy.py"),
    Path("scripts/check_typography.py"),
}


def iter_public_files() -> list[Path]:
    paths: list[Path] = []
    for root_name in PUBLIC_ROOTS:
        root = ROOT / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in PUBLIC_SUFFIXES:
                continue
            relative = path.relative_to(ROOT)
            if relative in IGNORED_FILES or any(
                part in IGNORED_PARTS for part in relative.parts
            ):
                continue
            paths.append(path)
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)

    findings: list[dict[str, object]] = []
    for path in iter_public_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for finding in scan_text(text):
            findings.append({"path": str(path.relative_to(ROOT)), **finding})
    report = {
        "policy_version": POLICY_VERSION,
        "scope": "public_api_core_sources",
        "finding_count": len(findings),
        "findings": findings,
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
