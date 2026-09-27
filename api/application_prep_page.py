"""Private-by-default application preparation workspace."""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from html import escape
from typing import Any

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard_copy import dashboard_copy
from api.integration_versions import AVDS_VERSION
from core.decision_support import program_truth
from core.models import OpportunityDetail

_DIGITAL_EQUIPMENT_REIMBURSEMENT_ID = "1684ec38-c20f-5844-9e69-140b4a595c28"
_DIGITAL_EQUIPMENT_REIMBURSEMENT: dict[str, dict[str, Any]] = {
    "ru": {
        "program_title": "Возмещение затрат на внедрение цифровых технологий",
        "organizer": "QazIndustry",
        "intake": "В течение календарного года, пока не исчерпан бюджет этого года",
        "amount": "40% затрат, принимаемых к возмещению, не более 60 млн ₸ за календарный год",
        "eligibility": (
            "Заявитель производит товар из Перечня приоритетных товаров, зарегистрирован "
            "не менее календарного года и не относится к исключённым категориям Правил. "
            "На дату подачи не должно быть задолженности по налогам, обязательным "
            "пенсионным и профессиональным пенсионным взносам, социальным отчислениям "
            "(кроме платежей с законной отсрочкой). Требуется ежегодный рост налоговых "
            "отчислений за предыдущие три года; это условие не применяется к освобождённым "
            "от налогов и зарегистрированным менее семи лет. С 2026 года заявитель также "
            "должен находиться в Реестре казахстанских товаропроизводителей."
        ),
        "official_source": "https://qazindustry.gov.kz/ru/business_reimbursement",
        "rules_source": "https://qazindustry.gov.kz/docs/v2200028320.22-12-2025.rus%20%281%29.pdf",
        "rules_source_label": "Правила №308 с изменениями №442 (RU, PDF)",
        "documents_source": "https://qazindustry.gov.kz/docs/instrukcia070726.pdf",
        "documents_source_label": "Инструкция QazIndustry (RU, PDF)",
        "application_portal": "https://sez.qazindustry.gov.kz/ru/service/5/evaluate",
        "application_portal_label": "Портал подачи QazIndustry (RU)",
        "copy": {
            "page_title": "Подготовка заявки на возмещение затрат",
            "eyebrow": "Рабочий черновик",
            "title": "Подготовьте черновик для возмещения затрат на цифровое оборудование",
            "lead": (
                "Внесите сведения о производителе и приобретённом цифровом "
                "оборудовании. QAZ.FUND соберёт локальный черновик для сверки "
                "с официальными условиями и формой QazIndustry."
            ),
            "known": "Условия программы",
            "program": "Программа",
            "organizer": "Оператор услуги",
            "deadline": "Период подачи",
            "amount": "Размер возмещения",
            "eligibility": "Критерии заявителя",
            "criteria_heading": "Критерии по правилам QazIndustry",
            "readiness": "Заполнение черновика",
            "required_done": "Заполнено обязательных полей черновика: {done} из {total}",
            "applicant_note": "Сведения о производителе и предварительная проверка критериев.",
            "org_name": "Наименование организации-производителя",
            "legal_form": "Организационно-правовая форма",
            "country": "Место регистрации организации",
            "contact": "Ответственный за черновик",
            "fit": "Самопроверка критериев заявителя",
            "fit_placeholder": (
                "Отметьте, как заявитель соответствует критериям, и укажите применимые исключения."
            ),
            "project": "Цифровое оборудование",
            "project_note": "Укажите приобретённое оборудование и его назначение для цифровизации.",
            "project_name": "Наименование, модель и производитель оборудования",
            "problem": "Задача предприятия, для которой приобретено оборудование",
            "solution": "Как оборудование используется в деятельности предприятия",
            "beneficiaries": "Приоритетный товар или вид продукции предприятия",
            "geography": "Место эксплуатации оборудования",
            "impact": "Покупка и подтверждение затрат",
            "impact_note": (
                "Для цифрового оборудования 24-месячный срок считают от последнего платежа, "
                "если покупка оплачена несколькими платежами."
            ),
            "outcomes": "Дата последнего платежа за цифровое оборудование",
            "indicators": "Сумма счетов-фактур на приобретённое оборудование",
            "evidence": "Платёжные документы и документы об оплате",
            "delivery": "Технические сведения",
            "delivery_note": "Заполните реквизиты и характеристики по документам на оборудование.",
            "team": "Изготовитель, дата выпуска и идентификационный номер оборудования",
            "timeline": "Основные технические характеристики",
            "partners": "Руководство, техпаспорт и спецификация комплектации (если имеются)",
            "risks": "Дополнительные сведения и документы на оборудование",
            "finance": "Расчёт возмещения",
            "finance_note": "Условия программы указывают ставку 40% и годовой предел 60 млн ₸.",
            "request_amount": "Запрашиваемое возмещение, ₸",
            "cofinance": "Общая сумма подтверждённых затрат, ₸",
            "budget": "Расчёт суммы и реквизиты оплаты",
            "documents": "Документы для цифрового оборудования",
            "documents_note": (
                "Список относится к приобретению цифрового оборудования; пакет и форму заявки "
                "смотрите в Правилах и инструкции QazIndustry."
            ),
            "criteria_note": (
                "Расхождение источников: страница условий QazIndustry указывает исключение "
                "«менее 3 лет», а действующие Правила №308 с изменениями №442 и инструкция "
                "указывают «менее 7 лет». Инструкция также требует включения в Реестр "
                "казахстанских товаропроизводителей с 2026 года; страница условий этого "
                "требования не показывает. Здесь приведена формулировка из Правил и инструкции."
            ),
            "draft_note": "Текст обновляется по мере заполнения и хранится только в этом браузере.",
            "empty_value": "",
            "source": "Открыть условия QazIndustry (RU)",
            "source_label": "Условия программы",
            "rules_source_link": "Открыть Правила №308 с изменениями №442 (RU, PDF)",
            "documents_source_link": "Открыть инструкцию QazIndustry (RU, PDF)",
            "application_portal_link": "Перейти к порталу подачи QazIndustry (RU)",
            "sections": {
                "programme": "Программа",
                "applicant": "Заявитель",
                "project": "Оборудование",
                "impact": "Покупка и оплата",
                "delivery": "Технические сведения",
                "finance": "Расчёт возмещения",
                "documents": "Документы",
            },
        },
        "checklist": [
            "Заявка",
            (
                "Отчёт о приобретённом цифровом оборудовании, деятельности предприятия и "
                "необходимости приобретения"
            ),
            "Копии счетов-фактур на общую сумму приобретённого цифрового оборудования",
            (
                "Копии платёжных документов на стоимость оборудования либо документы об оплате "
                "аккредитивом, зачёте требований или удержании штрафа"
            ),
            "Выписка из реестра казахстанских товаропроизводителей",
            "Копии документов об освобождении от налогов (если применимо)",
            "Копия договора на приобретение цифрового оборудования",
            (
                "Копии первичных учётных документов о приёмке и передаче: акт, накладная на "
                "отпуск запасов на сторону и другие документы"
            ),
            (
                "Копия технической документации: руководство, дата изготовления, "
                "идентификационный номер изготовителя, основные параметры; спецификация "
                "комплектации и техпаспорт при наличии"
            ),
            "Фотографии приобретённого цифрового оборудования",
        ],
    },
    "kk": {
        "program_title": "Цифрлық технологияларды енгізуге жұмсалған шығындарды өтеу",
        "organizer": "QazIndustry",
        "intake": "Күнтізбелік жыл ішінде, сол жылдың бюджеті толық игерілгенге дейін",
        "amount": "Өтеуге жататын шығындардың 40%-ы, күнтізбелік жылға ең көбі 60 млн ₸",
        "eligibility": (
            "Өтініш беруші Басым тауарлар тізбесіндегі өнімді өндіруі, кемінде бір "
            "күнтізбелік жыл бұрын тіркелуі және Қағидалардың 3-тармағында шығарылған "
            "субъектілер қатарына жатпауы керек. Өтінім күніне салықтар, міндетті және "
            "міндетті кәсіптік зейнетақы жарналары мен әлеуметтік аударымдар бойынша "
            "берешек болмауы тиіс (заңды кейінге шегеру жағдайынан басқа). Алдыңғы үш "
            "жылда салық аударымдары жыл сайын өсуі керек; бұл талап салықтан босатылған "
            "немесе тіркелгеніне жеті жыл толмаған субъектілерге қолданылмайды. 2026 "
            "жылдан бастап өтініш беруші Қазақстандық тауар өндірушілер тізілімінде де "
            "болуы керек."
        ),
        "official_source": "https://qazindustry.gov.kz/kk/business_reimbursement",
        "rules_source": "https://qazindustry.gov.kz/docs/v2200028320.22-12-2025.rus%20%281%29.pdf",
        "rules_source_label": "№308 қағидалар, №442 өзгерістерімен (RU, PDF)",
        "documents_source": "https://qazindustry.gov.kz/docs/instrukcia070726.pdf",
        "documents_source_label": "QazIndustry нұсқаулығы (RU, PDF)",
        "application_portal": "https://sez.qazindustry.gov.kz/kk/service/5/evaluate",
        "application_portal_label": "QazIndustry өтінім порталы (KK)",
        "copy": {
            "page_title": "Шығындарды өтеуге өтінімді дайындау",
            "eyebrow": "Жұмыс жобасы",
            "title": "Цифрлық технология шығындарын өтеуге арналған жобаны дайындаңыз",
            "lead": (
                "Өтініш беруші, енгізілетін цифрлық технология және шығындар туралы "
                "мәліметтерді енгізіңіз. QAZ.FUND ресми шарттармен салыстыруға арналған "
                "жергілікті жоба мәтінін құрастырады."
            ),
            "known": "Бағдарлама шарттары",
            "program": "Бағдарлама",
            "organizer": "Қызмет операторы",
            "deadline": "Өтінім қабылдау кезеңі",
            "amount": "Өтеу мөлшері",
            "eligibility": "Өтініш беруші критерийлері",
            "criteria_heading": "QazIndustry жариялаған өтініш беруші критерийлері",
            "readiness": "Жобаның толтырылуы",
            "required_done": "Жобаның міндетті өрістері толтырылды: {done}/{total}",
            "applicant_note": "Өндіруші туралы мәліметтер және критерийлерді алдын ала тексеру.",
            "org_name": "Өндіруші ұйымның атауы",
            "legal_form": "Ұйымдық-құқықтық нысаны",
            "country": "Ұйымның тіркелген жері",
            "contact": "Жобаға жауапты тұлға",
            "fit": "Өтініш беруші критерийлерін өзіндік тексеру",
            "fit_placeholder": (
                "Өтініш берушінің критерийлерге сәйкестігін және қолданылатын "
                "ерекшеліктерді көрсетіңіз."
            ),
            "project": "Цифрлық технология немесе жабдық",
            "project_note": (
                "Енгізілген технологияны, бағдарламалық өнімді немесе жабдықты және оның "
                "өндірісте қолданылуын сипаттаңыз."
            ),
            "project_name": "Технологияның, өнімнің немесе жабдықтың атауы",
            "problem": "Цифрлық технология енгізілетін кәсіпорын міндеті",
            "solution": (
                "Технология, бағдарлама немесе жабдық кәсіпорын жұмысында қалай қолданылады"
            ),
            "beneficiaries": "Кәсіпорын өндіретін басым тауар немесе өнім түрі",
            "geography": "Енгізу немесе жабдықты пайдалану орны",
            "impact": "Шығындар мен төлемді растау",
            "impact_note": (
                "Цифрлық жабдық үшін 24 айлық мерзім сатып алу бірнеше төлеммен жасалса, "
                "соңғы төлем күнінен есептеледі."
            ),
            "outcomes": "Цифрлық жабдық үшін соңғы төлем жасалған күн",
            "indicators": "Шарттар мен шот-фактуралардағы шығындардың жалпы сомасы",
            "evidence": "Төлем құжаттары",
            "delivery": "Техникалық мәліметтер",
            "delivery_note": "Технологияның сипаттамалары мен оны растайтын құжаттарды енгізіңіз.",
            "team": (
                "Жеткізуші/әзірлеуші, өнім нұсқасы немесе жабдықтың өндірушісі және ID нөмірі"
            ),
            "timeline": (
                "Технологияның немесе жабдықтың негізгі техникалық сипаттамалары"
            ),
            "partners": (
                "Нұсқаулық, лицензия, техникалық паспорт немесе спецификация (бар болса)"
            ),
            "risks": "Технологияны енгізу туралы қосымша мәліметтер мен құжаттар",
            "finance": "Өтеу есебі",
            "finance_note": (
                "Бағдарлама шарттары 40% мөлшерлеме мен жылына 60 млн ₸ шегін көрсетеді."
            ),
            "request_amount": "Сұралатын өтемақы, ₸",
            "cofinance": "Расталған шығындардың жалпы сомасы, ₸",
            "budget": "Сома есебі және төлем деректері",
            "documents": "Цифрлық жабдық құжаттары",
            "documents_note": (
                "Бұл тізім цифрлық жабдық сатып алуға арналған; лицензиялық БЖ мен өзге "
                "шығындарға арналған қосымша құжаттарды QazIndustry нұсқаулығынан қараңыз."
            ),
            "criteria_note": (
                "Дереккөздердегі айырмашылық: QazIndustry шарттар бетінде «3 жылдан аз» "
                "делінген, ал №442 өзгерістері енгізілген №308 қағидалар мен нұсқаулықта "
                "«7 жылдан аз» деп көрсетілген. Нұсқаулық 2026 жылдан бастап Қазақстандық "
                "тауар өндірушілер тізілімінде болуды да талап етеді, ал шарттар бетінде "
                "бұл талап көрсетілмеген. Мұнда қағидалар мен нұсқаулықтағы тұжырым қолданылды."
            ),
            "draft_note": "Мәтін толтырылғанда жаңартылады және тек осы браузерде сақталады.",
            "empty_value": "",
            "source": "QazIndustry шарттарын ашу (KK)",
            "source_label": "Бағдарлама шарттары",
            "rules_source_link": "№308 қағидаларды ашу (№442 өзгерістерімен, RU, PDF)",
            "documents_source_link": "QazIndustry нұсқаулығын ашу (RU, PDF)",
            "application_portal_link": "QazIndustry өтінім порталына өту (KK)",
            "sections": {
                "programme": "Бағдарлама",
                "applicant": "Өтініш беруші",
                "project": "Технология",
                "impact": "Сатып алу және төлем",
                "delivery": "Техникалық мәліметтер",
                "finance": "Өтеу есебі",
                "documents": "Жабдық құжаттары",
            },
        },
        "checklist": [
            "Өтінім",
            (
                "Сатып алынған цифрлық жабдық, қызмет түрі және оны сатып алу қажеттігі туралы "
                "өтініш берушінің есебі"
            ),
            (
                "Сатып алынған цифрлық жабдықтың жалпы сомасына берілген шот-фактуралардың "
                "көшірмелері"
            ),
            (
                "Жабдық құнына төлем құжаттарының көшірмелері немесе аккредитивпен төлеу, "
                "талаптарды есепке жатқызу не айыппұл ұстау туралы құжаттар"
            ),
            "Қазақстандық тауар өндірушілер тізілімінен үзінді",
            "Салықтан босатуды растайтын құжаттардың көшірмелері (қолданылса)",
            "Цифрлық жабдықты сатып алу шартының көшірмесі",
            (
                "Қабылдау-беруді растайтын бастапқы есеп құжаттарының көшірмелері: қабылдау-беру "
                "актісі, қорларды сыртқа босату жүкқұжаты және басқа құжаттар"
            ),
            (
                "Техникалық құжаттаманың көшірмесі: нұсқаулық, жасалған күні, жабдық "
                "өндірушісінің сәйкестендіру нөмірі, негізгі параметрлер; жиынтық ерекшелігі "
                "және техникалық паспорт (бар болса)"
            ),
            "Сатып алынған цифрлық жабдықтың фотосуреттері",
        ],
    },
    "en": {
        "program_title": "Reimbursement of costs for adoption of digital technologies",
        "organizer": "QazIndustry",
        "intake": "During the calendar year until that year's allocated budget is exhausted",
        "amount": "40% of eligible documented costs, capped at KZT 60 million per calendar year",
        "eligibility": (
            "The applicant must produce a priority-list good, have been registered "
            "for at least one calendar year, and not belong to the categories excluded "
            "under paragraph 3 of the Rules. On the application date there must be no "
            "arrears in taxes, mandatory pension or professional pension contributions, "
            "or social contributions, except legally deferred payments. Tax payments "
            "must have increased annually over the prior three years; this rule does "
            "not apply to tax-exempt applicants or entities registered for under seven "
            "years. From 2026, applicants must also be listed in the Register of "
            "Kazakhstani Commodity Producers."
        ),
        "official_source": "https://qazindustry.gov.kz/ru/business_reimbursement",
        "rules_source": "https://qazindustry.gov.kz/docs/v2200028320.22-12-2025.rus%20%281%29.pdf",
        "rules_source_label": "Rules No. 308 with amendments No. 442 (RU, PDF)",
        "documents_source": "https://qazindustry.gov.kz/docs/instrukcia070726.pdf",
        "documents_source_label": "QazIndustry instructions (RU, PDF)",
        "application_portal": "https://sez.qazindustry.gov.kz/ru/service/5/evaluate",
        "application_portal_label": "QazIndustry application portal (RU)",
        "copy": {
            "page_title": "Prepare a reimbursement application",
            "eyebrow": "Working draft",
            "title": "Prepare a draft for digital equipment cost reimbursement",
            "lead": (
                "Enter details about the producer and purchased digital equipment. "
                "QAZ.FUND will assemble a local working draft to check against "
                "QazIndustry's official terms and form."
            ),
            "known": "Programme terms",
            "program": "Programme",
            "organizer": "Service provider",
            "deadline": "Application period",
            "amount": "Reimbursement rate and cap",
            "eligibility": "Applicant criteria",
            "criteria_heading": "Applicant criteria published by QazIndustry",
            "readiness": "Draft completion",
            "required_done": "Draft fields completed: {done} of {total}",
            "applicant_note": "Producer details and a preliminary criteria check.",
            "org_name": "Producer organisation name",
            "legal_form": "Legal form",
            "country": "Organisation registration location",
            "contact": "Application contact",
            "fit": "Applicant criteria self-check",
            "fit_placeholder": (
                "Record how the applicant meets the criteria and note any applicable exceptions."
            ),
            "project": "Digital equipment",
            "project_note": (
                "Identify the purchased equipment and its role in digital technology adoption."
            ),
            "project_name": "Equipment name, model and manufacturer",
            "problem": "Business need addressed by the equipment",
            "solution": "How the equipment is used in the organisation",
            "beneficiaries": "Priority good or product made by the organisation",
            "geography": "Equipment use location",
            "impact": "Purchase and cost evidence",
            "impact_note": (
                "For digital equipment, the 24-month period is counted from the last payment "
                "when the purchase was paid in instalments."
            ),
            "outcomes": "Date of the last payment for the digital equipment",
            "indicators": "Total invoice amount for the purchased equipment",
            "evidence": "Payment records and proof of payment",
            "delivery": "Technical details",
            "delivery_note": "Record identifiers and specifications from the equipment documents.",
            "team": "Equipment manufacturer's identification number and manufacture date",
            "timeline": "Main technical specifications",
            "partners": (
                "Manual, technical passport and equipment composition specification, if available"
            ),
            "risks": "Other equipment details and supporting documents",
            "finance": "Reimbursement calculation",
            "finance_note": (
                "The programme terms state a 40% rate and an annual KZT 60 million cap."
            ),
            "request_amount": "Requested reimbursement, KZT",
            "cofinance": "Total documented eligible costs, KZT",
            "budget": "Calculation and payment reference",
            "documents": "Digital equipment documents",
            "documents_note": (
                "This list applies to digital equipment purchases. See the QazIndustry Rules and "
                "instructions for the application form and other eligible cost types."
            ),
            "criteria_note": (
                "Source discrepancy: the QazIndustry terms page says “under 3 years,” while "
                "Rules No. 308, amended by No. 442, and the instructions say “under 7 years.” "
                "The instructions also require Register listing from 2026, which the terms page "
                "does not mention. This page follows the Rules and instructions."
            ),
            "draft_note": "The text updates as you type and is stored only in this browser.",
            "empty_value": "",
            "source": "Open QazIndustry terms (RU)",
            "source_label": "Programme terms",
            "rules_source_link": "Open Rules No. 308 as amended by No. 442 (RU, PDF)",
            "documents_source_link": "Open QazIndustry instructions (RU, PDF)",
            "application_portal_link": "Open QazIndustry application portal (RU)",
            "sections": {
                "programme": "Programme",
                "applicant": "Applicant",
                "project": "Equipment",
                "impact": "Purchase and payment",
                "delivery": "Technical details",
                "finance": "Reimbursement calculation",
                "documents": "Equipment documents",
            },
        },
        "checklist": [
            "Application",
            (
                "Applicant report on acquired digital equipment, activities and the need for "
                "its purchase"
            ),
            "Copies of invoices for the total amount of the acquired digital equipment",
            (
                "Copies of payment records for the equipment cost, or documents for payment by "
                "letter of credit, offset or penalty withholding"
            ),
            "Extract from the Register of Kazakhstani Commodity Producers",
            "Copies of tax-exemption documents, if applicable",
            "Copy of the digital equipment purchase agreement",
            (
                "Copies of primary accounting records confirming acceptance and transfer: "
                "acceptance certificate, invoice for supplies released to a third party, etc."
            ),
            (
                "Copy of the technical documentation: equipment manual, manufacture date, "
                "manufacturer's identification number, key technical parameters and equipment "
                "composition specification (technical passport, if available)"
            ),
            "Photographs of the acquired digital equipment",
        ],
    },
}


