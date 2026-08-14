"""Official global training opportunities relevant to Kazakhstan applicants."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date

import httpx
import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text
from sources.base import BaseSource

log = structlog.get_logger()


@dataclass(frozen=True)
class GlobalTrainingProgram:
    url: str
    title: str
    summary: str
    title_ru: str
    summary_ru: str
    funder: str
    opportunity_type: OpportunityType
    deadline: date
    tags: tuple[str, ...]
    eligibility: tuple[str, ...]
    amount_raw: str
    application_url: str


PROGRAMS = (
    GlobalTrainingProgram(
        url=(
            "https://gpad.hiroshima-u.ac.jp/"
            "fy2026-mid-career-course-%E2%80%95call-for-applicants/"
        ),
        title="FY2026 Mid-Career Course for peacebuilding and development professionals",
        summary=(
            "Official Hiroshima University GPAD call for the FY2026 Mid-Career "
            "Course, implemented with UNITAR Hiroshima for mid-level "
            "professionals in peacebuilding and international development. "
            "The in-person course runs in Japan from 7 to 13 January 2027; "
            "applications are accepted until 31 August 2026 at 5:00 PM Japan time."
        ),
        title_ru=(
            "FY2026 Mid-Career Course для специалистов по миростроительству "
            "и развитию"
        ),
        summary_ru=(
            "Официальный конкурс Hiroshima University GPAD на курс FY2026 "
            "Mid-Career Course, который проводится совместно с UNITAR Hiroshima "
            "для специалистов среднего уровня в миростроительстве и международном "
            "развитии. Очная программа пройдёт в Японии 7–13 января 2027 года; "
            "заявки принимаются до 31 августа 2026 года, 17:00 по японскому времени."
        ),
        funder="Hiroshima University GPAD / UNITAR Hiroshima",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 8, 31),
        tags=(
            "global",
            "international",
            "central_asia_eligible",
            "japan",
            "unitar",
            "fellowship",
            "education",
            "capacity_building",
            "professional_development",
            "peacebuilding",
            "international_development",
        ),
        eligibility=(
            "Applicants from diverse countries with at least seven years of "
            "professional experience in peacebuilding or international development, "
            "fluency in English and availability for the full course",
        ),
        amount_raw=(
            "no participation fee; for non-Japanese participants the programme "
            "covers Tokyo-Higashi-Hiroshima transport and accommodation during "
            "training, while travel to and from Japan, food and personal expenses "
            "are not covered"
        ),
        application_url="mailto:gpad-midcareer@office.hiroshima-u.ac.jp",
    ),
    GlobalTrainingProgram(
        url=(
            "https://kz.usembassy.gov/fulbright-foreign-language-teaching-"
            "assistant-program-russian-language-instruction/"
        ),
        title="Fulbright Foreign Language Teaching Assistant Program for Kazakhstan",
        summary=(
            "Official U.S. Embassy Kazakhstan page for the Fulbright Foreign "
            "Language Teaching Assistant Program for Russian language instruction. "
            "The nine-month non-degree programme places Kazakhstan teachers or "
            "future teachers of English at U.S. host universities; applications "
            "are due by 15 August 2026 at 12:00 p.m. Astana time."
        ),
        title_ru=(
            "Fulbright Foreign Language Teaching Assistant Program для Казахстана"
        ),
        summary_ru=(
            "Fulbright FLTA приглашает преподавателей и будущих преподавателей "
            "английского языка из Казахстана провести девять месяцев в "
            "университете США. Участники помогают преподавать русский язык, "
            "проходят обязательные курсы и знакомят кампус с культурой Казахстана."
        ),
        funder="U.S. Embassy in Kazakhstan / Fulbright Program",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 8, 15),
        tags=(
            "kazakhstan",
            "us",
            "fulbright",
            "fellowship",
            "scholarship",
            "education",
            "higher_education",
            "teacher_training",
            "student_exchange",
        ),
        eligibility=(
            "Citizens of Kazakhstan residing in Kazakhstan who are teachers of "
            "English or training to become teachers of English and meet the "
            "official Fulbright FLTA eligibility rules",
        ),
        amount_raw=(
            "monthly stipend, accident and sickness coverage, travel support, "
            "and U.S. host university tuition waivers for required coursework"
        ),
        application_url="https://apply.iie.org/flta2027",
    ),
    GlobalTrainingProgram(
        url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57742121&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
        title="DAAD Research Grants in Germany",
        summary=(
            "Official DAAD Central Asia scholarship-database record for research "
            "stays in Germany during a doctorate or the early postdoc phase. "
            "Applicants from Kazakhstan can apply as PhD students or PhD holders; "
            "the next application deadline is 17 August 2026 for funding from "
            "February 2027."
        ),
        title_ru="Исследовательские гранты DAAD в Германии",
        summary_ru=(
            "Официальная запись базы стипендий DAAD Central Asia о "
            "исследовательских стажировках в Германии во время докторантуры "
            "или на раннем постдокторском этапе. Заявители из Казахстана могут "
            "подаваться как PhD students или PhD holders; ближайший дедлайн – "
            "17 августа 2026 года для финансирования с февраля 2027 года."
        ),
        funder="DAAD Central Asia",
        opportunity_type=OpportunityType.GRANT,
        deadline=date(2026, 8, 17),
        tags=(
            "kazakhstan",
            "central_asia",
            "germany",
            "daad",
            "grant",
            "scholarship",
            "research",
            "higher_education",
            "doctoral",
            "postdoc",
        ),
        eligibility=(
            "Applicants from Kazakhstan who are doctoral students outside Germany "
            "or PhD holders up to four years after completing the doctorate, "
            "under the official DAAD programme rules",
        ),
        amount_raw=(
            "monthly scholarship payments of EUR 1,400, insurance payments, "
            "travel allowance for funding periods over six months, and a EUR 460 "
            "research allowance for funding periods over six months"
        ),
        application_url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57742121&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
    ),
)


PROGRAM_EDITORIAL_RU = {
    "https://apply.iie.org/flta2027": {
        "social_title": "Fulbright FLTA: 9 месяцев в университете США",
        "summary": (
            "Для преподавателей и будущих преподавателей английского из "
            "Казахстана: учёба и работа в американском университете."
        ),
        "audience_label": "Кому подходит",
        "eligibility": [
            "Граждане Казахстана, которые живут в стране и преподают "
            "английский либо учатся на преподавателя английского"
        ],
        "highlights_label": "Что даёт программа",
        "highlights": [
            "ежемесячную стипендию",
            "поддержку поездки",
            "страхование от несчастных случаев и заболеваний",
            "обязательные курсы принимающего университета без оплаты",
        ],
        "amount": "США · очно · 9 месяцев · без получения степени",
        "amount_label": "Формат",
        "deadline_display": "15 августа · 12:00 по времени Астаны",
        "deadline_label": "Дедлайн",
        "steps_title": "Что сделать сейчас",
        "application_step_titles": [
            "Проверьте критерии FLTA",
            "Заполните анкету IIE",
            "Отправьте до дедлайна",
        ],
        "application_steps": [
            "Проверить критерии FLTA и список документов",
            "Заполнить анкету на официальном портале IIE",
            "Отправить до 15 августа, 12:00, и сохранить подтверждение",
        ],
        "prepare_items": [
            {
                "title": "Проверьте критерии FLTA",
                "text": (
                    "Сверьте гражданство, проживание в Казахстане и статус "
                    "преподавателя или будущего преподавателя английского языка."
                ),
            },
            {
                "title": "Сверьте список документов",
                "text": "Используйте актуальный перечень документов на портале IIE.",
            },
            {
                "title": "Заполните официальную анкету",
                "text": "Подача идёт через отдельную форму Fulbright FLTA на портале IIE.",
            },
            {
                "title": "Зафиксируйте срок",
                "text": (
                    "Отправьте заявку до 15 августа, 12:00 по времени Астаны, "
                    "и сохраните подтверждение."
                ),
            },
        ],
    },
    (
        "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
        "?detail_to_show=0&detail_to_show=57742121&intention=&onlydaad=0"
        "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
    ): {
        "social_title": "DAAD: исследовательский грант в Германии",
        "summary": (
            "Финансирование исследовательской работы в Германии для "
            "докторантов и исследователей на раннем постдокторском этапе."
        ),
        "audience_label": "Кому подходит",
        "eligibility": [
            "Докторанты из Казахстана, обучающиеся вне Германии, и postdocs, "
            "защитившиеся не более четырёх лет назад"
        ],
        "highlights_label": "Формат программы",
        "highlights": [
            "докторантам — от 2 до 12 месяцев",
            "postdocs — от 2 до 6 месяцев",
            "проект проводится в Германии по согласованию с научным руководителем",
        ],
        "amount": (
            "1 400 EUR в месяц, страхование; при сроке свыше 6 месяцев — "
            "доплата на поездку и 460 EUR на исследование"
        ),
        "amount_label": "Финансирование",
        "deadline_display": "17 августа 2026",
        "deadline_label": "Дедлайн",
        "steps_title": "Как подать",
        "application_step_titles": [
            "Согласуйте проект",
            "Подготовьте документы",
            "Подайте через портал DAAD",
        ],
        "application_steps": [
            "Согласовать тему и рабочий план с научным руководителем в Германии",
            "Подготовить исследовательское предложение, график и документы DAAD",
            "Загрузить заявку через портал DAAD до 17 августа",
        ],
        "prepare_items": [
            {
                "title": "Проверьте академический статус",
                "text": (
                    "Для докторантов действуют требования к сроку начала "
                    "докторантуры; для postdocs — до четырёх лет после защиты."
                ),
            },
            {
                "title": "Найдите научного руководителя",
                "text": (
                    "Исследовательский проект должен быть согласован с "
                    "принимающим научным руководителем в Германии."
                ),
            },
            {
                "title": "Соберите заявку",
                "text": (
                    "Подготовьте исследовательское предложение, рабочий график "
                    "и документы из актуального списка DAAD."
                ),
            },
            {
                "title": "Подайте через DAAD",
                "text": "Загрузите полный комплект через официальный портал до дедлайна.",
            },
        ],
    },
}


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    return clean_source_text(match.group("title")) or None


def _is_source_unavailable(page_title: str | None, html: str) -> bool:
    text = f"{page_title or ''} {html[:4000]}".lower()
    return "technical difficulties" in text or "currently experiencing" in text


class GlobalTrainingOpportunitiesSource(BaseSource):
    slug = "global_training_opportunities"
    name = "Global Training Opportunities"
    base_url = "https://gpad.hiroshima-u.ac.jp/"

    async def fetch(self) -> AsyncIterator[Opportunity]:
        count = 0
        for program in PROGRAMS:
            page_title: str | None = None
            status_code: int | None = None
            detail_fetch_status = "not_attempted"
            detail_fetch_error: str | None = None
            try:
                response = await self.client.get(program.url)
                status_code = response.status_code
                response.raise_for_status()
                page_title = _html_title(response.text)
                detail_fetch_status = (
                    "source_unavailable"
                    if _is_source_unavailable(page_title, response.text)
                    else "ok"
                )
                if detail_fetch_status == "source_unavailable":
                    page_title = None
            except httpx.HTTPError as exc:
                log.warning(
                    "global_training.fetch_failed",
                    url=program.url,
                    error=str(exc),
                )
                continue

            count += 1
            editorial_ru = PROGRAM_EDITORIAL_RU.get(program.application_url, {})
            ru_content = {
                "title": program.title_ru,
                "summary": program.summary_ru,
                **editorial_ru,
            }
            yield Opportunity(
                source=self.slug,
                source_url=program.url,  # type: ignore[arg-type]
                type=program.opportunity_type,
                title=program.title,
                summary=program.summary,
                funder=program.funder,
                deadline=program.deadline,
                eligibility=list(program.eligibility),
                tags=["official_source", *program.tags],
                opportunity_status="open",
                lifecycle="open",
                raw={
                    "external_id": program.url,
                    "page_title": page_title,
                    "status_code": status_code,
                    "detail_fetch_status": detail_fetch_status,
                    "detail_fetch_error": detail_fetch_error,
                    "amount_raw": program.amount_raw,
                    "application_url": program.application_url,
                    "deadline": program.deadline.isoformat(),
                    "opportunity_status": "open",
                    "lifecycle": "open",
                    "i18n": {
                        "ru": ru_content,
                        "en": {
                            "title": program.title,
                            "summary": program.summary,
                        },
                    },
                },
            )

        log.info("global_training.batch", count=count)


GlobalTrainingOpportunitiesParser = GlobalTrainingOpportunitiesSource
