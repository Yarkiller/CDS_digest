---
phase: 20-mail-02-signup-confirmation-mail
plan: 02
subsystem: auth
tags: [gotrue, smtp, runbook, debug-closure, mail-02, autoconfirm]

requires:
  - phase: 20-mail-02-signup-confirmation-mail
    provides: "Plan 20-01 honest (B) CONFIRM_MESSAGE + Playwright coverage to cite in Resolution"
provides:
  - "D-12 closed g-01-3b-signup-mailer.md with path-(B) fix reference (diagnosis retained)"
  - "D-13 runbook §4.1 GOTRUE_SMTP_*/SMTP_* shape, smoke, D-05 rollback, Pitfall-16 blocker"
  - "D-06 criterion-4 relay smoke proof explicitly deferred as Phase 21 precondition"
affects:
  - 21-mail-01-live-smtp-digest

actuals:
  tokens: 2177
  tasks: 2
  commits: 2

plan_head_before: 45f7b1dc06d64109c40b354aea84b43800423793
plan_head_after: 21f688925890d6f29a1f60bf74ccc6a089b3dc47

tech-stack:
  added: []
  patterns:
    - "Close debug sessions in place with status:resolved + Resolution citing shipped files"
    - "Document path-(A) SMTP as placeholders-only ops procedure; never half-enable in git"

key-files:
  created: []
  modified:
    - .planning/debug/g-01-3b-signup-mailer.md
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "D-12: Close g-01-3b in place (not deleted); Resolution cites 20-01 honest copy"
  - "D-03/D-13: Runbook records relay choice + GOTRUE_SMTP_*/SMTP_* shape only; no new ADR (D-04)"
  - "D-05/D-06: Rollback is GOTRUE_MAILER_AUTOCONFIRM=true + reload; criterion-4 proof → Phase 21"

patterns-established:
  - "Debug closure keeps Probe/Root cause; frontmatter status resolved + audit_acknowledged closed"
  - "Path (A) enablement documented under §4.1.x with smoke-before-flip and Pitfall-16 operator blocker"

requirements-completed: [MAIL-02]

coverage:
  - id: D1
    description: "g-01-3b debug session closed with Resolution citing path-(B) CONFIRM_MESSAGE; diagnosis preserved"
    requirement: MAIL-02
    verification:
      - kind: other
        ref: "git ls-files .planning/debug/g-01-3b-signup-mailer.md; rg '## Resolution|mailer_autoconfirm|unexpected_failure|CONFIRM_MESSAGE'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Runbook §4.1 documents GOTRUE_SMTP_*/SMTP_* shape, smoke, rollback, Phase 21 criterion-4 gap"
    requirement: MAIL-02
    verification:
      - kind: other
        ref: "rg GOTRUE_SMTP_|GOTRUE_MAILER_AUTOCONFIRM|SMTP_|Phase 21|/auth/v1/settings docs/agents/local-platform-runbook.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "ADR-0003 domain tripwire unmodified and green"
    requirement: MAIL-02
    verification:
      - kind: unit
        ref: "uv run pytest tests/unit/test_auth_email_domain.py -x"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-16
status: complete
---

# Phase 20 Plan 02: Close diagnosis + relay runbook Summary

**Closed g-01-3b signup-mailer diagnosis with path-(B) fix reference; extended runbook §4.1 with GOTRUE_SMTP_*/SMTP_* shape, smoke-before-flip, one-command rollback, and explicit criterion-4 → Phase 21 gap.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-16T08:43:00Z
- **Completed:** 2026-10-16T08:47:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Closed `.planning/debug/g-01-3b-signup-mailer.md` in place (`status: resolved`, audit closed); preserved Probe/Root cause (500 / unexpected_failure / mailer_autoconfirm); Resolution cites Plan 20-01 CONFIRM_MESSAGE + Playwright and states path (A) remains the target.
- Extended `docs/agents/local-platform-runbook.md` §4.1 with relay choice, GOTRUE_SMTP_* / SMTP_* placeholders, path-(A) enablement + smoke, D-05 rollback (`GOTRUE_MAILER_AUTOCONFIRM=true` + reload), Pitfall-16 signup-edge blocker, and D-06 criterion-4 → Phase 21 precondition.
- Domain tripwire `tests/unit/test_auth_email_domain.py` green (5 passed) with zero edits; no new ADR; no SMTP env/secrets committed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Close g-01-3b-signup-mailer with shipped path-(B) fix reference** - `6ab457e` (docs)
2. **Task 2: Extend runbook §4.1 with relay shape, smoke, rollback, and Phase 21 gap** - `21f6889` (docs)

**Plan metadata:** (pending final docs commit)

## Files Created/Modified

- `.planning/debug/g-01-3b-signup-mailer.md` — resolved frontmatter + Resolution; diagnosis body retained (D-12/D-14)
- `docs/agents/local-platform-runbook.md` — §4.1.1–4.1.3 relay shape / enablement / criterion-4 gap (D-03/D-05/D-06/D-13)

## Decisions Made

- D-12: Close debug in place (not delete / optional move skipped); cite 20-01 files in Resolution.
- D-03/D-04: Shape-only placeholders in runbook; no separate relay ADR.
- D-01/D-06: Path (A) remains target; live relay proof acknowledged as Phase 21 precondition, not half-enabled in git.
- D-05: Rollback is single flag `GOTRUE_MAILER_AUTOCONFIRM=true` + Auth reload.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification Outcomes

```text
git ls-files -- .planning/debug/g-01-3b-signup-mailer.md
→ .planning/debug/g-01-3b-signup-mailer.md tracked

rg -n "## Resolution|mailer_autoconfirm|unexpected_failure|CONFIRM_MESSAGE" .planning/debug --glob "*g-01-3b-signup-mailer.md"
→ hits include ## Resolution, mailer_autoconfirm, unexpected_failure, CONFIRM_MESSAGE

rg -n "GOTRUE_SMTP_|GOTRUE_MAILER_AUTOCONFIRM|SMTP_|Phase 21|mailer_autoconfirm|/auth/v1/settings" docs/agents/local-platform-runbook.md
→ all required tokens present

uv run pytest tests/unit/test_auth_email_domain.py -x
→ 5 passed; file unmodified
```

## User Setup Required

Operator-only (not this session): supply corporate relay `GOTRUE_SMTP_*` on the VM, prove smoke, then optionally flip to path (A). Values stay off git. See runbook §4.1.1–4.1.3.

## Next Phase Readiness

- Phase 20 docs/ops half of MAIL-02 complete; path (B) remains shipped honest end state.
- Phase 21 inherits explicit precondition: relay chosen and proven on GoTrue lane before MAIL-01 live digest send.
- No SMTP flips or runtime env changes performed this session.

## Self-Check: PASSED

- FOUND: `.planning/debug/g-01-3b-signup-mailer.md`
- FOUND: `docs/agents/local-platform-runbook.md`
- FOUND: commits `6ab457e`, `21f6889`
- FOUND: `## Resolution` + `unexpected_failure` + `mailer_autoconfirm` + `CONFIRM_MESSAGE` in closed debug file
- FOUND: `GOTRUE_SMTP_`, `GOTRUE_MAILER_AUTOCONFIRM`, `SMTP_`, `Phase 21`, `/auth/v1/settings` in runbook
- FOUND: no new ADR; `test_auth_email_domain.py` unmodified

---
*Phase: 20-mail-02-signup-confirmation-mail*
*Completed: 2026-10-16*
