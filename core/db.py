"""SQLAlchemy-backed repository for ingested opportunity records.

Provides `SqlRepository` implementing the `Repository` Protocol from
`core.persistence`. Uses SQLAlchemy 2.x style. Defaults to SQLite (file or
`:memory:`) for easy local/test setup; production can pass a Postgres URL.
"""

from __future__ import annotations

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
    Numeric,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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
        return OpportunityRow(
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
            raw=_json_payload(record),
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
                s.commit()
                return True
            existing.title = new_row.title or existing.title
            existing.source_url = new_row.source_url or existing.source_url
            existing.summary = new_row.summary or existing.summary
            existing.funder = new_row.funder or existing.funder
            existing.amount_min = new_row.amount_min or existing.amount_min
            existing.amount_max = new_row.amount_max or existing.amount_max
            existing.currency = new_row.currency or existing.currency
            existing.deadline = new_row.deadline or existing.deadline
            existing.score = (
                new_row.score if new_row.score is not None else existing.score
            )
            setattr(
                existing,
                "discovered_at",
                _utcnow(),
            )
            existing_raw = cast(dict[str, Any] | None, existing.raw)
            new_raw = cast(dict[str, Any] | None, new_row.raw)
            setattr(
                existing,
                "raw",
                preserve_localized_raw(existing_raw, new_raw),
            )
            s.commit()
            return False

    def all(self) -> Iterable[OpportunityRow]:
        with self._Session() as s:
            return list(s.scalars(select(OpportunityRow)).all())

    def size(self) -> int:
        with self._Session() as s:
            return len(list(s.scalars(select(OpportunityRow)).all()))

    def clear(self) -> None:
        with self._Session() as s:
            s.query(OpportunityRow).delete()
            s.commit()
