---
last_mapped_commit: 252c024622021ec59fe22abdd251c2047849d1da
---
<!-- refreshed: 2026-09-27 -->
# Codebase Concerns

**Analysis Date:** 2026-09-27

## Tech Debt

**Ingestion CLI spine only partially landed (Phase 7 scaffold):**
- Issue: `ingestion-service/` is a workspace member with URL parse, `IngestError`, error mappers, and proxy-aware client factories — but no Typer/`__main__` one-shot, no pipeline orchestration, no LLM/persist stages, and no Supabase writers. Requirements CLI-01…CLI-05 remain open.
- Files: `ingestion-service/src/ingestion_service/` (no `__main__.py`, no `pipeline/`), `ingestion-service/pyproject.toml`, `.planning/REQUIREMENTS.md` (CLI-01…05), `.planning/STATE.md` (Phase 7 complete → plan Phase 8)
- Impact: Admin shortlist still depends on seeded/demo drafts; operators cannot run YouTube→draft end-to-end; `Stage` Literal already advertises `consistency`/`llm`/`llm_truncation`/`persist` with no production mappers.
- Fix approach: Phase 8+ DeepSeek/LLM adapters → Phase 9/10 persist + Typer CLI wiring composition → ports only; keep domain free of SDKs.

**`data-collection` YouTube adapters exist; Foundry/LLM still absent (cross-package note):**
- Issue: Prior map claimed “DTO-only” for YouTube — Phase 7 added real caption/oEmbed adapters behind ports in `data-collection` (out of this remap path). Foundry/DeepSeek LLM + embed clients and draft persist remain unrealized. Schema tables `ingestion_*` / `source_texts` still have no application writers from this package.
- Files: `ingestion-service/` (consumes ports via future wiring only today), `data-collection/` (adapters — not re-verified in this scoped remap), `.planning/PROJECT.md`
- Impact: PIPE-01 ranking pipeline and ADR-0002 FoundryModels path still unrealized for production content.
- Fix approach: Land LLM ports/adapters → CLI persist via Supabase material/shortlist adapters; do not fake PIPE-01 scores.

**Live knowledge search uses StubQueryEmbedder, not FoundryModels:**
- Issue: `build_live_container()` wires `StubQueryEmbedder` (sha256→1024-d). Seeded chunk embeddings in migration 004 match the stub algorithm — semantic search is honesty-path, not production ML.
- Files: `backend/src/backend/composition/live.py`, `backend/src/backend/application/ports/query_embedder.py`, `supabase-integration/migrations/004_phase4_knowledge_razbory.sql`
- Impact: Replacing stub with a real embedder without reindexing yields nonsense rankings; claiming “pgvector semantic search” overstates capability.
- Fix approach: Add Foundry (or DeepSeek) `QueryEmbedder` adapter; reembed all chunks; keep stub for unit/demo only.

**Digest mail is stub-only; SMTP fails fast:**
- Issue: `resolve_mailer("smtp")` raises at startup; live send returns `delivery_status=stubbed` and logs body. Product “send” is editorial claim+publish honesty, not email delivery.
- Files: `backend/src/backend/infrastructure/stub_mailer.py`, `backend/src/backend/composition/settings.py` (`mailer`), `.planning/PROJECT.md` (Out of Scope)
- Impact: Operators may believe digests were emailed; recipients never receive mail.
- Fix approach: Implement SmtpMailer behind `Mailer` port with secrets in env; keep stub as default until verified.

**Default composition is in-memory; live is env-opt-in:**
- Issue: `APP_CONTAINER` defaults to `memory`; `VITE_USE_MOCKS` defaults to true. Misconfigured “prod-like” runs silently use fakes.
- Files: `backend/src/backend/composition/settings.py`, `backend/src/backend/interface/http/app.py` (`resolve_container`), `web/src/services/authEnv.js`, `.env.example`
- Impact: Green local demos that never touch Supabase; false confidence in adapters.
- Fix approach: Fail-fast when `APP_CONTAINER=live` missing secrets (already); document runbook as sole live path; consider refusing `memory` when `ENV=production`.

