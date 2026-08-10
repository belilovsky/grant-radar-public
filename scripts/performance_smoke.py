"""Measure repeatable public-route latency without mutating QAZ.FUND."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from typing import Any

import httpx

from scripts.http_utils import join_url as _url

DEFAULT_PATHS = (
    "/?lang=ru",
    "/insights?lang=ru",
    "/api/v1/insights?lang=ru",
    "/coverage",
    "/opportunities.ndjson?lang=ru&limit=500&min_score=0.3&compact=true",
)


def _request_with_reconnect(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    retries: int = 2,
) -> httpx.Response:
    """Retry transient connection drops without hiding HTTP failures."""

    for attempt in range(retries + 1):
        try:
            return client.request(method, url)
        except (
            httpx.RemoteProtocolError,
            httpx.ReadError,
            httpx.ConnectError,
            httpx.PoolTimeout,
        ):
            if attempt >= retries:
                raise
            time.sleep(0.15 * (attempt + 1))
    raise RuntimeError("unreachable request retry state")


def run_probe(
    *,
    base_url: str,
    paths: tuple[str, ...] = DEFAULT_PATHS,
    samples: int = 5,
    timeout: float = 30.0,
    max_warm_ms: float | None = None,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    if samples < 2:
        raise ValueError("samples must be at least 2")

    client_kwargs: dict[str, Any] = {
        "follow_redirects": True,
        "timeout": timeout,
    }
    if transport is not None:
        client_kwargs["transport"] = transport

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    with httpx.Client(**client_kwargs) as client:
        for path in paths:
            durations: list[float] = []
            response: httpx.Response | None = None
            for _ in range(samples):
                started = time.perf_counter()
                response = _request_with_reconnect(client, "GET", _url(base_url, path))
                elapsed_ms = (time.perf_counter() - started) * 1000
                response.raise_for_status()
                durations.append(elapsed_ms)

            head_started = time.perf_counter()
            head = _request_with_reconnect(client, "HEAD", _url(base_url, path))
            head_ms = (time.perf_counter() - head_started) * 1000
            head.raise_for_status()
            assert response is not None

            warm_values = durations[1:]
            warm_median = statistics.median(warm_values)
            if max_warm_ms is not None and warm_median > max_warm_ms:
                failures.append(
                    f"{path}: warm median {warm_median:.1f} ms exceeds "
                    f"{max_warm_ms:.1f} ms"
                )
            results.append(
                {
                    "path": path,
                    "first_ms": round(durations[0], 1),
                    "warm_median_ms": round(warm_median, 1),
                    "warm_max_ms": round(max(warm_values), 1),
                    "head_ms": round(head_ms, 1),
                    "response_bytes": len(response.content),
                    "cache_control": response.headers.get("cache-control", ""),
                    "etag": response.headers.get("etag", ""),
                }
            )

    return {
        "status": "error" if failures else "ok",
        "base_url": base_url.rstrip("/"),
        "samples": samples,
        "results": results,
        "failures": failures,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Probe this path instead of the default set; may be repeated.",
    )
    parser.add_argument(
        "--max-warm-ms",
        type=float,
        default=None,
        help="Fail when any warm median exceeds this value.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        payload = run_probe(
            base_url=args.base_url,
            paths=tuple(args.paths or DEFAULT_PATHS),
            samples=args.samples,
            timeout=args.timeout,
            max_warm_ms=args.max_warm_ms,
        )
    except (ValueError, httpx.HTTPError) as exc:
        print(f"performance smoke failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
