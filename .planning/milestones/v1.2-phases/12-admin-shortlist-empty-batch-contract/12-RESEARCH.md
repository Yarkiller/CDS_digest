# Phase 12: Admin shortlist empty-batch contract - Research

**Researched:** 2026-10-02
**Domain:** FastAPI/Pydantic admin shortlist HTTP contract + FE mock/Playwright empty-state taxonomy
**Confidence:** HIGH (implementation already present; phase is verify+harden)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- Admin material / email preview honesty — Phase 13
- Draft→ready control and justification honesty — Phase 14
- CLI `--debug` diagnostics — Phase 15 (note: Phase 11 text saying “Phase 12+” for debug channel refers to this later work, now numbered 15)
- PIPE-01 config UI — Phase 16
- Live Supabase empty-batch adapter test — out of FIX-01 per D-07
- Human RU `week_label` formatting on API — rejected for Phase 12

None additional from discussion beyond roadmap deferrals.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-01 | Empty admin shortlist HTTP contract aligned (`sent_at` / `week_label` / schema); proof tests green | Production already returns D-04 shapes; rename no-batch test; add empty-unsent HTTP unit; soft required-key asserts; `12-FIX-01-LOCK.md`; FE `__DIGEST_ADMIN_EMPTY_UNSENT__` + Playwright; update REQUIREMENTS/ROADMAP proof strings |
</phase_requirements>

## Project Constraints (from AGENTS.md / architecture / TDD)

No `./CLAUDE.md` or `./.claude/CLAUDE.md` found in this workspace. Enforce project rules from `AGENTS.md`, `.cursor/rules/tdd.mdc`, and `.cursor/rules/architecture.mdc`:

- **TDD:** `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST` — matches D-03.
- **Ports & Adapters:** domain/use-case stay free of FastAPI/Supabase; HTTP route stays thin (`get_admin_shortlist` → `_to_response`); in-memory fakes for unit HTTP.
- **FE API boundary:** SPA talks through `web/src/services/` only (`adminApi.js`).
- **Exceptions:** docs/lock artifacts and requirement string updates need no failing test first.

Project skills under `.agents/skills/` (`supabase`, `supabase-postgres-best-practices`, `hallmark`) are not primary for this phase (no live DB / PIPE work).

## Summary

Phase 12 closes FIX-01 as **verify + harden**, not a greenfield schema fix. The historical Phase 6–10 failure was brittle full-dict equality on `GET /admin/shortlist` when `week_label` / `sent_at` became declared response fields. Today that named unit already passes, and `get_admin_shortlist` already emits both locked empty shapes: no-batch nulls, and empty-unsent with `batch_id` + ISO `week_label`.

**Primary recommendation:** Ship tests + lock doc + mock/Playwright + REQUIREMENTS/ROADMAP proof-string updates first; touch production only if a new empty-unsent HTTP test fails under TDD.

Verified this session: `test_admin_shortlist_empty_batch_returns_200_empty_items` and `test_get_admin_shortlist.py` → **9 passed**; empty-unsent use-case probe with `items=()` returns `{batch_id: 7, week_label: '2026-10-06', sent_at: None, digest_rest: False, days_until_next_batch: None}`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Empty-state taxonomy (no-batch vs empty-unsent vs digest_rest) | API / Backend (use-case) | — | `get_admin_shortlist` owns branch logic over `ShortlistRepository` |
| HTTP 200 + JSON schema (`AdminShortlistResponse`, `extra="forbid"`) | API / Backend (HTTP) | — | Thin route + Pydantic `response_model` serialization/validation |
| In-memory FIX-01 proof tests | API / Backend (unit) | — | `test_http_admin.py` + `InMemoryShortlistRepository` (D-07) |
| SPA empty UI (D-80 copy) | Browser / Client | — | `AdminDigestPage` maps DTO → empty vs rest; no new design |
| Mock harness sticky flags | Browser / Client | — | `adminApi.js` `fetchShortlist` mock branch for Playwright |
| Playwright empty-path coverage | Browser / Client (E2E) | — | `tests/admin.spec.js` exercises both mock flags |
| Contract lock artifact | Docs / planning | — | `12-FIX-01-LOCK.md` is planner/executor authority |
| Live Supabase empty-batch | Database / Storage | — | **Out of scope** (D-07) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `0.141.1` | Admin HTTP routes + `response_model` | Already pinned in `backend/pyproject.toml`; validates/serializes responses [VERIFIED: uv run + backend/pyproject.toml:8] |
| Pydantic | `2.13.5` | `AdminShortlistResponse` / `ConfigDict(extra="forbid")` | FastAPI dependency; forbid catches undeclared construction [VERIFIED: uv run python import] |
| pytest | `>=8.3.0` (env has working pytest via `uv run`) | Unit HTTP contract tests | Project unit runner [VERIFIED: root pyproject.toml:28] |
| Playwright | `@playwright/test ^1.62.1` | Admin empty E2E | Existing `tests/admin.spec.js` harness [VERIFIED: package.json:18] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Starlette TestClient (via FastAPI) | bundled with FastAPI/Starlette | In-memory HTTP client in `test_http_admin.py` | Already used by admin HTTP units |
| `cryptography` / PyJWT | pinned in backend | Mint JWKS admin tokens in tests | Existing `_mint` / `_public_jwk` helpers — reuse, do not reimplement |
| Vite FE mocks (`VITE_USE_MOCKS`) | project | Sticky `window.__DIGEST_ADMIN_*__` flags | Playwright path only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Required-key / subset asserts | Full `response.json() == {…}` | Forbidden by D-08; caused the original FIX-01 flake |
| New `pytest-assert-utils` | stdlib `expected.items() <= body.items()` + explicit key asserts | No new dependency; enough for shallow DTO [ASSUMED community pattern; do not install] |
| Live Supabase empty-batch test | In-memory only | Explicitly out of scope (D-07) |
| Collapse empty shapes | Distinct `batch_id` null vs int | Forbidden by D-04 |

