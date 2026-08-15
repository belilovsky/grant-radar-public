"""Server-rendered public opportunity pages for QAZ.FUND."""

from __future__ import annotations

import json
import re
from datetime import date
from enum import Enum
from html import escape
from typing import cast
from urllib.parse import urlparse

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.avds_visual import OPPORTUNITY_AVDS4_CSS
from api.branding import BRAND_MARK_TEAL_HTML
from api.dashboard import dashboard_copy
from api.page_primitives import absolute_href as _absolute_href
from api.page_primitives import catalog_path as _catalog_path
from api.page_primitives import format_deadline as _format_deadline
from api.public_meta import analytics_head_html, og_image_url
from core.decision_support import browser_precheck_contract, program_truth
from core.opportunity_taxonomy import classify_opportunity
from core.models import (
    Opportunity,
    OpportunityDetail,
    OpportunityDetailSection,
    OpportunityMetadataField,
)
from core.nlp import clean_source_summary

PUBLIC_METADATA_KEYS = frozenset(
    {
        "source",
        "funder",
        "deadline",
        "amount",
        "amount_raw",
        "country",
        "region",
        "project_id",
        "reference",
        "status",
        "notice_type",
        "borrower",
        "board_approval",
        "closing_date",
    }
)
HERO_METADATA_KEYS = frozenset({"source", "funder", "deadline"})
SOURCE_SECTION_NOISE_HEADINGS = frozenset(
    {"notification", "search", "поиск", "уведомление"}
)
_DETAIL_SECTION_TECHNICAL_HEADINGS = frozenset(
    {
        "source status",
        "статус источника",
        "дереккөз мәртебесі",
    }
)
_DETAIL_SECTION_OVERVIEW_HEADINGS = frozenset({"overview", "обзор", "шолу"})
_DETAIL_SECTION_ELIGIBILITY_HEADINGS = frozenset(
    {
        "eligibility",
        "кто может подать заявку",
        "кім өтінім бере алады",
    }
)


OPPORTUNITY_DETAIL_CSS = r"""
    .opportunity-article {
      display: grid;
      gap: 16px;
    }
    .opportunity-hero {
      display: grid;
      gap: clamp(16px, 2vw, 22px);
      padding: clamp(22px, 3vw, 36px);
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-sm);
    }
    .opportunity-head {
      display: grid;
      gap: 12px;
      max-width: 1080px;
    }
    .opportunity-kicker {
      color: var(--brand);
      font-size: var(--av-text-xs);
      font-weight: 750;
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .opportunity-hero h1 {
      max-width: 31ch;
      margin: 0;
      color: var(--text);
      font-size: clamp(30px, 3.25vw, 50px);
      line-height: 1.08;
      letter-spacing: -0.035em;
      text-wrap: balance;
    }
    .opportunity-summary {
      max-width: 68ch;
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 34%);
      font-size: clamp(16px, 1.25vw, 19px);
      line-height: 1.56;
    }
    .opportunity-facts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
      gap: 10px;
      margin: 0;
    }
    .opportunity-fact {
      display: grid;
      align-content: start;
      gap: 5px;
      min-height: 74px;
      padding: 12px 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
    }
    .opportunity-fact--key {
      border-top: 2px solid color-mix(in oklab, var(--brand), white 18%);
      background: color-mix(in oklab, var(--surface), var(--brand-soft) 28%);
    }
    .opportunity-fact dt {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      line-height: 1.25;
    }
    .opportunity-fact dd {
      margin: 0;
      color: var(--text);
      font-size: var(--av-text-base);
      font-weight: 750;
      line-height: 1.32;
      overflow-wrap: anywhere;
    }
    .opportunity-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .opportunity-actions .button {
      min-height: 44px;
    }
    .opportunity-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.46fr) minmax(300px, .54fr);
      gap: clamp(18px, 3vw, 40px);
      align-items: start;
    }
    .opportunity-content {
      display: grid;
      gap: 14px;
      min-width: 0;
    }
    .detail-section {
      display: grid;
      gap: 14px;
      padding: clamp(18px, 2.4vw, 26px);
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }
    .detail-section-head {
      display: grid;
      gap: 5px;
      max-width: 760px;
    }
    .detail-section-head h2 {
      margin: 0;
      color: var(--text);
      font-size: clamp(20px, 2vw, 26px);
      line-height: 1.16;
      letter-spacing: -0.018em;
    }
    .detail-section-head p {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.48;
    }
    .eligibility-list,
    .key-conditions-list,
    .source-guidance-list,
    .application-steps {
      display: grid;
      gap: 9px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .eligibility-list li {
      position: relative;
      padding: 0 0 0 18px;
      color: color-mix(in oklab, var(--text), var(--muted) 22%);
      line-height: 1.58;
    }
    .eligibility-list li::before {
      position: absolute;
      top: .66em;
      left: 0;
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--brand);
      content: "";
    }
    .key-conditions-list {
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 225px), 1fr));
      gap: 10px;
      counter-reset: key-condition;
    }
    .key-condition {
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      min-height: 100%;
      padding: 13px 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
      color: color-mix(in oklab, var(--text), var(--muted) 22%);
      line-height: 1.52;
    }
    .key-condition::before {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 26px;
      border-radius: 999px;
      background: color-mix(in oklab, var(--brand-soft), var(--surface) 40%);
      color: var(--brand);
      counter-increment: key-condition;
      content: counter(key-condition, decimal-leading-zero);
      font-size: var(--av-text-xs);
      font-weight: 750;
      line-height: 1;
    }
    .detail-content-list {
      display: grid;
      gap: 22px;
    }
    .detail-content-entry {
      display: grid;
      gap: 9px;
    }
    .detail-content-entry + .detail-content-entry {
      padding-top: 22px;
      border-top: 1px solid var(--line-subtle);
    }
    .detail-content-entry h3 {
      margin: 0;
      color: var(--text);
      font-size: var(--av-text-lg);
      line-height: 1.3;
    }
    .detail-content-entry p {
      max-width: 78ch;
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 25%);
      line-height: 1.67;
    }
    .source-text-disclosure {
      display: grid;
      gap: 14px;
    }
    .source-text-disclosure summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      cursor: pointer;
      color: var(--text);
      font-weight: 750;
      list-style: none;
    }
    .source-text-disclosure summary::-webkit-details-marker {
      display: none;
    }
    .source-text-disclosure summary::after {
      flex: 0 0 auto;
      color: var(--brand);
      content: "+";
      font-size: 20px;
      font-weight: 600;
      line-height: 1;
    }
    .source-text-disclosure[open] summary::after {
      content: "–";
    }
    .source-text-disclosure-action {
      color: var(--muted);
      font-size: var(--av-text-sm);
      font-weight: 650;
    }
    .source-guidance-list {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .source-guidance-item,
    .application-step {
      display: grid;
      gap: 5px;
      padding: 13px 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
    }
    .source-guidance-item strong,
    .application-step h3 {
      margin: 0;
      color: var(--text);
      font-size: var(--av-text-sm);
      line-height: 1.35;
    }
    .source-guidance-item p,
    .application-step p {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.5;
    }
    .application-steps {
      counter-reset: application-step;
    }
    .application-step {
      grid-template-columns: 30px minmax(0, 1fr);
      gap: 11px;
    }
    .application-step::before {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      counter-increment: application-step;
      content: counter(application-step);
      font-size: var(--av-text-xs);
      font-weight: 750;
    }
    .source-panel {
      position: sticky;
      top: 88px;
      display: grid;
      gap: 14px;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }
    .source-panel-head {
      display: grid;
      gap: 5px;
    }
    .source-panel h2 {
      margin: 0;
      color: var(--text);
      font-size: var(--av-text-lg);
      line-height: 1.22;
      overflow-wrap: anywhere;
    }
    .source-host {
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .source-actions {
      display: grid;
      gap: 8px;
    }
    .source-actions .button {
      width: 100%;
      min-height: 44px;
    }
    .reference-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding-top: 14px;
      border-top: 1px solid var(--line-subtle);
    }
    .reference-list div {
      display: grid;
      gap: 3px;
    }
    .reference-list dt {
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }
    .reference-list dd {
      margin: 0;
      color: var(--text);
      font-size: var(--av-text-sm);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .site-footer--compact {
      margin-top: 2px;
    }
    @media (min-width: 1440px) {
      .opportunity-layout {
        grid-template-columns: minmax(0, 1.5fr) minmax(340px, .5fr);
      }
      .opportunity-content {
        max-width: 1120px;
      }
    }
    @media (min-width: 2200px) {
      .opportunity-layout {
        grid-template-columns: minmax(0, 1.56fr) minmax(400px, .44fr);
        gap: 56px;
      }
      .detail-content-entry p {
        max-width: 88ch;
      }
    }
    @media (max-width: 960px) {
      .opportunity-layout {
        grid-template-columns: 1fr;
      }
      .opportunity-facts {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .opportunity-fact:last-child:nth-child(odd) {
        grid-column: 1 / -1;
      }
      .source-panel {
        position: static;
      }
    }
    @media (max-width: 720px) {
      .opportunity-facts,
      .source-guidance-list,
      .key-conditions-list {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }
    @media (max-width: 540px) {
      .opportunity-hero,
      .detail-section,
      .source-panel {
        padding: 18px;
      }
      .opportunity-hero h1 {
        font-size: 30px;
      }
      .opportunity-facts,
      .source-guidance-list,
      .key-conditions-list {
        grid-template-columns: 1fr;
      }
      .opportunity-actions {
        display: grid;
      }
      .opportunity-actions .button {
        width: 100%;
      }
    }
"""


