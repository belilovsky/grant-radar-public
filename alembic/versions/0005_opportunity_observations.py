"""immutable opportunity observation ledger

Revision ID: 0005_opportunity_observations
Revises: 0004_runs_table
Create Date: 2026-07-27 18:00:00.000000

This revision is retained because it is already applied to the production
database.  The public normalized history read model follows it in revision
0006.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_opportunity_observations"
down_revision = "0004_runs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "opportunities",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE opportunities "
            "SET first_seen_at = discovered_at, last_seen_at = discovered_at "
            "WHERE discovered_at IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE opportunities "
            "SET first_seen_at = CURRENT_TIMESTAMP, last_seen_at = CURRENT_TIMESTAMP "
            "WHERE first_seen_at IS NULL OR last_seen_at IS NULL"
        )
    )
    with op.batch_alter_table("opportunities") as batch:
        batch.alter_column(
            "first_seen_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        )
        batch.alter_column(
            "last_seen_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        )
    op.add_column(
        "opportunities",
        sa.Column("content_hash", sa.String(length=71), nullable=True),
    )
    op.create_index(
        "ix_opportunities_last_seen_at",
        "opportunities",
        ["last_seen_at"],
    )
    op.create_table(
        "opportunity_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "opportunity_id",
            sa.String(length=255),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("change_type", sa.String(length=24), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column(
            "changed_fields",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "opportunity_id",
            "content_hash",
            name="uq_opportunity_observations_item_hash",
        ),
    )
    op.create_index(
        "ix_opportunity_observations_opportunity_id",
        "opportunity_observations",
        ["opportunity_id"],
    )
    op.create_index(
        "ix_opportunity_observations_source",
        "opportunity_observations",
        ["source"],
    )
    op.create_index(
        "ix_opportunity_observations_observed_at",
        "opportunity_observations",
        ["observed_at"],
    )
    op.create_index(
        "ix_opportunity_observations_change_type",
        "opportunity_observations",
        ["change_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_opportunity_observations_change_type",
        table_name="opportunity_observations",
    )
    op.drop_index(
        "ix_opportunity_observations_observed_at",
        table_name="opportunity_observations",
    )
    op.drop_index(
        "ix_opportunity_observations_source",
        table_name="opportunity_observations",
    )
    op.drop_index(
        "ix_opportunity_observations_opportunity_id",
        table_name="opportunity_observations",
    )
    op.drop_table("opportunity_observations")
    op.drop_index("ix_opportunities_last_seen_at", table_name="opportunities")
    op.drop_column("opportunities", "content_hash")
    op.drop_column("opportunities", "last_seen_at")
    op.drop_column("opportunities", "first_seen_at")
