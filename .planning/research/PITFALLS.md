# Pitfalls Research

**Domain:** Brownfield editorial knowledge platform (FastAPI + React/Vite SPA + self-hosted Supabase + Typer ingestion CLI), adding live mail and unattended scheduling to a shipped system
**Researched:** 2026-10-14
**Confidence:** MEDIUM (high for locally reproduced behaviour; medium for external docs)

**Framing:** this is a **subsequent milestone on a live, working system**. Every v1.3 item touches a shipped contract that is currently green: `GET /materials/{slug}` is ready-only by test, `beforeunload` is asserted by a passing Playwright test, `_StrictSafeLoader` fails closed, `send_digest` returns "Отправка записана", `/register` lands on `/` with a session, and `ingest` stdout is byte-locked. **The dominant failure mode is an over-narrow fix that satisfies the new feature while quietly changing one of those contracts.** Each pitfall below names the exact existing test or contract that will break.

**Proposed phase numbering used below** (roadmap owns the final numbers; matches the PROJECT.md ordering backlog → MAIL-02 → MAIL-01 → scheduler):

| Phase | Scope |
|-------|-------|
| 17 | Backlog 999.1 — reader-route honesty for draft materials |
| 18 | Backlog 999.6 — unsaved-changes guard (WR-04/WR-05) |
| 19 | Backlog 999.7 — YAML merge keys in the strict validator (WR-01) |
| 20 | MAIL-02 — signup confirmation mail |
| 21 | MAIL-01 — live SMTP digest to `profiles` |
| 22 | Scheduled ingestion (cron/systemd over the `ingest` CLI) |

---

## Critical Pitfalls

### Pitfall 1: "Fixing" the draft reader link by loosening the ready-only reader route

**What goes wrong:**
The cheapest-looking fix for 999.1 is to let `GET /materials/{slug}` return draft materials (drop the `material.status != MaterialStatus.READY` check, add an `?include_draft=` / `?preview=1` flag, or return 403 instead of 404 for drafts). Any reader — including one who merely guesses a short slug — then reads unpublished material. It also breaks the deliberate "draft and missing are indistinguishable" contract.

**Why it happens:**
The symptom is reported from the admin UI ("Открыть материал → leads to an error page"), so the fix gets aimed at the endpoint the admin link points to, not at *who* is allowed to see the target.

**How to avoid:**
- Keep `get_material_for_reader` and the reader route ready-only. Fix the *link*, not the gate.
- Prefer the path the codebase already supports: the admin shortlist DTO already carries `body_markdown`, `char_count`, `word_count`, `reading_minutes`, `provenance_label`, and `slug` (Phase 13 D-01: no fetch-on-open), and `AdminItemPreview` already renders the full body. A draft "Открыть материал →" should open an **admin-gated** surface (a new `GET /admin/materials/{id}/preview` behind `require_admin`, or a dedicated SPA route that reuses the loaded shortlist item), never the reader route.
- Keep missing and draft indistinguishable on the reader route (still 404 `material_not_found`, never 403) — that is both the shipped contract and the anti-enumeration behaviour.
- Add negative tests: a draft slug is 404 **for an admin's reader-route call too**; a draft id with no admin role on the preview route is 403/404; an unauthenticated preview call is 401.

**Warning signs:**
- `test_materials_draft_slug_returns_404_not_403` is deleted, skipped, or rewritten to expect 200/403.
- `MaterialStatus` disappears from `get_material_for_reader.py` or from the route's imports.
- Any new query parameter on `/materials/{slug}`.
- A "reader preview" that returns `provenance`/`tags`/`related` for a draft.

**Phase to address:** Phase 17.

---

### Pitfall 2: Draft leakage through join surfaces, cache headers, and SEO metadata

**What goes wrong:**
Even with the route kept honest, a new draft-capable response path can leak unpublished content through secondary fields and caching: `related` slugs/titles of unpublished materials, `tags`, `published_at: null` (an existence oracle once any intermediary caches the body), browser bfcache replay after a material is un-published, or SPA-level `<link rel="canonical">`/`og:`/heading extraction that makes a draft look indexable.

**Why it happens:**
`related` and `tags` are assembled in two places (`_related_ready` in the route, `_filter_ready_relations` in the Supabase adapter) and both filter on `ready` — a new preview path that bypasses `_to_response` or the adapter filter loses that protection silently. Caching is nobody's explicit job.

**How to avoid:**
- Reuse the *existing* ready-filtering helpers on every new path, and add a test that a preview of a draft with an unpublished related material returns no related entry.
- Mark any draft-bearing response `Cache-Control: private, no-store` and never serve draft content on a URL that is also a published canonical URL.
- Keep draft content out of anything an indexer or a link-preview bot can reach (it is JWT-gated, so also make sure no unauthenticated copy is introduced).
- Enforce the invariant "a material referenced by a published `digest_issue_items` row is never demoted to draft" — add a guard/test, because `SupabaseMaterialRepository.save` writes `status` from the domain object and a future triage path could re-draft a published material, breaking already-sent email links.

**Warning signs:**
- A draft response containing `published_at: null` served with no cache headers.
- `related` non-empty on a draft-preview payload.
- Any code path calling `repo.save(...)` with `status=draft` for a material whose id appears in `digest_issue_items`.

**Phase to address:** Phase 17.

---

### Pitfall 3: `window.confirm` inside `beforeunload` — shipped, and asserted by a passing test

**What goes wrong:**
`AdminPipelineConfigPage` currently calls `window.confirm(UNSAVED_LEAVE_CONFIRM)` inside its `beforeunload` listener. That is what WR-04/WR-05 flagged. The subtle trap is that **`tests/admin.spec.js` green-lights it**: the test dispatches a synthetic `new Event("beforeunload", { cancelable: true })` and asserts both `defaultPrevented === true` and a `dialog` carrying the Russian copy. The test therefore proves only that the listener runs in the test harness, not that a real browser shows anything.

**Why it happens:**
Headless Chromium lets a script dispatch the event and lets the handler open a dialog; real browsers do not allow page code to drive the unload prompt, and the prompt requires prior user interaction ("sticky activation"). A green test plus a plausible-looking handler makes the bug look already-fixed.

**How to avoid:**
- In the `beforeunload` handler do exactly two things, and nothing else: `event.preventDefault()` and `event.returnValue = true` (a truthy value — the legacy activation path still matters for Chrome/Edge below 119 and for cross-checking; `returnValue` as a *user-visible* message is deprecated and ignored by modern browsers).
- Never call `window.confirm`/`alert` inside `beforeunload`. Custom copy is impossible there — the prompt text is browser-owned.
- Move the actual 「Есть несохранённые изменения. Уйти без сохранения?」 decision into the **in-app** guard (a modal from the router guard), which is the only place the copy can be shown.
- Rewrite the existing Playwright proof. Assert the handler *contract* (registers only when dirty, sets the flag, removes itself on unmount and after a successful save) rather than the native dialog. Do not keep an assertion that a dialog appeared during `beforeunload` — that assertion is the bug's alibi.
- Remember the division of labour: `beforeunload` covers reload/close/tab; the router guard covers in-app navigation and explicitly does *not* cover hard reloads or cross-origin navigation. Both are required; neither alone is sufficient.

**Warning signs:**
- `window.confirm` still inside a `beforeunload` listener.
- Any test asserting a `dialog` or `defaultPrevented` after a *synthesised* `beforeunload` event.
- A guard that only reacts to a hand-dispatched event.

**Phase to address:** Phase 18.

---

### Pitfall 4: `useBlocker` requires a data router — and this app is on `<BrowserRouter>`

**What goes wrong:**
`useBlocker` calls the data-router context and throws when it is absent. `web/src/App.jsx` uses the declarative `<BrowserRouter>` (react-router-dom `^7.18.3`), which provides navigation and location contexts but no data-router context. So the "obvious" implementation of the router guard throws at render time.

**Why it happens:**
`useBlocker` is the documented modern answer for unsaved-form navigation, and the docs' data-router prerequisite is easy to skim past.

**How to avoid:**
- Either migrate `App.jsx` to `createBrowserRouter(...)` + `<RouterProvider>` — as its **own behaviour-preserving plan**, with the full Playwright suite (web + admin + auth + knowledge + razbory) green *before* the guard is wired — or avoid `useBlocker` entirely and implement the in-app guard inside the pipeline page (intercept the relevant navigation intent and gate it behind the existing modal).
- If you migrate, treat every route in `App.jsx` as an at-risk regression surface: the auth-gated parent route, the `*` → `/` catch-all, and `RequireAuth` all have Playwright coverage that can shift under a router swap.
- Do not combine the router migration and the guard in one plan; a throw from `useBlocker` would look like a router-migration failure and send the next session hunting the wrong cause.

**Warning signs:**
- `useBlocker must be used within a data router` in the console.
- `BrowserRouter` still imported while `useBlocker` is used.
- A router migration plan whose verification is "the page loads" rather than the whole suite.

**Phase to address:** Phase 18.

---

### Pitfall 5: A guard that fires on a successful save, or double-prompts

**What goes wrong:**
With two guard mechanisms and `dirty` derived as `yaml !== savedYaml`, four failure modes appear at once: (a) navigating immediately after a successful save still prompts, because `dirty` is still true in the same tick; (b) a server reject silently disarms the guard, because `onSave`'s failure branch leaves the document dirty but some implementations clear the flag optimistically; (c) both guards arm, so the user confirms the modal and then gets the browser prompt anyway; (d) the `beforeunload` listener leaks across React StrictMode remounts or is never removed after a save, so a clean editor prompts.

**Why it happens:**
The dirty state lives in the page, the guard lives in the router, and the save is asynchronous — three lifecycles with no shared "leave is allowed now" signal.

