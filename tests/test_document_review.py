from __future__ import annotations

from pathlib import Path

import pytest

from core.document_review import document_sha256, official_source_url, review_draft


def test_review_draft_is_non_publishing_and_does_not_retain_source_text():
    source_text = (
        "# Open AI fund\nDeadline: 2026-12-31\nBudget: USD 25,000\n"
        "Contact: private@example.org"
    )

    draft = review_draft(
        source_text,
        source_url="https://fund.example.org/call.pdf",
        source_sha256="abc123",
    )

    assert draft["publication_state"] == "draft"
    assert draft["review_required"] is True
    assert draft["source"] == {
        "url": "https://fund.example.org/call.pdf",
        "sha256": "abc123",
    }
    assert draft["candidates"]["title"] == "Open AI fund"
    assert draft["candidates"]["deadline_mentions"] == ["2026-12-31"]
    assert "private@example.org" not in str(draft)
    assert "source_text" not in draft


def test_review_source_requires_https_provenance():
    with pytest.raises(ValueError, match="HTTPS"):
        official_source_url("file:///tmp/private.pdf")


def test_document_hash_is_repeatable(tmp_path: Path):
    document = tmp_path / "notice.pdf"
    document.write_bytes(b"synthetic public notice")

    assert document_sha256(document) == document_sha256(document)
