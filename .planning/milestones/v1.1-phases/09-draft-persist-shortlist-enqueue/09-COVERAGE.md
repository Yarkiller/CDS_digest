# Phase 9 API Coverage Matrix

**Phase:** 09-draft-persist-shortlist-enqueue  
**External API/SDK/service:** Supabase (PostgREST/Postgres RPC via `supabase-py`)  
**Detected integration verbs:** persist, enqueue, RPC  
**Decision date:** 2026-09-27

| Capability | Decision | Reason |
|---|---|---|
| Service-role `create_client` (SUPABASE_SECRET_KEY) | INTEGRATE | Required for RLS-bypass writes to `materials`, `digest_shortlist_batches`, and `digest_shortlist_items` from the ingestion CLI. |
| Postgres RPC `persist_draft_and_enqueue(...)` | INTEGRATE | Atomic persist + enqueue boundary (D-05, D-06); replaces multiple SDK calls that would risk orphan rows. |
| Schema migration / `supabase db push` for `007_phase9_persist_draft.sql` | INTEGRATE | Adds provenance columns, unique constraint on `youtube_video_id`, and the RPC to the shared VM. |
| RLS-bypass service_role writes | INTEGRATE | RPC grants execute to `service_role` only; adapter uses a service-role client. |
| Auth (sign-up / sign-in / JWT) | OPT-OUT | Ingestion CLI uses service-role key; no end-user auth flow in this phase. |
| Realtime | OPT-OUT | No live subscription or broadcast needed for one-shot ingestion. |
| Storage | OPT-OUT | Drafts are text rows; no file uploads. |
| Edge Functions | OPT-OUT | Business logic lives in Python adapter + Postgres RPC; no Edge Function required. |
| `anon` / `authenticated` Data API access | OPT-OUT | Writes are service_role only; public read paths are unchanged and remain backend readers. |

## Scope Rationale

Phase 9 touches Supabase only through a single service-role RPC call. All other Supabase capabilities are intentionally out of scope to keep the ingestion write path small, auditable, and consistent with the existing `claim_and_publish_digest` RPC pattern (migrations 005/006).

## Verification

- INTEGRATE capabilities are exercised by unit tests with a mocked `supabase` client and by a SQL contract test against migration `007`.
- OPT-OUT capabilities are verified by absence: no imports, no policy changes, and no new public API roles beyond `service_role` execute on the RPC.