def _type_value(value: object) -> str:
    raw = value.value if isinstance(value, Enum) else value
    return str(raw or "grant").strip().lower()


def _public_label(value: object, lang: str) -> str:
    raw_value = value.value if isinstance(value, Enum) else value
    raw = str(raw_value or "").strip()
    if not raw:
        return ""
    label_map_raw = dashboard_copy(lang).get("label_map")
    label_map = label_map_raw if isinstance(label_map_raw, dict) else {}
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    mapped = label_map.get(normalized) or label_map.get(raw.lower())
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw.replace("_", " ")


def _deadline(value: date | None, lang: str) -> str:
    if value is None:
        return {
            "ru": "Без фиксированного срока",
            "kk": "Белгіленген мерзім жоқ",
            "en": "No fixed deadline",
        }.get(lang, "No fixed deadline")
    return value.strftime("%d.%m.%Y") if lang in {"ru", "kk"} else value.isoformat()


def _amount(detail: OpportunityDetail, lang: str) -> str:
    raw = detail.raw if isinstance(detail.raw, dict) else {}
    values = [detail.amount_min, detail.amount_max]
    if any(value is not None for value in values):
        formatted = [
            f"{value:,.0f}".replace(",", " ") for value in values if value is not None
        ]
        return "–".join(formatted) + f" {detail.currency}"
    amount_raw = str(raw.get("amount_raw") or "").strip()
    if amount_raw:
        return amount_raw
    return {
        "ru": "Сумма не опубликована",
        "kk": "Сома жарияланбаған",
        "en": "Amount not published",
    }.get(lang, "Amount not published")


