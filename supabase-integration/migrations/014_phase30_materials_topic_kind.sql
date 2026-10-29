-- Phase 30: persist closed topic_kind on materials (KIND-01, D-01, T-30-06).
-- Additive column + CHECK (text, not ENUM). DROP the live 12-arg
-- persist_draft_and_enqueue, then CREATE the 13-arg function with p_topic_kind.
-- CREATE OR REPLACE with a new argument would leave an overload (T-30-06).
-- Do not edit applied 007/008/009 in place. Shared VM apply is runbook §4l.
-- Idempotent column/check; RPC DROP+CREATE is a one-way arity change.
-- security invoker; revoke public/anon/authenticated; grant execute to service_role only (T-30-04).

alter table public.materials
  add column if not exists topic_kind text not null default 'conceptual';

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'materials_topic_kind_check'
    and conrelid = 'public.materials'::regclass
  ) then
    alter table public.materials
    add constraint materials_topic_kind_check
    check (topic_kind in ('practical', 'conceptual'));
  end if;
end $$;

drop function if exists public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], int);

create function public.persist_draft_and_enqueue(
  p_title text,
  p_dek text,
  p_body_markdown text,
  p_slug text,
  p_reading_minutes int,
  p_provenance_label text,
  p_source_url text,
  p_youtube_video_id text,
  p_source_author text,
  p_source_published_at timestamptz,
  p_roles text[],
  p_topic_kind text default 'conceptual',
  p_batch_size int
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_inserted int := 0;
  v_material_id bigint;
  v_batch_id bigint;
  v_rank int;
  v_item_count int := 0;
  v_slug text;
begin
  if p_batch_size is null or p_batch_size < 1 then
    raise exception 'persist_draft_and_enqueue: p_batch_size must be >= 1'
      using errcode = 'P0001';
  end if;

  insert into public.materials (
    slug,
    title,
    dek,
    body_markdown,
    format,
    status,
    reading_minutes,
    provenance_label,
    source_id,
    roles,
    source_url,
    youtube_video_id,
    source_author,
    source_published_at,
    topic_kind
  ) values (
    p_slug,
    p_title,
    p_dek,
    p_body_markdown,
    'статья', -- format='статья'
    'draft', -- status='draft'
    p_reading_minutes,
    p_provenance_label,
    null,
    -- IN-01 / decision A: RoleKind is closed in Python (normalize_roles).
    -- The RPC dumps already-normalized roles; no CHECK here.
    coalesce(p_roles, '{}'::text[]),
    p_source_url,
    p_youtube_video_id,
    p_source_author,
    p_source_published_at,
    p_topic_kind
  )
  on conflict (youtube_video_id) do nothing;

  get diagnostics v_inserted = row_count;

  select m.id
  into v_material_id
  from public.materials m
  where m.youtube_video_id = p_youtube_video_id;

  if v_material_id is null then
    raise exception 'persist_draft_and_enqueue: material lookup failed'
      using errcode = 'P0001';
  end if;

  -- Conflict: youtube_video_id already exists — return existing shortlist ids, no new item.
  if v_inserted = 0 then
    select si.batch_id, si.rank
    into v_batch_id, v_rank
    from public.digest_shortlist_items si
    join public.digest_shortlist_batches b on b.id = si.batch_id
    where si.material_id = v_material_id
      and b.sent_at is null
    order by b.week_start desc, b.created_at desc
    limit 1;

    -- D-08 / D-09: sent-batch-only shortlist still returns already_saved true.
    if v_batch_id is null then
      select si.batch_id, si.rank
      into v_batch_id, v_rank
      from public.digest_shortlist_items si
      join public.digest_shortlist_batches b on b.id = si.batch_id
      where si.material_id = v_material_id
      order by b.week_start desc, b.created_at desc
      limit 1;
    end if;

    if v_batch_id is null then
      raise exception 'persist_draft_and_enqueue: existing material % has no shortlist row', v_material_id
        using errcode = 'P0001';
    end if;

    -- D-12: stored materials.slug (not caller p_slug); D-09: already_saved true.
    select m.slug
    into v_slug
    from public.materials m
    where m.id = v_material_id;

    return jsonb_build_object(
      'material_id', v_material_id,
      'slug', v_slug,
      'batch_id', v_batch_id,
      'rank', v_rank,
      'already_saved', true
    );
  end if;

  -- New material: pick latest unsent batch. Skip batches where sent_at is not null
  -- (RESEARCH batch_sent fixture — a latest sent batch is not the enqueue target).
  select b.id
  into v_batch_id
  from public.digest_shortlist_batches b
  where b.sent_at is null
  order by b.week_start desc, b.created_at desc
  limit 1
  for update;

  if v_batch_id is not null then
    select count(*)
    into v_item_count
    from public.digest_shortlist_items si
    where si.batch_id = v_batch_id;
  end if;

  if v_batch_id is null or v_item_count >= p_batch_size then
    insert into public.digest_shortlist_batches (week_start)
    values ((date_trunc('week', current_date))::date)
    returning id into v_batch_id;
  end if;

  select coalesce(max(si.rank), 0) + 1
  into v_rank
  from public.digest_shortlist_items si
  where si.batch_id = v_batch_id;

  insert into public.digest_shortlist_items (
    batch_id,
    material_id,
    rank,
    decision
  ) values (
    v_batch_id,
    v_material_id,
    v_rank,
    'pending'
  );

  return jsonb_build_object(
    'material_id', v_material_id,
    'slug', p_slug,
    'batch_id', v_batch_id,
    'rank', v_rank,
    'already_saved', false
  );
end;
$$;

revoke all on function public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], text, int) from public;
revoke all on function public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], text, int) from anon, authenticated;
grant execute on function public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], text, int) to service_role;