**Dual frontend surfaces still coexist:**
- Issue: Static prototype `design-frontend/` (incl. large `design-frontend/scripts/app.js`) coexists with React `web/`. Spec keeps design as mockup reference; React is deliverable.
- Files: `design-frontend/`, `web/`, `package.json` (`serve:design`, `test:design`), `docs/digest-cds/technical_specification.md`
- Impact: Feature drift; agents editing the wrong tree; duplicate Playwright projects.
- Fix approach: Treat `design-frontend/` as read-only; all product changes in `web/`; eventually archive static tree.

**Manual schema apply on shared VM; no Compose/migrate CLI for app DB:**
- Issue: Migrations `001`–`006` applied via Studio/MCP/`psql` “once”; no Docker Compose/Dockerfile for app+API; README still points at Studio for `001`.
- Files: `supabase-integration/README.md`, `docs/agents/local-platform-runbook.md`, `supabase-integration/migrations/*.sql`
- Impact: Shared `knowledge-db.ru` drift risk; destructive reset forbidden; `006` apply noted pending in runbook while code already calls new RPC signature.
- Fix approach: Versioned migrate checklist with applied stamps; optional local Postgres+pgvector for offline; never reset shared VM.

**Publishable Supabase client constructed but unused in live wiring:**
- Issue: `create_publishable_client(...)` runs when key present, result discarded; all adapters use `service_role`.
- Files: `backend/src/backend/composition/live.py`
- Impact: Dead construction; future user-scoped RLS path not exercised; service_role blast radius is the only live path.
- Fix approach: Either remove unused call or wire user-JWT clients for least-privilege reads.

**`list_all` remains on KnowledgeChunkRepository:**
- Issue: Port still requires `list_all()`; live search correctly uses RPC `search`, but `list_all` can dump entire embedding table via service_role.
- Files: `backend/src/backend/application/ports/knowledge_chunk_repository.py`, `supabase-integration/src/supabase_integration/knowledge_chunk_repository.py`
- Impact: Accidental use-case regression reintroduces O(n) Python hybrid search / full-table fetch.
- Fix approach: Deprecate/remove `list_all` from production adapters; keep only on in-memory fake if needed for tests.

**Role vocabulary split (`sva` vs `employee`):**
- Issue: Material `roles` / Foundry `RoleHint` include `'sva'`; `app_role` enum is `'employee'|'analyst'|'ds'|'admin'`. Knowledge filter allowlist is only `analyst|ds`.
- Files: `data-collection/src/data_collection/dto/foundry.py`, `supabase-integration/migrations/001_initial_schema.sql`, `backend/src/backend/application/use_cases/search_knowledge.py`, seed SQL in `002`/`004`
- Impact: Mapping bugs when ingestion writes roles; UI must never send `sva` as filter (already rejected).
- Fix approach: Document single glossary; map `sva`→audience tag on materials only; never conflate with `profiles.role`.

**`ingestion-service` depends on `data-collection` only; SDK imports are transitive:**
- Issue: `composition/clients.py` imports `httpx` and `youtube_transcript_api` directly, but `ingestion-service/pyproject.toml` lists only `data-collection`. Runtime works via workspace transitive deps; packaging/isolation is fragile.
- Files: `ingestion-service/pyproject.toml`, `ingestion-service/src/ingestion_service/composition/clients.py`
- Impact: Standalone install of `ingestion-service` alone may miss SOCKS extras or pin drift; dependency graph opaque to auditors.
- Fix approach: Declare explicit `httpx[socks]` / `youtube-transcript-api` (or re-export factory from `data-collection` public API) before CLI shipping.

**Ingestion Settings is proxy-only (CLI-05 env split deferred):**
- Issue: `Settings` exposes only `YOUTUBE_PROXY_URL`; no DeepSeek/Supabase/service_role fields, no package-local `.env` loader yet.
- Files: `ingestion-service/src/ingestion_service/composition/settings.py`, `.planning/REQUIREMENTS.md` (CLI-05)
- Impact: Fine for Phase 7; Phase 8–10 will concentrate secrets here — risk of copying backend env patterns incorrectly.
- Fix approach: Grow Settings + dedicated `.env` per CLI-05; never read secrets in adapters (D-17 already enforced).

