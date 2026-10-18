---
phase: 21-mail-01-live-smtp-digest-delivery
plan: 02
subsystem: api
tags: [smtp, mailer, digest, ports-and-adapters, mail-honesty, configuration]

requires:
  - phase: 21-mail-01-live-smtp-digest-delivery
    provides: "Mailer port recipients/delivered_count contract, MailDeliveryError, StubMailer double (Plan 01)"
  - phase: 05-admin-digest-publish
    provides: "claim_and_publish publish-on-send path + send_digest post-publish containment"

provides:
  - "Real SmtpMailer behind the Mailer port: per-recipient send, TLS modes, consecutive-stop, MailDeliveryError map (D-05/D-07/D-08/D-13/D-14/MAIL-04)"
  - "ConfigurationError fail-fast for MAILER=smtp with incomplete SMTP_* (D-16, no silent stub fallback)"
  - "Settings SMTP_* fields with starttls default and fixed 10s/30s timeouts (D-13/D-14)"
  - "resolve_mailer(settings) composition-owned adapter selection (D-15)"

affects: [21-03]

actuals:
  tokens: 12158
  tasks: 2
  commits: 4
  plan_head_before: 421999f9c5e17f88974ba81a82aee1ad8feee41f
  plan_head_after: 3d7e77112cd765b46037cbae3239f2748c4038dd

tech-stack:
  added: []
  patterns:
    - "Injected SMTP factory: SmtpMailer takes ready primitives and a factory callable, so unit tests never open a socket"
    - "Adapter-boundary domain error: SMTPException|OSError|TimeoutError -> MailDeliveryError; no transport type escapes"
    - "Composition-owned adapter selection: resolve_mailer lives in composition so infrastructure never imports composition"
    - "Env-agnostic adapters: only Settings.from_env reads SMTP_*; SmtpMailer reads none (MAIL-05)"

key-files:
  created:
    - backend/src/backend/infrastructure/smtp_mailer.py
    - backend/src/backend/composition/config_error.py
    - backend/src/backend/composition/mailer_factory.py
    - tests/unit/test_smtp_mailer.py
  modified:
    - backend/src/backend/composition/settings.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/infrastructure/stub_mailer.py
    - tests/unit/test_stub_mailer.py
    - tests/unit/test_live_container_wiring.py
    - tests/unit/test_composition_container.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "resolve_mailer moved to backend.composition.mailer_factory: adapter selection is wiring, and infrastructure must not depend on composition (architecture.mdc)"
  - "SMTP_PORT is int|None (None = unset) so D-16 can require it explicitly, instead of silently defaulting to 587"
  - "D-08 consecutive-stop lives in the adapter (RESEARCH A2): the loop breaks at 3 consecutive failures and returns stop_reason; the use case only records it"
  - "Connection-level setup failures (connect/STARTTLS/login) raise MailDeliveryError; per-recipient send failures are counted, never raised"
  - "Settings.smtp_pass uses field(repr=False) so a logged Settings cannot disclose the relay credential (T-21-04)"
  - "Non-numeric SMTP_PORT raises ConfigurationError in from_env — fail-fast rather than silently unset"

patterns-established:
  - "One message per recipient with a scripted SMTP double: proves N-of-M honesty and single-To privacy without network"
  - "Fail-fast config: MAILER=smtp + incomplete SMTP_* raises ConfigurationError at resolve/build; a test asserts StubMailer is never returned"

requirements-completed: [MAIL-01, MAIL-04, MAIL-05]

