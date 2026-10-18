# Project Research Summary

**Project:** Digest CDS
**Domain:** Brownfield editorial knowledge service (Russian-language, corporate internal-audit department) — v1.3 "Live mail, scheduled ingestion & backlog debt"
**Researched:** 2026-10-14
**Confidence:** HIGH (stack, architecture, features), MEDIUM (external third-party particulars), MEDIUM (pitfalls — locally reproduced behaviour is HIGH, external docs are MEDIUM)

## Executive Summary

Digest CDS is a **shipped** four-module product (FastAPI `backend/`, React/Vite `web/`, self-hosted Supabase + `supabase-integration/`, `data-collection/` + `ingestion-service/` CLI) that is now adding three *classes* of capability rather than new product surface: paying down three recorded backlog items (999.1 draft reader-route honesty, 999.6 unsaved-changes guard, 999.7 YAML merge keys), making the weekly digest actually go out over SMTP instead of a log line (MAIL-01), resolving the never-delivered signup confirmation mail (MAIL-02), and driving the existing `ingest` CLI from a schedule so collection happens without a human. The architecture is Hexagonal/Ports-and-Adapters with a strict inward-dependency rule and mandatory TDD Red–Green–Refactor; every one of these items lands *next to a currently-green contract*, so the dominant risk is not "does it work" but "did the fix silently change a shipped contract."

All four researchers converge on the same headline: **v1.3 needs zero new runtime Python packages.** Digest mail is stdlib `smtplib` + `email.message.EmailMessage` behind the existing synchronous `Mailer` port; signup mail is GoTrue container configuration, not app code; the schedule is a systemd `Type=oneshot` service + timer; and 999.6/999.7 are a React Router data-router migration and a six-line fix to `_StrictSafeLoader.construct_mapping` (PyYAML 6.0.3 already implements merges). The recommended build order is **debt → mail-honesty → mail-delivery → scheduler**, which matches the user's stated product order for the backlog and the PROJECT.md ordering for mail.

The two decisions that must be made *before* certain phases can pass are (1) **the corporate SMTP relay choice** (one relay serves both GoTrue's signup mail and MAIL-01's digest lane — ADR-0002 contour isolation applies) and (2) **the YouTube listing source**, where the researchers disagree in a way that materially changes risk: STACK.md argues the public **Atom/RSS feed** (`videos.xml`) lists a channel/playlist with **no API key, no OAuth, no quota** and therefore fits ADR-0002 better, while FEATURES/ARCHITECTURE/PITFALLS all assume **YouTube Data API v3 + an API key** (with a channels.list→uploads→playlistItems.list quota strategy). Resolving that disagreement can remove the ADR/spike gate for the scheduler phase entirely. The single highest-severity technical risk the research surfaces is that the *correct* 999.7 merge fix silently makes a measured **merge-expansion DoS newly reachable** (~610-char document → >10 s of CPU), so the merge fix and its bound must ship together.

## Key Findings

### Recommended Stack

Summary of [STACK.md](STACK.md). The v1/v1.1/v1.2 stack is validated and was **not** re-researched; this is NEW v1.3 capability only. Every mechanism is stdlib, already-installed, or OS/container config — the only *optional* new dependency is `defusedxml` (if the YouTube feed is parsed in Python, promoted from an existing transitive dep).

**Core technologies:**
- **stdlib `smtplib` + `email.message.EmailMessage`** — MAIL-01 digest transport. The `Mailer` port and the `send_digest` use case are synchronous, so stdlib is the only zero-dependency fit; `set_content()` + `add_alternative(html, subtype="html")` produces the exact `multipart/alternative` the digest renderer already needs. No `aiosmtplib`/`emails`/`yagmail`.
- **Supabase Auth (GoTrue) SMTP env** — MAIL-02. The signup confirmation mail is sent by the **Auth container**, never by app code; the fix is `GOTRUE_SMTP_*` + `GOTRUE_MAILER_AUTOCONFIRM=false` on the Supabase VM, not a Python change.
- **YouTube public Atom/RSS feed** (`youtube.com/feeds/videos.xml?channel_id=|playlist_id=`) — channel/playlist enumeration with **no API key, no OAuth, no quota**; 15 most-recent entries, which is ample for a weekly idempotent scan. *(See reconciliation in "Gaps" — the other three researchers assumed Data API v3.)*
- **systemd `Type=oneshot` service + timer** — the schedule. Structural overlap guard, `Persistent=true` catch-up, journald logging, `OnFailure=`, `EnvironmentFile=`; strictly more moving parts to hand-roll under cron.
- **PyYAML 6.0.3 (already pinned)** — merge keys already work via `SafeConstructor.flatten_mapping`; the bug is in the repo's override, not the library. **No version change.**
- **React Router 7.18.3 (already installed)** — `useBlocker` for the in-app guard, **but only under a data router** (`createBrowserRouter` + `RouterProvider`); the app is currently on declarative `<BrowserRouter>`.

