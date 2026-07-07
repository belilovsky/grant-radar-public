"""Server-rendered public dashboard shell for Grant Radar."""

from __future__ import annotations

import json
from html import escape
from typing import Any, Mapping, cast

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url

SUPPORTED_LANGS = {"ru", "en"}
GOOGLE_SITE_VERIFICATION_FILENAME = "google6ce0cb641d438c0c.html"
GOOGLE_SITE_VERIFICATION_CONTENT = (
    f"google-site-verification: {GOOGLE_SITE_VERIFICATION_FILENAME}"
)
YANDEX_SITE_VERIFICATION_TOKEN = "01df12ab51cd6b70"  # nosec B105

COPY = {
    "ru": {
        "lang": "ru",
        "locale": "ru-KZ",
        "title": "QAZ.FUND — гранты и меры поддержки для Казахстана",
        "meta_description": (
            "QAZ.FUND — публичный навигатор по грантам, субсидиям, акселераторам "
            "и программам поддержки для Казахстана."
        ),
        "eyebrow": "Казахстанский навигатор",
        "headline": "QAZ.FUND",
        "subtitle": (
            "Публичный навигатор по грантам, субсидиям, акселераторам и "
            "программам поддержки для Казахстана."
        ),
        "hero_intro": (
            "Находите гранты, субсидии и программы поддержки для стартапов, "
            "бизнеса, фермеров, НКО и исследовательских команд без ручного "
            "обхода десятков сайтов."
        ),
        "hero_primary_cta": "Открыть каталог",
        "hero_secondary_cta": "Стартапам",
        "hero_tertiary_cta": "Субсидии РК",
        "hero_stage_eyebrow": "Почему сюда возвращаются",
        "hero_stage_title": "Один адрес вместо десятков разрозненных источников",
        "hero_stage_point_one": "Официальные и отобранные источники в одной публичной витрине",
        "hero_stage_point_two": "Локальная карточка, быстрая оценка и фильтры по сроку и региону",
        "hero_stage_point_three": "Казахстан в приоритете, но без потери международных программ",
        "hero_picks_label": "Быстрый старт",
        "hero_pick_startup": "Гранты для стартапов",
        "hero_pick_business": "Поддержка бизнеса",
        "hero_pick_farmer": "Фермерам",
        "hero_pick_science": "Исследователям",
        "hero_pick_tenders": "Тендеры",
        "spotlight_section_eyebrow": "Подборки для старта",
        "spotlight_section_title": "С чего начать просмотр",
        "spotlight_section_description": (
            "Живые маршруты по каталогу: горячие возможности, Казахстан в приоритете "
            "и прикладные меры поддержки."
        ),
        "spotlight_count": "В подборке: {count}",
        "spotlight_action_open": "Открыть подборку",
        "spotlight_empty": "Подходящие карточки появятся здесь после загрузки каталога.",
        "spotlight_preview_more": "+ ещё {count}",
        "spotlight_trending_kicker": "Популярно сейчас",
        "spotlight_trending_title": "Лучшие сигналы недели",
        "spotlight_trending_note": (
            "Высокая релевантность и живые программы, которые стоит открыть первыми."
        ),
        "spotlight_kazakhstan_kicker": "Казахстан в приоритете",
        "spotlight_kazakhstan_title": "Фокус на локальные возможности",
        "spotlight_kazakhstan_note": (
            "Гранты и программы с прямым сигналом по Казахстану и местным условиям."
        ),
        "spotlight_support_kicker": "Госсектор и субсидии",
        "spotlight_support_title": "Поддержка для бизнеса и команд",
        "spotlight_support_note": (
            "Субсидии, льготы и инструменты поддержки, где важны прикладные условия."
        ),
        "spotlight_deadline_kicker": "Скоро закрываются",
        "spotlight_deadline_title": "Не тянуть с подачей",
        "spotlight_deadline_note": (
            "Возможности с ближайшим сроком, которые лучше просмотреть сейчас."
        ),
        "pathways_section_eyebrow": "Маршруты по задачам",
        "pathways_section_title": "Куда идти вашему проекту",
        "pathways_section_description": (
            "Короткие входы для тех, кто ищет не просто список, а понятный старт "
            "под свой тип проекта."
        ),
        "pathways_count": "Сейчас: {count}",
        "pathways_action_open": "Открыть направление",
        "pathways_empty": "После обновления каталога здесь появятся подходящие карточки.",
        "pathway_startup_kicker": "Стартапам",
        "pathway_startup_title": "Акселераторы, гранты и облачные кредиты",
        "pathway_startup_note": (
            "Для продуктовых команд, ИИ-стартапов и тех, кто ищет быстрый путь к "
            "пилотам и ресурсам."
        ),
        "pathway_business_kicker": "Бизнесу",
        "pathway_business_title": "Субсидии, льготы и меры поддержки РК",
        "pathway_business_note": (
            "Для ИП, ТОО и операционного бизнеса, где важны локальные условия и "
            "механика подачи."
        ),
        "pathway_farmer_kicker": "Фермерам",
        "pathway_farmer_title": "Агро, животноводство и прикладные технологии",
        "pathway_farmer_note": (
            "Для хозяйств и агрокоманд, которым нужны программы с прямой "
            "практической пользой."
        ),
        "pathway_science_kicker": "Исследователям",
        "pathway_science_title": "Наука, коммерциализация и научные гранты",
        "pathway_science_note": (
            "Для университетов, лабораторий и команд, которые ищут финансирование под "
            "исследования и внедрение."
        ),
        "themes_section_eyebrow": "Темы для навигации",
        "themes_section_title": "Какой поток вам ближе",
        "themes_section_description": (
            "Быстрые входы по направлениям: можно сразу уйти в свою тему, не "
            "просматривая весь каталог подряд."
        ),
        "themes_count": "Сейчас: {count}",
        "themes_action_open": "Открыть тему",
        "themes_empty": "Подходящие карточки появятся здесь после обновления каталога.",
        "funder_section_eyebrow": "Фонды и доноры",
        "funder_section_title": "Кто сейчас реально активен",
        "funder_section_description": (
            "Сводка по фондам и программам: где есть живые возможности, какие "
            "темы они обычно поддерживают и куда смотреть дальше."
        ),
        "funder_open_profile": "Профиль фонда",
        "funder_empty": "Профили фондов появятся после загрузки каталога.",
        "funder_live_now": "Живые возможности",
        "funder_overview_intro": "Обычно поддерживает гранты и программы.",
        "funder_overview_topics": "Основные темы: {topics}.",
        "funder_overview_regions": "Фокус по регионам: {regions}.",
        "funder_page_eyebrow": "Профиль фонда",
        "funder_focus_title": "Что обычно поддерживается",
        "funder_focus_note": (
            "Собрали профиль по текущему индексу: форматы, регионы и рабочие "
            "темы без ручного просмотра всех карточек по одной."
        ),
        "funder_focus_types": "Форматы",
        "funder_focus_regions": "Регионы",
        "funder_focus_indexed": "В индексе",
        "funder_live_title": "Живые и рабочие возможности",
        "funder_live_note": (
            "Открытые, бессрочные и прогнозные записи, которые можно брать в работу."
        ),
        "funder_live_empty": "Сейчас у этого фонда нет открытых или прогнозных записей.",
        "funder_archive_title": "Архив и исторический след",
        "funder_archive_note": (
            "Закрытые и завершённые записи полезны для понимания ритма и профиля фонда."
        ),
        "funder_archive_empty": "Архивных записей пока не накопилось.",
        "funder_sources_title": "Откуда собран профиль",
        "funder_sources_note": "Официальные источники и страницы, из которых строится профиль.",
        "funder_back_to_catalog": "Вернуться в каталог",
        "funder_open_card": "Открыть карточку",
        "topic_brief_eyebrow": "В фокусе сейчас",
        "topic_brief_count": "В срезе: {count}",
        "topic_brief_what": "Что здесь обычно ищут",
        "topic_brief_best_for": "Лучше всего подходит",
        "topic_brief_reset": "Убрать тему",
        "topic_ai_best": "Продуктовым командам, ИИ-стартапам и цифровым инициативам.",
        "topic_ai_focus_1": "ИИ-пилоты и акселераторы",
        "topic_ai_focus_2": "Облачные кредиты и инфраструктура",
        "topic_ai_focus_3": "Цифровые навыки и прикладные программы",
        "topic_agro_best": "Фермерам, агрономам и проектам на стыке воды, климата и отраслей.",
        "topic_agro_focus_1": "Субсидии и отраслевые меры",
        "topic_agro_focus_2": "Вода, климат и устойчивость",
        "topic_agro_focus_3": "Животноводство, ветеринария и прикладные агротехнологии",
        "topic_science_best": "Университетам, лабораториям и исследовательским командам.",
        "topic_science_focus_1": "Коммерциализация исследований",
        "topic_science_focus_2": "Научные гранты, лаборатории и академическая мобильность",
        "topic_science_focus_3": "Образовательные и университетские треки",
        "topic_public_best": "Командам, работающим с госсектором, закупками и инфраструктурой.",
        "topic_public_focus_1": "Закупки, тендеры и запросы предложений",
        "topic_public_focus_2": "Программы развития и реализация",
        "topic_public_focus_3": "Гостех и крупные проектные линии",
        "topic_business_best": "ИП, ТОО и операционному бизнесу в Казахстане.",
        "topic_business_focus_1": "Локальные субсидии и меры РК",
        "topic_business_focus_2": "Льготы, гарантии и финансирование",
        "topic_business_focus_3": "Поддержка для МСБ, экспорта и роста",
        "topic_ngo_best": "НКО, медиа и гражданским командам с социальным эффектом.",
        "topic_ngo_focus_1": "Медиа, журналистика и общественно значимые проекты",
        "topic_ngo_focus_2": "Гранты для гражданского сектора и партнерства",
        "topic_ngo_focus_3": "Сообщество и программы с социальным эффектом",
        "theme_ai_kicker": "ИИ и цифровые решения",
        "theme_ai_title": "ИИ, облачные кредиты и цифровые навыки",
        "theme_ai_note": (
            "Для команд, которые ищут ИИ-программы, инфраструктуру, кредиты и "
            "цифровые инициативы."
        ),
        "theme_agro_kicker": "Агро / вет / эко",
        "theme_agro_title": "Агро, вода, климат и прикладной сектор",
        "theme_agro_note": (
            "Для ферм, агрокоманд и проектов на стыке устойчивости, воды и "
            "прикладных отраслей."
        ),
        "theme_science_kicker": "Образование и наука",
        "theme_science_title": "Наука, образование и коммерциализация",
        "theme_science_note": (
            "Для университетов, лабораторий и образовательных команд, которым "
            "нужны гранты и исследовательские треки."
        ),
        "theme_public_kicker": "Госсектор и инфраструктура",
        "theme_public_title": "Инфраструктура, закупки и программы развития",
        "theme_public_note": (
            "Для команд, работающих с госзаказом, закупками и крупными "
            "программами развития."
        ),
        "theme_business_kicker": "Бизнес и субсидии",
        "theme_business_title": "Субсидии, льготы и меры поддержки бизнеса",
        "theme_business_note": (
            "Для МСБ и операционных компаний, где важны локальные условия и "
            "механика подачи."
        ),
        "theme_ngo_kicker": "Медиа и НКО",
        "theme_ngo_title": "Медиа, гражданский сектор и социальный эффект",
        "theme_ngo_note": (
            "Для НКО, медиа и общественных проектов, которым нужны гранты и "
            "партнерские треки."
        ),
        "focus_aria": "Текущий продуктовый фокус",
        "focus_primary": "Приоритет: Казахстан и ЦА",
        "focus_secondary": "Темы: ИИ, образование, госсектор, агро, вет, эко, медиа",
        "status_checking": "Проверяем свежесть данных",
        "api_docs": "API",
        "methodology_link": "Как это работает",
        "status_link": "Статус данных",
        "language_switch": "Язык интерфейса",
        "nav_aria": "Разделы радара",
        "tab_opportunities": "Возможности",
        "tab_sources": "Источники",
        "tab_health": "Статус",
        "metrics_aria": "Сводные метрики",
        "metric_total": "В индексе",
        "metric_relevant": "Актуально сейчас",
        "metric_sources": "Источники",
        "opportunities_title": "Возможности",
        "opportunities_description": (
            "Открытые и бессрочные программы с приоритетом показа для Казахстана "
            "и Центральной Азии."
        ),
        "opportunities_description_all": (
            "Открытые, бессрочные и архивные записи индекса для аудита покрытия "
            "и источников."
        ),
        "search_label": "Поиск",
        "search_placeholder": "Название, фонд, теги, регион",
        "audience_label": "Для кого",
        "audience_aria": "Подборка по типу заявителя",
        "audience_all": "Все",
        "audience_startup": "Стартапам",
        "audience_business": "Бизнесу",
        "audience_farmer": "Фермерам",
        "audience_ngo": "НКО",
        "audience_science": "Исследователям",
        "format_label": "Что ищете",
        "format_aria": "Подборка по типу поддержки",
        "format_all": "Все форматы",
        "format_grants": "Гранты и конкурсы",
        "format_support": "Субсидии и меры",
        "format_accelerators": "Акселераторы и кредиты",
        "format_tenders": "Тендеры и закупки",
        "topic_label": "Тема",
        "topic_aria": "Подборка по направлению",
        "topic_all": "Все темы",
        "topic_ai": "ИИ и цифровые решения",
        "topic_agro": "Агро / вет / эко",
        "topic_science": "Образование и наука",
        "topic_public": "Госсектор и инфраструктура",
        "topic_ngo": "Медиа и НКО",
        "topic_business": "Бизнес и субсидии",
        "scope_label": "Покрытие",
        "scope_aria": "Покрытие списка",
        "scope_open": "Открытые",
        "scope_all": "Весь индекс",
        "lifecycle_label": "Стадия",
        "lifecycle_aria": "Жизненный цикл возможности",
        "lifecycle_all": "Любая стадия",
        "lifecycle_open": "Открыто сейчас",
        "lifecycle_forecast": "Прогноз / в планировании",
        "lifecycle_closing_soon": "Скоро закрывается",
        "lifecycle_rolling": "Бессрочно",
        "lifecycle_closed": "Закрыто",
        "lifecycle_awarded": "Завершено",
        "region_label": "Регион",
        "region_aria": "Регион подачи",
        "region_all": "Все регионы",
        "region_kazakhstan": "Казахстан",
        "region_central_asia": "Центральная Азия",
        "region_global": "Международные",
        "deadline_filter_label": "Срок",
        "deadline_filter_aria": "Срок подачи",
        "deadline_filter_all": "Любые сроки",
        "deadline_filter_soon": "Скоро закрываются",
        "deadline_filter_month": "В ближайший месяц",
        "deadline_filter_rolling": "Бессрочные",
        "sort_label": "Сортировка",
        "sort_aria": "Порядок показа возможностей",
        "sort_priority": "Лучшее совпадение",
        "sort_deadline": "Ближайший дедлайн",
        "sort_updated": "Недавно обновленные",
        "min_score_label": "Точность совпадения",
        "min_score_aria": "Точность совпадения",
        "source_label": "Источник",
        "source_aria": "Источник",
        "all_scores": "Все результаты",
        "score_option_03": "Базовое совпадение",
        "score_option_05": "Высокое совпадение",
        "score_option_07": "Только точные",
        "all_sources": "Все источники",
        "clear_filters": "Сбросить фильтры",
        "loading_opportunities": "Загружаем возможности...",
        "load_more": "Показать ещё",
        "sources_title": "Покрытие источников",
        "sources_description": (
            "Прямые адаптеры и отобранные страницы мониторинга, которые сейчас "
            "подключены к радару."
        ),
        "loading_sources": "Загружаем покрытие источников...",
        "show_all_sources": "Показать все источники",
        "show_fewer_sources": "Показать меньше",
        "health_title": "Статус данных",
        "health_description": (
            "Показываем, что каталог доступен и сколько источников сейчас участвует "
            "в витрине."
        ),
        "health_ok_value": "Данные актуальны",
        "health_attention_value": "Проверить",
        "health_note_loading": "Проверяем витрину и время последнего обновления...",
        "health_note_ready": (
            "Витрина проверена {checked_at}. Последнее обновление карточек: {updated_at}."
        ),
        "health_note_ready_no_items": (
            "Витрина проверена {checked_at}. Новые карточки появятся после следующего "
            "обхода источников."
        ),
        "reload_live_data": "Обновить данные",
        "api_status": "Поток данных",
        "stored_items": "Записей в каталоге",
        "health_sources": "Активные источники",
        "api_online": "Данные актуальны",
        "api_failed": "Нужна проверка данных",
        "api_error": "Ошибка загрузки данных",
        "source_catalog_unavailable": "Каталог источников сейчас недоступен.",
        "showing_sources": "Показываем {shown} из {total} источников",
        "sources_connected": "Подключено источников: {total}",
        "show_all_sources_with_total": "Показать все {total} источников",
        "coverage_unavailable": "Покрытие недоступно",
        "indexed_count": "В индексе: {count}",
        "relevant_open_count": "Релевантных открытых: {count}",
        "direct_badge": "Прямой",
        "watchlist_badge": "Мониторинг",
        "source_direct_note": "Прямое подключение к официальному источнику",
        "source_watchlist_note": "Внешний мониторинг и редакционная выборка",
        "regional_badge_kazakhstan": "Казахстан в приоритете",
        "regional_badge_central_asia": "Центральная Азия",
        "summary_matches": "Совпадений: {count}",
        "summary_search": "Поиск: {value}",
        "summary_audience": "Для кого: {value}",
        "summary_format": "Формат: {value}",
        "summary_topic": "Тема: {value}",
        "summary_lifecycle": "Стадия: {value}",
        "summary_region": "Регион: {value}",
        "summary_deadline": "Срок: {value}",
        "summary_sort": "Сортировка: {value}",
        "summary_score": "Точность: {value}",
        "summary_scope_all": "Включая архив",
        "methodology_title": "Как мы собираем и показываем данные",
        "methodology_description": (
            "Коротко объясняем, откуда берется каталог, что означает совпадение и "
            "что нужно обязательно перепроверять перед подачей."
        ),
        "method_card_sources_title": "Источники и обновление",
        "method_card_sources_text": (
            "Каталог собирается из официальных источников, открытых реестров и "
            "отобранных страниц мониторинга. Мы регулярно перепроверяем ссылки, "
            "дедлайны и наличие активных карточек."
        ),
        "method_card_relevance_title": "Почему карточка показана",
        "method_card_relevance_text": (
            "Порядок выдачи учитывает Казахстан и Центральную Азию, тему, формат, "
            "дедлайн и признаки того, кому программа подходит. Это рабочая "
            "эвристика, а не юридическая классификация."
        ),
        "method_card_trust_title": "Что считать финальной версией",
        "method_card_trust_text": (
            "QAZ.FUND помогает быстро найти и структурировать возможность, но "
            "финальные условия, формы и требования всегда нужно сверять на "
            "официальном сайте программы."
        ),
        "method_disclaimer_title": "Важно перед подачей",
        "method_disclaimer_text": (
            "Если карточка выглядит подходящей, откройте официальный источник и "
            "проверьте дедлайн, eligibility, состав документов и способ отправки "
            "заявки."
        ),
        "faq_title": "Частые вопросы",
        "faq_q1": "QAZ.FUND сам выдает гранты?",
        "faq_a1": (
            "Нет. Платформа агрегирует и упорядочивает возможности, а подача всегда "
            "происходит через официальный источник программы."
        ),
        "faq_q2": "Как часто обновляются данные?",
        "faq_a2": (
            "Мы регулярно перепроверяем индекс и состояние подключенных источников. "
            "Для оперативной оценки смотрите блок со статусом данных и последнее "
            "обновление витрины."
        ),
        "faq_q3": "Что означает точность совпадения?",
        "faq_a3": (
            "Это не оценка качества программы, а порог того, насколько карточка "
            "совпадает с выбранной темой, регионом, форматом и фокусом QAZ.FUND."
        ),
        "faq_q4": "Почему в выдаче бывают меры поддержки рядом с грантами?",
        "faq_a4": (
            "Некоторые программы юридически оформлены как мера поддержки или "
            "субсидия, но по смыслу полезны той же аудитории. Мы показываем их, "
            "если они действительно подходят по задаче."
        ),
        "collections_label": "Подборки",
        "collections_aria": "Сохранённые подборки и ссылки для повторного просмотра",
        "collections_empty": "Сохраните текущий набор фильтров, чтобы быстро возвращаться к нему.",
        "save_view": "Сохранить подборку",
        "share_view": "Скопировать ссылку",
        "saved_view_saved": "Подборка сохранена локально.",
        "saved_view_removed": "Подборка удалена.",
        "saved_view_shared": "Ссылка на текущую подборку скопирована.",
        "saved_view_default_name": "Моя подборка",
        "saved_view_remove_aria": "Удалить подборку",
        "saved_view_status_label": "Статус подборок",
        "saved_view_share_prompt": "Скопируйте ссылку на текущую подборку",
        "view_funder": "Профиль фонда",
        "fit_label": "Кому подходит",
        "fit_unknown": "Критерии нужно уточнить",
        "fit_deadline_soon": "Скоро закрывается",
        "fit_global": "Глобальная подача",
        "signal_label": "Почему это в фокусе",
        "signal_support_kz": (
            "Локальная мера поддержки для команд и бизнеса в Казахстане с "
            "практическими условиями подачи."
        ),
        "signal_public_sector": (
            "Подходит командам, которые работают с госсектором, инфраструктурой "
            "или крупными программами развития."
        ),
        "signal_business": (
            "Практическая возможность для бизнеса, где важны условия, пакет "
            "документов и механика подачи."
        ),
        "signal_startup": (
            "Полезно продуктовым и ИИ-командам, которым важны акселерация, "
            "пилоты или облачные кредиты."
        ),
        "signal_tender": (
            "Стоит быстро проверить требования к участнику, объем работ и состав заявки."
        ),
        "signal_science": (
            "Есть научный или коммерциализационный сигнал для университетов, "
            "лабораторий и научных команд."
        ),
        "signal_farmer": (
            "Есть прикладной агро-сигнал для хозяйств, ферм и отраслевых команд."
        ),
        "signal_ngo": (
            "Полезно НКО, медиа и командам с гражданским или социальным профилем."
        ),
        "signal_kazakhstan": (
            "Есть прямой сигнал по Казахстану или локальным условиям подачи."
        ),
        "signal_central_asia": (
            "Подходит проектам из Центральной Азии без узкой привязки к одной стране."
        ),
        "signal_global": (
            "Международная возможность, которую стоит проверить по критериям "
            "для вашей команды."
        ),
        "meta_format_label": "Формат",
        "meta_region_label": "Регион",
        "meta_deadline_label": "Срок",
        "meta_region_kazakhstan": "РК в приоритете",
        "meta_region_central_asia": "Центр. Азия",
        "meta_region_global": "Международно",
        "meta_deadline_rolling": "Без срока",
        "meta_deadline_soon_days": "Через {count} дн.",
        "meta_deadline_month": "До месяца",
        "meta_deadline_later": "Срок указан",
        "detail_fit_title": "Быстрая оценка",
        "detail_source_status_title": "Статус источника",
        "detail_fit_good": "Скорее всего подходит",
        "detail_fit_review": "Нужна ручная проверка критериев",
        "no_indexed_items": "Пока нет проиндексированных возможностей.",
        "no_filtered_items": "По текущим фильтрам ничего не найдено.",
        "no_filtered_items_hint": (
            "Попробуйте ослабить один из фильтров — каталог сразу пересчитает выдачу."
        ),
        "empty_action_clear": "Сбросить всё",
        "empty_action_region": "Все регионы",
        "empty_action_deadline": "Любые сроки",
        "empty_action_score": "Стандартный порог",
        "empty_action_scope": "Открыть весь индекс",
        "open_details": "Подробнее",
        "read_more": "Официальный источник",
        "open_rolling": "Открыто / бессрочно",
        "score_title": "Оценка релевантности по эвристикам QAZ.FUND",
        "source_agency": "Источник: {agency}",
        "no_summary": "Источник не передал краткое описание.",
        "reload_confirm": "Перечитать live-данные из всех источников?",
        "results_button": "Показать ещё {count}",
        "unknown_url": "URL недоступен",
        "views_aria": "Навигация по разделам панели",
        "breadcrumbs_aria": "Навигационная цепочка",
        "detail_panel_label": "Локальная карточка возможности",
        "detail_shell_title": "Локальная карточка",
        "detail_title_fallback": "Карточка возможности",
        "detail_loading": "Подтягиваем локальный текст и параметры...",
        "detail_error": (
            "Локальная карточка сейчас недоступна. Ниже оставили прямой путь к источнику."
        ),
        "detail_empty": (
            "Источник пока не отдал расширенный текст. Показываем краткое описание "
            "и структурированные поля."
        ),
        "detail_close": "Закрыть",
        "detail_open_page": "Открыть страницу",
        "detail_all_opportunities": "Все возможности",
        "detail_open_source": "Открыть источник",
        "detail_open_application": "Открыть подачу",
        "detail_meta_title": "Параметры",
        "detail_sections_title": "Текст и выдержки",
        "detail_status_ok": "Описание и ключевые поля собраны с официального источника",
        "detail_status_structured_only": "Показываем краткое описание и структурированные поля",
        "detail_status_blocked": "Источник не дал забрать полный текст автоматически",
        "detail_status_not_allowed": "Для этого источника локальная загрузка отключена",
        "detail_status_too_large": "Страница слишком тяжелая для локального чтения",
        "detail_status_unsupported_media": "Источник отдал неподдерживаемый формат",
        "detail_status_parse_error": "Не удалось корректно разобрать страницу источника",
        "detail_source_excerpt": "Выдержка с источника",
        "prepare_section_eyebrow": "Перед подачей",
        "prepare_section_title": "Что подготовить",
        "prepare_section_description": (
            "Короткий практический чек-лист по типу возможности. Финальные "
            "требования все равно сверяйте с официальным источником."
        ),
        "prepare_eligibility_title": "Проверьте критерии",
        "prepare_eligibility_text": (
            "Сверьте страну, тип заявителя, ограничения по отрасли и язык подачи."
        ),
        "prepare_deadline_title": "Зафиксируйте срок",
        "prepare_deadline_text": (
            "Оставьте запас на регистрацию, подписи, письма поддержки и загрузку "
            "документов."
        ),
        "prepare_rolling_title": "Проверьте актуальность",
        "prepare_rolling_text": (
            "У бессрочных программ условия могут меняться без отдельного срока."
        ),
        "prepare_grant_title": "Соберите проектную заявку",
        "prepare_grant_text": (
            "Нужны проблема, решение, бюджет, команда, результаты и план внедрения."
        ),
        "prepare_tender_title": "Проверьте пакет закупки",
        "prepare_tender_text": (
            "Сверьте объем работ, квалификацию, форму подачи, гарантии и обязательные "
            "приложения."
        ),
        "prepare_startup_title": "Подготовьте презентацию проекта",
        "prepare_startup_text": (
            "Соберите презентацию, описание продукта, показатели роста, команду "
            "и сценарий пилота."
        ),
        "prepare_subsidy_title": "Подготовьте локальные документы",
        "prepare_subsidy_text": (
            "Проверьте ИП/ТОО, ЭЦП, налоговый статус, банковские реквизиты и "
            "подтверждающие документы."
        ),
        "prepare_science_title": "Соберите исследовательский пакет",
        "prepare_science_text": (
            "Нужны научная новизна, команда, календарный план, бюджет и путь "
            "коммерциализации."
        ),
        "prepare_ngo_title": "Проверьте логику эффекта",
        "prepare_ngo_text": (
            "Сформулируйте бенефициаров, социальный эффект, партнеров и план "
            "отчетности."
        ),
        "prepare_source_title": "Сверьте официальный источник",
        "prepare_source_text": (
            "Перед подачей проверьте последнюю версию условий, форм и контактных "
            "данных."
        ),
        "apply_section_eyebrow": "Подача",
        "apply_section_title": "Как подать",
        "apply_section_description": (
            "Короткий маршрут до отправки заявки. Он помогает не потерять шаги, "
            "но не заменяет официальную инструкцию источника."
        ),
        "apply_step_open_apply_title": "Откройте страницу подачи",
        "apply_step_open_apply_text": (
            "Если у программы есть отдельная форма подачи, начинайте с нее и "
            "сверьте требования на этой странице."
        ),
        "apply_step_open_source_title": "Откройте официальный источник",
        "apply_step_open_source_text": (
            "На источнике проверьте актуальные условия, контакты и формат отправки."
        ),
        "apply_step_check_title": "Сверьте критерии",
        "apply_step_check_text": (
            "Проверьте страну, тип организации, отрасль, возраст проекта и "
            "ограничения по участникам."
        ),
        "apply_step_pack_title": "Соберите пакет",
        "apply_step_pack_text": (
            "Подготовьте описание проекта, бюджет, подтверждающие документы и "
            "письма поддержки, если они нужны."
        ),
        "apply_step_submit_title": "Отправьте и сохраните подтверждение",
        "apply_step_submit_text": (
            "После отправки сохраните номер заявки, копию письма или снимок "
            "экрана с подтверждением."
        ),
        "related_section_eyebrow": "Продолжить просмотр",
        "related_section_title": "Похожие возможности",
        "related_section_description": (
            "Еще несколько близких карточек из того же потока, чтобы не возвращаться "
            "в каталог вслепую."
        ),
        "related_reason_source": "Тот же источник",
        "related_reason_funder": "Похожий фонд",
        "related_reason_theme": "Близкая тема",
        "related_reason_format": "Похожий формат",
        "related_open": "Открыть карточку",
        "detail_meta_labels": {
            "source": "Источник",
            "funder": "Фонд",
            "deadline": "Срок подачи",
            "deadline_raw": "Срок с источника",
            "deadline_policy": "Правило срока",
            "amount": "Объем поддержки",
            "amount_raw": "Объем с источника",
            "project_id": "Номер проекта",
            "reference": "Номер объявления",
            "status": "Статус",
            "notice_type": "Тип объявления",
            "borrower": "Заемщик",
            "country": "Страна",
            "region": "Регион",
            "board_approval": "Одобрение советом",
            "closing_date": "Дата закрытия",
            "page_title": "Заголовок источника",
            "application_url": "Путь подачи",
            "status_note": "Статус загрузки",
        },
        "label_map": {
            "ai": "ИИ",
            "edtech": "Образовательные технологии",
            "govtech": "Гостех",
            "agrotech": "Агротехнологии",
            "vettech": "Веттехнологии",
            "ecotech": "Экотехнологии",
            "animal_health": "Веттехнологии",
            "climate": "Экотехнологии",
            "ngo": "НКО",
            "unesco": "UNESCO",
            "unicef": "UNICEF",
            "adb": "ADB",
            "aws": "AWS",
            "eeas": "EEAS",
            "microsoft": "Microsoft",
            "nvidia": "NVIDIA",
            "mongodb": "MongoDB",
            "central_asia_eligible": "Центральная Азия",
            "google_cloud_startup": "Google Cloud для стартапов",
            "google_org_ai_opportunity": "Google.org AI Opportunity Fund",
            "microsoft_founders_hub": "Microsoft Founders Hub",
            "world_bank_kazakhstan": "Всемирный банк Казахстан",
            "adb_kazakhstan": "АБР Казахстан",
            "eeas_kazakhstan": "Представительство ЕС в Казахстане",
            "unicef_kazakhstan": "UNICEF Казахстан",
            "unesco_iite": "UNESCO IITE",
            "isdb_project_procurement": "IsDB Procurement",
            "ebrd_ecepp_procurement": "EBRD ECEPP Procurement",
            "undp_procurement": "UNDP Procurement",
            "kazakhstan": "Казахстан",
            "central_asia": "Центральная Азия",
            "global": "Глобально",
            "education": "Образование",
            "digital_skills": "Цифровые навыки",
            "development": "Развитие",
            "project_pipeline": "Портфель проектов",
            "public_sector": "Госсектор",
            "startup_support": "Поддержка стартапов",
            "cloud_credits": "Облачные кредиты",
            "world_bank": "Всемирный банк",
            "europe_and_central_asia": "Европа и Центральная Азия",
            "republic_of_kazakhstan": "Республика Казахстан",
            "google": "Google",
            "azure": "Azure",
            "media": "Медиа",
            "journalism": "Журналистика",
            "open_data": "Открытые данные",
            "startup": "Стартап",
            "grant": "Грант",
            "accelerator": "Акселератор",
            "cloud_credit": "Облачный кредит",
            "tender": "Тендер",
            "contest": "Конкурс",
            "fellowship": "Стажировка",
            "open": "Открыто",
            "forecast": "Прогноз",
            "closing_soon": "Скоро закрывается",
            "rolling": "Бессрочно",
            "closed": "Закрыто",
            "awarded": "Завершено",
            "green_transition": "Экотехнологии",
            "climate_change": "Экотехнологии",
            "innovation": "Инновации",
            "commercialization": "Коммерциализация",
            "subsidy": "Субсидия",
            "sme": "МСБ",
            "business_support": "Поддержка бизнеса",
            "domestic_support": "Поддержка РК",
            "state_program": "Госпрограмма",
            "preferential_financing": "Льготное финансирование",
            "loan_guarantee": "Гарантия займа",
            "tax_benefit": "Налоговая льгота",
            "reimbursement": "Возмещение затрат",
            "leasing": "Лизинг",
            "employment": "Занятость",
            "industry": "Промышленность",
            "export": "Экспорт",
            "trade": "Торговля",
            "investment": "Инвестиции",
            "science": "Наука",
            "civil_society": "Гражданский сектор",
            "crop_production": "Растениеводство",
            "livestock": "Животноводство",
            "digitalization": "Цифровизация",
            "qazinnovations": "QazInnovations",
            "egov": "eGov",
            "damu": "Даму",
            "enbek": "Енбек",
            "gosagro": "Gosagro",
            "govkz": "Gov.kz",
            "ncste": "NCSTE",
            "science_fund": "Фонд науки",
            "cisc": "CISC",
            "qazindustry": "QazIndustry",
            "qaztrade": "QazTrade",
            "invest_gov": "KAZAKH INVEST",
            "baiterek": "Байтерек",
            "bgov": "BGov",
            "kazagrofinance": "KazAgroFinance",
            "agrocredit": "AgroCredit",
            "kazakhexport": "KazakhExport",
            "kdb": "БРК",
            "idf": "ФРП",
            "qic": "QIC",
            "private_equity": "Прямые инвестиции",
            "venture": "Венчур",
            "grants_gov": "Grants.gov",
            "fundsforngos": "FundsforNGOs",
            "opportunity_desk": "Opportunity Desk",
            "astana_hub": "Astana Hub",
            "kazakhstan_domestic_support": "Поддержка РК",
            "kazakhstan_watch": "Мониторинг Казахстана",
            "cloudflare_startups": "Cloudflare Startups",
            "mongodb_startups": "MongoDB Startups",
            "nvidia_inception": "NVIDIA Inception",
        },
    },
    "en": {
        "lang": "en",
        "locale": "en-KZ",
        "title": "QAZ.FUND — funding and support programs for Kazakhstan",
        "meta_description": (
            "QAZ.FUND is a public funding navigator for grants, subsidies, "
            "accelerators, and support programs in Kazakhstan."
        ),
        "eyebrow": "Kazakhstan funding navigator",
        "headline": "QAZ.FUND",
        "subtitle": (
            "Public funding navigator for grants, subsidies, accelerators, "
            "and support programs in Kazakhstan."
        ),
        "hero_intro": (
            "Find grants, subsidies, and support programs for startups, "
            "businesses, farms, NGOs, and research teams without checking "
            "dozens of separate sites by hand."
        ),
        "hero_primary_cta": "Open catalog",
        "hero_secondary_cta": "For startups",
        "hero_tertiary_cta": "Kazakhstan support",
        "hero_stage_eyebrow": "Why people stay here",
        "hero_stage_title": "One address instead of dozens of fragmented sources",
        "hero_stage_point_one": "Official and curated sources in one public feed",
        "hero_stage_point_two": "Local detail view, fit check, and deadline and region filters",
        "hero_stage_point_three": "Kazakhstan first, without losing useful global programs",
        "hero_picks_label": "Quick start",
        "hero_pick_startup": "Startup grants",
        "hero_pick_business": "Business support",
        "hero_pick_farmer": "For farmers",
        "hero_pick_science": "For researchers",
        "hero_pick_tenders": "Tenders",
        "spotlight_section_eyebrow": "Start here",
        "spotlight_section_title": "Where to begin",
        "spotlight_section_description": (
            "Live routes through the catalog: strong signals, Kazakhstan-first "
            "items and practical support programs."
        ),
        "spotlight_count": "In view: {count}",
        "spotlight_action_open": "Open collection",
        "spotlight_empty": "Matching items will appear here after the catalog loads.",
        "spotlight_preview_more": "+ {count} more",
        "spotlight_trending_kicker": "Trending now",
        "spotlight_trending_title": "Best signals this week",
        "spotlight_trending_note": (
            "High-relevance, active opportunities that deserve the first click."
        ),
        "spotlight_kazakhstan_kicker": "Kazakhstan first",
        "spotlight_kazakhstan_title": "Focus on local opportunities",
        "spotlight_kazakhstan_note": (
            "Grants and programs with direct Kazakhstan relevance and local context."
        ),
        "spotlight_support_kicker": "Support programs",
        "spotlight_support_title": "Support for businesses and teams",
        "spotlight_support_note": (
            "Subsidies, incentives and support tools with practical application rules."
        ),
        "spotlight_deadline_kicker": "Closing soon",
        "spotlight_deadline_title": "Worth reviewing today",
        "spotlight_deadline_note": (
            "Opportunities with upcoming deadlines so visitors can act in time."
        ),
        "pathways_section_eyebrow": "Routes by use case",
        "pathways_section_title": "Where your project should start",
        "pathways_section_description": (
            "Short guided entry points for visitors who need a practical start, "
            "not just another list."
        ),
        "pathways_count": "Now: {count}",
        "pathways_action_open": "Open route",
        "pathways_empty": "Matching opportunities will appear here after catalog refresh.",
        "pathway_startup_kicker": "For startups",
        "pathway_startup_title": "Accelerators, grants and cloud credits",
        "pathway_startup_note": (
            "For product teams and AI startups looking for the fastest route to "
            "pilots, credits and support."
        ),
        "pathway_business_kicker": "For businesses",
        "pathway_business_title": "Subsidies, incentives and Kazakhstan support",
        "pathway_business_note": (
            "For SMBs and operating companies where local rules and application "
            "mechanics matter most."
        ),
        "pathway_farmer_kicker": "For farmers",
        "pathway_farmer_title": "Agri support, livestock and practical AgroTech",
        "pathway_farmer_note": (
            "For farms and agri teams looking for programs with direct practical value."
        ),
        "pathway_science_kicker": "For researchers",
        "pathway_science_title": "Science funding, commercialization and research grants",
        "pathway_science_note": (
            "For universities, labs and teams seeking funding for research and transfer."
        ),
        "themes_section_eyebrow": "Theme routes",
        "themes_section_title": "Which stream fits your work",
        "themes_section_description": (
            "Quick topic-based entry points so visitors can move straight into "
            "their lane instead of scanning the whole catalog."
        ),
        "themes_count": "Now: {count}",
        "themes_action_open": "Open theme",
        "themes_empty": "Matching cards will appear here after the catalog refreshes.",
        "funder_section_eyebrow": "Funders",
        "funder_section_title": "Who is active right now",
        "funder_section_description": (
            "A quick funder layer: where live opportunities exist, what they "
            "usually support, and which profiles are worth opening next."
        ),
        "funder_open_profile": "Funder profile",
        "funder_empty": "Funder profiles will appear here after the catalog loads.",
        "funder_live_now": "Live opportunities",
        "funder_overview_intro": "Usually supports grants and support programs.",
        "funder_overview_topics": "Main topics: {topics}.",
        "funder_overview_regions": "Regional focus: {regions}.",
        "funder_page_eyebrow": "Funder profile",
        "funder_focus_title": "What this funder usually backs",
        "funder_focus_note": (
            "This profile is derived from the current index so visitors can see "
            "formats, regions, and themes without opening every record one by one."
        ),
        "funder_focus_types": "Formats",
        "funder_focus_regions": "Regions",
        "funder_focus_indexed": "Indexed",
        "funder_live_title": "Live and actionable opportunities",
        "funder_live_note": (
            "Open, rolling, and forecast records that are worth checking now."
        ),
        "funder_live_empty": "There are no open or forecast records for this funder right now.",
        "funder_archive_title": "Archive and historical trail",
        "funder_archive_note": (
            "Closed and completed records help explain the cadence and shape of this funder."
        ),
        "funder_archive_empty": "No archive records have accumulated yet.",
        "funder_sources_title": "Where this profile comes from",
        "funder_sources_note": "Official sources and program pages used for this profile.",
        "funder_back_to_catalog": "Back to catalog",
        "funder_open_card": "Open card",
        "topic_brief_eyebrow": "Active focus",
        "topic_brief_count": "In view: {count}",
        "topic_brief_what": "What people usually look for",
        "topic_brief_best_for": "Best fit",
        "topic_brief_reset": "Clear theme",
        "topic_ai_best": "Product teams, AI startups, and digital initiatives.",
        "topic_ai_focus_1": "AI pilots and accelerators",
        "topic_ai_focus_2": "Cloud credits and infrastructure",
        "topic_ai_focus_3": "Digital skills and applied programs",
        "topic_agro_best": (
            "Farms, agri teams, and projects spanning water, climate, and sector work."
        ),
        "topic_agro_focus_1": "Subsidies and sector support",
        "topic_agro_focus_2": "Water, climate, and resilience",
        "topic_agro_focus_3": "Livestock, vet, and applied AgroTech",
        "topic_science_best": "Universities, labs, and research teams.",
        "topic_science_focus_1": "Research commercialization",
        "topic_science_focus_2": "Research grants, labs, and mobility",
        "topic_science_focus_3": "Education and university tracks",
        "topic_public_best": "Teams working with public delivery, procurement, and infrastructure.",
        "topic_public_focus_1": "Procurement, tenders, and EOI/RFP",
        "topic_public_focus_2": "Development programs and delivery",
        "topic_public_focus_3": "GovTech and large project pipelines",
        "topic_business_best": "Sole proprietors, LLCs, and operating businesses in Kazakhstan.",
        "topic_business_focus_1": "Local subsidies and Kazakhstan support",
        "topic_business_focus_2": "Incentives, guarantees, and financing",
        "topic_business_focus_3": "Support for SMBs, exports, and growth",
        "topic_ngo_best": "NGOs, media teams, and civic groups with an impact mission.",
        "topic_ngo_focus_1": "Media, journalism, and public-interest projects",
        "topic_ngo_focus_2": "Civil society grants and partnerships",
        "topic_ngo_focus_3": "Community and impact programs",
        "theme_ai_kicker": "AI and digital",
        "theme_ai_title": "AI programs, cloud credits, and digital skills",
        "theme_ai_note": (
            "For teams looking for AI opportunities, infrastructure support, "
            "credits, and digital initiatives."
        ),
        "theme_agro_kicker": "Agri / Vet / Eco",
        "theme_agro_title": "Agri, water, climate, and practical sector tracks",
        "theme_agro_note": (
            "For farms and sector teams working across agriculture, resilience, "
            "water, and applied verticals."
        ),
        "theme_science_kicker": "Education and science",
        "theme_science_title": "Research, education, and commercialization",
        "theme_science_note": (
            "For universities, labs, and education teams seeking grants and "
            "research-oriented tracks."
        ),
        "theme_public_kicker": "Public sector and infra",
        "theme_public_title": "Infrastructure, procurement, and development programs",
        "theme_public_note": (
            "For teams working with public delivery, procurement, and large "
            "development programs."
        ),
        "theme_business_kicker": "Business and subsidies",
        "theme_business_title": "Subsidies, incentives, and business support",
        "theme_business_note": (
            "For SMBs and operating companies where local rules and application "
            "mechanics matter."
        ),
        "theme_ngo_kicker": "Media and NGOs",
        "theme_ngo_title": "Media, civil society, and impact programs",
        "theme_ngo_note": (
            "For NGOs, media teams, and civic projects looking for grants and "
            "partnership-led tracks."
        ),
        "focus_aria": "Current product focus",
        "focus_primary": "Priority: Kazakhstan and Central Asia",
        "focus_secondary": (
            "Themes: AI, EdTech, GovTech, AgroTech, VetTech, EcoTech, media"
        ),
        "status_checking": "Checking data freshness",
        "api_docs": "API",
        "methodology_link": "How it works",
        "status_link": "Data status",
        "language_switch": "Interface language",
        "nav_aria": "Radar sections",
        "tab_opportunities": "Opportunities",
        "tab_sources": "Sources",
        "tab_health": "Status",
        "metrics_aria": "Summary metrics",
        "metric_total": "Indexed",
        "metric_relevant": "Relevant now",
        "metric_sources": "Sources",
        "opportunities_title": "Opportunities",
        "opportunities_description": (
            "Open and rolling programs with Kazakhstan and Central Asia shown first."
        ),
        "opportunities_description_all": (
            "Open, rolling and archived index records for coverage and source audits."
        ),
        "search_label": "Search",
        "search_placeholder": "Title, funder, tags, region",
        "audience_label": "Who is it for",
        "audience_aria": "Audience shortcuts",
        "audience_all": "All",
        "audience_startup": "Startups",
        "audience_business": "Businesses",
        "audience_farmer": "Farmers",
        "audience_ngo": "NGOs",
        "audience_science": "Researchers",
        "format_label": "What are you looking for",
        "format_aria": "Funding format shortcuts",
        "format_all": "All formats",
        "format_grants": "Grants and contests",
        "format_support": "Subsidies and support",
        "format_accelerators": "Accelerators and credits",
        "format_tenders": "Tenders and procurement",
        "topic_label": "Theme",
        "topic_aria": "Topic shortcuts",
        "topic_all": "All themes",
        "topic_ai": "AI and digital",
        "topic_agro": "Agri / Vet / Eco",
        "topic_science": "Education and science",
        "topic_public": "Public sector and infrastructure",
        "topic_ngo": "Media and NGOs",
        "topic_business": "Business and subsidies",
        "scope_label": "Scope",
        "scope_aria": "List scope",
        "scope_open": "Open",
        "scope_all": "Full index",
        "lifecycle_label": "Lifecycle",
        "lifecycle_aria": "Opportunity lifecycle",
        "lifecycle_all": "Any lifecycle",
        "lifecycle_open": "Open now",
        "lifecycle_forecast": "Forecast / pipeline",
        "lifecycle_closing_soon": "Closing soon",
        "lifecycle_rolling": "Rolling",
        "lifecycle_closed": "Closed",
        "lifecycle_awarded": "Awarded / completed",
        "region_label": "Region",
        "region_aria": "Region focus",
        "region_all": "All regions",
        "region_kazakhstan": "Kazakhstan",
        "region_central_asia": "Central Asia",
        "region_global": "International",
        "deadline_filter_label": "Timing",
        "deadline_filter_aria": "Deadline window",
        "deadline_filter_all": "Any timing",
        "deadline_filter_soon": "Closing soon",
        "deadline_filter_month": "Within a month",
        "deadline_filter_rolling": "Rolling",
        "sort_label": "Sort",
        "sort_aria": "Opportunity order",
        "sort_priority": "Best match",
        "sort_deadline": "Nearest deadline",
        "sort_updated": "Recently updated",
        "min_score_label": "Match precision",
        "min_score_aria": "Match precision",
        "source_label": "Source",
        "source_aria": "Source",
        "all_scores": "All results",
        "score_option_03": "Baseline match",
        "score_option_05": "High match",
        "score_option_07": "Exact match first",
        "all_sources": "All sources",
        "clear_filters": "Clear filters",
        "loading_opportunities": "Loading opportunities...",
        "load_more": "Load more",
        "sources_title": "Source coverage",
        "sources_description": (
            "Direct adapters and curated watch pages currently wired into the radar."
        ),
        "loading_sources": "Loading source coverage...",
        "show_all_sources": "Show all sources",
        "show_fewer_sources": "Show fewer",
        "health_title": "Data status",
        "health_description": (
            "Shows whether the catalog is reachable and how many sources are "
            "currently active in the public feed."
        ),
        "health_ok_value": "Data is current",
        "health_attention_value": "Needs review",
        "health_note_loading": "Checking the public feed and latest refresh time...",
        "health_note_ready": (
            "Feed checked at {checked_at}. Latest opportunity refresh: {updated_at}."
        ),
        "health_note_ready_no_items": (
            "Feed checked at {checked_at}. New opportunities will appear after the "
            "next source refresh."
        ),
        "reload_live_data": "Refresh data",
        "api_status": "Data stream",
        "stored_items": "Catalog entries",
        "health_sources": "Active sources",
        "api_online": "Data is current",
        "api_failed": "Data needs attention",
        "api_error": "Data load error",
        "source_catalog_unavailable": "Source catalog is unavailable right now.",
        "showing_sources": "Showing {shown} of {total} sources",
        "sources_connected": "{total} sources connected",
        "show_all_sources_with_total": "Show all {total} sources",
        "coverage_unavailable": "Coverage unavailable",
        "indexed_count": "{count} indexed",
        "relevant_open_count": "{count} relevant open",
        "direct_badge": "Direct",
        "watchlist_badge": "Watchlist",
        "source_direct_note": "Direct connection to the official source",
        "source_watchlist_note": "External watch feed with curated monitoring",
        "regional_badge_kazakhstan": "Kazakhstan priority",
        "regional_badge_central_asia": "Central Asia",
        "summary_matches": "{count} matches",
        "summary_search": "Search: {value}",
        "summary_audience": "Audience: {value}",
        "summary_format": "Format: {value}",
        "summary_topic": "Theme: {value}",
        "summary_lifecycle": "Lifecycle: {value}",
        "summary_region": "Region: {value}",
        "summary_deadline": "Timing: {value}",
        "summary_sort": "Sort: {value}",
        "summary_score": "Precision: {value}",
        "summary_scope_all": "Including archive",
        "methodology_title": "How we collect and present data",
        "methodology_description": (
            "A short explanation of where the catalog comes from, what match "
            "precision means, and what you should still verify before applying."
        ),
        "method_card_sources_title": "Sources and refresh",
        "method_card_sources_text": (
            "The catalog combines official sources, open registers, and curated "
            "watch pages. We regularly recheck links, deadlines, and whether an "
            "item is still active."
        ),
        "method_card_relevance_title": "Why an item is shown",
        "method_card_relevance_text": (
            "Ordering considers Kazakhstan and Central Asia, topic, format, "
            "deadline, and signals about who the program fits. It is a working "
            "heuristic, not a legal classification."
        ),
        "method_card_trust_title": "What counts as final",
        "method_card_trust_text": (
            "QAZ.FUND helps you find and structure opportunities quickly, but the "
            "final rules, forms, and requirements should always be verified on the "
            "official program website."
        ),
        "method_disclaimer_title": "Before you apply",
        "method_disclaimer_text": (
            "If a card looks relevant, open the official source and verify the "
            "deadline, eligibility, required documents, and submission route."
        ),
        "faq_title": "FAQ",
        "faq_q1": "Does QAZ.FUND award grants itself?",
        "faq_a1": (
            "No. The platform aggregates and structures opportunities, while the "
            "actual application always happens through the official program source."
        ),
        "faq_q2": "How often is the data refreshed?",
        "faq_a2": (
            "We regularly recheck the index and connected sources. For the current "
            "state, use the data status block and the latest feed refresh note."
        ),
        "faq_q3": "What does match precision mean?",
        "faq_a3": (
            "It is not a quality rating. It is the threshold for how closely an "
            "item matches the selected theme, region, format, and current QAZ.FUND "
            "focus."
        ),
        "faq_q4": "Why do support measures sometimes appear near grants?",
        "faq_a4": (
            "Some programs are legally structured as support measures or subsidies "
            "but are still useful to the same audience. We keep them visible when "
            "they genuinely match the task."
        ),
        "collections_label": "Collections",
        "collections_aria": "Saved collections and shareable links",
        "collections_empty": "Save the current filter set so you can jump back to it later.",
        "save_view": "Save collection",
        "share_view": "Copy link",
        "saved_view_saved": "Collection saved locally.",
        "saved_view_removed": "Collection removed.",
        "saved_view_shared": "Copied a link to the current collection.",
        "saved_view_default_name": "My collection",
        "saved_view_remove_aria": "Remove collection",
        "saved_view_status_label": "Saved collection status",
        "saved_view_share_prompt": "Copy the link to the current collection",
        "view_funder": "Funder profile",
        "fit_label": "Who it fits",
        "fit_unknown": "Check eligibility",
        "fit_deadline_soon": "Closing soon",
        "fit_global": "Global application",
        "signal_label": "Why this is worth a look",
        "signal_support_kz": (
            "A local support measure for Kazakhstan-based teams and businesses "
            "with practical application mechanics."
        ),
        "signal_public_sector": (
            "Useful for teams working with public sector delivery, infrastructure, "
            "or large development programs."
        ),
        "signal_business": (
            "A practical route for businesses where terms, document pack, and "
            "application mechanics matter."
        ),
        "signal_startup": (
            "Useful for product and AI teams looking for acceleration, pilots, "
            "or cloud credits."
        ),
        "signal_tender": (
            "Worth a quick check of applicant requirements, scope, and submission pack."
        ),
        "signal_science": (
            "Has a research or commercialization signal for universities, labs, "
            "and science teams."
        ),
        "signal_farmer": (
            "Has a practical agri signal for farms, producers, and sector teams."
        ),
        "signal_ngo": (
            "Useful for NGOs, media teams, and projects with a civic or social impact angle."
        ),
        "signal_kazakhstan": (
            "Has a direct Kazakhstan signal or local application conditions."
        ),
        "signal_central_asia": (
            "Works for Central Asia teams without being tied to a single country."
        ),
        "signal_global": (
            "A global opportunity that is still worth checking for your team's eligibility."
        ),
        "meta_format_label": "Format",
        "meta_region_label": "Region",
        "meta_deadline_label": "Timing",
        "meta_region_kazakhstan": "KZ first",
        "meta_region_central_asia": "Central Asia",
        "meta_region_global": "Global",
        "meta_deadline_rolling": "Rolling",
        "meta_deadline_soon_days": "In {count} days",
        "meta_deadline_month": "Within a month",
        "meta_deadline_later": "Has a deadline",
        "detail_fit_title": "Quick fit check",
        "detail_source_status_title": "Source status",
        "detail_fit_good": "Likely a fit",
        "detail_fit_review": "Manual eligibility review needed",
        "no_indexed_items": "No opportunities are indexed yet.",
        "no_filtered_items": "No opportunities match the selected filters.",
        "no_filtered_items_hint": (
            "Try relaxing one of the filters and the catalog will recalculate right away."
        ),
        "empty_action_clear": "Clear all",
        "empty_action_region": "All regions",
        "empty_action_deadline": "Any timing",
        "empty_action_score": "Standard threshold",
        "empty_action_scope": "Open full index",
        "open_details": "Details",
        "read_more": "Official source",
        "open_rolling": "Open / Rolling",
        "score_title": "QAZ.FUND relevance score based on current heuristics",
        "source_agency": "Source agency: {agency}",
        "no_summary": "No summary provided by source.",
        "reload_confirm": "Reload live data from all sources?",
        "results_button": "Load {count} more",
        "unknown_url": "Unknown URL",
        "views_aria": "Dashboard section navigation",
        "breadcrumbs_aria": "Breadcrumbs",
        "detail_panel_label": "Local opportunity detail",
        "detail_shell_title": "Local detail",
        "detail_title_fallback": "Opportunity detail",
        "detail_loading": "Loading local text and structured fields...",
        "detail_error": (
            "The local detail view is unavailable right now. The direct source link "
            "is still available below."
        ),
        "detail_empty": (
            "The source did not provide a richer local text yet. Showing the "
            "stored summary and structured fields."
        ),
        "detail_close": "Close",
        "detail_open_page": "Open page",
        "detail_all_opportunities": "All opportunities",
        "detail_open_source": "Open source",
        "detail_open_application": "Open application",
        "detail_meta_title": "Key fields",
        "detail_sections_title": "Text and excerpts",
        "detail_status_ok": "Description and key fields were collected from the official source",
        "detail_status_structured_only": "Showing the stored summary and structured fields",
        "detail_status_blocked": "The source blocked automatic full-text retrieval",
        "detail_status_not_allowed": "Local fetch is disabled for this source",
        "detail_status_too_large": "The source page is too large for the local reader",
        "detail_status_unsupported_media": "The source returned an unsupported format",
        "detail_status_parse_error": "The source page could not be parsed cleanly",
        "detail_source_excerpt": "Source excerpt",
        "prepare_section_eyebrow": "Before applying",
        "prepare_section_title": "What to prepare",
        "prepare_section_description": (
            "A short practical checklist for this kind of opportunity. Always "
            "confirm final requirements on the official source."
        ),
        "prepare_eligibility_title": "Check eligibility",
        "prepare_eligibility_text": (
            "Confirm geography, applicant type, sector limits, and submission language."
        ),
        "prepare_deadline_title": "Lock the deadline",
        "prepare_deadline_text": (
            "Leave time for registration, signatures, support letters, and document "
            "upload."
        ),
        "prepare_rolling_title": "Check current terms",
        "prepare_rolling_text": (
            "Rolling programs can change conditions without a separate deadline."
        ),
        "prepare_grant_title": "Build the project application",
        "prepare_grant_text": (
            "Prepare the problem, solution, budget, team, outcomes, and delivery plan."
        ),
        "prepare_tender_title": "Review the procurement pack",
        "prepare_tender_text": (
            "Check the scope, qualification criteria, submission format, guarantees, "
            "and required attachments."
        ),
        "prepare_startup_title": "Prepare the pitch package",
        "prepare_startup_text": (
            "Collect the deck, product description, traction, team, and pilot use case."
        ),
        "prepare_subsidy_title": "Prepare local documents",
        "prepare_subsidy_text": (
            "Check company status, digital signature, tax status, bank details, and "
            "supporting documents."
        ),
        "prepare_science_title": "Assemble the research pack",
        "prepare_science_text": (
            "Prepare novelty, team, timeline, budget, and commercialization path."
        ),
        "prepare_ngo_title": "Check the impact logic",
        "prepare_ngo_text": (
            "Define beneficiaries, social effect, partners, and reporting plan."
        ),
        "prepare_source_title": "Verify the official source",
        "prepare_source_text": (
            "Before applying, check the latest terms, forms, and contact details."
        ),
        "apply_section_eyebrow": "Application",
        "apply_section_title": "How to apply",
        "apply_section_description": (
            "A short route to submission. It helps keep the steps visible, but does "
            "not replace the official source instructions."
        ),
        "apply_step_open_apply_title": "Open the application page",
        "apply_step_open_apply_text": (
            "If the program has a separate application form, start there and confirm "
            "the requirements on that page."
        ),
        "apply_step_open_source_title": "Open the official source",
        "apply_step_open_source_text": (
            "Check current terms, contacts, and submission format on the source page."
        ),
        "apply_step_check_title": "Check criteria",
        "apply_step_check_text": (
            "Confirm country, applicant type, sector, project stage, and participant "
            "restrictions."
        ),
        "apply_step_pack_title": "Assemble the pack",
        "apply_step_pack_text": (
            "Prepare project description, budget, supporting documents, and support "
            "letters when required."
        ),
        "apply_step_submit_title": "Submit and save confirmation",
        "apply_step_submit_text": (
            "After submission, save the application number, email copy, or confirmation "
            "screenshot."
        ),
        "related_section_eyebrow": "Keep exploring",
        "related_section_title": "Related opportunities",
        "related_section_description": (
            "A few nearby cards from the same stream so visitors can keep moving "
            "without jumping back into the full catalog."
        ),
        "related_reason_source": "Same source",
        "related_reason_funder": "Similar funder",
        "related_reason_theme": "Related theme",
        "related_reason_format": "Similar format",
        "related_open": "Open card",
        "detail_meta_labels": {
            "source": "Source",
            "funder": "Funder",
            "deadline": "Deadline",
            "deadline_raw": "Source deadline",
            "deadline_policy": "Deadline policy",
            "amount": "Support amount",
            "amount_raw": "Source amount",
            "project_id": "Project ID",
            "reference": "Reference",
            "status": "Status",
            "notice_type": "Notice type",
            "borrower": "Borrower",
            "country": "Country",
            "region": "Region",
            "board_approval": "Board approval",
            "closing_date": "Closing date",
            "page_title": "Source page title",
            "application_url": "Application path",
            "status_note": "Fetch status",
        },
        "label_map": {
            "ai": "AI",
            "edtech": "EdTech",
            "govtech": "GovTech",
            "agrotech": "AgroTech",
            "vettech": "VetTech",
            "ecotech": "EcoTech",
            "animal_health": "VetTech",
            "climate": "EcoTech",
            "ngo": "NGO",
            "unesco": "UNESCO",
            "unicef": "UNICEF",
            "adb": "ADB",
            "aws": "AWS",
            "eeas": "EEAS",
            "microsoft": "Microsoft",
            "nvidia": "NVIDIA",
            "mongodb": "MongoDB",
            "central_asia_eligible": "Central Asia",
            "google_cloud_startup": "Google Cloud Startup",
            "google_org_ai_opportunity": "Google.org AI Opportunity Fund",
            "microsoft_founders_hub": "Microsoft Founders Hub",
            "world_bank_kazakhstan": "World Bank Kazakhstan",
            "adb_kazakhstan": "ADB Kazakhstan",
            "eeas_kazakhstan": "EEAS Kazakhstan",
            "unicef_kazakhstan": "UNICEF Kazakhstan",
            "unesco_iite": "UNESCO IITE",
            "isdb_project_procurement": "IsDB Procurement",
            "ebrd_ecepp_procurement": "EBRD ECEPP Procurement",
            "undp_procurement": "UNDP Procurement",
            "kazakhstan": "Kazakhstan",
            "central_asia": "Central Asia",
            "media": "Media",
            "journalism": "Journalism",
            "open_data": "Open data",
            "startup": "Startup",
            "grant": "Grant",
            "accelerator": "Accelerator",
            "cloud_credit": "Cloud credit",
            "tender": "Tender",
            "contest": "Contest",
            "fellowship": "Fellowship",
            "open": "Open",
            "forecast": "Forecast",
            "closing_soon": "Closing soon",
            "rolling": "Rolling",
            "closed": "Closed",
            "awarded": "Completed",
            "green_transition": "EcoTech",
            "climate_change": "EcoTech",
            "innovation": "Innovation",
            "commercialization": "Commercialization",
            "subsidy": "Subsidy",
            "sme": "SME",
            "business_support": "Business support",
            "domestic_support": "KZ support",
            "state_program": "State program",
            "preferential_financing": "Preferential financing",
            "loan_guarantee": "Loan guarantee",
            "tax_benefit": "Tax benefit",
            "reimbursement": "Cost reimbursement",
            "leasing": "Leasing",
            "employment": "Employment",
            "industry": "Industry",
            "export": "Export",
            "trade": "Trade",
            "investment": "Investment",
            "science": "Science",
            "civil_society": "Civil society",
            "crop_production": "Crop production",
            "livestock": "Livestock",
            "digitalization": "Digitalization",
            "qazinnovations": "QazInnovations",
            "egov": "eGov",
            "damu": "Damu",
            "enbek": "Enbek",
            "gosagro": "Gosagro",
            "govkz": "Gov.kz",
            "ncste": "NCSTE",
            "science_fund": "Science Fund",
            "cisc": "CISC",
            "qazindustry": "QazIndustry",
            "qaztrade": "QazTrade",
            "invest_gov": "KAZAKH INVEST",
            "baiterek": "Baiterek",
            "bgov": "BGov",
            "kazagrofinance": "KazAgroFinance",
            "agrocredit": "AgroCredit",
            "kazakhexport": "KazakhExport",
            "kdb": "DBK",
            "idf": "IDF",
            "qic": "QIC",
            "private_equity": "Private equity",
            "venture": "Venture",
            "kazakhstan_domestic_support": "KZ domestic support",
        },
    },
}


