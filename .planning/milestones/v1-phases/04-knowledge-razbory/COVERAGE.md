# API Coverage - Phase 4 Knowledge & Razbory

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Detector fired on RESEARCH Environment table naming **FoundryModels API** (query embeddings).
> Phase 4 does **not** integrate Foundry HTTP — deterministic `QueryEmbedder` + seeded 1024-d vectors (RESEARCH Open Q1 / A3).
> Live data path is self-hosted **Supabase** (service_role PostgREST / SQL RPC) via FastAPI — same composition pattern as Phases 2–3.
> SPA never calls Supabase Data API or Foundry; Bearer JWT → FastAPI only.

## FoundryModels (query / chunk embeddings)

| capability | decision | reason |
|---|---|---|
| Live HTTP embed of search queries | OPT-OUT | not needed yet — no client in `data-collection`; deterministic stub + seed vectors (RESEARCH A3) |
| Live HTTP embed of material chunks at index time | OPT-OUT | not needed yet — seed embeddings in migration `004`; Foundry remains post–Phase 4 |
| DTO / dim contract `EMBEDDING_DIM=1024` reuse | INTEGRATE | Stub + seed must match schema `vector(1024)` |

## Supabase Auth (SPA - publishable client)

| capability | decision | reason |
|---|---|---|
| signInWithPassword / getSession / signUp | INTEGRATE | Inherited Phases 1–3 — JWT required for knowledge/razbor GETs |
| Auth Admin / OAuth / MFA / password reset | OPT-OUT | explicitly out of scope — unchanged |

## PostgREST / Database (service_role - composition/live.py only)

| capability | decision | reason |
|---|---|---|
| knowledge_chunks select + hybrid search (HNSW `<=>` + `content_tsv` / RPC) | INTEGRATE | KNOW-01…04 — `SupabaseKnowledgeChunkRepository.search` |
| materials select join for ready + roles filter | INTEGRATE | Role chips / hit presentation; ready-only |
| razbors select list + get by id | INTEGRATE | RAZB-01…04 — `SupabaseRazborRepository` |
| Idempotent seed `004_phase4_knowledge_razbory.sql` | INTEGRATE | Chunks+embeddings, published/announcement/overview razbors, notebook_path |
| Hybrid search SQL function / RPC (if PostgREST cannot express fusion) | INTEGRATE | Adapter-owned; parameterized only |
| profiles / activity_events / issues / votes | INTEGRATE | Inherited — unchanged live wiring |
| Storage buckets for notebooks | OPT-OUT | explicitly out of scope — `NOTEBOOK_ROOT` + FastAPI `FileResponse` (RESEARCH A5) |
| Realtime subscribe | OPT-OUT | explicitly out of scope for Phase 4 |
| Edge Functions invoke | OPT-OUT | explicitly out of scope for Phase 4 |
| SPA direct `.from(table)` knowledge/razbor reads | OPT-OUT | never — FastAPI Bearer only; razbors lack browser SELECT RLS |
| Destructive TRUNCATE / db reset | OPT-OUT | never on shared VM |

## Notes

- Secrets: `SUPABASE_SECRET_KEY` only in `composition/live.py`; never `VITE_`.
- Notebook bytes: authenticated `GET /razbory/{id}/notebook` with path containment under `NOTEBOOK_ROOT` — not public StaticFiles.
- Assumption-delta scan for phase 4: **no-change** (detector `detected: false`).

## Specless unclassified probe dispositions

Auto-generated `_edge_coverage4.json` entries with `category: unclassified` for KNOW-01 / KNOW-03 / KNOW-04 / RAZB-02 / RAZB-04 have no additional edge beyond the requirement text already planned. Disposition: **N/A — resolved as covered by existing plans** (not deferred features).

| Requirement | Disposition | Covered by |
|-------------|-------------|------------|
| KNOW-01 unclassified | N/A | 04-01/04-02 Submit+blank+no-score; 04-09 e2e gate |
| KNOW-03 unclassified | N/A | 04-03 DS filter → `/materials/{slug}`; 04-09 e2e gate |
| KNOW-04 unclassified | N/A | 04-03 zero-hit honesty + «Сбросить фильтр»; 04-09 e2e gate |
| RAZB-02 unclassified | N/A | 04-06 sticky TOC; 04-09 e2e gate |
| RAZB-04 unclassified | N/A | 04-06 content_kind quality/overview; 04-09 e2e gate |

Classified probes (KNOW-02 empty/encoding, RAZB-01 adjacency/empty/ordering, RAZB-03 concurrency) remain explicit ASSUMPTIONs in plan `must_haves` — not unclassified.
