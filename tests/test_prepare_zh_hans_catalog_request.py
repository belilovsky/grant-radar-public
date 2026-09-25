from __future__ import annotations

import argparse
import json

import pytest

from api import zh_hans
from scripts import prepare_zh_hans_catalog_request as request_builder


def _arguments(tmp_path) -> argparse.Namespace:
    source = tmp_path / "source.json"
    reference = tmp_path / "reference.json"
    copy = {key: f"copy {key}" for key in zh_hans.ZH_HANS_REQUIRED_KEYS}
    source.write_text(json.dumps(copy), encoding="utf-8")
    reference.write_text(json.dumps(copy), encoding="utf-8")
    return argparse.Namespace(
        product_source_sha="1" * 40,
        qmt_source_sha="2" * 40,
        qmt_image_digest="sha256:" + "3" * 64,
        qmt_runtime_receipt_digest="sha256:" + "4" * 64,
        qmt_migration_receipt_digest="sha256:" + "5" * 64,
        prompt_version="prompt-1",
        glossary_version="glossary-1",
        tm_version="tm-1",
        source=source,
        reference=reference,
    )


def test_request_is_exactly_source_bound(tmp_path) -> None:
    request = request_builder.build_request(_arguments(tmp_path))

    assert request["project"] == "qaz-fund"
    assert request["sourceLang"] == "ru"
    assert request["targetLang"] == "zh-Hans"
    assert request["requiredKeys"] == sorted(
        zh_hans.ZH_HANS_REQUIRED_KEYS, key=zh_hans._utf16_sort_key
    )
    assert request["publicRoutes"] == list(zh_hans.ZH_HANS_PUBLIC_ROUTES)
    assert request["productBinding"]["sourceSha"] == "1" * 40
    assert request["qmtRelease"]["imageDigest"] == "sha256:" + "3" * 64


def test_request_rejects_a_partial_source_catalog(tmp_path) -> None:
    arguments = _arguments(tmp_path)
    partial = json.loads(arguments.source.read_text(encoding="utf-8"))
    partial.pop(next(iter(partial)))
    arguments.source.write_text(json.dumps(partial), encoding="utf-8")

    with pytest.raises(ValueError, match="source-derived public key set"):
        request_builder.build_request(arguments)


def test_request_rejects_source_reference_placeholder_drift(tmp_path) -> None:
    arguments = _arguments(tmp_path)
    source = json.loads(arguments.source.read_text(encoding="utf-8"))
    reference = json.loads(arguments.reference.read_text(encoding="utf-8"))
    source["catalog.results_count"] = "Results: {count}"
    reference["catalog.results_count"] = "Results: {total}"
    arguments.source.write_text(json.dumps(source), encoding="utf-8")
    arguments.reference.write_text(json.dumps(reference), encoding="utf-8")

    with pytest.raises(ValueError, match="placeholders differ"):
        request_builder.build_request(arguments)


def test_checked_in_source_and_reference_cover_the_runtime_contract(tmp_path) -> None:
    arguments = _arguments(tmp_path)
    arguments.source = request_builder.SOURCE_PATH
    arguments.reference = request_builder.REFERENCE_PATH

    request = request_builder.build_request(arguments)

    assert len(request["sourceCatalog"]) == len(zh_hans.ZH_HANS_REQUIRED_KEYS)