coverage:
  - id: D1
    description: "SmtpMailer delivers exactly one SMTP message per recipient with a single To address (D-05) and reports sent/partial/failed from N of M (D-07)"
    requirement: MAIL-01
    verification:
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_sends_one_message_per_recipient"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_partial_when_some_recipients_fail"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_failed_when_all_recipients_fail"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-08 policy: continue past a failure, stop after three consecutive failures, reset the streak on success, report stop_reason"
    requirement: MAIL-04
    verification:
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_stops_after_three_consecutive_failures"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_streak_reset_on_success_continues_sending"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_streak_reset_then_stop_leaves_remaining_recipients_untouched"
        status: pass
    human_judgment: false
  - id: D3
    description: "MAIL-04: SMTPException / OSError / TimeoutError map to MailDeliveryError at the adapter boundary; smtplib never reaches domain or application"
    requirement: MAIL-04
    verification:
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_connect_failure_maps_to_mail_delivery_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_authentication_failure_maps_to_mail_delivery_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_starttls_failure_maps_to_mail_delivery_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_connect_timeout_maps_to_mail_delivery_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtplib_import_stays_out_of_domain_and_application"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-13/D-14: starttls default via ssl.create_default_context, ssl/none overrides, fixed 10s connect + 30s per-send timeouts as injected primitives (not env)"
    requirement: MAIL-05
    verification:
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_starttls_default_uses_default_context_and_connect_timeout"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_ssl_mode_uses_implicit_tls_transport"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_none_mode_skips_tls"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_settings_timeouts_are_not_env_driven"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-16: MAILER=smtp with incomplete SMTP_HOST/PORT/USER/PASS/FROM (or a bad SMTP_TLS_MODE) raises ConfigurationError at resolve and at live build — never a silent StubMailer"
    requirement: MAIL-05
    verification:
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_resolve_mailer_smtp_requires_each_field"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_resolve_mailer_smtp_never_silently_returns_stub"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_resolve_mailer_rejects_unknown_mode"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_resolve_mailer_smtp_rejects_invalid_tls_mode"
        status: pass
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py#test_build_live_container_rejects_incomplete_smtp_mailer"
        status: pass
    human_judgment: false
  - id: D6
    description: "D-15: MAILER defaults to stub; StubMailer remains the in-memory/live default and the port's test double; SmtpMailer is selected only with complete SMTP_*"
    requirement: MAIL-01
    verification:
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_settings_mailer_defaults_to_stub"
        status: pass
      - kind: unit
        ref: "tests/unit/test_composition_container.py#test_in_memory_container_keeps_stub_mailer_as_default"
        status: pass
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py#test_build_live_container_wires_smtp_mailer_when_settings_complete"
        status: pass
    human_judgment: false
  - id: D7
    description: "MAIL-05: SmtpMailer never reads the process environment; only constructor primitives from Settings via resolve_mailer; relay password never logged (T-21-04)"
    requirement: MAIL-05
    verification:
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_never_reads_process_environment"
        status: pass
      - kind: unit
        ref: "tests/unit/test_smtp_mailer.py#test_smtp_mailer_logs_never_contain_the_relay_password"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_settings_repr_never_leaks_the_smtp_password"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-16
status: complete
---

# Phase 21 Plan 02: SmtpMailer + fail-fast SMTP resolve Summary

**Real stdlib `smtplib` digest adapter behind the `Mailer` port (one message per recipient, three-consecutive-failure stop, `MailDeliveryError` mapping) plus `Settings`-injected `SMTP_*` wiring that fails fast with `ConfigurationError` instead of silently falling back to the stub**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-16T14:39:30Z
- **Completed:** 2026-10-16T14:51:30Z
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files modified:** 11 (4 created, 7 modified)

## Accomplishments