**How to avoid:**
- One source of truth for dirtiness, plus an explicit one-shot `allowLeave` (or `savedRef`) flag that both guards consult.
- Order the save: validate → persist → update `savedYaml` **and** set `allowLeave` → then navigate. Never navigate before the state settles.
- Preserve the shipped reject contract: `INVALID_CONFIG` keeps the document dirty and renders every structured error (Phase 16 D-03/D-07). The guard must stay armed after a reject.
- Cover all four with Playwright: save → navigate (no prompt); reject → navigate (prompt); confirm → navigate (exactly one prompt); cancel → stays with the draft intact.

**Warning signs:**
- A prompt after "Сохранено".
- Two dialogs for one navigation with a dirty editor.
- Guard still armed after a failed save.
- `expect.poll` on a dialog message used as the only proof of the guard.

**Phase to address:** Phase 18.

---

### Pitfall 6: Detecting duplicate keys before `flatten_mapping` — the merge tag has no constructor

**What goes wrong:**
`_StrictSafeLoader.construct_mapping` iterates `node.value` and calls `self.construct_object(key_node, deep=deep)` on every key **before** `SafeConstructor.construct_mapping` runs `flatten_mapping`. For a document using `<<`, the merge key node carries the tag `tag:yaml.org,2002:merge`, for which `SafeLoader` registers no constructor. The loader therefore raises a cryptic internal-tag error instead of merging.

**Reproduced on this checkout (PyYAML 6.0.3, Python 3.14):** a valid merge-key document that `yaml.SafeLoader` loads correctly raises

```
ConstructorError | could not determine a constructor for the tag 'tag:yaml.org,2002:merge'
```

This is the whole of WR-01: the failure is closed (structured 400, zero writes), but the message is an implementation detail leaking to the admin UI.

**Why it happens:**
The duplicate-key override was written to be ordered "cheapest first" (check keys, then delegate), and `node.value` for a merge document looks like an ordinary key/value list until you inspect the tag.

**How to avoid:**
- Skip key nodes whose `tag == "tag:yaml.org,2002:merge"` in the duplicate scan, and keep the scan **before** `flatten_mapping`.
- Do not construct key nodes you are not going to use as keys; the merge key is not a key of the resulting mapping at all.
- Verify with `yaml.SafeLoader` as the oracle: for every accepted-by-`SafeLoader` document the strict loader must produce the *same* mapping (loop this in a test rather than hand-writing cases).

**Warning signs:**
- The literal string `tag:yaml.org,2002:merge` appearing in any 400 response body.
- A fix that special-cases the string `'<<'` (the tag is what matters; a quoted `'<<'` is an ordinary key).
- `flatten_mapping` called before duplicate detection.

**Phase to address:** Phase 19.

---

### Pitfall 7: The naive fix — scanning *after* `flatten_mapping` — rejects valid documents

**What goes wrong:**
The next-most-obvious fix, "run `flatten_mapping` first, then look for duplicate keys", is worse than the bug: `flatten_mapping` moves merged keys to the front of `node.value`, so a perfectly valid document where a local key overrides a merged key now looks like a duplicate.

**Reproduced on this checkout:** for a valid document that `SafeLoader` resolves to `{'x': 1, 'y': 3}` (local `y: 3` overriding merged `y: 2`), the flatten-then-scan loader raises

```
ConstructorError | found duplicate key ('y')
```

Local-over-merged override is exactly the feature YAML merge keys exist for, so this fix trades a false negative for a false positive **and** makes merge keys useless.

**Why it happens:**
"Duplicate keys are bad" and "merged keys are inserted into the node list" are both true, and the interaction is invisible until you test an override.

**How to avoid:**
- Keep duplicate detection on the **pre-merge, own-key list** (the same list that must ignore the merge tag).
- Add an explicit accept-case test: `<<: *base` plus a local key that shadows a merged key must load, and the local value must win.
- Keep a reject-case test next to it: a genuine `y: 1` / `y: 2` in the same mapping (including when a `<<` is also present) must still be rejected.
- Keep `test_put_invalid_error_rows_are_verbatim_and_top_level` and the zero-writes assertions intact — the merge fix must not change the reject envelope.

**Warning signs:**
- A 400 `{errors:[...]}` for a document the admin can see is fine (a merge with an override).
- `flatten_mapping` appearing above the loop that builds `seen`.
- The merge test suite only contains cases with no overriding keys.

**Phase to address:** Phase 19.

---

### Pitfall 8: The correct merge fix silently opens a merge-expansion DoS under the existing char cap

**What goes wrong:**
Today the merge path is unreachable: the merge tag raises before `flatten_mapping` ever runs with merges present. The moment the skip-merge-key fix lands, `SafeConstructor.construct_mapping`'s own `flatten_mapping` runs on documents containing nested merges, and `flatten_mapping` *multiplies* the node list: each mapping that merges `k` copies of a mapping which itself merged `k` copies grows as `k^depth`, in place, in memory, before any duplicate scan.

**Reproduced on this checkout (fixed loader, skip merge tag + scan-before-flatten — i.e. the correct fix):**

| Levels | Fan-out | Source chars | Result |
|--------|---------|--------------|--------|
| 8 | 3 | 312 | 14 ms |
| 10 | 3 | 390 | 116 ms |
| 12 | 3 | 478 | 838 ms |
| 13 | 3 | 522 | 2 377 ms |
| 14 | 3 | 566 | 8 273 ms |
| 15 | 3 | **610** | **> 10 000 ms (killed)** |

A **610-character** document — 3 % of the `MAX_PIPELINE_CONFIG_CHARS = 20000` budget — already exceeds ten seconds, and cost roughly triples per level. Nothing in the current module bounds this, because the char cap measures the source, not the materialised node list. Note this is a *newly reachable* path: 999.7 converts a fail-closed rejection into an accepted document, so the fix must add its own bound.

**Why it happens:**
The existing DoS thinking in this module is about parser recursion (`RecursionError` → `_TOO_DEEP_MESSAGE`) and the source-length cap (`MAX_PIPELINE_CONFIG_CHARS`). Merge expansion defeats both: it is neither deep nor long.

**How to avoid:**
- Add a bound as part of the 999.7 fix, not as a follow-up: reject a mapping whose merge sources themselves contain a merge key (a one-level merge is all the 4-key schema can use), and/or cap the number of flattened entries constructed, and/or pre-count nodes with `yaml.compose` before constructing and reject over a node budget.
- Keep the structured-400 envelope: the merged-bomb reject must be `{errors:[{path, message}]}` with zero writes, in Russian, like the sibling messages `_OVER_CAP_MESSAGE` / `_TOO_DEEP_MESSAGE` / `_UNREADABLE_MESSAGE`.
- Add a regression test that a nested-merge bomb (well under the char cap) is rejected within a time bound — the test must assert the reject *and* be fast, so a future regression fails loudly instead of hanging CI.
- Wrap any new pre-pass (`yaml.compose`, node walk) in the same `RecursionError`/`YAMLError` mapping the loader already has, or a new pre-pass becomes a new 500 path.

**Warning signs:**
- A merge-key test document with only one merge level (the bomb shape is invisible).
- Test-suite wall-clock growth on the validator module.
- No entry-count / merge-depth guard in the diff.
- A phase plan whose verification is "the merge test passes" with no adversarial case.

**Phase to address:** Phase 19 (bound and test ship with the fix).

---

### Pitfall 9: Confusing alias expansion (billion laughs) with merge expansion — and reaching for the wrong loader

**What goes wrong:**
Two adjacent ideas invite a wrong fix: (i) treating 999.7 as a "billion laughs" problem and reaching for a loader change, and (ii) fixing the duplicate-key problem by swapping `_StrictSafeLoader` for `yaml.safe_load` or `Loader=yaml.FullLoader`.

**Measured on this checkout:** classic alias chains are **cheap to construct** — `yaml.safe_load` returned in 15 ms at 200 nesting levels, because YAML aliases are shared references, not copies. So alias expansion is *not* the dominant risk here. Meanwhile `yaml.safe_load` performs **no duplicate-key rejection**, so swapping it in silently deletes the PIPE-02 contract, and `FullLoader`/omitting `Loader=` re-opens arbitrary-object construction.

**Why it happens:**
"YAML + DoS" retrieves billion-laughs from memory, and "the strict loader rejects my valid YAML" retrieves "use `safe_load`" from muscle memory.

**How to avoid:**
- Target the bound at merge expansion (Pitfall 8), which is the measured amplifier in this code path.
- Never change the `Loader=` argument or the class hierarchy as part of a merge-key fix. Keep the loader a `SafeLoader` subclass in `infrastructure/` (`yaml` and `pydantic` must not reach `domain/` or `application/use_cases/` per architecture.mdc).
- Add a negative test asserting duplicate keys are *still* rejected after the fix (the guard against a `safe_load` regression).
- Keep the source-length cap checked before parse — it is the outer shell for both risks.

**Warning signs:**
- `yaml.load(...)` with no `Loader=`; `FullLoader`/`UnsafeLoader` in the diff.
- `yaml.safe_load(` in the validator.
- A duplicate-key test deleted at the same time as the merge fix.

**Phase to address:** Phase 19.

---

### Pitfall 10: A real mailer's exception escapes `send_digest` and turns a published digest into a 500

**What goes wrong:**
`send_digest` wraps `mailer.send_digest(...)` in `except PersistenceError`. The atomic claim+publish has already committed by then (D-88: publish is claimed before mail). A live SMTP adapter does not raise `PersistenceError` — it raises `smtplib.SMTPException` (auth, recipient refused, TLS), `OSError`/`ConnectionError`, or `socket.timeout`. Those propagate out of the use case, through the route, into a 500, while the digest **is** published and `sent_at` **is** stamped. The admin sees a failure for a successful publish, tries again, and gets `AlreadySentError`/409 — the exact contradiction the CR-02 contract exists to prevent.

**Why it happens:**
The stub cannot fail, so the only exception ever observed in this position historically was `PersistenceError` (from the audit recorder). The `except` clause was written against the stub's failure surface, and `SmtpMailer` is a `NotImplementedError` placeholder.

