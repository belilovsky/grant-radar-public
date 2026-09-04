"""Fail-closed local ``zh-Hans`` landing for QAZ.FUND.

The public site deliberately renders this bundle locally.  It never calls QMT
at request time: a catalog is an immutable release input, not a live service
dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from html import escape
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
QMT_RELEASE_TAG = "v4.4.2"
# A product image must pin the exact QMT source that produced its release
# evidence.  The development fallback is intentionally non-validating: a
# canonical catalog cannot become activatable until deployment supplies the
# real, immutable value.
QMT_RELEASE_SOURCE_SHA = os.environ.get("QMT_RELEASE_SOURCE_SHA", "")
UTC = timezone.utc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(value: Any) -> str:
    """Match QMT's recursive, UTF-8 canonical JSON representation."""

    if isinstance(value, dict):
        return (
            "{"
            + ",".join(
                f"{json.dumps(str(key), ensure_ascii=False, separators=(',', ':'))}:"
                f"{_canonical_json(value[key])}"
                for key in sorted(value)
            )
            + "}"
        )
    if isinstance(value, list):
        return "[" + ",".join(_canonical_json(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"[0-9a-f]{64}", value, re.IGNORECASE)
    )


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"sha256:[0-9a-f]{64}", value, re.IGNORECASE)
    )


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"[0-9a-f]{40}", value, re.IGNORECASE)
    )


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
            [
                "gpg",
                "--batch",
                "--with-colons",
                "--import-options",
                "show-only",
                "--import",
                str(QDEV_PUBLIC_KEY_PATH),
            ],
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
            [
                "gpg",
                "--batch",
                "--no-default-keyring",
                "--keyring",
                str(keyring),
                "--import",
                str(QDEV_PUBLIC_KEY_PATH),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if imported.returncode:
            raise RuntimeError("pinned QDev public key could not be imported")
        verified = subprocess.run(
            [
                "gpgv",
                "--status-fd",
                "1",
                "--keyring",
                str(keyring),
                str(OWNER_RECEIPT_SIGNATURE_PATH),
                str(OWNER_RECEIPT_PATH),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        # VALIDSIG names the signing key first and, depending on the gpg
        # version, includes the primary-key fingerprint later in the record.
        # Accept a valid signing subkey only when that primary fingerprint is
        # also present; never trust a caller-supplied fingerprint alone.
        valid = any(
            line.startswith("[GNUPG:] VALIDSIG ")
            and QDEV_SIGNING_FINGERPRINT
            in {token.upper() for token in line.split()[2:]}
            for line in verified.stdout.splitlines()
        )
        if verified.returncode or not valid:
            raise RuntimeError("zh-Hans owner receipt signature is invalid")
    return QDEV_SIGNING_FINGERPRINT


def _verify_v2_receipt(manifest: dict[str, Any]) -> bool:
    """Accept only a signed, unexpired controller authorization for activation."""

    if not OWNER_RECEIPT_PATH.is_file() or not OWNER_RECEIPT_SIGNATURE_PATH.is_file():
        return False
    try:
        receipt = _load_json(OWNER_RECEIPT_PATH)
    except (OSError, RuntimeError, json.JSONDecodeError):
        return False
    approval = receipt.get("approval")
    binding = manifest.get("productBinding")
    qmt_release = manifest.get("qmtRelease")
    if (
        not isinstance(approval, dict)
        or not isinstance(binding, dict)
        or not isinstance(qmt_release, dict)
        or receipt.get("qmtRelease") != qmt_release
        or manifest.get("schemaVersion") != "qmt.catalog-manifest.v1"
    ):
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
    if receipt.get("schemaVersion") != "qmt.catalog-owner-receipt.v2" or any(
        receipt.get(key) != value for key, value in required.items()
    ):
        return False
    product_source = manifest.get("sourceSha")
    if (
        not _is_sha(product_source)
        or receipt.get("productSourceSha") != product_source
        or receipt.get("approvalReviewHead") != approval.get("reviewHead")
        or not _is_sha(receipt.get("approvalReviewHead"))
        or not _is_sha(receipt.get("signerSourceSha"))
        or not _is_digest(receipt.get("candidateImageDigest"))
        or receipt.get("candidateImageDigest") != qmt_release.get("imageDigest")
        or receipt.get("manifestSha256") != _sha256(MANIFEST_PATH)
    ):
        return False
    if (
        binding.get("sourceSha") != product_source
        or binding.get("contractDigest") != QAZSTACK_CONTRACT_SHA256
        or binding.get("wheelDigest") != QAZSTACK_WHEEL_SHA256
    ):
        return False
    if (
        qmt_release.get("tag") != QMT_RELEASE_TAG
        or qmt_release.get("sourceSha") != QMT_RELEASE_SOURCE_SHA
        or not _is_sha(qmt_release.get("sourceSha"))
        or not _is_digest(qmt_release.get("imageDigest"))
        or not _is_digest(qmt_release.get("runtimeReceiptDigest"))
        or not _is_digest(qmt_release.get("migrationReceiptDigest"))
    ):
        return False
    authorization_digest = approval.get("authorizationDigest")
    if (
        approval.get("mode") != "controller-authorization"
        or not isinstance(approval.get("url"), str)
        or not approval["url"].startswith("https://")
        or not _is_digest(authorization_digest)
    ):
        return False
    runtime_source = os.environ.get("QDEV_SOURCE_SHA", "").strip().lower()
    if runtime_source != str(product_source).lower():
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
    legacy_manifest = manifest.get("schema_version") == "qaz-fund.zh-hans-manifest.v1"
    canonical_manifest = manifest.get("schemaVersion") == "qmt.catalog-manifest.v1"
    if not legacy_manifest and not canonical_manifest:
        raise RuntimeError("zh-Hans manifest schema is invalid")
    project = manifest.get("project")
    source_lang = (
        manifest.get("source_lang") if legacy_manifest else manifest.get("sourceLang")
    )
    target = (
        manifest.get("target_lang") if legacy_manifest else manifest.get("targetLang")
    )
    digest = (
        manifest.get("catalog_sha256")
        if legacy_manifest
        else manifest.get("catalogDigest")
    )
    if project != "qaz-fund" or source_lang != "ru" or target != "zh-Hans":
        raise RuntimeError("zh-Hans manifest project or target is invalid")

    # The legacy six-key fixture is retained only for dark-mode compatibility.
    # A public candidate must prove its source-derived key set and use QMT's
    # canonical JSON digest (never the incidental formatting of a JSON file).
    if canonical_manifest:
        required_keys = manifest.get("requiredKeys")
        public_routes = manifest.get("publicRoutes")
        coverage = manifest.get("coverage")
        if (
            not isinstance(required_keys, list)
            or not required_keys
            or any(not isinstance(key, str) or not key.strip() for key in required_keys)
            or len(set(required_keys)) != len(required_keys)
            or set(catalog) != set(required_keys)
            or any(
                not isinstance(catalog[key], str) or not catalog[key].strip()
                for key in required_keys
            )
            or not isinstance(public_routes, list)
            or not public_routes
            or any(
                not isinstance(route, str) or not route.startswith("/zh-hans/")
                for route in public_routes
            )
            or coverage
            != {
                "required": len(required_keys),
                "present": len(required_keys),
                "complete": True,
            }
        ):
            raise RuntimeError("zh-Hans catalog coverage is incomplete")
        if digest != _canonical_digest(catalog):
            raise RuntimeError(
                "zh-Hans catalog canonical digest does not match its manifest"
            )
        unsigned_manifest = dict(manifest)
        unsigned_manifest.pop("bundleDigest", None)
        if manifest.get("bundleDigest") != _canonical_digest(
            {"catalog": catalog, "manifest": unsigned_manifest}
        ):
            raise RuntimeError(
                "zh-Hans catalog bundle digest does not match its manifest"
            )
    else:
        required_keys = {"title", "description", "eyebrow", "headline", "body", "cta"}
        if set(catalog) != required_keys or any(
            not isinstance(catalog[key], str) or not catalog[key].strip()
            for key in required_keys
        ):
            raise RuntimeError("zh-Hans catalog coverage is incomplete")
        if digest != _sha256(CATALOG_PATH):
            raise RuntimeError("zh-Hans catalog digest does not match its manifest")

    binding = manifest.get("productBinding")
    if canonical_manifest and not isinstance(binding, dict):
        raise RuntimeError("zh-Hans canonical manifest is missing a product binding")
    contract = (
        binding.get("contractDigest")
        if canonical_manifest and isinstance(binding, dict)
        else manifest.get("qazstack_contract_sha256")
    )
    if contract != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("zh-Hans manifest has an unexpected QazStack contract")
    if _wheel_contract_sha256() != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("installed QazStack locale contract drifted")
    coverage = manifest.get("coverage")
    if legacy_manifest and coverage != {"required": 6, "translated": 6}:
        raise RuntimeError("zh-Hans manifest does not prove full public coverage")
    receipt_ok = canonical_manifest and _verify_v2_receipt(manifest)
    if require_owner_receipt and not receipt_ok:
        raise RuntimeError(
            "zh-Hans owner receipt is missing or does not match the catalog"
        )
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
    # The data catalogue is a public UI route, but it has no query schema.
    # Normalise its no-slash spelling and drop arbitrary query parameters in
    # the same way as the landing route.  The middleware still keeps the
    # entire namespace dark while the feature flag is disabled.
    if normalized_path == "/zh-hans/catalog":
        return "/zh-hans/catalog/"
    if normalized_path == "/" and normalized_lang in {"zh", "zh-cn", "zh-sg"}:
        return "/zh-hans/"
    return None


def is_zh_hans_namespace_path(path: str) -> bool:
    """Recognise only the public simplified-Chinese route namespace.

    This helper is deliberately narrower than a generic ``/zh`` prefix check:
    Traditional-Chinese paths (``zh-TW``) and unrelated identifiers must not
    be redirected or accidentally exposed when the feature flag is dark.
    """

    normalized = str(path or "").strip()
    return bool(
        re.fullmatch(r"/zh-hans(?:/.*)?", normalized, flags=re.IGNORECASE)
        or re.fullmatch(r"/zh(?:-cn|-sg)?(?:/.*)?", normalized, flags=re.IGNORECASE)
    )


def render_landing(*, site_origin: str) -> str:
    copy = _load_json(CATALOG_PATH)
    origin = site_origin.rstrip("/")
    canonical_url = f"{origin}/zh-hans/"
    ru_url = f"{origin}/ru/intro/"
    kk_url = f"{origin}/kk/intro/"
    en_url = f"{origin}/en/intro/"
    raw_copy = {key: str(value) for key, value in copy.items()}
    safe_copy = {key: escape(value, quote=True) for key, value in raw_copy.items()}
    schema = (
        json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": raw_copy["headline"],
                "url": canonical_url,
                "inLanguage": "zh-Hans",
                "isPartOf": {
                    "@type": "WebSite",
                    "name": "QAZ.FUND",
                    "url": origin,
                },
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
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
  <script type="application/ld+json">{schema}</script>
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
        **safe_copy,
        canonical=escape(canonical_url, quote=True),
        ru=escape(ru_url, quote=True),
        kk=escape(kk_url, quote=True),
        en=escape(en_url, quote=True),
        schema=schema,
    )


def render_catalog_page(*, site_origin: str) -> str:
    """Render the public Chinese UI shell around source-language cards.

    Card and opportunity text is intentionally not machine-translated in this
    release.  The page therefore carries an explicit source-language notice
    and is excluded from indexing by the route handler.
    """

    origin = site_origin.rstrip("/")
    catalog_url = f"{origin}/zh-hans/catalog/"
    landing_url = f"{origin}/zh-hans/"
    return """<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QAZ.FUND – 项目目录</title>
  <meta name="description" content="公开支持项目目录。项目卡片正文保留原始语言。">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="{catalog}">
</head>
<body>
  <main>
    <p><a href="{landing}">QAZ.FUND</a></p>
    <h1>公开支持项目目录</h1>
    <p lang="ru">Основной текст карточек показывается на языке источника.</p>
    <p>卡片正文保留来源语言；请打开官方来源核对条件和截止日期。</p>
  </main>
</body>
</html>""".format(
        catalog=escape(catalog_url, quote=True),
        landing=escape(landing_url, quote=True),
    )
