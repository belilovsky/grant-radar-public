"""SQLAlchemy-backed repository for ingested opportunity records.

Provides `SqlRepository` implementing the `Repository` Protocol from
`core.persistence`. Uses SQLAlchemy 2.x style. Defaults to SQLite (file or
`:memory:`) for easy local/test setup; production can pass a Postgres URL.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Optional, cast

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .history import changed_fields, history_entry, public_snapshot, snapshot_hash
from .localization import preserve_localized_raw
from .persistence import compute_fingerprint


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OpportunityRow(Base):
    __tablename__ = "opportunities"

    id = Column(String(255), primary_key=True)
    dedup_key = Column(String(255), nullable=False, unique=True)
    source = Column(String(64), nullable=False, index=True)
    source_url = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    funder = Column(String(256), nullable=True)
    amount_min = Column(Numeric(18, 2), nullable=True)
    amount_max = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(8), nullable=False, default="USD")
    deadline = Column(Date, nullable=True)
    score = Column(Float, nullable=True)
    discovered_at = Column(DateTime, default=_utcnow, nullable=False)
    first_seen_at = Column(DateTime, default=_utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    content_hash = Column(String(71), nullable=True)
    publication_state = Column(
        String(32),
        nullable=False,
        default="published",
        server_default="published",
        index=True,
    )
    raw = Column(JSON, nullable=True)

    @property
    def fingerprint(self) -> str:
        return str(self.dedup_key)

    @property
    def external_id(self) -> str:
        return str(self.id)

    @property
    def url(self) -> str:
        return str(self.source_url)

    @property
    def payload(self) -> str:
        return json.dumps(self.raw or {}, default=str, ensure_ascii=False)


class OpportunityVersionRow(Base):
    """Public change snapshots for an opportunity's source-grounded fields."""

    __tablename__ = "opportunity_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False)
    observed_at = Column(DateTime, nullable=False)
    content_hash = Column(String(80), nullable=False)
    changed_fields = Column(JSON, nullable=False)
    fields = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class OpportunityObservationRow(Base):
    """Immutable semantic snapshot captured when a record first appears or changes."""

    __tablename__ = "opportunity_observations"
    __table_args__ = (
        UniqueConstraint(
            "opportunity_id",
            "content_hash",
            name="uq_opportunity_observations_item_hash",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(
        String(255),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dedup_key = Column(String(255), nullable=False)
    source = Column(String(64), nullable=False, index=True)
    observed_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    change_type = Column(String(24), nullable=False, index=True)
    content_hash = Column(String(71), nullable=False)
    changed_fields = Column(JSON, nullable=False, default=list)
    snapshot = Column(JSON, nullable=False)


def _get(record: Any, key: str) -> Optional[Any]:
    if isinstance(record, dict):
        return record.get(key)
    return getattr(record, key, None)


def _value_scalar(value: Any) -> Any:
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value


def _serialize(record: Any) -> str:
    if isinstance(record, dict):
        try:
            return json.dumps(record, default=str, ensure_ascii=False)
        except Exception:
            return json.dumps(
                {k: str(v) for k, v in record.items()}, ensure_ascii=False
            )
    if is_dataclass(record):
        return json.dumps(
            asdict(record),  # type: ignore[call-overload]
            default=str,
            ensure_ascii=False,
        )
    # pydantic v2 first
    dump = getattr(record, "model_dump", None)
    if callable(dump):
        try:
            return json.dumps(dump(mode="json"), default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps({"repr": repr(record)}, ensure_ascii=False)
    # generic fallback
    return json.dumps({"repr": repr(record)}, ensure_ascii=False)


def _json_payload(record: Any) -> dict[str, Any]:
    dump = getattr(record, "model_dump", None)
    record_raw = getattr(record, "raw", None)
    if callable(dump) and isinstance(record_raw, dict):
        return {
            "type": _value_scalar(_get(record, "type") or "grant"),
            "eligibility": _get(record, "eligibility") or [],
            "tags": _get(record, "tags") or [],
            "languages": _get(record, "languages") or [],
            "opportunity_status": _get(record, "opportunity_status"),
            "lifecycle": _get(record, "lifecycle"),
            "raw": record_raw,
        }
    try:
        return json.loads(_serialize(record))
    except Exception:
        return {"repr": repr(record)}


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _as_date(value: Any) -> date | None:
    return value if isinstance(value, date) else None


def _semantic_snapshot(row: OpportunityRow) -> dict[str, Any]:
    """Return the stable, public-interest fields used for change detection."""

    stored_raw = cast(dict[str, Any] | None, row.raw) or {}
    nested_raw = stored_raw.get("raw")
    source_raw = nested_raw if isinstance(nested_raw, dict) else stored_raw

    def raw_value(key: str) -> Any:
        value = stored_raw.get(key)
        if value not in (None, "", [], {}):
            return value
        return source_raw.get(key)

    def decimal_value(value: Any) -> str | None:
        if value is None:
            return None
        try:
            normalized = Decimal(str(value)).normalize()
        except Exception:
            return str(value)
        return format(normalized, "f")

    return {
        "source": str(row.source or ""),
        "source_url": str(row.source_url or ""),
        "title": str(row.title or ""),
        "summary": str(row.summary or ""),
        "funder": str(row.funder or ""),
        "amount_min": decimal_value(row.amount_min),
        "amount_max": decimal_value(row.amount_max),
        "amount_raw": raw_value("amount_raw"),
        "currency": str(row.currency or ""),
        "deadline": row.deadline.isoformat() if row.deadline is not None else None,
        "deadline_policy": raw_value("deadline_policy"),
        "type": raw_value("type"),
        "eligibility": raw_value("eligibility"),
        "eligibility_summary": raw_value("eligibility_summary"),
        "tags": raw_value("tags"),
        "languages": raw_value("languages"),
        "application_url": (
            raw_value("application_url")
            or raw_value("apply_url")
            or raw_value("submission_url")
        ),
        "opportunity_status": (
            raw_value("opportunity_status")
            or raw_value("lifecycle")
            or raw_value("status")
        ),
        "i18n": raw_value("i18n"),
    }


def _snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _changed_fields(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    return sorted(
        key
        for key in set(previous).union(current)
        if previous.get(key) != current.get(key)
    )


def get_engine(url: str, *, echo: bool = False):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=echo, future=True, connect_args=connect_args)


class SqlRepository:
    """SQLAlchemy-backed repository keyed by fingerprint."""

    def __init__(self, url: str = "sqlite:///:memory:", echo: bool = False):
        self.url = url
        self.engine = get_engine(url, echo=echo)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(
            bind=self.engine, expire_on_commit=False, future=True
        )
        self._lock = threading.Lock()

    def _row_from_record(self, record: Any) -> OpportunityRow:
        fp = compute_fingerprint(record)
        source_url = str(_get(record, "source_url") or _get(record, "url") or fp)
        score_value = _get(record, "score")
        observed_at = _utcnow()
        row = OpportunityRow(
            id=fp[:255],
            dedup_key=fp[:255],
            source=str(_get(record, "source") or "unknown"),
            source_url=source_url[:1024],
            title=str(_get(record, "title") or "")[:512],
            summary=str(_get(record, "summary") or _get(record, "description") or "")
            or None,
            funder=str(_get(record, "funder") or "") or None,
            amount_min=_as_decimal(_get(record, "amount_min")),
            amount_max=_as_decimal(_get(record, "amount_max")),
            currency=str(_get(record, "currency") or "USD")[:8],
            deadline=_as_date(_get(record, "deadline")),
            score=float(score_value) if score_value is not None else None,
            discovered_at=observed_at,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            publication_state="published",
            raw=_json_payload(record),
        )
        setattr(row, "content_hash", _snapshot_hash(_semantic_snapshot(row)))
        return row

    @staticmethod
    def _observation(
        row: OpportunityRow,
        *,
        change_type: str,
        changed_fields: list[str],
        observed_at: datetime,
    ) -> OpportunityObservationRow:
        snapshot = _semantic_snapshot(row)
        content_hash = _snapshot_hash(snapshot)
        return OpportunityObservationRow(
            opportunity_id=str(row.id),
            dedup_key=str(row.dedup_key),
            source=str(row.source),
            observed_at=observed_at,
            change_type=change_type,
            content_hash=content_hash,
            changed_fields=changed_fields,
            snapshot=snapshot,
        )

    def exists(self, fingerprint: str) -> bool:
        with self._Session() as s:
            return s.get(OpportunityRow, fingerprint[:255]) is not None

    def upsert(self, record: Any) -> bool:
        new_row = self._row_from_record(record)
        with self._lock, self._Session() as s:
            existing = s.get(OpportunityRow, new_row.id)
            if existing is None:
                s.add(new_row)
                s.flush()
                new_id = cast(str, new_row.id)
                observed_at = cast(datetime | None, new_row.discovered_at) or _utcnow()
                self._append_history(
                    s,
                    opportunity_id=new_id,
                    observed_at=observed_at,
                    snapshot=public_snapshot(record),
                    changed=["initial"],
                )
                s.add(
                    self._observation(
                        new_row,
                        change_type="created",
                        changed_fields=sorted(_semantic_snapshot(new_row)),
                        observed_at=observed_at,
                    )
                )
                s.commit()
                return True
            previous_snapshot = public_snapshot(existing)
            previous_observation_snapshot = _semantic_snapshot(existing)
            next_snapshot = public_snapshot(record)
            now = _utcnow()
            existing.title = new_row.title or existing.title
            existing.source_url = new_row.source_url or existing.source_url
            existing.summary = new_row.summary or existing.summary
            existing.funder = new_row.funder or existing.funder
            existing.amount_min = (
                new_row.amount_min
                if new_row.amount_min is not None
                else existing.amount_min
            )
            existing.amount_max = (
                new_row.amount_max
                if new_row.amount_max is not None
                else existing.amount_max
            )
            existing.currency = new_row.currency or existing.currency
            existing.deadline = new_row.deadline or existing.deadline
            existing.score = (
                new_row.score if new_row.score is not None else existing.score
            )
            setattr(existing, "discovered_at", now)
            setattr(existing, "last_seen_at", now)
            # A fresh successful parser observation is the only automatic path
            # from a reconciled archive back into the public catalogue.
            setattr(existing, "publication_state", "published")
            if existing.first_seen_at is None:
                setattr(existing, "first_seen_at", now)
            existing_raw = cast(dict[str, Any] | None, existing.raw)
            new_raw = cast(dict[str, Any] | None, new_row.raw)
            setattr(
                existing,
                "raw",
                preserve_localized_raw(existing_raw, new_raw),
            )
            current_observation_snapshot = _semantic_snapshot(existing)
            current_hash = _snapshot_hash(current_observation_snapshot)
            observation_changed = _changed_fields(
                previous_observation_snapshot, current_observation_snapshot
            )
            baseline_needed = not existing.content_hash
            setattr(existing, "content_hash", current_hash)
            if observation_changed or baseline_needed:
                observation_exists = s.scalar(
                    select(OpportunityObservationRow.id).where(
                        OpportunityObservationRow.opportunity_id == existing.id,
                        OpportunityObservationRow.content_hash == current_hash,
                    )
                )
                if observation_exists is None:
                    s.add(
                        self._observation(
                            existing,
                            change_type=(
                                "changed" if observation_changed else "baseline"
                            ),
                            changed_fields=observation_changed,
                            observed_at=now,
                        )
                    )
            if snapshot_hash(previous_snapshot) != snapshot_hash(next_snapshot):
                latest = s.scalar(
                    select(OpportunityVersionRow)
                    .where(OpportunityVersionRow.opportunity_id == new_row.id)
                    .order_by(OpportunityVersionRow.version.desc())
                )
                previous_fields = (
                    cast(dict[str, Any] | None, latest.fields)
                    if latest is not None
                    else previous_snapshot
                )
                previous_fields = previous_fields or previous_snapshot
                next_version = int(latest.version) + 1 if latest is not None else 1
                self._append_history(
                    s,
                    opportunity_id=cast(str, new_row.id),
                    observed_at=now,
                    snapshot=next_snapshot,
                    changed=changed_fields(previous_fields, next_snapshot),
                    version=next_version,
                )
            s.commit()
            return False

    def all(self) -> Iterable[OpportunityRow]:
        with self._Session() as s:
            return list(s.scalars(select(OpportunityRow)).all())

    def size(self) -> int:
        with self._Session() as s:
            return int(s.scalar(select(func.count()).select_from(OpportunityRow)) or 0)

    def observations_since(
        self,
        since: datetime,
        *,
        limit: int = 500,
        include_baselines: bool = False,
    ) -> list[OpportunityObservationRow]:
        with self._Session() as s:
            query = (
                select(OpportunityObservationRow)
                .where(OpportunityObservationRow.observed_at >= since)
                .order_by(
                    OpportunityObservationRow.observed_at.desc(),
                    OpportunityObservationRow.id.desc(),
                )
                .limit(max(1, min(limit, 5000)))
            )
            if not include_baselines:
                query = query.where(OpportunityObservationRow.change_type != "baseline")
            return list(s.scalars(query).all())

    def clear(self) -> None:
        with self._Session() as s:
            s.execute(delete(OpportunityVersionRow))
            s.query(OpportunityObservationRow).delete()
            s.query(OpportunityRow).delete()
            s.commit()

    @staticmethod
    def _append_history(
        session: Any,
        *,
        opportunity_id: str,
        observed_at: datetime,
        snapshot: dict[str, Any],
        changed: list[str],
        version: int = 1,
    ) -> None:
        entry = history_entry(
            version=version,
            observed_at=observed_at,
            snapshot=snapshot,
            changed=changed,
        )
        session.add(
            OpportunityVersionRow(
                opportunity_id=opportunity_id,
                version=entry["version"],
                observed_at=observed_at,
                content_hash=entry["content_hash"],
                changed_fields=entry["changed_fields"],
                fields=entry["fields"],
            )
        )

    def history_for(self, fingerprint: str, *, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 200))
        with self._Session() as s:
            rows = list(
                s.scalars(
                    select(OpportunityVersionRow)
                    .where(OpportunityVersionRow.opportunity_id == fingerprint[:255])
                    .order_by(OpportunityVersionRow.version.desc())
                    .limit(bounded_limit)
                ).all()
            )
        rows.reverse()
        return [
            {
                "version": row.version,
                "observed_at": row.observed_at.isoformat(),
                "content_hash": row.content_hash,
                "changed_fields": list(row.changed_fields or []),
                "fields": dict(row.fields or {}),
            }
            for row in rows
        ]