- `SmtpMailer` (`backend/infrastructure/smtp_mailer.py`) sends **one message per recipient** with a single `To` and no `Bcc` (D-05), selects `starttls` (default, `ssl.create_default_context`), `ssl`, or `none` (D-13), and applies the injected 10s connect / 30s per-send timeouts to the live socket (D-14).
- Delivery honesty is derived inside the adapter: `sent` (N=M), `partial` (0<N<M), `failed` (N=0), with `recipient_count` echoing planned M and `delivered_count` = N; an empty audience is honestly `sent` with N=0 (D-04/D-07, RESEARCH Q3).
- **D-08 policy owned by the adapter** (RESEARCH A2): the per-recipient loop continues past a failure, stops after **three consecutive** failures, resets the streak on any success, and returns `stop_reason="consecutive_failures"`. The use case already records `stop_reason` in the `digest_send` ping (Plan 01).
- **MAIL-04 boundary mapping:** connection/STARTTLS/login failures and per-recipient transport failures (`smtplib.SMTPException`, `OSError`, `TimeoutError`) never escape — setup failures raise `MailDeliveryError`; per-recipient failures are counted. A tripwire test asserts `smtplib` is imported nowhere under `domain/` or `application/`.
- **D-16 fail-fast:** `MAILER=smtp` with any of `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` missing (or an invalid `SMTP_TLS_MODE`) raises `ConfigurationError` at `resolve_mailer` and therefore at `build_live_container`. A dedicated test proves a misconfigured `smtp` mode **never** returns a `StubMailer`.
- **D-15 preserved:** `MAILER` still defaults to `stub`; `StubMailer` remains the in-memory/live default and the port's test double (assumption-delta: live SMTP added *alongside*).
- **T-21-04:** `Settings.smtp_pass` is `field(repr=False)`, so logging a `Settings` instance cannot disclose the relay credential; the adapter logs recipient counts and batch ids only.
- Unit tests use an injected SMTP factory double — **zero real network** — and the plan's verification set plus the whole unit suite are green.

## Task Commits

Each task was committed atomically, RED before GREEN:

1. **Task 1 RED: failing SmtpMailer tests** — `bee7289` (test)
2. **Task 1 GREEN: real SmtpMailer adapter** — `4f2677d` (feat)
3. **Task 2 RED: SMTP settings / ConfigurationError / wiring tests** — `f14df1c` (test)
4. **Task 2 GREEN: Settings + resolve_mailer + live wiring** — `3d7e771` (feat)

**Plan metadata:** `_pending_` (docs: complete plan)

_TDD RED was observed for real both times: Task 1 as `ModuleNotFoundError: No module named 'backend.infrastructure.smtp_mailer'` (collection error on the new target module), Task 2 as `ModuleNotFoundError: No module named 'backend.composition.config_error'`._

## Files Created/Modified

- `backend/src/backend/infrastructure/smtp_mailer.py` — **NEW**: `SmtpMailer`, `SmtpConnection`/`SmtpFactory` protocols, `CONSECUTIVE_FAILURE_LIMIT = 3`, `_delivery_status`, `MailDeliveryError` mapping, D-05/D-08/D-13/D-14 logic.
- `backend/src/backend/composition/config_error.py` — **NEW**: `ConfigurationError` (plain `Exception`, mirrors the ingestion analog).
- `backend/src/backend/composition/mailer_factory.py` — **NEW**: `resolve_mailer(settings)` + `_build_smtp_mailer` (D-15 selection, D-16 completeness + TLS-mode validation).
- `tests/unit/test_smtp_mailer.py` — **NEW**: 20 tests (D-05/D-07/D-08/D-13/D-14/MAIL-04/MAIL-05 + two architecture tripwires), no network.
- `backend/src/backend/composition/settings.py` — `smtp_host/port/user/pass/from/from_name/tls_mode` + fixed `smtp_connect_timeout=10.0` / `smtp_send_timeout=30.0`; `_read_smtp_port`; `smtp_pass` excluded from `repr`.
- `backend/src/backend/composition/live.py` — imports `resolve_mailer` from `composition.mailer_factory` and passes the full `Settings`.
- `backend/src/backend/infrastructure/stub_mailer.py` — placeholder `SmtpMailer` replaced by a re-export of the real adapter; `resolve_mailer` removed (moved to composition); `StubMailer` behaviour untouched.
- `tests/unit/test_stub_mailer.py` — resolve-path cases rewritten for `ConfigurationError`, per-field D-16 coverage, SMTP settings/defaults/timeouts, repr redaction; obsolete `NotImplementedError` placeholder test replaced by a stable-import-path test.
- `tests/unit/test_live_container_wiring.py` — `MAILER=smtp` build now expects `ConfigurationError`; added the complete-`SMTP_*` → `SmtpMailer` wiring case.
- `tests/unit/test_composition_container.py` — D-15 tripwire: the in-memory container keeps `StubMailer`.
- `docs/agents/local-platform-runbook.md` — digest lane env block gains `MAILER`/`SMTP_FROM`/`SMTP_FROM_NAME`; documents the starttls+587 default and the fixed (non-env) timeouts; the stale "no live SMTP this phase / success copy is «Отправка записана»" note replaced with the stub-vs-live reality.

