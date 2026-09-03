from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from api import main as api_main
from api import zh_hans


def test_dark_catalog_is_complete_but_not_owner_approved(monkeypatch) -> None:
    monkeypatch.delenv("QAZ_FUND_ZH_HANS_ENABLED", raising=False)
    readiness = zh_hans.zh_hans_readiness(require_owner_receipt=False)

    assert readiness["enabled"] is False
    assert readiness["owner_receipt_verified"] is False
    with pytest.raises(RuntimeError, match="owner receipt"):
        zh_hans.zh_hans_readiness(require_owner_receipt=True)


def test_zh_hans_route_stays_dark_when_flag_is_false(monkeypatch) -> None:
    monkeypatch.setenv("QAZ_FUND_ZH_HANS_ENABLED", "false")
    client = TestClient(api_main.app)

    assert client.get("/zh-hans/").status_code == 404
    assert client.get("/zh-cn/", follow_redirects=False).status_code == 404


def test_alias_normalization_has_one_safe_destination() -> None:
    assert zh_hans.canonical_redirect_path("/ZH-CN/", None) == "/zh-hans/"
    assert zh_hans.canonical_redirect_path("/", "zh-SG") == "/zh-hans/"
    assert zh_hans.canonical_redirect_path("/", "zh-TW") is None
    assert zh_hans.canonical_redirect_path("/media", "zh") is None
