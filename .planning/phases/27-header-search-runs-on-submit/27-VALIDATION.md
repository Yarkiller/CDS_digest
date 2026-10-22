---
phase: 27
slug: header-search-runs-on-submit
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-22
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `27-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `@playwright/test` 1.62.1 (journeys) + `node:test` v24.21.0 (static gates) |
| **Config file** | `playwright.config.js` (root, `projects.web`, `VITE_USE_MOCKS: "true"`); `scripts/run-unit-js.cjs` (flat glob of `tests/unit/*.js`) |
| **Quick run command** | `npx playwright test --project=web tests/knowledge.spec.js -g "<slice>"` / `npm run test:js` for static gates |
| **Full suite command** | `npm run test:web && npm run test:js` |
| **Estimated runtime** | ~90 s (mock mode, Chromium only) |

> **Script-name trap:** `"test:js": "node scripts/run-unit-js.cjs"`, `"test:web": "playwright test --project=web"`, **`"test:unit": "uv run pytest"`** (Python). JS gates run under `npm run test:js`; `npm run test:unit` proves nothing for this phase.

---

## Sampling Rate

- **After every task commit:** the slice's `-g` command, or `npm run test:js` for static-gate slices (S0/S3/S8).
- **After every plan wave:** `npx playwright test --project=web tests/knowledge.spec.js tests/web-app.spec.js && npm run test:js`
- **Before `/gsd-verify-work`:** `npm run test:web && npm run test:js` green against a fresh `5174` server
- **Max feedback latency:** ~40 s per slice

---

## Per-Task Verification Map

Slices come from `27-RESEARCH.md` § Proposed TDD Slice Order; plan/wave IDs are assigned by the planner.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| S0 — adapter digest pin | 27-01 | 1 | KNOW-05 | — | `knowledgeApi.js` byte-identical (no adapter edit) | unit | `npm run test:js` | ❌ W0 | ⬜ pending |
| S1 — tracer: header Enter ⇒ rows | 27-02 | 2 | KNOW-05 | T-27-V5 | Query validated before request; `?q` rendered as text only | e2e | `npx playwright test --project=web tests/knowledge.spec.js -g "header submit"` | ❌ W0 | ⬜ pending |
| S2 — single request + non-vacuity | 27-02 | 2 | KNOW-05 | — | Exactly one `searchKnowledge` call per submit (StrictMode-safe) | e2e | `-g "single request\|counter non-vacuity"` | ❌ W0 | ⬜ pending |
| S3 — single call site gate | 27-01 | 1 | KNOW-05 | — | No second bypass of the counter | unit | `npm run test:js` | ❌ W0 | ⬜ pending |
| S4 — cache + Back/Forward restore | 27-03 | 3 | KNOW-05 | — | No request on history navigation; snapshot per `(q, role)` | e2e | `-g "back\|streak"` | ❌ W0 | ⬜ pending |
| S5 — `submitId` resubmit + strip | 27-03 | 3 | KNOW-05 | T-27-T | One-shot marker compared only, never used as URL/selector | e2e | `-g "resubmit\|strip"` | ❌ W0 | ⬜ pending |
| S6 — blank submit ⇒ landing, 0 requests | 27-04 | 4 | KNOW-05 | T-27-V5 | Blank guard returns before the network | e2e | `-g "blank"` | ❌ W0 | ⬜ pending |
| S7 — overlong submit ⇒ inline error, 0 requests | 27-04 | 4 | KNOW-05 | T-27-V5, T-27-DoS | 500 code-point cap enforced before any request | e2e | `-g "overlong"` | ❌ W0 | ⬜ pending |
| S8 — R-1 render gate + landing rule | 27-04 | 4 | KNOW-05 | — | Live region exists only during `searching`; landing keyed on `qUrl` | e2e | `-g "affordance"` | ❌ W0 | ⬜ pending |
| S9 — history discipline (`replace`) | 27-05 | 5 | KNOW-05 | — | Back leaves the page instead of replaying queries | e2e | `-g "history"` | ❌ W0 | ⬜ pending |
| S10 — error path reuses `kb-search-error` | 27-05 | 5 | KNOW-05 | — | Errors never cached (seed-then-fail proves eviction); retry issues exactly one new request | e2e | `-g "error"` | ❌ W0 | ⬜ pending |
| S11 — XSS probe on `?q` | 27-05 | 5 | KNOW-05 | T-27-XSS | `q=<img src=x onerror=alert(1)>` renders as text, zero rows, no dialog | e2e | `-g "xss\|markup"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Notes on ownership: the five plans map one-to-one onto waves 1–5, and every slice above belongs to a task in its plan (S0 → 27-01 Task 1, S3 → 27-01 Task 2; S1 → 27-02 Task 1, S2 → 27-02 Task 2; S4 → 27-03 Task 1, S5 → 27-03 Task 2; S6 → 27-04 Task 1, S7 → 27-04 Task 2, S8 → 27-04 Task 3; S9 → 27-05 Task 1, S10 → 27-05 Task 2, S11 → 27-05 Task 3). S8's assertions land in 27-04 Task 3, while R-1's one-line render gate that makes them reachable is applied in 27-02 Task 2. S10's "never cached" proof is a seed-then-fail case (success → seed, failure → evict, history revisit → +1), because the cache store is success-only and a case that begins with a failure could never redden.

---

## Wave 0 Requirements

- [ ] `tests/unit/test_knowledge_api_snapshot.js` — NEW; captures the pre-edit `knowledgeApi.js` sha256 digest. **Authored in S0, before any page edit.
- [ ] `tests/unit/test_knowledge_search_single_call_site.js` — NEW; exactly one `searchKnowledge` import and one non-comment call site in `web/src/**/*.{js,jsx}` (auto-discovered by `scripts/run-unit-js.cjs`).
- [ ] `tests/knowledge.spec.js` — counter (`X-1`) and affordance-collector (`X-2`) helpers + the KNOW-05 cases. **No new spec file**, therefore **no `testMatch` change** in `playwright.config.js`.
- [ ] No framework install; no fixture shared with other specs (helpers stay local to the file).
- [ ] Pre-flight: assert port `5174` is free before the first Playwright run (STATE § Blockers).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| C-12 «Показать ещё» offset resume | KNOW-05 | Structural in mocks: the 8-row mock catalogue with `DEFAULT_SEARCH_LIMIT = 10` never sets `has_more`, so the paging half of C-12 cannot be exercised. Recorded as an explicit deviation from the UI-SPEC assertion. | After execution, manually verify against a live/large dataset that restored snapshots resume at `nextOffset` = shown-rows count. Every other C-12 claim (identical row set/order restored, zero requests) is automated. |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
