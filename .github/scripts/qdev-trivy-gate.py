#!/usr/bin/env python3
"""Carrier-lane gate for the fixed CRITICAL/HIGH container scans.

The native IPOS lane runs trivy with ``exit-code: 1`` and no report file, so a
gate failure there is one opaque job status.  The carrier lane keeps the
identical severity and ``ignore-unfixed`` filters but writes machine-readable
JSON, prints every finding into the run log and fails the job when any fixed
CRITICAL/HIGH finding exists.  The gate semantics are unchanged: a finding
still fails the lane, and a missing or unreadable report also fails it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_findings(path: Path) -> list[dict]:
    payload = json.loads(path.read_text("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("report is not a JSON object")
    rows: list[dict] = []
    for result in payload.get("Results") or []:
        if not isinstance(result, dict):
            continue
        for vuln in result.get("Vulnerabilities") or []:
            rows.append(
                {
                    "target": str(result.get("Target", "unknown")),
                    "severity": str(vuln.get("Severity", "UNKNOWN")).upper(),
                    "vulnerability_id": str(vuln.get("VulnerabilityID", "UNKNOWN")),
                    "package": str(vuln.get("PkgName", "unknown")),
                    "installed": str(vuln.get("InstalledVersion", "unknown")),
                    "fixed": str(vuln.get("FixedVersion") or "not-fixed"),
                    "title": " ".join(str(vuln.get("Title") or "").split()),
                }
            )
    return rows


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: qdev-trivy-gate.py REPORT.json [REPORT.json ...]", file=sys.stderr)
        return 2

    total = 0
    for raw in argv[1:]:
        path = Path(raw)
        if not path.is_file() or path.stat().st_size == 0:
            print(f"scan_report=missing_or_empty path={path}")
            total += 1
            continue
        try:
            rows = load_findings(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"scan_report=unreadable path={path} error={error}")
            total += 1
            continue
        rows.sort(
            key=lambda row: (
                row["severity"] != "CRITICAL",
                row["severity"],
                row["package"],
                row["vulnerability_id"],
            )
        )
        print(f"scan_report={path} fixed_critical_high={len(rows)}")
        for row in rows:
            print(
                f"finding severity={row['severity']} id={row['vulnerability_id']} "
                f"package={row['package']} installed={row['installed']} "
                f"fixed={row['fixed']} target={row['target']} title={row['title']}"
            )
        total += len(rows)

    print(f"trivy_fixed_critical_high_total={total}")
    if total:
        print(
            "gate_result=blocked: fixed CRITICAL/HIGH vulnerabilities exist "
            "in the candidate images"
        )
        return 1
    print("gate_result=pass: no fixed CRITICAL/HIGH vulnerabilities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
