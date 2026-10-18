-- Digest CDS initial schema: ingestion → publication → knowledge (pgvector) → editorial
-- Embedding dimension defaults to 1024 (FoundryModels; adjust when model is locked).

create extension if not exists vector;
create extension if not exists pg_trgm;

-- Roles for profiles
do $$ begin
  create type app_role as enum ('employee', 'analyst', 'ds', 'admin');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type material_status as enum ('draft', 'ready');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type ingestion_status as enum ('pending', 'running', 'succeeded', 'failed');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type shortlist_decision as enum ('pending', 'approved', 'rejected');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type voting_cycle_status as enum ('open', 'closed');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type razbor_status as enum ('announcement', 'published');
exception when duplicate_object then null;
end $$;

-- Auth profile (Supabase auth.users id)
create table if not exists profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  role app_role not null default 'employee',
  display_name text,
  created_at timestamptz not null default now()
);

-- ─── Ingestion ───────────────────────────────────────────────
create table if not exists ingestion_sources (
  id bigint generated always as identity primary key,
  source_system text not null,
  external_id text not null,
  canonical_url text,
  title text,
  channel_id text,
  published_at timestamptz,
  view_count bigint,
  metadata jsonb not null default '{}'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now(),
  status ingestion_status not null default 'pending',
  unique (source_system, external_id)
);

create table if not exists ingestion_jobs (
  id bigint generated always as identity primary key,
  source_id bigint not null references ingestion_sources (id) on delete cascade,
  stage text not null,
  status ingestion_status not null default 'pending',
  error_code text,
  model_id text,
  pipeline_version text,
  started_at timestamptz,
  finished_at timestamptz
);

create index if not exists ingestion_jobs_source_id_idx on ingestion_jobs (source_id);

create table if not exists source_texts (
  id bigint generated always as identity primary key,
  source_id bigint not null unique references ingestion_sources (id) on delete cascade,
  text text not null,
  language text not null default 'ru',
  content_sha256 text not null,
  model_id text,
  created_at timestamptz not null default now()
);

