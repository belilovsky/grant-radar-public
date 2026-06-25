"""opportunities indexes

Revision ID: 0003_opportunities_indexes
Revises: 0002_sources_table
Create Date: 2026-05-20 13:00:00.000000

"""

from __future__ import annotations

from alembic import op

revision = "0003_opportunities_indexes"
down_revision = "0002_sources_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_opportunities_source",
        "opportunities",
        ["source"],
    )
    op.create_index(
        "ix_opportunities_deadline",
        "opportunities",
        ["deadline"],
    )
    op.create_index(
        "ix_opportunities_dedup_key",
        "opportunities",
        ["dedup_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_dedup_key", table_name="opportunities")
    op.drop_index("ix_opportunities_deadline", table_name="opportunities")
    op.drop_index("ix_opportunities_source", table_name="opportunities")