**Installation:** none — no new packages for Phase 12.

**Version verification:** FastAPI `0.141.1`, Pydantic `2.13.5` via `uv run python -c "import fastapi, pydantic; …"` on 2026-10-02.

## Package Legitimacy Audit

> No external packages are installed in this phase.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | N/A | No installs |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none  

Do **not** add `pytest-assert-utils` / `pytest-partial-compare` for D-08 — use explicit asserts or stdlib subset on the shallow shortlist DTO.

## Architecture Patterns

### System Architecture Diagram

```text
Playwright (admin.spec.js)
  │ sticky window.__DIGEST_ADMIN_EMPTY__
  │ sticky window.__DIGEST_ADMIN_EMPTY_UNSENT__  (NEW)
  │ sticky window.__DIGEST_ADMIN_DIGEST_REST__
  ▼
AdminDigestPage.jsx ──fetchShortlist──► adminApi.js
                                         │
                          mocks on? ─────┤
                           yes │         │ no
                               ▼         ▼
                    emptyDto / emptyUnsentDto / restDto
                                         │
                                         ▼
                              GET /admin/shortlist
                                         │
                                         ▼
                         routes/admin.py::read_admin_shortlist
                                         │
                                         ▼
                         get_admin_shortlist(shortlist_repo)
                              │
              get_current_batch() ──None──► get_latest_batch()
                              │                 │
                              │          sent? ──yes──► digest_rest=true shape
                              │                 │
                              │                no ──► no-batch null shape (D-04 #1)
                              │
                         unsent batch (items may be empty)
                              │
                              ▼
                    batch_id + week_label=isoformat + items
                    (empty items ⇒ D-04 #2 empty-unsent)
                              │
                              ▼
                    _to_response → AdminShortlistResponse (extra=forbid)
                              │
                              ▼
                         HTTP 200 JSON
```

### Recommended Project Structure
```
tests/unit/test_http_admin.py          # rename no-batch; add empty-unsent; soft asserts
backend/.../use_cases/get_admin_shortlist.py   # touch only if TDD fails
backend/.../interface/http/routes/admin.py     # keep extra=forbid; touch only if TDD fails
backend/.../domain/shortlist.py                # AdminShortlist fields already complete
backend/.../tests_support/in_memory.py         # seed empty-unsent ShortlistBatch(items=())
web/src/services/adminApi.js                   # emptyUnsentDto + sticky flag + reset
web/src/main.jsx                               # harness already exposes resetAdminHarness
web/src/pages/AdminDigestPage.jsx              # no chrome work unless failing E2E forces it
tests/admin.spec.js                            # empty-unsent path mirroring empty
.planning/phases/12-.../12-FIX-01-LOCK.md      # NEW contract tables (D-10)
.planning/REQUIREMENTS.md                      # FIX-01 proof strings (D-05)
.planning/ROADMAP.md                           # success criteria proof names (D-05)
```

