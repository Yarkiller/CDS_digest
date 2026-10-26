# Phase 5: Admin Digest Publish - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Админ (CDS) triages the weekly digest **shortlist** (≤5 ranked candidates), Approve/Reject, mandatory email preview, then send → **new published issue** in archive + stub mailer record with issue link/`returnUrl`. Closes **AUTH-03** admin-API **403**. Scope is ADMIN-01…08 only — not YAML pipeline UI (PIPE-01 / post-v1), not live SMTP delivery, not public leaderboard or quizzes.

</domain>

<decisions>
## Implementation Decisions

### Admin gate & AUTH-03
- **D-74:** Admin = **`profiles.role = admin` only** — no separate «delegate» flag/claim in v1. — **Reversibility:** reversible — enum already includes `admin`.
- **D-75:** Non-admins: **hide «Админ» nav**; deep-link to admin route shows **403 page** («Недостаточно прав») + CTA **«На выпуск»** — never an empty shortlist. Matches `error_handling.md` §2.7.
- **D-76:** SPA learns role from **`GET /me` profile DTO** (nav + client gate); **all admin APIs still enforce 403** server-side. — **Reversibility:** costly — couples `/me` shape to shell.
- **D-77:** AUTH-03 proof in Phase 5: **pytest** non-admin → 403 on all admin routes **and** Playwright employee deep-link → 403 page. Closes Phase 1 verify gap.

### Shortlist source & scoring honesty
- **D-78:** v1 shortlist = **seeded/ops batch** in `digest_shortlist_batches` + `digest_shortlist_items` (≤5). **UI does not label** seed vs pipeline. **Runbook + docs** state: v1 batch from seed; live pipeline = PIPE-01+. **Seed file** comment: «demo batch для Phase 5». Future pipeline swap keeps the same UI contract. — **Reversibility:** costly — source swap is adapter-only if ports stay clean.
- **D-79:** Each row shows **numeric score + ≥2 readable factor labels** when `score_factors` provides them; otherwise **«обоснование недоступно»** (ADMIN-05).
- **D-80:** Empty shortlist copy: **«Кандидатов пока нет» + «Обновить»** — **no** «пайплайн не вернул» wording in UI (avoids implying a live job ran).
- **D-81:** **Current batch** = latest unsent (`sent_at IS NULL`, newest `week_start` / `created_at`). No week picker in v1.

### Triage & batch selection
- **D-82:** Inclusion for send = **`shortlist_decision`**: `approved` in send pool; `rejected` out; `pending` not sendable. Persist Approve/Reject (ADMIN-02). — **Reversibility:** costly — decision enum is the send contract.
- **D-83:** Row **checkboxes are batch-action targets only** (Approve/Reject selected). Send pool = all **`approved` + ready** materials — not a separate «include» checkbox.
- **D-84:** **«Выбрать все»** / **«Оставить топ-N»** (e.g. топ-3) **only update checkboxes** in one operation; admin still must Approve/Reject. Manual uncheck of one row keeps other checks (ADMIN-06).
- **D-85:** Every row shows **draft vs ready** badge. **Approve allowed on drafts**; **Send blocked** if any `approved` item is still draft (list draft badges + error_handling copy).

### Preview → send → email
- **D-86:** **Mandatory successful email preview this session** before Send unlocks (for current approved set). Failed preview never marks send verified (ADMIN-04). Aligns with prototype hint + §2.7 policy.
- **D-87:** **Mailer port** (Protocol/ABC). v1: **`StubMailer`** (`MAILER=stub`) — persist send + log email body; **no live SMTP**. **`SmtpMailer`** class exists but **`NotImplementedError`**; `MAILER=smtp` → **fail fast at startup** with clear «SMTP не настроен, используйте stub». Persist: `sent_at`, `recipient_count`, `issue_url`, `delivery_status='stubbed'` + **audit** `action='send'` (actor, batch_id, delivery_status). Success UI: **«Отправка записана»** — never «отправлено N подписчикам». Runbook §4e documents stub vs Phase 6+ SMTP. — **Reversibility:** costly — delivery_status + audit shape become the send contract.
- **D-88:** Successful send **publishes a new `digest_issues` row** (approved ready materials attached), sets batch **`sent_at`**, issue URL points at that issue (archive/current update for Phase 2 readers). — **Reversibility:** one-way — creates published issue rows.
- **D-89:** **Hard block** on repeat send for an already-sent batch: UI/API **«Уже отправлено»** — no second issue, no second stub send (ADMIN-07). Network/send failure → not marked sent; selection preserved (existing error patterns).
- **D-90:** Digest email (stub body) contains **link to the published issue**; unauthenticated open → login then **`returnUrl`** to that issue (ADMIN-08 / existing Phase 1 returnUrl).

