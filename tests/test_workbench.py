from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.workbench import (
    WORKBENCH_SCHEMA_VERSION,
    WorkbenchError,
    build_workbench,
    read_ndjson_text,
    selection_hash,
    write_workbench,
)


def _row(item_id: str, *, title: str, deadline: str | None = "2026-09-01") -> dict:
    return {
        "id": item_id,
        "source": "source_a",
        "source_url": f"https://example.org/{item_id}",
        "type": "grant",
        "title": title,
        "summary": "Support for Kazakhstan teams.",
        "funder": "Example Funder",
        "amount_min": 1000,
        "amount_max": 5000,
        "currency": "USD",
        "deadline": deadline,
        "eligibility": ["Kazakhstan teams"],
        "tags": ["Kazakhstan", "AI"],
        "lifecycle": "open",
        "score": 0.8,
        "evidence_state": "sourced",
        "discovered_at": "2026-08-04T00:00:00Z",
        "raw": {
            "application_url": f"https://example.org/{item_id}/apply",
            "secret_operator_note": "must never leave raw",
            "provenance": {
                "schema_version": "provenance.v1",
                "evidence_state": "sourced",
                "source_language": "en",
                "private_note": "must never leave provenance",
            },
        },
    }


def test_workbench_projects_only_safe_fields_and_filters_deterministically():
    other = _row("b", title="Other programme")
    other["tags"] = ["Kazakhstan"]
    rows = [other, _row("a", title="AI programme")]
    payload, selected = build_workbench(
        rows,
        input_label="fixture.ndjson",
        query="ai",
        tag="AI",
        deadline_after="2026-08-01",
    )

    assert payload["schema_version"] == WORKBENCH_SCHEMA_VERSION
    assert [item["id"] for item in selected] == ["a"]
    assert selected[0]["application_url"].endswith("/apply")
    assert "raw" not in selected[0]
    assert "secret_operator_note" not in json.dumps(selected, ensure_ascii=False)
    assert "private_note" not in json.dumps(selected, ensure_ascii=False)
    assert payload["selection"]["hash"].startswith("sha256:")


def test_selection_hash_does_not_depend_on_input_order():
    first = [_row("a", title="A"), _row("b", title="B")]
    second = list(reversed(first))
    _, selected_first = build_workbench(first, input_label="a")
    _, selected_second = build_workbench(second, input_label="b")

    assert selection_hash(selected_first) == selection_hash(selected_second)


def test_workbench_writes_json_csv_readme_and_refuses_accidental_overwrite(
    tmp_path: Path,
):
    payload, selected = build_workbench(
        [_row("a", title="A")], input_label="fixture.ndjson"
    )
    paths = write_workbench(tmp_path / "export", payload, selected)
    assert all(path.exists() for path in paths)
    assert "raw" not in paths[0].read_text(encoding="utf-8")
    assert "secret_operator_note" not in paths[1].read_text(encoding="utf-8")
    assert "QAZ.FUND" in paths[2].read_text(encoding="utf-8")

    with pytest.raises(WorkbenchError, match="already exists"):
        write_workbench(tmp_path / "export", payload, selected)
    write_workbench(tmp_path / "export", payload, selected, force=True)


def test_ndjson_reader_reports_line_number_and_rejects_non_objects():
    with pytest.raises(WorkbenchError, match="fixture.ndjson:2: invalid JSON"):
        read_ndjson_text('{"id": "ok"}\nnot-json\n', input_label="fixture.ndjson")

    with pytest.raises(WorkbenchError, match="each row must be an object"):
        read_ndjson_text("[]\n", input_label="fixture.ndjson")


def test_invalid_deadline_is_not_silently_exported():
    row = _row("bad", title="Bad", deadline="soon")
    with pytest.raises(WorkbenchError, match="deadline must start with an ISO date"):
        build_workbench([row], input_label="fixture.ndjson")