### Pattern 1: Distinct empty taxonomy in the use-case
**What:** Three outcomes from `get_admin_shortlist`: no-batch empty, empty-unsent (batch present, `items` empty), digest_rest (current None + latest sent).  
**When to use:** Always for `GET /admin/shortlist`.  
**Example (current production — empty-unsent path):**
```python
# Source: backend/src/backend/application/use_cases/get_admin_shortlist.py:15-58
# Verbatim behavior verified: empty items=() still takes the non-None batch branch
# and sets week_label=batch.week_start.isoformat(), digest_rest=False.
```

### Pattern 2: Required-key HTTP asserts (D-08)
**What:** Assert status + critical keys/values; allow additional *declared* fields.  
**When to use:** Both FIX-01 proof tests after rename.  
**Example:**
```python
# Source: community subset idiom (Simon Willison TIL) — do not install packages
assert response.status_code == 200
body = response.json()
assert body["items"] == []
assert body["batch_id"] is None  # or == 7 for empty-unsent
assert body["week_label"] is None  # or == "2026-10-06"
assert body["sent_at"] is None
assert body["digest_rest"] is False
assert body["days_until_next_batch"] is None
# optional soft check that required keys exist:
for key in ("batch_id", "items", "week_label", "sent_at", "digest_rest", "days_until_next_batch"):
    assert key in body
```

### Pattern 3: Sticky mock flag + harness reset
**What:** `gotoAsRole` sets init flags, then `resetAdminHarness()`, then re-applies `extraInit`, then reloads.  
**When to use:** Every Playwright admin empty path.  
**Example:**
```javascript
// Source: tests/admin.spec.js:9-34 (gotoAsRole) + adminApi.js fetchShortlist stickyFlag checks
await gotoAsRole(page, "admin", "/admin/digest", {
  __DIGEST_ADMIN_EMPTY_UNSENT__: true,
});
```
Must also clear `__DIGEST_ADMIN_EMPTY_UNSENT__` inside `resetAdminHarness()` so cross-test leakage cannot occur.

### Anti-Patterns to Avoid
- **Full-dict equality on shortlist JSON:** Root cause of the original FIX-01 failure once declared fields grew.
- **Collapsing empty-unsent into no-batch:** Violates D-04; SPA may later branch on `batch_id`.
- **Treating digest_rest as empty:** Rest uses `digest_rest=true` and different UI (`admin-digest-rest`).
- **Production edits without a failing test:** Violates D-03 / project TDD.
- **Live Supabase FIX-01 proof:** Out of scope (D-07).
- **Human RU `week_label` on API:** Rejected for Phase 12 (D-06 / deferred).
- **New empty-state UI chrome for empty-unsent:** `AdminDigestPage` currently passes `weekDek` only when `showTriage` (`itemCount > 0`), so empty-unsent looks like no-batch in UI today — do not force “Неделя …” unless a failing test requires it (D-13).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Response schema validation | Custom dict validators in the route | Pydantic `AdminShortlistResponse` + FastAPI `response_model` | Invalid construction → 500 contract break [CITED: fastapi.tiangolo.com response_model] |
| Forbid undeclared fields | Manual key allowlists | `ConfigDict(extra="forbid")` | Raises `extra_forbidden` [CITED: pydantic docs validation_errors] |
| Empty-batch repository fake | Ad-hoc stubs per test | `InMemoryShortlistRepository` | Already mirrors `sent_at IS NULL` current-batch semantics |
| Playwright mock modes | Per-test network stubs | Sticky `__DIGEST_ADMIN_*__` + `resetAdminHarness` | Established Phase 5 harness |
| Nested JSON soft-match library | New pytest plugin | Explicit key asserts | Zero new deps; shallow DTO |

**Key insight:** The expensive part of FIX-01 was schema drift vs brittle tests — lock taxonomy + soft asserts, do not reinvent response validation.

## Runtime State Inventory

Phase includes a **proof-test rename** and harness flag addition (not a product rebrand). Checked:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — empty shapes are API/DTO only; no DB rename | none |
| Live service config | None for this contract | none |
| OS-registered state | None | none |
| Secrets/env vars | None — no env key rename | none |
| Build artifacts | None | none |
| Docs / proof strings | `REQUIREMENTS.md` FIX-01, `ROADMAP.md` Phase 12 success #1, `PROJECT.md` checklist, Phase 10 `deferred-items.md` cite old test name | **docs edit** to new names (D-05); not a data migration |
| FE harness globals | New sticky `window.__DIGEST_ADMIN_EMPTY_UNSENT__` | code edit in `adminApi.js` + clear in `resetAdminHarness` |

