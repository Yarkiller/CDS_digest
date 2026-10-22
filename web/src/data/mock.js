/** Mock content mirrored from design-frontend for homework UI. */

export const currentIssue = {
  number: 14,
  period: '17–23 марта 2026',
  title: 'Новости DS для СВА',
  editor: 'Редакция Digest CDS',
  votingOpenUntil: '28 марта 2026',
}

/** Past published issue for archive demo (D-27 / ISSUE-04) — not current. */
export const pastIssue = {
  number: 13,
  period: '10–16 марта 2026',
  title: 'Прошлый выпуск · DS для СВА',
  editor: 'Редакция Digest CDS',
  items: [
    {
      slug: 'sql-dashboards',
      title: 'SQL-дашборды для аудиторской отчётности',
      position: 1,
      format: 'Статья',
      reading_minutes: 9,
      dek: 'Шаблоны витрин и дашбордов для ежемесячной отчётности аналитика СВА.',
    },
    {
      slug: 'prompt-engineering',
      title: 'Prompt Engineering Patterns 2026',
      position: 2,
      format: 'Статья',
      reading_minutes: 7,
      dek: 'Паттерны формулировок запросов к LLM для аудита.',
    },
  ],
}

export const materials = [
  {
    id: 'rag-systems',
    title: 'Building Production RAG Systems',
    dek: 'Как быстро находить нужные фрагменты регламентов СВА без ручного перебора документов.',
    format: 'Статья',
    readingMinutes: 8,
    date: '20 марта 2026',
    provenance: 'внешний текстовый источник',
    cover: '/covers/rag-systems.png',
    roles: ['ds', 'sva'],
    tags: ['RAG', 'LLM'],
    topic: 'ml-search',
    keywords: 'rag llm корпоративн документ поиск',
    snippet: 'Гибридный поиск по корпоративной базе знаний с reranking…',
    inIssue: true,
    issuePosition: 1,
    summary:
      'Статья описывает полный цикл построения RAG-системы для корпоративной базы знаний: ingestion, chunking, embedding, гибридный retrieval и reranking.',
    body: [
      'Для СВА наиболее релевантны сценарии поиска по регламентам, методологиям аудита и внутренним отчётам с цитированием источников.',
      'На этапе поиска система объединяет семантическое совпадение с точным совпадением терминов.',
    ],
    // NAV-01 fixture (test-only, C-02/C-03): the first section stays short (under one
    // viewport) while at least one viewport of prose sits below every target, so the
    // C-00 reachability gate (maxScroll >= headingDocTop) is satisfied, not bypassed.
    body_markdown: [
      '## Введение',
      '',
      'Для СВА наиболее релевантны сценарии поиска по регламентам, методологиям аудита и внутренним отчётам с цитированием источников.',
      '',
      '## Гибридный поиск',
      '',
      'На этапе поиска система объединяет семантическое совпадение с точным совпадением терминов.',
      '',
      'Точное совпадение важно для артикулов, номеров стандартов и редких аббревиатур, которые эмбеддинги размывают. Поэтому оба списка кандидатов объединяются до финального ранжирования, а не после него.',
      '',
      'Веса двух каналов подбираются на размеченной выборке запросов аудиторов. Единая формула для всех типов документов работает хуже, чем отдельные веса для регламентов и для отчётов.',
      '',
      '## Чанкинг',
      '',
      'Документы режутся на фрагменты по границам разделов, а не по фиксированному числу символов. Заголовок раздела остаётся частью фрагмента, иначе поиск теряет контекст, ради которого фрагмент и создавался.',
      '',
      'Слишком крупный фрагмент размывает смысл и ухудшает ранжирование, слишком мелкий теряет связность изложения. Практический ориентир — от трёхсот до шестисот токенов с сохранением структуры исходного текста.',
      '',
      'Таблицы и списки выносятся в отдельные фрагменты с повторением заголовка родительского раздела. Без этого повторения таблица находится по запросу, но не отвечает на него.',
      '',
      '### Перекрытие окон',
      '',
      'Соседние фрагменты перекрываются на небольшую долю, чтобы предложение на границе не терялось. Перекрытие увеличивает индекс, поэтому его размер проверяется отдельным замером стоимости.',
      '',
      '## Эмбеддинги',
      '',
      'Модель эмбеддингов выбирается по качеству на русскоязычных текстах, а не по размеру. Смена модели означает полную переиндексацию, поэтому выбор фиксируется до первого промышленного запуска.',
      '',
      'Векторы нормализуются, а близость считается по косинусу. Это позволяет менять размерность и порог отсечения без пересчёта самих векторов.',
      '',
      'Индекс строится офлайн и обновляется инкрементально при публикации материала. Полная перестройка на каждый новый документ слишком дорога для рабочего контура.',
      '',
      '## Ретривер',
      '',
      'На запрос возвращается ограниченное число кандидатов — обычно от пятидесяти до ста. Дальше работают более дорогие механизмы, и их стоимость ограничена именно этим числом.',
      '',
      'Фильтры по типу документа и дате применяются до поиска, а не после. Иначе кандидаты тратятся на устаревшие версии регламентов, которые аудитор всё равно не откроет.',
      '',
      'Пустой результат не маскируется: интерфейс честно сообщает, что подходящих фрагментов нет. Расширение запроса по синонимам выполняется только по явному запросу пользователя.',
      '',
      '## Реранкинг',
      '',
      'Кросс-энкодер пересчитывает пары «запрос — фрагмент» и меняет порядок кандидатов. Он дороже векторного поиска, поэтому применяется только к первой сотне.',
      '',
      'Порог отсечения подбирается так, чтобы в ответ попадали цитируемые фрагменты, а не похожие по теме. Метрика качества здесь — доля ответов с корректной ссылкой на источник.',
      '',
      'Порядок фрагментов в ответе влияет на доверие читателя сильнее, чем абсолютные оценки. Поэтому первые три позиции проверяются вручную на каждом релизе.',
      '',
      '## Оценка качества',
      '',
      'Набор для оценки собирается из реальных вопросов аудиторов с эталонными ссылками на пункты регламентов. Без эталона метрики измеряют гладкость формулировок, а не пользу.',
      '',
      'Каждый релиз прогоняет один и тот же набор, чтобы сравнение оставалось осмысленным. Изменение набора фиксируется отдельно и не смешивается с изменением модели.',
      '',
      'Отдельно измеряется задержка ответа: медленный поиск возвращает аудитора к ручному перебору. Целевой ориентир — ответ в пределах нескольких секунд на типичный запрос.',
      '',
      'Полнота ответа проверяется по эталонным ссылкам, а не по числу найденных фрагментов. Десять похожих абзацев без нужного пункта регламента считаются провалом.',
      '',
      'Точность проверяется вручную на подвыборке: часть ответов модель формулирует уверенно, но неверно. Такие случаи важнее промахов поиска, потому что их труднее заметить.',
      '',
      'Стабильность оценивается повторным прогоном одного вопроса с переформулировкой. Если ответ меняет смысл от смены падежа, набор помечается как нестабильный.',
      '',
      'Покрытие типов документов отслеживается отдельно для регламентов, методик и внутренних отчётов. Перекос в сторону одного типа документов виден только в разбивке.',
      '',
      'Стоимость одного ответа считается вместе с реранкингом, а не только по векторному поиску. Иначе оптимизация одной стадии переносит расход в соседнюю.',
      '',
      'Ручная проверка первых трёх позиций занимает около получаса на релиз. Это дешевле, чем разбор одного неверного ответа в рабочем контуре.',
      '',
      'Ошибки размечаются по категориям: неверный документ, неверный пункт, верный пункт с неверным выводом. Категории нужны, чтобы правка промпта не считалась универсальным средством.',
      '',
      'Отдельный набор вопросов проверяет отказ: если в базе нет ответа, система обязана это сказать. Уверенный ответ на отсутствующий документ — самый дорогой класс ошибки.',
      '',
      'Результаты прогонов хранятся рядом с версией индекса и версией промпта. Без этой привязки сравнение двух релизов через месяц становится невозможным.',
      '',
      'Метрики публикуются внутри команды, а не только в отчёте релиза. Регулярный просмотр чисел удерживает набор актуальным лучше, чем редкая большая ревизия.',
      '',
      'Раз в квартал набор пересматривается вместе с владельцами регламентов. Устаревшие эталоны тихо занижают качество и создают ложную работу над моделью.',
    ].join('\n'),
    related: [{ slug: 'anomaly-detection', title: 'Anomaly Detection in Audit Pipelines' }],
  },
  {
    id: 'empty-dek-article',
    title: 'Empty Dek Article',
    dek: '',
    format: 'Статья',
    readingMinutes: 3,
    date: '15 марта 2026',
    provenance: '',
    cover: '/covers/rag-systems.png',
    roles: ['ds'],
    tags: [],
    topic: 'ml-search',
    keywords: 'empty dek',
    snippet: 'Fixture for D-36 empty dek.',
    inIssue: false,
    issuePosition: 99,
    summary: '',
    body: ['Fixture body without dek.'],
    body_markdown: '## Section One\n\nFixture prose without an audit dek.',
    related: [],
  },
  {
    id: 'anomaly-detection',
    title: 'Anomaly Detection in Audit Pipelines',
    dek: 'Как вовремя замечать аномалии в аудиторских выборках и сокращать ручную проверку.',
    format: 'Статья',
    readingMinutes: 5,
    date: '18 марта 2026',
    provenance: 'внутренний разбор',
    // null cover for knowledge hit-row degradation (RESEARCH Q2 / KNOW-01)
    cover: null,
    roles: ['analyst', 'sva'],
    tags: ['SQL', 'BI', 'аудит'],
    topic: 'reporting',
    keywords: 'sql дашборд аналитик отчётность bi reporting dashboard anomaly',
    snippet: 'Шаблоны витрин и дашбордов для ежемесячной отчётности аналитика СВА…',
    inIssue: true,
    issuePosition: 2,
    summary: 'Практики выявления аномалий в аудиторских пайплайнах на SQL и BI-витринах.',
    body: [
      'Материал показывает, как сочетать правила DQ и статистические сигналы без тяжёлого ML-стека.',
    ],
  },
  {
    id: 'langgraph-agents',
    title: 'LangGraph Multi-Agent Systems',
    dek: 'Как разделить сложную проверку на шаги с контролем и понятным итогом для аудитора.',
    format: 'Статья',
    readingMinutes: 12,
    date: '19 марта 2026',
    provenance: 'внешний текстовый источник',
    cover: '/covers/langgraph-agents.png',
    roles: ['ds'],
    tags: ['LangGraph', 'LLM'],
    topic: 'agents',
    keywords: 'langgraph агент multi-agent llm',
    snippet: 'Оркестрация агентов для многошаговых задач анализа данных…',
    inIssue: true,
    issuePosition: 3,
    summary: 'Оркестрация агентов для многошаговых проверок с явным контролем состояния.',
    body: ['Черновик для Data Scientist: границы ответственности агентов и точки эскалации.'],
  },
  {
    id: 'pgvector',
    title: 'pgvector for Enterprise Search',
    dek: 'PostgreSQL + pgvector как основа корпоративного семантического поиска.',
    format: 'Статья',
    readingMinutes: 6,
    date: '17 марта 2026',
    provenance: 'внешний текстовый источник',
    cover: '/covers/pgvector.png',
    roles: ['ds', 'sva'],
    tags: ['pgvector', 'RAG'],
    topic: 'ml-search',
    keywords: 'pgvector postgresql семантическ поиск rag',
    snippet: 'PostgreSQL + pgvector как основа корпоративного семантического поиска…',
    inIssue: true,
    issuePosition: 4,
    summary: 'Как поднять семантический поиск на PostgreSQL без отдельного vector DB.',
    body: ['Описаны индексы, ограничения и типовые ошибки эксплуатации в закрытом контуре.'],
  },
  {
    id: 'prompt-engineering',
    title: 'Prompt Engineering Patterns 2026',
    dek: 'Паттерны формулировок запросов к LLM для аудита.',
    format: 'Статья',
    readingMinutes: 7,
    date: '16 марта 2026',
    provenance: 'внешний текстовый источник',
    cover: '/covers/prompt-engineering.png',
    roles: ['analyst', 'sva'],
    tags: ['LLM', 'аудит'],
    topic: 'agents',
    keywords: 'prompt llm аудит формулировк',
    snippet: 'Чек-листы DQ и SQL-проверки полноты витрин перед отчётным циклом…',
    inIssue: true,
    issuePosition: 5,
    summary: 'Паттерны промптов для задач внутреннего аудита.',
    body: ['Фокус на воспроизводимости и проверке цитат, а не на «магии» модели.'],
  },
  {
    id: 'sql-dashboards',
    title: 'SQL-дашборды для аудиторской отчётности',
    dek: 'Шаблоны витрин и дашбордов для ежемесячной отчётности аналитика СВА.',
    format: 'Статья',
    readingMinutes: 9,
    date: '15 марта 2026',
    provenance: 'внутренний гайд',
    cover: '/covers/anomaly-detection.png',
    roles: ['analyst', 'sva'],
    tags: ['SQL', 'BI', 'аудит'],
    topic: 'reporting',
    keywords: 'sql дашборд аналитик отчётность bi',
    snippet: 'Шаблоны витрин и дашбордов для ежемесячной отчётности аналитика СВА…',
    inIssue: false,
    issuePosition: null,
    summary: 'Гайд для Data Analyst: витрины, KPI и контроль сроков отчётности.',
    body: ['Содержит примеры SQL и структуру дашборда цикла аудита.'],
  },
  {
    id: 'analyst-sql-notes',
    title: 'Заметки аналитика по SQL-проверкам',
    dek: 'Короткий материал только для роли Analyst.',
    format: 'Статья',
    readingMinutes: 4,
    date: '14 марта 2026',
    provenance: 'внутренний гайд',
    cover: null,
    roles: ['analyst'],
    tags: ['SQL'],
    topic: 'reporting',
    keywords: 'analyst-only-sql проверки',
    snippet: 'Чек-лист SQL-проверок для роли Analyst без DS-материалов…',
    inIssue: false,
    issuePosition: null,
    summary: 'Fixture: membership role analyst, not ds (KNOW-02).',
    body: ['Только роль analyst.'],
  },
]

