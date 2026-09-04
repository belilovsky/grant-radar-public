from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import main as api_main
from api import zh_hans


def test_dark_catalog_is_complete_but_not_owner_approved(monkeypatch) -> None:
    monkeypatch.delenv("QAZ_FUND_ZH_HANS_ENABLED", raising=False)
    readiness = zh_hans.zh_hans_readiness(require_owner_receipt=False)

    assert readiness["enabled"] is False
    assert readiness["owner_receipt_verified"] is False
    with pytest.raises(RuntimeError, match="owner receipt"):
        zh_hans.zh_hans_readiness(require_owner_receipt=True)


def test_canonical_json_matches_shared_cross_language_golden_vectors() -> None:
    fixture_path = (
        Path(__file__).parents[1]
        / "docs/contracts/qmt-canonical-json-golden-vectors.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture["schemaVersion"] == "qmt.canonical-json-golden-v1"
    for vector in fixture["vectors"]:
        assert zh_hans._canonical_json(vector["value"]) == vector["canonical"]
        assert zh_hans._canonical_digest(vector["value"]) == vector["sha256"]


def test_zh_hans_route_stays_dark_when_flag_is_false(monkeypatch) -> None:
    monkeypatch.setenv("QAZ_FUND_ZH_HANS_ENABLED", "false")
    client = TestClient(api_main.app)

    assert client.get("/zh-hans/").status_code == 404
    assert client.get("/zh-cn/", follow_redirects=False).status_code == 404
    assert client.get("/zh-hans/catalog", follow_redirects=False).status_code == 404


def test_catalog_query_is_dropped_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("QAZ_FUND_ZH_HANS_ENABLED", "true")
    monkeypatch.setattr(api_main, "_zh_hans_enabled", lambda: True)
    client = TestClient(api_main.app)

    response = client.get("/zh-hans/catalog?utm_source=unsafe", follow_redirects=False)

    assert response.status_code == 308
    assert response.headers["location"] == "/zh-hans/catalog/"


def test_alias_normalization_has_one_safe_destination() -> None:
    assert zh_hans.canonical_redirect_path("/ZH-CN/", None) == "/zh-hans/"
    assert zh_hans.canonical_redirect_path("/", "zh-SG") == "/zh-hans/"
    assert zh_hans.canonical_redirect_path("/", "zh-TW") is None
    assert zh_hans.canonical_redirect_path("/media", "zh") is None
    assert (
        zh_hans.canonical_redirect_path("/zh-hans/catalog", None) == "/zh-hans/catalog/"
    )


def test_landing_escapes_catalog_copy_and_json_ld(monkeypatch) -> None:
    """A sealed catalog cannot turn into executable markup at render time."""

    unsafe = {
        "title": "Title <img src=x onerror=alert(1)>",
        "description": "Description & details",
        "eyebrow": "Eyebrow",
        "headline": '</script><script>alert("x")</script>',
        "body": "Body",
        "cta": "Open",
    }
    monkeypatch.setattr(zh_hans, "_load_json", lambda _path: unsafe)

    page = zh_hans.render_landing(site_origin="https://qaz.fund")

    assert "<img src=x onerror=alert(1)>" not in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in page
    assert "</script><script>alert" not in page
    assert "\\u003c/script\\u003e" in page


def test_v2_receipt_rejects_a_manifest_with_divergent_source_binding(
    monkeypatch, tmp_path
) -> None:
    """A signature cannot rescue a receipt bound to the wrong product SHA."""

    receipt_path = tmp_path / "owner-receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schemaVersion": "qmt.catalog-owner-receipt.v2",
                "project": "qaz-fund",
                "sourceLang": "ru",
                "targetLang": "zh-Hans",
                "catalogDigest": "a" * 64,
                "bundleDigest": "b" * 64,
                "contractDigest": zh_hans.QAZSTACK_CONTRACT_SHA256,
                "wheelDigest": zh_hans.QAZSTACK_WHEEL_SHA256,
                "signerFingerprint": zh_hans.QDEV_SIGNING_FINGERPRINT,
                "qmtRelease": {
                    "tag": zh_hans.QMT_RELEASE_TAG,
                    "sourceSha": zh_hans.QMT_RELEASE_SOURCE_SHA,
                    "runtimeReceiptDigest": "sha256:" + "1" * 64,
                    "migrationReceiptDigest": "sha256:" + "2" * 64,
                },
                "sourceSha": "c" * 40,
                "approval": {
                    "mode": "controller-authorization",
                    "url": "https://ci.qdev.run/audit/catalog",
                    "authorizationDigest": "sha256:" + "d" * 64,
                    "expiresAt": "2099-01-01T00:00:00Z",
                    "reviewHead": "e" * 40,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(zh_hans, "OWNER_RECEIPT_PATH", receipt_path)
    monkeypatch.setattr(
        zh_hans, "OWNER_RECEIPT_SIGNATURE_PATH", tmp_path / "owner-receipt.json.asc"
    )
    monkeypatch.setenv("QDEV_SOURCE_SHA", "c" * 40)

    manifest = {
        "sourceSha": "c" * 40,
        "catalogDigest": "a" * 64,
        "bundleDigest": "b" * 64,
        "productBinding": {
            "sourceSha": "e" * 40,
            "contractDigest": zh_hans.QAZSTACK_CONTRACT_SHA256,
            "wheelDigest": zh_hans.QAZSTACK_WHEEL_SHA256,
        },
        "qmtRelease": {
            "tag": zh_hans.QMT_RELEASE_TAG,
            "sourceSha": zh_hans.QMT_RELEASE_SOURCE_SHA,
            "runtimeReceiptDigest": "sha256:" + "1" * 64,
            "migrationReceiptDigest": "sha256:" + "2" * 64,
        },
    }
    assert zh_hans._verify_v2_receipt(manifest) is False