**Nothing found in category:** Stored data / live service / OS / secrets / build artifacts — verified by reading phase surfaces and grep for the old test name (docs-only citations).

## Common Pitfalls

### Pitfall 1: Confusing the three empty-ish shapes
**What goes wrong:** Test seeds a sent batch and expects D-80 empty, or expects empty-unsent but gets digest_rest.  
**Why it happens:** `InMemoryShortlistRepository.get_current_batch()` returns `None` when `sent_at is not None`, then use-case falls through to digest_rest.  
**How to avoid:** Empty-unsent seed = `ShortlistBatch(..., sent_at=None, items=())`. Digest_rest seed = sent batch. No-batch = `batch=None`.  
**Warning signs:** `digest_rest is True` or `batch_id is None` when expecting empty-unsent.

### Pitfall 2: Full-dict equality regresses FIX-01
**What goes wrong:** Adding a declared optional field with a default breaks every `== {…}` test.  
**Why it happens:** Historical Phase 6–10 failure mode.  
**How to avoid:** D-08 required-key asserts; keep `extra="forbid"` so *undeclared* extras still fail construction.  
**Warning signs:** Diff noise listing only newly declared keys.

### Pitfall 3: Harness flag leak / reset wipe
**What goes wrong:** Empty-unsent flag survives across tests, or `resetAdminHarness` clears it and `gotoAsRole` forgets to re-apply.  
**Why it happens:** Module-level mocks + sticky window flags.  
**How to avoid:** Clear new flag in `resetAdminHarness`; rely on `gotoAsRole` re-apply pattern already used for `__DIGEST_ADMIN_EMPTY__`.  
**Warning signs:** Flaky Playwright empty vs populated rows.

### Pitfall 4: Asserting week chrome on empty-unsent E2E
**What goes wrong:** Playwright expects `Неделя 2026-10-06` but heading dek is gated by `showTriage`.  
**Why it happens:** `weekDek={showTriage ? weekDek : null}` [VERIFIED: AdminDigestPage.jsx:450].  
**How to avoid:** Mirror existing empty UI asserts only (D-12/D-13); do not add chrome unless TDD forces it.  
**Warning signs:** E2E failure on heading dek while empty copy is visible.

### Pitfall 5: Scope creep into preview / draft→ready / PIPE
**What goes wrong:** Phase 12 touches ADUX/PIPE surfaces.  
**Why it happens:** Same `/admin/digest` page.  
**How to avoid:** Stick to shortlist empty contract + harness/Playwright empty paths.  
**Warning signs:** Edits under preview composition or material status controls.

### Pitfall 6: Assuming production needs a schema “fix”
**What goes wrong:** Rewriting use-case/HTTP without a failing test.  
**Why it happens:** Roadmap wording still sounds like a greenfield bugfix.  
**How to avoid:** Scout + this research: green named unit + empty-unsent use-case already matches D-04; add the missing HTTP edge first.  
**Warning signs:** Large production diffs in Phase 12 SUMMARY.

## Code Examples

### Empty-unsent HTTP unit seed (planner/executor template)
```python
# Pattern from existing digest_rest / populated tests in test_http_admin.py
# Seed empty unsent — do not set sent_at
container.shortlist = InMemoryShortlistRepository(
    batch=ShortlistBatch(
        id=7,
        week_start=date(2026, 10, 6),
        sent_at=None,
        items=(),
    )
)
# Then GET /admin/shortlist as admin; assert D-04 #2 required keys
```

### AdminShortlistResponse contract (keep)
```python
# Source: backend/src/backend/interface/http/routes/admin.py:48-56
class AdminShortlistResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = None
    items: list[AdminShortlistItemResponse] = []
    digest_rest: bool = False
    days_until_next_batch: int | None = None
    week_label: str | None = None
    sent_at: datetime | None = None
```

### Mock empty-unsent DTO (to add)
```javascript
// Align with D-04 #2 / D-12 — ISO week_label, not human RU
function emptyUnsentDto() {
  return {
    batch_id: 7,
    sent_at: null,
    week_label: '2026-10-06',
    items: [],
    digest_rest: false,
    days_until_next_batch: null,
  }
}
// In fetchShortlist mock branch, after DIGEST_REST, before or after EMPTY:
// if (stickyFlag('__DIGEST_ADMIN_EMPTY_UNSENT__')) return emptyUnsentDto()
```

