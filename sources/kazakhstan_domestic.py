"""Curated Kazakhstan domestic support programs.

This source tracks official Kazakhstan grant, subsidy, tax-benefit and
state-support entry points. Most of these pages are evergreen services rather
than item-level grant feeds, so the parser keeps one normalized rolling record
per official program page.
"""

from __future__ import annotations

import hashlib
import re
import ssl
import tempfile
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from core.models import Opportunity, OpportunityType
from core.source_text import clean_plain_source_text as _clean_text
from sources.base import BaseSource
from sources.parsing import html_title as _shared_html_title
from sources.parsing import is_blocked_fetch as _is_blocked_fetch
from sources.parsing import is_unavailable_page as _shared_is_unavailable_page
from sources.parsing import unique_normalized as _unique

log = structlog.get_logger()

MAX_DETAIL_TEXT_CHARS = 12_000
MAX_DETAIL_SECTION_CHARS = 1_800
MAX_DETAIL_SECTIONS = 8
DETAIL_BLOCK_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "iframe",
    "button",
    "input",
    "select",
    "textarea",
    "footer",
}
DETAIL_CONTAINER_SELECTORS = (
    "main",
    "article",
    "[role='main']",
    ".content",
    ".entry-content",
    ".post-content",
    ".article-content",
    ".article-body",
    ".page-content",
    ".news-detail",
    ".news-item",
    ".detail",
)
_CYRILLIC_RE = re.compile(r"[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]")
GOVKZ_SEO_HEADERS = {
    "User-Agent": "python-httpx/0.27.2",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
}
QAZINDUSTRY_INTERMEDIATE_CA_URL = "http://crt.usertrust.com/GoGetSSLRSADVCA.crt"
_QAZINDUSTRY_CA_BUNDLE_PATH: str | None = None
DETAIL_NOISE_HEADINGS = {
    "другие новости по теме",
    "получите консультацию!",
    "получите консультацию",
    "other related news",
    "get a consultation!",
    "get a consultation",
}
SKIP_DETAIL_HEADING = "__skip_detail_section__"
DETAIL_NOISE_PHRASES = (
    "call center",
    "about the company",
    "corporate structure",
    "board of directors",
    "organizational structure",
    "corporate governance",
    "corporate documents",
    "policy in the field of quality",
    "external audit",
    "the ombudsman",
    "corporate reporting",
    "financial and annual reports",
    "financial and annual report",
    "sustainable development",
    "un sustainable development",
    "loan program",
    "our activities",
    "open an account online",
    "opening an online account",
    "settlement of problem debt",
    "corporate branches",
    "press center",
    "purchase",
    "jobs",
    "investor",
    "information for investors",
    "media about us",
    "other related news",
    "get a consultation",
)


@dataclass(frozen=True)
class DomesticProgram:
    url: str
    title: str
    summary: str
    tags: tuple[str, ...]
    type: OpportunityType = OpportunityType.GRANT
    rolling: bool = True
    deadline: date | None = None
    opportunity_status: str | None = None
    lifecycle: str | None = None
    retain_on_fetch_error: bool = True
    eligibility: tuple[str, ...] = ()
    title_ru: str = ""
    summary_ru: str = ""
    amount_raw: str | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    currency: str = "USD"
    application_url: str | None = None
    taxonomy_instrument: str = ""
    taxonomy_application_mode: str = ""
    taxonomy_deadline_model: str = ""
    application_windows: tuple[tuple[str, str], ...] = ()