## Known Bugs

**Hybrid search RPC scores all chunks (no ANN prefilter):**
- Symptoms: `search_knowledge_chunks` CTE scans `knowledge_chunks` with `<=>` + `ts_rank` without HNSW/IVF candidate cut; fine for seed size, degrades as corpus grows.
- Files: `supabase-integration/migrations/004_phase4_knowledge_razbory.sql`
- Trigger: Corpus growth beyond demo seeds.
- Workaround: Seed-sized data only; add `ORDER BY embedding <=> query LIMIT k` / HNSW ops before hybrid blend.

**Vote tally path loads wide tables into Python:**
- Symptoms: `SupabaseVoteRepository.list_topics_with_counts` selects all `topic_materials` and cycle votes, then counts in process — correct but chatty.
- Files: `supabase-integration/src/supabase_integration/vote_repository.py`
- Trigger: Large topic graphs / many votes.
- Workaround: Acceptable for homework scale; replace with SQL `GROUP BY` / view.

**Vote CAS timestamp format fragility:**
- Symptoms: Upsert CAS retries alternate ISO forms (`Z` vs `+00:00`) because PostgREST/timestamptz string equality is brittle — empty update → `VoteConflictError`.
- Files: `supabase-integration/src/supabase_integration/vote_repository.py` (`upsert_vote`)
- Trigger: Cross-client timestamp serialization differences.
- Workaround: Dual-format retry already present; prefer DB-side CAS RPC long-term.

**Migration 006 vs shared VM apply lag:**
- Symptoms: Python `SupabaseDigestPublisher` expects `claim_and_publish_digest(..., p_material_ids)`; runbook marks 006 apply as pending.
- Files: `supabase-integration/migrations/006_claim_publish_material_ids.sql`, `supabase-integration/src/supabase_integration/digest_publisher.py`, `docs/agents/local-platform-runbook.md`
- Trigger: Live admin send against VM without 006.
- Workaround: Apply 006 once via Studio/`psql` before live publish UAT; confirm RPC signature.

**Default mock SPA can mask live regressions:**
- Symptoms: Playwright honesty suites and default Vite env run under `VITE_USE_MOCKS=true`; live FE↔BE smoke remains human-gated.
- Files: `web/src/services/authEnv.js`, `tests/*.spec.js`, `.planning/PROJECT.md` (Known debt)
- Trigger: CI/local green while live wiring broken.
- Workaround: Explicit runbook live proof (`VITE_USE_MOCKS=false` + `APP_CONTAINER=live`).

**Deferred YouTube URL forms rejected until later phase:**
- Symptoms: `/live/`, `/v/`, `/e/` paths raise `InvalidYouTubeUrl` (intentional D-02 allowlist) — operators pasting those URLs get fail-closed errors, not silent accept.
- Files: `ingestion-service/src/ingestion_service/url.py`, `tests/unit/test_extract_video_id.py`
- Trigger: Live-stream or legacy embed URLs.
- Workaround: Convert to `watch?v=` / bare id; extend allowlist when product asks.

## Security Considerations

**Resolved in `ingestion-service` (Phase 7 CR/WR fixes, 2026-09-27):**
- **CR-01 / WR-02:** Diagnostic envelopes no longer embed raw credentialed URLs. `InvalidYouTubeUrl` strips userinfo via `_safe_url_for_diagnostics`; `map_url_error` / captions / metadata mappers use context allowlists; messages built from reason + `video_id` only. Coverage in `tests/unit/test_ingest_error.py`, `test_captions_error_mapping.py`, `test_metadata_error_mapping.py`. Commits per `07-REVIEW-FIX.md`: `8e2162a`, `2c06275`.
- **Related adapter fixes (data-collection, not re-audited here):** WR-01 Cookie/SDK catch-all, WR-03 snippet join, WR-04 oEmbed 5xx/429→network, WR-05 malformed `language_code` — see `07-REVIEW-FIX.md`.

