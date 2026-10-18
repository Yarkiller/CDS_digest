---
phase: 09-draft-persist-shortlist-enqueue
plan: 01
subsystem: ingestion
tags: [roles, pydantic, article-draft, material-draft, deepseek, templates]

requires:
  - phase: 08-deepseek-article-templates
    provides: ArticleDraft, DeepSeekArticleGenerator, lecture/podcast templates, assembler

provides:
  - RoleKind closed set (employee, analyst, ds) in data_collection.dto.role_kind
  - ArticleDraft.roles and MaterialDraft.roles with unknown-filter + empty fallback
  - Audience-role instruction in lecture.md and podcast.md
  - DeepSeek adapter role normalization after model_validate
  - Assembler copy of article.roles into MaterialDraft

affects:
  - 09-02 (persist port receives MaterialDraft.roles)
  - 09-03 (RPC payload roles)
  - 09-04 (composition / CAP-02 spy)

actuals:
  tokens: 2800
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - Shared normalize_roles helper used by DTO before-validators and the DeepSeek adapter
    - Closed RoleKind Literal; admin excluded from ingestion drafts

key-files:
  created:
    - data-collection/src/data_collection/dto/role_kind.py
    - tests/unit/test_article_draft_roles.py
    - tests/unit/test_material_draft_roles.py
  modified:
    - data-collection/src/data_collection/dto/article_draft.py
    - data-collection/src/data_collection/dto/material_draft.py
    - data-collection/src/data_collection/assemble.py
    - data-collection/src/data_collection/templates/lecture.md
    - data-collection/src/data_collection/templates/podcast.md
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - tests/unit/test_assemble_material_draft.py
    - tests/unit/test_deepseek_article_adapter.py
    - tests/unit/test_fake_article_generator.py
    - tests/unit/test_article_draft_internal.py
    - tests/unit/test_data_collection_public_api.py

key-decisions:
  - Promoted RoleKind to a first-class list on both drafts; empty/missing/unknown falls back to ["employee"].
  - Shared normalize_roles in role_kind.py rather than duplicating filter logic in the adapter.
  - Did not export RoleKind, ArticleDraft, or normalize_roles from data_collection.__all__.

patterns-established:
  - "Role lists are filtered against VALID_ROLES before Pydantic Literal validation (mode=before)."
  - "Assembler copies article.roles with no extra role logic."

requirements-completed:
  - PERS-01
  - PERS-02

coverage:
  - id: D1
    description: "ArticleDraft.roles keeps valid values, filters unknown, and falls back to employee when missing or empty."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_article_draft_roles.py#test_article_draft_keeps_valid_roles"
        status: pass
      - kind: unit
        ref: "tests/unit/test_article_draft_roles.py#test_article_draft_filters_unknown_roles"
        status: pass
      - kind: unit
        ref: "tests/unit/test_article_draft_roles.py#test_article_draft_empty_roles_falls_back_to_employee"
        status: pass
    human_judgment: false
  - id: D2
    description: "MaterialDraft.roles uses the same normalization rules."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_material_draft_roles.py#test_material_draft_keeps_valid_roles"
        status: pass
      - kind: unit
        ref: "tests/unit/test_material_draft_roles.py#test_material_draft_constructor_normalization"
        status: pass
    human_judgment: false
  - id: D3
    description: "lecture.md and podcast.md ask the LLM for a JSON array of employee, analyst, ds."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_article_draft_roles.py#test_lecture_and_podcast_templates_ask_for_role_json_array"
        status: pass
    human_judgment: false
  - id: D4
    description: "DeepSeek adapter stub JSON with roles round-trips; empty roles become [employee]."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_keeps_valid_roles_from_json_payload"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_empty_roles_falls_back_to_employee"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_single_ds_role_round_trips"
        status: pass
    human_judgment: false
  - id: D5
    description: "assemble_material_draft copies article.roles onto MaterialDraft."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_assemble_material_draft.py#test_assemble_material_draft_copies_article_roles"
        status: pass
    human_judgment: false
  - id: D6
    description: "RoleKind, ArticleDraft, and normalize_roles stay off the public package root."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_negative_names_not_importable_from_package_root"
        status: pass
    human_judgment: false
  - id: D7
    description: "FakeArticleGenerator returns a scripted ArticleDraft including roles and records the call."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_fake_article_generator.py#test_fake_article_generator_returns_scripted_roles_unchanged"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-09-27
