from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from api import funder_page as funder_page_module
from api import main as api_main
from api import opportunity_og
from api import opportunity_page as opportunity_page_module
from api.dashboard import dashboard_copy
from api.insights_page import _bar_chart, _source_label, build_insights_snapshot
from api.opportunity_og import _amount_text, _facts, _source_text
from core.db import SqlRepository
from core.models import (
    Opportunity,
    OpportunityDetail,
    OpportunityDetailSection,
    OpportunityMetadataField,
    OpportunityType,
)
from core.public_contract import to_opportunity_v1
from sources.base import GrantRecord


def _with_generated_assets(client: TestClient, response) -> str:
    urls = re.findall(r'(?:href|src)="([^"]*/assets/generated/[^"]+)"', response.text)
    return response.text + "".join(client.get(url).text for url in urls)


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", raising=False)
    monkeypatch.delenv("GRANT_RADAR_SEMANTIC_SEARCH_URL", raising=False)
    for name in (
        "APP_REVISION",
        "APP_SOURCE_DIRTY",
        "APP_IMAGE_DIGEST",
        "APP_ARTIFACT_DIGEST",
        "APP_BUILT_AT",
        "APP_DEPLOYED_AT",
    ):
        monkeypatch.delenv(name, raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def test_current_catalog_uses_kazakhstan_business_date(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setattr(api_main, "public_today", lambda: date(2026, 7, 28))
    api_main._cache.extend(
        [
            Opportunity(
                source="astana_hub",
                source_url="https://example.org/expired",
                type=OpportunityType.GRANT,
                title="Kazakhstan AI programme expired yesterday",
                tags=["kazakhstan", "ai"],
                score=0.9,
                deadline=date(2026, 7, 27),
            ),
            Opportunity(
                source="astana_hub",
                source_url="https://example.org/current",
                type=OpportunityType.GRANT,
                title="Kazakhstan AI programme closing today",
                tags=["kazakhstan", "ai"],
                score=0.9,
                deadline=date(2026, 7, 28),
            ),
        ]
    )

    current = api_main._cached_current_catalog_items("en")

    assert [item.title for item in current] == ["Kazakhstan AI programme closing today"]


def test_known_unsafe_publication_is_absent_from_all_public_surfaces(monkeypatch):
    _reset_api_state(monkeypatch)
    blocked = Opportunity(
        source="opportunity_desk",
        source_url=(
            "https://opportunitydesk.org/2026/06/30/"
            "ifc-women-led-business-grant-2026/"
        ),
        type=OpportunityType.GRANT,
        title="International Finance Corporation Women-Led Business Grant 2026",
        summary="Secondary publication for a confirmed unsafe programme.",
        tags=["kazakhstan", "grant"],
        score=0.9,
        deadline=date(2099, 8, 20),
    )
    api_main._cache.append(blocked)
    client = TestClient(api_main.app)

    catalog = client.get(
        "/opportunities?limit=5000&min_score=0&include_irrelevant=true"
    )
    detail = client.get(f"/opportunity/{blocked.id}?lang=ru")
    sitemap = client.get("/sitemap.xml")

    assert catalog.status_code == 200
    assert catalog.json() == []
    assert detail.status_code == 404
    assert str(blocked.id) not in sitemap.text


def test_root_renders_service_landing(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/")

    assert response.status_code == 200
    asset_urls = re.findall(
        r'(?:href|src)="([^"]*/assets/generated/[^"]+)"', response.text
    )
    assets = {url: client.get(url).text for url in asset_urls}
    styles = "".join(body for url, body in assets.items() if url.endswith(".css"))
    scripts = "".join(body for url, body in assets.items() if url.endswith(".js"))
    rendered = response.text + styles + scripts
    assert len(response.content) < 100_000
    assert len(asset_urls) == 2
    assert '<html lang="ru"' in response.text
    assert 'data-avds="grant-radar"' in response.text
    assert 'data-av-theme="light"' in response.text
    assert 'data-lang="ru"' in response.text
    assert 'data-avds-component="admin-shell"' in response.text
    assert 'data-avds-component="hero-band"' in response.text
    assert "<h1>QAZ.FUND</h1>" in response.text
    assert "Каталог программ поддержки для Казахстана" in response.text
    assert (
        "Открытые программы с источником, сроком и условиями, которые можно "
        "проверить до подачи." in response.text
    )
    assert "Стартапам" in response.text
    assert "Поиск по названию" in response.text
    assert "Программы в Казахстане" in response.text
    assert "qaz-fund-ornamental-background-1920x1080.webp" in styles
    assert "radial-gradient(circle at 92% 6%" not in styles
    assert "#F0C64D" not in styles
    assert 'data-avds-component="quick-links-rail"' not in response.text
    assert 'data-avds-component="public-summary-strip"' not in response.text
    assert '<strong id="metric-total">' not in response.text
    assert '<strong id="metric-strong"' not in response.text
    assert 'id="workspace-filter"' not in response.text
    assert 'id="profile-builder"' not in response.text
    assert 'data-avds-pattern="applicant-journey"' in response.text
    assert 'id="compare-selected"' in response.text
    assert 'id="export-csv"' in response.text
    assert 'id="export-deadlines"' in response.text
    assert 'id="share-view"' in response.text
    assert 'data-compare-opportunity="${opportunityId}"' in rendered
    assert "const COMPARE_LIMIT = 4;" in rendered
    assert "function renderComparisonControls()" in rendered
    assert 'data-avds-component="discovery-library"\n      hidden' in response.text
    assert 'data-avds-component="trust-library"\n      hidden' in response.text
    assert 'id="filter-disclosure"' in response.text
    assert 'id="opportunities-list"' in response.text
    assert 'data-avds-component="opportunity-card"' in rendered
    assert 'data-avds-pattern="catalog-card"' in rendered
    assert 'data-mobile-view="opportunities"' in rendered
    assert 'data-mobile-view="sources"' not in rendered
    assert 'data-mobile-action="saved"' not in rendered
    assert 'data-mobile-action="filters"' in rendered
    assert 'href="/?lang=kk"' in response.text
    assert 'href="/?lang=ru"' in response.text
    assert 'href="/?lang=en"' in response.text
    assert 'href="/docs?lang=ru"' not in response.text
    assert 'href="/status?lang=ru"' not in response.text
    assert 'href="/terms?lang=ru"' in response.text
    assert 'href="/data-policy?lang=ru"' in response.text
    assert 'href="/attribution?lang=ru"' in response.text
    assert 'rel="canonical" href="http://testserver/?lang=ru"' in response.text
    assert 'type="application/ld+json"' in response.text
    assert '"@type": "CollectionPage"' in response.text
    assert '"@type": "FAQPage"' not in response.text
    assert (
        'property="og:image" content="http://testserver/og-image.png?lang=ru"'
        in response.text
    )
    assert (
        'property="og:image:alt" content="QAZ.FUND: найти, проверить, сравнить '
        'и подготовить программу поддержки"' in response.text
    )
    assert 'name="twitter:card" content="summary_large_image"' in response.text
    assert "startAnalytics" not in rendered
    assert "googletagmanager.com" not in response.text
    assert "mc.yandex.ru" not in response.text
    assert "clarity.ms" not in response.text
    assert "syncFilterDisclosureForViewport" in rendered
    assert "function publicDateISO" in rendered
    assert "getTimezoneOffset" not in rendered


def test_root_rejects_untrusted_host_header(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/", headers={"host": "evil.example"})

    assert response.status_code == 400


def test_root_landing_preserves_root_path_prefix(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app, root_path="/grant-radar")

    response = client.get("/")

    assert response.status_code == 200
    assert 'data-api-base="/grant-radar"' in response.text
    assert 'href="/grant-radar/terms?lang=ru"' in response.text
    assert 'href="/grant-radar/?lang=ru"' in response.text
    assert 'href="/grant-radar/?lang=en"' in response.text
    assert (
        'rel="canonical" href="http://testserver/grant-radar/?lang=ru"' in response.text
    )
    assert 'href="/grant-radar/opportunities?limit=20"' not in response.text


def test_docs_exposes_swagger_with_return_link(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/docs")
    head_response = client.head("/docs")

    assert response.status_code == 200
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("text/html")
    assert "QAZ.FUND API" in response.text
    assert "SwaggerUIBundle" in response.text
    assert '<html lang="ru" data-avds="grant-radar"' in response.text
    assert '<span class="qazfund-docs-title">Документация API</span>' in response.text
    assert (
        '<main id="swagger-ui" data-avds-component="api-docs"></main>' in response.text
    )
    assert 'data-avds="grant-radar" data-av-theme="light"' in response.text
    assert "--av-color-primary: var(--av-color-blue-700);" in response.text
    assert 'meta name="description"' in response.text
    assert 'rel="canonical" href="http://testserver/docs?lang=ru"' in response.text
    assert 'href="/?lang=ru"' in response.text
    assert "Вернуться на сайт" in response.text
    assert "url: '/openapi.json'" in response.text
    assert ".swagger-ui .opblock .opblock-summary" in response.text
    assert ".swagger-ui .opblock-control-arrow" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert ".swagger-ui .opblock.opblock-get .opblock-summary-method" in response.text
    assert ".swagger-ui .info .url" in response.text
    assert ".swagger-ui .json-schema-2020-12-expand-deep-button" in response.text
    assert "box-sizing: border-box;" in response.text
    assert "grid-template-columns: minmax(0, 1fr) auto;" in response.text
    assert "grid-column: 2;" in response.text
    assert "grid-column: 1 / -1;" in response.text
    assert "min-width: var(--av-control-height-lg);" in response.text
    assert ".qazfund-docs-langs a" in response.text
    assert "display: inline-flex;" in response.text
    assert '"deepLinking": false' in response.text
    assert 'href="/docs?lang=kk" lang="kk">KAZ</a>' in response.text
    assert 'href="/docs?lang=ru" lang="ru" aria-current="page">RU</a>' in response.text
    assert 'href="/docs?lang=en" lang="en">EN</a>' in response.text


def test_docs_supports_english_return_link(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/docs?lang=en", headers={"Accept-Encoding": "identity"})

    assert response.status_code == 200
    assert '<html lang="en" data-avds="grant-radar"' in response.text
    assert '<span class="qazfund-docs-title">API documentation</span>' in response.text
    assert 'rel="canonical" href="http://testserver/docs?lang=en"' in response.text
    assert 'href="/?lang=en"' in response.text
    assert "Back to site" in response.text
    assert response.headers["content-length"] == str(len(response.content))


def test_docs_supports_kazakh_shell_and_language_switch(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/docs?lang=kk", headers={"Accept-Encoding": "identity"})

    assert response.status_code == 200
    assert '<html lang="kk" data-avds="grant-radar"' in response.text
    assert '<span class="qazfund-docs-title">API құжаттамасы</span>' in response.text
    assert 'rel="canonical" href="http://testserver/docs?lang=kk"' in response.text
    assert 'href="/?lang=kk"' in response.text
    assert 'href="/docs?lang=kk" lang="kk" aria-current="page">KAZ</a>' in response.text
    assert 'href="/docs?lang=ru" lang="ru">RU</a>' in response.text
    assert 'href="/docs?lang=en" lang="en">EN</a>' in response.text


def test_docs_preserves_root_path_prefix(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app, root_path="/grant-radar")

    response = client.get("/docs")

    assert response.status_code == 200
    assert 'href="/grant-radar/?lang=ru"' in response.text
    assert "url: '/grant-radar/openapi.json'" in response.text


def test_seo_excerpt_trims_read_more_and_length():
    value = (
        "Глобальный конкурс для команд из Центральной Азии по цифровому образованию "
        "и ИИ. Читать далее подробности на сайте организатора с большим длинным "
        "хвостом, который не должен попадать в мета-описание."
    )

    excerpt = opportunity_page_module._seo_excerpt(value, max_length=120)

    assert "Читать далее" not in excerpt
    assert len(excerpt) <= 123
    assert excerpt.startswith("Глобальный конкурс")
    assert (
        opportunity_page_module._clean_summary_text("Текст. Читать далее хвост")
        == "Текст."
    )
    assert (
        opportunity_page_module._clean_summary_text(
            "Закупочная возможность в Казахстане: Закупочная возможность в "
            "Казахстане: консультационные услуги. Проверьте техническое задание.",
            title="Закупочная возможность в Казахстане: консультационные услуги",
        )
        == "Проверьте техническое задание."
    )


def test_sections_markup_strips_repeated_title_prefix():
    detail = OpportunityDetail(
        source="unesco_iite",
        source_url="https://example.org/source",
        type=OpportunityType.TENDER,
        title="Закупочная возможность в Казахстане: консультационные услуги",
        summary="Проверьте техническое задание.",
        detail_fetch_status="structured_only",
        detail_sections=[
            OpportunityDetailSection(
                heading="Источник",
                text=(
                    "Закупочная возможность в Казахстане: Закупочная возможность в "
                    "Казахстане: консультационные услуги. Проверьте техническое задание."
                ),
            )
        ],
    )
    markup = opportunity_page_module._sections_markup(
        detail,
        "Описание",
        title=detail.title,
    )

    assert "Проверьте техническое задание." in markup
    assert (
        "Закупочная возможность в Казахстане: Закупочная возможность в Казахстане"
        not in markup
    )


def test_sections_markup_splits_source_wall_of_text_into_paragraphs():
    sentence = (
        "Программа поддерживает технологические команды и исследовательские проекты. "
    )
    detail = OpportunityDetail(
        source="science_fund",
        source_url="https://example.org/source",
        type=OpportunityType.GRANT,
        title="Программа поддержки",
        summary="Краткое описание.",
        detail_sections=[OpportunityDetailSection(heading="Обзор", text=sentence * 18)],
    )

    markup = opportunity_page_module._sections_markup(
        detail,
        "Описание",
        title=detail.title,
    )

    assert markup.count("<p>") >= 3


def test_sections_markup_collapses_long_source_text():
    sentence = (
        "Официальный источник описывает условия программы, критерии участия, "
        "порядок подачи и перечень документов. "
    )
    detail = OpportunityDetail(
        source="science_fund",
        source_url="https://example.org/source",
        type=OpportunityType.GRANT,
        title="Программа поддержки",
        summary="Краткое описание.",
        detail_sections=[
            OpportunityDetailSection(heading="Выдержка с источника", text=sentence * 28)
        ],
    )

    markup = opportunity_page_module._sections_markup(
        detail,
        "Описание",
        title=detail.title,
        expand_label="Показать выдержку",
    )

    assert 'class="section-card source-disclosure"' in markup
    assert 'data-avds-component="evidence-disclosure"' in markup
    assert 'data-avds-pattern="evidence-disclosure"' in markup
    assert '<span class="source-disclosure-title">Описание</span>' in markup
    assert "Показать выдержку" in markup
    assert markup.count("<p>") >= 4


def test_sections_markup_removes_duplicate_and_taxonomy_only_sections():
    summary = "Программа поддерживает образовательные команды из Казахстана."
    detail = OpportunityDetail(
        source="science_fund",
        source_url="https://example.org/source",
        type=OpportunityType.GRANT,
        title="Образовательная программа",
        summary=summary,
        eligibility=["education_organization"],
        detail_sections=[
            OpportunityDetailSection(heading="Обзор", text=summary),
            OpportunityDetailSection(
                heading="Обзор",
                text=f"{summary} Читать далее на странице программы.",
            ),
            OpportunityDetailSection(
                heading="Кто может подать заявку",
                text="education_organization",
            ),
            OpportunityDetailSection(
                heading="",
                text="Служебная выдержка с навигацией официального сайта.",
            ),
        ],
    )

    markup = opportunity_page_module._sections_markup(
        detail,
        "Выдержка с источника",
        title=detail.title,
        expand_label="Показать выдержку",
    )

    assert markup.count(">Обзор<") == 1
    assert "education organization" not in markup
    assert 'class="section-card source-disclosure"' in markup


def test_working_brief_uses_only_available_fields_and_keeps_source_boundary():
    detail = OpportunityDetail(
        source="kazakhstan_domestic",
        source_url="https://example.kz/program",
        application_url="https://example.kz/program/apply",
        type=OpportunityType.GRANT,
        title="Программа поддержки бизнеса",
        summary="Поддержка проектов в Казахстане.",
        metadata=[
            OpportunityMetadataField(key="region", value="kazakhstan"),
            OpportunityMetadataField(key="amount", value="10 000 000 KZT"),
        ],
    )
    copy = dashboard_copy("ru")

    brief = opportunity_page_module._working_brief(
        detail,
        title=detail.title,
        summary=detail.summary,
        source_label="Официальная программа",
        format_label="Грант",
        deadline_label="Без срока",
        copy=copy,
    )

    assert "QAZ.FUND – сведения о программе" in brief
    assert "Организатор или источник: Официальная программа" in brief
    assert "Регион: Казахстан" in brief
    assert "Сумма: 10 000 000 KZT" in brief
    assert "Официальный источник: https://example.kz/program" in brief
    assert "Подача: https://example.kz/program/apply" in brief
    assert "Проверьте на официальном источнике условия" in brief


def test_opportunity_action_path_uses_source_specific_editorial_steps():
    detail = OpportunityDetail(
        source="global_training_opportunities",
        source_url="https://example.org/flta",
        type=OpportunityType.FELLOWSHIP,
        title="Fulbright FLTA",
        summary="Программа для преподавателей английского языка.",
        deadline=date(2026, 8, 15),
        raw={
            "i18n": {
                "ru": {
                    "prepare_items": [
                        {
                            "title": "Сверьте список документов",
                            "text": "Используйте перечень на портале IIE.",
                        }
                    ],
                    "application_step_titles": ["Заполните анкету IIE"],
                    "application_steps": ["Откройте официальную форму FLTA."],
                }
            }
        },
    )
    copy = dashboard_copy("ru")

    prepare = opportunity_page_module._prepare_markup(detail, copy=copy, lang="ru")
    apply = opportunity_page_module._apply_markup(
        detail=detail,
        has_application_url=True,
        copy=copy,
        lang="ru",
    )

    assert "Сверьте список документов" in prepare
    assert "Соберите исследовательский пакет" not in prepare
    assert "Заполните анкету IIE" in apply
    assert "Подготовьте описание проекта" not in apply


def test_root_prefers_public_base_url_for_canonical_links(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://qaz.fund")
    client = TestClient(api_main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'rel="canonical" href="https://qaz.fund/?lang=ru"' in response.text
    assert (
        'rel="alternate" hreflang="en" href="https://qaz.fund/?lang=en"'
        in response.text
    )
    assert 'property="og:url" content="https://qaz.fund/?lang=ru"' in response.text


def test_root_dashboard_does_not_reference_removed_compare_items_symbol(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/")
    rendered = _with_generated_assets(client, response)

    assert response.status_code == 200
    assert "sort(compareItems)" not in rendered
    assert "sort(comparePriorityItems)" in rendered


def test_root_supports_explicit_english_dashboard(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/?lang=en")
    rendered = _with_generated_assets(client, response)

    assert response.status_code == 200
    assert '<html lang="en"' in response.text
    assert (
        "<title>QAZ.FUND – open support programs for Kazakhstan</title>"
        in response.text
    )
    assert "A working navigator for support in Kazakhstan" in response.text
    assert "Find open programs and turn them into a clear next step." in response.text
    assert "For startups" in response.text
    assert "Search by name" in response.text
    assert "Kazakhstan programs" in response.text
    assert "Theme" in response.text
    assert "Region" in response.text
    assert "Timing" in response.text
    assert "All regions" in response.text
    assert "Rolling" in response.text
    assert "Open card" in rendered
    assert 'rel="canonical" href="http://testserver/?lang=en"' in response.text
    assert 'data-avds-component="quick-links-rail"' not in response.text
    assert 'data-avds-component="public-summary-strip"' not in response.text
    assert 'href="/docs?lang=en"' not in response.text
    assert 'href="/status?lang=en"' not in response.text
    assert 'id="workspace-filter"' not in response.text
    assert 'id="profile-builder"' not in response.text


def test_root_supports_explicit_kazakh_dashboard_route(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/?lang=kk")
    rendered = _with_generated_assets(client, response)

    assert response.status_code == 200
    assert '<html lang="kk"' in response.text
    assert 'data-lang="kk"' in response.text
    assert 'href="/?lang=kk"' in response.text
    assert 'hreflang="kk"' in response.text
    assert 'lang="kk"' in response.text
    assert ">KAZ</a>" in response.text
    assert 'aria-current="page"' in response.text
    assert 'rel="canonical" href="http://testserver/?lang=kk"' in response.text
    assert "Қазақстандағы қолдауды іздеу навигаторы" in response.text
    assert (
        "Ашық бағдарламаларды тауып, келесі қадамды түсінікті етіңіз." in response.text
    )
    assert "Стартаптарға" in response.text
    assert "Атауы бойынша іздеу" in response.text
    assert "Қазақстандағы бағдарламалар" in response.text
    assert 'data-avds-component="quick-links-rail"' not in response.text
    assert 'data-avds-component="public-summary-strip"' not in response.text
    assert 'data-mobile-view="sources"' not in rendered
    assert 'data-mobile-action="saved"' not in rendered


def test_root_head_is_available(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.head("/")

    assert response.status_code == 200


def test_public_dedupe_prefers_latest_discovered_at_for_equal_records():
    older = Opportunity(
        source="google_org_ai_opportunity",
        source_url="https://example.org/opportunity",
        type=OpportunityType.GRANT,
        title="AI Opportunity",
        summary="Same summary",
        score=0.8,
        discovered_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        raw={"external_id": "GOOG-1"},
    )
    newer = Opportunity(
        source="google_org_ai_opportunity",
        source_url="https://example.org/opportunity",
        type=OpportunityType.GRANT,
        title="AI Opportunity",
        summary="Same summary",
        score=0.8,
        discovered_at=datetime(2026, 7, 7, tzinfo=timezone.utc),
        raw={"external_id": "GOOG-1"},
    )

    deduped = api_main._dedupe_public_items([older, newer], content_lang="en")

    assert len(deduped) == 1
    assert deduped[0].discovered_at == newer.discovered_at


def test_public_dedupe_uses_undp_notice_url_when_reference_changes():
    original = Opportunity(
        source="undp_procurement",
        source_url="https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=42",
        type=OpportunityType.TENDER,
        title="Climate risk expert",
        summary="UNDP Kazakhstan procurement notice.",
        score=0.7,
        discovered_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        raw={"external_id": "UNDP-KAZ-42"},
    )
    revised = original.model_copy(
        update={
            "score": 0.8,
            "discovered_at": datetime(2026, 7, 7, tzinfo=timezone.utc),
            "raw": {"external_id": "UNDP-KAZ-42,1"},
        }
    )

    deduped = api_main._dedupe_public_items([original, revised], content_lang="en")

    assert len(deduped) == 1
    assert deduped[0].raw["external_id"] == "UNDP-KAZ-42,1"


def test_public_dedupe_uses_grants_gov_opportunity_number_across_revisions():
    older = Opportunity(
        source="grants_gov",
        source_url="https://www.grants.gov/search-results-detail/363033",
        type=OpportunityType.GRANT,
        title="Regional AI program",
        score=0.8,
        discovered_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        raw={"number": "DFOP0018586"},
    )
    revised = older.model_copy(
        update={
            "source_url": "https://www.grants.gov/search-results-detail/363227",
            "discovered_at": datetime(2026, 7, 17, tzinfo=timezone.utc),
        }
    )

    deduped = api_main._dedupe_public_items([older, revised], content_lang="en")

    assert len(deduped) == 1
    assert str(deduped[0].source_url).endswith("/363227")


def test_marketing_endpoints_are_exposed(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/open",
                type=OpportunityType.GRANT,
                title="Open science commercialization",
                summary="Open call for commercialization teams in Kazakhstan.",
                funder="Science Fund",
                tags=["science", "kazakhstan"],
                score=0.91,
            ),
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/forecast",
                type=OpportunityType.TENDER,
                title="Forecast project support",
                summary="Program roadmap for innovation and applied research.",
                funder="Science Fund",
                tags=["science", "forecast"],
                score=0.73,
            ),
        ]
    )
    client = TestClient(api_main.app)

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert robots.headers["content-type"].startswith("text/plain")
    assert robots.headers["cache-control"].startswith("public, max-age=300")
    assert "User-agent: *" in robots.text
    assert "Allow: /" in robots.text
    assert "Disallow: /health" in robots.text
    assert "Disallow: /ready" in robots.text
    assert "Disallow: /refresh" in robots.text
    assert "Sitemap: http://testserver/sitemap.xml" in robots.text
    robots_head = client.head("/robots.txt")
    assert robots_head.status_code == 200
    assert robots_head.headers["content-type"].startswith("text/plain")
    assert robots_head.headers["cache-control"].startswith("public, max-age=300")

    llms = client.get("/llms.txt")
    assert llms.status_code == 200
    assert llms.headers["content-type"].startswith("text/plain")
    assert llms.headers["cache-control"].startswith("public, max-age=300")
    assert "# QAZ.FUND" in llms.text
    assert "Home: http://testserver/" in llms.text
    assert "Sitemap: http://testserver/sitemap.xml" in llms.text
    assert "API docs: http://testserver/docs" in llms.text
    assert "OpenAPI schema: http://testserver/openapi.json" in llms.text
    assert "Site discovery JSON: http://testserver/site-discovery.json" in llms.text
    assert (
        "Ecosystem integration JSON: "
        "http://testserver/.well-known/qdev-ecosystem.json"
    ) in llms.text
    assert (
        "Release metadata JSON: " "http://testserver/.well-known/release.json"
    ) in llms.text
    assert (
        "QazStack consumer contract: "
        "http://testserver/.well-known/qazstack-consumer.json"
    ) in llms.text
    assert (
        "AV DS 4 UI contract: " "http://testserver/.well-known/avds-ui-contract.json"
    ) in llms.text
    assert (
        "Source onboarding contract: "
        "http://testserver/.well-known/source-onboarding.json"
    ) in llms.text
    assert (
        "Kazakhstan data-route contract: "
        "http://testserver/.well-known/kazakhstan-data-routes.json"
    ) in llms.text
    assert "Source status page: http://testserver/status" in llms.text
    assert "Catalog insights: http://testserver/insights" in llms.text
    assert "Media page: http://testserver/media" in llms.text
    assert "Terms of use: http://testserver/terms" in llms.text
    assert "Data policy: http://testserver/data-policy" in llms.text
    assert "Official Kazakhstan data routes: http://testserver/data-routes" in llms.text
    assert "Data attribution: http://testserver/attribution" in llms.text
    assert "Coverage JSON: http://testserver/coverage" in llms.text
    assert "Opportunities JSON: http://testserver/opportunities" in llms.text
    assert "Opportunities NDJSON: http://testserver/opportunities.ndjson" in llms.text
    assert (
        "Compact Opportunities NDJSON: "
        "http://testserver/opportunities.ndjson?compact=true"
    ) in llms.text
    assert "## AI consumption guidance" in llms.text
    assert "Prefer compact Opportunities NDJSON for bulk discovery reads" in llms.text
    assert "Opportunity detail JSON: /opportunities/{id}?lang=kk|ru|en" in llms.text
    assert (
        "Opportunity history JSON: "
        "http://testserver/opportunities/{id}/history.json?lang=kk|ru|en&limit={n}"
    ) in llms.text
    assert "Digest JSON: http://testserver/digest" in llms.text
    assert (
        "Comparison JSON template: "
        "http://testserver/compare.json?ids={id},{id}&lang=ru|kk|en" in llms.text
    )
    assert "Opportunity page: /opportunity/{id}?lang=kk|ru|en" in llms.text
    assert "Funder page: /funder/{slug}?lang=kk|ru|en" in llms.text
    assert "Insights page: /insights?lang=kk|ru|en" in llms.text
    assert "Media page: /media?lang=kk|ru|en" in llms.text
    assert "Media JSON: /media.json?lang=kk|ru|en" in llms.text
    assert "Media JSON Feed: /media/feed.json?lang=kk|ru|en" in llms.text
    assert "Media RSS: /media/rss.xml?lang=kk|ru|en" in llms.text
    assert "Opportunities filters: q, source, lifecycle, region, tag" in llms.text
    assert "evidence_state=sourced means that a direct public source link" in llms.text
    llms_head = client.head("/llms.txt")
    assert llms_head.status_code == 200
    assert llms_head.headers["content-type"].startswith("text/plain")
    assert llms_head.headers["cache-control"].startswith("public, max-age=300")

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    openapi_paths = openapi.json()["paths"]
    assert "/refresh" not in openapi_paths
    operation_ids = [
        operation["operationId"]
        for path_item in openapi_paths.values()
        for method, operation in path_item.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    assert len(operation_ids) == len(set(operation_ids))

    discovery = client.get("/site-discovery.json")
    assert discovery.status_code == 200
    assert discovery.headers["content-type"].startswith("application/json")
    assert discovery.headers["cache-control"].startswith("public, max-age=300")
    data = discovery.json()
    assert data["site"] == "QAZ.FUND"
    assert data["home"] == "http://testserver/"
    assert data["openapi"] == "http://testserver/openapi.json"
    assert data["versioned_api"] == "http://testserver/api/v1"
    assert data["api_v1_schema"] == "http://testserver/api/v1/schema"
    assert data["languages"] == ["kk", "ru", "en"]
    assert data["contracts"]["qazpipe"].endswith("/.well-known/qazpipe-source.json")
    assert data["contracts"]["qazcompute"].endswith(
        "/.well-known/qazcompute-profiles.json"
    )
    assert data["contracts"]["kazakhstan_data_routes"].endswith(
        "/.well-known/kazakhstan-data-routes.json"
    )
    assert data["routes"]["data_routes"] == "/data-routes?lang={lang}"
    assert data["routes"]["opportunity_history"] == (
        "/opportunities/{id}/history.json?lang={lang}&limit={n}"
    )
    assert data["routes"]["media_citation"] == (
        "/media/v1/opportunities/{id}/citation.txt?lang={lang}"
    )
    assert data["data_endpoints"]["api_v1_opportunities"] == (
        "http://testserver/api/v1/opportunities"
    )
    assert data["data_endpoints"]["data_routes"] == "http://testserver/data-routes"
    assert data["media_endpoints"]["feed_json"] == (
        "http://testserver/media/v1/feed.json"
    )
    assert data["ai_consumption"]["preferred_bulk_export"] == (
        "http://testserver/api/v1/opportunities.ndjson"
    )
    assert data["ai_consumption"]["preferred_legacy_bulk_export"] == (
        "http://testserver/opportunities.ndjson?compact=true"
    )
    assert "machine-readable media feeds" in data["capabilities"]
    assert "qazpipe pull-source contract" in data["capabilities"]
    assert "qazcompute profile contract" in data["capabilities"]
    discovery_head = client.head("/site-discovery.json")
    assert discovery_head.status_code == 200
    assert discovery_head.headers["content-type"].startswith("application/json")
    assert discovery_head.headers["cache-control"].startswith("public, max-age=300")

    qazstack_contract = client.get("/.well-known/qazstack-consumer.json")
    assert qazstack_contract.status_code == 200
    assert qazstack_contract.json()["schema_version"] == "qazstack-consumer-v1"
    assert qazstack_contract.json()["qazstack_version"] == "1.41.2"
    assert qazstack_contract.json()["source_revision"] == (
        "986cfca3779f74c0f734ed174e7a28c944fd30f7"
    )
    assert qazstack_contract.json()["integration_mode"] == "python-package"
    assert {
        "opportunity-public-contract",
        "opportunity-ranking-evaluation",
    }.issubset(set(qazstack_contract.json()["primitives"]))
    assert qazstack_contract.json()["evidence"]["environment"] == "production"
    assert qazstack_contract.json()["evidence"]["source_revision"] == (
        qazstack_contract.json()["source_revision"]
    )
    assert client.head("/.well-known/qazstack-consumer.json").status_code == 200

    avds_contract = client.get("/.well-known/avds-ui-contract.json")
    assert avds_contract.status_code == 200
    assert avds_contract.json()["schema_version"] == "avds-ui-contract-v1"
    assert avds_contract.json()["avds_source"] == {
        "site": "https://avds.digital",
        "package": "@sgeo/ui-kit",
        "package_version": "4.7.0",
        "version": "4.7.0",
        "source_revision": "aa91d2ec56c64d56df3270b805f7d0d18ed84246",
    }
    assert avds_contract.json()["runtime_neutral_patterns"] == {
        "package": "@av/patterns",
        "version": "0.2.0",
        "source_revision": "ea32d93aa05fa6faa4278ccc030c1d3567c1de35",
        "source": (
            "https://github.com/belilovsky/av-platform-core/tree/"
            "ea32d93aa05fa6faa4278ccc030c1d3567c1de35/packages/patterns"
        ),
        "adopted": [
            "evidence-summary",
            "filter-state-summary",
            "decision-summary",
            "evidence-disclosure",
            "action-path",
        ],
        "rendering": "server-rendered-local-adapter",
        "calculation_ownership": "qaz-fund",
    }
    assert client.head("/.well-known/avds-ui-contract.json").status_code == 200

    notifications = client.get("/.well-known/notification-contract.json")
    assert notifications.status_code == 200
    assert notifications.json()["schema_version"] == "notification-v1"
    assert notifications.json()["status"] == "not_enabled"
    assert notifications.json()["delivery"]["worker_running"] is False
    assert notifications.json()["calendar_export"] == {
        "enabled": True,
        "delivery": "user_initiated_ics_download",
        "server_side_schedule": False,
        "description": (
            "A dated application workspace can export local calendar reminders; "
            "this is not a subscription or background notification."
        ),
    }
    assert notifications.json()["identity"] == {
        "anonymous_read_access": True,
        "authenticated_owner": False,
        "server_side_profile": False,
        "cross_device_sync": False,
        "local_browser_storage_only": True,
    }
    assert notifications.json()["consent"] == {
        "collection_enabled": False,
        "version": None,
        "purpose": None,
        "frequency": None,
        "withdrawal_path": "not_available_until_activation",
    }
    assert notifications.json()["storage"]["server_side_saved_views"] is False
    assert notifications.json()["public_behavior"]["subscription_ui"] is False
    assert notifications.json()["public_behavior"]["account_ui"] is False
    assert notifications.json()["public_behavior"]["sync_ui"] is False
    assert (
        notifications.json()["public_behavior"]["calendar_export_is_subscription"]
        is False
    )
    assert client.head("/.well-known/notification-contract.json").status_code == 200

    ecosystem = client.get("/.well-known/qdev-ecosystem.json")
    assert ecosystem.status_code == 200
    ecosystem_payload = ecosystem.json()
    assert ecosystem_payload["integrations"]["qazstack"]["status"] == ("runtime-proven")
    assert ecosystem_payload["integrations"]["qazpipe"]["status"] == ("producer-ready")
    assert ecosystem_payload["integrations"]["qazlake"]["direct_write"] is False
    assert ecosystem_payload["integrations"]["qazgeo"]["status"] == (
        "deferred-no-geometry"
    )
    assert ecosystem_payload["integrations"]["qazcompute"]["status"] == (
        "local-runtime-proven"
    )
    assert ecosystem_payload["integrations"]["qazcompute"]["decision_ready"] is False
    assert (
        ecosystem_payload["integrations"]["notifications"]["delivery_enabled"] is False
    )
    assert client.head("/.well-known/qdev-ecosystem.json").status_code == 200

    qazpipe = client.get("/.well-known/qazpipe-source.json")
    assert qazpipe.status_code == 200
    assert qazpipe.headers["cache-control"].startswith("public, max-age=60")
    qazpipe_payload = qazpipe.json()
    assert qazpipe_payload["schema_version"] == "qazpipe-pull-source-v1"
    assert qazpipe_payload["direction"] == "outbound-read-only"
    assert qazpipe_payload["endpoints"]["bulk_ndjson"] == (
        "http://testserver/api/v1/opportunities.ndjson"
    )
    assert qazpipe_payload["qazlake_handoff"]["direct_write"] is False
    assert client.head("/.well-known/qazpipe-source.json").status_code == 200

    qazcompute = client.get("/.well-known/qazcompute-profiles.json")
    assert qazcompute.status_code == 200
    assert qazcompute.headers["cache-control"].startswith("public, max-age=60")
    qazcompute_payload = qazcompute.json()
    assert qazcompute_payload["schema_version"] == "qazcompute-profile-contract-v1"
    assert qazcompute_payload["execution"]["runtime_status"] == "proven"
    assert qazcompute_payload["execution"]["remote_execution_active"] is False
    assert qazcompute_payload["execution"]["decision_ready"] is False
    assert {
        profile["schema_version"] for profile in qazcompute_payload["profiles"]
    } == {
        "evidence_readiness.v1",
        "deadline_anomaly.v1",
        "source_freshness.v1",
        "duplicate_cluster.v1",
    }
    assert client.head("/.well-known/qazcompute-profiles.json").status_code == 200

    release = client.get("/.well-known/release.json")
    assert release.status_code == 200
    assert release.json() == {
        "schemaVersion": "qaz-fund-release-v1",
        "service": "qaz-fund",
        "revision": "development",
        "deployed_at": None,
        "sourceSha": "development",
        "sourceDirty": True,
        "imageDigest": None,
        "artifactDigest": None,
        "builtAt": None,
        "deployedAt": None,
    }
    assert release.headers["cache-control"] == "no-store"
    assert client.head("/.well-known/release.json").status_code == 200
    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/x-icon")
    assert favicon.headers["cache-control"].startswith("public, max-age=3600")
    assert favicon.content.startswith(b"\x00\x00\x01\x00")
    favicon_head = client.head("/favicon.ico")
    assert favicon_head.status_code == 200
    assert favicon_head.headers["content-type"].startswith("image/x-icon")
    assert favicon_head.headers["cache-control"].startswith("public, max-age=3600")

    brand_symbol = client.get("/assets/branding/qaz-fund-symbol.svg")
    assert brand_symbol.status_code == 200
    assert brand_symbol.headers["content-type"].startswith("image/svg+xml")
    assert brand_symbol.headers["cache-control"].startswith("public, max-age=3600")
    assert 'aria-label="QAZ.FUND ornamental symbol"' in brand_symbol.text
    assert client.head("/assets/branding/qaz-fund-symbol.svg").status_code == 200

    brand_background = client.head(
        "/assets/branding/qaz-fund-ornamental-background-1920x1080.webp"
    )
    assert brand_background.status_code == 200
    assert brand_background.headers["content-type"].startswith("image/webp")

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert sitemap.headers["content-type"].startswith("application/xml")
    assert sitemap.headers["cache-control"].startswith("public, max-age=300")
    assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in sitemap.text
    sitemap_head = client.head("/sitemap.xml")
    assert sitemap_head.status_code == 200
    assert sitemap_head.headers["cache-control"].startswith("public, max-age=300")
    assert sitemap_head.headers["content-type"].startswith("application/xml")
    assert "<loc>http://testserver/?lang=ru</loc>" in sitemap.text
    assert (
        '<xhtml:link rel="alternate" hreflang="en" href="http://testserver/?lang=en" />'
        in sitemap.text
    )
    assert (
        f"<loc>http://testserver/opportunity/{api_main._cache[0].id}?lang=ru</loc>"
        in sitemap.text
    )
    assert (
        '<xhtml:link rel="alternate" hreflang="en" href="http://testserver/'
        f'opportunity/{api_main._cache[0].id}?lang=en" />'
    ) in sitemap.text
    assert "<loc>http://testserver/funder/science-fund?lang=ru</loc>" in sitemap.text
    assert (
        '<xhtml:link rel="alternate" hreflang="en" href="http://testserver/'
        'funder/science-fund?lang=en" />'
    ) in sitemap.text


def test_release_metadata_accepts_only_an_immutable_git_revision(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("APP_REVISION", "A" * 40)
    monkeypatch.setenv("APP_SOURCE_DIRTY", "false")
    monkeypatch.setenv("APP_IMAGE_DIGEST", "sha256:" + "b" * 64)
    monkeypatch.setenv("APP_ARTIFACT_DIGEST", "sha256:" + "c" * 64)
    monkeypatch.setenv("APP_BUILT_AT", "2026-07-15T17:48:00Z")
    monkeypatch.setenv("APP_DEPLOYED_AT", "2026-07-15T17:51:42Z")
    client = TestClient(api_main.app)

    release = client.get("/.well-known/release.json")

    assert release.json() == {
        "schemaVersion": "qaz-fund-release-v1",
        "service": "qaz-fund",
        "revision": "a" * 40,
        "deployed_at": "2026-07-15T17:51:42Z",
        "sourceSha": "a" * 40,
        "sourceDirty": False,
        "imageDigest": "sha256:" + "b" * 64,
        "artifactDigest": "sha256:" + "c" * 64,
        "builtAt": "2026-07-15T17:48:00Z",
        "deployedAt": "2026-07-15T17:51:42Z",
    }

    monkeypatch.setenv("APP_REVISION", "not-a-release")
    assert client.get("/.well-known/release.json").json()["revision"] == ("development")

    monkeypatch.setenv("APP_REVISION", "d" * 40)
    monkeypatch.delenv("APP_SOURCE_DIRTY", raising=False)
    assert client.get("/.well-known/release.json").json()["sourceDirty"] is True


def test_marketing_endpoints_prefer_public_base_url(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://qaz.fund")
    api_main._cache.extend(
        [
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/open",
                type=OpportunityType.GRANT,
                title="Open science commercialization",
                summary="Open call for commercialization teams in Kazakhstan.",
                funder="Science Fund",
                tags=["science", "kazakhstan"],
                score=0.91,
            )
        ]
    )
    client = TestClient(api_main.app)

    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap: https://qaz.fund/sitemap.xml" in robots.text

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "<loc>https://qaz.fund/?lang=ru</loc>" in sitemap.text
    assert (
        f"https://qaz.fund/opportunity/{api_main._cache[0].id}?lang=ru" in sitemap.text
    )
    assert "http://testserver" not in sitemap.text


def test_sitemap_reuses_single_stored_items_pass(monkeypatch):
    _reset_api_state(monkeypatch)
    sample = Opportunity(
        id=uuid4(),
        source="sample",
        source_url="https://example.org/opportunity",
        type=OpportunityType.GRANT,
        title="Sample opportunity",
        summary="Sample summary",
        funder="Sample funder",
        funder_slug="sample-funder",
        tags=["kazakhstan"],
        languages=["en"],
        score=10.0,
        discovered_at=datetime.now(timezone.utc),
        raw={},
    )
    calls = {"stored_items": 0}

    def fake_stored_items(content_lang: str = "en"):
        calls["stored_items"] += 1
        return [sample]

    monkeypatch.setattr(api_main, "_stored_items", fake_stored_items)
    client = TestClient(api_main.app)

    response = client.get("/sitemap.xml")
    cached_response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert cached_response.status_code == 200
    assert calls["stored_items"] == 1


def test_sitemap_excludes_archived_opportunities(monkeypatch):
    _reset_api_state(monkeypatch)
    current = Opportunity(
        source="science_fund",
        source_url="https://example.org/current",
        type=OpportunityType.GRANT,
        title="Current Kazakhstan science grant",
        summary="Open science opportunity for Kazakhstan teams.",
        tags=["kazakhstan", "science"],
        deadline=date.today() + timedelta(days=20),
        score=0.8,
    )
    archived = current.model_copy(
        update={
            "id": uuid4(),
            "source_url": "https://example.org/archived",
            "title": "Archived Kazakhstan science grant",
            "deadline": date.today() - timedelta(days=1),
        }
    )
    api_main._cache.extend([current, archived])
    client = TestClient(api_main.app)

    sitemap = client.get("/sitemap.xml")

    assert sitemap.status_code == 200
    assert str(current.id) in sitemap.text
    assert str(archived.id) not in sitemap.text


def test_security_headers_are_added(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]


def test_health_head_is_available(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.head("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"


def test_health_uses_in_memory_cache_without_database(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.append(
        Opportunity(
            source="memory",
            source_url="https://example.org/memory",
            type=OpportunityType.GRANT,
            title="Memory item",
            tags=["ai"],
            score=0.7,
        )
    )

    client = TestClient(api_main.app)
    assert client.get("/health").json() == {"status": "ok", "items": 1}


def test_ready_reports_memory_backend(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "backend": "memory", "items": 0}


def test_ready_head_is_available(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.head("/ready")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"


def test_ready_reports_database_backend(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'ready.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)
    SqlRepository(db_url).upsert(
        Opportunity(
            source="ready",
            source_url="https://example.org/ready",
            type=OpportunityType.GRANT,
            title="Ready item",
            tags=["ai"],
            score=0.7,
        )
    )
    client = TestClient(api_main.app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "backend": "database", "items": 1}


def test_opportunities_deduplicate_existing_database_rows_by_external_id(
    tmp_path, monkeypatch
):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'dedup.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)
    repo = SqlRepository(db_url)
    row_one = repo._row_from_record(  # noqa: SLF001 - targeted duplicate fixture.
        Opportunity(
            source="unicef_kazakhstan",
            source_url="https://example.org/tenders",
            type=OpportunityType.TENDER,
            title="English title",
            summary="Short summary",
            score=0.6,
            raw={"external_id": "RFP/KAZA/2026/001"},
        )
    )
    row_one.id = "legacy-unicef-1"
    row_one.dedup_key = "legacy-unicef-1"
    row_two = repo._row_from_record(  # noqa: SLF001 - targeted duplicate fixture.
        Opportunity(
            source="unicef_kazakhstan",
            source_url="https://example.org/tender-results",
            type=OpportunityType.TENDER,
            title="Русский заголовок",
            summary="Более полное описание для локальной выдачи.",
            score=0.8,
            raw={
                "external_id": "RFP/KAZA/2026/001",
                "i18n": {"ru": {"title": "Русский заголовок"}},
            },
        )
    )
    row_two.id = "legacy-unicef-2"
    row_two.dedup_key = "legacy-unicef-2"
    with repo._Session() as session:  # noqa: SLF001 - targeted duplicate fixture.
        session.add(row_one)
        session.add(row_two)
        session.commit()

    client = TestClient(api_main.app)
    response = client.get(
        "/opportunities?lang=ru&limit=5000&include_irrelevant=true&min_score=0"
    )

    assert response.status_code == 200
    data = response.json()
    items = [item for item in data if item["source"] == "unicef_kazakhstan"]
    assert len(items) == 1
    assert items[0]["title"] == "Русский заголовок"
    assert items[0]["source_url"] == "https://example.org/tender-results"


def test_ready_hides_backend_errors(monkeypatch):
    _reset_api_state(monkeypatch)

    def broken_repository():
        raise RuntimeError("postgresql://secret@example/db")

    monkeypatch.setattr(api_main, "_configured_repository", broken_repository)
    client = TestClient(api_main.app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "error", "backend": "database"}}


def test_ready_head_hides_backend_errors(monkeypatch):
    _reset_api_state(monkeypatch)

    def broken_repository():
        raise RuntimeError("postgresql://secret@example/db")

    monkeypatch.setattr(api_main, "_configured_repository", broken_repository)
    client = TestClient(api_main.app)

    response = client.head("/ready")

    assert response.status_code == 503
    assert response.text == ""


def test_sources_catalog_lists_registered_parsers(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/sources")

    assert response.status_code == 200
    data = response.json()
    slugs = {item["slug"] for item in data}
    assert {"grants_gov", "astana_hub", "internews"}.issubset(slugs)
    assert {"opportunity_desk", "fundsforngos"}.issubset(slugs)
    assert {
        "kazakhstan_domestic_support",
        "kazakhstan_watch",
        "eeas_kazakhstan",
        "world_bank_kazakhstan",
        "adb_kazakhstan",
        "isdb_project_procurement",
        "ebrd_ecepp_procurement",
        "erasmus_kazakhstan",
        "google_cloud_startup",
        "microsoft_founders_hub",
        "aws_activate",
        "nvidia_inception",
        "cloudflare_startups",
        "mongodb_startups",
        "unicef_kazakhstan",
        "google_org_ai_opportunity",
        "unesco_iite",
        "undp_procurement",
    }.issubset(slugs)
    by_slug = {item["slug"]: item for item in data}
    assert by_slug["kazakhstan_watch"]["base_url"] == "https://qaz.fund/"
    assert by_slug["undp_procurement"]["name"] == "UNDP Procurement"
    assert by_slug["isdb_project_procurement"]["name"] == "IsDB Procurement"
    assert by_slug["ebrd_ecepp_procurement"]["name"] == "EBRD ECEPP Procurement"
    assert (
        by_slug["google_org_ai_opportunity"]["name"] == "Google.org AI Opportunity Fund"
    )
    assert all(item["enabled"] is True for item in data)


def test_coverage_reports_source_counts(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="world_bank_kazakhstan",
                source_url="https://example.org/world-bank",
                type=OpportunityType.TENDER,
                title="Kazakhstan AI project",
                summary="Kazakhstan digital public sector program",
                tags=["kazakhstan", "ai", "govtech"],
                deadline=date(2027, 1, 1),
                score=0.8,
            ),
            Opportunity(
                source="eeas_kazakhstan",
                source_url="https://example.org/eeas-expired",
                type=OpportunityType.GRANT,
                title="Expired Kazakhstan call",
                summary="Kazakhstan civil society",
                tags=["kazakhstan", "grant"],
                deadline=date(2026, 1, 1),
                score=0.7,
            ),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/coverage")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["items"] == 2
    assert data["enabled_sources"] >= 9
    assert data["fresh_sources"] >= 2
    assert data["fresh_sources"] <= data["enabled_sources"]
    assert data["stale_sources"] == 0
    assert data["unknown_freshness_sources"] >= 1
    assert data["unknown_freshness_sources"] <= data["enabled_sources"]
    sources = {item["slug"]: item for item in data["sources"]}
    assert sources["world_bank_kazakhstan"]["items"] == 1
    assert sources["world_bank_kazakhstan"]["relevant_open_items"] == 1
    assert sources["world_bank_kazakhstan"]["freshness_status"] == "fresh"
    assert isinstance(sources["world_bank_kazakhstan"]["age_hours"], float)
    assert sources["eeas_kazakhstan"]["items"] == 1
    assert sources["eeas_kazakhstan"]["open_items"] == 0
    head_response = client.head("/coverage")
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("application/json")


def test_public_status_page_renders_coverage_without_operator_details(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://qaz.fund")
    api_main._cache.append(
        Opportunity(
            source="world_bank_kazakhstan",
            source_url="https://example.org/status-item",
            type=OpportunityType.GRANT,
            title="Kazakhstan digital grant",
            summary="Digital program for Kazakhstan.",
            tags=["kazakhstan", "digital"],
            deadline=date.today() + timedelta(days=30),
            score=0.8,
        )
    )
    client = TestClient(api_main.app)

    response = client.get("/status?lang=ru")

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    assert "Статус источников" in response.text
    assert 'aria-label="Сводка состояния источников"' in response.text
    assert 'data-av-theme="light" data-theme="light"' in response.text
    assert 'data-avds-component="status-page"' in response.text
    assert 'data-avds-component="hero-band"' in response.text
    assert 'data-avds-component="data-table"' in response.text
    assert 'class="status-topbar"' in response.text
    assert 'class="lang-switch"' in response.text
    assert 'href="/status?lang=en"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert "min-height:var(--av-control-height-lg);" in response.text
    assert ".status-topbar .back" in response.text
    assert (
        ".site-footer-nav a { min-width:var(--av-control-height-lg); "
        "justify-content:center; }" in response.text
    )
    assert (
        "--av-container-dashboard: clamp(1280px, calc(100vw - 96px), 2240px);"
        in response.text
    )
    assert "Всемирный банк Казахстан" in response.text
    assert "Последняя проверка" in response.text
    assert 'rel="canonical" href="https://qaz.fund/status?lang=ru"' in response.text
    assert "error" not in response.text.lower()
    assert client.head("/status?lang=en").status_code == 200


def test_operator_page_is_noindex_and_never_embeds_admin_token(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "server-only-secret")
    client = TestClient(api_main.app)

    response = client.get("/operator?lang=ru")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert 'name="robots" content="noindex,nofollow"' in response.text
    assert "Контроль источников" in response.text
    assert 'data-av-theme="light" data-theme="light"' in response.text
    assert 'class="operator-brand"' in response.text
    assert '<label for="token">Служебный токен</label>' in response.text
    assert 'class="lang-switch"' in response.text
    assert 'href="/operator?lang=en"' in response.text
    assert "X-Grant-Radar-Admin-Token" in response.text
    assert "sessionStorage" in response.text
    assert 'autocomplete="username"' in response.text
    assert 'autocomplete="current-password"' in response.text
    assert ".auth-controls > :is(input, button)" in response.text
    assert ".catalog-link" in response.text
    assert (
        ".operator-brand { min-height: var(--av-control-height-lg); align-items: center; }"
        in response.text
    )
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert "server-only-secret" not in response.text
    head_response = client.head("/operator?lang=en")
    assert head_response.status_code == 200
    assert head_response.headers["cache-control"] == "no-store"


def test_source_freshness_marks_old_and_missing_timestamps():
    old = datetime.now(timezone.utc) - timedelta(hours=96)

    missing = api_main._source_freshness(None)
    assert missing["freshness_status"] == "unknown"
    assert missing["age_hours"] is None
    assert missing["qazcompute_source_freshness"]["schema_version"] == (
        "source_freshness.v1"
    )
    assert missing["qazcompute_source_freshness"]["decision_ready"] is False
    assert api_main._source_freshness(old)["freshness_status"] == "stale"
    assert (
        api_main._source_freshness(datetime.now(timezone.utc))["freshness_status"]
        == "fresh"
    )


def test_source_coverage_uses_successful_empty_source_check(monkeypatch):
    _reset_api_state(monkeypatch)
    checked_at = datetime.now(timezone.utc) - timedelta(hours=2)
    rows = api_main._source_coverage([], {"canada_cfli_ca": checked_at})
    source = next(row for row in rows if row["slug"] == "canada_cfli_ca")

    assert source["items"] == 0
    assert source["last_discovered_at"] is None
    assert source["last_checked_at"] == checked_at.isoformat()
    assert source["freshness_basis"] == "source_check"
    assert source["freshness_status"] == "fresh"


def test_source_coverage_prefers_newer_successful_check(monkeypatch):
    _reset_api_state(monkeypatch)
    discovered_at = datetime.now(timezone.utc) - timedelta(days=5)
    checked_at = datetime.now(timezone.utc) - timedelta(hours=1)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/old-record",
        type=OpportunityType.GRANT,
        title="Older indexed record",
        summary="Previously indexed Kazakhstan opportunity.",
        tags=["kazakhstan"],
        discovered_at=discovered_at,
    )

    rows = api_main._source_coverage([item], {"world_bank_kazakhstan": checked_at})
    source = next(row for row in rows if row["slug"] == "world_bank_kazakhstan")

    assert source["last_discovered_at"] == discovered_at.isoformat()
    assert source["last_checked_at"] == checked_at.isoformat()
    assert source["freshness_basis"] == "source_check"
    assert source["freshness_status"] == "fresh"


def test_source_coverage_marks_partial_check_for_review(monkeypatch):
    _reset_api_state(monkeypatch)
    checked_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    rows = api_main._source_coverage(
        [],
        {"kazakhstan_domestic_support": checked_at},
        {"kazakhstan_domestic_support": "partial"},
    )
    source = next(row for row in rows if row["slug"] == "kazakhstan_domestic_support")

    assert source["last_checked_at"] == checked_at.isoformat()
    assert source["last_check_status"] == "partial"
    assert source["freshness_status"] == "watch"


def test_funders_endpoint_aggregates_lifecycle(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/open",
                type=OpportunityType.GRANT,
                title="Open science commercialization",
                summary="Open call for research commercialization teams.",
                funder="Science Fund",
                tags=["science", "commercialization", "kazakhstan"],
                deadline=date(2027, 2, 1),
                score=0.91,
            ),
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/pipeline",
                type=OpportunityType.GRANT,
                title="Pipeline university innovation program",
                summary="Project pipeline for university innovation teams.",
                funder="Science Fund",
                tags=["science", "project_pipeline", "kazakhstan"],
                score=0.72,
            ),
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/closed",
                type=OpportunityType.GRANT,
                title="Closed lab capacity grant",
                summary="Recently closed lab support.",
                funder="Science Fund",
                tags=["science"],
                deadline=date(2026, 1, 1),
                score=0.52,
            ),
            Opportunity(
                source="science_fund",
                source_url="https://example.org/science/awarded",
                type=OpportunityType.TENDER,
                title="Awarded research equipment lot",
                summary="Award notice for research equipment.",
                funder="Science Fund",
                tags=["science"],
                score=0.4,
                raw={"status": "Awarded"},
            ),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/funders", params={"limit": 10})

    assert response.status_code == 200
    data = response.json()
    science_fund = next(item for item in data if item["slug"] == "science-fund")
    assert science_fund["name"] == "Science Fund"
    assert science_fund["total_items"] == 4
    assert science_fund["open_items"] == 1
    assert science_fund["forecast_items"] == 1
    assert science_fund["closed_items"] == 1
    assert science_fund["awarded_items"] == 1
    assert science_fund["current_items"] == 1
    assert science_fund["top_types"][0] == "grant"
    assert "science" in science_fund["top_tags"]
    assert science_fund["sources"][0]["slug"] == "science_fund"

    opportunities = client.get(
        "/opportunities", params={"include_irrelevant": True}
    ).json()
    by_title = {item["title"]: item for item in opportunities}
    assert by_title["Open science commercialization"]["funder_slug"] == "science-fund"
    assert by_title["Pipeline university innovation program"]["lifecycle"] == "forecast"


def test_funders_head_uses_live_dashboard_cache_policy(monkeypatch):
    _reset_api_state(monkeypatch)
    response = TestClient(api_main.app).head("/funders")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_api_lists_persisted_opportunities_when_database_is_configured(
    tmp_path, monkeypatch
):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        GrantRecord(
            source="grants_gov",
            external_id="API-1",
            title="AI education grant",
            url="https://example.org/api-1",
            description="Open to Central Asia schools",
            tags=["ai", "education"],
            score=0.9,
        )
    )
    repo.upsert(
        GrantRecord(
            source="internews",
            external_id="API-2",
            title="Media program",
            url="https://example.org/api-2",
            description="For media",
            tags=["media"],
            score=0.4,
        )
    )
    repo.upsert(
        Opportunity(
            source="astana_hub",
            source_url="https://example.org/expired",
            type=OpportunityType.GRANT,
            title="Expired Kazakhstan education grant",
            summary="Kazakhstan grant",
            tags=["kz", "education"],
            deadline=date(2026, 1, 1),
            score=0.9,
        )
    )
    repo.upsert(
        GrantRecord(
            source="grants_gov",
            external_id="API-US-TRIBAL",
            title="AI3 Action Institute - Artificial Intelligence for American Indians",
            url="https://example.org/api-us-tribal",
            description="US domestic tribal grant",
            tags=["ai", "us", "federal"],
            score=0.9,
        )
    )

    client = TestClient(api_main.app)

    assert client.get("/health").json() == {"status": "ok", "items": 4}

    response = client.get("/opportunities", params={"tag": "ai", "min_score": 0.5})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["source"] == "grants_gov"
    assert data[0]["title"] == "AI education grant"
    assert data[0]["summary"] == "Open to Central Asia schools"
    assert data[0]["tags"] == ["ai", "education"]
    assert data[0]["type"] == "grant"

    audit_response = client.get(
        "/opportunities",
        params={"tag": "ai", "min_score": 0.5, "include_irrelevant": True},
    )
    assert audit_response.status_code == 200
    audit_data = audit_response.json()
    assert len(audit_data) == 1
    assert audit_data[0]["title"] == "AI education grant"

    open_response = client.get(
        "/opportunities",
        params={"min_score": 0.5, "deadline_after": "2026-05-22"},
    )
    assert open_response.status_code == 200
    assert all(
        item["title"] != "Expired Kazakhstan education grant"
        for item in open_response.json()
    )

    paged_response = client.get(
        "/opportunities",
        params={"include_irrelevant": True, "limit": 2, "offset": 1},
    )
    assert paged_response.status_code == 200
    paged_data = paged_response.json()
    assert len(paged_data) == 2
    assert all(
        item["title"]
        != "AI3 Action Institute - Artificial Intelligence for American Indians"
        for item in paged_data
    )


def test_opportunities_support_server_search_filters_and_count_headers(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="astana_hub",
                source_url="https://example.org/kazakhstan-ai-accelerator",
                type=OpportunityType.ACCELERATOR,
                title="Kazakhstan AI accelerator",
                summary="Acceleration program for local startups.",
                tags=["kazakhstan", "ai", "startup"],
                deadline=date.today() + timedelta(days=40),
                score=0.9,
            ),
            Opportunity(
                source="internews",
                source_url="https://example.org/central-asia-media",
                type=OpportunityType.GRANT,
                title="Central Asia media grant",
                summary="Media support for Central Asia organizations.",
                tags=["central_asia", "media"],
                deadline=date.today() + timedelta(days=5),
                score=0.8,
            ),
            Opportunity(
                source="grants_gov",
                source_url="https://example.org/global-award",
                type=OpportunityType.GRANT,
                title="Completed global award",
                summary="Historical award notice.",
                tags=["global"],
                score=0.4,
                raw={"status": "Awarded"},
            ),
        ]
    )
    client = TestClient(api_main.app)
    params = {
        "q": "AI accelerator",
        "source": "astana_hub",
        "lifecycle": "open",
        "region": "kazakhstan",
        "include_irrelevant": True,
    }

    response = client.get("/opportunities", params=params)

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Kazakhstan AI accelerator"]
    assert response.headers["x-total-count"] == "1"
    assert response.headers["x-result-count"] == "1"

    head_response = client.head("/opportunities", params=params)
    assert head_response.status_code == 200
    assert head_response.headers["x-total-count"] == "1"
    assert head_response.headers["x-result-count"] == "1"
    assert (
        client.get("/opportunities", params={"lifecycle": "invalid"}).status_code == 422
    )


def test_opportunities_use_internal_semantic_order_without_bypassing_filters(
    monkeypatch,
):
    _reset_api_state(monkeypatch)
    first = Opportunity(
        source="astana_hub",
        source_url="https://example.org/first",
        type=OpportunityType.GRANT,
        title="Cloud credits for early-stage teams",
        tags=["kazakhstan", "cloud"],
        deadline=date.today() + timedelta(days=30),
        score=0.8,
    )
    second = Opportunity(
        source="astana_hub",
        source_url="https://example.org/second",
        type=OpportunityType.GRANT,
        title="Startup support track",
        tags=["kazakhstan", "startup"],
        deadline=date.today() + timedelta(days=30),
        score=0.8,
    )
    excluded = Opportunity(
        source="internews",
        source_url="https://example.org/excluded",
        type=OpportunityType.GRANT,
        title="Media support track",
        tags=["central_asia", "media"],
        deadline=date.today() + timedelta(days=30),
        score=0.8,
    )
    api_main._cache.extend([first, second, excluded])
    monkeypatch.setattr(
        api_main,
        "_search_semantic_opportunities",
        lambda query, items, **_kwargs: [
            type("Hit", (), {"opportunity_id": second.id, "score": 0.99})(),
            type("Hit", (), {"opportunity_id": excluded.id, "score": 0.98})(),
            type("Hit", (), {"opportunity_id": first.id, "score": 0.97})(),
        ],
    )
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", "1")
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_URL", "http://semantic:8010")
    client = TestClient(api_main.app)

    response = client.get(
        "/opportunities",
        params={"q": "financial support", "source": "astana_hub"},
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [str(second.id), str(first.id)]
    assert response.headers["x-total-count"] == "2"


def test_hybrid_search_fuses_lexical_and_semantic_ranks_without_extra_records():
    lexical = Opportunity(
        source="astana_hub",
        source_url="https://example.org/lexical",
        type=OpportunityType.GRANT,
        title="AI accelerator",
    )
    semantic = Opportunity(
        source="astana_hub",
        source_url="https://example.org/semantic",
        type=OpportunityType.GRANT,
        title="Startup programme",
    )
    unrelated = Opportunity(
        source="astana_hub",
        source_url="https://example.org/unrelated",
        type=OpportunityType.GRANT,
        title="Unrelated call",
    )
    hits = [
        type("Hit", (), {"opportunity_id": semantic.id, "score": 0.99})(),
        type("Hit", (), {"opportunity_id": lexical.id, "score": 0.98})(),
    ]

    rows = api_main._fuse_hybrid_query_results(
        [lexical, semantic, unrelated],
        [lexical],
        hits,
    )

    assert [row.id for row in rows] == [lexical.id, semantic.id]


def test_opportunities_priority_prefers_actionable_runway_at_equal_relevance(
    monkeypatch,
):
    _reset_api_state(monkeypatch)
    today = date.today()
    no_deadline = Opportunity(
        source="science_fund",
        source_url="https://example.org/no-deadline",
        type=OpportunityType.GRANT,
        title="Kazakhstan AI support without deadline",
        tags=["kazakhstan", "ai"],
    )
    actionable = Opportunity(
        source="science_fund",
        source_url="https://example.org/actionable",
        type=OpportunityType.GRANT,
        title="Kazakhstan AI support with application window",
        tags=["kazakhstan", "ai"],
        deadline=today + timedelta(days=14),
    )
    api_main._cache.extend([no_deadline, actionable])

    response = TestClient(api_main.app).get(
        "/opportunities",
        params={"min_score": 0.3, "lang": "en"},
    )

    assert response.status_code == 200
    rows = response.json()
    assert [row["id"] for row in rows] == [str(actionable.id), str(no_deadline.id)]
    assert rows[0]["score"] == rows[1]["score"]
    assert rows[0]["raw"]["ranking"]["priority"] > rows[1]["raw"]["ranking"]["priority"]


def test_api_hides_retired_kazakhstan_watch_items_from_storage(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'watch.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="kazakhstan_watch",
            source_url="https://www.undp.org/kazakhstan/procurement",
            type=OpportunityType.GRANT,
            title="Retired UNDP watch page",
            summary="Legacy watch item",
            tags=["kazakhstan", "watchlist"],
            score=0.7,
        )
    )
    active_watch_url = next(iter(api_main.ACTIVE_WATCH_URLS))
    repo.upsert(
        Opportunity(
            source="kazakhstan_watch",
            source_url=active_watch_url,
            type=OpportunityType.GRANT,
            title="Active watch page",
            summary="Current curated watch item",
            tags=["kazakhstan", "watchlist", "rolling"],
            score=0.7,
        )
    )

    client = TestClient(api_main.app)

    response = client.get(
        "/opportunities",
        params={"include_irrelevant": True, "limit": 20},
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["title"] for item in data] == [
        api_main.WATCH_PAGE_BY_URL[active_watch_url].title
    ]
    assert "rolling" in data[0]["tags"]
    assert data[0]["raw"]["deadline_policy"] == "rolling"

    coverage = client.get("/coverage")
    assert coverage.status_code == 200
    sources = {item["slug"]: item for item in coverage.json()["sources"]}
    assert sources["kazakhstan_watch"]["items"] == 1


def test_api_hides_unesco_listing_index_from_storage(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'unesco.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="unesco_iite",
            source_url=api_main.UNESCO_IITE_ANNOUNCEMENTS_URL,
            type=OpportunityType.GRANT,
            title="Announcements",
            summary="Stale UNESCO index page",
            tags=["global", "unesco", "education"],
            score=0.8,
        )
    )

    client = TestClient(api_main.app)
    response = client.get(
        "/opportunities",
        params={"include_irrelevant": True, "limit": 20},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_digest_returns_open_relevant_items_with_tag_filter(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="google_cloud_startup",
                source_url="https://startup.google.com/cloud/",
                type=OpportunityType.CLOUD_CREDIT,
                title="Google for Startups Cloud Program",
                summary="Global AI startup support",
                tags=["global", "startup", "ai", "cloud_credits"],
                score=0.8,
            ),
            Opportunity(
                source="eeas_kazakhstan",
                source_url="https://example.org/expired-digest",
                type=OpportunityType.GRANT,
                title="Expired Kazakhstan grant",
                summary="Kazakhstan grant",
                tags=["kazakhstan", "ai"],
                deadline=date(2024, 1, 1),
                score=0.9,
            ),
            Opportunity(
                source="grants_gov",
                source_url="https://example.org/us-only-digest",
                type=OpportunityType.GRANT,
                title="AI3 Action Institute - Artificial Intelligence for American Indians",
                summary="US domestic tribal grant",
                tags=["ai", "us", "federal"],
                score=0.9,
            ),
        ]
    )

    client = TestClient(api_main.app)
    response = client.get("/digest", params={"tag": "cloud_credits", "limit": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["channel"] == "api"
    assert len(data["items"]) == 1
    assert data["items"][0]["source"] == "google_cloud_startup"
    assert data["items"][0]["title"] == "Google Cloud для стартапов"
    head_response = client.head("/digest", params={"tag": "cloud_credits", "limit": 5})
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("application/json")


def test_digest_defaults_to_russian_without_lang(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="google_cloud_startup",
                source_url="https://example.org/digest-default-russian",
                type=OpportunityType.CLOUD_CREDIT,
                title="Cloud credits digest",
                summary="Cloud credits in English",
                tags=["startup", "cloud"],
                score=0.91,
                deadline=date(2026, 12, 31),
                raw={
                    "i18n": {
                        "ru": {
                            "title": "Дайджест в рубрике облака",
                            "summary": "Кредиты для облака по-русски.",
                        }
                    }
                },
            )
        ]
    )

    client = TestClient(api_main.app)
    response = client.get("/digest", params={"limit": 5, "min_score": 0.3})

    assert response.status_code == 200
    data = response.json()
    assert data["channel"] == "api"
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Дайджест в рубрике облака"


def test_opportunities_endpoint_defaults_to_russian_without_lang(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="world_bank_kazakhstan",
                source_url="https://example.org/project/default-russian-opps",
                type=OpportunityType.GRANT,
                title="English title",
                summary="English summary",
                tags=["kazakhstan", "digitalization"],
                score=0.77,
                raw={
                    "i18n": {
                        "ru": {
                            "title": "Заголовок на русском",
                            "summary": "Краткое описание на русском языке.",
                        }
                    }
                },
            )
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/opportunities", params={"min_score": 0.3})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Заголовок на русском"
    assert data[0]["summary"] == "Краткое описание на русском языке."
    head_response = client.head("/opportunities", params={"min_score": 0.5})
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("application/json")


def test_api_returns_clean_source_raw_for_persisted_opportunity(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-clean-raw.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/api-clean-raw",
            type=OpportunityType.GRANT,
            title="Clean raw grant",
            summary="A normalized opportunity for Central Asia",
            tags=["ai", "education"],
            score=0.8,
            raw={"external_id": "RAW-1", "agency": "Example Agency"},
        )
    )

    client = TestClient(api_main.app)
    response = client.get("/opportunities", params={"min_score": 0.5})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tags"] == ["ai", "education"]
    assert data[0]["score"] == 0.7
    raw = data[0]["raw"]
    assert {
        key: value
        for key, value in raw.items()
        if key
        not in {
            "ranking",
            "qazcompute_evidence_readiness",
            "qazcompute_deadline_anomaly",
            "provenance",
            "program_truth",
        }
    } == {
        "external_id": "RAW-1",
        "agency": "Example Agency",
        "decision_readiness": {
            "status": "partial",
            "known_fields": 0,
            "total_fields": 4,
            "missing_fields": ["deadline", "amount", "eligibility", "application"],
        },
    }
    assert raw["ranking"]["model_version"] == "qazfund-relevance-v2"
    assert raw["qazcompute_deadline_anomaly"]["schema_version"] == (
        "deadline_anomaly.v1"
    )
    assert raw["qazcompute_deadline_anomaly"]["decision_ready"] is False
    assert "source_url" not in raw


def test_duplicate_candidates_endpoint_returns_review_only_clusters(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="astana_hub",
                source_url="https://example.org/program",
                type=OpportunityType.GRANT,
                title="Kazakhstan innovation grant for startups",
                summary="Support for Kazakhstan technology startups.",
                tags=["kazakhstan", "startup"],
                score=0.8,
            ),
            Opportunity(
                source="astana_hub",
                source_url="https://www.example.org/program/",
                type=OpportunityType.GRANT,
                title="Kazakhstan innovation grant for startups",
                summary="Technology startup support in Kazakhstan.",
                tags=["kazakhstan", "startup"],
                score=0.8,
            ),
        ]
    )
    api_main._clear_public_items_cache()
    client = TestClient(api_main.app)

    response = client.get(
        "/opportunities/duplicate-candidates",
        params={"min_score": 0.1, "content_lang": "en"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "duplicate_cluster.v1"
    assert payload["decision_ready"] is False
    assert payload["cluster_count"] == 1
    assert payload["pairs"][0]["tier"] == "duplicate_candidate"


def test_compact_opportunities_keep_dashboard_fields_without_ingestion_payload(
    tmp_path, monkeypatch
):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-compact-raw.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/api-compact-raw",
            type=OpportunityType.GRANT,
            title="Compact API grant",
            summary="A normalized opportunity for Central Asia",
            tags=["ai", "education"],
            score=0.8,
            raw={
                "external_id": "COMPACT-1",
                "agency": "Example Agency",
                "application_url": "https://example.org/apply",
                "deadline_policy": "rolling",
                "detail_text": "x" * 10_000,
                "source_html": "<main>Large source payload</main>",
            },
        )
    )

    client = TestClient(api_main.app)
    response = client.get(
        "/opportunities", params={"min_score": 0.5, "compact": "true"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    raw = data[0]["raw"]
    assert {
        key: value
        for key, value in raw.items()
        if key
        not in {
            "ranking",
            "qazcompute_evidence_readiness",
            "qazcompute_deadline_anomaly",
            "provenance",
            "program_truth",
        }
    } == {
        "agency": "Example Agency",
        "application_url": "https://example.org/apply",
        "deadline_policy": "rolling",
        "decision_readiness": {
            "status": "partial",
            "known_fields": 2,
            "total_fields": 4,
            "missing_fields": ["amount", "eligibility"],
        },
    }
    ranking = raw["ranking"]
    assert raw["provenance"]["schema_version"] == "provenance.v1"
    assert raw["provenance"]["evidence_state"] == "sourced"
    assert raw["provenance"]["deadline_confidence"] == "supported"
    assert raw["provenance"]["amount_confidence"] == "unknown"
    assert ranking["model_version"] == "qazfund-relevance-v2"
    assert ranking["relevance"] == data[0]["score"]
    readiness = raw["qazcompute_evidence_readiness"]
    assert readiness["schema_version"] == "evidence_readiness.v1"
    assert readiness["provider"] == "qazfund-local-fallback"
    assert readiness["model"] == "evidence-readiness-deterministic-v1"
    assert readiness["decision_ready"] is False
    assert readiness["tier"] == "watch"
    assert readiness["features"]["required_evidence_count"] == 4
    anomaly = raw["qazcompute_deadline_anomaly"]
    assert anomaly["schema_version"] == "deadline_anomaly.v1"
    assert anomaly["decision_ready"] is False
    assert anomaly["tier"] == "clean"


def test_decision_readiness_marks_complete_source_facts(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-decision-readiness.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/complete-application",
            type=OpportunityType.GRANT,
            title="Complete application facts",
            summary="A fully described opportunity for Kazakhstan organizations.",
            amount_min=1000,
            amount_max=5000,
            deadline=date(2027, 2, 1),
            eligibility=["Registered organizations"],
            tags=["kazakhstan"],
            score=0.9,
            raw={"application_url": "https://example.org/complete-application/apply"},
        )
    )

    response = TestClient(api_main.app).get(
        "/opportunities", params={"min_score": 0.3, "compact": "true"}
    )

    assert response.status_code == 200
    readiness = response.json()[0]["raw"]["decision_readiness"]
    assert readiness == {
        "status": "complete",
        "known_fields": 4,
        "total_fields": 4,
        "missing_fields": [],
    }
    compute_readiness = response.json()[0]["raw"]["qazcompute_evidence_readiness"]
    assert compute_readiness["schema_version"] == "evidence_readiness.v1"
    assert compute_readiness["decision_ready"] is False
    assert compute_readiness["tier"] == "ready"
    assert compute_readiness["score"] >= 85


def test_public_items_cache_reuses_loaded_items_until_invalidated(monkeypatch):
    _reset_api_state(monkeypatch)
    calls = {"count": 0}
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/cache",
        type=OpportunityType.GRANT,
        title="Cacheable grant",
        summary="Cacheable Central Asia opportunity",
        tags=["central_asia"],
        score=0.8,
    )

    def fake_stored_items(content_lang: str = "en"):
        calls["count"] += 1
        return [item]

    monkeypatch.setattr(api_main, "_stored_items", fake_stored_items)

    assert api_main._cached_public_items("en")[0].title == "Cacheable grant"
    assert api_main._cached_public_items("en")[0].title == "Cacheable grant"
    assert calls["count"] == 1

    api_main._clear_public_items_cache()
    assert api_main._cached_public_items("en")[0].title == "Cacheable grant"
    assert calls["count"] == 2


def test_public_items_cache_serves_complete_stale_snapshot_until_refresh(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/stale-cache",
        type=OpportunityType.GRANT,
        title="Complete cached grant",
        summary="Complete cached Central Asia opportunity",
        tags=["central_asia"],
        score=0.8,
    )
    api_main._public_items_cache["en"] = (
        datetime.now(timezone.utc) - api_main._PUBLIC_ITEMS_CACHE_TTL * 2,
        [item],
    )

    def unexpected_reload(content_lang: str = "en"):
        raise AssertionError("request handler attempted a synchronous full reload")

    monkeypatch.setattr(api_main, "_stored_items", unexpected_reload)

    assert api_main._cached_public_items("en") == [item]


def test_public_query_cache_reuses_sorted_dashboard_result(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/query-cache",
        type=OpportunityType.GRANT,
        title="Query cache grant",
        summary="Query cache opportunity for Kazakhstan teams.",
        deadline=date(2027, 2, 1),
        tags=["kazakhstan"],
        score=0.8,
    )
    calls = {"scope": 0, "priority": 0}

    def fake_scope_items(content_lang: str = "en", *, include_irrelevant: bool = False):
        calls["scope"] += 1
        return [item]

    def fake_priority_score(*args, **kwargs):
        calls["priority"] += 1
        return 0.8

    monkeypatch.setattr(api_main, "_cached_public_scope_items", fake_scope_items)
    monkeypatch.setattr(api_main, "priority_score", fake_priority_score)
    query = {
        "tag": None,
        "q": None,
        "source": None,
        "lifecycle": None,
        "region": None,
        "min_score": 0.0,
        "deadline_after": date(2026, 8, 4),
        "deadline_before": None,
        "include_irrelevant": False,
        "limit": 5000,
        "offset": 0,
        "lang": "ru",
        "compact": True,
    }

    first, first_total = api_main._query_opportunities(**query)
    second, second_total = api_main._query_opportunities(**query)

    assert first_total == second_total == 1
    assert first[0].title == second[0].title == "Query cache grant"
    assert calls == {"scope": 1, "priority": 1}


def test_deadline_after_excludes_explicitly_closed_items(monkeypatch):
    _reset_api_state(monkeypatch)
    open_item = Opportunity(
        source="astana_hub",
        source_url="https://example.org/open-current",
        type=OpportunityType.GRANT,
        title="Open Kazakhstan grant",
        summary="Current support for Kazakhstan teams.",
        deadline=date(2026, 9, 1),
        tags=["kazakhstan"],
        score=0.8,
    )
    closed_item = open_item.model_copy(
        update={
            "source_url": "https://example.org/closed-current",
            "title": "Closed Kazakhstan grant",
            "lifecycle": "closed",
        }
    )
    monkeypatch.setattr(
        api_main,
        "_cached_prepared_scope_items",
        lambda content_lang="en", include_irrelevant=False: [open_item, closed_item],
    )

    items, total = api_main._query_opportunities(
        tag=None,
        q=None,
        source=None,
        lifecycle=None,
        region=None,
        min_score=0.3,
        deadline_before=None,
        deadline_after=date(2026, 8, 10),
        include_irrelevant=False,
        limit=5000,
        offset=0,
        lang="ru",
        compact=False,
    )

    assert total == 1
    assert [item.title for item in items] == ["Open Kazakhstan grant"]


def test_find_opportunity_falls_back_across_language_dedupe_models(monkeypatch):
    _reset_api_state(monkeypatch)
    english = Opportunity(
        id=uuid4(),
        source="sample",
        source_url="https://example.org/shared",
        type=OpportunityType.GRANT,
        title="English record",
        summary="Shared opportunity for Kazakhstan teams.",
        tags=["kazakhstan"],
        raw={"external_id": "SHARED-1"},
    )
    russian = english.model_copy(
        update={
            "id": uuid4(),
            "title": "Русская запись",
        }
    )

    def fake_public_items(content_lang: str = "en"):
        return [english] if content_lang == "en" else [russian]

    monkeypatch.setattr(api_main, "_cached_public_items", fake_public_items)

    assert api_main._find_opportunity(english.id, content_lang="ru") == english
    assert api_main._find_opportunity(russian.id, content_lang="en") == russian


def test_public_scope_cache_reuses_expensive_geography_filter(monkeypatch):
    _reset_api_state(monkeypatch)
    calls = {"count": 0}
    items = [
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/scoped-cache",
            type=OpportunityType.GRANT,
            title="Scoped cache grant",
            summary="Opportunity for Central Asia teams.",
            tags=["central_asia"],
            score=0.8,
        )
    ]

    def fake_scope(values, *, include_irrelevant: bool):
        calls["count"] += 1
        assert values == items
        assert include_irrelevant is False
        return values

    monkeypatch.setattr(api_main, "_cached_public_items", lambda lang: items)
    monkeypatch.setattr(api_main, "_public_scope_items", fake_scope)

    assert api_main._cached_public_scope_items("en")[0].title == "Scoped cache grant"
    assert api_main._cached_public_scope_items("en")[0].title == "Scoped cache grant"
    assert calls["count"] == 1


def test_prepared_scope_cache_reuses_ranking_projection(monkeypatch):
    _reset_api_state(monkeypatch)
    calls = {"count": 0}
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/prepared-cache",
        type=OpportunityType.GRANT,
        title="Prepared cache grant",
        summary="Opportunity for Central Asia teams.",
        tags=["central_asia", "grant"],
        score=0.8,
    )
    original = api_main._with_decision_readiness

    def counted_projection(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        api_main,
        "_cached_public_scope_items",
        lambda content_lang="en", include_irrelevant=False: [item],
    )
    monkeypatch.setattr(api_main, "_with_decision_readiness", counted_projection)

    assert api_main._cached_prepared_scope_items("en")[0].id == item.id
    assert api_main._cached_prepared_scope_items("en")[0].id == item.id
    assert calls["count"] == 1


def test_public_v1_cache_reuses_machine_projection(monkeypatch):
    _reset_api_state(monkeypatch)
    calls = {"count": 0}
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/v1-cache",
        type=OpportunityType.GRANT,
        title="Versioned cache grant",
        summary="Opportunity for Central Asia teams.",
        tags=["central_asia", "grant"],
        score=0.8,
    )
    original = api_main.to_opportunity_v1

    def counted_projection(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        api_main,
        "_cached_prepared_scope_items",
        lambda content_lang="en", include_irrelevant=False: [item],
    )
    monkeypatch.setattr(api_main, "to_opportunity_v1", counted_projection)

    first = api_main._cached_public_v1_index(
        content_lang="en",
        include_irrelevant=False,
        public_base_url="https://qaz.fund",
    )
    second = api_main._cached_public_v1_index(
        content_lang="en",
        include_irrelevant=False,
        public_base_url="https://qaz.fund",
    )

    assert first[item.id] == second[item.id]
    assert calls["count"] == 1


def test_ndjson_body_cache_skips_repeated_catalog_projection(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.append(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/ndjson-cache",
            type=OpportunityType.GRANT,
            title="NDJSON cache grant",
            summary="Opportunity for Kazakhstan teams.",
            tags=["kazakhstan", "grant"],
            score=0.8,
        )
    )
    calls = {"count": 0}
    original = api_main._query_opportunities

    def counted_query(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(api_main, "_query_opportunities", counted_query)
    client = TestClient(api_main.app)

    first = client.get("/opportunities.ndjson?lang=ru&compact=true")
    second = client.get("/opportunities.ndjson?lang=ru&compact=true")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.text == second.text
    assert first.headers["etag"] == second.headers["etag"]
    assert calls["count"] == 1


def test_coverage_cache_reuses_source_aggregation(monkeypatch):
    _reset_api_state(monkeypatch)
    calls = {"count": 0}
    item = Opportunity(
        source="grants_gov",
        source_url="https://example.org/coverage-cache",
        type=OpportunityType.GRANT,
        title="Coverage cache grant",
        summary="Coverage cache opportunity for Central Asia.",
        tags=["central_asia"],
        score=0.8,
    )

    def fake_coverage(items, source_checks, source_check_statuses):
        calls["count"] += 1
        assert items == [item]
        assert source_checks == {}
        assert source_check_statuses == {}
        return [
            {
                "slug": "grants_gov",
                "enabled": True,
                "relevant_open_items": 1,
            }
        ]

    monkeypatch.setattr(api_main, "_cached_public_items", lambda: [item])
    monkeypatch.setattr(api_main, "_source_coverage", fake_coverage)

    assert api_main._cached_coverage_payload()["items"] == 1
    assert api_main._cached_coverage_payload()["relevant_open_items"] == 1
    assert calls["count"] == 1


def test_api_cleans_source_ui_noise_from_persisted_summary(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-clean-summary.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="unesco_iite",
            source_url="https://example.org/api-clean-summary",
            type=OpportunityType.GRANT,
            title="Clean summary grant",
            summary="Описание программы. Читать далее Прием заявок",
            tags=["kazakhstan", "education"],
            score=0.8,
            raw={"external_id": "SUMMARY-1"},
        )
    )

    client = TestClient(api_main.app)
    response = client.get("/opportunities", params={"min_score": 0.5})

    assert response.status_code == 200
    data = response.json()
    assert data[0]["summary"] == "Описание программы."


def test_opportunities_detail_endpoint_defaults_to_russian_without_lang(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/project/default-russian-detail",
        type=OpportunityType.GRANT,
        title="English title",
        summary="English detail summary",
        tags=["kazakhstan", "digital"],
        score=0.83,
        raw={
            "i18n": {
                "ru": {
                    "title": "Подробная карточка",
                    "summary": "Резюме на русском.",
                    "detail_sections": [
                        {
                            "heading": "Кто может подать",
                            "text": "Инновационные команды и стартапы.",
                        }
                    ],
                }
            },
            "application_url": "https://example.org/apply",
            "detail_text": "English fallback detail",
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunities/{item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Подробная карточка"
    assert data["summary"] == "Резюме на русском."
    assert data["detail_sections"][0]["heading"] == "Обзор"
    assert data["detail_sections"][0]["text"] == "Резюме на русском."
    assert data["raw"]["provenance"]["schema_version"] == "provenance.v1"
    assert data["raw"]["provenance"]["evidence_state"] == "sourced"


def test_api_localizes_english_detail_section_headings_for_russian_detail_view(
    monkeypatch,
):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="eeas_kazakhstan",
        source_url="https://example.org/detail-heading",
        type=OpportunityType.GRANT,
        title="English title",
        summary="English detail summary",
        tags=["kazakhstan"],
        score=0.81,
        raw={
            "detail_text": "English fallback detail",
            "detail_sections": [
                {"heading": "Overview", "text": "English overview text."},
                {"heading": "Eligibility", "text": "Registered NGOs."},
                {"heading": "Source status", "text": "Fetched from source."},
            ],
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunities/{item.id}", params={"lang": "ru"})

    assert response.status_code == 200
    data = response.json()
    assert data["detail_sections"][0]["heading"] == "Обзор"
    assert data["detail_sections"][1]["heading"] == "Обзор"
    assert data["detail_sections"][2]["heading"] == "Кто может подать заявку"
    assert data["detail_sections"][3]["heading"] == "Статус источника"

    kk_response = client.get(f"/opportunities/{item.id}", params={"lang": "kk"})

    assert kk_response.status_code == 200
    kk_data = kk_response.json()
    assert kk_data["detail_sections"][0]["heading"] == "Шолу"


def test_api_excludes_legacy_irrelevant_grants_gov_rows(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-grants-summary.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        GrantRecord(
            source="grants_gov",
            external_id="362341",
            title="Strengthening Uzbekistan&rsquo;s Anti-Corruption Framework",
            url="https://www.grants.gov/search-results-detail/362341",
            description="",
            tags=["us", "federal", "grant", "governance"],
            raw={
                "agency": "Bureau of International Narcotics-Law Enforcement",
                "agencyCode": "DOS-INL",
                "closeDate": "06/09/2026",
            },
            score=0.33,
        )
    )

    client = TestClient(api_main.app)
    response = client.get("/opportunities", params={"min_score": 0.3})

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_api_excludes_legacy_irrelevant_grants_gov_rows_for_russian_feed(
    tmp_path, monkeypatch
):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-grants-summary-ru.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        GrantRecord(
            source="grants_gov",
            external_id="362341-ru",
            title="Strengthening Uzbekistan&rsquo;s Anti-Corruption Framework",
            url="https://www.grants.gov/search-results-detail/362341-ru",
            description="",
            tags=["us", "federal", "grant", "governance"],
            raw={
                "agency": "Bureau of International Narcotics-Law Enforcement",
                "agencyCode": "DOS-INL",
                "closeDate": "06/09/2026",
            },
            score=0.33,
        )
    )

    client = TestClient(api_main.app)
    response = client.get("/opportunities", params={"min_score": 0.3, "lang": "ru"})

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_api_returns_russian_localized_content_when_lang_ru(tmp_path, monkeypatch):
    _reset_api_state(monkeypatch)
    db_url = f"sqlite:///{tmp_path / 'api-localized.sqlite'}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", db_url)

    repo = SqlRepository(db_url)
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/api-localized",
            type=OpportunityType.GRANT,
            title="AI education grant",
            summary="Open to Central Asia schools",
            eligibility=["Registered nonprofits", "Universities"],
            tags=["ai", "education"],
            score=0.9,
            raw={
                "agency": "Example Agency",
                "i18n": {
                    "ru": {
                        "title": "Грант на ИИ в образовании",
                        "summary": "Открыт для школ Центральной Азии",
                        "eligibility": [
                            "Зарегистрированные НПО",
                            "Университеты",
                        ],
                    }
                },
            },
        )
    )

    client = TestClient(api_main.app)
    response = client.get("/opportunities", params={"min_score": 0.5, "lang": "ru"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Грант на ИИ в образовании"
    assert data[0]["summary"] == "Открыт для школ Центральной Азии"
    assert data[0]["eligibility"] == [
        "Зарегистрированные НПО",
        "Университеты",
    ]


def test_opportunity_detail_endpoint_returns_structured_local_payload(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/project/P179204",
        type=OpportunityType.GRANT,
        title="Kazakhstan Digital Acceleration",
        summary="Broadband infrastructure and digital inclusion support.",
        tags=["kazakhstan", "digitalization", "project_pipeline"],
        score=0.92,
        raw={
            "project_id": "P179204",
            "borrower": "Republic of Kazakhstan",
            "region": "Europe and Central Asia",
            "application_url": "https://example.org/apply/P179204",
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunities/{item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(item.id)
    assert data["detail_available"] is True
    assert data["detail_fetch_status"] == "structured_only"
    assert data["application_url"] == "https://example.org/apply/P179204"
    assert data["detail_sections"][0]["heading"] == "Обзор"
    assert "Проект Всемирного банка" in data["detail_sections"][0]["text"]
    metadata = {entry["key"]: entry["value"] for entry in data["metadata"]}
    assert metadata["project_id"] == "P179204"
    assert metadata["borrower"] == "Republic of Kazakhstan"

    english_response = client.get(f"/opportunities/{item.id}", params={"lang": "en"})
    assert english_response.status_code == 200
    assert (
        "Broadband infrastructure"
        in english_response.json()["detail_sections"][0]["text"]
    )


def test_opportunity_detail_endpoint_returns_russian_localized_payload(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/project/P179204-ru",
        type=OpportunityType.GRANT,
        title="Kazakhstan Digital Acceleration",
        summary="Broadband infrastructure and digital inclusion support.",
        eligibility=["Registered NGOs"],
        tags=["kazakhstan", "digitalization", "project_pipeline"],
        score=0.92,
        raw={
            "project_id": "P179204-RU",
            "status_note": "Source page mirrored from upstream.",
            "i18n": {
                "ru": {
                    "title": "Цифровое ускорение Казахстана",
                    "summary": "Поддержка цифровой инфраструктуры и инклюзивного доступа.",
                    "eligibility": ["Зарегистрированные НПО"],
                    "status_note": "Страница источника зеркалируется из upstream.",
                    "detail_sections": [
                        {
                            "heading": "Что финансируется",
                            "text": "Проект поддерживает цифровую инфраструктуру и доступ к связи.",
                        }
                    ],
                    "detail_text": (
                        "Что финансируется\n"
                        "Проект поддерживает цифровую инфраструктуру и доступ к связи."
                    ),
                }
            },
            "detail_sections": [
                {
                    "heading": "What is funded",
                    "text": "The project supports digital infrastructure and connectivity.",
                }
            ],
            "detail_text": (
                "What is funded\n"
                "The project supports digital infrastructure and connectivity."
            ),
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunities/{item.id}", params={"lang": "ru"})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Цифровое ускорение Казахстана"
    assert data["summary"] == (
        "Поддержка цифровой инфраструктуры и инклюзивного доступа."
    )
    assert data["detail_sections"][0]["heading"] == "Обзор"
    assert (
        data["detail_sections"][0]["text"]
        == "Поддержка цифровой инфраструктуры и инклюзивного доступа."
    )
    assert data["detail_sections"][1]["heading"] == "Кто может подать заявку"
    assert data["detail_sections"][1]["text"] == "Зарегистрированные НПО"
    assert data["detail_sections"][2]["heading"] == "Статус источника"
    assert data["detail_sections"][3]["heading"] == "Что финансируется"
    assert "цифровую инфраструктуру" in data["detail_sections"][3]["text"]


def test_opportunity_page_renders_public_permalink(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/project/P179204-page",
        type=OpportunityType.GRANT,
        title="Kazakhstan Digital Acceleration",
        summary="Broadband infrastructure and digital inclusion support.",
        funder="Development Fund",
        amount_max=Decimal("25000"),
        deadline=date(2026, 10, 31),
        eligibility=["Registered NGOs"],
        tags=["kazakhstan", "digitalization", "project_pipeline"],
        score=0.92,
        raw={
            "project_id": "P179204-PAGE",
            "reference": "QF-2026-17",
            "borrower": "Republic of Kazakhstan",
            "country": "kazakhstan",
            "region": "central_asia",
            "application_url": "https://example.org/apply/P179204-page",
            "deadline_raw": "deadline is October 31st, 2026",
            "page_title": "English source page title",
            "i18n": {
                "ru": {
                    "title": "Цифровое ускорение Казахстана",
                    "summary": "Поддержка цифровой инфраструктуры и инклюзивного доступа.",
                    "eligibility": ["Зарегистрированные НПО"],
                    "detail_sections": [
                        {
                            "heading": "Что финансируется",
                            "text": "Проект поддерживает цифровую инфраструктуру и доступ к связи.",
                        }
                    ],
                }
            },
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{item.id}", params={"lang": "ru"})

    assert response.status_code == 200
    assert "grid-template-columns: minmax(0, 1fr)" in response.text
    assert ".opportunity-head > *" in response.text
    assert "overflow-wrap: anywhere" in response.text
    assert "public, max-age=60" in response.headers["cache-control"]
    assert '<html lang="ru"' in response.text
    assert 'data-avds-component="opportunity-page"' in response.text
    assert 'data-avds-component="opportunity-detail"' in response.text
    assert "<title>Цифровое ускорение Казахстана – QAZ.FUND</title>" in response.text
    assert (
        'rel="canonical" href="http://testserver/opportunity/'
        f'{item.id}?lang=ru"' in response.text
    )
    assert "Поддержка цифровой инфраструктуры и инклюзивного доступа." in response.text
    assert "31.10.2026" in response.text
    assert "25" in response.text
    assert "Казахстан" in response.text
    assert "Организатор" in response.text
    assert "Development Fund" in response.text
    assert "Номер проекта" in response.text
    assert "P179204-PAGE" in response.text
    assert "Номер объявления" in response.text
    assert "QF-2026-17" in response.text
    assert "Кому подходит" in response.text
    assert "Что финансируется" in response.text
    assert "Зарегистрированные НПО" in response.text
    assert "Официальный источник" in response.text
    assert 'class="opportunity-facts"' in response.text
    assert 'class="source-panel"' in response.text
    assert 'class="detail-content-list"' in response.text
    assert 'class="application-steps"' not in response.text
    assert 'data-avds-component="hero-band"' not in response.text
    assert 'data-avds-component="trust-facts-panel"' not in response.text
    assert 'data-avds-component="evidence-disclosure"' not in response.text
    assert 'data-avds-component="action-path"' not in response.text
    assert 'data-avds-pattern="opportunity-readiness-meter"' not in response.text
    assert 'class="decision-support"' not in response.text
    assert 'id="profile-fit"' not in response.text
    assert 'id="copy-working-brief"' not in response.text
    assert 'id="share-opportunity"' not in response.text
    assert "qazfund-applicant-profile-v1" not in response.text
    assert "Соберите проектную заявку" not in response.text
    assert "Ключевые условия" not in response.text
    assert (
        "Описание и ключевые поля собраны с официального источника" not in response.text
    )
    assert "Статус источника" not in response.text
    assert "<strong>Точное</strong>" not in response.text
    assert ">0.92<" not in response.text
    assert response.text.index("31.10.2026") < response.text.index("Кому подходит")
    assert response.text.index("Кому подходит") < response.text.index(
        "Что финансируется"
    )
    assert "structured_only" not in response.text
    assert "English source page title" not in response.text
    assert "deadline is October" not in response.text
    assert 'href="https://example.org/project/P179204-page"' in response.text
    assert 'href="https://example.org/apply/P179204-page"' in response.text
    assert 'href="/?lang=ru#opportunities"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/status?lang=ru"' not in response.text
    assert 'href="/docs?lang=ru"' not in response.text
    assert 'aria-label="Навигационная цепочка"' in response.text
    assert 'class="hero-fact hero-fact--source"' not in response.text
    assert ".opportunity-facts" in response.text
    assert ".source-panel" in response.text
    assert (
        'class="button primary" href="https://example.org/apply/P179204-page"'
        in response.text
    )
    social_image_prefix = (
        f"http://testserver/opportunity/{item.id}/og.png?lang=ru&amp;v="
    )
    assert f'property="og:image" content="{social_image_prefix}' in response.text
    assert f'name="twitter:image" content="{social_image_prefix}' in response.text
    assert 'property="og:image:type" content="image/png"' in response.text
    assert (
        'property="og:image:alt" content="QAZ.FUND: Цифровое ускорение Казахстана"'
        in response.text
    )
    assert "googletagmanager.com" not in response.text
    assert "mc.yandex.ru" not in response.text
    assert "clarity.ms" not in response.text
    assert '"@type": "BreadcrumbList"' in response.text
    assert '"identifier": "' in response.text
    assert '"sameAs": "https://example.org/project/P179204-page"' in response.text

    head_response = client.head(f"/opportunity/{item.id}", params={"lang": "ru"})
    assert head_response.status_code == 200
    assert "public, max-age=60" in head_response.headers["cache-control"]

    kk_response = client.get(f"/opportunity/{item.id}", params={"lang": "kk"})
    assert kk_response.status_code == 200
    assert '<html lang="kk"' in kk_response.text
    assert 'data-language-fallback="source"' in kk_response.text
    assert (
        f'href="http://testserver/opportunity/{item.id}?lang=kk" lang="kk" '
        'aria-current="page">KAZ</a>' in kk_response.text
    )
    assert "Ресми дереккөз" in kk_response.text
    assert "Кімге арналған" in kk_response.text
    assert "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды." in kk_response.text
    assert "QAZ.FUND не выдаёт средства и не принимает заявки." not in kk_response.text


def test_opportunity_page_defaults_to_russian_without_lang(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="world_bank_kazakhstan",
        source_url="https://example.org/project/P179204-default",
        type=OpportunityType.GRANT,
        title="Default language digital acceleration",
        summary="Open support for digital services in Kazakhstan.",
        tags=["kazakhstan", "digitalization", "project_pipeline"],
        score=0.8,
        raw={
            "i18n": {
                "ru": {
                    "title": "Цифровое ускорение без параметра языка",
                    "summary": "Поддержка цифровых сервисов в Казахстане.",
                }
            }
        },
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{item.id}")

    assert response.status_code == 200
    assert "public, max-age=60" in response.headers["cache-control"]
    assert '<html lang="ru"' in response.text
    assert "Цифровое ускорение без параметра языка" in response.text


def test_opportunity_page_hides_duplicate_source_funder_metadata(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="unesco_iite",
        source_url="https://example.org/unesco/notice",
        type=OpportunityType.TENDER,
        title="UNESCO consultancy notice",
        summary="Consultancy procurement notice.",
        funder="UNESCO IITE",
        deadline=date(2026, 7, 13),
        tags=["unesco", "education", "consultancy"],
        score=0.72,
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{item.id}", params={"lang": "ru"})

    assert response.status_code == 200
    assert '<h2 id="source-title">UNESCO IITE</h2>' in response.text
    assert "Организатор" in response.text
    assert '<aside class="sidebar-card">' not in response.text
    assert "<span>Фонд</span>" not in response.text
    assert "13.07.2026" in response.text

    detail_head = client.head(f"/opportunities/{item.id}", params={"lang": "ru"})
    assert detail_head.status_code == 200


def test_stored_domestic_program_overlay_replaces_stale_facts_and_renders_conditions():
    source_url = "https://qazindustry.gov.kz/ru/business_reimbursement"
    row = SimpleNamespace(
        id=uuid4(),
        dedup_key="qazindustry-reimbursement",
        raw={
            "deadline_policy": "rolling",
            "amount_raw": "up to 60,000,000 USD",
            "i18n": {
                "ru": {
                    "detail_sections": [
                        {
                            "heading": "Меры стимулирования",
                            "text": "Полный фрагмент официального источника.",
                        }
                    ],
                    "detail_text": "Полный фрагмент официального источника.",
                    "detail_language": "ru",
                }
            },
        },
        source="kazakhstan_domestic_support",
        source_url=source_url,
        type=OpportunityType.GRANT,
        title="Stale QazIndustry record",
        summary="Stale summary.",
        funder=None,
        funder_slug=None,
        amount_min=None,
        amount_max=Decimal("60000000"),
        currency="USD",
        deadline=None,
        eligibility=[],
        tags=["grant"],
        languages=["en", "ru"],
        score=0.7,
        opportunity_status="open",
        lifecycle="open",
        first_seen_at=None,
        last_seen_at=None,
        discovered_at=None,
    )

    item = api_main._stored_opportunity(row)
    localized = api_main.localize_opportunity(item, "ru")
    detail = OpportunityDetail(
        **localized.model_dump(),
        detail_sections=[
            OpportunityDetailSection(
                heading="Меры стимулирования",
                text="Полный фрагмент официального источника.",
            )
        ],
        metadata=[
            OpportunityMetadataField(key="amount_raw", value=item.raw["amount_raw"]),
            OpportunityMetadataField(key="country", value=item.raw["country"]),
        ],
    )
    markup = opportunity_page_module.render_opportunity_page(
        detail=detail,
        lang="ru",
        root_path="",
        site_origin="http://testserver",
    )

    assert item.funder == "QazIndustry"
    assert item.amount_max is None
    assert item.currency == "KZT"
    assert item.lifecycle == "open"
    assert "deadline_policy" not in item.raw
    assert item.raw["opportunity_taxonomy"]["instrument"] == "reimbursement"
    assert item.raw["i18n"]["ru"]["detail_sections"][0]["text"] == (
        "Полный фрагмент официального источника."
    )
    assert "40% затрат – до 20–60 млн ₸" in markup
    assert "Возмещение затрат" in markup
    assert "Что компенсируют" in markup
    assert "Не указано организатором" not in markup
    assert 'class="source-text-disclosure"' in markup
    assert "Полный фрагмент официального источника." in markup


def test_opportunity_page_uses_taxonomy_and_only_published_facts():
    detail = OpportunityDetail(
        source="kazakhstan_domestic_support",
        source_url="https://agrocredit.kz/en/main/our-activities/programs/3569/",
        type=OpportunityType.GRANT,
        title="Льготное кредитование откормочных площадок и птицефабрик",
        summary="Пополнение оборотного капитала откормочных площадок и птицефабрик.",
        funder="Agrarian Credit Corporation",
        tags=["kazakhstan", "preferential_financing", "livestock"],
        raw={
            "country": "kazakhstan",
            "i18n": {
                "ru": {
                    "amount": "5% годовых для прямых заёмщиков – 1–15 млрд ₸",
                    "amount_label": "Ставка и сумма",
                    "highlights_label": "Ключевые условия",
                    "highlights": [
                        "Срок кредитной линии – до 36 месяцев, срок транша – до 12 месяцев.",
                        "Залог принимается по залоговой политике Аграрной кредитной корпорации.",
                    ],
                }
            },
        },
        metadata=[OpportunityMetadataField(key="country", value="kazakhstan")],
    )

    markup = opportunity_page_module.render_opportunity_page(
        detail=detail,
        lang="ru",
        root_path="",
        site_origin="http://testserver",
    )

    assert '<span class="opportunity-kicker">Льготное финансирование</span>' in markup
    assert "Ставка и сумма" in markup
    assert "5% годовых для прямых заёмщиков – 1–15 млрд ₸" in markup
    assert "Ключевые условия" in markup
    assert "Не указано организатором" not in markup


def test_stored_domestic_legacy_alias_uses_current_canonical_source():
    legacy = Opportunity(
        source="kazakhstan_domestic_support",
        source_url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-zapustila-novoe-napravlenie-"
            "kreditovaniya/"
        ),
        type=OpportunityType.GRANT,
        title="Legacy livestock lending record",
        summary="Legacy summary.",
        tags=["grant"],
        raw={
            "external_id": "legacy-livestock",
            "deadline_policy": "rolling",
            "i18n": {
                "ru": {
                    "detail_text": "Устаревшие условия из публикации 2025 года.",
                    "detail_sections": [
                        {
                            "heading": "Старые условия",
                            "text": "Не должны попасть в новую карточку.",
                        }
                    ],
                }
            },
        },
    )

    item = api_main._stored_opportunity(legacy)

    assert str(item.source_url) == (
        "https://agrocredit.kz/en/main/our-activities/programs/3569/"
    )
    assert item.title == "Agrarian Credit Corporation feedlot and poultry financing"
    assert item.funder == "Agrarian Credit Corporation"
    assert item.raw["canonical_source_url"] == str(item.source_url)
    assert item.raw["legacy_source_url"].endswith("kreditovaniya/")
    assert "detail_text" not in item.raw["i18n"]["ru"]
    assert "deadline_policy" not in item.raw
    refreshed = legacy.model_copy(
        update={
            "id": uuid4(),
            "source_url": str(item.source_url),
            "discovered_at": legacy.discovered_at + timedelta(days=1),
            "raw": {"canonical_source_url": str(item.source_url)},
        }
    )
    current_item = api_main._stored_opportunity(refreshed)

    assert api_main._public_dedup_key(item) == api_main._public_dedup_key(current_item)
    deduped = api_main._dedupe_public_items([item, current_item], content_lang="ru")
    assert [candidate.id for candidate in deduped] == [item.id]


def test_funder_page_defaults_to_russian_without_lang(monkeypatch):
    _reset_api_state(monkeypatch)
    open_item = Opportunity(
        source="science_fund",
        source_url="https://example.org/science/open-default",
        type=OpportunityType.GRANT,
        title="Open science commercialization",
        summary="Open call for research commercialization teams.",
        funder="Science Fund",
        tags=["science", "commercialization", "kazakhstan"],
        deadline=date(2027, 3, 1),
        score=0.91,
    )
    api_main._cache.append(open_item)
    client = TestClient(api_main.app)

    response = client.get("/funder/science-fund")

    assert response.status_code == 200
    assert "public, max-age=60" in response.headers["cache-control"]
    assert '<html lang="ru"' in response.text
    assert "Фонд науки" in response.text

    head_response = client.head("/funder/science-fund")
    assert head_response.status_code == 200
    assert "public, max-age=60" in head_response.headers["cache-control"]


def test_public_funder_index_excludes_usamraa_domestic_grants(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="grants_gov",
        source_url="https://grants.gov/opportunity/dod-amraa",
        type=OpportunityType.GRANT,
        title="DoD Epilepsy Research Program Award",
        summary="Clinical research opportunity from USAMRAA.",
        funder="DOD-AMRAA",
        tags=["us", "federal", "grant", "artificial intelligence"],
        deadline=date(2026, 8, 17),
        score=0.72,
        raw={"agencyName": "USAMRAA", "agencyCode": "DOD-AMRAA"},
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    funders = client.get("/funders").json()
    legacy_response = client.get("/funder/dod-amraa", follow_redirects=False)

    assert all(row["slug"] != "dod-amraa" for row in funders)
    assert legacy_response.status_code == 302
    assert legacy_response.headers["location"] == "/?lang=ru&q=DOD-AMRAA"


def test_opportunity_page_keeps_subsidy_page_to_source_facts(monkeypatch):
    _reset_api_state(monkeypatch)
    item = Opportunity(
        source="govkz",
        source_url="https://example.org/subsidy",
        type=OpportunityType.GRANT,
        title="Kazakhstan SME subsidy",
        summary="Local subsidy for registered businesses in Kazakhstan.",
        tags=["subsidy", "domestic_support", "sme", "kazakhstan"],
        score=0.82,
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{item.id}", params={"lang": "en"})

    assert response.status_code == 200
    assert 'aria-label="Breadcrumbs"' in response.text
    assert 'data-avds-component="opportunity-detail"' in response.text
    assert "Open source" in response.text
    assert "Not published by the organizer" not in response.text
    assert "Subsidy" in response.text
    assert "What to prepare" not in response.text
    assert "Copy working brief" not in response.text
    assert "Before applying" not in response.text
    assert "Procurement documents" not in response.text
    assert "does not confirm eligibility" not in response.text
    assert "Prepare local documents" not in response.text
    assert "Check company status, digital signature, tax status" not in response.text


def test_opportunity_page_lists_related_opportunities(monkeypatch):
    _reset_api_state(monkeypatch)
    target = Opportunity(
        source="science_fund",
        source_url="https://example.org/grants/alpha",
        type=OpportunityType.GRANT,
        title="Science commercialization track",
        summary="Support for research teams and commercialization pilots.",
        funder="Science Fund",
        tags=["science", "commercialization", "kazakhstan"],
        score=0.88,
    )
    same_source = Opportunity(
        source="science_fund",
        source_url="https://example.org/grants/beta",
        type=OpportunityType.GRANT,
        title="Applied labs grant",
        summary="Applied research and lab capacity support.",
        funder="Science Fund",
        tags=["science", "labs", "kazakhstan"],
        score=0.74,
        raw={
            "deadline_policy": "rolling",
            "i18n": {
                "ru": {
                    "title": "Прикладной грант для лабораторий",
                    "summary": "Поддержка прикладных исследований и лабораторий.",
                }
            },
        },
    )
    same_theme = Opportunity(
        source="govkz",
        source_url="https://example.org/grants/gamma",
        type=OpportunityType.GRANT,
        title="University innovation support",
        summary="University innovation teams can apply for scale-up support.",
        tags=["science", "education", "kazakhstan"],
        score=0.68,
        raw={
            "i18n": {
                "ru": {
                    "summary": (
                        "Крайний срок: 4 июня 2026 г. "
                        "Поддержка университетских инноваций доступна для команд. "
                        "Университетские команды могут подать заявку на рост."
                    ),
                }
            }
        },
    )
    unrelated = Opportunity(
        source="adb_kazakhstan",
        source_url="https://example.org/tenders/delta",
        type=OpportunityType.TENDER,
        title="Road corridor procurement",
        summary="Infrastructure procurement notice.",
        tags=["infrastructure", "procurement"],
        score=0.9,
    )
    api_main._cache.extend([target, same_source, same_theme, unrelated])
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{target.id}", params={"lang": "en"})

    assert response.status_code == 200
    assert "Related opportunities" in response.text
    assert "Applied labs grant" in response.text
    assert "University innovation support" in response.text
    assert "Same source" in response.text
    assert "Related theme" in response.text
    assert response.text.count('data-avds-component="document-card"') == 2
    assert f'href="/opportunity/{same_source.id}?lang=en"' in response.text
    assert f'href="/opportunity/{same_theme.id}?lang=en"' in response.text
    assert "Road corridor procurement" not in response.text
    assert "Open / Rolling" not in response.text

    ru_response = client.get(f"/opportunity/{target.id}", params={"lang": "ru"})

    assert ru_response.status_code == 200
    assert "Похожие программы" in ru_response.text
    assert "Прикладной грант для лабораторий" in ru_response.text
    assert "Поддержка университетских инноваций доступна для команд" in ru_response.text
    assert "Поддержка прикладных исследований и лабораторий." in ru_response.text
    assert "Applied labs grant" not in ru_response.text
    assert "University innovation support" not in ru_response.text


def test_public_insights_page_renders_avds_charts(monkeypatch):
    _reset_api_state(monkeypatch)
    today = date.today()
    api_main._cache.extend(
        [
            Opportunity(
                source="source_a",
                source_url="https://example.org/a",
                type=OpportunityType.GRANT,
                title="Local grant",
                summary="Support for Kazakhstan teams.",
                funder="Source A",
                deadline=today + timedelta(days=12),
                amount_min=1000,
                eligibility=["Kazakhstan teams"],
                score=0.82,
            ),
            Opportunity(
                source="source_b",
                source_url="https://example.org/b",
                type=OpportunityType.TENDER,
                title="Public procurement",
                summary="Open procurement notice.",
                funder="Source B",
                score=0.46,
            ),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/insights", params={"lang": "ru"})

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    assert '<html lang="ru"' in response.text
    assert "Где искать поддержку" in response.text
    assert "<h2>Каталог в разрезе</h2>" in response.text
    assert "<h2>Форматы поддержки</h2>" not in response.text
    assert 'data-avds-component="DataViz"' in response.text
    assert 'data-avds-pattern="format-distribution"' in response.text
    assert 'data-avds-pattern="deadline-distribution"' in response.text
    assert 'data-avds-pattern="decision-readiness"' in response.text
    assert 'class="chart-label chart-label-mobile"' in response.text
    assert ".chart-label-desktop{display:none}" in response.text
    assert ".upcoming-title{min-height:44px" in response.text
    assert "Гранты" in response.text
    assert "До 30 дней" in response.text
    assert 'property="og:type" content="website"' in response.text
    assert (
        'property="og:url" content="http://testserver/insights?lang=ru"'
        in response.text
    )
    assert 'name="twitter:card" content="summary_large_image"' in response.text
    assert (
        'name="twitter:image" content="http://testserver/og-image.png?lang=ru"'
        in response.text
    )
    assert 'href="/insights?lang=kk"' in response.text
    assert (
        'href="/insights?lang=ru" lang="ru" aria-current="page">RU</a>' in response.text
    )
    assert 'rel="alternate" hreflang="kk"' in response.text
    assert 'type="application/json"' in response.text

    data_response = client.get("/insights.json", params={"lang": "ru"})
    assert data_response.status_code == 200
    assert data_response.headers["cache-control"].startswith("public, max-age=60")
    data = data_response.json()
    assert data["schema_version"] == "insights.v1"
    assert data["language"] == "ru"
    assert data["deadlines"]["buckets"]["within_30"] == 1
    assert data["deadlines"]["buckets"]["no_deadline"] == 1
    assert data["deadlines"]["upcoming"][0]["title"] == "Local grant"
    assert data["decision_readiness"]["complete"] == 1
    assert data["decision_readiness"]["partial"] == 1
    assert data["links"]["human"].endswith("/insights?lang=ru")

    kk_response = client.get("/insights", params={"lang": "kk"})
    assert kk_response.status_code == 200
    assert '<html lang="kk"' in kk_response.text
    assert 'data-language-fallback="source"' in kk_response.text
    assert "Қолдауды қайдан іздеу керек" in kk_response.text
    assert "Гранттар" in kk_response.text
    assert (
        "Кейбір карточкалардағы сипаттама әзірге бастапқы тілде көрсетіледі."
        in kk_response.text
    )


def test_insights_snapshot_is_reproducible(monkeypatch):
    _reset_api_state(monkeypatch)
    as_of = date(2026, 8, 4)
    item = Opportunity(
        source="source_a",
        source_url="https://example.org/a",
        type=OpportunityType.GRANT,
        title="Rolling support",
        deadline=None,
        raw={"deadline_policy": "rolling"},
    )
    snapshot = build_insights_snapshot(
        items=[item],
        coverage={"enabled_sources": 1, "relevant_open_items": 1, "sources": []},
        as_of=as_of,
    )
    assert snapshot["as_of"] == "2026-08-04"
    assert snapshot["catalog"]["relevant_open_items"] == 1
    assert snapshot["catalog"]["coverage_relevant_open_items"] == 1
    assert snapshot["deadlines"]["buckets"] == {
        "within_30": 0,
        "within_90": 0,
        "later": 0,
        "rolling": 1,
        "no_deadline": 0,
    }


def test_insights_source_labels_hide_adapter_identifiers():
    assert _source_label("kazakhstan_domestic_support", "ru") == "Поддержка РК"
    assert _source_label("national_institutes_of_health", "ru") == (
        "Национальные институты здравоохранения США (NIH)"
    )
    assert _source_label("world_bank", "ru") == "Всемирный банк"
    assert _source_label("kazakhstan_domestic_support", "en") == "KZ domestic support"
    assert _source_label("world_bank", "kk") == "Дүниежүзілік банк"
    assert _source_label("United Nations Development Programme", "kk") == (
        "БҰҰ-ның Даму бағдарламасы (БҰҰДБ)"
    )
    assert _source_label("custom_source", "ru") == "custom source"


def test_insights_chart_keeps_full_label_in_svg_title():
    chart = _bar_chart(
        [("Очень длинное название официального источника", 4)],
        chart_id="source-distribution",
        color="#15724e",
        empty_label="Нет данных",
    )
    assert "Очень длинное название официального источника: 4" in chart
    assert "Очень длинное название…" in chart
    assert "Очень длинное…" in chart
    assert 'class="chart-label chart-label-mobile"' in chart


def test_public_info_pages_remain_directly_linkable(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    root = client.get("/?lang=ru")
    assert "/terms?lang=ru" in root.text
    assert "/data-policy?lang=ru" in root.text
    assert "/attribution?lang=ru" in root.text
    assert "/insights?lang=ru" not in root.text
    assert "/data-routes?lang=ru" not in root.text

    for path, marker in (
        ("/terms", "Как пользоваться QAZ.FUND"),
        ("/data-policy", "Откуда берутся данные"),
        ("/attribution", "Как ссылаться на QAZ.FUND"),
    ):
        response = client.get(path, params={"lang": "ru"})
        assert response.status_code == 200
        assert marker in response.text
        assert 'data-avds="grant-radar"' in response.text
        assert ".info-layout { align-items: start; min-height: 0; }" in response.text
        assert (
            ".back,.langs a,.footer a{display:inline-flex;align-items:center;min-height:44px}"
            in response.text
        )
        assert (
            ".cards { height: auto; grid-template-rows: none; gap: 12px; }"
            in response.text
        )
        language_nav = response.text.split('<nav class="langs"', 1)[1].split(
            "</nav>", 1
        )[0]
        assert language_nav.index('lang="kk"') < language_nav.index('lang="ru"')
        assert language_nav.index('lang="ru"') < language_nav.index('lang="en"')


def test_sitemap_includes_public_story_pages(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert "/insights?lang=ru" in response.text
    assert "/data-policy?lang=ru" in response.text
    assert "/data-routes?lang=ru" in response.text


def test_sitemap_contains_each_location_once(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    root = ET.fromstring(response.content)
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text for node in root.findall("s:url/s:loc", namespace)]
    assert locations
    assert len(locations) == len(set(locations))


def test_related_opportunities_diversify_sources(monkeypatch):
    _reset_api_state(monkeypatch)
    target = Opportunity(
        source="science_fund",
        source_url="https://example.org/target",
        type=OpportunityType.GRANT,
        title="Kazakhstan science commercialization",
        funder="Science Fund",
        tags=["science", "commercialization", "kazakhstan"],
        score=0.8,
    )
    same_source_rows = [
        Opportunity(
            source="science_fund",
            source_url=f"https://example.org/same-{index}",
            type=OpportunityType.GRANT,
            title=f"Science Fund call {index}",
            funder="Science Fund",
            tags=["science", "kazakhstan"],
            score=0.75 - index * 0.01,
        )
        for index in range(3)
    ]
    other_source = Opportunity(
        source="innovation_agency",
        source_url="https://example.org/other-source",
        type=OpportunityType.GRANT,
        title="University commercialization support",
        funder="Innovation Agency",
        tags=["science", "commercialization", "kazakhstan"],
        score=0.7,
    )
    api_main._cache.extend([target, *same_source_rows, other_source])

    related = api_main._related_opportunities(target, lang="en", limit=3)

    assert len(related) == 3
    assert other_source.id in {item.id for item, _ in related}
    assert len({item.source for item, _ in related}) >= 2


def test_funder_page_renders_public_profile(monkeypatch):
    _reset_api_state(monkeypatch)
    open_item = Opportunity(
        source="science_fund",
        source_url="https://example.org/science/open",
        type=OpportunityType.GRANT,
        title="Open science commercialization",
        summary="Open call for research commercialization teams.",
        funder="Science Fund",
        tags=["science", "commercialization", "kazakhstan"],
        deadline=date(2027, 2, 1),
        score=0.91,
    )
    forecast_item = Opportunity(
        source="science_fund",
        source_url="https://example.org/science/pipeline",
        type=OpportunityType.GRANT,
        title="Pipeline university innovation program",
        summary="Project pipeline for university innovation teams.",
        funder="Science Fund",
        tags=["science", "project_pipeline", "kazakhstan"],
        score=0.72,
    )
    closed_item = Opportunity(
        source="science_fund",
        source_url="https://example.org/science/closed",
        type=OpportunityType.GRANT,
        title="Closed lab capacity grant",
        summary="Recently closed lab support.",
        funder="Science Fund",
        tags=["science"],
        deadline=date(2026, 1, 1),
        score=0.52,
    )
    api_main._cache.extend([open_item, forecast_item, closed_item])
    client = TestClient(api_main.app)

    response = client.get("/funder/science-fund", params={"lang": "ru"})

    assert response.status_code == 200
    assert '<html lang="ru"' in response.text
    assert "<title>Фонд науки – QAZ.FUND</title>" in response.text
    assert "<h1>Фонд науки</h1>" in response.text
    assert "Организация и её программы" in response.text
    assert "--brand: var(--color-accent);" in response.text
    assert "--panel-wash-section:" in response.text
    assert "background: var(--panel-wash-section);" in response.text
    assert "background: var(--panel-wash-card);" in response.text
    assert "border-left: 3px solid color-mix" in response.text
    assert "--av-color-primary-700" not in response.text
    assert "Открытые возможности" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert ".opportunity-card h3 a," in response.text
    assert "Архив" in response.text
    assert (
        "Сведения собраны по опубликованным программам и объявлениям." in response.text
    )
    assert "Форматы:" in response.text
    assert "Основные темы:" in response.text
    assert "Регионы:" in response.text
    assert "science_fund" not in response.text
    assert "opportunitytype." not in response.text.lower()
    assert "Open science commercialization" in response.text
    assert "Pipeline university innovation program" in response.text
    assert "Closed lab capacity grant" in response.text
    assert "Точное" not in response.text
    assert ">0.91<" not in response.text
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in response.text
    assert "Ближайший срок" in response.text
    assert f'href="/opportunity/{open_item.id}?lang=ru"' in response.text
    assert f'href="/opportunity/{forecast_item.id}?lang=ru"' in response.text

    kk_response = client.get("/funder/science-fund", params={"lang": "kk"})
    assert kk_response.status_code == 200
    assert '<html lang="kk"' in kk_response.text
    assert "Қор профилі" in kk_response.text
    assert "Ашық мүмкіндіктер" in kk_response.text
    assert "Деректер мәртебесі" in kk_response.text
    assert "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды." in kk_response.text
    assert "QAZ.FUND не выдаёт средства и не принимает заявки." not in kk_response.text
    assert 'href="/?lang=ru#opportunities"' in response.text
    assert 'class="hero-copy"' in response.text
    assert 'data-avds-component="funder-page"' in response.text
    assert 'data-avds-component="hero-band"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/status?lang=ru"' in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert (
        'rel="alternate" hreflang="en" href="http://testserver/funder/science-fund?lang=en"'
        in response.text
    )
    assert (
        'rel="alternate" hreflang="kk" href="http://testserver/funder/science-fund?lang=kk"'
        in response.text
    )
    assert (
        'href="http://testserver/funder/science-fund?lang=kk" lang="kk">KAZ</a>'
        in response.text
    )
    assert (
        'href="http://testserver/funder/science-fund?lang=ru" lang="ru" '
        'aria-current="page">RU</a>' in response.text
    )
    assert (
        'property="og:image" content="http://testserver/og-image.png?lang=ru"'
        in response.text
    )
    assert (
        'name="twitter:image" content="http://testserver/og-image.png?lang=ru"'
        in response.text
    )
    assert "googletagmanager.com" not in response.text
    assert "mc.yandex.ru" not in response.text
    assert "clarity.ms" not in response.text
    assert '"@type": "Organization"' in response.text
    assert '"@type": "CollectionPage"' in response.text

    kk_response = client.get("/funder/science-fund", params={"lang": "kk"})
    assert kk_response.status_code == 200
    assert '<html lang="kk"' in kk_response.text
    assert 'data-language-fallback="source"' in kk_response.text
    assert (
        'href="http://testserver/funder/science-fund?lang=kk" lang="kk" '
        'aria-current="page">KAZ</a>' in kk_response.text
    )


def test_funder_labels_keep_acronyms_and_normalized_case():
    copy = dashboard_copy("ru")

    assert funder_page_module._label_value("undp_procurement", copy) == "Закупки ПРООН"
    assert funder_page_module._label_value("ebrd_ecepp_procurement", copy) == (
        "Закупки ЕБРР ECEPP"
    )
    assert funder_page_module._label_value("isdb_project_procurement", copy) == (
        "Закупки Исламского банка развития"
    )
    assert funder_page_module._label_value("support_rk", copy) == "Support RK"
    assert (
        funder_page_module._label_value("united nations development programme", copy)
        == "Программа развития ООН (ПРООН)"
    )
    assert funder_page_module._label_value("dod-amraa", copy) == "DOD-AMRAA"
    assert (
        funder_page_module._label_value("national_institutes_of_health", copy)
        == "Национальные институты здравоохранения США (NIH)"
    )
    assert (
        funder_page_module._label_value(
            "national_institutes_of_health", dashboard_copy("en")
        )
        == "National Institutes of Health (NIH)"
    )


def test_funder_topics_do_not_repeat_opportunity_format():
    copy = dashboard_copy("ru")
    funder = {
        "top_types": [OpportunityType.TENDER],
        "top_tags": ["tender", "ebrd", "ecepp", "tender"],
    }

    assert funder_page_module._public_topic_labels(funder, copy) == ["ЕБРР", "ECEPP"]
    assert funder_page_module._overview_sentence(funder, copy) == (
        "Сведения собраны по опубликованным программам и объявлениям. "
        "Форматы: Тендер. "
        "Основные темы: ЕБРР, ECEPP."
    )


def test_root_keeps_metrics_out_of_public_hero(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            Opportunity(
                source="astana_hub",
                source_url="https://example.org/one",
                type=OpportunityType.ACCELERATOR,
                title="One",
                summary="One summary",
                tags=["kz", "startup"],
                score=0.9,
            ),
            Opportunity(
                source="grants_gov",
                source_url="https://example.org/two",
                type=OpportunityType.GRANT,
                title="Two",
                summary="Two summary",
                tags=["us"],
                score=0.1,
            ),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert '<strong id="metric-total">' not in response.text
    assert '<strong id="metric-strong"' not in response.text
    assert '<strong id="metric-sources"' not in response.text
    assert 'data-avds-component="public-summary-strip"' not in response.text


def test_root_keeps_public_hero_quiet_on_cold_start(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert '<strong id="metric-strong"' not in response.text
    assert '<strong id="metric-sources"' not in response.text
    assert 'data-avds-component="public-summary-strip"' not in response.text
    assert 'data-avds-component="quick-links-rail"' not in response.text


def test_large_opportunity_response_supports_gzip(monkeypatch):
    _reset_api_state(monkeypatch)
    api_main._cache.append(
        Opportunity(
            source="astana_hub",
            source_url="https://example.org/large-gzip-response",
            type=OpportunityType.ACCELERATOR,
            title="Large catalog response",
            summary="Central Asia opportunity details. " * 120,
            tags=["kazakhstan", "startup"],
            score=0.9,
        )
    )
    client = TestClient(api_main.app)

    response = client.get(
        "/opportunities",
        params={"include_irrelevant": True},
        headers={"Accept-Encoding": "gzip"},
    )

    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert response.json()[0]["title"] == "Large catalog response"


def test_opportunity_page_prefers_public_base_url(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://qaz.fund")
    item = Opportunity(
        source="google_cloud_startup",
        source_url="https://example.org/startup",
        type=OpportunityType.CLOUD_CREDIT,
        title="Startup credits",
        summary="Infrastructure support for eligible startups.",
        score=0.8,
    )
    api_main._cache.append(item)
    client = TestClient(api_main.app)

    response = client.get(f"/opportunity/{item.id}", params={"lang": "en"})

    assert response.status_code == 200
    assert 'aria-label="Breadcrumbs"' in response.text
    assert (
        'rel="canonical" href="https://qaz.fund/opportunity/'
        f'{item.id}?lang=en"' in response.text
    )
    assert (
        'rel="alternate" hreflang="ru" href="https://qaz.fund/opportunity/'
        f'{item.id}?lang=ru"' in response.text
    )
    assert (
        'rel="alternate" hreflang="kk" href="https://qaz.fund/opportunity/'
        f'{item.id}?lang=kk"' in response.text
    )
    assert (
        'property="og:image" content="https://qaz.fund/opportunity/'
        f"{item.id}/og.png?lang=en&amp;v=" in response.text
    )


def test_og_image_route_supports_get_and_head() -> None:
    client = TestClient(api_main.app)

    response = client.get("/og-image.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in response.text
    assert "QAZ.FUND" in response.text

    head_response = client.head("/og-image.svg")
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("image/svg+xml")

    png_response = client.get("/og-image.png")
    assert png_response.status_code == 200
    assert png_response.headers["content-type"].startswith("image/png")
    assert png_response.content.startswith(b"\x89PNG\r\n\x1a\n")

    png_head_response = client.head("/og-image.png")
    assert png_head_response.status_code == 200
    assert png_head_response.headers["content-type"].startswith("image/png")

    localized = {
        lang: client.get("/og-image.png", params={"lang": lang}).content
        for lang in ("ru", "kk", "en")
    }
    assert all(
        payload.startswith(b"\x89PNG\r\n\x1a\n") for payload in localized.values()
    )
    assert len(set(localized.values())) == 3
    assert (
        client.get("/og-image.png", params={"lang": "invalid"}).content
        == localized["ru"]
    )


def test_opportunity_open_graph_cards_are_unique_raster_assets(monkeypatch) -> None:
    _reset_api_state(monkeypatch)
    first = Opportunity(
        source="official_source",
        source_url="https://example.org/first",
        type=OpportunityType.GRANT,
        title="Компенсация цифровых решений для производственных компаний",
        summary="Возмещение части затрат на внедрение цифровых технологий.",
        amount_max=Decimal("60000000"),
        currency="KZT",
        deadline=date(2026, 9, 30),
        tags=["kazakhstan", "digital"],
        score=0.9,
    )
    second = Opportunity(
        source="agrocredit",
        source_url="https://example.org/second",
        type=OpportunityType.GRANT,
        title="Льготное кредитование животноводства",
        summary="Кредитование откормочных площадок и производителей кормов.",
        deadline=None,
        lifecycle="rolling",
        tags=["kazakhstan", "livestock"],
        score=0.9,
        raw={"deadline_policy": "rolling"},
    )
    api_main._cache.extend([first, second])
    client = TestClient(api_main.app)

    first_page = client.get(f"/opportunity/{first.id}", params={"lang": "ru"})
    second_page = client.get(f"/opportunity/{second.id}", params={"lang": "ru"})
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    first_prefix = f"http://testserver/opportunity/{first.id}/og.png?lang=ru&amp;v="
    second_prefix = f"http://testserver/opportunity/{second.id}/og.png?lang=ru&amp;v="
    assert first_prefix in first_page.text
    assert second_prefix in second_page.text
    assert first_prefix != second_prefix

    first_image = client.get(f"/opportunity/{first.id}/og.png?lang=ru&v=first")
    second_image = client.get(f"/opportunity/{second.id}/og.png?lang=ru&v=second")
    assert first_image.status_code == 200
    assert second_image.status_code == 200
    assert first_image.headers["content-type"].startswith("image/png")
    assert first_image.headers["cache-control"].startswith("public, max-age=3600")
    assert first_image.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert int.from_bytes(first_image.content[16:20], "big") == 1200
    assert int.from_bytes(first_image.content[20:24], "big") == 630
    assert first_image.content != second_image.content

    head_response = client.head(f"/opportunity/{first.id}/og.png?lang=ru&v=first")
    assert head_response.status_code == 200
    assert head_response.headers["content-type"].startswith("image/png")


def test_opportunity_og_uses_localized_facts_and_official_source_domain() -> None:
    contest = Opportunity(
        source="kazakhstan_domestic_support",
        source_url="https://aaiff.ai/",
        type=OpportunityType.CONTEST,
        title="Международный конкурс Astana AI Film Festival",
        summary="Официальный конкурс короткометражных AI-фильмов.",
        amount_max=Decimal("1000000"),
        currency="USD",
        tags=["kazakhstan", "contest"],
        score=0.9,
        raw={"amount_raw": "total prize fund of USD 1,000,000"},
    )
    item = to_opportunity_v1(
        contest,
        source_name="Kazakhstan domestic support",
    )

    assert _amount_text(item, "ru") == "1 000 000 USD"
    assert _source_text(item) == "aaiff.ai"
    assert _facts(item, "ru")[0] == ("Призы", "1 000 000 USD")


def test_opportunity_og_uses_pillow_font_when_host_fonts_are_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(opportunity_og, "_FONT_PATHS", {"regular": (), "bold": ()})
    opportunity_og._font.cache_clear()
    try:
        fallback = opportunity_og._font(25, "bold")
        assert fallback.getbbox("Қазақша кириллица") is not None
    finally:
        opportunity_og._font.cache_clear()


def test_opportunity_detail_endpoint_returns_404_for_unknown_id(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/opportunities/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    assert response.status_code == 404


def test_refresh_is_disabled_without_admin_token(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.post("/refresh")

    assert response.status_code == 404


def test_operator_health_requires_token_and_returns_actionable_summary(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "secret")
    api_main._cache.append(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/stale-operator-item",
            type=OpportunityType.GRANT,
            title="Stale Central Asia grant",
            summary="Grant for Central Asia organizations.",
            tags=["central_asia"],
            score=0.8,
            discovered_at=datetime.now(timezone.utc) - timedelta(days=4),
        )
    )
    api_main._clear_public_items_cache()
    monkeypatch.setattr(
        api_main,
        "_operator_run_rows",
        lambda **_kwargs: [
            {
                "id": 7,
                "source": "pipeline",
                "status": "error",
                "error": "sample failure",
            }
        ],
    )
    client = TestClient(api_main.app)

    assert client.get("/operator/health").status_code == 401
    response = client.get(
        "/operator/health", headers={"Authorization": "Bearer secret"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "attention"
    assert data["catalog_items"] == 1
    assert data["stale_sources"][0]["slug"] == "grants_gov"
    assert data["failed_runs"][0]["error"] == "sample failure"


def test_operator_health_clears_recovered_source_failure(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "secret")
    monkeypatch.setattr(
        api_main,
        "_operator_run_rows",
        lambda **_kwargs: [
            {"id": 9, "source": "unicef_kazakhstan", "status": "ok"},
            {
                "id": 8,
                "source": "unicef_kazakhstan",
                "status": "error",
                "error": "HTTP 403",
            },
        ],
    )
    client = TestClient(api_main.app)

    response = client.get(
        "/operator/health", headers={"Authorization": "Bearer secret"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["failed_runs"] == []
    assert len(data["recent_runs"]) == 2


def test_operator_health_exposes_latest_partial_source_run(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "secret")
    monkeypatch.setattr(
        api_main,
        "_operator_run_rows",
        lambda **_kwargs: [
            {
                "id": 10,
                "source": "kazakhstan_domestic_support",
                "status": "partial",
                "error": "ConnectTimeout: retained official page",
            }
        ],
    )
    client = TestClient(api_main.app)

    response = client.get(
        "/operator/health", headers={"Authorization": "Bearer secret"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "attention"
    assert data["failed_runs"] == []
    assert data["partial_runs"][0]["source"] == "kazakhstan_domestic_support"


def test_operator_run_rows_accepts_success_without_error_text(monkeypatch):
    from types import SimpleNamespace

    from sqlalchemy import (
        Column,
        DateTime,
        Integer,
        MetaData,
        String,
        Table,
        create_engine,
    )

    engine = create_engine("sqlite://")
    metadata = MetaData()
    runs = Table(
        "runs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("source", String),
        Column("started_at", DateTime),
        Column("finished_at", DateTime),
        Column("status", String),
        Column("items_seen", Integer),
        Column("items_new", Integer),
        Column("items_dup", Integer),
        Column("error", String),
    )
    metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(
            runs.insert().values(
                source="grants_gov",
                started_at=now,
                finished_at=now,
                status="ok",
                items_seen=3,
                items_new=2,
                items_dup=1,
                error=None,
            )
        )
    monkeypatch.setattr(
        api_main,
        "_configured_repository",
        lambda: SimpleNamespace(engine=engine),
    )

    rows = api_main._operator_run_rows()

    assert len(rows) == 1
    assert rows[0]["status"] == "ok"
    assert rows[0]["error"] == ""
    checks = api_main._latest_successful_source_checks()
    assert checks["grants_gov"].replace(tzinfo=timezone.utc) == now


def test_refresh_rejects_bad_admin_token(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "secret")
    client = TestClient(api_main.app)

    response = client.post("/refresh", headers={"X-Grant-Radar-Admin-Token": "wrong"})

    assert response.status_code == 401


def test_refresh_accepts_admin_token(monkeypatch):
    _reset_api_state(monkeypatch)
    monkeypatch.setenv("GRANT_RADAR_ADMIN_TOKEN", "secret")

    async def fake_run_all(sources):
        assert sources
        return [
            Opportunity(
                source="memory",
                source_url="https://example.org/refreshed",
                type=OpportunityType.GRANT,
                title="Refreshed item",
                tags=["ai"],
                score=0.8,
            )
        ]

    monkeypatch.setattr(api_main, "run_all", fake_run_all)
    client = TestClient(api_main.app)

    response = client.post("/refresh", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.json() == {"refreshed": 1}
    assert len(api_main._cache) == 1


def test_google_site_verification_file(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/google6ce0cb641d438c0c.html")

    assert response.status_code == 200
    assert response.text == "google-site-verification: google6ce0cb641d438c0c.html"