def _checklist(detail: OpportunityDetail, lang: str) -> list[str]:
    if str(detail.id) == _DIGITAL_EQUIPMENT_REIMBURSEMENT_ID:
        reimbursement = _DIGITAL_EQUIPMENT_REIMBURSEMENT.get(lang)
        if reimbursement:
            return list(reimbursement["checklist"])
    type_value = _type_value(detail.type)
    tags = {str(value).lower() for value in detail.tags}
    if type_value == "tender" or {"procurement", "tender"}.intersection(tags):
        key = "tender"
    elif {"science", "research", "university"}.intersection(tags):
        key = "science"
    elif {"subsidy", "reimbursement", "tax_benefit"}.intersection(tags):
        key = "subsidy"
    elif type_value in {"accelerator", "cloud_credit"} or "startup" in tags:
        key = "startup"
    elif {"ngo", "civil_society", "nonprofit"}.intersection(tags):
        key = "ngo"
    else:
        key = "grant"
    ru = {
        "grant": [
            "Описание проекта и ожидаемого результата",
            "Смета с обоснованием расходов",
            "План работ и календарь",
            "Документы заявителя",
            "Письма партнёров, если они нужны",
        ],
        "tender": [
            "Техническое предложение по требованиям закупки",
            "Ценовое предложение и расчёт",
            "Регистрационные и налоговые документы",
            "Подтверждение опыта и квалификации",
            "Требуемые гарантии и подписанные формы",
        ],
        "science": [
            "Научная задача и состояние исследований",
            "Методика, рабочий план и измеримые результаты",
            "Состав исследовательской группы",
            "Смета и обоснование оборудования",
            "Письма организаций и сведения об этике",
        ],
        "subsidy": [
            "Регистрационные и налоговые документы",
            "Подтверждение затрат или план финансирования",
            "Банковские реквизиты и финансовая отчётность",
            "Разрешения, сертификаты и договоры",
            "Электронная подпись для официальной подачи",
        ],
        "startup": [
            "Краткая презентация проекта",
            "Описание продукта, рынка и пользователей",
            "Данные о команде и стадии проекта",
            "Показатели роста или результаты испытаний",
            "План использования поддержки",
        ],
        "ngo": [
            "Описание общественной проблемы и целевой группы",
            "Логика результата и показатели",
            "План мероприятий и смета",
            "Документы НКО и подтверждение опыта",
            "Письма партнёров и план устойчивости",
        ],
    }
    en = {
        "grant": [
            "Project description and expected outcome",
            "Budget with cost rationale",
            "Work plan and timetable",
            "Applicant documents",
            "Partner letters when required",
        ],
        "tender": [
            "Technical proposal mapped to the procurement requirements",
            "Financial offer and calculations",
            "Registration and tax documents",
            "Evidence of experience and qualifications",
            "Required guarantees and signed forms",
        ],
        "science": [
            "Research question and state of the field",
            "Method, work plan and measurable outputs",
            "Research team",
            "Budget and equipment rationale",
            "Institutional letters and ethics information",
        ],
        "subsidy": [
            "Registration and tax documents",
            "Cost evidence or financing plan",
            "Bank details and financial statements",
            "Permits, certificates and agreements",
            "Digital signature for the official submission",
        ],
        "startup": [
            "Concise project deck",
            "Product, market and user description",
            "Team and project-stage information",
            "Growth metrics or pilot results",
            "Support-use plan",
        ],
        "ngo": [
            "Public problem and target group",
            "Outcome logic and indicators",
            "Activity plan and budget",
            "NGO documents and track record",
            "Partner letters and sustainability plan",
        ],
    }
    kk = {
        "grant": [
            "Жобаның сипаттамасы және күтілетін нәтиже",
            "Шығындар негіздемесі бар бюджет",
            "Жұмыс жоспары және күнтізбе",
            "Өтініш берушінің құжаттары",
            "Қажет болса, серіктестердің хаттары",
        ],
        "tender": [
            "Сатып алу талаптарына сай техникалық ұсыныс",
            "Баға ұсынысы және есеп",
            "Тіркеу және салық құжаттары",
            "Тәжірибе мен біліктілікті растау",
            "Қажетті кепілдіктер және қол қойылған формалар",
        ],
        "science": [
            "Ғылыми міндет және зерттеулердің қазіргі күйі",
            "Әдістеме, жұмыс жоспары және өлшенетін нәтижелер",
            "Зерттеу тобының құрамы",
            "Бюджет және жабдық негіздемесі",
            "Ұйымдардың хаттары және этика туралы мәліметтер",
        ],
        "subsidy": [
            "Тіркеу және салық құжаттары",
            "Шығындарды растау немесе қаржыландыру жоспары",
            "Банктік деректемелер және қаржылық есептілік",
            "Рұқсаттар, сертификаттар және шарттар",
            "Ресми өтінімге арналған электрондық қолтаңба",
        ],
        "startup": [
            "Жобаның қысқаша таныстырылымы",
            "Өнім, нарық және пайдаланушылар сипаттамасы",
            "Команда және жоба кезеңі туралы мәліметтер",
            "Өсу көрсеткіштері немесе сынақ нәтижелері",
            "Қолдауды пайдалану жоспары",
        ],
        "ngo": [
            "Қоғамдық мәселе және нысаналы топ сипаттамасы",
            "Нәтиже логикасы және көрсеткіштер",
            "Іс-шаралар жоспары және бюджет",
            "ҮЕҰ құжаттары және тәжірибені растау",
            "Серіктестердің хаттары және тұрақтылық жоспары",
        ],
    }
    return {"ru": ru, "kk": kk, "en": en}.get(lang, en)[key]


