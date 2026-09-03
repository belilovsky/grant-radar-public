"""Fail-closed local ``zh-Hans`` landing for QAZ.FUND.

The public site deliberately renders this bundle locally.  It never calls QMT
at request time: a catalog is an immutable release input, not a live service
dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs/qazstack/zh-hans/catalog.json"
MANIFEST_PATH = ROOT / "docs/qazstack/zh-hans/manifest.json"
OWNER_RECEIPT_PATH = ROOT / "docs/qazstack/zh-hans/owner-receipt.json"
QAZSTACK_CONTRACT_SHA256 = (
    "c309401ed21a2488ab61478d6db7380544b07bf83b8cf35399f128b0888af031"
)


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


def zh_hans_readiness(*, require_owner_receipt: bool) -> dict[str, str | bool]:
    """Validate release inputs without exposing catalog text or credentials."""

    if not CATALOG_PATH.is_file() or not MANIFEST_PATH.is_file():
        raise RuntimeError("zh-Hans catalog bundle is missing")
    manifest = _load_json(MANIFEST_PATH)
    catalog = _load_json(CATALOG_PATH)
    required_keys = {"title", "description", "eyebrow", "headline", "body", "cta"}
    if set(catalog) != required_keys or any(not str(catalog[key]).strip() for key in required_keys):
        raise RuntimeError("zh-Hans catalog coverage is incomplete")
    if manifest.get("schema_version") != "qaz-fund.zh-hans-manifest.v1":
        raise RuntimeError("zh-Hans manifest schema is invalid")
    if manifest.get("project") != "qaz-fund" or manifest.get("target_lang") != "zh-Hans":
        raise RuntimeError("zh-Hans manifest project or target is invalid")
    if manifest.get("catalog_sha256") != _sha256(CATALOG_PATH):
        raise RuntimeError("zh-Hans catalog digest does not match its manifest")
    if manifest.get("qazstack_contract_sha256") != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("zh-Hans manifest has an unexpected QazStack contract")
    if _wheel_contract_sha256() != QAZSTACK_CONTRACT_SHA256:
        raise RuntimeError("installed QazStack locale contract drifted")
    if manifest.get("coverage") != {"required": 6, "translated": 6}:
        raise RuntimeError("zh-Hans manifest does not prove full public coverage")
    receipt_ok = False
    if OWNER_RECEIPT_PATH.is_file():
        receipt = _load_json(OWNER_RECEIPT_PATH)
        receipt_ok = (
            receipt.get("catalog_sha256") == manifest["catalog_sha256"]
            and receipt.get("bundle_sha256") == manifest.get("bundle_sha256")
            and receipt.get("owner") == "belilovsky"
            and receipt.get("verification") == "verified"
        )
    if require_owner_receipt and not receipt_ok:
        raise RuntimeError("zh-Hans owner receipt is missing or does not match the catalog")
    return {
        "enabled": zh_hans_enabled(),
        "catalog_sha256": str(manifest["catalog_sha256"]),
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
