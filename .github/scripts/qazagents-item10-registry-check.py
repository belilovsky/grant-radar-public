#!/usr/bin/env python3
"""Assert the item-10 registration invariants of a belilovsky/qazagents checkout.

Run from the root of the verified private checkout. Prints a JSON summary and
exits non-zero when any invariant fails. Reads only registry and skill-release
metadata; it never prints skill content, so it is safe to run on the carrier.
"""

import json
import sys


def main() -> int:
    problems = []

    with open("registry/codex-skills.json", encoding="utf-8") as handle:
        registry = json.load(handle)
    with open("registry/runtime-allowlist.v1.json", encoding="utf-8") as handle:
        allowlist = json.load(handle)

    registry_ids = [entry.get("id") for entry in registry["skills"]]
    binding_ids = [entry.get("logical_id") for entry in allowlist["bindings"]]

    if len(registry_ids) != 88:
        problems.append("registry entries=%d expected 88" % len(registry_ids))
    if len(binding_ids) != 88:
        problems.append("runtime bindings=%d expected 88" % len(binding_ids))
    if len(set(registry_ids)) != len(registry_ids):
        problems.append("duplicate registry ids")
    if len(set(binding_ids)) != len(binding_ids):
        problems.append("duplicate runtime binding ids")

    for skill_id in (
        "kz-regulatory-source-lifecycle",
        "regulatory-product-applicability-evidence",
    ):
        if skill_id not in registry_ids:
            problems.append("%s missing from registry" % skill_id)
        if skill_id not in binding_ids:
            problems.append("%s missing from runtime allowlist" % skill_id)
        with open(
            "codex-skills/%s/skill-release.json" % skill_id, encoding="utf-8"
        ) as handle:
            release = json.load(handle)
        distribution = release.get("distribution") or {}
        expected = "https://qazagents.qdev.run/downloads/%s.zip" % skill_id
        if release.get("version") != "0.1.0":
            problems.append("%s version=%r" % (skill_id, release.get("version")))
        if distribution.get("canonical") != expected:
            problems.append(
                "%s distribution.canonical=%r" % (skill_id, distribution.get("canonical"))
            )
        if distribution.get("mirrors") not in ([], None):
            problems.append("%s mirrors=%r" % (skill_id, distribution.get("mirrors")))

    if "regulatory-report-evidence" in registry_ids:
        problems.append(
            "regulatory-report-evidence must stay unregistered (not admitted)"
        )
    if "regulatory-report-evidence" in binding_ids:
        problems.append("regulatory-report-evidence must stay unbound")

    print(
        json.dumps(
            {
                "registry_entries": len(registry_ids),
                "runtime_bindings": len(binding_ids),
                "problems": problems,
            },
            indent=2,
        )
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
