---
phase: 02-issue-materials-archive
verified: 2026-09-20T11:25:00Z
status: passed
score: 4/5 must-haves verified
behavior_unverified: 1
overrides_applied: 0
re_verification: false
decision_coverage:
  honored: 20
  total: 20
  not_honored: []
behavior_unverified_items:

  - truth: "UI-SPEC backstops held for verify: IssueTOC overflow/plural/long-title; archive overflow; material overflow/long-title; callout long-text; hero overflow; nav mobile reflow"
    test: "At 320/390/1280 viewports, open current issue (long title), archive grid, material with deep headings, open callout with long date text, and AppShell nav"
    expected: "No horizontal overflow of primary chrome; Russian plural captions correct for 1/2/5+; 44px hit targets; sticky TOC usable; nav does not overlap wordmark"
    why_human: "Intentionally describe.skip in tests/web-app.spec.js — visual judgment, not greppable"
human_verification:

  - test: "UI-SPEC visual backstops (held-out)"
    expected: "IssueTOC/archive/material/callout/hero/nav pass overflow, plural, and mobile reflow checks in 02-UI-SPEC"
    why_human: "describe.skip placeholder — verify-work visual gate"

  - test: "Live FE↔BE smoke (VITE_USE_MOCKS=false)"
    expected: "Authenticated `/` shows issue №14 typography hero + TOC; `/materials/rag-systems` shows Статья + prose + TOC; `/archive` lists №13 → `/issues/13` without callout"
    why_human: "Playwright phase gate runs under mocks; shared-VM JWT session and live adapters need a human pass"

  - test: "Advisory: live tags + open-cycle clock (02-REVIEW WR-01, WR-03)"
    expected: "Tag chips show display labels (not slugs); callout open/closed matches editorial intent after closes_at"
    why_human: "Code-review warnings — live tag tuple order and status-only cycle selection; do not block must-haves alone"
---

# Phase 2: Issue, Materials & Archive Verification Report

**Phase Goal:** Readers open the current editorial issue, read prepared articles (never media-as-material), and revisit past issues  
**Verified:** 2026-09-20T11:25:00Z  
**Status:** human_needed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | User opens current published issue with typography-only hero (number/period/title, no cover image) and IssueTOC, or sees honest empty «выпуск готовится» | ✓ VERIFIED | `IssuePage.jsx` typography hero (no `img`/`cover`); `IssueToc` when items present; empty → «Выпуск готовится» + `/archive` CTA. Playwright: empty harness + TOC→material. Unit: `test_http_issues` / `test_get_current_issue` |
| 2 | Voting-cycle EditorialCallout reflects open vs closed state correctly | ✓ VERIFIED | `voting_cycle` on current DTO; open → «Голосование открыто до …» + CTA `/voting`; closed → closed copy, no topic CTA; absent → hidden. Playwright open/closed/absent. Past `/issues/:number` omits callout (`isCurrent={false}`) |
| 3 | User reads a material as prose + section TOC with «Статья» badge/provenance/tags/related links as available; unknown id shows editorial 404 | ✓ VERIFIED | `MaterialPage` + `react-markdown`/`rehype-slug`/`rehype-sanitize`; badge always; provenance/tags/related conditional. Soft 404 «Материал не найден» without `bad_gateway`. Playwright slug + TOC + soft 404. Unit: `test_get_material_for_reader` / `test_http_materials` |
| 4 | Audit-dek appears under title when present; archive opens a past issue or empty-archive CTA to current | ✓ VERIFIED | Dek block only when trimmed non-empty (`material-dek`); empty dek test asserts omission. Archive cards → `/issues/:number`; empty «Архив пуст» + CTA `/`. Playwright archive nav/empty/soft issue 404. Live DB: issues 13+14 present |
| 5 | UI-SPEC backstops (overflow/plural/long-title/mobile reflow) held for verify | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Code present; `test.describe.skip("phase 2 UI-SPEC visual backstops")` — intentional human gate |