## Decisions Made

- **`resolve_mailer` lives in `composition/mailer_factory.py`, not `infrastructure/stub_mailer.py`.** Adapter selection is wiring; keeping it in infrastructure would make infrastructure import composition (`Settings`, `ConfigurationError`) and invert the dependency direction mandated by `architecture.mdc`. `stub_mailer.py` therefore keeps only `StubMailer` + the `SmtpMailer` re-export. See Deviations #1.
- **`Settings.smtp_port` is `int | None` with `None` = unset.** D-16 lists `SMTP_PORT` among the required keys, so a defaulted 587 would make an unset port indistinguishable from a configured one and silently weaken the completeness check.
- **D-08 stop policy owned by the adapter** (RESEARCH A2 disposition): the adapter returns `stop_reason` and counts; the use case already forwards `stop_reason` into the ping payload, so no use-case change was needed.
- **Connection-level vs per-recipient failures are treated differently on purpose:** a failed connect/STARTTLS/login raises `MailDeliveryError` (the run could not start), while individual send failures are counted toward the D-08 streak — that is what makes "N of M" meaningful.
- **A non-numeric `SMTP_PORT` raises `ConfigurationError` in `Settings.from_env`** rather than being silently discarded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `resolve_mailer` relocated to `composition/mailer_factory.py`**
- **Found during:** Task 2 (Settings SMTP_* + resolve wiring)
- **Issue:** The plan keeps `resolve_mailer` in `backend/infrastructure/stub_mailer.py` while changing it to accept `Settings` (a composition type) and to raise `ConfigurationError` (a composition type). That forces `infrastructure → composition` imports, inverting the dependency direction required by `.cursor/rules/architecture.mdc` ("Зависимости направлены внутрь… Никогда наоборот") and by `AGENTS.md`.
- **Fix:** Added `backend/composition/mailer_factory.py` owning `resolve_mailer(settings)` + `_build_smtp_mailer`; removed `resolve_mailer` from `stub_mailer.py`; updated `live.py` and `tests/unit/test_stub_mailer.py` imports. Behaviour is unchanged from the plan's contract (`resolve_mailer(settings) → StubMailer | SmtpMailer`, `ConfigurationError` fail-fast).
- **Files modified:** `backend/.../composition/mailer_factory.py` (new), `backend/.../composition/live.py`, `backend/.../infrastructure/stub_mailer.py`, `tests/unit/test_stub_mailer.py`
- **Verification:** `uv run pytest tests/unit -q` → 882 passed; all `resolve_mailer` call sites re-grepped and updated.
- **Committed in:** `3d7e771`

**2. [Rule 2 - Missing Critical] Runbook documented the pre-Plan-02 (now false) mailer state**
- **Found during:** Task 2, after the resolve behaviour changed
- **Issue:** `docs/agents/local-platform-runbook.md` stated "`MAILER=smtp` **fail-fast** … **no live SMTP this phase**" and "Success copy is «Отправка записана»". Both became factually wrong with this plan's change, and D-13 explicitly requires documenting the relay posture in the runbook.
- **Fix:** Digest lane env block now lists `MAILER`, `SMTP_FROM`, `SMTP_FROM_NAME`; added the starttls+587 default, the fixed (non-env) 10s/30s timeouts, the D-16 required-key list, and an accurate stub-vs-live paragraph. GoTrue `GOTRUE_SMTP_*` lane and the smoke/rollback procedure were left untouched.
- **Files modified:** `docs/agents/local-platform-runbook.md`
- **Verification:** re-read the section against CONTEXT D-13/D-14/D-15/D-16.
- **Committed in:** `3d7e771`

