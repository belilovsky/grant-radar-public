"""Repository factory: choose repository backend by env/url.

Usage:
    repo = make_repository()  # picks backend from GRANT_RADAR_DB_URL env
    repo = make_repository("sqlite:///./data/grants.db")
    repo = make_repository("memory")

Keeps PipelineRunner / DedupProcessor backend-agnostic.
"""

from __future__ import annotations

from .persistence import InMemoryRepository, Repository
from .runtime_config import resolve_database_url


def _load_sql_repository(url: str, echo: bool = False) -> Repository:
    # Local import: SQLAlchemy is optional for in-memory tests.
    from .db import SqlRepository  # type: ignore

    return SqlRepository(url=url, echo=echo)  # type: ignore[return-value]


def make_repository(url: str | None = None, *, echo: bool = False) -> Repository:
    """Create a repository instance based on `url` or env variable.

    Resolution order:
      1. Explicit `url` argument.
      2. Environment variable `GRANT_RADAR_DB_URL`.
      3. Default: in-memory repository (suitable for tests/dev).

    Special values:
      * "memory" / ":memory:" / "" -> InMemoryRepository
      * any sqlite/postgres/mysql URL -> SqlRepository (SQLAlchemy)
    """
    resolved = resolve_database_url(url)

    if resolved in ("", "memory", ":memory:"):
        return InMemoryRepository()

    return _load_sql_repository(resolved, echo=echo)


__all__ = ["make_repository"]
