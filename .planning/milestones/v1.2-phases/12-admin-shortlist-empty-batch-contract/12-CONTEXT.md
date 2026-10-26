# Phase 12: Admin shortlist empty-batch contract - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Close FIX-01 (Phase 10 carry): lock the `GET /admin/shortlist` empty-state HTTP contract so empty shortlist responses return HTTP 200 with empty `items` (never schema/validation 500), with distinct shapes for “no batches” vs “empty unsent batch,” plus aligned FE mock harness and Playwright coverage.

Scout note: `test_admin_shortlist_empty_batch_returns_200_empty_items` already passes locally (Phase 5 WR-04 added `week_label`/`sent_at`). This phase is **verify + harden**, not a greenfield fix — extend taxonomy coverage, document the lock, update requirement proof strings, and align mock/E2E. No new admin preview/draft→ready/PIPE work (Phases 13–16).

</domain>

<decisions>
## Implementation Decisions

### Done bar
- **D-01:** Phase 12 is **verify + harden** — green named unit alone is not enough; add explicit regression coverage for fuzzy empty edges. — **Reversibility:** reversible — tests/docs only if production already matches.
- **D-02:** **Scope-bound green:** FIX-01 proof tests (renamed no-batch + new empty-unsent) must be green; Phase 12 must introduce **no new** suite failures. Pre-existing unrelated `tests/unit` failures → note in SUMMARY as deferred / v1.2 backlog tickets, not Phase 12 scope. Fully green suite after FIX-01 is ideal but not a blocker for unrelated debt. — **Reversibility:** reversible.
- **D-03:** **No production change unless a failing test forces it** (project TDD). If use-case/HTTP already return the distinct shapes, ship tests + lock docs + mock/Playwright only. — **Reversibility:** reversible.

### Empty-state taxonomy
- **D-04:** **Distinct HTTP shapes** (not collapsed):
  - **No batches:** `{batch_id: null, items: [], week_label: null, sent_at: null, digest_rest: false, days_until_next_batch: null}` (plus any other already-declared fields at their empty defaults).
  - **Empty unsent batch:** `{batch_id: <id>, items: [], week_label: <week_start.isoformat()>, sent_at: null, digest_rest: false, days_until_next_batch: null}`.
  — **Reversibility:** costly — SPA and tests will branch on null vs present `batch_id`.
- **D-05:** Rename existing `test_admin_shortlist_empty_batch_returns_200_empty_items` → `test_admin_shortlist_no_batches_returns_null_batch_id` (keep exact no-batch semantics). Add `test_admin_shortlist_empty_unsent_batch_returns_batch_id`. Update REQUIREMENTS FIX-01 and ROADMAP success criteria to cite both. — **Reversibility:** reversible — rename + docs.
- **D-06:** Empty-unsent `week_label` = `batch.week_start.isoformat()` (same as non-empty path). No human RU formatter in this phase. — **Reversibility:** costly if clients later assume human strings from API.
- **D-07:** HTTP empty-edge coverage is **in-memory unit only** (`test_http_admin.py` + `InMemoryShortlistRepository`). No live Supabase adapter test required for FIX-01.

### Contract authority
- **D-08:** Tests assert **required keys + critical values** (status 200, `items == []`, `batch_id` null-vs-int, `week_label` null-vs-isoformat, `sent_at is null`, `digest_rest is false`). Do **not** use brittle full-dict `response.json() == {…}` equality so additive *declared* fields can land later without rewriting the whole blob. — **Reversibility:** reversible.
- **D-09:** Keep `AdminShortlistResponse` **`extra="forbid"`**. Additive API fields require explicit model + test + PR; forbid catches internal construction bugs. — **Reversibility:** costly — changes response validation posture.
- **D-10:** Author phase artifact `12-FIX-01-LOCK.md` under this phase directory documenting both empty shapes and required-key asserts. Downstream planner/executor MUST read it. — **Reversibility:** reversible.

### FIX-01 surface (FE / E2E)
- **D-11:** Phase 12 includes **HTTP unit + FE mock harness + Playwright** (not docs-only). Preview honesty / draft→ready remain Phases 13–14. — **Reversibility:** reversible.
- **D-12:** Mock both shapes; Playwright covers each path with the same empty UI asserts («Кандидатов пока нет», Обновить, no «пайплайн», not digest-rest). Keep `__DIGEST_ADMIN_EMPTY__` as no-batch `emptyDto()`. Add sticky flag `__DIGEST_ADMIN_EMPTY_UNSENT__` returning `{batch_id, week_label: ISO, items: [], sent_at: null, digest_rest: false}`. — **Reversibility:** costly — harness flag becomes E2E contract.
- **D-13:** Empty-unsent mock `week_label` uses **ISO** (API parity). No intentional new empty-state design/copy (D-80 stands). Playwright **may** assert incidental existing week chrome (`Неделя {week_label}`) if empty-unsent already surfaces it — no new chrome work unless a failing test requires it under TDD.

