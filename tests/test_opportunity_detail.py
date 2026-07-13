from __future__ import annotations

import httpx
import pytest

from api import opportunity_detail as detail_api
from core.models import Opportunity, OpportunityType

respx = pytest.importorskip("respx")


@pytest.fixture(autouse=True)
def _clear_detail_cache() -> None:
    detail_api._DETAIL_CACHE.clear()


def test_extract_remote_sections_groups_headings_and_paragraphs():
    html = """
    <html>
      <body>
        <main>
          <h1>Programme overview</h1>
          <p>Support for civic and digital projects in Kazakhstan.</p>
          <p>Applicants can use the route for pilot deployments.</p>
          <h2>Who can apply</h2>
          <ul>
            <li>NGOs</li>
            <li>Universities</li>
          </ul>
        </main>
      </body>
    </html>
    """

    sections, excerpt_only = detail_api._extract_remote_sections(html)

    assert excerpt_only is False
    assert sections[0].heading == "Programme overview"
    assert "Support for civic and digital projects" in sections[0].text
    assert sections[1].heading == "Who can apply"
    assert "NGOs" in sections[1].text
    assert "Universities" in sections[1].text


def test_extract_remote_sections_skips_agrocredit_navigation_noise():
    html = """
    <html>
      <body>
        <main>
          <p>
            1408 Call Center About the company Strategy, mission, vision
            Corporate structure The Board of Directors Organizational structure
            Corporate governance Open an account online ForteBank
          </p>
          <h1>Аграрная кредитная корпорация запускает новую программу кредитования</h1>
          <p>Новая программа направлена на поддержку развития животноводства.</p>
          <h2>Другие новости по теме</h2>
          <p>Получите консультацию!</p>
        </main>
      </body>
    </html>
    """

    sections, excerpt_only = detail_api._extract_remote_sections(html)

    assert excerpt_only is False
    assert len(sections) == 1
    assert sections[0].heading == (
        "Аграрная кредитная корпорация запускает новую программу кредитования"
    )
    assert "животноводства" in sections[0].text
    assert "Call Center" not in sections[0].text


def test_drop_host_specific_navigation_section_for_agrocredit():
    sections = [
        detail_api.OpportunityDetailSection(
            heading="",
            text="1408 Support for green and sustainable projects Purchase Jobs",
        ),
        detail_api.OpportunityDetailSection(
            heading="Agrarian Credit Corporation Launches New Lending Program",
            text="Support for livestock development.",
        ),
    ]

    cleaned = detail_api._drop_host_specific_navigation_section(
        sections,
        "https://agrocredit.kz/en/main/press-center/news/example/",
    )

    assert len(cleaned) == 1
    assert cleaned[0].heading == (
        "Agrarian Credit Corporation Launches New Lending Program"
    )


@pytest.mark.asyncio
async def test_amount_metadata_is_grouped_and_localized():
    item = Opportunity(
        source="example",
        source_url="https://example.org/funding",
        type=OpportunityType.GRANT,
        title="Startup credits",
        summary="Support for eligible startups.",
        amount_max=35000,
        currency="USD",
    )

    ru_detail = await detail_api.build_opportunity_detail(item, lang="ru")
    en_detail = await detail_api.build_opportunity_detail(item, lang="en")

    assert next(
        field.value for field in ru_detail.metadata if field.key == "amount"
    ) == ("до 35 000 USD")
    assert next(
        field.value for field in en_detail.metadata if field.key == "amount"
    ) == ("up to 35,000 USD")


@pytest.mark.asyncio
async def test_public_detail_can_skip_remote_source_fetch(monkeypatch):
    item = Opportunity(
        source="example",
        source_url="https://slow.example.org/funding",
        type=OpportunityType.GRANT,
        title="Structured public opportunity",
        summary="A complete local summary for the public page.",
    )

    async def unexpected_fetch(*args, **kwargs):
        raise AssertionError("public detail must not fetch a remote source")

    monkeypatch.setattr(detail_api, "_fetch_remote_detail", unexpected_fetch)

    detail = await detail_api.build_opportunity_detail(
        item,
        lang="ru",
        allow_remote_fetch=False,
    )

    assert detail.detail_fetch_status == "structured_only"
    assert detail.summary == item.summary