def _copy_for(lang: str) -> dict[str, object]:
    return cast(dict[str, object], COPY["en" if lang == "en" else "ru"])


def dashboard_copy(lang: str) -> dict[str, object]:
    return _copy_for(lang if lang in SUPPORTED_LANGS else "ru")


def _root_href(base: str, lang: str) -> str:
    if base:
        return f"{base}/?lang={lang}"
    return f"/?lang={lang}"


def _absolute_href(origin: str, path: str) -> str:
    clean_origin = origin.rstrip("/")
    if not path:
        return clean_origin or "/"
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{clean_origin}{path}" if clean_origin else path


def _json_ld(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _dashboard_schema(
    *,
    copy: dict[str, object],
    canonical_href: str,
    ru_href: str,
    en_href: str,
    items: int,
) -> str:
    organization_id = f"{canonical_href}#organization"
    website_id = f"{canonical_href}#website"
    page_id = f"{canonical_href}#page"
    catalog_id = f"{canonical_href}#catalog"
    faq_id = f"{canonical_href}#faq"
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": organization_id,
                "name": str(copy["title"]),
                "url": canonical_href,
                "description": str(copy["meta_description"]),
            },
            {
                "@type": "WebSite",
                "@id": website_id,
                "url": canonical_href,
                "name": str(copy["title"]),
                "description": str(copy["meta_description"]),
                "inLanguage": str(copy["lang"]),
                "publisher": {"@id": organization_id},
            },
            {
                "@type": "CollectionPage",
                "@id": page_id,
                "url": canonical_href,
                "name": str(copy["headline"]),
                "description": str(copy["meta_description"]),
                "inLanguage": str(copy["lang"]),
                "isPartOf": {"@id": website_id},
                "mainEntity": {"@id": catalog_id},
            },
            {
                "@type": "ItemList",
                "@id": catalog_id,
                "name": str(copy["opportunities_title"]),
                "description": str(copy["opportunities_description"]),
                "url": canonical_href,
                "numberOfItems": items,
            },
            {
                "@type": "FAQPage",
                "@id": faq_id,
                "url": f"{canonical_href}#methodology-panel",
                "inLanguage": str(copy["lang"]),
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q1"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a1"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q2"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a2"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q3"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a3"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q4"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a4"]),
                        },
                    },
                ],
            },
        ],
    }
    # Keep explicit alternate URLs in the graph for crawlers that cross-check.
    payload["@graph"][1]["hasPart"] = [  # type: ignore[index]
        {"@type": "WebPage", "url": ru_href, "inLanguage": "ru"},
        {"@type": "WebPage", "url": en_href, "inLanguage": "en"},
    ]
    return _json_ld(payload)


