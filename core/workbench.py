"""Build a safe, deterministic editorial workbench from public NDJSON.

The workbench is intentionally a local export contract.  It projects public
opportunity records into a small set of fields, never carries ``raw`` source
payloads forward, and makes the selected set content-addressable so an editor
can reproduce a handoff later.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

WORKBENCH_SCHEMA_VERSION = "qazfund-workbench.v1"
DEFAULT_INPUT_URL = (
    "https://qaz.fund/opportunities.ndjson?lang=ru&limit=5000&min_score=0"
    "&include_irrelevant=true&compact=true"
)
WORKBENCH_FIELDS = (
    "id",
    "source",
    "source_url",
    "type",
    "title",
    "summary",
    "funder",
    "amount_min",
    "amount_max",
    "currency",
    "deadline",
    "eligibility",
    "tags",
    "opportunity_status",
    "lifecycle",
    "application_url",
    "score",
    "evidence_state",
    "discovered_at",
    "provenance",
)
CSV_FIELDS = (
    "id",
    "source",
    "source_url",
    "type",
    "title",
    "summary",
    "funder",
    "amount_min",
    "amount_max",
    "currency",
    "deadline",
    "eligibility",
    "tags",
    "opportunity_status",
    "lifecycle",
    "application_url",
    "score",
    "evidence_state",
    "discovered_at",
)
_PROVENANCE_FIELDS = (
    "schema_version",
    "source",
    "source_url",
    "evidence_state",
    "evidence_basis",
    "observed_at",
    "last_verified_at",
    "source_language",
    "source_language_basis",
    "status",
    "deadline_confidence",
    "amount_confidence",
    "missing_metadata",
)


class WorkbenchError(ValueError):
    """Raised when an input cannot be safely converted into a workbench."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    values: Sequence[Any] = [value] if isinstance(value, str) else value
    if not isinstance(values, Sequence):
        values = [value]
    return [_text(item) for item in values if _text(item)]


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _date_text(value: Any, *, field: str, item_id: str) -> str:
    text = _text(value)
    if not text:
        return ""
    try:
        date.fromisoformat(text[:10])
    except ValueError as exc:
        raise WorkbenchError(
            f"item {item_id}: {field} must start with an ISO date, got {text!r}"
        ) from exc
    return text


def _number(value: Any, *, field: str, item_id: str) -> float | int | str | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise WorkbenchError(f"item {item_id}: {field} must be numeric")
    if isinstance(value, (int, float)):
        return value
    text = _text(value)
    try:
        number = float(text)
    except ValueError as exc:
        raise WorkbenchError(
            f"item {item_id}: {field} must be numeric, got {text!r}"
        ) from exc
    return int(number) if number.is_integer() else number


