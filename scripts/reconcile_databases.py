"""Lossless, publication-safe reconciliation of two QAZ.FUND databases.

The target is the canonical database.  Source-only opportunities are retained
as ``archived_unverified`` and therefore cannot appear publicly.  A common
record replaces the target value only when it is newer and belongs to a source
with a successful run at or after that observation.  Version and observation
history is merged by content hash; ingestion runs are merged by a stable
natural key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import MetaData, Table, create_engine, delete, insert, select, update
from sqlalchemy.engine import Connection, Engine, RowMapping

SUCCESS_STATES = frozenset({"success", "succeeded", "ok", "completed"})


def _plain(row: RowMapping) -> dict[str, Any]:
    return {str(key): value for key, value in row.items()}


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stable_hash(rows: Iterable[Mapping[str, Any]], keys: tuple[str, ...]) -> str:
    normalized = [
        {key: row.get(key) for key in keys}
        for row in sorted(
            rows, key=lambda item: tuple(str(item.get(key)) for key in keys)
        )
    ]
    payload = json.dumps(normalized, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reflect(engine: Engine) -> dict[str, Table]:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    required = {"opportunities", "opportunity_versions", "opportunity_observations"}
    missing = sorted(required - set(metadata.tables))
    if missing:
        raise RuntimeError(f"database is missing required tables: {', '.join(missing)}")
    return dict(metadata.tables)


def _rows(connection: Connection, table: Table) -> list[dict[str, Any]]:
    return [_plain(row) for row in connection.execute(select(table)).mappings()]


def _successful_sources(
    connection: Connection, runs: Table | None
) -> dict[str, datetime]:
    if runs is None:
        return {}
    successful: dict[str, datetime] = {}
    for row in connection.execute(select(runs)).mappings():
        if str(row.get("status") or "").lower() not in SUCCESS_STATES:
            continue
        completed_at = _timestamp(row.get("finished_at") or row.get("started_at"))
        source = str(row.get("source") or "")
        if source and completed_at > successful.get(
            source, datetime.min.replace(tzinfo=timezone.utc)
        ):
            successful[source] = completed_at
    return successful


def _copy_values(source: Mapping[str, Any], target: Table) -> dict[str, Any]:
    return {
        column.name: source[column.name]
        for column in target.columns
        if column.name in source
    }


def _merge_versions(
    connection: Connection,
    target: Table,
    source_rows: list[dict[str, Any]],
    *,
    opportunity_id: str,
    source_opportunity_id: str,
) -> int:
    target_rows = [
        _plain(row)
        for row in connection.execute(
            select(target).where(target.c.opportunity_id == opportunity_id)
        ).mappings()
    ]
    candidates = target_rows + [
        row
        for row in source_rows
        if str(row.get("opportunity_id")) == source_opportunity_id
    ]
    by_hash: dict[str, dict[str, Any]] = {}
    for row in sorted(candidates, key=lambda item: _timestamp(item.get("observed_at"))):
        by_hash.setdefault(str(row.get("content_hash") or ""), row)
    ordered = sorted(
        by_hash.values(), key=lambda item: _timestamp(item.get("observed_at"))
    )
    if len(ordered) == len(target_rows) and {
        str(row.get("content_hash")) for row in ordered
    } == {str(row.get("content_hash")) for row in target_rows}:
        return 0
    connection.execute(delete(target).where(target.c.opportunity_id == opportunity_id))
    for version, row in enumerate(ordered, start=1):
        values = _copy_values(row, target)
        values.pop("id", None)
        values["opportunity_id"] = opportunity_id
        values["version"] = version
        connection.execute(insert(target).values(**values))
    return max(0, len(ordered) - len(target_rows))


def _merge_observations(
    connection: Connection,
    target: Table,
    source_rows: list[dict[str, Any]],
    *,
    opportunity_id: str,
    source_opportunity_id: str,
) -> int:
    existing = {
        str(value)
        for value in connection.execute(
            select(target.c.content_hash).where(
                target.c.opportunity_id == opportunity_id
            )
        ).scalars()
    }
    inserted = 0
    for row in source_rows:
        if str(row.get("opportunity_id")) != source_opportunity_id:
            continue
        content_hash = str(row.get("content_hash") or "")
        if content_hash in existing:
            continue
        values = _copy_values(row, target)
        values.pop("id", None)
        values["opportunity_id"] = opportunity_id
        connection.execute(insert(target).values(**values))
        existing.add(content_hash)
        inserted += 1
    return inserted


def _merge_runs(
    connection: Connection,
    target: Table | None,
    source_rows: list[dict[str, Any]],
) -> int:
    if target is None:
        return 0
    key_fields = (
        "source",
        "started_at",
        "finished_at",
        "status",
        "items_seen",
        "items_new",
        "items_dup",
        "error",
    )
    existing = {
        tuple(str(row.get(key)) for key in key_fields)
        for row in connection.execute(select(target)).mappings()
    }
    inserted = 0
    for row in source_rows:
        key = tuple(str(row.get(field)) for field in key_fields)
        if key in existing:
            continue
        values = _copy_values(row, target)
        values.pop("id", None)
        connection.execute(insert(target).values(**values))
        existing.add(key)
        inserted += 1
    return inserted


def reconcile(
    *,
    source_url: str,
    target_url: str,
    apply: bool = False,
    expected_source_count: int | None = None,
    expected_target_count: int | None = None,
) -> dict[str, Any]:
    """Reconcile source into target and return an auditable report."""

    source_engine = create_engine(source_url, future=True)
    target_engine = create_engine(target_url, future=True)
    source_tables = _reflect(source_engine)
    target_tables = _reflect(target_engine)
    target_opportunities = target_tables["opportunities"]
    if "publication_state" not in target_opportunities.c:
        raise RuntimeError(
            "target lacks opportunities.publication_state; run alembic upgrade head"
        )

    source_connection = source_engine.connect()
    target_connection = target_engine.connect()
    transaction = target_connection.begin()
    try:
        source_items = _rows(source_connection, source_tables["opportunities"])
        target_items_before = _rows(target_connection, target_opportunities)
        if (
            expected_source_count is not None
            and len(source_items) != expected_source_count
        ):
            raise RuntimeError(
                f"source count mismatch: {len(source_items)} != {expected_source_count}"
            )
        if (
            expected_target_count is not None
            and len(target_items_before) != expected_target_count
        ):
            raise RuntimeError(
                f"target count mismatch: {len(target_items_before)} != {expected_target_count}"
            )

        source_by_key = {str(row["dedup_key"]): row for row in source_items}
        target_by_key = {str(row["dedup_key"]): row for row in target_items_before}
        target_ids = {
            str(row["id"]): str(row["dedup_key"]) for row in target_items_before
        }
        successful = _successful_sources(source_connection, source_tables.get("runs"))
        source_versions = _rows(
            source_connection, source_tables["opportunity_versions"]
        )
        source_observations = _rows(
            source_connection, source_tables["opportunity_observations"]
        )
        source_runs = (
            _rows(source_connection, source_tables["runs"])
            if "runs" in source_tables
            else []
        )

        stats = {
            "source_only_archived": 0,
            "common_source_selected": 0,
            "common_target_retained": 0,
            "versions_added": 0,
            "observations_added": 0,
            "runs_added": 0,
        }
        touched_ids: set[str] = set()
        for dedup_key, source_row in source_by_key.items():
            source_id = str(source_row["id"])
            target_row = target_by_key.get(dedup_key)
            if target_row is None:
                conflicting_key = target_ids.get(source_id)
                if conflicting_key is not None and conflicting_key != dedup_key:
                    raise RuntimeError(
                        f"id collision for {source_id}: {conflicting_key} vs {dedup_key}"
                    )
                values = _copy_values(source_row, target_opportunities)
                values["publication_state"] = "archived_unverified"
                target_connection.execute(insert(target_opportunities).values(**values))
                stats["source_only_archived"] += 1
                opportunity_id = source_id
            else:
                opportunity_id = str(target_row["id"])
                source_confirmed_at = successful.get(
                    str(source_row.get("source") or "")
                )
                source_is_confirmed = (
                    source_confirmed_at is not None
                    and source_confirmed_at
                    >= _timestamp(source_row.get("last_seen_at"))
                )
                source_is_newer = _timestamp(
                    source_row.get("last_seen_at")
                ) > _timestamp(target_row.get("last_seen_at"))
                if source_is_confirmed and source_is_newer:
                    values = _copy_values(source_row, target_opportunities)
                    values.pop("id", None)
                    values.pop("dedup_key", None)
                    values.pop("publication_state", None)
                    values["first_seen_at"] = min(
                        _timestamp(source_row.get("first_seen_at")),
                        _timestamp(target_row.get("first_seen_at")),
                    ).replace(tzinfo=None)
                    target_connection.execute(
                        update(target_opportunities)
                        .where(target_opportunities.c.id == opportunity_id)
                        .values(**values)
                    )
                    stats["common_source_selected"] += 1
                else:
                    stats["common_target_retained"] += 1
            touched_ids.add(opportunity_id)
            stats["versions_added"] += _merge_versions(
                target_connection,
                target_tables["opportunity_versions"],
                source_versions,
                opportunity_id=opportunity_id,
                source_opportunity_id=source_id,
            )
            stats["observations_added"] += _merge_observations(
                target_connection,
                target_tables["opportunity_observations"],
                source_observations,
                opportunity_id=opportunity_id,
                source_opportunity_id=source_id,
            )

        stats["runs_added"] = _merge_runs(
            target_connection, target_tables.get("runs"), source_runs
        )
        target_items_after = _rows(target_connection, target_opportunities)
        report = {
            "mode": "apply" if apply else "dry-run",
            "source": {
                "opportunities": len(source_items),
                "hash": _stable_hash(source_items, ("dedup_key", "content_hash")),
            },
            "target_before": {
                "opportunities": len(target_items_before),
                "hash": _stable_hash(
                    target_items_before,
                    ("dedup_key", "content_hash", "publication_state"),
                ),
            },
            "target_after": {
                "opportunities": len(target_items_after),
                "published": sum(
                    row.get("publication_state") == "published"
                    for row in target_items_after
                ),
                "archived_unverified": sum(
                    row.get("publication_state") == "archived_unverified"
                    for row in target_items_after
                ),
                "hash": _stable_hash(
                    target_items_after,
                    ("dedup_key", "content_hash", "publication_state"),
                ),
            },
            "common": len(set(source_by_key) & set(target_by_key)),
            "touched": len(touched_ids),
            "stats": stats,
        }
        if apply:
            transaction.commit()
        else:
            transaction.rollback()
        return report
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        raise
    finally:
        source_connection.close()
        target_connection.close()
        source_engine.dispose()
        target_engine.dispose()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-source-count", type=int)
    parser.add_argument("--expected-target-count", type=int)
    return parser


def main() -> int:
    args = _parser().parse_args()
    report = reconcile(
        source_url=args.source_url,
        target_url=args.target_url,
        apply=args.apply,
        expected_source_count=args.expected_source_count,
        expected_target_count=args.expected_target_count,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Dry run only. Re-run with --apply after reviewing the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
