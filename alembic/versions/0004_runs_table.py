"""runs table for pipeline audit log

Revision ID: 0004_runs_table
Revises: 0003_opportunities_indexes
Create Date: 2026-05-20 13:30:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_runs_table"
down_revision = "0003_opportunities_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="running"
        ),
        sa.Column("items_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_dup", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_runs_source", "runs", ["source"])
    op.create_index("ix_runs_started_at", "runs", ["started_at"])
    op.create_index("ix_runs_status", "runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_runs_status", table_name="runs")
    op.drop_index("ix_runs_started_at", table_name="runs")
    op.drop_index("ix_runs_source", table_name="runs")
    op.drop_table("runs")
