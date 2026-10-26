# Decisions (from ADRs)

## ADR-0001: Публичный лидерборд активности
- source: docs/adr/0001-public-leaderboard-gamification.md
- status: locked
- decision: Chose a public leaderboard visible to all authenticated users to drive participation in digests, voting, and tests; deferred past v1 (activity collected from v1, leaderboard shown later). Rejected private-only stats and anonymous average comparison for the long-term design.
- scope: public leaderboard, gamification, digests, voting, tests

## ADR-0002: Развёртывание на Cloud.ru и обработка через FoundryModels
- source: docs/adr/0002-cloud-ru-foundrymodels-deployment.md
- status: proposed
- decision: Deploy Digest CDS on a Cloud.ru VM; process YouTube/text via FoundryModels API (transcription/import, summarization, analysis, tagging, embeddings) — not public foreign APIs and not local Whisper on the VM. Video/audio remain external input only; store prepared article and provenance metadata, not media as material.
- scope: Cloud.ru, FoundryModels, Digest CDS, YouTube, ML-pipeline, Whisper

## ADR-0003: Ограничение регистрации двумя доменами
- source: docs/adr/0003-email-domain-restriction.md
- status: proposed
- decision: Registration/login limited to fixed email domains `@sberbank.ru` and `@omega.sbrf.ru` via config; no dynamic admin-managed domain list.
- scope: email domain restriction, registration, sberbank.ru, omega.sbrf.ru

## ADR-0004: Self-hosted Supabase на отдельной VM
- source: docs/adr/0004-self-hosted-supabase-on-vm.md
- status: proposed
- decision: Use self-hosted Supabase (PostgreSQL + pgvector, Auth/Storage/REST) on a separate VM via Docker Compose; reject managed Supabase Cloud and managed PostgreSQL Cloud.ru. Base URL `https://knowledge-db.ru/` and keys are configurable; access encapsulated in `supabase-integration` adapter. Initial schema in `supabase-integration/migrations/001_initial_schema.sql` with RLS on all 18 public tables.
- scope: self-hosted Supabase, VM, Docker Compose, PostgreSQL, pgvector, supabase-integration, knowledge-db.ru
