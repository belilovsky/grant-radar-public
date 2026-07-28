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
    opportunity_status: str = "open"
    lifecycle: str = "open"


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
            "Официальная страница Посольства США в Казахстане о программе "
            "Fulbright Foreign Language Teaching Assistant для преподавания "
            "русского языка. Девятимесячная неакадемическая программа размещает "
            "казахстанских преподавателей или будущих преподавателей английского "
            "языка в принимающих университетах США; заявки принимаются до "
            "15 августа 2026 года, 12:00 по времени Астаны."
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
            "Официальная запись базы стипендий DAAD Central Asia об "
            "исследовательских стажировках в Германии во время докторантуры "
            "или на раннем постдокторском этапе. Заявители из Казахстана могут "
            "подаваться как докторанты или недавние обладатели докторской "
            "степени; ближайший срок подачи – 17 августа 2026 года для "
            "финансирования с февраля 2027 года."
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
    GlobalTrainingProgram(
        url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=50026200&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
        title="DAAD Study Scholarships for Master's Studies",
        summary=(
            "Official DAAD Central Asia scholarship-database record for a full "
            "postgraduate or master's programme in Germany, or one year of study "
            "in Germany within a master's programme at the home university. "
            "Applicants from Kazakhstan with a first degree can apply by "
            "2 November 2026; funding lasts 10-24 months and begins in 2027."
        ),
        title_ru="Стипендии DAAD для обучения в магистратуре",
        summary_ru=(
            "Официальная запись базы стипендий DAAD Central Asia для полного "
            "курса магистратуры в Германии или одного года обучения в Германии "
            "в рамках магистерской программы домашнего вуза. Заявители из "
            "Казахстана с первым высшим образованием могут подать заявку до "
            "2 ноября 2026 года; финансирование рассчитано на 10–24 месяца и "
            "начинается в 2027 году."
        ),
        funder="DAAD Central Asia",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 11, 2),
        tags=(
            "kazakhstan",
            "central_asia",
            "germany",
            "daad",
            "scholarship",
            "education",
            "higher_education",
            "master_studies",
            "graduates",
            "student_exchange",
            "german_language",
        ),
        eligibility=(
            "Applicants from Kazakhstan who have completed a first degree by "
            "the start of funding and meet the official DAAD programme requirements",
        ),
        amount_raw=(
            "EUR 992 monthly scholarship, insurance payments, travel allowance, "
            "annual study allowance of EUR 460, and possible additional benefits; "
            "tuition fees are not covered"
        ),
        application_url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=50026200&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
    ),
    GlobalTrainingProgram(
        url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57135739&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
        title="DAAD Doctoral Programmes in Germany",
        summary=(
            "Official DAAD scholarship-database record for completing a doctoral "
            "degree in Germany through an individual supervised project or a "
            "structured doctoral programme. Applicants from Kazakhstan with "
            "above-average qualifications can apply by 16 November 2026; funding "
            "begins in 2027 and can last up to four years."
        ),
        title_ru="Гранты DAAD на докторантуру в Германии",
        summary_ru=(
            "Официальная запись базы стипендий DAAD для получения докторской "
            "степени в Германии: индивидуальный исследовательский проект под "
            "научным руководством или структурированная докторская программа. "
            "Заявители из Казахстана с сильной академической подготовкой могут "
            "подать заявку до 16 ноября 2026 года; финансирование начинается "
            "в 2027 году и может длиться до четырёх лет."
        ),
        funder="DAAD",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 11, 16),
        tags=(
            "kazakhstan",
            "central_asia",
            "germany",
            "daad",
            "scholarship",
            "research",
            "higher_education",
            "doctoral",
            "graduates",
            "german_language",
        ),
        eligibility=(
            "Applicants from Kazakhstan with above-average qualifications who "
            "completed a master's degree, Diplom, or in exceptional cases a "
            "bachelor's degree by the start of funding and meet the official "
            "DAAD programme requirements",
        ),
        amount_raw=(
            "EUR 1,400 monthly scholarship, insurance payments, travel allowance, "
            "annual research allowance of EUR 460, and possible additional "
            "benefits including language-course support"
        ),
        application_url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57135739&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
    ),
    GlobalTrainingProgram(
        url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57507783&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
        title="DAAD Bi-nationally Supervised Doctoral Degrees / Cotutelle",
        summary=(
            "Official DAAD Central Asia scholarship-database record for "
            "bi-national doctoral supervision or a Cotutelle doctorate between "
            "the home university and a German university. Applicants from "
            "Kazakhstan can apply by 16 November 2026; funding begins in 2027 "
            "and covers 7-24 months of research stays in Germany."
        ),
        title_ru="Гранты DAAD на совместную докторантуру Cotutelle",
        summary_ru=(
            "Официальная запись базы стипендий DAAD Central Asia для "
            "совместной докторантуры: научное руководство в домашнем вузе и "
            "немецком университете либо формат Cotutelle с индивидуальным "
            "соглашением между университетами. Заявители из Казахстана могут "
            "подать заявку до 16 ноября 2026 года; финансирование начинается "
            "в 2027 году и покрывает 7–24 месяца исследовательских поездок "
            "в Германию."
        ),
        funder="DAAD Central Asia",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 11, 16),
        tags=(
            "kazakhstan",
            "central_asia",
            "germany",
            "daad",
            "scholarship",
            "research",
            "higher_education",
            "doctoral",
            "graduates",
            "cotutelle",
            "university_partnership",
            "german_language",
        ),
        eligibility=(
            "Applicants from Kazakhstan pursuing bi-national doctoral supervision "
            "who have earned a master's degree, Diplom or in exceptional cases a "
            "bachelor's degree by the start of funding, or Cotutelle applicants "
            "admitted to a doctoral programme by the start of funding",
        ),
        amount_raw=(
            "EUR 1,400 monthly payments during stays in Germany, insurance "
            "payments, travel allowance for up to three outward and return "
            "journeys on application, EUR 460 research allowance, and possible "
            "language-course support"
        ),
        application_url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=57507783&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
    ),
    GlobalTrainingProgram(
        url="https://arts.britishcouncil.org/connections-through-culture",
        title="Connections Through Culture Grants 2026 for Kazakhstan",
        summary=(
            "Official British Council Arts call for Connections Through Culture "
            "2026. The programme funds creative collaboration between at least "
            "one UK-based partner and at least one partner in an eligible country, "
            "including Kazakhstan. Applications close on 12 August 2026 at "
            "23:59 BST; partnerships with Kazakhstan can request up to "
            "GBP 10,000."
        ),
        title_ru="Гранты Connections Through Culture 2026 для Казахстана",
        summary_ru=(
            "Официальный конкурс British Council Arts Connections Through "
            "Culture 2026 для творческого сотрудничества между партнёром из "
            "Великобритании и партнёром из одной из стран-участниц, включая "
            "Казахстан. Заявки принимаются до 12 августа 2026 года, 23:59 BST; "
            "партнёрства с Казахстаном могут запросить до 10 000 GBP."
        ),
        funder="British Council Arts",
        opportunity_type=OpportunityType.GRANT,
        deadline=date(2026, 8, 12),
        tags=(
            "kazakhstan",
            "uk",
            "british_council",
            "grant",
            "creative_industries",
            "culture",
            "partnership",
            "digital",
        ),
        eligibility=(
            "Applications must involve at least one UK-based partner and at "
            "least one partner legally based in Kazakhstan or another eligible "
            "participating country throughout the project activity period",
        ),
        amount_raw=(
            "up to GBP 10,000 for partnerships between UK-based partners and "
            "partners in Kazakhstan; grant funding must cover the full partnership "
            "activity"
        ),
        application_url=("https://britishcouncilarts.grantplatform.com/"),
    ),
    GlobalTrainingProgram(
        url=(
            "https://www.daad-kyrgyzstan.org/en/find-funding/scholarship-database/"
            "?detail_to_show=0&detail_to_show=50110016&intention=&onlydaad=0"
            "&origin=73&pg=1&q=&status=0&subject=0&tab=&target=73&type=a"
        ),
        title="DAAD Study Visits for Academics – Artists and Architects",
        summary=(
            "Official DAAD Central Asia scholarship-database record for study "
            "visits in Germany by university teachers in architecture, fine art, "
            "film, design, visual communication, performing arts or music. "
            "Applicants from Kazakhstan can apply by 17 August 2026 for funding "
            "from February 2027; a second 2026 deadline is 16 November."
        ),
        title_ru=("Стажировки DAAD для преподавателей искусства и архитектуры"),
        summary_ru=(
            "Официальная запись базы стипендий DAAD Central Asia о "
            "стажировках в Германии для преподавателей вузов в архитектуре, "
            "изобразительном искусстве, кино, дизайне, визуальной коммуникации, "
            "исполнительских искусствах и музыке. Заявители из Казахстана могут "
            "подать заявку до 17 августа 2026 года для финансирования с февраля "
            "2027 года; второй срок подачи в 2026 году – 16 ноября."
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
            "higher_education",
            "faculty",
            "study_visit",
            "architecture",
            "creative_industries",
            "arts",
            "design",
            "music",
            "performing_arts",
            "university_partnership",
        ),
        eligibility=(
            "University teachers from Kazakhstan in architecture, fine art, "
            "film, design, visual communication, performing arts or music whose "
            "study visit is coordinated with a German host institution",
        ),
        amount_raw=(
            "monthly payments of EUR 2,000 for assistant teachers, assistant "
            "professors and lecturers, EUR 2,150 for professors, plus travel "
            "allowance; funding lasts one to three months and must begin in 2027"
        ),
        application_url=(
            "https://www2.daad.de/deutschland/stipendium/datenbank/en/"
            "21148-scholarship-database/?detail=50110016"
        ),
    ),
    GlobalTrainingProgram(
        url="https://www.chevening.org/scholarship/kazakhstan/",
        title="Chevening Scholarship for Kazakhstan 2027-2028",
        summary=(
            "Official Chevening country page for Kazakhstan and the 2027-2028 "
            "scholarship cycle. Applications open on 4 August 2026 at 11:00 UTC "
            "and close on 6 October 2026 at 11:00 UTC; the award supports a "
            "one-year master's degree in the United Kingdom."
        ),
        title_ru="Стипендия Chevening для Казахстана 2027–2028",
        summary_ru=(
            "Официальная страница Chevening для Казахстана и цикла стипендий "
            "2027–2028. Приём заявок откроется 4 августа 2026 года в 11:00 UTC "
            "и завершится 6 октября 2026 года в 11:00 UTC; стипендия покрывает "
            "годичную магистратуру в Великобритании."
        ),
        funder="Chevening / UK Foreign, Commonwealth and Development Office",
        opportunity_type=OpportunityType.FELLOWSHIP,
        deadline=date(2026, 10, 6),
        tags=(
            "kazakhstan",
            "uk",
            "chevening",
            "fcdo",
            "scholarship",
            "fellowship",
            "higher_education",
            "master_studies",
            "leadership",
            "student_exchange",
        ),
        eligibility=(
            "Citizens of Kazakhstan applying through the official Chevening "
            "country page who meet Chevening eligibility, work-experience and "
            "course-selection requirements",
        ),
        amount_raw=(
            "fully funded one-year master's degree in the United Kingdom; "
            "Chevening scholarships generally cover tuition, travel and living "
            "support under the official award rules"
        ),
        application_url="https://www.chevening.org/scholarship/kazakhstan/",
        opportunity_status="upcoming",
        lifecycle="forecast",
    ),
    GlobalTrainingProgram(
        url="https://www.explorers.org/grants/rising-explorer-grant/",
        title="Rising Explorer Grant 2027",
        summary=(
            "Official Explorers Club grant for high school students, college "
            "undergraduates and independent researchers working at an equivalent "
            "level anywhere in the world. The programme supports field-science "
            "projects across disciplines such as ecology, conservation, "
            "environmental science, archaeology and anthropology; 2027-cycle "
            "applications are due by 31 August 2026 at 6:00 PM ET."
        ),
        title_ru="Грант Rising Explorer 2027",
        summary_ru=(
            "Официальный грант The Explorers Club для старшеклассников, "
            "студентов бакалавриата и независимых исследователей сопоставимого "
            "уровня из любой страны, включая Казахстан. Программа поддерживает "
            "полевые научные проекты в экологии, охране природы, науках об "
            "окружающей среде, археологии, антропологии и близких областях; "
            "заявки на цикл 2027 принимаются до 31 августа 2026 года, "
            "18:00 ET."
        ),
        funder="The Explorers Club",
        opportunity_type=OpportunityType.GRANT,
        deadline=date(2026, 8, 31),
        tags=(
            "global",
            "central_asia_eligible",
            "grant",
            "science",
            "research",
            "field_research",
            "environment",
            "conservation",
            "ecology",
            "biology",
            "archaeology",
            "anthropology",
            "youth",
            "undergraduate",
            "high_school",
            "explorers_club",
        ),
        eligibility=(
            "High school students, college undergraduates and independent "
            "researchers at an equivalent level worldwide, including applicants "
            "from Kazakhstan, with a field-science project designed to generate "
            "new knowledge",
        ),
        amount_raw=(
            "awards average USD 2,000; funds support real-world field research "
            "projects rather than adventure travel, school trips or non-scientific "
            "expeditions"
        ),
        application_url="https://www.explorers.org/grants/rising-explorer-grant/",
    ),
    GlobalTrainingProgram(
        url="https://www.isocfoundation.org/grant-programme/beyond-the-net-grant-program/",
        title="Beyond the Net Grant Program",
        summary=(
            "Official Internet Society Foundation grant programme for Internet "
            "Society Chapters. The call is open until 1 October 2026 and supports "
            "local projects that improve meaningful access to an open, trusted "
            "and globally connected Internet, including connectivity, affordable "
            "access, online safety and open-Internet work."
        ),
        title_ru="Грантовая программа Beyond the Net",
        summary_ru=(
            "Официальная грантовая программа Internet Society Foundation для "
            "отделений Internet Society. Приём заявок открыт до 1 октября "
            "2026 года; поддерживаются локальные проекты по доступу к открытому, "
            "надёжному и глобально связанному интернету, включая подключение "
            "сообществ, доступность связи, онлайн-безопасность и защиту открытого "
            "интернета."
        ),
        funder="Internet Society Foundation",
        opportunity_type=OpportunityType.GRANT,
        deadline=date(2026, 10, 1),
        tags=(
            "global",
            "central_asia_eligible",
            "grant",
            "digital",
            "internet_access",
            "connectivity",
            "digital_inclusion",
            "online_safety",
            "open_internet",
            "community",
            "civil_society",
            "infrastructure",
            "cybersecurity",
            "capacity_building",
            "isoc",
            "internet_society_foundation",
        ),
        eligibility=(
            "Internet Society Chapters in good standing, including eligible "
            "chapters in Central Asia, with an official bank account and current "
            "reporting status under Internet Society Foundation rules",
        ),
        amount_raw=(
            "chapters may manage up to two simultaneous Beyond the Net grants, "
            "not exceeding USD 55,000 in total; projects above USD 20,000 require "
            "an external partner and at least a six-month implementation period"
        ),
        application_url=(
            "https://www.isocfoundation.org/grant-programme/"
            "beyond-the-net-grant-program/"
        ),
    ),
)


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
                opportunity_status=program.opportunity_status,
                lifecycle=program.lifecycle,
                raw={
                    "external_id": program.url,
                    "page_title": page_title,
                    "status_code": status_code,
                    "detail_fetch_status": detail_fetch_status,
                    "detail_fetch_error": detail_fetch_error,
                    "amount_raw": program.amount_raw,
                    "application_url": program.application_url,
                    "deadline": program.deadline.isoformat(),
                    "opportunity_status": program.opportunity_status,
                    "lifecycle": program.lifecycle,
                    "i18n": {
                        "ru": {
                            "title": program.title_ru,
                            "summary": program.summary_ru,
                        },
                        "en": {
                            "title": program.title,
                            "summary": program.summary,
                        },
                    },
                },
            )

        log.info("global_training.batch", count=count)


GlobalTrainingOpportunitiesParser = GlobalTrainingOpportunitiesSource