**How to avoid:**
- Define a mailer error type, raise it from the SMTP adapter (mapping `SMTPAuthenticationError`, `SMTPRecipientsRefused`, `SMTPNotSupportedError`, `SMTPResponseException`, `OSError`, `timeout` at the boundary), and catch that plus `PersistenceError` in `send_digest`. Never let an SMTP failure reach the route.
- Add the mirror of `test_send_audit_failure_after_publish_still_returns_success`: a mailer that raises the real exception type must still return `SendDigestResult` with the published `issue_url`, and `sent_at` must stay stamped.
- Keep the D-88/D-89 semantics untouched: mail failure is logged, best-effort, and never re-claims or un-claims the batch.

**Warning signs:**
- `except PersistenceError:` as the only guard around the mailer call.
- Any HTTP 5xx from `POST /admin/shortlist/send` while the issue exists in `digest_issues`.
- A second send attempt returning 409 after the UI reported a mail failure.

**Phase to address:** Phase 21.

---

### Pitfall 11: `delivery_status` and `recipient_count` are stamped *before* mail — so live mail would still report `stubbed` / `0`

**What goes wrong:**
`claim_and_publish_digest` stamps `delivery_status` (default `'stubbed'`) and `recipient_count` (default `0`), and `SupabaseDigestPublisher.claim_and_publish` never passes `p_delivery_status`/`p_recipient_count`. `send_digest` then reads `publication.delivery_status` / `publication.recipient_count` and **discards the mailer's return value**. So wiring a real SMTP adapter still reports "stubbed, 0 recipients" in the API response, in the audit ping payload, and in the `digest_shortlist_batches` row — while MAIL-01's acceptance criterion is "an honest `recipient_count`".

**Why it happens:**
The delivery columns were designed for the stub era. `Mailer.send_digest` returns `{delivery_status, recipient_count, issue_url}` and the use case never reads it — the honest value exists and is thrown away.

**How to avoid:**
- Decide and document the honest contract explicitly, because the two halves cannot both be "the truth": `sent_at`+publish stay inside the atomic claim (pre-mail, required for retry integrity), while delivery facts can only be known post-mail.
- Simplest honest option: keep the atomic publish as-is, then write the mailer's real result (status + count) in a **separate, idempotent** post-send update, and make the API response and the audit ping carry the mailer's values rather than the publication's. Do not move `sent_at` out of the claim transaction.
- Update `test_send_digest.py`'s `delivery_status == "stubbed"` / `payload["delivery_status"] == "stubbed"` assertions deliberately (they encode the stub contract, not the product contract), and add a test that the response `recipient_count` equals the number of recipients the mailer actually received.
- If the migration changes the RPC, use `create or replace function` with defaulted new parameters so old and new code can coexist during the apply-then-deploy window.

**Warning signs:**
- A live send whose response says `delivery_status: "stubbed"`.
- `recipient_count: 0` in the `pings` payload for a real send.
- A "recipient list" plumbed into the mailer while the reported count still comes from `DigestPublication`.

**Phase to address:** Phase 21.

---

### Pitfall 12: SMTP transport details — TLS mode, timeouts, and the synchronous request path

**What goes wrong:**
Four independent ways a live relay turns into an outage or a silent downgrade: (a) `SMTP_SSL` (implicit TLS, port 465) chosen for a 587 relay or vice versa — the STARTTLS upgrade requires the server to advertise it and otherwise raises `SMTPNotSupportedError`, while a 465 port never answers plaintext; (b) falling back to plaintext after a TLS failure, which puts credentials on the wire; (c) the default `smtplib` timeout is the global socket default — a black-holed relay stalls the admin HTTP request; (d) sending the whole audience in one request path with per-recipient sequential connects, so elapsed time grows linearly with `len(profiles)` against the NFR p95 target.

**Why it happens:**
The mailer has no implementation yet, so every transport decision is being made for the first time inside a feature phase, and the `from_env` seam carries no SMTP settings to shape it.

**How to avoid:**
- Make the TLS mode explicit config (`SMTP_TLS_MODE=starttls|ssl|none` plus a validated port pairing), never a silent fallback after a TLS error.
- Pass a bounded `timeout` to the SMTP constructor (a `timeout` of `0` raises `ValueError`; a missing one means unbounded) and bound the whole send with a wall-clock budget.
- Prefer one `send_message` per delivery with the whole audience in `Bcc` (see Pitfall 13) over N sequential connects, and cap the audience per run.
- Decide synchronously-vs-asynchronously **before** coding: the API response contract ("Отправка записана") and the audit ping depend on it.
- Settle the relay choice and its constraints in an ADR/spike before the phase can pass, the same way the YouTube key decision is deferred (PROJECT.md key-context bullet).

**Warning signs:**
- No `timeout=` on the SMTP constructor.
- A plaintext/`none` fallback branch reachable after a TLS error.
- Send duration proportional to the number of profiles.
- The relay's port/TLS mode still undecided at plan time.

**Phase to address:** Phase 21 (decision spike early; adapter in the phase).

---

### Pitfall 13: The recipient audience — missing port method, `To:`-header PII, domain gaps, and a `profiles` table that isn't "all users"

**What goes wrong:**
Four audience traps: (a) `ProfileRepository` has no "list all" method and `profiles` RLS only allows a user to select their own row, so a naive implementation either adds an RLS policy (weakening the data boundary) or reads through the publishable client and gets zero rows; (b) putting every recipient in `To:` exposes the internal distribution list to every recipient and to relay logs; (c) `profiles.email` is never validated against the two corporate domains — ADR-0003 fixes `@sberbank.ru` / `@omega.sbrf.ru`, and a stray foreign address either fails the relay or ships internal content outside the contour; (d) `profiles` rows are created lazily by `get_or_upsert` on the first `/me` call, so a user who registered but never signed in has **no** `profiles` row — `profiles` is not the set of users with access, and `recipient_count` from `profiles` is therefore an under-count that must be described honestly.

**Why it happens:**
The port was built for the `/me` upsert, not for enumeration. The "audience" concept is new in v1.3, and `recipient_count` has been hardcoded `0` by migrations 005/006 until now, so nothing has ever forced the question.

**How to avoid:**
- Add the audience read as an **additive port method** implemented by a service-role adapter wired only in `composition/live.py`; do not add an RLS policy to `profiles`.
- Use `Bcc` for the audience (or a relay-side alias), with a single stable `To` (e.g. the admin or a digest alias). Test the header composition, including that no `Bcc` leaks into the transmitted headers.
- Filter the audience with the existing `is_allowed_corporate_email` domain rule and assert it in a test; never introduce a dynamic admin-managed domain list (ADR-0003).
- Document and (if it matters to the acceptance criterion) surface the `profiles`-vs-`auth.users` divergence, so `recipient_count` is labelled as "profiles rows with a corporate address", not "all authorized users".

**Warning signs:**
- A new RLS policy on `profiles`.
- Recipient addresses in the `To:` header of the generated message.
- Audience rows with a non-corporate domain reaching the mailer.
- `recipient_count` claimed as "все сотрудники" in copy.

**Phase to address:** Phase 21.

---

### Pitfall 14: MAIL-02's root cause is a deliberate configuration state, not missing code

**What goes wrong:**
"Signup confirmation mail never arrives" is currently **true by design**. The Phase 1 unblock set `GOTRUE_MAILER_AUTOCONFIRM=true` (the runbook's §4.1: "Turn Confirm email OFF"; verified `GET /auth/v1/settings` → `mailer_autoconfirm: true`). With autoconfirm on, GoTrue never sends a confirmation email. A phase that opens with implementation instead of investigation will "fix" a mailer that is intentionally bypassed, or will conflate MAIL-02 with GoTrue's own SMTP config.

**Why it happens:**
The debug record (`.planning/debug/g-01-3b-signup-mailer.md`) is `audit_acknowledged` with `status: unknown`, and the symptom ("no mail") reads like a code defect. The original 500 (`Error sending confirmation email`) was diagnosed but the *chosen* remedy was to remove the email dependency.

**How to avoid:**
- Open the phase with diagnosis and record the current state: `GET /auth/v1/settings` (`mailer_autoconfirm`, `disable_signup`, `external.email`), whether GoTrue's SMTP vars are populated (`GOTRUE_SMTP_HOST/PORT/USER/PASS/ADMIN_EMAIL`), whether the relay is reachable from the auth container, and whether the SPA or GoTrue is the intended sender.
- Then decide the product contract explicitly — one of:
  1. keep autoconfirm ON and send the confirmation through the **app's own `Mailer` port** (keeps GoTrue out of the mail path, reuses MAIL-01's adapter, and leaves `/register` behaviour unchanged); or
  2. turn autoconfirm OFF and let GoTrue send it (requires a healthy relay, changes the signup response shape, and re-arms Pitfall 15).
