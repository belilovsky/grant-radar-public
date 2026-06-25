"""Alembic environment.

Reads database URL from GRANT_RADAR_DB_URL env var (fallback to alembic.ini).
Uses Base.metadata from core.db for autogenerate support.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve DB URL: env wins over alembic.ini.
db_url = (
    os.getenv("GRANT_RADAR_DB_URL")
    or os.getenv("DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)
if not db_url:
    raise RuntimeError(
        "GRANT_RADAR_DB_URL/DATABASE_URL is not set and sqlalchemy.url is empty in alembic.ini"
    )
config.set_main_option("sqlalchemy.url", db_url)

# Import metadata for autogenerate.
try:
    from core.db import Base  # type: ignore

    target_metadata = Base.metadata
except Exception:  # pragma: no cover - allows alembic to load without app deps
    target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