@pytest.mark.asyncio
async def test_build_opportunity_detail_uses_persisted_detail_payload():
    item = Opportunity(
        source="eeas_kazakhstan",
        source_url="https://example.org/eeas/call",
        type=OpportunityType.GRANT,
        title="EEAS grant call",
        summary="Summary from storage.",
        tags=["kazakhstan", "grant"],
        score=0.8,
        raw={
            "detail_text": "Local snapshot of the source page.",
            "detail_fetch_status": "ok",
            "detail_sections": [
                {"heading": "Overview", "text": "Local snapshot of the source page."},
                {"heading": "Eligibility", "text": "Civil society organizations."},
            ],
            "detail_fetched_at": "2026-05-28T12:00:00+00:00",
        },
    )

    detail = await detail_api.build_opportunity_detail(item)

    assert detail.detail_fetch_status == "ok"
    assert detail.detail_available is True
    assert detail.detail_text == "Local snapshot of the source page."
    assert detail.detail_sections[0].heading == "Overview"
    assert any(
        section.text == "Civil society organizations."
        for section in detail.detail_sections
    )


@pytest.mark.asyncio
async def test_build_opportunity_detail_uses_russian_source_detail_language():
    item = Opportunity(
        source="kazakhstan_domestic_support",
        source_url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
        type=OpportunityType.GRANT,
        title="State grants for social entrepreneurship",
        summary="Official eGov service for social entrepreneurship grants.",
        tags=["kazakhstan", "domestic_support", "rolling"],
        score=0.8,
        raw={
            "detail_language": "ru",
            "detail_fetch_status": "ok",
            "detail_sections": [
                {
                    "heading": "Как получить услугу онлайн",
                    "text": "Авторизоваться на портале и заполнить заявку.",
                }
            ],
            "detail_text": (
                "Как получить услугу онлайн\n"
                "Авторизоваться на портале и заполнить заявку."
            ),
        },
    )

    detail = await detail_api.build_opportunity_detail(item, lang="ru")

    assert detail.detail_fetch_status == "ok"
    assert detail.detail_available is True
    assert detail.detail_sections[-1].heading == "Как получить услугу онлайн"
    assert "заполнить заявку" in detail.detail_text


@pytest.mark.asyncio
async def test_build_opportunity_detail_sanitizes_persisted_russian_noise_sections():
    item = Opportunity(
        source="kazakhstan_domestic_support",
        source_url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-zapustila-novoe-napravlenie-kreditovaniya/"
        ),
        type=OpportunityType.GRANT,
        title="Agrarian Credit Corporation livestock lending",
        summary="Structured summary.",
        tags=["kazakhstan", "domestic_support", "rolling"],
        score=0.8,
        raw={
            "type": "grant",
            "tags": ["kazakhstan", "domestic_support", "rolling"],
            "languages": ["en", "ru"],
            "raw": {
                "detail_fetch_status": "ok",
                "detail_language": "en",
                "detail_sections": [
                    {
                        "heading": "Agrarian Credit Corporation Launches New Lending Program",
                        "text": "Support for livestock development.",
                    }
                ],
                "i18n": {
                    "ru": {
                        "detail_sections": [
                            {
                                "heading": "",
                                "text": (
                                    "1408 Call Center About the company Strategy, mission, vision "
                                    "Corporate structure The Board of Directors"
                                ),
                            },
                            {
                                "heading": (
                                    "Аграрная кредитная корпорация запускает "
                                    "новую программу кредитования"
                                ),
                                "text": "Поддержка развития животноводства.",
                            },
                            {
                                "heading": "Другие новости по теме",
                                "text": "Получите консультацию!",
                            },
                        ],
                        "detail_text": "noisy cached text",
                    }
                },
            },
        },
    )

    detail = await detail_api.build_opportunity_detail(item, lang="ru")

    assert len(detail.detail_sections) == 2
    assert detail.detail_sections[0].heading == "Обзор"
    assert detail.detail_sections[1].heading == (
        "Аграрная кредитная корпорация запускает новую программу кредитования"
    )
    assert "Call Center" not in detail.detail_text
    assert "Другие новости по теме" not in detail.detail_text


