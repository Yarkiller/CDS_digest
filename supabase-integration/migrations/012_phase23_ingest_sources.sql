-- Phase 23: admin-managed ingest sources (SRC-01/SRC-03, D-16/D-17).
-- Subscription list for YouTube channel/playlist ids — NOT the fetched-items
-- table public.ingestion_sources from 001 (materials/jobs/texts FK target).
-- Idempotent: create-if-not-exists; unique (kind, source_id) is the concurrency
-- backstop. No wipe, no reset. Shared VM: apply once via Studio SQL / psql /
-- supabase db push when SUPABASE_ACCESS_TOKEN is configured.

create table if not exists public.pipeline_ingest_sources (
  id bigint generated always as identity primary key,
  kind text not null check (kind in ('channel', 'playlist')),
  source_id text not null,
  label text,
  is_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (kind, source_id)
);

-- Deny-by-default: RLS enabled, NO permissive policy (T-23-11, D-17).
-- Only the service_role client (backend composition/live.py) reaches this table;
-- admin gating for the ingest-sources routes is backend require_admin.
alter table public.pipeline_ingest_sources enable row level security;

-- Verify after apply (expect 0+ rows; empty OK):
-- select count(*) from public.pipeline_ingest_sources;
-- select relrowsecurity from pg_class where relname = 'pipeline_ingest_sources';  -- expect t
-- select count(*) from pg_policies where tablename = 'pipeline_ingest_sources';   -- expect 0
