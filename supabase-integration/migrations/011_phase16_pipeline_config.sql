-- Phase 16: PIPE-01 MVP pipeline config singleton (PIPE-01/PIPE-02/PIPE-03, D-08).
-- Singleton row id = 1 holds the raw YAML document + last-saved timestamp (D-08/D-11).
-- Idempotent: create-if-not-exists; the primary key + CHECK enforce the single row.
-- No wipe, no reset. Shared VM: apply once via Studio SQL / psql / supabase db push.

create table if not exists public.pipeline_config (
  id integer primary key default 1 check (id = 1),
  yaml text not null default '',
  updated_at timestamptz not null default now()
);

-- Deny-by-default: RLS enabled, NO permissive policy (T-16-10, RESEARCH Pitfall 7).
-- Only the service_role client (backend composition/live.py) reaches this table;
-- admin gating for the GET/PUT routes is backend require_admin (D-10).
alter table public.pipeline_config enable row level security;

-- Verify after apply (expect 0 or 1):
-- select count(*) from public.pipeline_config;
-- select relrowsecurity from pg_class where relname = 'pipeline_config';  -- expect t
-- select count(*) from pg_policies where tablename = 'pipeline_config';   -- expect 0
