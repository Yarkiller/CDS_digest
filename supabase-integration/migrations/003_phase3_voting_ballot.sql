-- Phase 3 voting ballot seed + open-cycle vote trigger (VOTE-01/03/04, option-a).
-- Idempotent: WHERE NOT EXISTS on topics by (cycle_id, name); insert-only (no table wipes).
-- Shared VM (knowledge-db.ru): apply once via MCP/psql or supabase db push — never reset.
-- Decision locked: option-a — BEFORE INSERT OR UPDATE trigger + application use-case checks.

-- ─── Guard: reject closed-cycle or cross-cycle topic writes (service_role last line) ───
create or replace function public.enforce_votes_open_cycle_and_topic()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1
    from public.voting_cycles vc
    where vc.id = new.cycle_id
      and vc.status = 'open'
  ) then
    raise exception 'votes: cycle % is not open', new.cycle_id
      using errcode = 'check_violation';
  end if;

  if not exists (
    select 1
    from public.topics t
    where t.id = new.topic_id
      and t.cycle_id = new.cycle_id
  ) then
    raise exception 'votes: topic % does not belong to cycle %', new.topic_id, new.cycle_id
      using errcode = 'check_violation';
  end if;

  return new;
end;
$$;

drop trigger if exists votes_enforce_open_and_topic on public.votes;
create trigger votes_enforce_open_and_topic
  before insert or update on public.votes
  for each row
  execute function public.enforce_votes_open_cycle_and_topic();

-- Optional tally helper index (vote counts by topic within a cycle)
create index if not exists votes_cycle_id_topic_id_idx
  on public.votes (cycle_id, topic_id);

-- ─── Topics for the Phase 2 open cycle (mock.js votingTopics titles) ─────────
-- Bind to the seeded window 2026-04-03 … 2026-04-16 when present; else any open cycle.
insert into public.topics (cycle_id, name, description)
select vc.id, v.name, v.description
from public.voting_cycles vc
cross join (
  values
    (
      'LLM для анализа аудиторских данных',
      'Проверка полноты выборок и аномалий в аудиторских данных с помощью LLM. Аудит: границы применимости, воспроизводимость и контроль ложных срабатываний.'
    ),
    (
      'RAG в корпоративной среде',
      'Корпоративный RAG: источники, доступы и контроль галлюцинаций. Аудит: трассируемость цитат, разграничение контуров и журнал обращений к базе знаний.'
    ),
    (
      'AutoML для прогнозирования рисков',
      'AutoML-пайплайны для оценки операционных и кредитных рисков. Аудит: прозрачность признаков, валидация на hold-out и ответственность за модель.'
    )
) as v(name, description)
where vc.status = 'open'
  and (
    (
      vc.opens_at = timestamptz '2026-04-03 00:00:00+00'
      and vc.closes_at = timestamptz '2026-04-16 23:59:59+00'
    )
    or not exists (
      select 1
      from public.voting_cycles preferred
      where preferred.status = 'open'
        and preferred.opens_at = timestamptz '2026-04-03 00:00:00+00'
        and preferred.closes_at = timestamptz '2026-04-16 23:59:59+00'
    )
  )
  and not exists (
    select 1
    from public.topics t
    where t.cycle_id = vc.id
      and t.name = v.name
  );

-- Link materials to LLM + RAG topics (AutoML stays at 0 materials — VOTE-04).
insert into public.topic_materials (topic_id, material_id)
select t.id, m.id
from public.topics t
join public.voting_cycles vc on vc.id = t.cycle_id
cross join (
  values
    ('LLM для анализа аудиторских данных', 'prompt-engineering'),
    ('LLM для анализа аудиторских данных', 'anomaly-detection'),
    ('LLM для анализа аудиторских данных', 'sql-dashboards'),
    ('RAG в корпоративной среде', 'rag-systems'),
    ('RAG в корпоративной среде', 'pgvector'),
    ('RAG в корпоративной среде', 'langgraph-agents'),
    ('RAG в корпоративной среде', 'prompt-engineering'),
    ('RAG в корпоративной среде', 'anomaly-detection')
) as v(topic_name, slug)
join public.materials m on m.slug = v.slug
where t.name = v.topic_name
  and vc.status = 'open'
on conflict (topic_id, material_id) do nothing;
