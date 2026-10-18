# Phase 21: MAIL-01 live SMTP digest delivery - Context

**Gathered:** 2026-10-16
**Status:** Ready for planning

<domain>
## Phase Boundary

The weekly digest is delivered by a real SMTP mailer (stdlib `smtplib`/`email`) behind the extended `Mailer` port to an audience resolved server-side from `profiles`, with honest planned vs delivered counts, and mail failures contained so an already-published digest never becomes a 500 (D-88 / CR-02).

This phase does **not** route signup confirmation through `Mailer` (Phase 20 / GoTrue owns that), does **not** require a live corporate-relay smoke to merge code (`MAILER=stub` remains the default), and does **not** add a public leaderboard or new editorial capabilities.

</domain>

<decisions>
## Implementation Decisions

### Audience from `profiles`
- **D-01:** Digest recipients = **all** `profiles` rows that have a usable email — no role filter, no admin exclusion.
- **D-02:** Empty or malformed emails are **excluded** from the audience and **logged** (who/why); they do not count toward M.
- **D-03:** The send address is **`profiles.email` only** (no alternate address fields).
- **D-04:** If the filtered audience is empty (`M=0`): still **publish** the issue; mail is a no-op; `recipient_count=0` with an honest delivery status — do **not** block publish. — **Reversibility:** costly — changing this later would reintroduce a pre-publish audience gate and conflict with D-88 best-effort mail.

### Send shape & partial failure
- **D-05:** Send **one SMTP message per recipient** (not a single Bcc blast), so N of M is meaningful and addresses are not leaked across employees.
- **D-06:** Persist honesty via **option (i)**: batch/`claim_and_publish` keeps **planned** `recipient_count=M`; actual N and status details go to the **API response** and the `digest_send` **activity/`pings` payload**. No `DigestPublisher.update_delivery` in this phase. — **Reversibility:** reversible — option (ii) can be added later without rewriting the mailer.
- **D-07:** Live `delivery_status` values: `sent` (N=M, M>0), `partial` (0<N<M), `failed` (N=0, M>0); `stubbed` remains for `MAILER=stub`.
- **D-08:** On per-recipient failure: **continue**; **stop after three consecutive SMTP failures**; a successful send **resets** the consecutive counter; record the stop reason and counts in the activity/`pings` event. — **Reversibility:** reversible — threshold is a constant in the adapter/use-case policy.

### Admin response after send
- **D-09:** Response `message` is two honest sentences: publish confirmation + delivery line (e.g. «Выпуск опубликован. Доставлено N из M» / «… Письма не доставлены» on full mail fail). Never claim organisation-wide delivery.
- **D-10:** API exposes both counts: `recipient_count` = planned **M**, `delivered_count` = actual **N**; `message` is composed from them. — **Reversibility:** costly — additive field on `SendDigestResponse` / SPA `adminApi` contract once clients depend on it.
- **D-11:** HTTP status stays **200** when claim+publish succeeded, even if mail is `partial`/`failed` (D-88; tripwire PRESERVE).
- **D-12:** When `MAILER=stub`, message must say so explicitly, e.g. «Выпуск опубликован. Доставка писем: stub (0 из M)» — never look like a live SMTP failure.