### Claude's Discretion
- Exact admin route path (e.g. `/admin` vs `/admin/digest`) — prefer prototype/`acceptance_criteria` (`admin-digest`) unless planner finds a clearer plural/section convention with AppShell.
- Email preview modal vs page layout — follow `design-frontend/pages/admin-digest.html` unless UI-SPEC overrides.
- Confirm-send dialog copy; item-preview modal behavior; exact top-N default (3 vs 5); audit_log table vs reuse existing activity if present.
- Carry forward: same `VITE_USE_MOCKS` gate; shortlist GET fail → ServiceUnavailable/banner+Retry; mutation fail → toast/banner, never fake success; composition `service_role` only; Ports & Adapters + TDD.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, ADMIN-* mapping
- `.planning/REQUIREMENTS.md` — ADMIN-01…08, AUTH-03 remainder
- `.planning/PROJECT.md` — admin shortlist→send milestone; PIPE-01 deferred
- `CONTEXT.md` — shortlist, дайджест, админ glossary

### Prior phase decisions
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md` — D-09 mocks, D-12 returnUrl, JWT/`/me`
- `.planning/phases/02-issue-materials-archive/02-CONTEXT.md` — D-20…23 errors; D-24 current issue = latest published; archive
- `.planning/phases/03-voting-cycle/03-CONTEXT.md` — mutation toast/ErrorPanel patterns; D-56 mocks
- `.planning/phases/04-knowledge-razbory/04-CONTEXT.md` — honesty empty states; AppShell nav patterns

### Specs & UX
- `docs/digest-cds/acceptance_criteria.md` — US-06, US-22…US-27, US-31
- `docs/digest-cds/error_handling.md` — §2.7 admin shortlist / preview / send / 403
- `docs/digest-cds/user_stories.md` — admin journeys if present
- `docs/agents/local-platform-runbook.md` — must document stub mailer + seed batch honesty (§4e)
- `design-frontend/pages/admin-digest.html` — shortlist UI, preview modals, send gates

### Schema & architecture
- `supabase-integration/migrations/001_initial_schema.sql` — `app_role`, `shortlist_decision`, `digest_shortlist_batches` / `digest_shortlist_items`, `digest_issues` / issue materials
- `.cursor/rules/architecture.mdc` — Ports & Adapters; Mailer port in application; adapters outside domain
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `.planning/codebase/CONCERNS.md` — missing admin React route; shortlist ports gap
- `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`

### Brownfield code to evolve
- `web/src/App.jsx`, `web/src/components/AppShell.jsx` — admin route + role-gated nav
- `web/src/services/meApi.js` — ensure `role` on `/me` DTO
- `backend/src/backend/interface/http/` — admin routers + role dependency
- `backend/src/backend/composition/` — wire shortlist repos + StubMailer
- Phase 2 issue publish/read paths — send creates current/archive issue

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `design-frontend/pages/admin-digest.html` — layout, badges, select-all, email preview modal, send disabled until preview
- Schema tables for shortlist batches/items + `digest_issues` already exist
- Phase 1 `/me` + JWT deps; Phase 2 issue/archive read DTOs; Phase 3 mutation error UX
- `VITE_USE_MOCKS` + `web/src/services/` boundary for Playwright vs live

### Established Patterns
- Ports in `application/ports/`; adapters in `supabase-integration/`; wiring only in composition
- Honesty: never imply capabilities that are stubbed without runbook + neutral UI copy
- GET fail → splash/banner+Retry; mutation fail → keep form state, do not mark success
- Browser never receives `service_role`

### Integration Points
- New admin HTTP API + `web/src/services/adminApi.js` (name flexible)
- AppShell «Админ» only when `role === admin`
- Seed migration/script for demo shortlist batch (with honesty comment)
- Stub mailer + audit persist; issue publish on send links ADMIN-08 → Phase 1 returnUrl

</code_context>

<specifics>
## Specific Ideas

- User insisted seed vs pipeline honesty: **UI silent**, **docs/runbook + seed comment explicit** — same pattern as Phase 2–4 honesty rules.
- Mailer contract specified in detail: `MAILER=stub`, startup fail on smtp, `delivery_status='stubbed'`, success copy **«Отправка записана»**, runbook §4e for Phase 6+ SMTP.
- Empty shortlist deliberately avoids «пайплайн» wording even though error_handling §2.7 uses it — product language deferred until live pipeline exists.

</specifics>

<deferred>
## Deferred Ideas

- Live ranking / YAML pipeline UI (PIPE-01 / REQ-US-30) — post-v1
- Real SMTP/API delivery (`MAILER=smtp` + credentials) — Phase 6+ / separate ops ticket
- Week picker for shortlist batches
- Explicit re-send / re-open sent batch
- Separate «delegate» role beyond `app_role=admin`
- Public leaderboard, quizzes — already post-v1

None folded from todos (none matched).

</deferred>

---

*Phase: 5-Admin Digest Publish*
*Context gathered: 2026-09-21*
