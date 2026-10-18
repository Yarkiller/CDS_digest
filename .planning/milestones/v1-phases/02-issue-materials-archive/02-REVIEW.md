---
phase: 02-issue-materials-archive
reviewed: 2026-09-20T11:15:00Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - backend/src/backend/domain/issue.py
  - backend/src/backend/domain/voting_cycle.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/application/ports/issue_repository.py
  - backend/src/backend/application/ports/material_repository.py
  - backend/src/backend/application/ports/voting_cycle_reader.py
  - backend/src/backend/application/use_cases/get_current_issue.py
  - backend/src/backend/application/use_cases/get_material_for_reader.py
  - backend/src/backend/application/use_cases/list_archive_issues.py
  - backend/src/backend/application/use_cases/get_issue_by_number.py
  - backend/src/backend/interface/http/routes/issues.py
  - backend/src/backend/interface/http/routes/materials.py
  - backend/src/backend/interface/http/app.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/tests_support/in_memory.py
  - supabase-integration/migrations/002_phase2_issue_seed.sql
  - supabase-integration/src/supabase_integration/issue_repository.py
  - supabase-integration/src/supabase_integration/material_repository.py
  - supabase-integration/src/supabase_integration/voting_cycle_repository.py
  - supabase-integration/src/supabase_integration/__init__.py
  - web/src/services/contentApi.js
  - web/src/pages/IssuePage.jsx
  - web/src/pages/MaterialPage.jsx
  - web/src/pages/ArchivePage.jsx
  - web/src/main.jsx
  - web/src/utils/markdownToc.js
  - web/src/components/ServiceUnavailable.jsx
  - web/src/components/EditorialCallout.jsx
  - web/src/data/mock.js
  - web/src/App.jsx
  - web/src/components/AppShell.jsx
findings:
  critical: 0
  warning: 6
  info: 3
  total: 9
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-20T11:15:00Z
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

Phase 02 content path (ports → use-cases → FastAPI → Supabase adapters → `contentApi` → pages) is structurally sound: JWT gates, draft→404 (not 403), no silent mock fallback, markdown sanitized without `rehype-raw` / `dangerouslySetInnerHTML`, and `service_role` confined to `composition/live.py`. No secrets in `web/`.

Issues center on live-path correctness: tag tuple order mismatch between Supabase adapter and HTTP DTO, TOC that can surface draft materials, voting selection that ignores `closes_at`, and a few SPA edge-case UX/error-mapping gaps.

## Warnings

### WR-01: Supabase material tags stored as `(slug, label)` but HTTP expects `(label, slug)`

**File:** `supabase-integration/src/supabase_integration/material_repository.py:38`
**Issue:** Adapter builds `tags` as `(tag_slug, tag_label)`. Route maps labels with `label for label, _slug in material.tags` (`materials.py:78`), and unit fixtures use `(("RAG", "rag"), ...)`. Live GETs therefore return slugs (`rag`, `llm`) instead of display labels (`RAG`, `LLM`). Contract test soft-asserts either order, so this ships green.
**Fix:**
```python
tags.append((str(tag["tag_label"]), str(tag["tag_slug"])))
```
Tighten `test_get_by_slug_returns_ready_material_with_tags` to require `("RAG", "rag")` only.

### WR-02: Issue TOC join does not filter ready materials

**File:** `supabase-integration/src/supabase_integration/issue_repository.py:35-46`
**Issue:** `_item_from_join` accepts any joined `materials` row. A draft (or deleted-but-orphaned) item linked on a published issue appears in TOC; reader then hits `material_not_found` (404). Reader use-case correctly hides drafts by slug, but the issue list can advertise them.
**Fix:** Filter in SQL/select or in `_item_from_join`:
```python
if str(material.get("status") or "") != "ready":
    return None
```
Include `status` in the nested `materials(...)` select.

### WR-03: Active voting cycle ignores calendar window

**File:** `backend/src/backend/application/use_cases/get_current_issue.py:19-27`
**Issue:** `select_active_voting_cycle` prefers `status == "open"` by `closes_at` only — it never compares `closes_at` / `opens_at` to “now”. Seed migration inserts an `open` cycle closing `2026-04-16` (`002_phase2_issue_seed.sql:168-172`). After that date the API can still emit an “open” callout CTA to `/voting`.
**Fix:** Treat as open only when `opens_at <= now < closes_at` (and optionally auto-fall through to latest closed). Align seed status with narrative clock or make selection time-aware.

### WR-04: Empty `items` collapses any issue into “Выпуск готовится”

**File:** `web/src/pages/IssuePage.jsx:134-151`
**Issue:** UI uses `items.length === 0` as the sole empty signal. A published issue DTO with `number`/`title` set but zero TOC items (or past `/issues/:n` with empty items) shows the “preparing” copy instead of title/metadata or a distinct empty-TOC state. Honest-empty for *no* published issue (`number: null`) is correct; the conflation is not.
**Fix:** Branch on `issue.number == null` (or missing title) for D-30 empty; if `number` is set and `items` empty, render issue chrome + “в выпуске пока нет материалов”.

### WR-05: `UNAUTHORIZED` content errors surface as ServiceUnavailable Retry

**File:** `web/src/pages/IssuePage.jsx:81-88` (same pattern in `MaterialPage.jsx:80-87`, `ArchivePage.jsx:35-38`)
**Issue:** `ContentApiError` with `code === 'UNAUTHORIZED'` / `retryable: false` is treated like network failure → splash + Retry. Retry cannot fix an expired session; users should re-auth.
**Fix:** On `UNAUTHORIZED`, clear session / navigate to `/login` (or dedicated session-expired UI). Reserve `ServiceUnavailable` for `retryable === true`.

### WR-06: Non-numeric `/issues/:number` becomes `NaN` request

**File:** `web/src/services/contentApi.js:247-263`
**Issue:** `const n = Number(number)` with no `Number.isFinite` guard. Invalid route params yield `fetch(.../issues/NaN)` → non-404 failure → NETWORK splash instead of soft NOT_FOUND.
**Fix:**
```javascript
const n = Number(number)
if (!Number.isFinite(n) || !Number.isInteger(n) || n < 1) {
  throw new ContentApiError('Выпуск не найден.', { code: 'NOT_FOUND', retryable: false })
}
```

## Info

### IN-01: Playwright content harness exposed on `window` in all builds

**File:** `web/src/main.jsx:25-30`
**Issue:** `__DIGEST_CONTENT_HARNESS__` (and fail/empty flags) ship in production bundles. Not a secret leak; with XSS an attacker already owns the page. Prefer gating behind `import.meta.env.DEV` or `VITE_USE_MOCKS`.

### IN-02: Discarded publishable Supabase client in live composition

**File:** `backend/src/backend/composition/live.py:33-37`
**Issue:** `create_publishable_client(...)` return value is unused. Harmless but confusing; remove or assign when user-scoped reads exist.

### IN-03: TOC slugify is ASCII-`\w` only — Cyrillic headings break anchors

**File:** `web/src/utils/markdownToc.js:10-17`
**Issue:** Custom `slugify` strips non-ASCII; `rehype-slug` keeps Unicode ids. Seed English headings match; Russian ATX headings would desync TOC `#href` from rendered ids.
**Fix:** Share github-slugger (or rehype-slug’s algorithm) between TOC extractor and markdown pipeline.

---

_Reviewed: 2026-09-20T11:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