### Flag precedence recommendation (discretion)
Order in `fetchShortlist` mock path: `DIGEST_REST` → `EMPTY_UNSENT` → `EMPTY` → sent_at rest → cloneBatch. Document mutual exclusivity in Playwright (set only one empty-ish flag per test).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Empty shortlist DTO without `week_label`/`sent_at` in tests | Declared fields on `AdminShortlist` + HTTP model (WR-04 / Phase 5) | Phase 5 WR-04 | Old full-dict test failed until expectations caught up |
| Single “empty” mental model | Distinct no-batch / empty-unsent / digest_rest | Phase 12 D-04 lock | FE/tests may branch on `batch_id` |
| Full JSON equality proofs | Required-key asserts (D-08) | Phase 12 | Survives additive *declared* fields |

**Deprecated/outdated:**
- Proof string `test_admin_shortlist_empty_batch_returns_200_empty_items` as the sole FIX-01 name — replace with the two D-05 names in REQUIREMENTS/ROADMAP.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Stdlib subset / explicit key asserts are sufficient; no pytest soft-assert plugin needed | Don't Hand-Roll / Code Examples | Planner might over-scope a dependency — low risk |
| A2 | Unrelated pre-existing unit failures may still exist outside FIX-01 files | Done bar D-02 | SUMMARY deferral list may be empty if suite is already fully green |

**If production empty-unsent HTTP path somehow 500s:** not assumed — will be proven by the new failing test under TDD (discretion item). Use-case probe this session already matches D-04 #2.

## Open Questions (RESOLVED)

1. **Should use-case layer also gain `test_get_admin_shortlist_empty_unsent_batch`?** — RESOLVED
   - What we know: D-07 locks FIX-01 HTTP surface to `test_http_admin.py`; use-case already behaves correctly.
   - What's unclear: whether planner wants a cheap domain-level twin for faster feedback.
   - Recommendation: optional, not required for FIX-01; HTTP unit is the proof.
   - **Resolution:** No use-case twin. Per D-07 and 12-01, FIX-01 proofs are HTTP in-memory units only (`test_http_admin.py`); do not add `test_get_admin_shortlist_empty_unsent_batch`.

2. **REQUIREMENTS FIX-01 wording rewrite scope** — RESOLVED
   - What we know: D-05 requires citing both new test names.
   - What's unclear: whether to keep checkbox text mentioning “schema extras” historically or rephrase to taxonomy lock.
   - Recommendation: rephrase to “no-batch + empty-unsent HTTP contracts (D-04) green under required-key asserts.”
   - **Resolution:** Per 12-02 task 2 / D-05, rephrase FIX-01 to cite both proof names as no-batch + empty-unsent HTTP contracts (D-04) green under required-key asserts (D-08).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python / uv | unit tests | ✓ | Python 3.14.0 / uv 0.10.9 | — |
| pytest via `uv run` | FIX-01 units | ✓ | project pin ≥8.3.0 | — |
| FastAPI / Pydantic | HTTP contract | ✓ | 0.141.1 / 2.13.5 | — |
| Node | Playwright | ✓ | v22.13.0 | — |
| Playwright | FE empty E2E | ✓ | ^1.62.1 | — |
| Live Supabase | — | n/a | — | Not required (D-07) |
| Tavily MCP | research web Q | ✗ (needsAuth) | — | Used built-in WebSearch |

**Missing dependencies with no fallback:** none for Phase 12 execution.

**Missing dependencies with fallback:** Tavily auth (research-only; WebSearch used).

## Validation Architecture

> `.planning/config.json` has no `workflow.nyquist_validation` key → treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Python units) + Playwright (admin E2E) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]`; Playwright via root `package.json` / playwright config |
| Quick run command | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id -x` |
| Full suite command | `uv run pytest` and `npm run test:web` (or project Playwright admin filter) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | No batches → 200, `batch_id` null, `items=[]`, null week/sent, not rest | unit HTTP | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id -x` | ❌ Wave 0 (rename from existing) |
| FIX-01 | Empty unsent → 200, `batch_id` int, ISO `week_label`, `items=[]`, not rest | unit HTTP | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id -x` | ❌ Wave 0 |
| FIX-01 | FE mock no-batch empty UI (D-80) | e2e | Playwright existing empty test | ✅ `tests/admin.spec.js` |
| FIX-01 | FE mock empty-unsent same empty UI, not digest_rest | e2e | new Playwright case with `__DIGEST_ADMIN_EMPTY_UNSENT__` | ❌ Wave 0 |
| FIX-01 | Lock doc documents both shapes | docs | file presence review | ❌ Wave 0 (`12-FIX-01-LOCK.md`) |