### Relay contract & proof gate
- **D-13:** Default TLS posture: **`starttls` on port 587**; operator may override via env (`SMTP_TLS_MODE` / port). Document in runbook.
- **D-14:** Bounded timeouts are **fixed in `Settings`** (not env): connect ≈ **10s**, per-send ≈ **30s**; injected into the adapter as ready primitives — no `os.environ` in the adapter (MAIL-05).
- **D-15:** Ship real `SmtpMailer` + recipients/honesty with **`MAILER=stub` as default**. Live `MAILER=smtp` is an ops flip after relay smoke. Phase 20 criterion-4 relay **proof is not a merge blocker** for this phase's code; keep the smoke/rollback procedure in the runbook.
- **D-16:** `MAILER=smtp` with incomplete `SMTP_*` → **fail-fast at startup** (`ConfigurationError`), never silent stub fallback. Required at minimum: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` (TLS mode defaults to starttls). Align From with ADR-0003 domains. — **Reversibility:** reversible — env completeness check only.

### Claude's Discretion
- Exact Russian wording of the two-sentence `message` variants (sent / partial / failed / stub / M=0), as long as D-09/D-12 hold.
- Whether consecutive-failure stop lives primarily in the SMTP adapter vs use-case orchestration, provided D-08 semantics and event payload are identical.
- `Recipient` DTO shape (email + optional display_name) vs bare emails on the port — prefer explicit DTO per research, as long as the port stays typed (no `Any`).
- Exact log fields for excluded emails (D-02) and redaction of SMTP credentials in logs.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §Phase 21 — goal, success criteria, decision gate, tripwires (`test_send_digest.py` stubbed asserts AMEND; D-88 audit-failure PRESERVE; stub mailer PRESERVE; composition wiring AMEND).
- `.planning/REQUIREMENTS.md` — `MAIL-01`, `MAIL-03`, `MAIL-04`, `MAIL-05`.
- `.planning/PROJECT.md` — v1.3 framing; SMTP relay operator-supplied; recipients from `profiles`.
- `.planning/STATE.md` — Phase 21 position; Phase 20 decisions carried forward.

### Prior phase (shared relay / anti-features)
- `.planning/phases/20-mail-02-signup-confirmation-mail/20-CONTEXT.md` — GoTrue owns signup mail; `GOTRUE_SMTP_*` vs `SMTP_*` lanes; criterion-4 gap inherited.
- `docs/agents/local-platform-runbook.md` — relay shape, smoke/rollback; Phase 21 digest `SMTP_*` block.
- `.planning/debug/g-01-3b-signup-mailer.md` — closed diagnosis (do not reopen as product work here).

### Architecture & research
- `.planning/research/ARCHITECTURE.md` §(a)/(b) — `SmtpMailer` in `backend/infrastructure`; recipients port; option (i) vs (ii); build order honesty-before-live-SMTP.
- `.planning/research/STACK.md` — stdlib `smtplib`/`EmailMessage`; `SMTP_*` / `SMTP_FROM` table; per-recipient send guidance.
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — contour isolation for the corporate relay.
- `docs/adr/0003-email-domain-restriction.md` — From/audience domain gate.
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition-only wiring.
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor mandatory.

### Live code seams
- `backend/src/backend/application/ports/mailer.py` — extend with recipients; clarify return contract.
- `backend/src/backend/infrastructure/stub_mailer.py` — keep `StubMailer`; replace `SmtpMailer` placeholder / `resolve_mailer`.
- `backend/src/backend/application/use_cases/send_digest.py` — resolve audience → publish → mail → audit; surface mailer N/status.
- `backend/src/backend/application/ports/profile_repository.py` — add `list_digest_recipients` (or equivalent).
- `backend/src/backend/composition/settings.py` / `live.py` — `SMTP_*` + `resolve_mailer` wiring.
- `backend/src/backend/interface/http/routes/admin.py` — `SendDigestResponse` (+ `delivered_count`, message).
- `web/src/services/adminApi.js` / `web/src/pages/AdminDigestPage.jsx` — consume new fields/banner copy.
- `supabase-integration/src/supabase_integration/profile_repository.py` — list recipients adapter.
- `supabase-integration/migrations/005_*.sql` / `006_*.sql` — `p_recipient_count` already exists; forward planned M at publish.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StubMailer` + `resolve_mailer` — honest stub double; extend for live SMTP without deleting stub.
- `send_digest` already treats mail/audit as best-effort after `claim_and_publish` (catches `PersistenceError` only today — extend mapping for SMTP domain errors per MAIL-04).
- `render_email_html` / `compose_digest_body` — keep email composition; SMTP adapter only delivers.
- `ProfileRepository` + `SupabaseProfileRepository` / `InMemoryProfileRepository` — add list-recipients method + fakes.
- `PingRecorder` / `digest_send` activity — already written after mail; expand payload for audience/delivered/stop reason (D-06/D-08).
- Admin banner already shows `result.message` — update backend message + optional SPA display of N/M.

### Established Patterns
- Settings via `Settings.from_env()` only; adapters receive ready primitives (D-17 / MAIL-05).
- `MAILER=smtp` already fail-fasts at startup — replace NotImplemented path with real adapter + incomplete-config `ConfigurationError` (D-16).
- Keyword-only `Mailer.send_digest` — additive `recipients` param keeps stub callers valid.
- TDD: amend `"stubbed"` asserts; preserve D-88 success-after-publish tests; preserve `test_stub_mailer.py`.

### Integration Points
- Composition: `build_live_container` / `build_in_memory_container` wire mailer + profiles.
- HTTP: `POST /admin/shortlist/send` → `SendDigestResponse`.
- SPA: `sendDigest` in `adminApi.js` → banner on `AdminDigestPage`.
- Ops: VM env `SMTP_*` + runbook smoke; GoTrue lane stays `GOTRUE_SMTP_*` (untouched by digest adapter).

</code_context>

<specifics>
## Specific Ideas

- Stub banner example locked in discussion: «Выпуск опубликован. Доставка писем: stub (0 из M)».
- Consecutive-failure policy: three **consecutive** per-recipient SMTP failures → stop; success resets the streak; emit event with stop + N/M.
- Option (i) deliberately chosen over `update_delivery` for v1.3.
- Env naming from runbook: `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_TLS_MODE`; add `SMTP_FROM` (and optional `SMTP_FROM_NAME` per STACK research).

</specifics>

<deferred>
## Deferred Ideas

- **Option (ii) `update_delivery`** — post-mail update of batch delivery columns; not in this phase (D-06).
- **Relay/contour formal ADR** — declined in Phase 20 (D-04 there); still optional if ops needs a formal record when values land.
- **GoTrue confirmation path (A)** / flipping autoconfirm — ops after relay smoke; not digest `Mailer` work.
- **SPA `authApi.js` confirmation-mailer error mapping** — deferred from Phase 20 (D-08 there).
- **Bcc single-message send** — rejected for v1.3 in favour of per-recipient (D-05).

None — discussion stayed within phase scope for product capabilities.

</deferred>

---

*Phase: 21-MAIL-01 live SMTP digest delivery*
*Context gathered: 2026-10-16*
