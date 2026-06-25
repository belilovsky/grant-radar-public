"""Ingest pipeline: source.fetch → dedupe → score → persist."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

import structlog

from core.models import Opportunity
from core.scoring import score as score_opportunity
from sources.base import BaseSource

log = structlog.get_logger()


async def run_source(source: BaseSource, seen: set[str]) -> list[Opportunity]:
    out: list[Opportunity] = []
    async with source:
        async for opp in source.fetch():
            fp = opp.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            opp.score = score_opportunity(opp)
            out.append(opp)
    log.info("pipeline.source_done", source=source.slug, collected=len(out))
    return out


async def run_all(sources: Sequence[BaseSource]) -> list[Opportunity]:
    seen: set[str] = set()
    results = await asyncio.gather(
        *(run_source(s, seen) for s in sources),
        return_exceptions=True,
    )
    out: list[Opportunity] = []
    for r in results:
        if isinstance(r, BaseException):
            log.error("pipeline.source_failed", error=str(r))
            continue
        out.extend(r)
    out.sort(key=lambda o: o.score, reverse=True)
    return out