def _safe_provenance(raw: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(raw.get("provenance"))
    if not provenance:
        return {}
    return {
        key: provenance[key]
        for key in _PROVENANCE_FIELDS
        if key in provenance and provenance[key] is not None
    }


def project_safe_item(item: Mapping[str, Any]) -> dict[str, Any]:
    """Project one public row without copying the ingestion payload."""

    item_id = _text(item.get("id"))
    if not item_id:
        raise WorkbenchError("each item must have a non-empty id")
    raw = _mapping(item.get("raw"))
    provenance = _safe_provenance(raw)
    deadline = _date_text(item.get("deadline"), field="deadline", item_id=item_id)
    discovered_at = _text(item.get("discovered_at"))
    application_url = _first_text(
        item.get("application_url"), raw.get("application_url")
    )
    evidence_state = _first_text(
        item.get("evidence_state"), provenance.get("evidence_state")
    )
    projected: dict[str, Any] = {
        "id": item_id,
        "source": _first_text(item.get("source"), raw.get("source")),
        "source_url": _first_text(item.get("source_url"), raw.get("source_url")),
        "type": _first_text(item.get("type"), raw.get("type")),
        "title": _first_text(item.get("title"), raw.get("title")),
        "summary": _first_text(item.get("summary"), raw.get("summary")),
        "funder": _first_text(item.get("funder"), raw.get("funder")),
        "amount_min": _number(
            item.get("amount_min"), field="amount_min", item_id=item_id
        ),
        "amount_max": _number(
            item.get("amount_max"), field="amount_max", item_id=item_id
        ),
        "currency": _first_text(item.get("currency"), raw.get("currency")),
        "deadline": deadline,
        "eligibility": _list(item.get("eligibility") or raw.get("eligibility")),
        "tags": _list(item.get("tags") or raw.get("tags")),
        "opportunity_status": _first_text(
            item.get("opportunity_status"),
            item.get("lifecycle"),
            raw.get("opportunity_status"),
            raw.get("status"),
        ),
        "lifecycle": _first_text(item.get("lifecycle"), raw.get("lifecycle")),
        "application_url": application_url,
        "score": _number(item.get("score"), field="score", item_id=item_id),
        "evidence_state": evidence_state,
        "discovered_at": discovered_at,
        "provenance": provenance,
    }
    return {field: projected[field] for field in WORKBENCH_FIELDS}


def _match_text(item: Mapping[str, Any]) -> str:
    values = [
        item.get("title"),
        item.get("summary"),
        item.get("funder"),
        item.get("source"),
        " ".join(_list(item.get("tags"))),
    ]
    return " ".join(_text(value) for value in values).casefold()


def _deadline_sort_key(item: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        _text(item.get("deadline")) or "9999-12-31",
        _text(item.get("title")).casefold(),
        _text(item.get("id")),
    )


def select_items(
    items: Iterable[Mapping[str, Any]],
    *,
    query: str = "",
    tag: str = "",
    source: str = "",
    deadline_after: str = "",
    lifecycle: str = "",
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Project, filter, and deterministically order public rows."""

    if limit < 1:
        raise WorkbenchError("limit must be at least 1")
    after: date | None = None
    if deadline_after:
        try:
            after = date.fromisoformat(deadline_after)
        except ValueError as exc:
            raise WorkbenchError(
                f"deadline-after must be an ISO date, got {deadline_after!r}"
            ) from exc

    selected: list[dict[str, Any]] = []
    query_value = query.casefold().strip()
    tag_value = tag.casefold().strip()
    source_value = source.casefold().strip()
    lifecycle_value = lifecycle.casefold().strip()
    for raw_item in items:
        item = project_safe_item(raw_item)
        if query_value and query_value not in _match_text(item):
            continue
        if tag_value and tag_value not in {
            value.casefold() for value in _list(item.get("tags"))
        }:
            continue
        if source_value and _text(item.get("source")).casefold() != source_value:
            continue
        if (
            lifecycle_value
            and _text(item.get("lifecycle")).casefold() != lifecycle_value
        ):
            continue
        if after:
            deadline_text = _text(item.get("deadline"))
            if not deadline_text or date.fromisoformat(deadline_text[:10]) < after:
                continue
        selected.append(item)
    selected.sort(key=_deadline_sort_key)
    return selected[:limit]


def selection_hash(items: Iterable[Mapping[str, Any]]) -> str:
    """Hash the selected safe rows, independent of timestamp and input order."""

    rows = sorted(
        (dict(item) for item in items),
        key=lambda item: _text(item.get("id")),
    )
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_workbench(
    items: Iterable[Mapping[str, Any]],
    *,
    input_label: str,
    query: str = "",
    tag: str = "",
    source: str = "",
    deadline_after: str = "",
    lifecycle: str = "",
    limit: int = 200,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected = select_items(
        items,
        query=query,
        tag=tag,
        source=source,
        deadline_after=deadline_after,
        lifecycle=lifecycle,
        limit=limit,
    )
    urls = sorted(
        {
            _text(item.get("source_url"))
            for item in selected
            if _text(item.get("source_url"))
        }
    )
    payload: dict[str, Any] = {
        "schema_version": WORKBENCH_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "input": {"label": input_label, "format": "application/x-ndjson"},
        "filters": {
            "query": query or None,
            "tag": tag or None,
            "source": source or None,
            "deadline_after": deadline_after or None,
            "lifecycle": lifecycle or None,
            "limit": limit,
        },
        "selection": {
            "count": len(selected),
            "ids": [str(item["id"]) for item in selected],
            "hash": selection_hash(selected),
        },
        "source_urls": urls,
        "items": selected,
    }
    return payload, selected


def csv_text(items: Iterable[Mapping[str, Any]]) -> str:
    """Render a spreadsheet-friendly projection with no raw source payload."""

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row = dict(item)
        row["eligibility"] = "; ".join(_list(row.get("eligibility")))
        row["tags"] = "; ".join(_list(row.get("tags")))
        writer.writerow(row)
    return output.getvalue()


def read_ndjson_text(text: str, *, input_label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WorkbenchError(
                f"{input_label}:{line_number}: invalid JSON: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise WorkbenchError(
                f"{input_label}:{line_number}: each row must be an object"
            )
        rows.append(value)
    return rows


def read_ndjson_path(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkbenchError(f"cannot read {path}: {exc}") from exc
    return read_ndjson_text(text, input_label=str(path))


def read_ndjson_url(url: str, *, timeout: float = 60.0) -> list[dict[str, Any]]:
    try:
        import httpx

        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            text = response.text
    except (
        Exception
    ) as exc:  # pragma: no cover - network error text is environment-specific
        raise WorkbenchError(f"cannot fetch {url}: {exc}") from exc
    return read_ndjson_text(text, input_label=url)


def write_workbench(
    output_dir: Path,
    payload: Mapping[str, Any],
    items: Iterable[Mapping[str, Any]],
    *,
    force: bool = False,
) -> tuple[Path, Path, Path]:
    """Write JSON, CSV, and a short handoff README atomically."""

    paths = (
        output_dir / "workbench.json",
        output_dir / "opportunities.csv",
        output_dir / "README.md",
    )
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        names = ", ".join(str(path) for path in existing)
        raise WorkbenchError(f"output already exists: {names}; pass --force to replace")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(items)
    count = len(rows)
    selection = _mapping(payload.get("selection"))
    selection_hash_value = _text(selection.get("hash"))
    readme = "\n".join(
        (
            "# QAZ.FUND: рабочий набор",
            "",
            f"Собрано записей: **{count}**.",
            f"Хеш выборки: `{selection_hash_value}`.",
            "",
            "Файлы содержат только публичные нормализованные поля. Исходные "
            "тексты, служебные ответы адаптеров, ключи и пользовательские данные "
            "в экспорт не попадают.",
            "",
            "Перед публикацией или подачей заявки проверьте условия на официальной "
            "странице источника.",
            "",
            "## Источники",
            "",
            *(
                f"- [{url}]({url})"
                for url in payload.get("source_urls", [])
                if _text(url)
            ),
            "",
        )
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    contents = (rendered, csv_text(rows), readme)
    for path, content in zip(paths, contents):
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8", newline="")
        temporary.replace(path)
    return paths


__all__ = [
    "CSV_FIELDS",
    "DEFAULT_INPUT_URL",
    "WORKBENCH_FIELDS",
    "WORKBENCH_SCHEMA_VERSION",
    "WorkbenchError",
    "build_workbench",
    "csv_text",
    "project_safe_item",
    "read_ndjson_path",
    "read_ndjson_text",
    "read_ndjson_url",
    "select_items",
    "selection_hash",
    "write_workbench",
]