**Proxy URL must stay out of operator JSON:**
- Risk: `YOUTUBE_PROXY_URL` may contain SOCKS credentials; accidental inclusion in `IngestError.context` would leak to CLI stdout when Phase 10 emits `to_dict()`.
- Files: `ingestion-service/src/ingestion_service/composition/settings.py`, `mapping/captions.py`, `mapping/metadata.py` (`_CONTEXT_ALLOWLIST`)
- Current mitigation: Allowlists exclude proxy/env keys; unit tests assert credentialed proxy strings absent from mapped context.
- Recommendations: Keep allowlists when adding llm/persist mappers; never dump `Settings` into error context.

**Service-role backend bypasses RLS for all product I/O:**
- Risk: Live adapters use `create_service_role_client`; RLS policies protect only direct PostgREST/authenticated clients. A compromised API process = full DB. Future ingestion CLI persist will likely also use service_role (same blast radius class).
- Files: `backend/src/backend/composition/live.py`, `supabase-integration/src/supabase_integration/*.py`, `supabase-integration/migrations/001_initial_schema.sql`
- Current mitigation: Secrets only in server env (never `VITE_`); JWT + corporate email gate on HTTP deps; admin gated via `profiles.role` not JWT claim (`deps.require_admin`).
- Recommendations: Minimize service_role surface; prefer SECURITY DEFINER RPCs with explicit checks; never expose secret key to browser; isolate ingestion CLI env (CLI-05).

**RLS policy coverage still incomplete for product tables:**
- Risk: Policies cover ready materials/chunks, digests, own votes, own profile SELECT. Authenticated clients lack SELECT on `topics`, `voting_cycles`, `razbors`, `material_tags`, shortlist, etc.
- Files: `supabase-integration/migrations/001_initial_schema.sql` (RLS ~240–297), `supabase-integration/README.md`
- Current mitigation: Default-deny for anon; app reads go through FastAPI + service_role.
- Recommendations: If browser ever talks PostgREST directly, add least-privilege policies first; keep privileged writes server-side.

**`votes_update_own` policy alone does not check cycle open:**
- Risk: RLS UPDATE allows own row without `voting_cycles.status = 'open'`.
- Files: `supabase-integration/migrations/001_initial_schema.sql`, `supabase-integration/migrations/003_phase3_voting_ballot.sql` (`enforce_votes_open_cycle_and_topic`)
- Current mitigation: DB trigger enforces open cycle + topic∈cycle; use-case `cast_vote` also checks cycle status.
- Recommendations: Keep trigger + use-case; do not rely on RLS alone if user JWT ever writes votes.

**SPA session in Supabase localStorage (accepted XSS→token theft):**
- Risk: Default supabase-js persistence stores access tokens in browser storage; XSS can exfiltrate.
- Files: `web/src/services/supabaseClient.js`, `web/src/services/authApi.js`, `.planning/milestones/v1-phases/01-platform-foundation-auth/01-SECURITY.md` (AR-01-09)
- Current mitigation: Accepted risk for Phase 1; domain gate; sanitize `returnUrl` (`authEnv.sanitizeReturnUrl`).
- Recommendations: httpOnly BFF session when threat model tightens; strict CSP; never put secret key in Vite.

**Self-hosted Supabase attack surface:**
- Risk: Team owns hardening/backups for `knowledge-db.ru`; open Studio or leaked service_role is catastrophic.
- Files: `docs/adr/0004-self-hosted-supabase-on-vm.md`, `docs/agents/local-platform-runbook.md`
- Current mitigation: Architectural intent to encapsulate access in `supabase-integration` + backend composition.
- Recommendations: Network-restrict Studio/API; rotate keys; policy/RPC regression tests.