DOMESTIC_PROGRAMS = (
    DomesticProgram(
        url="https://qazinn.kz/en/granty-qazinnovations",
        title="QazInnovations grants",
        summary=(
            "Official Kazakhstan innovation grant routes for commercialization "
            "of technologies, technology development and consortium projects."
        ),
        tags=(
            "grant",
            "innovation",
            "commercialization",
            "startup",
            "business_support",
            "qazinnovations",
        ),
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/sci/press/news/details/1243733?lang=ru",
        title="Kazakhstan state educational grants competition",
        summary=(
            "Official Ministry of Science and Higher Education notice for the "
            "2026 state educational-grant competition. Applications were accepted "
            "from 13 to 20 July 2026 through university admission offices, virtual "
            "admission offices and eGov; grant-holder lists are expected by 10 August."
        ),
        title_ru="Конкурс государственных образовательных грантов",
        summary_ru=(
            "Официальное сообщение Министерства науки и высшего образования "
            "о конкурсе образовательных грантов 2026 года. Заявления принимались "
            "с 13 по 20 июля через приёмные комиссии вузов, виртуальные приёмные "
            "и eGov; списки обладателей грантов должны быть опубликованы до 10 августа."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "citizen_support",
            "egov",
            "ministry_science_higher_education",
        ),
        eligibility=(
            "Kazakhstan applicants entering higher education under the official admission rules",
        ),
        application_url="https://egov.kz/cms/ru/services/university_degree/182pass_mon",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/sci/press/news/details/1260614?lang=ru",
        title="Kazakhstan master's degree state educational grants",
        summary=(
            "Official Ministry of Science and Higher Education notice on the "
            "2026 master's admission cycle. Around 11,000 state educational "
            "grants are allocated for master's training in priority fields; "
            "applications for the grant competition are accepted from 12 to "
            "18 August 2026, with results expected by 25 August."
        ),
        title_ru="Государственные образовательные гранты в магистратуру",
        summary_ru=(
            "Официальное сообщение Министерства науки и высшего образования "
            "о приёмной кампании в магистратуру 2026 года. На подготовку "
            "магистрантов выделено около 11 тысяч государственных грантов "
            "по востребованным направлениям; документы на конкурс принимаются "
            "с 12 по 18 августа 2026 года, списки обладателей грантов должны "
            "быть опубликованы до 25 августа."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "research",
            "citizen_support",
            "ministry_science_higher_education",
        ),
        rolling=False,
        deadline=date(2026, 8, 18),
        opportunity_status="upcoming",
        lifecycle="forecast",
        eligibility=(
            "Kazakhstan applicants to master's programmes who meet the official "
            "complex-testing thresholds and admission requirements",
        ),
        amount_raw="around 11,000 state educational grants for master's training in 2026",
        application_url="https://egov.kz/cms/ru/services/university_degree/182pass_mon",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/sci/press/news/details/1262257?lang=ru",
        title="State educational grants for the Taraz RCTU branch",
        summary=(
            "Official Ministry notice on the 2026-2027 admission campaign for the "
            "Taraz branch of D. Mendeleev University. The state allocated 100 "
            "educational grants for inorganic chemical technology and analytical "
            "chemistry programmes; documents are accepted until 9 August 2026."
        ),
        title_ru="100 образовательных грантов для Таразского филиала РХТУ",
        summary_ru=(
            "Официальное сообщение Министерства науки и высшего образования "
            "о приёме документов в Таразский филиал РХТУ имени Д. И. Менделеева. "
            "На 2026-2027 учебный год выделено 100 государственных грантов по "
            "программам химической технологии неорганических веществ и аналитической "
            "химии; документы принимаются до 9 августа 2026 года."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "engineering",
            "chemistry",
            "citizen_support",
            "ministry_science_higher_education",
        ),
        rolling=False,
        deadline=date(2026, 8, 9),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Applicants to the Taraz branch admission campaign who meet the "
            "official competition requirements",
        ),
        amount_raw="100 state educational grants for 2026-2027",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/sci/press/news/details/1263399?lang=ru",
        title="State educational grants for Anhalt International University",
        summary=(
            "Official Ministry notice on state educational grants at Anhalt "
            "International University in Almaty. Kazakhstan applicants can apply "
            "for electrical engineering, information technology and biomedical "
            "engineering programmes; documents are accepted until 10 August 2026."
        ),
        title_ru="Государственные образовательные гранты Anhalt International University",
        summary_ru=(
            "Официальное сообщение Министерства науки и высшего образования "
            "о государственных образовательных грантах в Anhalt International "
            "University в Алматы. Абитуриенты из Казахстана могут подать документы "
            "на направления «Электротехника и информационные технологии» и "
            "«Биомедицинская инженерия» до 10 августа 2026 года."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "engineering",
            "it",
            "citizen_support",
            "ministry_science_higher_education",
        ),
        rolling=False,
        deadline=date(2026, 8, 10),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Kazakhstan applicants meeting the official admission criteria, "
            "including UNT and English-language requirements",
        ),
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/pavlodar-edu/press/events/details/47017",
        title="Pavlodar region college state-funded places",
        summary=(
            "Official Pavlodar Region Education Department notice on the "
            "2026-2027 technical, vocational and post-secondary admission cycle. "
            "The region allocated 6,300 state-funded college places. Applications "
            "are accepted through eGov.kz or directly by colleges, with deadlines "
            "depending on the track: 10 August for pedagogy and some medical "
            "routes, 15 August for medical routes after grade 11 or TVET, "
            "22 August for middle-specialist and applied-bachelor programmes, "
            "27 August for working qualifications and 20 September for part-time study."
        ),
        title_ru="6300 мест по госзаказу в колледжах Павлодарской области",
        summary_ru=(
            "Официальное сообщение Управления образования Павлодарской области "
            "о приёме в колледжи на 2026-2027 учебный год. Регион выделил "
            "6300 мест по государственному образовательному заказу. Документы "
            "подаются через eGov.kz или напрямую в колледж; сроки зависят от "
            "траектории: до 10 августа для педагогических и части медицинских "
            "направлений, до 15 августа для медицинских направлений после 11 класса "
            "или ТиПО, до 22 августа для специальностей среднего звена и прикладного "
            "бакалавриата, до 27 августа для рабочих квалификаций и до 20 сентября "
            "для заочной формы."
        ),
        tags=(
            "education_admission",
            "state_funded_seat",
            "education",
            "citizen_support",
            "regional_development",
            "govkz",
        ),
        rolling=False,
        deadline=date(2026, 9, 20),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Applicants to technical, vocational and post-secondary education "
            "organizations in Pavlodar Region under the official admission rules",
        ),
        amount_raw="6,300 state-funded college places for 2026-2027",
        application_url="https://egov.kz/cms/ru/online-services/for_citizen/pr_5",
        taxonomy_instrument="education_admission",
        taxonomy_application_mode="admission",
        taxonomy_deadline_model="multiple",
        application_windows=(
            ("creative_programmes", "2026-07-20"),
            ("pedagogy_and_some_medical_programmes", "2026-08-10"),
            ("medical_after_grade_11_or_tvet", "2026-08-15"),
            ("state_order_middle_specialist_and_applied_bachelor", "2026-08-22"),
            ("working_qualifications", "2026-08-27"),
            ("part_time_study", "2026-09-20"),
        ),
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/astana/press/news/details/1247988?lang=ru",
        title="Astana college state-funded places",
        summary=(
            "Official Astana akimat notice on the 2026-2027 college admission "
            "campaign. The city allocated 10,300 state-funded college places, "
            "including working qualifications, middle-specialist and applied "
            "bachelor programmes, target orders with employers and inclusive "
            "education places. Applications are accepted online through eGov.kz; "
            "published deadlines run by track from 20 July to 20 September 2026."
        ),
        title_ru="10 300 мест по госзаказу в колледжах Астаны",
        summary_ru=(
            "Официальное сообщение акимата Астаны о приёме в колледжи на "
            "2026-2027 учебный год. В городе выделено 10 300 грантовых мест, "
            "включая рабочие квалификации, специальности среднего звена и "
            "прикладного бакалавриата, целевой заказ с работодателями и места "
            "по инклюзивному образованию. Документы принимаются онлайн через "
            "eGov.kz; опубликованные сроки зависят от траектории и идут с "
            "20 июля до 20 сентября 2026 года."
        ),
        tags=(
            "education_admission",
            "state_funded_seat",
            "education",
            "citizen_support",
            "regional_development",
            "govkz",
        ),
        rolling=False,
        deadline=date(2026, 9, 20),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Applicants to technical, vocational and post-secondary education "
            "organizations in Astana under the official admission rules",
        ),
        amount_raw="10,300 state-funded college places for 2026-2027",
        application_url="https://egov.kz/cms/ru/online-services/for_citizen/pr_5",
        taxonomy_instrument="education_admission",
        taxonomy_application_mode="admission",
        taxonomy_deadline_model="multiple",
        application_windows=(
            ("creative_programmes", "2026-07-20"),
            ("pedagogy_and_some_medical_programmes", "2026-08-10"),
            ("medical_after_grade_11_or_tvet", "2026-08-15"),
            ("state_order_middle_specialist_and_applied_bachelor", "2026-08-22"),
            ("working_qualifications", "2026-08-27"),
            ("part_time_study", "2026-09-20"),
        ),
    ),
    DomesticProgram(
        url="https://aaiff.ai/",
        title="Astana AI Film Festival international contest",
        summary=(
            "Official Astana AI Film Festival open call for AI-created short "
            "films. Applications are free and open to individual authors, teams "
            "and studios worldwide until 31 August 2026; the total prize fund is "
            "USD 1 million."
        ),
        title_ru="Международный конкурс Astana AI Film Festival",
        summary_ru=(
            "Официальный open call Astana AI Film Festival для короткометражных "
            "фильмов, созданных с использованием генеративного AI. Бесплатные "
            "заявки принимаются от индивидуальных авторов, команд и студий со "
            "всего мира до 31 августа 2026 года; общий призовой фонд составляет "
            "1 млн долларов США."
        ),
        tags=(
            "contest",
            "ai",
            "creative_industries",
            "culture",
            "media",
            "digital",
            "international",
        ),
        type=OpportunityType.CONTEST,
        rolling=False,
        deadline=date(2026, 8, 31),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Individual authors and teams from any country submitting an "
            "AI-created short film under the official festival rules",
        ),
        amount_raw="total prize fund of USD 1,000,000",
        amount_max=Decimal("1000000"),
        currency="USD",
        application_url="https://aaiff.ai/",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/mam/press/news/details/1214247?lang=ru",
        title="Aiboz national literary prize",
        summary=(
            "Official Ministry of Culture and Information notice on the Aiboz "
            "national literary prize for Kazakhstan authors. The 2026 contest "
            "accepts unpublished works in seven nominations until 1 September "
            "2026; the total prize fund is 35 million KZT, with 5 million KZT "
            "planned for each nomination."
        ),
        title_ru="Национальная литературная премия «Айбоз»",
        summary_ru=(
            "Официальное сообщение Министерства культуры и информации о "
            "Национальной литературной премии «Айбоз» для казахстанских авторов. "
            "В 2026 году принимаются ранее не опубликованные произведения по "
            "семи номинациям; заявки принимаются до 1 сентября, общий призовой "
            "фонд составляет 35 млн тенге, по 5 млн тенге на каждую номинацию."
        ),
        tags=(
            "contest",
            "culture",
            "literature",
            "creative_industries",
            "translation",
            "comics",
        ),
        type=OpportunityType.CONTEST,
        rolling=False,
        deadline=date(2026, 9, 1),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Kazakhstan authors submitting previously unpublished literary works "
            "under the official Aiboz prize rules",
        ),
        amount_raw="total prize fund of 35,000,000 KZT; 5,000,000 KZT per nomination",
        amount_max=Decimal("35000000"),
        currency="KZT",
        application_url="https://www.aiboz.kz/",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/mfa-gorgan/press/news/details/1245087?lang=ru",
        title="Kazakhstan Through My Eyes international drawing contest",
        summary=(
            "Official Kazakhstan MFA notice on the Otandastar Qory international "
            "online drawing contest for ethnic Kazakh children aged 12-17 living "
            "abroad. Works on Kazakhstan-related themes are accepted by email "
            "until 28 August 2026; winners receive a laptop, tablet, smart watch "
            "and other prizes."
        ),
        title_ru="Международный конкурс рисунков «Казахстан моими глазами»",
        summary_ru=(
            "Официальное сообщение МИД Казахстана о международном онлайн-конкурсе "
            "рисунков Фонда «Отандастар» для этнических казахских детей "
            "12–17 лет, проживающих за рубежом. Работы о природе, культуре, "
            "наследии и будущем Казахстана принимаются по электронной почте "
            "до 28 августа 2026 года; победителей наградят ноутбуком, планшетом, "
            "смарт-часами и другими призами."
        ),
        tags=(
            "contest",
            "culture",
            "creative_industries",
            "diaspora",
            "children",
            "visual_arts",
            "drawing",
            "youth",
        ),
        type=OpportunityType.CONTEST,
        rolling=False,
        deadline=date(2026, 8, 28),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Ethnic Kazakh children aged 12-17 living outside Kazakhstan under "
            "the official contest rules",
        ),
        amount_raw=(
            "prizes include a laptop, tablet, smart watch and incentive prizes"
        ),
        application_url="mailto:oqbaiqau@gmail.com",
    ),
    DomesticProgram(
        url=(
            "https://bolashak.gov.kz/ru/allnews/"
            "100-obrazovatelnyh-grantov-dlya-kazahstancev-vydelili-vuzy-"
            "respubliki-tadzhikistan"
        ),
        title="Tajikistan intergovernmental education grants for Kazakhstan citizens",
        summary=(
            "Official Center for International Programs notice on 100 education "
            "grants for Kazakhstan citizens at universities in Tajikistan for the "
            "2026-2027 academic year. The package covers tuition, monthly "
            "stipend and medical service; documents are accepted from 17 to "
            "28 July 2026 through eGov or the Center."
        ),
        title_ru="100 образовательных грантов в вузах Таджикистана для казахстанцев",
        summary_ru=(
            "Официальное сообщение АО «Центр международных программ» о 100 "
            "образовательных грантах для граждан Казахстана в вузах Республики "
            "Таджикистан на 2026-2027 учебный год. Грант покрывает обучение, "
            "ежемесячную стипендию и медицинское обслуживание; документы "
            "принимаются с 17 по 28 июля 2026 года через eGov или Центр."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "mobility",
            "student_exchange",
            "citizen_support",
            "intergovernmental_grant",
            "bolashak",
            "tajikistan",
        ),
        rolling=False,
        deadline=date(2026, 7, 28),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Kazakhstan citizens applying under the official intergovernmental "
            "education-grant selection rules",
        ),
        amount_raw="100 education grants for 2026-2027",
        application_url="https://egov.kz/cms/ru/services/higher_education/pass_203_mon",
    ),
    DomesticProgram(
        url=(
            "https://bolashak.gov.kz/ru/allnews/"
            "10-obrazovatelnyh-grantov-dlya-kazahstancev-vydelili-vuzy-"
            "kyrgyzskoj-respubliki"
        ),
        title="Kyrgyzstan intergovernmental education grants for Kazakhstan citizens",
        summary=(
            "Official Center for International Programs notice on 10 education "
            "grants for Kazakhstan citizens at universities in Kyrgyzstan for the "
            "2026-2027 academic year. The package covers tuition and monthly "
            "stipend; documents are accepted from 17 to 28 July 2026 through "
            "eGov or the Center."
        ),
        title_ru="10 образовательных грантов в вузах Кыргызстана для казахстанцев",
        summary_ru=(
            "Официальное сообщение АО «Центр международных программ» о 10 "
            "образовательных грантах для граждан Казахстана в вузах Кыргызской "
            "Республики на 2026-2027 учебный год. Грант покрывает обучение и "
            "ежемесячную стипендию; документы принимаются с 17 по 28 июля "
            "2026 года через eGov или Центр."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "mobility",
            "student_exchange",
            "citizen_support",
            "intergovernmental_grant",
            "bolashak",
            "kyrgyzstan",
        ),
        rolling=False,
        deadline=date(2026, 7, 28),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Kazakhstan citizens applying under the official intergovernmental "
            "education-grant selection rules",
        ),
        amount_raw="10 education grants for 2026-2027",
        application_url="https://egov.kz/cms/ru/services/higher_education/pass_203_mon",
    ),
    DomesticProgram(
        url="https://bolashak.gov.kz/en/allnews/otkryt-priem-dokumentov-dlya-obucheniya-v-marokko",
        title="Morocco intergovernmental education grants for Kazakhstan citizens",
        summary=(
            "Official Center for International Programs notice on 20 Moroccan "
            "government education grants with scholarships for the 2026-2027 "
            "academic year. The programme covers study in public higher, "
            "technical and vocational institutions in Morocco; the final-stage "
            "deadline for submitting baccalaureate exam results is 31 July 2026."
        ),
        title_ru="20 образовательных грантов Марокко для казахстанцев",
        summary_ru=(
            "Официальное сообщение АО «Центр международных программ» о 20 "
            "образовательных грантах Королевства Марокко со стипендией на "
            "2026-2027 учебный год. Программа охватывает обучение в государственных "
            "высших, технических и профессиональных учебных заведениях Марокко; "
            "срок представления результатов экзаменов на финальном этапе – "
            "31 июля 2026 года."
        ),
        tags=(
            "grant",
            "scholarship",
            "education",
            "higher_education",
            "vocational_training",
            "mobility",
            "student_exchange",
            "citizen_support",
            "intergovernmental_grant",
            "bolashak",
            "morocco",
        ),
        rolling=False,
        deadline=date(2026, 7, 31),
        opportunity_status="open",
        lifecycle="open",
        eligibility=(
            "Kazakhstan citizens applying under the official Moroccan "
            "intergovernmental education-grant selection rules",
        ),
        amount_raw=(
            "20 education grants with scholarship for the 2026-2027 academic year"
        ),
        application_url="mailto:studyinmorocco.kz@gmail.com",
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/mobile-services/pass455_mir",
        title="Innovation grants for commercialization of technologies",
        summary=(
            "Official eGov service page for Kazakhstan innovation grants handled "
            "through QazInnovations and the digital development ministry."
        ),
        tags=(
            "grant",
            "innovation",
            "commercialization",
            "research",
            "qazinnovations",
            "egov",
        ),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/sme_subsidy/",
        title="Damu subsidies for small businesses",
        summary=(
            "Damu SME support route with interest-rate subsidies and financing "
            "support for eligible small businesses."
        ),
        tags=("subsidy", "sme", "startup", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/enterprise_development/",
        title="Damu Unified Integrated Programme subsidies",
        summary=(
            "Damu subsidy route under the unified entrepreneurship support "
            "programme for eligible Kazakhstan businesses."
        ),
        tags=("subsidy", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/guarantee/",
        title="Damu Fund guarantee programmes",
        summary=(
            "Official Damu guarantee-programmes entry point for business loans "
            "and access-to-finance support."
        ),
        tags=("loan_guarantee", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/guarantee/invest_projects/",
        title="Damu guarantees for investment projects",
        summary=(
            "Guarantee route for eligible Kazakhstan investment projects, "
            "including priority investment-project financing support."
        ),
        tags=("loan_guarantee", "investment", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/inner_support/",
        title="Damu support for domestic trade entities",
        summary=(
            "Damu subsidy and guarantee support for eligible domestic trade "
            "entities in Kazakhstan."
        ),
        tags=("subsidy", "loan_guarantee", "trade", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/mobile-services/pass258_mne",
        title="Interest-rate subsidy service for entrepreneurs",
        summary=(
            "Official eGov service for subsidizing part of the interest rate on "
            "business loans and financial leasing under Kazakhstan entrepreneurship "
            "support programs."
        ),
        tags=(
            "subsidy",
            "preferential_financing",
            "leasing",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=(
            "Kazakhstan entrepreneurs applying for loan or financial-leasing interest-rate support",
        ),
        application_url="https://egov.kz/cms/ru/mobile-services/pass258_mne",
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/road_business_map",
        title="Road Map of Business support programme",
        summary=(
            "Official eGov overview of Kazakhstan business-support instruments, "
            "including loan and leasing subsidies, guarantees, grants and "
            "non-financial support routes."
        ),
        tags=(
            "subsidy",
            "loan_guarantee",
            "grant",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=("Kazakhstan SMEs and entrepreneurs under programme conditions",),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
        title="State grants for social entrepreneurship",
        summary=(
            "Official eGov service for Kazakhstan state grants for social "
            "entrepreneurship entities, including online application steps and "
            "required documents."
        ),
        tags=(
            "grant",
            "social_entrepreneurship",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=(
            "Kazakhstan individual entrepreneurs and legal entities that are "
            "social-entrepreneurship SMEs",
        ),
        amount_raw="up to 5,000,000 KZT according to current service conditions",
        amount_max=Decimal("5000000"),
        currency="KZT",
        application_url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/kyzylorda-kasipkerlik/activities/37552",
        title="Kyzylorda regional grants for social entrepreneurship",
        summary=(
            "Official Kyzylorda Entrepreneurship and Industry Department guidance "
            "on regional state grants for social-entrepreneurship entities. Grants "
            "are awarded through competitive selection for business projects up "
            "to 18 months, with at least 20% co-financing, new jobs and required "
            "project infrastructure."
        ),
        title_ru="Региональные гранты Кызылординской области для социального предпринимательства",
        summary_ru=(
            "Официальная справка Управления предпринимательства и промышленности "
            "Кызылординской области о государственных грантах для субъектов "
            "социального предпринимательства. Гранты выдаются по итогам конкурсного "
            "отбора на бизнес-проекты сроком до 18 месяцев; обязательны "
            "софинансирование не менее 20%, создание рабочих мест и наличие "
            "инфраструктуры для проекта."
        ),
        tags=(
            "grant",
            "social_entrepreneurship",
            "sme",
            "business_support",
            "regional_development",
            "one_village_one_product",
            "kezekte",
            "kyzylorda",
            "govkz",
        ),
        eligibility=(
            "Social-entrepreneurship entities and One Village One Product finalists "
            "under Kyzylorda regional competition conditions",
        ),
        amount_raw="up to 5,000,000 KZT",
        amount_max=Decimal("5000000"),
        currency="KZT",
        application_url="https://kezekte.kz/",
    ),
    DomesticProgram(
        url="https://www.gov.kz/memleket/entities/mangystau-upp/press/article/details/212349",
        title="Mangystau regional grants for social entrepreneurship",
        summary=(
            "Official Mangystau Entrepreneurship and Trade Department guidance "
            "on non-repayable regional grants for social entrepreneurs and One "
            "Village One Product finalists. The page explains eligible spending "
            "on raw materials, repairs, new equipment, technologies, franchise "
            "and research work, with at least 20% co-financing, documented "
            "cashless payments and new jobs."
        ),
        title_ru="Региональные гранты Мангистауской области для социального предпринимательства",
        summary_ru=(
            "Официальная справка Управления предпринимательства и торговли "
            "Мангистауской области о безвозмездных грантах для социальных "
            "предпринимателей и финалистов программы «Одно село – один продукт». "
            "Средства можно направлять на сырье, ремонт, новое оборудование, "
            "технологии, франшизу и исследовательские работы; требуются "
            "софинансирование не менее 20%, безналичная оплата с подтверждающими "
            "документами и создание рабочих мест."
        ),
        tags=(
            "grant",
            "social_entrepreneurship",
            "sme",
            "business_support",
            "regional_development",
            "one_village_one_product",
            "kezekte",
            "mangystau",
            "govkz",
        ),
        eligibility=(
            "Social entrepreneurs and One Village One Product finalists under "
            "Mangystau regional grant conditions",
        ),
        amount_raw="up to 5,000,000 KZT",
        amount_max=Decimal("5000000"),
        currency="KZT",
        application_url="https://kezekte.kz/",
    ),
    DomesticProgram(
        url="https://www.enbek.kz/ru/node/3481",
        title="State grant for startup business development",
        summary=(
            "Official Enbek page for grants issued free of charge for new "
            "business ideas and startup-business development through Business Enbek."
        ),
        tags=("grant", "startup", "employment", "business_support", "enbek"),
        eligibility=(
            "Eligible Kazakhstan individuals with a business project and "
            "programme certificate",
        ),
        amount_raw="up to 400 MRP",
    ),
    DomesticProgram(
        url="https://www.gov.kz/situations/501/1169?lang=ru",
        title="How to get a state grant to start a business",
        summary=(
            "Official gov.kz guidance on the conditions, categories and application "
            "process for Kazakhstan state grants for opening or developing a "
            "business."
        ),
        tags=("grant", "startup", "employment", "business_support", "govkz"),
        eligibility=(
            "Eligible socially vulnerable Kazakhstan citizens after training "
            "certificate and project defense",
        ),
        amount_raw="up to 400 MRP",
    ),
    DomesticProgram(
        url="https://baiterek.gov.kz/en/entrepreneurship-support/sme-support-and-development/",
        title="Baiterek SME support and development",
        summary=(
            "Official Baiterek overview of SME support routes through Damu, "
            "KazakhExport, Industrial Development Fund, QIC and related subsidiaries."
        ),
        tags=("sme", "preferential_financing", "business_support", "baiterek"),
    ),
    DomesticProgram(
        url=(
            "https://baiterek.gov.kz/en/pr/news/"
            "bgov-kz-the-unified-platform-for-financial-support-to-businesses"
        ),
        title="Bgov.kz unified financial support platform",
        summary=(
            "Official Baiterek launch page for the unified platform covering Damu, "
            "DBK, KazAgroFinance, Agrarian Credit Corporation, IDF, QIC and KazakhExport."
        ),
        tags=("sme", "preferential_financing", "business_support", "baiterek", "bgov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/agriculture/subsidies_for_agriculture",
        title="Subsidies for crop production",
        summary=(
            "Official eGov guide to crop-production subsidies including seed, "
            "fertilizer, water and priority-crop support routes."
        ),
        tags=("subsidy", "agrotech", "agriculture", "crop_production", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/livestock/subsidies_for_animals",
        title="Subsidies for animal breeding",
        summary=(
            "Official eGov guide to livestock and animal-breeding subsidies for "
            "eligible Kazakhstan producers."
        ),
        tags=("subsidy", "vettech", "livestock", "animal_health", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/livestock/demands_for_subsidies",
        title="Criteria for producers applying for subsidies",
        summary=(
            "Official eGov guide to eligibility criteria and verification methods "
            "for agricultural subsidy applicants."
        ),
        tags=("subsidy", "agrotech", "vettech", "agriculture", "egov"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3794",
        title="APK loan guarantee and insurance subsidies",
        summary=(
            "Official Kazakhstan government service for subsidizing guarantees "
            "and insurance of loans for agro-industrial complex entities."
        ),
        tags=("subsidy", "loan_guarantee", "agrotech", "agriculture", "govkz"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3377",
        title="Priority crop production subsidies",
        summary=(
            "Official government service for subsidies supporting priority crop "
            "production, including perennial plantations."
        ),
        tags=("subsidy", "agrotech", "agriculture", "crop_production", "govkz"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3388",
        title="Breeding livestock productivity subsidies",
        summary=(
            "Official government service for subsidies supporting breeding "
            "livestock, productivity and livestock-product quality."
        ),
        tags=("subsidy", "vettech", "livestock", "animal_health", "govkz"),
    ),
    DomesticProgram(
        url="https://www.kaf.kz/en/media/news/85249/",
        title="KazAgroFinance Own Feed and Preferential Leasing",
        summary=(
            "Official KazAgroFinance application announcement for preferential "
            "agricultural machinery leasing and the Own Feed program."
        ),
        tags=(
            "preferential_financing",
            "leasing",
            "agrotech",
            "agriculture",
            "kazagrofinance",
        ),
    ),
    DomesticProgram(
        url="https://www.kaf.kz/en/media/news/82782/",
        title="KazAgroFinance preferential agricultural leasing",
        summary=(
            "Official KazAgroFinance page for concessional agricultural machinery "
            "leasing at preferential rates for Kazakhstan farmers."
        ),
        tags=(
            "preferential_financing",
            "leasing",
            "agrotech",
            "agriculture",
            "kazagrofinance",
        ),
    ),
    DomesticProgram(
        url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-zapustila-novoe-napravlenie-"
            "kreditovaniya/"
        ),
        title="Agrarian Credit Corporation livestock lending",
        summary=(
            "Official Agrarian Credit Corporation program for preferential "
            "short-term lending to livestock and feedlot producers."
        ),
        tags=(
            "preferential_financing",
            "agrotech",
            "vettech",
            "livestock",
            "agrocredit",
        ),
    ),
    DomesticProgram(
        url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-prodolzhaet-finansirovanie-"
            "vesenne-polevykh-rabot/"
        ),
        title="Agrarian Credit Corporation Ken Dala financing",
        summary=(
            "Official Agrarian Credit Corporation page for preferential lending "
            "for spring field and harvesting work under the Ken Dala program."
        ),
        tags=(
            "preferential_financing",
            "agrotech",
            "agriculture",
            "crop_production",
            "agrocredit",
        ),
    ),
    DomesticProgram(
        url="https://www.ncste.kz/en/competition",
        title="NCSTE science grant competitions",
        summary=(
            "Official NCSTE competition list for Kazakhstan science grants, "
            "young-scientist calls and commercialization financing."
        ),
        tags=("grant", "research", "science", "commercialization", "ncste"),
    ),
    DomesticProgram(
        url="https://cisc.kz/ru/category/malye-granty/",
        title="CISC small grants",
        summary=(
            "Official Center for Support of Civil Initiatives category for small "
            "grants supporting NGOs, volunteers and civic initiatives."
        ),
        tags=("grant", "ngo", "civic", "civil_society", "cisc"),
    ),
    DomesticProgram(
        url="https://qazindustry.gov.kz/ru/business_reimbursement",
        title="QazIndustry productivity reimbursement measures",
        summary=(
            "Official QazIndustry state-stimulation measures for partial cost "
            "reimbursement to improve industrial productivity."
        ),
        tags=("reimbursement", "industry", "digitalization", "business_support"),
    ),
    DomesticProgram(
        url="https://qazindustry.gov.kz/o-nas/business_support",
        title="QazIndustry business support measures",
        summary=(
            "Official QazIndustry overview of industrial state-stimulation and "
            "business-support measures."
        ),
        tags=("reimbursement", "industry", "business_support", "qazindustry"),
    ),
    DomesticProgram(
        url="https://export.gov.kz/export/support?lang=en",
        title="Kazakhstan export cost recovery",
        summary=(
            "Official export.gov.kz support page for partial cost recovery and "
            "export-promotion support for Kazakhstan producers."
        ),
        tags=("reimbursement", "export", "trade", "business_support", "qaztrade"),
    ),
    DomesticProgram(
        url=("https://egov.kz/cms/ru/services/state_support_measures/" "reimbursement"),
        title="Reimbursement of export-promotion costs",
        summary=(
            "Official eGov service for partial reimbursement of costs to promote "
            "domestic processed goods, works and services abroad."
        ),
        tags=("reimbursement", "export", "trade", "business_support", "egov"),
    ),
    DomesticProgram(
        url="https://kazakhexport.kz/en/services/",
        title="KazakhExport services",
        summary=(
            "Official KazakhExport service entry point for export-credit agency "
            "support, insurance and trade-finance instruments."
        ),
        tags=(
            "preferential_financing",
            "export",
            "trade",
            "business_support",
            "kazakhexport",
        ),
    ),
    DomesticProgram(
        url=(
            "https://egov.kz/cms/ru/services/state_support_measures/" "pass003mgp_miid"
        ),
        title="Reimbursement for technological-process improvement",
        summary=(
            "Official eGov service for reimbursement of costs for improving "
            "technological processes at eligible enterprises."
        ),
        tags=("reimbursement", "industry", "technology", "digitalization", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/government-services/for_busunesses/pass1404004_mps",
        title="Reimbursement for adoption of digital technologies",
        summary=(
            "Official eGov service for reimbursement of expenses related to "
            "adoption of digital technologies."
        ),
        tags=("reimbursement", "industry", "digitalization", "technology", "egov"),
    ),
    DomesticProgram(
        url="https://www.kdb.kz/en/services/investment-projects/",
        title="Development Bank of Kazakhstan investment-project financing",
        summary=(
            "Official DBK financing route for large investment projects, export "
            "operations, project finance and long-term industrial development."
        ),
        tags=(
            "preferential_financing",
            "investment",
            "industry",
            "business_support",
            "kdb",
        ),
    ),
    DomesticProgram(
        url="https://www.kdb.kz/en/services/guarantee/",
        title="Development Bank of Kazakhstan guarantees",
        summary=(
            "Official DBK guarantee instrument for medium-sized businesses and "
            "priority investment projects financed through banks and financial institutions."
        ),
        tags=(
            "loan_guarantee",
            "investment",
            "industry",
            "business_support",
            "kdb",
        ),
    ),
    DomesticProgram(
        url=(
            "https://idfrk.kz/en/pr/news/"
            "industrial-development-fund-jsc-expands-leasing-program-for-the-"
            "construction-of-small-industrial-zon"
        ),
        title="Industrial Development Fund small industrial zones leasing",
        summary=(
            "Official IDF program page for leasing support for construction of "
            "small industrial zones across Kazakhstan."
        ),
        tags=(
            "leasing",
            "industry",
            "preferential_financing",
            "business_support",
            "idf",
        ),
    ),
    DomesticProgram(
        url="https://invest.gov.kz/invest-guide/support/investment-activity1/tax-incentives1/",
        title="Kazakhstan investment tax incentives",
        summary=(
            "Official KAZAKH INVEST guide to tax preferences available under "
            "Kazakhstan investment contracts and special investment projects."
        ),
        tags=("tax_benefit", "investment", "business_support", "invest_gov"),
    ),
    DomesticProgram(
        url="https://invest.gov.kz/doing-business-here/fez-and/the-list-of-sez-and/",
        title="Kazakhstan special economic zones",
        summary=(
            "Official KAZAKH INVEST guide to special economic zones and related "
            "investment benefits in Kazakhstan."
        ),
        tags=("tax_benefit", "investment", "sez", "business_support", "invest_gov"),
    ),
    DomesticProgram(
        url="https://astanahub.com/en/registration/",
        title="Astana Hub participant tax benefits",
        summary=(
            "Official Astana Hub participant-registration page for tax "
            "preferences, visa benefits and startup-development support."
        ),
        tags=("tax_benefit", "startup", "it", "business_support", "astana_hub"),
    ),
    DomesticProgram(
        url=(
            "https://qic.kz/en/novosti-i-insayty/"
            "qazaqstan-investment-corporation-signed-an-agreement-to-join-the-"
            "alem-ventures-fund-venture-fund/"
        ),
        title="QIC Alem Ventures Fund participation",
        summary=(
            "Official QIC page on participation in the Alem Ventures fund of funds "
            "supporting IT projects in Kazakhstan, Central Asia and adjacent markets."
        ),
        tags=("investment", "private_equity", "venture", "startup", "qic"),
    ),
    DomesticProgram(
        url="https://astanahub.com/en/faq/information",
        title="Astana Hub participant registration FAQ",
        summary=(
            "Official Astana Hub FAQ describing participant eligibility, tax "
            "preferences, application timing and required registration conditions."
        ),
        tags=("tax_benefit", "startup", "it", "business_support", "astana_hub"),
    ),
    DomesticProgram(
        url="https://astanahub.com/en/l/SeedMoneySmartCity",
        title="Astana Hub Seed Money Smart City",
        summary=(
            "Official Astana Hub financing route for smart-city technology "
            "startups. Applicants submit documents through the Astana Hub "
            "platform, pass eligibility review and present the project before "
            "agreement signing and escrow-based disbursement."
        ),
        title_ru="Astana Hub Seed Money Smart City",
        summary_ru=(
            "Официальная программа финансирования Astana Hub для технологических "
            "стартапов в сфере умного города. Заявитель подаёт документы через "
            "платформу Astana Hub, проходит проверку условий и презентацию проекта; "
            "после одобрения финансирование перечисляется через эскроу."
        ),
        tags=("grant", "startup", "innovation", "smart_city", "astana_hub"),
        eligibility=(
            "Technology startups meeting the Astana Hub programme requirements, "
            "including legal-entity, team and activity-priority conditions",
        ),
        application_url="https://astanahub.com/en/l/SeedMoneySmartCity",
    ),
)

DOMESTIC_EDITORIAL_RU: dict[str, dict[str, Any]] = {
    "https://aaiff.ai/": {
        "social_title": "Astana AI Film Festival: конкурс с фондом 1 млн USD",
        "summary": (
            "Международный конкурс короткометражных фильмов, в которых "
            "генеративный AI является частью процесса создания."
        ),
        "audience_label": "Кому подходит",
        "eligibility": [
            "Индивидуальные авторы, команды и студии из любой страны; "
            "участие бесплатное"
        ],
        "highlights_label": "Требования к фильму",
        "highlights": [
            "продолжительность – от 3 минут",
            "генеративный AI должен участвовать в создании, а не только в постобработке",
            "в видео нужны встроенные английские субтитры",
            "для YouTube обязателен хэштег #SpecialForAAIFF в описании",
        ],
        "amount": "общий фонд – 1 000 000 USD; главный приз – 450 000 USD",
        "amount_label": "Призы",
        "deadline_display": "31 августа 2026",
        "deadline_label": "Дедлайн",
        "steps_title": "Как подать",
        "application_step_titles": [
            "Загрузите фильм",
            "Выберите секцию",
            "Заполните форму",
        ],
        "application_steps": [
            "Загрузить фильм в 1080p на YouTube или Google Drive и открыть доступ",
            "Выбрать тематическую или открытую конкурсную секцию",
            "Заполнить форму на aaiff.ai, указать AI-инструменты и всех участников",
        ],
        "prepare_items": [
            {
                "title": "Проверьте хронометраж",
                "text": "Фестиваль принимает фильмы продолжительностью от трёх минут.",
            },
            {
                "title": "Добавьте английские субтитры",
                "text": "Субтитры должны быть встроены непосредственно в видео.",
            },
            {
                "title": "Опишите AI-процесс",
                "text": (
                    "В заявке нужно раскрыть использованные модели, инструменты "
                    "и вклад участников."
                ),
            },
            {
                "title": "Подготовьте ссылку",
                "text": (
                    "Можно использовать публичное или unlisted-видео на YouTube "
                    "либо Google Drive с доступом по ссылке."
                ),
            },
        ],
    }
}

ACTIVE_DOMESTIC_URLS = frozenset(program.url for program in DOMESTIC_PROGRAMS)


def _detect_detail_language(text: str, html: str = "") -> str:
    soup_lang = ""
    try:
        soup = BeautifulSoup(html, "lxml")
        soup_lang = str((soup.html or {}).get("lang") or "").strip().lower()
    except Exception:  # noqa: BLE001
        soup_lang = ""
    if soup_lang.startswith("en"):
        return "en"
    if soup_lang.startswith(("ru", "kk")):
        return "ru"
    return "ru" if _CYRILLIC_RE.search(text) else "en"


def _candidate_container(soup: BeautifulSoup) -> Any:
    body = soup.body or soup
    candidates = [body]
    for selector in DETAIL_CONTAINER_SELECTORS:
        candidates.extend(soup.select(selector))
    return max(
        candidates,
        key=lambda node: len(_clean_text(node.get_text(" ", strip=True))),
        default=body,
    )


def _append_detail_section(
    sections: list[dict[str, str]],
    heading: str,
    chunks: list[str],
) -> bool:
    filtered_chunks = [
        chunk
        for chunk in chunks
        if chunk and not _is_noise_heading(chunk) and not _is_noise_chunk(chunk)
    ]
    text = "\n".join(filtered_chunks)
    text = text[:MAX_DETAIL_SECTION_CHARS].strip()
    if not text:
        return False
    if not heading.strip() and _is_noise_chunk(text):
        return False
    sections.append({"heading": heading.strip(), "text": text})
    return True


def _is_noise_heading(value: str) -> bool:
    normalized = _clean_text(value).lower()
    return normalized in DETAIL_NOISE_HEADINGS


def _is_noise_chunk(text: str) -> bool:
    normalized = _clean_text(text).lower()
    if not normalized:
        return True
    if len(normalized) <= 160 and any(
        phrase in normalized for phrase in DETAIL_NOISE_PHRASES
    ):
        return True
    hits = sum(1 for phrase in DETAIL_NOISE_PHRASES if phrase in normalized)
    if hits >= 3:
        return True
    return (
        len(normalized) > 400
        and hits >= 2
        and normalized.count(".") <= 2
        and normalized.count(":") <= 1
    )


def _extract_detail_sections(html: str) -> tuple[list[dict[str, str]], bool]:
    soup = BeautifulSoup(html, "lxml")
    for tag_name in DETAIL_BLOCK_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    container = _candidate_container(soup)
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_chunks: list[str] = []
    excerpt_only = False
    seen_chunks: set[str] = set()

    for node in container.find_all(["h1", "h2", "h3", "p", "li", "tr"], limit=260):
        if len(sections) >= MAX_DETAIL_SECTIONS:
            excerpt_only = True
            break
        if node.name == "tr":
            text = _clean_text(
                " | ".join(
                    _clean_text(cell.get_text(" ", strip=True))
                    for cell in node.find_all(["th", "td"])
                )
            )
        else:
            text = _clean_text(node.get_text(" ", strip=True))
        if not text or len(text) < 3:
            continue
        normalized = text.lower()
        if normalized in seen_chunks:
            continue
        seen_chunks.add(normalized)
        if node.name in {"h1", "h2", "h3"}:
            if _is_noise_heading(text):
                if _append_detail_section(sections, current_heading, current_chunks):
                    current_chunks = []
                current_heading = SKIP_DETAIL_HEADING
                current_chunks = []
                continue
            if _append_detail_section(sections, current_heading, current_chunks):
                current_chunks = []
            current_heading = text
            continue
        if current_heading == SKIP_DETAIL_HEADING:
            continue
        if _is_noise_heading(current_heading) or _is_noise_chunk(text):
            continue
        current_chunks.append(text)

    if len(sections) < MAX_DETAIL_SECTIONS:
        _append_detail_section(sections, current_heading, current_chunks)

    if not sections:
        fallback = _clean_text(container.get_text(" ", strip=True))
        if fallback:
            sections.append(
                {"heading": "", "text": fallback[:MAX_DETAIL_SECTION_CHARS]}
            )
            excerpt_only = len(fallback) > MAX_DETAIL_SECTION_CHARS
    return sections, excerpt_only


def _detail_text_from_sections(sections: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for section in sections:
        text = _clean_text(str(section.get("text") or ""))
        if not text:
            continue
        heading = _clean_text(str(section.get("heading") or ""))
        blocks.append(f"{heading}\n{text}".strip() if heading else text)
    return "\n\n".join(blocks)[:MAX_DETAIL_TEXT_CHARS].strip()


def _drop_leading_navigation_section(
    sections: list[dict[str, str]],
) -> list[dict[str, str]]:
    if len(sections) < 2:
        return sections
    first = sections[0]
    if _clean_text(str(first.get("heading") or "")):
        return sections
    text = str(first.get("text") or "")
    has_following_heading = any(
        _clean_text(str(section.get("heading") or "")) for section in sections[1:]
    )
    if has_following_heading:
        return sections[1:]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 8:
        return sections
    short_lines = sum(1 for line in lines if len(line.split()) <= 6)
    punctuation_hits = text.count(".") + text.count("!") + text.count("?")
    if has_following_heading and short_lines >= 6 and punctuation_hits <= 3:
        return sections[1:]
    return sections


def _curated_detail_payload(program: DomesticProgram, status: str) -> dict[str, Any]:
    sections = [{"heading": "Overview", "text": program.summary}]
    if program.eligibility:
        sections.append(
            {
                "heading": "Eligibility",
                "text": "\n".join(program.eligibility),
            }
        )
    if program.amount_raw:
        sections.append({"heading": "Support amount", "text": program.amount_raw})
    return {
        "detail_fetch_status": status,
        "detail_excerpt_only": True,
        "detail_language": "en",
        "detail_sections": sections,
        "detail_text": _detail_text_from_sections(sections),
    }


def _amount_raw_payload(program: DomesticProgram) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if program.amount_raw:
        payload["amount_raw"] = program.amount_raw
    if program.amount_min is not None:
        payload["amount_min"] = str(program.amount_min)
    if program.amount_max is not None:
        payload["amount_max"] = str(program.amount_max)
    if program.amount_min is not None or program.amount_max is not None:
        payload["currency"] = program.currency
    return payload


def _taxonomy_payload(program: DomesticProgram) -> dict[str, Any]:
    taxonomy = {
        key: value
        for key, value in {
            "instrument": program.taxonomy_instrument,
            "application_mode": program.taxonomy_application_mode,
            "deadline_model": program.taxonomy_deadline_model,
        }.items()
        if value
    }
    payload: dict[str, Any] = {}
    if taxonomy:
        payload["opportunity_taxonomy"] = taxonomy
    if program.application_windows:
        payload["application_windows"] = [
            {"route": route, "deadline": deadline}
            for route, deadline in program.application_windows
        ]
    return payload


def _i18n_payload(program: DomesticProgram) -> dict[str, Any]:
    editorial = DOMESTIC_EDITORIAL_RU.get(program.url, {})
    if not program.title_ru and not program.summary_ru and not editorial:
        return {}
    ru: dict[str, Any] = {}
    if program.title_ru:
        ru["title"] = program.title_ru
    if program.summary_ru:
        ru["summary"] = program.summary_ru
    ru.update(editorial)
    return {"i18n": {"ru": ru}}


def _detail_snapshot(html: str) -> dict[str, Any] | None:
    sections, excerpt_only = _extract_detail_sections(html)
    sections = _drop_leading_navigation_section(sections)
    detail_text = _detail_text_from_sections(sections)
    if not detail_text:
        return None
    encoded = html.encode("utf-8", errors="ignore")
    return {
        "detail_fetch_status": "ok",
        "detail_excerpt_only": excerpt_only
        or len(detail_text) >= MAX_DETAIL_TEXT_CHARS,
        "detail_fetched_at": datetime.now(timezone.utc).isoformat(),
        "detail_language": _detect_detail_language(detail_text, html),
        "detail_html_sha256": hashlib.sha256(encoded).hexdigest(),
        "detail_sections": sections[:MAX_DETAIL_SECTIONS],
        "detail_text": detail_text,
    }


def _html_title(html: str) -> str | None:
    return _shared_html_title(html, _clean_text, strip_tags=True)


def _is_unavailable_page(html: str) -> bool:
    return _shared_is_unavailable_page(html, _clean_text)


def _needs_qazindustry_ca_fallback(url: str, exc: Exception) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return (
        hostname == "qazindustry.gov.kz"
        and isinstance(exc, httpx.ConnectError)
        and "CERTIFICATE_VERIFY_FAILED" in repr(exc)
        and "unable to get local issuer certificate" in repr(exc)
    )


async def _qazindustry_ca_bundle_path() -> str:
    global _QAZINDUSTRY_CA_BUNDLE_PATH
    if _QAZINDUSTRY_CA_BUNDLE_PATH and Path(_QAZINDUSTRY_CA_BUNDLE_PATH).exists():
        return _QAZINDUSTRY_CA_BUNDLE_PATH

    import certifi

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(QAZINDUSTRY_INTERMEDIATE_CA_URL)
        response.raise_for_status()
        cert_bytes = response.content

    if b"BEGIN CERTIFICATE" in cert_bytes:
        intermediate_pem = cert_bytes.decode("ascii", errors="ignore")
    else:
        intermediate_pem = ssl.DER_cert_to_PEM_cert(cert_bytes)

    base_bundle = Path(certifi.where()).read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="grant-radar-qazindustry-ca-",
        suffix=".pem",
        delete=False,
    ) as bundle:
        bundle.write(base_bundle)
        bundle.write("\n")
        bundle.write(intermediate_pem)
        bundle.write("\n")
        bundle_path = bundle.name
    _QAZINDUSTRY_CA_BUNDLE_PATH = bundle_path
    return bundle_path


def _looks_like_unhydrated_govkz_shell(url: str, html: str) -> bool:
    if "gov.kz/" not in url:
        return False
    title = (_html_title(html) or "").lower()
    if not title.startswith("gov.kz - "):
        return False
    return not re.search(r"<(?:h1|h2|h3|p|li|tr)\b", html, re.IGNORECASE)


def _program_tags(program: DomesticProgram, default_tags: Iterable[str]) -> list[str]:
    tags = [*default_tags, *program.tags]
    if program.rolling:
        tags.append("rolling")
    return _unique(tags)


class KazakhstanDomesticSupportSource(BaseSource):
    slug = "kazakhstan_domestic_support"
    name = "Kazakhstan domestic support"
    base_url = "https://egov.kz/"
    default_tags: ClassVar[list[str]] = [
        "kazakhstan",
        "domestic_support",
        "state_program",
    ]
    programs = DOMESTIC_PROGRAMS

    def _opportunity(
        self,
        program: DomesticProgram,
        *,
        raw: dict[str, Any],
    ) -> Opportunity:
        return Opportunity(
            source=self.slug,
            source_url=program.url,  # type: ignore[arg-type]
            type=program.type,
            title=program.title,
            summary=program.summary,
            amount_min=program.amount_min,
            amount_max=program.amount_max,
            currency=program.currency,
            deadline=program.deadline,
            eligibility=list(program.eligibility),
            tags=_program_tags(program, self.default_tags),
            opportunity_status=program.opportunity_status,
            lifecycle=program.lifecycle,
            raw=raw,
        )

    async def _get_program_response(self, url: str) -> httpx.Response:
        try:
            response = await self.client.get(url)
        except httpx.ConnectError as exc:
            if not _needs_qazindustry_ca_fallback(url, exc):
                raise
            ca_bundle_path = await _qazindustry_ca_bundle_path()
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "grant-radar/0.1 "
                        "(+https://github.com/belilovsky/grant-radar)"
                    )
                },
                follow_redirects=True,
                verify=ca_bundle_path,
            ) as client:
                response = await client.get(url)
        except (httpx.ReadTimeout, httpx.RemoteProtocolError):
            response = await self.client.get(url)
        if _looks_like_unhydrated_govkz_shell(url, response.text):
            return await self.client.get(url, headers=GOVKZ_SEO_HEADERS)
        return response

    async def fetch(self) -> AsyncIterator[Opportunity]:
        count = 0
        for program in self.programs:
            try:
                response = await self._get_program_response(program.url)
                if response.status_code == 404 or response.status_code >= 500:
                    response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                self._mark_fetch_error(exc)
                if program.retain_on_fetch_error and not isinstance(
                    exc, httpx.HTTPStatusError
                ):
                    log.info(
                        "kazakhstan_domestic_support.fetch_retained",
                        url=program.url,
                        reason=type(exc).__name__,
                    )
                    count += 1
                    yield self._opportunity(
                        program,
                        raw={
                            "external_id": program.url,
                            "page_title": program.title,
                            "status_code": None,
                            "deadline_policy": ("rolling" if program.rolling else None),
                            "deadline": (
                                program.deadline.isoformat()
                                if program.deadline
                                else None
                            ),
                            "opportunity_status": program.opportunity_status,
                            "lifecycle": program.lifecycle,
                            **_i18n_payload(program),
                            **_amount_raw_payload(program),
                            **_taxonomy_payload(program),
                            "application_url": program.application_url,
                            "eligibility_raw": list(program.eligibility),
                            **_curated_detail_payload(program, "parse_error"),
                            "status_note": (
                                "official curated domestic-support page "
                                "retained; automated fetch failed with "
                                f"{type(exc).__name__}"
                            ),
                        },
                    )
                    continue
                log.warning(
                    "kazakhstan_domestic_support.fetch_failed",
                    url=program.url,
                    error=repr(exc),
                )
                continue
            if _is_unavailable_page(response.text):
                log.info(
                    "kazakhstan_domestic_support.unavailable_page",
                    url=program.url,
                )
                continue

            page_title = _html_title(response.text)
            raw = {
                "external_id": program.url,
                "page_title": page_title,
                "status_code": response.status_code,
                "deadline_policy": "rolling" if program.rolling else None,
                "deadline": (
                    program.deadline.isoformat() if program.deadline else None
                ),
                "opportunity_status": program.opportunity_status,
                "lifecycle": program.lifecycle,
                **_i18n_payload(program),
                **_amount_raw_payload(program),
                **_taxonomy_payload(program),
                "application_url": program.application_url,
                "eligibility_raw": list(program.eligibility),
            }
            if _is_blocked_fetch(response.status_code, page_title):
                raw.update(
                    {
                        "page_title": program.title,
                        **_curated_detail_payload(program, "blocked"),
                        "status_note": (
                            "official curated domestic-support page retained; "
                            "automated fetch was blocked or rate limited"
                        ),
                    }
                )
            else:
                snapshot = _detail_snapshot(response.text)
                if snapshot is not None:
                    raw.update(snapshot)
                else:
                    raw.update(_curated_detail_payload(program, "parse_error"))

            count += 1
            yield self._opportunity(program, raw=raw)

        log.info("kazakhstan_domestic_support.batch", count=count)


KazakhstanDomesticSupportParser = KazakhstanDomesticSupportSource
DOMESTIC_PROGRAM_BY_URL = {program.url: program for program in DOMESTIC_PROGRAMS}
DOMESTIC_PROGRAM_TAGS = {
    program.url: _program_tags(program, KazakhstanDomesticSupportSource.default_tags)
    for program in DOMESTIC_PROGRAMS
}
