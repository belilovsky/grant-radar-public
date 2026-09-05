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
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

from api.avds import AVDS_CSS
from core.models import Opportunity, OpportunityType
from core.provenance import provenance_profile

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs/qazstack/zh-hans/catalog.json"
MANIFEST_PATH = ROOT / "docs/qazstack/zh-hans/manifest.json"
APPROVAL_ROOT = Path(
    os.environ.get("ZH_HANS_APPROVAL_DIR", str(ROOT / "docs/qazstack/zh-hans"))
)
OWNER_RECEIPT_PATH = APPROVAL_ROOT / "owner-receipt.json"
OWNER_RECEIPT_SIGNATURE_PATH = APPROVAL_ROOT / "owner-receipt.json.asc"
AUTHORIZATION_RECORD_PATH = APPROVAL_ROOT / "controller-authorization.json"
AUTHORIZATION_SIGNATURE_PATH = APPROVAL_ROOT / "controller-authorization.json.asc"
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
CATALOG_PAGE_SIZE = 12
_MESSAGE_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
_CATALOG_QUERY_KEYS = {"q", "type", "page"}
_CATALOG_TYPES = {member.value for member in OpportunityType}
ZH_HANS_LANDING_KEYS = frozenset(
    {"title", "description", "eyebrow", "headline", "body", "cta"}
)
ZH_HANS_CATALOG_KEYS = frozenset(
    {
        "catalog.title",
        "catalog.description",
        "catalog.heading",
        "catalog.intro",
        "catalog.search_label",
        "catalog.search_placeholder",
        "catalog.type_label",
        "catalog.type_all",
        *{f"catalog.type.{value}" for value in _CATALOG_TYPES},
        "catalog.filter_apply",
        "catalog.results_count",
        "catalog.empty_title",
        "catalog.empty_body",
        "catalog.load_error",
        "catalog.source_language",
        "catalog.unknown_language",
        "catalog.official_source",
        "catalog.previous",
        "catalog.next",
        "catalog.page_label",
        "catalog.verification_note",
        "catalog.landing_link",
    }
)
ZH_HANS_REQUIRED_KEYS = ZH_HANS_LANDING_KEYS | ZH_HANS_CATALOG_KEYS
ZH_HANS_PUBLIC_ROUTES = ("/zh-hans/", "/zh-hans/catalog/")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utf16_sort_key(value: str) -> bytes:
    """Return the ECMAScript property-order key used by QMT.

    JavaScript's default string ordering compares UTF-16 code units, while
    Python orders Unicode code points.  The distinction matters for a catalog
    key containing a non-BMP character, so encode with surrogatepass and sort
    the resulting big-endian code units explicitly.
    """

    return value.encode("utf-16-be", "surrogatepass")


