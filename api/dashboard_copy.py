"""Localized public-dashboard copy kept separate from rendering logic."""

from __future__ import annotations

from typing import cast

SUPPORTED_LANGS = {"ru", "en"}

COPY = {
    "ru": {
        "lang": "ru",
        "locale": "ru-KZ",
        "title": "QAZ.FUND – гранты и меры поддержки для Казахстана",
        "meta_description": (
            "QAZ.FUND – публичный навигатор по грантам, субсидиям, акселераторам "
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
        "hero_stage_eyebrow": "Рабочие сценарии",
        "hero_stage_title": "Что нужно сделать сейчас?",
        "hero_stage_point_one": "Отфильтруйте каталог и сохраните ссылку на точную выдачу",
        "hero_stage_point_two": "Скопируйте рабочую справку с источником и полями для проверки",
        "hero_stage_point_three": "Выгрузите таблицу или добавьте ближайшие сроки в календарь",
        "hero_picks_label": "Рабочие сценарии",
        "hero_pick_startup": "Найти поддержку",
        "hero_pick_business": "Проверить программу",
        "hero_pick_farmer": "Сроки до месяца",
        "hero_pick_science": "Господдержка РК",
        "hero_pick_tenders": "Тендеры и закупки",
        "spotlight_section_eyebrow": "Подборки для старта",
        "spotlight_section_title": "Актуально сейчас",
        "spotlight_section_description": (
            "Главные сигналы каталога: сильные совпадения, локальные меры поддержки "
            "и ближайшие сроки."
        ),
        "spotlight_count": "В подборке: {count}",
        "spotlight_action_open": "Открыть подборку",
        "spotlight_empty": "В этой подборке сейчас нет активных карточек.",
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
        "pathways_section_title": "По типу проекта",
        "pathways_section_description": (
            "Выберите, кому нужна поддержка, и сразу получите подходящую выдачу."
        ),
        "pathways_count": "Сейчас: {count}",
        "pathways_action_open": "Открыть направление",
        "pathways_empty": "Для этого типа проекта сейчас нет активных карточек.",
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
        "themes_section_title": "По направлению",
        "themes_section_description": (
            "Откройте возможности по теме без ручного просмотра всего каталога."
        ),
        "discovery_library_summary": "Подборки и маршруты",
        "discovery_library_description": (
            "Готовые срезы для первого знакомства с каталогом."
        ),
        "themes_count": "Сейчас: {count}",
        "themes_action_open": "Открыть тему",
        "themes_empty": "По этому направлению сейчас нет активных карточек.",
        "funder_section_eyebrow": "Фонды и доноры",
        "funder_section_title": "Активные фонды и программы",
        "funder_section_description": (
            "Сводка по фондам и программам: где есть живые возможности, какие "
            "темы они обычно поддерживают и куда смотреть дальше."
        ),
        "funder_open_profile": "Профиль фонда",
        "funder_empty": "Активные профили фондов сейчас не найдены.",
        "funder_live_now": "Живые возможности",
        "funder_total_items": "Всего в индексе",
        "funder_next_deadline": "Ближайший срок",
        "funder_overview_intro": (
            "Профиль построен по опубликованным программам и объявлениям."
        ),
        "funder_overview_types": "Форматы: {types}.",
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
        "status_checking": "Каталог доступен",
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
        "metric_relevant": "Актуально в индексе",
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
        "sort_priority": "По приоритету действий",
        "sort_deadline": "Ближайший дедлайн",
        "sort_updated": "Недавно обновленные",
        "min_score_label": "Релевантность каталога",
        "min_score_aria": "Минимальная релевантность каталога",
        "source_label": "Источник",
        "source_aria": "Источник",
        "all_scores": "Все результаты",
        "score_option_03": "Базовая релевантность",
        "score_option_05": "Хорошая релевантность",
        "score_option_07": "Высокая релевантность",
        "score_help": (
            "Оценка учитывает регион и тему, а порядок – ещё и доступный срок. "
            "Это не вероятность одобрения; условия сверяйте с первоисточником."
        ),
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
        "trust_library_summary": "Источники и прозрачность",
        "trust_library_description": (
            "Покрытие, свежесть данных, активные фонды и методология."
        ),
        "source_refresh_title": "Последнее успешное обновление источника",
        "source_refresh_value": "Обновлено {date}",
        "source_refresh_unknown": "Дата обновления не указана",
        "health_title": "Статус данных",
        "health_description": (
            "Показываем, что каталог доступен и сколько источников сейчас участвует "
            "в витрине."
        ),
        "health_ok_value": "Данные актуальны",
        "health_attention_value": "Проверить",
        "health_note_loading": (
            "Данные каталога доступны. Уточняем время последнего обновления."
        ),
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
        "health_stale_sources": "Устаревшие источники",
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
        "summary_score": "Релевантность: {value}",
        "summary_scope_all": "Включая архив",
        "methodology_title": "Как мы собираем и показываем данные",
        "methodology_description": (
            "Коротко объясняем, откуда берется каталог, что означает релевантность и "
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
            "Релевантность учитывает регион и тему; порядок – ещё и доступный срок. "
            "Компоненты ограничены и объяснимы. Это не вероятность одобрения и не "
            "юридическое заключение."
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
            "проверьте дедлайн, критерии участия, состав документов и способ отправки "
            "заявки."
        ),
        "role_guide_title": "Как использовать QAZ.FUND в работе",
        "role_guide_description": (
            "Одни и те же данные можно быстро превратить в проверяемую подборку, "
            "редакционную справку или служебный материал."
        ),
        "role_analyst_title": "Аналитику",
        "role_analyst_text": (
            "Зафиксируйте фильтры ссылкой, сравните поля и выгрузите выдачу в CSV."
        ),
        "role_journalist_title": "Журналисту",
        "role_journalist_text": (
            "Скопируйте справку из карточки, укажите официальный источник и дату проверки."
        ),
        "role_editor_title": "Редактору",
        "role_editor_text": (
            "Отделите подтверждённые поля от того, что ещё нужно сверить перед публикацией."
        ),
        "role_lawyer_title": "Юристу",
        "role_lawyer_text": (
            "Проверьте актуальную редакцию условий, заявителя, документы, срок и канал подачи."
        ),
        "role_official_title": "Госслужащему",
        "role_official_text": (
            "Соберите воспроизводимую подборку по РК, выгрузите таблицу и календарь сроков."
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
        "collections_label": "Рабочие подборки",
        "collections_aria": "Сохранённые фильтры и инструменты для повторной работы",
        "collections_empty": "Сохраните текущие фильтры, чтобы быстро вернуться к этой выдаче.",
        "save_view": "Сохранить фильтры",
        "share_view": "Поделиться выдачей",
        "saved_view_saved": "Подборка сохранена локально.",
        "saved_view_removed": "Подборка удалена.",
        "saved_view_shared": "Ссылка на текущую подборку скопирована.",
        "saved_view_default_name": "Моя подборка",
        "saved_view_remove_aria": "Удалить подборку",
        "saved_view_status_label": "Статус подборок",
        "saved_view_share_prompt": "Скопируйте ссылку на текущую подборку",
        "advanced_filters": "Дополнительные фильтры",
        "mobile_filters_summary": "Настроить выдачу",
        "mobile_app_navigation": "Основные разделы QAZ.FUND",
        "mobile_app_tagline": "Навигатор возможностей",
        "mobile_catalog": "Каталог",
        "mobile_sources": "Источники",
        "mobile_saved": "Сохранённое",
        "mobile_filters": "Фильтры",
        "mobile_open_filters": "Открыть фильтры каталога",
        "mobile_close_filters": "Закрыть фильтры",
        "mobile_show_results": "Показать результаты",
        "export_csv": "Таблица CSV",
        "export_deadlines": "Сроки в календарь",
        "saved_opportunity_saved": "Карточка сохранена локально.",
        "saved_opportunity_removed": "Карточка удалена из локальных сохранённых.",
        "save_opportunity": "Сохранить",
        "unsave_opportunity": "Убрать",
        "workspace_filter": "Сохранённые",
        "workspace_filter_count": "Сохранённые: {count}",
        "workspace_filter_empty": "Сначала сохраните подходящую карточку.",
        "workflow_label": "Этап работы",
        "workflow_review": "На проверке",
        "workflow_fit": "Подходит",
        "workflow_preparing": "Готовим заявку",
        "workflow_submitted": "Отправлено",
        "workflow_result": "Получен результат",
        "workflow_updated": "Этап карточки обновлён.",
        "workspace_queue_title": "Следующие действия",
        "workspace_queue_aria": "Очередь действий по сохранённым возможностям",
        "workspace_queue_local": "Сохраняется только в этом браузере.",
        "workspace_queue_empty": "В текущем каталоге нет активных сохранённых карточек.",
        "workspace_queue_more": "Ещё в работе: {count}",
        "workspace_action_review": "Проверьте критерии на официальном источнике.",
        "workspace_action_fit": "Подтвердите соответствие требованиям и срок.",
        "workspace_action_preparing": "Соберите пакет и зафиксируйте срок подачи.",
        "workspace_action_submitted": "Сохраните подтверждение и следите за условиями.",
        "workspace_action_result": "Зафиксируйте результат по этой возможности.",
        "workspace_deadline_today": "Срок сегодня",
        "workspace_deadline_days": "Срок через {count} дн.",
        "workspace_deadline_date": "Срок: {date}",
        "workspace_deadline_rolling": "Постоянный приём",
        "workspace_backup": "Выгрузить",
        "workspace_backup_aria": "Выгрузка данных и резервная копия локальной работы",
        "workspace_export": "Резервная копия",
        "workspace_import": "Восстановить копию",
        "workspace_exported": "Резервная копия скачана.",
        "workspace_imported": "Рабочее пространство восстановлено.",
        "workspace_import_error": "Не удалось прочитать резервную копию.",
        "report_issue": "Уточнить данные",
        "open_source_short": "Официальный источник",
        "footer_owner": "QAZ.FUND – публичный навигатор возможностей. Сделано",
        "footer_disclaimer": (
            "QAZ.FUND не выдаёт гранты и не принимает заявки. Финальные условия, "
            "сроки и формы подачи проверяйте на официальном источнике."
        ),
        "footer_support": "Обратная связь",
        "footer_qdev": "qdev.run",
        "view_funder": "Профиль фонда",
        "fit_label": "Кому подходит",
        "fit_unknown": "Критерии нужно уточнить",
        "fit_deadline_soon": "Скоро закрывается",
        "fit_global": "Глобальная подача",
        "signal_label": "Почему это в фокусе",
        "card_meta_label": "Параметры",
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
        "meta_deadline_later": "Позже месяца",
        "detail_fit_title": "Быстрая оценка",
        "detail_source_status_title": "Статус источника",
        "detail_fit_good": "Скорее всего подходит",
        "detail_fit_review": "Нужна ручная проверка критериев",
        "no_indexed_items": "Каталог временно не содержит доступных карточек.",
        "no_filtered_items": "По текущим фильтрам ничего не найдено.",
        "no_filtered_items_hint": (
            "Попробуйте ослабить один из фильтров – каталог сразу пересчитает выдачу."
        ),
        "empty_action_clear": "Сбросить всё",
        "empty_action_region": "Все регионы",
        "empty_action_deadline": "Любые сроки",
        "empty_action_score": "Стандартный порог",
        "empty_action_scope": "Открыть весь индекс",
        "open_details": "Быстрый просмотр",
        "read_more": "Полная карточка",
        "open_rolling": "Открыто / бессрочно",
        "score_title": "Объяснимая релевантность каталога; не вероятность одобрения",
        "score_exact": "Высокая",
        "score_high": "Хорошая",
        "score_base": "Базовая",
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
        "detail_readiness_title": "Полнота данных",
        "detail_readiness_complete": "Подтверждены все {total} ключевых поля.",
        "detail_readiness_partial": (
            "Подтверждено {known} из {total}. На источнике проверьте: {missing}."
        ),
        "detail_copy_brief": "Скопировать справку",
        "detail_copy_brief_done": "Рабочая справка скопирована.",
        "detail_copy_brief_prompt": "Скопируйте рабочую справку",
        "detail_brief_heading": "QAZ.FUND – рабочая справка",
        "detail_brief_summary": "Кратко",
        "detail_brief_source": "Организатор или источник",
        "detail_brief_format": "Формат",
        "detail_brief_region": "Регион",
        "detail_brief_deadline": "Срок",
        "detail_brief_amount": "Сумма",
        "detail_brief_official_url": "Официальный источник",
        "detail_brief_application_url": "Подача",
        "detail_brief_caveat": (
            "Проверить на официальном источнике: действующие условия, право на "
            "участие, документы, срок и канал подачи."
        ),
        "verification_eyebrow": "Проверка и передача",
        "verification_title": "Перед использованием карточки",
        "verification_description": (
            "Карточка подходит для первичного анализа и рабочей справки, но не "
            "подтверждает право на участие и не заменяет официальные условия."
        ),
        "verification_eligibility_title": "Право на участие",
        "verification_eligibility_text": (
            "Сверьте тип заявителя, юрисдикцию, ограничения и требуемый опыт."
        ),
        "verification_terms_title": "Действующие условия",
        "verification_terms_text": (
            "Проверьте последнюю редакцию, срок, сумму и способ отправки заявки."
        ),
        "verification_procurement_title": "Закупочная документация",
        "verification_procurement_text": (
            "Для тендеров отдельно проверьте лоты, квалификацию, приложения и изменения."
        ),
        "verification_publication_title": "Публикация и служебная записка",
        "verification_publication_text": (
            "Укажите официальный источник и дату фактической проверки сведений."
        ),
        "detail_missing_labels": {
            "deadline": "срок",
            "amount": "сумму",
            "eligibility": "требования к заявителю",
            "application": "путь подачи",
        },
        "detail_sections_title": "Текст и выдержки",
        "detail_status_ok": "Описание и ключевые поля собраны с официального источника",
        "detail_status_structured_only": "Показываем краткое описание и структурированные поля",
        "detail_status_blocked": "Источник не дал забрать полный текст автоматически",
        "detail_status_not_allowed": "Для этого источника локальная загрузка отключена",
        "detail_status_too_large": "Страница слишком тяжелая для локального чтения",
        "detail_status_unsupported_media": "Источник отдал неподдерживаемый формат",
        "detail_status_parse_error": "Не удалось корректно разобрать страницу источника",
        "detail_source_excerpt": "Выдержка с источника",
        "detail_expand_source": "Показать выдержку",
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
            "world_bank_procurement_ca": "Закупки Всемирного банка в Центральной Азии",
            "eu_funding_tenders_ca": "Конкурсы ЕС для Центральной Азии",
            "canada_cfli_ca": "Канадский фонд местных инициатив",
            "adb_kazakhstan": "АБР Казахстан",
            "eeas_kazakhstan": "Представительство ЕС в Казахстане",
            "unicef_kazakhstan": "UNICEF Казахстан",
            "unesco_iite": "UNESCO IITE",
            "isdb_project_procurement": "IsDB Procurement",
            "islamic_development_bank": "Исламский банк развития",
            "ebrd_ecepp_procurement": "EBRD ECEPP Procurement",
            "undp_procurement": "UNDP Procurement",
            "kazakhstan": "Казахстан",
            "central_asia": "Центральная Азия",
            "eligibility_check_required": "Требуется проверка условий",
            "canada": "Канада",
            "turkmenistan": "Туркменистан",
            "global": "Глобально",
            "kz": "Казахстан",
            "program": "Программа",
            "education": "Образование",
            "education_organisation": "Образовательные организации",
            "agriculture": "Сельское хозяйство",
            "assessment": "Оценка",
            "capacity_building": "Развитие потенциала",
            "children": "Дети",
            "civic": "Гражданские инициативы",
            "cloudflare": "Cloudflare",
            "consultancy": "Консультационные услуги",
            "consulting": "Консалтинг",
            "creative_industries": "Креативные индустрии",
            "culture": "Культура",
            "database": "Базы данных",
            "developer_tools": "Инструменты разработчика",
            "digital": "Цифровые решения",
            "donor": "Донорские программы",
            "ebrd": "ЕБРР",
            "ecepp": "ECEPP",
            "energy": "Энергетика",
            "environment": "Окружающая среда",
            "erasmus": "Erasmus+",
            "erasmus_mundus": "Erasmus Mundus",
            "eu": "ЕС",
            "eu_studies": "Европейские исследования",
            "evaluation": "Оценка проектов",
            "federal": "Федеральные программы",
            "finance": "Финансы",
            "firebase": "Firebase",
            "governance": "Управление",
            "gpu": "GPU",
            "health": "Здравоохранение",
            "higher_education": "Высшее образование",
            "human_rights": "Права человека",
            "infrastructure": "Инфраструктура",
            "isdb": "Исламский банк развития",
            "it": "ИТ",
            "jean_monnet": "Жан Моне",
            "joint_degrees": "Совместные программы",
            "kyrgyz": "Кыргызстан",
            "kyrgyzstan": "Кыргызстан",
            "mobility": "Академическая мобильность",
            "nonprofit_required": "Только для НКО",
            "partnership": "Партнёрство",
            "policy": "Государственная политика",
            "procurement": "Закупки",
            "public_diplomacy": "Публичная дипломатия",
            "regional_development": "Региональное развитие",
            "research": "Исследования",
            "security": "Безопасность",
            "serverless": "Бессерверные технологии",
            "sez": "СЭЗ",
            "social_entrepreneurship": "Социальное предпринимательство",
            "student_exchange": "Студенческий обмен",
            "tajikistan": "Таджикистан",
            "teacher_training": "Подготовка педагогов",
            "technology": "Технологии",
            "transport": "Транспорт",
            "undp": "ПРООН",
            "us": "США",
            "uzbekistan": "Узбекистан",
            "watchlist": "Мониторинг",
            "water": "Водные ресурсы",
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
            "invitation_for_tenders_single": "Тендер",
            "grants_gov": "Grants.gov",
            "fundsforngos": "FundsforNGOs",
            "opportunity_desk": "Opportunity Desk",
            "astana_hub": "Astana Hub",
            "kazakhstan_domestic_support": "Поддержка РК",
            "kazakhstan_opportunity_watch": "Мониторинг возможностей Казахстана",
            "dod_amraa": "DOD-AMRAA",
            "hhs_nih11": "HHS-NIH",
            "united_nations_development_programme": "Программа развития ООН (ПРООН)",
            "european_bank_for_reconstruction_and_development": (
                "Европейский банк реконструкции и развития (ЕБРР)"
            ),
            "kazakhstan_watch": "Мониторинг Казахстана",
            "cloudflare_startups": "Cloudflare Startups",
            "mongodb_startups": "MongoDB Startups",
            "nvidia_inception": "NVIDIA Inception",
        },
    },
    "en": {
        "lang": "en",
        "locale": "en-KZ",
        "title": "QAZ.FUND – funding and support programs for Kazakhstan",
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
        "hero_stage_eyebrow": "Workflows",
        "hero_stage_title": "What do you need to do now?",
        "hero_stage_point_one": "Filter the catalog and save a link to the exact result set",
        "hero_stage_point_two": "Copy a working brief with its source and verification fields",
        "hero_stage_point_three": "Export a table or add the nearest deadlines to your calendar",
        "hero_picks_label": "Workflows",
        "hero_pick_startup": "Find support",
        "hero_pick_business": "Check a program",
        "hero_pick_farmer": "Deadlines this month",
        "hero_pick_science": "Kazakhstan support",
        "hero_pick_tenders": "Tenders and procurement",
        "spotlight_section_eyebrow": "Start here",
        "spotlight_section_title": "Current opportunities",
        "spotlight_section_description": (
            "The catalog's strongest signals: high-fit opportunities, Kazakhstan "
            "support measures, and approaching deadlines."
        ),
        "spotlight_count": "In view: {count}",
        "spotlight_action_open": "Open collection",
        "spotlight_empty": "There are no active items in this collection right now.",
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
        "pathways_section_title": "By project type",
        "pathways_section_description": (
            "Choose who needs support and open a focused result set immediately."
        ),
        "pathways_count": "Now: {count}",
        "pathways_action_open": "Open route",
        "pathways_empty": "There are no active items for this project type right now.",
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
        "themes_section_title": "By focus area",
        "themes_section_description": (
            "Open opportunities by topic without scanning the full catalog."
        ),
        "discovery_library_summary": "Collections and routes",
        "discovery_library_description": (
            "Ready-made views for getting acquainted with the catalog."
        ),
        "themes_count": "Now: {count}",
        "themes_action_open": "Open theme",
        "themes_empty": "There are no active items in this focus area right now.",
        "funder_section_eyebrow": "Funders",
        "funder_section_title": "Active funders and programs",
        "funder_section_description": (
            "A quick funder layer: where live opportunities exist, what they "
            "usually support, and which profiles are worth opening next."
        ),
        "funder_open_profile": "Funder profile",
        "funder_empty": "No active funder profiles are available right now.",
        "funder_live_now": "Live opportunities",
        "funder_total_items": "Total indexed",
        "funder_next_deadline": "Nearest deadline",
        "funder_overview_intro": (
            "This profile is built from published programs and announcements."
        ),
        "funder_overview_types": "Formats: {types}.",
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
        "status_checking": "Catalog available",
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
        "metric_relevant": "Relevant in index",
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
        "sort_priority": "Action priority",
        "sort_deadline": "Nearest deadline",
        "sort_updated": "Recently updated",
        "min_score_label": "Catalog relevance",
        "min_score_aria": "Minimum catalog relevance",
        "source_label": "Source",
        "source_aria": "Source",
        "all_scores": "All results",
        "score_option_03": "Baseline relevance",
        "score_option_05": "Good relevance",
        "score_option_07": "High relevance",
        "score_help": (
            "The estimate considers region and topic; ordering also uses deadline "
            "runway. It is not an award probability; verify the official source."
        ),
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
        "trust_library_summary": "Sources and transparency",
        "trust_library_description": (
            "Coverage, data freshness, active funders, and methodology."
        ),
        "source_refresh_title": "Latest successful source refresh",
        "source_refresh_value": "Updated {date}",
        "source_refresh_unknown": "Refresh date unavailable",
        "health_title": "Data status",
        "health_description": (
            "Shows whether the catalog is reachable and how many sources are "
            "currently active in the public feed."
        ),
        "health_ok_value": "Data is current",
        "health_attention_value": "Needs review",
        "health_note_loading": (
            "Catalog data is available. Confirming the latest refresh time."
        ),
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
        "health_stale_sources": "Stale sources",
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
        "summary_score": "Relevance: {value}",
        "summary_scope_all": "Including archive",
        "methodology_title": "How we collect and present data",
        "methodology_description": (
            "A short explanation of where the catalog comes from, what relevance "
            "means, and what you should still verify before applying."
        ),
        "method_card_sources_title": "Sources and refresh",
        "method_card_sources_text": (
            "The catalog combines official sources, open registers, and curated "
            "watch pages. We regularly recheck links, deadlines, and whether an "
            "item is still active."
        ),
        "method_card_relevance_title": "Why an item is shown",
        "method_card_relevance_text": (
            "Relevance considers region and topic; ordering also uses deadline "
            "runway. Components are bounded and explainable. This is not an award "
            "probability or legal classification."
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
        "role_guide_title": "How to use QAZ.FUND at work",
        "role_guide_description": (
            "Turn the same source data into a reproducible selection, an editorial "
            "brief, or a working note."
        ),
        "role_analyst_title": "For analysts",
        "role_analyst_text": (
            "Save filters as a link, compare structured fields, and export results to CSV."
        ),
        "role_journalist_title": "For journalists",
        "role_journalist_text": (
            "Copy the card brief and record the official source and verification date."
        ),
        "role_editor_title": "For editors",
        "role_editor_text": (
            "Separate confirmed fields from details that still need checking before publication."
        ),
        "role_lawyer_title": "For legal review",
        "role_lawyer_text": (
            "Check the current terms, applicant type, documents, deadline, and submission route."
        ),
        "role_official_title": "For public-sector teams",
        "role_official_text": (
            "Build a reproducible Kazakhstan selection and export a table and deadline calendar."
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
        "collections_label": "Working selections",
        "collections_aria": "Saved filters and tools for repeat work",
        "collections_empty": "Save the current filters to return to this result set later.",
        "save_view": "Save filters",
        "share_view": "Share results",
        "saved_view_saved": "Collection saved locally.",
        "saved_view_removed": "Collection removed.",
        "saved_view_shared": "Copied a link to the current collection.",
        "saved_view_default_name": "My collection",
        "saved_view_remove_aria": "Remove collection",
        "saved_view_status_label": "Saved collection status",
        "saved_view_share_prompt": "Copy the link to the current collection",
        "advanced_filters": "Advanced filters",
        "mobile_filters_summary": "Refine results",
        "mobile_app_navigation": "Main QAZ.FUND sections",
        "mobile_app_tagline": "Opportunity navigator",
        "mobile_catalog": "Catalogue",
        "mobile_sources": "Sources",
        "mobile_saved": "Saved",
        "mobile_filters": "Filters",
        "mobile_open_filters": "Open catalogue filters",
        "mobile_close_filters": "Close filters",
        "mobile_show_results": "Show results",
        "export_csv": "CSV table",
        "export_deadlines": "Deadlines to calendar",
        "saved_opportunity_saved": "Card saved locally.",
        "saved_opportunity_removed": "Card removed from local saved items.",
        "save_opportunity": "Save",
        "unsave_opportunity": "Remove",
        "workspace_filter": "Saved items",
        "workspace_filter_count": "Saved items: {count}",
        "workspace_filter_empty": "Save a relevant card first.",
        "workflow_label": "Work stage",
        "workflow_review": "Under review",
        "workflow_fit": "Good fit",
        "workflow_preparing": "Preparing application",
        "workflow_submitted": "Submitted",
        "workflow_result": "Result received",
        "workflow_updated": "Card stage updated.",
        "workspace_queue_title": "Next actions",
        "workspace_queue_aria": "Action queue for saved opportunities",
        "workspace_queue_local": "Stored only in this browser.",
        "workspace_queue_empty": "There are no active saved cards in the current catalogue.",
        "workspace_queue_more": "Still in progress: {count}",
        "workspace_action_review": "Check the criteria on the official source.",
        "workspace_action_fit": "Confirm eligibility and the deadline.",
        "workspace_action_preparing": "Assemble the package and record the deadline.",
        "workspace_action_submitted": "Keep the confirmation and monitor the terms.",
        "workspace_action_result": "Record the outcome for this opportunity.",
        "workspace_deadline_today": "Due today",
        "workspace_deadline_days": "Due in {count} days",
        "workspace_deadline_date": "Due: {date}",
        "workspace_deadline_rolling": "Rolling application",
        "workspace_backup": "Export",
        "workspace_backup_aria": "Export data and back up local work",
        "workspace_export": "Workspace backup",
        "workspace_import": "Restore backup",
        "workspace_exported": "Workspace backup downloaded.",
        "workspace_imported": "Workspace restored.",
        "workspace_import_error": "The workspace backup could not be read.",
        "report_issue": "Correct the data",
        "open_source_short": "Official source",
        "footer_owner": "QAZ.FUND is a public opportunity navigator. Built by",
        "footer_disclaimer": (
            "QAZ.FUND does not award grants or process applications. Always verify "
            "final terms, deadlines, and forms on the official source."
        ),
        "footer_support": "Feedback",
        "footer_qdev": "qdev.run",
        "view_funder": "Funder profile",
        "fit_label": "Who it fits",
        "fit_unknown": "Check eligibility",
        "fit_deadline_soon": "Closing soon",
        "fit_global": "Global application",
        "signal_label": "Why this is worth a look",
        "card_meta_label": "Key details",
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
        "meta_deadline_later": "More than a month",
        "detail_fit_title": "Quick fit check",
        "detail_source_status_title": "Source status",
        "detail_fit_good": "Likely a fit",
        "detail_fit_review": "Manual eligibility review needed",
        "no_indexed_items": "The catalog currently has no available items.",
        "no_filtered_items": "No opportunities match the selected filters.",
        "no_filtered_items_hint": (
            "Try relaxing one of the filters and the catalog will recalculate right away."
        ),
        "empty_action_clear": "Clear all",
        "empty_action_region": "All regions",
        "empty_action_deadline": "Any timing",
        "empty_action_score": "Standard threshold",
        "empty_action_scope": "Open full index",
        "open_details": "Quick view",
        "read_more": "Full card",
        "open_rolling": "Open / Rolling",
        "score_title": "Explainable catalog relevance; not an award probability",
        "score_exact": "High",
        "score_high": "Good",
        "score_base": "Baseline",
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
        "detail_readiness_title": "Data completeness",
        "detail_readiness_complete": "All {total} key fields are confirmed.",
        "detail_readiness_partial": (
            "{known} of {total} fields confirmed. Verify at source: {missing}."
        ),
        "detail_copy_brief": "Copy working brief",
        "detail_copy_brief_done": "Working brief copied.",
        "detail_copy_brief_prompt": "Copy the working brief",
        "detail_brief_heading": "QAZ.FUND – working brief",
        "detail_brief_summary": "Summary",
        "detail_brief_source": "Organizer or source",
        "detail_brief_format": "Format",
        "detail_brief_region": "Region",
        "detail_brief_deadline": "Deadline",
        "detail_brief_amount": "Amount",
        "detail_brief_official_url": "Official source",
        "detail_brief_application_url": "Application",
        "detail_brief_caveat": (
            "Verify at the official source: current terms, eligibility, required "
            "documents, deadline, and submission route."
        ),
        "verification_eyebrow": "Verification and handoff",
        "verification_title": "Before using this card",
        "verification_description": (
            "The card supports initial analysis and working briefs, but does not "
            "confirm eligibility or replace the official terms."
        ),
        "verification_eligibility_title": "Eligibility",
        "verification_eligibility_text": (
            "Confirm applicant type, jurisdiction, restrictions, and required experience."
        ),
        "verification_terms_title": "Current terms",
        "verification_terms_text": (
            "Check the latest version, deadline, amount, and submission route."
        ),
        "verification_procurement_title": "Procurement documents",
        "verification_procurement_text": (
            "For tenders, check lots, qualifications, attachments, and amendments separately."
        ),
        "verification_publication_title": "Publication and internal notes",
        "verification_publication_text": (
            "Record the official source and the date when the information was verified."
        ),
        "detail_missing_labels": {
            "deadline": "deadline",
            "amount": "amount",
            "eligibility": "applicant eligibility",
            "application": "application route",
        },
        "detail_sections_title": "Text and excerpts",
        "detail_status_ok": "Description and key fields were collected from the official source",
        "detail_status_structured_only": "Showing the stored summary and structured fields",
        "detail_status_blocked": "The source blocked automatic full-text retrieval",
        "detail_status_not_allowed": "Local fetch is disabled for this source",
        "detail_status_too_large": "The source page is too large for the local reader",
        "detail_status_unsupported_media": "The source returned an unsupported format",
        "detail_status_parse_error": "The source page could not be parsed cleanly",
        "detail_source_excerpt": "Source excerpt",
        "detail_expand_source": "Show excerpt",
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
            "world_bank_procurement_ca": "World Bank Central Asia Procurement",
            "eu_funding_tenders_ca": "EU Funding & Tenders Central Asia",
            "canada_cfli_ca": "Canada Fund for Local Initiatives",
            "adb_kazakhstan": "ADB Kazakhstan",
            "eeas_kazakhstan": "EEAS Kazakhstan",
            "unicef_kazakhstan": "UNICEF Kazakhstan",
            "unesco_iite": "UNESCO IITE",
            "isdb_project_procurement": "IsDB Procurement",
            "islamic_development_bank": "Islamic Development Bank",
            "ebrd_ecepp_procurement": "EBRD ECEPP Procurement",
            "undp_procurement": "UNDP Procurement",
            "kazakhstan": "Kazakhstan",
            "central_asia": "Central Asia",
            "eligibility_check_required": "Eligibility check required",
            "canada": "Canada",
            "turkmenistan": "Turkmenistan",
            "global": "Global",
            "kz": "Kazakhstan",
            "program": "Program",
            "education_organisation": "Education organizations",
            "agriculture": "Agriculture",
            "assessment": "Assessment",
            "astana_hub": "Astana Hub",
            "azure": "Azure",
            "capacity_building": "Capacity building",
            "children": "Children",
            "civic": "Civic initiatives",
            "cloud_credits": "Cloud credits",
            "cloudflare": "Cloudflare",
            "consultancy": "Consultancy",
            "consulting": "Consulting",
            "creative_industries": "Creative industries",
            "culture": "Culture",
            "database": "Databases",
            "developer_tools": "Developer tools",
            "development": "Development",
            "digital": "Digital solutions",
            "digital_skills": "Digital skills",
            "donor": "Donor programs",
            "ebrd": "EBRD",
            "ecepp": "ECEPP",
            "education": "Education",
            "energy": "Energy",
            "environment": "Environment",
            "erasmus": "Erasmus+",
            "erasmus_mundus": "Erasmus Mundus",
            "eu": "EU",
            "eu_studies": "EU studies",
            "evaluation": "Evaluation",
            "federal": "Federal programs",
            "finance": "Finance",
            "firebase": "Firebase",
            "google": "Google",
            "governance": "Governance",
            "gpu": "GPU",
            "health": "Health",
            "higher_education": "Higher education",
            "human_rights": "Human rights",
            "infrastructure": "Infrastructure",
            "isdb": "IsDB",
            "it": "IT",
            "jean_monnet": "Jean Monnet",
            "joint_degrees": "Joint degrees",
            "kyrgyz": "Kyrgyzstan",
            "kyrgyzstan": "Kyrgyzstan",
            "mobility": "Academic mobility",
            "nonprofit_required": "Nonprofits only",
            "opportunity_desk": "Opportunity Desk",
            "partnership": "Partnership",
            "policy": "Public policy",
            "procurement": "Procurement",
            "project_pipeline": "Project pipeline",
            "public_diplomacy": "Public diplomacy",
            "public_sector": "Public sector",
            "regional_development": "Regional development",
            "research": "Research",
            "security": "Security",
            "serverless": "Serverless",
            "sez": "Special economic zones",
            "social_entrepreneurship": "Social entrepreneurship",
            "startup_support": "Startup support",
            "student_exchange": "Student exchange",
            "tajikistan": "Tajikistan",
            "teacher_training": "Teacher training",
            "technology": "Technology",
            "transport": "Transport",
            "undp": "UNDP",
            "us": "US",
            "uzbekistan": "Uzbekistan",
            "watchlist": "Watchlist",
            "water": "Water",
            "world_bank": "World Bank",
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
            "invitation_for_tenders_single": "Invitation for tenders",
            "kazakhstan_domestic_support": "KZ domestic support",
            "kazakhstan_opportunity_watch": "Kazakhstan opportunity watch",
            "dod_amraa": "DOD-AMRAA",
            "hhs_nih11": "HHS-NIH",
            "united_nations_development_programme": (
                "United Nations Development Programme (UNDP)"
            ),
            "european_bank_for_reconstruction_and_development": (
                "European Bank for Reconstruction and Development (EBRD)"
            ),
        },
    },
}


def _copy_for(lang: str) -> dict[str, object]:
    return cast(dict[str, object], COPY["en" if lang == "en" else "ru"])


def dashboard_copy(lang: str) -> dict[str, object]:
    return _copy_for(lang if lang in SUPPORTED_LANGS else "ru")
