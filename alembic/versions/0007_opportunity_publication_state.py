"""Add a publication boundary for reconciled opportunity archives."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0007_opportunity_publication_state"
down_revision: Union[str, None] = "0006_opportunity_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("opportunities")}
    if "publication_state" not in columns:
        op.add_column(
            "opportunities",
            sa.Column(
                "publication_state",
                sa.String(length=32),
                nullable=False,
                server_default="published",
            ),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("opportunities")}
    if "ix_opportunities_publication_state" not in indexes:
        op.create_index(
            "ix_opportunities_publication_state",
            "opportunities",
            ["publication_state"],
        )


def downgrade() -> None:
    op.drop_index("ix_opportunities_publication_state", table_name="opportunities")
    op.drop_column("opportunities", "publication_state")
