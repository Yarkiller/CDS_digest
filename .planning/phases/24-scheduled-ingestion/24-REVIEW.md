---
phase: 24-scheduled-ingestion
reviewed: 2026-10-18T17:40:00Z
depth: standard
scope: "gap closure 24-07 (G-24-3) + 24-08 (G-24-4); tree at 64812b7 (diff 97e3b2d..64812b7)"
files_reviewed: 4
files_reviewed_list:
  - deploy/systemd/digest-ingest.service
  - deploy/systemd/digest-ingest-alert.service
  - tests/unit/test_phase24_systemd_units.py
  - docs/agents/local-platform-runbook.md
records_reviewed:
  - .planning/phases/24-scheduled-ingestion/24-07-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-08-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-07-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-08-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-VERIFICATION.md
  - .planning/phases/24-scheduled-ingestion/24-SECURITY.md
  - .planning/phases/24-scheduled-ingestion/24-PATTERNS.md
  - .planning/phases/24-scheduled-ingestion/24-VALIDATION.md
  - .planning/phases/24-scheduled-ingestion/24-CONTEXT.md
  - .planning/phases/24-scheduled-ingestion/24-UAT.md
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 24: Code Review Report (gap closure 24-07 / 24-08)

**Reviewed:** 2026-10-18T17:40:00Z
**Depth:** standard
**Files Reviewed:** 4 source/doc files + 10 planning records
**Status:** issues_found
**Scope:** `97e3b2d..64812b7` — plan 24-07 (G-24-3, oneshot start-phase bound) and plan 24-08 (G-24-4, numeric alert exit status), reviewed on the current tree after the `64812b7` fix pass.

## Summary

All three warnings from the previous revision are genuinely fixed in the tree, not just in the diff summary: §5e now prescribes the mutation-proven `TimeoutStartSec=500ms` and explains why 2 s cannot discriminate, §4k and §5e item 5 qualify the "not stamped" claim with "when the kill lands before `stamp_last_run`", `24-CONTEXT.md:19` no longer advertises the inert knob, and item 8's cleanup removes the runtime drop-in with an explicit warning against a whole-unit revert. `uv run pytest tests/unit/test_phase24_systemd_units.py -q` → **15 passed**; `uv run pytest -q` → **1151 passed**. Both new negative assertions and the new positive one were mutation-proved (each fails when the regression returns) and the tree was restored byte-exact.

Two warnings remain, both documentation/contract, none in the runtime units. First, `24-VERIFICATION.md` still states the unconditional "killed run → `last_run_at` not updated" in two places, and its own test text invites the operator to "temporarily reduce the limit" — the exact case the probe showed still stamps. Second, the new §5e negative bans do more than block a bad recipe: they make §5e unable to *name* the command it forbids, they force the rejected value to be spelled around (`2 s`), and the run-limit recipe lost its explicit drop-in removal command. One further contract-coverage note (IN-03): the qualification itself is unpinned — deleting both "before `stamp_last_run`" clauses keeps the suite green, which I verified.

## Critical Issues

None.

## Warnings

### WR-04: `24-VERIFICATION.md` still states the unconditional "not stamped" invariant, and its own instruction invites the limit that stamps

**File:** `.planning/phases/24-scheduled-ingestion/24-VERIFICATION.md:89-91, :267-269` (secondary: `24-UAT.md:36,97`)
**Issue:** The frontmatter human-verification item and body item 3 still read "Прогон убит; `last_run_at` не обновлён" with no caveat, while the runbook (`:606`, `:721`) now says the stamp is skipped only "**when the kill lands before `stamp_last_run`**". Worse, the frontmatter test text is "имитировать зависший прогон дольше 1800 с (**или временно уменьшить лимит**)" — the reduce-the-limit branch is exactly what `24-07-SUMMARY.md:179` measured: at `TimeoutStartSec=2` the unit ended `Result=timeout` *and* `last_run_at` advanced. An operator who follows this record with a short limit records a false failure against a mitigation that works. The same unqualified wording survives in `24-UAT.md:36,97`, which the gap plans deliberately keep as defect history — note only, not a required edit.
**Why it matters:** This is the surviving half of WR-01: the runbook and the SUMMARY were corrected, but the record that `/gsd-verify-work` and the operator actually execute still demands the behaviour the probe disproved for short limits.
**Fix:** Append the same qualifier and a pointer, e.g. `expected: "Прогон убит; last_run_at не обновлён (при условии, что kill пришёл до stamp_last_run — короткий лимит может попасть в shutdown tail; см. §5e item 5 и 24-07-SUMMARY § Deviations 1); следующий тик снова due"`, in both the frontmatter item (`:90`) and body item 3 (`:268`); narrow "временно уменьшить лимит" to "уменьшить лимит до 500 ms".