export const votingCycle = {
  label: 'Цикл голосования',
  period: '3–16 апреля 2026',
  closesOn: '16 апреля 2026',
  progressRatio: 0.55,
}

export const votingTopics = [
  {
    id: 'llm-audit',
    title: 'LLM для анализа аудиторских данных',
    description: 'Проверка полноты выборок и аномалий в аудиторских данных с помощью LLM.',
    materialsCount: 3,
    votes: 24,
  },
  {
    id: 'rag-corp',
    title: 'RAG в корпоративной среде',
    description: 'Корпоративный RAG: источники, доступы и контроль галлюцинаций.',
    materialsCount: 5,
    votes: 31,
  },
  {
    id: 'automl-risk',
    title: 'AutoML для прогнозирования рисков',
    description: 'AutoML-пайплайны для оценки операционных и кредитных рисков.',
    materialsCount: 0,
    votes: 18,
  },
]

export function getMaterialById(id) {
  return materials.find((item) => item.id === id) ?? null
}

export function getIssueMaterials() {
  return materials
    .filter((item) => item.inIssue)
    .sort((a, b) => a.issuePosition - b.issuePosition)
}

/**
 * Razbory chronology + detail seed for mocks (RAZB-01 / RAZB-02 / D-67 / D-68).
 * Order: meeting_at DESC (newest first) — matches backend list_for_reader.
 * Multi-section published bodies enable sticky TOC; announcement has no prose.
 */
