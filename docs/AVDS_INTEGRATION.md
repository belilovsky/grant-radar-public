# Связь с AV DS 4

QAZ.FUND формирует страницы на сервере через FastAPI и не зависит в рабочей
среде от React-пакета `@sgeo/ui-kit`. Связь с AV DS 4.7.0 обеспечивает локальный
адаптер в `api/avds.py`; канонический каталог компонентов находится на
`https://avds.digital`. Публичный release contract фиксирует выпуск 4.7.0 и
ревизию `aa91d2ec56c64d56df3270b805f7d0d18ed84246`, проверенные 25 августа
2026 года. Его UI contract отдельно указывает пакет `@sgeo/ui-kit` 4.7.0.
QAZ.FUND не импортирует этот пакет в runtime: совместимость обеспечивает
проверяемый SSR-адаптер. `ui.qdev.run`
перенаправляет на тот же канонический адрес.

- The root document declares `data-avds="grant-radar"` and
  `data-av-theme="light"`.
- `api/avds.py` exposes the local AV DS token subset used by this dashboard:
  color, spacing, radius, shadow, motion and typography variables.
- The local token subset also includes product-density primitives for this
  operational surface: dashboard container width, compact/regular control
  heights, card padding, section gap and a shared focus ring.
- The adapter follows the AV DS 4 semantic token roles used in the shared UI kit
  where this static FastAPI surface needs them: `--font-sans`, `--font-serif`,
  `--font-mono`, `--button-outline`, `--badge-outline`, `--shadow-*`,
  `--radius`, `--motion-*`, and semantic border aliases.
- Dashboard CSS maps the local AV DS variables into the shared semantic names
  used by the rest of the QDev ecosystem: `--color-bg`, `--color-surface`,
  `--color-text`, `--color-border`, `--color-accent`, `--color-success`,
  `--color-warning`, and `--color-danger`.
- Public story pages use the same tokens for AV DS data visualizations: the
  `/insights` page renders source-grounded SVG bar charts for formats, donors,
  deadlines, freshness and match quality. Opportunity pages expose a compact
  `opportunity-readiness-meter` showing which application facts are present.
- The dashboard keeps AV DS as a restrained admin surface: `TabsList` /
  `TabsTrigger` tab anatomy, `avds-field`-style inputs, `StatKpiCard`-style
  metric typography, `SourceCard` source rows with the real
  `avds-source-card__icon/body/name/meta/arrow` anatomy, compact document rows,
  visible keyboard focus and a reduced-motion fallback.
- Rendered controls expose `data-avds-component` markers for smoke tests and
  future migration: `admin-shell`, `toolbar`, `button`, `panel`, `metric-card`,
  `field`, `source-card`, `source-icon`, `source-main`, `source-meta`,
  `source-url`, `source-count`, `opportunity-card`, `badge`, `tag`, `score`,
  `health-card`, `sticky-shell`, `filter-summary`, and `DataViz`.
- `scripts/production_smoke.py` treats the AV DS shell markers as part of the
  live release gate, so production deploys fail smoke if the rendered page
  loses `data-avds="grant-radar"`, `data-av-theme="light"`, the default
  Russian shell markers, or the current AV DS component markers.
- `/.well-known/avds-ui-contract.json` publishes the machine-readable AV DS 4
  compatibility boundary. It intentionally reports
  `direct_package_import: false` through the ecosystem manifest; the SSR adapter
  must not be mistaken for a React package import.
- The runtime-neutral `@av/patterns` contracts adopted from AV DS are
  `EvidenceSummary`, `FilterStateSummary` and `DecisionSummary`. Their live
  instances are marked with `data-avds-pattern`; the Python service continues
  to own rendering, filtering, localization and all relevance calculations.

Корневой документ содержит признаки `data-avds="grant-radar"` и
`data-av-theme="light"`. Адаптер определяет используемые цвета, интервалы,
скругления, тени, движение, типографику, плотность элементов и общий стиль
фокуса. Семантические переменные AV DS связаны с переменными интерфейса
QAZ.FUND, поэтому визуальные роли сохраняются без копирования исходного кода
React-компонентов.

Рабочие элементы обозначены атрибутом `data-avds-component`. Проверка выпуска
контролирует оболочку, поля, кнопки, панели, показатели, карточки источников,
состояния, быстрые ссылки и сводную полосу показателей. Машиночитаемая граница
опубликована в `/.well-known/avds-ui-contract.json`; значение
`direct_package_import: false` честно указывает на серверный адаптер, а не на
прямой импорт React-пакета.

QAZ.FUND использует `QuickLinksRail`, `PublicSummaryStrip`, `TrustStrip`,
`TrustFactsPanel`, `EditorialLeadRail`, `LiteReadingSurface` и `DocumentCard`.
Центр данных использует `DataQualityScorecard`, `Progress`, `Table`, `Card`,
`Alert` и `Button`. Рабочее место заявки собирается из `FormField`,
`TextInput`, `Textarea`, `Checkbox`, `Progress`, `Card`, `Alert` и `Button`.
Общие контракты `@av/patterns` охватывают `EvidenceSummary`,
`FilterStateSummary`, `DecisionSummary`, `EvidenceDisclosure` и `ActionPath`;
их рабочие экземпляры отмечены атрибутом `data-avds-pattern`.

Главная страница следует модели компактного рабочего каталога: один сильный
первый экран, спокойная полоса доверия, плотные фильтры и карточки без вложенных
служебных панелей. Страница программы использует редакционный первый экран и
единую полосу чтения. Точные выдержки из первоисточника раскрываются по запросу,
а расширенные сведения не конкурируют с условиями и действиями пользователя.

Диаграммы, журнал изменений, машинные точки входа и рабочее место заявки
остаются композициями QAZ.FUND. Они обозначены `data-avds-pattern`, но не
выдаются за отдельные компоненты пакета AV DS. Это соответствует границе
системы: аналитика и прикладное поведение принадлежат продукту, а AV DS задаёт
переменные, состояния и базовые элементы.

`EvidenceDisclosure` и `ActionPath` появились в QAZ.FUND и затем были
перенесены в AVDS как независимые от React шаблоны. Точная ревизия обмена
закреплена в публичном контракте.

## Почему адаптер остается локальным

QAZ.FUND работает как компактная служба Python в контейнере. Загрузка закрытых
пакетов интерфейса при выпуске потребовала бы учетных данных реестра и усложнила
бы воспроизводимость сборки. Локальный адаптер сохраняет визуальный договор с
AV DS без новой зависимости рабочей среды.

Переход на прямой пакет оправдан только после появления независимого от
прикладной среды набора стилей AV DS, пригодного для образа Python. До этого
соответствие подтверждают семантические роли, карта компонентов, проверки
разметки, настольная и мобильная визуальная проверка и контроль рабочего сайта.

## Что намеренно не переносится

Поиск в PostgreSQL и выпущенные средства QazStack остаются основой каталога:
памятный поисковый модуль не обеспечит ту же выборку и разбиение на страницы.
QAZ.FUND также сохраняет проверенное расписание обновлений и журнал запусков.
Общие формы, уведомления и вход пользователя не подключаются, пока на публичном
сайте нет соответствующих процессов.

Так AV DS отвечает за повторно используемое представление, а QAZ.FUND – за
данные, правила продукта, безопасность и выпуск.