_DECISION_SUPPORT_COPY: dict[str, dict[str, object]] = {
    "ru": {
        "title": "Проверка карточки",
        "note": "Сначала убедитесь, что это набор заявок, а не справка или постоянная услуга. Затем сравните опубликованные условия со своим профилем; данные остаются в браузере.",
        "kind_label": "Тип записи",
        "action_label": "Что можно сделать сейчас",
        "known_label": "Что подтверждено в карточке",
        "fit_title": "Проверить свой профиль",
        "fit_note": "Выберите известные признаки. Профиль остаётся в этом браузере и не подтверждает право на участие.",
        "fit_boundary": "Это предварительная сверка по опубликованным данным, а не подтверждение права на участие.",
        "applicant": "Кто подаёт",
        "legal_form": "Форма заявителя",
        "region": "Где проект",
        "sector": "Направление",
        "support_need": "Что нужно",
        "has_eds": "Есть ЭЦП",
        "all": "Не указывать",
        "applicant_options": {
            "startup": "Стартап",
            "business": "Бизнес",
            "farmer": "Фермер / АПК",
            "ngo": "НКО",
            "researcher": "Исследователь / вуз",
            "student": "Студент",
            "individual": "Физлицо",
            "supplier": "Поставщик / подрядчик",
        },
        "legal_form_options": {
            "ip": "ИП",
            "too": "ТОО",
            "kfh": "КХ / ФХ",
            "ngo": "НКО",
            "university": "Вуз / НИИ",
            "individual": "Физлицо",
            "government": "Госорган / акимат",
        },
        "region_options": {
            "almaty_city": "Алматы",
            "astana": "Астана",
            "shymkent": "Шымкент",
            "almaty_region": "Алматинская область",
            "abay": "область Абай",
            "akmola": "Акмолинская область",
            "aktobe": "Актюбинская область",
            "atyrau": "Атырауская область",
            "east_kazakhstan": "Восточно-Казахстанская область",
            "zhambyl": "Жамбылская область",
            "zhetysu": "область Жетісу",
            "west_kazakhstan": "Западно-Казахстанская область",
            "karaganda": "Карагандинская область",
            "kostanay": "Костанайская область",
            "kyzylorda": "Кызылординская область",
            "mangystau": "Мангистауская область",
            "pavlodar": "Павлодарская область",
            "north_kazakhstan": "Северо-Казахстанская область",
            "turkistan": "Туркестанская область",
            "ulytau": "область Ұлытау",
        },
        "sector_options": {
            "agro": "Растениеводство / АПК",
            "livestock": "Животноводство / вет",
            "ecology": "Экология / отходы",
            "climate": "Климат / зелёные решения",
            "it": "IT / цифровые продукты",
            "science": "Наука / R&D",
            "social": "Социальный проект",
            "manufacturing": "Производство",
            "export": "Экспорт",
        },
        "support_options": {
            "grant": "Грант / конкурс",
            "subsidy": "Субсидия / возмещение",
            "loan": "Кредит / гарантия / лизинг",
            "accelerator": "Акселератор",
            "procurement": "Тендер / закупка",
            "tax": "Налоговая льгота",
        },
        "eds_options": {"yes": "Да", "no": "Нет / не знаю"},
        "fit_action": "Проверить признаки",
        "fit_loading": "Сверяем только опубликованные признаки…",
        "fit_local_error": "Браузер не разрешил сохранить профиль. Проверка всё равно работает на этой странице.",
        "status": {
            "potential_fit": "Есть признаки совпадения",
            "verification_needed": "Нужна проверка условий",
            "profile_needed": "Заполните хотя бы один признак",
            "not_an_application": "Это не открытая заявка",
        },
        "kind": {
            "application_call": "Набор заявок",
            "standing_service": "Постоянная мера / услуга",
            "regulatory_guidance": "Правила и справка",
            "procurement_notice": "Закупка / тендер",
            "procurement_plan": "План закупок",
            "award_result": "Результаты / архив",
            "information": "Информационная запись",
        },
        "action": {
            "apply": "Есть отдельный путь подачи",
            "verify": "Проверьте путь подачи у организатора",
            "reference": "Используйте как правила перед подачей",
            "plan": "Следите за публикацией объявления",
            "results": "Сверьте результаты и следующий набор",
            "monitor": "Следите за обновлением источника",
            "closed": "Приём завершён или результаты опубликованы",
        },
        "fact": {
            "source": "Источник",
            "deadline": "Срок",
            "amount": "Сумма",
            "eligibility": "Критерии",
            "application_route": "Путь подачи",
            "region": "Регион",
        },
        "signals": {
            "applicant_signal": "тип заявителя совпадает по тексту",
            "legal_form_signal": "форма заявителя упомянута",
            "sector_signal": "направление совпадает",
            "support_need_signal": "формат поддержки совпадает",
            "region_signal": "регион указан напрямую",
            "kazakhstan_scope": "Казахстан указан в охвате",
            "eds_ready": "ЭЦП отмечена как готовая",
            "applicant_verify": "подтвердите тип заявителя",
            "legal_form_verify": "подтвердите допустимую форму заявителя",
            "sector_verify": "подтвердите отраслевое ограничение",
            "support_need_verify": "подтвердите формат поддержки",
            "region_verify": "подтвердите региональную доступность",
            "eds_verify": "уточните требование к ЭЦП",
            "eligibility_missing": "в карточке нет полного критерия участия",
            "programme_facts_missing": "в карточке не хватает части ключевых фактов",
            "application_route_verify": "уточните отдельную форму подачи",
            "record_reference": "это справочная запись, а не набор",
            "record_results": "это результаты или архив",
            "record_plan": "это план, а не объявление",
            "record_monitor": "источник нужно мониторить",
            "record_closed": "приём завершён",
        },
    },
    "kk": {
        "title": "Әрекет алдындағы тексеру",
        "note": "Нақты қабылдауды анықтамалықтан ажыратып, бағдарламаны жеке профиліңізбен серверге дерек жібермей салыстырыңыз.",
        "kind_label": "Жазба түрі",
        "action_label": "Қазір не істеуге болады",
        "known_label": "Карточкада расталғаны",
        "fit_title": "Профильді тексеру",
        "fit_note": "Тек жұмыс белгілерін таңдаңыз. Профиль осы браузерде қалады және қатысу құқығын растамайды.",
        "fit_boundary": "Бұл жарияланған дерекке негізделген алдын ала тексеру, қатысу құқығын растау емес.",
        "applicant": "Өтініш беруші",
        "legal_form": "Ұйым нысаны",
        "region": "Жоба өңірі",
        "sector": "Бағыт",
        "support_need": "Қажет қолдау",
        "has_eds": "ЭЦҚ бар",
        "all": "Көрсетпеу",
        "applicant_options": {
            "startup": "Стартап",
            "business": "Бизнес",
            "farmer": "Фермер / АӨК",
            "ngo": "ҮЕҰ",
            "researcher": "Зерттеуші / ЖОО",
            "student": "Студент",
            "individual": "Жеке тұлға",
            "supplier": "Жеткізуші / мердігер",
        },
        "legal_form_options": {
            "ip": "ЖК",
            "too": "ЖШС",
            "kfh": "ШҚ / ФҚ",
            "ngo": "ҮЕҰ",
            "university": "ЖОО / ҒЗИ",
            "individual": "Жеке тұлға",
            "government": "Меморган / әкімдік",
        },
        "region_options": {
            "almaty_city": "Алматы",
            "astana": "Астана",
            "shymkent": "Шымкент",
            "almaty_region": "Алматы облысы",
            "abay": "Абай облысы",
            "akmola": "Ақмола облысы",
            "aktobe": "Ақтөбе облысы",
            "atyrau": "Атырау облысы",
            "east_kazakhstan": "Шығыс Қазақстан облысы",
            "zhambyl": "Жамбыл облысы",
            "zhetysu": "Жетісу облысы",
            "west_kazakhstan": "Батыс Қазақстан облысы",
            "karaganda": "Қарағанды облысы",
            "kostanay": "Қостанай облысы",
            "kyzylorda": "Қызылорда облысы",
            "mangystau": "Маңғыстау облысы",
            "pavlodar": "Павлодар облысы",
            "north_kazakhstan": "Солтүстік Қазақстан облысы",
            "turkistan": "Түркістан облысы",
            "ulytau": "Ұлытау облысы",
        },
        "sector_options": {
            "agro": "Өсімдік шаруашылығы / АӨК",
            "livestock": "Мал шаруашылығы / ветеринария",
            "ecology": "Экология / қалдық",
            "climate": "Климат / жасыл шешім",
            "it": "IT / цифрлық өнім",
            "science": "Ғылым / R&D",
            "social": "Әлеуметтік жоба",
            "manufacturing": "Өндіріс",
            "export": "Экспорт",
        },
        "support_options": {
            "grant": "Грант / конкурс",
            "subsidy": "Субсидия / өтеу",
            "loan": "Несие / кепілдік / лизинг",
            "accelerator": "Акселератор",
            "procurement": "Тендер / сатып алу",
            "tax": "Салықтық жеңілдік",
        },
        "eds_options": {"yes": "Иә", "no": "Жоқ / білмеймін"},
        "fit_action": "Белгілерді тексеру",
        "fit_loading": "Тек жарияланған белгілер салыстырылуда…",
        "fit_local_error": "Браузер профильді сақтауға рұқсат бермеді. Тексеру осы бетте жұмыс істейді.",
        "status": {
            "potential_fit": "Сәйкестік белгілері бар",
            "verification_needed": "Шарттарды тексеру қажет",
            "profile_needed": "Кемінде бір белгіні толтырыңыз",
            "not_an_application": "Бұл ашық өтінім емес",
        },
        "kind": {
            "application_call": "Өтінім қабылдау",
            "standing_service": "Тұрақты шара / қызмет",
            "regulatory_guidance": "Ереже және анықтама",
            "procurement_notice": "Сатып алу / тендер",
            "procurement_plan": "Сатып алу жоспары",
            "award_result": "Нәтижелер / мұрағат",
            "information": "Ақпараттық жазба",
        },
        "action": {
            "apply": "Бөлек өтінім жолы бар",
            "verify": "Өтінім жолын ұйымдастырушыдан тексеріңіз",
            "reference": "Өтінім алдында ереже ретінде қолданыңыз",
            "plan": "Хабарландыруды күтіңіз",
            "results": "Нәтиже мен келесі қабылдауды тексеріңіз",
            "monitor": "Дереккөз жаңартуын бақылаңыз",
            "closed": "Қабылдау аяқталды немесе нәтиже шықты",
        },
        "fact": {
            "source": "Дереккөз",
            "deadline": "Мерзім",
            "amount": "Сома",
            "eligibility": "Талаптар",
            "application_route": "Өтінім жолы",
            "region": "Өңір",
        },
        "signals": {
            "applicant_signal": "өтінім беруші түрі мәтінде сәйкес",
            "legal_form_signal": "ұйым нысаны аталған",
            "sector_signal": "бағыт сәйкес",
            "support_need_signal": "қолдау форматы сәйкес",
            "region_signal": "өңір тікелей көрсетілген",
            "kazakhstan_scope": "Қазақстан қамтуда көрсетілген",
            "eds_ready": "ЭЦҚ дайын деп белгіленді",
            "applicant_verify": "өтінім беруші түрін растаңыз",
            "legal_form_verify": "ұйым нысанын растаңыз",
            "sector_verify": "салалық шектеуді растаңыз",
            "support_need_verify": "қолдау форматын растаңыз",
            "region_verify": "өңірлік қолжетімділікті растаңыз",
            "eds_verify": "ЭЦҚ талабын нақтылаңыз",
            "eligibility_missing": "карточкада толық талап жоқ",
            "programme_facts_missing": "карточкада кей маңызды дерек жетіспейді",
            "application_route_verify": "жеке өтінім формасын нақтылаңыз",
            "record_reference": "бұл анықтама, қабылдау емес",
            "record_results": "бұл нәтиже немесе мұрағат",
            "record_plan": "бұл жоспар, хабарландыру емес",
            "record_monitor": "дереккөзді бақылау керек",
            "record_closed": "қабылдау аяқталды",
        },
    },
    "en": {
        "title": "Check before acting",
        "note": "First separate a live call from a guide or standing service. Then compare published signals with your profile without sending it to the server.",
        "kind_label": "Record type",
        "action_label": "What you can do now",
        "known_label": "Confirmed in this card",
        "fit_title": "Check your profile",
        "fit_note": "Choose only working facts. The profile stays in this browser and does not confirm eligibility.",
        "fit_boundary": "This is a pre-check based on published facts, not a confirmation of eligibility.",
        "applicant": "Applicant",
        "legal_form": "Legal form",
        "region": "Project region",
        "sector": "Sector",
        "support_need": "Need",
        "has_eds": "Digital signature",
        "all": "Do not specify",
        "applicant_options": {
            "startup": "Startup",
            "business": "Business",
            "farmer": "Farmer / agriculture",
            "ngo": "NGO",
            "researcher": "Researcher / university",
            "student": "Student",
            "individual": "Individual",
            "supplier": "Supplier / contractor",
        },
        "legal_form_options": {
            "ip": "Sole proprietor",
            "too": "LLP",
            "kfh": "Farm enterprise",
            "ngo": "NGO",
            "university": "University / research institute",
            "individual": "Individual",
            "government": "Public body",
        },
        "region_options": {
            "almaty_city": "Almaty",
            "astana": "Astana",
            "shymkent": "Shymkent",
            "almaty_region": "Almaty region",
            "abay": "Abai region",
            "akmola": "Akmola region",
            "aktobe": "Aktobe region",
            "atyrau": "Atyrau region",
            "east_kazakhstan": "East Kazakhstan region",
            "zhambyl": "Zhambyl region",
            "zhetysu": "Zhetysu region",
            "west_kazakhstan": "West Kazakhstan region",
            "karaganda": "Karaganda region",
            "kostanay": "Kostanay region",
            "kyzylorda": "Kyzylorda region",
            "mangystau": "Mangystau region",
            "pavlodar": "Pavlodar region",
            "north_kazakhstan": "North Kazakhstan region",
            "turkistan": "Turkistan region",
            "ulytau": "Ulytau region",
        },
        "sector_options": {
            "agro": "Crop production / agriculture",
            "livestock": "Livestock / veterinary",
            "ecology": "Environment / waste",
            "climate": "Climate / green solutions",
            "it": "IT / digital product",
            "science": "Science / R&D",
            "social": "Social project",
            "manufacturing": "Manufacturing",
            "export": "Export",
        },
        "support_options": {
            "grant": "Grant / contest",
            "subsidy": "Subsidy / reimbursement",
            "loan": "Loan / guarantee / leasing",
            "accelerator": "Accelerator",
            "procurement": "Tender / procurement",
            "tax": "Tax incentive",
        },
        "eds_options": {"yes": "Yes", "no": "No / unsure"},
        "fit_action": "Check signals",
        "fit_loading": "Checking published signals…",
        "fit_local_error": "The browser did not allow profile storage. The check still works on this page.",
        "status": {
            "potential_fit": "There are matching signals",
            "verification_needed": "Terms need checking",
            "profile_needed": "Choose at least one signal",
            "not_an_application": "This is not an open application",
        },
        "kind": {
            "application_call": "Application call",
            "standing_service": "Standing service",
            "regulatory_guidance": "Rules and guidance",
            "procurement_notice": "Tender / procurement",
            "procurement_plan": "Procurement plan",
            "award_result": "Results / archive",
            "information": "Information record",
        },
        "action": {
            "apply": "A dedicated application route is known",
            "verify": "Verify the application route with the organiser",
            "reference": "Use as rules before applying",
            "plan": "Watch for the published notice",
            "results": "Check results and the next call",
            "monitor": "Monitor the source for changes",
            "closed": "The call is closed or results are published",
        },
        "fact": {
            "source": "Source",
            "deadline": "Deadline",
            "amount": "Amount",
            "eligibility": "Eligibility",
            "application_route": "Application route",
            "region": "Region",
        },
        "signals": {
            "applicant_signal": "applicant type is mentioned",
            "legal_form_signal": "legal form is mentioned",
            "sector_signal": "sector matches",
            "support_need_signal": "support format matches",
            "region_signal": "region is stated directly",
            "kazakhstan_scope": "Kazakhstan is in scope",
            "eds_ready": "digital signature marked ready",
            "applicant_verify": "verify applicant type",
            "legal_form_verify": "verify legal form",
            "sector_verify": "verify sector restriction",
            "support_need_verify": "verify support format",
            "region_verify": "verify regional availability",
            "eds_verify": "verify digital-signature requirement",
            "eligibility_missing": "full eligibility is missing from the card",
            "programme_facts_missing": "some key facts are missing from the card",
            "application_route_verify": "verify a dedicated application form",
            "record_reference": "this is a reference record, not a call",
            "record_results": "this is a result or archive",
            "record_plan": "this is a plan, not a notice",
            "record_monitor": "monitor the source",
            "record_closed": "the call is closed",
        },
    },
}