def render_dashboard(
    *,
    root_path: str,
    items: int,
    relevant_items: int = 0,
    source_count: int = 0,
    lang: str = "ru",
    site_origin: str = "",
) -> str:
    copy = _copy_for(lang if lang in SUPPORTED_LANGS else "ru")
    base_raw = root_path.rstrip("/")
    base = escape(base_raw, quote=True)
    active_lang = str(copy["lang"])
    docs_path = (
        f"{base_raw}/docs?lang={active_lang}"
        if base_raw
        else f"/docs?lang={active_lang}"
    )
    docs_href = escape(docs_path, quote=True)
    ru_href = escape(_root_href(base_raw, "ru"), quote=True)
    en_href = escape(_root_href(base_raw, "en"), quote=True)
    canonical_path = _root_href(base_raw, active_lang)
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    ru_canonical = escape(
        _absolute_href(site_origin, _root_href(base_raw, "ru")),
        quote=True,
    )
    en_canonical = escape(
        _absolute_href(site_origin, _root_href(base_raw, "en")),
        quote=True,
    )
    schema_json = _dashboard_schema(
        copy=copy,
        canonical_href=_absolute_href(site_origin, canonical_path),
        ru_href=_absolute_href(site_origin, _root_href(base_raw, "ru")),
        en_href=_absolute_href(site_origin, _root_href(base_raw, "en")),
        items=items,
    )
    copy_json = json.dumps(copy, ensure_ascii=False)
    html_lang = escape(active_lang, quote=True)
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    social_image = escape(og_image_url(site_origin, base_raw), quote=True)
    analytics_head = analytics_head_html()
    html_theme_attrs = (
        'data-avds="grant-radar" data-av-theme="light" data-theme="light"'
    )
    language_switch_label = escape(str(copy["language_switch"]), quote=True)
    loading_sources_label = escape(str(copy["loading_sources"]))
    initial_health_status = escape(str(copy["status_checking"]))
    initial_health_items = escape(str(items))
    initial_health_sources = escape(str(source_count))
    lang_ru_class = "lang-link active" if active_lang == "ru" else "lang-link"
    lang_en_class = "lang-link active" if active_lang == "en" else "lang-link"
    lang_ru_current = ' aria-current="true"' if active_lang == "ru" else ""
    lang_en_current = ' aria-current="true"' if active_lang == "en" else ""

    return f"""<!doctype html>
<html lang="{html_lang}" {html_theme_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(copy["title"]))}</title>
  <meta name="description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta name="yandex-verification" content="{YANDEX_SITE_VERIFICATION_TOKEN}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="ru" href="{ru_canonical}">
  <link rel="alternate" hreflang="en" href="{en_canonical}">
  <link rel="alternate" hreflang="x-default" href="{ru_canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escape(str(copy["title"]), quote=True)}">
  <meta property="og:description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(str(copy["title"]), quote=True)}">
  <meta name="twitter:description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
{analytics_head}
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme: light;
      --bg: var(--color-bg);
      --panel: var(--color-surface);
      --panel-subtle: var(--color-bg-subtle);
      --panel-strong: color-mix(in oklab, var(--panel), var(--brand-soft) 10%);
      --ink: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --line-strong: var(--color-border-strong);
      --line-subtle: var(--color-border-subtle);
      --brand: var(--color-accent);
      --brand-hover: var(--color-accent-hover);
      --brand-soft: var(--color-accent-subtle);
      --good: var(--color-success);
      --good-soft: var(--color-success-subtle);
      --warn: var(--color-warning);
      --warn-soft: var(--color-warning-subtle);
      --danger: var(--color-danger);
      --danger-soft: var(--color-danger-subtle);
      --surface-raised: var(--color-surface-raised);
      --focus-ring: var(--color-focus-ring);
      --container-max: var(--av-container-dashboard);
      --control-height: var(--av-control-height-md);
      --control-height-sm: var(--av-control-height-sm);
      --card-padding: var(--av-card-padding-md);
      --compact-card-padding: var(--av-card-padding-sm);
      --section-gap: var(--av-section-gap);
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: var(--av-font-sans);
      font-size: var(--av-text-base);
      line-height: var(--av-leading-normal);
      background: var(--bg);
      color: var(--ink);
    }}
    body.modal-open {{
      overflow: hidden;
    }}
    a {{ color: inherit; }}
    button, input, select {{ font: inherit; }}
    input, select {{ min-width: 0; }}
    .shell {{
      width: min(var(--container-max), calc(100% - 32px));
      margin: 0 auto;
      padding: var(--av-spacing-4) 0 var(--av-spacing-8);
    }}
    .hero-band {{
      position: relative;
      overflow: hidden;
      padding: 18px 22px 14px;
      margin-bottom: var(--av-spacing-2);
      border: 1px solid color-mix(in oklab, var(--brand), white 78%);
      border-radius: var(--av-radius-lg);
      background:
        radial-gradient(circle at top left, rgb(37 99 235 / 0.14), transparent 34%),
        radial-gradient(circle at 82% 18%, rgb(245 158 11 / 0.13), transparent 28%),
        linear-gradient(
          180deg,
          color-mix(in oklab, var(--panel), var(--brand-soft) 24%),
          color-mix(in oklab, var(--panel), white 12%)
        );
      box-shadow: var(--shadow-md);
      isolation: isolate;
    }}
    .hero-band::before {{
      content: "";
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgb(148 163 184 / 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgb(148 163 184 / 0.08) 1px, transparent 1px);
      background-size: 28px 28px;
      mask-image: linear-gradient(180deg, rgb(0 0 0 / 0.68), transparent 78%);
      pointer-events: none;
      z-index: -2;
    }}
    .hero-band::after {{
      content: "";
      position: absolute;
      inset: auto -8% -34% auto;
      width: 320px;
      height: 320px;
      border-radius: 50%;
      background: radial-gradient(circle, rgb(37 99 235 / 0.18), transparent 70%);
      filter: blur(12px);
      pointer-events: none;
      z-index: -1;
    }}
    .sticky-shell {{
      position: sticky;
      top: 0;
      z-index: 24;
      padding: 0 0 var(--av-spacing-2);
      margin-bottom: var(--av-spacing-1);
      background: transparent;
      backdrop-filter: none;
    }}
    .sticky-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-3);
      padding: 10px 14px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--bg), var(--panel) 84%);
      box-shadow: var(--shadow-sm);
      backdrop-filter: blur(18px);
    }}
    .topbar {{
      display: grid;
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-3);
    }}
    .brand {{
      min-width: 0;
      display: grid;
      gap: var(--av-spacing-2);
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-family: var(--font-sans);
      font-weight: 650;
      letter-spacing: 0;
      text-transform: none;
    }}
    .brand-row {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .brand h1 {{
      margin: 0;
      font-size: clamp(26px, 3vw, 32px);
      line-height: var(--av-leading-tight);
      letter-spacing: 0;
    }}
    .brand p {{
      margin: 0;
      max-width: 720px;
      color: color-mix(in oklab, var(--ink), white 28%);
      font-size: var(--av-text-base);
      line-height: 1.6;
    }}
    .focus-row {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-2);
      align-items: flex-start;
    }}
    .focus-chip {{
      display: inline-flex;
      align-items: center;
      width: fit-content;
      max-width: 100%;
      min-height: 28px;
      padding: 2px var(--av-spacing-2);
      border: 1px solid color-mix(in oklab, var(--brand), white 64%);
      border-radius: var(--av-radius-sm);
      background: rgb(255 255 255 / 0.54);
      color: color-mix(in oklab, var(--brand), var(--ink) 18%);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      overflow-wrap: anywhere;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
      gap: var(--av-spacing-3);
      align-items: stretch;
      margin-bottom: var(--av-spacing-3);
    }}
    .hero-copy {{
      display: grid;
      gap: var(--av-spacing-2);
      align-content: start;
      min-width: 0;
    }}
    .hero-intro {{
      margin: 0;
      max-width: 60ch;
      color: color-mix(in oklab, var(--ink), white 20%);
      font-size: var(--av-text-base);
      line-height: 1.58;
    }}
    .hero-actions {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .button.primary {{
      border-color: transparent;
      background: var(--brand);
      color: var(--color-accent-contrast);
      box-shadow: 0 10px 20px rgb(37 99 235 / 0.18);
    }}
    .button.primary:hover {{
      background: var(--brand-hover);
      border-color: transparent;
      color: var(--color-accent-contrast);
    }}
    .button.soft {{
      border-color: color-mix(in oklab, var(--brand), white 52%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 36%);
      color: var(--brand);
    }}
    .button.soft:hover {{
      border-color: color-mix(in oklab, var(--brand), white 34%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 56%);
      color: var(--brand-hover);
    }}
    .button.subtle {{
      border-color: var(--line);
      background: rgb(255 255 255 / 0.5);
      color: var(--ink);
    }}
    .button.subtle:hover {{
      background: rgb(255 255 255 / 0.8);
    }}
    .hero-stage {{
      display: grid;
      gap: var(--av-spacing-2);
      min-width: 0;
      align-content: start;
      padding: 18px;
      border: 1px solid color-mix(in oklab, var(--brand), white 72%);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / 0.58);
      box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.45);
    }}
    .hero-stage-eyebrow {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 650;
      letter-spacing: 0;
      text-transform: none;
    }}
    .hero-stage-title {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(20px, 2vw, 24px);
      font-weight: 700;
      line-height: var(--av-leading-tight);
      letter-spacing: 0;
    }}
    .hero-points {{
      display: grid;
      gap: 10px;
    }}
    .hero-point {{
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: var(--av-spacing-2);
      align-items: start;
      color: color-mix(in oklab, var(--ink), white 22%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .hero-point-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: var(--av-radius-full);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 46%);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--brand), white 52%);
    }}
    .hero-picks {{
      display: grid;
      gap: 6px;
      min-width: 0;
    }}
    .hero-pick-row {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .hero-pick {{
      min-height: 30px;
      padding-inline: 10px;
      border-radius: var(--av-radius-sm);
      border: 1px solid color-mix(in oklab, var(--line), var(--brand) 18%);
      background: rgb(255 255 255 / 0.56);
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .hero-pick:hover,
    .hero-pick:focus-visible {{
      border-color: color-mix(in oklab, var(--brand), white 36%);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 36%);
      color: var(--brand);
    }}
    .hero-band .grid {{
      width: 100%;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-bottom: 0;
      border-color: color-mix(in oklab, var(--brand), white 78%);
      background: rgb(255 255 255 / 0.72);
      backdrop-filter: blur(14px);
    }}
    .hero-band .metric {{
      min-height: 78px;
      padding: 14px 16px;
    }}
    .hero-band .metric span {{
      color: color-mix(in oklab, var(--muted), var(--ink) 22%);
    }}
    .spotlight-section {{
      display: grid;
      gap: var(--av-spacing-3);
      margin-bottom: var(--av-spacing-4);
    }}
    .funder-section {{
      display: grid;
      gap: var(--av-spacing-3);
      margin-bottom: var(--av-spacing-4);
    }}
    .spotlight-copy {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .spotlight-copy h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(22px, 3vw, 28px);
      font-weight: 700;
      line-height: var(--av-leading-tight);
      letter-spacing: 0;
    }}
    .spotlight-copy p {{
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }}
    .spotlight-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }}
    .spotlight-card {{
      display: grid;
      gap: var(--av-spacing-3);
      min-height: 218px;
      padding: 18px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), white 10%),
        color-mix(in oklab, var(--panel-subtle), white 12%)
      );
      box-shadow: var(--shadow-sm);
    }}
    .spotlight-card[data-tone="brand"] {{
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--brand-soft) 36%),
        color-mix(in oklab, var(--panel-subtle), white 14%)
      );
      border-color: color-mix(in oklab, var(--brand), white 72%);
    }}
    .spotlight-card[data-tone="good"] {{
      border-color: color-mix(in oklab, var(--good), white 72%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--good-soft) 34%),
        color-mix(in oklab, var(--panel-subtle), white 14%)
      );
    }}
    .spotlight-card[data-tone="amber"] {{
      border-color: color-mix(in oklab, var(--warn), white 74%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--warn-soft) 34%),
        color-mix(in oklab, var(--panel-subtle), white 12%)
      );
    }}
    .spotlight-card[data-tone="neutral"] {{
      border-color: color-mix(in oklab, var(--line), var(--brand) 12%);
    }}
    .spotlight-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }}
    .spotlight-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .spotlight-count {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.74);
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: inset 0 0 0 1px var(--line-subtle);
    }}
    .spotlight-card h3 {{
      margin: 0;
      font-size: var(--av-text-xl);
      line-height: 1.18;
      letter-spacing: 0;
    }}
    .spotlight-note {{
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 30%);
      font-size: var(--av-text-sm);
      line-height: 1.58;
    }}
    .spotlight-list {{
      display: grid;
      gap: 8px;
      min-width: 0;
    }}
    .spotlight-item {{
      display: grid;
      gap: 2px;
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--ink);
      text-align: left;
      cursor: pointer;
    }}
    .spotlight-item:hover strong,
    .spotlight-item:focus-visible strong {{
      color: var(--brand);
    }}
    .spotlight-item strong {{
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
      overflow: hidden;
      font-size: var(--av-text-sm);
      line-height: 1.45;
      transition: color var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .spotlight-item span {{
      color: var(--muted);
      font-size: var(--av-text-xs);
    }}
    .spotlight-empty {{
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .spotlight-more {{
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }}
    .spotlight-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }}
    .pathways-section {{
      display: grid;
      gap: var(--av-spacing-3);
      margin-bottom: var(--av-spacing-4);
    }}
    .themes-section {{
      display: grid;
      gap: var(--av-spacing-3);
      margin-bottom: var(--av-spacing-4);
    }}
    .funder-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }}
    .funder-card {{
      display: grid;
      gap: var(--av-spacing-2);
      min-height: 184px;
      padding: 18px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), white 10%),
        color-mix(in oklab, var(--panel-subtle), white 18%)
      );
      box-shadow: var(--shadow-sm);
    }}
    .funder-card-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }}
    .funder-card h3 {{
      margin: 0;
      font-size: var(--av-text-lg);
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .funder-card p {{
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 26%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .funder-kpi {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: var(--brand-soft);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
    }}
    .funder-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .funder-actions {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }}
    .funder-actions .button {{
      min-height: 34px;
    }}
    .themes-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }}
    .theme-card {{
      display: grid;
      gap: var(--av-spacing-3);
      min-height: 186px;
      padding: 18px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), white 10%),
        color-mix(in oklab, var(--panel-subtle), white 18%)
      );
      box-shadow: var(--shadow-sm);
    }}
    .theme-card[data-tone="brand"] {{
      border-color: color-mix(in oklab, var(--brand), white 74%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--brand-soft) 26%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .theme-card[data-tone="good"] {{
      border-color: color-mix(in oklab, var(--good), white 72%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--good-soft) 26%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .theme-card[data-tone="amber"] {{
      border-color: color-mix(in oklab, var(--warn), white 74%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--warn-soft) 28%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .theme-card[data-tone="violet"] {{
      border-color: color-mix(in oklab, var(--accent-violet), white 76%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--accent-violet-soft) 24%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .theme-card[data-tone="neutral"] {{
      border-color: color-mix(in oklab, var(--line), var(--brand) 12%);
    }}
    .theme-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }}
    .theme-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .theme-count {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.74);
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: inset 0 0 0 1px var(--line-subtle);
    }}
    .theme-card h3 {{
      margin: 0;
      font-size: var(--av-text-lg);
      line-height: 1.24;
      letter-spacing: 0;
    }}
    .theme-note {{
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 30%);
      font-size: var(--av-text-sm);
      line-height: 1.58;
    }}
    .theme-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }}
    .topic-brief {{
      display: grid;
      gap: 14px;
      margin-bottom: var(--av-spacing-3);
      padding: 16px 18px;
      border-inline-start: 3px solid color-mix(in oklab, var(--brand), white 20%);
      border-radius: 0 var(--av-radius-sm) var(--av-radius-sm) 0;
      background: color-mix(in oklab, var(--panel-subtle), var(--brand-soft) 14%);
    }}
    .topic-brief.hidden {{
      display: none;
    }}
    .topic-brief-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .topic-brief-kicker {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .topic-brief-count {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.78);
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: inset 0 0 0 1px var(--line-subtle);
    }}
    .topic-brief h3 {{
      margin: 0;
      font-size: clamp(22px, 3vw, 28px);
      line-height: 1.15;
      letter-spacing: 0;
    }}
    .topic-brief-note {{
      margin: 0;
      max-width: 720px;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }}
    .topic-brief-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(220px, 0.9fr);
      gap: var(--av-spacing-3);
      align-items: start;
    }}
    .topic-brief-group {{
      display: grid;
      gap: 8px;
      min-width: 0;
    }}
    .topic-brief-label {{
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .topic-brief-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .topic-brief-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 0 12px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.72);
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--line), var(--brand) 10%);
    }}
    .topic-brief-audience {{
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }}
    .topic-brief-actions {{
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: var(--av-spacing-2);
    }}
    .pathways-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }}
    .pathway-card {{
      display: grid;
      gap: var(--av-spacing-3);
      min-height: 190px;
      padding: 18px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), white 8%),
        color-mix(in oklab, var(--panel-subtle), white 18%)
      );
      box-shadow: var(--shadow-sm);
    }}
    .pathway-card[data-tone="brand"] {{
      border-color: color-mix(in oklab, var(--brand), white 74%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--brand-soft) 28%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .pathway-card[data-tone="good"] {{
      border-color: color-mix(in oklab, var(--good), white 72%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--good-soft) 28%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .pathway-card[data-tone="amber"] {{
      border-color: color-mix(in oklab, var(--warn), white 74%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--warn-soft) 28%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .pathway-card[data-tone="violet"] {{
      border-color: color-mix(in oklab, var(--accent-violet), white 76%);
      background: linear-gradient(
        180deg,
        color-mix(in oklab, var(--panel), var(--accent-violet-soft) 24%),
        color-mix(in oklab, var(--panel-subtle), white 16%)
      );
    }}
    .pathway-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--av-spacing-2);
    }}
    .pathway-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .pathway-count {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: var(--av-radius-full);
      background: rgb(255 255 255 / 0.72);
      color: var(--ink);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
      box-shadow: inset 0 0 0 1px var(--line-subtle);
    }}
    .pathway-card h3 {{
      margin: 0;
      font-size: var(--av-text-xl);
      line-height: 1.22;
      letter-spacing: 0;
    }}
    .pathway-note {{
      margin: 0;
      color: color-mix(in oklab, var(--muted), var(--ink) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.58;
    }}
    .pathway-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      margin-top: auto;
      flex-wrap: wrap;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      width: fit-content;
      gap: var(--av-spacing-2);
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-2);
      border: 1px solid color-mix(in oklab, var(--good), white 62%);
      border-radius: var(--av-radius-full);
      background: var(--good-soft);
      color: var(--good);
      font-size: var(--av-text-xs);
      font-weight: 700;
      white-space: nowrap;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: var(--av-radius-full);
      background: currentColor;
    }}
    .topbar-actions {{
      display: grid;
      gap: var(--av-spacing-2);
      justify-items: end;
      min-width: 0;
    }}
    .sticky-actions {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
      min-width: 0;
    }}
    .utility-links {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .utility-link {{
      color: var(--muted);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
      white-space: nowrap;
    }}
    .utility-link:hover,
    .utility-link:focus-visible {{
      color: var(--brand);
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .lang-switch {{
      display: inline-flex;
      align-items: center;
      gap: 2px;
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel-subtle);
    }}
    .lang-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-2);
      border-radius: var(--av-radius-sm);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      text-decoration: none;
    }}
    .lang-link.active {{
      background: var(--panel);
      color: var(--ink);
      box-shadow: var(--shadow-xs);
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 4px;
      overflow-x: auto;
      min-height: 40px;
      max-width: 100%;
      padding: 4px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--panel-subtle), white 18%);
      scrollbar-width: none;
      white-space: nowrap;
      flex: 1 1 auto;
      min-width: 0;
    }}
    .toolbar::-webkit-scrollbar {{ display: none; }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: var(--control-height);
      padding: 0 var(--av-spacing-3);
      border: 1px solid var(--button-outline);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .button:hover {{
      border-color: var(--line-strong);
      background: var(--panel-subtle);
      box-shadow: var(--shadow-xs);
    }}
    .button.slim {{
      min-height: var(--control-height-sm);
      padding: 0 var(--av-spacing-2);
    }}
    .button.tab {{
      border-color: transparent;
      background: transparent;
      box-shadow: none;
      color: var(--muted);
      white-space: nowrap;
      flex: 0 0 auto;
      min-height: 32px;
      border-radius: var(--av-radius-sm);
    }}
    .button.tab:hover {{
      color: var(--brand);
      background: var(--panel-subtle);
      border-color: transparent;
    }}
    .button[aria-pressed="true"] {{
      border-color: transparent;
      background: var(--panel);
      color: var(--ink);
      font-weight: 700;
      box-shadow: var(--shadow-xs);
    }}
    .button:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
    }}
    .button:focus-visible,
    .field:focus-visible,
    .text-button:focus-visible,
    .source-card:focus-visible,
    .more-link:focus-visible,
    .utility-link:focus-visible,
    .lang-link:focus-visible {{
      outline: 0;
      box-shadow: var(--focus-ring);
      outline-offset: 2px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(148px, 196px));
      gap: 0;
      width: fit-content;
      max-width: 100%;
      justify-content: start;
      margin-bottom: var(--av-spacing-2);
      align-items: stretch;
      overflow: hidden;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      box-shadow: var(--shadow-xs);
    }}
    .metric {{
      border: 0;
      border-top: 3px solid var(--brand);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      min-height: 74px;
      min-width: 0;
      padding: 14px 18px;
      display: grid;
      align-content: center;
    }}
    .metric + .metric {{ border-left: 1px solid var(--line-subtle); }}
    .metric.strong {{ border-top-color: var(--good); }}
    .metric.sources {{ border-top-color: var(--warn); }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
      margin-bottom: var(--av-spacing-1);
    }}
    .metric strong {{
      font-family: var(--font-sans);
      font-size: 26px;
      font-weight: 700;
      line-height: 1;
      letter-spacing: 0;
      font-feature-settings: "tnum" 1, "lnum" 1;
    }}
    .panel {{
      padding: var(--section-gap) 0 0;
      margin-top: var(--section-gap);
      border-top: 1px solid var(--line);
      scroll-margin-top: 156px;
    }}
    .panel.primary {{
      border-top: 0;
      margin-top: 0;
      padding-top: var(--av-spacing-1);
    }}
    .panel-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-2);
    }}
    .panel-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: var(--av-text-xl);
      font-weight: 700;
      line-height: var(--av-leading-tight);
    }}
    .panel-head p {{
      margin: var(--av-spacing-1) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .panel-actions {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .panel-summary {{
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) repeat(3, minmax(128px, 0.28fr));
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-2);
      align-items: end;
    }}
    .preset-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-2);
    }}
    .preset-group {{
      display: grid;
      gap: 6px;
      min-width: 0;
    }}
    .preset-row {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
      min-width: 0;
    }}
    .preset-button {{
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-sm);
      background: var(--panel);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      cursor: pointer;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        background var(--av-duration-base) var(--av-easing-emphasized),
        color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .preset-button:hover {{
      border-color: var(--line-strong);
      background: var(--panel-subtle);
      color: var(--ink);
    }}
    .preset-button[aria-pressed="true"] {{
      border-color: color-mix(in oklab, var(--brand), white 34%);
      background: var(--brand-soft);
      color: var(--brand);
      box-shadow: var(--shadow-xs);
    }}
    .filter-block {{
      display: grid;
      gap: 6px;
    }}
    .filter-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }}
    .filters-meta {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
      margin-bottom: var(--av-spacing-3);
    }}
    .filter-summary {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .saved-views {{
      display: grid;
      gap: var(--av-spacing-2);
      margin-bottom: var(--av-spacing-3);
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--panel), var(--panel-subtle) 20%);
    }}
    .saved-views-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .saved-actions {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-1);
      flex-wrap: wrap;
    }}
    .saved-view-row {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .saved-view-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 30px;
      max-width: 100%;
      padding: 0 10px;
      border: 1px solid var(--badge-outline);
      border-radius: var(--av-radius-sm);
      background: var(--panel);
    }}
    .saved-view-pill button {{
      border: 0;
      background: transparent;
      padding: 0;
      cursor: pointer;
      font: inherit;
    }}
    .saved-view-pill .saved-apply {{
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .saved-view-pill .saved-remove {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1;
    }}
    .saved-empty {{
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .saved-view-notice {{
      min-height: 20px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.45;
    }}
    .summary-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border: 1px solid var(--badge-outline);
      border-radius: var(--av-radius-sm);
      padding: 0 7px;
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }}
    .summary-pill.result {{
      background: var(--brand-soft);
      color: var(--brand);
    }}
    .text-button {{
      min-height: var(--control-height-sm);
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: transparent;
      color: var(--muted);
      font-size: var(--av-text-sm);
      font-weight: 600;
      padding: 0 var(--av-spacing-2);
      cursor: pointer;
    }}
    .text-button:hover,
    .text-button:focus-visible {{
      color: var(--brand);
      background: var(--brand-soft);
      text-decoration: none;
    }}
    .field {{
      width: 100%;
      min-height: var(--control-height);
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: 0 var(--av-spacing-3);
      color: var(--ink);
      outline: 0;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .field:focus-visible {{
      border-color: var(--brand);
      box-shadow: var(--focus-ring);
    }}
    select.field {{
      appearance: none;
      padding-right: var(--av-spacing-8);
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 16px) calc(50% - 2px),
        calc(100% - 11px) calc(50% - 2px);
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }}
    .message {{
      min-height: var(--control-height);
      display: flex;
      align-items: center;
      color: var(--muted);
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      padding: 10px;
      background: var(--panel-subtle);
    }}
    .message.empty {{
      align-items: stretch;
    }}
    .message-shell {{
      width: 100%;
      display: grid;
      gap: var(--av-spacing-2);
    }}
    .message-title {{
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 650;
      line-height: var(--av-leading-snug);
    }}
    .message-note {{
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }}
    .message-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .message-action {{
      min-height: 32px;
      padding-inline: 10px;
      border-radius: var(--av-radius-sm);
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .message.error {{
      color: var(--danger);
      border-color: var(--danger);
      background: var(--danger-soft);
    }}
    .list {{ display: grid; gap: var(--av-spacing-2); }}
    .list-actions {{
      display: flex;
      justify-content: center;
      margin-top: var(--av-spacing-3);
    }}
    .opportunity {{
      border: 1px solid var(--line-subtle);
      border-top: 3px solid var(--line-strong);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: 14px;
      box-shadow: none;
      position: relative;
      overflow: hidden;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized);
      content-visibility: auto;
      contain-intrinsic-size: 180px;
    }}
    .opportunity.good {{ border-top-color: var(--good); }}
    .opportunity.warn {{ border-top-color: var(--warn); }}
    .opportunity.low {{ border-top-color: var(--line-strong); }}
    .opportunity:hover {{
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 10%);
      border-color: var(--line);
      box-shadow: var(--shadow-xs);
    }}
    .opportunity-main {{
      display: grid;
      gap: var(--av-spacing-1);
    }}
    .opportunity-top {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: var(--av-spacing-2);
      align-items: start;
    }}
    .opportunity h3 {{
      margin: 0 0 var(--av-spacing-2);
      font-size: var(--av-text-base);
      font-weight: 650;
      line-height: var(--av-leading-snug);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .opportunity h3 a {{
      color: var(--ink);
      text-decoration: none;
      transition: color var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .opportunity h3 a:hover,
    .opportunity h3 a:focus-visible {{
      color: var(--brand);
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .opportunity p {{
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .tags {{ display: flex; flex-wrap: wrap; gap: var(--av-spacing-1); }}
    .tag {{
      border-radius: var(--av-radius-sm);
      border: 1px solid var(--badge-outline);
      background: color-mix(in oklab, var(--panel-subtle), var(--panel) 26%);
      color: var(--muted);
      padding: 2px 6px;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      line-height: 1.4;
    }}
    .fit-block {{
      display: grid;
      gap: 6px;
    }}
    .fit-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }}
    .fit-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .fit-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      max-width: 100%;
      padding: 0 8px;
      border: 1px solid var(--badge-outline);
      border-radius: var(--av-radius-sm);
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
      overflow-wrap: anywhere;
    }}
    .fit-pill.good {{
      background: var(--good-soft);
      color: var(--good);
      border-color: color-mix(in oklab, var(--good), white 36%);
    }}
    .fit-pill.warn {{
      background: var(--warn-soft);
      color: var(--warn);
      border-color: color-mix(in oklab, var(--warn), white 40%);
    }}
    .signal-box {{
      display: grid;
      gap: 8px;
      padding: 10px 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 10%);
    }}
    .signal-label {{
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }}
    .signal-lede {{
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      font-weight: 600;
      line-height: var(--av-leading-snug);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .signal-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: var(--av-spacing-1);
    }}
    .signal-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 22px;
      max-width: 100%;
      padding: 0 8px;
      border: 1px solid var(--badge-outline);
      border-radius: var(--av-radius-sm);
      background: var(--panel);
      color: var(--ink);
      font-size: var(--av-text-xs);
      font-weight: 700;
      overflow-wrap: anywhere;
    }}
    .signal-pill span {{
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }}
    .side {{
      min-width: 118px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
      gap: var(--av-spacing-2);
    }}
    .score {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 56px;
      min-height: 24px;
      border-radius: var(--av-radius-sm);
      background: var(--brand-soft);
      color: var(--brand);
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .score.good {{ background: var(--good-soft); color: var(--good); }}
    .score.warn {{ background: var(--warn-soft); color: var(--warn); }}
    .score.low {{
      background: var(--panel-subtle);
      color: var(--muted);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 22px;
      width: max-content;
      max-width: 100%;
      border: 1px solid transparent;
      border-radius: var(--av-radius-sm);
      padding: 0 var(--av-spacing-2);
      background: var(--brand-soft);
      color: var(--brand);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .badge.watchlist {{ background: var(--good-soft); color: var(--good); }}
    .badge.regional {{ background: var(--warn-soft); color: var(--warn); }}
    .badge.lifecycle {{
      background: var(--panel-subtle);
      color: var(--ink);
      border-color: var(--line-subtle);
    }}
    .health-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }}
    .method-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--av-spacing-3);
    }}
    .source-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: var(--av-spacing-2);
    }}
    .source-card {{
      display: flex;
      align-items: center;
      gap: 0.85rem;
      border: 1.5px solid var(--line);
      border-radius: var(--av-radius-md);
      padding: 0.85rem 1.1rem;
      background: var(--panel);
      min-height: 66px;
      color: inherit;
      text-decoration: none;
      transition:
        border-color var(--av-duration-base) var(--av-easing-emphasized),
        box-shadow var(--av-duration-base) var(--av-easing-emphasized),
        background var(--av-duration-base) var(--av-easing-emphasized),
        transform var(--av-duration-base) var(--av-easing-emphasized);
      content-visibility: auto;
      contain-intrinsic-size: 76px;
    }}
    .source-icon {{
      width: 38px;
      height: 38px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 0 0 auto;
      border-radius: 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0;
      box-shadow: inset 0 0 0 1px color-mix(in oklab, currentColor, transparent 80%);
    }}
    .source-icon--blue {{
      background: rgb(96 165 250 / 0.12);
      color: var(--av-color-blue-700);
    }}
    .source-icon--green {{
      background: rgb(16 185 129 / 0.12);
      color: var(--av-color-emerald-700);
    }}
    .source-icon--amber {{
      background: rgb(245 158 11 / 0.14);
      color: var(--av-color-amber-700);
    }}
    .source-icon--violet {{
      background: rgb(139 92 246 / 0.12);
      color: #6d28d9;
    }}
    .source-icon--slate {{
      background: rgb(100 116 139 / 0.12);
      color: var(--av-color-slate-500);
    }}
    .source-icon--red {{
      background: rgb(239 68 68 / 0.11);
      color: var(--av-color-red-700);
    }}
    .source-card:hover {{
      border-color: var(--brand);
      background: var(--brand-soft);
      box-shadow: var(--shadow-sm);
      transform: translateY(-1px);
    }}
    .source-card strong {{
      display: block;
      font-size: 14px;
      font-weight: 650;
      line-height: var(--av-leading-snug);
    }}
    .source-main {{
      min-width: 0;
      flex: 1 1 auto;
    }}
    .source-meta {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--av-spacing-2);
      margin-top: var(--av-spacing-1);
      min-width: 0;
    }}
    .source-note {{
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.2;
      min-width: 0;
      overflow-wrap: anywhere;
    }}
    .source-url {{
      flex: 0 1 180px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      display: inline-block;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .source-card:hover .source-url {{ color: var(--brand); }}
    .source-count {{
      flex: 0 0 136px;
      justify-self: end;
      display: grid;
      gap: 4px;
      min-width: 0;
      text-align: right;
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: var(--av-leading-snug);
    }}
    .source-count span {{
      min-width: 0;
      overflow-wrap: anywhere;
    }}
    .source-arrow {{
      flex: 0 0 auto;
      color: color-mix(in oklab, var(--muted), transparent 18%);
      font-size: 20px;
      line-height: 1;
      transition:
        color var(--av-duration-base) var(--av-easing-emphasized),
        transform var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .source-card:hover .source-arrow {{
      color: var(--brand);
      transform: translateX(2px);
    }}
    .opportunity-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
      padding-top: var(--av-spacing-2);
      border-top: 1px solid var(--line-subtle);
      color: var(--muted);
      font-size: var(--av-text-xs);
    }}
    .card-actions {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .detail-link {{
      min-height: var(--control-height-sm);
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: transparent;
      color: var(--brand);
      font-size: var(--av-text-sm);
      font-weight: 600;
      padding: 0;
      cursor: pointer;
    }}
    .detail-link:hover,
    .detail-link:focus-visible {{
      color: var(--brand-hover);
      text-decoration: underline;
      text-underline-offset: 2px;
      background: transparent;
      box-shadow: none;
    }}
    .opportunity-click {{
      position: absolute;
      inset: 0;
      border: 0;
      background: transparent;
      cursor: pointer;
      opacity: 0;
      appearance: none;
      z-index: 0;
    }}
    .opportunity-click:focus-visible {{
      outline: 0;
      box-shadow: inset var(--focus-ring);
      outline-offset: 2px;
      opacity: 1;
    }}
    .opportunity-main,
    .opportunity-footer,
    .side,
    .opportunity h3,
    .tags,
    .signal-box,
    .signal-pills,
    .card-actions,
    .detail-link,
    .more-link {{
      position: relative;
      z-index: 1;
    }}
    .opportunity:hover .score,
    .opportunity:hover .tag {{
      background-color: color-mix(in oklab, currentColor, transparent 92%);
    }}
    .score,
    .tag {{
      transition: background-color var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .footer-source {{
      display: inline-flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .footer-funder-link {{
      color: var(--brand);
      font-weight: 600;
      text-decoration: none;
    }}
    .footer-funder-link:hover,
    .footer-funder-link:focus-visible {{
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .footer-sep {{ color: var(--line-strong); }}
    .more-link {{
      color: var(--brand);
      font-size: var(--av-text-sm);
      font-weight: 600;
      text-decoration: none;
    }}
    .more-link:hover,
    .more-link:focus-visible {{
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .detail-backdrop {{
      position: fixed;
      inset: 0;
      z-index: 70;
      background: rgb(15 23 42 / 0.38);
      backdrop-filter: blur(8px);
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--av-duration-base) var(--av-easing-emphasized);
    }}
    .detail-backdrop.open {{
      opacity: 1;
      pointer-events: auto;
    }}
    .detail-drawer {{
      position: fixed;
      inset: 0 0 0 auto;
      z-index: 80;
      width: min(720px, 100vw);
      border-left: 1px solid var(--line);
      background: color-mix(in oklab, var(--panel), white 6%);
      box-shadow: -24px 0 64px rgb(15 23 42 / 0.18);
      transform: translateX(100%);
      transition: transform var(--av-duration-base) var(--av-easing-emphasized);
      display: grid;
      grid-template-rows: auto 1fr auto;
    }}
    .detail-drawer.open {{
      transform: translateX(0);
    }}
    .detail-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: var(--av-spacing-2);
      padding: var(--av-spacing-3);
      border-bottom: 1px solid var(--line-subtle);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 9%);
    }}
    .detail-header h2 {{
      margin: var(--av-spacing-1) 0 0;
      font-family: var(--font-sans);
      font-size: var(--av-text-xl);
      line-height: var(--av-leading-tight);
    }}
    .detail-status {{
      margin: var(--av-spacing-2) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }}
    .detail-close {{
      min-width: var(--control-height);
      padding: 0;
      flex: 0 0 auto;
    }}
    .detail-body {{
      overflow-y: auto;
      padding: var(--av-spacing-3);
      display: grid;
      gap: var(--av-spacing-3);
      align-content: start;
    }}
    .detail-meta {{
      display: grid;
      gap: var(--av-spacing-2);
    }}
    .detail-fit {{
      display: grid;
      gap: var(--av-spacing-2);
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 10%);
    }}
    .detail-fit h3 {{
      margin: 0;
      font-size: var(--av-text-sm);
      font-weight: 700;
      line-height: var(--av-leading-snug);
    }}
    .detail-fit p {{
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }}
    .detail-meta-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--av-spacing-2);
    }}
    .detail-meta-item {{
      min-width: 0;
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
    }}
    .detail-meta-item span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
    }}
    .detail-meta-item strong {{
      display: block;
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
      overflow-wrap: anywhere;
    }}
    .detail-section-block {{
      padding-top: var(--av-spacing-2);
      border-top: 1px solid var(--line-subtle);
    }}
    .detail-section-block h3,
    .detail-meta h3 {{
      margin: 0 0 var(--av-spacing-2);
      font-size: var(--av-text-sm);
      font-weight: 700;
      line-height: var(--av-leading-snug);
    }}
    .detail-richtext {{
      display: grid;
      gap: var(--av-spacing-2);
    }}
    .detail-richtext p {{
      margin: 0;
      color: var(--ink);
      font-size: var(--av-text-sm);
      line-height: 1.65;
      overflow-wrap: anywhere;
    }}
    .detail-empty {{
      padding: 12px;
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: var(--av-leading-snug);
    }}
    .detail-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
      padding: var(--av-spacing-3);
      border-top: 1px solid var(--line-subtle);
      background: color-mix(in oklab, var(--panel), var(--panel-subtle) 20%);
    }}
    .detail-footer-actions {{
      display: flex;
      align-items: center;
      gap: var(--av-spacing-2);
      flex-wrap: wrap;
    }}
    .health-item {{
      border: 1px solid var(--line-subtle);
      border-top: 3px solid var(--brand);
      border-radius: var(--av-radius-md);
      padding: 14px;
      background: var(--panel);
    }}
    .health-item span {{
      display: block;
      color: var(--muted);
      font-family: var(--font-sans);
      font-size: var(--av-text-xs);
      font-weight: 600;
      letter-spacing: 0;
      text-transform: none;
      margin-bottom: var(--av-spacing-2);
    }}
    .health-item strong {{
      display: block;
      font-family: var(--font-sans);
      font-size: var(--av-text-xl);
      line-height: 1.1;
      overflow-wrap: anywhere;
    }}
    .health-note {{
      margin: var(--av-spacing-3) 0 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .method-card,
    .faq-item,
    .method-disclaimer {{
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: 16px 18px;
    }}
    .method-card h3,
    .faq-item h3,
    .method-disclaimer strong {{
      display: block;
      margin: 0 0 var(--av-spacing-2);
      font-size: var(--av-text-lg);
      line-height: 1.25;
    }}
    .method-card p,
    .faq-item p,
    .method-disclaimer p {{
      margin: 0;
      color: var(--muted);
      font-size: var(--av-text-sm);
      line-height: 1.6;
    }}
    .method-disclaimer {{
      margin-top: var(--av-spacing-3);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 12%);
      border-color: color-mix(in oklab, var(--brand), white 74%);
    }}
    .faq-list {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--av-spacing-3);
      margin-top: var(--av-spacing-3);
    }}
    .hidden {{ display: none; }}

    @media (max-width: 980px) {{
      .hero-grid {{
        grid-template-columns: 1fr;
      }}
      .spotlight-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .funder-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .themes-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .pathways-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .method-grid,
      .faq-list {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .topic-brief-grid {{
        grid-template-columns: 1fr;
      }}
      .hero-stage {{
        padding: 16px;
      }}
      .sticky-bar {{
        align-items: flex-start;
        flex-wrap: wrap;
      }}
      .sticky-actions {{
        width: 100%;
        justify-content: space-between;
      }}
      .preset-grid,
      .filters {{
        grid-template-columns: 1fr 1fr;
      }}
      .filters .filter-block:first-child {{
        grid-column: 1 / -1;
      }}
      .health-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}

    @media (max-width: 760px) {{
      .shell {{
        width: min(100% - 24px, var(--container-max));
        padding-top: var(--av-spacing-2);
      }}
      .hero-band {{
        padding: 22px 18px 16px;
      }}
      .topic-brief {{
        padding: 14px 16px;
      }}
      .sticky-shell {{
        position: static;
        top: auto;
        z-index: auto;
        margin-bottom: var(--av-spacing-2);
        padding-top: 0;
        backdrop-filter: none;
      }}
      .sticky-bar {{
        display: grid;
        gap: var(--av-spacing-2);
        padding: 10px 12px;
      }}
      .topbar {{
        gap: var(--av-spacing-2);
        margin-bottom: var(--av-spacing-3);
      }}
      .hero-intro {{
        font-size: var(--av-text-base);
        line-height: 1.55;
      }}
      .hero-actions,
      .hero-pick-row {{
        width: 100%;
      }}
      .hero-actions > .button,
      .hero-pick-row > .button {{
        flex: 1 1 auto;
      }}
      .topbar-actions {{
        width: 100%;
        justify-items: stretch;
      }}
      .sticky-actions {{
        width: 100%;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--av-spacing-2);
      }}
      .utility-links {{
        justify-content: flex-start;
      }}
      .brand p {{
        max-width: 34rem;
        font-size: var(--av-text-sm);
        line-height: var(--av-leading-snug);
      }}
      .spotlight-card {{
        min-height: 224px;
      }}
      .pathway-card {{
        min-height: 214px;
      }}
      .hero-stage-title {{
        font-size: 22px;
      }}
      .focus-chip {{
        min-height: var(--control-height-sm);
        font-size: 11px;
      }}
      .grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
        width: 100%;
        gap: 0;
      }}
      .health-grid,
      .source-grid,
      .method-grid,
      .faq-list {{
        grid-template-columns: 1fr;
      }}
      .preset-grid,
      .filters {{
        grid-template-columns: 1fr;
      }}
      .panel {{
        padding-top: var(--av-spacing-5);
        margin-top: var(--av-spacing-5);
      }}
      .source-card {{
        display: grid;
        grid-template-columns: 32px minmax(0, 1fr) auto;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.75rem 0.85rem;
      }}
      .source-icon {{
        grid-column: 1;
        grid-row: 1 / 4;
        width: 32px;
        height: 32px;
        border-radius: var(--av-radius-md);
        font-size: 10px;
      }}
      .source-main,
      .source-url,
      .source-count {{
        grid-column: 2;
        min-width: 0;
        width: auto;
      }}
      .source-count {{
        flex-basis: auto;
        justify-self: stretch;
        text-align: left;
      }}
      .source-arrow {{
        grid-column: 3;
        grid-row: 1;
        margin-left: 0;
        padding-top: 4px;
      }}
      .opportunity-top {{
        grid-template-columns: 1fr;
      }}
      .side {{
        justify-content: flex-start;
        min-width: 0;
      }}
      .panel-actions,
      .filters-meta {{
        width: 100%;
        justify-content: space-between;
      }}
      .saved-views-head {{
        align-items: flex-start;
      }}
      .saved-actions {{
        width: 100%;
      }}
      .health-grid {{
        grid-template-columns: 1fr;
      }}
      .detail-drawer {{
        width: 100vw;
        border-left: 0;
      }}
      .detail-header,
      .detail-body,
      .detail-footer {{
        padding-left: var(--av-spacing-2);
        padding-right: var(--av-spacing-2);
      }}
      .detail-meta-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 560px) {{
      .hero-grid {{
        gap: var(--av-spacing-3);
        margin-bottom: var(--av-spacing-3);
      }}
      .hero-copy {{
        gap: var(--av-spacing-2);
      }}
      .grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}
      .spotlight-grid {{
        grid-template-columns: 1fr;
      }}
      .funder-grid {{
        grid-template-columns: 1fr;
      }}
      .themes-grid {{
        grid-template-columns: 1fr;
      }}
      .pathways-grid {{
        grid-template-columns: 1fr;
      }}
      .spotlight-card {{
        min-height: 0;
        padding: 16px;
      }}
      .theme-card {{
        min-height: 0;
        padding: 16px;
      }}
      .pathway-card {{
        min-height: 0;
        padding: 16px;
      }}
      .metric.sources {{
        grid-column: auto;
        border-left: 1px solid var(--line-subtle);
      }}
      .filters-meta {{
        align-items: flex-start;
        display: grid;
        grid-template-columns: 1fr;
        justify-items: start;
      }}
      .filter-summary {{
        width: 100%;
      }}
      .focus-row {{
        display: flex;
        flex-wrap: wrap;
        gap: var(--av-spacing-1);
      }}
      .hero-actions,
      .hero-pick-row {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .hero-actions > .button.primary {{
        grid-column: 1 / -1;
      }}
      .hero-stage {{
        gap: var(--av-spacing-2);
        padding-top: var(--av-spacing-2);
      }}
      .hero-point {{
        font-size: var(--av-text-xs);
        line-height: 1.45;
      }}
      .spotlight-copy h2 {{
        font-size: 24px;
      }}
      .pathway-card h3 {{
        font-size: var(--av-text-lg);
      }}
      .hero-picks {{
        display: none;
      }}
      .hero-stage-title {{
        font-size: 20px;
      }}
      .hero-point {{
        grid-template-columns: 24px minmax(0, 1fr);
        font-size: var(--av-text-sm);
      }}
      .hero-point-index {{
        width: 24px;
        height: 24px;
      }}
      .preset-row {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .focus-chip {{
        width: auto;
        min-height: 24px;
      }}
      .opportunity,
      .source-card,
      .health-item {{
        min-width: 0;
      }}
    }}

    @media (max-width: 480px) {{
      .brand-row {{
        gap: var(--av-spacing-1);
      }}
      .brand h1 {{ font-size: 24px; }}
      .hero-band {{
        padding: 10px 12px 8px;
      }}
      .topbar {{
        gap: var(--av-spacing-1);
        margin-bottom: var(--av-spacing-2);
      }}
      .brand {{
        gap: var(--av-spacing-1);
      }}
      .brand p {{
        font-size: var(--av-text-xs);
        line-height: 1.42;
      }}
      .focus-chip:last-child {{
        display: none;
      }}
      .hero-intro {{
        font-size: var(--av-text-sm);
        line-height: 1.48;
      }}
      .hero-actions {{
        gap: var(--av-spacing-1);
      }}
      .hero-actions > .button,
      .hero-pick-row > .button {{
        min-height: 34px;
      }}
      .hero-stage {{
        gap: var(--av-spacing-1);
        padding-top: var(--av-spacing-1);
      }}
      .hero-point:last-child {{
        display: none;
      }}
      .hero-stage-title {{
        font-size: 17px;
      }}
      .status-pill {{
        min-height: var(--control-height-sm);
        justify-content: center;
      }}
      .lang-link {{
        min-width: 38px;
        min-height: var(--control-height-sm);
      }}
      .metric {{
        min-height: 62px;
        padding: 10px;
      }}
      .metric span {{
        font-size: 10px;
        line-height: var(--av-leading-snug);
      }}
      .metric strong {{ font-size: 22px; }}
      .toolbar {{ gap: var(--av-spacing-1); }}
      .button.tab {{
        padding-left: var(--av-spacing-2);
        padding-right: var(--av-spacing-2);
      }}
      .spotlight-footer {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .pathway-footer {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .focus-row {{
        align-items: flex-start;
        gap: var(--av-spacing-1);
      }}
      .opportunity p {{
        -webkit-line-clamp: 2;
      }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      html {{
        scroll-behavior: auto;
      }}
      *,
      *::before,
      *::after {{
        animation-duration: 1ms !important;
        transition-duration: 1ms !important;
      }}
    }}
  </style>
</head>
<body>
  <main
    class="shell"
    data-api-base="{base}"
    data-lang="{escape(active_lang, quote=True)}"
    data-avds-component="admin-shell"
  >
    <section class="hero-band" data-avds-component="hero-band">
      <header class="topbar" data-avds-component="topbar">
        <div class="brand">
          <span class="eyebrow">{escape(str(copy["eyebrow"]))}</span>
          <div class="brand-row">
            <h1>{escape(str(copy["headline"]))}</h1>
          </div>
          <p>{escape(str(copy["subtitle"]))}</p>
          <div class="focus-row" aria-label="{escape(str(copy["focus_aria"]), quote=True)}">
            <span class="focus-chip">{escape(str(copy["focus_primary"]))}</span>
            <span class="focus-chip">{escape(str(copy["focus_secondary"]))}</span>
          </div>
        </div>
      </header>
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="hero-intro">{escape(str(copy["hero_intro"]))}</p>
          <div class="hero-actions">
            <button
              class="button primary"
              type="button"
              data-hero-reset="true"
              data-hero-view="opportunities"
              data-avds-component="button"
            >{escape(str(copy["hero_primary_cta"]))}</button>
            <button
              class="button soft"
              type="button"
              data-hero-reset="true"
              data-hero-view="opportunities"
              data-hero-audience="startup"
              data-hero-format="grants"
              data-avds-component="button"
            >{escape(str(copy["hero_secondary_cta"]))}</button>
            <button
              class="button subtle"
              type="button"
              data-hero-reset="true"
              data-hero-view="opportunities"
              data-hero-format="support"
              data-hero-region="kazakhstan"
              data-avds-component="button"
            >{escape(str(copy["hero_tertiary_cta"]))}</button>
          </div>
        </div>
        <section
          class="hero-stage"
          aria-label="{escape(str(copy["hero_picks_label"]), quote=True)}"
        >
          <span class="hero-stage-eyebrow">{escape(str(copy["hero_stage_eyebrow"]))}</span>
          <h2 class="hero-stage-title">{escape(str(copy["hero_stage_title"]))}</h2>
          <div class="hero-points">
            <div class="hero-point">
              <span class="hero-point-index">01</span>
              <span>{escape(str(copy["hero_stage_point_one"]))}</span>
            </div>
            <div class="hero-point">
              <span class="hero-point-index">02</span>
              <span>{escape(str(copy["hero_stage_point_two"]))}</span>
            </div>
            <div class="hero-point">
              <span class="hero-point-index">03</span>
              <span>{escape(str(copy["hero_stage_point_three"]))}</span>
            </div>
          </div>
          <div class="hero-picks">
            <span class="filter-label">{escape(str(copy["hero_picks_label"]))}</span>
            <div class="hero-pick-row">
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-audience="startup"
                data-hero-format="grants"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_startup"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-audience="business"
                data-hero-format="support"
                data-hero-region="kazakhstan"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_business"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-audience="farmer"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_farmer"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-audience="science"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_science"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-format="tenders"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_tenders"]))}</button>
            </div>
          </div>
        </section>
      </div>

      <section class="grid" aria-label="{escape(str(copy["metrics_aria"]), quote=True)}">
        <div class="metric avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_total"]))}</span>
          <strong id="metric-total">{items}</strong>
        </div>
        <div class="metric strong avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_relevant"]))}</span>
          <strong id="metric-strong">{relevant_items}</strong>
        </div>
        <div class="metric sources avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_sources"]))}</span>
          <strong id="metric-sources">{source_count}</strong>
        </div>
      </section>
    </section>

    <div class="sticky-shell" data-avds-component="sticky-shell">
      <div class="sticky-bar">
        <nav
          class="toolbar avds-tabs-list"
          aria-label="{escape(str(copy["views_aria"]), quote=True)}"
          data-avds-component="toolbar"
        >
          <button
            class="button tab avds-tabs-trigger"
            type="button"
            data-view="opportunities"
            data-avds-component="button"
            aria-pressed="true"
          >{escape(str(copy["tab_opportunities"]))}</button>
          <button
            class="button tab avds-tabs-trigger"
            type="button"
            data-view="sources"
            data-avds-component="button"
          >{escape(str(copy["tab_sources"]))}</button>
        </nav>
        <div class="sticky-actions">
          <div class="status-pill" id="status-pill" data-avds-component="status-pill">
            <span class="status-dot"></span>
            <span>{escape(str(copy["status_checking"]))}</span>
          </div>
          <div class="topbar-actions">
            <div class="utility-links">
              <a class="utility-link" href="{docs_href}">{escape(str(copy["api_docs"]))}</a>
              <a class="utility-link" href="#methodology-panel"
                >{escape(str(copy["methodology_link"]))}</a
              >
              <a class="utility-link" href="#health-panel">{escape(str(copy["status_link"]))}</a>
            </div>
            <div class="lang-switch" role="group" aria-label="{language_switch_label}">
              <a
                class="{lang_ru_class}"
                href="{ru_href}"
                hreflang="ru"
                lang="ru"
                {lang_ru_current}
              >RU</a>
              <a
                class="{lang_en_class}"
                href="{en_href}"
                hreflang="en"
                lang="en"
                {lang_en_current}
              >EN</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <section class="spotlight-section" aria-labelledby="spotlight-title">
      <div class="spotlight-copy">
        <span class="eyebrow">{escape(str(copy["spotlight_section_eyebrow"]))}</span>
        <h2 id="spotlight-title">{escape(str(copy["spotlight_section_title"]))}</h2>
        <p>{escape(str(copy["spotlight_section_description"]))}</p>
      </div>
      <div
        class="spotlight-grid"
        id="spotlight-grid"
        data-avds-component="spotlight-grid"
      ></div>
    </section>

    <section class="pathways-section" aria-labelledby="pathways-title">
      <div class="spotlight-copy">
        <span class="eyebrow">{escape(str(copy["pathways_section_eyebrow"]))}</span>
        <h2 id="pathways-title">{escape(str(copy["pathways_section_title"]))}</h2>
        <p>{escape(str(copy["pathways_section_description"]))}</p>
      </div>
      <div
        class="pathways-grid"
        id="pathways-grid"
        data-avds-component="pathways-grid"
      ></div>
    </section>

    <section class="themes-section" aria-labelledby="themes-title">
      <div class="spotlight-copy">
        <span class="eyebrow">{escape(str(copy["themes_section_eyebrow"]))}</span>
        <h2 id="themes-title">{escape(str(copy["themes_section_title"]))}</h2>
        <p>{escape(str(copy["themes_section_description"]))}</p>
      </div>
      <div
        class="themes-grid"
        id="themes-grid"
        data-avds-component="themes-grid"
      ></div>
    </section>

    <section class="funder-section" aria-labelledby="funders-title">
      <div class="spotlight-copy">
        <span class="eyebrow">{escape(str(copy["funder_section_eyebrow"]))}</span>
        <h2 id="funders-title">{escape(str(copy["funder_section_title"]))}</h2>
        <p>{escape(str(copy["funder_section_description"]))}</p>
      </div>
      <div
        class="funder-grid"
        id="funder-grid"
        data-avds-component="funder-grid"
      >
        <div class="message">{escape(str(copy["loading_opportunities"]))}</div>
      </div>
    </section>

    <section class="panel primary" id="opportunities-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["opportunities_title"]))}</h2>
          <p id="opportunities-description">{escape(str(copy["opportunities_description"]))}</p>
        </div>
      </div>
      <div class="preset-grid">
        <div class="preset-group" aria-label="{escape(str(copy["audience_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["audience_label"]))}</span>
          <div
            class="preset-row"
            id="audience-presets"
            data-avds-component="preset-row"
          ></div>
        </div>
        <div class="preset-group" aria-label="{escape(str(copy["format_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["format_label"]))}</span>
          <div
            class="preset-row"
            id="format-presets"
            data-avds-component="preset-row"
          ></div>
        </div>
        <div class="preset-group" aria-label="{escape(str(copy["topic_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["topic_label"]))}</span>
          <div
            class="preset-row"
            id="topic-presets"
            data-avds-component="preset-row"
          ></div>
        </div>
      </div>
      <div class="filters" aria-label="{escape(str(copy["opportunities_title"]), quote=True)}">
        <label class="filter-block" for="search">
          <span class="filter-label">{escape(str(copy["search_label"]))}</span>
          <input
            class="field avds-field"
            id="search"
            type="search"
            placeholder="{escape(str(copy["search_placeholder"]), quote=True)}"
            data-avds-component="field"
          >
        </label>
        <label class="filter-block" for="scope-filter">
          <span class="filter-label">{escape(str(copy["scope_label"]))}</span>
          <select
            class="field avds-field"
            id="scope-filter"
            aria-label="{escape(str(copy["scope_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="open" selected>{escape(str(copy["scope_open"]))}</option>
            <option value="all">{escape(str(copy["scope_all"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="lifecycle-filter">
          <span class="filter-label">{escape(str(copy["lifecycle_label"]))}</span>
          <select
            class="field avds-field"
            id="lifecycle-filter"
            aria-label="{escape(str(copy["lifecycle_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="all" selected>{escape(str(copy["lifecycle_all"]))}</option>
            <option value="open">{escape(str(copy["lifecycle_open"]))}</option>
            <option value="forecast">{escape(str(copy["lifecycle_forecast"]))}</option>
            <option value="closing_soon">{escape(str(copy["lifecycle_closing_soon"]))}</option>
            <option value="rolling">{escape(str(copy["lifecycle_rolling"]))}</option>
            <option value="closed">{escape(str(copy["lifecycle_closed"]))}</option>
            <option value="awarded">{escape(str(copy["lifecycle_awarded"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="region-filter">
          <span class="filter-label">{escape(str(copy["region_label"]))}</span>
          <select
            class="field avds-field"
            id="region-filter"
            aria-label="{escape(str(copy["region_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="all" selected>{escape(str(copy["region_all"]))}</option>
            <option value="kazakhstan">{escape(str(copy["region_kazakhstan"]))}</option>
            <option value="central_asia">{escape(str(copy["region_central_asia"]))}</option>
            <option value="global">{escape(str(copy["region_global"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="deadline-filter">
          <span class="filter-label">{escape(str(copy["deadline_filter_label"]))}</span>
          <select
            class="field avds-field"
            id="deadline-filter"
            aria-label="{escape(str(copy["deadline_filter_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="all" selected>{escape(str(copy["deadline_filter_all"]))}</option>
            <option value="soon">{escape(str(copy["deadline_filter_soon"]))}</option>
            <option value="month">{escape(str(copy["deadline_filter_month"]))}</option>
            <option value="rolling">{escape(str(copy["deadline_filter_rolling"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="sort-filter">
          <span class="filter-label">{escape(str(copy["sort_label"]))}</span>
          <select
            class="field avds-field"
            id="sort-filter"
            aria-label="{escape(str(copy["sort_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="priority" selected>{escape(str(copy["sort_priority"]))}</option>
            <option value="deadline">{escape(str(copy["sort_deadline"]))}</option>
            <option value="updated">{escape(str(copy["sort_updated"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="score-filter">
          <span class="filter-label">{escape(str(copy["min_score_label"]))}</span>
          <select
            class="field avds-field"
            id="score-filter"
            aria-label="{escape(str(copy["min_score_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="0">{escape(str(copy["all_scores"]))}</option>
            <option value="0.3" selected>{escape(str(copy["score_option_03"]))}</option>
            <option value="0.5">{escape(str(copy["score_option_05"]))}</option>
            <option value="0.7">{escape(str(copy["score_option_07"]))}</option>
          </select>
        </label>
        <label class="filter-block" for="source-filter">
          <span class="filter-label">{escape(str(copy["source_label"]))}</span>
          <select
            class="field avds-field"
            id="source-filter"
            aria-label="{escape(str(copy["source_aria"]), quote=True)}"
            data-avds-component="field"
          >
            <option value="all">{escape(str(copy["all_sources"]))}</option>
          </select>
        </label>
      </div>
      <div class="filters-meta">
        <div id="filter-summary" class="filter-summary" data-avds-component="filter-summary"></div>
        <button
          class="text-button"
          type="button"
          id="clear-filters"
          data-avds-component="button"
        >{escape(str(copy["clear_filters"]))}</button>
      </div>
      <div
        class="saved-views"
        aria-label="{escape(str(copy["collections_aria"]), quote=True)}"
        data-avds-component="saved-views"
      >
        <div class="saved-views-head">
          <span class="filter-label">{escape(str(copy["collections_label"]))}</span>
          <div class="saved-actions">
            <button
              class="text-button"
              type="button"
              id="save-view"
              data-avds-component="button"
            >{escape(str(copy["save_view"]))}</button>
            <button
              class="text-button"
              type="button"
              id="share-view"
              data-avds-component="button"
            >{escape(str(copy["share_view"]))}</button>
          </div>
        </div>
        <div id="saved-views" class="saved-view-row">
          <span class="saved-empty">{escape(str(copy["collections_empty"]))}</span>
        </div>
        <div
          id="saved-view-notice"
          class="saved-view-notice hidden"
          aria-live="polite"
          aria-label="{escape(str(copy["saved_view_status_label"]), quote=True)}"
        ></div>
      </div>
      <div
        id="topic-brief"
        class="topic-brief hidden"
        data-avds-component="topic-brief"
      ></div>
      <div
        id="opportunities-message"
        class="message"
        data-avds-component="message"
      >{escape(str(copy["loading_opportunities"]))}</div>
      <div id="opportunities-list" class="list" aria-live="polite"></div>
      <div id="load-more-wrap" class="list-actions hidden">
        <button
          class="button slim"
          type="button"
          id="load-more"
          data-avds-component="button"
        >{escape(str(copy["load_more"]))}</button>
      </div>
    </section>

    <section class="panel" id="sources-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["sources_title"]))}</h2>
          <p>{escape(str(copy["sources_description"]))}</p>
        </div>
        <div class="panel-actions">
          <span class="panel-summary" id="source-summary">{loading_sources_label}</span>
          <button
            class="button slim"
            type="button"
            id="toggle-sources"
            data-avds-component="button"
          >{escape(str(copy["show_all_sources"]))}</button>
        </div>
      </div>
      <div id="source-list" class="source-grid"></div>
    </section>

    <section class="panel" id="health-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["health_title"]))}</h2>
          <p>{escape(str(copy["health_description"]))}</p>
        </div>
        <div class="panel-actions">
          <button
            class="button slim"
            type="button"
            id="reload"
            data-avds-component="button"
          >{escape(str(copy["reload_live_data"]))}</button>
        </div>
      </div>
      <div class="health-grid">
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["api_status"]))}</span>
          <strong id="health-status">{initial_health_status}</strong>
        </div>
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["stored_items"]))}</span>
          <strong id="health-items">{initial_health_items}</strong>
        </div>
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["health_sources"]))}</span>
          <strong id="health-sources">{initial_health_sources}</strong>
        </div>
      </div>
      <p class="health-note" id="health-note">{escape(str(copy["health_note_loading"]))}</p>
    </section>

    <section class="panel" id="methodology-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["methodology_title"]))}</h2>
          <p>{escape(str(copy["methodology_description"]))}</p>
        </div>
      </div>
      <div class="method-grid" data-avds-component="method-grid">
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_sources_title"]))}</h3>
          <p>{escape(str(copy["method_card_sources_text"]))}</p>
        </article>
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_relevance_title"]))}</h3>
          <p>{escape(str(copy["method_card_relevance_text"]))}</p>
        </article>
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_trust_title"]))}</h3>
          <p>{escape(str(copy["method_card_trust_text"]))}</p>
        </article>
      </div>
      <div class="method-disclaimer" data-avds-component="method-disclaimer">
        <strong>{escape(str(copy["method_disclaimer_title"]))}</strong>
        <p>{escape(str(copy["method_disclaimer_text"]))}</p>
      </div>
      <div class="faq-list" data-avds-component="faq-list">
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q1"]))}</h3>
          <p>{escape(str(copy["faq_a1"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q2"]))}</h3>
          <p>{escape(str(copy["faq_a2"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q3"]))}</h3>
          <p>{escape(str(copy["faq_a3"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q4"]))}</h3>
          <p>{escape(str(copy["faq_a4"]))}</p>
        </article>
      </div>
    </section>
  </main>

  <div
    class="detail-backdrop"
    id="detail-backdrop"
    hidden
    aria-hidden="true"
  ></div>
  <aside
    class="detail-drawer"
    id="detail-drawer"
    hidden
    aria-hidden="true"
    aria-label="{escape(str(copy["detail_panel_label"]), quote=True)}"
  >
    <div class="detail-header">
      <div>
        <span class="eyebrow">{escape(str(copy["detail_shell_title"]))}</span>
        <h2 id="detail-title">{escape(str(copy["detail_title_fallback"]))}</h2>
        <p class="detail-status" id="detail-status">{escape(str(copy["detail_loading"]))}</p>
      </div>
      <button
        class="button slim detail-close"
        type="button"
        id="detail-close"
        data-avds-component="button"
      >{escape(str(copy["detail_close"]))}</button>
    </div>
    <div class="detail-body">
      <div class="detail-empty" id="detail-empty">{escape(str(copy["detail_loading"]))}</div>
      <div class="detail-fit hidden" id="detail-fit">
        <h3>{escape(str(copy["detail_fit_title"]))}</h3>
        <p id="detail-fit-summary">{escape(str(copy["detail_fit_review"]))}</p>
        <div class="fit-pills" id="detail-fit-pills"></div>
      </div>
      <div class="detail-meta hidden" id="detail-meta">
        <h3>{escape(str(copy["detail_meta_title"]))}</h3>
        <div class="detail-meta-grid" id="detail-meta-grid"></div>
      </div>
      <div class="detail-sections hidden" id="detail-sections">
        <h3>{escape(str(copy["detail_sections_title"]))}</h3>
        <div class="detail-richtext" id="detail-sections-body"></div>
      </div>
    </div>
    <div class="detail-footer">
      <div class="detail-footer-actions">
        <a
          class="button slim soft"
          href="#"
          id="detail-open-page"
          data-avds-component="button"
        >{escape(str(copy["detail_open_page"]))}</a>
        <a
          class="button slim"
          href="#"
          id="detail-open-source"
          target="_blank"
          rel="noopener"
          data-avds-component="button"
        >{escape(str(copy["detail_open_source"]))}</a>
        <a
          class="button slim hidden"
          href="#"
          id="detail-open-application"
          target="_blank"
          rel="noopener"
          data-avds-component="button"
        >{escape(str(copy["detail_open_application"]))}</a>
      </div>
    </div>
  </aside>

  <script>
    const copy = {copy_json};
    const root = document.querySelector("[data-api-base]");
    const datasetApiBase = root.dataset.apiBase || "";
    const deriveApiBase = () => {{
      if (datasetApiBase) return datasetApiBase.replace(/\\/$/, "");
      const path = window.location.pathname || "/";
      if (!path || path === "/") return "";
      return path.endsWith("/") ? path.slice(0, -1) : path;
    }};
    const apiBase = deriveApiBase();
    const state = {{
      health: null,
      coverage: null,
      sources: [],
      funders: [],
      items: [],
      sort: "priority",
      minScore: 0.3,
      query: "",
      source: "all",
      audience: "all",
      format: "all",
      topic: "all",
      lifecycle: "all",
      region: "all",
      deadlineMode: "all",
      includeArchived: false,
      showAllSources: false,
      visibleLimit: 15,
      lastCheckedAt: "",
      detailId: "",
      detailFallbackUrl: "",
      detailItem: null
    }};
    const DEFAULT_SORT = "priority";
    const DEFAULT_SCORE = 0.3;
    const ALL_INDEX_SCORE = 0;
    const DEFAULT_AUDIENCE = "all";
    const DEFAULT_FORMAT = "all";
    const DEFAULT_TOPIC = "all";
    const DEFAULT_LIFECYCLE = "all";
    const DEFAULT_REGION = "all";
    const DEFAULT_DEADLINE = "all";
    const DEFAULT_VISIBLE_ITEMS = 15;
    const COLLAPSED_SOURCES = 5;
    const SAVED_VIEW_STORAGE_KEY = "grantRadarSavedViews.v1";
    const formatNumber = new Intl.NumberFormat(copy.locale || "ru-KZ");
    const formatScoreNumber = new Intl.NumberFormat(copy.locale || "ru-KZ", {{
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }});

    const $ = (selector) => document.querySelector(selector);
    const labelMap = copy.label_map || copy.labelMap || {{}};
    const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (char) => ({{
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }}[char]));
    const interpolate = (template, values = {{}}) => Object.entries(values).reduce(
      (result, [key, value]) => result.split(`{{${{key}}}}`).join(String(value)),
      template || ""
    );
    const text = (key, values) => interpolate(copy[key] || "", values);
    const formatScore = (score) => formatScoreNumber.format(Number(score || 0));
    const normalizeKey = (value) => String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[\\s-]+/g, "_");
    const supportedLifecycleValues = new Set([
      "open",
      "forecast",
      "closing_soon",
      "rolling",
      "closed",
      "awarded"
    ]);
    const rawObject = (item) => (
      item && item.raw && typeof item.raw === "object" ? item.raw : {{}}
    );
    function fallbackFunderSlug(value) {{
      const normalized = String(value || "").trim().toLowerCase().replace(/\\s+/g, " ");
      const ascii = normalized
        .normalize("NFKD")
        .replace(/[\\u0300-\\u036f]/g, "")
        .replace(/[^\\x00-\\x7F]/g, "");
      const slug = ascii.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      if (slug) return slug;
      let hash = 0;
      for (const char of normalized) {{
        hash = ((hash * 31) + char.charCodeAt(0)) >>> 0;
      }}
      return `funder-${{hash.toString(16).padStart(8, "0").slice(0, 10)}}`;
    }}
    function funderSlug(item) {{
      const raw = rawObject(item);
      return item.funder_slug || raw.funder_slug
        || fallbackFunderSlug(item.funder || item.source || "funder");
    }}
    function funderPageHref(funderSlugValue) {{
      if (!funderSlugValue) return "#";
      return withLang(`${{apiBase}}/funder/${{encodeURIComponent(String(funderSlugValue))}}`);
    }}
    function lifecycleLabel(value) {{
      return copy[`lifecycle_${{value}}`] || humanizeLabel(value);
    }}
    function itemLifecycle(item) {{
      const raw = rawObject(item);
      const declared = normalizeKey(
        item.lifecycle || item.opportunity_status || raw.lifecycle || raw.opportunity_status || ""
      );
      if (supportedLifecycleValues.has(declared)) {{
        return declared;
      }}
      if (declared === "upcoming" || declared === "draft") {{
        return "forecast";
      }}
      if (declared === "archived") {{
        return "closed";
      }}
      const statusBlob = [
        raw.status,
        raw.status_raw,
        raw.project_status,
        raw.projectstatusdisplay,
        raw.notice_type
      ].join(" ").toLowerCase();
      const forecastSignal = new RegExp(
        "forecast|pipeline|planned|preparation|upcoming|concept|prequalification|pre-solicitation"
      );
      if (/(award|winner|selected|contract signed|completed|implemented)/.test(statusBlob)) {{
        return "awarded";
      }}
      if (
        raw.deadline_policy === "closed"
        || hasTag(item, "closed")
        || /(closed|expired|cancelled|canceled|archived)/.test(statusBlob)
      ) {{
        return "closed";
      }}
      if (
        hasTag(item, "project_pipeline")
        || forecastSignal.test(statusBlob)
      ) {{
        return "forecast";
      }}
      if (raw.deadline_policy === "rolling" || hasTag(item, "rolling")) {{
        return "rolling";
      }}
      const days = daysUntilDeadline(item);
      if (days !== null && days >= 0 && days <= 14) {{
        return "closing_soon";
      }}
      if (days !== null && days < 0) {{
        return "closed";
      }}
      return "open";
    }}
    function isStartupAudience(item) {{
      return matchesAnyTag(item, [
        "startup",
        "startup_support",
        "cloud_credits",
        "venture",
        "private_equity",
        "microsoft_founders_hub",
        "google_cloud_startup",
        "cloudflare_startups",
        "mongodb_startups",
        "nvidia_inception",
        "aws_activate"
      ]) || matchesType(item, ["accelerator", "cloud_credit"]);
    }}

    function isFarmerAudience(item) {{
      return matchesAnyTag(item, [
        "crop_production",
        "livestock",
        "gosagro",
        "kazagrofinance",
        "agrocredit",
        "animal_health"
      ]) || (
        hasTag(item, "agrotech")
        && presetById(FORMAT_PRESETS, "support").matches(item)
      );
    }}

    function isPublicSectorOpportunity(item) {{
      return matchesType(item, ["tender"]) && matchesAnyTag(item, [
        "public_sector",
        "project_pipeline",
        "development",
        "govtech",
        "infrastructure"
      ]);
    }}
    const detailStatusCopy = {{
      ok: copy.detail_status_ok,
      structured_only: copy.detail_status_structured_only,
      blocked: copy.detail_status_blocked,
      not_allowed: copy.detail_status_not_allowed,
      too_large: copy.detail_status_too_large,
      unsupported_media: copy.detail_status_unsupported_media,
      parse_error: copy.detail_status_parse_error
    }};
    const AUDIENCE_PRESETS = [
      {{
        id: "all",
        label: copy.audience_all,
        matches: () => true
      }},
      {{
        id: "startup",
        label: copy.audience_startup,
        matches: (item) => isStartupAudience(item)
      }},
      {{
        id: "business",
        label: copy.audience_business,
        matches: (item) => matchesAnyTag(item, [
          "business_support",
          "sme",
          "domestic_support",
          "state_program",
          "subsidy",
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing",
          "employment",
          "industry",
          "export",
          "trade",
          "investment",
          "qazindustry",
          "qaztrade",
          "damu",
          "enbek",
          "baiterek",
          "bgov",
          "kdb",
          "idf"
        ])
      }},
      {{
        id: "farmer",
        label: copy.audience_farmer,
        matches: (item) => isFarmerAudience(item)
      }},
      {{
        id: "ngo",
        label: copy.audience_ngo,
        matches: (item) => matchesAnyTag(item, [
          "ngo",
          "civil_society",
          "media",
          "journalism",
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ]) || matchesAnyEligibility(item, [
          "некоммерческая организация",
          "nonprofit",
          "ngo"
        ])
      }},
      {{
        id: "science",
        label: copy.audience_science,
        matches: (item) => matchesAnyTag(item, [
          "science",
          "commercialization",
          "research",
          "education",
          "science_fund",
          "ncste"
        ]) || matchesAnyEligibility(item, [
          "образование_организация",
          "образовательный_партнер",
          "research",
          "university"
        ])
      }}
    ];
    const FORMAT_PRESETS = [
      {{
        id: "all",
        label: copy.format_all,
        matches: () => true
      }},
      {{
        id: "grants",
        label: copy.format_grants,
        matches: (item) => matchesType(item, ["grant", "contest", "fellowship"])
      }},
      {{
        id: "support",
        label: copy.format_support,
        matches: (item) => matchesAnyTag(item, [
          "subsidy",
          "domestic_support",
          "state_program",
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing",
          "employment",
          "business_support",
          "investment"
        ])
      }},
      {{
        id: "accelerators",
        label: copy.format_accelerators,
        matches: (item) => matchesType(item, ["accelerator", "cloud_credit"])
          || matchesAnyTag(item, [
            "startup_support",
            "cloud_credits",
            "microsoft_founders_hub",
            "google_cloud_startup",
            "cloudflare_startups",
            "mongodb_startups",
            "nvidia_inception"
          ])
      }},
      {{
        id: "tenders",
        label: copy.format_tenders,
        matches: (item) => matchesType(item, ["tender"])
          || matchesAnyTag(item, ["procurement", "tender", "consulting", "ecepp"])
      }}
    ];
    const TOPIC_PRESETS = [
      {{
        id: "all",
        label: copy.topic_all,
        matches: () => true
      }},
      {{
        id: "ai",
        label: copy.topic_ai,
        matches: (item) => matchesAnyTag(item, [
          "ai",
          "digital_skills",
          "digitalization",
          "digital",
          "cloud_credits"
        ])
      }},
      {{
        id: "agro",
        label: copy.topic_agro,
        matches: (item) => matchesAnyTag(item, [
          "agrotech",
          "vettech",
          "ecotech",
          "green_transition",
          "agriculture",
          "crop_production",
          "livestock",
          "animal_health",
          "water",
          "climate_change"
        ])
      }},
      {{
        id: "science",
        label: copy.topic_science,
        matches: (item) => matchesAnyTag(item, [
          "education",
          "edtech",
          "teacher_training",
          "higher_education",
          "science",
          "research",
          "commercialization"
        ]) || matchesAnyEligibility(item, [
          "образование_организация",
          "образовательный_партнер",
          "research",
          "university"
        ])
      }},
      {{
        id: "public",
        label: copy.topic_public,
        matches: (item) => matchesAnyTag(item, [
          "public_sector",
          "project_pipeline",
          "development",
          "govtech",
          "infrastructure",
          "procurement"
        ]) || matchesType(item, ["tender"])
      }},
      {{
        id: "ngo",
        label: copy.topic_ngo,
        matches: (item) => matchesAnyTag(item, [
          "ngo",
          "civil_society",
          "media",
          "journalism",
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ]) || matchesAnyEligibility(item, [
          "некоммерческая организация",
          "nonprofit",
          "ngo"
        ])
      }},
      {{
        id: "business",
        label: copy.topic_business,
        matches: (item) => matchesAnyTag(item, [
          "business_support",
          "state_program",
          "subsidy",
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing",
          "industry",
          "investment",
          "sme",
          "export",
          "trade"
        ])
      }}
    ];
    const REGION_FILTERS = [
      {{
        id: "all",
        label: copy.region_all,
        matches: () => true
      }},
      {{
        id: "kazakhstan",
        label: copy.region_kazakhstan,
        matches: (item) => regionalPriority(item) >= 3
      }},
      {{
        id: "central_asia",
        label: copy.region_central_asia,
        matches: (item) => regionalPriority(item) === 2
      }},
      {{
        id: "global",
        label: copy.region_global,
        matches: (item) => regionalPriority(item) <= 1
      }}
    ];
    const LIFECYCLE_FILTERS = [
      {{
        id: "all",
        label: copy.lifecycle_all,
        matches: () => true
      }},
      {{
        id: "open",
        label: copy.lifecycle_open,
        matches: (item) => itemLifecycle(item) === "open"
      }},
      {{
        id: "forecast",
        label: copy.lifecycle_forecast,
        matches: (item) => itemLifecycle(item) === "forecast"
      }},
      {{
        id: "closing_soon",
        label: copy.lifecycle_closing_soon,
        matches: (item) => itemLifecycle(item) === "closing_soon"
      }},
      {{
        id: "rolling",
        label: copy.lifecycle_rolling,
        matches: (item) => itemLifecycle(item) === "rolling"
      }},
      {{
        id: "closed",
        label: copy.lifecycle_closed,
        matches: (item) => itemLifecycle(item) === "closed"
      }},
      {{
        id: "awarded",
        label: copy.lifecycle_awarded,
        matches: (item) => itemLifecycle(item) === "awarded"
      }}
    ];
    const DEADLINE_FILTERS = [
      {{
        id: "all",
        label: copy.deadline_filter_all,
        matches: () => true
      }},
      {{
        id: "soon",
        label: copy.deadline_filter_soon,
        matches: (item) => {{
          const days = daysUntilDeadline(item);
          return days !== null && days >= 0 && days <= 14;
        }}
      }},
      {{
        id: "month",
        label: copy.deadline_filter_month,
        matches: (item) => {{
          const days = daysUntilDeadline(item);
          return days !== null && days >= 0 && days <= 31;
        }}
      }},
      {{
        id: "rolling",
        label: copy.deadline_filter_rolling,
        matches: (item) => !item.deadline
      }}
    ];
    const SORT_OPTIONS = [
      {{
        id: "priority",
        label: copy.sort_priority
      }},
      {{
        id: "deadline",
        label: copy.sort_deadline
      }},
      {{
        id: "updated",
        label: copy.sort_updated
      }}
    ];
    const SCORE_OPTIONS = [
      {{
        id: "0",
        value: 0,
        label: copy.all_scores
      }},
      {{
        id: "0.3",
        value: 0.3,
        label: copy.score_option_03
      }},
      {{
        id: "0.5",
        value: 0.5,
        label: copy.score_option_05
      }},
      {{
        id: "0.7",
        value: 0.7,
        label: copy.score_option_07
      }}
    ];

    function metadataLabel(key) {{
      const map = copy.detail_meta_labels || {{}};
      return map[key] || humanizeLabel(key);
    }}

    function metadataValue(entry) {{
      const key = String(entry.key || "");
      const value = String(entry.value || "");
      const normalizedValue = normalizeKey(value);
      const hasMappedLabel = Boolean(labelMap[value] || labelMap[normalizedValue]);
      if (key === "source") return humanizeLabel(value);
      if (
        hasMappedLabel
        && ["funder", "country", "region", "deadline_policy", "status", "notice_type"].includes(key)
      ) {{
        return humanizeLabel(value);
      }}
      return value;
    }}

    function detailStatusText(status) {{
      return detailStatusCopy[status] || copy.detail_status_structured_only;
    }}

    function withLang(path) {{
      const [pathname, query = ""] = String(path || "").split("?");
      const params = new URLSearchParams(query);
      params.set("lang", copy.lang || "ru");
      const serialized = params.toString();
      return serialized ? `${{pathname}}?${{serialized}}` : pathname;
    }}

    function opportunityPageHref(opportunityId) {{
      if (!opportunityId) return "#";
      return withLang(`${{apiBase}}/opportunity/${{encodeURIComponent(String(opportunityId))}}`);
    }}

    function renderTextBlocks(value) {{
      const paragraphs = String(value || "")
        .split(/\\n+/)
        .map((entry) => cleanSummaryText(entry) || entry.trim())
        .filter(Boolean);
      return paragraphs.map((entry) => `<p>${{escapeHtml(entry)}}</p>`).join("");
    }}

    function renderDetailFit(item) {{
      const root = $("#detail-fit");
      const summary = $("#detail-fit-summary");
      const pills = $("#detail-fit-pills");
      if (!item) {{
        root.classList.add("hidden");
        summary.textContent = copy.detail_fit_review;
        pills.innerHTML = "";
        return;
      }}
      summary.textContent = fitSummaryText(item);
      pills.innerHTML = fitPillsMarkup(item);
      root.classList.remove("hidden");
    }}

    function openDetailShell() {{
      document.body.classList.add("modal-open");
      $("#detail-backdrop").hidden = false;
      $("#detail-drawer").hidden = false;
      window.requestAnimationFrame(() => {{
        $("#detail-backdrop").classList.add("open");
        $("#detail-drawer").classList.add("open");
      }});
      $("#detail-drawer").setAttribute("aria-hidden", "false");
    }}

    function closeDetailShell() {{
      state.detailId = "";
      state.detailFallbackUrl = "";
      state.detailItem = null;
      $("#detail-backdrop").classList.remove("open");
      $("#detail-drawer").classList.remove("open");
      $("#detail-drawer").setAttribute("aria-hidden", "true");
      document.body.classList.remove("modal-open");
      window.setTimeout(() => {{
        if ($("#detail-drawer").classList.contains("open")) return;
        $("#detail-backdrop").hidden = true;
        $("#detail-drawer").hidden = true;
      }}, 180);
    }}

    function renderDetailLoading() {{
      $("#detail-title").textContent = copy.detail_title_fallback;
      $("#detail-status").textContent = copy.detail_loading;
      $("#detail-empty").textContent = copy.detail_loading;
      $("#detail-empty").classList.remove("hidden");
      renderDetailFit(state.detailItem);
      $("#detail-meta").classList.add("hidden");
      $("#detail-sections").classList.add("hidden");
      $("#detail-meta-grid").innerHTML = "";
      $("#detail-sections-body").innerHTML = "";
      $("#detail-open-source").setAttribute("href", state.detailFallbackUrl || "#");
      $("#detail-open-page").setAttribute("href", opportunityPageHref(state.detailId));
      $("#detail-open-application").classList.add("hidden");
    }}

    function renderDetailFailure() {{
      $("#detail-title").textContent = copy.detail_title_fallback;
      $("#detail-status").textContent = copy.detail_error;
      $("#detail-empty").textContent = copy.detail_error;
      $("#detail-empty").classList.remove("hidden");
      renderDetailFit(state.detailItem);
      $("#detail-meta").classList.add("hidden");
      $("#detail-sections").classList.add("hidden");
      $("#detail-open-source").setAttribute("href", state.detailFallbackUrl || "#");
      $("#detail-open-page").setAttribute("href", opportunityPageHref(state.detailId));
      $("#detail-open-application").classList.add("hidden");
    }}

    function renderDetail(detail) {{
      const title = detail && detail.title ? detail.title : copy.detail_title_fallback;
      const statusText = detailStatusText(detail.detail_fetch_status);
      const metadata = Array.isArray(detail.metadata) ? detail.metadata.filter(
        (entry) => entry && entry.key && entry.value
      ) : [];
      const sections = Array.isArray(detail.detail_sections) ? detail.detail_sections.filter(
        (section) => section && section.text
      ) : [];
      $("#detail-title").textContent = title;
      $("#detail-status").textContent = statusText;
      $("#detail-open-source").setAttribute(
        "href",
        detail.source_url || state.detailFallbackUrl || "#"
      );
      $("#detail-open-page").setAttribute("href", opportunityPageHref(detail.id));
      renderDetailFit(detail);

      const applicationButton = $("#detail-open-application");
      if (detail.application_url) {{
        applicationButton.setAttribute("href", detail.application_url);
        applicationButton.classList.remove("hidden");
      }} else {{
        applicationButton.classList.add("hidden");
      }}

      const metaGrid = $("#detail-meta-grid");
      metaGrid.innerHTML = metadata.map((entry) => `
        <div class="detail-meta-item">
          <span>${{escapeHtml(metadataLabel(entry.key))}}</span>
          <strong>${{escapeHtml(metadataValue(entry))}}</strong>
        </div>
      `).join("");
      $("#detail-meta").classList.toggle("hidden", !metadata.length);

      const sectionBody = $("#detail-sections-body");
      sectionBody.innerHTML = sections.map((section) => `
        <section class="detail-section-block">
          <h3>${{escapeHtml(section.heading || copy.detail_source_excerpt)}}</h3>
          ${{renderTextBlocks(section.text)}}
        </section>
      `).join("");
      $("#detail-sections").classList.toggle("hidden", !sections.length);

      const emptyMessage = $("#detail-empty");
      if (sections.length || metadata.length) {{
        emptyMessage.classList.add("hidden");
      }} else {{
        emptyMessage.textContent = copy.detail_empty;
        emptyMessage.classList.remove("hidden");
      }}
    }}

    async function openOpportunityDetail(opportunityId, fallbackUrl = "") {{
      if (!opportunityId) return;
      state.detailId = opportunityId;
      state.detailFallbackUrl = fallbackUrl;
      state.detailItem = state.items.find(
        (item) => String(item.id) === String(opportunityId)
      ) || null;
      openDetailShell();
      renderDetailLoading();
      try {{
        const detail = await fetchJson(withLang(`/opportunities/${{opportunityId}}`));
        if (state.detailId !== opportunityId) return;
        renderDetail(detail);
      }} catch (error) {{
        if (state.detailId !== opportunityId) return;
        renderDetailFailure();
      }}
    }}

    async function fetchJson(path) {{
      const response = await fetch(`${{apiBase}}${{path}}`, {{
        headers: {{ Accept: "application/json" }}
      }});
      if (!response.ok) {{
        throw new Error(`Request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      return response.json();
    }}

    function scoreClass(score) {{
      if (score >= 0.8) return "good";
      if (score >= 0.5) return "warn";
      return "low";
    }}

    function hasTag(item, tagName) {{
      const tags = Array.isArray(item.tags) ? item.tags : [];
      return tags.some((tag) => String(tag).toLowerCase() === tagName);
    }}

    function sourceBadge(source) {{
      const isWatchlist = hasTag(source, "watchlist");
      const label = isWatchlist ? copy.watchlist_badge : copy.direct_badge;
      const cls = isWatchlist ? "badge watchlist" : "badge";
      return `<span class="${{cls}}" data-avds-component="badge">${{escapeHtml(label)}}</span>`;
    }}

    function sourceContextLabel(source) {{
      return hasTag(source, "watchlist")
        ? copy.source_watchlist_note
        : copy.source_direct_note;
    }}

    function sourceIconVariant(source) {{
      const variants = ["blue", "green", "amber", "violet", "slate", "red"];
      const key = String(source.slug || source.name || "");
      const hash = Array.from(key).reduce((sum, char) => sum + char.charCodeAt(0), 0);
      return variants[hash % variants.length];
    }}

    function sourceInitials(source) {{
      const label = String(source.name || humanizeLabel(source.slug) || "GR");
      const words = label
        .replace(/[^0-9A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]+/g, " ")
        .trim()
        .split(/\\s+/)
        .filter(Boolean);
      const initials = words.length > 1
        ? `${{words[0][0] || ""}}${{words[1][0] || ""}}`
        : label.slice(0, 2);
      return (initials || "GR").toUpperCase();
    }}

    function itemBadges(item) {{
      const badges = [];
      const lifecycle = itemLifecycle(item);
      if (lifecycle && lifecycle !== "open") {{
        badges.push(
          `<span class="badge lifecycle" data-avds-component="badge">`
          + `${{escapeHtml(lifecycleLabel(lifecycle))}}</span>`
        );
      }}
      const regionalBadge = regionalBadgeLabel(item);
      if (regionalBadge) {{
        badges.push(
          `<span class="badge regional" data-avds-component="badge">`
          + `${{escapeHtml(regionalBadge)}}</span>`
        );
      }}
      if (hasTag(item, "watchlist")) {{
        badges.push(
          `<span class="badge watchlist" data-avds-component="badge">`
          + `${{escapeHtml(copy.watchlist_badge)}}</span>`
        );
      }}
      return badges.join("");
    }}

    function shortUrl(value) {{
      try {{
        const url = new URL(value);
        const host = url.hostname.startsWith("www.")
          ? url.hostname.slice(4)
          : url.hostname;
        return host;
      }} catch {{
        return value || copy.unknown_url;
      }}
    }}

    function humanizeLabel(value) {{
      const key = String(value || "").trim();
      const normalizedKey = normalizeKey(key);
      if (!key) return "";
      if (labelMap[key]) return labelMap[key];
      if (labelMap[normalizedKey]) return labelMap[normalizedKey];
      const acronymMap = {{
        ai: "AI",
        adb: "ADB",
        eu: "EU",
        uk: "UK",
        us: "US",
        ngo: "NGO",
        saas: "SaaS",
        api: "API",
        db: "DB",
        qa: "QA",
        ebrd: "EBRD",
        ecepp: "ECEPP",
        isdb: "IsDB",
        qic: "QIC",
        rk: "RK",
        undp: "UNDP",
        unesco: "UNESCO",
        unicef: "UNICEF",
        aws: "AWS",
        eeas: "EEAS",
        iite: "IITE"
      }};
      return key
        .split(/[_-]+/)
        .filter(Boolean)
        .map((part) => {{
          const lower = part.toLowerCase();
          if (acronymMap[lower]) return acronymMap[lower];
          return lower.charAt(0).toUpperCase() + lower.slice(1);
        }})
        .join(" ");
    }}

    function itemTags(item) {{
      return (Array.isArray(item.tags) ? item.tags : []).map(normalizeKey);
    }}

    function itemEligibility(item) {{
      return (Array.isArray(item.eligibility) ? item.eligibility : []).map(normalizeKey);
    }}

    function matchesAnyTag(item, keys) {{
      const tags = itemTags(item);
      return keys.some((key) => tags.includes(normalizeKey(key)));
    }}

    function matchesAnyEligibility(item, keys) {{
      const eligibility = itemEligibility(item);
      return keys.some((key) => eligibility.includes(normalizeKey(key)));
    }}

    function matchesType(item, types) {{
      const currentType = normalizeKey(item.type || "");
      return types.some((type) => currentType === normalizeKey(type));
    }}

    function presetById(presets, id) {{
      return presets.find((preset) => preset.id === id) || presets[0];
    }}

    function activeAudiencePreset() {{
      return presetById(AUDIENCE_PRESETS, state.audience);
    }}

    function activeFormatPreset() {{
      return presetById(FORMAT_PRESETS, state.format);
    }}

    function activeTopicPreset() {{
      return presetById(TOPIC_PRESETS, state.topic);
    }}

    function activeTopicBrief() {{
      const topicId = state.topic;
      if (!topicId || topicId === DEFAULT_TOPIC) return null;
      const briefs = {{
        ai: {{
          title: copy.theme_ai_title,
          note: copy.theme_ai_note,
          bestFor: copy.topic_ai_best,
          focuses: [
            copy.topic_ai_focus_1,
            copy.topic_ai_focus_2,
            copy.topic_ai_focus_3
          ]
        }},
        agro: {{
          title: copy.theme_agro_title,
          note: copy.theme_agro_note,
          bestFor: copy.topic_agro_best,
          focuses: [
            copy.topic_agro_focus_1,
            copy.topic_agro_focus_2,
            copy.topic_agro_focus_3
          ]
        }},
        science: {{
          title: copy.theme_science_title,
          note: copy.theme_science_note,
          bestFor: copy.topic_science_best,
          focuses: [
            copy.topic_science_focus_1,
            copy.topic_science_focus_2,
            copy.topic_science_focus_3
          ]
        }},
        public: {{
          title: copy.theme_public_title,
          note: copy.theme_public_note,
          bestFor: copy.topic_public_best,
          focuses: [
            copy.topic_public_focus_1,
            copy.topic_public_focus_2,
            copy.topic_public_focus_3
          ]
        }},
        business: {{
          title: copy.theme_business_title,
          note: copy.theme_business_note,
          bestFor: copy.topic_business_best,
          focuses: [
            copy.topic_business_focus_1,
            copy.topic_business_focus_2,
            copy.topic_business_focus_3
          ]
        }},
        ngo: {{
          title: copy.theme_ngo_title,
          note: copy.theme_ngo_note,
          bestFor: copy.topic_ngo_best,
          focuses: [
            copy.topic_ngo_focus_1,
            copy.topic_ngo_focus_2,
            copy.topic_ngo_focus_3
          ]
        }}
      }};
      return briefs[topicId] || null;
    }}

    function activeRegionFilter() {{
      return presetById(REGION_FILTERS, state.region);
    }}

    function activeLifecycleFilter() {{
      return presetById(LIFECYCLE_FILTERS, state.lifecycle);
    }}

    function activeDeadlineFilter() {{
      return presetById(DEADLINE_FILTERS, state.deadlineMode);
    }}

    function activeSortOption() {{
      return presetById(SORT_OPTIONS, state.sort);
    }}

    function activeScoreOption() {{
      return (
        SCORE_OPTIONS.find((option) => option.value === state.minScore)
        || SCORE_OPTIONS[0]
      );
    }}

    function matchingAudiencePresets(item) {{
      const priority = {{
        science: 0,
        farmer: 1,
        ngo: 2,
        business: 3,
        startup: 4
      }};
      return AUDIENCE_PRESETS
        .filter((preset) => preset.id !== DEFAULT_AUDIENCE && preset.matches(item))
        .sort((left, right) => {{
          const leftRank = priority[left.id] ?? 99;
          const rightRank = priority[right.id] ?? 99;
          return leftRank - rightRank || left.label.localeCompare(right.label);
        }});
    }}

    function daysUntilDeadline(item) {{
      if (!item || !item.deadline) return null;
      const parsed = Date.parse(`${{item.deadline}}T00:00:00`);
      if (Number.isNaN(parsed)) return null;
      const today = new Date();
      const todayStart = Date.UTC(
        today.getUTCFullYear(),
        today.getUTCMonth(),
        today.getUTCDate()
      );
      return Math.ceil((parsed - todayStart) / (1000 * 60 * 60 * 24));
    }}

    function fitPills(item) {{
      const pills = matchingAudiencePresets(item)
        .slice(0, 2)
        .map((preset) => ({{
          label: preset.label,
          tone: "good"
        }}));
      if (!pills.length) {{
        pills.push({{
          label: copy.fit_unknown,
          tone: "warn"
        }});
      }}
      if (hasTag(item, "global")) {{
        pills.push({{
          label: copy.fit_global,
          tone: "neutral"
        }});
      }}
      const days = daysUntilDeadline(item);
      if (days !== null && days >= 0 && days <= 14) {{
        pills.push({{
          label: copy.fit_deadline_soon,
          tone: "warn"
        }});
      }}
      return pills.slice(0, 3);
    }}

    function fitSummaryText(item) {{
      const audiences = matchingAudiencePresets(item).map((preset) => preset.label);
      if (audiences.length) {{
        return `${{copy.detail_fit_good}}: ${{audiences.join(", ")}}`;
      }}
      return copy.detail_fit_review;
    }}

    function fitPillsMarkup(item) {{
      return fitPills(item).map((pill) => {{
        const toneClass = pill.tone && pill.tone !== "neutral" ? ` ${{pill.tone}}` : "";
        return (
          `<span class="fit-pill${{toneClass}}" data-avds-component="fit-pill">`
          + `${{escapeHtml(pill.label)}}`
          + `</span>`
        );
      }}).join("");
    }}

    function opportunityFormatLabel(item) {{
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      if (supportPreset.matches(item)) return supportPreset.label;
      const acceleratorsPreset = presetById(FORMAT_PRESETS, "accelerators");
      if (acceleratorsPreset.matches(item)) return acceleratorsPreset.label;
      const tendersPreset = presetById(FORMAT_PRESETS, "tenders");
      if (tendersPreset.matches(item)) return tendersPreset.label;
      const grantsPreset = presetById(FORMAT_PRESETS, "grants");
      if (grantsPreset.matches(item)) return grantsPreset.label;
      return humanizeLabel(item.type || "");
    }}

    function opportunityRegionLabel(item) {{
      const priority = regionalPriority(item);
      if (priority >= 3) return copy.meta_region_kazakhstan;
      if (priority >= 2) return copy.meta_region_central_asia;
      return copy.meta_region_global;
    }}

    function opportunityDeadlineLabel(item) {{
      const days = daysUntilDeadline(item);
      if (days === null) return copy.meta_deadline_rolling;
      if (days >= 0 && days <= 14) {{
        return text("meta_deadline_soon_days", {{ count: formatNumber.format(days) }});
      }}
      if (days >= 0 && days <= 31) return copy.meta_deadline_month;
      return copy.meta_deadline_later;
    }}

    function opportunitySignalText(item) {{
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      if (supportPreset.matches(item) && regionalPriority(item) >= 3) {{
        return copy.signal_support_kz;
      }}
      if (isPublicSectorOpportunity(item)) {{
        return copy.signal_public_sector;
      }}
      if (matchesType(item, ["tender"])) {{
        return copy.signal_tender;
      }}
      if (presetById(AUDIENCE_PRESETS, "science").matches(item)) {{
        return copy.signal_science;
      }}
      if (presetById(AUDIENCE_PRESETS, "farmer").matches(item)) {{
        return copy.signal_farmer;
      }}
      if (presetById(AUDIENCE_PRESETS, "ngo").matches(item)) {{
        return copy.signal_ngo;
      }}
      if (presetById(AUDIENCE_PRESETS, "business").matches(item)) {{
        return copy.signal_business;
      }}
      if (presetById(AUDIENCE_PRESETS, "startup").matches(item)) {{
        return copy.signal_startup;
      }}
      if (regionalPriority(item) >= 3) {{
        return copy.signal_kazakhstan;
      }}
      if (regionalPriority(item) >= 2) {{
        return copy.signal_central_asia;
      }}
      return copy.signal_global;
    }}

    function opportunitySignalPillsMarkup(item) {{
      const entries = [
        {{
          label: copy.meta_format_label,
          value: opportunityFormatLabel(item)
        }},
        {{
          label: copy.meta_region_label,
          value: opportunityRegionLabel(item)
        }},
        {{
          label: copy.meta_deadline_label,
          value: opportunityDeadlineLabel(item)
        }}
      ];
      return entries.map((entry) => (
        `<span class="signal-pill" data-avds-component="signal-pill">`
        + `<span>${{escapeHtml(entry.label)}}</span>`
        + `${{escapeHtml(entry.value)}}`
        + `</span>`
      )).join("");
    }}

    function externalActionUrl(item) {{
      const raw = item && item.raw && typeof item.raw === "object" ? item.raw : {{}};
      const applicationUrl = typeof raw.application_url === "string"
        ? raw.application_url.trim()
        : "";
      return applicationUrl || item.source_url || opportunityPageHref(item && item.id) || "#";
    }}

    function primaryActionUrl(item) {{
      return opportunityPageHref(item && item.id) || externalActionUrl(item);
    }}

    function spotlightBaseItems() {{
      return state.items.slice().sort(comparePriorityItems);
    }}

    function heroActionAttributes(action = {{}}) {{
      return [
        ["data-hero-reset", "true"],
        ["data-hero-view", action.view || "opportunities"],
        ["data-hero-audience", action.audience],
        ["data-hero-format", action.format],
        ["data-hero-topic", action.topic],
        ["data-hero-region", action.region],
        ["data-hero-deadline", action.deadline]
      ].filter(([, value]) => value).map(
        ([name, value]) => `${{name}}="${{escapeHtml(value)}}"`,
      ).join(" ");
    }}

    function spotlightPreviewMarkup(items, totalCount) {{
      if (!items.length) {{
        return `<div class="spotlight-empty">${{escapeHtml(copy.spotlight_empty)}}</div>`;
      }}
      const preview = items.slice(0, 3);
      const moreCount = Math.max(0, totalCount - preview.length);
      const previews = preview.map((item) => {{
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const sourceName = humanizeLabel(item.source);
        const metaBits = [sourceName, formatDeadline(item.deadline)].filter(Boolean);
        return `
          <button
            class="spotlight-item"
            type="button"
            data-opportunity-detail="${{opportunityId}}"
            data-opportunity-url="${{cardUrl}}"
          >
            <strong>${{escapeHtml(item.title || copy.detail_title_fallback)}}</strong>
            <span>${{escapeHtml(metaBits.join(" • "))}}</span>
          </button>
        `;
      }}).join("");
      const more = moreCount
        ? `<div class="spotlight-more">${{escapeHtml(
            text("spotlight_preview_more", {{ count: formatNumber.format(moreCount) }}),
          )}}</div>`
        : "";
      return `<div class="spotlight-list">${{previews}}${{more}}</div>`;
    }}

    function spotlightCardMarkup(config) {{
      return `
        <article
          class="spotlight-card"
          data-tone="${{escapeHtml(config.tone || "neutral")}}"
          data-avds-component="spotlight-card"
        >
          <div class="spotlight-head">
            <span class="spotlight-label">${{escapeHtml(config.kicker)}}</span>
            <span class="spotlight-count">${{escapeHtml(
              text("spotlight_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="spotlight-note">${{escapeHtml(config.note)}}</p>
          </div>
          ${{spotlightPreviewMarkup(config.preview, config.count)}}
          <div class="spotlight-footer">
            <button
              class="button slim soft spotlight-action"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.spotlight_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function renderSpotlights() {{
      const root = $("#spotlight-grid");
      if (!root) return;
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      const trendingItems = items.filter((item) => Number(item.score || 0) >= 0.5);
      const kazakhstanItems = items.filter((item) => regionalPriority(item) >= 3);
      const supportItems = items.filter(
        (item) => regionalPriority(item) >= 3 && supportPreset.matches(item),
      );
      const deadlineItems = items.filter((item) => {{
        const days = daysUntilDeadline(item);
        return days !== null && days >= 0 && days <= 21;
      }});
      const cards = [
        {{
          tone: "brand",
          kicker: copy.spotlight_trending_kicker,
          title: copy.spotlight_trending_title,
          note: copy.spotlight_trending_note,
          count: trendingItems.length,
          preview: trendingItems,
          action: {{ view: "opportunities" }}
        }},
        {{
          tone: "good",
          kicker: copy.spotlight_kazakhstan_kicker,
          title: copy.spotlight_kazakhstan_title,
          note: copy.spotlight_kazakhstan_note,
          count: kazakhstanItems.length,
          preview: kazakhstanItems,
          action: {{ view: "opportunities", region: "kazakhstan" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.spotlight_support_kicker,
          title: copy.spotlight_support_title,
          note: copy.spotlight_support_note,
          count: supportItems.length,
          preview: supportItems,
          action: {{ view: "opportunities", format: "support", region: "kazakhstan" }}
        }},
        {{
          tone: "amber",
          kicker: copy.spotlight_deadline_kicker,
          title: copy.spotlight_deadline_title,
          note: copy.spotlight_deadline_note,
          count: deadlineItems.length,
          preview: deadlineItems,
          action: {{ view: "opportunities", deadline: "soon" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(spotlightCardMarkup).join("");
    }}

    function pathwayPreviewMarkup(items, totalCount) {{
      if (!items.length) {{
        return `<div class="spotlight-empty">${{escapeHtml(copy.pathways_empty)}}</div>`;
      }}
      const preview = items.slice(0, 3);
      const moreCount = Math.max(0, totalCount - preview.length);
      const previews = preview.map((item) => {{
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const sourceName = humanizeLabel(item.source);
        const metaBits = [sourceName, formatDeadline(item.deadline)].filter(Boolean);
        return `
          <button
            class="spotlight-item"
            type="button"
            data-opportunity-detail="${{opportunityId}}"
            data-opportunity-url="${{cardUrl}}"
          >
            <strong>${{escapeHtml(item.title || copy.detail_title_fallback)}}</strong>
            <span>${{escapeHtml(metaBits.join(" • "))}}</span>
          </button>
        `;
      }}).join("");
      const more = moreCount
        ? `<div class="spotlight-more">${{escapeHtml(
            text("spotlight_preview_more", {{ count: formatNumber.format(moreCount) }}),
          )}}</div>`
        : "";
      return `<div class="spotlight-list">${{previews}}${{more}}</div>`;
    }}

    function pathwayCardMarkup(config) {{
      return `
        <article
          class="pathway-card"
          data-tone="${{escapeHtml(config.tone || "brand")}}"
          data-avds-component="pathway-card"
        >
          <div class="pathway-head">
            <span class="pathway-label">${{escapeHtml(config.kicker)}}</span>
            <span class="pathway-count">${{escapeHtml(
              text("pathways_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="pathway-note">${{escapeHtml(config.note)}}</p>
          </div>
          ${{pathwayPreviewMarkup(config.preview, config.count)}}
          <div class="pathway-footer">
            <button
              class="button slim soft"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.pathways_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function renderPathways() {{
      const root = $("#pathways-grid");
      if (!root) return;
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const startupPreset = presetById(AUDIENCE_PRESETS, "startup");
      const businessPreset = presetById(AUDIENCE_PRESETS, "business");
      const farmerPreset = presetById(AUDIENCE_PRESETS, "farmer");
      const sciencePreset = presetById(AUDIENCE_PRESETS, "science");
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      const startupItems = items.filter((item) => startupPreset.matches(item));
      const businessItems = items.filter((item) => (
        businessPreset.matches(item)
        && supportPreset.matches(item)
        && regionalPriority(item) >= 3
      ));
      const farmerItems = items.filter((item) => farmerPreset.matches(item));
      const scienceItems = items.filter((item) => sciencePreset.matches(item));
      const cards = [
        {{
          tone: "brand",
          kicker: copy.pathway_startup_kicker,
          title: copy.pathway_startup_title,
          note: copy.pathway_startup_note,
          count: startupItems.length,
          preview: startupItems,
          action: {{ view: "opportunities", audience: "startup" }}
        }},
        {{
          tone: "good",
          kicker: copy.pathway_business_kicker,
          title: copy.pathway_business_title,
          note: copy.pathway_business_note,
          count: businessItems.length,
          preview: businessItems,
          action: {{
            view: "opportunities",
            audience: "business",
            format: "support",
            region: "kazakhstan"
          }}
        }},
        {{
          tone: "amber",
          kicker: copy.pathway_farmer_kicker,
          title: copy.pathway_farmer_title,
          note: copy.pathway_farmer_note,
          count: farmerItems.length,
          preview: farmerItems,
          action: {{ view: "opportunities", audience: "farmer" }}
        }},
        {{
          tone: "violet",
          kicker: copy.pathway_science_kicker,
          title: copy.pathway_science_title,
          note: copy.pathway_science_note,
          count: scienceItems.length,
          preview: scienceItems,
          action: {{ view: "opportunities", audience: "science" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(pathwayCardMarkup).join("");
    }}

    function themePreviewMarkup(items, totalCount) {{
      if (!items.length) {{
        return `<div class="spotlight-empty">${{escapeHtml(copy.themes_empty)}}</div>`;
      }}
      const preview = items.slice(0, 3);
      const moreCount = Math.max(0, totalCount - preview.length);
      const previews = preview.map((item) => {{
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const sourceName = humanizeLabel(item.source);
        const metaBits = [sourceName, formatDeadline(item.deadline)].filter(Boolean);
        return `
          <button
            class="spotlight-item"
            type="button"
            data-opportunity-detail="${{opportunityId}}"
            data-opportunity-url="${{cardUrl}}"
          >
            <strong>${{escapeHtml(item.title || copy.detail_title_fallback)}}</strong>
            <span>${{escapeHtml(metaBits.join(" • "))}}</span>
          </button>
        `;
      }}).join("");
      const more = moreCount
        ? `<div class="spotlight-more">${{escapeHtml(
            text("spotlight_preview_more", {{ count: formatNumber.format(moreCount) }}),
          )}}</div>`
        : "";
      return `<div class="spotlight-list">${{previews}}${{more}}</div>`;
    }}

    function themeCardMarkup(config) {{
      return `
        <article
          class="theme-card"
          data-tone="${{escapeHtml(config.tone || "neutral")}}"
          data-avds-component="theme-card"
        >
          <div class="theme-head">
            <span class="theme-label">${{escapeHtml(config.kicker)}}</span>
            <span class="theme-count">${{escapeHtml(
              text("themes_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="theme-note">${{escapeHtml(config.note)}}</p>
          </div>
          ${{themePreviewMarkup(config.preview, config.count)}}
          <div class="theme-footer">
            <button
              class="button slim soft"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.themes_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function renderThemes() {{
      const root = $("#themes-grid");
      if (!root) return;
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const aiPreset = presetById(TOPIC_PRESETS, "ai");
      const agroPreset = presetById(TOPIC_PRESETS, "agro");
      const sciencePreset = presetById(TOPIC_PRESETS, "science");
      const publicPreset = presetById(TOPIC_PRESETS, "public");
      const businessPreset = presetById(TOPIC_PRESETS, "business");
      const ngoPreset = presetById(TOPIC_PRESETS, "ngo");
      const aiItems = items.filter((item) => aiPreset.matches(item));
      const agroItems = items.filter((item) => agroPreset.matches(item));
      const scienceItems = items.filter((item) => sciencePreset.matches(item));
      const publicItems = items.filter((item) => publicPreset.matches(item));
      const businessItems = items.filter((item) => businessPreset.matches(item));
      const ngoItems = items.filter((item) => ngoPreset.matches(item));
      const cards = [
        {{
          tone: "brand",
          kicker: copy.theme_ai_kicker,
          title: copy.theme_ai_title,
          note: copy.theme_ai_note,
          count: aiItems.length,
          preview: aiItems,
          action: {{ view: "opportunities", topic: "ai" }}
        }},
        {{
          tone: "amber",
          kicker: copy.theme_agro_kicker,
          title: copy.theme_agro_title,
          note: copy.theme_agro_note,
          count: agroItems.length,
          preview: agroItems,
          action: {{ view: "opportunities", topic: "agro" }}
        }},
        {{
          tone: "violet",
          kicker: copy.theme_science_kicker,
          title: copy.theme_science_title,
          note: copy.theme_science_note,
          count: scienceItems.length,
          preview: scienceItems,
          action: {{ view: "opportunities", topic: "science" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.theme_public_kicker,
          title: copy.theme_public_title,
          note: copy.theme_public_note,
          count: publicItems.length,
          preview: publicItems,
          action: {{ view: "opportunities", topic: "public" }}
        }},
        {{
          tone: "good",
          kicker: copy.theme_business_kicker,
          title: copy.theme_business_title,
          note: copy.theme_business_note,
          count: businessItems.length,
          preview: businessItems,
          action: {{ view: "opportunities", topic: "business", region: "kazakhstan" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.theme_ngo_kicker,
          title: copy.theme_ngo_title,
          note: copy.theme_ngo_note,
          count: ngoItems.length,
          preview: ngoItems,
          action: {{ view: "opportunities", topic: "ngo" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(themeCardMarkup).join("");
    }}

    function funderOverviewText(funder) {{
      const topics = (Array.isArray(funder.top_tags) ? funder.top_tags : [])
        .slice(0, 2)
        .map(humanizeLabel)
        .join(", ");
      const regions = (Array.isArray(funder.top_regions) ? funder.top_regions : [])
        .slice(0, 2)
        .map(humanizeLabel)
        .join(", ");
      const bits = [copy.funder_overview_intro];
      if (topics) {{
        bits.push(text("funder_overview_topics", {{ topics }}));
      }}
      if (regions) {{
        bits.push(text("funder_overview_regions", {{ regions }}));
      }}
      return bits.join(" ").trim();
    }}

    function funderCardMarkup(funder) {{
      const tags = (Array.isArray(funder.top_tags) ? funder.top_tags : []).slice(0, 3);
      const forecastCount = Number(funder.forecast_items || 0);
      const rollingCount = Number(funder.rolling_items || 0);
      const sourceCount = Array.isArray(funder.sources) ? funder.sources.length : 0;
      const nextDeadline = funder.next_deadline
        ? formatDeadline(funder.next_deadline)
        : copy.open_rolling;
      return `
        <article class="funder-card" data-avds-component="funder-card">
          <div class="funder-card-head">
            <div>
              <span class="spotlight-label">${{escapeHtml(copy.funder_section_eyebrow)}}</span>
              <h3>${{escapeHtml(funder.name || "")}}</h3>
            </div>
            <span class="funder-kpi">${{
              escapeHtml(copy.funder_live_now)
            }} · ${{formatNumber.format(Number(funder.current_items || 0))}}</span>
          </div>
          <p>${{escapeHtml(funderOverviewText(funder))}}</p>
          <div class="funder-meta">
            ${{tags.map((tag) => (
              `<span class="summary-pill">${{escapeHtml(humanizeLabel(tag))}}</span>`
            )).join("")}}
            ${{
              forecastCount
                ? (
                  `<span class="summary-pill">${{escapeHtml(copy.lifecycle_forecast)}}`
                  + ` · ${{formatNumber.format(forecastCount)}}</span>`
                )
                : ""
            }}
            ${{
              rollingCount
                ? (
                  `<span class="summary-pill">${{escapeHtml(copy.lifecycle_rolling)}}`
                  + ` · ${{formatNumber.format(rollingCount)}}</span>`
                )
                : ""
            }}
          </div>
          <div class="funder-actions">
            <span class="panel-summary">${{escapeHtml(
              `${{formatNumber.format(sourceCount)}} · ${{nextDeadline}}`
            )}}</span>
            <a
              class="button slim soft"
              href="${{escapeHtml(funderPageHref(funder.slug))}}"
              data-avds-component="button"
            >${{escapeHtml(copy.funder_open_profile)}}</a>
          </div>
        </article>
      `;
    }}

    function renderFunders() {{
      const root = $("#funder-grid");
      if (!root) return;
      if (!state.funders.length) {{
        root.innerHTML = `<div class="message">${{escapeHtml(copy.funder_empty)}}</div>`;
        return;
      }}
      root.innerHTML = state.funders.slice(0, 6).map(funderCardMarkup).join("");
    }}

    function renderTopicBrief(items) {{
      const root = $("#topic-brief");
      if (!root) return;
      const brief = activeTopicBrief();
      if (!brief) {{
        root.className = "topic-brief hidden";
        root.innerHTML = "";
        return;
      }}
      const chips = (brief.focuses || []).map((label) => (
        `<span class="topic-brief-chip" data-avds-component="topic-chip">`
        + `${{escapeHtml(label)}}`
        + `</span>`
      )).join("");
      root.className = "topic-brief";
      root.innerHTML = `
        <div class="topic-brief-head">
          <span class="topic-brief-kicker">${{escapeHtml(copy.topic_brief_eyebrow)}}</span>
          <span class="topic-brief-count">${{escapeHtml(
            text("topic_brief_count", {{ count: formatNumber.format(items.length) }}),
          )}}</span>
        </div>
        <div class="spotlight-copy">
          <h3>${{escapeHtml(brief.title)}}</h3>
          <p class="topic-brief-note">${{escapeHtml(brief.note)}}</p>
        </div>
        <div class="topic-brief-grid">
          <div class="topic-brief-group">
            <span class="topic-brief-label">${{escapeHtml(copy.topic_brief_what)}}</span>
            <div class="topic-brief-chips">${{chips}}</div>
          </div>
          <div class="topic-brief-group">
            <span class="topic-brief-label">${{escapeHtml(copy.topic_brief_best_for)}}</span>
            <p class="topic-brief-audience">${{escapeHtml(brief.bestFor)}}</p>
            <div class="topic-brief-actions">
              <button
                class="text-button"
                type="button"
                data-topic-reset="true"
                data-avds-component="button"
              >${{escapeHtml(copy.topic_brief_reset)}}</button>
            </div>
          </div>
        </div>
      `;
    }}

    function syncControlsFromState() {{
      $("#search").value = state.query;
      $("#sort-filter").value = state.sort;
      $("#score-filter").value = String(state.minScore);
      $("#scope-filter").value = state.includeArchived ? "all" : "open";
      $("#lifecycle-filter").value = state.lifecycle;
      $("#region-filter").value = state.region;
      $("#deadline-filter").value = state.deadlineMode;
      const sourceFilter = $("#source-filter");
      if (sourceFilter) {{
        sourceFilter.value = state.source;
      }}
    }}

    function syncUrlState() {{
      const params = new URLSearchParams(window.location.search);
      params.set("lang", copy.lang || "ru");
      if (state.query.trim()) {{
        params.set("q", state.query.trim());
      }} else {{
        params.delete("q");
      }}
      if (state.source !== "all") {{
        params.set("source", state.source);
      }} else {{
        params.delete("source");
      }}
      if (state.audience !== DEFAULT_AUDIENCE) {{
        params.set("audience", state.audience);
      }} else {{
        params.delete("audience");
      }}
      if (state.format !== DEFAULT_FORMAT) {{
        params.set("format", state.format);
      }} else {{
        params.delete("format");
      }}
      if (state.topic !== DEFAULT_TOPIC) {{
        params.set("topic", state.topic);
      }} else {{
        params.delete("topic");
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        params.set("lifecycle", state.lifecycle);
      }} else {{
        params.delete("lifecycle");
      }}
      if (state.region !== DEFAULT_REGION) {{
        params.set("region", state.region);
      }} else {{
        params.delete("region");
      }}
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        params.set("deadline", state.deadlineMode);
      }} else {{
        params.delete("deadline");
      }}
      if (state.includeArchived) {{
        params.set("scope", "all");
      }} else {{
        params.delete("scope");
      }}
      if (state.sort !== DEFAULT_SORT) {{
        params.set("sort", state.sort);
      }} else {{
        params.delete("sort");
      }}
      if (state.minScore !== scoreDefaultForScope()) {{
        params.set("score", String(state.minScore));
      }} else {{
        params.delete("score");
      }}
      const query = params.toString();
      const nextUrl = (
        `${{window.location.pathname}}`
        + `${{query ? `?${{query}}` : ""}}`
        + `${{window.location.hash}}`
      );
      window.history.replaceState(null, "", nextUrl);
    }}

    function applyStateFromUrl() {{
      const params = new URLSearchParams(window.location.search);
      state.query = params.get("q") || "";
      state.source = params.get("source") || "all";
      state.includeArchived = params.get("scope") === "all";
      const sort = params.get("sort") || DEFAULT_SORT;
      state.sort = SORT_OPTIONS.some((option) => option.id === sort)
        ? sort
        : DEFAULT_SORT;
      const scoreParam = params.get("score");
      const score = scoreParam === null ? Number.NaN : Number(scoreParam);
      state.minScore = [0, 0.3, 0.5, 0.7].includes(score)
        ? score
        : scoreDefaultForScope();
      const audience = params.get("audience") || DEFAULT_AUDIENCE;
      state.audience = AUDIENCE_PRESETS.some((preset) => preset.id === audience)
        ? audience
        : DEFAULT_AUDIENCE;
      const format = params.get("format") || DEFAULT_FORMAT;
      state.format = FORMAT_PRESETS.some((preset) => preset.id === format)
        ? format
        : DEFAULT_FORMAT;
      const topic = params.get("topic") || DEFAULT_TOPIC;
      state.topic = TOPIC_PRESETS.some((preset) => preset.id === topic)
        ? topic
        : DEFAULT_TOPIC;
      const lifecycle = params.get("lifecycle") || DEFAULT_LIFECYCLE;
      state.lifecycle = LIFECYCLE_FILTERS.some((preset) => preset.id === lifecycle)
        ? lifecycle
        : DEFAULT_LIFECYCLE;
      if (
        (state.lifecycle === "closed" || state.lifecycle === "awarded")
        && !state.includeArchived
      ) {{
        state.includeArchived = true;
      }}
      const region = params.get("region") || DEFAULT_REGION;
      state.region = REGION_FILTERS.some((preset) => preset.id === region)
        ? region
        : DEFAULT_REGION;
      const deadline = params.get("deadline") || DEFAULT_DEADLINE;
      state.deadlineMode = DEADLINE_FILTERS.some((preset) => preset.id === deadline)
        ? deadline
        : DEFAULT_DEADLINE;
    }}

    function readSavedViews() {{
      try {{
        const stored = window.localStorage.getItem(SAVED_VIEW_STORAGE_KEY);
        const parsed = stored ? JSON.parse(stored) : [];
        return Array.isArray(parsed) ? parsed : [];
      }} catch {{
        return [];
      }}
    }}

    function writeSavedViews(rows) {{
      try {{
        window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(rows));
      }} catch {{
        // ignore storage quota or privacy-mode errors
      }}
    }}

    function savedViewNameFromState() {{
      if (state.query.trim()) return state.query.trim();
      const labels = [];
      if (state.audience !== DEFAULT_AUDIENCE) labels.push(activeAudiencePreset().label);
      if (state.format !== DEFAULT_FORMAT) labels.push(activeFormatPreset().label);
      if (state.topic !== DEFAULT_TOPIC) labels.push(activeTopicPreset().label);
      if (state.lifecycle !== DEFAULT_LIFECYCLE) labels.push(activeLifecycleFilter().label);
      if (state.region !== DEFAULT_REGION) labels.push(activeRegionFilter().label);
      return labels.slice(0, 2).join(" • ") || copy.saved_view_default_name;
    }}

    function renderSavedViews() {{
      const root = $("#saved-views");
      if (!root) return;
      const views = readSavedViews();
      if (!views.length) {{
        root.innerHTML = `<span class="saved-empty">${{escapeHtml(copy.collections_empty)}}</span>`;
        return;
      }}
      root.innerHTML = views.map((view) => `
        <span class="saved-view-pill">
          <button
            class="saved-apply"
            type="button"
            data-saved-view="${{escapeHtml(String(view.query || ""))}}"
          >${{escapeHtml(String(view.name || copy.saved_view_default_name))}}</button>
          <button
            class="saved-remove"
            type="button"
            data-remove-saved-view="${{escapeHtml(String(view.query || ""))}}"
            aria-label="${{escapeHtml(copy.saved_view_remove_aria)}}"
          >×</button>
        </span>
      `).join("");
    }}

    function setSavedViewNotice(message) {{
      const root = $("#saved-view-notice");
      if (!root) return;
      const text = String(message || "").trim();
      root.textContent = text;
      root.classList.toggle("hidden", !text);
    }}

    function saveCurrentView() {{
      syncUrlState();
      const currentUrl = new URL(window.location.href);
      const params = new URLSearchParams(currentUrl.search);
      params.set("lang", copy.lang || "ru");
      const query = params.toString();
      const next = {{
        name: savedViewNameFromState(),
        query
      }};
      const deduped = readSavedViews().filter((view) => view.query !== query);
      deduped.unshift(next);
      writeSavedViews(deduped.slice(0, 8));
      renderSavedViews();
      setSavedViewNotice(copy.saved_view_saved);
    }}

    function applySavedView(query) {{
      if (!query) return;
      const nextUrl = `${{window.location.pathname}}?${{query}}${{window.location.hash || ""}}`;
      window.history.replaceState(null, "", nextUrl);
      applyStateFromUrl();
      resetVisibleLimit();
      reloadAll();
    }}

    function removeSavedView(query) {{
      const next = readSavedViews().filter((view) => view.query !== query);
      writeSavedViews(next);
      renderSavedViews();
      setSavedViewNotice(copy.saved_view_removed);
    }}

    async function shareCurrentView() {{
      syncUrlState();
      const href = window.location.href;
      try {{
        await navigator.clipboard.writeText(href);
        setSavedViewNotice(copy.saved_view_shared);
      }} catch {{
        window.prompt(copy.saved_view_share_prompt, href);
      }}
    }}

    function cleanSummaryText(value) {{
      const raw = String(value || "").replace(/\\s+/g, " ").trim();
      if (!raw) return "";
      return raw
        .split(/Читать далее|Read more/i)[0]
        .replace(/[\\s\\-:;,]+$/u, "")
        .trim();
    }}

    function summarize(item) {{
      if (item.summary) return cleanSummaryText(item.summary) || copy.no_summary;
      const agency = item.raw && (item.raw.agency || item.raw.agencyCode);
      return agency ? text("source_agency", {{ agency }}) : copy.no_summary;
    }}

    function formatDeadline(value) {{
      if (!value) return copy.open_rolling;
      const parsed = new Date(`${{value}}T00:00:00`);
      if (Number.isNaN(parsed.getTime())) return value;
      return new Intl.DateTimeFormat(copy.locale || "ru-KZ", {{
        month: "short",
        day: "numeric",
        year: "numeric"
      }}).format(parsed);
    }}

    function formatDateTime(value) {{
      if (!value) return "—";
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return "—";
      return new Intl.DateTimeFormat(copy.locale || "ru-KZ", {{
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }}).format(parsed);
    }}

    function hasActiveFilters() {{
      return Boolean(state.query.trim())
        || state.sort !== DEFAULT_SORT
        || state.source !== "all"
        || state.audience !== DEFAULT_AUDIENCE
        || state.format !== DEFAULT_FORMAT
        || state.topic !== DEFAULT_TOPIC
        || state.lifecycle !== DEFAULT_LIFECYCLE
        || state.region !== DEFAULT_REGION
        || state.deadlineMode !== DEFAULT_DEADLINE
        || state.includeArchived
        || state.minScore !== scoreDefaultForScope();
    }}

    function scoreDefaultForScope() {{
      return state.includeArchived ? ALL_INDEX_SCORE : DEFAULT_SCORE;
    }}

    function resetVisibleLimit() {{
      state.visibleLimit = DEFAULT_VISIBLE_ITEMS;
    }}

    function emptyStateActions() {{
      const actions = [];
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        actions.push({{ id: "reset-deadline", label: copy.empty_action_deadline }});
      }}
      if (state.region !== DEFAULT_REGION) {{
        actions.push({{ id: "reset-region", label: copy.empty_action_region }});
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        actions.push({{ id: "reset-lifecycle", label: copy.lifecycle_all }});
      }}
      if (state.minScore !== scoreDefaultForScope()) {{
        actions.push({{ id: "reset-score", label: copy.empty_action_score }});
      }}
      if (!state.includeArchived) {{
        actions.push({{ id: "show-archive", label: copy.empty_action_scope }});
      }}
      if (hasActiveFilters()) {{
        actions.push({{ id: "clear", label: copy.empty_action_clear }});
      }}
      return actions.slice(0, 4);
    }}

    function renderEmptyState() {{
      const actions = emptyStateActions();
      return `
        <div class="message-shell">
          <div class="message-title">${{escapeHtml(copy.no_filtered_items)}}</div>
          <div class="message-note">${{escapeHtml(copy.no_filtered_items_hint)}}</div>
          ${{
            actions.length
              ? `<div class="message-actions">${{actions.map((action) => `
                  <button
                    class="text-button message-action"
                    type="button"
                    data-empty-action="${{escapeHtml(action.id)}}"
                    data-avds-component="button"
                  >${{escapeHtml(action.label)}}</button>
                `).join("")}}</div>`
              : ""
          }}
        </div>
      `;
    }}

    function applyEmptyAction(actionId) {{
      switch (actionId) {{
        case "reset-deadline":
          state.deadlineMode = DEFAULT_DEADLINE;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-region":
          state.region = DEFAULT_REGION;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-lifecycle":
          state.lifecycle = DEFAULT_LIFECYCLE;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-score":
          state.minScore = scoreDefaultForScope();
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "show-archive":
          state.includeArchived = true;
          state.minScore = scoreDefaultForScope();
          reloadAll();
          return;
        case "clear":
          clearAllFilters();
          return;
        default:
          return;
      }}
    }}

    function clearAllFilters() {{
      state.query = "";
      state.sort = DEFAULT_SORT;
      state.minScore = DEFAULT_SCORE;
      state.source = "all";
      state.audience = DEFAULT_AUDIENCE;
      state.format = DEFAULT_FORMAT;
      state.topic = DEFAULT_TOPIC;
      state.lifecycle = DEFAULT_LIFECYCLE;
      state.region = DEFAULT_REGION;
      state.deadlineMode = DEFAULT_DEADLINE;
      state.includeArchived = false;
      resetVisibleLimit();
      reloadAll();
    }}

    function applyHeroAction(button) {{
      if (!button) return;
      const shouldReset = button.getAttribute("data-hero-reset") === "true";
      const audience = button.getAttribute("data-hero-audience");
      const format = button.getAttribute("data-hero-format");
      const topic = button.getAttribute("data-hero-topic");
      const region = button.getAttribute("data-hero-region");
      const deadline = button.getAttribute("data-hero-deadline");
      const view = button.getAttribute("data-hero-view") || "opportunities";
      if (shouldReset) {{
        state.query = "";
        state.sort = DEFAULT_SORT;
        state.source = "all";
        state.minScore = DEFAULT_SCORE;
        state.audience = DEFAULT_AUDIENCE;
        state.format = DEFAULT_FORMAT;
        state.topic = DEFAULT_TOPIC;
        state.lifecycle = DEFAULT_LIFECYCLE;
        state.region = DEFAULT_REGION;
        state.deadlineMode = DEFAULT_DEADLINE;
        state.includeArchived = false;
      }}
      if (audience) {{
        state.audience = AUDIENCE_PRESETS.some((preset) => preset.id === audience)
          ? audience
          : DEFAULT_AUDIENCE;
      }}
      if (format) {{
        state.format = FORMAT_PRESETS.some((preset) => preset.id === format)
          ? format
          : DEFAULT_FORMAT;
      }}
      if (topic) {{
        state.topic = TOPIC_PRESETS.some((preset) => preset.id === topic)
          ? topic
          : DEFAULT_TOPIC;
      }}
      if (region) {{
        state.region = REGION_FILTERS.some((preset) => preset.id === region)
          ? region
          : DEFAULT_REGION;
      }}
      if (deadline) {{
        state.deadlineMode = DEADLINE_FILTERS.some((preset) => preset.id === deadline)
          ? deadline
          : DEFAULT_DEADLINE;
      }}
      resetVisibleLimit();
      renderOpportunities();
      goToView(view);
    }}

    function localDateISO(date = new Date()) {{
      const timezoneOffsetMs = date.getTimezoneOffset() * 60 * 1000;
      return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 10);
    }}

    function localRelevantBySource() {{
      const today = localDateISO();
      return state.items.reduce((counts, item) => {{
        if (item.score >= 0.3 && (!item.deadline || item.deadline >= today)) {{
          counts.set(item.source, (counts.get(item.source) || 0) + 1);
        }}
        return counts;
      }}, new Map());
    }}

    function haystackFor(item) {{
      const tags = Array.isArray(item.tags) ? item.tags : [];
      const eligibility = Array.isArray(item.eligibility) ? item.eligibility : [];
      const raw = item.raw && typeof item.raw === "object" ? item.raw : {{}};
      return [
        item.title,
        item.summary,
        item.funder,
        item.source,
        tags.join(" "),
        eligibility.join(" "),
        raw.region,
        raw.country,
        raw.agency,
        raw.notice_type
      ].join(" ").toLowerCase();
    }}

    function regionalPriority(item) {{
      const textValue = haystackFor(item);
      const source = String(item.source || "");
      const hasKazakhstanSignal = /kazakhstan|казахстан|қазақстан/.test(textValue)
        || source.includes("_kazakhstan")
        || hasTag(item, "kazakhstan");
      const hasCentralAsiaSignal = /central[\\s_-]+asia|central[\\s_-]+asian/i.test(textValue)
        || /центральн(ая|ой)\\s+ази/i.test(textValue)
        || hasTag(item, "central_asia_eligible")
        || hasTag(item, "central_asia");
      if (hasKazakhstanSignal) {{
        return 3;
      }}
      if (
        hasCentralAsiaSignal
      ) {{
        return 2;
      }}
      if (/eurasia|cis|uzbekistan|kyrgyzstan|tajikistan|turkmenistan/.test(textValue)) {{
        return 1;
      }}
      return 0;
    }}

    function regionalBadgeLabel(item) {{
      const priority = regionalPriority(item);
      if (priority >= 3) return copy.regional_badge_kazakhstan;
      if (priority >= 2) return copy.regional_badge_central_asia;
      return "";
    }}

    function deadlineRank(item) {{
      if (!item.deadline) return Number.POSITIVE_INFINITY;
      const parsed = Date.parse(`${{item.deadline}}T00:00:00`);
      return Number.isNaN(parsed) ? Number.POSITIVE_INFINITY : parsed;
    }}

    function discoveredRank(item) {{
      const parsed = Date.parse(item.discovered_at || "");
      return Number.isNaN(parsed) ? 0 : parsed;
    }}

    function comparePriorityItems(left, right) {{
      return (
        regionalPriority(right) - regionalPriority(left)
        || Number(right.score || 0) - Number(left.score || 0)
        || deadlineRank(left) - deadlineRank(right)
        || discoveredRank(right) - discoveredRank(left)
      );
    }}

    function compareDeadlineItems(left, right) {{
      return (
        deadlineRank(left) - deadlineRank(right)
        || comparePriorityItems(left, right)
      );
    }}

    function compareUpdatedItems(left, right) {{
      return (
        discoveredRank(right) - discoveredRank(left)
        || comparePriorityItems(left, right)
      );
    }}

    function topicPriorityScore(item) {{
      const topicId = state.topic;
      if (!topicId || topicId === DEFAULT_TOPIC) return 0;
      let score = 0;
      if (topicId === "ai") {{
        if (matchesAnyTag(item, ["ai"])) score += 14;
        if (matchesAnyTag(item, ["cloud_credits"])) score += 12;
        if (matchesType(item, ["accelerator", "cloud_credit"])) score += 8;
        if (matchesAnyTag(item, ["digital_skills", "digitalization", "digital"])) {{
          score += 6;
        }}
      }} else if (topicId === "agro") {{
        if (matchesAnyTag(item, ["agrotech", "vettech", "ecotech"])) score += 12;
        if (matchesAnyTag(item, [
          "agriculture",
          "crop_production",
          "livestock",
          "animal_health"
        ])) {{
          score += 10;
        }}
        if (matchesAnyTag(item, ["water", "climate_change", "green_transition"])) {{
          score += 8;
        }}
      }} else if (topicId === "science") {{
        if (matchesAnyTag(item, ["commercialization"])) score += 12;
        if (matchesAnyTag(item, ["science", "research", "higher_education"])) score += 10;
        if (matchesAnyTag(item, ["education", "edtech", "teacher_training"])) score += 8;
      }} else if (topicId === "public") {{
        if (matchesType(item, ["tender"])) score += 16;
        if (matchesAnyTag(item, ["procurement", "project_pipeline"])) score += 12;
        if (matchesAnyTag(item, ["public_sector", "infrastructure", "development", "govtech"])) {{
          score += 9;
        }}
      }} else if (topicId === "business") {{
        if (presetById(FORMAT_PRESETS, "support").matches(item)) score += 12;
        if (matchesAnyTag(item, ["subsidy", "state_program", "business_support"])) score += 10;
        if (matchesAnyTag(item, [
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing"
        ])) {{
          score += 8;
        }}
        if (regionalPriority(item) >= 3) score += 5;
      }} else if (topicId === "ngo") {{
        if (matchesAnyTag(item, ["ngo", "civil_society", "media", "journalism"])) score += 12;
        if (matchesAnyTag(item, [
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ])) {{
          score += 10;
        }}
      }}
      if (activeTopicPreset().matches(item)) score += 2;
      return score;
    }}

    function compareVisibleItems(left, right) {{
      if (state.sort === "deadline") {{
        return compareDeadlineItems(left, right);
      }}
      if (state.sort === "updated") {{
        return compareUpdatedItems(left, right);
      }}
      return (
        topicPriorityScore(right) - topicPriorityScore(left)
        || comparePriorityItems(left, right)
      );
    }}

    function visibleItems() {{
      const query = state.query.trim().toLowerCase();
      const today = localDateISO();
      const historicalLifecycle = state.lifecycle === "closed" || state.lifecycle === "awarded";
      const audiencePreset = activeAudiencePreset();
      const formatPreset = activeFormatPreset();
      const topicPreset = activeTopicPreset();
      const lifecycleFilter = activeLifecycleFilter();
      const regionFilter = activeRegionFilter();
      const deadlineFilter = activeDeadlineFilter();
      return state.items
        .filter((item) => {{
          const haystack = haystackFor(item);
          return item.score >= state.minScore
            && (
              (state.includeArchived || historicalLifecycle)
              || !item.deadline
              || item.deadline >= today
            )
            && (state.source === "all" || item.source === state.source)
            && audiencePreset.matches(item)
            && formatPreset.matches(item)
            && topicPreset.matches(item)
            && lifecycleFilter.matches(item)
            && regionFilter.matches(item)
            && deadlineFilter.matches(item)
            && (!query || haystack.includes(query));
        }})
        .slice()
        .sort(compareVisibleItems);
    }}

    function renderSourceFilter() {{
      const select = $("#source-filter");
      const sources = [
        ...new Set([
          ...state.items.map((item) => item.source),
          ...state.sources.map((source) => source.slug).filter(Boolean)
        ])
      ].sort();
      const options = sources.map((source) => (
        `<option value="${{escapeHtml(source)}}">`
        + `${{escapeHtml(humanizeLabel(source))}}</option>`
      ));
      select.innerHTML = (
        `<option value="all">${{escapeHtml(copy.all_sources)}}</option>`
        + options.join("")
      );
      select.value = state.source;
      if (select.value !== state.source) {{
        state.source = "all";
        select.value = state.source;
      }}
    }}

    function renderPresetControls() {{
      const audienceRoot = $("#audience-presets");
      const formatRoot = $("#format-presets");
      const topicRoot = $("#topic-presets");
      audienceRoot.innerHTML = AUDIENCE_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="audience"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.audience === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
      formatRoot.innerHTML = FORMAT_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="format"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.format === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
      topicRoot.innerHTML = TOPIC_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="topic"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.topic === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
    }}

    function renderMetrics() {{
      const highPriority = visibleItems().length;
      const sourceCount = new Set(state.items.map((item) => item.source)).size;
      $("#metric-total").textContent = formatNumber.format(
        state.health ? state.health.items : state.items.length
      );
      $("#metric-strong").textContent = formatNumber.format(highPriority);
      $("#metric-sources").textContent = formatNumber.format(
        state.coverage
          ? state.coverage.enabled_sources
          : state.sources.length || sourceCount || 0
      );
    }}

    function renderSourceControls() {{
      const summary = $("#source-summary");
      const toggle = $("#toggle-sources");
      const total = state.sources.length;
      if (!total) {{
        summary.textContent = copy.source_catalog_unavailable;
        toggle.classList.add("hidden");
        return;
      }}
      const shown = state.showAllSources ? total : Math.min(total, COLLAPSED_SOURCES);
      summary.textContent = total > COLLAPSED_SOURCES
        ? text("showing_sources", {{
            shown: formatNumber.format(shown),
            total: formatNumber.format(total)
          }})
        : text("sources_connected", {{ total: formatNumber.format(total) }});
      if (total <= COLLAPSED_SOURCES) {{
        toggle.classList.add("hidden");
        return;
      }}
      toggle.classList.remove("hidden");
      toggle.textContent = state.showAllSources
        ? copy.show_fewer_sources
        : text("show_all_sources_with_total", {{ total: formatNumber.format(total) }});
    }}

    function renderSources() {{
      const list = $("#source-list");
      if (!state.sources.length) {{
        list.innerHTML = (
          `<div class="message">${{escapeHtml(copy.source_catalog_unavailable)}}</div>`
        );
        renderSourceControls();
        return;
      }}
      const localRelevantCounts = localRelevantBySource();
      const sources = state.showAllSources
        ? state.sources
        : state.sources.slice(0, COLLAPSED_SOURCES);
      list.innerHTML = sources.map((source) => {{
        const items = Number.isFinite(source.items) ? source.items : null;
        const relevant = Number.isFinite(source.relevant_open_items)
          ? source.relevant_open_items
          : null;
        const localRelevant = localRelevantCounts.get(source.slug);
        const relevantCount = Number.isFinite(localRelevant)
          ? localRelevant
          : relevant || 0;
        const countIndexed = items === null
          ? copy.coverage_unavailable
          : text("indexed_count", {{ count: formatNumber.format(items) }});
        const countRelevant = text("relevant_open_count", {{
          count: formatNumber.format(relevantCount)
        }});
        const iconVariant = sourceIconVariant(source);
        const sourceName = escapeHtml(source.name || humanizeLabel(source.slug));
        return `
        <a
          class="source-card avds-source-card"
          href="${{escapeHtml(source.base_url)}}"
          target="_blank"
          rel="noopener"
          data-avds-component="source-card"
        >
          <span
            class="
              source-icon
              avds-source-card__icon
              avds-source-card__icon--${{iconVariant}}
              source-icon--${{iconVariant}}
            "
            aria-hidden="true"
            data-avds-component="source-icon"
          >${{escapeHtml(sourceInitials(source))}}</span>
          <div
            class="source-main avds-source-card__body"
            data-avds-component="source-main"
          >
            <strong class="avds-source-card__name">${{sourceName}}</strong>
            <div class="source-meta" data-avds-component="source-meta">
              ${{sourceBadge(source)}}
              <span class="source-note">${{escapeHtml(sourceContextLabel(source))}}</span>
            </div>
          </div>
          <span
            class="source-url avds-source-card__meta"
            title="${{escapeHtml(source.base_url)}}"
            data-avds-component="source-url"
          >${{escapeHtml(shortUrl(source.base_url))}}</span>
          <div class="source-count" data-avds-component="source-count">
            <span>${{escapeHtml(countIndexed)}}</span>
            <span>${{escapeHtml(countRelevant)}}</span>
          </div>
          <span
            class="source-arrow avds-source-card__arrow"
            aria-hidden="true"
          >›</span>
        </a>
      `;
      }}).join("");
      renderSourceControls();
    }}

    function renderHealth() {{
      const status = state.health && state.health.status ? state.health.status : "-";
      const statusValue = status === "ok"
        ? copy.health_ok_value
        : copy.health_attention_value;
      const items = state.health && Number.isFinite(state.health.items)
        ? formatNumber.format(state.health.items)
        : "-";
      const sources = state.coverage && Number.isFinite(state.coverage.enabled_sources)
        ? formatNumber.format(state.coverage.enabled_sources)
        : formatNumber.format(state.sources.length || 0);
      const latestUpdate = state.items.reduce((latest, item) => {{
        const rank = discoveredRank(item);
        return rank > latest ? rank : latest;
      }}, 0);
      const checkedAt = formatDateTime(state.lastCheckedAt);
      const updatedAt = latestUpdate
        ? formatDateTime(new Date(latestUpdate).toISOString())
        : "—";
      $("#health-status").textContent = statusValue;
      $("#health-items").textContent = items;
      $("#health-sources").textContent = sources;
      $("#health-note").textContent = latestUpdate
        ? text("health_note_ready", {{
            checked_at: checkedAt,
            updated_at: updatedAt
          }})
        : text("health_note_ready_no_items", {{
            checked_at: checkedAt
          }});
      $("#status-pill span:last-child").textContent = status === "ok"
        ? copy.api_online
        : copy.api_failed;
    }}

    function renderFilterSummary(resultCount) {{
      const summary = $("#filter-summary");
      const pills = [
        `<span class="summary-pill result">${{escapeHtml(
          text("summary_matches", {{ count: formatNumber.format(resultCount) }})
        )}}</span>`
      ];
      if (state.query.trim()) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_search", {{ value: state.query.trim() }})
          )}}</span>`
        );
      }}
      if (state.audience !== DEFAULT_AUDIENCE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_audience", {{ value: activeAudiencePreset().label }})
          )}}</span>`
        );
      }}
      if (state.format !== DEFAULT_FORMAT) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_format", {{ value: activeFormatPreset().label }})
          )}}</span>`
        );
      }}
      if (state.topic !== DEFAULT_TOPIC) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_topic", {{ value: activeTopicPreset().label }})
          )}}</span>`
        );
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_lifecycle", {{ value: activeLifecycleFilter().label }})
          )}}</span>`
        );
      }}
      if (state.region !== DEFAULT_REGION) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_region", {{ value: activeRegionFilter().label }})
          )}}</span>`
        );
      }}
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_deadline", {{ value: activeDeadlineFilter().label }})
          )}}</span>`
        );
      }}
      if (state.sort !== DEFAULT_SORT) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_sort", {{ value: activeSortOption().label }})
          )}}</span>`
        );
      }}
      if (state.source !== "all") {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(humanizeLabel(state.source))}}</span>`
        );
      }}
      if (state.includeArchived) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(copy.summary_scope_all)}}</span>`
        );
      }}
      if (state.minScore !== DEFAULT_SCORE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_score", {{ value: activeScoreOption().label }})
          )}}</span>`
        );
      }}
      summary.innerHTML = pills.join("");
      $("#clear-filters").disabled = !hasActiveFilters();
    }}

    function renderOpportunities() {{
      const list = $("#opportunities-list");
      const message = $("#opportunities-message");
      const loadMoreWrap = $("#load-more-wrap");
      const loadMore = $("#load-more");
      const items = visibleItems();
      renderPresetControls();
      syncControlsFromState();
      syncUrlState();
      $("#opportunities-description").textContent = state.includeArchived
        ? copy.opportunities_description_all
        : copy.opportunities_description;
      if (hasActiveFilters()) {{
        $("#opportunities-description").textContent = [
          text("summary_matches", {{ count: formatNumber.format(items.length) }}),
          state.audience !== DEFAULT_AUDIENCE ? activeAudiencePreset().label : "",
          state.format !== DEFAULT_FORMAT ? activeFormatPreset().label : "",
          state.topic !== DEFAULT_TOPIC ? activeTopicPreset().label : "",
          state.region !== DEFAULT_REGION ? activeRegionFilter().label : ""
        ].filter(Boolean).join(" • ");
      }}
      renderMetrics();
      renderSpotlights();
      renderPathways();
      renderThemes();
      renderTopicBrief(items);
      renderFilterSummary(items.length);

      if (!state.items.length) {{
        message.className = "message";
        message.textContent = copy.no_indexed_items;
        list.innerHTML = "";
        loadMoreWrap.classList.add("hidden");
        return;
      }}
      if (!items.length) {{
        message.className = "message empty";
        message.innerHTML = renderEmptyState();
        list.innerHTML = "";
        loadMoreWrap.classList.add("hidden");
        return;
      }}

      message.className = "message hidden";
      const visible = items.slice(0, state.visibleLimit);
      list.innerHTML = visible.map((item) => {{
        const tags = Array.from(
          new Map(
            (Array.isArray(item.tags) ? item.tags : []).map((tag) => [
              String(tag).trim().toLowerCase(),
              tag
            ])
          ).values()
        ).slice(0, 5);
        const scoreTone = scoreClass(item.score);
        const deadline = formatDeadline(item.deadline);
        const sourceName = humanizeLabel(item.source);
        const funderLabel = item.funder ? escapeHtml(item.funder) : escapeHtml(sourceName);
        const funderHref = escapeHtml(funderPageHref(funderSlug(item)));
        const funderProfileLink = (
          `<a class="footer-funder-link" href="${{funderHref}}">`
          + `${{escapeHtml(copy.view_funder)}}</a>`
        );
        const footerSource = item.funder
          && String(item.funder).toLowerCase() !== sourceName.toLowerCase()
          ? `${{funderLabel}}<span class="footer-sep">|</span>${{escapeHtml(sourceName)}}`
          : funderLabel;
        const badges = itemBadges(item);
        const cardTitleText = String(item.title || "");
        const cardTitle = escapeHtml(cardTitleText);
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const pageUrl = escapeHtml(opportunityPageHref(item.id));
        const clickLabel = escapeHtml(cardTitleText);
        return `<article
          class="opportunity avds-document-row ${{scoreTone}}"
          data-avds-component="opportunity-card"
        >
          <div class="opportunity-main">
            <div class="opportunity-top">
              <div>
                <h3>
                  <a href="${{pageUrl}}">
                    ${{cardTitle}}
                  </a>
                </h3>
                <div class="tags">
                  ${{tags.map((tag) => (
                    `<span class="tag" data-avds-component="tag">`
                    + `${{escapeHtml(humanizeLabel(tag))}}</span>`
                  )).join("")}}
                </div>
              </div>
              <aside class="side">
                <span
                  class="score ${{scoreTone}}"
                  data-avds-component="score"
                  title="${{escapeHtml(copy.score_title)}}"
                >${{formatScore(item.score)}}</span>
                ${{badges}}
              </aside>
            </div>
            <p>${{escapeHtml(summarize(item))}}</p>
            <div class="signal-box">
              <span class="signal-label">${{escapeHtml(copy.signal_label)}}</span>
              <p class="signal-lede">${{escapeHtml(opportunitySignalText(item))}}</p>
              <div class="signal-pills">
                ${{opportunitySignalPillsMarkup(item)}}
              </div>
            </div>
            <div class="fit-block">
              <span class="fit-label">${{escapeHtml(copy.fit_label)}}</span>
              <div class="fit-pills">
                ${{fitPillsMarkup(item)}}
              </div>
            </div>
            <div class="card-actions">
              <button
                class="detail-link"
                type="button"
                data-opportunity-detail="${{opportunityId}}"
                data-opportunity-url="${{cardUrl}}"
              >${{escapeHtml(copy.open_details)}}</button>
              <a
                class="more-link"
                href="${{pageUrl}}"
                target="_blank"
                rel="noopener"
              >${{escapeHtml(copy.read_more)}}</a>
            </div>
            <div class="opportunity-footer">
              <span class="footer-source">${{footerSource}}
                <span class="footer-sep">|</span>${{funderProfileLink}}
              </span>
              <span class="footer-deadline">${{escapeHtml(deadline)}}</span>
            </div>
            <button
              class="opportunity-click"
              type="button"
              data-opportunity-id="${{opportunityId}}"
              data-opportunity-url="${{cardUrl}}"
              aria-label="${{escapeHtml(copy.open_details)}}: ${{clickLabel}}"
            ></button>
          </div>
        </article>`;
      }}).join("");
      if (items.length > visible.length) {{
        loadMoreWrap.classList.remove("hidden");
        loadMore.textContent = text("results_button", {{
          count: formatNumber.format(Math.min(DEFAULT_VISIBLE_ITEMS, items.length - visible.length))
        }});
      }} else {{
        loadMoreWrap.classList.add("hidden");
      }}
      bindOpportunityCards();
    }}

    let searchRenderTimer = 0;
    function scheduleOpportunityRender() {{
      window.clearTimeout(searchRenderTimer);
      searchRenderTimer = window.setTimeout(renderOpportunities, 120);
    }}

    function bindOpportunityCards() {{
      const cards = document.querySelectorAll("[data-opportunity-id]");
      cards.forEach((button) => {{
        if (button.dataset.bound === "true") {{
          return;
        }}
        button.dataset.bound = "true";
        button.addEventListener("click", () => {{
          const opportunityId = button.getAttribute("data-opportunity-id");
          const fallbackUrl = button.getAttribute("data-opportunity-url") || "";
          openOpportunityDetail(opportunityId, fallbackUrl);
        }});
      }});
      const detailButtons = document.querySelectorAll("[data-opportunity-detail]");
      detailButtons.forEach((button) => {{
        if (button.dataset.bound === "true") {{
          return;
        }}
        button.dataset.bound = "true";
        button.addEventListener("click", () => {{
          const opportunityId = button.getAttribute("data-opportunity-detail");
          const fallbackUrl = button.getAttribute("data-opportunity-url") || "";
          openOpportunityDetail(opportunityId, fallbackUrl);
        }});
      }});
    }}

    async function loadHealth() {{
      state.health = await fetchJson("/health");
      state.lastCheckedAt = new Date().toISOString();
      renderHealth();
      renderMetrics();
    }}

    async function loadSources() {{
      try {{
        state.coverage = await fetchJson("/coverage");
        state.sources = Array.isArray(state.coverage.sources)
          ? state.coverage.sources
          : [];
      }} catch (error) {{
        state.coverage = null;
        state.sources = await fetchJson("/sources");
      }}
      state.lastCheckedAt = new Date().toISOString();
      renderSources();
      renderHealth();
      renderMetrics();
    }}

    async function loadFunders() {{
      try {{
        state.funders = await fetchJson("/funders?limit=24");
      }} catch {{
        state.funders = [];
      }}
      renderFunders();
    }}

    async function loadOpportunities() {{
      const message = $("#opportunities-message");
      const today = localDateISO();
      const params = state.includeArchived
        ? "limit=5000&min_score=0&include_irrelevant=true"
        : `limit=5000&min_score=0&deadline_after=${{today}}`;
      message.className = "message";
      message.textContent = copy.loading_opportunities;
      state.items = await fetchJson(withLang(`/opportunities?${{params}}`));
      state.lastCheckedAt = new Date().toISOString();
      resetVisibleLimit();
      renderSourceFilter();
      renderSources();
      renderOpportunities();
    }}

    async function reloadAll() {{
      try {{
        await Promise.all([loadHealth(), loadSources(), loadFunders(), loadOpportunities()]);
      }} catch (error) {{
        $("#opportunities-message").className = "message error";
        $("#opportunities-message").textContent = error.message;
        $("#status-pill span:last-child").textContent = copy.api_error;
      }} finally {{
        syncViewFromHash();
      }}
    }}

    const viewTargets = {{
      opportunities: "#opportunities-panel",
      sources: "#sources-panel",
      health: "#health-panel"
    }};
    const viewButtons = document.querySelectorAll("[data-view]");

    function setActiveView(view) {{
      viewButtons.forEach((button) => {{
        button.setAttribute(
          "aria-pressed",
          String(button.dataset.view === view)
        );
      }});
    }}

    function goToView(view, options = {{}}) {{
      const selector = viewTargets[view] || viewTargets.opportunities;
      const target = document.querySelector(selector);
      if (!target) return;
      const shouldScroll = options.scroll !== false;
      setActiveView(view);
      const nextHash = `#${{view}}`;
      if (window.location.hash !== nextHash) {{
        window.history.replaceState(
          null,
          "",
          `${{window.location.pathname}}${{window.location.search}}${{nextHash}}`
        );
      }}
      if (shouldScroll) {{
        target.scrollIntoView({{ behavior: "auto", block: "start" }});
      }}
    }}

    function syncViewFromHash(options = {{}}) {{
      const view = window.location.hash.replace("#", "");
      if (viewTargets[view]) {{
        goToView(view, options);
      }} else {{
        setActiveView("opportunities");
      }}
    }}

    let resizeSyncTimer = 0;
    function scheduleHashViewSync() {{
      const view = window.location.hash.replace("#", "");
      if (!viewTargets[view]) return;
      window.clearTimeout(resizeSyncTimer);
      resizeSyncTimer = window.setTimeout(() => {{
        syncViewFromHash({{ scroll: false }});
      }}, 120);
    }}

    viewButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        goToView(button.dataset.view);
      }});
    }});

    applyStateFromUrl();
    renderSavedViews();
    window.addEventListener("hashchange", syncViewFromHash);
    window.addEventListener("resize", scheduleHashViewSync);
    window.requestAnimationFrame(syncViewFromHash);
    $("#detail-close").addEventListener("click", closeDetailShell);
    $("#detail-backdrop").addEventListener("click", closeDetailShell);
    window.addEventListener("keydown", (event) => {{
      if (event.key === "Escape" && !$("#detail-drawer").hidden) {{
        closeDetailShell();
      }}
    }});

    $("#toggle-sources").addEventListener("click", () => {{
      state.showAllSources = !state.showAllSources;
      renderSources();
    }});
    $("#reload").addEventListener("click", () => {{
      if (!window.confirm(copy.reload_confirm)) return;
      reloadAll();
    }});
    $("#load-more").addEventListener("click", () => {{
      state.visibleLimit += DEFAULT_VISIBLE_ITEMS;
      renderOpportunities();
    }});
    document.addEventListener("click", (event) => {{
      const heroAction = event.target.closest("[data-hero-view]");
      if (heroAction) {{
        applyHeroAction(heroAction);
        return;
      }}
      const emptyAction = event.target.closest("[data-empty-action]");
      if (emptyAction) {{
        applyEmptyAction(emptyAction.getAttribute("data-empty-action") || "");
        return;
      }}
      const topicReset = event.target.closest("[data-topic-reset]");
      if (topicReset) {{
        state.topic = DEFAULT_TOPIC;
        resetVisibleLimit();
        renderOpportunities();
        return;
      }}
      const button = event.target.closest("[data-preset-kind]");
      if (!button) return;
      const presetKind = button.getAttribute("data-preset-kind");
      const presetId = button.getAttribute("data-preset-id") || "all";
      if (presetKind === "audience") {{
        state.audience = presetId;
      }}
      if (presetKind === "format") {{
        state.format = presetId;
      }}
      if (presetKind === "topic") {{
        state.topic = presetId;
      }}
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#search").addEventListener("input", (event) => {{
      state.query = event.target.value;
      resetVisibleLimit();
      scheduleOpportunityRender();
    }});
    $("#sort-filter").addEventListener("change", (event) => {{
      state.sort = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#score-filter").addEventListener("change", (event) => {{
      state.minScore = Number(event.target.value);
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#scope-filter").addEventListener("change", (event) => {{
      state.includeArchived = event.target.value === "all";
      state.minScore = scoreDefaultForScope();
      if (
        !state.includeArchived
        && (state.lifecycle === "closed" || state.lifecycle === "awarded")
      ) {{
        state.lifecycle = DEFAULT_LIFECYCLE;
      }}
      reloadAll();
    }});
    $("#lifecycle-filter").addEventListener("change", (event) => {{
      state.lifecycle = event.target.value;
      resetVisibleLimit();
      if (
        (state.lifecycle === "closed" || state.lifecycle === "awarded")
        && !state.includeArchived
      ) {{
        state.includeArchived = true;
        state.minScore = scoreDefaultForScope();
        reloadAll();
        return;
      }}
      renderOpportunities();
    }});
    $("#source-filter").addEventListener("change", (event) => {{
      state.source = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#region-filter").addEventListener("change", (event) => {{
      state.region = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#deadline-filter").addEventListener("change", (event) => {{
      state.deadlineMode = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#clear-filters").addEventListener("click", () => {{
      if (!hasActiveFilters()) return;
      clearAllFilters();
    }});
    $("#save-view").addEventListener("click", saveCurrentView);
    $("#share-view").addEventListener("click", () => {{
      shareCurrentView();
    }});
    document.addEventListener("click", (event) => {{
      const applyButton = event.target.closest("[data-saved-view]");
      if (applyButton) {{
        applySavedView(applyButton.getAttribute("data-saved-view") || "");
        return;
      }}
      const removeButton = event.target.closest("[data-remove-saved-view]");
      if (removeButton) {{
        removeSavedView(removeButton.getAttribute("data-remove-saved-view") || "");
      }}
    }});

    reloadAll();
  </script>
</body>
</html>"""  # nosec B608