**3. [Rule 1 - Bug] Obsolete `NotImplementedError` placeholder test removed with the placeholder**
- **Found during:** Task 1 (real `SmtpMailer` landing)
- **Issue:** `tests/unit/test_stub_mailer.py::test_smtp_mailer_send_raises_not_implemented` asserted the *placeholder* `SmtpMailer` raises `NotImplementedError`. Once the real adapter replaced it the assertion could not hold, and the plan explicitly called for replacing it.
- **Fix:** Replaced with `test_smtp_mailer_import_path_is_stable_and_real` (asserts the historical `stub_mailer` import path re-exports the real adapter). `StubMailer`'s own honesty tests were preserved unchanged, plus the `delivered_count` assertion was strengthened.
- **Files modified:** `tests/unit/test_stub_mailer.py`
- **Verification:** `uv run pytest tests/unit/test_stub_mailer.py -q` → green
- **Committed in:** `4f2677d`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** No scope creep. Deviation #1 is a layering correction with identical external behaviour; #2 keeps operator documentation honest (D-13); #3 removes a test that could only contradict the plan's own deliverable. Everything else executed as written — `tests/unit/test_send_digest.py` and the D-88 audit-failure tripwire were not touched and stay green.

## Issues Encountered

None.

## TDD Gate Compliance

Both tasks ran RED → GREEN with the RED committed before the GREEN:

| Task | RED | GREEN | REFACTOR | Status |
| ---- | --- | ----- | -------- | ------ |
| 1 — SmtpMailer | `bee7289` (test) | `4f2677d` (feat) | not needed | Pass |
| 2 — Settings + resolve | `f14df1c` (test) | `3d7e771` (feat) | not needed | Pass |

RED evidence in both cases was a genuine missing-module failure on the target under test (`backend.infrastructure.smtp_mailer`, then `backend.composition.config_error`) — not a syntax error, zero-test discovery, or an unrelated assertion.

## Known Stubs

None. `SmtpMailer` is a complete adapter; no placeholder branch, no hardcoded empty values, and no unwired data source were introduced in this plan.

## Deferred / Out of Scope

- `backend/src/backend/interface/http/routes/admin.py:523` and the SPA (`web/src/services/adminApi.js`, `tests/admin.spec.js`) still carry the pre-Plan-01 «Отправка записана» copy. Those are Plan 03 / phase-3 deliverables (HTTP `delivered_count` + SPA contract) and were already stale before this plan — left untouched per the scope boundary.
- Live corporate-relay smoke remains an **ops** step after merge (D-15); no credentials or live network calls were used here.

## User Setup Required

None for code merge — `MAILER=stub` remains the default. Live delivery requires the operator to set `MAILER=smtp` plus `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS`/`SMTP_FROM` on the VM after the relay smoke passes (see the runbook §4.1.1); incomplete values fail fast with `ConfigurationError`.

## Next Phase Readiness

- Ready for **21-03**: `SupabaseProfileRepository.list_digest_recipients` (service_role), `p_recipient_count` forwarding, HTTP `SendDigestResponse.delivered_count`, and the SPA banner/`adminApi` contract — the live adapter, the `MailDeliveryError` boundary, and the fail-fast wiring it depends on are now fixed and covered.
- `Mailer` port signature and the `{delivery_status, recipient_count, delivered_count, issue_url, stop_reason?}` return contract are unchanged, so Plan 03 needs no adapter edits.
- No blockers.

## Self-Check: PASSED

- `backend/src/backend/infrastructure/smtp_mailer.py` exists on disk: FOUND
- `backend/src/backend/composition/config_error.py` exists on disk: FOUND
- `backend/src/backend/composition/mailer_factory.py` exists on disk: FOUND
- `tests/unit/test_smtp_mailer.py` exists on disk: FOUND
- Commits `bee7289`, `4f2677d`, `f14df1c`, `3d7e771` present in `git log`: FOUND
- `uv run pytest tests/unit -q` → 882 passed (baseline before plan: 845)

---
*Phase: 21-mail-01-live-smtp-digest-delivery*
*Completed: 2026-10-16*