def _page_path(root_path: str, opportunity_id: str, lang: str) -> str:
    base = root_path.rstrip("/")
    path = f"/opportunity/{opportunity_id}"
    if base:
        path = f"{base}{path}"
    return f"{path}?lang={lang}"


def _host_label(value: str) -> str:
    try:
        host = urlparse(value).hostname or ""
    except ValueError:
        host = ""
    if host.startswith("www."):
        host = host[4:]
    return host or value


def _label_value(value: object, copy: dict[str, object]) -> str:
    raw_value = value.value if isinstance(value, Enum) else value
    raw = str(raw_value or "").strip()
    if not raw:
        return ""
    label_map_raw = copy.get("label_map")
    label_map = label_map_raw if isinstance(label_map_raw, dict) else {}
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    mapped = label_map.get(normalized) or label_map.get(raw.lower())
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw.replace("_", " ")


def _localized_item_value(
    item: Opportunity,
    field: str,
    lang: str,
    fallback: str,
) -> str:
    raw = item.raw if isinstance(item.raw, dict) else {}
    i18n = raw.get("i18n")
    localized = i18n.get(lang) if isinstance(i18n, dict) else None
    value = localized.get(field) if isinstance(localized, dict) else None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raw_value = raw.get(field)
    if isinstance(raw_value, str) and raw_value.strip():
        return raw_value.strip()
    return fallback.strip()


def _localized_item_list(item: Opportunity, field: str, lang: str) -> list[str]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    i18n = raw.get("i18n")
    localized = i18n.get(lang) if isinstance(i18n, dict) else None
    value = localized.get(field) if isinstance(localized, dict) else None
    if not isinstance(value, list):
        value = raw.get(field)
    if not isinstance(value, list):
        return []
    return [str(entry).strip() for entry in value if str(entry).strip()]


def _localized_card_items(
    item: Opportunity, field: str, lang: str
) -> list[tuple[str, str]]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    i18n = raw.get("i18n")
    localized = i18n.get(lang) if isinstance(i18n, dict) else None
    value = localized.get(field) if isinstance(localized, dict) else None
    if not isinstance(value, list):
        value = raw.get(field)
    if not isinstance(value, list):
        return []
    cards: list[tuple[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title") or "").strip()
        text = str(entry.get("text") or "").strip()
        if title and text:
            cards.append((title, text))
    return cards


def _has_cyrillic(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value))


def _needs_russian_title_fallback(title: str, summary: str, lang: str) -> bool:
    if lang != "ru" or not title or not _has_cyrillic(summary):
        return False
    latin_count = len(re.findall(r"[A-Za-z]", title))
    cyrillic_count = len(re.findall(r"[А-Яа-яЁё]", title))
    return latin_count > cyrillic_count


def _summary_title_fallback(summary: str) -> str:
    sentence_candidates = re.split(r"(?<=[.!?])\s+", summary.strip(), maxsplit=3)
    candidate = sentence_candidates[0] if sentence_candidates else summary.strip()
    skip_prefixes = (
        "крайний срок",
        "срок подачи",
        "дата закрытия",
        "заявки принимаются до",
    )
    for sentence in sentence_candidates:
        normalized = sentence.strip().lower()
        if normalized and not normalized.startswith(skip_prefixes):
            candidate = sentence
            break
    candidate = candidate.rstrip(".!?").strip()
    if len(candidate) <= 120:
        return candidate
    return candidate[:117].rstrip() + "..."


def _clean_summary_text(text: str, *, title: str = "") -> str:
    return clean_source_summary(text, title=title)


def _seo_excerpt(text: str, *, max_length: int = 280) -> str:
    normalized = _clean_summary_text(text)
    if not normalized:
        return ""
    if len(normalized) <= max_length:
        return normalized
    window = normalized[: max_length + 1]
    cut = window.rfind(" ")
    if cut >= max_length * 0.6:
        window = window[:cut]
    else:
        window = normalized[:max_length]
    return window.rstrip(" -:;,") + "..."


def _metadata_markup(
    metadata: list[OpportunityMetadataField],
    labels: dict[str, str],
    copy: dict[str, object],
    *,
    lang: str,
) -> str:
    if not metadata:
        return ""
    items = []
    source_value = next(
        (
            entry.value
            for entry in metadata
            if entry.key == "source" and str(entry.value or "").strip()
        ),
        "",
    )
    for entry in metadata:
        if entry.key not in PUBLIC_METADATA_KEYS:
            continue
        if (
            entry.key == "funder"
            and source_value
            and str(entry.value or "").strip().casefold()
            == str(source_value).strip().casefold()
        ):
            continue
        label = labels.get(entry.key, entry.key.replace("_", " ").title())
        value = _label_value(entry.value, copy)
        if entry.key in {"deadline", "closing_date", "board_approval"}:
            try:
                parsed_date = date.fromisoformat(str(entry.value).strip())
            except ValueError:
                parsed_date = None
            if parsed_date is not None:
                value = _format_deadline(parsed_date, lang, str(copy["open_rolling"]))
        items.append(
            """
            <div class="meta-item">
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
            """.format(
                label=escape(label),
                value=escape(value),
            )
        )
    return "".join(items)


def _readiness_markup(detail: OpportunityDetail, copy: dict[str, object]) -> str:
    """Turn available application facts into a quiet, source-grounded signal."""
    raw = detail.raw if isinstance(detail.raw, dict) else {}
    signals = [
        ("readiness_source", bool(str(detail.source_url).strip())),
        (
            "readiness_deadline",
            bool(detail.deadline or raw.get("deadline_policy") == "rolling"),
        ),
        (
            "readiness_amount",
            bool(
                detail.amount_min is not None
                or detail.amount_max is not None
                or raw.get("amount_raw")
            ),
        ),
        ("readiness_eligibility", bool(detail.eligibility or raw.get("eligibility"))),
    ]
    known = sum(1 for _, available in signals if available)
    rows = "".join(
        f'<div class="readiness-signal {"is-known" if available else "is-missing"}"><span class="readiness-dot" aria-hidden="true"></span><span>{escape(str(copy[label_key]))}</span></div>'
        for label_key, available in signals
    )
    return f"""
    <section class="readiness-panel" data-avds-component="DataViz" data-avds-pattern="opportunity-readiness-meter" aria-label="{escape(str(copy["readiness_title"]), quote=True)}">
      <div class="readiness-head"><div><h2>{escape(str(copy["readiness_title"]))}</h2><p>{escape(str(copy["readiness_note"]))}</p></div><strong>{known}/4</strong></div>
      <div class="readiness-track" role="img" aria-label="{known} of 4 signals available"><span style="width:{known * 25}%"></span></div>
      <div class="readiness-grid">{rows}</div>
    </section>"""


def _decision_copy(lang: str) -> dict[str, object]:
    return _DECISION_SUPPORT_COPY.get(lang, _DECISION_SUPPORT_COPY["en"])


def _profile_select_markup(
    *,
    name: str,
    label: str,
    options: object,
    empty_label: str,
) -> str:
    items = options if isinstance(options, dict) else {}
    rows = [f'<option value="">{escape(empty_label)}</option>']
    for value, option_label in items.items():
        rows.append(
            f'<option value="{escape(str(value), quote=True)}">'
            f"{escape(str(option_label))}</option>"
        )
    return f"""
      <label class="profile-fit-field" for="profile-fit-{escape(name, quote=True)}">
        <span>{escape(label)}</span>
        <select id="profile-fit-{escape(name, quote=True)}" name="{escape(name, quote=True)}">
          {''.join(rows)}
        </select>
      </label>"""


def _decision_support_markup(
    detail: OpportunityDetail,
    *,
    lang: str,
    lifecycle: str,
) -> str:
    """Render an anonymous, source-bound pre-check on a detail page."""

    copy = _decision_copy(lang)
    truth = program_truth(detail, lifecycle=lifecycle)
    known = truth["known_fields"]
    fact_labels = (
        cast(dict[str, object], copy.get("fact"))
        if isinstance(copy.get("fact"), dict)
        else {}
    )
    known_rows = "".join(
        '<li class="{state}"><span aria-hidden="true"></span>{label}</li>'.format(
            state="is-known" if available else "is-missing",
            label=escape(str(fact_labels.get(field, field))),
        )
        for field, available in known.items()
    )
    kind_labels = (
        cast(dict[str, object], copy.get("kind"))
        if isinstance(copy.get("kind"), dict)
        else {}
    )
    action_labels = (
        cast(dict[str, object], copy.get("action"))
        if isinstance(copy.get("action"), dict)
        else {}
    )
    applicant_options = copy.get("applicant_options")
    legal_form_options = copy.get("legal_form_options")
    region_options = copy.get("region_options")
    sector_options = copy.get("sector_options")
    support_options = copy.get("support_options")
    eds_options = copy.get("eds_options")
    fields = "".join(
        (
            _profile_select_markup(
                name="applicant",
                label=str(copy["applicant"]),
                options=applicant_options,
                empty_label=str(copy["all"]),
            ),
            _profile_select_markup(
                name="legal_form",
                label=str(copy["legal_form"]),
                options=legal_form_options,
                empty_label=str(copy["all"]),
            ),
            _profile_select_markup(
                name="region",
                label=str(copy["region"]),
                options=region_options,
                empty_label=str(copy["all"]),
            ),
            _profile_select_markup(
                name="sector",
                label=str(copy["sector"]),
                options=sector_options,
                empty_label=str(copy["all"]),
            ),
            _profile_select_markup(
                name="support_need",
                label=str(copy["support_need"]),
                options=support_options,
                empty_label=str(copy["all"]),
            ),
            _profile_select_markup(
                name="has_eds",
                label=str(copy["has_eds"]),
                options=eds_options,
                empty_label=str(copy["all"]),
            ),
        )
    )
    copy_json = json.dumps(copy, ensure_ascii=False).replace("<", "\\u003c")
    truth_json = json.dumps(truth, ensure_ascii=False).replace("<", "\\u003c")
    precheck_json = json.dumps(
        browser_precheck_contract(detail, lifecycle=lifecycle), ensure_ascii=False
    ).replace("<", "\\u003c")
    return """
    <section class="decision-support" aria-labelledby="decision-support-title" data-avds-component="decision-support">
      <div class="decision-support-head">
        <div>
          <span class="eyebrow">QAZ.FUND</span>
          <h2 id="decision-support-title">{title}</h2>
          <p>{note}</p>
        </div>
        <div class="decision-truth" aria-label="{kind_label}">
          <span>{kind_label}</span>
          <strong>{kind}</strong>
          <small>{action}</small>
        </div>
      </div>
      <div class="decision-facts">
        <span>{known_label}</span>
        <ul>{known_rows}</ul>
      </div>
      <details class="profile-fit" id="profile-fit">
        <summary>
          <span>{fit_title}</span>
          <span>{fit_note}</span>
        </summary>
        <form id="profile-fit-form" novalidate>
          <div class="profile-fit-grid">{fields}</div>
          <div class="profile-fit-actions">
            <button class="button primary" type="submit">{fit_action}</button>
            <p id="profile-fit-storage" aria-live="polite"></p>
          </div>
          <div class="profile-fit-result" id="profile-fit-result" hidden aria-live="polite"></div>
        </form>
      </details>
    </section>
    <script>
      (() => {{
        const form = document.getElementById("profile-fit-form");
        if (!form) return;
        const result = document.getElementById("profile-fit-result");
        const storageStatus = document.getElementById("profile-fit-storage");
        const storageKey = "qazfund-applicant-profile-v1";
        const copy = {copy_json};
        const truth = {truth_json};
        const precheck = {precheck_json};
        const fieldNames = ["applicant", "legal_form", "region", "sector", "support_need", "has_eds"];
        const escapeHtml = (value) => String(value || "")
          .replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/\"/g, "&quot;");
        const labels = copy.signals || {{}};
        const statusLabels = copy.status || {{}};
        const restore = () => {{
          try {{
            const saved = JSON.parse(localStorage.getItem(storageKey) || "{{}}");
            fieldNames.forEach((name) => {{
              const control = form.elements.namedItem(name);
              if (control && typeof saved[name] === "string") control.value = saved[name];
            }});
          }} catch {{
            try {{ localStorage.removeItem(storageKey); }} catch {{}}
          }}
        }};
        const save = () => {{
          const values = Object.fromEntries(fieldNames.map((name) => [
            name, String(form.elements.namedItem(name)?.value || "")
          ]));
          try {{
            localStorage.setItem(storageKey, JSON.stringify(values));
          }} catch {{
            if (storageStatus) storageStatus.textContent = copy.fit_local_error;
          }}
          return values;
        }};
        const renderResult = (payload) => {{
          const status = statusLabels[payload.status] || payload.status;
          const signals = Array.isArray(payload.positive_signals) ? payload.positive_signals : [];
          const checks = Array.isArray(payload.checks) ? payload.checks : [];
          const list = [...signals, ...checks].map((code) => `
            <li class="${{signals.includes(code) ? "is-positive" : "is-check"}}">
              ${{escapeHtml(labels[code] || code.replaceAll("_", " "))}}
            </li>`).join("");
          result.hidden = false;
          result.innerHTML = `
            <strong>${{escapeHtml(status)}}</strong>
            <p>${{escapeHtml(payload.legal_boundary || "")}}</p>
            ${{list ? `<ul>${{list}}</ul>` : ""}}`;
          result.dataset.actionability = String(payload.truth?.actionability || truth.actionability || "");
        }};
        const evaluateProfile = (values) => {{
          const localTruth = precheck.truth || truth || {{}};
          const matches = precheck.matches || {{}};
          const actionability = String(localTruth.actionability || "");
          const kind = String(localTruth.kind || "");
          const positiveSignals = [];
          const checks = [];
          const recordStates = ["reference", "results", "plan", "monitor", "closed"];
          if (recordStates.includes(actionability)) checks.push(`record_${{actionability}}`);
          ["applicant", "legal_form", "sector", "support_need"].forEach((field) => {{
            const value = values[field];
            if (!value) return;
            if (Array.isArray(matches[field]) && matches[field].includes(value)) {{
              positiveSignals.push(`${{field}}_signal`);
            }} else {{
              checks.push(`${{field}}_verify`);
            }}
          }});
          if (values.region) {{
            if (Array.isArray(matches.region) && matches.region.includes(values.region)) {{
              positiveSignals.push("region_signal");
            }} else if (precheck.kazakhstan_scope) {{
              positiveSignals.push("kazakhstan_scope");
            }} else {{
              checks.push("region_verify");
            }}
          }}
          if (values.has_eds === "yes" && ["standing_service", "application_call", "procurement_notice"].includes(kind)) {{
            positiveSignals.push("eds_ready");
          }} else if (["standing_service", "procurement_notice"].includes(kind)) {{
            checks.push("eds_verify");
          }}
          const known = localTruth.known_fields || {{}};
          if (!known.eligibility) checks.push("eligibility_missing");
          if (!known.application_route && actionability === "apply") {{
            checks.push("application_route_verify");
          }}
          if (Array.isArray(localTruth.missing_fields) && localTruth.missing_fields.length) {{
            checks.push("programme_facts_missing");
          }}
          const hasProfile = Object.values(values).some(Boolean);
          let status = "verification_needed";
          if (recordStates.includes(actionability)) status = "not_an_application";
          else if (!hasProfile) status = "profile_needed";
          else if (positiveSignals.length >= 2 && !checks.includes("eligibility_missing")) {{
            status = "potential_fit";
          }}
          return {{
            status,
            truth: localTruth,
            positive_signals: positiveSignals,
            checks: [...new Set(checks)],
            legal_boundary: copy.fit_boundary || "",
          }};
        }};
        restore();
        form.addEventListener("submit", (event) => {{
          event.preventDefault();
          const values = save();
          renderResult(evaluateProfile(values));
        }});
      }})();
    </script>
    """.format(
        title=escape(str(copy["title"])),
        note=escape(str(copy["note"])),
        kind_label=escape(str(copy["kind_label"])),
        kind=escape(str(kind_labels.get(truth["kind"], truth["kind"]))),
        action=escape(
            str(action_labels.get(truth["actionability"], truth["actionability"]))
        ),
        known_label=escape(str(copy["known_label"])),
        known_rows=known_rows,
        fit_title=escape(str(copy["fit_title"])),
        fit_note=escape(str(copy["fit_note"])),
        fields=fields,
        fit_action=escape(str(copy["fit_action"])),
        copy_json=copy_json,
        truth_json=truth_json,
        precheck_json=precheck_json,
    )


def _json_ld(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _opportunity_schema(
    *,
    detail: OpportunityDetail,
    page_title: str,
    display_title: str,
    summary: str,
    canonical_href: str,
    catalog_href: str,
    site_root_href: str,
    lang: str,
    funder_name: str,
) -> str:
    breadcrumb_id = f"{canonical_href}#breadcrumb"
    page_id = f"{canonical_href}#page"
    graph: list[dict[str, object]] = [
        {
            "@type": "BreadcrumbList",
            "@id": breadcrumb_id,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "QAZ.FUND",
                    "item": catalog_href,
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": display_title,
                    "item": canonical_href,
                },
            ],
        },
        {
            "@type": "WebPage",
            "@id": page_id,
            "url": canonical_href,
            "name": page_title,
            "description": summary,
            "inLanguage": lang,
            "breadcrumb": {"@id": breadcrumb_id},
            "isPartOf": {"@id": f"{site_root_href}#website"},
            "about": {
                "@type": "Thing",
                "name": detail.title,
                "description": summary,
                "identifier": str(detail.id),
                "keywords": ", ".join(detail.tags),
                "sameAs": str(detail.source_url),
            },
        },
    ]
    if funder_name:
        graph.append(
            {
                "@type": "Organization",
                "@id": f"{canonical_href}#funder",
                "name": funder_name,
            }
        )
        graph[1]["publisher"] = {"@id": f"{canonical_href}#funder"}
    return _json_ld({"@context": "https://schema.org", "@graph": graph})