### Carried forward (do not re-open)
- Phase 5 **D-80:** empty shortlist UI «Кандидатов пока нет» + «Обновить»; never 404 for empty.
- Phase 5 **D-81:** current batch = latest unsent (`sent_at IS NULL`).
- Phase 5 **G-05-2 / digest_rest:** after-send rest is a separate shape (`digest_rest=true`); must not be confused with genuine empty.

### Claude's Discretion
- Exact assertion helpers / shared fixtures in `test_http_admin.py` as long as D-04/D-08 hold.
- Exact Playwright test naming/structure as long as both mock flags are exercised.
- Whether production `get_admin_shortlist` already satisfies D-04 without edits (prove via failing-then-passing tests only if a gap appears).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/ROADMAP.md` — Phase 12 goal, success criteria, FIX-01 mapping (update proof test names per D-05)
- `.planning/REQUIREMENTS.md` — FIX-01 (update wording per D-05 / D-08)
- `.planning/PROJECT.md` — v1.2 focus; empty-batch unit carry
- `.planning/STATE.md` — deferred_items pointer from Phase 10

### Prior phase locks
- `.planning/milestones/v1-phases/05-admin-digest-publish/05-CONTEXT.md` — D-80, D-81, shortlist HTTP contract, digest_rest
- `.planning/milestones/v1.1-phases/10-cli-composition-uat/deferred-items.md` — original FIX-01 deferral (`sent_at` / `week_label` extras)
- `.planning/milestones/v1.1-phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-CONTEXT.md` — out of scope for admin empty-batch (CLI diagnostics)

### Phase lock artifact (to create during execution)
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — empty-shape contract tables (MUST write in this phase)

### Implementation surfaces
- `tests/unit/test_http_admin.py` — rename no-batch test; add empty-unsent test
- `backend/src/backend/interface/http/routes/admin.py` — `AdminShortlistResponse` (`extra="forbid"`)
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` — empty / digest_rest assembly
- `backend/src/backend/domain/shortlist.py` — `AdminShortlist` DTO
- `backend/src/backend/tests_support/in_memory.py` — `InMemoryShortlistRepository`
- `web/src/services/adminApi.js` — mock DTOs + sticky flags
- `web/src/pages/AdminDigestPage.jsx` — empty / week_label chrome
- `tests/admin.spec.js` — empty shortlist + digest_rest E2E

### Architecture / TDD
- `.cursor/rules/architecture.mdc` — Ports & Adapters; thin HTTP
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — no production code without failing test first

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AdminShortlistResponse` already declares `week_label`, `sent_at`, `digest_rest`, `days_until_next_batch` with `extra="forbid"`.
- `get_admin_shortlist` already returns no-batch nulls and digest_rest for sent latest; non-empty path sets `batch_id` + iso `week_label` — empty-unsent with `items=()` likely already yields D-04’s second shape if `get_current_batch()` returns a batch.
- `adminApi.js`: `emptyDto()`, `restDto()`, `__DIGEST_ADMIN_EMPTY__`, `__DIGEST_ADMIN_DIGEST_REST__` harness pattern to extend.
- `tests/admin.spec.js`: existing empty + digest_rest Playwright cases to mirror for empty-unsent.

### Established Patterns
- In-memory HTTP tests via `build_in_memory_container` + JWKS minting in `test_http_admin.py`.
- Sticky `window.__DIGEST_ADMIN_*__` flags for Playwright mock modes.
- Honesty empty copy D-80; digest_rest must not masquerade as empty.

### Integration Points
- `GET /admin/shortlist` → `get_admin_shortlist` → `_to_response`.
- SPA `AdminDigestPage` maps `batch_id` / `week_label` / `sent_at` / `digest_rest` from DTO.
- FIX-01 checkbox in REQUIREMENTS + Phase 12 roadmap row.

</code_context>

<specifics>
## Specific Ideas

- User-specified proof tests: `test_admin_shortlist_no_batches_returns_null_batch_id` and `test_admin_shortlist_empty_unsent_batch_returns_batch_id`.
- User-specified lock file: `12-FIX-01-LOCK.md` with contract tables; tests use required-key asserts (not full `==`).
- Done bar checklist from user: (1) renamed no-batch green (2) new edge green (3) no NEW failures from Phase 12 (4) pre-existing unrelated → SUMMARY deferred.
- New mock flag name: `__DIGEST_ADMIN_EMPTY_UNSENT__`.

</specifics>

<deferred>
## Deferred Ideas

- Admin material / email preview honesty — Phase 13
- Draft→ready control and justification honesty — Phase 14
- CLI `--debug` diagnostics — Phase 15 (note: Phase 11 text saying “Phase 12+” for debug channel refers to this later work, now numbered 15)
- PIPE-01 config UI — Phase 16
- Live Supabase empty-batch adapter test — out of FIX-01 per D-07
- Human RU `week_label` formatting on API — rejected for Phase 12

None additional from discussion beyond roadmap deferrals.

</deferred>

---

*Phase: 12-Admin shortlist empty-batch contract*
*Context gathered: 2026-10-02*
