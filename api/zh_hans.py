"""Fail-closed local ``zh-Hans`` landing for QAZ.FUND.

The public site deliberately renders this bundle locally.  It never calls QMT
at request time: a catalog is an immutable release input, not a live service
dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs/qazstack/zh-hans/catalog.json"
MANIFEST_PATH = ROOT / "docs/qazstack/zh-hans/manifest.json"
OWNER_RECEIPT_PATH = ROOT / "docs/qazstack/zh-hans/owner-receipt.json"
OWNER_RECEIPT_SIGNATURE_PATH = ROOT / "docs/qazstack/zh-hans/owner-receipt.json.asc"
QDEV_PUBLIC_KEY_PATH = ROOT / "docs/qazstack/qdev-release-signing-key.asc"
QAZSTACK_CONTRACT_SHA256 = (
    "c309401ed21a2488ab61478d6db7380544b07bf83b8cf35399f128b0888af031"
)
QAZSTACK_WHEEL_SHA256 = (
    "a86092b3406eabbcaee7d2ecd9cd2d16263aa1392ea5f6472499214b08790b2"
)
QDEV_SIGNING_FINGERPRINT = "6808C85195786EFBFBA3ED88B1DDD6B455DFBEFD"
QMT_RELEASE_TAG = "v4.4.0"
QMT_RELEASE_SOURCE_SHA = "0a10953c470523698d5006a3071359c8146ee466"
UTC = timezone.utc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def zh_hans_enabled() -> bool:
    return os.environ.get("QAZ_FUND_ZH_HANS_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"zh-Hans release input must be an object: {path.name}")
    return value


def _wheel_contract_sha256() -> str:
    resource = files("qazstack").joinpath("i18n/resources/locale-contract.v1.json")
    return hashlib.sha256(resource.read_bytes()).hexdigest()


def _parse_expiry(value: object) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError("zh-Hans owner receipt expiry is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("zh-Hans owner receipt expiry is invalid") from exc
    if parsed.tzinfo is None:
        raise RuntimeError("zh-Hans owner receipt expiry is not timezone-aware")
    return parsed.astimezone(UTC)


def _verify_detached_receipt_signature() -> str:
    """Verify the pinned QDev signature without loading a user keyring."""

    if not QDEV_PUBLIC_KEY_PATH.is_file() or not OWNER_RECEIPT_SIGNATURE_PATH.is_file():
        raise RuntimeError("zh-Hans signed owner receipt or QDev public key is missing")
    with tempfile.TemporaryDirectory(prefix="qazfund-zh-hans-gpg-") as tmpdir:
        keyring = Path(tmpdir) / "trustedkeys.gpg"
        show = subprocess.run(
            ["gpg", "--batch", "--with-colons", "--import-options", "show-only", "--import", str(QDEV_PUBLIC_KEY_PATH)],
            check=False,
            capture_output=True,
            text=True,
        )
        fingerprints = {
            line.split(":")[9].upper()
            for line in show.stdout.splitlines()
            if line.startswith("fpr:") and len(line.split(":")) > 9
        }
        if show.returncode or QDEV_SIGNING_FINGERPRINT not in fingerprints:
            raise RuntimeError("pinned QDev public key fingerprint is invalid")
        imported = subprocess.run(
            ["gpg", "--batch", "--no-default-keyring", "--keyring", str(keyring), "--import", str(QDEV_PUBLIC_KEY_PATH)],
            check=False,
            capture_output=True,
            text=True,
        )
        if imported.returncode:
            raise RuntimeError("pinned QDev public key could not be imported")
        verified = subprocess.run(
            [
                "gpgv", "--status-fd", "1", "--keyring", str(keyring),
                str(OWNER_RECEIPT_SIGNATURE_PATH), str(OWNER_RECEIPT_PATH),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        valid = any(
            line.startswith("[GNUPG:] VALIDSIG ")
            and line.split()[2].upper() == QDEV_SIGNING_FINGERPRINT
            for line in verified.stdout.splitlines()
        )
        if verified.returncode or not valid:
            raise RuntimeError("zh-Hans owner receipt signature is invalid")
    return QDEV_SIGNING_FINGERPRINT


def _verify_v2_receipt(manifest: dict[str, Any]) -> bool:
    """Accept only a signed, unexpired controller authorization for activation."""

    if not OWNER_RECEIPT_PATH.is_file() or not OWNER_RECEIPT_SIGNATURE_PATH.is_file():
        return False
    receipt = _load_json(OWNER_RECEIPT_PATH)
    approval = receipt.get("approval")
    binding = manifest.get("productBinding")
    qmt_release = manifest.get("qmtRelease")
    receipt_qmt_release = receipt.get("qmtRelease")
    if (
        not isinstance(approval, dict)
        or not isinstance(binding, dict)
        or not isinstance(qmt_release, dict)
        or receipt_qmt_release != qmt_release
    ):
        return False
    if receipt.get("schemaVersion") != "qmt.catalog-owner-receipt.v2":
        return False
    required = {
        "project": "qaz-fund",
        "sourceLang": "ru",
        "targetLang": "zh-Hans",
        "catalogDigest": manifest.get("catalogDigest"),
        "bundleDigest": manifest.get("bundleDigest"),
        "contractDigest": QAZSTACK_CONTRACT_SHA256,
        "wheelDigest": QAZSTACK_WHEEL_SHA256,
        "signerFingerprint": QDEV_SIGNING_FINGERPRINT,
    }
    if any(receipt.get(key) != value for key, value in required.items()):
        return False
    if approval.get("mode") != "controller-authorization" or not isinstance(approval.get("url"), str):
        return False
    authorization_digest = approval.get("authorizationDigest")
    if not isinstance(authorization_digest, str) or not authorization_digest.startswith("sha256:"):
        return False
    if len(authorization_digest) != len("sha256:") + 64 or any(
        character not in "0123456789abcdef" for character in authorization_digest[len("sha256:") :].lower()
    ):
        return False
    if (
        receipt.get("sourceSha") != manifest.get("sourceSha")
        or manifest.get("sourceSha") != binding.get("sourceSha")
        or approval.get("reviewHead") != binding.get("sourceSha")
    ):
        return False
    if binding.get("contractDigest") != QAZSTACK_CONTRACT_SHA256 or binding.get("wheelDigest") != QAZSTACK_WHEEL_SHA256:
        return False
    if (
        qmt_release.get("tag") != QMT_RELEASE_TAG
        or qmt_release.get("sourceSha") != QMT_RELEASE_SOURCE_SHA
        or not isinstance(qmt_release.get("runtimeReceiptDigest"), str)
        or not isinstance(qmt_release.get("migrationReceiptDigest"), str)
        or not all(
            str(qmt_release[key]).startswith("sha256:")
            and len(str(qmt_release[key])) == 71
            and all(character in "0123456789abcdef" for character in str(qmt_release[key])[7:].lower())
            for key in ("runtimeReceiptDigest", "migrationReceiptDigest")
        )
    ):
        return False
    runtime_source = os.environ.get("QDEV_SOURCE_SHA", "").strip()
    if runtime_source != receipt.get("sourceSha"):
        return False
    try:
        now = datetime.now(UTC)
        expiry = _parse_expiry(approval.get("expiresAt"))
        if expiry <= now or expiry > now + timedelta(hours=24):
            return False
        return _verify_detached_receipt_signature() == QDEV_SIGNING_FINGERPRINT
    except (OSError, RuntimeError):
        return False


def zh_hans_readiness(*, require_owner_receipt: bool) -> dict[str, str | bool]:
    """Validate release inputs without exposing catalog text or credentials."""

    if not CATALOG_PATH.is_file() or not MANIFEST_PATH.is_file():
        raise RuntimeError("zh-Hans catalog bundle is missing")
    manifest = _load_json(MANIFEST_PATH)
    catalog = _load_json(CATALOG_PATH)
    required_keys = {"title", "description", "eyebrow", "headline", "body", "cta"}
    if set(catalog) != required_keys or any(not str(catalog[key]).strip() for key in required_keys):
        raise RuntimeError("zh-Hans catalog coverage is incomplete")
    legacy_manifest = manifest.get("schema_version") == "qaz-fund.zh-hans-manifest.v1"
    canonical_manifest = manifest.get("schemaVersion") == "qmt.catalog-manifest.v1"
    if not legacy_manifest and not canonical_manifest:
        raise RuntimeError("zh-Hans manifest schema is invalid")
    project = manifest.get("project")
    target = manifest.get("target_lang") if legacy_manifest else manifest.get("targetLang")
    digest = manifest.get("catalog_sha256") if legacy_manifest else manifest.get("catalogDigest")
    if project != "qaz-fund" or target != "zh-Hans":
        raise RuntimeError("zh-Hans manifest project or target is invalid")
    if digest != _sha256(CATALOG_PATH):
        raise RuntimeError("zh-Hans catalog digest does not match its manifest")
    binding = manifest.get("productBinding")
    if canonical_manifest and not isinstance(binding, dict):
        raise RuntimeError("zh-Hans canonical manifest is missing a product binding")
    contract = manifest.get("qazstack_contract_sha256") if legacy_manifest else binding.get("contractDigest")
    if contract != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("zh-Hans manifest has an unexpected QazStack contract")
    if _wheel_contract_sha256() != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("installed QazStack locale contract drifted")
    coverage = manifest.get("coverage")
    if legacy_manifest and coverage != {"required": 6, "translated": 6}:
        raise RuntimeError("zh-Hans manifest does not prove full public coverage")
    if canonical_manifest and coverage != {"required": 6, "present": 6, "complete": True}:
        raise RuntimeError("zh-Hans manifest does not prove full public coverage")
    receipt_ok = canonical_manifest and _verify_v2_receipt(manifest)
    if require_owner_receipt and not receipt_ok:
        raise RuntimeError("zh-Hans owner receipt is missing or does not match the catalog")
    return {
        "enabled": zh_hans_enabled(),
        "catalog_sha256": str(digest),
        "contract_sha256": QAZSTACK_CONTRACT_SHA256,
        "owner_receipt_verified": receipt_ok,
    }


def canonical_redirect_path(path: str, query_lang: str | None) -> str | None:
    """Return the sole safe Chinese public destination, or ``None``.

    Traditional Chinese is intentionally not an alias.  The landing has no
    public query schema, so selectors and unknown parameters are dropped.
    """

    normalized_path = path.lower().rstrip("/") or "/"
    normalized_lang = str(query_lang or "").strip().lower().replace("_", "-")
    if normalized_path in {"/zh", "/zh-cn", "/zh-sg", "/zh-hans"}:
        return "/zh-hans/"
    if normalized_path == "/" and normalized_lang in {"zh", "zh-cn", "zh-sg"}:
        return "/zh-hans/"
    return None


def render_landing(*, site_origin: str) -> str:
    copy = _load_json(CATALOG_PATH)
    canonical = f"{site_origin.rstrip('/')}/zh-hans/"
    ru = f"{site_origin.rstrip('/')}/?lang=ru"
    kk = f"{site_origin.rstrip('/')}/?lang=kk"
    en = f"{site_origin.rstrip('/')}/?lang=en"
    return """<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="ru" href="{ru}">
  <link rel="alternate" hreflang="kk" href="{kk}">
  <link rel="alternate" hreflang="en" href="{en}">
  <link rel="alternate" hreflang="zh-Hans" href="{canonical}">
  <link rel="alternate" hreflang="x-default" href="{ru}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{headline}","url":"{canonical}","inLanguage":"zh-Hans","isPartOf":{{"@type":"WebSite","name":"QAZ.FUND","url":"{site_origin}"}}}}</script>
</head>
<body>
  <main>
    <p>{eyebrow}</p>
    <h1>{headline}</h1>
    <p>{body}</p>
    <p><a href="{ru}">{cta}</a></p>
  </main>
</body>
</html>""".format(
        **{key: str(value) for key, value in copy.items()},
        canonical=canonical,
        ru=ru,
        kk=kk,
        en=en,
        site_origin=site_origin.rstrip("/"),
    )
