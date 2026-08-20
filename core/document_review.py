"""Review-only extraction helpers for official opportunity documents.

This module intentionally produces a compact review draft, not an Opportunity.
No document text is persisted and no extraction result can enter the public
catalog without the existing source and editorial review paths.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_DATE_PATTERN = re.compile(
    r"\b(?:20\d{2}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[./]\d{1,2}[./]20\d{2})\b"
)
_AMOUNT_PATTERN = re.compile(
    r"\b(?:USD|EUR|KZT|₸|\$|€)\s?[\d][\d\s,.]*(?:million|mln|m|тыс\.?|миллион(?:ов|а)?)?\b",
    re.IGNORECASE,
)


def official_source_url(value: str) -> str:
    """Accept an explicit HTTPS provenance link and reject local/opaque values."""

    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("source_url must be an absolute HTTPS URL")
    return normalized


def document_sha256(path: Path) -> str:
    """Return a provenance hash without retaining the source document."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def review_draft(
    markdown: str,
    *,
    source_url: str,
    source_sha256: str,
) -> dict[str, Any]:
    """Create a non-publishing fact-candidate envelope from extracted Markdown."""

    normalized_url = official_source_url(source_url)
    lines = [" ".join(line.split()) for line in markdown.splitlines()]
    visible_lines = [line.lstrip("# ").strip() for line in lines if line.strip()]
    title = next((line for line in visible_lines if len(line) >= 8), "")
    deadlines = list(dict.fromkeys(_DATE_PATTERN.findall(markdown)))[:8]
    amounts = list(dict.fromkeys(_AMOUNT_PATTERN.findall(markdown)))[:8]
    return {
        "schema_version": "qazfund-document-review-draft.v1",
        "publication_state": "draft",
        "review_required": True,
        "source": {
            "url": normalized_url,
            "sha256": source_sha256,
        },
        "candidates": {
            "title": title or None,
            "deadline_mentions": deadlines,
            "amount_mentions": amounts,
        },
        "limitations": [
            "Extraction is a reviewer aid, not evidence of eligibility or an open call.",
            "No extracted text, contact details, or document images are retained in this draft.",
            "A reviewed source adapter is required before public catalog publication.",
        ],
    }


def convert_document_to_review_draft(path: Path, *, source_url: str) -> dict[str, Any]:
    """Run Docling locally and return a compact non-publishing review draft."""

    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover - optional heavyweight dependency
        raise RuntimeError(
            "Docling is not installed; install requirements-document-review.txt"
        ) from exc
    result = DocumentConverter().convert(path)
    markdown = result.document.export_to_markdown()
    return review_draft(
        markdown,
        source_url=source_url,
        source_sha256=document_sha256(path),
    )
