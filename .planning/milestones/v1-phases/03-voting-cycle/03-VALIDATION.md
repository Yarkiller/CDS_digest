---
phase: 3
slug: voting-cycle
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-20
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.3.0 + Playwright ^1.62.1 |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| **Quick run command** | `uv run pytest tests/unit/test_cast_vote.py tests/unit/test_http_voting.py -x` |
| **Full suite command** | `uv run pytest` && `npx playwright test --project=web` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run targeted pytest file `-x` or a single Playwright test
- **After every plan wave:** `uv run pytest` + `npx playwright test --project=web`
- **Before `/gsd-verify-work`:** Full unit + web Playwright suite must be green
- **Max feedback latency:** Prefer &lt;60s per task; full suite ~120s allowed at phase gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-W0-01 | 00 | 0 | VOTE-01 | T-03-01 | JWT user_id only; one row per (cycle, user) | unit | `uv run pytest tests/unit/test_cast_vote.py -x` | ❌ W0 | ⬜ pending |
| 03-W0-02 | 00 | 0 | VOTE-01, VOTE-03 | T-03-02 | closed cycle 409; extra fields 422 | unit | `uv run pytest tests/unit/test_http_voting.py -x` | ❌ W0 | ⬜ pending |
| 03-W0-03 | 00 | 0 | VOTE-04 | T-03-03 | topic∈cycle; leaders/ties from server | unit | `uv run pytest tests/unit/test_get_ballot.py -x` | ❌ W0 | ⬜ pending |
| 03-W0-04 | 00 | 0 | VOTE-02 | — | «голос не отдан»; no pre-selected radio | e2e | `npx playwright test tests/web-app.spec.js -g "голос не отдан"` | ⚠️ rewrite | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → assertion path (phase gate)

| Requirement | Automated path |
|-------------|----------------|
| VOTE-01 | unit `test_cast_vote` / `test_http_voting` + e2e confirm stores one vote; empty submit blocked |
| VOTE-02 | e2e never-voted copy «голос не отдан»; `getByRole('radio')` checked count 0; leader strip separate from personal choice |
| VOTE-03 | unit A→B while open; POST 409 `CYCLE_CLOSED` with ballot in body; e2e «Изменить голос» |
| VOTE-04 | unit ballot DTO dek + `materials_count` including 0; e2e «0 материалов» |
| D-51/D-54 | unit HTTP 409 body contains ballot snapshot |
| D-53/D-55 | e2e GET splash vs POST ErrorPanel (`?simulateError=1` + GET fail arm) |

---

## Wave 0 Requirements

- [ ] `tests/unit/test_cast_vote.py` — in-memory fake: one row, A→B, closed reject, bad topic, CAS conflict
- [ ] `tests/unit/test_http_voting.py` — JWT 401; GET snapshot; POST 200 snapshot; POST 409 `CYCLE_CLOSED` includes ballot; extra fields 422
- [ ] `tests/unit/test_get_ballot.py` — leaders/ties/hide-when-zero; empty topics; no cycle
- [ ] Playwright: never-voted copy + no «Лидирует» + «Изменить голос» + empty submit «Выберите тему»; never `toBeChecked()` on `<button role="radio">`
- [ ] `InMemoryVoteRepository` in `tests_support/in_memory.py`
- [ ] Framework install: none — existing pytest + Playwright cover the stack

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Ballot visual: leader strip vs personal choice | VOTE-02 / UI-SPEC | Contrast and layout judgment | Open `/voting` never-voted at 1280 and 390; confirm leading topic is not the selected radio |
| Closed-cycle copy and disabled radios | VOTE-03 / D-48 | Visual + copy judgment | Load closed snapshot; confirm closed message and radios not actionable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency &lt;60s for non-gate tasks
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
