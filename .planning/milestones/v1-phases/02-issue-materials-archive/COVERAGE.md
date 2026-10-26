# API Coverage — Supabase (Content read path)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Phase 2 integrates self-hosted Supabase on the shared VM for published issues + materials (D-20, D-25).
> Surfaces: FastAPI JWT-gated content APIs; service_role PostgREST adapters in `composition/live.py` only.
> SPA does **not** call Supabase Data API for content — Bearer → FastAPI only (D-20).

## Supabase Auth (SPA — publishable client)

| capability | decision | reason |
|---|---|---|
| signInWithPassword / getSession / signUp | INTEGRATE | Inherited Phase 1 — login/register still required for content reads |
| Auth Admin / OAuth / MFA / password reset | OPT-OUT | explicitly out of scope — unchanged from Phase 1 |

## PostgREST / Database (service_role — composition/live.py only)

| capability | decision | reason |
|---|---|---|
| digest_issues select (latest published, by number, list past) | INTEGRATE | ISSUE-01 / ISSUE-04 — SupabaseIssueRepository |
| digest_issue_items select (ordered TOC) | INTEGRATE | ISSUE-01 / ISSUE-04 — items on issue DTOs |
| materials select by slug (ready-only) | INTEGRATE | MAT-01 — SupabaseMaterialRepository.get_by_slug |
| material_tags / material_relations select | INTEGRATE | MAT-02 honesty fields on material reader DTO |
| voting_cycles select (read-only stub) | INTEGRATE | ISSUE-02 — open/closed callout source on current issue |
| profiles / activity_events | INTEGRATE | Inherited Phase 1 — `/me` + ping still live |
| votes cast / change / ballot write | OPT-OUT | not needed yet — Phase 3 Voting Cycle |
| materials write / admin publish | OPT-OUT | not needed yet — Phase 5 Admin Digest Publish |
| Realtime subscribe | OPT-OUT | explicitly out of scope for Phase 2 |
| Storage upload/download | OPT-OUT | explicitly out of scope for Phase 2 |
| Edge Functions invoke | OPT-OUT | explicitly out of scope for Phase 2 |
| SPA direct `.from(table)` content reads | OPT-OUT | never — SPA uses FastAPI Bearer only (D-20) |

## Seed / ops (shared VM)

| capability | decision | reason |
|---|---|---|
| Idempotent SQL seed `002_phase2_issue_seed.sql` | INTEGRATE | D-25 / D-27 — applied once via MCP PostgREST insert |
| Destructive TRUNCATE / db reset | OPT-OUT | never on shared VM (D-25) |

## Notes

- Secrets: publishable key in SPA; `SUPABASE_SECRET_KEY` / service_role only in server composition (T-01-06).
- Load-failure UX is first-party FastAPI/network splash — not a Supabase SDK surface.