**Notebook path containment depends on NOTEBOOK_ROOT config:**
- Risk: Mis-set `NOTEBOOK_ROOT` to overly broad filesystem expands readable files for authenticated users who know relative paths (after resolve checks).
- Files: `backend/src/backend/infrastructure/local_notebook_storage.py`, `backend/src/backend/composition/settings.py`
- Current mitigation: Rejects absolute paths and `..` parts; resolves under root.
- Recommendations: Keep root to a dedicated notebooks tree; prefer object storage later.

## Performance Bottlenecks

**Knowledge hybrid SQL without ANN shortlist:**
- Problem: Full-chunk hybrid scoring in `search_knowledge_chunks` (see Known Bugs).
- Files: `supabase-integration/migrations/004_phase4_knowledge_razbory.sql`
- Cause: Correctness-first Phase 4 RPC over seed data.
- Improvement path: HNSW/IVF candidate retrieval then re-rank with FTS blend; tune `result_limit`.

**Ballot snapshot rebuild after every vote:**
- Problem: `cast_vote` always re-fetches full ballot (topics + counts + personal) after upsert.
- Files: `backend/src/backend/application/use_cases/cast_vote.py`, `get_ballot.py`
- Cause: D-52 honesty snapshot contract.
- Improvement path: Acceptable at current scale; cache tallies or return upsert DTO if load grows.

**Client mock delays add artificial latency:**
- Problem: Mock voting/knowledge paths use `delay()` for UX demos.
- Files: `web/src/utils/delay.js`, `web/src/services/votingApi.js`, `web/src/services/knowledgeApi.js`
- Cause: Prototype honesty harness.
- Improvement path: No-op delay in CI; keep only for local demos.

**Ingestion I/O latency not yet a product path:**
- Problem: No CLI pipeline; caption/metadata fetches only exercised in unit/integration stubs. Live YouTube + future LLM will dominate wall time once wired.
- Files: `ingestion-service/src/ingestion_service/composition/clients.py` (`_DEFAULT_TIMEOUT = 30.0`)
- Cause: Phase 7 composition-only scope.
- Improvement path: Timeouts/retries at composition; fail-closed stages already planned; measure after Phase 10 one-shot.

## Fragile Areas

**Schema / migration contract tests are substring presence checks:**
- Files: `tests/unit/test_schema_migration_contract.py`, `tests/unit/test_phase5_migration_005.py`
- Why fragile: Renames, broken policies, or missing indexes can still “pass”; no live DB apply in CI.
- Safe modification: Change migration then update assertions; add integration migrate+query job before trusting prod.
- Test coverage: Unit contract + offline adapter stubs; no RLS matrix against live DB.

**Embedding dimension + stub algorithm locked across layers:**
- Files: `data-collection/src/data_collection/dto/foundry.py` (`EMBEDDING_DIM = 1024`), migration `vector(1024)`, `StubQueryEmbedder`, seed SQL comments
- Why fragile: Model or dim change requires coordinated migration + reindex + seed rewrite.
- Safe modification: Confirm production embedder before writing real vectors; plan alter+reembed runbook.
- Test coverage: DTO length validator; stub determinism in knowledge tests.

**`design-frontend/scripts/app.js` monolith:**
- Files: `design-frontend/scripts/app.js`
- Why fragile: Large imperative script; easy regressions when syncing UX to React.
- Safe modification: Prefer implementing behavior in `web/`; treat static JS as reference.
- Test coverage: Playwright `tests/design-frontend.spec.js` (separate project).

**Mock harness window flags are sticky global state:**
- Files: `web/src/services/votingApi.js`, `knowledgeApi.js`, `meApi.js`, `authApi.js`
- Why fragile: Playwright/reloads depend on `window.__DIGEST_*__`; leakage between tests if reset missed.
- Safe modification: Always call reset helpers in `beforeEach`; avoid production builds reading harness flags.
- Test coverage: Spec files arm/clear harnesses; fragile if new flags added without cleanup.