def _sections_markup(
    detail: OpportunityDetail,
    fallback_heading: str,
    *,
    title: str,
    expand_label: str = "",
    collapse_label: str = "",
) -> str:
    sections = [section for section in detail.detail_sections if section.text.strip()]
    if not sections:
        return ""
    entries = []
    seen_sections: list[tuple[str, str]] = []
    for section in sections:
        if detail.eligibility and len(section.text) < 96 and "_" in section.text:
            continue
        normalized_heading = re.sub(
            r"\W+", " ", (section.heading or fallback_heading).casefold()
        ).strip()
        if normalized_heading in SOURCE_SECTION_NOISE_HEADINGS:
            continue
        normalized_text = re.sub(r"\W+", " ", section.text.casefold()).strip()
        fallback_normalized = re.sub(r"\W+", " ", fallback_heading.casefold()).strip()
        if (
            normalized_heading == fallback_normalized
            and len(_clean_summary_text(section.text, title=title)) < 80
        ):
            continue
        if any(
            normalized_heading == seen_heading
            and (
                normalized_text.startswith(seen_text)
                or seen_text.startswith(normalized_text)
            )
            for seen_heading, seen_text in seen_sections
            if normalized_text and seen_text
        ):
            continue
        if normalized_text:
            seen_sections.append((normalized_heading, normalized_text))
        paragraphs = "".join(
            "<p>"
            + escape(
                (_clean_summary_text(chunk, title=title) or chunk.strip()).replace(
                    "_", " "
                )
            )
            + "</p>"
            for chunk in _paragraph_chunks(section.text)
            if chunk.strip()
        )
        heading = escape(section.heading or fallback_heading)
        entries.append(
            """
            <section class="source-entry">
              <h3>{heading}</h3>
              <div class="richtext">{paragraphs}</div>
            </section>
            """.format(
                heading=heading,
                paragraphs=paragraphs,
            )
        )
    if not entries:
        return ""
    return """
    <details
      class="section-card source-disclosure"
      data-avds-component="evidence-disclosure"
      data-avds-pattern="evidence-disclosure"
    >
      <summary>
        <span class="source-disclosure-title">{heading}</span>
        <span class="source-disclosure-action">
          <span class="source-action-open">{action}</span>
          <span class="source-action-close">{collapse_action}</span>
        </span>
      </summary>
      <div class="source-excerpts">{entries}</div>
    </details>
    """.format(
        heading=escape(fallback_heading),
        action=escape(expand_label or fallback_heading),
        collapse_action=escape(collapse_label or expand_label or fallback_heading),
        entries="".join(entries),
    )


def _paragraph_chunks(text: str, *, target_length: int = 520) -> list[str]:
    """Turn source walls of text into stable, readable paragraphs."""

    blocks: list[str] = []
    for raw_block in text.splitlines():
        normalized = re.sub(r"\s+", " ", raw_block).strip()
        if not normalized:
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZА-ЯӘҒҚҢӨҰҮҺІ0-9«])", normalized)
        current: list[str] = []
        current_length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            projected = current_length + len(sentence) + (1 if current else 0)
            if current and projected > target_length:
                blocks.append(" ".join(current))
                current = []
                current_length = 0
            current.append(sentence)
            current_length += len(sentence) + (1 if current_length else 0)
        if current:
            blocks.append(" ".join(current))
    return blocks


def _term_blob(detail: OpportunityDetail) -> str:
    raw = detail.raw if isinstance(detail.raw, dict) else {}
    raw_bits: list[str] = []
    for value in raw.values():
        if isinstance(value, str):
            raw_bits.append(value)
        elif isinstance(value, (list, tuple, set)):
            raw_bits.extend(str(item) for item in value if isinstance(item, str))
    return " ".join(
        [
            detail.title,
            detail.summary,
            detail.source,
            detail.funder or "",
            " ".join(detail.tags),
            " ".join(detail.eligibility),
            " ".join(raw_bits),
        ]
    ).lower()


def _prepare_focus_key(detail: OpportunityDetail) -> str:
    terms = _term_blob(detail)
    type_value = detail.type.value
    if any(token in terms for token in ("tender", "procurement", "rfp", "eoi")):
        return "tender"
    if type_value in {"tender"}:
        return "tender"
    if any(
        token in terms
        for token in (
            "subsidy",
            "субсид",
            "tax_benefit",
            "loan_guarantee",
            "preferential_financing",
            "domestic_support",
            "egov",
            "bgov",
            "damu",
        )
    ):
        return "subsidy"
    if any(
        token in terms
        for token in ("science", "research", "commercialization", "lab", "university")
    ):
        return "science"
    if any(
        token in terms
        for token in ("ngo", "nonprofit", "civil_society", "media", "journalism")
    ):
        return "ngo"
    if type_value in {"accelerator", "cloud_credit"} or any(
        token in terms
        for token in ("startup", "accelerator", "cloud", "pitch", "pilot")
    ):
        return "startup"
    return "grant"


def _prepare_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    focus_key = _prepare_focus_key(detail)
    focus_map = {
        "grant": ("prepare_grant_title", "prepare_grant_text"),
        "tender": ("prepare_tender_title", "prepare_tender_text"),
        "startup": ("prepare_startup_title", "prepare_startup_text"),
        "subsidy": ("prepare_subsidy_title", "prepare_subsidy_text"),
        "science": ("prepare_science_title", "prepare_science_text"),
        "ngo": ("prepare_ngo_title", "prepare_ngo_text"),
    }
    deadline_pair = (
        ("prepare_deadline_title", "prepare_deadline_text")
        if detail.deadline is not None
        else ("prepare_rolling_title", "prepare_rolling_text")
    )
    custom_cards = _localized_card_items(detail, "prepare_items", lang)
    cards = custom_cards or [
        (str(copy["prepare_eligibility_title"]), str(copy["prepare_eligibility_text"])),
        (str(copy[deadline_pair[0]]), str(copy[deadline_pair[1]])),
        (str(copy[focus_map[focus_key][0]]), str(copy[focus_map[focus_key][1]])),
        (str(copy["prepare_source_title"]), str(copy["prepare_source_text"])),
    ]
    card_markup = []
    for index, (title, text) in enumerate(cards, start=1):
        card_markup.append(
            """
            <article class="prepare-card">
              <span class="prepare-index">{index:02d}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
            """.format(
                index=index,
                title=escape(title),
                text=escape(text),
            )
        )
    return """
    <section
      class="prepare-section"
      data-avds-component="action-path"
      data-avds-pattern="action-path"
    >
      <div class="prepare-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div class="prepare-grid">{cards}</div>
    </section>
    """.format(
        eyebrow=escape(str(copy["prepare_section_eyebrow"])),
        title=escape(str(copy["prepare_section_title"])),
        description=escape(str(copy["prepare_section_description"])),
        cards="".join(card_markup),
    )


def _decision_check_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
    source_label: str,
    format_label: str,
    deadline_label: str,
) -> str:
    amount = _detail_metadata_value(detail, "amount", "amount_raw")
    known_items = [
        str(copy["decision_check_known_source"]).format(source=source_label),
        str(copy["decision_check_known_format"]).format(format=format_label),
    ]
    if detail.deadline is not None:
        known_items.append(
            str(copy["decision_check_known_deadline"]).format(deadline=deadline_label)
        )
    if amount:
        known_items.append(
            str(copy["decision_check_known_amount"]).format(amount=amount)
        )
    if detail.eligibility:
        eligibility = "; ".join(detail.eligibility[:2])
        known_items.append(
            str(copy["decision_check_known_eligibility"]).format(
                eligibility=eligibility
            )
        )

    missing_labels = copy.get("detail_missing_labels")
    labels = missing_labels if isinstance(missing_labels, dict) else {}
    missing = []
    if detail.deadline is None:
        missing.append(str(labels.get("deadline", "deadline")))
    if not amount:
        missing.append(str(labels.get("amount", "amount")))
    if not detail.eligibility:
        missing.append(str(labels.get("eligibility", "eligibility")))
    if not detail.application_url:
        missing.append(str(labels.get("application", "application")))

    if missing:
        missing_text = str(copy["decision_check_missing_text"]).format(
            items=", ".join(missing)
        )
    else:
        missing_text = str(copy["decision_check_missing_none"])

    route_text = (
        str(copy["decision_check_route_application"])
        if detail.application_url
        else str(copy["decision_check_route_source"])
    )

    cards = (
        (
            "decision_check_known_title",
            "; ".join(known_items) or str(copy["decision_check_known_empty"]),
        ),
        ("decision_check_missing_title", missing_text),
        ("decision_check_route_title", route_text),
        ("decision_check_boundary_title", str(copy["decision_check_boundary_text"])),
    )
    card_markup = "".join(
        """
        <article class="decision-check-card">
          <span class="decision-check-label">{label}</span>
          <p>{text}</p>
        </article>
        """.format(
            label=escape(str(copy[title_key])),
            text=escape(text),
        )
        for title_key, text in cards
    )
    return """
    <section class="decision-check-section" lang="{lang}">
      <div class="decision-check-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div class="decision-check-grid">{cards}</div>
    </section>
    """.format(
        lang=escape(lang, quote=True),
        eyebrow=escape(str(copy["decision_check_eyebrow"])),
        title=escape(str(copy["decision_check_title"])),
        description=escape(str(copy["decision_check_description"])),
        cards=card_markup,
    )


