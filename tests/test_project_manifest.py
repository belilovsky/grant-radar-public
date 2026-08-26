"""Repository-level contract for Platform discovery and cold-start verification."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_qdev_project_manifest_describes_the_public_runtime() -> None:
    manifest = json.loads((ROOT / "qdev-project.json").read_text())

    assert manifest["schema_version"] == "qdev-project-manifest-v1"
    assert manifest["project_id"] == "qaz-fund"
    assert manifest["profile"] == "public-web"
    assert manifest["lifecycle"] == "production"
    assert manifest["repository"] == {
        "url": "https://github.com/belilovsky/grant-radar-public",
        "default_branch": "main",
    }
    assert manifest["entrypoints"]["public"] == "https://qaz.fund"
    assert manifest["operations"]["readiness_path"] == "/ready"
    assert manifest["operations"]["release_revision_path"] == (
        "/.well-known/release.json"
    )
    assert manifest["capabilities"]["qazstack"]["version"] == "1.41.2"
    assert manifest["capabilities"]["avds"]["version"] == "4.7.0"
    assert manifest["capabilities"]["identity"]["mode"] == "not-applicable"
    assert manifest["exceptions"] == [
        {
            "gate": "identity",
            "reason": (
                "The public runtime is anonymous and read-only, with no account, "
                "profile, upload, personal notification, or application-submission "
                "surface."
            ),
            "owner": "QDev",
            "expires": "2026-12-31",
        }
    ]


def test_qdev_project_manifest_references_existing_local_contracts() -> None:
    manifest = json.loads((ROOT / "qdev-project.json").read_text())
    local_contracts = {
        contract
        for capability in manifest["capabilities"].values()
        for contract in capability["contracts"]
        if not contract.startswith("https://")
    }
    local_contracts.update(manifest["quality"]["required_documents"])

    assert local_contracts
    assert all((ROOT / contract).exists() for contract in local_contracts)
