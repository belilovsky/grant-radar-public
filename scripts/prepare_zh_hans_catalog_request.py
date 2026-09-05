"""Build the private, source-bound QMT catalog-generation request.

The output contains RU/EN copy and must stay in the existing private artifact
workflow.  The command prints metadata only; catalog text is never logged.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from api.zh_hans import (
    QAZSTACK_CONTRACT_SHA256,
    QAZSTACK_WHEEL_SHA256,
    QMT_RELEASE_TAG,
    ZH_HANS_PUBLIC_ROUTES,
    ZH_HANS_REQUIRED_KEYS,
    _utf16_sort_key,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs/qazstack/zh-hans/source.ru.json"
REFERENCE_PATH = ROOT / "docs/qazstack/zh-hans/reference.en.json"
_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")


def _digest(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", normalized):
        raise ValueError("release digest must be an immutable sha256 reference")
    return normalized


def _sha(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized):
        raise ValueError("source SHA must contain exactly 40 hexadecimal characters")
    return normalized


def _load_copy(path: Path) -> dict[str, str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != ZH_HANS_REQUIRED_KEYS:
        raise ValueError(
            f"{path.name} does not match the source-derived public key set"
        )
    if any(not isinstance(item, str) or not item.strip() for item in value.values()):
        raise ValueError(f"{path.name} contains a blank or non-string value")
    return value


def build_request(arguments: argparse.Namespace) -> dict[str, Any]:
    product_source = _sha(arguments.product_source_sha)
    source = _load_copy(Path(arguments.source))
    reference = _load_copy(Path(arguments.reference))
    mismatched_placeholders = sorted(
        key
        for key in ZH_HANS_REQUIRED_KEYS
        if set(_PLACEHOLDER_RE.findall(source[key]))
        != set(_PLACEHOLDER_RE.findall(reference[key]))
    )
    if mismatched_placeholders:
        raise ValueError(
            "RU source and EN semantic reference placeholders differ for: "
            + ", ".join(mismatched_placeholders)
        )
    return {
        "project": "qaz-fund",
        "sourceSha": product_source,
        "sourceLang": "ru",
        "targetLang": "zh-Hans",
        "sourceCatalog": source,
        "requiredKeys": sorted(ZH_HANS_REQUIRED_KEYS, key=_utf16_sort_key),
        "publicRoutes": list(ZH_HANS_PUBLIC_ROUTES),
        "semanticReference": reference,
        "brands": ["QAZ.FUND", "QazStack", "QMT"],
        "profile": {
            "id": "qaz-fund:ru:zh-Hans",
            "promptVersion": arguments.prompt_version,
            "glossaryVersion": arguments.glossary_version,
            "tmVersion": arguments.tm_version,
        },
        "qmtRelease": {
            "tag": QMT_RELEASE_TAG,
            "sourceSha": _sha(arguments.qmt_source_sha),
            "imageDigest": _digest(arguments.qmt_image_digest),
            "runtimeReceiptDigest": _digest(arguments.qmt_runtime_receipt_digest),
            "migrationReceiptDigest": _digest(arguments.qmt_migration_receipt_digest),
        },
        "productBinding": {
            "sourceSha": product_source,
            "contractDigest": QAZSTACK_CONTRACT_SHA256,
            "wheelDigest": QAZSTACK_WHEEL_SHA256,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--product-source-sha", required=True)
    parser.add_argument("--qmt-source-sha", required=True)
    parser.add_argument("--qmt-image-digest", required=True)
    parser.add_argument("--qmt-runtime-receipt-digest", required=True)
    parser.add_argument("--qmt-migration-receipt-digest", required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument("--glossary-version", required=True)
    parser.add_argument("--tm-version", required=True)
    parser.add_argument("--source", type=Path, default=SOURCE_PATH)
    parser.add_argument("--reference", type=Path, default=REFERENCE_PATH)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    request = build_request(arguments)
    arguments.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{arguments.output.name}.", dir=arguments.output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(request, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.chmod(temporary, 0o600)
        temporary.replace(arguments.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "schemaVersion": "qmt.catalog-generation-request-prepared.v1",
                "project": request["project"],
                "sourceSha": request["sourceSha"],
                "keys": len(request["requiredKeys"]),
                "publicRoutes": len(request["publicRoutes"]),
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