def render_application_prep_page(
    *,
    detail: OpportunityDetail,
    lang: str,
    root_path: str,
    site_origin: str,
    lifecycle: str = "open",
) -> str:
    active_lang = lang if lang in {"kk", "ru", "en"} else "ru"
    copy: dict[str, Any] = {
        "ru": {
            "page_title": "Подготовка заявки",
            "eyebrow": "Рабочая заявка",
            "title": "Черновик заявки по полям программы",
            "lead": (
                "Заполните сведения о проекте. QAZ.FUND соберёт черновик и отметит "
                "разделы, которые ещё не заполнены."
            ),
            "privacy": (
                "Данные остаются в этом браузере. QAZ.FUND не получает и не "
                "отправляет содержимое формы."
            ),
            "back": "Вернуться к карточке",
            "source": "Открыть источник",
            "source_label": "Источник",
            "known": "Известно о программе",
            "program": "Название в источнике",
            "organizer": "Организатор",
            "deadline": "Срок",
            "amount": "Сумма",
            "eligibility": "Требования из источника",
            "unknown": "Нужно проверить у организатора",
            "readiness": "Готовность черновика",
            "required_done": "{done} из {total} обязательных полей",
            "applicant": "Заявитель",
            "applicant_note": "Кто подаёт заявку и почему имеет право участвовать.",
            "org_name": "Название организации или команды",
            "legal_form": "Организационная форма",
            "country": "Страна и город",
            "contact": "Ответственный за заявку",
            "fit": "Основание для участия",
            "fit_placeholder": "Как заявитель соответствует критериям программы",
            "project": "Проект",
            "project_note": "Опишите проблему, способ работы и ожидаемый результат.",
            "project_name": "Название проекта",
            "problem": "Проблема",
            "solution": "Предлагаемое решение",
            "beneficiaries": "Кто получит пользу",
            "geography": "Где будет реализован проект",
            "impact": "Результаты и доказательства",
            "impact_note": "Что изменится и как это будет измерено.",
            "outcomes": "Ожидаемые результаты",
            "indicators": "Показатели и исходные значения",
            "evidence": "Данные, исследования и подтверждения",
            "delivery": "Реализация",
            "delivery_note": "Команда, сроки, партнёры и основные риски.",
            "team": "Команда и роли",
            "timeline": "Этапы и сроки",
            "partners": "Партнёры",
            "risks": "Риски и способы управления",
            "finance": "Финансирование",
            "finance_note": "Запрашиваемая сумма и обоснование расходов.",
            "request_amount": "Запрашиваемая сумма",
            "cofinance": "Собственный вклад и софинансирование",
            "budget": "Основные статьи бюджета",
            "documents": "Пакет документов",
            "documents_note": (
                "Рабочая памятка по типу программы. Точный перечень берите из "
                "официальной документации."
            ),
            "draft": "Черновик",
            "draft_note": (
                "Текст обновляется по мере заполнения. Перед подачей адаптируйте "
                "его к форме и ограничениям организатора."
            ),
            "copy": "Скопировать",
            "copied": "Черновик скопирован",
            "download": "Скачать .md",
            "clear": "Очистить",
            "clear_confirm": "Удалить сохранённый в этом браузере черновик?",
            "empty_value": "[не заполнено]",
            "draft_heading": "Черновик заявки",
            "generated_note": (
                "Рабочий документ QAZ.FUND. Не является поданной заявкой и не "
                "подтверждает соответствие условиям."
            ),
            "terms": "Условия",
            "data_policy": "Политика данных",
            "attribution": "Использование данных",
            "closed_notice": (
                "Приём по этой программе завершён. Черновик можно использовать "
                "только как основу для следующего набора после проверки условий."
            ),
            "forecast_notice": (
                "Приём ещё не открыт. Заполняйте черновик предварительно и "
                "перепроверьте требования после публикации условий."
            ),
            "storage_error": (
                "Браузер не разрешил локальное сохранение. Черновик открыт, но "
                "перед уходом скачайте файл."
            ),
            "sections": {
                "programme": "Программа",
                "applicant": "Заявитель",
                "project": "Проект",
                "impact": "Результаты и доказательства",
                "delivery": "Реализация",
                "finance": "Финансирование",
                "documents": "Проверка пакета",
            },
        },
        "kk": {
            "page_title": "Өтінімді дайындау",
            "eyebrow": "Жұмыс өтінімі",
            "title": "Бағдарлама талаптарына сай өтінім жобасын құрастырыңыз",
            "lead": (
                "Жоба туралы мәліметтерді бір рет енгізіңіз. QAZ.FUND оларды "
                "құрылымдалған жобаға жинап, толтырылмаған бөлімдерді көрсетеді."
            ),
            "privacy": (
                "Деректер осы браузерде қалады. QAZ.FUND форма мазмұнын алмайды "
                "және жібермейді."
            ),
            "back": "Карточкаға оралу",
            "source": "Ресми дереккөзді ашу",
            "source_label": "Дереккөз",
            "known": "Бағдарлама туралы белгілі деректер",
            "program": "Дереккөздегі атауы",
            "organizer": "Ұйымдастырушы",
            "deadline": "Мерзім",
            "amount": "Сома",
            "eligibility": "Дереккөздегі талаптар",
            "unknown": "Ұйымдастырушыдан нақтылау қажет",
            "readiness": "Жоба дайындығы",
            "required_done": "{done}/{total} міндетті өріс",
            "applicant": "Өтініш беруші",
            "applicant_note": (
                "Өтінімді кім береді және қатысуға неге құқылы екенін көрсетіңіз."
            ),
            "org_name": "Ұйымның немесе команданың атауы",
            "legal_form": "Ұйымдық-құқықтық нысан",
            "country": "Ел және қала",
            "contact": "Өтінімге жауапты тұлға",
            "fit": "Қатысу негіздемесі",
            "fit_placeholder": (
                "Өтініш берушінің бағдарлама талаптарына сәйкестігін сипаттаңыз"
            ),
            "project": "Жоба",
            "project_note": "Қысқа әрі нақты: мәселе, шешім және нәтиже.",
            "project_name": "Жоба атауы",
            "problem": "Мәселе",
            "solution": "Ұсынылатын шешім",
            "beneficiaries": "Пайда алушылар",
            "geography": "Жобаны іске асыру орны",
            "impact": "Нәтижелер мен дәлелдер",
            "impact_note": "Не өзгереді және ол қалай өлшенеді.",
            "outcomes": "Күтілетін нәтижелер",
            "indicators": "Көрсеткіштер және бастапқы мәндер",
            "evidence": "Деректер, зерттеулер және растаушы материалдар",
            "delivery": "Іске асыру",
            "delivery_note": (
                "Команда, мерзімдер, серіктестер және негізгі тәуекелдер."
            ),
            "team": "Команда және рөлдер",
            "timeline": "Кезеңдер мен мерзімдер",
            "partners": "Серіктестер",
            "risks": "Тәуекелдер және оларды басқару",
            "finance": "Қаржыландыру",
            "finance_note": "Сұралатын сома және шығындардың негіздемесі.",
            "request_amount": "Сұралатын сома",
            "cofinance": "Өз үлесі және бірлесіп қаржыландыру",
            "budget": "Бюджеттің негізгі баптары",
            "documents": "Құжаттар пакеті",
            "documents_note": (
                "Бағдарлама түріне негізделген жұмыс тізімі. Нақты тізімді "
                "ресми құжаттамадан алыңыз."
            ),
            "draft": "Жоба нұсқасы",
            "draft_note": (
                "Мәтін толтыру барысында жаңартылады. Жіберер алдында оны "
                "ұйымдастырушының формасы мен шектеулеріне бейімдеңіз."
            ),
            "copy": "Көшіру",
            "copied": "Жоба мәтіні көшірілді",
            "download": ".md жүктеп алу",
            "clear": "Тазарту",
            "clear_confirm": ("Осы браузерде сақталған жоба мәтінін жою керек пе?"),
            "empty_value": "[толтырылмаған]",
            "draft_heading": "Өтінім жобасы",
            "generated_note": (
                "QAZ.FUND жұмыс құжаты. Бұл жіберілген өтінім емес және "
                "талаптарға сәйкестікті растамайды."
            ),
            "terms": "Пайдалану шарттары",
            "data_policy": "Деректер саясаты",
            "attribution": "Деректерді пайдалану",
            "closed_notice": (
                "Қабылдау аяқталды. Шарттарды тексергеннен "
                "кейін жоба мәтінін келесі қабылдауға негіз ретінде ғана "
                "пайдаланыңыз."
            ),
            "forecast_notice": (
                "Қабылдау әлі ашылған жоқ. Жоба мәтінін алдын ала толтырып, "
                "шарттар жарияланғаннан кейін талаптарды қайта тексеріңіз."
            ),
            "storage_error": (
                "Браузер жергілікті сақтауға рұқсат бермеді. Жоба мәтіні ашық, "
                "бірақ парақтан шығар алдында файлды жүктеп алыңыз."
            ),
            "sections": {
                "programme": "Бағдарлама",
                "applicant": "Өтініш беруші",
                "project": "Жоба",
                "impact": "Нәтижелер мен дәлелдер",
                "delivery": "Іске асыру",
                "finance": "Қаржыландыру",
                "documents": "Құжаттарды тексеру",
            },
        },
        "en": {
            "page_title": "Application preparation",
            "eyebrow": "Working application",
            "title": "Build a draft around the programme requirements",
            "lead": (
                "Enter project facts once. QAZ.FUND will assemble a structured "
                "draft and show which sections are still incomplete."
            ),
            "privacy": (
                "The data stays in this browser. QAZ.FUND does not receive or "
                "transmit the form content."
            ),
            "back": "Back to opportunity",
            "source": "Open official source",
            "source_label": "Source",
            "known": "Known programme facts",
            "program": "Source title",
            "organizer": "Organizer",
            "deadline": "Deadline",
            "amount": "Amount",
            "eligibility": "Source requirements",
            "unknown": "Confirm with the organizer",
            "readiness": "Draft readiness",
            "required_done": "{done} of {total} required fields",
            "applicant": "Applicant",
            "applicant_note": "Who is applying and why the applicant is eligible.",
            "org_name": "Organization or team name",
            "legal_form": "Legal form",
            "country": "Country and city",
            "contact": "Application lead",
            "fit": "Eligibility rationale",
            "fit_placeholder": "How the applicant meets the programme criteria",
            "project": "Project",
            "project_note": "Keep it specific: problem, response and result.",
            "project_name": "Project name",
            "problem": "Problem",
            "solution": "Proposed solution",
            "beneficiaries": "Who benefits",
            "geography": "Delivery location",
            "impact": "Outcomes and evidence",
            "impact_note": "What will change and how it will be measured.",
            "outcomes": "Expected outcomes",
            "indicators": "Indicators and baselines",
            "evidence": "Data, research and supporting evidence",
            "delivery": "Delivery",
            "delivery_note": "Team, timing, partners and principal risks.",
            "team": "Team and roles",
            "timeline": "Milestones and timing",
            "partners": "Partners",
            "risks": "Risks and mitigation",
            "finance": "Finance",
            "finance_note": "Requested amount and spending rationale.",
            "request_amount": "Requested amount",
            "cofinance": "Own contribution and co-financing",
            "budget": "Main budget lines",
            "documents": "Document pack",
            "documents_note": (
                "A working checklist based on programme type. Use the official "
                "documentation for the exact list."
            ),
            "draft": "Draft",
            "draft_note": (
                "The text updates as you type. Adapt it to the organizer's form "
                "and limits before submission."
            ),
            "copy": "Copy",
            "copied": "Draft copied",
            "download": "Download .md",
            "clear": "Clear",
            "clear_confirm": "Delete the draft stored in this browser?",
            "empty_value": "[not completed]",
            "draft_heading": "Application draft",
            "generated_note": (
                "QAZ.FUND working document. It is not a submitted application and "
                "does not confirm eligibility."
            ),
            "terms": "Terms",
            "data_policy": "Data policy",
            "attribution": "Data reuse",
            "closed_notice": (
                "Applications are closed. Use the draft only "
                "as a starting point for a future round after checking its terms."
            ),
            "forecast_notice": (
                "Applications are not open yet. Treat this as a preliminary draft "
                "and recheck the requirements after launch."
            ),
            "storage_error": (
                "This browser blocked local storage. The draft remains open, but "
                "download it before leaving."
            ),
            "sections": {
                "programme": "Programme",
                "applicant": "Applicant",
                "project": "Project",
                "impact": "Outcomes and evidence",
                "delivery": "Delivery",
                "finance": "Finance",
                "documents": "Document check",
            },
        },
    }[active_lang]
    reimbursement = (
        _DIGITAL_EQUIPMENT_REIMBURSEMENT.get(active_lang)
        if str(detail.id) == _DIGITAL_EQUIPMENT_REIMBURSEMENT_ID
        else None
    )
    if reimbursement:
        copy.update(reimbursement["copy"])
    reminder_copy = {
        "ru": {
            "title": "Напоминания о сроке",
            "note": (
                "Скачайте событие с напоминаниями за 14 и 3 дня. Оно будет "
                "работать в выбранном календаре, а не только в этом браузере."
            ),
            "download": "Добавить в календарь",
            "unavailable": (
                "У программы нет подтверждённого фиксированного срока. "
                "Следите за страницей источника."
            ),
            "event_title": "QAZ.FUND: срок подачи",
        },
        "kk": {
            "title": "Мерзім еске салғыштары",
            "note": (
                "14 және 3 күн бұрынғы еске салғыштары бар оқиғаны жүктеп "
                "алыңыз. Ол тек осы браузерде емес, таңдалған күнтізбеде "
                "жұмыс істейді."
            ),
            "download": "Күнтізбеге қосу",
            "unavailable": "Бағдарламада расталған нақты мерзім жоқ. Дереккөз бетін бақылаңыз.",
            "event_title": "QAZ.FUND: өтінім мерзімі",
        },
        "en": {
            "title": "Deadline reminders",
            "note": (
                "Download a calendar event with 14- and 3-day reminders. "
                "It works in your chosen calendar, not only in this browser."
            ),
            "download": "Add to calendar",
            "unavailable": (
                "No confirmed fixed deadline is published. " "Monitor the source page."
            ),
            "event_title": "QAZ.FUND: application deadline",
        },
    }[active_lang]
    base = root_path.rstrip("/")
    detail_path = f"{base}/opportunity/{detail.id}?lang={active_lang}"
    source_href = (
        reimbursement["official_source"] if reimbursement else str(detail.source_url)
    )
    rules_source = reimbursement["rules_source"] if reimbursement else ""
    documents_source = reimbursement["documents_source"] if reimbursement else ""
    application_portal = reimbursement["application_portal"] if reimbursement else ""
    organizer = (
        reimbursement["organizer"]
        if reimbursement
        else _public_label(detail.funder or detail.source, active_lang)
    )
    eligibility = (
        "; ".join(
            _public_label(value, active_lang)
            for value in detail.eligibility
            if str(value).strip()
        )
        or copy["unknown"]
    )
    deadline = (
        reimbursement["intake"]
        if reimbursement
        else _deadline(detail.deadline, active_lang)
    )
    amount = reimbursement["amount"] if reimbursement else _amount(detail, active_lang)
    program_title = reimbursement["program_title"] if reimbursement else detail.title
    if reimbursement:
        eligibility = reimbursement["eligibility"]
    checklist = _checklist(detail, active_lang)
    truth = program_truth(detail, lifecycle=lifecycle)
    checklist_markup = "".join(f"""
        <label class="check-row" data-avds-component="FormField">
          <input type="checkbox" name="document_{index}" data-avds-component="Checkbox">
          <span>{escape(label)}</span>
        </label>
        """ for index, label in enumerate(checklist, 1))
    facts = {
        "opportunity_id": str(detail.id),
        "programme_specific": bool(reimbursement),
        "program": program_title,
        "organizer": organizer,
        "deadline": deadline,
        "deadline_iso": detail.deadline.isoformat() if detail.deadline else "",
        "amount": amount,
        "eligibility": eligibility,
        "official_source": source_href,
        "rules_source": rules_source,
        "rules_source_label": (
            reimbursement["rules_source_label"] if reimbursement else ""
        ),
        "documents_source": documents_source,
        "documents_source_label": (
            reimbursement["documents_source_label"] if reimbursement else ""
        ),
        "application_url": application_portal or str(detail.application_url or ""),
        "application_portal_label": (
            reimbursement["application_portal_label"] if reimbursement else ""
        ),
        "checklist": checklist,
        "actionability": truth["actionability"],
    }
    facts_json = json.dumps(facts, ensure_ascii=False).replace("<", "\\u003c")
    copy_json = json.dumps(copy, ensure_ascii=False).replace("<", "\\u003c")
    reminder_copy_json = json.dumps(reminder_copy, ensure_ascii=False).replace(
        "<", "\\u003c"
    )
    storage_key = (
        f"qazfund-application-draft-reimbursement-v1:{detail.id}:{active_lang}"
        if reimbursement
        else f"qazfund-application-draft-v1:{detail.id}:{active_lang}"
    )
    canonical = (
        f"{site_origin.rstrip('/')}{base}/opportunity/{detail.id}/prepare"
        f"?lang={active_lang}"
    )
    terms_href = (
        f"{base}/terms?lang={active_lang}" if base else f"/terms?lang={active_lang}"
    )
    data_policy_href = (
        f"{base}/data-policy?lang={active_lang}"
        if base
        else f"/data-policy?lang={active_lang}"
    )
    data_routes_href = (
        f"{base}/data-routes?lang={active_lang}"
        if base
        else f"/data-routes?lang={active_lang}"
    )
    data_routes_label = {
        "ru": "Официальные данные РК",
        "kk": "Қазақстанның ресми деректері",
        "en": "Official Kazakhstan data",
    }[active_lang]
    attribution_href = (
        f"{base}/attribution?lang={active_lang}"
        if base
        else f"/attribution?lang={active_lang}"
    )
    state_notice = ""
    if lifecycle in {"closed", "awarded"}:
        state_notice = copy["closed_notice"]
    elif lifecycle == "forecast":
        state_notice = copy["forecast_notice"]
    state_notice_markup = (
        '<div class="state-notice" data-avds-component="Alert">'
        f"{escape(state_notice)}</div>"
        if state_notice
        else ""
    )
    reminder_button_attr = "" if detail.deadline else "disabled"
    reminder_note = escape(
        reminder_copy["note"] if detail.deadline else reminder_copy["unavailable"]
    )
    reminder_markup = (
        ""
        if reimbursement
        else f"""
        <section class="panel reminder-panel" data-avds-component="Card">
          <div class="panel-head">
            <div>
              <h2>{escape(reminder_copy["title"])}</h2>
              <p>{reminder_note}</p>
            </div>
          </div>
          <button
            class="button secondary"
            id="download-deadline-reminder"
            type="button"
            {reminder_button_attr}
          >{escape(reminder_copy["download"])}</button>
        </section>
    """
    )
    source_links_markup = (
        f'<a href="{escape(source_href, quote=True)}" target="_blank" rel="noopener">'
        f'{escape(copy["source"])}</a>'
        if not reimbursement
        else (
            f'<a href="{escape(source_href, quote=True)}" target="_blank" rel="noopener">'
            f'{escape(copy["source"])}</a> · '
            f'<a href="{escape(rules_source, quote=True)}" target="_blank" rel="noopener">'
            f'{escape(copy["rules_source_link"])}</a> · '
            f'<a href="{escape(documents_source, quote=True)}" target="_blank" rel="noopener">'
            f'{escape(copy["documents_source_link"])}</a> · '
            f'<a href="{escape(application_portal, quote=True)}" target="_blank" rel="noopener">'
            f'{escape(copy["application_portal_link"])}</a>'
        )
    )

    def field(
        name: str,
        label: str,
        *,
        textarea: bool = False,
        required: bool = False,
        placeholder: str = "",
    ) -> str:
        required_attr = " required" if required else ""
        required_mark = '<span aria-hidden="true">*</span>' if required else ""
        placeholder_attr = (
            f' placeholder="{escape(placeholder, quote=True)}"' if placeholder else ""
        )
        control = (
            f'<textarea id="{name}" name="{name}" rows="4" '
            f'data-avds-component="Textarea"{required_attr}'
            f"{placeholder_attr}></textarea>"
            if textarea
            else f'<input id="{name}" name="{name}" type="text" '
            f'data-avds-component="TextInput"{required_attr}'
            f"{placeholder_attr}>"
        )
        return (
            f'<label class="field" for="{name}" data-avds-component="FormField">'
            f"<span>{escape(label)}{required_mark}</span>{control}</label>"
        )

    fit_field = field(
        "fit",
        copy["fit"],
        textarea=True,
        required=True,
        placeholder=copy["fit_placeholder"],
    )

    def step(
        number: int,
        title: str,
        note: str,
        body: str,
        *,
        opened: bool = False,
    ) -> str:
        open_attr = " open" if opened else ""
        return f"""
        <details
          class="panel step-panel"
          data-step="{number}"
          data-avds-component="Card"
          {open_attr}
        >
          <summary class="step-summary">
            <span class="step-number">{number}</span>
            <span class="step-copy">
              <h2>{escape(title)}</h2>
              <p>{escape(note)}</p>
            </span>
            <span class="step-progress" aria-live="polite">0/0</span>
          </summary>
          <div class="step-body">{body}</div>
        </details>
        """

    eligibility_markup = (
        '<aside class="state-notice light" data-avds-component="Alert" role="note">'
        f'<strong>{escape(copy["criteria_heading"])}</strong>'
        f"<p>{escape(eligibility)}</p>"
        f"<p>{escape(copy['criteria_note'])}</p></aside>"
        if reimbursement
        else ""
    )
    applicant_step = step(
        1,
        copy["applicant"],
        copy["applicant_note"],
        f"""
          {eligibility_markup}
          <div class="field-grid">
            {field("org_name", copy["org_name"], required=True)}
            {field("legal_form", copy["legal_form"])}
            {field("country", copy["country"], required=True)}
            {field("contact", copy["contact"])}
          </div>
          <div class="field-grid single" style="margin-top:12px">{fit_field}</div>
        """,
        opened=True,
    )
    project_step = step(
        2,
        copy["project"],
        copy["project_note"],
        f"""
          <div class="field-grid">
            {field("project_name", copy["project_name"], required=True)}
            {field("geography", copy["geography"])}
            {field("problem", copy["problem"], textarea=True, required=True)}
            {field("solution", copy["solution"], textarea=True, required=True)}
            {field("beneficiaries", copy["beneficiaries"], textarea=True)}
          </div>
        """,
    )
    impact_step = step(
        3,
        copy["impact"],
        copy["impact_note"],
        f"""
          <div class="field-grid">
            {field("outcomes", copy["outcomes"], textarea=True, required=True)}
            {field("indicators", copy["indicators"], textarea=True, required=True)}
            {field("evidence", copy["evidence"], textarea=True)}
          </div>
        """,
    )
    delivery_step = step(
        4,
        copy["delivery"],
        copy["delivery_note"],
        f"""
          <div class="field-grid">
            {field("team", copy["team"], textarea=True, required=True)}
            {field("timeline", copy["timeline"], textarea=True, required=True)}
            {field("partners", copy["partners"], textarea=True)}
            {field("risks", copy["risks"], textarea=True)}
          </div>
        """,
    )
    finance_step = step(
        5,
        copy["finance"],
        copy["finance_note"],
        f"""
          <div class="field-grid">
            {field("request_amount", copy["request_amount"], required=True)}
            {field("cofinance", copy["cofinance"])}
            {field("budget", copy["budget"], textarea=True, required=True)}
          </div>
        """,
    )
    documents_step = step(
        6,
        copy["documents"],
        copy["documents_note"],
        f'<div class="check-list">{checklist_markup}</div>',
    )

    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(copy["page_title"])} – {escape(program_title)} – QAZ.FUND</title>
  <meta name="description" content="{escape(copy["lead"], quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme: light;
      --ink: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --soft: var(--color-bg-subtle);
      --panel: var(--color-surface);
      --navy: #091a30;
      --blue: var(--color-accent);
      --green: var(--color-success);
      --amber: var(--color-warning);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--color-bg);
      color: var(--ink);
      font-family: var(--av-font-sans);
      line-height: 1.45;
    }}
    button, input, textarea {{ font: inherit; }}
    .shell {{
      width: min(1320px, calc(100% - 28px));
      margin: 14px auto 40px;
    }}
    .topbar {{
      min-height: 48px;
      padding: 0 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
    }}
    .topbar a {{
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      color: inherit;
      font-size: 12px;
      font-weight: 750;
      text-decoration: none;
    }}
    .topbar > a:first-child {{ font-size: 14px; font-weight: 850; }}
    .hero {{
      margin-top: 10px;
      padding: 32px;
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(300px, .75fr);
      gap: 34px;
      border-radius: var(--av-radius-lg);
      background: var(--navy);
      color: white;
    }}
    .eyebrow {{
      color: #83b3ff;
      font-size: 10px;
      font-weight: 850;
      letter-spacing: .12em;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 760px;
      margin: 8px 0 12px;
      font-size: clamp(31px, 4.5vw, 55px);
      line-height: 1;
      letter-spacing: -.05em;
    }}
    .hero-lead {{
      max-width: 720px;
      margin: 0;
      color: #c8d6e7;
      font-size: 15px;
    }}
    .privacy {{
      margin-top: 20px;
      padding: 11px 13px;
      display: inline-flex;
      gap: 9px;
      align-items: center;
      border: 1px solid rgb(255 255 255 / .14);
      border-radius: 9px;
      color: #b9cadd;
      font-size: 11px;
    }}
    .privacy::before {{
      content: "";
      width: 8px;
      height: 8px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: #56d49d;
    }}
    .state-notice {{
      margin-top: 12px;
      padding: 11px 13px;
      border: 1px solid rgb(255 255 255 / .18);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / .08);
      color: #dbe7f5;
      font-size: 12px;
      line-height: 1.5;
    }}
    .state-notice.light {{
      margin: 0 0 18px;
      border-color: #c9d8e8;
      background: #f2f7fc;
      color: #193451;
      font-size: 13px;
    }}
    .state-notice.light p {{ margin: 5px 0 0; color: #405a74; }}
    .facts {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1px;
      align-self: stretch;
      border: 1px solid rgb(255 255 255 / .14);
      border-radius: var(--av-radius-lg);
      background: rgb(255 255 255 / .14);
      overflow: hidden;
    }}
    .fact {{
      min-height: 90px;
      padding: 15px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: #112c4e;
    }}
    .fact span {{
      color: #9fb3cb;
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .fact strong {{ font-size: 12px; line-height: 1.35; }}
    .workspace {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(360px, .7fr);
      gap: 10px;
      align-items: start;
    }}
    .form-stack {{ display: grid; gap: 10px; }}
    .panel {{
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
    }}
    .panel-head {{
      margin-bottom: 17px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }}
    .panel-head h2 {{ margin: 0 0 4px; font-size: 20px; letter-spacing: -.025em; }}
    .panel-head p {{ max-width: 650px; margin: 0; color: var(--muted); font-size: 11px; }}
    .step-panel {{ padding: 0; overflow: clip; }}
    .step-summary {{
      min-height: 76px;
      padding: 16px 20px;
      display: grid;
      grid-template-columns: 36px minmax(0, 1fr) auto auto;
      gap: 13px;
      align-items: center;
      cursor: pointer;
      list-style: none;
    }}
    .step-summary::-webkit-details-marker {{ display: none; }}
    .step-summary::after {{
      content: "+";
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border: 1px solid var(--line);
      border-radius: 50%;
      color: var(--blue);
      font-size: 18px;
      font-weight: 750;
    }}
    .step-panel[open] > .step-summary::after {{ content: "−"; }}
    .step-panel[open] > .step-summary {{ border-bottom: 1px solid var(--line); }}
    .step-number {{
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border-radius: 10px;
      background: var(--color-bg-subtle);
      color: var(--blue);
      font: 800 11px/1 var(--av-font-mono);
    }}
    .step-panel[data-complete="true"] .step-number {{
      background: color-mix(in srgb, var(--green) 16%, white);
      color: var(--green);
    }}
    .step-copy h2 {{ margin: 0 0 4px; font-size: 19px; letter-spacing: -.025em; }}
    .step-copy p {{ margin: 0; color: var(--muted); font-size: 11px; }}
    .step-body {{ padding: 20px; }}
    .step-progress {{ color: var(--muted); font: 750 10px/1 var(--av-font-mono); }}
    .field-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .field-grid.single {{ grid-template-columns: 1fr; }}
    .field {{
      display: grid;
      gap: 6px;
      color: #3d4b60;
      font-size: 11px;
      font-weight: 750;
    }}
    .field > span span {{ color: #bd3a3a; }}
    .field input, .field textarea {{
      width: 100%;
      min-height: var(--av-control-height-lg);
      padding: 10px 11px;
      border: 1px solid #cfd9e5;
      border-radius: var(--av-radius-md);
      background: var(--color-bg-subtle);
      color: var(--ink);
      resize: vertical;
      outline: none;
    }}
    .field textarea {{ min-height: 105px; }}
    .field input:focus, .field textarea:focus {{
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgb(41 89 202 / .12);
    }}
    .field input:user-invalid, .field textarea:user-invalid {{
      border-color: #cf4f4f;
    }}
    .check-list {{ display: grid; gap: 7px; }}
    .check-row {{
      min-height: var(--av-control-height-lg);
      padding: 9px 11px;
      display: flex;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--color-bg-subtle);
      color: #344258;
      font-size: 11px;
      cursor: pointer;
    }}
    .check-row input {{ width: 17px; height: 17px; accent-color: var(--green); }}
    .side {{
      position: sticky;
      top: 10px;
      display: grid;
      gap: 10px;
    }}
    .readiness {{
      padding: 18px;
      border-radius: var(--av-radius-lg);
      background: var(--navy);
      color: white;
    }}
    .readiness-top {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 14px;
    }}
    .readiness-top span {{ color: #aec0d5; font-size: 11px; }}
    .readiness-top strong {{ font-size: 28px; }}
    .progress {{
      height: 7px;
      margin: 13px 0 8px;
      border-radius: 99px;
      background: rgb(255 255 255 / .12);
      overflow: hidden;
    }}
    .progress span {{
      height: 100%;
      display: block;
      width: 0;
      background: #58d59e;
      transition: width 160ms ease;
    }}
    .readiness small {{ color: #aec0d5; font-size: 10px; }}
    .button {{
      min-height: var(--av-control-height-lg);
      padding: 10px 14px;
      border: 1px solid var(--blue);
      border-radius: var(--av-radius-md);
      background: var(--blue);
      color: white;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
    }}
    .button:hover {{ background: color-mix(in oklab, var(--blue), black 14%); }}
    .button:disabled {{ opacity: .55; cursor: not-allowed; }}
    .draft-panel {{ padding: 0; overflow: hidden; }}
    .draft-head {{
      padding: 17px 18px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--line);
    }}
    .draft-head h2 {{ margin: 0 0 3px; font-size: 17px; }}
    .draft-head p {{ margin: 0; color: var(--muted); font-size: 10px; }}
    .draft-actions {{ display: flex; flex-wrap: wrap; gap: 5px; justify-content: flex-end; }}
    .action {{
      min-height: 44px;
      padding: 7px 9px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      color: var(--ink);
      font-size: 10px;
      font-weight: 800;
      cursor: pointer;
    }}
    .action.primary {{ border-color: var(--blue); background: var(--blue); color: white; }}
    .action.danger {{ color: #a23838; }}
    #draft-output {{
      width: 100%;
      min-height: 560px;
      max-height: 68vh;
      margin: 0;
      padding: 18px;
      border: 0;
      background: var(--color-bg-subtle);
      color: #26344a;
      font: 11px/1.55 var(--av-font-mono);
      resize: vertical;
      outline: none;
    }}
    .draft-status {{
      min-height: 28px;
      padding: 7px 18px;
      border-top: 1px solid var(--line);
      color: var(--green);
      font-size: 10px;
    }}
    .footer {{
      padding: 18px 4px 0;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 10px 24px;
      color: var(--muted);
      font-size: 10px;
    }}
    .footer p {{ max-width: 760px; margin: 0; }}
    .footer nav {{ display: flex; gap: 12px; }}
    .footer a {{ color: var(--ink); font-weight: 750; }}
    @media (max-width: 980px) {{
      .hero, .workspace {{ grid-template-columns: 1fr; }}
      .side {{ position: static; }}
      #draft-output {{ max-height: none; }}
      .footer nav a,
      .footer p a {{ display:inline-flex; align-items:center; min-height:44px; }}
      .footer nav a {{ min-width:44px; justify-content:center; }}
    }}
    @media (max-width: 620px) {{
      .shell {{ width: calc(100% - 14px); margin-top: 7px; }}
      .topbar {{ min-height: 44px; padding: 0 10px; }}
      .hero {{ padding: 24px 18px; border-radius: 13px; }}
      h1 {{ font-size: 38px; }}
      .facts, .field-grid {{ grid-template-columns: 1fr; }}
      .fact {{ min-height: 72px; }}
      .panel {{ padding: 18px 14px; }}
      .step-panel {{ padding: 0; }}
      .step-summary {{
        min-height: 72px;
        padding: 14px;
        grid-template-columns: 34px minmax(0, 1fr) auto;
      }}
      .step-progress {{ display: none; }}
      .step-body {{ padding: 16px 14px; }}
      .panel-head, .draft-head {{ flex-direction: column; }}
      .draft-actions {{ width: 100%; justify-content: flex-start; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .progress span {{ transition: none; }}
    }}
  </style>
</head>
<body>
  <main
    class="shell"
    data-avds-component="application-workspace"
    data-avds-version="{AVDS_VERSION}"
  >
    <header class="topbar" data-avds-component="Breadcrumbs">
      <a href="{escape(detail_path, quote=True)}">QAZ.FUND</a>
      <a href="{escape(detail_path, quote=True)}">← {escape(copy["back"])}</a>
    </header>
    <section class="hero" data-avds-pattern="editorial-lead-rail">
      <div>
        <div class="eyebrow">{escape(copy["eyebrow"])}</div>
        <h1>{escape(copy["title"])}</h1>
        <p class="hero-lead">{escape(copy["lead"])}</p>
        <div class="privacy" data-avds-component="Alert">{escape(copy["privacy"])}</div>
        {state_notice_markup}
      </div>
      <aside
        class="facts"
        aria-label="{escape(copy["known"], quote=True)}"
        data-avds-component="PublicSummaryStrip"
      >
        <div class="fact">
          <span>{escape(copy["program"])}</span>
          <strong>{escape(program_title)}</strong>
        </div>
        <div class="fact">
          <span>{escape(copy["organizer"])}</span>
          <strong>{escape(organizer or copy["unknown"])}</strong>
        </div>
        <div class="fact">
          <span>{escape(copy["deadline"])}</span>
          <strong>{escape(deadline)}</strong>
        </div>
        <div class="fact">
          <span>{escape(copy["amount"])}</span>
          <strong>{escape(amount)}</strong>
        </div>
      </aside>
    </section>

    <form
      class="workspace"
      id="application-form"
      novalidate
      data-avds-pattern="application-workspace"
    >
      <div class="form-stack">
        {applicant_step}
        {project_step}
        {impact_step}
        {delivery_step}
        {finance_step}
        {documents_step}
      </div>

      <aside class="side">
        <section class="readiness" data-avds-component="Progress">
          <div class="readiness-top">
            <span>{escape(copy["readiness"])}</span>
            <strong id="readiness-percent">0%</strong>
          </div>
          <div
            class="progress"
            role="progressbar"
            aria-label="{escape(copy["readiness"], quote=True)}"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow="0"
          ><span id="readiness-bar"></span></div>
          <small id="readiness-label"></small>
        </section>
        {reminder_markup}
        <section
          class="panel draft-panel"
          data-avds-component="Card"
          data-avds-pattern="document-card"
        >
          <div class="draft-head">
            <div>
              <h2>{escape(copy["draft"])}</h2>
              <p>{escape(copy["draft_note"])}</p>
            </div>
            <div class="draft-actions">
              <button
                class="action primary"
                id="copy-draft"
                type="button"
                data-avds-component="Button"
              >{escape(copy["copy"])}</button>
              <button
                class="action"
                id="download-draft"
                type="button"
                data-avds-component="Button"
              >{escape(copy["download"])}</button>
              <button
                class="action danger"
                id="clear-draft"
                type="button"
                data-avds-component="Button"
              >{escape(copy["clear"])}</button>
            </div>
          </div>
          <textarea
            id="draft-output"
            readonly
            aria-label="{escape(copy["draft"], quote=True)}"
            data-avds-component="Textarea"
          ></textarea>
          <div class="draft-status" id="draft-status" aria-live="polite"></div>
        </section>
      </aside>
    </form>
    <footer class="footer">
      <a class="footer-contact" href="mailto:contact@qaz.fund">contact@qaz.fund</a>
      <p>
        {escape(copy["generated_note"])}
        {source_links_markup}.
      </p>
      <nav>
        <a href="{escape(terms_href, quote=True)}">{escape(copy["terms"])}</a>
        <a href="{escape(data_policy_href, quote=True)}">{escape(copy["data_policy"])}</a>
        <a href="{escape(data_routes_href, quote=True)}">{escape(data_routes_label)}</a>
        <a href="{escape(attribution_href, quote=True)}">{escape(copy["attribution"])}</a>
      </nav>
    </footer>
  </main>
  <script>
    (() => {{
      const form = document.getElementById("application-form");
      const output = document.getElementById("draft-output");
      const status = document.getElementById("draft-status");
      const readinessBar = document.getElementById("readiness-bar");
      const readinessPercent = document.getElementById("readiness-percent");
      const readinessLabel = document.getElementById("readiness-label");
      const progress = document.querySelector(".progress");
      const facts = {facts_json};
      const copy = {copy_json};
      const reminderCopy = {reminder_copy_json};
      const storageKey = {json.dumps(storage_key)};
      const inputs = [...form.querySelectorAll("input, textarea")];
      const required = [...form.querySelectorAll("[required]")];
      const steps = [...form.querySelectorAll(".step-panel")];
      const isDone = (control) => control.type === "checkbox"
        ? control.checked
        : Boolean(String(control.value || "").trim());
      const updateSteps = () => steps.forEach((step) => {{
        const requiredControls = [...step.querySelectorAll("[required]")];
        const controls = requiredControls.length
          ? requiredControls
          : [...step.querySelectorAll('input[type="checkbox"]')];
        const done = controls.filter(isDone).length;
        const total = controls.length;
        step.dataset.complete = String(total > 0 && done === total);
        const label = step.querySelector(".step-progress");
        if (label) label.textContent = `${{done}}/${{total}}`;
      }});
      const value = (name) => {{
        const control = form.elements.namedItem(name);
        return String(control?.value || "").trim() || copy.empty_value;
      }};
      const line = (label, name) => `**${{label}}:** ${{value(name)}}`;
      const buildDraft = () => {{
        const checked = facts.checklist.map((label, index) => {{
          const control = form.elements.namedItem(`document_${{index + 1}}`);
          return `- [${{control?.checked ? "x" : " "}}] ${{label}}`;
        }}).join("\\n");
        if (facts.programme_specific) {{
          const draftValue = (name) => String(
            form.elements.namedItem(name)?.value || ""
          ).trim();
          const draftLine = (label, name) => draftValue(name)
            ? `**${{label}}:** ${{draftValue(name)}}`
            : "";
          const draftSection = (key, rows) => {{
            const completedRows = rows.filter(Boolean);
            return completedRows.length
              ? [`## ${{copy.sections[key]}}`, ...completedRows, ""]
              : [];
          }};
          return [
            `# ${{copy.draft_heading}}: ${{facts.program}}`,
            "",
            `> ${{copy.generated_note}}`,
            "",
            ...draftSection("programme", [
              `**${{copy.program}}:** ${{facts.program}}`,
              `**${{copy.organizer}}:** ${{facts.organizer}}`,
              `**${{copy.deadline}}:** ${{facts.deadline}}`,
              `**${{copy.amount}}:** ${{facts.amount}}`,
              `**${{copy.eligibility}}:** ${{facts.eligibility}}`,
              copy.criteria_note || "",
            ]),
            ...draftSection("applicant", [
              draftLine(copy.org_name, "org_name"),
              draftLine(copy.legal_form, "legal_form"),
              draftLine(copy.country, "country"),
              draftLine(copy.contact, "contact"),
              draftLine(copy.fit, "fit"),
            ]),
            ...draftSection("project", [
              draftLine(copy.project_name, "project_name"),
              draftLine(copy.problem, "problem"),
              draftLine(copy.solution, "solution"),
              draftLine(copy.beneficiaries, "beneficiaries"),
              draftLine(copy.geography, "geography"),
            ]),
            ...draftSection("impact", [
              draftLine(copy.outcomes, "outcomes"),
              draftLine(copy.indicators, "indicators"),
              draftLine(copy.evidence, "evidence"),
            ]),
            ...draftSection("delivery", [
              draftLine(copy.team, "team"),
              draftLine(copy.timeline, "timeline"),
              draftLine(copy.partners, "partners"),
              draftLine(copy.risks, "risks"),
            ]),
            ...draftSection("finance", [
              draftLine(copy.request_amount, "request_amount"),
              draftLine(copy.cofinance, "cofinance"),
              draftLine(copy.budget, "budget"),
            ]),
            `## ${{copy.sections.documents}}`,
            checked,
            "",
            `${{copy.source_label}}: ${{facts.official_source}}`,
            `${{facts.rules_source_label}}: ${{facts.rules_source}}`,
            `${{facts.documents_source_label}}: ${{facts.documents_source}}`,
            `${{facts.application_portal_label}}: ${{facts.application_url}}`,
          ].filter(Boolean).join("\\n");
        }}
        return [
          `# ${{copy.draft_heading}}: ${{value("project_name")}}`,
          "",
          `> ${{copy.generated_note}}`,
          "",
          `## ${{copy.sections.programme}}`,
          `**${{copy.program}}:** ${{facts.program}}`,
          `**${{copy.organizer}}:** ${{facts.organizer || copy.unknown}}`,
          `**${{copy.deadline}}:** ${{facts.deadline}}`,
          `**${{copy.amount}}:** ${{facts.amount}}`,
          `**${{copy.eligibility}}:** ${{facts.eligibility}}`,
          copy.criteria_note || "",
          `**URL:** ${{facts.application_url || facts.official_source}}`,
          "",
          `## ${{copy.sections.applicant}}`,
          line(copy.org_name, "org_name"),
          line(copy.legal_form, "legal_form"),
          line(copy.country, "country"),
          line(copy.contact, "contact"),
          line(copy.fit, "fit"),
          "",
          `## ${{copy.sections.project}}`,
          line(copy.project_name, "project_name"),
          line(copy.problem, "problem"),
          line(copy.solution, "solution"),
          line(copy.beneficiaries, "beneficiaries"),
          line(copy.geography, "geography"),
          "",
          `## ${{copy.sections.impact}}`,
          line(copy.outcomes, "outcomes"),
          line(copy.indicators, "indicators"),
          line(copy.evidence, "evidence"),
          "",
          `## ${{copy.sections.delivery}}`,
          line(copy.team, "team"),
          line(copy.timeline, "timeline"),
          line(copy.partners, "partners"),
          line(copy.risks, "risks"),
          "",
          `## ${{copy.sections.finance}}`,
          line(copy.request_amount, "request_amount"),
          line(copy.cofinance, "cofinance"),
          line(copy.budget, "budget"),
          "",
          `## ${{copy.sections.documents}}`,
          checked,
          "",
          `${{copy.source_label}}: ${{facts.official_source}}`,
          facts.rules_source
            ? `${{facts.rules_source_label}}: ${{facts.rules_source}}`
            : "",
          facts.documents_source
            ? `${{facts.documents_source_label}}: ${{facts.documents_source}}`
            : "",
        ].filter(Boolean).join("\\n");
      }};
      const serialize = () => Object.fromEntries(inputs.map((control) => [
        control.name,
        control.type === "checkbox" ? control.checked : control.value
      ]));
      const restore = () => {{
        try {{
          const data = JSON.parse(localStorage.getItem(storageKey) || "{{}}");
          inputs.forEach((control) => {{
            if (!(control.name in data)) return;
            if (control.type === "checkbox") control.checked = Boolean(data[control.name]);
            else control.value = String(data[control.name] || "");
          }});
        }} catch {{
          try {{ localStorage.removeItem(storageKey); }} catch {{}}
          status.textContent = copy.storage_error;
        }}
      }};
      const update = (persist = true) => {{
        const done = required.filter((control) => String(control.value || "").trim()).length;
        const percent = required.length ? Math.round(done / required.length * 100) : 100;
        readinessBar.style.width = `${{percent}}%`;
        readinessPercent.textContent = `${{percent}}%`;
        readinessLabel.textContent = copy.required_done
          .replace("{{done}}", String(done))
          .replace("{{total}}", String(required.length));
        progress.setAttribute("aria-valuenow", String(percent));
        output.value = buildDraft();
        updateSteps();
        if (persist) {{
          try {{
            localStorage.setItem(storageKey, JSON.stringify(serialize()));
          }} catch {{
            status.textContent = copy.storage_error;
          }}
        }}
      }};
      let timer;
      inputs.forEach((control) => control.addEventListener("input", () => {{
        clearTimeout(timer);
        timer = setTimeout(update, 80);
      }}));
      inputs.forEach((control) => control.addEventListener("change", update));
      inputs.forEach((control) => control.addEventListener("focus", () => {{
        const step = control.closest(".step-panel");
        if (step) step.open = true;
      }}));
      document.getElementById("copy-draft").addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(output.value);
          status.textContent = copy.copied;
        }} catch {{
          output.select();
          document.execCommand("copy");
          status.textContent = copy.copied;
        }}
      }});
      document.getElementById("download-draft").addEventListener("click", () => {{
        const blob = new Blob([output.value], {{ type: "text/markdown;charset=utf-8" }});
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `qazfund-${{String(facts.program || "application")
          .toLowerCase().replace(/[^a-zа-яёәғқңөұүһі0-9]+/gi, "-").replace(/^-|-$/g, "")
          .slice(0, 60)}}.md`;
        anchor.click();
        URL.revokeObjectURL(url);
      }});
      document.getElementById("download-deadline-reminder")?.addEventListener("click", () => {{
        const deadline = String(facts.deadline_iso || "").replace(/-/g, "");
        if (!/^\\d{{8}}$/.test(deadline)) return;
        const dueDateText = [
          `${{deadline.slice(0, 4)}}-${{deadline.slice(4, 6)}}-`,
          `${{deadline.slice(6, 8)}}T00:00:00Z`
        ].join("");
        const dueDate = new Date(dueDateText);
        dueDate.setUTCDate(dueDate.getUTCDate() + 1);
        const endDate = dueDate.toISOString().slice(0, 10).replace(/-/g, "");
        const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\\.\\d{{3}}Z$/, "Z");
        const title = `${{reminderCopy.event_title}}: ${{facts.program}}`;
        const description = [
          facts.application_url || facts.official_source,
          facts.organizer ? `${{copy.organizer}}: ${{facts.organizer}}` : "",
          `${{copy.deadline}}: ${{facts.deadline}}`
        ].filter(Boolean).join("\\n");
        const escapeIcs = (value) => String(value || "")
          .replace(/\\\\/g, "\\\\\\\\").replace(/;/g, "\\\\;").replace(/,/g, "\\\\,")
          .replace(/\\r?\\n/g, "\\\\n");
        const body = [
          "BEGIN:VCALENDAR",
          "VERSION:2.0",
          "PRODID:-//QAZ.FUND//Deadline reminder//RU",
          "BEGIN:VEVENT",
          `UID:qazfund-${{facts.opportunity_id}}-${{deadline}}@qaz.fund`,
          `DTSTAMP:${{stamp}}`,
          `DTSTART;VALUE=DATE:${{deadline}}`,
          `DTEND;VALUE=DATE:${{endDate}}`,
          `SUMMARY:${{escapeIcs(title)}}`,
          `DESCRIPTION:${{escapeIcs(description)}}`,
          `URL:${{facts.application_url || facts.official_source}}`,
          "BEGIN:VALARM",
          "TRIGGER:-P14D",
          "ACTION:DISPLAY",
          `DESCRIPTION:${{escapeIcs(title)}}`,
          "END:VALARM",
          "BEGIN:VALARM",
          "TRIGGER:-P3D",
          "ACTION:DISPLAY",
          `DESCRIPTION:${{escapeIcs(title)}}`,
          "END:VALARM",
          "END:VEVENT",
          "END:VCALENDAR"
        ].join("\\r\\n");
        const blob = new Blob([body], {{ type: "text/calendar;charset=utf-8" }});
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "qazfund-deadline.ics";
        anchor.click();
        URL.revokeObjectURL(url);
      }});
      document.getElementById("clear-draft").addEventListener("click", () => {{
        if (!window.confirm(copy.clear_confirm)) return;
        try {{
          localStorage.removeItem(storageKey);
        }} catch {{
          status.textContent = copy.storage_error;
        }}
        form.reset();
        steps.forEach((step, index) => {{ step.open = index === 0; }});
        if (status.textContent !== copy.storage_error) status.textContent = "";
        update(!facts.programme_specific);
      }});
      restore();
      update();
    }})();
  </script>
</body>
</html>
"""


__all__ = ["render_application_prep_page"]
