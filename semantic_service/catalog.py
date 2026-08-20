"""Build a minimal, public-safe text representation for semantic indexing."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [normalized for entry in value if (normalized := _text(entry))]


def public_search_document(item: dict[str, Any]) -> dict[str, str] | None:
    """Return an index document without raw source or private data fields."""

    item_id = _text(item.get("id"))
    title = _text(item.get("title"))
    if not item_id or not title:
        return None
    parts = [
        title,
        _text(item.get("summary")),
        _text(item.get("funder")),
        _text(item.get("type")),
        " ".join(_values(item.get("tags"))),
        " ".join(_values(item.get("eligibility"))),
        _text(item.get("source")),
    ]
    return {"id": item_id, "text": "\n".join(part for part in parts if part)}


def public_search_documents(items: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        document = public_search_document(item)
        if document is None or document["id"] in seen:
            continue
        seen.add(document["id"])
        documents.append(document)
    return documents