- Close the debug session in the same change that ships the fix (Retrospective lesson #1/#6 — un-closed debug sessions resurface at the next milestone close, and the v1.2 close had to acknowledge nine of them).

**Warning signs:**
- A plan whose first task is "implement the mailer" with no diagnosis task.
- No recorded `mailer_autoconfirm` value at plan time.
- MAIL-02 and MAIL-01 sharing one implementation task.
- The debug file still `diagnosed`/`unknown` after the fix ships.

**Phase to address:** Phase 20.

---

### Pitfall 15: Turning autoconfirm off re-introduces the v1 signup 500 and breaks a shipped Playwright test

**What goes wrong:**
If MAIL-02's fix is "turn `MAILER_AUTOCONFIRM` off", signup becomes email-dependent again. With a broken or unreachable relay, `POST /auth/v1/signup` returns 500 `Error sending confirmation email` and **no Auth user is created** — the original v1 defect. And even with a healthy relay, `signUp` no longer returns a session, so `RegisterPage` takes its `!session` branch ("Регистрация принята. Подтвердите email по ссылке из письма, затем войдите."), stays on `/register`, and `tests/auth.spec.js`'s `shows Логин as shell identity after register` (which asserts a redirect to `/` and the shell identity) **fails**.

**Why it happens:**
The shipped `/register` flow was built *after* autoconfirm was turned on; its happy path and its `!session` branch are both already written, and the Playwright suite locks the autoconfirm-era behaviour.

**How to avoid:**
- Treat the autoconfirm flip as a behaviour change with an explicit test amendment: update `tests/auth.spec.js` (and `RegisterPage` copy if needed) under TDD, and record the reason — never delete the assertion silently.
- Add a fail-closed error mapping so a broken relay shows honest Russian copy instead of the generic «Сервис входа временно недоступен» NETWORK banner (the SPA follow-up that was deferred in Phase 1 and is still open).
- Verify the relay end-to-end with a single internal address **before** flipping the flag, and keep a documented one-command rollback to autoconfirm.
- Keep the two-domain allowlist intact (Pitfall 16) — do not let the mailer change become the domain gate.

**Warning signs:**
- A plan that flips a GoTrue env var with no `tests/auth.spec.js` change.
- A register test deleted rather than amended.
- A 500 `Error sending confirmation email` reappearing in the runbook smoke.
- No rollback step in the runbook.

**Phase to address:** Phase 20.

---

### Pitfall 16: A working relay turns `/auth/v1/signup` into an open email-sender — and the domain gate is client-side + post-hoc only

**What goes wrong:**
Today the two-domain rule (ADR-0003) is enforced in exactly two places: `web/src/services/emailDomain.js` (client side, bypassable) and `backend/.../deps.get_principal` (server side, but only on *authenticated* requests → 403 `domain_not_allowed`). Nothing gates signup itself: a direct `POST /auth/v1/signup` with `user@gmail.com` creates an Auth user. Once GoTrue gets a healthy relay and autoconfirm is off, **any address on the internet can make the corporate relay send a confirmation email**, revealing that signup is open and abusing the relay; the only limiter is `GOTRUE_RATE_LIMIT_EMAIL_SENT` (default 30) which is a **global, process-level** limiter shared by all users, not per-IP — so it is simultaneously the abuse cap and a self-inflicted registration outage.

**Why it happens:**
The domain rule was designed for the read path, and autoconfirm hid the signup path entirely. GoTrue has no built-in corporate-domain allowlist.

**How to avoid:**
- Enforce the domain rule at the signup edge — a GoTrue pre-signup hook, or a reverse-proxy/edge check in front of `/auth/v1/signup` — in addition to the existing FastAPI gate. Never rely on the SPA check.
- Do not mirror GoTrue's "already registered" message verbatim; keep the SPA's error surface non-enumerating.
- Keep the existing `deps.get_principal` domain gate and `test_auth_email_domain.py` assertions exactly as they are; a signup-side gate is additive.
- Document the per-hour relay/SMTP limits as an operational constraint (they interact with bursty registration and with the digest send).

**Warning signs:**
- A signup success for a non-corporate domain.
- Only `emailDomain.js` and `deps.py` as domain checks in a v1.3 diff.
- `test_auth_email_domain.py` or the `domain_not_allowed` 403 loosened or removed.
- Registration failing in bursts with no relay log evidence.

**Phase to address:** Phase 20 (gate) with a cross-check in Phase 21 (the digest audience uses the same rule).

---

### Pitfall 17: Confirmation tokens and redirect targets

**What goes wrong:**
A confirmation flow introduces a privileged token in a URL. Failure modes: logging the link (or the token) in the app/relay/GoTrue logs; resending on every failed login and thereby minting many live tokens; accepting a token for a different address; and an unrestricted `redirect_to`, which turns the corporate mail into a phishing/open-redirect vector.

**Why it happens:**
The SPA already has one URL-safety helper (`sanitizeReturnUrl`, same-origin relative paths only), and it is easy to assume it covers confirmation redirects. It does not — the confirmation target is a different surface, and it is GoTrue-configured, not SPA-configured.

**How to avoid:**
- Configure the confirmation redirect to an allowlisted origin; do not accept an arbitrary `redirect_to`.
- Never log the confirmation URL or token — the repo already has a redaction contract and a `SecretRegistry` for the CLI; extend the same discipline to any new mail/HTTP logging (values, not just key names).
- Keep tokens single-use and short-lived; one resend per explicit user action.
- Add a test that the SPA's URL handling rejects a foreign-origin confirmation target.

**Warning signs:**
- A confirmation link in application logs or in an error message.
- A free-form `redirect_to` accepted from the query string.
- Resend wired to a retry loop.

**Phase to address:** Phase 20.

---

### Pitfall 18: Scheduled runs overlap — the CLI's idempotency is not a concurrency control

**What goes wrong:**
`ingest` is idempotent **per video** (unique `youtube_video_id` → `already_saved`), and `persist_draft_and_enqueue` locks the latest unsent batch `FOR UPDATE`, so ranks do not collide. But two overlapping runs still (a) both pay full captions + LLM cost for the same videos, (b) can create a second unsent batch mid-run, and (c) interleave shortlist writes. Cron has no concept of "this job is already running" — every tick execs a fresh process.

**Why it happens:**
"the ingest CLI is already idempotent" (PROJECT.md) is true and reassuring, and it reads like it also solves overlap. It solves *duplicate rows*, not *duplicate work*.

**How to avoid:**
- Use a systemd `Type=oneshot` service + timer for the schedule: systemd will not start a unit that is already active, so an overrunning run causes the next trigger to be skipped rather than stacked.
- Because the operator will also run the CLI by hand (and possibly cron during migration), add an `flock` on a **local** lock file as the one guard that holds regardless of trigger. Never put the lock on NFS.
- Never leave two schedulers configured for the same job; comment out the cron line in the same change that enables the timer.
- Add a bounded `RuntimeMaxSec=` so a hung run is killed rather than blocking every subsequent trigger.

**Warning signs:**
- Two `ingest` processes overlapping in `ps` / the journal.
- Duplicate `batch_id`s created close together.
- A lock file on a network mount.
- A crontab line and a timer both present.

**Phase to address:** Phase 22.

---

### Pitfall 19: Unattended runs fail silently — cron's env is empty and nobody reads its mail

**What goes wrong:**
A cron job runs with a minimal environment: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `DEEPSEEK_API_KEY`, and any YouTube API key are absent (the CLI uses a **separate `.env`** and `Settings.from_env`), so the run exits 1 with a `ConfigurationError` on stderr. Cron mails that stderr to a mailbox nobody reads, so the schedule can be dead for weeks while everyone assumes ingestion is running. Even when it runs, a per-video failure is a single JSON line on stderr that nobody sees.

**Why it happens:**
Interactively the operator has the env loaded; the CLI's design (human-run, stderr diagnostics) is correct for a human and invisible for a scheduler.

**How to avoid:**
- Run under systemd with an `EnvironmentFile=` (mode 0600, outside the repo) or explicit `Environment=` entries, so stdout/stderr and the exit code land in the journal per run (`journalctl -u <unit>`).
- Add `OnFailure=` for alerting, and consider `RandomizedDelaySec=` to avoid a fleet-wide thundering herd.
- Smoke it by hand first: `systemctl start <unit>.service` before `enable --now <unit>.timer`, so the service half is proven independently of the schedule.
- Record a per-run heartbeat the operator can query (the initial schema already has `ingestion_jobs` / `activity_events`), so "the schedule stopped" is detectable rather than guessed.
- Keep secrets out of unit files and out of logs — follow the existing `repr=False` / `.env.example`-names-only / redaction conventions.

**Warning signs:**
- A timer whose only evidence is a crontab line.
- `ConfigurationError` in the journal on the first unattended run.
- No `OnFailure=` / no alerting path.
- Secrets pasted into a unit file or a wrapper script.

**Phase to address:** Phase 22.

---

### Pitfall 20: Timezone/DST and catch-up semantics for a weekly-ish schedule

**What goes wrong:**
`OnCalendar` is evaluated in the timer's timezone. A schedule near the DST transition can be skipped during the spring-forward missing hour, or fire twice (or be skipped entirely) during the duplicated fall-back hour. `Persistent=true` fires **one** catch-up run after downtime — it does not replay every missed interval, so relying on it for "we must not miss a week" is wrong, while using it for a job that must stay inside a maintenance window is equally wrong.

**Why it happens:**
Cron uses system local time and mostly does "the right thing" by luck; systemd makes the timezone explicit and therefore exposes the choice.

**How to avoid:**
- Pin the timezone in the unit and choose an hour away from the 02:00–03:00 transition.
- Decide `Persistent=` deliberately and document which one was chosen and why.
- Because the job is "collect new videos", design it to be catch-up-safe: the incremental high-water mark (Pitfall 21) means a missed or late run simply picks up more, so correctness does not depend on the run firing exactly once.

**Warning signs:**
- No timezone in the unit, or a schedule in the transition hour.
- `Persistent=true` used without a stated reason.
- A plan that treats "ran once a day" as a correctness requirement.

**Phase to address:** Phase 22.

---

### Pitfall 21: Re-processing the same videos because listing is not incremental

**What goes wrong:**
The unique `youtube_video_id` prevents duplicate *materials*, but it acts **after** captions + LLM have been paid for: the CLI resolves the video, fetches captions, calls the LLM, and only then reaches `persist_draft_and_enqueue`, which returns `already_saved`. A scheduler that re-lists an entire channel/playlist every run therefore re-pays for every already-saved video, and run duration grows with channel size until the job overruns its own interval.

**Why it happens:**
"idempotent" is conflated with "cheap to re-run". The idempotency lives in the persist RPC; the expensive work happens before it.

**How to avoid:**
- Keep a per-source high-water mark (last seen `contentDetails.videoPublishedAt` or last seen video id) and only submit videos newer than it.
- Do the filtering at the listing step, before the pipeline; do not rely on the persist RPC to filter.
- Lock it with a test: a re-scan of an unchanged playlist performs **zero** LLM calls.
- Also bound the run (max videos per invocation) so a large first backfill cannot run forever.

**Warning signs:**
- `already_saved: true` appearing for most videos on every run.
- Run duration growing linearly with channel age.
- A scheduler script that lists everything with no cursor/state.

**Phase to address:** Phase 22.

---

### Pitfall 22: Listing a channel/playlist — key vs OAuth, and quota maths

**What goes wrong:**
Listing uploads needs the YouTube Data API. `search.list` costs **100 quota units**, while `playlistItems.list` costs **1**; Google's own guidance is to resolve the channel's uploads playlist via `channels.list(part=contentDetails)` and then page through `playlistItems.list` (~6 units total). Additionally `channels.list(mine=true)` needs **OAuth** with `youtube.readonly`, not an API key — so an API-key-only design must resolve a channel handle/id to its uploads playlist instead. The default project quota is 10,000 units/day, shared with anything else using the key, and paging (`pageToken` / `nextPageToken`) is mandatory for a channel with more than `maxResults` uploads.

**Why it happens:**
`search.list` is the method everyone reaches for, and it is the single most expensive one. The ADR-0002 constraint (contour isolation, no public foreign APIs) also means the listing dependency must be evaluated on its own, not assumed.

**How to avoid:**
- Settle the key-vs-OAuth decision and the channel→uploads-playlist resolution in a spike/ADR **before** the scheduler phase can pass (PROJECT.md already flags this as a v1.3 key risk).
- Use `channels.list` → `contentDetails.relatedPlaylists.uploads` → `playlistItems.list`; never `search.list` for a known channel.
- Handle pagination to exhaustion and make the listing failure mode a distinct, closed reason in the CLI's reason vocabulary rather than a generic failure; quota exhaustion is not retryable within the same day.

**Warning signs:**
- `search.list` in the listing adapter.
- A hard-coded `maxResults` with no `nextPageToken` loop.
- Quota-exhaustion errors treated as transient.
- The key/OAuth decision still open when implementation starts.

**Phase to address:** Phase 22 (decision earlier, in the roadmap/spike).

---

### Pitfall 23: The scheduler becoming a publish/send path

**What goes wrong:**
An unattended job that reaches publication or the digest send would deliver drafts to real readers without a human. This is explicitly out of scope for v1.3 ("drafts only, never auto-publish or auto-send"), and it is easy to introduce by "reusing" the wrong entry point.

**Why it happens:**
The backend and the CLI share a database; a scheduler that imports `backend` gets `publish_material` and `send_digest` for free.

**How to avoid:**
- The timer must invoke only the collection/persist path (`ingestion-service` CLI → `persist_draft_and_enqueue`), never `backend` publish/send use cases, and never `POST /admin/shortlist/send`.
- Add a guard test that the scheduled entry point does not import `backend` / reference `send_digest` / `publish`.
- Keep the scheduler outside the app container's lifecycle; it is a host-level concern, not an app feature.

**Warning signs:**
- `backend` in the scheduler script's imports.
- Any `publish`/`send_digest` reference in the unit or wrapper.
- Drafts disappearing from the shortlist without an admin action.

**Phase to address:** Phase 22.

---

### Pitfall 24: Mock/live divergence makes the fix invisible to — or unprovable by — the offline Playwright suite

**What goes wrong:**
`playwright.config.js` forces `VITE_USE_MOCKS=true`. `web/src/data/mock.js`'s `materials` array has **no status field at all**, and `getMaterialById` returns a material for any id in the list. So (a) the 999.1 draft→404 bug is **structurally unreproducible** in the offline suite — no mock material is a draft — and (b) the 999.7 validator is server-side and entirely absent from the SPA mock path. A plan that tries to write the RED test as a Playwright test will either be unable to fail, or will fail for a mock reason and then be "fixed" in the mock.

**Why it happens:**
The mock layer models the *published* world; drafts became a first-class state only with the v1.1 ingestion work, and the mock never caught up.

**How to avoid:**
- Put the RED test for 999.1 in pytest HTTP tests (`tests/unit/test_http_materials.py` already has the ready-only harness) and the RED test for 999.7 in the validator/HTTP config tests. Playwright is the *integration* proof, not the primary RED.
- If a Playwright proof is genuinely needed, give the mock a draft state **first** — as its own TDD change with its own RED — and keep the mock's shape honest (a `status` field), rather than special-casing a slug.
- Never "fix" a failing test by editing the mock to match the buggy assumption.

**Warning signs:**
- A Playwright test asserting a 404 for a slug that the mock happily serves.
- A mock edit introduced inside the same plan as the production fix with no separate RED.
- A merge-key/config test written as a browser test.

**Phase to address:** Phases 17, 18, 19 (any phase whose RED test is browser-only).

---

### Pitfall 25: Breaking the byte-identical CLI stdout contract

**What goes wrong:**
`tests/unit/test_cli_ingest_contract.py` locks the happy path exactly: `result.stdout.splitlines() == EXPECTED_SUCCESS_LINES` and `result.stderr == ""`. Any scheduler convenience — a "polling playlist…" line, a per-video banner, a `--source` flag that prints, or progress output pushed to stdout — breaks the contract immediately. Symmetrically, a scheduler that consumes stdout and *also* relies on stderr JSON for error detection needs the existing stderr-only error envelope preserved.

**Why it happens:**
A batch scheduler naturally wants to report progress, and stdout is where progress usually goes. This repo's contract is the opposite: stdout is the machine-readable success payload, stderr is diagnostics.

**How to avoid:**
- The scheduler must not modify `cli.py`'s output paths. Anything new goes to **stderr**, and behind an opt-in flag — the `--debug` precedent (Phase 15: opt-in, stderr-only, default path byte-identical, `StageDiagnostics`/`Clock` ports, `NullDiagnostics` no-op).
- Keep the stdout contract test untouched. If a multi-video/bulk mode is added, give it its **own** contract test rather than widening the single-video one.
- If the scheduler wraps the CLI, do the aggregation in the wrapper (shell/systemd), not inside the command.

**Warning signs:**
- Any diff under `ingest-service/src/ingestion_service/cli.py` in a scheduler phase.
- A new `typer.echo(...)` without `err=True`.
- `EXPECTED_SUCCESS_LINES` edited.
- Progress text appearing in a captured stdout assert.

**Phase to address:** Phase 22 (and any phase that touches the CLI).

---

### Pitfall 26: Additive port changes that actually ripple — `Mailer`, `ProfileRepository`, `AppContainer`

**What goes wrong:**
The natural MAIL-01 shape (mailer needs the recipient list; the audience needs a list method) touches three seams that are locked by tests: `Mailer.send_digest` is a `Protocol` with keyword-only args (adding a required argument breaks `StubMailer`, `test_stub_mailer.py`, and `test_send_digest.py`); `ProfileRepository` is a `Protocol` implemented by `SupabaseProfileRepository` and an in-memory fake; and `AppContainer` fields are constructed explicitly in tests (`test_app_container_still_constructs_without_pipeline_kwargs` exists precisely because a new field once broke this). `resolve_mailer` is annotated `-> StubMailer` and raises for `smtp`, which is the documented fail-fast contract.

**Why it happens:**
Ports feel cheap to change because they are "just interfaces" — but each one has an in-memory fake and a container test acting as a tripwire, and the fail-fast `MAILER=smtp` behaviour is documented in the runbook as intentional.

**How to avoid:**
- Make port changes **additive with defaults**; update the in-memory fakes first (RED), then the live adapter, then the wiring.
- Keep `test_composition_container.py` / `test_live_container_wiring.py` green as the wiring gate, and be deliberate about changing a fail-fast that the runbook documents.
- Keep the mailer's secret fields `repr=False` and mirror the `.env.example` names-only convention (`test_env_example.py` asserts the name list).
- Update the `Mailer` docstring's claim ("stub always returns `stubbed`") when the contract changes, or the next session will trust a stale docstring.

**Warning signs:**
- A required new keyword-only arg on a port method.
- `StubMailer`/in-memory fakes updated *after* the production change instead of before.
- A container-wiring test edited to accommodate a new field rather than the field defaulted.
- `.env.example` gaining values instead of names.

**Phase to address:** Phase 21 (and Phase 20 if the app-mailer path is chosen).

---

### Pitfall 27: Live-contract drift — apply order, migration idempotency, and stale verification

**What goes wrong:**
Three process pitfalls that have bitten this repo before: (a) a live migration applied **after** the code deploys (or an RPC signature change applied in the wrong order) leaves the window where new code calls an old function — the shared VM must never be reset, and migrations are applied by hand via Studio SQL; (b) a source fix landing *after* the phase verifier ran makes the covered digest stale (the v1.2 retrospective's lesson #4; Phase 16 needed two stale re-verifications); (c) `core.autocrlf=true` makes covered-file digests line-ending sensitive.

**Why it happens:**
These are scheduling/ordering mistakes, not coding mistakes, and each one has a plausible local justification ("fix it now, verify after").

**How to avoid:**
- Write migrations idempotently (`add column if not exists`, `create or replace function` with **defaulted** new parameters), document an apply-then-deploy ordering in the runbook, and keep the operator SQL step explicit and blocking (as migration 011 established).
- Order the tail gates review → verify; if a fix lands after verification, restamp the covered digest.
- Pin `eol=lf` for covered files so cross-platform checkouts do not churn fingerprints.
- Close debug sessions in the same change that ships their fix.

**Warning signs:**
- A migration plan without an "apply before deploy" note or with a non-idempotent DDL body.
- A review fix committed after `verify` with no re-verification.
- A `git status` full of stat-dirty covered files.

**Phase to address:** All phases (process gate); explicitly Phase 21 if the delivery columns change.

---

### Pitfall 28: Existing tests that encode the old contract — amend deliberately, never delete

**What goes wrong:**
Every v1.3 fix lands next to a test that asserts the *current* behaviour. Silently deleting or weakening one converts a deliberate behaviour change into a hidden regression.

**The v1.3 tripwire list:**

| Existing test / contract | Asserts today | v1.3 pressure on it |
|---|---|---|
| `test_materials_draft_slug_returns_404_not_403` | draft slug → 404 on the reader route | 999.1 (Pitfall 1) |
| `tests/admin.spec.js` "pipeline config dirty gating arms the unsaved-leave guard" | a `dialog` appears on a synthesised `beforeunload` | 999.6 (Pitfall 3) |
| `test_put_invalid_error_rows_are_verbatim_and_top_level` + zero-writes asserts | strict reject envelope `{errors:[…]}`, zero writes | 999.7 (Pitfall 7) |
| `test_put_deeply_nested_yaml_returns_400_not_500` / `..._control_char_...` | structured 400 for parser-level abuse | 999.7 bound (Pitfall 8) |
| `test_send_digest.py` `delivery_status == "stubbed"` / audit `delivery_status` | stub-era delivery contract | MAIL-01 (Pitfall 11) |
| `test_send_audit_failure_after_publish_still_returns_success` | post-publish failures must not fail the send | MAIL-01 (Pitfall 10) |
| `tests/auth.spec.js` "shows Логин as shell identity after register" | register → session → `/` | MAIL-02 (Pitfall 15) |
| `test_auth_email_domain.py`, `domain_not_allowed` 403 in `deps.py` | two-domain server gate | MAIL-02 (Pitfall 16) |
| `test_cli_ingest_contract.py` `EXPECTED_SUCCESS_LINES` + `stderr == ""` | byte-identical CLI stdout | scheduler (Pitfall 25) |
| `test_stub_mailer.py`, `test_composition_container.py`, `test_live_container_wiring.py` | port signatures, container field set, fail-fast `MAILER=smtp` | MAIL-01 (Pitfall 26) |

**How to avoid:**
- For each row, the plan must state *amend* or *preserve*, with the reason. "Deleted because it was failing" is not a valid disposition.
- Where a test is amended, the new assertion must be *stronger* (e.g. draft-slug 404 stays and gains an admin-route positive case; the guard test gains the SPA-navigation proof).
- Where a contract legitimately changes (delivery status, register session), update the in-memory fake and the test together, and record the decision in PROJECT.md's decision log.

**Warning signs:**
- A diff whose only test change is a deletion or an `assert` loosening.
- `pytest -q` count dropping.
- A contract change with no PROJECT.md decision row.

**Phase to address:** All phases (each phase plan owns its rows).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Serve drafts through the reader route with an admin query flag | One-line fix for 999.1 | The reader route is no longer ready-only; every future caller must remember the flag | Never — add an admin-gated surface instead |
| `useBlocker` bolted onto `<BrowserRouter>` via a shim | Avoids the router migration | Throws or silently no-ops; the guard looks present and is not | Never |
| Scan duplicate keys after `flatten_mapping` | Removes the merge-tag error | Rejects valid local-over-merged documents (merge keys become useless) | Never |
| Skip merge keys **without** adding a merge-expansion bound | Fixes WR-01 with a tiny diff | A ~600-char document hangs the request; a fail-closed reject becomes an accepted DoS | Never for the bound; ship the bound with the fix |
| Swap `_StrictSafeLoader` for `yaml.safe_load` | Fewest lines | Silently drops duplicate-key rejection (PIPE-02) | Never |
| Catch only `PersistenceError` around mail | Matches the stub's failure surface | A live SMTP failure 500s a published digest (D-87/D-88 violation) | Never once the mailer is real |
| Stamp `delivery_status`/`recipient_count` before mail and ignore the mailer's return | Zero schema work | The honesty requirement (MAIL-01) is unmet while the API looks green | Never for MAIL-01's acceptance criterion |
| Flip `MAILER_AUTOCONFIRM` off to "fix" MAIL-02 | Looks like the direct fix | Re-introduces the v1 signup 500 and breaks a shipped Playwright test | Only with the register-flow test amendment + a relay smoke + rollback |
| Recipients in the `To:` header | Easiest `send_message` call | Internal distribution list exposed to every recipient and relay log | Never |
| `search.list` for channel listing | Familiar method | 100 units/call against a 10,000/day quota | Never for a known channel |
| Re-list the whole playlist each run | No cursor state to maintain | Re-pays captions + LLM for every saved video; runs overrun their interval | Never |
| Rely on the CLI's `already_saved` as the overlap guard | No `flock`/unit config | Duplicate work, extra batches, concurrent shortlist writes | Never |
| Add the guard mechanism and the router migration in one plan | One less plan | A `useBlocker` throw is misattributed to the migration | Never — separate plans |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Self-hosted Supabase Auth (GoTrue) | Assuming "no confirmation mail" is a code bug | It is the deliberate `GOTRUE_MAILER_AUTOCONFIRM=true` state (runbook §4.1); diagnose the setting first |
| GoTrue email settings | Configuring only `SMTP_HOST` | `GOTRUE_SMTP_ADMIN_EMAIL` is required (the `From`); `GOTRUE_SMTP_MAX_FREQUENCY` (default 900 s) and the **global** `GOTRUE_RATE_LIMIT_EMAIL_SENT` (default 30) shape available behaviour |
| GoTrue signup surface | Assuming the corporate domain list gates signup | It does not — the gate is client-side plus a post-auth 403; add a signup-edge check |
| SMTP relay (starttls) | `starttls()` against a 465 relay, or plaintext fallback after a TLS failure | Explicit TLS mode + port pairing; never downgrade after a TLS error; `starttls()` raises `SMTPNotSupportedError` when not advertised and `SMTPResponseException` on 454/501 |
| SMTP relay (timeouts) | Not passing `timeout=` to the SMTP constructor | Always bound the connect/handshake/send; `timeout=0` raises `ValueError` |
| SMTP headers | Audience in `To:` | Single stable `To` + audience in `Bcc`; verify no `Bcc` leaks into transmitted headers |
| Supabase `profiles` | Reading the audience through the publishable client | `profiles` RLS allows only own-row select; read via the service-role client wired in `composition/live.py` behind a new port method |
| YouTube Data API | `search.list` / `channels.list(mine=true)` with an API key | `search.list` is 100 units; `mine=true` needs OAuth. Use `channels.list(part=contentDetails)` → uploads playlist → `playlistItems.list` (1 unit) with `pageToken` |
| Playwright mock layer | Assuming the browser suite can reproduce a draft-404 or a server-side YAML reject | `VITE_USE_MOCKS=true` is forced; `mock.js` materials have no `status`. Make the RED test pytest |
| systemd/journald | cron-style job with env inherited from the operator shell | `EnvironmentFile=` (0600) + journal capture + `OnFailure=` + `RuntimeMaxSec=` |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Merge expansion in `flatten_mapping` | Validator request hangs; CPU pinned | Bound merge depth / flattened entries; reject nested merges; node budget before construction | Measured: **610 chars, fanout 3, 15 levels > 10 s**; 20,000-char cap allows hundreds of levels |
| Duplicate scan over a post-merge node list | Same as above, once flatten-then-scan is chosen | Keep the scan on the pre-merge own-key list | Same threshold as above |
| Parser-deep nesting | `RecursionError` surfaced as 500 before WR-02 | Already handled: `_TOO_DEEP_MESSAGE` structured 400 | Depth > `sys.getrecursionlimit()`; tests derive depth from the limit (IN-02 coupling) |
| Alias chains ("billion laughs") | Feared, but not the amplifier here | Not the measured risk: aliases are shared refs (200 levels loaded in 15 ms). Do not weaken the loader over it | Only if a fix starts deep-copying merged/aliased structures |
| Synchronous SMTP per recipient | Admin send latency grows with `len(profiles)`; request timeouts | One transaction with `Bcc`, bounded timeouts, audience cap, or an out-of-request delivery path | Tens of recipients on a slow relay |
| Re-listing a whole channel per run | Run duration grows with channel age; captions/LLM cost repeats | Incremental high-water mark at the listing step | Every run after the first |
| `profiles`-sized audience query on every send | Adapter latency; N+1 if built per-recipient | One select for the audience, filtered by the corporate domain rule | Hundreds of profiles |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Draft exposure via a loosened reader route or a new preview path | Unpublished/internal material read by any authenticated user; slug enumeration | Keep the reader route ready-only; admin-gate the preview; keep missing≡draft (404, never 403); negative tests |
| Draft leak via `related`/`tags`/cache headers | Unpublished relations and an existence oracle through caches | Reuse the ready filters; `Cache-Control: private, no-store` on draft responses; no canonical/SEO metadata for drafts |
| Open email-sending endpoint at GoTrue signup | Relay abuse from arbitrary addresses; signup enumeration; a global rate limit that can lock out real registration | Domain check at the signup edge; non-enumerating SPA copy; keep the FastAPI 403 gate |
| Confirmation token in logs / free-form `redirect_to` | Account takeover via log access; open redirect / phishing from corporate mail | Never log tokens/links; allowlisted redirect origin; single-use, short-lived tokens |
| SMTP credentials in unit files, wrapper scripts, or logs | Secret leakage outside Cloud.ru/SecretRegistry | Env/`EnvironmentFile` only, `repr=False` on settings, `.env.example` names only, extend the redaction discipline to new logging |
| Full recipient list in message headers or relay logs | Internal distribution list disclosure (PII) | `Bcc` audience; single stable `To` |
| Unvalidated `profiles.email` in the audience | Internal digest delivered outside the corporate contour | Filter with `is_allowed_corporate_email`; no dynamic domain list (ADR-0003) |
| New RLS policy on `profiles` to enable enumeration | Weakens the profiles data boundary for a mailer convenience | Service-role adapter behind a port, wired only in composition |
| Mail failure surfaced as a transport error after publish | Admin retries a published digest → 409 contradiction; operator believes mail failed when the issue is live | Map SMTP exceptions at the adapter boundary; catch them in `send_digest`; keep publish/mail ordering documented |
| Scheduler reaching publish/send | Unattended publication to real readers | Restrict the entry point to collection+persist; add an import guard test |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Draft link lands on «Материал не найден» | Admin believes the material is broken/lost | Open the admin-gated preview (body already loaded in the shortlist DTO); no reader-route 404 for an admin action |
| Browser-default unload prompt with no copy | User loses a typed config with no explanation | In-app modal with the existing Russian copy; `beforeunload` as a silent hard-navigation backstop only |
| Prompt after a successful save | User distrusts the save button | Clear dirtiness before navigating; `allowLeave` flag |
| Double prompt (modal then browser dialog) | Confusing, looks broken | One guard owns the message; the other defers to it |
| Merge-key document rejected with an internal-tag string | Admin sees an untranslatable English implementation detail and cannot fix the file | Skipping the merge tag removes the error entirely; any remaining merge reject uses Russian copy in the same error-row shape |
| Merge bomb hangs the save | Editor freezes; no error, no revert | Bound the expansion and return the structured 400; the SPA's retry path already exists |
| Live send reports "stubbed"/0 recipients | Admin cannot tell whether mail went out — the honesty goal of MAIL-01 | Report the mailer's real status/count; label `profiles`-derived counts precisely |
| Silent scheduler death | Everyone assumes ingestion runs; drafts stop appearing with no signal | Journal + `OnFailure=` alert + queryable per-run heartbeat |
| Email-preview link behaves oddly inside the sandboxed frame | "Открыть материал" from the HTML preview may navigate the iframe itself rather than the app | Rule out as a second cause of 999.1 before concluding the fix works — the preview iframe is `sandbox=""` (no `allow-same-origin`, no `allow-top-navigation`), so a link click cannot reach the top-level app. Decide whether the preview should expose an out-of-frame CTA instead |

## "Looks Done But Isn't" Checklist

- [ ] **999.1 reader honesty:** the draft link opens an admin-gated surface — verify `test_materials_draft_slug_returns_404_not_403` still passes **and** a new test proves an admin's reader-route call for a draft is still 404.
- [ ] **999.1 second cause ruled out:** the email-preview "Читать →" behaviour inside the `sandbox=""` iframe is explained, not assumed — verify by opening the preview and clicking.
- [ ] **999.1 no leak:** a draft-preview payload has no `related`/`tags`, carries `no-store`, and emits no canonical/SEO metadata.
- [ ] **999.6 handler contract:** `beforeunload` calls `preventDefault()` + sets a truthy `returnValue`, contains no `window.confirm`, is attached only when dirty, and is removed on unmount/save.
- [ ] **999.6 SPA navigation:** clicking a shell nav link with a dirty editor prompts once; cancel keeps the draft; confirm navigates exactly once.
- [ ] **999.6 save/reject:** save→navigate does not prompt; a server reject keeps the guard armed and the document dirty.
- [ ] **999.6 router:** `useBlocker` is used only under a data router, or was deliberately avoided — verify the console is free of `useBlocker must be used within a data router`.
- [ ] **999.7 merge accepted:** a merge document loads and equals the `yaml.SafeLoader` result (loop over cases, `SafeLoader` as oracle).
- [ ] **999.7 override accepted:** a local key overriding a merged key is accepted and the local value wins.
- [ ] **999.7 strictness kept:** genuine duplicate keys — with and without a `<<` present — are still rejected, and the reject body is the verbatim `{errors:[…]}` with zero writes.
- [ ] **999.7 bounded:** a nested-merge bomb well under `MAX_PIPELINE_CONFIG_CHARS` is rejected as a structured 400 within a couple of seconds.
- [ ] **999.7 loader unchanged:** still a `SafeLoader` subclass; `Loader=` argument untouched; `yaml` not imported from `domain/`/`application/`.
- [ ] **MAIL-02 diagnosis recorded:** the current `mailer_autoconfirm` value, GoTrue SMTP vars, and the chosen product contract are written down before implementation.
- [ ] **MAIL-02 signup gate:** a non-corporate address cannot trigger a confirmation email; `deps.py`'s `domain_not_allowed` gate and its tests are intact.
- [ ] **MAIL-02 register flow:** `tests/auth.spec.js` was deliberately amended (not deleted) if the post-register UX changed; the relay smoke and rollback steps are in the runbook.
- [ ] **MAIL-02 token safety:** no confirmation token/URL in logs; redirect origin allowlisted; tokens single-use.
- [ ] **MAIL-01 failure isolation:** a mailer raising a real SMTP exception still returns a successful `SendDigestResult`, with `sent_at` stamped and the issue published.
- [ ] **MAIL-01 honesty:** the API response, the audit ping, and the batch row all report the mailer's actual status and recipient count; `test_send_digest.py`'s stub-era assertions were consciously replaced.
- [ ] **MAIL-01 audience:** read via a service-role port (no new RLS policy), filtered by the corporate domain rule, placed in `Bcc`, with the "profiles ≠ all authorized users" caveat recorded.
- [ ] **MAIL-01 transport:** explicit TLS mode + port pairing, bounded timeouts, no plaintext fallback, relay choice settled in an ADR/spike.
- [ ] **Scheduler isolation:** systemd `Type=oneshot` + timer (plus `flock` if a second trigger path exists), `EnvironmentFile=` 0600, `OnFailure=`, `RuntimeMaxSec=`, timezone pinned, `Persistent=` justified.
- [ ] **Scheduler efficiency:** an unchanged playlist re-scan performs zero LLM calls; a per-source high-water mark exists; a per-run video cap exists.
- [ ] **Scheduler scope:** the job cannot reach publish/send (import/reference guard test).
- [ ] **Regression gates:** `pytest` count did not drop; the Playwright web + admin + auth suites are green; `EXPECTED_SUCCESS_LINES` and `stderr == ""` still hold.
- [ ] **Process:** migrations are idempotent with an apply-before-deploy note; review ran before verify; affected debug sessions closed with their fix.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Draft exposed through the reader route | HIGH | Revert the route to ready-only immediately; audit access logs for the draft slugs served; decide whether the material must be unpublished/re-edited; add the negative tests |
| Draft leaked via cache/SEO metadata | MEDIUM | Purge the cache/CDN entries; add `no-store`; re-check canonical/og output for the affected slugs |
| `useBlocker` throw after a router migration | MEDIUM | Revert to the previous `App.jsx` router (one file) and re-run the full Playwright suite; reintroduce the guard without the migration |
| Unsaved config lost through in-app navigation | LOW | The DB is safe (no save → no write); the operator re-types; keep the typed text visible until the guard ships (the draft is only in memory) |
| Valid merge-key config rejected (current WR-01) | LOW | Already fail-closed: rewrite the document without `<<` (the 4-key schema needs no merge); the admin sees the structured error |
| Merge bomb hangs the validator | MEDIUM | Kill the request; confirm nothing was written (validate-before-persist); ship the bound before re-enabling merge acceptance |
| Duplicate keys silently accepted after a loader swap | HIGH | Restore `_StrictSafeLoader`; re-run `test_put_invalid_error_rows_are_verbatim_and_top_level`; audit saved configs for double keys |
| Live send 500s while the digest is published | MEDIUM | Do not re-send (409 by design); confirm the issue exists and the email was likely delivered; widen the exception handling; verify `sent_at`/publish integrity |
| Recipient count reported as 0 for a real send | LOW | The issue is live and links are valid; correct the reported fields in a patch; reconcile from the relay's logs |
| Signup 500s after the autoconfirm flip | HIGH | Re-enable `GOTRUE_MAILER_AUTOCONFIRM=true` (documented rollback) to restore registration; fix the relay; re-attempt the flip with the register-flow test amendment |
| Non-corporate signup triggered corporate mail | MEDIUM | Add the signup-edge domain check; review the relay's sent log for the affected addresses; rotate relay credentials if abused |
| Overlapping scheduled runs | LOW | Kill the duplicate; `flock` and/or remove the duplicate trigger; check for a second unsent batch and reconcile the shortlist |
| Silent scheduler death discovered late | MEDIUM | Load the env file; re-run the missed window by hand (the CLI is idempotent per video); add `OnFailure=` + heartbeat before re-enabling |
| Scheduler re-processing every video | LOW | Add the high-water mark; the duplicate materials were already prevented by the unique `youtube_video_id`; the cost was LLM tokens and time |
| CLI stdout contract broken | MEDIUM | Revert `cli.py`; re-run `test_cli_ingest_contract.py`; move the new output to stderr behind a flag |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 — reader route loosened | 17 | `test_materials_draft_slug_returns_404_not_403` still green + new admin-route positive/negative tests; no draft status escape in `get_material_for_reader.py` |
| 2 — join/cache/SEO leak | 17 | draft-preview payload test: no `related`/`tags`, `no-store` header; published-issue material never demoted test |
| 3 — `window.confirm` in `beforeunload` | 18 | source lock: no `window.confirm` in the handler; handler-contract unit test; no dialog assertion after a synthetic event |
| 4 — `useBlocker` without a data router | 18 | console free of the data-router error; full Playwright suite green after any router change; migration and guard in separate plans |
| 5 — guard on save / double prompt | 18 | four Playwright cases: save→navigate, reject→navigate, confirm→navigate (one prompt), cancel→stays dirty |
| 6 — merge tag has no constructor | 19 | merge document loads in the strict loader; no `tag:yaml.org,2002:merge` in any response body |
| 7 — flatten-then-scan false positive | 19 | local-over-merged accept test; genuine-duplicate reject test (with and without `<<`) |
| 8 — merge expansion DoS | 19 | nested-merge bomb (< cap) rejected as a structured 400 with a time bound; merge depth/entry guard present |
| 9 — wrong loader / alias confusion | 19 | `SafeLoader` subclass intact; duplicate-key test still green; no `safe_load`/`FullLoader` in the diff |
| 10 — SMTP exception escapes `send_digest` | 21 | mailer-raises-SMTPException test returns success with `sent_at` stamped and the issue published |
| 11 — pre-mail delivery stamp | 21 | response/ping/batch-row `delivery_status` + `recipient_count` equal the mailer's actual result |
| 12 — TLS mode / timeouts / sync path | 21 | explicit TLS config test; bounded-timeout test; send latency independent of audience size (or an out-of-request path) |
| 13 — audience port/PII/domain/`profiles` gap | 21 | service-role-only audience read; `Bcc` header test; domain filter test; documented `profiles` caveat |
| 14 — MAIL-02 misdiagnosed | 20 | recorded `mailer_autoconfirm` + SMTP vars + chosen contract at phase start; debug session closed with the fix |
| 15 — autoconfirm flip regressions | 20 | `tests/auth.spec.js` amended (not deleted); relay smoke before the flip; rollback step in the runbook |
| 16 — open signup / client-only domain gate | 20 | non-corporate signup cannot trigger mail; `test_auth_email_domain.py` + `domain_not_allowed` intact |
| 17 — token/redirect handling | 20 | no token in logs; allowlisted redirect; single-use token test |
| 18 — overlapping runs | 22 | `Type=oneshot` + timer (and `flock`); no two concurrent `ingest` processes; no duplicate trigger path |
| 19 — silent failure / cron env | 22 | journal entry per run with an exit code; `OnFailure=`; hand-run service smoke before enabling the timer; heartbeat queryable |
| 20 — DST / catch-up | 22 | timezone pinned; schedule away from the transition hour; `Persistent=` justified |
| 21 — re-processing videos | 22 | unchanged-playlist re-scan performs zero LLM calls; high-water mark present; per-run cap present |
| 22 — key vs OAuth / quota | 22 (decision earlier) | ADR/spike recorded; `channels.list`→uploads→`playlistItems.list`; `nextPageToken` loop; quota exhaustion is a distinct non-retryable reason |
| 23 — scheduler reaches publish/send | 22 | import/reference guard test; no `backend`/`send_digest`/`publish` in the scheduled entry point |
| 24 — mock/live divergence | 17, 18, 19 | the RED test for each is pytest; any mock change is a separate TDD change |
| 25 — CLI stdout contract | 22 | `test_cli_ingest_contract.py` untouched and green; no new stdout output |
| 26 — additive port ripples | 20, 21 | in-memory fakes updated first; container-wiring tests green; `repr=False` + `.env.example` names-only |
| 27 — apply order / stale verification | all (explicit in 21) | migrations idempotent with an apply-before-deploy note; review before verify; digest restamped after post-verify fixes |
| 28 — old-contract tests deleted | all | the tripwire table above is dispositioned per phase; `pytest` count non-decreasing |

## Sources

**Measured on this checkout (highest confidence — reproduced locally, 2026-10-14, PyYAML 6.0.3 / Python 3.14.0):**
- `_StrictSafeLoader` on a merge-key document → `ConstructorError | could not determine a constructor for the tag 'tag:yaml.org,2002:merge'`; the same document loads correctly under `yaml.SafeLoader`. (Pitfall 6)
- Scan duplicate keys **after** `flatten_mapping` → `ConstructorError | found duplicate key ('y')` for a document `SafeLoader` resolves to `{'x': 1, 'y': 3}`. (Pitfall 7)
- With the fix (skip the merge tag, scan before flatten): merge documents, list-of-merges, and local-over-merged overrides all load; genuine duplicates — with and without a `<<` — are still rejected; a self-merge cycle is handled. (Pitfalls 6, 7)
- Merge expansion: fan-out 3 at 8/10/12/13/14/15 levels → 312/390/478/522/566/610 chars and 14/116/838/2377/8273/>10000 ms. (Pitfall 8)
- Alias chains: `yaml.safe_load` at 10/16/20/30/200 levels → 1.9/2.1/1.8/2.5/15.4 ms; aliases are shared references, so alias expansion is not the amplifier in this path. (Pitfall 9)
- `flatten_mapping` entry growth without construction (fan-out 2 at 5/9/12/14/16 levels → 126/2046/16382/65534/262142 flattened mapping entries from 176–568-char documents). (Pitfall 8)

**Repository sources (authoritative for this system's contracts):**
- `.planning/PROJECT.md` — v1.3 scope, D-87/D-88 publish-on-send, ADR-0002/0003, the YouTube key risk, "drafts only, never auto-send".
- `.planning/ROADMAP.md` — backlog 999.1 / 999.6 / 999.7 details (WR-01, WR-04, WR-05).
- `.planning/STATE.md` — blockers/concerns, Phase 16 advisories (WR-01, IN-01…IN-03).
- `.planning/RETROSPECTIVE.md` — lessons: close debug sessions with the fix; live mail is separate from the product path; review-before-verify; `eol=lf` for covered digests.
- `.planning/milestones/v1.2-MILESTONE-AUDIT.md` — W-1 (draft reader link), W-2/W-5 resolutions, E2E flow table.
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-REVIEW.md` — WR-01 text, IN-01 Pydantic lax coercion, IN-02 recursion-limit coupling, IN-03 tautological assertions.
- `.planning/debug/g-01-3b-signup-mailer.md` — the original GoTrue SMTP 500 and the autoconfirm remedy.
- `docs/agents/local-platform-runbook.md` §4.1 — autoconfirm on/off procedure, "do not ship email-dependent features until the mailer is healthy", `MAILER=smtp` fail-fast.
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — contour isolation, no public foreign APIs, secrets inside Cloud.ru.
- `docs/adr/0003-email-domain-restriction.md` — fixed two domains, no dynamic admin-managed list.
- Source read: `backend/.../use_cases/send_digest.py` (mail-catch scope, discarded mailer return), `backend/.../ports/digest_publisher.py` + `supabase-integration/.../digest_publisher.py` (pre-mail delivery stamp), `supabase-integration/migrations/005` (`p_delivery_status`/`p_recipient_count` defaults), `backend/.../infrastructure/stub_mailer.py` (`resolve_mailer` fail-fast, `SmtpMailer` placeholder), `backend/.../infrastructure/yaml_pipeline_config_validator.py`, `backend/.../interface/http/routes/materials.py` + `use_cases/get_material_for_reader.py`, `backend/.../interface/http/deps.py`, `backend/.../composition/{live,settings}.py`, `web/src/App.jsx`, `web/src/pages/AdminPipelineConfigPage.jsx`, `web/src/pages/MaterialPage.jsx`, `web/src/pages/RegisterPage.jsx`, `web/src/data/mock.js`, `web/src/services/pipelineConfigApi.js`, `web/src/services/contentApi.js`, `playwright.config.js`, `ingestion-service/.../cli.py`, `ingestion-service/.../use_cases/ingest_pipeline.py`, `tests/unit/test_http_materials.py`, `tests/unit/test_http_pipeline_config.py`, `tests/unit/test_send_digest.py`, `tests/unit/test_cli_ingest_contract.py`, `tests/admin.spec.js`, `tests/auth.spec.js`.

**External documentation (Context7 / web, MEDIUM confidence — all marked "verified" at the MEDIUM tier, none presented as authoritative-only):**
- React Router — `useBlocker(shouldBlock)` signature, `Blocker` state machine (`unblocked`/`blocked`/`proceeding`, `proceed()`, `reset()`), the explicit "does not handle hard-reloads or cross-origin navigations" note, and the source-level requirement that `useDataRouterContext` be present (declarative `BrowserRouter` provides only navigation/location contexts, so `useBlocker` is unsupported there).
- MDN — `beforeunload`: call `preventDefault()` and also set `returnValue` to a truthy value for legacy cases; `returnValue` is deprecated; returning a truthy value from the handler only works via the `onbeforeunload` property, not `addEventListener`; the dialog requires sticky activation and its text cannot be customised; `window.confirm`/`alert` inside `beforeunload` is not usable for the prompt. Support: Chrome/Edge 119+, Firefox 6+, Safari 8+; not Safari on iOS.
- PyYAML (`yaml.constructor`) — `SafeConstructor.construct_mapping` = `flatten_mapping(node)` then `BaseConstructor.construct_mapping`; `flatten_mapping` mutates the `MappingNode` in place (moves merge sources to the front, re-tags `tag:yaml.org,2002:value`); `BaseConstructor.construct_mapping` raises `ConstructorError` for unhashable keys; `construct_pairs` exists as the non-hashing alternative.
- CPython `smtplib` — `SMTP(host, port, local_hostname, source_address, timeout)` auto-connects; `timeout=0` raises `ValueError`; `SMTP_SSL` wraps TLS from the start (default 465); `starttls()` raises `SMTPNotSupportedError` when STARTTLS is not advertised and `SMTPResponseException` on 454/501; `send_message` derives addresses from headers, strips `Bcc`/`Resent-Bcc`, and needs the `SMTPUTF8` extension for non-ASCII addresses.
- Supabase Auth (GoTrue) — `GOTRUE_SMTP_HOST/PORT/USER/PASS/ADMIN_EMAIL` (ADMIN_EMAIL required, the `From`), `GOTRUE_SMTP_SENDER_NAME`, `GOTRUE_MAILER_SUBJECTS_CONFIRMATION`, `GOTRUE_SMTP_MAX_FREQUENCY` (default 900 s), and `GOTRUE_MAILER_AUTOCONFIRM`; `GOTRUE_RATE_LIMIT_EMAIL_SENT` (default 30) is a **global** process-level limiter, not per-IP, applied to `/signup`, `/invite`, `/magiclink`, `/recover`, `/otp`, `/user` when autoconfirm is off.
- systemd timers / cron — a `Type=oneshot` unit cannot run concurrently with itself (systemd skips the overlapping trigger), unlike cron; `flock` with a local (non-NFS) lock file is the guard that survives multiple trigger paths; `Persistent=true` fires one catch-up run, not a replay; `OnCalendar` is evaluated in the timer's timezone and can skip or double-fire around DST; `RandomizedDelaySec=` spreads a herd; the journal captures stdout/stderr and exit codes per run.
- YouTube Data API v3 — `playlistItems.list` = 1 quota unit, `search.list` = 100; Google recommends `channels.list(part=contentDetails, forUsername|id)` → `contentDetails.relatedPlaylists.uploads` → `playlistItems.list` (~6 units) instead of `search.list`; results page via `maxResults`/`pageToken`/`nextPageToken`; `channels.list(mine=true)` requires OAuth rather than an API key.

---
*Pitfalls research for: Digest CDS v1.3 — live mail, scheduled ingestion, and backlog debt*
*Researched: 2026-10-14*