**Explicitly rejected:** async mailer port, Celery/APScheduler/Airflow/Redis, in-process schedulers, `google-api-python-client`/`google-auth`, `search.list`, `yt-dlp`/`youtube-dl` in the unattended path, `feedparser`, `ruamel.yaml`/loader swaps/`unsafe_load`, a second SMTP abstraction, scheduler-only dedupe stores, auto-publish/auto-send. Integration map, env-var tables (`SMTP_*`), the `smtplib` exception→domain-error mapping table, and the systemd unit skeletons are all in [STACK.md](STACK.md).

### Expected Features

Summary of [FEATURES.md](FEATURES.md). Six items, all in-scope for v1.3; the ordering axis is **dependency and risk**, not value. Two cross-cutting realities shape everything: the backend is a *reader* of Supabase while the CLI owns ingestion writes (so MAIL-01 goes through the backend `Mailer` port, but MAIL-02 is **GoTrue-owned** — conflating them is the single most likely v1.3 design mistake), and **honesty is a first-class product rule** (D-87/D-88, PIPE-02, ADMIN-03), so every feature must fail closed and never claim more than it did.

**Must have (table stakes):**
- **999.1** — an admin can open any draft from the shortlist/preview and read it in the normal reader rendering; ordinary readers still get an opaque 404 (missing ≡ draft, never 403); authorization is server-side (`require_admin` from `profiles.role`); draft responses are `no-store` and visually marked as previews.
- **999.6** — a dirty pipeline editor prompts on in-app SPA navigation **and** on reload/close; no prompt when clean; dirty clears after a successful save; Russian confirm copy («Есть несохранённые изменения. Уйти без сохранения?»); Cancel keeps the draft.
- **999.7** — a valid `<<` merge document validates and saves; **duplicate *explicit* keys are still rejected** with the verbatim structured 400 `{errors:[…]}`; merge-override is not reported as a duplicate; the strict 4-key `extra="forbid"` schema still governs the result.
- **MAIL-02** — root cause identified and documented, then either a working confirmation email **or** honestly-autoconfirmed copy; never a silent "registered, no mail."
- **MAIL-01** — the send actually delivers to a server-side `profiles`-derived audience; `recipient_count` reflects the real audience (not hardcoded `0`); partial failure is reported honestly (e.g. «доставлено N из M»); mail stays best-effort **after** publish (CR-02/D-88); SMTP config only from VM env.
- **Scheduled ingestion** — runs unattended without a human; discovers only genuinely new videos; writes **drafts + pending shortlist rows only**; re-running is safe; per-run outcome is visible; a bad video does not abort the batch.