export const razbory = [
  {
    id: 4,
    title: 'RAG в корпоративной среде',
    meeting_at: '2026-04-14T10:00:00.000Z',
    status: 'announcement',
    body_markdown: '',
    notebook_path: null,
  },
  {
    id: 3,
    title: 'LLM для анализа аудиторских данных',
    meeting_at: '2026-03-31T10:00:00.000Z',
    status: 'published',
    body_markdown:
      '## Контекст\n\nКак LLM помогают разбирать аудиторские выборки.\n\n## Подход\n\nЧанкинг, промпты и проверка фактов.\n\n## Итоги\n\nЧто взять в следующий цикл.',
    notebook_path: null,
  },
  {
    id: 2,
    title: 'Anomaly Detection во внутреннем аудите',
    meeting_at: '2026-03-17T10:00:00.000Z',
    status: 'published',
    body_markdown:
      '## Введение\n\nАномалии в проводках и ложные срабатывания.\n\n## Модель\n\nIsolation Forest и пороги.\n\n## Качество\n\n| Метрика | Значение |\n| --- | --- |\n| Precision | 0.82 |\n| Recall | 0.71 |\n',
    notebook_path: 'notebooks/anomaly.ipynb',
  },
  {
    id: 1,
    title: 'Vector Search с pgvector',
    meeting_at: '2026-03-03T10:00:00.000Z',
    status: 'published',
    body_markdown:
      '## Зачем pgvector\n\nСемантический поиск без отдельного движка.\n\n## Схема\n\nHNSW и индексы.\n\n## Практика\n\nКак мы индексируем чанки.',
    notebook_path: null,
  },
]

