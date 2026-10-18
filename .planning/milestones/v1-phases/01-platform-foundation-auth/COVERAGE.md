# API Coverage — Supabase (Auth + PostgREST)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Phase 1 integrates self-hosted Supabase on the shared VM (D-01, D-05, D-11).
> Surfaces: SPA `@supabase/supabase-js` Auth; FastAPI JWT via JWKS; service_role PostgREST for profiles + activity_events.

## Supabase Auth (SPA — publishable client)

| capability | decision | reason |
|---|---|---|
| signInWithPassword | INTEGRATE | D-03 / D-11 — Phase 1 login path |
| getSession | INTEGRATE | Session restore + Bearer token for `/me` |
| signOut | INTEGRATE | API present; UI logout control deferred (non-blocking) |
| updateUser (user_metadata) | INTEGRATE | Display-name sync (`full_name` / `display_name`) |
| onAuthStateChange | OPT-OUT | not needed yet — getSession on route load is enough for Phase 1 |
| signUp | INTEGRATE | amend D-08 / G-01-3 — self-service register via publishable client; Логин on /register |
| signInWithOAuth / SSO | OPT-OUT | D-03 — no corporate SSO in Phase 1 |
| MFA / TOTP / phone | OPT-OUT | D-03 — email+password only |
| resetPasswordForEmail / exchangeCodeForSession | OPT-OUT | not needed yet — ops reset via dashboard |
| refreshSession (explicit) | OPT-OUT | not needed yet — SDK default refresh via getSession |
| getUser | OPT-OUT | not needed yet — identity from JWT + `/me` profile |
| linkIdentity / unlinkIdentity | OPT-OUT | explicitly out of scope |
| reauthenticate | OPT-OUT | not needed yet |
| admin.* (Auth Admin API from browser) | OPT-OUT | never — service_role must not ship to SPA |

## Supabase Auth / JWT (FastAPI edge)

| capability | decision | reason |
|---|---|---|
| JWKS verify access token | INTEGRATE | D-01 — `verify_access_token` + corporate email gate |
| Proxy login through FastAPI | OPT-OUT | D-11 — SPA talks to Auth directly |
| Issue custom JWTs | OPT-OUT | explicitly out of scope — Supabase Auth is IdP |

## PostgREST / Database (service_role — composition/live.py only)

| capability | decision | reason |
|---|---|---|
| profiles select/upsert | INTEGRATE | GET/PATCH `/me` via ProfileRepository |
| activity_events insert (platform_ping) | INTEGRATE | POST `/me/ping` via PingRecorder |
| materials / issues / votes CRUD | OPT-OUT | not needed yet — Phase 2+ (live materials still in-memory in Phase 1) |
| Realtime subscribe | OPT-OUT | explicitly out of scope for Phase 1 |
| Storage upload/download | OPT-OUT | explicitly out of scope for Phase 1 |
| Edge Functions invoke | OPT-OUT | explicitly out of scope for Phase 1 |
| RPC / custom functions | OPT-OUT | not needed yet |
| SPA direct `.from(table)` reads | OPT-OUT | never for content — RLS gaps; SPA uses FastAPI Bearer only |

## Notes

- Secrets: publishable key in SPA; `SUPABASE_SECRET_KEY` / service_role only in server `composition/live.py` (T-01-06).
- Self-service `/register` (signUp + «Логин») is the primary Auth path (amended D-08 / G-01-3). Manual Auth dashboard seed remains an optional ops fallback on the shared VM — documented in `docs/agents/local-platform-runbook.md`; no automated seed scripts.
