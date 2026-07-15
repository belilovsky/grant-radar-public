from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from scripts.deepseek_enrich_content import call_qazcompute, summary_is_decision_ready


def test_qazcompute_enrichment_preserves_decision_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "secret"
        assert request.headers["X-Caller"] == "qaz-fund"
        assert request.url.path == "/api/v1/tasks/opportunity-enrich"
        return httpx.Response(
            200,
            json={
                "schema_version": "opportunity_enrich.v1",
                "status": "available",
                "provider": "llm_gateway",
                "model": "test-model",
                "quality_tier": "estimated",
                "decision_ready": False,
                "fallback_reason": None,
                "omitted_capabilities": [],
                "results": [
                    {
                        "id": "opp-1",
                        "summary_ru": "Описание возможности.",
                        "entities": {"regions": ["kazakhstan"]},
                        "quality_flags": [],
                        "evidence": [],
                    }
                ],
            },
        )

    async def run() -> dict[str, object]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await call_qazcompute(
                client=client,
                api_key="secret",
                base_url="https://compute.example",
                item=SimpleNamespace(
                    id="opp-1",
                    title="Kazakhstan grant",
                    summary="Open for teams.",
                    source="example",
                    tags=["grant"],
                    eligibility=[],
                ),
                detail_text="Official source text.",
            )

    result = asyncio.run(run())

    assert result["summary_ru"] == "Описание возможности."
    assert result["entities"] == {"regions": ["kazakhstan"]}
    assert result["runtime"] == {
        "schema_version": "opportunity_enrich.v1",
        "status": "available",
        "provider": "llm_gateway",
        "model": "test-model",
        "quality_tier": "estimated",
        "decision_ready": False,
        "fallback_reason": None,
        "omitted_capabilities": [],
    }


def test_qazcompute_enrichment_rejects_contract_drift() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"schema_version": "unknown"})
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await call_qazcompute(
                client=client,
                api_key="secret",
                base_url="https://compute.example",
                item=SimpleNamespace(
                    id="opp-1",
                    title="Grant",
                    summary="Summary",
                    source="example",
                    tags=[],
                    eligibility=[],
                ),
                detail_text="",
            )

    try:
        asyncio.run(run())
    except ValueError as exc:
        assert "invalid opportunity enrichment contract" in str(exc)
    else:
        raise AssertionError("contract drift must fail closed")


def test_qazcompute_enrichment_rejects_mismatched_item_id() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "schema_version": "opportunity_enrich.v1",
                    "status": "degraded",
                    "provider": "local_rules",
                    "model": "shadow",
                    "quality_tier": "degraded",
                    "decision_ready": False,
                    "results": [{"id": "another-opportunity"}],
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await call_qazcompute(
                client=client,
                api_key="secret",
                base_url="https://compute.example",
                item=SimpleNamespace(
                    id="opp-1",
                    title="Grant",
                    summary="Summary",
                    source="example",
                    tags=[],
                    eligibility=[],
                ),
                detail_text="",
            )

    with pytest.raises(ValueError, match="mismatched opportunity id"):
        asyncio.run(run())


def test_public_summary_requires_explicit_decision_readiness() -> None:
    enrichment = {
        "summary_ru": "Описание возможности.",
        "runtime": {
            "status": "available",
            "quality_tier": "estimated",
            "decision_ready": False,
        },
    }

    assert not summary_is_decision_ready(enrichment)
    enrichment["runtime"] = {
        "status": "available",
        "quality_tier": "estimated",
        "decision_ready": True,
    }
    assert summary_is_decision_ready(enrichment)


def test_public_summary_rejects_degraded_runtime_even_with_ready_flag() -> None:
    enrichment = {
        "summary_ru": "Описание возможности.",
        "runtime": {
            "status": "degraded",
            "quality_tier": "degraded",
            "decision_ready": True,
        },
    }

    assert not summary_is_decision_ready(enrichment)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "unknown", "invalid runtime status"),
        ("quality_tier", "shadow", "invalid quality tier"),
        ("decision_ready", "false", "invalid decision-ready flag"),
    ],
)
def test_qazcompute_enrichment_rejects_invalid_runtime_metadata(
    field: str,
    value: object,
    message: str,
) -> None:
    payload = {
        "schema_version": "opportunity_enrich.v1",
        "status": "available",
        "provider": "llm_gateway",
        "model": "test-model",
        "quality_tier": "estimated",
        "decision_ready": False,
        "results": [{"id": "opp-1"}],
    }
    payload[field] = value

    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, json=payload)
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await call_qazcompute(
                client=client,
                api_key="secret",
                base_url="https://compute.example",
                item=SimpleNamespace(
                    id="opp-1",
                    title="Grant",
                    summary="Summary",
                    source="example",
                    tags=[],
                    eligibility=[],
                ),
                detail_text="",
            )

    with pytest.raises(ValueError, match=message):
        asyncio.run(run())


def test_qazcompute_enrichment_rejects_degraded_publication_readiness() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "schema_version": "opportunity_enrich.v1",
                    "status": "degraded",
                    "provider": "local_rules",
                    "model": "opportunity-rules-v1",
                    "quality_tier": "degraded",
                    "decision_ready": True,
                    "results": [{"id": "opp-1"}],
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await call_qazcompute(
                client=client,
                api_key="secret",
                base_url="https://compute.example",
                item=SimpleNamespace(
                    id="opp-1",
                    title="Grant",
                    summary="Summary",
                    source="example",
                    tags=[],
                    eligibility=[],
                ),
                detail_text="",
            )

    with pytest.raises(ValueError, match="inconsistent publication readiness"):
        asyncio.run(run())
