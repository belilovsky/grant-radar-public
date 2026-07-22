from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from api import funder_page as funder_page_module
from api import main as api_main
from api import opportunity_page as opportunity_page_module
from api.dashboard import dashboard_copy
from core.db import SqlRepository
from core.models import (
    Opportunity,
    OpportunityDetail,
    OpportunityDetailSection,
    OpportunityMetadataField,
    OpportunityType,
)
from sources.base import GrantRecord


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("GRANT_RADAR_ALLOWED_HOSTS", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_sitemap_cache()
    api_main._clear_public_items_cache()


def test_root_renders_service_landing(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    assert '<html lang="ru"' in response.text
    assert (
        "<title>QAZ.FUND – гранты и меры поддержки для Казахстана</title>"
        in response.text
    )
    assert "\u2014" not in response.text
    assert "fonts.googleapis.com" not in response.text
    assert '--av-font-sans: Arial, "Helvetica Neue", Helvetica' in response.text
    assert 'data-avds="grant-radar"' in response.text
    assert 'data-av-theme="light"' in response.text
    assert "--av-color-background" in response.text
    assert "--av-control-height-md" in response.text
    assert "--av-control-height-lg: 44px;" in response.text
    assert "--av-card-padding-md" in response.text
    assert "--av-font-serif" in response.text
    assert "--button-outline" in response.text
    assert "--badge-outline" in response.text
    assert "--color-focus-ring: var(--av-focus-ring)" in response.text
    assert "--color-bg: var(--av-color-background)" in response.text
    assert "width: min(var(--container-max), calc(100% - 48px));" in response.text
    assert "grid-template-columns: repeat(3, minmax(148px, 196px));" in response.text
    assert "width: fit-content;" in response.text
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in response.text
    assert "font-family: var(--font-sans);" in response.text
    assert "text-transform: uppercase;" not in response.text
    assert "letter-spacing: 0.12em;" not in response.text
    assert "border: 1.5px solid var(--line);" not in response.text
    assert ".source-card {" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert ".utility-link {" in response.text
    message_css = response.text.split(".message {", 1)[1].split("}", 1)[0]
    assert "color: color-mix(in oklab, var(--muted), var(--ink) 18%);" in message_css
    assert "avds-tabs-list" in response.text
    assert "avds-tabs-trigger" in response.text
    assert "avds-field" in response.text
    assert "avds-stat-kpi-card" in response.text
    assert "avds-source-card" in response.text
    assert "avds-source-card__icon" in response.text
    assert "avds-source-card__arrow" in response.text
    assert 'data-avds-component="source-icon"' in response.text
    assert "avds-document-row" in response.text
    assert 'data-avds-component="hero-band"' in response.text
    assert "QAZ.FUND" in response.text
    assert "Публичный навигатор по грантам, субсидиям" in response.text
    assert "Гранты, субсидии и программы поддержки для Казахстана" in response.text
    assert "Что нужно сделать сейчас?" in response.text
    assert "Открыть каталог" in response.text
    assert "Прямое подключение к официальному источнику" in response.text
    assert "Внешний мониторинг и редакционная выборка" in response.text
    assert "Рабочие сценарии" in response.text
    assert "Найти поддержку" in response.text
    assert "Проверить программу" in response.text
    assert "Сроки до месяца" in response.text
    assert "Господдержка РК" in response.text
    assert "Тендеры и закупки" in response.text
    assert 'data-hero-focus="search"' in response.text
    assert 'data-hero-sort="deadline"' in response.text
    assert response.text.index('<div class="hero-points"') < response.text.index(
        '<section\n          class="hero-stage"'
    )
    assert "function pathwayPreviewMarkup" not in response.text
    assert "function themePreviewMarkup" not in response.text
    assert "Дополнительные фильтры" in response.text
    assert "qdev.run" in response.text
    assert "QAZ.FUND не выдаёт гранты и не принимает заявки" in response.text
    assert "Обратная связь" in response.text
    assert "qazfund-opportunities.csv" in response.text
    assert "qazfund-deadlines.ics" in response.text
    assert "grantRadarSavedOpportunities.v1" in response.text
    assert 'id="workspace-backup"' in response.text
    assert 'id="export-workspace"' in response.text
    assert 'id="import-workspace"' in response.text
    assert 'id="workspace-queue"' in response.text
    assert 'id="workspace-queue-list"' in response.text
    assert 'data-avds-component="workspace-queue-item"' in response.text
    assert "function exportWorkspace" in response.text
    assert "function sanitizeWorkspacePayload" in response.text
    assert "function importWorkspace" in response.text
    assert "function renderWorkspaceQueue" in response.text
    assert "workspace_action_preparing" in response.text
    assert "Сохраняется только в этом браузере." in response.text
    assert "Уточнить данные" in response.text
    assert "Рабочие подборки" in response.text
    assert "Сохранить фильтры" in response.text
    assert "Поделиться выдачей" in response.text
    assert "Сроки в календарь" in response.text
    assert "Как использовать QAZ.FUND в работе" in response.text
    assert "Аналитику" in response.text
    assert "Журналисту" in response.text
    assert "Редактору" in response.text
    assert "Юристу" in response.text
    assert "Госслужащему" in response.text
    assert "Подборки для старта" in response.text
    assert "Актуально сейчас" in response.text
    assert "Лучшие сигналы недели" in response.text
    assert "Госсектор и субсидии" in response.text
    assert "Не тянуть с подачей" in response.text
    assert "Маршруты по задачам" in response.text
    assert "По типу проекта" in response.text
    assert "Акселераторы, гранты и облачные кредиты" in response.text
    assert "Субсидии, льготы и меры поддержки РК" in response.text
    assert "Темы для навигации" in response.text
    assert "По направлению" in response.text
    assert "Активные фонды и программы" in response.text
    assert "ИИ, облачные кредиты и цифровые навыки" in response.text
    assert "Инфраструктура, закупки и программы развития" in response.text
    assert "В фокусе сейчас" in response.text
    assert "Что здесь обычно ищут" in response.text
    assert "Лучше всего подходит" in response.text
    assert "ИИ-пилоты и акселераторы" in response.text
    assert "Локальные субсидии и меры РК" in response.text
    assert "Убрать тему" in response.text
    assert "Приоритет: Казахстан и ЦА" in response.text
    assert (
        '<strong id="metric-strong" data-catalog-count="0">0</strong>' in response.text
    )
    assert '<strong id="metric-sources">0</strong>' in response.text
    assert '<strong id="health-status">Каталог доступен</strong>' in response.text
    assert '<strong id="health-items">0</strong>' in response.text
    assert '<strong id="health-sources">0</strong>' in response.text
    assert '<strong id="health-stale-sources">0</strong>' in response.text
    assert 'class="discovery-grid"' in response.text
    assert response.text.index('id="opportunities-panel"') < response.text.index(
        'data-avds-component="discovery-library"'
    )
    assert response.text.index(
        'data-avds-component="discovery-library"'
    ) < response.text.index('data-avds-component="funder-library"')
    assert 'data-avds-component="trust-library"' in response.text
    assert 'data-avds-component="funder-library"' in response.text
    assert 'data-avds-component="methodology-library"' in response.text
    assert 'id="methodology-panel"' in response.text
    assert "Источники и прозрачность" in response.text
    assert response.text.index(
        'data-avds-component="trust-library"'
    ) < response.text.index('data-avds-component="funder-library"')
    assert "Оценка учитывает регион и тему" in response.text
    assert "Это не вероятность одобрения" in response.text
    assert "По приоритету действий" in response.text
    assert "Точность совпадения" not in response.text
    assert "медиа" in response.text
    assert "-webkit-line-clamp: 2;" in response.text
    assert ".hero-band" in response.text
    assert ".hero-grid" in response.text
    assert ".sticky-bar" in response.text
    assert ".spotlight-grid" in response.text
    assert ".spotlight-card" in response.text
    assert ".themes-grid" in response.text
    assert ".theme-card" in response.text
    assert ".pathways-grid" in response.text
    assert ".pathway-card" in response.text
    assert ".topbar-actions" in response.text
    assert ">API</a>" in response.text
    assert "Статус данных" in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert 'href="/status?lang=ru"' in response.text
    assert 'href="/?lang=ru"' in response.text
    assert 'href="/?lang=en"' in response.text
    assert 'name="yandex-verification" content="01df12ab51cd6b70"' in response.text
    assert 'rel="canonical" href="http://testserver/?lang=ru"' in response.text
    assert (
        'rel="alternate" hreflang="ru" href="http://testserver/?lang=ru"'
        in response.text
    )
    assert (
        'rel="alternate" hreflang="en" href="http://testserver/?lang=en"'
        in response.text
    )
    assert (
        'rel="alternate" hreflang="x-default" href="http://testserver/?lang=ru"'
        in response.text
    )
    assert 'property="og:type" content="website"' in response.text
    assert (
        'property="og:title" content="QAZ.FUND – гранты и меры поддержки '
        'для Казахстана"' in response.text
    )
    assert 'property="og:url" content="http://testserver/?lang=ru"' in response.text
    assert (
        'property="og:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert 'name="twitter:card" content="summary_large_image"' in response.text
    assert (
        'name="twitter:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert "googletagmanager.com/gtag/js?id=G-9EF720PSER" in response.text
    assert 'window.ym("109803011","init"' in response.text
    assert "https://www.clarity.ms/tag/x5ualin2jv" in response.text
    assert "const startAnalytics = () =>" in response.text
    assert 'navigator.doNotTrack === "1"' in response.text
    assert "navigator.globalPrivacyControl === true" in response.text
    assert "window.setTimeout(startAnalytics, 20000)" in response.text
    assert 'script async src="https://www.googletagmanager.com' not in response.text
    assert 'type="application/ld+json"' in response.text
    assert '"@type": "FAQPage"' in response.text
    assert '"@type": "CollectionPage"' in response.text
    assert '"numberOfItems": 0' in response.text
    assert '"name": "QAZ.FUND"' in response.text
    assert 'data-view="opportunities"' in response.text
    assert 'data-view="sources"' in response.text
    assert 'data-view="health"' not in response.text
    assert 'data-avds-component="sticky-shell"' in response.text
    assert 'data-avds-component="admin-shell"' in response.text
    assert 'data-avds-component="button"' in response.text
    assert 'data-avds-component="source-card"' in response.text
    assert 'data-avds-component="source-url"' in response.text
    assert 'data-avds-component="source-count"' in response.text
    assert 'data-avds-component="opportunity-card"' in response.text
    assert 'data-avds-component="filter-summary"' in response.text
    assert 'id="source-list"' in response.text
    assert 'id="toggle-sources"' in response.text
    assert 'id="opportunities-list"' in response.text
    assert 'id="load-more-wrap"' in response.text
    assert 'data-avds-component="discovery-library"' in response.text
    assert "Подборки и маршруты" in response.text
    assert 'id="spotlight-grid"' in response.text
    assert 'id="themes-grid"' in response.text
    assert 'id="pathways-grid"' in response.text
    assert 'id="funder-grid"' in response.text
    assert 'id="topic-brief"' in response.text
    assert 'id="save-view"' in response.text
    assert 'id="workspace-filter"' in response.text
    assert 'id="filter-disclosure"' in response.text
    assert 'window.matchMedia("(max-width: 820px)")' in response.text
    assert 'document.documentElement.dataset.compactFilters = "true";' in response.text
    assert 'html[data-compact-filters="true"]' in response.text
    assert 'document.documentElement.removeAttribute("data-compact-filters");' in (
        response.text
    )
    assert 'data-avds-component="mobile-app-bar"' in response.text
    assert 'data-avds-component="mobile-app-navigation"' in response.text
    assert 'data-mobile-view="opportunities"' in response.text
    assert 'data-mobile-view="sources"' in response.text
    assert 'data-mobile-action="saved"' in response.text
    assert 'data-mobile-action="filters"' in response.text
    assert 'id="mobile-filter-trigger"' in response.text
    assert 'id="mobile-filter-backdrop"' in response.text
    assert 'id="mobile-filter-done"' in response.text
    assert "function openMobileFilterSheet" in response.text
    assert "function closeMobileFilterSheet" in response.text
    assert "env(safe-area-inset-bottom)" in response.text
    assert "body.filter-sheet-open" in response.text
    audience_presets = response.text.split('id="audience-presets"', 1)[1].split(
        "</div>", 1
    )[0]
    format_presets = response.text.split('id="format-presets"', 1)[1].split(
        "</div>", 1
    )[0]
    topic_presets = response.text.split('id="topic-presets"', 1)[1].split("</div>", 1)[
        0
    ]
    assert audience_presets.count("<button") == 6
    assert format_presets.count("<button") == 5
    assert topic_presets.count("<button") == 7
    assert 'data-preset-id="all" aria-pressed="true"' in audience_presets
    assert 'id="metric-strong" data-catalog-count=' in response.text
    assert "state.coverage.relevant_open_items" in response.text
    assert 'id="detail-readiness"' in response.text
    assert "function renderDetailReadiness" in response.text
    assert 'role="dialog"' in response.text
    assert 'aria-modal="true"' in response.text
    assert ".detail-drawer[hidden]" in response.text
    assert '$("#main-content").inert = true;' in response.text
    assert 'id="share-view"' in response.text
    assert 'id="saved-view-notice"' in response.text
    assert 'aria-label="Статус подборок"' in response.text
    assert 'aria-live="polite"' in response.text
    assert 'id="detail-drawer"' in response.text
    assert 'id="detail-fit"' in response.text
    assert 'id="detail-fit-summary"' in response.text
    assert 'id="detail-fit-pills"' in response.text
    assert 'id="detail-open-page"' in response.text
    assert 'id="detail-open-source"' in response.text
    assert 'id="detail-open-application"' in response.text
    assert 'id="health-sources"' in response.text
    assert 'value="0.3" selected' in response.text
    assert 'fetchJson("/coverage")' in response.text
    assert 'fetchJson("/sources")' in response.text
    assert "function withLang(path)" in response.text
    assert "function opportunityPageHref(opportunityId)" in response.text
    assert "fetchJson(withLang(`/opportunities/${opportunityId}`))" in response.text
    assert "function humanizeLabel" in response.text
    assert "function sourceDisplayName" in response.text
    assert "function metadataValue(entry)" in response.text
    assert "function formatDeadline" in response.text
    assert "function sourceRefreshInfo" in response.text
    assert "source.last_discovered_at" in response.text
    assert "rankedSources.slice(0, COLLAPSED_SOURCES)" in response.text
    assert 'class="source-freshness ${refresh.tone}"' in response.text
    assert "function normalizedDetailMetadata" in response.text
    assert "function normalizeSearchText" in response.text
    assert "function oneEditAway" in response.text
    assert "function matchesSearchQuery" in response.text
    assert "SEARCH_SYNONYM_GROUPS" in response.text
    assert "return copy.score_exact" in response.text
    assert 'aria-label="${sourceName}"' in response.text
    assert "function localDateISO" in response.text
    assert "function localRelevantBySource" in response.text
    assert "function regionalPriority" in response.text
    assert "function regionalBadgeLabel" in response.text
    assert "function comparePriorityItems" in response.text
    assert "regionalPriority(right) - regionalPriority(left)" not in response.text
    assert "function compareDeadlineItems" in response.text
    assert "function compareUpdatedItems" in response.text
    assert "labelMap[normalizedKey]" in response.text
    assert "copy.label_map || copy.labelMap" in response.text
    assert "return 3;" in response.text
    assert '"grants_gov": "Grants.gov"' in response.text
    assert '"world_bank_kazakhstan": "Всемирный банк Казахстан"' in response.text
    assert '"europe_and_central_asia": "Европа и Центральная Азия"' in response.text
    assert "new Map(" in response.text
    assert (
        "limit=5000&min_score=0&deadline_after=${today}&compact=true" in response.text
    )
    assert (
        "limit=5000&min_score=0&include_irrelevant=true&compact=true" in response.text
    )
    assert 'params.set("lang", copy.lang || "ru");' in response.text
    assert 'id="scope-filter"' in response.text
    assert 'id="lifecycle-filter"' in response.text
    assert 'id="region-filter"' in response.text
    assert 'id="deadline-filter"' in response.text
    assert 'id="sort-filter"' in response.text
    assert 'id="opportunities-description"' in response.text
    assert 'id="audience-presets"' in response.text
    assert 'id="format-presets"' in response.text
    assert 'id="topic-presets"' in response.text
    assert "Для кого" in response.text
    assert "Что ищете" in response.text
    assert "Тема" in response.text
    assert "Регион" in response.text
    assert "Срок" in response.text
    assert "Стартапам" in response.text
    assert "Субсидии и меры" in response.text
    assert "ИИ и цифровые решения" in response.text
    assert "Агро / вет / эко" in response.text
    assert "Все регионы" in response.text
    assert "Бессрочные" in response.text
    assert "Кому подходит" in response.text
    assert "Почему это в фокусе" in response.text
    assert "Локальная мера поддержки для команд и бизнеса" in response.text
    assert "Подходит командам, которые работают с госсектором" in response.text
    assert "Быстрая оценка" in response.text
    assert "Критерии нужно уточнить" in response.text
    assert "Попробуйте ослабить один из фильтров" in response.text
    assert "Сбросить всё" in response.text
    assert "Открыть весь индекс" in response.text
    assert "Быстрый просмотр" in response.text
    assert "Официальный источник" in response.text
    assert "Полная карточка" in response.text
    assert '"read_more": "Полная карточка"' in response.text
    assert '"kz": "Казахстан"' in response.text
    assert '"program": "Программа"' in response.text
    assert '"education_organisation": "Образовательные организации"' in response.text
    assert 'value="all">Весь индекс' in response.text
    assert "state.includeArchived" in response.text
    assert "const ALL_INDEX_SCORE = 0;" in response.text
    assert "function scoreDefaultForScope()" in response.text
    assert "state.minScore = scoreDefaultForScope();" in response.text
    assert "state.minScore = [0, 0.3, 0.5, 0.7].includes(score)" in response.text
    assert 'audience: "all"' in response.text
    assert 'format: "all"' in response.text
    assert 'topic: "all"' in response.text
    assert 'lifecycle: "all"' in response.text
    assert 'region: "all"' in response.text
    assert 'deadlineMode: "all"' in response.text
    assert "const AUDIENCE_PRESETS = [" in response.text
    assert "const SUPPORT_FORMAT_TAGS = [" in response.text
    assert "const FORMAT_PRESETS = [" in response.text
    assert "&& !matchesAnyTag(item, SUPPORT_FORMAT_TAGS)" in response.text
    assert '&& !matchesAnyTag(item, ["grant"])' in response.text
    assert "const TOPIC_PRESETS = [" in response.text
    assert "const LIFECYCLE_FILTERS = [" in response.text
    assert "const REGION_FILTERS = [" in response.text
    assert "const DEADLINE_FILTERS = [" in response.text
    assert "function itemLifecycle(item)" in response.text
    assert "function funderPageHref(funderSlugValue)" in response.text
    assert "function renderFunders()" in response.text
    assert "function fitPills(item)" in response.text
    assert "function fitSummaryText(item)" in response.text
    assert "function isStartupAudience(item)" in response.text
    assert "function isFarmerAudience(item)" in response.text
    assert "function isPublicSectorOpportunity(item)" in response.text
    assert "function opportunitySignalText(item)" in response.text
    assert "function opportunityFormatLabel(item)" in response.text
    assert "function opportunitySignalPillsMarkup(item)" in response.text
    assert "function externalActionUrl(item)" in response.text
    assert "function primaryActionUrl(item)" in response.text
    assert "raw.application_url" in response.text
    assert 'href="${pageUrl}"' in response.text
    assert "function renderDetailFit(item)" in response.text
    assert "function renderSpotlights()" in response.text
    assert (
        "function takeUniqueSpotlightPreview(items, usedKeys, count = 3)"
        in response.text
    )
    assert "function renderThemes()" in response.text
    assert "function themeCardMarkup(config)" in response.text
    assert "function activeTopicBrief()" in response.text
    assert "function topicPriorityScore(item)" in response.text
    assert "function compareVisibleItems(left, right)" in response.text
    assert "function renderTopicBrief(items)" in response.text
    assert "function renderPathways()" in response.text
    assert "function pathwayCardMarkup(config)" in response.text
    assert "function spotlightCardMarkup(config)" in response.text
    assert "function heroActionAttributes(action = {})" in response.text
    assert "function renderEmptyState()" in response.text
    assert "function applyEmptyAction(actionId)" in response.text
    assert "function applyHeroAction(button)" in response.text
    assert 'data-avds-component="fit-pill"' in response.text
    assert "color: color-mix(in oklab, var(--muted), var(--ink) 18%);" in response.text
    assert 'href="#methodology-panel"' in response.text
    assert 'id="methodology-panel"' in response.text
    assert "Как мы собираем и показываем данные" in response.text
    assert "Как это работает" in response.text
    assert 'data-avds-component="signal-pill"' in response.text
    assert "function renderPresetControls()" in response.text
    assert 'data-preset-kind="audience"' in response.text
    assert 'data-preset-kind="format"' in response.text
    assert 'data-preset-kind="topic"' in response.text
    assert 'data-avds-component="preset-button"' in response.text
    assert "function syncUrlState()" in response.text
    assert 'params.set("audience", state.audience);' in response.text
    assert 'params.set("format", state.format);' in response.text
    assert 'params.set("topic", state.topic);' in response.text
    assert 'params.set("lifecycle", state.lifecycle);' in response.text
    assert 'params.set("region", state.region);' in response.text
    assert 'params.set("deadline", state.deadlineMode);' in response.text
    assert 'params.set("lang", copy.lang || "ru");' in response.text
    assert "function applyStateFromUrl()" in response.text
    assert "state.topic = TOPIC_PRESETS.some" in response.text
    assert "state.lifecycle = LIFECYCLE_FILTERS.some" in response.text
    assert "state.region = REGION_FILTERS.some" in response.text
    assert "state.deadlineMode = DEADLINE_FILTERS.some" in response.text
    assert "copy.opportunities_description_all" in response.text
    assert "sourceBadge(source)" in response.text
    assert "shortUrl(source.base_url)" in response.text
    assert 'data-empty-action="' in response.text
    assert 'data-hero-view="opportunities"' in response.text
    assert 'data-hero-reset="true"' in response.text
    assert 'data-hero-focus="search"' in response.text
    assert 'data-hero-deadline="month"' in response.text
    assert 'data-hero-format="support"' in response.text
    assert "data-hero-topic" in response.text
    assert 'data-avds-component="spotlight-grid"' in response.text
    assert 'data-avds-component="spotlight-card"' in response.text
    assert 'data-avds-component="themes-grid"' in response.text
    assert 'data-avds-component="theme-card"' in response.text
    assert 'data-avds-component="topic-brief"' in response.text
    assert 'data-avds-component="topic-chip"' in response.text
    assert 'data-avds-component="pathways-grid"' in response.text
    assert 'data-avds-component="pathway-card"' in response.text
    assert 'data-topic-reset="true"' in response.text
    assert response.text.count("const total = state.sources.length;") == 1
    assert (
        "...state.sources.map((source) => source.slug).filter(Boolean)" in response.text
    )
    assert "itemBadges(item)" in response.text
    assert "copy.reload_confirm" in response.text
    assert "Казахстан в приоритете" in response.text
    assert "Показать ещё" in response.text
    assert "renderSavedViews();" in response.text
    assert "grantRadarOpportunityWorkflow.v1" in response.text
    assert "function renderWorkspaceFilter()" in response.text
    assert "function setOpportunityWorkflowStatus" in response.text
    assert 'data-workflow-status="${opportunityId}"' in response.text
    assert "function setSavedViewNotice(message)" in response.text
    assert "setSavedViewNotice(copy.saved_view_saved);" in response.text
    assert "setSavedViewNotice(copy.saved_view_removed);" in response.text
    assert "setSavedViewNotice(copy.saved_view_shared);" in response.text
    assert "window.alert(" not in response.text
    assert "window.prompt(copy.saved_view_share_prompt, href);" in response.text
    assert 'aria-pressed="true"' in response.text
    assert "goToView(button.dataset.view)" in response.text
    assert "function goToView(view, options = {})" in response.text
    assert 'const trustLibrary = $("#trust-library");' in response.text
    assert "trustLibrary.open = true;" in response.text
    assert 'function openTrustDisclosure(targetId = "")' in response.text
    assert "methodologyLibrary.open = true;" in response.text
    assert "function syncViewFromHash" in response.text
    assert "function scheduleHashViewSync" in response.text
    assert "const shouldScroll = options.scroll !== false;" in response.text
    assert "document.getElementById(view)?.scrollIntoView" in response.text
    assert "syncViewFromHash({ scroll: false })" in response.text
    assert "function scheduleOpportunityRender" in response.text
    assert (
        'function openOpportunityDetail(opportunityId, fallbackUrl = "")'
        in response.text
    )
    assert "data-opportunity-detail" in response.text
    assert "detail_meta_labels" in response.text
    assert "content-visibility: auto;" not in response.text
    assert "contain-intrinsic-size:" not in response.text
    assert ".opportunity {" in response.text
    opportunity_css = response.text.split(".opportunity {", 1)[1].split("}", 1)[0]
    assert "border: 0;" in opportunity_css
    assert "border-top: 1px solid var(--line);" in opportunity_css
    assert "border-left:" not in opportunity_css
    assert ".opportunity-content {" in response.text
    assert ".opportunity-rail {" in response.text
    assert 'class="opportunity-rail"' in response.text
    assert 'class="opportunity-summary"' in response.text
    assert "Параметры" in response.text
    assert ".signal-box" in response.text
    assert ".signal-pill" in response.text
    assert ".topic-brief" in response.text
    assert ".topic-brief-chip" in response.text
    assert "@media (max-width: 820px)" in response.text
    assert ".sticky-shell {\n        display: none;" in response.text
    assert "backdrop-filter: blur(18px);" in response.text
    assert 'window.addEventListener("hashchange", syncViewFromHash)' in response.text
    assert 'window.addEventListener("resize", scheduleHashViewSync)' in response.text
    assert "window.requestAnimationFrame(syncViewFromHash)" in response.text
    assert 'href="/opportunities?limit=20"' not in response.text


def test_browser_404_is_branded_while_api_404_stays_json(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    browser_response = client.get(
        "/missing-public-page?lang=en",
        headers={"Accept": "text/html"},
    )
    api_response = client.get(f"/opportunities/{uuid4()}")

    assert browser_response.status_code == 404
    assert browser_response.headers["content-type"].startswith("text/html")
    assert browser_response.headers["x-robots-tag"] == "noindex, follow"
    assert "This page does not exist" in browser_response.text
    assert 'meta name="description"' in browser_response.text
    assert 'href="/?lang=en"' in browser_response.text
    assert 'class="primary-action"' in browser_response.text
    assert ".primary-action {" in browser_response.text
    assert "grid-template-rows: auto 1fr auto;" in browser_response.text
    assert 'class="brand"' in browser_response.text
    assert "contact@qaz.fund" not in browser_response.text
    assert api_response.status_code == 404
    assert api_response.headers["content-type"].startswith("application/json")


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
    assert 'href="/grant-radar/docs?lang=ru"' in response.text
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
    assert '<main id="swagger-ui"></main>' in response.text
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
    assert '"deepLinking": false' in response.text


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

    assert '<details class="section-card source-disclosure">' in markup
    assert '<span class="source-disclosure-title">Выдержка с источника</span>' in markup
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
    assert '<details class="section-card source-disclosure">' in markup


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

    assert "QAZ.FUND – рабочая справка" in brief
    assert "Организатор или источник: Официальная программа" in brief
    assert "Регион: Казахстан" in brief
    assert "Сумма: 10 000 000 KZT" in brief
    assert "Официальный источник: https://example.kz/program" in brief
    assert "Подача: https://example.kz/program/apply" in brief
    assert "Проверить на официальном источнике" in brief


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

    assert response.status_code == 200
    assert "sort(compareItems)" not in response.text
    assert "sort(comparePriorityItems)" in response.text


def test_root_supports_explicit_english_dashboard(monkeypatch):
    _reset_api_state(monkeypatch)
    client = TestClient(api_main.app)

    response = client.get("/?lang=en")

    assert response.status_code == 200
    assert '<html lang="en"' in response.text
    assert (
        "<title>QAZ.FUND – funding and support programs for Kazakhstan</title>"
        in response.text
    )
    assert "\u2014" not in response.text
    assert (
        "Public funding navigator for grants, subsidies, accelerators" in response.text
    )
    assert "Grants, subsidies and support programs for Kazakhstan" in response.text
    assert "What people usually look for" in response.text
    assert "Clear theme" in response.text
    assert "What do you need to do now?" in response.text
    assert "Find support" in response.text
    assert "Check a program" in response.text
    assert "Deadlines this month" in response.text
    assert "Tenders and procurement" in response.text
    assert "How to use QAZ.FUND at work" in response.text
    assert "For analysts" in response.text
    assert "For journalists" in response.text
    assert "For editors" in response.text
    assert "For legal review" in response.text
    assert "For public-sector teams" in response.text
    assert "Priority: Kazakhstan and Central Asia" in response.text
    assert ">API</a>" in response.text
    assert "Data status" in response.text
    assert "Theme" in response.text
    assert "Region" in response.text
    assert "Timing" in response.text
    assert "All regions" in response.text
    assert "Rolling" in response.text
    assert "Open catalog" in response.text
    assert '<strong id="health-status">Catalog available</strong>' in response.text
    assert "Current opportunities" in response.text
    assert "Best signals this week" in response.text
    assert "Support for businesses and teams" in response.text
    assert "By project type" in response.text
    assert "Accelerators, grants and cloud credits" in response.text
    assert "Theme routes" in response.text
    assert "By focus area" in response.text
    assert "AI programs, cloud credits, and digital skills" in response.text
    assert "AI and digital" in response.text
    assert "Why this is worth a look" in response.text
    assert "Useful for product and AI teams" in response.text
    assert "Useful for teams working with public sector delivery" in response.text
    assert "Try relaxing one of the filters" in response.text
    assert 'rel="canonical" href="http://testserver/?lang=en"' in response.text
    assert "Load more" in response.text
    assert 'aria-label="Saved collection status"' in response.text
    assert "Copy the link to the current collection" in response.text
    assert "Next actions" in response.text
    assert "Stored only in this browser." in response.text
    assert "Check the criteria on the official source." in response.text


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
    assert "Source status page: http://testserver/status" in llms.text
    assert "Coverage JSON: http://testserver/coverage" in llms.text
    assert "Opportunities JSON: http://testserver/opportunities" in llms.text
    assert "Opportunities NDJSON: http://testserver/opportunities.ndjson" in llms.text
    assert (
        "Compact Opportunities NDJSON: "
        "http://testserver/opportunities.ndjson?compact=true"
    ) in llms.text
    assert "## AI consumption guidance" in llms.text
    assert "Prefer compact Opportunities NDJSON for bulk discovery reads" in llms.text
    assert "Opportunity detail JSON: /opportunities/{id}?lang=ru|en" in llms.text
    assert "Digest JSON: http://testserver/digest" in llms.text
    assert "Opportunity page: /opportunity/{id}?lang=ru|en" in llms.text
    assert "Funder page: /funder/{slug}?lang=ru|en" in llms.text
    assert "Opportunities filters: q, source, lifecycle, region, tag" in llms.text
    assert "evidence_state=sourced means that a direct public source link" in llms.text
    llms_head = client.head("/llms.txt")
    assert llms_head.status_code == 200
    assert llms_head.headers["content-type"].startswith("text/plain")
    assert llms_head.headers["cache-control"].startswith("public, max-age=300")

    discovery = client.get("/site-discovery.json")
    assert discovery.status_code == 200
    assert discovery.headers["content-type"].startswith("application/json")
    assert discovery.headers["cache-control"].startswith("public, max-age=300")
    assert discovery.json() == {
        "site": "QAZ.FUND",
        "type": "public-funding-navigator",
        "home": "http://testserver/",
        "sitemap": "http://testserver/sitemap.xml",
        "llms": "http://testserver/llms.txt",
        "api_docs": "http://testserver/docs",
        "openapi": "http://testserver/openapi.json",
        "source_status": "http://testserver/status",
        "ecosystem": "http://testserver/.well-known/qdev-ecosystem.json",
        "release": "http://testserver/.well-known/release.json",
        "contracts": {
            "qazstack": ("http://testserver/.well-known/qazstack-consumer.json"),
            "avds4": "http://testserver/.well-known/avds-ui-contract.json",
        },
        "languages": ["ru", "en"],
        "routes": {
            "home": "/?lang={lang}",
            "coverage": "/coverage",
            "source_status": "/status?lang={lang}",
            "opportunities": "/opportunities?lang={lang}",
            "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
            "opportunities_ndjson_compact": (
                "/opportunities.ndjson?lang={lang}&compact=true"
            ),
            "opportunity_api": "/opportunities/{id}?lang={lang}",
            "opportunity": "/opportunity/{id}?lang={lang}",
            "funder": "/funder/{slug}?lang={lang}",
            "digest": "/digest?lang={lang}",
        },
        "data_endpoints": {
            "coverage": "http://testserver/coverage",
            "opportunities": "http://testserver/opportunities",
            "opportunities_ndjson": "http://testserver/opportunities.ndjson",
            "opportunities_ndjson_compact": (
                "http://testserver/opportunities.ndjson?compact=true"
            ),
            "digest": "http://testserver/digest",
        },
        "ai_consumption": {
            "preferred_bulk_export": (
                "http://testserver/opportunities.ndjson?compact=true"
            ),
            "preferred_detail_template": "/opportunities/{id}?lang=ru|en",
            "preferred_human_template": "/opportunity/{id}?lang=ru|en",
            "recommended_language_order": ["ru", "en"],
            "cache_policy": {
                "discovery_seconds": 300,
                "catalog_seconds": 60,
                "ndjson_seconds": 300,
            },
            "public_evidence_fields": [
                "source",
                "source_url",
                "discovered_at",
                "deadline",
                "score",
                "evidence_state",
                "raw.decision_readiness",
                "raw.ranking",
            ],
            "do_not_infer": [
                "eligibility",
                "deadline",
                "award amount",
                "application result",
            ],
        },
        "query_templates": {
            "opportunities_recent": (
                "/opportunities?lang=ru&limit=50&min_score=0.5"
                "&deadline_after={yyyy-mm-dd}"
            ),
            "opportunities_by_tag": "/opportunities?lang=ru&limit=50&tag={tag}",
            "opportunities_search": "/opportunities?lang=ru&limit=50&q={query}",
            "opportunities_by_source": (
                "/opportunities?lang=ru&limit=50&source={source}"
            ),
            "opportunities_by_lifecycle": (
                "/opportunities?lang=ru&limit=50&lifecycle={lifecycle}"
            ),
            "opportunities_ai_export": (
                "/opportunities.ndjson?lang=ru&limit=500&min_score=0.3" "&compact=true"
            ),
            "digest_ai": "/digest?lang=ru&limit=5&tag=ai",
        },
        "capabilities": [
            "public opportunity pages",
            "public funder pages",
            "machine-readable opportunity api",
            "cache-aware ndjson export",
            "machine-readable source coverage",
            "public source freshness status",
            "official source links",
            "read-only public catalog",
            "qdev ecosystem contract",
        ],
    }
    discovery_head = client.head("/site-discovery.json")
    assert discovery_head.status_code == 200
    assert discovery_head.headers["content-type"].startswith("application/json")
    assert discovery_head.headers["cache-control"].startswith("public, max-age=300")

    qazstack_contract = client.get("/.well-known/qazstack-consumer.json")
    assert qazstack_contract.status_code == 200
    assert qazstack_contract.json()["schema_version"] == "qazstack-consumer-v1"
    assert qazstack_contract.json()["qazstack_version"] == "1.40.0"
    assert qazstack_contract.json()["source_revision"] == (
        "a0a4bfc6ea6b2fce205afe24fbf732fb3de3bc68"
    )
    assert qazstack_contract.json()["integration_mode"] == "python-package"
    assert qazstack_contract.json()["evidence"]["environment"] == "production"
    assert qazstack_contract.json()["evidence"]["source_revision"] == (
        qazstack_contract.json()["source_revision"]
    )
    assert client.head("/.well-known/qazstack-consumer.json").status_code == 200

    avds_contract = client.get("/.well-known/avds-ui-contract.json")
    assert avds_contract.status_code == 200
    assert avds_contract.json()["schema_version"] == "avds-ui-contract-v1"
    assert avds_contract.json()["avds_source"] == {
        "site": "https://ui.qdev.run",
        "package": "@sgeo/ui-kit",
        "version": "4.3.2",
    }
    assert avds_contract.json()["runtime_neutral_patterns"] == {
        "package": "@av/patterns",
        "version": "0.1.0",
        "adopted": [
            "evidence-summary",
            "filter-state-summary",
            "decision-summary",
        ],
        "rendering": "server-rendered-local-adapter",
        "calculation_ownership": "qaz-fund",
    }
    assert client.head("/.well-known/avds-ui-contract.json").status_code == 200

    ecosystem = client.get("/.well-known/qdev-ecosystem.json")
    assert ecosystem.status_code == 200
    ecosystem_payload = ecosystem.json()
    assert ecosystem_payload["integrations"]["qazstack"]["status"] == ("runtime-proven")
    assert ecosystem_payload["integrations"]["qazlake"]["direct_write"] is False
    assert ecosystem_payload["integrations"]["qazgeo"]["status"] == (
        "deferred-no-geometry"
    )
    assert ecosystem_payload["integrations"]["qazcompute"]["status"] == (
        "candidate-not-enabled"
    )
    assert client.head("/.well-known/qdev-ecosystem.json").status_code == 200

    release = client.get("/.well-known/release.json")
    assert release.status_code == 200
    assert release.json() == {
        "service": "qaz-fund",
        "revision": "development",
        "deployed_at": None,
    }
    assert release.headers["cache-control"] == "no-store"
    assert client.head("/.well-known/release.json").status_code == 200
    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg+xml")
    assert favicon.headers["cache-control"].startswith("public, max-age=3600")
    assert "<svg" in favicon.text
    favicon_head = client.head("/favicon.ico")
    assert favicon_head.status_code == 200
    assert favicon_head.headers["content-type"].startswith("image/svg+xml")
    assert favicon_head.headers["cache-control"].startswith("public, max-age=3600")

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
    monkeypatch.setenv("APP_DEPLOYED_AT", "2026-07-15T17:51:42Z")
    client = TestClient(api_main.app)

    release = client.get("/.well-known/release.json")

    assert release.json() == {
        "service": "qaz-fund",
        "revision": "a" * 40,
        "deployed_at": "2026-07-15T17:51:42Z",
    }

    monkeypatch.setenv("APP_REVISION", "not-a-release")
    assert client.get("/.well-known/release.json").json()["revision"] == ("development")


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
    assert data["stale_sources"] == 0
    assert data["unknown_freshness_sources"] >= 1
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
    assert 'class="status-topbar"' in response.text
    assert 'class="lang-switch"' in response.text
    assert 'href="/status?lang=en"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert "min-height:var(--av-control-height-lg);" in response.text
    assert ".status-topbar .back" in response.text
    assert "--av-container-dashboard: 1280px" in response.text
    assert "World Bank Kazakhstan" in response.text
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
    assert '<label for="token">Операторский токен</label>' in response.text
    assert 'class="lang-switch"' in response.text
    assert 'href="/operator?lang=en"' in response.text
    assert "X-Grant-Radar-Admin-Token" in response.text
    assert "sessionStorage" in response.text
    assert 'autocomplete="username"' in response.text
    assert 'autocomplete="current-password"' in response.text
    assert ".auth-controls > :is(input, button)" in response.text
    assert ".catalog-link" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert "server-only-secret" not in response.text
    head_response = client.head("/operator?lang=en")
    assert head_response.status_code == 200
    assert head_response.headers["cache-control"] == "no-store"


def test_source_freshness_marks_old_and_missing_timestamps():
    old = datetime.now(timezone.utc) - timedelta(hours=96)

    assert api_main._source_freshness(None) == {
        "freshness_status": "unknown",
        "age_hours": None,
    }
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
    assert data["items"][0]["title"] == "Google for Startups Cloud Program"
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
    assert {key: value for key, value in raw.items() if key != "ranking"} == {
        "external_id": "RAW-1",
        "agency": "Example Agency",
        "decision_readiness": {
            "status": "partial",
            "known_fields": 1,
            "total_fields": 4,
            "missing_fields": ["deadline", "amount", "eligibility"],
        },
    }
    assert raw["ranking"]["model_version"] == "qazfund-relevance-v2"
    assert "source_url" not in raw


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
    assert {key: value for key, value in raw.items() if key != "ranking"} == {
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
    assert ranking["model_version"] == "qazfund-relevance-v2"
    assert ranking["relevance"] == data[0]["score"]


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

    def fake_coverage(items, source_checks):
        calls["count"] += 1
        assert items == [item]
        assert source_checks == {}
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
        eligibility=["Registered NGOs"],
        tags=["kazakhstan", "digitalization", "project_pipeline"],
        score=0.92,
        raw={
            "project_id": "P179204-PAGE",
            "borrower": "Republic of Kazakhstan",
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
    assert '<html lang="ru"' in response.text
    assert "<title>Цифровое ускорение Казахстана – QAZ.FUND</title>" in response.text
    assert (
        'rel="canonical" href="http://testserver/opportunity/'
        f'{item.id}?lang=ru"' in response.text
    )
    assert "Поддержка цифровой инфраструктуры и инклюзивного доступа." in response.text
    assert "Что финансируется" in response.text
    assert "Зарегистрированные НПО" in response.text
    assert "Что подготовить" in response.text
    assert "Проверьте критерии" in response.text
    assert "Соберите проектную заявку" in response.text
    assert "Как подать" in response.text
    assert "Скопировать справку" in response.text
    assert 'id="copy-working-brief"' in response.text
    assert 'id="copy-working-brief-status"' in response.text
    assert "Рабочая справка скопирована." in response.text
    assert "Перед использованием карточки" in response.text
    assert "Право на участие" in response.text
    assert "Закупочная документация" in response.text
    assert "Публикация и служебная записка" in response.text
    assert "не подтверждает право на участие" in response.text
    assert "QAZ.FUND – рабочая справка" in response.text
    assert "Проверить на официальном источнике" in response.text
    assert "Откройте страницу подачи" in response.text
    assert "Сверьте критерии" in response.text
    assert (
        "Описание и ключевые поля собраны с официального источника" not in response.text
    )
    assert "Статус источника" not in response.text
    assert "<strong>Точное</strong>" not in response.text
    assert ">0.92<" not in response.text
    assert response.text.index("Что финансируется") < response.text.index(
        "Что подготовить"
    )
    assert "Быстрая оценка" not in response.text
    assert "structured_only" not in response.text
    assert "English source page title" not in response.text
    assert "deadline is October" not in response.text
    assert 'href="https://example.org/project/P179204-page"' in response.text
    assert 'href="https://example.org/apply/P179204-page"' in response.text
    assert 'href="/?lang=ru#opportunities"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/status?lang=ru"' in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert 'aria-label="Навигационная цепочка"' in response.text
    assert 'class="hero-fact hero-fact--source"' in response.text
    assert ".hero-actions .button" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    hero_actions = response.text.split('<div class="hero-actions">', 1)[1].split(
        "</div>", 1
    )[0]
    assert 'href="/?lang=ru#opportunities"' not in hero_actions
    assert (
        'class="button primary" href="https://example.org/project/P179204-page"'
        in response.text
    )
    assert (
        'property="og:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert (
        'name="twitter:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert "googletagmanager.com/gtag/js?id=G-9EF720PSER" in response.text
    assert '"@type": "BreadcrumbList"' in response.text
    assert '"identifier": "' in response.text
    assert '"sameAs": "https://example.org/project/P179204-page"' in response.text

    head_response = client.head(f"/opportunity/{item.id}", params={"lang": "ru"})
    assert head_response.status_code == 200


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
    assert "<strong>UNESCO IITE</strong>" in response.text
    assert '<aside class="sidebar-card">' not in response.text
    assert "<span>Фонд</span>" not in response.text
    assert "<strong>13.07.2026</strong>" in response.text

    detail_head = client.head(f"/opportunities/{item.id}", params={"lang": "ru"})
    assert detail_head.status_code == 200


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
    assert '<html lang="ru"' in response.text
    assert "Фонд науки" in response.text

    head_response = client.head("/funder/science-fund")
    assert head_response.status_code == 200


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


def test_opportunity_page_tailors_prepare_checklist_for_subsidies(monkeypatch):
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
    assert "What to prepare" in response.text
    assert "Copy working brief" in response.text
    assert "Before using this card" in response.text
    assert "Procurement documents" in response.text
    assert "does not confirm eligibility" in response.text
    assert "Prepare local documents" in response.text
    assert "Check company status, digital signature, tax status" in response.text
    assert "Check current terms" in response.text


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
            "i18n": {
                "ru": {
                    "title": "Прикладной грант для лабораторий",
                    "summary": "Поддержка прикладных исследований и лабораторий.",
                }
            }
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
    assert f'href="/opportunity/{same_source.id}?lang=en"' in response.text
    assert f'href="/opportunity/{same_theme.id}?lang=en"' in response.text
    assert "Road corridor procurement" not in response.text

    ru_response = client.get(f"/opportunity/{target.id}", params={"lang": "ru"})

    assert ru_response.status_code == 200
    assert "Похожие возможности" in ru_response.text
    assert "Прикладной грант для лабораторий" in ru_response.text
    assert "Поддержка университетских инноваций доступна для команд" in ru_response.text
    assert "Поддержка прикладных исследований и лабораторий." in ru_response.text
    assert "Applied labs grant" not in ru_response.text
    assert "University innovation support" not in ru_response.text


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
    assert "Профиль фонда" in response.text
    assert "--brand: var(--color-accent);" in response.text
    assert "--av-color-primary-700" not in response.text
    assert "Живые и рабочие возможности" in response.text
    assert "min-height: var(--av-control-height-lg);" in response.text
    assert "Архив и исторический след" in response.text
    assert (
        "Профиль построен по опубликованным программам и объявлениям." in response.text
    )
    assert "Форматы:" in response.text
    assert "Основные темы:" in response.text
    assert "Фокус по регионам:" in response.text
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
    assert 'href="/?lang=ru#opportunities"' in response.text
    assert 'class="hero-copy"' in response.text
    assert 'class="site-footer-nav"' in response.text
    assert 'href="/?lang=ru#sources"' in response.text
    assert 'href="/status?lang=ru"' in response.text
    assert 'href="/docs?lang=ru"' in response.text
    assert (
        'rel="alternate" hreflang="en" href="http://testserver/funder/science-fund?lang=en"'
        in response.text
    )
    assert (
        'property="og:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert (
        'name="twitter:image" content="http://testserver/og-image.svg"' in response.text
    )
    assert "googletagmanager.com/gtag/js?id=G-9EF720PSER" in response.text
    assert '"@type": "Organization"' in response.text
    assert '"@type": "CollectionPage"' in response.text


def test_funder_labels_keep_acronyms_and_normalized_case():
    copy = dashboard_copy("ru")

    assert (
        funder_page_module._label_value("undp_procurement", copy) == "UNDP Procurement"
    )
    assert funder_page_module._label_value("ebrd_ecepp_procurement", copy) == (
        "EBRD ECEPP Procurement"
    )
    assert funder_page_module._label_value("support_rk", copy) == "Support RK"
    assert (
        funder_page_module._label_value("united nations development programme", copy)
        == "Программа развития ООН (ПРООН)"
    )
    assert funder_page_module._label_value("dod-amraa", copy) == "DOD-AMRAA"


def test_funder_topics_do_not_repeat_opportunity_format():
    copy = dashboard_copy("ru")
    funder = {
        "top_types": [OpportunityType.TENDER],
        "top_tags": ["tender", "ebrd", "ecepp", "tender"],
    }

    assert funder_page_module._public_topic_labels(funder, copy) == ["ЕБРР", "ECEPP"]
    assert funder_page_module._overview_sentence(funder, copy) == (
        "Профиль построен по опубликованным программам и объявлениям. "
        "Форматы: Тендер. "
        "Основные темы: ЕБРР, ECEPP."
    )


def test_root_renders_initial_metrics_from_cached_items(monkeypatch):
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
    assert '<strong id="metric-total">2</strong>' in response.text
    assert (
        '<strong id="metric-strong" data-catalog-count="1">1</strong>' in response.text
    )
    assert '<strong id="metric-sources">2</strong>' in response.text
    assert '<strong id="health-items">2</strong>' in response.text
    assert '<strong id="health-sources">2</strong>' in response.text


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
        'property="og:image" content="https://qaz.fund/og-image.svg"' in response.text
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
        lambda limit=50: [
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
