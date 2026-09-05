from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import main as api_main
from api import zh_hans
from core.models import Opportunity


def _catalog_copy() -> dict[str, str]:
    return {
        "catalog.title": "目录",
        "catalog.description": "公开项目",
        "catalog.heading": "项目目录",
        "catalog.intro": "查找公开项目。",
        "catalog.search_label": "搜索",
        "catalog.search_placeholder": "关键词",
        "catalog.type_label": "类型",
        "catalog.type_all": "全部",
        "catalog.type.grant": "资助",
        "catalog.type.accelerator": "加速器",
        "catalog.type.cloud_credit": "云额度",
        "catalog.type.tender": "招标",
        "catalog.type.contest": "竞赛",
        "catalog.type.fellowship": "研修",
        "catalog.filter_apply": "筛选",
        "catalog.results_count": "结果：{count}",
        "catalog.empty_title": "没有结果",
        "catalog.empty_body": "请更改筛选条件。",
        "catalog.load_error": "目录暂时不可用",
        "catalog.source_language": "来源语言：{language}",
        "catalog.unknown_language": "未知",
        "catalog.official_source": "打开官方来源",
        "catalog.previous": "上一页",
        "catalog.next": "下一页",
        "catalog.page_label": "第 {current} 页，共 {total} 页",
        "catalog.verification_note": "请在官方来源核对条件。",
        "catalog.landing_link": "QAZ.FUND 首页",
    }


def _write_canonical_bundle(
    tmp_path: Path,
    *,
    catalog: dict[str, str],
    required_keys: list[str],
    public_routes: list[str],
) -> tuple[Path, Path]:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "schemaVersion": "qmt.catalog-manifest.v1",
        "project": "qaz-fund",
        "sourceSha": "1" * 40,
        "sourceLang": "ru",
        "targetLang": "zh-Hans",
        "catalogDigest": zh_hans._canonical_digest(catalog),
        "requiredKeys": required_keys,
        "publicRoutes": public_routes,
        "coverage": {
            "required": len(required_keys),
            "present": len(required_keys),
            "complete": True,
        },
        "profile": {
            "id": "qaz-fund:ru:zh-Hans",
            "modelRoutes": ["generator-a"],
            "promptVersion": "1",
            "glossaryVersion": "1",
            "tmVersion": "1",
        },
        "quorum": {
            "required": "2/3",
            "positive": 3,
            "routes": ["critic-a", "critic-b", "critic-c"],
            "criticalMqmCount": 0,
        },
        "reviewState": "approved",
        "ownerReceipt": None,
        "qmtRelease": {
            "tag": zh_hans.QMT_RELEASE_TAG,
            "sourceSha": "2" * 40,
            "imageDigest": "sha256:" + "3" * 64,
            "runtimeReceiptDigest": "sha256:" + "4" * 64,
            "migrationReceiptDigest": "sha256:" + "5" * 64,
        },
        "productBinding": {
            "sourceSha": "1" * 40,
            "contractDigest": zh_hans.QAZSTACK_CONTRACT_SHA256,
            "wheelDigest": zh_hans.QAZSTACK_WHEEL_SHA256,
        },
    }
    manifest["bundleDigest"] = zh_hans._canonical_digest(
        {"catalog": catalog, "manifest": manifest}
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return catalog_path, manifest_path


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


def test_catalog_query_schema_is_preserved_and_normalized(monkeypatch) -> None:
    monkeypatch.setenv("QAZ_FUND_ZH_HANS_ENABLED", "true")
    monkeypatch.setattr(api_main, "_zh_hans_enabled", lambda: True)
    client = TestClient(api_main.app)

    response = client.get(
        "/ZH-HANS/CATALOG?q=AI&type=GRANT&page=2&lang=zh-CN&unknown=x",
        follow_redirects=False,
    )

    assert response.status_code == 308
    assert response.headers["location"] == "/zh-hans/catalog/?q=AI&type=grant&page=2"


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
    assert 'href="https://qaz.fund/zh-hans/catalog/"' in page


def test_catalog_renders_real_items_without_translating_or_trusting_markup(
    monkeypatch,
) -> None:
    monkeypatch.setattr(zh_hans, "_load_json", lambda _path: _catalog_copy())
    item = Opportunity(
        source="official",
        source_url="https://example.org/programme",
        type="grant",
        title='<script lang="ru">Опасный заголовок</script>',
        summary="Описание программы",
        languages=["ru"],
    )

    page = zh_hans.render_catalog_page(
        site_origin="https://qaz.fund",
        items=[item],
        query="Опасный",
        kind="grant",
    )

    assert '<html lang="zh-Hans">' in page
    assert '<script lang="ru">' not in page
    assert "&lt;script lang=&quot;ru&quot;&gt;" in page
    assert 'lang="ru"' in page
    assert "来源语言：ru" in page
    assert 'href="https://example.org/programme"' in page
    assert '<meta name="robots" content="noindex,follow">' in page


def test_catalog_route_never_uses_runtime_translation(monkeypatch) -> None:
    item = Opportunity(
        source="official",
        source_url="https://example.org/programme",
        type="grant",
        title="Исходный заголовок",
        summary="Исходное описание",
        languages=["ru"],
    )
    monkeypatch.setattr(api_main, "_zh_hans_enabled", lambda: True)
    monkeypatch.setattr(
        api_main, "_current_source_language_catalog_items", lambda: [item]
    )
    monkeypatch.setattr(zh_hans, "_load_json", lambda _path: _catalog_copy())
    monkeypatch.setattr(
        api_main,
        "localize_opportunity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("runtime localization must not be called")
        ),
    )
    client = TestClient(api_main.app)

    response = client.get("/zh-hans/catalog/")

    assert response.status_code == 200
    assert "Исходный заголовок" in response.text


