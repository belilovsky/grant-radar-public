"""initial schema (opportunities, sources, dedup keys)

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-20

Baseline migration. Reflects the schema produced by core.db.Base.metadata
as of the introduction of the SQLAlchemy persistence layer.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("funder", sa.String(length=256), nullable=True),
        sa.Column("amount_min", sa.Numeric(18, 2), nullable=True),
        sa.Column("amount_max", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "currency", sa.String(length=8), nullable=False, server_default="USD"
        ),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("raw", sa.JSON(), nullable=True),
    )

    op.create_table(
        "dedup_keys",
        sa.Column("key", sa.String(length=255), primary_key=True),
        sa.Column("opportunity_id", sa.String(length=255), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("dedup_keys")
    op.drop_table("opportunities")
