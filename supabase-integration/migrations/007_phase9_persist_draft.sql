-- Phase 9 persist+enqueue: provenance columns, unique youtube_video_id, atomic RPC (D-05, D-06, D-09).
-- Idempotent: add column if not exists, create or replace function, idempotent grants/revokes.
-- Shared VM: apply once via Studio/MCP or supabase db push — never reset.
-- Target (D-09): youtube_video_id text not null unique

-- ─── Provenance columns (nullable first for existing seed rows) ───────────────
alter table materials add column if not exists source_url text not null default '';
alter table materials add column if not exists youtube_video_id text;
alter table materials add column if not exists source_author text not null default '';
alter table materials add column if not exists source_published_at timestamptz;

-- Backfill the Phase 5 demo row before NOT NULL / unique (must_haves).
update public.materials
set
  source_url = coalesce(nullif(source_url, ''), 'https://example.invalid/phase5-admin-draft'),
  youtube_video_id = coalesce(nullif(youtube_video_id, ''), 'phase5-admin-draft'),
  source_author = coalesce(nullif(source_author, ''), 'phase5-seed')
where slug = 'phase5-admin-draft';

-- Remaining legacy rows need distinct youtube_video_id values before UNIQUE.
update public.materials
set
  source_url = coalesce(nullif(source_url, ''), 'https://example.invalid/legacy-' || slug),
  youtube_video_id = coalesce(nullif(youtube_video_id, ''), 'legacy-' || slug),
  source_author = coalesce(nullif(source_author, ''), 'legacy')
where source_url is null
   or source_url = ''
   or youtube_video_id is null
   or youtube_video_id = ''
   or source_author is null
   or source_author = '';

alter table public.materials
  alter column youtube_video_id set not null;

alter table public.materials
  alter column source_url drop default;

alter table public.materials
  alter column source_author drop default;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'materials_youtube_video_id_key'
  ) then
    alter table public.materials
      add constraint materials_youtube_video_id_key unique (youtube_video_id);
  end if;
end
$$;

-- WR-05: ranks must be unique within a batch (idempotent on re-apply).
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'digest_shortlist_items_batch_id_rank_key'
  ) then
    alter table public.digest_shortlist_items
      add constraint digest_shortlist_items_batch_id_rank_key unique (batch_id, rank);
  end if;
end
$$;

-- ─── Atomic persist + enqueue (security invoker; service_role only) ──────────
create or replace function public.persist_draft_and_enqueue(
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
    source_published_at
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
    p_source_published_at
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

    if v_batch_id is null then
      raise exception 'persist_draft_and_enqueue: existing material % has no shortlist row', v_material_id
        using errcode = 'P0001';
    end if;

    return jsonb_build_object(
      'material_id', v_material_id,
      'slug', p_slug,
      'batch_id', v_batch_id,
      'rank', v_rank
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
    'rank', v_rank
  );
end;
$$;

revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from public;
revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from anon, authenticated;
grant execute on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) to service_role;
