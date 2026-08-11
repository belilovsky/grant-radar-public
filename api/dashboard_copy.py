"""Localized public-dashboard copy kept separate from rendering logic."""

from __future__ import annotations

from typing import cast

SUPPORTED_LANGS = {"kk", "ru", "en"}

COPY = {
    "ru": {
        "lang": "ru",
        "locale": "ru-KZ",
        "title": "QAZ.FUND – открытые программы поддержки для Казахстана",
        "meta_description": (
            "Гранты, субсидии, акселераторы, тендеры и другие программы поддержки "
            "для Казахстана. Найдите подходящий маршрут, проверьте условия и "
            "перейдите к источнику."
        ),
        "eyebrow": "Рабочий навигатор поддержки в Казахстане",
        "headline": "QAZ.FUND",
        "subtitle": (
            "Находим открытые программы и помогаем превратить их в понятный "
            "следующий шаг."
        ),
        "hero_intro": (
            "Гранты, субсидии, акселераторы и закупки – с источником, статусом "
            "данных и сроками."
        ),
        "hero_primary_cta": "Найти поддержку",
        "hero_stage_eyebrow": "В три шага",
        "hero_stage_title": "С чего начать?",
        "hero_stage_point_one": "Сузьте поле по задаче, типу заявителя и теме.",
        "hero_stage_point_two": "Откройте карточку и сверяйте условия на странице источника.",
        "hero_stage_point_three": "Сохраните маршрут, поделитесь им или выгрузите сроки.",
        "hero_picks_label": "Быстрый выбор",
        "hero_pick_startup": "Найти поддержку",
        "hero_pick_business": "Проверить программу",
        "hero_pick_farmer": "Сроки до месяца",
        "hero_pick_science": "Господдержка РК",
        "hero_pick_tenders": "Тендеры и закупки",
        "spotlight_section_eyebrow": "Начните с задачи",
        "spotlight_section_title": "Что можно проверить сейчас",
        "spotlight_section_description": (
            "Подходящие карточки, местные меры поддержки и ближайшие сроки – в "
            "одном рабочем срезе."
        ),
        "spotlight_count": "Карточек: {count}",
        "spotlight_action_open": "Открыть список",
        "spotlight_empty": "В списке пока нет открытых карточек.",
        "catalog_empty": "Каталог временно не содержит доступных карточек.",
        "spotlight_preview_more": "+ ещё {count}",
        "spotlight_trending_kicker": "Сильные сигналы",
        "spotlight_trending_title": "Что проверить первым",
        "spotlight_trending_note": (
            "Карточки с сильными сигналами и открытым статусом."
        ),
        "spotlight_kazakhstan_kicker": "Казахстан",
        "spotlight_kazakhstan_title": "Возможности для Казахстана",
        "spotlight_kazakhstan_note": (
            "Программы с условиями для заявителей из Казахстана."
        ),
        "spotlight_support_kicker": "Субсидии и меры",
        "spotlight_support_title": "Поддержка для бизнеса",
        "spotlight_support_note": (
            "Субсидии, льготы и другие меры с понятными условиями подачи."
        ),
        "spotlight_deadline_kicker": "Ближайшие сроки",
        "spotlight_deadline_title": "Что закрывается первым",
        "spotlight_deadline_note": (
            "Откройте карточки заранее и проверьте требования."
        ),
        "pathways_section_eyebrow": "По задаче",
        "pathways_section_title": "По типу заявителя",
        "pathways_section_description": (
            "Начните с типа заявителя, чтобы быстрее найти свой маршрут."
        ),
        "pathways_count": "Карточек: {count}",
        "pathways_action_open": "Открыть список",
        "pathways_empty": "Для этого типа заявителя пока нет открытых карточек.",
        "pathway_startup_kicker": "Стартапам",
        "pathway_startup_title": "Акселераторы, гранты и облачные кредиты",
        "pathway_startup_note": (
            "Для продуктовых и технологических команд, которым нужны пилоты, кредиты "
            "или акселерация."
        ),
        "pathway_business_kicker": "Бизнесу",
        "pathway_business_title": "Субсидии, льготы и меры поддержки РК",
        "pathway_business_note": (
            "Для ИП, ТОО и компаний, которым важны местные условия и порядок подачи."
        ),
        "pathway_farmer_kicker": "Фермерам",
        "pathway_farmer_title": "Агро, животноводство и прикладные технологии",
        "pathway_farmer_note": (
            "Для хозяйств и агрокоманд с задачами в агро, животноводстве и технологиях."
        ),
        "pathway_science_kicker": "Исследователям",
        "pathway_science_title": "Наука, коммерциализация и научные гранты",
        "pathway_science_note": (
            "Для университетов, лабораторий и команд, которым нужно финансирование "
            "исследований и внедрения."
        ),
        "themes_section_eyebrow": "По теме",
        "themes_section_title": "По направлению",
        "themes_section_description": (
            "Выберите направление, чтобы убрать лишний шум и увидеть относящиеся "
            "к задаче карточки."
        ),
        "discovery_library_summary": "Готовые маршруты",
        "discovery_library_description": (
            "Подборки для первого поиска, проверки сроков и повторной работы."
        ),
        "themes_count": "Карточек: {count}",
        "themes_action_open": "Открыть список",
        "themes_empty": "По этой теме пока нет открытых карточек.",
        "funder_section_eyebrow": "Фонды и доноры",
        "funder_section_title": "Активные фонды и программы",
        "funder_section_description": (
            "Фонды и программы, их направления и открытые возможности."
        ),
        "funder_open_profile": "Открыть профиль",
        "funder_empty": "Профили фондов пока не найдены.",
        "funder_live_now": "Открытые возможности",
        "funder_total_items": "Всего в индексе",
        "funder_next_deadline": "Ближайший срок",
        "funder_overview_intro": (
            "Сведения собраны по опубликованным программам и объявлениям."
        ),
        "funder_overview_types": "Форматы: {types}.",
        "funder_overview_topics": "Основные темы: {topics}.",
        "funder_overview_regions": "Регионы: {regions}.",
        "funder_page_eyebrow": "Организация и её программы",
        "funder_focus_title": "Что видно по текущему индексу",
        "funder_focus_note": "Форматы, регионы и темы по текущему индексу.",
        "funder_focus_types": "Форматы",
        "funder_focus_regions": "Регионы",
        "funder_focus_indexed": "В индексе",
        "funder_live_title": "Открытые возможности",
        "funder_live_note": "Открытые, бессрочные и планируемые записи для проверки.",
        "funder_live_empty": "У этого фонда нет открытых или планируемых записей.",
        "funder_archive_title": "Архив",
        "funder_archive_note": (
            "Закрытые записи показывают профиль фонда и сроки его программ."
        ),
        "funder_archive_empty": "Архивных записей нет.",
        "funder_sources_title": "Источники профиля",
        "funder_sources_note": "Официальные страницы, использованные для профиля.",
        "funder_back_to_catalog": "Вернуться в каталог",
        "funder_open_card": "Открыть карточку",
        "topic_brief_eyebrow": "Текущая подборка",
        "topic_brief_count": "В подборке: {count}",
        "topic_brief_what": "Что здесь обычно ищут",
        "topic_brief_best_for": "Кому может быть полезно",
        "topic_brief_reset": "Убрать тему",
        "topic_ai_best": (
            "Продуктовым командам, командам по искусственному интеллекту и "
            "цифровым инициативам."
        ),
        "topic_ai_focus_1": "Программы для искусственного интеллекта и акселераторы",
        "topic_ai_focus_2": "Облачные кредиты и инфраструктура",
        "topic_ai_focus_3": "Цифровые навыки и прикладные программы",
        "topic_agro_best": "Фермерам, агрономам и проектам на стыке воды, климата и отраслей.",
        "topic_agro_focus_1": "Субсидии и отраслевые меры",
        "topic_agro_focus_2": "Вода, климат и устойчивость",
        "topic_agro_focus_3": "Животноводство, ветеринария и прикладные агротехнологии",
        "topic_science_best": "Университетам, лабораториям и исследовательским командам.",
        "topic_science_focus_1": "Коммерциализация исследований",
        "topic_science_focus_2": "Научные гранты, лаборатории и академическая мобильность",
        "topic_science_focus_3": "Образовательные и университетские программы",
        "topic_public_best": "Командам, работающим с госсектором, закупками и инфраструктурой.",
        "topic_public_focus_1": "Закупки, тендеры и запросы предложений",
        "topic_public_focus_2": "Программы развития и реализация",
        "topic_public_focus_3": "Цифровые решения для госсектора и крупные проекты",
        "topic_business_best": "ИП, ТОО и действующему бизнесу в Казахстане.",
        "topic_business_focus_1": "Локальные субсидии и меры РК",
        "topic_business_focus_2": "Льготы, гарантии и финансирование",
        "topic_business_focus_3": "Поддержка для МСБ, экспорта и роста",
        "topic_ngo_best": "НКО, СМИ и гражданским командам с социальным эффектом.",
        "topic_ngo_focus_1": "СМИ, журналистика и общественно значимые проекты",
        "topic_ngo_focus_2": "Гранты для гражданского сектора и партнёрства",
        "topic_ngo_focus_3": "Сообщество и программы с социальным эффектом",
        "theme_ai_kicker": "Искусственный интеллект и цифровые решения",
        "theme_ai_title": "Искусственный интеллект, облачные кредиты и цифровые навыки",
        "theme_ai_note": (
            "Для команд, которые ищут программы по искусственному интеллекту, "
            "инфраструктуру, кредиты и "
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
            "нужны гранты и исследовательские программы."
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
            "Для МСБ и действующих компаний, где важны местные условия и "
            "правила подачи."
        ),
        "theme_ngo_kicker": "СМИ и НКО",
        "theme_ngo_title": "СМИ, гражданский сектор и социальный эффект",
        "theme_ngo_note": (
            "Для НКО, СМИ и общественных проектов, которым нужны гранты и "
            "партнёрские программы."
        ),
        "focus_aria": "Текущий продуктовый фокус",
        "focus_primary": "Приоритет: Казахстан и Центральная Азия",
        "focus_secondary": (
            "Темы: искусственный интеллект, образование, госсектор, агро, "
            "ветеринария, экология, медиа"
        ),
        "status_checking": "Каталог доступен",
        "api_docs": "API",
        "media_link": "Медиа",
        "insights_link": "Аналитика",
        "terms_link": "Условия",
        "data_policy_link": "Политика данных",
        "attribution_link": "Использование данных",
        "readiness_title": "Что уже видно из карточки",
        "readiness_note": "Четыре поля для проверки перед подачей.",
        "readiness_source": "Источник",
        "readiness_deadline": "Срок",
        "readiness_amount": "Сумма",
        "readiness_eligibility": "Критерии",
        "methodology_link": "Как это работает",
        "status_link": "Статус данных",
        "language_switch": "Язык интерфейса",
        "nav_aria": "Разделы каталога",
        "tab_opportunities": "Программы",
        "tab_sources": "Источники",
        "tab_health": "Статус",
        "metrics_aria": "Показатели каталога",
        "metric_total": "Всего программ",
        "metric_relevant": "В текущем каталоге",
        "metric_sources": "Источников отслеживается",
        "opportunities_title": "Каталог программ",
        "opportunities_description": (
            "Открытые и бессрочные программы с приоритетом для Казахстана и "
            "Центральной Азии."
        ),
        "opportunities_description_all": (
            "Открытые, бессрочные и архивные записи для проверки покрытия и источников."
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
        "topic_ngo": "СМИ и НКО",
        "topic_business": "Бизнес и субсидии",
        "scope_label": "Покрытие",
        "scope_aria": "Покрытие списка",
        "scope_open": "Открытые",
        "scope_all": "Весь индекс",
        "lifecycle_label": "Стадия",
        "lifecycle_aria": "Состояние программы",
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
        "sort_aria": "Порядок показа программ",
        "sort_priority": "По приоритету проверки",
        "sort_deadline": "Ближайший срок",
        "sort_updated": "Недавно обновлённые",
        "min_score_label": "Соответствие запросу",
        "min_score_aria": "Минимальное соответствие запросу",
        "source_label": "Источник",
        "source_aria": "Источник",
        "all_scores": "Все результаты",
        "score_option_03": "Базовая релевантность",
        "score_option_05": "Хорошая релевантность",
        "score_option_07": "Высокая релевантность",
        "score_help": (
            "Регион и тема влияют на релевантность, срок – на порядок показа. "
            "Это не вероятность одобрения; условия смотрите у источника."
        ),
        "all_sources": "Все источники",
        "clear_filters": "Сбросить фильтры",
        "loading_opportunities": "Загрузка возможностей",
        "load_more": "Показать ещё",
        "sources_title": "Покрытие источников",
        "sources_description": (
            "Официальные источники и страницы мониторинга, подключённые к каталогу."
        ),
        "loading_sources": "Загрузка источников",
        "show_all_sources": "Показать все источники",
        "show_fewer_sources": "Показать меньше",
        "trust_library_summary": "Источники и прозрачность",
        "trust_library_description": "Покрытие, свежесть данных, фонды и методика.",
        "funder_library_summary": "Профили фондов",
        "funder_library_description": (
            "Кто публикует программы и где есть открытые возможности."
        ),
        "methodology_library_summary": "Проверка данных и методика",
        "methodology_library_description": (
            "Статус источников, отбор и правила проверки."
        ),
        "source_refresh_title": "Последнее успешное обновление источника",
        "source_refresh_value": "Обновлено {date}",
        "source_refresh_unknown": "Дата обновления не указана",
        "health_title": "Статус данных",
        "health_description": (
            "Показываем доступность каталога и число активных источников."
        ),
        "health_ok_value": "Данные актуальны",
        "health_attention_value": "Проверить",
        "health_note_loading": (
            "Данные каталога доступны. Уточняем время последнего обновления."
        ),
        "health_note_ready": (
            "Источники проверены {checked_at}. Последнее изменение карточек: {updated_at}."
        ),
        "health_note_ready_no_items": (
            "Витрина проверена {checked_at}. Новые карточки появятся после следующего "
            "обхода источников."
        ),
        "reload_live_data": "Обновить данные",
        "api_status": "Состояние каталога",
        "stored_items": "Записей в каталоге",
        "health_sources": "Активные источники",
        "health_stale_sources": "Устаревшие источники",
        "api_online": "Каталог доступен",
        "api_failed": "Нужна проверка данных",
        "api_error": "Ошибка загрузки данных",
        "source_catalog_unavailable": "Каталог источников временно недоступен.",
        "showing_sources": "Показываем {shown} из {total} источников",
        "sources_connected": "Подключено источников: {total}",
        "show_all_sources_with_total": "Показать все {total} источников",
        "coverage_unavailable": "Покрытие недоступно",
        "indexed_count": "В индексе: {count}",
        "relevant_open_count": "Открытых по запросу: {count}",
        "direct_badge": "Прямое подключение",
        "watchlist_badge": "Мониторинг",
        "source_direct_note": "Прямое подключение к официальному источнику",
        "source_watchlist_note": "Страница мониторинга с редакционной проверкой",
        "regional_badge_kazakhstan": "Казахстан",
        "regional_badge_central_asia": "Центральная Азия",
        "summary_matches": "Найдено: {count}",
        "summary_search": "Поиск: {value}",
        "summary_audience": "Для кого: {value}",
        "summary_format": "Формат: {value}",
        "summary_topic": "Тема: {value}",
        "summary_lifecycle": "Стадия: {value}",
        "summary_region": "Регион: {value}",
        "summary_deadline": "Срок: {value}",
        "summary_sort": "Сортировка: {value}",
        "summary_score": "Соответствие: {value}",
        "summary_scope_all": "Включая архив",
        "methodology_title": "Как мы работаем",
        "methodology_description": (
            "Карточка ведёт к источнику, показывает границы данных и оставляет "
            "решение человеку."
        ),
        "method_card_sources_title": "Источники и обновление",
        "method_card_sources_text": (
            "Собираем официальные источники, открытые реестры и страницы "
            "мониторинга. Рядом показываем ссылку и статус данных."
        ),
        "method_card_relevance_title": "Почему карточка здесь",
        "method_card_relevance_text": (
            "Тема, регион, тип заявителя и срок влияют на порядок показа. Это "
            "рабочая сортировка, а не обещание одобрения."
        ),
        "method_card_trust_title": "Источник важнее карточки",
        "method_card_trust_text": (
            "Карточка помогает сориентироваться. Действующие условия, формы и "
            "требования проверяйте на странице программы."
        ),
        "method_disclaimer_title": "Решение остаётся за вами",
        "method_disclaimer_text": (
            "QAZ.FUND не выдаёт средства и не принимает заявки. Перед действием "
            "проверьте на источнике срок, критерии, документы и способ подачи."
        ),
        "role_guide_title": "Для работы, а не для бесконечного поиска",
        "role_guide_description": (
            "Если карточки используются для редакции, аналитики или проверки, "
            "перенесите рабочий процесс в операторский раздел."
        ),
        "role_guide_link_label": "Открыть операторский раздел",
        "role_analyst_title": "Аналитику",
        "role_analyst_text": (
            "Зафиксируйте фильтры ссылкой, сравните поля и выгрузите результаты в CSV."
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
        "role_official_title": "Руководителю госоргана",
        "role_official_text": (
            "Соберите воспроизводимую подборку по РК, выгрузите таблицу и "
            "календарь сроков."
        ),
        "faq_title": "Частые вопросы",
        "faq_q1": "QAZ.FUND сам выдает гранты?",
        "faq_a1": (
            "Нет. QAZ.FUND собирает и упорядочивает открытые возможности; заявку "
            "подают организатору."
        ),
        "faq_q2": "Как часто обновляются данные?",
        "faq_a2": (
            "Источники и индекс регулярно перепроверяются. Текущее состояние видно "
            "в блоке «Статус данных»."
        ),
        "faq_q3": "Что означает точность совпадения?",
        "faq_a3": (
            "Это не оценка программы. Порог показывает, насколько карточка совпадает "
            "с выбранными темой, регионом и форматом."
        ),
        "faq_q4": "Почему в выдаче бывают меры поддержки рядом с грантами?",
        "faq_a4": (
            "Некоторые меры поддержки не являются грантами, но подходят той же "
            "аудитории. Мы оставляем их при совпадении с задачей."
        ),
        "collections_label": "Сохранённые подборки",
        "collections_aria": "Сохранённые фильтры для повторной работы",
        "collections_empty": "Сохраните фильтры, чтобы вернуться к этому списку.",
        "profile_title": "Собрать подборку по профилю",
        "profile_intro": (
            "Укажите тип заявителя, географию, формат поддержки и срок – каталог "
            "соберёт воспроизводимую подборку."
        ),
        "profile_audience": "Кто подаёт",
        "profile_region": "Где проект",
        "profile_format": "Что нужно",
        "profile_deadline": "Когда подаёте",
        "profile_apply": "Показать подборку по профилю",
        "profile_reset": "Очистить профиль",
        "profile_local_note": (
            "Профиль не отправляется на сервер. Выбранные параметры сохраняются "
            "в ссылке и их можно переслать."
        ),
        "profile_applied": "Подборка по профилю обновлена.",
        "save_view": "Сохранить фильтры",
        "share_view": "Поделиться выдачей",
        "saved_view_saved": "Подборка сохранена в этом браузере.",
        "saved_view_removed": "Подборка удалена.",
        "saved_view_shared": "Ссылка на текущую подборку скопирована.",
        "saved_view_default_name": "Моя подборка",
        "saved_view_remove_aria": "Удалить подборку",
        "saved_view_status_label": "Статус подборок",
        "saved_view_share_prompt": "Скопируйте ссылку на эту подборку",
        "advanced_filters": "Дополнительные фильтры",
        "mobile_filters_summary": "Настроить выдачу",
        "mobile_app_navigation": "Основные разделы QAZ.FUND",
        "mobile_app_tagline": "Навигатор поддержки",
        "mobile_catalog": "Каталог",
        "mobile_sources": "Источники",
        "mobile_saved": "Сохранённое",
        "mobile_filters": "Фильтры",
        "mobile_open_filters": "Открыть фильтры каталога",
        "mobile_close_filters": "Закрыть фильтры",
        "mobile_show_results": "Показать результаты",
        "export_csv": "Таблица CSV",
        "export_deadlines": "Сроки в календарь",
        "saved_opportunity_saved": "Карточка сохранена в этом браузере.",
        "saved_opportunity_removed": "Карточка удалена из сохранённых.",
        "save_opportunity": "Сохранить",
        "unsave_opportunity": "Убрать",
        "workspace_filter": "Сохранённые карточки",
        "workspace_filter_count": "Сохранённые карточки: {count}",
        "workspace_filter_empty": "Сначала сохраните карточку.",
        "workflow_label": "Этап работы",
        "workflow_review": "На проверке",
        "workflow_fit": "Подходит",
        "workflow_preparing": "Готовим заявку",
        "workflow_submitted": "Отправлено",
        "workflow_result": "Получен результат",
        "workflow_updated": "Этап карточки обновлён.",
        "workspace_queue_title": "Следующие шаги",
        "workspace_queue_aria": "Следующие шаги для сохранённых карточек",
        "workspace_queue_local": "Данные хранятся в этом браузере.",
        "workspace_queue_empty": "Нет сохранённых открытых карточек.",
        "workspace_queue_more": "Ещё карточек: {count}",
        "workspace_action_review": "Проверьте критерии на официальном источнике.",
        "workspace_action_fit": "Подтвердите соответствие требованиям и срок.",
        "workspace_action_preparing": "Соберите пакет и зафиксируйте срок подачи.",
        "workspace_action_submitted": "Сохраните подтверждение и следите за условиями.",
        "workspace_action_result": "Зафиксируйте результат по этой программе.",
        "workspace_deadline_today": "Срок сегодня",
        "workspace_deadline_days": "Срок через {count} дн.",
        "workspace_deadline_date": "Срок: {date}",
        "workspace_deadline_rolling": "Постоянный приём",
        "workspace_backup": "Выгрузить",
        "workspace_backup_aria": "Выгрузка данных и резервная копия локальной работы",
        "workspace_export": "Резервная копия",
        "workspace_import": "Восстановить копию",
        "workspace_exported": "Резервная копия скачана.",
        "workspace_imported": "Сохранённые данные восстановлены.",
        "workspace_import_error": "Не удалось прочитать резервную копию.",
        "report_issue": "Уточнить данные",
        "open_source_short": "Перейти к источнику",
        "footer_owner": "QAZ.FUND – открытый навигатор возможностей. Сделано",
        "footer_disclaimer": (
            "QAZ.FUND не выдаёт средства и не принимает заявки. Финальные условия "
            "всегда проверяйте на странице источника."
        ),
        "footer_support": "Обратная связь",
        "footer_qdev": "qdev.run",
        "footer_terms": "Условия",
        "footer_data_policy": "Политика данных",
        "footer_attribution": "Использование данных",
        "view_funder": "Профиль фонда",
        "fit_label": "Признаки совпадения",
        "fit_unknown": "Критерии нужно проверить",
        "fit_deadline_soon": "Скоро закрывается",
        "fit_global": "Глобальная подача",
        "signal_label": "Почему показана",
        "card_meta_label": "Параметры",
        "signal_support_kz": (
            "Мера поддержки для команд и бизнеса в Казахстане с понятным порядком "
            "подачи."
        ),
        "signal_public_sector": (
            "Для команд, работающих с госсектором, инфраструктурой и программами "
            "развития."
        ),
        "signal_business": (
            "Подходит бизнесу, если важны условия, документы и порядок подачи."
        ),
        "signal_startup": (
            "Для продуктовых и ИИ-команд, которым нужны акселерация, пилоты или "
            "облачные кредиты."
        ),
        "signal_tender": (
            "Проверьте требования к участнику, объём работ и пакет заявки."
        ),
        "signal_science": "Для университетов, лабораторий и научных команд.",
        "signal_farmer": ("Для хозяйств, ферм и аграрных компаний."),
        "signal_ngo": ("Для НКО, СМИ и общественных организаций."),
        "signal_kazakhstan": (
            "В условиях прямо указан Казахстан или местный порядок подачи."
        ),
        "signal_central_asia": (
            "Подходит проектам из Центральной Азии без узкой привязки к одной стране."
        ),
        "signal_global": (
            "Международная возможность – проверьте критерии для своей команды."
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
        "detail_fit_title": "Что проверить",
        "detail_source_status_title": "Статус источника",
        "detail_fit_good": "Есть признаки совпадения",
        "detail_fit_review": "Проверьте критерии вручную",
        "detail_meta_title": "Главное",
        "detail_readiness_title": "Полнота данных",
        "no_indexed_items": "В каталоге пока нет доступных карточек.",
        "no_filtered_items": "По текущим фильтрам ничего не найдено.",
        "no_filtered_items_hint": "Снимите один фильтр и попробуйте снова.",
        "empty_action_clear": "Сбросить всё",
        "empty_action_region": "Все регионы",
        "empty_action_deadline": "Любые сроки",
        "empty_action_score": "Базовый порог",
        "empty_action_scope": "Открыть весь каталог",
        "open_details": "Краткий просмотр",
        "read_more": "Полная карточка",
        "open_rolling": "Открыто / бессрочно",
        "score_title": "Релевантность по правилам каталога; это не вероятность одобрения",
        "score_exact": "Высокая",
        "score_high": "Хорошая",
        "score_base": "Базовая",
        "source_agency": "Источник: {agency}",
        "no_summary": "Источник не передал описание.",
        "reload_confirm": "Перезагрузить данные из всех источников?",
        "results_button": "Показать ещё {count}",
        "unknown_url": "URL недоступен",
        "views_aria": "Навигация по разделам панели",
        "breadcrumbs_aria": "Навигационная цепочка",
        "detail_panel_label": "Подробности возможности",
        "detail_shell_title": "Подробности",
        "detail_title_fallback": "Карточка возможности",
        "detail_loading": "Загрузка описания и параметров",
        "detail_error": "Локальное описание недоступно. Откройте источник ниже.",
        "detail_empty": "Доступны краткое описание и ключевые условия.",
        "detail_close": "Закрыть",
        "detail_open_page": "Открыть страницу",
        "detail_all_opportunities": "Все программы",
        "detail_open_source": "Открыть источник",
        "detail_open_application": "Открыть подачу",
        "detail_prepare_application": "Подготовить заявку",
        "detail_closed_notice": (
            "Приём завершён. Карточка сохранена для справки; новый набор "
            "проверяйте у организатора."
        ),
        "detail_forecast_notice": (
            "Приём ещё не открыт. Условия и сроки могут измениться до начала набора."
        ),
        "detail_compute_readiness": (
            "Оценка полноты данных: {score} / 100, {tier}. Это вспомогательный "
            "показатель, а не решение о праве на участие."
        ),
        "detail_compute_ready": "данных достаточно",
        "detail_compute_watch": "нужна сверка",
        "detail_compute_blocked": "есть блокеры",
        "detail_compute_unknown": "статус неизвестен",
        "detail_copy_brief": "Скопировать сведения",
        "detail_copy_brief_done": "Рабочая справка скопирована.",
        "detail_copy_brief_prompt": "Скопируйте рабочую справку",
        "detail_share": "Поделиться карточкой",
        "detail_share_done": "Карточка готова к отправке.",
        "detail_share_prompt": "Скопируйте ссылку на карточку",
        "detail_brief_heading": "QAZ.FUND – сведения о программе",
        "detail_brief_legacy_heading": "QAZ.FUND – рабочая справка",
        "detail_brief_summary": "Кратко",
        "detail_brief_source": "Организатор или источник",
        "detail_brief_format": "Формат",
        "detail_brief_region": "Регион",
        "detail_brief_deadline": "Срок",
        "detail_brief_amount": "Сумма",
        "detail_brief_official_url": "Официальный источник",
        "detail_brief_application_url": "Подача",
        "detail_brief_caveat": (
            "Проверьте на официальном источнике условия, право на участие, документы, "
            "срок и способ подачи."
        ),
        "verification_eyebrow": "Проверка",
        "verification_title": "Перед подачей",
        "verification_description": (
            "Карточка помогает начать проверку, но не подтверждает право на участие "
            "и не заменяет официальные условия."
        ),
        "decision_check_eyebrow": "Перед подачей",
        "decision_check_title": "Ключевые условия",
        "decision_check_description": (
            "Сначала проверьте четыре пункта на странице организатора."
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
        "decision_check_known_title": "Что известно",
        "decision_check_known_source": "источник: {source}",
        "decision_check_known_format": "формат: {format}",
        "decision_check_known_deadline": "срок: {deadline}",
        "decision_check_known_amount": "объём поддержки: {amount}",
        "decision_check_known_eligibility": "требования: {eligibility}",
        "decision_check_known_empty": "Пока известны только источник и описание.",
        "decision_check_missing_title": "Что уточнить",
        "decision_check_missing_text": "На официальной странице проверьте: {items}.",
        "decision_check_missing_none": (
            "Основные поля заполнены. Проверьте актуальную редакцию условий."
        ),
        "decision_check_route_title": "Куда подавать",
        "decision_check_route_application": (
            "Используйте отдельную форму подачи и сверяйте требования "
            "с первоисточником."
        ),
        "decision_check_route_source": (
            "Отдельная форма не указана. Подавайте заявку только через "
            "страницу организатора."
        ),
        "decision_check_boundary_title": "Важно",
        "decision_check_boundary_text": (
            "Карточка помогает с отбором; решение принимают по правилам организатора."
        ),
        "verification_publication_title": "Источник и дата проверки",
        "verification_publication_text": (
            "Укажите официальный источник и дату проверки."
        ),
        "detail_missing_labels": {
            "deadline": "срок",
            "amount": "сумму",
            "eligibility": "требования к заявителю",
            "application": "путь подачи",
        },
        "detail_sections_title": "Описание и выдержки",
        "detail_status_ok": "Описание и ключевые поля собраны с официального источника",
        "detail_status_structured_only": "Показываем краткое описание и поля",
        "detail_status_blocked": "Источник не разрешил автоматическую загрузку полного текста",
        "detail_status_not_allowed": "Для этого источника локальная загрузка отключена",
        "detail_status_too_large": "Страница слишком большая для локального чтения",
        "detail_status_unsupported_media": "Источник отдал неподдерживаемый формат",
        "detail_status_parse_error": "Не удалось корректно разобрать страницу источника",
        "detail_source_excerpt": "Фрагмент первоисточника",
        "detail_expand_source": "Развернуть текст",
        "detail_collapse_source": "Свернуть текст",
        "prepare_section_eyebrow": "Перед подачей",
        "prepare_section_title": "Что подготовить",
        "prepare_section_description": (
            "Чек-лист для этой возможности. Окончательные требования смотрите на "
            "официальном источнике."
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
            "Опишите проблему, решение, бюджет, команду, ожидаемые результаты и план внедрения."
        ),
        "prepare_tender_title": "Проверьте пакет закупки",
        "prepare_tender_text": (
            "Сверьте объём работ, квалификацию, форму подачи, гарантии и обязательные "
            "приложения."
        ),
        "prepare_startup_title": "Подготовьте презентацию проекта",
        "prepare_startup_text": (
            "Подготовьте презентацию продукта с показателями, составом команды "
            "и планом опытного внедрения."
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
        "prepare_ngo_title": "Опишите ожидаемый результат",
        "prepare_ngo_text": (
            "Укажите аудиторию проекта, ожидаемый общественный результат, партнёров "
            "и порядок отчётности."
        ),
        "prepare_source_title": "Сверьте официальный источник",
        "prepare_source_text": (
            "Перед подачей проверьте последнюю версию условий, форм и контактных "
            "данных."
        ),
        "apply_section_eyebrow": "Подача",
        "apply_section_title": "Как подать",
        "apply_section_description": (
            "Короткий порядок действий. Он не заменяет инструкцию источника."
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
        "related_section_eyebrow": "Похожие карточки",
        "related_section_title": "Похожие программы",
        "related_section_description": (
            "Ещё несколько карточек с похожими параметрами."
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
            "amount": "Объём поддержки",
            "amount_raw": "Объём с источника",
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
            "alemplus": "AlemPlus",
            "anthropology": "Антропология",
            "archaeology": "Археология",
            "architecture": "Архитектура",
            "artificial_intelligence": "Искусственный интеллект",
            "arts": "Искусство",
            "b2b": "B2B",
            "biodiversity": "Биоразнообразие",
            "biology": "Биология",
            "brief_information": "Краткая информация",
            "british_council": "Британский совет",
            "central_asia_relevant": "Центральная Азия",
            "chevening": "Chevening",
            "community": "Местные сообщества",
            "conservation": "Охрана природы",
            "cotutelle": "Совместная аспирантура",
            "doctoral": "Докторантура",
            "ecology": "Экология",
            "education_research": "Исследования в образовании",
            "eoi": "Выражение заинтересованности",
            "equity": "Социальное равенство",
            "explorers_club": "Explorers Club",
            "faculty": "Преподаватели",
            "fcdo": "FCDO",
            "field_research": "Полевые исследования",
            "final_report": "Итоговый отчёт",
            "fulbright": "Fulbright",
            "future_call": "Будущий конкурс",
            "gef": "ГЭФ",
            "gender": "Гендерное равенство",
            "german_language": "Немецкий язык",
            "germany": "Германия",
            "giz": "GIZ",
            "graduates": "Выпускники",
            "grant_funding": "Грантовое финансирование",
            "high_school": "Среднее образование",
            "inclusion": "Инклюзия",
            "interim_report": "Промежуточный отчёт",
            "international_development": "Международное развитие",
            "iom": "МОМ",
            "japan": "Япония",
            "leadership": "Лидерство",
            "market_entry": "Выход на рынок",
            "master_studies": "Магистратура",
            "migration": "Миграция",
            "music": "Музыка",
            "official_source": "Официальный источник",
            "osce": "ОБСЕ",
            "out_of_competition": "Вне конкурса",
            "peacebuilding": "Миростроительство",
            "performing_arts": "Исполнительские искусства",
            "photography": "Фотография",
            "planning_grant": "Грант на планирование",
            "professional_development": "Профессиональное развитие",
            "program_targeted_financing": "Целевое финансирование программы",
            "results_archive": "Архив результатов",
            "rfp": "Запрос предложений",
            "scholarship": "Стипендия",
            "silicon_valley": "Кремниевая долина",
            "source_watch": "Мониторинг источника",
            "spencer_foundation": "Spencer Foundation",
            "study_visit": "Учебная поездка",
            "supplies": "Поставка оборудования",
            "systems_change": "Системные изменения",
            "uk": "Великобритания",
            "un_women": "ООН-женщины",
            "undergraduate": "Бакалавриат",
            "unitar": "UNITAR",
            "university_partnership": "Партнёрство университетов",
            "women_entrepreneurship": "Женское предпринимательство",
            "ai": "ИИ",
            "artificial intelligence": "ИИ",
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
            "global_training_opportunities": "Международные программы подготовки",
            "microsoft_founders_hub": "Microsoft Founders Hub",
            "world_bank_kazakhstan": "Всемирный банк Казахстан",
            "world_bank_procurement_ca": "Закупки Всемирного банка в Центральной Азии",
            "eu_funding_tenders_ca": "Конкурсы ЕС для Центральной Азии",
            "canada_cfli_ca": "Канадский фонд местных инициатив",
            "adb_kazakhstan": "АБР Казахстан",
            "eeas_kazakhstan": "Представительство ЕС в Казахстане",
            "unicef_kazakhstan": "UNICEF Казахстан",
            "unesco_iite": "UNESCO IITE",
            "isdb_project_procurement": "Закупки Исламского банка развития",
            "islamic_development_bank": "Исламский банк развития",
            "ebrd_ecepp_procurement": "Закупки ЕБРР ECEPP",
            "undp_procurement": "Закупки ПРООН",
            "aws_activate": "AWS Activate",
            "erasmus_kazakhstan": "Erasmus+ Казахстан",
            "internews": "Internews",
            "ungm_opportunities": "Глобальный рынок ООН",
            "osce_procurement": "Закупки ОБСЕ",
            "iom_kazakhstan_procurement": "Закупки МОМ в Казахстане",
            "edb_procurement": "Закупки ЕАБР",
            "daad_central_asia": "DAAD Центральная Азия",
            "gef_sgp_kazakhstan": "Малые гранты ГЭФ в Казахстане",
            "germany": "Германия",
            "global_innovation_fund": "Глобальный инновационный фонд",
            "kazakhstan": "Казахстан",
            "central_asia": "Центральная Азия",
            "central_asia_relevant": "Центральная Азия",
            "official_source": "Официальный источник",
            "source_watch": "Мониторинг источника",
            "daad": "DAAD",
            "edb": "ЕАБР",
            "eoi": "Выражение заинтересованности",
            "future_call": "Будущий конкурс",
            "gef": "ГЭФ",
            "gif": "Глобальный инновационный фонд",
            "iom": "МОМ",
            "migration": "Миграция",
            "osce": "ОБСЕ",
            "rfp": "Запрос предложений",
            "scholarship": "Стипендия",
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
            "daad": "DAAD",
            "design": "Дизайн",
            "cloudflare": "Cloudflare",
            "consultancy": "Консультационные услуги",
            "consulting": "Консультационные услуги",
            "creative_industries": "Креативные индустрии",
            "culture": "Культура",
            "database": "Базы данных",
            "developer_tools": "Инструменты разработчика",
            "diaspora": "Диаспора",
            "digital": "Цифровые решения",
            "donor": "Донорские программы",
            "doctoral": "Докторантура",
            "drawing": "Рисунок",
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
            "fulbright": "Fulbright",
            "founder_training": "Подготовка основателей",
            "governance": "Управление",
            "gpu": "GPU",
            "alemplus": "AlemPlus",
            "health": "Здравоохранение",
            "higher_education": "Высшее образование",
            "human_rights": "Права человека",
            "infrastructure": "Инфраструктура",
            "international": "Международная возможность",
            "international_development": "Международное развитие",
            "isdb": "Исламский банк развития",
            "it": "ИТ",
            "japan": "Япония",
            "jean_monnet": "Жан Моне",
            "joint_degrees": "Совместные программы",
            "kyrgyz": "Кыргызстан",
            "kyrgyzstan": "Кыргызстан",
            "literature": "Литература",
            "morocco": "Марокко",
            "mobility": "Академическая мобильность",
            "nonprofit_required": "Только для НКО",
            "partnership": "Партнёрство",
            "peacebuilding": "Миростроительство",
            "policy": "Государственная политика",
            "postdoc": "Постдок",
            "pre_seed": "Предпосевное финансирование",
            "procurement": "Закупки",
            "professional_development": "Профессиональное развитие",
            "public_diplomacy": "Публичная дипломатия",
            "south_kazakhstan": "Юг Казахстана",
            "cooperative_agreement": "Соглашение о сотрудничестве",
            "youth": "Молодежь",
            "regional_development": "Региональное развитие",
            "research": "Исследования",
            "security": "Безопасность",
            "serverless": "Бессерверные технологии",
            "sez": "СЭЗ",
            "social_entrepreneurship": "Социальное предпринимательство",
            "silicon_valley": "Кремниевая долина",
            "student_exchange": "Студенческий обмен",
            "tajikistan": "Таджикистан",
            "teacher_training": "Подготовка педагогов",
            "technology": "Технологии",
            "translation": "Перевод",
            "transport": "Транспорт",
            "un": "ООН",
            "unitar": "UNITAR",
            "visual_arts": "Изобразительное искусство",
            "undp": "ПРООН",
            "us": "США",
            "uzbekistan": "Узбекистан",
            "vocational_training": "Профессиональное образование",
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
            "media": "СМИ",
            "journalism": "Журналистика",
            "open_data": "Открытые данные",
            "startup": "Стартап",
            "grant": "Грант",
            "accelerator": "Акселератор",
            "b2b": "B2B",
            "market_entry": "Выход на рынок",
            "cloud_credit": "Облачный кредит",
            "comics": "Комиксы",
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
            "citizen_support": "Для граждан",
            "one_village_one_product": "Одно село – один продукт",
            "kezekte": "Kezekte",
            "kyzylorda": "Кызылординская область",
            "mangystau": "Мангистауская область",
            "engineering": "Инженерия",
            "chemistry": "Химия",
            "industry": "Промышленность",
            "export": "Экспорт",
            "trade": "Торговля",
            "investment": "Инвестиции",
            "science": "Наука",
            "civil_society": "Гражданский сектор",
            "smart_city": "Умный город",
            "crop_production": "Растениеводство",
            "livestock": "Животноводство",
            "digitalization": "Цифровизация",
            "ministry_science_higher_education": "Миннауки РК",
            "intergovernmental_grant": "Межправительственный грант",
            "bolashak": "Болашак",
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
            "kazakhstan_opportunity_watch": "Мониторинг программ Казахстана",
            "dod_amraa": "DOD-AMRAA",
            "hhs_nih11": "HHS-NIH",
            "national_institutes_of_health": "Национальные институты здравоохранения США (NIH)",
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
        "title": "QAZ.FUND – open support programs for Kazakhstan",
        "meta_description": (
            "Grants, subsidies, accelerators, tenders, and other support programs "
            "for Kazakhstan. Find a relevant route, verify the terms, and follow "
            "the source."
        ),
        "eyebrow": "A working navigator for support in Kazakhstan",
        "headline": "QAZ.FUND",
        "subtitle": ("Find open programs and turn them into a clear next step."),
        "hero_intro": (
            "Grants, subsidies, accelerators, and procurement – with source links, "
            "data status, and deadlines."
        ),
        "hero_primary_cta": "Find support",
        "hero_stage_eyebrow": "Three steps",
        "hero_stage_title": "Where to start?",
        "hero_stage_point_one": "Narrow the field by task, applicant type, and topic.",
        "hero_stage_point_two": "Open a card and check the terms on the source page.",
        "hero_stage_point_three": "Save the route, share it, or export the deadlines.",
        "hero_picks_label": "Quick picks",
        "hero_pick_startup": "Find support",
        "hero_pick_business": "Check a program",
        "hero_pick_farmer": "Deadlines this month",
        "hero_pick_science": "Kazakhstan support",
        "hero_pick_tenders": "Tenders and procurement",
        "spotlight_section_eyebrow": "Start with a task",
        "spotlight_section_title": "What you can check now",
        "spotlight_section_description": (
            "Relevant cards, local support measures, and upcoming deadlines in one "
            "working view."
        ),
        "spotlight_count": "Cards: {count}",
        "spotlight_action_open": "Open list",
        "spotlight_empty": "There are no open cards in this list yet.",
        "catalog_empty": "The catalogue temporarily has no available opportunities.",
        "spotlight_preview_more": "+ {count} more",
        "spotlight_trending_kicker": "Strong signals",
        "spotlight_trending_title": "What to check first",
        "spotlight_trending_note": "Cards with strong signals and an open status.",
        "spotlight_kazakhstan_kicker": "Kazakhstan",
        "spotlight_kazakhstan_title": "Kazakhstan opportunities",
        "spotlight_kazakhstan_note": "Programs with terms for applicants in Kazakhstan.",
        "spotlight_support_kicker": "Subsidies and support",
        "spotlight_support_title": "Support for businesses",
        "spotlight_support_note": (
            "Subsidies, incentives, and other programs with clear application rules."
        ),
        "spotlight_deadline_kicker": "Upcoming deadlines",
        "spotlight_deadline_title": "What closes first",
        "spotlight_deadline_note": "Open these cards early and check the requirements.",
        "pathways_section_eyebrow": "By use case",
        "pathways_section_title": "By applicant type",
        "pathways_section_description": (
            "Start with an applicant type to find the route that fits your task."
        ),
        "pathways_count": "Cards: {count}",
        "pathways_action_open": "Open list",
        "pathways_empty": "No open cards for this applicant type yet.",
        "pathway_startup_kicker": "For startups",
        "pathway_startup_title": "Accelerators, grants and cloud credits",
        "pathway_startup_note": (
            "For product teams and AI startups looking for pilots, credits, or "
            "acceleration."
        ),
        "pathway_business_kicker": "For businesses",
        "pathway_business_title": "Subsidies, incentives and Kazakhstan support",
        "pathway_business_note": (
            "For SMBs and companies where local rules and application steps matter."
        ),
        "pathway_farmer_kicker": "For farmers",
        "pathway_farmer_title": "Agri support, livestock and practical AgroTech",
        "pathway_farmer_note": (
            "For farms and agri teams working in agriculture, livestock, and technology."
        ),
        "pathway_science_kicker": "For researchers",
        "pathway_science_title": "Science funding, commercialization and research grants",
        "pathway_science_note": (
            "For universities, labs, and teams seeking research and implementation funding."
        ),
        "themes_section_eyebrow": "By topic",
        "themes_section_title": "By focus area",
        "themes_section_description": (
            "Choose a focus area to remove noise and see the cards relevant to your "
            "task."
        ),
        "discovery_library_summary": "Ready-made routes",
        "discovery_library_description": (
            "Lists for first discovery, deadline checks, and repeat work."
        ),
        "themes_count": "Cards: {count}",
        "themes_action_open": "Open list",
        "themes_empty": "There are no open cards for this topic yet.",
        "funder_section_eyebrow": "Funders",
        "funder_section_title": "Active funders and programs",
        "funder_section_description": (
            "Funders and programs, their focus areas, and open opportunities."
        ),
        "funder_open_profile": "Open profile",
        "funder_empty": "No funder profiles were found yet.",
        "funder_live_now": "Open opportunities",
        "funder_total_items": "Total indexed",
        "funder_next_deadline": "Nearest deadline",
        "funder_overview_intro": (
            "This profile is built from published programs and announcements."
        ),
        "funder_overview_types": "Formats: {types}.",
        "funder_overview_topics": "Main topics: {topics}.",
        "funder_overview_regions": "Regional focus: {regions}.",
        "funder_page_eyebrow": "Funder profile",
        "funder_focus_title": "What the current index shows",
        "funder_focus_note": "Formats, regions, and themes in the current index.",
        "funder_focus_types": "Formats",
        "funder_focus_regions": "Regions",
        "funder_focus_indexed": "Indexed",
        "funder_live_title": "Open opportunities",
        "funder_live_note": "Open, rolling, and planned records available to review.",
        "funder_live_empty": "There are no open or planned records for this funder.",
        "funder_archive_title": "Archive",
        "funder_archive_note": "Closed records show the funder's profile and program timing.",
        "funder_archive_empty": "There are no archive records.",
        "funder_sources_title": "Profile sources",
        "funder_sources_note": "Official pages used for this profile.",
        "funder_back_to_catalog": "Back to catalog",
        "funder_open_card": "Open card",
        "topic_brief_eyebrow": "Active focus",
        "topic_brief_count": "In view: {count}",
        "topic_brief_what": "What people usually look for",
        "topic_brief_best_for": "Who may find it useful",
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
        "focus_aria": "Current focus",
        "focus_primary": "Priority: Kazakhstan and Central Asia",
        "focus_secondary": (
            "Themes: AI, education, public sector, agriculture, veterinary, climate, media"
        ),
        "status_checking": "Catalog available",
        "api_docs": "API",
        "media_link": "Media",
        "insights_link": "Insights",
        "terms_link": "Terms",
        "data_policy_link": "Data policy",
        "attribution_link": "Data use",
        "readiness_title": "What the card already shows",
        "readiness_note": "Four fields to check before applying.",
        "readiness_source": "Source",
        "readiness_deadline": "Deadline",
        "readiness_amount": "Amount",
        "readiness_eligibility": "Eligibility",
        "methodology_link": "How it works",
        "status_link": "Data status",
        "language_switch": "Interface language",
        "nav_aria": "Radar sections",
        "tab_opportunities": "Opportunities",
        "tab_sources": "Sources",
        "tab_health": "Status",
        "metrics_aria": "Summary metrics",
        "metric_total": "Indexed",
        "metric_relevant": "Current catalogue",
        "metric_sources": "Sources monitored",
        "opportunities_title": "Opportunities",
        "opportunities_description": (
            "Open and rolling programs prioritized for Kazakhstan and Central Asia."
        ),
        "opportunities_description_all": (
            "Open, rolling, and archived records for coverage and source checks."
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
            "Region and topic affect relevance; deadlines affect order. This is not "
            "an award probability. Verify the source."
        ),
        "all_sources": "All sources",
        "clear_filters": "Clear filters",
        "loading_opportunities": "Loading opportunities",
        "load_more": "Load more",
        "sources_title": "Source coverage",
        "sources_description": (
            "Official sources and monitored pages connected to the catalog."
        ),
        "loading_sources": "Loading sources",
        "show_all_sources": "Show all sources",
        "show_fewer_sources": "Show fewer",
        "trust_library_summary": "Sources and transparency",
        "trust_library_description": (
            "Coverage, data freshness, funders, and methodology."
        ),
        "funder_library_summary": "Funder profiles",
        "funder_library_description": (
            "Who publishes programs and where open opportunities are listed."
        ),
        "methodology_library_summary": "Data checks and methodology",
        "methodology_library_description": (
            "Source status, selection, and verification guidance."
        ),
        "source_refresh_title": "Latest successful source refresh",
        "source_refresh_value": "Updated {date}",
        "source_refresh_unknown": "Refresh date unavailable",
        "health_title": "Data status",
        "health_description": (
            "Shows whether the catalog is available and how many sources are active."
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
        "api_status": "Data feed",
        "stored_items": "Catalog entries",
        "health_sources": "Active sources",
        "health_stale_sources": "Stale sources",
        "api_online": "Data is current",
        "api_failed": "Data needs attention",
        "api_error": "Data load error",
        "source_catalog_unavailable": "Source catalog is temporarily unavailable.",
        "showing_sources": "Showing {shown} of {total} sources",
        "sources_connected": "{total} sources connected",
        "show_all_sources_with_total": "Show all {total} sources",
        "coverage_unavailable": "Coverage unavailable",
        "indexed_count": "{count} indexed",
        "relevant_open_count": "{count} relevant open",
        "direct_badge": "Direct",
        "watchlist_badge": "Watchlist",
        "source_direct_note": "Direct connection to the official source",
        "source_watchlist_note": "Monitored page with editorial review",
        "regional_badge_kazakhstan": "Kazakhstan",
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
        "methodology_title": "How we work",
        "methodology_description": (
            "Each card leads to a source, shows the limits of its data, and leaves "
            "the decision to a person."
        ),
        "method_card_sources_title": "Sources and refresh",
        "method_card_sources_text": (
            "We combine official sources, open registers, and monitored pages. The "
            "catalog shows the source link and data status."
        ),
        "method_card_relevance_title": "Why a card is here",
        "method_card_relevance_text": (
            "Topic, region, applicant type, and deadline affect the order. This is "
            "a working sort, not a promise of an award."
        ),
        "method_card_trust_title": "The source comes first",
        "method_card_trust_text": (
            "Use the card to orient yourself. Check current terms, forms, and "
            "requirements on the program page."
        ),
        "method_disclaimer_title": "You make the decision",
        "method_disclaimer_text": (
            "QAZ.FUND does not award funds or process applications. Before acting, "
            "check the deadline, criteria, documents, and submission route at the "
            "source."
        ),
        "role_guide_title": "For working decisions, not endless browsing",
        "role_guide_description": (
            "For editorial, analytical, or verification work, continue in the "
            "operator workspace."
        ),
        "role_guide_link_label": "Open operator workspace",
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
            "No. QAZ.FUND organizes public opportunities; applications go to the "
            "program organizer."
        ),
        "faq_q2": "How often is the data refreshed?",
        "faq_a2": (
            "Sources and the index are rechecked regularly. See Data status for the "
            "current state."
        ),
        "faq_q3": "What does match precision mean?",
        "faq_a3": (
            "It is not a program rating. The threshold shows how closely a card "
            "matches the selected theme, region, and format."
        ),
        "faq_q4": "Why do support measures sometimes appear near grants?",
        "faq_a4": (
            "Some support measures are not grants but serve the same audience. We "
            "keep them when they match the use case."
        ),
        "collections_label": "Saved selections",
        "collections_aria": "Saved filters for repeat work",
        "collections_empty": "Save filters to return to this list later.",
        "profile_title": "Build a profile shortlist",
        "profile_intro": (
            "Choose the applicant type, geography, support format and timing. "
            "The catalogue will build a reproducible shortlist."
        ),
        "profile_audience": "Who is applying",
        "profile_region": "Where is the project",
        "profile_format": "What do you need",
        "profile_deadline": "When are you applying",
        "profile_apply": "Show the profile shortlist",
        "profile_reset": "Clear profile",
        "profile_local_note": (
            "The profile is not sent to the server. Selected parameters stay in "
            "the link and can be shared."
        ),
        "profile_applied": "Profile-based shortlist updated.",
        "save_view": "Save filters",
        "share_view": "Share results",
        "saved_view_saved": "Collection saved in this browser.",
        "saved_view_removed": "Collection removed.",
        "saved_view_shared": "Copied a link to the current collection.",
        "saved_view_default_name": "My collection",
        "saved_view_remove_aria": "Remove collection",
        "saved_view_status_label": "Saved collection status",
        "saved_view_share_prompt": "Copy the link to this collection",
        "advanced_filters": "Advanced filters",
        "mobile_filters_summary": "Refine results",
        "mobile_app_navigation": "Main QAZ.FUND sections",
        "mobile_app_tagline": "Support navigator",
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
        "workspace_queue_local": "Stored in this browser.",
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
        "open_source_short": "Go to source",
        "footer_owner": "QAZ.FUND is an open opportunity navigator. Built by",
        "footer_disclaimer": (
            "QAZ.FUND does not award funds or process applications. Always verify "
            "final terms on the source page."
        ),
        "footer_support": "Feedback",
        "footer_qdev": "qdev.run",
        "footer_terms": "Terms",
        "footer_data_policy": "Data policy",
        "footer_attribution": "Data use",
        "view_funder": "Funder profile",
        "fit_label": "Match signals",
        "fit_unknown": "Check the criteria",
        "fit_deadline_soon": "Closing soon",
        "fit_global": "Global application",
        "signal_label": "Why it is shown",
        "card_meta_label": "Key details",
        "signal_support_kz": (
            "A support measure for teams and businesses in Kazakhstan with clear "
            "application steps."
        ),
        "signal_public_sector": (
            "For teams working with public-sector delivery, infrastructure, and "
            "development programs."
        ),
        "signal_business": (
            "For businesses where terms, documents, and application steps matter."
        ),
        "signal_startup": (
            "For product and AI teams looking for acceleration, pilots, or cloud "
            "credits."
        ),
        "signal_tender": (
            "Check applicant requirements, scope, and submission documents."
        ),
        "signal_science": "For universities, labs, and research teams.",
        "signal_farmer": "For farms, producers, and agri teams.",
        "signal_ngo": "For NGOs, media teams, and civic or social-impact projects.",
        "signal_kazakhstan": (
            "The terms name Kazakhstan or local application conditions."
        ),
        "signal_central_asia": (
            "Works for Central Asia teams without being tied to a single country."
        ),
        "signal_global": (
            "A global opportunity – check the eligibility rules for your team."
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
        "detail_fit_title": "What to verify",
        "detail_source_status_title": "Source status",
        "detail_fit_good": "Some signals match",
        "detail_fit_review": "Check eligibility manually",
        "no_indexed_items": "The catalog has no available cards yet.",
        "no_filtered_items": "No opportunities match the selected filters.",
        "no_filtered_items_hint": "Clear one filter and try again.",
        "empty_action_clear": "Clear all",
        "empty_action_region": "All regions",
        "empty_action_deadline": "Any timing",
        "empty_action_score": "Baseline threshold",
        "empty_action_scope": "Open full catalog",
        "open_details": "Brief view",
        "read_more": "Full card",
        "open_rolling": "Open / Rolling",
        "score_title": "Rule-based catalog relevance; not an award probability",
        "score_exact": "High",
        "score_high": "Good",
        "score_base": "Baseline",
        "source_agency": "Source agency: {agency}",
        "no_summary": "No description provided by source.",
        "reload_confirm": "Reload data from all sources?",
        "results_button": "Load {count} more",
        "unknown_url": "Unknown URL",
        "views_aria": "Dashboard section navigation",
        "breadcrumbs_aria": "Breadcrumbs",
        "detail_panel_label": "Opportunity details",
        "detail_shell_title": "Details",
        "detail_title_fallback": "Opportunity detail",
        "detail_loading": "Loading description and fields",
        "detail_error": (
            "The local description is unavailable. Open the source below."
        ),
        "detail_empty": (
            "No expanded description is available. Showing the summary and fields."
        ),
        "detail_close": "Close",
        "detail_open_page": "Open page",
        "detail_all_opportunities": "All opportunities",
        "detail_open_source": "Open source",
        "detail_open_application": "Open application",
        "detail_prepare_application": "Prepare application",
        "detail_closed_notice": (
            "Applications are closed. This record remains available for reference; "
            "check with the organizer for a new round."
        ),
        "detail_forecast_notice": (
            "Applications are not open yet. Terms and dates may change before launch."
        ),
        "detail_compute_readiness": (
            "Data completeness: {score} / 100, {tier}. This is a supporting "
            "indicator, not an eligibility decision."
        ),
        "detail_compute_ready": "enough data",
        "detail_compute_watch": "review needed",
        "detail_compute_blocked": "blocked",
        "detail_compute_unknown": "status unknown",
        "detail_meta_title": "At a glance",
        "detail_readiness_title": "What to check",
        "detail_readiness_complete": (
            "The main details are present. Check the current terms before applying."
        ),
        "detail_readiness_partial": ("Confirm on the organizer's page: {missing}."),
        "detail_copy_brief": "Copy working brief",
        "detail_copy_brief_done": "Working brief copied.",
        "detail_copy_brief_prompt": "Copy the working brief",
        "detail_share": "Share opportunity",
        "detail_share_done": "The opportunity is ready to share.",
        "detail_share_prompt": "Copy the link to this opportunity",
        "detail_brief_heading": "QAZ.FUND – working brief",
        "detail_brief_legacy_heading": "QAZ.FUND – working brief",
        "detail_brief_summary": "Summary",
        "detail_brief_source": "Organizer or source",
        "detail_brief_format": "Format",
        "detail_brief_region": "Region",
        "detail_brief_deadline": "Deadline",
        "detail_brief_amount": "Amount",
        "detail_brief_official_url": "Official source",
        "detail_brief_application_url": "Application",
        "detail_brief_caveat": (
            "Verify terms, eligibility, documents, deadline, and submission route "
            "on the official source."
        ),
        "verification_eyebrow": "Verification",
        "verification_title": "Before applying",
        "verification_description": (
            "Use the card to start a check. It does not confirm eligibility or replace "
            "the official terms."
        ),
        "decision_check_eyebrow": "Before applying",
        "decision_check_title": "Key conditions",
        "decision_check_description": (
            "Check these four points on the organizer's page first."
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
        "decision_check_known_title": "What is known",
        "decision_check_known_source": "source: {source}",
        "decision_check_known_format": "format: {format}",
        "decision_check_known_deadline": "deadline: {deadline}",
        "decision_check_known_amount": "support amount: {amount}",
        "decision_check_known_eligibility": "requirements: {eligibility}",
        "decision_check_known_empty": "Only the source and summary are known so far.",
        "decision_check_missing_title": "What to confirm",
        "decision_check_missing_text": "Confirm on the official page: {items}.",
        "decision_check_missing_none": (
            "The main fields are present. Check the current terms before applying."
        ),
        "decision_check_route_title": "Where to apply",
        "decision_check_route_application": (
            "Use the dedicated application form and compare its requirements "
            "with the source."
        ),
        "decision_check_route_source": (
            "No separate form is listed. Apply only through the organizer's page."
        ),
        "decision_check_boundary_title": "Important",
        "decision_check_boundary_text": (
            "The card helps with selection; the organizer's rules govern the decision."
        ),
        "verification_publication_title": "Source and verification date",
        "verification_publication_text": (
            "Record the official source and verification date."
        ),
        "detail_missing_labels": {
            "deadline": "deadline",
            "amount": "amount",
            "eligibility": "applicant eligibility",
            "application": "application route",
        },
        "detail_sections_title": "Description and excerpts",
        "detail_status_ok": "Description and key fields were collected from the official source",
        "detail_status_structured_only": "Showing the stored summary and fields",
        "detail_status_blocked": "The source did not allow automatic full-text retrieval",
        "detail_status_not_allowed": "Local fetch is disabled for this source",
        "detail_status_too_large": "The source page is too large for local reading",
        "detail_status_unsupported_media": "The source returned an unsupported format",
        "detail_status_parse_error": "The source page could not be parsed cleanly",
        "detail_source_excerpt": "Source excerpt",
        "detail_expand_source": "Show excerpt",
        "detail_collapse_source": "Hide excerpt",
        "prepare_section_eyebrow": "Before applying",
        "prepare_section_title": "What to prepare",
        "prepare_section_description": (
            "A checklist for this opportunity. Verify final requirements on the "
            "official source."
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
            "A short sequence of steps. It does not replace the source instructions."
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
        "related_section_eyebrow": "Similar cards",
        "related_section_title": "Related opportunities",
        "related_section_description": "A few cards with similar parameters.",
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
            "alemplus": "AlemPlus",
            "anthropology": "Anthropology",
            "archaeology": "Archaeology",
            "architecture": "Architecture",
            "artificial_intelligence": "Artificial intelligence",
            "arts": "Arts",
            "b2b": "B2B",
            "biodiversity": "Biodiversity",
            "biology": "Biology",
            "brief_information": "Brief information",
            "british_council": "British Council",
            "central_asia_relevant": "Central Asia",
            "chevening": "Chevening",
            "community": "Communities",
            "conservation": "Conservation",
            "cotutelle": "Cotutelle",
            "doctoral": "Doctoral studies",
            "diaspora": "Diaspora",
            "ecology": "Ecology",
            "education_research": "Education research",
            "eoi": "Expression of interest",
            "equity": "Equity",
            "explorers_club": "Explorers Club",
            "faculty": "Faculty",
            "fcdo": "FCDO",
            "field_research": "Field research",
            "final_report": "Final report",
            "founder_training": "Founder training",
            "fulbright": "Fulbright",
            "future_call": "Future call",
            "gef": "GEF",
            "gender": "Gender equality",
            "german_language": "German language",
            "germany": "Germany",
            "gif": "Global Innovation Fund",
            "giz": "GIZ",
            "graduates": "Graduates",
            "grant_funding": "Grant funding",
            "high_school": "High school",
            "inclusion": "Inclusion",
            "interim_report": "Interim report",
            "international_development": "International development",
            "iom": "IOM",
            "japan": "Japan",
            "leadership": "Leadership",
            "market_entry": "Market entry",
            "master_studies": "Master's studies",
            "migration": "Migration",
            "music": "Music",
            "official_source": "Official source",
            "osce": "OSCE",
            "out_of_competition": "Out of competition",
            "peacebuilding": "Peacebuilding",
            "performing_arts": "Performing arts",
            "photography": "Photography",
            "planning_grant": "Planning grant",
            "professional_development": "Professional development",
            "program_targeted_financing": "Program-targeted financing",
            "results_archive": "Results archive",
            "rfp": "Request for proposals",
            "scholarship": "Scholarship",
            "silicon_valley": "Silicon Valley",
            "source_watch": "Source monitoring",
            "spencer_foundation": "Spencer Foundation",
            "study_visit": "Study visit",
            "supplies": "Supplies",
            "systems_change": "Systems change",
            "uk": "United Kingdom",
            "un_women": "UN Women",
            "undergraduate": "Undergraduate",
            "unitar": "UNITAR",
            "university_partnership": "University partnership",
            "women_entrepreneurship": "Women entrepreneurship",
            "youth": "Youth",
            "ai": "AI",
            "artificial intelligence": "AI",
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
            "aws_activate": "AWS Activate",
            "cloudflare_startups": "Cloudflare Startups",
            "daad_central_asia": "DAAD Central Asia",
            "edb_procurement": "EDB Procurement",
            "erasmus_kazakhstan": "Erasmus+ Kazakhstan",
            "fundsforngos": "FundsforNGOs",
            "gef_sgp_kazakhstan": "GEF Small Grants Kazakhstan",
            "germany": "Germany",
            "global_innovation_fund": "Global Innovation Fund",
            "global_training_opportunities": "Global Training Opportunities",
            "grants_gov": "Grants.gov",
            "internews": "Internews",
            "iom_kazakhstan_procurement": "IOM Kazakhstan Procurement",
            "kazakhstan_watch": "Kazakhstan Opportunity Watch",
            "mongodb_startups": "MongoDB Startups",
            "nvidia_inception": "NVIDIA Inception",
            "osce_procurement": "OSCE Procurement",
            "ungm_opportunities": "UN Global Marketplace",
            "kazakhstan": "Kazakhstan",
            "central_asia": "Central Asia",
            "central_asia_relevant": "Central Asia",
            "official_source": "Official source",
            "source_watch": "Source monitoring",
            "daad": "DAAD",
            "edb": "EDB",
            "eoi": "Expression of interest",
            "future_call": "Future call",
            "gef": "GEF",
            "gif": "Global Innovation Fund",
            "iom": "IOM",
            "migration": "Migration",
            "osce": "OSCE",
            "rfp": "Request for proposals",
            "scholarship": "Scholarship",
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
            "daad": "DAAD",
            "design": "Design",
            "digital": "Digital solutions",
            "digital_skills": "Digital skills",
            "donor": "Donor programs",
            "doctoral": "Doctoral studies",
            "drawing": "Drawing",
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
            "fulbright": "Fulbright",
            "founder_training": "Founder training",
            "google": "Google",
            "governance": "Governance",
            "gpu": "GPU",
            "alemplus": "AlemPlus",
            "health": "Health",
            "higher_education": "Higher education",
            "human_rights": "Human rights",
            "infrastructure": "Infrastructure",
            "international": "International opportunity",
            "international_development": "International development",
            "isdb": "IsDB",
            "it": "IT",
            "japan": "Japan",
            "jean_monnet": "Jean Monnet",
            "joint_degrees": "Joint degrees",
            "kyrgyz": "Kyrgyzstan",
            "kyrgyzstan": "Kyrgyzstan",
            "literature": "Literature",
            "morocco": "Morocco",
            "mobility": "Academic mobility",
            "nonprofit_required": "Nonprofits only",
            "opportunity_desk": "Opportunity Desk",
            "partnership": "Partnership",
            "peacebuilding": "Peacebuilding",
            "policy": "Public policy",
            "postdoc": "Postdoc",
            "procurement": "Procurement",
            "professional_development": "Professional development",
            "project_pipeline": "Project pipeline",
            "public_diplomacy": "Public diplomacy",
            "south_kazakhstan": "South Kazakhstan",
            "cooperative_agreement": "Cooperative agreement",
            "youth": "Youth",
            "public_sector": "Public sector",
            "regional_development": "Regional development",
            "research": "Research",
            "security": "Security",
            "serverless": "Serverless",
            "sez": "Special economic zones",
            "social_entrepreneurship": "Social entrepreneurship",
            "silicon_valley": "Silicon Valley",
            "startup_support": "Startup support",
            "student_exchange": "Student exchange",
            "tajikistan": "Tajikistan",
            "translation": "Translation",
            "visual_arts": "Visual arts",
            "teacher_training": "Teacher training",
            "technology": "Technology",
            "transport": "Transport",
            "un": "UN",
            "unitar": "UNITAR",
            "undp": "UNDP",
            "us": "US",
            "uzbekistan": "Uzbekistan",
            "vocational_training": "Vocational training",
            "watchlist": "Watchlist",
            "water": "Water",
            "world_bank": "World Bank",
            "media": "Media",
            "journalism": "Journalism",
            "open_data": "Open data",
            "startup": "Startup",
            "grant": "Grant",
            "accelerator": "Accelerator",
            "b2b": "B2B",
            "market_entry": "Market entry",
            "pre_seed": "Pre-seed funding",
            "cloud_credit": "Cloud credit",
            "comics": "Comics",
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
            "citizen_support": "Citizen support",
            "one_village_one_product": "One Village One Product",
            "kezekte": "Kezekte",
            "kyzylorda": "Kyzylorda region",
            "mangystau": "Mangystau region",
            "engineering": "Engineering",
            "chemistry": "Chemistry",
            "industry": "Industry",
            "export": "Export",
            "trade": "Trade",
            "investment": "Investment",
            "science": "Science",
            "civil_society": "Civil society",
            "smart_city": "Smart city",
            "crop_production": "Crop production",
            "livestock": "Livestock",
            "digitalization": "Digitalization",
            "ministry_science_higher_education": "Science ministry",
            "intergovernmental_grant": "Intergovernmental grant",
            "bolashak": "Bolashak",
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
            "national_institutes_of_health": "National Institutes of Health (NIH)",
            "united_nations_development_programme": (
                "United Nations Development Programme (UNDP)"
            ),
            "european_bank_for_reconstruction_and_development": (
                "European Bank for Reconstruction and Development (EBRD)"
            ),
        },
    },
}


KK_DASHBOARD_COPY = {
    "catalog_empty": "Каталогта уақытша қолжетімді карточкалар жоқ.",
    "title": "Қазақстанға арналған қолдау бағдарламалары – QAZ.FUND",
    "mobile_app_tagline": "Қолдау навигаторы",
    "eyebrow": "Қазақстандағы қолдауды іздеу навигаторы",
    "subtitle": "Ашық бағдарламаларды тауып, келесі қадамды түсінікті етіңіз.",
    "focus_primary": "Басымдық: Қазақстан және Орталық Азия",
    "focus_secondary": (
        "Тақырыптар: ЖИ, білім, мемлекеттік сектор, агро, ветеринария, экология, медиа"
    ),
    "hero_intro": (
        "Гранттар, субсидиялар, акселераторлар және сатып алулар – дереккөзі, "
        "деректер мәртебесі және мерзімдерімен."
    ),
    "hero_primary_cta": "Қолдауды табу",
    "hero_stage_point_one": "Міндет, өтініш беруші түрі және тақырып бойынша іздеуді тарылтыңыз.",
    "hero_stage_point_two": "Карточканы ашып, шарттарды дереккөз бетінде тексеріңіз.",
    "hero_stage_point_three": "Маршрутты сақтаңыз, бөлісіңіз немесе мерзімдерді жүктеп алыңыз.",
    "hero_stage_eyebrow": "Үш қадам",
    "hero_stage_title": "Неден бастау керек?",
    "hero_pick_startup": "Қолдауды табу",
    "hero_pick_business": "Бағдарламаны тексеру",
    "hero_pick_farmer": "Осы айдағы мерзімдер",
    "hero_pick_science": "ҚР қолдауы",
    "hero_pick_tenders": "Тендерлер мен сатып алулар",
    "funder_focus_indexed": "Индексте",
    "metric_relevant": "Индекстегі өзекті",
    "status_checking": "Каталог қолжетімді",
    "methodology_link": "Қалай жұмыс істейді",
    "opportunities_description": (
        "Қазақстан мен Орталық Азияға басымдық берілген ашық және тұрақты бағдарламалар."
    ),
    "mobile_filters_summary": "Іріктеуді баптау",
    "audience_label": "Кім үшін",
    "audience_all": "Барлығы",
    "pathway_startup_kicker": "Стартаптарға",
    "pathway_business_kicker": "Бизнеске",
    "pathway_farmer_kicker": "Фермерлерге",
    "audience_ngo": "ҮЕҰ-ларға",
    "pathway_science_kicker": "Зерттеушілерге",
    "format_label": "Не іздейсіз",
    "format_all": "Барлық формат",
    "format_grants": "Гранттар мен конкурстар",
    "spotlight_support_kicker": "Субсидиялар мен шаралар",
    "format_accelerators": "Акселераторлар мен кредиттер",
    "topic_label": "Тақырып",
    "topic_all": "Барлық тақырып",
    "theme_ai_kicker": "ЖИ және цифрлық шешімдер",
    "theme_agro_kicker": "Агро / вет / эко",
    "theme_science_kicker": "Білім және ғылым",
    "theme_public_kicker": "Мемлекеттік сектор және инфрақұрылым",
    "theme_ngo_kicker": "Медиа және ҮЕҰ",
    "theme_business_kicker": "Бизнес және субсидиялар",
    "search_label": "Іздеу",
    "region_label": "Өңір",
    "region_all": "Барлық өңір",
    "spotlight_kazakhstan_kicker": "Қазақстан",
    "region_central_asia": "Орталық Азия",
    "region_global": "Халықаралық",
    "scope_label": "Қамту",
    "scope_open": "Ашық",
    "scope_all": "Бүкіл индекс",
    "advanced_filters": "Қосымша сүзгілер",
    "lifecycle_label": "Кезең",
    "lifecycle_all": "Кез келген кезең",
    "lifecycle_open": "Қазір ашық",
    "lifecycle_closing_soon": "Жақында жабылады",
    "lifecycle_closed": "Жабық",
    "lifecycle_awarded": "Аяқталған",
    "readiness_deadline": "Мерзім",
    "deadline_filter_all": "Кез келген мерзім",
    "deadline_filter_soon": "Жақында жабылатындар",
    "deadline_filter_month": "Келесі айда",
    "deadline_filter_rolling": "Тұрақты қабылдау",
    "sort_label": "Сұрыптау",
    "sort_priority": "Әрекет басымдығы бойынша",
    "sort_deadline": "Ең жақын мерзім",
    "sort_updated": "Жаңартылғаны бойынша",
    "min_score_label": "Каталог сәйкестігі",
    "all_scores": "Барлық нәтиже",
    "score_option_03": "Базалық сәйкестік",
    "score_option_05": "Жақсы сәйкестік",
    "score_option_07": "Жоғары сәйкестік",
    "score_help": (
        "Өңір мен тақырып сәйкестікке, ал мерзім көрсету ретіне әсер етеді. "
        "Бұл мақұлдау ықтималдығы емес; шарттарды дереккөзден қараңыз."
    ),
    "readiness_source": "Дереккөз",
    "all_sources": "Барлық дереккөз",
    "mobile_show_results": "Нәтижелерді көрсету",
    "clear_filters": "Сүзгілерді тазарту",
    "collections_label": "Сақталған іріктеулер",
    "workspace_filter": "Сақталған карточкалар",
    "workspace_backup": "Жүктеп алу",
    "export_csv": "CSV кестесі",
    "export_deadlines": "Мерзімдерді күнтізбеге",
    "workspace_export": "Резервтік көшірме",
    "workspace_import": "Көшірмені қалпына келтіру",
    "save_view": "Сүзгілерді сақтау",
    "share_view": "Нәтижемен бөлісу",
    "collections_empty": "Осы тізімге оралу үшін сүзгілерді сақтаңыз.",
    "workspace_queue_title": "Келесі қадамдар",
    "workspace_queue_local": "Деректер осы браузерде сақталады.",
    "profile_title": "Профиль бойынша іріктеу жасау",
    "profile_intro": (
        "Өтініш беруші түрін, географияны, қолдау форматын және мерзімді көрсетіңіз – "
        "каталог қайта пайдалануға болатын іріктеу жасайды."
    ),
    "profile_audience": "Кім өтініш береді",
    "profile_region": "Жоба қайда",
    "profile_format": "Не қажет",
    "profile_deadline": "Қашан бересіз",
    "profile_apply": "Профиль бойынша іріктеуді көрсету",
    "profile_reset": "Профильді тазарту",
    "profile_local_note": (
        "Профиль серверге жіберілмейді. Таңдалған параметрлер сілтемеде сақталады, "
        "оны қайта жібере аласыз."
    ),
    "loading_opportunities": "Мүмкіндіктер жүктелуде",
    "load_more": "Тағы көрсету",
    "discovery_library_summary": "Дайын маршруттар",
    "discovery_library_description": (
        "Алғашқы іздеуге, мерзімдерді тексеруге және қайталап жұмыс істеуге арналған іріктеулер."
    ),
    "spotlight_section_eyebrow": "Міндеттен бастаңыз",
    "spotlight_section_title": "Қазір нені тексеруге болады",
    "spotlight_section_description": (
        "Сәйкес карточкалар, жергілікті қолдау шаралары және жақын мерзімдер – "
        "бір жұмыс көрінісінде."
    ),
    "pathways_section_eyebrow": "Міндет бойынша",
    "pathways_section_title": "Өтініш беруші түрі бойынша",
    "pathways_section_description": "Маршрутты жылдам табу үшін өтініш беруші түрінен бастаңыз.",
    "themes_section_eyebrow": "Тақырып бойынша",
    "themes_section_title": "Бағыт бойынша",
    "themes_section_description": (
        "Артық ақпаратты алып тастап, міндетке қатысты карточкаларды көру үшін бағытты таңдаңыз."
    ),
    "trust_library_summary": "Дереккөздер және ашықтық",
    "trust_library_description": "Қамту, деректердің жаңалығы, қорлар және әдістеме.",
    "funder_library_summary": "Қор профильдері",
    "funder_library_description": (
        "Бағдарламаларды кім жариялайды және қай жерде ашық мүмкіндіктер бар."
    ),
    "sources_title": "Дереккөздер қамтуы",
    "sources_description": "Каталогқа қосылған ресми дереккөздер мен мониторинг беттері.",
    "show_all_sources": "Барлық дереккөзді көрсету",
    "methodology_library_summary": "Деректерді тексеру және әдістеме",
    "methodology_library_description": "Дереккөз мәртебесі, іріктеу және тексеру қағидалары.",
    "health_description": "Каталогтың қолжетімділігін және белсенді дереккөздер санын көрсетеміз.",
    "reload_live_data": "Деректерді жаңарту",
    "api_status": "Деректер ағыны",
    "stored_items": "Каталогтағы жазбалар",
    "health_sources": "Белсенді дереккөздер",
    "health_stale_sources": "Ескірген дереккөздер",
    "health_note_loading": (
        "Каталог деректері қолжетімді. Соңғы жаңарту уақытын анықтап жатырмыз."
    ),
    "method_card_sources_title": "Дереккөздер және жаңарту",
    "method_card_sources_text": (
        "Ресми дереккөздерді, ашық тізілімдерді және мониторинг беттерін жинаймыз. "
        "Жанында сілтеме мен деректер мәртебесін көрсетеміз."
    ),
    "method_card_relevance_title": "Карточка неге осында",
    "method_card_relevance_text": (
        "Тақырып, өңір, өтініш беруші түрі және мерзім көрсету ретіне әсер етеді. "
        "Бұл жұмыс сұрыптауы, мақұлдау уәдесі емес."
    ),
    "method_card_trust_title": "Карточкадан гөрі дереккөз маңызды",
    "method_card_trust_text": (
        "Карточка бағыт алуға көмектеседі. Қолданыстағы шарттарды, нысандарды және "
        "талаптарды бағдарлама бетінде тексеріңіз."
    ),
    "method_disclaimer_title": "Шешім өзіңізде",
    "method_disclaimer_text": (
        "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды. Әрекет етпес бұрын "
        "дереккөзден мерзімді, өлшемдерді, құжаттарды және беру тәсілін тексеріңіз."
    ),
    "role_guide_title": "Шексіз іздеу емес, жұмыс үшін",
    "role_guide_description": (
        "Карточкаларды редакциялық, талдамалық немесе тексеру жұмысына қолдансаңыз, "
        "оператор бөліміне өтіңіз."
    ),
    "role_guide_link_label": "Оператор бөліміне өту",
    "role_analyst_title": "Талдаушыға",
    "role_analyst_text": (
        "Сүзгілерді сілтемемен бекітіп, өрістерді салыстырып, нәтижені CSV-ге жүктеңіз."
    ),
    "role_journalist_title": "Журналистке",
    "role_journalist_text": (
        "Карточкадан анықтаманы көшіріп, ресми дереккөз бен тексеру күнін көрсетіңіз."
    ),
    "role_editor_title": "Редакторға",
    "role_editor_text": (
        "Жарияламас бұрын расталған өрістерді қайта тексеруді қажет ететіндерден ажыратыңыз."
    ),
    "role_lawyer_title": "Заңгерге",
    "role_lawyer_text": (
        "Шарттардың қолданыстағы нұсқасын, өтініш берушіні, құжаттарды, мерзімді және "
        "беру арнасын тексеріңіз."
    ),
    "role_official_title": "Мемлекеттік қызметшіге",
    "role_official_text": (
        "ҚР бойынша қайта өндіруге болатын іріктеу жасап, кесте мен мерзім күнтізбесін жүктеңіз."
    ),
    "faq_q1": "QAZ.FUND өзі грант береді ме?",
    "faq_a1": "Жоқ. QAZ.FUND ашық мүмкіндіктерді жинап, реттейді; өтінім ұйымдастырушыға беріледі.",
    "faq_q2": "Деректер қаншалықты жиі жаңартылады?",
    "faq_a2": (
        "Дереккөздер мен индекс тұрақты түрде қайта тексеріледі. Ағымдағы күй "
        "«Деректер мәртебесі» бөлімінде көрінеді."
    ),
    "faq_q3": "Сәйкестік дәлдігі нені білдіреді?",
    "faq_a3": (
        "Бұл бағдарламаны бағалау емес. Шек карточканың таңдалған тақырыпқа, өңірге "
        "және форматқа қаншалықты сәйкес келетінін көрсетеді."
    ),
    "faq_q4": "Неге гранттармен қатар қолдау шаралары да көрсетіледі?",
    "faq_a4": (
        "Кейбір қолдау шаралары грант емес, бірақ сол аудиторияға сәйкес келеді. "
        "Міндетпен үйлессе, оларды да қалдырамыз."
    ),
    "footer_support": "Кері байланыс",
    "footer_terms": "Шарттар",
    "footer_data_policy": "Деректер саясаты",
    "footer_attribution": "Деректерді пайдалану",
    "mobile_catalog": "Каталог",
    "mobile_saved": "Сақталғандар",
    "mobile_filters": "Сүзгілер",
    "detail_shell_title": "Толығырақ",
    "detail_loading": "Сипаттама мен параметрлер жүктелуде",
    "detail_close": "Жабу",
    "detail_fit_title": "Нені тексеру керек",
    "detail_fit_review": "Өлшемдерді қолмен тексеріңіз",
    "detail_readiness_title": "Деректердің толықтығы",
    "detail_sections_title": "Сипаттама мен үзінділер",
    "detail_open_page": "Бетті ашу",
    "meta_description": (
        "Қазақстанға арналған гранттар, субсидиялар, акселераторлар, тендерлер және "
        "басқа қолдау бағдарламалары. Сәйкес маршрутты тауып, шарттарды тексеріңіз."
    ),
    "headline": "QAZ.FUND",
    "hero_picks_label": "Жылдам таңдау",
    "spotlight_count": "Карточкалар: {count}",
    "spotlight_action_open": "Тізімді ашу",
    "spotlight_empty": "Бұл тізімде әзірге ашық карточкалар жоқ.",
    "spotlight_preview_more": "+ тағы {count}",
    "spotlight_trending_kicker": "Маңызды белгілер",
    "spotlight_trending_title": "Алдымен нені тексеру керек",
    "spotlight_trending_note": "Маңызды белгілері бар және ашық күйдегі карточкалар.",
    "spotlight_kazakhstan_title": "Қазақстанға арналған мүмкіндіктер",
    "spotlight_kazakhstan_note": (
        "Қазақстаннан өтініш берушілерге арналған шарттары бар бағдарламалар."
    ),
    "spotlight_support_title": "Бизнеске арналған қолдау",
    "spotlight_support_note": (
        "Өтінім беру тәртібі түсінікті субсидиялар, жеңілдіктер және басқа шаралар."
    ),
    "spotlight_deadline_kicker": "Жақын мерзімдер",
    "spotlight_deadline_title": "Алдымен қайсысы жабылады",
    "spotlight_deadline_note": "Карточкаларды ертерек ашып, талаптарды тексеріңіз.",
    "pathways_count": "Карточкалар: {count}",
    "pathways_action_open": "Тізімді ашу",
    "pathways_empty": "Бұл өтініш беруші түріне арналған ашық карточкалар әзірге жоқ.",
    "pathway_startup_title": "Акселераторлар, гранттар және бұлттық кредиттер",
    "pathway_startup_note": (
        "Пилот, кредит немесе акселерация қажет өнімдік командалар мен ЖИ-стартаптарға."
    ),
    "pathway_business_title": "ҚР субсидиялары, жеңілдіктері және қолдау шаралары",
    "pathway_business_note": (
        "Жергілікті талаптар мен өтінім беру тәртібі маңызды жеке кәсіпкерлер мен компанияларға."
    ),
    "pathway_farmer_title": "Агро, мал шаруашылығы және қолданбалы технологиялар",
    "pathway_farmer_note": (
        "Агро, мал шаруашылығы және технология міндеттері бар шаруашылықтар мен агрокомандаларға."
    ),
    "pathway_science_title": "Ғылым, коммерцияландыру және ғылыми гранттар",
    "pathway_science_note": (
        "Зерттеу мен енгізуге қаржы қажет университеттерге, зертханаларға және командаларға."
    ),
    "themes_count": "Карточкалар: {count}",
    "themes_action_open": "Тізімді ашу",
    "themes_empty": "Бұл тақырып бойынша ашық карточкалар әзірге жоқ.",
    "funder_section_eyebrow": "Қорлар мен донорлар",
    "funder_section_title": "Белсенді қорлар мен бағдарламалар",
    "funder_section_description": (
        "Қорлар мен бағдарламалар, олардың бағыттары және ашық мүмкіндіктері."
    ),
    "funder_empty": "Қор профильдері әзірге табылған жоқ.",
    "funder_archive_title": "Архив",
    "funder_archive_empty": "Архивте жазбалар жоқ.",
    "topic_brief_eyebrow": "Қазір назарда",
    "topic_brief_count": "Іріктеуде: {count}",
    "topic_brief_what": "Мұнда әдетте не іздейді",
    "topic_brief_best_for": "Кімге пайдалы болуы мүмкін",
    "topic_brief_reset": "Тақырыпты алып тастау",
    "topic_ai_best": "Өнімдік командаларға, ЖИ-стартаптарға және цифрлық бастамаларға.",
    "topic_ai_focus_1": "ЖИ-пилоттар мен акселераторлар",
    "topic_ai_focus_2": "Бұлттық кредиттер мен инфрақұрылым",
    "topic_ai_focus_3": "Цифрлық дағдылар мен қолданбалы бағдарламалар",
    "topic_agro_best": (
        "Фермерлерге, агрономдарға және су, климат пен салалар тоғысындағы жобаларға."
    ),
    "topic_agro_focus_1": "Субсидиялар мен салалық шаралар",
    "topic_agro_focus_2": "Су, климат және тұрақтылық",
    "topic_agro_focus_3": "Мал шаруашылығы, ветеринария және агротехнологиялар",
    "topic_science_best": "Университеттерге, зертханаларға және зерттеу командаларына.",
    "topic_science_focus_1": "Зерттеулерді коммерцияландыру",
    "topic_science_focus_2": "Ғылыми гранттар, зертханалар және академиялық ұтқырлық",
    "topic_science_focus_3": "Білім беру және университет бағыттары",
    "topic_public_best": (
        "Мемлекеттік сектор, сатып алу және инфрақұрылыммен жұмыс істейтін командаларға."
    ),
    "topic_public_focus_1": "Сатып алулар, тендерлер және ұсыныс сұраулары",
    "topic_public_focus_2": "Даму бағдарламалары мен іске асыру",
    "topic_public_focus_3": "Мемлекеттік технологиялар және ірі жобалық бағыттар",
    "topic_business_best": (
        "Қазақстандағы жеке кәсіпкерлерге, серіктестіктерге және жұмыс істеп тұрған бизнеске."
    ),
    "topic_business_focus_1": "Жергілікті субсидиялар мен ҚР шаралары",
    "topic_business_focus_2": "Жеңілдіктер, кепілдіктер және қаржыландыру",
    "topic_business_focus_3": "ШОБ, экспорт және өсуге арналған қолдау",
    "topic_ngo_best": "ҮЕҰ-ларға, медиаға және әлеуметтік әсері бар азаматтық командаларға.",
    "topic_ngo_focus_1": "Медиа, журналистика және қоғамдық маңызы бар жобалар",
    "topic_ngo_focus_2": "Азаматтық сектор мен серіктестікке арналған гранттар",
    "topic_ngo_focus_3": "Қауымдастықтар және әлеуметтік әсері бар бағдарламалар",
    "theme_ai_title": "ЖИ, бұлттық кредиттер және цифрлық дағдылар",
    "theme_ai_note": (
        "ЖИ бағдарламаларын, инфрақұрылым, кредиттер мен цифрлық бастамаларды іздейтін "
        "командаларға."
    ),
    "theme_agro_kicker": "Агро / вет / эко",
    "theme_agro_title": "Агро, су, климат және қолданбалы сектор",
    "theme_agro_note": (
        "Фермаларға, агрокомандаларға және тұрақтылық, су мен қолданбалы салалар "
        "тоғысындағы жобаларға."
    ),
    "theme_science_title": "Ғылым, білім және коммерцияландыру",
    "theme_science_note": (
        "Гранттар мен зерттеу бағыттары қажет университеттерге, зертханаларға және "
        "білім беру командаларына."
    ),
    "theme_public_title": "Инфрақұрылым, сатып алулар және даму бағдарламалары",
    "theme_public_note": (
        "Мемлекеттік тапсырыс, сатып алулар және ірі даму бағдарламаларымен жұмыс "
        "істейтін командаларға."
    ),
    "theme_business_title": "Субсидиялар, жеңілдіктер және бизнеске қолдау шаралары",
    "theme_business_note": (
        "Жергілікті талаптар мен өтінім беру тетігі маңызды ШОБ пен жұмыс істеп тұрған "
        "компанияларға."
    ),
    "theme_ngo_title": "Медиа, азаматтық сектор және әлеуметтік әсер",
    "theme_ngo_note": (
        "Гранттар мен серіктестік бағыттары қажет ҮЕҰ-ларға, медиаға және қоғамдық жобаларға."
    ),
    "focus_aria": "Өнімнің ағымдағы бағыты",
    "readiness_amount": "Сома",
    "readiness_eligibility": "Талаптар",
    "language_switch": "Интерфейс тілі",
    "nav_aria": "Навигатор бөлімдері",
    "tab_health": "Күйі",
    "metrics_aria": "Жиынтық көрсеткіштер",
    "metric_total": "Индексте",
    "metric_sources": "Дереккөздер",
    "opportunities_description_all": (
        "Қамту мен дереккөздерді тексеруге арналған ашық, тұрақты және архив жазбалары."
    ),
    "search_placeholder": "Атауы, қор, тегтер, өңір",
    "audience_aria": "Өтініш беруші түрі бойынша іріктеу",
    "audience_startup": "Стартаптарға",
    "audience_business": "Бизнеске",
    "audience_farmer": "Фермерлерге",
    "audience_science": "Зерттеушілерге",
    "format_aria": "Қолдау форматы бойынша іріктеу",
    "format_support": "Субсидиялар мен шаралар",
    "format_tenders": "Тендерлер мен сатып алулар",
    "topic_aria": "Бағыт бойынша іріктеу",
    "topic_ai": "ЖИ және цифрлық шешімдер",
    "topic_agro": "Агро / вет / эко",
    "topic_science": "Білім және ғылым",
    "topic_public": "Мемлекеттік сектор және инфрақұрылым",
    "topic_ngo": "Медиа және ҮЕҰ",
    "topic_business": "Бизнес және субсидиялар",
    "scope_aria": "Тізімді қамту",
    "lifecycle_aria": "Мүмкіндік кезеңі",
    "region_aria": "Өтінім беру өңірі",
    "region_kazakhstan": "Қазақстан",
    "deadline_filter_label": "Мерзім",
    "deadline_filter_aria": "Өтінім беру мерзімі",
    "sort_aria": "Мүмкіндіктерді көрсету реті",
    "min_score_aria": "Каталог сәйкестігінің ең төменгі деңгейі",
    "source_label": "Дереккөз",
    "source_aria": "Дереккөз",
    "loading_sources": "Дереккөздер жүктелуде",
    "show_fewer_sources": "Азырақ көрсету",
    "source_refresh_title": "Дереккөздің соңғы сәтті жаңартылуы",
    "source_refresh_value": "Жаңартылды: {date}",
    "source_refresh_unknown": "Жаңарту күні көрсетілмеген",
    "health_title": "Деректер мәртебесі",
    "health_ok_value": "Деректер өзекті",
    "health_attention_value": "Тексеру қажет",
    "health_note_ready": (
        "Витрина тексерілді: {checked_at}. Карточкалардың соңғы жаңартылуы: {updated_at}."
    ),
    "health_note_ready_no_items": (
        "Витрина тексерілді: {checked_at}. Жаңа карточкалар дереккөздер келесі рет "
        "қаралғаннан кейін шығады."
    ),
    "api_online": "Деректер өзекті",
    "api_failed": "Деректерді тексеру қажет",
    "api_error": "Деректерді жүктеу қатесі",
    "showing_sources": "{total} дереккөздің {shown} көрсетілді",
    "sources_connected": "Қосылған дереккөздер: {total}",
    "show_all_sources_with_total": "Барлық {total} дереккөзді көрсету",
    "coverage_unavailable": "Қамту дерегі қолжетімсіз",
    "indexed_count": "Индексте: {count}",
    "relevant_open_count": "Өзекті ашықтары: {count}",
    "direct_badge": "Тікелей",
    "watchlist_badge": "Мониторинг",
    "source_direct_note": "Ресми дереккөзге тікелей қосылу",
    "source_watchlist_note": "Редакциялық тексеруден өтетін мониторинг беті",
    "regional_badge_kazakhstan": "Қазақстан",
    "regional_badge_central_asia": "Орталық Азия",
    "summary_matches": "Сәйкестіктер: {count}",
    "summary_search": "Іздеу: {value}",
    "summary_audience": "Кім үшін: {value}",
    "summary_format": "Формат: {value}",
    "summary_topic": "Тақырып: {value}",
    "summary_lifecycle": "Кезең: {value}",
    "summary_region": "Өңір: {value}",
    "summary_deadline": "Мерзім: {value}",
    "summary_sort": "Сұрыптау: {value}",
    "summary_score": "Сәйкестік: {value}",
    "summary_scope_all": "Архивті қоса",
    "methodology_title": "Қалай жұмыс істейміз",
    "methodology_description": (
        "Карточка дереккөзге апарады, деректер шегін көрсетеді және шешімді адамға қалдырады."
    ),
    "faq_title": "Жиі қойылатын сұрақтар",
    "collections_aria": "Қайта пайдалану үшін сақталған сүзгілер",
    "profile_applied": "Профиль бойынша іріктеу жаңартылды.",
    "saved_view_saved": "Іріктеу осы браузерде сақталды.",
    "saved_view_removed": "Іріктеу өшірілді.",
    "saved_view_shared": "Ағымдағы іріктеу сілтемесі көшірілді.",
    "saved_view_default_name": "Менің іріктеуім",
    "saved_view_remove_aria": "Іріктеуді өшіру",
    "saved_view_status_label": "Іріктеулер мәртебесі",
    "saved_view_share_prompt": "Осы іріктеудің сілтемесін көшіріңіз",
    "mobile_app_navigation": "QAZ.FUND негізгі бөлімдері",
    "mobile_sources": "Дереккөздер",
    "mobile_open_filters": "Каталог сүзгілерін ашу",
    "mobile_close_filters": "Сүзгілерді жабу",
    "saved_opportunity_saved": "Карточка осы браузерде сақталды.",
    "saved_opportunity_removed": "Карточка сақталғандардан өшірілді.",
    "save_opportunity": "Сақтау",
    "unsave_opportunity": "Өшіру",
    "workspace_filter_count": "Сақталған карточкалар: {count}",
    "workspace_filter_empty": "Алдымен карточканы сақтаңыз.",
    "workflow_label": "Жұмыс кезеңі",
    "workflow_review": "Тексеруде",
    "workflow_fit": "Сәйкес келеді",
    "workflow_preparing": "Өтінім дайындалуда",
    "workflow_submitted": "Жіберілді",
    "workflow_result": "Нәтиже алынды",
    "workflow_updated": "Карточка кезеңі жаңартылды.",
    "workspace_action_review": "Талаптарды ресми дереккөзден тексеріңіз.",
    "workspace_action_fit": "Талаптарға және мерзімге сәйкестікті растаңыз.",
    "workspace_action_preparing": (
        "Құжаттар топтамасын жинап, өтінім беру мерзімін белгілеңіз."
    ),
    "workspace_action_submitted": "Растауды сақтап, шарттарды бақылаңыз.",
    "workspace_action_result": "Осы мүмкіндік бойынша нәтижені белгілеңіз.",
    "workspace_deadline_today": "Мерзім бүгін",
    "workspace_deadline_days": "Мерзімге {count} күн қалды",
    "workspace_deadline_date": "Мерзім: {date}",
    "workspace_deadline_rolling": "Тұрақты қабылдау",
    "workspace_exported": "Резервтік көшірме жүктелді.",
    "workspace_imported": "Жұмыс кеңістігі қалпына келтірілді.",
    "workspace_import_error": "Резервтік көшірмені оқу мүмкін болмады.",
    "report_issue": "Деректерді нақтылау",
    "open_source_short": "Дереккөзге өту",
    "view_funder": "Қор профилі",
    "fit_label": "Сәйкестік белгілері",
    "fit_unknown": "Талаптарды тексеру қажет",
    "fit_deadline_soon": "Жақында жабылады",
    "fit_global": "Халықаралық өтінім",
    "signal_label": "Неліктен көрсетілді",
    "card_meta_label": "Параметрлер",
    "signal_support_kz": (
        "Қазақстандағы командалар мен бизнеске арналған қолдау шарасы, өтінім беру "
        "тәртібі түсінікті."
    ),
    "signal_public_sector": (
        "Мемлекеттік сектор, инфрақұрылым және даму бағдарламаларымен жұмыс істейтін "
        "командаларға."
    ),
    "signal_business": "Шарттар, құжаттар және өтінім беру тәртібі маңызды бизнеске сәйкес келеді.",
    "signal_startup": (
        "Акселерация, пилот немесе бұлттық кредит қажет өнімдік және ЖИ-командаларға."
    ),
    "signal_tender": (
        "Қатысушыға қойылатын талаптарды, жұмыс көлемін және өтінім топтамасын тексеріңіз."
    ),
    "signal_science": "Университеттерге, зертханаларға және ғылыми командаларға.",
    "signal_farmer": "Шаруашылықтарға, фермаларға және агрокомандаларға.",
    "signal_ngo": "ҮЕҰ-ларға, медиаға және азаматтық немесе әлеуметтік әсері бар жобаларға.",
    "signal_kazakhstan": (
        "Шарттарда Қазақстан немесе жергілікті өтінім беру тәртібі тікелей көрсетілген."
    ),
    "signal_central_asia": "Бір елмен шектелмей, Орталық Азия жобаларына сәйкес келеді.",
    "signal_global": "Халықаралық мүмкіндік – командаңызға қойылатын талаптарды тексеріңіз.",
    "meta_format_label": "Формат",
    "meta_region_label": "Өңір",
    "meta_deadline_label": "Мерзім",
    "meta_region_kazakhstan": "ҚР басымдықта",
    "meta_region_central_asia": "Орталық Азия",
    "meta_region_global": "Халықаралық",
    "meta_deadline_rolling": "Мерзімсіз",
    "meta_deadline_soon_days": "{count} күннен кейін",
    "meta_deadline_month": "Бір айға дейін",
    "meta_deadline_later": "Бір айдан кейін",
    "detail_source_status_title": "Дереккөз мәртебесі",
    "detail_fit_good": "Сәйкестік белгілері бар",
    "no_indexed_items": "Каталогта әзірге қолжетімді карточкалар жоқ.",
    "no_filtered_items": "Ағымдағы сүзгілер бойынша ештеңе табылмады.",
    "no_filtered_items_hint": "Бір сүзгіні алып тастап, қайта көріңіз.",
    "empty_action_clear": "Барлығын тазарту",
    "empty_action_region": "Барлық өңір",
    "empty_action_deadline": "Кез келген мерзім",
    "empty_action_score": "Базалық шек",
    "empty_action_scope": "Бүкіл каталогты ашу",
    "open_details": "Қысқаша көру",
    "read_more": "Толық карточка",
    "score_title": "Каталог ережелері бойынша сәйкестік; бұл мақұлдау ықтималдығы емес",
    "score_exact": "Жоғары",
    "score_high": "Жақсы",
    "score_base": "Базалық",
    "source_agency": "Дереккөз: {agency}",
    "reload_confirm": "Барлық дереккөзден деректер қайта жүктелсін бе?",
    "results_button": "Тағы көрсету: {count}",
    "unknown_url": "URL қолжетімсіз",
}


KK_PUBLIC_UI_COPY = {
    "api_docs": "API",
    "apply_section_description": (
        "Нақты тәртіпті ұйымдастырушының ресми бетінен тексеріңіз."
    ),
    "apply_section_eyebrow": "Өтінім беру",
    "apply_section_title": "Қалай өтінім беруге болады",
    "attribution_link": "Деректерді пайдалану көзі",
    "breadcrumbs_aria": "Навигация жолы",
    "data_policy_link": "Деректер саясаты",
    "detail_brief_amount": "Сома",
    "detail_brief_application_url": "Өтінім беру сілтемесі",
    "detail_brief_caveat": "Ескерту",
    "detail_brief_deadline": "Мерзім",
    "detail_brief_format": "Формат",
    "detail_brief_heading": "QAZ.FUND – жұмыс анықтамасы",
    "detail_brief_legacy_heading": "QAZ.FUND – жұмыс анықтамасы",
    "detail_brief_official_url": "Ресми сілтеме",
    "detail_brief_region": "Өңір",
    "detail_brief_source": "Дереккөз",
    "detail_brief_summary": "Қысқаша сипаттама",
    "detail_copy_brief": "Қысқаша анықтаманы көшіру",
    "detail_copy_brief_done": "Анықтама көшірілді.",
    "detail_copy_brief_prompt": "Қысқаша анықтама",
    "detail_empty": "Бұл мүмкіндік бойынша қосымша мәлімет жарияланбаған.",
    "detail_expand_source": "Мәтінді ашу",
    "detail_meta_title": "Параметрлер",
    "detail_open_application": "Өтінім беруге өту",
    "detail_open_source": "Ресми дереккөзді ашу",
    "detail_share": "Бөлісу",
    "detail_share_done": "Сілтеме дайын.",
    "detail_share_prompt": "Осы мүмкіндікті бөлісу",
    "detail_source_excerpt": "Бастапқы дереккөзден үзінді",
    "detail_title_fallback": "Қолдау бағдарламасы",
    "footer_disclaimer": (
        "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды. Соңғы шарттарды "
        "әрқашан бастапқы дереккөз бетінен тексеріңіз."
    ),
    "footer_owner": "QAZ.FUND – қолдау мүмкіндіктерінің ашық навигаторы. Жобаны іске асырған",
    "footer_qdev": "qdev.run",
    "funder_archive_note": (
        "Жабылған жазбалар қордың профилі мен бағдарламаларының мерзімін көрсетеді."
    ),
    "funder_archive_title": "Архив",
    "funder_back_to_catalog": "Каталогқа оралу",
    "funder_focus_indexed": "Индексте",
    "funder_focus_note": "Ағымдағы индекстегі форматтар, өңірлер мен тақырыптар.",
    "funder_focus_regions": "Өңірлер",
    "funder_focus_title": "Ағымдағы индекстен не көруге болады",
    "funder_focus_types": "Форматтар",
    "funder_live_empty": "Бұл қор бойынша ашық немесе жоспарланған жазбалар жоқ.",
    "funder_live_note": "Тексеруге болатын ашық, тұрақты және жоспарланған жазбалар.",
    "funder_live_now": "Ашық мүмкіндіктер",
    "funder_live_title": "Ашық мүмкіндіктер",
    "funder_next_deadline": "Ең жақын мерзім",
    "funder_open_card": "Карточканы ашу",
    "funder_open_profile": "Профильді ашу",
    "funder_overview_intro": (
        "Профиль жарияланған бағдарламалар мен хабарландырулар негізінде жасалған."
    ),
    "funder_overview_regions": "Өңірлік бағыт: {regions}.",
    "funder_overview_topics": "Негізгі тақырыптар: {topics}.",
    "funder_overview_types": "Форматтар: {types}.",
    "funder_page_eyebrow": "Қор профилі",
    "funder_sources_note": "Профиль үшін пайдаланылған ресми беттер.",
    "funder_sources_title": "Профиль дереккөздері",
    "funder_total_items": "Индекстегі жалпы саны",
    "insights_link": "Талдау",
    "media_link": "Медиа",
    "lang": "kk",
    "lifecycle_forecast": "Жоспарланған",
    "lifecycle_rolling": "Тұрақты қабылдау",
    "meta_format_label": "Формат",
    "no_summary": "Сипаттама жарияланбаған.",
    "open_rolling": "Тұрақты қабылдау",
    "opportunities_title": "Мүмкіндіктер",
    "prepare_section_description": (
        "Талаптар бағдарламаға қарай өзгереді. Соңғы нұсқаны ресми дереккөзден тексеріңіз."
    ),
    "prepare_section_eyebrow": "Өтінімге дайындық",
    "prepare_section_title": "Не дайындау керек",
    "readiness_note": (
        "Толтырылған өрістер карточканы жылдам бағалауға көмектеседі. Соңғы "
        "шарттарды ресми дереккөзден тексеріңіз."
    ),
    "readiness_title": "Деректердің толықтығы",
    "related_open": "Карточканы ашу",
    "related_reason_theme": "Ұқсас тақырып",
    "related_section_description": "Бір дереккөзге, форматқа немесе бағытқа жақын карточкалар.",
    "related_section_eyebrow": "Көруді жалғастыру",
    "related_section_title": "Ұқсас бағдарламалар",
    "source_catalog_unavailable": "Дереккөздер каталогы уақытша қолжетімсіз.",
    "status_link": "Деректер мәртебесі",
    "tab_opportunities": "Мүмкіндіктер",
    "tab_sources": "Дереккөздер",
    "terms_link": "Пайдалану шарттары",
    "verification_description": (
        "Карточка бастапқы бағалауға арналған. Өтінім берер алдында ресми "
        "дереккөздегі шарттарды қайта тексеріңіз."
    ),
    "decision_check_eyebrow": "Өтінім берер алдында",
    "decision_check_title": "Негізгі шарттар",
    "decision_check_description": (
        "Алдымен ұйымдастырушының парақшасында осы төрт тармақты тексеріңіз."
    ),
    "decision_check_boundary_title": "Маңызды",
    "decision_check_boundary_text": (
        "Карточка іріктеуге көмектеседі; шешім ұйымдастырушының ережелері бойынша қабылданады."
    ),
    "verification_eyebrow": "Өтінім берер алдында",
    "verification_title": "Нені қайта тексеру керек",
    "views_aria": "QAZ.FUND негізгі бөлімдері",
    "workspace_queue_aria": "Сақталған карточкаларға арналған келесі қадамдар",
    "workspace_queue_empty": "Сақталған ашық карточкалар жоқ.",
    "workspace_queue_more": "Тағы карточкалар: {count}",
    "workspace_backup_aria": "Жергілікті жұмысты жүктеу және резервтік көшіру",
    "detail_panel_label": "Мүмкіндік туралы толық мәлімет",
    "detail_error": "Жергілікті сипаттама қолжетімсіз. Төмендегі дереккөзді ашыңыз.",
    "detail_all_opportunities": "Барлық мүмкіндіктер",
    "detail_readiness_complete": "Негізгі {total} өрістің барлығы расталды.",
    "detail_readiness_partial": (
        "{total} өрістің {known} расталды. Дереккөзден мынаны тексеріңіз: {missing}."
    ),
    "detail_compute_readiness": (
        "Деректер толықтығы: {score} / 100, {tier}. Бұл көмекші көрсеткіш, "
        "қатысу құқығы туралы шешім емес."
    ),
    "detail_compute_ready": "дерек жеткілікті",
    "detail_compute_watch": "қайта тексеру қажет",
    "detail_compute_blocked": "шектеулер бар",
    "detail_compute_unknown": "мәртебе белгісіз",
    "verification_eligibility_title": "Қатысу құқығы",
    "verification_eligibility_text": (
        "Өтініш беруші түрін, юрисдикцияны, шектеулерді және талап етілетін тәжірибені тексеріңіз."
    ),
    "verification_terms_title": "Қолданыстағы шарттар",
    "verification_terms_text": (
        "Шарттардың соңғы нұсқасын, мерзімді, соманы және өтінімді жіберу тәсілін тексеріңіз."
    ),
    "verification_procurement_title": "Сатып алу құжаттары",
    "verification_procurement_text": (
        "Тендерлер бойынша лоттарды, біліктілікті, қосымшаларды және өзгерістерді бөлек тексеріңіз."
    ),
    "verification_publication_title": "Дереккөз және тексеру күні",
    "verification_publication_text": "Ресми дереккөзді және тексеру күнін көрсетіңіз.",
    "detail_status_ok": "Сипаттама мен негізгі өрістер ресми дереккөзден жиналды",
    "detail_status_structured_only": "Қысқаша сипаттама мен өрістер көрсетілді",
    "detail_status_blocked": "Дереккөз толық мәтінді автоматты жүктеуге рұқсат бермеді",
    "detail_status_not_allowed": "Бұл дереккөз үшін жергілікті жүктеу өшірілген",
    "detail_status_too_large": "Бет жергілікті оқу үшін тым үлкен",
    "detail_status_unsupported_media": "Дереккөз қолдау көрсетілмейтін формат жіберді",
    "detail_status_parse_error": "Дереккөз бетін дұрыс талдау мүмкін болмады",
    "prepare_eligibility_title": "Талаптарды тексеріңіз",
    "prepare_eligibility_text": (
        "Елді, өтініш беруші түрін, сала бойынша шектеулерді және өтінім тілін салыстырыңыз."
    ),
    "prepare_deadline_title": "Мерзімді белгілеңіз",
    "prepare_deadline_text": (
        "Тіркелу, қол қою, қолдау хаттары мен құжаттарды жүктеуге уақыт қалдырыңыз."
    ),
    "prepare_rolling_title": "Өзектілігін тексеріңіз",
    "prepare_rolling_text": (
        "Тұрақты бағдарламалардың шарттары нақты жабылу мерзімінсіз өзгеруі мүмкін."
    ),
    "prepare_grant_title": "Жоба өтінімін жинаңыз",
    "prepare_grant_text": "Мәселе, шешім, бюджет, команда, нәтиже және іске асыру жоспары қажет.",
    "prepare_tender_title": "Сатып алу топтамасын тексеріңіз",
    "prepare_tender_text": (
        "Жұмыс көлемін, біліктілікті, өтінім формасын, кепілдіктерді және "
        "қосымшаларды салыстырыңыз."
    ),
    "prepare_startup_title": "Жоба таныстырылымын дайындаңыз",
    "prepare_startup_text": (
        "Өнім сипаттамасын, өсу көрсеткіштерін, команданы және пилот сценарийін жинаңыз."
    ),
    "prepare_subsidy_title": "Жергілікті құжаттарды дайындаңыз",
    "prepare_subsidy_text": (
        "ЖК/ЖШС, ЭЦҚ, салық мәртебесі, банк деректері мен растайтын құжаттарды тексеріңіз."
    ),
    "prepare_science_title": "Зерттеу топтамасын жинаңыз",
    "prepare_science_text": (
        "Ғылыми жаңалық, команда, күнтізбелік жоспар, бюджет және коммерцияландыру жолы қажет."
    ),
    "prepare_ngo_title": "Әсер логикасын тексеріңіз",
    "prepare_ngo_text": (
        "Бенефициарларды, әлеуметтік әсерді, серіктестерді және есеп жоспарын айқындаңыз."
    ),
    "prepare_source_title": "Ресми дереккөзді салыстырыңыз",
    "prepare_source_text": (
        "Өтінім берер алдында шарттардың, формалардың және байланыс деректерінің соңғы "
        "нұсқасын тексеріңіз."
    ),
    "apply_step_open_apply_title": "Өтінім беру бетін ашыңыз",
    "apply_step_open_apply_text": (
        "Жеке өтінім формасы болса, одан бастаңыз да, талаптарды осы беттен салыстырыңыз."
    ),
    "apply_step_open_source_title": "Ресми дереккөзді ашыңыз",
    "apply_step_open_source_text": (
        "Дереккөзден қолданыстағы шарттарды, байланыстарды және жіберу форматын тексеріңіз."
    ),
    "apply_step_check_title": "Талаптарды салыстырыңыз",
    "apply_step_check_text": (
        "Елді, ұйым түрін, саланы, жоба жасын және қатысушы шектеулерін тексеріңіз."
    ),
    "apply_step_pack_title": "Топтаманы жинаңыз",
    "apply_step_pack_text": (
        "Жоба сипаттамасын, бюджетті, растайтын құжаттарды және қажет болса қолдау "
        "хаттарын дайындаңыз."
    ),
    "apply_step_submit_title": "Жіберіп, растауды сақтаңыз",
    "apply_step_submit_text": (
        "Жібергеннен кейін өтінім нөмірін, хат көшірмесін немесе растау экранын сақтаңыз."
    ),
    "related_reason_source": "Сол дереккөз",
    "related_reason_funder": "Ұқсас қор",
    "related_reason_format": "Ұқсас формат",
    "detail_meta_labels": {
        "source": "Дереккөз",
        "funder": "Қор",
        "deadline": "Өтінім беру мерзімі",
        "deadline_raw": "Дереккөздегі мерзім",
        "deadline_policy": "Мерзім ережесі",
        "amount": "Қолдау көлемі",
        "amount_raw": "Дереккөздегі көлем",
        "project_id": "Жоба нөмірі",
        "reference": "Хабарландыру нөмірі",
        "status": "Мәртебе",
        "notice_type": "Хабарландыру түрі",
        "borrower": "Қарыз алушы",
        "country": "Ел",
        "region": "Өңір",
        "board_approval": "Кеңес мақұлдауы",
        "closing_date": "Жабылу күні",
        "page_title": "Дереккөз тақырыбы",
        "application_url": "Өтінім беру жолы",
        "status_note": "Жүктеу мәртебесі",
    },
    "detail_missing_labels": {
        "deadline": "мерзім",
        "amount": "соманы",
        "eligibility": "өтініш берушіге қойылатын талаптар",
        "application": "өтінім беру жолы",
    },
}


def _copy_for(lang: str) -> dict[str, object]:
    if lang == "en":
        return cast(dict[str, object], COPY["en"])
    if lang == "kk":
        copy = dict(cast(dict[str, object], COPY["ru"]))
        copy.update(KK_DASHBOARD_COPY)
        copy.update(KK_PUBLIC_UI_COPY)
        copy["lang"] = "kk"
        copy["locale"] = "kk-KZ"
        copy["language_fallback_note"] = (
            "Кейбір бөлімдер мен карточкалардағы мәтін әзірге бастапқы тілде "
            "көрсетіледі. Соңғы шарттарды ұйымдастырушының ресми бетінен тексеріңіз."
        )
        return copy
    return cast(dict[str, object], COPY["ru"])


def dashboard_copy(lang: str) -> dict[str, object]:
    return _copy_for(lang if lang in SUPPORTED_LANGS else "ru")