**Shared VM migration discipline:**
- Files: `docs/agents/local-platform-runbook.md`
- Why fragile: Human “apply once” stamps; MCP `raw_sql` needs `POSTGRES_URL` many operators lack.
- Safe modification: Record applied date/method in runbook after each file; never wipe.
- Test coverage: None automated against VM.

**`IngestError.Stage` ahead of pipeline implementation:**
- Files: `ingestion-service/src/ingestion_service/domain/errors.py`, `mapping/` (url/captions/metadata only)
- Why fragile: Seven stages locked in Literal; only three mappers exist. Callers can invent `stage="llm"` strings without mapper symmetry tests.
- Safe modification: Add mapper + reason frozenset + unit table per new stage before CLI emits that stage; keep `to_dict()` contract stable.
- Test coverage: `test_ingest_error.py` asserts Literal membership; no end-to-end stage sequencing test yet.

**URL parser allowlist vs product URL drift:**
- Files: `ingestion-service/src/ingestion_service/url.py`
- Why fragile: Host/path allowlist is explicit; YouTube product URL changes or music.youtube.com will fail closed until code updates.
- Safe modification: Extend accept matrix + parametrized tests together; never substring-match hosts.
- Test coverage: Strong unit matrix in `test_extract_video_id.py`; no live URL corpus.

**Composition client factories close responsibility on callers:**
- Files: `ingestion-service/src/ingestion_service/composition/clients.py`
- Why fragile: `build_httpx_client` returns open `AsyncClient`; tests must `aclose()`. Future CLI must use context managers or leak FDs under retries.
- Safe modification: Prefer `async with` in pipeline; document ownership at composition boundary.
- Test coverage: Settings/client unit tests close clients; no pipeline lifecycle test.

## Scaling Limits

**Knowledge retrieval:**
- Current capacity: Seed-sized chunk sets + stub embeddings.
- Limit: Full hybrid scan + stub vectors break usefulness and latency as chunk count grows.
- Scaling path: Real embedder + ANN prefilter; optional partition by material status.

**Voting tallies:**
- Current capacity: Fine for homework topic counts.
- Limit: Python aggregation over all topic_materials/votes rows.
- Scaling path: Aggregate SQL; materialized tallies if needed.

**Activity / leaderboard:**
- Current capacity: `activity_events` + platform ping writers exist; public leaderboard deferred (ADR-0001).
- Limit: Unbounded inserts without retention once instrumentation expands.
- Scaling path: Indexes on `user_id`/`created_at` exist; define retention before UI.

**Admin digest send:**
- Current capacity: Stub mailer + atomic claim RPC (post-006).
- Limit: Real SMTP/batch recipients not implemented; no async worker.
- Scaling path: Queue + SmtpMailer; keep claim+publish atomic.

**Ingestion throughput:**
- Current capacity: No production CLI; unit-level adapters only.
- Limit: One-shot sequential YouTube→LLM→persist will be rate-limited by YouTube bot challenges and LLM quotas once Phase 10 ships.
- Scaling path: Optional proxy (`YOUTUBE_PROXY_URL`); batch/queue deferred; CAP-02 fail-closed writes zero rows on caption failure (persist spy Phase 9/10).

## Dependencies at Risk

**FoundryModels / DeepSeek (Cloud.ru contour):**
- Risk: External ML pipeline for transcript/summary/tags/embeddings (ADR-0002); v1.1 temporarily bends toward DeepSeek captions MVP — no LLM client code in `ingestion-service` yet.
- Impact: Draft material generation blocked after captions; NFR-A3 degradation path unimplemented.
- Migration plan: Stable ports; swap provider adapter without touching domain; wire secrets only in ingestion composition.

**YouTube transcript + oEmbed (via composition clients):**
- Risk: Unofficial `youtube-transcript-api` + public oEmbed; bot challenges / IP blocks common; proxy optional via `YOUTUBE_PROXY_URL`.
- Impact: CAP-01 fail-closed on blocked/empty captions; operators need SOCKS on restricted networks.
- Migration plan: Keep adapters in `data-collection`; inject ready clients from `ingestion-service` composition; integration stubs under `tests/integration/`.