def _apply_markup(
    *,
    detail: OpportunityDetail,
    has_application_url: bool,
    copy: dict[str, object],
    lang: str,
) -> str:
    first_step = (
        ("apply_step_open_apply_title", "apply_step_open_apply_text")
        if has_application_url
        else ("apply_step_open_source_title", "apply_step_open_source_text")
    )
    custom_titles = _localized_item_list(detail, "application_step_titles", lang)
    custom_steps = _localized_item_list(detail, "application_steps", lang)
    steps = (
        list(zip(custom_titles, custom_steps, strict=True))
        if custom_titles and len(custom_titles) == len(custom_steps)
        else [
            (str(copy[first_step[0]]), str(copy[first_step[1]])),
            (str(copy["apply_step_check_title"]), str(copy["apply_step_check_text"])),
            (str(copy["apply_step_pack_title"]), str(copy["apply_step_pack_text"])),
            (str(copy["apply_step_submit_title"]), str(copy["apply_step_submit_text"])),
        ]
    )
    step_markup = []
    for index, (title, text) in enumerate(steps, start=1):
        step_markup.append(
            """
            <li class="apply-step">
              <span class="apply-index">{index:02d}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </li>
            """.format(
                index=index,
                title=escape(title),
                text=escape(text),
            )
        )
    return """
    <section
      class="apply-section"
      data-avds-component="action-path"
      data-avds-pattern="action-path"
    >
      <div class="apply-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <ol class="apply-list">{steps}</ol>
    </section>
    """.format(
        eyebrow=escape(str(copy["apply_section_eyebrow"])),
        title=escape(str(copy["apply_section_title"])),
        description=escape(str(copy["apply_section_description"])),
        steps="".join(step_markup),
    )


def _verification_markup(copy: dict[str, object]) -> str:
    items = (
        ("verification_eligibility_title", "verification_eligibility_text"),
        ("verification_terms_title", "verification_terms_text"),
        ("verification_procurement_title", "verification_procurement_text"),
        ("verification_publication_title", "verification_publication_text"),
    )
    item_markup = "".join(
        """
        <li class="verification-item">
          <strong>{title}</strong>
          <span>{text}</span>
        </li>
        """.format(
            title=escape(str(copy[title_key])),
            text=escape(str(copy[text_key])),
        )
        for title_key, text_key in items
    )
    return """
    <section class="verification-section">
      <div class="verification-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <ul class="verification-list">{items}</ul>
    </section>
    """.format(
        eyebrow=escape(str(copy["verification_eyebrow"])),
        title=escape(str(copy["verification_title"])),
        description=escape(str(copy["verification_description"])),
        items=item_markup,
    )


def _detail_metadata_value(detail: OpportunityDetail, *keys: str) -> str:
    wanted = set(keys)
    for entry in detail.metadata:
        if entry.key in wanted and str(entry.value or "").strip():
            return str(entry.value).strip()
    return ""


def _detail_metadata_values(detail: OpportunityDetail) -> dict[str, str]:
    values: dict[str, str] = {}
    for entry in detail.metadata:
        key = str(entry.key or "").strip()
        value = str(entry.value or "").strip()
        if key and value and key not in values:
            values[key] = value
    return values


def _display_detail_metadata_value(
    value: str,
    *,
    key: str,
    copy: dict[str, object],
    lang: str,
) -> str:
    if not value:
        return ""
    if key in {"deadline", "closing_date", "board_approval"}:
        try:
            return _format_deadline(
                date.fromisoformat(value), lang, str(copy["open_rolling"])
            )
        except ValueError:
            pass
    if key == "deadline_policy" and value.casefold() in {"rolling", "open"}:
        return str(copy["open_rolling"])
    return _label_value(value, copy)


def _detail_format_label(detail: OpportunityDetail, copy: dict[str, object]) -> str:
    """Use the orthogonal taxonomy when it is more precise than the source type."""

    instrument = str(classify_opportunity(detail).get("instrument") or "").strip()
    display_token = {
        "loan": "preferential_financing",
        "procurement": "tender",
        "prize": "contest",
        "scholarship": "fellowship",
        "in_kind_support": "cloud_credit",
    }.get(instrument, instrument)
    if display_token and display_token != "unknown":
        return _label_value(display_token, copy)
    return _label_value(detail.type, copy)


def _published_deadline_label(
    item: Opportunity,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    """Show a deadline only when a source actually provides one."""

    display = _localized_item_value(item, "deadline_display", lang, "")
    if display:
        return display
    if item.deadline is not None:
        return _format_deadline(item.deadline, lang, str(copy["open_rolling"]))
    raw = item.raw if isinstance(item.raw, dict) else {}
    policy = str(raw.get("deadline_policy") or "").strip().casefold()
    if policy in {"rolling", "open"}:
        return str(copy["open_rolling"])
    return ""


def _related_deadline_label(
    item: Opportunity,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    """Keep related cards focused on dates or source-specific time windows."""

    display = _localized_item_value(item, "deadline_display", lang, "")
    if display:
        return display
    if item.deadline is not None:
        return _format_deadline(item.deadline, lang, str(copy["open_rolling"]))
    return ""


def _opportunity_facts_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    """Render every user-facing fact once, in an action-first order."""

    values = _detail_metadata_values(detail)
    raw_labels = copy.get("detail_meta_labels")
    labels = raw_labels if isinstance(raw_labels, dict) else {}
    deadline = _published_deadline_label(detail, copy=copy, lang=lang)
    if not deadline:
        deadline = _display_detail_metadata_value(
            values.get("deadline_raw") or "",
            key="deadline_raw",
            copy=copy,
            lang=lang,
        )
    amount = _localized_item_value(detail, "amount", lang, "")
    if not amount:
        amount = _display_detail_metadata_value(
            values.get("amount") or values.get("amount_raw") or "",
            key="amount" if values.get("amount") else "amount_raw",
            copy=copy,
            lang=lang,
        )
    geography_values: list[str] = []
    for key in ("country", "region"):
        value = _display_detail_metadata_value(
            values.get(key, ""), key=key, copy=copy, lang=lang
        )
        if value and value.casefold() not in {
            item.casefold() for item in geography_values
        }:
            geography_values.append(value)
    geography = ", ".join(geography_values)
    organizer = _display_detail_metadata_value(
        detail.funder or values.get("funder", ""),
        key="funder",
        copy=copy,
        lang=lang,
    )

    deadline_label = _localized_item_value(
        detail,
        "deadline_label",
        lang,
        str(labels.get("deadline", "Deadline")),
    )
    amount_label = _localized_item_value(
        detail,
        "amount_label",
        lang,
        str(labels.get("amount", "Amount")),
    )
    facts: list[tuple[str, str, bool]] = []
    if deadline:
        facts.append((deadline_label, deadline, True))
    if amount:
        facts.append((amount_label, amount, True))
    format_label = _detail_format_label(detail, copy)
    if format_label:
        facts.append((str(copy["meta_format_label"]), format_label, False))
    if geography:
        facts.append((str(copy["detail_geography_label"]), geography, False))
    if organizer:
        facts.append((str(copy["detail_organizer_label"]), organizer, False))
    for key in (
        "status",
        "notice_type",
        "borrower",
        "board_approval",
        "closing_date",
    ):
        value = _display_detail_metadata_value(
            values.get(key, ""), key=key, copy=copy, lang=lang
        )
        if (
            value
            and value not in {deadline, amount}
            and all(value.casefold() != existing.casefold() for _, existing, _ in facts)
        ):
            facts.append(
                (str(labels.get(key, key.replace("_", " ").title())), value, False)
            )

    rows = "".join(
        """
        <div class="opportunity-fact{key_class}">
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
        """.format(
            key_class=" opportunity-fact--key" if is_key else "",
            label=escape(label),
            value=escape(value),
        )
        for label, value, is_key in facts
    )
    return f'<dl class="opportunity-facts">{rows}</dl>'


def _eligibility_markup(detail: OpportunityDetail, *, copy: dict[str, object]) -> str:
    values = [
        _label_value(value, copy)
        for value in detail.eligibility
        if isinstance(value, str) and value.strip()
    ]
    unique_values: list[str] = []
    for value in values:
        if value and value.casefold() not in {
            item.casefold() for item in unique_values
        }:
            unique_values.append(value)
    if not unique_values:
        return ""
    rows = "".join(f"<li>{escape(value)}</li>" for value in unique_values)
    return """
    <section class="detail-section" aria-labelledby="eligibility-title">
      <div class="detail-section-head">
        <h2 id="eligibility-title">{title}</h2>
      </div>
      <ul class="eligibility-list">{rows}</ul>
    </section>
    """.format(
        title=escape(str(copy["detail_eligibility_title"])),
        rows=rows,
    )


def _highlights_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    highlights = _localized_item_list(detail, "highlights", lang)
    if not highlights:
        return ""
    title = _localized_item_value(
        detail,
        "highlights_label",
        lang,
        str(copy["decision_check_title"]),
    )
    rows = "".join(
        '<li class="key-condition">{value}</li>'.format(value=escape(value))
        for value in highlights
    )
    return """
    <section class="detail-section detail-section--conditions" aria-labelledby="conditions-title">
      <div class="detail-section-head">
        <h2 id="conditions-title">{title}</h2>
      </div>
      <ol class="key-conditions-list">{rows}</ol>
    </section>
    """.format(title=escape(title), rows=rows)


def _content_sections_markup(
    detail: OpportunityDetail,
    *,
    title: str,
    summary: str,
    copy: dict[str, object],
    collapsed: bool = False,
) -> str:
    """Keep source-derived conditions readable without repeating the card header."""

    sections = [section for section in detail.detail_sections if section.text.strip()]
    if not sections and detail.detail_text.strip():
        sections = [OpportunityDetailSection(heading="", text=detail.detail_text)]
    normalized_summary = re.sub(r"\W+", " ", summary.casefold()).strip()
    eligibility_text = re.sub(
        r"\W+", " ", " ".join(detail.eligibility).casefold()
    ).strip()
    seen_sections: list[tuple[str, str]] = []
    entries: list[str] = []
    for section in sections:
        heading_raw = (section.heading or "").strip()
        text_raw = section.text.strip()
        normalized_heading = re.sub(r"\W+", " ", heading_raw.casefold()).strip()
        normalized_text = re.sub(r"\W+", " ", text_raw.casefold()).strip()
        if (
            not normalized_text
            or normalized_heading in SOURCE_SECTION_NOISE_HEADINGS
            or normalized_heading in _DETAIL_SECTION_TECHNICAL_HEADINGS
        ):
            continue
        if (
            normalized_heading in _DETAIL_SECTION_OVERVIEW_HEADINGS
            and normalized_text == normalized_summary
        ):
            continue
        if (
            normalized_heading in _DETAIL_SECTION_ELIGIBILITY_HEADINGS
            and eligibility_text
            and normalized_text == eligibility_text
        ):
            continue
        if any(
            normalized_heading == seen_heading
            and (
                normalized_text.startswith(seen_text)
                or seen_text.startswith(normalized_text)
            )
            for seen_heading, seen_text in seen_sections
            if normalized_text and seen_text
        ):
            continue
        seen_sections.append((normalized_heading, normalized_text))
        paragraphs = "".join(
            "<p>"
            + escape(
                (_clean_summary_text(chunk, title=title) or chunk.strip()).replace(
                    "_", " "
                )
            )
            + "</p>"
            for chunk in _paragraph_chunks(text_raw, target_length=440)
            if chunk.strip()
        )
        if not paragraphs:
            continue
        heading = heading_raw or str(copy["detail_content_fallback_heading"])
        entries.append(
            """
            <section class="detail-content-entry">
              <h3>{heading}</h3>
              {paragraphs}
            </section>
            """.format(
                heading=escape(heading),
                paragraphs=paragraphs,
            )
        )
    if not entries:
        return ""
    entries_markup = "".join(entries)
    if collapsed:
        return """
        <section class="detail-section detail-section--source">
          <details class="source-text-disclosure">
            <summary>
              <span>{title}</span>
              <span class="source-text-disclosure-action">{action}</span>
            </summary>
            <div class="detail-content-list">{entries}</div>
          </details>
        </section>
        """.format(
            title=escape(str(copy["detail_source_excerpt"])),
            action=escape(str(copy["detail_expand_source"])),
            entries=entries_markup,
        )
    return """
    <section class="detail-section" aria-labelledby="content-title">
      <div class="detail-section-head">
        <h2 id="content-title">{title}</h2>
      </div>
      <div class="detail-content-list">{entries}</div>
    </section>
    """.format(
        title=escape(str(copy["detail_content_title"])),
        entries=entries_markup,
    )


def _source_guidance_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    cards = _localized_card_items(detail, "prepare_items", lang)
    if not cards:
        return ""
    rows = "".join("""
        <li class="source-guidance-item">
          <strong>{title}</strong>
          <p>{text}</p>
        </li>
        """.format(title=escape(title), text=escape(text)) for title, text in cards)
    return """
    <section class="detail-section" aria-labelledby="guidance-title">
      <div class="detail-section-head">
        <h2 id="guidance-title">{title}</h2>
      </div>
      <ul class="source-guidance-list">{rows}</ul>
    </section>
    """.format(title=escape(str(copy["detail_guidance_title"])), rows=rows)


def _application_steps_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
) -> str:
    titles = _localized_item_list(detail, "application_step_titles", lang)
    steps = _localized_item_list(detail, "application_steps", lang)
    if not titles or len(titles) != len(steps):
        return ""
    rows = "".join(
        """
        <li class="application-step">
          <div>
            <h3>{title}</h3>
            <p>{text}</p>
          </div>
        </li>
        """.format(title=escape(title), text=escape(text))
        for title, text in zip(titles, steps, strict=True)
    )
    return """
    <section class="detail-section" aria-labelledby="application-title">
      <div class="detail-section-head">
        <h2 id="application-title">{title}</h2>
      </div>
      <ol class="application-steps">{rows}</ol>
    </section>
    """.format(title=escape(str(copy["detail_application_steps_title"])), rows=rows)


def _source_panel_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
    lang: str,
    source_label: str,
    source_host: str,
    source_href: str,
    application_href: str,
    applications_closed: bool,
) -> str:
    values = _detail_metadata_values(detail)
    raw_labels = copy.get("detail_meta_labels")
    labels = raw_labels if isinstance(raw_labels, dict) else {}
    reference_rows: list[str] = []
    for key in ("reference", "project_id"):
        value = _display_detail_metadata_value(
            values.get(key, ""), key=key, copy=copy, lang=lang
        )
        if value:
            reference_rows.append(
                """
                <div><dt>{label}</dt><dd>{value}</dd></div>
                """.format(
                    label=escape(str(labels.get(key, key.replace("_", " ").title()))),
                    value=escape(value),
                )
            )
    reference_markup = (
        """
        <dl class="reference-list">
          <div class="reference-list-title"><dt>{title}</dt></div>
          {rows}
        </dl>
        """.format(
            title=escape(str(copy["detail_reference_title"])),
            rows="".join(reference_rows),
        )
        if reference_rows
        else ""
    )
    application_action = (
        """
        <a class="button primary" href="{href}" target="_blank" rel="noopener">{label}</a>
        """.format(
            href=application_href,
            label=escape(str(copy["detail_open_application"])),
        )
        if application_href and not applications_closed
        else ""
    )
    source_button_class = "button slim" if application_action else "button primary"
    return """
    <aside class="source-panel" aria-labelledby="source-title">
      <div class="source-panel-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2 id="source-title">{source_label}</h2>
        <p class="source-host">{source_host}</p>
      </div>
      <div class="source-actions">
        {application_action}
        <a class="{source_button_class}" href="{source_href}" target="_blank" rel="noopener">{source_button_label}</a>
      </div>
      {reference_markup}
    </aside>
    """.format(
        eyebrow=escape(str(copy["detail_source_title"])),
        source_label=escape(source_label),
        source_host=escape(source_host),
        application_action=application_action,
        source_button_class=source_button_class,
        source_href=source_href,
        source_button_label=escape(str(copy["detail_open_source"])),
        reference_markup=reference_markup,
    )


