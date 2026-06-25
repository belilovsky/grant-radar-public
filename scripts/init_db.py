#!/usr/bin/env python3
"""Initialize the grant-radar repository schema.

Usage:
    python -m scripts.init_db                 # uses GRANT_RADAR_DB_URL
    python -m scripts.init_db --url sqlite:///./data/grants.db
    python -m scripts.init_db --reset          # drop + recreate schema
    python -m scripts.init_db --check          # only verify connectivity / row count

Exits with code 0 on success, 1 on configuration / connection error,
2 if SQLAlchemy is not installed (the in-memory backend has no schema to init).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("grant_radar.init_db")


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize grant-radar repository schema."
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Database URL. Falls back to GRANT_RADAR_DB_URL env variable.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables before recreating them. DESTRUCTIVE.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify connectivity and report current row count without creating tables.",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Echo SQL statements (debugging).",
    )
    return parser.parse_args(argv)


def _resolve_url(cli_url: Optional[str]) -> str:
    if cli_url:
        return cli_url
    env_url = (
        os.environ.get("GRANT_RADAR_DB_URL") or os.environ.get("DATABASE_URL") or ""
    ).strip()
    if env_url and env_url not in ("memory", ":memory:"):
        return env_url
    raise SystemExit(
        "GRANT_RADAR_DB_URL is not set or points to an in-memory backend; "
        "pass --url sqlite:///./data/grants.db or set the env variable."
    )


def main(argv: Optional[list[str]] = None) -> int:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
        )
    logger.setLevel(logging.INFO)
    args = _parse_args(argv)
    url = _resolve_url(args.url)

    try:
        from sqlalchemy import create_engine

        from core.db import Base, OpportunityRow, SqlRepository
    except ImportError as exc:  # pragma: no cover - environmental
        logger.error("SQLAlchemy is not available: %s", exc)
        return 2

    if args.check:
        repo = SqlRepository(url=url, echo=args.echo)
        size = repo.size()
        logger.info(
            "connected url=%s rows=%d table=%s", url, size, OpportunityRow.__tablename__
        )
        return 0

    engine = create_engine(url, echo=args.echo, future=True)

    if args.reset:
        logger.warning("dropping existing tables on %s", url)
        Base.metadata.drop_all(engine)

    logger.info("creating tables on %s", url)
    Base.metadata.create_all(engine)

    repo = SqlRepository(url=url, echo=args.echo)
    logger.info("schema ready url=%s rows=%d", url, repo.size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
