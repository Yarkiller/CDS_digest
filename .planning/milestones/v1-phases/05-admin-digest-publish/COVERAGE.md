# API Coverage - Phase 5 Admin Digest Publish

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Detector assumption: phase touches mailer / SMTP / Cloud.ru delivery paths.
> Phase 5 does **not** integrate live SMTP or any third-party mail API — `StubMailer` only (CONTEXT D-87).
> Live data path remains self-hosted **Supabase** (service_role PostgREST / SQL) via FastAPI — same composition pattern as Phases 2–4.
> SPA never calls Supabase Data API or SMTP; Bearer JWT → FastAPI only.

## Mailer / SMTP (digest send)

| capability | decision | reason |
|---|---|---|
| Live SMTP / API delivery (`MAILER=smtp`) | OPT-OUT | D-87 — `SmtpMailer` class may exist with `NotImplementedError`; composition **fail-fast** if `MAILER=smtp`; no credentials this phase |
| Stub digest send persist + log body | INTEGRATE | `Mailer` Protocol + `StubMailer`; `delivery_status='stubbed'`; success copy «Отправка записана» |
| Subscriber list / recipient fan-out | OPT-OUT | stub `recipient_count=0` (or fixed stub); never imply real subscriber counts |
| External ESP (SendGrid, SES, …) | OPT-OUT | deferred Phase 6+ / ops ticket |

## Supabase Auth (SPA - publishable client)

| capability | decision | reason |
|---|---|---|
| signInWithPassword / getSession / returnUrl | INTEGRATE | Inherited Phase 1 — ADMIN-08 reuses `sanitizeReturnUrl` |
| Auth Admin / OAuth / MFA | OPT-OUT | unchanged out of scope |

## PostgREST / Database (service_role - composition/live.py only)

| capability | decision | reason |
|---|---|---|
| digest_shortlist_batches / items select + decision update | INTEGRATE | ADMIN-01…03, ADMIN-05 — `SupabaseShortlistRepository` |
| claim sent + publish digest_issues / issue items | INTEGRATE | ADMIN-07 / D-88 — atomic claim preferred (RPC or UPDATE … WHERE sent_at IS NULL) |
| activity_events audit row on send | INTEGRATE | D-87 — reuse PingRecorder / activity_events (`kind=digest_send` or payload action=send) |
| profiles.role read for admin gate | INTEGRATE | D-74 / AUTH-03 — authorize from `profiles.role`, never JWT `role` claim |
| Idempotent seed `005_phase5_admin_shortlist.sql` | INTEGRATE | ≤5 demo candidates; honesty comment «demo batch для Phase 5» |
| SPA direct `.from(shortlist/issues)` writes | OPT-OUT | never — FastAPI Bearer only; shortlist RLS has no authenticated policies |
| Destructive TRUNCATE / db reset | OPT-OUT | never on shared VM |

## FoundryModels / scoring pipeline

| capability | decision | reason |
|---|---|---|
| Live ranking / YAML pipeline UI | OPT-OUT | PIPE-01 / deferred Ideas — seeded batch only (D-78) |
| Fabricated score_factors when missing | OPT-OUT | ADMIN-05 honesty — «обоснование недоступно» |

## Notes

- Secrets: `SUPABASE_SECRET_KEY` only in `composition/live.py`; never `VITE_`.
- Assumption-delta scan for phase 5: **no-change** (admin vs employee roles already exist in `app_role` enum; no new pluralization/optional delta to promote).
- Package installs: **none new** (see RESEARCH Package Legitimacy Audit).

## Specless unclassified probe dispositions

Auto-generated edge coverage entries with `category: unclassified` for ADMIN-01…04 have no additional edge beyond the requirement text already planned. Disposition: **N/A — resolved as covered by existing plans**.

| Requirement | Disposition | Covered by |
|-------------|-------------|------------|
| ADMIN-01 unclassified | N/A | 05-01 GET ≤5 + 403; 05-04/05-06 empty + e2e |
| ADMIN-02 unclassified | N/A | 05-02 Approve/Reject persist |
| ADMIN-03 unclassified | N/A | 05-02 badges + 05-03 send draft block |
| ADMIN-04 unclassified | N/A | 05-03 preview match + fail gate; 05-04/05-06 SPA |

Classified probes (ADMIN-05 boundary/precision, ADMIN-06 adjacency/empty/ordering, ADMIN-07 idempotency/concurrency, ADMIN-08 adjacency/empty/ordering) remain explicit ASSUMPTIONs / edge truths in plan `must_haves`.