def _working_brief(
    detail: OpportunityDetail,
    *,
    title: str,
    summary: str,
    source_label: str,
    format_label: str,
    deadline_label: str,
    copy: dict[str, object],
) -> str:
    region = _detail_metadata_value(detail, "region", "country")
    amount = _detail_metadata_value(detail, "amount", "amount_raw")
    lines = [
        str(copy["detail_brief_heading"]),
        title,
        "",
        f'{copy["detail_brief_summary"]}: {summary}',
        f'{copy["detail_brief_source"]}: {source_label}',
        f'{copy["detail_brief_format"]}: {format_label}',
    ]
    if region:
        lines.append(f'{copy["detail_brief_region"]}: {_label_value(region, copy)}')
    lines.append(f'{copy["detail_brief_deadline"]}: {deadline_label}')
    if amount:
        lines.append(f'{copy["detail_brief_amount"]}: {amount}')
    lines.append(f'{copy["detail_brief_official_url"]}: {detail.source_url}')
    if detail.application_url:
        lines.append(
            f'{copy["detail_brief_application_url"]}: {detail.application_url}'
        )
    lines.extend(("", str(copy["detail_brief_caveat"])))
    return "\n".join(lines)


def _related_markup(
    related_items: list[tuple[Opportunity, str]],
    *,
    lang: str,
    root_path: str,
    copy: dict[str, object],
) -> str:
    if not related_items:
        return ""
    cards: list[str] = []
    for item, reason_key in related_items:
        title = _localized_item_value(
            item,
            "title",
            lang,
            item.title or str(copy["detail_title_fallback"]),
        ) or str(copy["detail_title_fallback"])
        summary = _clean_summary_text(
            _localized_item_value(
                item,
                "summary",
                lang,
                item.summary or str(copy["no_summary"]),
            ),
            title=title,
        ) or str(copy["no_summary"])
        if _needs_russian_title_fallback(title, summary, lang):
            title = _summary_title_fallback(summary)
        href = escape(_page_path(root_path, str(item.id), lang), quote=True)
        reason = escape(str(copy.get(reason_key, copy["related_reason_theme"])))
        source_label = escape(item.funder or _label_value(item.source, copy))
        deadline_label = _related_deadline_label(item, copy=copy, lang=lang)
        deadline_markup = (
            '<span class="related-deadline">{deadline}</span>'.format(
                deadline=escape(deadline_label)
            )
            if deadline_label
            else ""
        )
        cards.append(
            """
            <article class="related-card" data-avds-component="document-card">
              <div class="related-top">
                <span class="related-reason">{reason}</span>
                {deadline}
              </div>
              <h3><a href="{href}">{title}</a></h3>
              <p class="related-summary">{summary}</p>
              <div class="related-meta">
                <span>{source}</span>
                <a class="related-link" href="{href}">{action}</a>
              </div>
            </article>
            """.format(
                reason=reason,
                deadline=deadline_markup,
                href=href,
                title=escape(title),
                summary=escape(summary),
                source=source_label,
                action=escape(str(copy["related_open"])),
            )
        )
    return """
    <section class="related-section">
      <div class="related-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div class="related-grid">{cards}</div>
    </section>
    """.format(
        eyebrow=escape(str(copy["related_section_eyebrow"])),
        title=escape(str(copy["related_section_title"])),
        description=escape(str(copy["related_section_description"])),
        cards="".join(cards),
    )


