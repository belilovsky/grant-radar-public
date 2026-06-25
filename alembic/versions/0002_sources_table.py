"""add sources table

Revision ID: 0002_sources_table
Revises: 0001_initial
Create Date: 2026-05-20

Introduces the `sources` registry: per-source metadata (slug, kind, last_run_at,
last_status, error_count). Used by SourceScheduler to plan fetches and by the
dashboard to surface health.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_sources_table"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_sources_kind", "sources", ["kind"], unique=False)
    op.create_index("ix_sources_enabled", "sources", ["enabled"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sources_enabled", table_name="sources")
    op.drop_index("ix_sources_kind", table_name="sources")
    op.drop_table("sources")