-- ─── Publication ─────────────────────────────────────────────
create table if not exists materials (
  id bigint generated always as identity primary key,
  slug text not null unique,
  title text not null,
  dek text not null default '',
  body_markdown text not null,
  format text not null default 'статья' check (format = 'статья'),
  status material_status not null default 'draft',
  reading_minutes int not null default 0 check (reading_minutes >= 0),
  provenance_label text not null,
  source_id bigint references ingestion_sources (id) on delete set null,
  roles text[] not null default '{}',
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists materials_status_idx on materials (status);
create index if not exists materials_roles_gin on materials using gin (roles);

create table if not exists material_tags (
  material_id bigint not null references materials (id) on delete cascade,
  tag_slug text not null,
  tag_label text not null,
  primary key (material_id, tag_slug)
);

create table if not exists material_relations (
  from_material_id bigint not null references materials (id) on delete cascade,
  to_material_id bigint not null references materials (id) on delete cascade,
  kind text not null default 'related',
  primary key (from_material_id, to_material_id),
  check (from_material_id <> to_material_id)
);

create table if not exists digest_issues (
  id bigint generated always as identity primary key,
  number int not null unique,
  period_label text not null,
  title text not null,
  published_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists digest_issue_items (
  issue_id bigint not null references digest_issues (id) on delete cascade,
  material_id bigint not null references materials (id) on delete restrict,
  position int not null check (position > 0),
  primary key (issue_id, material_id),
  unique (issue_id, position)
);

create table if not exists digest_shortlist_batches (
  id bigint generated always as identity primary key,
  week_start date not null,
  created_at timestamptz not null default now(),
  sent_at timestamptz
);

create table if not exists digest_shortlist_items (
  batch_id bigint not null references digest_shortlist_batches (id) on delete cascade,
  material_id bigint not null references materials (id) on delete restrict,
  rank int not null check (rank > 0),
  score numeric,
  score_factors jsonb not null default '{}'::jsonb,
  decision shortlist_decision not null default 'pending',
  decided_by uuid references profiles (id),
  decided_at timestamptz,
  primary key (batch_id, material_id)
);

-- ─── Knowledge (atomic chunks + vector + FTS) ────────────────
create table if not exists knowledge_chunks (
  id bigint generated always as identity primary key,
  material_id bigint not null references materials (id) on delete cascade,
  chunk_index int not null check (chunk_index >= 0),
  heading text,
  content_md text not null,
  content_tsv tsvector generated always as (
    to_tsvector('simple', coalesce(heading, '') || ' ' || content_md)
  ) stored,
  embedding vector(1024) not null,
  embedding_model_id text not null,
  content_sha256 text not null,
  created_at timestamptz not null default now(),
  unique (material_id, chunk_index)
);

create index if not exists knowledge_chunks_material_id_idx on knowledge_chunks (material_id);
create index if not exists knowledge_chunks_tsv_gin on knowledge_chunks using gin (content_tsv);
-- HNSW requires sufficient rows in production; create for search readiness.
create index if not exists knowledge_chunks_embedding_hnsw
  on knowledge_chunks using hnsw (embedding vector_cosine_ops);

-- ─── Voting / razbor / activity ──────────────────────────────
create table if not exists voting_cycles (
  id bigint generated always as identity primary key,
  opens_at timestamptz not null,
  closes_at timestamptz not null,
  status voting_cycle_status not null default 'open',
  check (closes_at > opens_at)
);

create table if not exists topics (
  id bigint generated always as identity primary key,
  cycle_id bigint not null references voting_cycles (id) on delete cascade,
  name text not null,
  description text not null default ''
);

create index if not exists topics_cycle_id_idx on topics (cycle_id);

create table if not exists topic_materials (
  topic_id bigint not null references topics (id) on delete cascade,
  material_id bigint not null references materials (id) on delete cascade,
  primary key (topic_id, material_id)
);

create table if not exists votes (
  cycle_id bigint not null references voting_cycles (id) on delete cascade,
  user_id uuid not null references profiles (id) on delete cascade,
  topic_id bigint not null references topics (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (cycle_id, user_id)
);

create table if not exists razbors (
  id bigint generated always as identity primary key,
  topic_id bigint not null references topics (id) on delete restrict,
  title text not null,
  body_markdown text not null default '',
  meeting_at timestamptz,
  status razbor_status not null default 'announcement',
  notebook_path text,
  created_at timestamptz not null default now()
);

create table if not exists activity_events (
  id bigint generated always as identity primary key,
  user_id uuid references profiles (id) on delete set null,
  kind text not null,
  entity_type text,
  entity_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists activity_events_user_id_idx on activity_events (user_id);
create index if not exists activity_events_created_at_idx on activity_events (created_at);

-- ─── RLS ─────────────────────────────────────────────────────
alter table profiles enable row level security;
alter table ingestion_sources enable row level security;
alter table ingestion_jobs enable row level security;
alter table source_texts enable row level security;
alter table materials enable row level security;
alter table material_tags enable row level security;
alter table material_relations enable row level security;
alter table digest_issues enable row level security;
alter table digest_issue_items enable row level security;
alter table digest_shortlist_batches enable row level security;
alter table digest_shortlist_items enable row level security;
alter table knowledge_chunks enable row level security;
alter table voting_cycles enable row level security;
alter table topics enable row level security;
alter table topic_materials enable row level security;
alter table votes enable row level security;
alter table razbors enable row level security;
alter table activity_events enable row level security;

-- Authenticated users: read ready materials and their chunks
create policy materials_select_ready on materials
  for select to authenticated
  using (status = 'ready');

create policy knowledge_chunks_select_ready on knowledge_chunks
  for select to authenticated
  using (
    exists (
      select 1 from materials m
      where m.id = knowledge_chunks.material_id and m.status = 'ready'
    )
  );

create policy digest_issues_select on digest_issues
  for select to authenticated
  using (true);

create policy digest_issue_items_select on digest_issue_items
  for select to authenticated
  using (true);

create policy votes_select_own on votes
  for select to authenticated
  using (user_id = auth.uid());

create policy votes_insert_own on votes
  for insert to authenticated
  with check (user_id = auth.uid());

create policy votes_update_own on votes
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy profiles_select_own on profiles
  for select to authenticated
  using (id = auth.uid());