def _canonical_json(value: Any) -> str:
    """Match QMT's recursive, UTF-8 canonical JSON representation."""

    if isinstance(value, dict):
        keys = list(value)
        keys.sort(key=lambda key: _utf16_sort_key(str(key)))
        return (
            "{"
            + ",".join(
                f"{json.dumps(str(key), ensure_ascii=False, separators=(',', ':'))}:"
                f"{_canonical_json(value[key])}"
                for key in keys
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


def _verify_detached_signature(data_path: Path, signature_path: Path) -> str:
    """Verify a QDev detached signature without loading a user keyring."""

    if (
        not QDEV_PUBLIC_KEY_PATH.is_file()
        or not data_path.is_file()
        or not signature_path.is_file()
    ):
        raise RuntimeError("zh-Hans signed release input or QDev public key is missing")
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
                str(signature_path),
                str(data_path),
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
        invalid_statuses = (
            "[GNUPG:] BADSIG ",
            "[GNUPG:] ERRSIG ",
            "[GNUPG:] EXPSIG ",
            "[GNUPG:] EXPKEYSIG ",
            "[GNUPG:] REVKEYSIG ",
            "[GNUPG:] KEYREVOKED",
        )
        explicitly_invalid = any(
            line.startswith(invalid_statuses) for line in verified.stdout.splitlines()
        )
        if verified.returncode or not valid or explicitly_invalid:
            raise RuntimeError("zh-Hans owner receipt signature is invalid")
    return QDEV_SIGNING_FINGERPRINT


def _verify_detached_receipt_signature() -> str:
    return _verify_detached_signature(OWNER_RECEIPT_PATH, OWNER_RECEIPT_SIGNATURE_PATH)


_FORBIDDEN_RELEASE_FIELDS = {
    "catalog",
    "sourcecatalog",
    "translatedcatalog",
    "rawtext",
    "text",
    "translation",
    "translations",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "tokens",
    "password",
    "passwords",
    "cookie",
    "cookies",
}


def _contains_forbidden_release_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in _FORBIDDEN_RELEASE_FIELDS
            or _contains_forbidden_release_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_release_field(item) for item in value)
    return False


def _verify_controller_authorization(
    approval: dict[str, Any],
    expiry: datetime,
    expected_binding: dict[str, Any],
) -> bool:
    """Bind and cryptographically verify the controller authorization record."""

    signature_digest = approval.get("authorizationSignatureDigest")
    authorization_digest = approval.get("authorizationDigest")
    if (
        not AUTHORIZATION_RECORD_PATH.is_file()
        or not AUTHORIZATION_SIGNATURE_PATH.is_file()
        or not isinstance(signature_digest, str)
        or not isinstance(authorization_digest, str)
        or not _is_sha256(signature_digest)
        or not _is_digest(authorization_digest)
    ):
        return False
    try:
        authorization = _load_json(AUTHORIZATION_RECORD_PATH)
        if _contains_forbidden_release_field(authorization):
            return False
        if (
            authorization.get("schemaVersion") != "qdev.controller-authorization.v1"
            or authorization.get("action") != "catalog-owner-receipt"
            or authorization.get("binding") != expected_binding
        ):
            return False
        if authorization.get("reviewHead") != approval.get("reviewHead"):
            return False
        authorization_expiry = _parse_expiry(authorization.get("expiresAt"))
        if authorization_expiry != expiry:
            return False
        if _canonical_digest(authorization) != authorization_digest.removeprefix(
            "sha256:"
        ):
            return False
        if _sha256(AUTHORIZATION_SIGNATURE_PATH) != signature_digest:
            return False
        return (
            _verify_detached_signature(
                AUTHORIZATION_RECORD_PATH,
                AUTHORIZATION_SIGNATURE_PATH,
            )
            == QDEV_SIGNING_FINGERPRINT
        )
    except (OSError, RuntimeError, json.JSONDecodeError):
        return False


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
    product_image_digest = os.environ.get("APP_IMAGE_DIGEST", "").strip().lower()
    runtime_qmt_release = {
        "tag": os.environ.get("QMT_RELEASE_TAG", "").strip(),
        "sourceSha": os.environ.get("QMT_RELEASE_SOURCE_SHA", "").strip().lower(),
        "imageDigest": os.environ.get("QMT_IMAGE_DIGEST", "").strip().lower(),
        "runtimeReceiptDigest": os.environ.get("QMT_RUNTIME_RECEIPT_DIGEST", "")
        .strip()
        .lower(),
        "migrationReceiptDigest": os.environ.get("QMT_MIGRATION_RECEIPT_DIGEST", "")
        .strip()
        .lower(),
    }
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
        or receipt.get("candidateImageDigest") != product_image_digest
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
        or runtime_qmt_release != qmt_release
    ):
        return False
    authorization_digest = approval.get("authorizationDigest")
    if (
        approval.get("mode") != "controller-authorization"
        or not isinstance(approval.get("url"), str)
        or not approval["url"].startswith("https://")
        or not _is_digest(authorization_digest)
        or not _is_sha256(approval.get("authorizationSignatureDigest"))
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
        expected_authorization_binding = {
            "project": manifest.get("project"),
            "productSourceSha": product_source,
            "sourceLang": manifest.get("sourceLang"),
            "targetLang": manifest.get("targetLang"),
            "catalogDigest": manifest.get("catalogDigest"),
            "bundleDigest": manifest.get("bundleDigest"),
            "contractDigest": binding.get("contractDigest"),
            "wheelDigest": binding.get("wheelDigest"),
            "qmtRelease": qmt_release,
            "candidateImageDigest": receipt.get("candidateImageDigest"),
            "approvalReviewHead": receipt.get("approvalReviewHead"),
            "signerSourceSha": receipt.get("signerSourceSha"),
        }
        if not _verify_controller_authorization(
            approval, expiry, expected_authorization_binding
        ):
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
        profile = manifest.get("profile")
        quorum = manifest.get("quorum")
        qmt_release = manifest.get("qmtRelease")
        binding = manifest.get("productBinding")
        expected_keys = sorted(ZH_HANS_REQUIRED_KEYS, key=_utf16_sort_key)
        if (
            _contains_forbidden_release_field(manifest)
            or required_keys != expected_keys
            or set(catalog) != ZH_HANS_REQUIRED_KEYS
            or any(
                not isinstance(catalog[key], str) or not catalog[key].strip()
                for key in expected_keys
            )
            or public_routes != list(ZH_HANS_PUBLIC_ROUTES)
            or coverage
            != {
                "required": len(expected_keys),
                "present": len(expected_keys),
                "complete": True,
            }
        ):
            raise RuntimeError("zh-Hans catalog coverage is incomplete")
        if (
            not _is_sha(manifest.get("sourceSha"))
            or manifest.get("reviewState") != "approved"
            or manifest.get("ownerReceipt") is not None
            or not isinstance(profile, dict)
            or profile.get("id") != "qaz-fund:ru:zh-Hans"
            or not isinstance(profile.get("modelRoutes"), list)
            or not profile["modelRoutes"]
            or any(
                not isinstance(route, str) or not route.strip()
                for route in profile["modelRoutes"]
            )
            or any(
                not isinstance(profile.get(field), str) or not profile[field].strip()
                for field in ("promptVersion", "glossaryVersion", "tmVersion")
            )
            or not isinstance(quorum, dict)
            or quorum.get("required") != "2/3"
            or not isinstance(quorum.get("positive"), int)
            or not 2 <= quorum["positive"] <= 3
            or not isinstance(quorum.get("routes"), list)
            or len(quorum["routes"]) != 3
            or len(set(quorum["routes"])) != 3
            or quorum.get("criticalMqmCount") != 0
            or not isinstance(qmt_release, dict)
            or qmt_release.get("tag") != QMT_RELEASE_TAG
            or not _is_sha(qmt_release.get("sourceSha"))
            or not _is_digest(qmt_release.get("imageDigest"))
            or not _is_digest(qmt_release.get("runtimeReceiptDigest"))
            or not _is_digest(qmt_release.get("migrationReceiptDigest"))
            or not isinstance(binding, dict)
            or binding.get("sourceSha") != manifest.get("sourceSha")
            or binding.get("contractDigest") != QAZSTACK_CONTRACT_SHA256
            or binding.get("wheelDigest") != QAZSTACK_WHEEL_SHA256
        ):
            raise RuntimeError("zh-Hans canonical release evidence is invalid")
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
        required_keys = ZH_HANS_LANDING_KEYS
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


def _canonical_catalog_query(
    query_items: Sequence[tuple[str, str]],
) -> str:
    """Keep only one valid value for each public catalog query field."""

    accepted: dict[str, str] = {}
    for raw_key, raw_value in query_items:
        key = str(raw_key).strip()
        if key not in _CATALOG_QUERY_KEYS or key in accepted:
            continue
        value = str(raw_value).strip()
        if key == "q":
            if value:
                accepted[key] = value[:120]
        elif key == "type":
            normalized = value.lower()
            if normalized in _CATALOG_TYPES:
                accepted[key] = normalized
        elif key == "page" and value.isascii() and value.isdigit():
            page = int(value)
            if 1 <= page <= 10_000:
                accepted[key] = str(page)
    return urlencode(accepted, doseq=False)


def canonical_redirect_path(
    path: str,
    query_lang: str | None,
    query_items: Sequence[tuple[str, str]] = (),
) -> str | None:
    """Return the sole safe Chinese public destination, or ``None``.

    Traditional Chinese is intentionally not an alias.  The landing has no
    public query schema, so selectors and unknown parameters are dropped.
    """

    normalized_path = path.lower().rstrip("/") or "/"
    normalized_lang = str(query_lang or "").strip().lower().replace("_", "-")
    if normalized_path in {"/zh", "/zh-cn", "/zh-sg", "/zh-hans"}:
        return "/zh-hans/"
    if normalized_path == "/zh-hans/catalog":
        query = _canonical_catalog_query(query_items)
        return "/zh-hans/catalog/" + (f"?{query}" if query else "")
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
    missing = sorted(
        key
        for key in ZH_HANS_LANDING_KEYS
        if not isinstance(copy.get(key), str) or not copy[key].strip()
    )
    if missing:
        raise RuntimeError("zh-Hans landing copy is incomplete")
    origin = site_origin.rstrip("/")
    canonical_url = f"{origin}/zh-hans/"
    catalog_url = f"{origin}/zh-hans/catalog/"
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
    <p><a href="{catalog}">{cta}</a></p>
  </main>
</body>
</html>""".format(
        **safe_copy,
        canonical=escape(canonical_url, quote=True),
        catalog=escape(catalog_url, quote=True),
        ru=escape(ru_url, quote=True),
        kk=escape(kk_url, quote=True),
        en=escape(en_url, quote=True),
        schema=schema,
    )


def render_catalog_page(
    *,
    site_origin: str,
    items: Sequence[Opportunity],
    query: str = "",
    kind: str = "",
    page: int = 1,
    load_error: bool = False,
) -> str:
    """Render a local Chinese UI around source-language opportunity data."""

    copy = _load_json(CATALOG_PATH)
    missing = sorted(
        key
        for key in ZH_HANS_CATALOG_KEYS
        if not isinstance(copy.get(key), str) or not copy[key].strip()
    )
    if missing:
        raise RuntimeError("zh-Hans catalog UI copy is incomplete")

    normalized_query = query.strip()[:120]
    normalized_kind = kind.strip().lower()
    if normalized_kind not in _CATALOG_TYPES:
        normalized_kind = ""
    needle = normalized_query.casefold()
    filtered = [
        item
        for item in items
        if (not normalized_kind or item.type.value == normalized_kind)
        and (
            not needle
            or needle
            in " ".join((item.title, item.summary, item.funder or "")).casefold()
        )
    ]
    total_pages = max(1, (len(filtered) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    current_page = min(max(int(page), 1), total_pages)
    start = (current_page - 1) * CATALOG_PAGE_SIZE
    visible = filtered[start : start + CATALOG_PAGE_SIZE]

    origin = site_origin.rstrip("/")
    catalog_url = f"{origin}/zh-hans/catalog/"
    landing_url = f"{origin}/zh-hans/"

    def c(key: str, **values: object) -> str:
        message = str(copy[key])
        placeholders = set(_MESSAGE_PLACEHOLDER_RE.findall(message))
        if placeholders != set(values):
            raise RuntimeError(f"zh-Hans catalog placeholder mismatch for {key}")
        for name, value in values.items():
            message = message.replace("{" + name + "}", str(value))
        return escape(message, quote=True)

    def query_url(target_page: int) -> str:
        values: list[tuple[str, str]] = []
        if normalized_query:
            values.append(("q", normalized_query))
        if normalized_kind:
            values.append(("type", normalized_kind))
        if target_page > 1:
            values.append(("page", str(target_page)))
        suffix = urlencode(values)
        return "/zh-hans/catalog/" + (f"?{suffix}" if suffix else "")

    cards: list[str] = []
    for item in visible:
        profile = provenance_profile(item)
        source_language = str(profile.get("source_language") or "").strip()
        display_language = source_language or str(copy["catalog.unknown_language"])
        lang_attr = (
            source_language
            if re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", source_language)
            else "und"
        )
        source_url = str(item.source_url)
        parsed_url = urlsplit(source_url)
        source_link = ""
        if parsed_url.scheme == "https" and parsed_url.netloc:
            source_link = (
                '<p class="zh-catalog__source"><a rel="noopener noreferrer" '
                f'href="{escape(source_url, quote=True)}">{c("catalog.official_source")}</a></p>'
            )
        summary = (
            f'<p class="zh-catalog__summary" lang="{escape(lang_attr, quote=True)}">'
            f"{escape(item.summary)}</p>"
            if item.summary.strip()
            else ""
        )
        cards.append(
            '<article class="zh-catalog__card">'
            f'<p class="zh-catalog__kind">{c(f"catalog.type.{item.type.value}")}</p>'
            f'<h2 lang="{escape(lang_attr, quote=True)}">{escape(item.title)}</h2>'
            f"{summary}"
            f'<p class="zh-catalog__language">'
            f'{c("catalog.source_language", language=display_language)}</p>'
            f"{source_link}"
            "</article>"
        )

    if load_error:
        result_markup = (
            f'<section role="alert"><h2>{c("catalog.load_error")}</h2></section>'
        )
    elif not cards:
        result_markup = (
            '<section class="zh-catalog__empty">'
            f'<h2>{c("catalog.empty_title")}</h2>'
            f'<p>{c("catalog.empty_body")}</p>'
            "</section>"
        )
    else:
        result_markup = (
            '<section class="zh-catalog__grid">' + "".join(cards) + "</section>"
        )

    pagination: list[str] = []
    if current_page > 1:
        previous_url = escape(query_url(current_page - 1), quote=True)
        pagination.append(
            f'<a rel="prev" href="{previous_url}">{c("catalog.previous")}</a>'
        )
    pagination.append(
        f'<span>{c("catalog.page_label", current=current_page, total=total_pages)}</span>'
    )
    if current_page < total_pages:
        next_url = escape(query_url(current_page + 1), quote=True)
        pagination.append(f'<a rel="next" href="{next_url}">{c("catalog.next")}</a>')

    options = [
        f'<option value="">{c("catalog.type_all")}</option>',
        *[
            '<option value="{value}"{selected}>{label}</option>'.format(
                value=escape(value, quote=True),
                selected=" selected" if normalized_kind == value else "",
                label=c(f"catalog.type.{value}"),
            )
            for value in sorted(_CATALOG_TYPES)
        ],
    ]
    escaped_query = escape(normalized_query, quote=True)
    filter_options = "".join(options)
    pagination_links = "".join(pagination)
    pagination_label = c("catalog.page_label", current=current_page, total=total_pages)
    style = AVDS_CSS + """
.zh-catalog { max-width: 76rem; margin: 0 auto; padding: clamp(1rem, 3vw, 3rem); }
.zh-catalog__header { max-width: 52rem; }
.zh-catalog__filters { display: grid; gap: .75rem; align-items: end; margin: 2rem 0;
  grid-template-columns: minmax(0, 2fr) minmax(10rem, 1fr) auto; }
.zh-catalog__field { display: grid; gap: .35rem; }
.zh-catalog__field input, .zh-catalog__field select, .zh-catalog__filters button {
  min-height: 2.75rem; font: inherit; }
.zh-catalog__grid { display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr)); }
.zh-catalog__card { min-width: 0; padding: 1rem; overflow-wrap: anywhere;
  border: 1px solid var(--avds-border-subtle, #d8dde6); border-radius: .75rem; }
.zh-catalog__card h2 { font-size: 1.125rem; }
.zh-catalog__kind, .zh-catalog__language {
  color: var(--avds-text-muted, #596273); font-size: .875rem; }
.zh-catalog__pagination { display: flex; flex-wrap: wrap; justify-content: center;
  gap: 1rem; margin-top: 2rem; }
@media (max-width: 42rem) { .zh-catalog__filters { grid-template-columns: 1fr; } }
"""
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{c("catalog.title")}</title>
  <meta name="description" content="{c("catalog.description")}">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="{escape(catalog_url, quote=True)}">
  <style>{style}</style>
</head>
<body>
  <main class="zh-catalog" id="main-content">
    <header class="zh-catalog__header">
      <p><a href="{escape(landing_url, quote=True)}">{c("catalog.landing_link")}</a></p>
      <h1>{c("catalog.heading")}</h1>
      <p>{c("catalog.intro")}</p>
      <p>{c("catalog.verification_note")}</p>
    </header>
    <form class="zh-catalog__filters" method="get" action="/zh-hans/catalog/">
      <label class="zh-catalog__field">{c("catalog.search_label")}
        <input name="q" type="search" maxlength="120" value="{escaped_query}"
          placeholder="{c("catalog.search_placeholder")}">
      </label>
      <label class="zh-catalog__field">{c("catalog.type_label")}
        <select name="type">{filter_options}</select>
      </label>
      <button type="submit">{c("catalog.filter_apply")}</button>
    </form>
    <p aria-live="polite">{c("catalog.results_count", count=len(filtered))}</p>
    {result_markup}
    <nav class="zh-catalog__pagination" aria-label="{pagination_label}">
      {pagination_links}
    </nav>
  </main>
</body>
</html>"""