### Sampling Rate
- **Per task commit:** quick FIX-01 pytest pair above
- **Per wave merge:** `uv run pytest tests/unit/test_http_admin.py -q` + Playwright empty/empty-unsent cases
- **Phase gate:** FIX-01 pair green; no **new** failures introduced (D-02); lock doc present; REQUIREMENTS/ROADMAP strings updated

### Wave 0 Gaps
- [ ] Rename `test_admin_shortlist_empty_batch_returns_200_empty_items` → `test_admin_shortlist_no_batches_returns_null_batch_id` and convert to required-key asserts (D-05/D-08)
- [ ] Add `test_admin_shortlist_empty_unsent_batch_returns_batch_id` in `tests/unit/test_http_admin.py`
- [ ] Add `emptyUnsentDto` + `__DIGEST_ADMIN_EMPTY_UNSENT__` handling + reset clear in `web/src/services/adminApi.js`
- [ ] Add Playwright empty-unsent case in `tests/admin.spec.js`
- [ ] Create `12-FIX-01-LOCK.md` with both shapes + assert rules
- [ ] Update `.planning/REQUIREMENTS.md` FIX-01 and `.planning/ROADMAP.md` Phase 12 success criteria proof names

*(Existing infrastructure covers runners/fixtures — gaps are phase-specific tests/docs only.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (endpoint already admin-gated) | Existing JWT + JWKS mint in tests; no auth redesign |
| V3 Session Management | no (no session changes) | — |
| V4 Access Control | yes | `require_admin` on `GET /admin/shortlist` unchanged |
| V5 Input Validation | yes | Pydantic response/request models; `extra="forbid"` on response construction |
| V6 Cryptography | no new crypto | Existing test JWT minting only |

### Known Threat Patterns for FastAPI admin shortlist

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Response schema confusion / info leak via undeclared fields | Information Disclosure | `extra="forbid"` + explicit model fields (D-09) |
| Privilege escalation to admin shortlist | Elevation of Privilege | Keep `Depends(require_admin)` — do not weaken for empty tests |
| Test harness sticky flags leaking across E2E | Tampering (test integrity) | `resetAdminHarness` clears all empty flags |
| Accidental live DB writes in FIX-01 proof | Tampering | In-memory repository only (D-07) |

## Sources

### Primary (HIGH confidence — in-repo verified)
- `backend/src/backend/application/use_cases/get_admin_shortlist.py:15-58` — empty / digest_rest / unsent assembly [VERIFIED: Read]
- `backend/src/backend/interface/http/routes/admin.py:48-56,160-205` — `AdminShortlistResponse` + route [VERIFIED: Read]
- `backend/src/backend/domain/shortlist.py:74-81` — `AdminShortlist` fields [VERIFIED: Read]
- `backend/src/backend/tests_support/in_memory.py:178-193` — current vs latest batch [VERIFIED: Read]
- `tests/unit/test_http_admin.py:187-215` — current no-batch full equality test [VERIFIED: Read]
- `web/src/services/adminApi.js:126-146,212-276` — empty/rest DTOs + sticky flags [VERIFIED: Read]
- `web/src/pages/AdminDigestPage.jsx:441-452,518-524,566-571` — empty vs rest UI + weekDek gate [VERIFIED: Read]
- `tests/admin.spec.js:9-34,111-126,464-477` — gotoAsRole + empty + digest_rest E2E [VERIFIED: Read]
- Local pytest run 2026-10-02: 9 passed for named empty + use-case suite [VERIFIED: uv run pytest]
- Empty-unsent use-case probe [VERIFIED: uv run python]

### Secondary (MEDIUM confidence)
- Context7 `/websites/fastapi_tiangolo` — `response_model` validation → 500 on contract violation [CITED: fastapi.tiangolo.com/tutorial/response-model]
- Context7 `/pydantic/pydantic` — `extra='forbid'` → `extra_forbidden` [CITED: pydantic validation_errors / models]

### Tertiary (LOW confidence)
- WebSearch subset-assert idiom (`expected.items() <= actual.items()`) — used as discretionary helper pattern only [ASSUMED community practice]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned versions verified in this environment
- Architecture: HIGH — production path already implements D-04; gaps are coverage/docs/FE harness
- Pitfalls: HIGH — historical FIX-01 failure mode + weekDek gating verified in source

**Research date:** 2026-10-02  
**Valid until:** 2026-11-01 (stable in-repo contract; re-check if `AdminShortlistResponse` fields change)
