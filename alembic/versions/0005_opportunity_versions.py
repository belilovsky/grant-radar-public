"""Add public, source-grounded opportunity version snapshots.

The backfill creates one explicit ``initial`` snapshot for existing records.
Future parser refreshes append a version only when a normalized public field
changes, keeping routine observations out of the history feed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from core.history import public_snapshot, snapshot_hash

revision: str = "0005_opportunity_versions"
down_revision: Union[str, None] = "0004_runs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    op.create_table(
        "opportunity_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("opportunity_id", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=80), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_opportunity_versions_opportunity_id",
        "opportunity_versions",
        ["opportunity_id"],
    )
    op.create_index(
        "uq_opportunity_versions_opportunity_version",
        "opportunity_versions",
        ["opportunity_id", "version"],
        unique=True,
    )

    bind = op.get_bind()
    opportunities = sa.table(
        "opportunities",
        sa.column("id", sa.String()),
        sa.column("source", sa.String()),
        sa.column("source_url", sa.String()),
        sa.column("title", sa.String()),
        sa.column("summary", sa.Text()),
        sa.column("funder", sa.String()),
        sa.column("amount_min", sa.Numeric()),
        sa.column("amount_max", sa.Numeric()),
        sa.column("currency", sa.String()),
        sa.column("deadline", sa.Date()),
        sa.column("discovered_at", sa.DateTime()),
        sa.column("raw", sa.JSON()),
    )
    versions = sa.table(
        "opportunity_versions",
        sa.column("opportunity_id", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("observed_at", sa.DateTime()),
        sa.column("content_hash", sa.String()),
        sa.column("changed_fields", sa.JSON()),
        sa.column("fields", sa.JSON()),
    )
    rows = list(bind.execute(sa.select(opportunities)).mappings())
    if not rows:
        return
    values = []
    for row in rows:
        row_dict = dict(row)
        snapshot = public_snapshot(row_dict)
        values.append(
            {
                "opportunity_id": str(row_dict["id"]),
                "version": 1,
                "observed_at": row_dict.get("discovered_at") or _now(),
                "content_hash": snapshot_hash(snapshot),
                "changed_fields": ["initial"],
                "fields": snapshot,
            }
        )
    bind.execute(versions.insert(), values)


def downgrade() -> None:
    op.drop_index(
        "uq_opportunity_versions_opportunity_version",
        table_name="opportunity_versions",
    )
    op.drop_index(
        "ix_opportunity_versions_opportunity_id",
        table_name="opportunity_versions",
    )
    op.drop_table("opportunity_versions")
