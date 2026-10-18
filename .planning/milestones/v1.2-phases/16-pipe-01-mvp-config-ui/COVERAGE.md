# API Coverage — Phase 16 (no external API integration)

No external API integration: internal FastAPI route plus the existing Supabase platform behind the PipelineConfigRepository port; no new external API, SDK, or third-party service.

Phase 16 adds an admin-only pipeline-config YAML surface backed by an internal FastAPI route (`GET`/`PUT /admin/pipeline/config`) and a Supabase singleton row behind the existing `PipelineConfigRepository` port.

Evidence:
- `node gsd-core/bin/lib/api-coverage.cjs --json` over the Phase 16 ROADMAP scope → `{"detected": false, "signals": []}`.
- The only new runtime dependency is `pyyaml` (a local parser library, not an API), added behind a package-legitimacy checkpoint.
- `SupabasePipelineConfigRepository` is an adapter for the project's existing Postgres/Supabase platform, reached through the `supabase_integration` workspace package — the same integration already covered by earlier phases, not a new external API surface.
