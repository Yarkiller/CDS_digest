-- Phase 2 content seed (D-25, D-27): mock.js narrative → published issues + materials.
-- Idempotent: ON CONFLICT upserts on number/slug; insert-only (no table wipes).
-- Shared VM (knowledge-db.ru): apply once via MCP/psql or supabase db push — never reset.

-- ─── Materials (Playwright slugs, format check = статья) ─────
insert into materials (
  slug, title, dek, body_markdown, format, status, reading_minutes,
  provenance_label, roles, published_at
) values
(
  'rag-systems',
  'Building Production RAG Systems',
  'Как быстро находить нужные фрагменты регламентов СВА без ручного перебора документов.',
  E'## Retrieval и reranking\n\nДля СВА наиболее релевантны сценарии поиска по регламентам, методологиям аудита и внутренним отчётам с цитированием источников.\n\nНа этапе поиска система объединяет семантическое совпадение с точным совпадением терминов.',
  'статья',
  'ready',
  8,
  'внешний текстовый источник',
  array['ds', 'sva']::text[],
  timestamptz '2026-03-20 12:00:00+00'
),
(
  'anomaly-detection',
  'Anomaly Detection in Audit Pipelines',
  'Как вовремя замечать аномалии в аудиторских выборках и сокращать ручную проверку.',
  E'## DQ и статистика\n\nМатериал показывает, как сочетать правила DQ и статистические сигналы без тяжёлого ML-стека.',
  'статья',
  'ready',
  5,
  'внутренний разбор',
  array['analyst', 'sva']::text[],
  timestamptz '2026-03-18 12:00:00+00'
),
(
  'langgraph-agents',
  'LangGraph Multi-Agent Systems',
  'Как разделить сложную проверку на шаги с контролем и понятным итогом для аудитора.',
  E'## Оркестрация агентов\n\nЧерновик для Data Scientist: границы ответственности агентов и точки эскалации.',
  'статья',
  'ready',
  12,
  'внешний текстовый источник',
  array['ds']::text[],
  timestamptz '2026-03-19 12:00:00+00'
),
(
  'pgvector',
  'pgvector for Enterprise Search',
  'PostgreSQL + pgvector как основа корпоративного семантического поиска.',
  E'## Индексы и эксплуатация\n\nОписаны индексы, ограничения и типовые ошибки эксплуатации в закрытом контуре.',
  'статья',
  'ready',
  6,
  'внешний текстовый источник',
  array['ds', 'sva']::text[],
  timestamptz '2026-03-17 12:00:00+00'
),
(
  'prompt-engineering',
  'Prompt Engineering Patterns 2026',
  'Паттерны формулировок запросов к LLM для аудита.',
  E'## Воспроизводимые промпты\n\nФокус на воспроизводимости и проверке цитат, а не на «магии» модели.',
  'статья',
  'ready',
  7,
  'внешний текстовый источник',
  array['analyst', 'sva']::text[],
  timestamptz '2026-03-16 12:00:00+00'
),
(
  'sql-dashboards',
  'SQL-дашборды для аудиторской отчётности',
  'Шаблоны витрин и дашбордов для ежемесячной отчётности аналитика СВА.',
  E'## Витрины и KPI\n\nСодержит примеры SQL и структуру дашборда цикла аудита.',
  'статья',
  'ready',
  9,
  'внутренний гайд',
  array['analyst', 'sva']::text[],
  timestamptz '2026-03-15 12:00:00+00'
)
on conflict (slug) do update set
  title = excluded.title,
  dek = excluded.dek,
  body_markdown = excluded.body_markdown,
  format = excluded.format,
  status = excluded.status,
  reading_minutes = excluded.reading_minutes,
  provenance_label = excluded.provenance_label,
  roles = excluded.roles,
  published_at = excluded.published_at,
  updated_at = now();

-- Tags for seeded materials (idempotent PK)
insert into material_tags (material_id, tag_slug, tag_label)
select m.id, t.tag_slug, t.tag_label
from materials m
join (
  values
    ('rag-systems', 'rag', 'RAG'),
    ('rag-systems', 'llm', 'LLM'),
    ('anomaly-detection', 'sql', 'SQL'),
    ('anomaly-detection', 'bi', 'BI'),
    ('anomaly-detection', 'audit', 'аудит'),
    ('langgraph-agents', 'langgraph', 'LangGraph'),
    ('langgraph-agents', 'llm', 'LLM'),
    ('pgvector', 'pgvector', 'pgvector'),
    ('pgvector', 'rag', 'RAG'),
    ('prompt-engineering', 'llm', 'LLM'),
    ('prompt-engineering', 'audit', 'аудит'),
    ('sql-dashboards', 'sql', 'SQL'),
    ('sql-dashboards', 'bi', 'BI'),
    ('sql-dashboards', 'audit', 'аудит')
) as t(slug, tag_slug, tag_label) on m.slug = t.slug
on conflict (material_id, tag_slug) do update set tag_label = excluded.tag_label;

-- Related links (ready → ready only); idempotent PK
insert into material_relations (from_material_id, to_material_id, kind)
select f.id, t.id, 'related'
from materials f
join materials t on t.slug = 'pgvector'
where f.slug = 'rag-systems'
on conflict (from_material_id, to_material_id) do nothing;

insert into material_relations (from_material_id, to_material_id, kind)
select f.id, t.id, 'related'
from materials f
join materials t on t.slug = 'rag-systems'
where f.slug = 'pgvector'
on conflict (from_material_id, to_material_id) do nothing;

-- ─── Digest issues: current №14 + past №13 (D-27) ───────────
insert into digest_issues (number, period_label, title, published_at)
values
  (13, '10–16 марта 2026', 'Архивный выпуск DS', timestamptz '2026-03-10 12:00:00+00'),
  (14, '17–23 марта 2026', 'Новости DS для СВА', timestamptz '2026-03-17 12:00:00+00')
on conflict (number) do update set
  period_label = excluded.period_label,
  title = excluded.title,
  published_at = excluded.published_at;

-- Past issue №13: sql-dashboards only
insert into digest_issue_items (issue_id, material_id, position)
select i.id, m.id, 1
from digest_issues i
join materials m on m.slug = 'sql-dashboards'
where i.number = 13
on conflict (issue_id, material_id) do update set position = excluded.position;

-- Current issue №14: five inIssue materials from mock.js
insert into digest_issue_items (issue_id, material_id, position)
select i.id, m.id, v.position
from digest_issues i
cross join (
  values
    ('rag-systems', 1),
    ('anomaly-detection', 2),
    ('langgraph-agents', 3),
    ('pgvector', 4),
    ('prompt-engineering', 5)
) as v(slug, position)
join materials m on m.slug = v.slug
where i.number = 14
on conflict (issue_id, material_id) do update set position = excluded.position;

-- ─── Voting cycle (ISSUE-02 stub source for 02-05) ───────────
-- No natural unique key: insert once when no overlapping open window exists.
insert into voting_cycles (opens_at, closes_at, status)
select
  timestamptz '2026-04-03 00:00:00+00',
  timestamptz '2026-04-16 23:59:59+00',
  'open'::voting_cycle_status
where not exists (
  select 1
  from voting_cycles vc
  where vc.opens_at = timestamptz '2026-04-03 00:00:00+00'
    and vc.closes_at = timestamptz '2026-04-16 23:59:59+00'
);
