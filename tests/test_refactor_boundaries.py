from datetime import date

from starlette.middleware.gzip import GZipMiddleware

from api import main as api_main
from api.catalog import matches_opportunity_query, slugify_funder
from api.http_policy import (
    PUBLIC_DISCOVERY_CACHE,
    PUBLIC_FAST_CACHE,
    PUBLIC_LONG_CACHE,
    cache_control_for,
    is_machine_route,
)
from api.page_primitives import absolute_href, catalog_path, format_deadline
from api.runtime_config import allowed_hosts, bearer_token
from core.models import Opportunity, OpportunityType
from core.runtime_config import resolve_database_url
from scripts.http_utils import join_url
from sources.parsing import contains_term, infer_tags, unique_normalized


def test_runtime_configuration_normalizes_hosts_and_bearer_tokens(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_ALLOWED_HOSTS", " API.EXAMPLE.KZ, qaz.fund ")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://Public.Example.KZ/base/")

    assert allowed_hosts() == sorted(
        {
            "localhost",
            "127.0.0.1",
            "::1",
            "testserver",
            "qaz.fund",
            "api.example.kz",
            "public.example.kz",
        }
    )
    assert bearer_token("Bearer secret") == "secret"
    assert bearer_token("Basic secret") == ""


def test_database_configuration_has_one_explicit_precedence_rule(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_DB_URL", " sqlite:///primary.db ")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///fallback.db")

    assert resolve_database_url() == "sqlite:///primary.db"
    assert resolve_database_url(" memory ") == "memory"


def test_page_primitives_preserve_root_path_and_locale_contracts():
    assert (
        absolute_href("https://qaz.fund/", "/opportunity/1")
        == "https://qaz.fund/opportunity/1"
    )
    assert absolute_href("", "") == "/"
    assert catalog_path("/fund", "kk") == "/fund/?lang=kk#opportunities"
    assert format_deadline(date(2026, 8, 10), "en", "Rolling") == "Aug 10, 2026"
    assert format_deadline(None, "ru", "Без срока") == "Без срока"


def test_http_policy_keeps_machine_and_cache_surfaces_explicit():
    assert is_machine_route("/api/v1/opportunities") is False
    assert is_machine_route("/opportunities.ndjson") is True
    assert cache_control_for("/opportunities") == PUBLIC_FAST_CACHE
    assert cache_control_for("/site-discovery.json") == PUBLIC_DISCOVERY_CACHE
    assert cache_control_for("/og-image.png") == PUBLIC_LONG_CACHE
    assert cache_control_for("/google-unrelated") is None


def test_application_has_single_gzip_layer_after_policy_extraction():
    assert (
        sum(layer.cls is GZipMiddleware for layer in api_main.app.user_middleware) == 1
    )


def test_source_parsing_primitives_are_ordered_and_boundary_aware():
    assert unique_normalized([" AI ", "ai", "GovTech", ""]) == ["ai", "govtech"]
    assert contains_term("AI-enabled public service", "ai") is True
    assert contains_term("paid program", "ai") is False
    assert infer_tags("AI and public data", {"ai": ("ai",), "media": ("media",)}) == [
        "ai"
    ]


def test_catalog_primitives_keep_search_and_funder_identity_stable():
    item = Opportunity(
        source="astana_hub",
        source_url="https://example.org/program",
        type=OpportunityType.ACCELERATOR,
        title="Kazakhstan AI accelerator",
        summary="Support for local founders",
        tags=["startup"],
    )

    assert matches_opportunity_query(item, "AI founders") is True
    assert matches_opportunity_query(item, "media") is False
    assert (
        slugify_funder("European Bank for Reconstruction & Development")
        == "european-bank-for-reconstruction-development"
    )


def test_operator_url_joining_is_shared_and_query_safe():
    assert (
        join_url("https://qaz.fund/base/", "/coverage?lang=ru")
        == "https://qaz.fund/base/coverage?lang=ru"
    )
