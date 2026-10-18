---
phase: 02-issue-materials-archive
plan: 04
subsystem: api
tags: [fastapi, jwt, react, react-markdown, rehype-sanitize, ports-adapters, material-reader, playwright, pytest]

requires:
  - phase: 02-issue-materials-archive
    provides: MaterialRepository get_by_slug, seed rag-systems, IssuePage/contentApi patterns, archive soft-404
provides:
  - get_material_for_reader ready-only by slug (draft → MaterialNotFoundError)
  - GET /materials/{slug} JWT-gated; 404 material_not_found
  - markdownToc extractMarkdownHeadings + pinned react-markdown stack
  - MaterialPage prose + TOC + honesty meta + soft editorial 404
affects:
  - 02-05 voting cycle stub (material links unchanged)
  - 02-06 load-failure splash (retryable NETWORK path on material fetch)

actuals:
  tokens: 26972
  tasks: 3
  commits: 7

tech-stack:
  added:
    - react-markdown@10.1.0
    - remark-gfm@4.0.1
    - rehype-slug@6.0.0
    - rehype-sanitize@6.0.0
  patterns:
    - Ready-only reader use-case treats draft as not-found (IDOR → 404)
    - Related DTO resolved at HTTP edge for ready targets only
    - Soft ContentApiError NOT_FOUND for material 404 (no splash)

key-files:
  created:
    - backend/src/backend/application/use_cases/get_material_for_reader.py
    - backend/src/backend/interface/http/routes/materials.py
    - web/src/utils/markdownToc.js
    - tests/unit/test_markdown_toc.js
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/interface/http/app.py
    - tests/unit/test_get_material_for_reader.py
    - tests/unit/test_http_materials.py
    - web/package.json
    - web/package-lock.json
    - web/src/pages/MaterialPage.jsx
    - web/src/services/contentApi.js
    - web/src/data/mock.js
    - tests/web-app.spec.js

key-decisions:
  - "MaterialNotFoundError accepts int|str so slug misses share the same domain error"
  - "Editor byline constant «Редакция Digest CDS» in DTO — no schema migration"
  - "Mobile TOC uses details without duplicate nav landmark; desktop sticky nav aria-label Содержание"
  - "Mock empty-dek-article fixture for D-36 Playwright (inIssue=false)"

patterns-established:
  - "GET /materials/{slug} Path pattern alphanumeric/hyphen; draft never 403"
  - "MaterialPage: rehypeSlug + rehypeSanitize only — no rehype-raw / dangerouslySetInnerHTML"

requirements-completed: [MAT-01, MAT-02, MAT-03, ISSUE-03]

coverage:
  - id: D1
    description: "Ready-only material by slug; draft/missing → MaterialNotFoundError / HTTP 404 material_not_found"
    requirement: MAT-02
    verification:
      - kind: unit
        ref: tests/unit/test_get_material_for_reader.py#test_get_material_for_reader_draft_raises_not_found
        status: pass
      - kind: unit
        ref: tests/unit/test_http_materials.py#test_materials_draft_slug_returns_404_not_403
        status: pass
    human_judgment: false
  - id: D2
    description: "JWT-required GET /materials/{slug} returns body_markdown + related ready-only DTO"
    requirement: MAT-01
    verification:
      - kind: unit
        ref: tests/unit/test_http_materials.py#test_materials_ready_rag_systems_returns_200_with_body_markdown
        status: pass
      - kind: unit
        ref: tests/unit/test_http_materials.py#test_materials_by_slug_without_authorization_returns_401
        status: pass
    human_judgment: false
  - id: D3
    description: "Markdown TOC util extracts rehype-slug-compatible ASCII heading ids"
    requirement: MAT-01
    verification:
      - kind: unit
        ref: tests/unit/test_markdown_toc.js
        status: pass
    human_judgment: false
  - id: D4
    description: "/materials/rag-systems shows Статья badge, prose, TOC; soft 404 without bad_gateway; empty dek hidden"
    requirement: MAT-03
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#opens a material from the issue table of contents
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#hides material dek block when empty
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#shows not-found recovery for an unknown material id
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 04: Material Reader Summary

**Ready-only GET /materials/{slug} plus sanitized markdown MaterialPage with TOC and honesty rules (MAT-01/02/03, ISSUE-03).**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-20T10:43:19Z
- **Completed:** 2026-09-20T11:00:00Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- Ready-only reader use-case + JWT `GET /materials/{slug}` with draft→404 (not 403) and related DTO honesty
- Pinned markdown toolchain + pure `extractMarkdownHeadings` for section TOC
- MaterialPage loads via `contentApi.fetchMaterial`; soft editorial 404; hide empty dek/tags/related; always show «Статья»

## Task Commits

Each task was committed atomically:

1. **Task 1: get_material_for_reader + GET /materials/{slug}**
   - `2026935` test(02-04): add failing tests for material reader API
   - `bc8d746` feat(02-04): implement ready-only GET /materials/{slug}
2. **Task 2: Install markdown stack + markdownToc utility**
   - `8fe3871` test(02-04): add failing test for markdown TOC extraction
   - `e8e9182` feat(02-04): add markdown TOC util and pinned markdown stack
3. **Task 3: MaterialPage markdown prose, honesty meta, soft 404**
   - `530b636` test(02-04): add failing Playwright for material reader UX
   - `3746e05` feat(02-04): render MaterialPage markdown prose with honesty rules
   - `dae4185` fix(02-04): give empty-dek fixture a non-empty cover src

**Plan metadata:** `724aacb` (docs: complete material reader plan)

## Files Created/Modified

- `backend/.../get_material_for_reader.py` — ready-only by slug
- `backend/.../routes/materials.py` — GET /materials/{slug} response DTO
- `web/src/utils/markdownToc.js` — heading → TOC ids
- `web/src/pages/MaterialPage.jsx` — prose + TOC + soft 404
- `web/src/services/contentApi.js` — `fetchMaterial`
- `tests/unit/test_*.py` / `test_markdown_toc.js` / `tests/web-app.spec.js` — TDD coverage

## Decisions Made

- Constant editor byline in DTO (RESEARCH A1) — no materials.editor column
- Related links resolved in route layer from `related_material_ids` via `repo.get` ready filter
- Mobile TOC in `<details>`; single desktop `nav[aria-label=Содержание]` to avoid duplicate landmarks

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Empty cover src on empty-dek fixture**
- **Found during:** Task 3 (Playwright knowledge filter arm matched by grep)
- **Issue:** `cover: ''` caused React empty `src` warning in MaterialListRow
- **Fix:** Use a real cover path on the fixture
- **Files modified:** `web/src/data/mock.js`
- **Commit:** `dae4185`

## Threat Flags

None — surfaces match plan threat model (T-02-01 draft→404, T-02-06 rehype-sanitize, no rehype-raw).

## Known Stubs

None — reader path wired end-to-end under mocks; live path uses same API DTO.

## Auth Gates

None.

## Self-Check: PASSED