**Score:** 4/5 truths verified (1 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `backend/.../ports/issue_repository.py` | IssueRepository Protocol | ✓ VERIFIED | Exists, substantive |
| `backend/.../use_cases/get_current_issue.py` | D-24 + voting select | ✓ VERIFIED | Wired to HTTP |
| `backend/.../use_cases/list_archive_issues.py` | Past issues excl. current | ✓ VERIFIED | Delegates `list_past_published` |
| `backend/.../use_cases/get_issue_by_number.py` | Past issue by number | ✓ VERIFIED | Wired; 404 → `issue_not_found` |
| `backend/.../use_cases/get_material_for_reader.py` | Ready-only by slug | ✓ VERIFIED | Draft/missing → `MaterialNotFoundError` |
| `backend/.../routes/issues.py` | GET current/archive/by-number | ✓ VERIFIED | JWT via `get_principal` |
| `backend/.../routes/materials.py` | GET `/materials/{slug}` | ✓ VERIFIED | JWT; tags/related mapped |
| `backend/.../ports/voting_cycle_reader.py` | Read-only cycle port | ✓ VERIFIED | Used by `get_current_issue` |
| `backend/composition/live.py` | Supabase adapters | ✓ VERIFIED | `SupabaseIssueRepository` + `SupabaseMaterialRepository` + voting reader; not InMemory |
| `supabase-integration/migrations/002_phase2_issue_seed.sql` | Idempotent seed | ✓ VERIFIED | ON CONFLICT; rag-systems; no TRUNCATE; live rows confirmed via MCP |
| `supabase-integration/.../issue_repository.py` | Live issue adapter | ✓ VERIFIED | Wired in live container |
| `supabase-integration/.../material_repository.py` | Live material + `get_by_slug` | ✓ VERIFIED | Wired; **WR-01** tag tuple order advisory |
| `web/src/services/contentApi.js` | Mock/live cutover | ✓ VERIFIED | `isMocksEnabled`; 404→NOT_FOUND; no silent mock fallback |
| `web/src/pages/IssuePage.jsx` | Current + past issue UI | ✓ VERIFIED | Wired to contentApi |
| `web/src/pages/ArchivePage.jsx` | Archive list/empty | ✓ VERIFIED | Wired |
| `web/src/pages/MaterialPage.jsx` | Reader + TOC | ✓ VERIFIED | Wired |
| `web/src/utils/markdownToc.js` | Heading TOC | ✓ VERIFIED | Used by MaterialPage |
| `web/src/components/EditorialCallout.jsx` | Voting callout | ✓ VERIFIED | Optional CTA |
| `web/src/components/ServiceUnavailable.jsx` | Load-failure splash | ✓ VERIFIED | `bad_gateway.png` + «Ошибочка вышла» + «Повторить» |
| `web/public/bad_gateway.png` | Splash asset | ✓ VERIFIED | Exists |
| `web/src/App.jsx` | Routes | ✓ VERIFIED | `/`, `/archive`, `/issues/:number`, `/materials/:id` |
| `docs/agents/local-platform-runbook.md` | Seed apply docs | ✓ VERIFIED | §4b Phase 2 seed |
| `tests/web-app.spec.js` | Phase e2e gate | ✓ VERIFIED | Functional coverage green under mocks; visual backstops skipped |

gsd-tools `verify.artifacts`: all declared PLAN artifact paths passed (existence).

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `IssuePage` | `contentApi.fetchCurrentIssue` / `fetchIssueByNumber` | useEffect | ✓ WIRED | Manual (gsd-tools needs file-path `from:`) |
| `GET /issues/current` | `get_current_issue` | `Depends(get_principal)` | ✓ WIRED | `issues.py` |
| `GET /archive` | `list_archive_issues` | archive_router | ✓ WIRED | Excludes current (D-31) |
| `ArchivePage` | `/issues/:number` | card Link | ✓ WIRED | `isCurrent={false}` on IssuePage |
| `AppShell` «Архив» | `/archive` | NavLink between Выпуск/База | ✓ WIRED | Playwright nav order |
| `MaterialPage` | `fetchMaterial(slug)` | useParams `.id` | ✓ WIRED | |
| `get_material_for_reader` | HTTP 404 | `MaterialNotFoundError` | ✓ WIRED | |
| `react-markdown` | rehype-slug + sanitize | rehypePlugins | ✓ WIRED | No `rehype-raw` / `dangerouslySetInnerHTML` |
| `get_current_issue` | EditorialCallout | `voting_cycle` DTO | ✓ WIRED | Only when `isCurrent` |
| `EditorialCallout` open CTA | `/voting` | `actionTo` | ✓ WIRED | Closed omits action |
| `create_service_role_client` | Supabase repos | `build_live_container` | ✓ WIRED | `live.py` |
| `armFailNextContentFetch` | ServiceUnavailable | retryable ContentApiError | ✓ WIRED | Playwright splash + Retry |
| `isMocksEnabled` | contentApi mock branch | `authEnv` / `VITE_USE_MOCKS` | ✓ WIRED | Live errors do not fall through to mock.js |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| IssuePage | `issue` | `GET /issues/current` → use-case → IssueRepository (Supabase or in-memory/mock) | Yes (mock fixtures; live seed 13/14 confirmed) | ✓ FLOWING |
| IssuePage | `voting_cycle` | VotingCycleReader → select_active_voting_cycle | Yes | ✓ FLOWING |
| ArchivePage | `issues` | `GET /archive` → list_past_published | Yes | ✓ FLOWING |
| MaterialPage | `material` | `GET /materials/{slug}` → get_by_slug ready-only | Yes (`rag-systems` ready on VM) | ✓ FLOWING |
| MaterialPage tags | `tags` | material.tags → HTTP labels | Live adapter may emit slug-first (**WR-01**) | ⚠️ PARTIAL (live labels) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Unit issue/material/archive HTTP | `uv run pytest tests/unit/test_get_current_issue.py test_get_material_for_reader.py test_list_archive_issues.py test_get_issue_by_number.py test_http_issues.py test_http_materials.py -q` | 29 passed | ✓ PASS |
| Live wiring types | `uv run pytest tests/unit/test_live_container_wiring.py -q` | 6 passed | ✓ PASS |
| Playwright empty issue / archive / splash / dek-empty | `npx playwright test … -g "Выпуск готовится\|Архив пуст\|ошибочка\|dek"` | 4 passed | ✓ PASS |
| Playwright callout open/closed + archive past | `… -g "open voting\|closed voting\|Архив"` | 4 passed | ✓ PASS |
| Playwright material + soft 404s | `… -g "opens material\|not-found\|Выпуск не найден"` | 4 passed | ✓ PASS |
| Live seed presence | Supabase MCP `digest_issues` / `materials` / `voting_cycles` | issues 13+14; rag-systems ready; 1 open cycle | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ISSUE-01 | 02-01, 02-02 | Current issue + TOC or empty preparing | ✓ SATISFIED | Typography hero (cover deferred D-26 / ROADMAP SC1 — REQUIREMENTS still says «cover»; treat ROADMAP+CONTEXT as contract) |
| ISSUE-02 | 02-05 | Open/closed EditorialCallout | ✓ SATISFIED | Playwright + DTO wiring |
| ISSUE-03 | 02-04 | Audit-dek when present; omit when empty | ✓ SATISFIED | Conditional render + empty-dek Playwright |
| ISSUE-04 | 02-03 | Past issue from archive; empty CTA | ✓ SATISFIED | ArchivePage + routes + Playwright |
| MAT-01 | 02-02, 02-04 | Prepared article prose + section TOC; no media-as-material | ✓ SATISFIED | body_markdown markdown path; no video/audio player as content |
| MAT-02 | 02-04 | Статья type; unknown → material not found | ✓ SATISFIED | Badge + soft 404 |
| MAT-03 | 02-04 | Badge, provenance, tags, related without fabricating | ✓ SATISFIED | Conditional sections; related only ready targets. Live tag *labels* advisory WR-01 |

**Orphaned requirements:** none — all Phase 2 IDs claimed in PLAN frontmatter.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts (20/20). Non-blocking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| ----------- | ----------- | ------ | ------- | -------- | --------------- | ------- |
| `tests/web-app.spec.js` (main/edge) | ISSUE-*/MAT-* | Yes | — | No | Behavioral | PASS |
| `tests/web-app.spec.js` UI-SPEC backstops | 02-06 visual | No | `describe.skip` | No | N/A | WARNING — held for human, not silent-pass |
| `tests/unit/test_http_*.py` / use-cases | ISSUE/MAT | Yes | None found | No | Value/status | PASS |

**Disabled tests on requirements:** 0 blockers (skip is visual held-out, not sole proof of ISSUE/MAT)  
**Circular patterns:** 0  
**Insufficient assertions:** 0 blockers (positive dek-present assertion thin — covered by render code + empty branch)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `supabase_integration/material_repository.py` | ~38 | tags `(slug, label)` vs HTTP `(label, slug)` | ⚠️ Warning | Live tag chips may show slugs (02-REVIEW WR-01) |
| `get_current_issue.py` | ~19–27 | Open cycle ignores calendar window | ⚠️ Warning | Seed `closes_at` 2026-04-16 still `status=open` → live open CTA (WR-03) |
| `IssuePage.jsx` | ~134–151 | Empty TOC ≡ «Выпуск готовится» | ⚠️ Warning | Published issue with 0 items conflated with no issue (WR-04) |
| `IssuePage`/`MaterialPage`/`ArchivePage` | error catch | UNAUTHORIZED → ServiceUnavailable | ⚠️ Warning | Session expiry shows Retry splash (WR-05) |
| `contentApi.js` | `fetchIssueByNumber` | `Number(number)` → NaN URL | ⚠️ Warning | Non-numeric param → NETWORK splash (WR-06) |
| — | — | TBD/FIXME/XXX in phase files | — | None found |

Advisory only — do not fail must-haves solely on these (per orchestrator instruction).

### Human Verification Required

### 1. UI-SPEC visual backstops (held-out)

**Test:** Walk 02-UI-SPEC UI Considerations at 320 / 390 / 1280: IssueTOC long titles + plural, archive grid targets, material sticky TOC, callout wrap, hero title, AppShell nav.  
**Expected:** No broken overflow; 44px targets; nav clear of wordmark.  
**Why human:** `describe.skip` visual gate.

### 2. Live FE↔BE smoke

**Test:** With mocks off and corporate session, open `/`, `/materials/rag-systems`, `/archive` → №13.  
**Expected:** Same editorial behaviors as mocks against shared VM seed (confirmed: issues 13/14, rag-systems ready).  
**Why human:** E2E suite is mock-gated.

### 3. Advisory live quirks (WR-01 / WR-03)

**Test:** Inspect tag chips on live rag-systems; note callout still «открыто» despite past `closes_at`.  
**Expected:** Decide whether to fix before Phase 3 or accept.  
**Why human:** Product judgment on review warnings.

### Gaps Summary

No must-have **FAILED**. Phase goal is implemented and behaviorally proven under mocks for all four ROADMAP success criteria; ISSUE-01…04 and MAT-01…03 are satisfied in code. Overall status is **human_needed** because (1) UI-SPEC visual backstops remain held-out, and (2) live FE↔BE + advisory review items need a human pass before treating the phase as UAT-complete.

---

_Verified: 2026-09-20T11:25:00Z_  
_Verifier: Claude (gsd-verifier)_
