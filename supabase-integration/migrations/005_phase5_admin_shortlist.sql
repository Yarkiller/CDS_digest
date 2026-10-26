-- Phase 5 admin shortlist delivery columns + demo seed (ADMIN-01, D-78, D-87).
-- Idempotent: ADD COLUMN IF NOT EXISTS / WHERE NOT EXISTS; insert-only (no table wipes).
-- Shared VM (knowledge-db.ru): apply once via MCP/Studio SQL or supabase db push — never reset.
-- Live Python path: atomic UPDATE … WHERE sent_at IS NULL RETURNING, then IssueRepository.publish.
-- Optional RPC claim_and_publish_digest for single-transaction claim+publish (RESEARCH A4).

-- ─── Delivery persistence on batches (D-87 / A3) ─────────────────────────────
alter table public.digest_shortlist_batches
  add column if not exists delivery_status text;

alter table public.digest_shortlist_batches
  add column if not exists recipient_count int;

alter table public.digest_shortlist_batches
  add column if not exists published_issue_id bigint
    references public.digest_issues (id) on delete set null;

alter table public.digest_shortlist_batches
  add column if not exists issue_url text;

-- ─── Atomic claim + publish RPC (SECURITY INVOKER; service_role only) ────────
-- Claims unsent batch, inserts digest_issues + items for approved∩ready, stamps delivery.
create or replace function public.claim_and_publish_digest(
  p_batch_id bigint,
  p_sent_at timestamptz,
  p_period_label text,
  p_title text,
  p_delivery_status text default 'stubbed',
  p_recipient_count int default 0
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_batch public.digest_shortlist_batches%rowtype;
  v_issue_id bigint;
  v_issue_number int;
  v_issue_url text;
  v_item_count int := 0;
begin
  update public.digest_shortlist_batches b
  set sent_at = p_sent_at
  where b.id = p_batch_id
    and b.sent_at is null
  returning b.* into v_batch;

  if not found then
    raise exception 'claim_and_publish_digest: batch % already sent or missing', p_batch_id
      using errcode = 'P0001';
  end if;

  select coalesce(max(i.number), 0) + 1 into v_issue_number
  from public.digest_issues i;

  insert into public.digest_issues (number, period_label, title, published_at)
  values (v_issue_number, p_period_label, p_title, p_sent_at)
  returning id into v_issue_id;

  insert into public.digest_issue_items (issue_id, material_id, position)
  select v_issue_id, si.material_id, si.rank
  from public.digest_shortlist_items si
  join public.materials m on m.id = si.material_id
  where si.batch_id = p_batch_id
    and si.decision = 'approved'
    and m.status = 'ready'
  order by si.rank;

  get diagnostics v_item_count = row_count;
  if v_item_count = 0 then
    raise exception 'claim_and_publish_digest: empty approved∩ready pool for batch %', p_batch_id
      using errcode = 'check_violation';
  end if;

  v_issue_url := '/issues/' || v_issue_number::text;

  update public.digest_shortlist_batches
  set
    delivery_status = p_delivery_status,
    recipient_count = coalesce(p_recipient_count, 0),
    published_issue_id = v_issue_id,
    issue_url = v_issue_url
  where id = p_batch_id;

  return jsonb_build_object(
    'batch_id', p_batch_id,
    'issue_id', v_issue_id,
    'issue_number', v_issue_number,
    'issue_url', v_issue_url,
    'delivery_status', p_delivery_status,
    'recipient_count', coalesce(p_recipient_count, 0),
    'item_count', v_item_count
  );
end;
$$;

-- Revoke from PUBLIC / anon / authenticated; grant execute to service_role only (T-05-17).
revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) from public;
revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) from anon, authenticated;
grant execute on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) to service_role;

-- ─── Draft candidate for ADMIN-03 demos (idempotent upsert by slug) ──────────
insert into public.materials (
  slug, title, dek, body_markdown, format, status, reading_minutes,
  provenance_label, roles, published_at
) values (
  'phase5-admin-draft',
  'Phase 5 draft candidate (admin triage)',
  'Черновик для демо Approve/Reject и блокировки send при draft в пуле.',
  E'## Черновик\n\nМатериал намеренно в статусе draft для ADMIN-03 / D-85 демо.',
  'статья',
  'draft',
  3,
  'внутренний демо-сид Phase 5',
  array['ds']::text[],
  null
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
  updated_at = now();

-- ─── Demo unsent shortlist batch (≤5 items; D-78 / ADMIN-01) ─────────────────
-- Honesty comment: demo batch для Phase 5 (seed, not PIPE-01 ranking pipeline).
insert into public.digest_shortlist_batches (week_start, created_at)
select date '2026-09-15', timestamptz '2026-09-15 08:00:00+00'
where not exists (
  select 1
  from public.digest_shortlist_batches b
  where b.week_start = date '2026-09-15'
    and b.sent_at is null
);

insert into public.digest_shortlist_items (
  batch_id, material_id, rank, score, score_factors, decision
)
select
  b.id,
  m.id,
  v.rank,
  v.score,
  v.score_factors::jsonb,
  v.decision::public.shortlist_decision
from public.digest_shortlist_batches b
cross join (
  values
    -- ready + ≥2 factor labels (ADMIN-05 honesty)
    (
      'rag-systems',
      1,
      0.92::numeric,
      '{"релевантность теме недели": 0.9, "качество источников": 0.85, "factors": []}'::text,
      'pending'
    ),
    (
      'pgvector',
      2,
      0.88::numeric,
      '{"практическая применимость": 0.8, "глубина разбора": 0.75}'::text,
      'pending'
    ),
    (
      'anomaly-detection',
      3,
      0.81::numeric,
      '{"релевантность теме недели": 0.7, "качество источников": 0.7}'::text,
      'pending'
    ),
    (
      'sql-dashboards',
      4,
      0.74::numeric,
      '{"практическая применимость": 0.65}'::text,
      'pending'
    ),
    -- draft candidate for ADMIN-03 / D-85 demos
    (
      'phase5-admin-draft',
      5,
      0.40::numeric,
      '{}'::text,
      'pending'
    )
) as v(slug, rank, score, score_factors, decision)
join public.materials m on m.slug = v.slug
where b.week_start = date '2026-09-15'
  and b.sent_at is null
  and not exists (
    select 1
    from public.digest_shortlist_items si
    where si.batch_id = b.id
      and si.material_id = m.id
  );
