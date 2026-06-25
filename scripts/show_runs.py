"""Operator CLI: show recent pipeline runs from the `runs` table.

Usage:
    python -m scripts.show_runs                # last 20 runs across all sources
    python -m scripts.show_runs --source grants_gov --limit 5
    python -m scripts.show_runs --status error --limit 50
    python -m scripts.show_runs --since 24h    # last 24 hours

DB URL is taken from $GRANT_RADAR_DB_URL / $DATABASE_URL (or --url).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from typing import Optional

_DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_since(value: str) -> _dt.datetime:
    m = _DURATION_RE.match(value.strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(
            f"--since expects e.g. 30m, 24h, 7d (got {value!r})"
        )
    n, unit = int(m.group(1)), m.group(2)
    delta = _dt.timedelta(seconds=n * _UNIT_SECONDS[unit])
    return _dt.datetime.now(_dt.timezone.utc) - delta


def _fmt_dt(value: Optional[_dt.datetime]) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _duration(start: Optional[_dt.datetime], end: Optional[_dt.datetime]) -> str:
    if start is None:
        return "-"
    if end is None:
        end = _dt.datetime.now(_dt.timezone.utc)
        if start.tzinfo is None:
            end = end.replace(tzinfo=None)
    secs = max(0, int((end - start).total_seconds()))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m{secs % 60:02d}s"
    return f"{secs // 3600}h{(secs % 3600) // 60:02d}m"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Show recent grant-radar pipeline runs.")
    p.add_argument(
        "--url", default=None, help="DB URL (overrides $GRANT_RADAR_DB_URL)."
    )
    p.add_argument("--source", default=None, help="Filter by source name.")
    p.add_argument(
        "--status",
        default=None,
        choices=["running", "ok", "error"],
        help="Filter by run status.",
    )
    p.add_argument("--since", type=_parse_since, default=None, help="e.g. 30m, 24h, 7d")
    p.add_argument("--limit", type=int, default=20, help="Max rows (default: 20).")
    return p


def fetch_runs(url, *, source=None, status=None, since=None, limit=20):
    from sqlalchemy import MetaData, Table, create_engine, select

    engine = create_engine(url)
    md = MetaData()
    runs = Table("runs", md, autoload_with=engine)

    stmt = select(runs).order_by(runs.c.started_at.desc()).limit(limit)
    if source is not None:
        stmt = stmt.where(runs.c.source == source)
    if status is not None:
        stmt = stmt.where(runs.c.status == status)
    if since is not None:
        stmt = stmt.where(runs.c.started_at >= since)

    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(stmt).mappings().all()]


def format_table(rows):
    if not rows:
        return "(no runs)"
    headers = [
        "id",
        "source",
        "status",
        "started_at",
        "duration",
        "seen",
        "new",
        "dup",
        "error",
    ]
    lines = [
        "\t".join(headers),
        "\t".join(["-" * len(h) for h in headers]),
    ]
    for r in rows:
        err_lines = (r.get("error") or "").splitlines()
        err = err_lines[0][:80] if err_lines else ""
        lines.append(
            "\t".join(
                [
                    str(r["id"]),
                    str(r["source"]),
                    str(r["status"]),
                    _fmt_dt(r.get("started_at")),
                    _duration(r.get("started_at"), r.get("finished_at")),
                    str(r.get("items_seen", 0)),
                    str(r.get("items_new", 0)),
                    str(r.get("items_dup", 0)),
                    err,
                ]
            )
        )
    return "\n".join(lines)


def main(argv=None):
    args = _build_parser().parse_args(argv)
    url = (
        args.url
        or os.environ.get("GRANT_RADAR_DB_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        print(
            "error: GRANT_RADAR_DB_URL/DATABASE_URL is not set; pass --url or export it",
            file=sys.stderr,
        )
        return 2
    rows = fetch_runs(
        url,
        source=args.source,
        status=args.status,
        since=args.since,
        limit=args.limit,
    )
    print(format_table(rows))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