**Self-hosted Supabase + pgvector:**
- Risk: Single shared VM; operator-applied migrations; SDK pinned only in `supabase-integration`.
- Impact: Outage or schema drift blocks all live proof.
- Migration plan: Keep adapters in one package; document backup/rotate; avoid managed-cloud divergence (ADR-0004).

**No CI pipeline:**
- Risk: No `.github/workflows` detected; quality depends on local `npm test` / `uv run pytest`.
- Impact: Broken main can land unnoticed; Playwright browsers via postinstall only.
- Migration plan: Add CI for unit + Playwright web project; optional live smoke as manual/gated job.

**Supabase Auth email confirmation / signup mail deferred:**
- Risk: Self-service signup UX depends on Auth dashboard config; signup mail out of milestone scope.
- Impact: Live registration friction / incomplete onboarding.
- Migration plan: Document Studio Auth settings in runbook; defer product mail.

## Missing Critical Features

**Content ingestion end-to-end (v1.1 remaining):**
- Problem: Phase 7 delivered URL→`video_id`, `IngestError` envelope, captions/metadata error mapping, and proxy composition — not the Typer one-shot, LLM draft generation, or DB persist/shortlist enqueue.
- Blocks: Fresh weekly content without manual SQL/seed; CLI-01 success print contract; PIPE-01 honesty vs demo seed (D-78).
- Partial: CAP-01/CAP-02 unit contracts green; live zero-row persist spy deferred Phase 9/10 (D-14).

**Production embeddings + SMTP:**
- Problem: Stub embedder + StubMailer in live container.
- Blocks: Real semantic search and email delivery NFRs.

**Local/prod parity tooling:**
- Problem: No app Dockerfile/Compose; migrate-by-operator only.
- Blocks: Repeatable onboarding without shared VM access.

**httpOnly session / BFF:**
- Problem: Deferred past Phase 1 security acceptance.
- Blocks: Stronger XSS resistance for corporate deployment.

## Test Coverage Gaps

**No live Supabase / RLS integration suite in CI:**
- What's not tested: Real PostgREST+RLS deny/allow, migration apply on ephemeral DB, end-to-end live FE↔BE under `VITE_USE_MOCKS=false`.
- Files: `tests/unit/test_supabase_*_contract.py` (offline stubs), `tests/*.spec.js` (mostly mocks)
- Risk: Green unit suite with broken production path or unapplied 006.
- Priority: High before claiming production readiness

**Ingestion pipeline E2E still absent; package unit surface exists:**
- What's tested: `extract_video_id` accept/reject matrix, `IngestError.to_dict()`, url/captions/metadata mappers + redaction, Settings/proxy client factories (`tests/unit/test_extract_video_id.py`, `test_ingest_error.py`, `test_captions_error_mapping.py`, `test_metadata_error_mapping.py`, `test_ingestion_settings.py`).
- What's not tested: Typer CLI exit codes/JSON stdout, LLM truncation stage, persist writers, CAP-02 live `persist.calls == []` spy, consistency stage, full URL→draft happy path.
- Files: Planned Phases 8–10; optional `tests/integration/test_youtube_oembed_live.py` (network/proxy)
- Risk: First real CLI lands with thin regression net beyond Stage 7 contracts.
- Priority: High for v1.1 Phases 8–10

**Auth domain restriction covered in unit; live Auth edge cases thin:**
- What's tested: `is_allowed_corporate_email`, JWT verify unit, Playwright auth under mocks.
- What's thin: Live signup confirmation, lockout, JWKS rotation failures.
- Files: `tests/unit/test_auth_email_domain.py`, `tests/unit/test_jwt_verify.py`, `tests/auth.spec.js`
- Priority: Medium (raise when live Auth is default)

**Performance / load:**
- What's not tested: Hybrid search latency at corpus scale; concurrent vote CAS; admin send under contention; ingestion under YouTube rate limits.
- Priority: Medium (post-seed / post-CLI)

---

*Concerns analysis: 2026-09-27*