@pytest.mark.asyncio
async def test_build_opportunity_detail_drops_taxonomy_like_sections():
    item = Opportunity(
        source="unesco_iite",
        source_url="https://example.org/unesco/call",
        type=OpportunityType.TENDER,
        title="Kazakhstan consulting services",
        summary="Structured summary.",
        tags=["global", "education_organisation"],
        score=0.8,
        raw={
            "detail_fetch_status": "ok",
            "detail_sections": [
                {
                    "heading": "Overview",
                    "text": "Detailed public explanation for applicants.",
                },
                {
                    "heading": "",
                    "text": "global education_organisation",
                },
            ],
            "detail_text": "Overview\nDetailed public explanation for applicants.",
        },
    )

    detail = await detail_api.build_opportunity_detail(item)

    assert any(
        section.text == "Detailed public explanation for applicants."
        for section in detail.detail_sections
    )
    assert all(section.heading != "Eligibility" for section in detail.detail_sections)
    assert all(
        "education_organisation" not in section.text
        for section in detail.detail_sections
    )
    assert "global" not in detail.detail_text.lower()
    assert "education_organisation" not in detail.detail_text


@pytest.mark.asyncio
@respx.mock
async def test_build_opportunity_detail_follows_same_family_redirect(monkeypatch):
    source_url = "https://internews.org/opportunity/media-grant-2026/"
    redirected_url = "https://www.internews.org/opportunity/media-grant-2026/"

    async def _public_ip(_: str) -> bool:
        return True

    monkeypatch.setattr(detail_api, "_resolves_to_public_ip", _public_ip)
    respx.get(source_url).mock(
        return_value=httpx.Response(302, headers={"location": redirected_url})
    )
    respx.get(redirected_url).mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><body><main><h1>Overview</h1>"
                "<p>Support for independent media in Kazakhstan.</p>"
                "</main></body></html>"
            ),
        )
    )

    item = Opportunity(
        source="internews",
        source_url=source_url,
        type=OpportunityType.GRANT,
        title="Media Grant 2026",
        summary="Structured summary.",
        tags=["kazakhstan", "media"],
        score=0.8,
    )

    detail = await detail_api.build_opportunity_detail(item)

    assert detail.detail_fetch_status == "ok"
    assert any(
        "independent media" in section.text for section in detail.detail_sections
    )


@pytest.mark.asyncio
@respx.mock
async def test_build_opportunity_detail_blocks_redirect_to_private_host(monkeypatch):
    source_url = "https://internews.org/opportunity/media-grant-2026/"

    async def _public_ip(_: str) -> bool:
        return True

    monkeypatch.setattr(detail_api, "_resolves_to_public_ip", _public_ip)
    respx.get(source_url).mock(
        return_value=httpx.Response(
            302,
            headers={"location": "http://127.0.0.1/internal-admin"},
        )
    )

    item = Opportunity(
        source="internews",
        source_url=source_url,
        type=OpportunityType.GRANT,
        title="Media Grant 2026",
        summary="Structured summary.",
        tags=["kazakhstan", "media"],
        score=0.8,
    )

    detail = await detail_api.build_opportunity_detail(item)

    assert detail.detail_fetch_status == "not_allowed"


@pytest.mark.asyncio
async def test_build_opportunity_detail_blocks_private_dns_resolution(monkeypatch):
    source_url = "https://internews.org/opportunity/media-grant-2026/"

    async def _private_ip(_: str) -> bool:
        return False

    monkeypatch.setattr(detail_api, "_resolves_to_public_ip", _private_ip)

    item = Opportunity(
        source="internews",
        source_url=source_url,
        type=OpportunityType.GRANT,
        title="Media Grant 2026",
        summary="Structured summary.",
        tags=["kazakhstan", "media"],
        score=0.8,
    )

    detail = await detail_api.build_opportunity_detail(item)

    assert detail.detail_fetch_status == "not_allowed"