**Should have (differentiators):** preview via the *same* fetch/render path as the reader (parity); `sessionStorage` draft persistence (999.6's own recommended alternative); "Сохранить и выйти"; Russia-language merge-error text with line numbers (999.7); branded Russian confirmation template + resend (MAIL-02); per-recipient personalization + persisted per-recipient delivery summary + bounded retry (MAIL-01); `ingestion_jobs` run history with `--max-new` cap and dry-run mode (scheduler).

**Defer (v2+):** unsubscribe/preference management, multiple ingestion sources / allowlist UI, PIPE-01 full pipeline execution, ingestion HTTP API. Backlog **999.4 and 999.5 stay parked** (product preference, not debt).

### Architecture Approach

Summary of [ARCHITECTURE.md](ARCHITECTURE.md). Every seam was read from the live codebase; the invariants (inward dependencies, `typing.Protocol` ports with no `Any`, wiring only in `composition/`, adapter-boundary error mapping, no `os.environ` in adapters) must not be broken.

**Major components / integration points:**
1. **`backend/infrastructure/smtp_mailer.py`** (NEW, replaces the `NotImplementedError` placeholder) — real `SmtpMailer` behind the unchanged synchronous `Mailer` port; wired only in `composition/live.py`; `SMTP_*` parsed only in `composition/settings.py`. **`Mailer.send_digest` gains a `recipients` parameter** (the port currently carries a count but no addresses).
2. **`Recipient` DTO + `ProfileRepository.list_digest_recipients()`** (NEW) — audience resolution is an **application** concern expressed against a port; recommended shape is to extend `ProfileRepository` (Option A — least surface, `profiles` already wired in both containers) rather than a new `RecipientDirectory` port. The use case computes `recipient_count`; the RPC only **persists** it. The `p_recipient_count` parameter already exists in migrations 005/006, so no migration is needed for the count itself. **Audience predicate belongs in the domain** (`is_digest_recipient(role)`), and `profiles` has no `email_confirmed` column, so confirmation state cannot be filtered without schema work.
3. **`get_material_for_preview` use case + `GET /admin/materials/{slug}`** (NEW) — draft-or-ready for admins; **`get_material_for_reader` and `GET /materials/{slug}` stay ready-only and untouched**. Who may preview = interface layer (`require_admin`); what is visible = application use case.
4. **`data-collection` listing port/DTO/adapter** (NEW) — `VideoLister` (`Protocol`) + `VideoRef`/`VideoListing` DTOs + `ListingError` taxonomy + adapter with an injected client (mirrors `YouTubeOEmbedAdapter`). **`data_collection.__all__` is a deliberately-locked public surface**; adding to it is an explicit, test-visible decision.
5. **`ingestion-service` `run_playlist_ingest` use case + subcommand** (NEW) — lists ids, then loops the existing `run_ingest_pipeline` per id; wired via `build_ingest_deps()`. Keeps `ingest <url>` byte-identical.
6. **Ops** — systemd timer + `EnvironmentFile` (0600) + runbook; the scheduler is **host-level infrastructure, not a module or port**. It must never import `backend` or reach publish/send.

**Data-flow changes:** (a) digest send resolves recipients from `profiles` → planned count into the claim RPC → mailer receives real addresses → delivery status/count reported back; (b) draft preview goes through a new admin-gated path, public reader path untouched; (c) timer → `ingest-playlist` → lister → existing pipeline → `persist_draft_and_enqueue` (`already_saved`) → drafts + shortlist rows, no HTTP API, no auto-ready, no auto-send; (d) signup mail is a GoTrue/SMTP-env data flow with **no** backend data flow.

**Suggested dependency-aware build order (ARCHITECTURE.md Track A/B/C):** Track A debt (999.7 → 999.1 → 999.6) · Track B mail (settle relay → MAIL-02 → MAIL-01a recipients+honest count *with the stub* → MAIL-01b real `SmtpMailer`) · Track C ingestion (listing contract → adapter + ADR gate → orchestration + CLI → ops → UAT). Note the deliberate split: **honesty (recipients/count) lands and is testable before delivery (SMTP)**.

### Critical Pitfalls

Summary of [PITFALLS.md](PITFALLS.md). Framing: every item touches a currently-green contract, and the dominant failure mode is an **over-narrow fix that satisfies the new feature while quietly changing a shipped contract**. 28 pitfalls are catalogued with reproductions; The five most consequential:

1. **Loosening the ready-only reader route to "fix" the draft link** (Pitfall 1–2) — leaks unpublished content to any authenticated reader and breaks "draft and missing are indistinguishable." Keep `get_material_for_reader` ready-only; fix the *link* to an admin-gated surface; keep 404 (never 403); reuse the existing `_related_ready`/`_filter_ready_relations` filters so a preview exposes no `related`/`tags`; serve drafts `private, no-store`.
2. **`window.confirm` inside `beforeunload` — and a passing Playwright test that green-lights it** (Pitfall 3–5) — the shipped test dispatches a synthetic event and asserts a dialog, proving only that the listener runs in the harness. Handler must do exactly `preventDefault()` + truthy `returnValue`, be attached only when dirty, and be removed on save/unmount; the Russian copy moves to the in-app guard. Guard must not fire after a successful save, must stay armed after a server reject, and must not double-prompt.
3. **`useBlocker` requires a data router; the app is on `<BrowserRouter>`** (Pitfall 4) — the obvious implementation throws at render. **Migrate `App.jsx` to `createBrowserRouter`+`RouterProvider` as its own behaviour-preserving plan** with the full Playwright suite green *before* wiring the guard; never combine migration + guard in one plan.
4. **999.7's correct fix silently opens a merge-expansion DoS** (Pitfall 6–9, 8 is the severe one) — today the merge path is unreachable (the merge tag raises first). Measured on this checkout with the fix in place: fan-out 3, **610 chars, 15 levels → >10 s**; cost ~triples per level, while the source cap is 20,000 chars. A **bound (merge-depth / flattened-entry / node budget) must ship with the fix**, as a structured 400, with a fast regression test. Do not confuse this with billion-laughs (aliases are shared refs, ~15 ms at 200 levels) and never swap in `safe_load`/`FullLoader` — that silently deletes duplicate-key rejection (PIPE-02).
5. **A real SMTP exception escaping `send_digest`, and delivery columns stamped before mail** (Pitfall 10–13) — the mail call is guarded only by `except PersistenceError`, but a live adapter raises `SMTPException`/`OSError`/`timeout`; those would 500 a digest that **is already published** (D-88 violation) and the retry gets a 409. Symmetrically, `delivery_status`/`recipient_count` are stamped *before* mail and the use case **discards the mailer's return value**, so live mail would still report `stubbed`/`0`. Define a mailer error type caught alongside `PersistenceError`; write the mailer's real status/count post-send (idempotently) and make the response/ping/batch row carry it.

Also high-severity: **MAIL-02 is a deliberate config state, not a bug** (Pitfall 14) and flipping autoconfirm off re-introduces the v1 signup 500 **and breaks a shipped `tests/auth.spec.js` assertion** (Pitfall 15); a working relay turns `/auth/v1/signup` into an **open email sender** because the two-domain gate is client-side + post-auth only (Pitfall 16); **overlapping scheduled runs** are not prevented by per-video idempotency (Pitfall 18); **cron's empty env + unread mail = silent scheduler death** (Pitfall 19); **re-listing the whole channel re-pays captions + LLM** because dedupe happens after the expensive work (Pitfall 21); and **`VITE_USE_MOCKS=true` makes 999.1's draft-404 structurally unreproducible in the browser suite** (mock materials have no `status` field) — the RED tests for 999.1/999.7 must be **pytest HTTP/validator tests**, Playwright is only the integration proof (Pitfall 24).

[PITFALLS.md](PITFALLS.md) also provides the **v1.3 tripwire table** (Pitfall 28): ten existing tests that encode the old contract (`test_materials_draft_slug_returns_404_not_403`, `tests/admin.spec.js` dirty-gating, `test_put_invalid_error_rows_are_verbatim_and_top_level`, `test_send_digest.py` `"stubbed"` asserts, `test_send_audit_failure_after_publish_still_returns_success`, `tests/auth.spec.js` post-register, `test_auth_email_domain.py`, `test_cli_ingest_contract.py` `EXPECTED_SUCCESS_LINES`, `test_stub_mailer.py`/`test_composition_container.py`/`test_live_container_wiring.py`). Each phase plan must state **amend or preserve**, with a reason; "deleted because it was failing" is not a valid disposition.

## Implications for Roadmap

Recommended phase structure for v1.3 (phases continue from 17; **the roadmap owns the final numbering** — see the reconciliation note below). Six phases, three tracks, debt first per PROJECT.md.

### Phase 17: Backlog 999.1 — reader-route honesty for draft materials
**Rationale:** Explicitly first in the user's chosen order and PROJECT.md; the v1.2 milestone audit carries it as W-1. Independent of every other phase.
**Delivers:** an admin-gated draft preview (new `GET /admin/materials/{slug}` + `get_material_for_preview`, or reuse of the already-loaded shortlist DTO) returning the reader DTO; the admin «Открыть материал →» link retargeted; a visible draft banner; `no-store`; the reader route and `get_material_for_reader` provably unchanged.
**Addresses:** 999.1.
**Avoids:** Pitfalls 1, 2, 24. **Phase decision required:** new endpoint vs reuse the Phase-13 shortlist DTO (which already carries `body_markdown`) — PITFALLS prefers the latter (no fetch-on-open), ARCHITECTURE proposes the former for deep-link support. Also rule out the **second cause**: the email-preview CTA inside the `sandbox=""` iframe cannot navigate the top-level app.

### Phase 18: Backlog 999.6 — unsaved-changes guard
**Rationale:** Independent FE-only work (can run parallel with 17/19); the actual defect is in-app SPA navigation, not `beforeunload`.
**Delivers:** a correct dirty-scoped `beforeunload` handler; an in-app navigation guard with the existing Russian copy; **possibly** an `App.jsx` migration to a data router.
**Addresses:** 999.6.
**Avoids:** Pitfalls 3, 4, 5. **Phase decision required:** router migration as its **own behaviour-preserving plan** gated by the full Playwright suite (STACK's recommendation), or avoid `useBlocker` and gate the pipeline page without migrating. Never combine the migration and the guard in one plan.

### Phase 19: Backlog 999.7 — YAML merge-key acceptance in the strict validator
**Rationale:** Lowest blast radius, no cross-module deps, test-locked — hence STACK/ARCHITECTURE/FEATURES all want it **first** in the debt track (see reconciliation).
**Delivers:** `_StrictSafeLoader.construct_mapping` skips the `tag:yaml.org,2002:merge` key node and duplicate-checks **explicit keys only, before** `flatten_mapping`; `SafeLoader` used as the test oracle; **and a merge-expansion bound** so the newly-reachable path stays bounded.
**Addresses:** 999.7.
**Avoids:** Pitfalls 6, 7, 8, 9, 24. The fix and the DoS bound ship in the same phase — not as a follow-up.

### Phase 20: MAIL-02 — signup confirmation mail
**Rationale:** Opens with **investigation** (PROJECT.md), and must settle the shared relay decision before MAIL-01.
**Delivers:** recorded current state (`GET /auth/v1/settings` → `mailer_autoconfirm`, GoTrue `GOTRUE_SMTP_*` presence, relay reachability) and an explicit product contract; whichever of the two honest end states is chosen (**A** mail works, or **B** autoconfirm intended with copy that does not claim mail was sent); a signup-edge domain gate; honest Russian error copy; the debug session closed with the fix.
**Addresses:** MAIL-02.
**Avoids:** Pitfalls 14, 15, 16, 17, 26. **Decision required before this phase can pass:** the corporate SMTP relay (one relay serves GoTrue *and* MAIL-01). **If autoconfirm is flipped off, `tests/auth.spec.js` must be deliberately amended** and a relay smoke + one-command rollback must exist.

### Phase 21: MAIL-01 — live SMTP digest delivery to `profiles`
**Rationale:** Depends on Phase 20's relay decision; ARCHITECTURE deliberately splits it so **honesty lands before delivery**.
**Delivers:** `Recipient` DTO + `ProfileRepository.list_digest_recipients()` + adapter + fakes; the use case computes and passes `recipient_count` through the claim RPC (no migration needed for the param); a mailer error type caught alongside `PersistenceError`; the **real** `SmtpMailer` (stdlib) behind the extended `Mailer` port; `Settings`/`resolve_mailer`/composition wiring; the mailer's real status/count written post-send (idempotently) and surfaced in the response, ping, and batch row; TLS mode + port pairing + bounded timeouts.
**Addresses:** MAIL-01.
**Uses:** stdlib `smtplib`/`email`, Supabase service-role client.
**Avoids:** Pitfalls 10, 11, 12, 13, 26, 27. **Phases 21a (recipients/honest count, testable with the stub) and 21b (real SMTP adapter) may warrant separate plans.** Subject to the milestone constraint: **no auto-send**.

### Phase 22: Scheduled ingestion (systemd over the `ingest` CLI)
**Rationale:** Last — it carries the only new external dependency (YouTube listing) and the only new ops surface (systemd).
**Delivers:** `data-collection` listing port/DTO/error taxonomy + adapter (injected client); `run_playlist_ingest` + an `ingest-playlist` subcommand; a per-source durable high-water mark at the listing step; a systemd `Type=oneshot` service + timer (`EnvironmentFile=` 0600, `OnFailure=`, `RuntimeMaxSec=`, pinned timezone, justified `Persistent=`, `flock` if a second trigger path exists); run-history visibility; an import/reference guard test proving the job cannot reach publish/send.
**Addresses:** Scheduled ingestion.
**Avoids:** Pitfalls 18, 19, 20, 21, 22, 23, 25. **Decision required before this phase can pass:** the YouTube source/key decision vs ADR-0002 (see reconciliation — the Atom feed may remove the gate entirely). `test_cli_ingest_contract.py`'s byte-identical stdout must not be touched.

### Phase Ordering Rationale

- **Debt first** is explicit in the user's order, PROJECT.md, and FEATURES.md; the three items are mutually independent, cheap, and reduce risk before new-feature work. Pitfalls research frames the risk as "don't quietly break a green contract," which is best absorbed while the diff is small.
- **One relay decision, two mail lanes:** sequencing MAIL-02 before MAIL-01 lets the shared relay be proven on the simpler GoTrue path first, and lets MAIL-01's *honesty* half (recipients/count) ship and be tested **with the stub** before real SMTP lands (ARCHITECTURE's explicit split).
- **Scheduler last** because it is gated on the YouTube decision and adds VM ops on top of an already-shipped pipeline; its efficiency property (high-water mark) and its scope property (never reach publish/send) are independent of the mail track.
- **How this avoids pitfalls:** the order keeps each phase's tripwire test adjacent to its own diff; it separates the router migration from the guard (Pitfall 4); it forces the merge bound to ship with the merge fix (Pitfall 8); and it makes mail honesty a precondition for mail delivery (Pitfall 11).

### Research Flags

**Phases likely needing deeper research / an ADR-spike during planning:**
- **Phase 21 (MAIL-01):** the relay's TLS mode/port pairing, batch-vs-per-recipient semantics, timeouts, and partial-failure semantics must be settled in a spike/ADR before the adapter is written (STACK's "Open Questions" #1/#2; PITFALLS Pitfall 12). Also decide `recipient_count` = planned audience vs delivered count, and whether a `DigestPublisher.update_delivery` port method is warranted.
- **Phase 22 (scheduler):** the **listing source decision** (Atom feed vs Data API v3 + key), channel-vs-playlist source parsing, pagination/quota behaviour, run-away listing guards, and the ADR-0002 contour question (STACK "Open Questions" #1; PITFALLS Pitfall 22). **If the Atom feed is chosen, the heavy part of this gate largely dissolves.**
- **Phase 20 (MAIL-02):** the root cause is *unknown* per PROJECT.md — the phase must open with diagnosis (PITFALLS Pitfall 14). GoTrue signup-edge domain gating has no built-in support and needs an approach (Pitfall 16).

**Phases with standard patterns (skip research-phase):**
- **Phase 19 (999.7):** the fix is documented against primary PyYAML sources and **reproduced locally**; only the new bound needs care.
- **Phase 18 (999.6):** `useBlocker`/`beforeunload` behaviour is well-documented (React Router + MDN); the work is engineering discipline, not research.
- **Phase 17 (999.1):** the codebase already contains the needed seams (`require_admin`, the shortlist DTO, `MaterialPage`).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Stdlib SMTP/`email`/`ssl`, systemd, and the existing PyYAML/React Router facts are verified against stdlib docs, man pages, Context7, and the live repo. MEDIUM only on YouTube *listing under ADR-0002* — and STACK.md itself downgrades that. |
| Features | **HIGH** (999.1/999.6/999.7/MAIL-02), **HIGH–MEDIUM** (MAIL-01, scheduler) | Grounded in the live codebase plus Context7/primary sources. FEATURES.md notes its research-seam limitation (the `research-plan`/`classify-confidence` runtime was unavailable), so it used direct Context7 + web + codebase grounding. |
| Architecture | **HIGH** for integration points / NEW-vs-MODIFIED / build order; **MEDIUM** for third-party particulars | Every boundary was read from the codebase and the mandatory architecture rules. SMTP-relay and YouTube Data API v3 listing semantics were **not** vendor-doc-verified this session. |
| Pitfalls | **MEDIUM** overall (**HIGH** for locally reproduced behaviour) | The 999.7/PyYAML findings (merge tag, flatten-then-scan false positive, expansion timings, alias timings) were **reproduced on this checkout** (PyYAML 6.0.3 / Python 3.14). External docs (MDN, smtplib, GoTrue, systemd, YouTube quota) are MEDIUM. |

**Overall confidence:** **HIGH** for the debt track and the architectural seams; **MEDIUM** for the two external-dependency decisions (relay, YouTube source), which are explicitly deferred to in-phase spikes/ADRs by PROJECT.md.

### Gaps to Address

**Reconciled disagreements between researchers (the roadmap must pick one):**

1. **Backlog internal ordering — 999.7 first vs 999.1 first.** [STACK.md](STACK.md) and [ARCHITECTURE.md](ARCHITECTURE.md) and [FEATURES.md](FEATURES.md) all sequence **999.7 first** (isolated, test-locked, zero cross-module deps, cheapest to verify); [PITFALLS.md](PITFALLS.md) hardcodes **17 = 999.1, 18 = 999.6, 19 = 999.7**, matching the user's stated order and PROJECT.md's listing. All four agree the three are independent. **Recommendation:** treat the three as one debt track whose internal order is low-risk-first (999.7 → 999.1 → 999.6) *unless* the roadmap deliberately preserves the user's product order; either way, do not let the numbering imply a dependency that does not exist. The roadmap owns the final phase numbers.
2. **YouTube listing source — Atom feed vs Data API v3.** STACK.md recommends the **public Atom/RSS feed** (no key, no OAuth, no quota, 15 recent entries, fits ADR-0002 better and may **remove the ADR/spike gate**). FEATURES.md, ARCHITECTURE.md, and PITFALLS.md all assume **Data API v3 + an API key**, with the quota strategy `channels.list(part=contentDetails)` → uploads playlist → `playlistItems.list` (1 unit/page) and an explicit "never `search.list`" rule. **This is the most consequential disagreement in the set.** Resolve it in the Phase 22 spike; if the feed is acceptable, the scheduler's ADR-0002 exception and the quota/API-key risk largely disappear (the feed's 15-entry window is a *recent-window* source, so a high-water mark is still needed to avoid re-paying LLM cost — Pitfalls 21).
3. **MAIL-02 sender — GoTrue vs the app's `Mailer`.** STACK.md, FEATURES.md, and ARCHITECTURE.md are emphatic that signup confirmation is **GoTrue-owned** and that routing it through the `Mailer` port is an anti-feature. PITFALLS.md Pitfall 14 raises a *third* option — keep autoconfirm ON and send the confirmation through the **app's own `Mailer` port** (reuses MAIL-01's adapter, leaves `/register` unchanged). **Reconciliation:** the GoTrue path (A/B) is the default recommendation and the only one with primary-source backing; the app-`Mailer` variant is a legitimate fallback that must be an *explicit* decision, not a silent conflation of the two mailers. Record whichever is chosen with its consequences (Pitfall 15's test amendment if autoconfirm is flipped).
4. **Digest addressing — per-recipient sends vs `Bcc`.** STACK.md prefers one connection, N messages with an explicit envelope (feeds an honest per-recipient count, leaks nothing); PITFALLS Pitfall 13 prefers a single stable `To` + audience in `Bcc` (and warns that `To` exposes the internal distribution list). **Both satisfy the PII requirement** — the roadmap should pick per-recipient `send_message(msg, to_addrs=[addr])` as the default (it also gives the honest count) and treat `Bcc` as the fallback when the relay rate-limits.

**Open decisions that must be settled before phases can pass:**
- **SMTP relay choice** (before Phase 20/21) — one relay for GoTrue and MAIL-01; TLS mode/port pairing; CA bundle for an internal CA; ADR-0002 contour isolation.
- **YouTube source/key** (before Phase 22) — Atom feed vs Data API v3; if the API, an ADR-0002 exception and `channels.list`→uploads→`playlistItems.list`.
- **`recipient_count` semantics** (Phase 21) — planned audience size vs delivered count; whether to add `DigestPublisher.update_delivery` (ARCHITECTURE option i vs ii) or carry the mailer's values in the response/ping only.
- **`profiles` ≠ all authorized users** (Phase 21) — `profiles` rows are created lazily by `get_or_upsert`, so `recipient_count` from `profiles` is an **under-count** and its copy must not claim "all employees" (Pitfall 13). There is no `email_confirmed` column, so confirmation state cannot be filtered without schema work.
- **999.1 shape** (Phase 17) — new admin endpoint vs reuse of the loaded shortlist DTO; and whether any admin surface beyond the shortlist row links to drafts.
- **999.6 router strategy** (Phase 18) — migrate to a data router (separate plan) vs avoid `useBlocker`.

**Process gaps:** migrations must be idempotent with a documented apply-before-deploy order (Pitfall 27); review must run before verify with covered digests re-stamped after any post-verify fix; debug sessions must be closed in the same change that ships their fix.

## Sources

### Primary (HIGH confidence)
- **Live codebase (read by all four researchers)** — `backend/src/backend/{application/ports,application/use_cases,infrastructure,composition,interface/http,domain,tests_support}/*`; `supabase-integration/src/supabase_integration/*` + `migrations/001,005,006,007,008,009,011`; `data-collection/src/data_collection/*`; `ingestion-service/src/ingestion_service/*`; `web/src/{pages,services,components,App.jsx,data/mock.js}`; `playwright.config.js`; `tests/{unit,admin.spec.js,auth.spec.js}`.
- **Mandatory project rules** — `.cursor/rules/architecture.mdc`, `.cursor/rules/tdd.mdc`, `AGENTS.md`, `CONTEXT.md`.
- **Planning artifacts** — `.planning/PROJECT.md`, `.planning/ROADMAP.md` (backlog 999.1/999.6/999.7), `.planning/STATE.md`, `.planning/RETROSPECTIVE.md`, `.planning/milestones/v1.2-MILESTONE-AUDIT.md` (W-1 draft reader link), `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-REVIEW.md` (WR-01), `.planning/debug/g-01-3b-signup-mailer.md`.
- **ADRs** — `docs/adr/0001-public-leaderboard-gamification.md`, `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` (contour isolation), `docs/adr/0003-email-domain-restriction.md`, `docs/adr/0004-self-hosted-supabase-on-vm.md`.
- **Runbook** — `docs/agents/local-platform-runbook.md` §4.1 (autoconfirm on/off, `MAILER=smtp` fail-fast).
- **Locally reproduced measurements (PITFALLS.md, PyYAML 6.0.3 / Python 3.14.0, 2026-10-14)** — merge-tag `ConstructorError`; flatten-then-scan false duplicate; merge-expansion timings (610 chars / fan-out 3 / 15 levels → >10 s); alias-chain timings (200 levels → 15 ms); confirmed-safe merge/override/duplicate behaviour under the proposed fix.
- **Context7** — `/yaml/pyyaml` (`flatten_mapping`, `construct_mapping` ordering, merge-tag errors); `/remix-run/react-router` (`useBlocker` data-router requirement, `createBrowserRouter`).
- **Official docs** — [systemd.timer(5)](https://freedesktop.org/software/systemd/man/latest/systemd.timer.html); [YouTube quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost) + [`playlistItems.list`](https://developers.google.com/youtube/v3/docs/playlistItems/list); [Supabase self-hosting](https://supabase.com/docs/guides/self-hosting/docker) + [Auth config](https://supabase.com/docs/guides/self-hosting/auth/config) + `supabase/auth` `example.env`; CPython `smtplib` and `email.message` docs; MDN `beforeunload`; PyPI JSON 2026-10-14 (`pyyaml==6.0.3`, `defusedxml==0.7.1`, `feedparser==6.0.14`, `aiosmtplib==5.1.3`).

### Secondary (MEDIUM confidence)
- CMS preview/draft workflow pattern guides (Vercel Draft Mode, headless-CMS guides) — server-side state signal, never shared-cache, never index.
- Email sending-limit / queue-architecture / transactional rate-limiting guides — transactional-vs-bulk lane separation, batching, backoff+jitter, DLQ, monitoring 429/bounce/queue-age.
- Scheduled-job observability / systemd-timer / feed-ingest idempotency guides — `Persistent=true`, single-flight, durable watermark, run records, check-ins.
- YouTube Atom feed behaviour (cors.dev, Feeder KB, Stack Overflow 29752447) — no API key, 15 most-recent entries, `UULF`/`UU` playlist variants; **not vendor-doc-verified**.
- yt-dlp README + community guidance — `--flat-playlist`/`-J`, monthly extractor cadence, datacenter-IP bot checks; used to reject `yt-dlp` in the unattended path.
- cron-vs-systemd operational write-ups — overlap/logging/env/failure-hook comparison.

### Tertiary (LOW confidence)
- One AI-authored blog (aident.ai) on PyYAML duplicate-vs-merge policy — used only as corroboration; the same claim is independently supported by pyyaml issue #165 / PR #954.
- SMTP-relay and YouTube Data API v3 third-party particulars — flagged by ARCHITECTURE.md as **not verified against vendor docs this session**; settle in the phase spike/ADR.

---
*Research completed: 2026-10-14*
*Ready for roadmap: yes*