### WR-05: The §5e negative bans suppress the prohibition they encode, and item 5 lost its drop-in removal command

**File:** `tests/unit/test_phase24_systemd_units.py:215-220`; `docs/agents/local-platform-runbook.md:725, :732`
**Issue:** Two effects of the new whole-section bans:
1. `assert "systemctl revert" not in section_5e` bans the token anywhere in §5e, so the runbook can no longer *name* the command it forbids — it must say "a whole-unit revert" (`:732`). The operator's muscle memory is the literal command; a warning that cannot spell it is strictly weaker, and the next editor who makes the warning explicit gets a red test whose message ("§5e must not prescribe systemctl revert") mislabels a prohibition as a prescription. The same over-reach applies to `assert "TimeoutStartSec=2" not in section_5e`, which is why the factual counter-example had to be written as "2 s" / "2s" (`:725`) instead of the value the operator would type.
2. Item 5's drop-in teardown lost its command entirely: it now ends "…then remove the drop-in and show the next start stamps" (`:725`) with no `rm`/revert line and no pointer, while the only concrete removal command lives in item 8's alert recipe (`:732`). The run-limit recipe is therefore no longer self-contained/copy-pasteable, which the 24-07 plan required of both §5e recipes.
**Why it matters:** A gate that punishes naming a forbidden command pushes future edits toward vaguer prose, which is the failure mode the drift tests exist to prevent; and a probe recipe that omits its teardown leaves the operator to improvise — plausibly with the very `systemctl revert` the section forbids.
**Fix:** Prefer *positive* pins of the recipe, which give the same protection without suppressing prose:
```python
    assert "apply the `TimeoutStartSec=500ms` runtime drop-in" in section_5e
    assert "rm -f /run/systemd/system/digest-ingest.service.d/override.conf" in section_5e
```
A regression that swaps either command makes the positive assertion fail, so the bare-token bans are redundant. If a negative is still wanted for the "someone adds a second, dangerous recipe" case, bind it to the prescription phrase (`"TimeoutStartSec=2` runtime drop-in"`) rather than the bare value `TimeoutStartSec=2`, and move the "revert deletes every drop-in" hazard to §4k, where no ban applies. Restore an explicit teardown in item 5: `sudo rm -f /run/systemd/system/digest-ingest.service.d/override.conf; sudo systemctl daemon-reload`.

## Info

### IN-01: Text contract still does not pin `RuntimeDirectoryMode=0750` or the exact `EnvironmentFile=` path

**File:** `tests/unit/test_phase24_systemd_units.py:61-82`; `deploy/systemd/digest-ingest.service:12,15`
**Issue:** Both bytes are intact today and both 24-07 and 24-08 list them among the "untouched bytes", but `test_service_tokens` asserts only the `EnvironmentFile=` prefix and `RuntimeDirectory=digest-ingest`. A regression to `RuntimeDirectoryMode=0777` — a world-writable directory holding `/run/digest-ingest/lock` — or to a repo-local env file keeps 15/15 and 1151 green. Left at Info deliberately: this is coverage advice with no current defect, and `test_service_lock_path_via_runtime_directory` already pins the directory name and path.
**Fix:** Add `"EnvironmentFile=/etc/digest-cds/ingest.env"` and `"RuntimeDirectoryMode=0750"` to the token tuple in `test_service_tokens`.

### IN-02: Historical research records still prescribe the superseded mechanisms

**File:** `.planning/phases/24-scheduled-ingestion/24-RESEARCH.md:881,915,927` (also `24-04-SUMMARY.md:33,142`, `24-03-PLAN.md:45`, `24-04-PLAN.md:31`, `24-DISCUSSION-LOG.md:272`)
**Issue:** Research acceptance criteria still require `RuntimeMaxSec=1800`, A8 still concludes "Ubuntu 24.04 = systemd 255, где применим" (the opposite of the finding), and `:927` prescribes `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}`. 24-07's source audit does address A8, but no plan mentions `24-RESEARCH.md:927` at all, so the broken alert expression sits in the research record with no supersession marker. Stays Info: these are immutable history and must keep the defect description; the risk is a future planner re-deriving the broken contract from them.
**Fix:** Append the same "SUPERSEDED (mechanism token only)" marker to A8 and to `:927`, or record the research file explicitly in a plan's source audit. Do not add these files to the whole-file negative gates.

### IN-03: The "kill lands before `stamp_last_run`" qualification is itself unpinned

**File:** `tests/unit/test_phase24_systemd_units.py:204-221`; `docs/agents/local-platform-runbook.md:606, :721`
**Issue:** Mutation-proved: deleting both qualifiers ("`last_run_at` is **not** stamped **when the kill lands before `stamp_last_run`**" in §5e, and the "provided the kill lands before `stamp_last_run`" clause in §4k) leaves the suite at **15 passed**. The gates pin the value (500 ms) and the absence of the bad tokens, but not the caveat that WR-01 added — so the prose half of that fix can silently regress.
**Fix:** Add `assert "stamp_last_run" in section_4k` and `assert "stamp_last_run" in section_5e` to `test_runbook_and_records_name_the_oneshot_start_limit` (a short stable token, so it does not over-constrain the wording the way WR-05 does).

## Resolved since the previous revision (commit `64812b7`)

| Was | Fixed by | Verified in the current tree |
|---|---|---|
| **WR-01** — §5e prescribed `TimeoutStartSec=2` while expecting "not stamped", contradicting the recorded probe; SUMMARY claimed a 500 ms fallback the recipe did not have | `64812b7` | `runbook.md:725` now prescribes `TimeoutStartSec=500ms` and names the 2 s counter-example; `:606` and `:721` qualify the claim; `24-07-SUMMARY.md:181-182` now records that the recipe prescribed 2 s and was corrected at this gate. Mutation: reverting to `TimeoutStartSec=2` fails `test_phase24_systemd_units.py:215`. |
| **WR-02** — `24-CONTEXT.md:19` still advertised `RuntimeMaxSec=` with no marker | `64812b7` | In-scope bullet now reads `TimeoutStartSec=` plus an inline supersession note naming 24-07; matches D-19/D-23 at `:63,:67`. |
| **WR-03** — `systemctl revert` as cleanup deletes every drop-in, persistent included | `64812b7` | `runbook.md:732` now removes only `/run/systemd/system/digest-ingest.service.d/override.conf` and warns against a whole-unit revert. Mutation: substituting `sudo systemctl revert digest-ingest.service` fails `:220`. |

## Checked and Found Sound

**Gate strength (mutation-proved on the current tree, then restored byte-exact):**

| Mutation applied | Result |
|---|---|
| `digest-ingest.service`: `TimeoutStartSec=1800` → `RuntimeMaxSec=1800` | 2 failed (`test_service_tokens`, `test_service_does_not_use_runtime_limit_on_oneshot`) |
| good token kept **and** `RuntimeMaxSec=1800` appended | 1 failed (`test_service_does_not_use_runtime_limit_on_oneshot`) — the negative gate is not shadowed by the positive one |
| alert: numeric substitution → `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}` | 2 failed (`test_alert_unit`, `test_alert_unit_does_not_read_exit_qualifier`) |
| runbook §4k/§5e `TimeoutStartSec` → `RuntimeMaxSec`, §5e `MONITOR_EXIT_STATUS` → `MONITOR_EXIT_CODE` | 2 failed (`test_runbook_and_records_name_the_oneshot_start_limit`, `test_runbook_and_verification_name_numeric_status`) |
| §5e `TimeoutStartSec=500ms` → `TimeoutStartSec=2` | 1 failed at `:215` |
| §5e cleanup → `sudo systemctl revert digest-ingest.service` | 1 failed at `:220` |
| both "before `stamp_last_run`" qualifiers deleted | **15 passed** — see IN-03 |
| restored tree | `15 passed`; full suite `1151 passed` |

**Counts:** `test_phase24_systemd_units.py` collects **15** tests; `24-VERIFICATION.md:130` and the ING-06 row (`:233`) both say **15** text checks, and the three new assertions live inside the existing test, so the number still holds. No `10 text-проверок` / `10 text-checks` claim remains.

**Untouched-byte constraints** — present in `digest-ingest.service`: `Type=oneshot`, `flock -n -E 75 /run/digest-ingest/lock <venv>/ingest-collect`, `SuccessExitStatus=0 75`, `RuntimeDirectory=digest-ingest`, `RuntimeDirectoryMode=0750`, `OnFailure=digest-ingest-alert.service`, `User/Group=digestcds`, `EnvironmentFile=/etc/digest-cds/ingest.env`, `TZ=UTC`, `NoNewPrivileges`, `PrivateTmp`; the timer keeps `OnCalendar=*:0/15`, `Persistent=false`, `Unit=digest-ingest.service`. Pinning coverage is complete except for IN-01.

**§5e item 8 factual correctness:** `systemctl edit --runtime` writes `/run/systemd/system/<unit>.d/override.conf`, so the new `rm -f` path is exactly right (verified against `systemctl revert` semantics on systemd 255: `revert` removes the `*.d/` trees below both `/etc/systemd/system` and `/run/systemd/system`). The `ExecStart=`-then-`ExecStart=` reset sequence is the correct way to replace the command in a drop-in.

**Alert `case` for a killed run:** a SIGTERM kill yields `MONITOR_EXIT_STATUS=15`; there is no `15)` arm, so it falls to `*)` and prints `unexpected failure (exit 15)` with the numeric code. The plan explicitly excludes a `killed)` arm; acceptable and consistent with the recorded pre-fix `(exit killed)` / post-fix `(exit 15)` behaviour.

**Records:** `24-VERIFICATION.md`, `24-PATTERNS.md` and `24-VALIDATION.md` are clean of the inert token; `24-VERIFICATION.md` is clean of the qualifier; `24-SECURITY.md` T-24-32/T-24-34 name the working mechanisms, keep `closed`, and the alias/audit-trail edits are consistent (30 distinct + 2 aliases). `24-UAT.md` and the SECURITY re-verification notes keep the defect history and are correctly excluded from the gates; `ROADMAP.md` criterion 3 keeps the milestone wording per the 24-07 source audit.

**Live probes reported by the orchestrator are not re-litigated** (WSL2 / systemd 255): `TimeoutStartUSec=30min` / `RuntimeMaxUSec=infinity`, scratch-unit kill at ≈3115 ms (`Result=timeout`, `ExecMainStatus=15`), `RuntimeMaxSec` control at ≈10011 ms (`Result=success`), the 500 ms real-unit kill at 530 ms without a stamp followed by a stamping run, and the exit-1/exit-2 alert lines with `digestcds` + hardening intact.

## Prior review findings (refreshed against the current tree)

**Resolved and dropped:** CR-01 (cursor write wrapped in its own `try/except`, `collect_batch.py:192-202`), WR-02 (unexpected feed exceptions isolated, `:138-145`), WR-03 (zero-source due run no longer stamps), WR-04 (alert runs as `digestcds` with hardening), WR-05 (cleared time restores the saved value), WR-06 (empty upsert re-reads the row).

**Carried over, unchanged and outside this diff (not counted above):**
- The previous **WR-01** (cursor advances past a failed video) remains an accepted risk under D-09; reversal was explicitly declined by the operator.
- The previous **IN-01..IN-03** (feed skip-reason taxonomy, double `Settings.from_env()`, AST blind spot for dynamic imports) remain deferred polish; they are recorded in `24-VERIFICATION.md`’s anti-patterns table. They are unrelated to IN-01..IN-03 in this revision, which are numbered independently for the gap-closure scope.

---

_Reviewed: 2026-10-18T17:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