/** @returns {Array<{ id: number, title: string, meeting_at: string | null, status: string }>} */
export function getRazboryList() {
  return razbory.map((row) => ({
    id: row.id,
    title: row.title,
    meeting_at: row.meeting_at,
    status: row.status,
  }))
}

/**
 * @param {number | string} id
 * @returns {(typeof razbory)[number] | null}
 */
export function getRazborById(id) {
  const numericId = Number(id)
  if (!Number.isFinite(numericId)) return null
  return razbory.find((row) => row.id === numericId) ?? null
}

/** Archive cards: past published only (excludes current — D-31). */
export function getArchiveIssues() {
  return [
    {
      number: pastIssue.number,
      period_label: pastIssue.period,
      title: pastIssue.title,
      material_count: pastIssue.items.length,
    },
  ]
}

/**
 * @param {number} number
 * @returns {import('../services/contentApi.js').IssueDto | null}
 */
export function getIssueByNumber(number) {
  const n = Number(number)
  if (n === currentIssue.number) {
    return {
      number: currentIssue.number,
      period_label: currentIssue.period,
      title: currentIssue.title,
      editor: currentIssue.editor,
      items: getIssueMaterials().map((m) => ({
        slug: m.id,
        title: m.title,
        position: m.issuePosition,
        format: m.format,
        reading_minutes: m.readingMinutes,
        dek: m.dek ?? null,
      })),
    }
  }
  if (n === pastIssue.number) {
    return {
      number: pastIssue.number,
      period_label: pastIssue.period,
      title: pastIssue.title,
      editor: pastIssue.editor,
      items: pastIssue.items.map((item) => ({ ...item })),
    }
  }
  return null
}
