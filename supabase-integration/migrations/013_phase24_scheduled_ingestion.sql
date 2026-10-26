-- Phase 24: scheduled ingestion cursor + singleton schedule (ING-05/ING-06, D-06/D-14).
-- Cursor columns live on pipeline_ingest_sources (die with the source).
-- Singleton ingestion_schedule holds enabled/time/days/last_run_at; defaults come
-- from application code when no row exists — do NOT seed id = 1 here (D-14).
-- Idempotent: add-column-if-not-exists + create-table-if-not-exists.
-- No wipe, no reset. Shared VM: apply once via Studio SQL / psql.

alter table public.pipeline_ingest_sources
  add column if not exists last_seen_published_at timestamptz;

alter table public.pipeline_ingest_sources
  add column if not exists last_seen_video_id text;

create table if not exists public.ingestion_schedule (
  id integer primary key default 1 check (id = 1),
  enabled boolean not null default true,
  time_of_day time not null default '06:00',
  days_of_week smallint[] not null default '{1,2,3,4,5,6,7}'::smallint[],
  last_run_at timestamptz,
  updated_at timestamptz not null default now(),
  constraint ingestion_schedule_days_within_iso_week check (
    days_of_week <@ array[1,2,3,4,5,6,7]::smallint[]
    and cardinality(days_of_week) > 0
  )
);

-- Deny-by-default: RLS enabled, NO permissive policy (T-24-10, D-14).
-- Only the service_role client (composition) reaches this table;
-- admin gating for GET/PATCH routes is backend require_admin (Phase 24-05).
alter table public.ingestion_schedule enable row level security;

-- Verify after apply:
-- select column_name, data_type from information_schema.columns
--   where table_name='pipeline_ingest_sources'
--     and column_name in ('last_seen_published_at','last_seen_video_id');
-- select enabled, time_of_day, days_of_week from public.ingestion_schedule;  -- expect 0
-- select relrowsecurity from pg_class where relname = 'ingestion_schedule';  -- expect t
-- select count(*) from pg_policies where tablename = 'ingestion_schedule';   -- expect 0