def test_catalog_rejects_incomplete_ui_copy(monkeypatch) -> None:
    monkeypatch.setattr(zh_hans, "_load_json", lambda _path: {"catalog.title": "目录"})

    with pytest.raises(RuntimeError, match="UI copy is incomplete"):
        zh_hans.render_catalog_page(site_origin="https://qaz.fund", items=[])


def test_catalog_rejects_runtime_placeholder_drift(monkeypatch) -> None:
    copy = _catalog_copy()
    copy["catalog.results_count"] = "结果：{total}"
    monkeypatch.setattr(zh_hans, "_load_json", lambda _path: copy)

    with pytest.raises(RuntimeError, match="placeholder mismatch"):
        zh_hans.render_catalog_page(site_origin="https://qaz.fund", items=[])


def test_canonical_readiness_requires_the_source_derived_key_and_route_sets(
    monkeypatch, tmp_path
) -> None:
    catalog = {key: key for key in zh_hans.ZH_HANS_REQUIRED_KEYS}
    expected_keys = sorted(zh_hans.ZH_HANS_REQUIRED_KEYS, key=zh_hans._utf16_sort_key)
    catalog_path, manifest_path = _write_canonical_bundle(
        tmp_path,
        catalog=catalog,
        required_keys=expected_keys,
        public_routes=list(zh_hans.ZH_HANS_PUBLIC_ROUTES),
    )
    monkeypatch.setattr(zh_hans, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(zh_hans, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        zh_hans, "_wheel_contract_sha256", lambda: zh_hans.QAZSTACK_CONTRACT_SHA256
    )

    readiness = zh_hans.zh_hans_readiness(require_owner_receipt=False)

    assert readiness["catalog_sha256"] == zh_hans._canonical_digest(catalog)


@pytest.mark.parametrize("mutation", ["key", "route"])
def test_canonical_readiness_rejects_caller_defined_partial_coverage(
    monkeypatch, tmp_path, mutation
) -> None:
    catalog = {key: key for key in zh_hans.ZH_HANS_REQUIRED_KEYS}
    required_keys = sorted(zh_hans.ZH_HANS_REQUIRED_KEYS, key=zh_hans._utf16_sort_key)
    public_routes = list(zh_hans.ZH_HANS_PUBLIC_ROUTES)
    if mutation == "key":
        removed = required_keys.pop()
        catalog.pop(removed)
    else:
        public_routes.pop()
    catalog_path, manifest_path = _write_canonical_bundle(
        tmp_path,
        catalog=catalog,
        required_keys=required_keys,
        public_routes=public_routes,
    )
    monkeypatch.setattr(zh_hans, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(zh_hans, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        zh_hans, "_wheel_contract_sha256", lambda: zh_hans.QAZSTACK_CONTRACT_SHA256
    )

    with pytest.raises(RuntimeError, match="coverage is incomplete"):
        zh_hans.zh_hans_readiness(require_owner_receipt=False)


def test_v2_receipt_keeps_product_and_qmt_image_identities_distinct(
    monkeypatch, tmp_path
) -> None:
    product_sha = "1" * 40
    signer_sha = "2" * 40
    approval_head = "3" * 40
    product_image = "sha256:" + "4" * 64
    qmt_image = "sha256:" + "5" * 64
    qmt_source = "6" * 40
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    qmt_release = {
        "tag": zh_hans.QMT_RELEASE_TAG,
        "sourceSha": qmt_source,
        "imageDigest": qmt_image,
        "runtimeReceiptDigest": "sha256:" + "7" * 64,
        "migrationReceiptDigest": "sha256:" + "8" * 64,
    }
    approval = {
        "mode": "controller-authorization",
        "url": "https://ci.qdev.run/audit/catalog",
        "authorizationDigest": "sha256:" + "9" * 64,
        "authorizationSignatureDigest": "a" * 64,
        "expiresAt": expiry,
        "reviewHead": approval_head,
    }
    manifest = {
        "schemaVersion": "qmt.catalog-manifest.v1",
        "project": "qaz-fund",
        "sourceLang": "ru",
        "targetLang": "zh-Hans",
        "sourceSha": product_sha,
        "catalogDigest": "b" * 64,
        "bundleDigest": "c" * 64,
        "productBinding": {
            "sourceSha": product_sha,
            "contractDigest": zh_hans.QAZSTACK_CONTRACT_SHA256,
            "wheelDigest": zh_hans.QAZSTACK_WHEEL_SHA256,
        },
        "qmtRelease": qmt_release,
    }
    receipt = {
        "schemaVersion": "qmt.catalog-owner-receipt.v2",
        "project": "qaz-fund",
        "sourceLang": "ru",
        "targetLang": "zh-Hans",
        "catalogDigest": manifest["catalogDigest"],
        "bundleDigest": manifest["bundleDigest"],
        "contractDigest": zh_hans.QAZSTACK_CONTRACT_SHA256,
        "wheelDigest": zh_hans.QAZSTACK_WHEEL_SHA256,
        "signerFingerprint": zh_hans.QDEV_SIGNING_FINGERPRINT,
        "productSourceSha": product_sha,
        "approvalReviewHead": approval_head,
        "signerSourceSha": signer_sha,
        "candidateImageDigest": product_image,
        "manifestSha256": zh_hans._sha256(manifest_path),
        "qmtRelease": qmt_release,
        "approval": approval,
    }
    receipt_path = tmp_path / "owner-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    signature_path = tmp_path / "owner-receipt.json.asc"
    signature_path.write_text("signature", encoding="utf-8")
    monkeypatch.setattr(zh_hans, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(zh_hans, "OWNER_RECEIPT_PATH", receipt_path)
    monkeypatch.setattr(zh_hans, "OWNER_RECEIPT_SIGNATURE_PATH", signature_path)
    monkeypatch.setattr(zh_hans, "QMT_RELEASE_SOURCE_SHA", qmt_source)
    monkeypatch.setattr(zh_hans, "_verify_controller_authorization", lambda *_: True)
    monkeypatch.setattr(
        zh_hans,
        "_verify_detached_receipt_signature",
        lambda: zh_hans.QDEV_SIGNING_FINGERPRINT,
    )
    monkeypatch.setenv("QDEV_SOURCE_SHA", product_sha)
    monkeypatch.setenv("APP_IMAGE_DIGEST", product_image)
    monkeypatch.setenv("QMT_RELEASE_TAG", zh_hans.QMT_RELEASE_TAG)
    monkeypatch.setenv("QMT_RELEASE_SOURCE_SHA", qmt_source)
    monkeypatch.setenv("QMT_IMAGE_DIGEST", qmt_image)
    monkeypatch.setenv(
        "QMT_RUNTIME_RECEIPT_DIGEST", qmt_release["runtimeReceiptDigest"]
    )
    monkeypatch.setenv(
        "QMT_MIGRATION_RECEIPT_DIGEST", qmt_release["migrationReceiptDigest"]
    )

    assert zh_hans._verify_v2_receipt(manifest) is True


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