def render_opportunity_page(
    *,
    detail: OpportunityDetail,
    lang: str,
    root_path: str,
    site_origin: str,
    related_items: list[tuple[Opportunity, str]] | None = None,
    lifecycle: str = "open",
) -> str:
    copy = dashboard_copy(lang)
    active_lang = str(copy["lang"])
    title = detail.title or str(copy["detail_title_fallback"])
    summary = _clean_summary_text(detail.summary, title=title) or str(
        copy["detail_empty"]
    )
    seo_summary = _seo_excerpt(summary) or summary
    page_title = f"{title} – QAZ.FUND"
    canonical_path = _page_path(root_path, str(detail.id), active_lang)
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    ru_href = escape(
        _absolute_href(site_origin, _page_path(root_path, str(detail.id), "ru")),
        quote=True,
    )
    en_href = escape(
        _absolute_href(site_origin, _page_path(root_path, str(detail.id), "en")),
        quote=True,
    )
    kk_href = escape(
        _absolute_href(site_origin, _page_path(root_path, str(detail.id), "kk")),
        quote=True,
    )
    catalog_href = escape(_catalog_path(root_path, active_lang), quote=True)
    detail_base = root_path.rstrip("/")
    asset_base = f"{detail_base}/assets/branding" if detail_base else "/assets/branding"
    favicon_href = f"{detail_base}/favicon.ico" if detail_base else "/favicon.ico"
    sources_href = escape(
        (
            f"{detail_base}/?lang={active_lang}#sources"
            if detail_base
            else f"/?lang={active_lang}#sources"
        ),
        quote=True,
    )
    terms_href = escape(
        (
            f"{detail_base}/terms?lang={active_lang}"
            if detail_base
            else f"/terms?lang={active_lang}"
        ),
        quote=True,
    )
    data_policy_href = escape(
        (
            f"{detail_base}/data-policy?lang={active_lang}"
            if detail_base
            else f"/data-policy?lang={active_lang}"
        ),
        quote=True,
    )
    source_href = escape(str(detail.source_url), quote=True)
    application_href = (
        escape(detail.application_url, quote=True) if detail.application_url else ""
    )
    prepare_href = escape(
        (
            f"{detail_base}/opportunity/{detail.id}/prepare?lang={active_lang}"
            if detail_base
            else f"/opportunity/{detail.id}/prepare?lang={active_lang}"
        ),
        quote=True,
    )
    related_markup = _related_markup(
        related_items or [],
        lang=active_lang,
        root_path=root_path,
        copy=copy,
    )
    source_text = detail.funder or _label_value(detail.source, copy)
    format_text = _detail_format_label(detail, copy)
    source_host = _host_label(str(detail.source_url))
    applications_closed = lifecycle in {"closed", "awarded"}
    actionability = str(program_truth(detail, lifecycle=lifecycle)["actionability"])
    application_button = (
        """
        <a class="button primary" href="{href}" target="_blank" rel="noopener">
          {label}
        </a>
        """.format(
            href=application_href,
            label=escape(str(copy["detail_open_application"])),
        )
        if application_href and not applications_closed
        else ""
    )
    prepare_button = (
        """
        <a class="button slim" href="{href}">{label}</a>
        """.format(
            href=prepare_href,
            label=escape(str(copy["detail_prepare_application"])),
        )
        if not applications_closed and actionability in {"apply", "verify"}
        else ""
    )
    source_button_class = "button slim" if application_button else "button primary"
    opportunity_facts = _opportunity_facts_markup(
        detail,
        copy=copy,
        lang=active_lang,
    )
    eligibility_markup = _eligibility_markup(detail, copy=copy)
    highlights_markup = _highlights_markup(detail, copy=copy, lang=active_lang)
    guidance_markup = _source_guidance_markup(
        detail,
        copy=copy,
        lang=active_lang,
    )
    application_steps_markup = (
        _application_steps_markup(detail, copy=copy, lang=active_lang)
        if not applications_closed
        else ""
    )
    content_markup = _content_sections_markup(
        detail,
        title=title,
        summary=summary,
        copy=copy,
        collapsed=bool(
            highlights_markup
            or eligibility_markup
            or guidance_markup
            or application_steps_markup
        ),
    )
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    canonical_url = _absolute_href(site_origin, canonical_path)
    catalog_url = _absolute_href(site_origin, _catalog_path(root_path, active_lang))
    site_root_url = _absolute_href(
        site_origin,
        (
            f"{root_path.rstrip('/')}/?lang={active_lang}"
            if root_path.rstrip("/")
            else f"/?lang={active_lang}"
        ),
    )
    social_image = escape(og_image_url(site_origin, root_path), quote=True)
    analytics_head = analytics_head_html()
    ru_lang_class = "active" if active_lang == "ru" else ""
    kk_lang_class = "active" if active_lang == "kk" else ""
    en_lang_class = "active" if active_lang == "en" else ""
    ru_lang_current = ' aria-current="page"' if active_lang == "ru" else ""
    kk_lang_current = ' aria-current="page"' if active_lang == "kk" else ""
    en_lang_current = ' aria-current="page"' if active_lang == "en" else ""
    fallback_note = str(copy.get("language_fallback_note") or "").strip()
    fallback_note_markup = (
        f'<p class="language-fallback-note" lang="kk" data-language-fallback="source">{escape(fallback_note)}</p>'
        if fallback_note
        else ""
    )
    lifecycle_notice = ""
    if applications_closed:
        lifecycle_notice = str(copy["detail_closed_notice"])
    elif lifecycle == "forecast":
        lifecycle_notice = str(copy["detail_forecast_notice"])
    lifecycle_notice_markup = (
        '<p class="lifecycle-notice" data-avds-component="Alert">'
        f"{escape(lifecycle_notice)}</p>"
        if lifecycle_notice
        else ""
    )
    source_panel_markup = _source_panel_markup(
        detail,
        copy=copy,
        lang=active_lang,
        source_label=source_text,
        source_host=source_host,
        source_href=source_href,
        application_href=application_href,
        applications_closed=applications_closed,
    )
    html_attrs = (
        f'lang="{escape(active_lang, quote=True)}" '
        'data-avds="grant-radar" data-av-theme="light" data-theme="light"'
    )
    schema_json = _opportunity_schema(
        detail=detail,
        page_title=page_title,
        display_title=title,
        summary=seo_summary,
        canonical_href=canonical_url,
        catalog_href=catalog_url,
        site_root_href=site_root_url,
        lang=active_lang,
        funder_name=detail.funder or "",
    )

    return f"""<!doctype html>
<html {html_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#00545D">
  <link rel="icon" href="{favicon_href}" sizes="any">
  <link rel="icon" type="image/svg+xml" href="{asset_base}/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="{asset_base}/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="{asset_base}/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{asset_base}/apple-touch-icon.png">
  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(seo_summary, quote=True)}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="kk" href="{kk_href}">
  <link rel="alternate" hreflang="ru" href="{ru_href}">
  <link rel="alternate" hreflang="en" href="{en_href}">
  <link rel="alternate" hreflang="x-default" href="{ru_href}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{escape(page_title, quote=True)}">
  <meta property="og:description" content="{escape(seo_summary, quote=True)}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(page_title, quote=True)}">
  <meta name="twitter:description" content="{escape(seo_summary, quote=True)}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
{analytics_head}
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme: light;
      --bg: var(--color-bg);
      --surface: var(--color-surface);
      --surface-subtle: var(--color-bg-subtle);
      --surface-raised: var(--color-surface-raised);
      --surface-wash: color-mix(in oklab, var(--surface), var(--surface-subtle) 42%);
      --surface-wash-soft: color-mix(in oklab, var(--surface), var(--surface-subtle) 28%);
      --surface-wash-card: color-mix(in oklab, var(--surface), var(--surface-subtle) 36%);
      --accent-wash: color-mix(in oklab, var(--surface), var(--brand-soft) 24%);
      --text: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --line-strong: var(--color-border-strong);
      --brand: var(--color-accent);
      --brand-soft: var(--color-accent-subtle);
      --success: var(--color-success);
      --success-soft: var(--color-success-subtle);
      --radius: var(--av-radius-lg);
      --shadow: var(--shadow-md);
      --container-max: min(var(--av-container-dashboard), calc(100% - 48px));
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 12% 0%, var(--brand-soft), transparent 28rem),
        var(--bg);
      color: var(--text);
      font-family: var(--av-font-sans);
      font-size: var(--av-text-base);
      line-height: var(--av-leading-normal);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{
      width: var(--container-max);
      margin: 0 auto;
      padding: 18px 0 44px;
    }}
    .topbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      position: sticky;
      top: 12px;
      z-index: 20;
      margin-bottom: 18px;
      padding: 10px 14px;
      border: 1px solid color-mix(in oklab, var(--line), transparent 18%);
      border-radius: var(--av-radius-lg);
      background: color-mix(in oklab, var(--surface), transparent 7%);
      box-shadow: var(--av-shadow-sm);
      backdrop-filter: blur(16px);
    }}
    .breadcrumbs {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .language-fallback-note {{ margin:0 0 14px; padding:9px 12px; border-left:3px solid var(--brand);
      color:var(--muted); background:var(--surface-subtle); font-size:12px; line-height:1.45; }}
    .breadcrumbs a:hover {{
      color: var(--brand);
    }}
    .lang-switch {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .lang-switch a {{
      min-width: 34px;
      padding: 6px 8px;
      border-bottom: 2px solid transparent;
      color: var(--muted);
      text-align: center;
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .lang-switch a.active {{
      border-bottom-color: var(--brand);
      color: var(--text);
    }}
    .hero {{
      display: grid;
      gap: 12px;
      padding: 24px 26px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--accent-wash);
      box-shadow: var(--shadow);
      margin-bottom: 14px;
    }}
    .eyebrow {{
      color: var(--brand);
      font-size: var(--av-text-xs);
      font-family: var(--font-sans);
      font-weight: 750;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .hero h1 {{
      margin: 0;
      max-width: 24ch;
      font-size: clamp(34px, 4.2vw, 58px);
      line-height: 1.02;
      letter-spacing: -0.035em;
      text-wrap: balance;
    }}
    .summary {{
      margin: 0;
      max-width: 60ch;
      color: color-mix(in oklab, var(--text), var(--muted) 35%);
      font-size: clamp(16px, 1.4vw, 19px);
      line-height: 1.55;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(260px, 0.66fr);
      gap: clamp(28px, 5vw, 72px);
      align-items: start;
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 46px;
      padding: 0 18px;
      border-radius: var(--av-radius-md);
      border: 1px solid var(--line);
      background: var(--surface);
      font-weight: 700;
      cursor: pointer;
      transition:
        transform var(--av-motion-fast) ease,
        border-color var(--av-motion-fast) ease,
        box-shadow var(--av-motion-fast) ease;
    }}
    .button:hover {{
      transform: translateY(-1px);
      border-color: var(--line-strong);
      box-shadow: var(--av-shadow-sm);
    }}
    .button.primary {{
      border-color: color-mix(in oklab, var(--brand), black 12%);
      background: var(--brand);
      color: white;
    }}
    .button:hover {{
      border-color: var(--line-strong);
      background: var(--surface-subtle);
    }}
    .button.primary:hover {{
      border-color: color-mix(in oklab, var(--brand), black 18%);
      background: color-mix(in oklab, var(--brand), black 10%);
      color: white;
    }}
    .button.slim {{
      min-height: 46px;
      background: color-mix(in oklab, var(--surface), white 14%);
    }}
    .hero-stats {{
      display: grid;
      gap: 0;
      padding: 18px;
      border: 1px solid color-mix(in oklab, var(--line), transparent 12%);
      border-radius: var(--av-radius-lg);
      background: color-mix(in oklab, var(--surface), transparent 12%);
      box-shadow: var(--av-shadow-xs);
    }}
    .hero-stats > div {{
      display: grid;
      gap: 4px;
      padding: 12px 0;
      border-bottom: 1px solid var(--line-subtle);
    }}
    .hero-stats > div:first-child {{
      padding-top: 0;
    }}
    .hero-stats > div:last-child {{
      padding-bottom: 0;
      border-bottom: 0;
    }}
    .hero-stats strong {{
      font-size: var(--av-text-base);
      line-height: 1.15;
    }}
    .metric {{
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-left: 3px solid var(--brand);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / 0.56);
      box-shadow: var(--av-shadow-xs);
    }}
    .metric span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      text-transform: none;
      letter-spacing: 0;
    }}
    .metric strong {{
      font-size: var(--av-text-base);
      line-height: 1.2;
    }}
    .pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 18px;
      padding: 0 4px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: var(--av-control-height-sm);
      padding: 0 12px;
      border-radius: 999px;
      border: 1px solid var(--line-subtle);
      background: var(--success-soft);
      color: color-mix(in oklab, var(--success), black 20%);
      font-size: var(--av-text-sm);
      font-weight: 600;
    }}
    .readiness-panel {{
      display: grid;
      gap: 10px;
      margin: 0 0 14px;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .readiness-head {{
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 16px;
    }}
    .readiness-head h2 {{ margin: 0 0 3px; font-size: 16px; line-height: 1.2; }}
    .readiness-head p {{ margin: 0; color: var(--muted); font-size: var(--av-text-sm); }}
    .readiness-head > strong {{ color: var(--brand); font-size: 18px; line-height: 1; }}
    .readiness-track {{ height: 7px; overflow: hidden; border-radius: 999px; background: var(--surface-subtle); }}
    .readiness-track span {{ display: block; height: 100%; border-radius: inherit; background: var(--brand); transition: width 180ms ease; }}
    .readiness-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
    .readiness-signal {{ display: flex; align-items: center; gap: 7px; color: var(--muted); font-size: var(--av-text-xs); font-weight: 700; }}
    .readiness-dot {{ width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; background: var(--line-strong); }}
    .readiness-signal.is-known {{ color: var(--success); }}
    .readiness-signal.is-known .readiness-dot {{ background: var(--success); }}
    .decision-support {{
      display: grid;
      gap: 14px;
      margin: 0 0 14px;
      padding: clamp(16px, 2.4vw, 26px);
      border: 1px solid color-mix(in oklab, var(--brand), white 72%);
      border-radius: var(--av-radius-lg);
      background: linear-gradient(128deg, var(--surface-wash-soft), var(--surface));
      box-shadow: var(--av-shadow-xs);
    }}
    .decision-support-head {{
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 20px;
    }}
    .decision-support-head h2 {{ margin: 3px 0 6px; font-size: clamp(18px, 2vw, 24px); line-height: 1.16; }}
    .decision-support-head p {{ max-width: 760px; margin: 0; color: var(--muted); font-size: var(--av-text-sm); line-height: 1.48; }}
    .decision-truth {{
      display: grid;
      min-width: min(250px, 36vw);
      gap: 4px;
      padding: 11px 13px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--surface);
    }}
    .decision-truth > span {{ color: var(--muted); font-size: var(--av-text-xs); font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }}
    .decision-truth strong {{ color: var(--brand); font-size: var(--av-text-sm); line-height: 1.25; }}
    .decision-truth small {{ color: var(--muted); font-size: var(--av-text-xs); line-height: 1.35; }}
    .decision-facts {{ display: grid; gap: 8px; }}
    .decision-facts > span {{ font-size: var(--av-text-sm); font-weight: 700; }}
    .decision-facts ul {{ display: flex; flex-wrap: wrap; gap: 7px 12px; margin: 0; padding: 0; list-style: none; }}
    .decision-facts li {{ display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: var(--av-text-xs); font-weight: 700; }}
    .decision-facts li > span {{ width: 7px; height: 7px; border-radius: 999px; background: var(--line-strong); }}
    .decision-facts li.is-known {{ color: var(--success); }}
    .decision-facts li.is-known > span {{ background: var(--success); }}
    .profile-fit {{ border-top: 1px solid var(--line); padding-top: 12px; }}
    .profile-fit summary {{ display: grid; gap: 3px; cursor: pointer; list-style: none; }}
    .profile-fit summary::-webkit-details-marker {{ display: none; }}
    .profile-fit summary > span:first-child {{ color: var(--brand); font-size: var(--av-text-base); font-weight: 750; }}
    .profile-fit summary > span:last-child {{ color: var(--muted); font-size: var(--av-text-sm); line-height: 1.42; }}
    .profile-fit form {{ display: grid; gap: 12px; margin-top: 14px; }}
    .profile-fit-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .profile-fit-field {{ display: grid; gap: 5px; color: var(--muted); font-size: var(--av-text-xs); font-weight: 700; }}
    .profile-fit-field select {{ min-width: 0; min-height: 40px; padding: 8px 30px 8px 10px; border: 1px solid var(--line-strong); border-radius: var(--av-radius-sm); color: var(--text); background: var(--surface); font: inherit; }}
    .profile-fit-actions {{ display: flex; align-items: center; gap: 12px; }}
    .profile-fit-actions p {{ margin: 0; color: var(--muted); font-size: var(--av-text-xs); line-height: 1.35; }}
    .profile-fit-result {{ display: grid; gap: 7px; padding: 12px 13px; border-radius: var(--av-radius-md); background: var(--surface); box-shadow: var(--av-shadow-2xs); }}
    .profile-fit-result > strong {{ color: var(--brand); font-size: var(--av-text-sm); }}
    .profile-fit-result > p {{ margin: 0; color: var(--muted); font-size: var(--av-text-xs); line-height: 1.42; }}
    .profile-fit-result ul {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; margin: 0; padding-left: 16px; }}
    .profile-fit-result li {{ color: var(--muted); font-size: var(--av-text-xs); line-height: 1.36; }}
    .profile-fit-result li.is-positive {{ color: var(--success); }}
    .profile-fit-result li.is-check {{ color: color-mix(in oklab, var(--text), var(--muted) 28%); }}
    .content-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.48fr) minmax(280px, 0.62fr);
      gap: 20px;
      align-items: start;
      padding-top: 0;
      border-top: 0;
    }}
    .content-grid--single {{
      grid-template-columns: minmax(0, 1fr);
    }}
    .content-grid--single .section-stack {{
      grid-template-columns: repeat(2, minmax(0, 1fr));
      column-gap: 14px;
    }}
    .content-grid--single .source-disclosure {{ grid-column: 1 / -1; }}
    .section-stack {{
      display: grid;
      gap: 12px;
    }}
    .section-card {{
      padding: 0;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
      overflow: clip;
    }}
    .source-disclosure summary {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 62px;
      padding: 17px 20px;
      cursor: pointer;
      list-style: none;
    }}
    .source-disclosure summary::-webkit-details-marker {{
      display: none;
    }}
    .source-disclosure-title {{
      font-size: clamp(17px, 1.8vw, 21px);
      font-weight: 750;
      line-height: 1.2;
    }}
    .source-disclosure-action {{
      flex: 0 0 auto;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--brand-soft);
      color: var(--brand);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .source-disclosure[open] summary {{
      margin-bottom: 0;
      padding-bottom: 17px;
      border-bottom: 1px solid var(--line-subtle);
    }}
    .source-disclosure[open] .source-disclosure-action {{
      color: var(--text);
      background: var(--surface-subtle);
    }}
    .source-action-close {{ display: none; }}
    .source-disclosure[open] .source-action-open {{ display: none; }}
    .source-disclosure[open] .source-action-close {{ display: inline; }}
    .source-excerpts {{
      display: grid;
      gap: 18px;
      padding: 18px 20px 20px;
    }}
    .source-entry {{
      padding-top: 18px;
      border-top: 1px solid var(--line-subtle);
    }}
    .source-entry:first-child {{
      padding-top: 0;
      border-top: 0;
    }}
    .source-entry h3 {{
      margin: 0 0 8px;
      font-size: var(--av-text-base);
      line-height: 1.3;
    }}
    .sidebar-card {{
      position: sticky;
      top: 88px;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .section-card h2,
    .sidebar-card h2 {{
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.2;
    }}
    .richtext {{
      display: grid;
      gap: 12px;
    }}
    .richtext p {{
      margin: 0;
      max-width: 72ch;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      line-height: 1.68;
    }}
    .meta-grid {{
      display: grid;
      gap: 8px;
    }}
    .meta-item {{
      padding: 11px 0;
      border: 0;
      border-bottom: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }}
    .meta-item:first-child {{
      padding-top: 0;
      border-top: 0;
    }}
    .meta-item span {{
      display: block;
      margin-bottom: 4px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      text-transform: none;
      letter-spacing: 0;
    }}
    .meta-item strong {{
      font-size: var(--av-text-base);
      line-height: 1.4;
    }}
    .status-note {{
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .empty-state {{
      padding: 14px;
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
      color: var(--muted);
    }}
    .hero-action-status {{
      min-height: 18px;
      margin: 6px 0 0;
      color: var(--success);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }}
    .lifecycle-notice {{
      max-width: 720px;
      margin: 16px 0 0;
      padding: 11px 13px;
      border: 1px solid rgb(255 255 255 / .18);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / .08);
      color: #dbe7f5;
      font-size: 13px;
      line-height: 1.5;
    }}
    .verification-section {{
      display: grid;
      gap: 12px;
      margin-bottom: 12px;
      padding: 16px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-lg);
      background: var(--surface-wash-soft);
      box-shadow: var(--av-shadow-2xs);
    }}
    .verification-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .verification-head h2 {{
      margin: 0;
      font-size: clamp(17px, 2vw, 21px);
      line-height: 1.16;
    }}
    .verification-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .verification-list {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .verification-item {{
      display: grid;
      gap: 3px;
      min-height: 100%;
      padding: 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
    }}
    .verification-item strong {{
      font-size: var(--av-text-sm);
      line-height: 1.35;
    }}
    .verification-item span {{
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.48;
    }}
    .decision-check-section {{
      display: grid;
      gap: 18px;
      margin-top: 18px;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .decision-check-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .decision-check-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .decision-check-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .decision-check-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .decision-check-card {{
      display: grid;
      gap: 8px;
      min-height: 100%;
      padding: 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
    }}
    .decision-check-label {{
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .decision-check-card p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 18%);
      font-size: var(--av-text-sm);
      line-height: 1.5;
    }}
    .prepare-section {{
      display: grid;
      gap: 10px;
      margin-bottom: 12px;
      padding: 16px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-lg);
      background: var(--surface-wash-soft);
      box-shadow: var(--av-shadow-2xs);
    }}
    .prepare-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .prepare-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .prepare-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .prepare-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }}
    .prepare-card {{
      display: grid;
      gap: 6px;
      min-height: 0;
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-left: 3px solid color-mix(in oklab, var(--brand), white 36%);
      border-radius: var(--av-radius-md);
      background: var(--surface-wash-card);
      box-shadow: var(--av-shadow-2xs);
    }}
    .prepare-card:first-child {{ border-left-color: var(--brand); }}
    .prepare-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 24px;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .prepare-card h3 {{
      margin: 0;
      font-size: var(--av-text-base);
      line-height: 1.25;
    }}
    .prepare-card p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .apply-section {{
      display: grid;
      gap: 10px;
      margin-bottom: 12px;
      padding: 16px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-lg);
      background: var(--surface-wash-soft);
      box-shadow: var(--av-shadow-2xs);
    }}
    .apply-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .apply-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .apply-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .apply-list {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      padding: 0;
      margin: 0;
      list-style: none;
    }}
    .apply-step {{
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-left: 3px solid color-mix(in oklab, var(--success), white 34%);
      border-radius: var(--av-radius-md);
      background: var(--surface-wash-card);
    }}
    .apply-step:first-child {{ border-left-color: var(--success); }}
    .apply-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 24px;
      border-radius: 999px;
      background: color-mix(in oklab, var(--success), black 8%);
      color: white;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .apply-step h3 {{
      margin: 0 0 6px;
      font-size: var(--av-text-base);
      line-height: 1.25;
    }}
    .apply-step p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .related-section {{
      display: grid;
      gap: 18px;
      margin-top: 18px;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .related-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .related-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .related-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .related-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .related-card {{
      display: grid;
      gap: 10px;
      min-height: 100%;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .related-top,
    .related-meta {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .related-reason,
    .related-deadline {{
      display: inline-flex;
      align-items: center;
      min-height: var(--av-control-height-sm);
      padding: 0 10px;
      border-radius: 999px;
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: none;
      background: var(--surface-subtle);
      color: var(--muted);
    }}
    .related-card h3 {{
      margin: 0;
      font-size: var(--av-text-base);
      line-height: 1.22;
    }}
    .related-card h3 a:hover {{
      color: var(--brand);
    }}
    .related-summary {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 30%);
      font-size: var(--av-text-sm);
      line-height: 1.48;
    }}
    .related-meta {{
      margin-top: auto;
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }}
    .related-link {{
      color: var(--brand);
      font-weight: 700;
    }}
    .related-link:hover {{
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .site-footer {{
      display: grid;
      gap: 8px;
      margin-top: 18px;
      padding: 22px 24px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--surface);
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.5;
    }}
    .site-footer-nav {{
      display:flex;
      flex-wrap:wrap;
      gap:6px 16px;
      align-items:center;
      font-size:var(--av-text-xs);
      font-weight:650;
    }}
    .site-footer p {{ margin: 0; }}
    .site-footer a {{ color: var(--text); font-weight: 700; }}
    a:focus-visible, button:focus-visible {{
      outline:2px solid var(--brand);
      outline-offset:2px;
      border-radius:var(--av-radius-sm);
    }}
    @media (min-width:1440px) {{
      .hero-grid {{
        grid-template-columns:minmax(0,1.55fr) minmax(360px,.65fr);
        gap:64px;
      }}
      .content-grid--single .section-stack {{
        grid-template-columns:repeat(3,minmax(0,1fr));
        column-gap:32px;
      }}
      .prepare-grid,
      .related-grid {{ gap:16px; }}
      .readiness-grid {{ gap:16px; }}
    }}
    @media (min-width:2200px) {{
      .shell {{
        width: min(1920px, calc(100% - 160px));
      }}
      .hero-grid {{
        grid-template-columns: minmax(0, 1.35fr) minmax(420px, .65fr);
        gap: 72px;
      }}
      .hero h1 {{ max-width: 36ch; }}
      .summary {{ max-width: 78ch; }}
      .content-grid--single .section-stack > .section-card:not(.source-disclosure) {{
        grid-column: span 2;
      }}
      .richtext p {{ max-width: 90ch; }}
      .verification-head,
      .related-head {{ max-width: 920px; }}
    }}
    @media (max-width: 900px) {{
      .hero-grid,
      .content-grid,
      .prepare-grid,
      .decision-check-grid,
      .apply-list,
      .related-grid,
      .verification-list {{
        grid-template-columns: 1fr;
      }}
      .content-grid--single .section-stack {{ grid-template-columns: 1fr; }}
      .decision-support-head {{ display: grid; }}
      .decision-truth {{ min-width: 0; }}
      .profile-fit-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .hero-stats,
      .sidebar-card {{
        position: static;
        padding: 18px;
        border: 1px solid var(--line);
      }}
      .hero-stats {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px 14px;
      }}
      .hero-stats > div:first-child {{ grid-column: 1 / -1; }}
      .prepare-card,
      .prepare-card:first-child,
      .decision-check-card,
      .apply-step,
      .apply-step:first-child {{
        padding: 12px;
        border-left: 3px solid color-mix(in oklab, var(--brand), white 36%);
        border-top: 1px solid var(--line-subtle);
        border-radius: var(--av-radius-md);
        background: var(--surface-wash-card);
      }}
      .prepare-card:first-child {{ border-left-color: var(--brand); }}
      .apply-step,
      .apply-step:first-child {{
        border-left-color: color-mix(in oklab, var(--success), white 34%);
      }}
      .apply-step:first-child {{ border-left-color: var(--success); }}
    }}
    @media (max-width: 820px) {{
      .lang-switch a {{ min-width: 44px; min-height: 44px; }}
      .breadcrumbs a,
      .related-card h3 a,
      .related-link,
      .site-footer-nav a,
      .site-footer > p a {{ display: inline-flex; align-items: center; min-height: 44px; }}
      .site-footer-nav a {{ justify-content: center; min-width: 44px; }}
    }}
    @media (max-width: 640px) {{
      .hero-actions .button,
      .lang-switch a {{ min-height: var(--av-control-height-lg); }}
      .lang-switch a {{ min-width: var(--av-control-height-lg); }}
      .shell {{
        width: min(100%, calc(100% - 24px));
        padding: 14px 0 32px;
      }}
      .topbar {{
        top: 8px;
        padding: 8px 10px;
      }}
      .breadcrumbs span:last-child {{
        display: none;
      }}
      .hero {{
        padding: 22px 18px;
        border-radius: 20px;
      }}
      .hero {{ padding: 16px; }}
      .hero h1 {{
        font-size: 30px;
      }}
      .summary {{
        font-size: 14px;
      }}
      .hero-actions {{
        display: grid;
        grid-template-columns: 1fr;
      }}
      .hero-actions .button {{ width: 100%; }}
      .hero-stats {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .hero-stats > div:first-child {{ display: none; }}
      .hero-stats > div:nth-child(2) {{ grid-column: 1 / -1; }}
      .hero-stats strong {{
        font-size: 14px;
      }}
      .readiness-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .profile-fit-grid,
      .profile-fit-result ul {{ grid-template-columns: 1fr; }}
      .profile-fit-actions {{ align-items: flex-start; flex-direction: column; }}
      .prepare-head h2,
      .apply-head h2,
      .related-head h2 {{
        font-size: 18px;
      }}
    }}
{OPPORTUNITY_AVDS4_CSS}
{OPPORTUNITY_DETAIL_CSS}
  </style>
</head>
<body>
  <main class="shell" data-avds-component="opportunity-page">
    <div class="topbar">
      <nav class="breadcrumbs" aria-label="{escape(str(copy["breadcrumbs_aria"]), quote=True)}">
        <a class="site-brand" href="{catalog_href}">
          <span class="brand-mark brand-mark--compact">{BRAND_MARK_TEAL_HTML}</span>
          <strong>QAZ.FUND</strong>
        </a>
        <span>/</span>
        <a href="{catalog_href}">{escape(str(copy["opportunities_title"]))}</a>
        <span>/</span>
        <span>{escape(title)}</span>
      </nav>
      <nav class="lang-switch" aria-label="{escape(str(copy['language_switch']), quote=True)}">
        <a class="{kk_lang_class}" href="{kk_href}" lang="kk"{kk_lang_current}>KAZ</a>
        <a class="{ru_lang_class}" href="{ru_href}" lang="ru"{ru_lang_current}>RU</a>
        <a class="{en_lang_class}" href="{en_href}" lang="en"{en_lang_current}>EN</a>
      </nav>
    </div>
    {fallback_note_markup}

    <article class="opportunity-article" data-avds-component="opportunity-detail">
      <header class="opportunity-hero">
        <div class="opportunity-head">
          <span class="opportunity-kicker">{escape(format_text)}</span>
          <h1>{escape(title)}</h1>
          <p class="opportunity-summary">{escape(summary)}</p>
        </div>
        {lifecycle_notice_markup}
        {opportunity_facts}
        <div class="opportunity-actions">
          {application_button}
          <a class="{source_button_class}" href="{source_href}" target="_blank" rel="noopener">
            {escape(str(copy["detail_open_source"]))}
          </a>
          {prepare_button}
        </div>
      </header>

      <div class="opportunity-layout">
        <div class="opportunity-content">
          {highlights_markup}
          {eligibility_markup}
          {guidance_markup}
          {application_steps_markup}
          {content_markup}
        </div>
        {source_panel_markup}
      </div>
      {related_markup}
    </article>
    <footer class="site-footer site-footer--compact">
      <nav class="site-footer-nav" aria-label="{escape(str(copy["views_aria"]), quote=True)}">
        <a href="{catalog_href}">{escape(str(copy["tab_opportunities"]))}</a>
        <a href="{sources_href}">{escape(str(copy["tab_sources"]))}</a>
        <a href="{terms_href}">{escape(str(copy["terms_link"]))}</a>
        <a href="{data_policy_href}">{escape(str(copy["data_policy_link"]))}</a>
      </nav>
      <p>
        {escape(str(copy["footer_owner"]))}
        <a href="https://qdev.run">{escape(str(copy["footer_qdev"]))}</a>
        · <a class="footer-contact" href="mailto:contact@qaz.fund">contact@qaz.fund</a>
      </p>
      <p>{escape(str(copy["footer_disclaimer"]))}</p>
    </footer>
  </main>
</body>
</html>"""