status: complete
---

# Phase 9 Plan 01: RoleKind on drafts Summary

**RoleKind is a first-class non-empty list on ArticleDraft and MaterialDraft; templates ask the LLM; DeepSeek normalizes unknown/empty to employee**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-27T15:11:08Z
- **Completed:** 2026-09-27T15:16:30Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Promoted `RoleKind = Literal["employee", "analyst", "ds"]` with shared `normalize_roles`
- Both drafts carry `roles`; missing, empty, or unknown values become `["employee"]`
- Stubbed LLM JSON with roles round-trips through validation, the adapter, the assembler, and the fake
- Public `data_collection.__all__` remains the seven existing names

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: failing role-contract tests** - `a135e7a` (test)
2. **Task 1 GREEN: RoleKind + DTO/template/adapter normalization** - `1b608b4` (feat)
3. **Task 2: keep RoleKind and ArticleDraft off the public root** - `4b0d99f` (test)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `data-collection/src/data_collection/dto/role_kind.py` - RoleKind, VALID_ROLES, normalize_roles
- `data-collection/src/data_collection/dto/article_draft.py` - roles field + before-validator
- `data-collection/src/data_collection/dto/material_draft.py` - roles field + before-validator
- `data-collection/src/data_collection/assemble.py` - copies article.roles
- `data-collection/src/data_collection/templates/lecture.md` - ## Аудитория JSON array instruction
- `data-collection/src/data_collection/templates/podcast.md` - ## Аудитория JSON array instruction
- `data-collection/src/data_collection/adapters/deepseek_article.py` - post-validate role normalization
- `tests/unit/test_article_draft_roles.py` - DTO + template contract
- `tests/unit/test_material_draft_roles.py` - DTO contract
- `tests/unit/test_assemble_material_draft.py` - assembler copy
- `tests/unit/test_deepseek_article_adapter.py` - stub JSON role cases
- `tests/unit/test_fake_article_generator.py` - scripted roles
- `tests/unit/test_article_draft_internal.py` - model_fields includes roles
- `tests/unit/test_data_collection_public_api.py` - RoleKind/normalize_roles negatives

## Decisions Made
- Shared `normalize_roles` on the DTO and adapter so a stubbed JSON payload and a constructor path share one fallback.
- `admin` stays out of RoleKind for ingestion drafts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated Phase 8 field-set assertion for roles**
- **Found during:** Task 1 GREEN
- **Issue:** `test_article_draft_internal.py` asserted `model_fields == {title, dek, body_markdown}`; adding `roles` would fail the full suite. The file was omitted from `files_modified`.
- **Fix:** Include `roles` in the expected field set and assert the default `["employee"]`.
- **Files modified:** `tests/unit/test_article_draft_internal.py`
- **Verification:** `uv run pytest tests/unit/test_article_draft_internal.py` exits 0
- **Committed in:** `a135e7a` (Task 1 RED)

---

**Total deviations:** 1 auto-fixed (1 blocking). `fakes.py` needed no edit because FakeArticleGenerator already returns the scripted draft unchanged.
**Impact on plan:** Required for Phase 8 suite green. No scope creep.

## Issues Encountered
- Full `uv run pytest` is 518 passed / 1 failed: pre-existing `test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (noted in Phase 8 STATE). Unrelated to roles; not fixed.
- Task 2 test additions were immediately green because the names were never exported (desired state).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 09-02 (PersistPort + slug/reading_minutes + mapper + fake). Role lists on both drafts are locked.

## Self-Check: PASSED
- key-files.created exist on disk
- `git log --oneline --all --grep="09-01"` returns 3 commits
- Task acceptance criteria and plan focused suite: 77 passed
- Tracer verify re-run: 50 passed

---
*Phase: 09-draft-persist-shortlist-enqueue*
*Completed: 2026-09-27*
