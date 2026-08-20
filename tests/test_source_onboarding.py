from api.source_onboarding import (
    SOURCE_ONBOARDING_SCHEMA_VERSION,
    source_onboarding_contract,
)


def test_source_onboarding_contract_is_explicit_and_credential_safe():
    payload = source_onboarding_contract(
        "https://qaz.fund",
        ["world_bank_kazakhstan", "grants_gov", "world_bank_kazakhstan"],
    )

    assert payload["schema_version"] == SOURCE_ONBOARDING_SCHEMA_VERSION
    assert payload["active"] == {
        "count": 2,
        "slugs": ["grants_gov", "world_bank_kazakhstan"],
    }
    assert payload["policy"]["credentials_in_public_contract"] is False
    candidates = {row["slug"]: row for row in payload["candidates"]}
    assert candidates["openalex_context"]["status"] == "candidate"
    assert candidates["data_egov_kz"]["status"] == "gated"
    assert candidates["ungm_notices"]["status"] == "gated"
    assert "OAuth" in candidates["ungm_notices"]["access"]
    assert payload["links"]["source_registry"].endswith(
        "/.well-known/source-onboarding.json"
    )


def test_public_source_onboarding_route(monkeypatch):
    from fastapi.testclient import TestClient

    from api import main as api_main

    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    api_main._repository_for_url.cache_clear()
    response = TestClient(api_main.app).get("/.well-known/source-onboarding.json")

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    assert response.json()["schema_version"] == SOURCE_ONBOARDING_SCHEMA_VERSION
