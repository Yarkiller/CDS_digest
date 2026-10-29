---
phase: 30-classifier-practical-conceptual
plan: 03
subsystem: ingestion-classifier
tags: [topic-kind, kind-03, guide-strip, body-sanitizer, tdd]

requires:
  - phase: 30-classifier-practical-conceptual
    provides: TopicKindClassifier port, topic_kind on ArticleDraft, DeepSeekTopicKindClassifier wiring
provides:
  - strip_guide_section sibling of strip_audience_section
  - ArticleDraft body_markdown validator that drops ATX Гайд and ссылки скоро появятся on every pass-1 body
  - characterization pin that lecture/podcast assembled user messages omit Гайд
affects: [30-04-migration-014, 32-pass-2-enricher, 33-reader-downloads]

actuals:
  tokens: 2203
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - Body sanitizers run in DTO validators; never a fail-closed heading parser (D-09, Phase 8 D-15)
    - _GUIDE_HEADING_RE clones audience ATX shape with re.IGNORECASE (RESEARCH A3)
    - Pass-1 templates stay free of Гайд; the strip, not the prompt, is the KIND-03 gate

key-files:
  created:
    - tests/unit/test_article_draft_body_guide.py
  modified:
    - data-collection/src/data_collection/dto/_body.py
    - data-collection/src/data_collection/dto/article_draft.py
    - tests/unit/test_deepseek_article_adapter.py

key-decisions:
  - "strip_guide_section clones the audience heading-until-next-h1/h2 walk; then deletes every occurrence of ссылки скоро появятся"
  - "Second @field_validator(body_markdown) runs after the audience strip on every pass-1 body including practical (D-11)"
  - "D-12 exact match only: Guide / How-to / Как сделать / Tutorial / Шпаргалка and in-prose гайд stay"
  - "Task 2 is a characterization pin of the Phase 29 lock — templates were not rewritten"

patterns-established:
  - "Pattern: extras furniture is stripped in ArticleDraft validators, never by rejecting ingest"
  - "Pattern: lowercase Cyrillic ATX гайд is covered by re.IGNORECASE, pinned by an explicit lowercase heading test (A3)"

requirements-completed: [KIND-03]

coverage:
  - id: D1
    description: "ArticleDraft.model_validate strips an entire ATX Гайд section (empty or filled) from every pass-1 body, including practical-stamped drafts (KIND-03, D-09, D-10, D-11)"
    requirement: KIND-03
    verification:
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_strips_trailing_empty_guide_section
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_strips_filled_guide_section
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_practical_draft_also_loses_guide_section
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_audience.py
        status: pass
    human_judgment: false
  - id: D2
    description: "The exact substring ссылки скоро появятся is removed even when it sits outside the Гайд section (KIND-03, D-10)"
    requirement: KIND-03
    verification:
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_strips_placeholder_substring_outside_the_guide_section
        status: pass
    human_judgment: false
  - id: D3
    description: "In-prose гайд and D-12 talk headings (Guide, How-to, Как сделать, Tutorial, Шпаргалка) remain; lowercase ATX гайд is stripped; mid-body strip keeps the following h2; second validate is idempotent"
    requirement: KIND-03
    verification:
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_mention_of_guide_mid_text_is_preserved
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_d12_talk_headings_are_kept
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_strips_lowercase_atx_guide_heading
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_body_keeps_a_later_section_that_follows_the_guide_block
        status: pass
      - kind: unit
        ref: tests/unit/test_article_draft_body_guide.py#test_guide_stripping_is_idempotent
        status: pass
    human_judgment: false
  - id: D4
    description: "Assembled lecture and podcast user messages omit Гайд; SHARED_PROMPT_HEADINGS stays the three Phase 29 output headings (KIND-03, D-11)"
    requirement: KIND-03
    verification:
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_assembled_user_message_omits_guide_heading
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_create_kwargs_include_json_object_and_disabled_thinking
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-29
status: complete
---

# Phase 30 Plan 03: Guide-section body strip Summary

**Every pass-1 `ArticleDraft` drops ATX `Гайд` (empty or filled, including lowercase) and the exact substring `ссылки скоро появятся` in a validator, without touching D-12 talk headings or fail-closing ingest**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-29T03:23:28Z
- **Completed:** 2026-10-29T03:27:21Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `strip_guide_section` clones the `strip_audience_section` walk (`_GUIDE_HEADING_RE` + reused `_NEXT_TOP_HEADING_RE`) and then deletes every occurrence of `ссылки скоро появятся`.
- A second `@field_validator("body_markdown")` on `ArticleDraft` runs the strip on every pass-1 body, including `topic_kind=practical` (D-11). A leaked heading is deleted; ingest is not rejected (D-09, Phase 8 D-15).
- D-12 titles and in-prose `гайд` survive. Lowercase ATX `гайд` is stripped (RESEARCH A3).
- Lecture and podcast assembled user messages still omit `Гайд`; `SHARED_PROMPT_HEADINGS` is unchanged. Templates were not edited.

## RED assertions (Task 1)

Command: `uv run pytest tests/unit/test_article_draft_body_guide.py tests/unit/test_article_draft_body_audience.py -x`

- `test_body_strips_trailing_empty_guide_section` — `AssertionError: assert 'Гайд' not in '## Тезис\n\nМысль.\n\n## Гайд'`

## Task 2 characterization

Command: `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_guide.py tests/unit/test_article_draft_body_audience.py -q`

Landed green immediately: Phase 29 templates already omit `Гайд`. The new pin would redden if a template gained the heading.

## GREEN command output

- Task 1: `17 passed` (`uv run pytest tests/unit/test_article_draft_body_guide.py tests/unit/test_article_draft_body_audience.py -x`)
- Task 2: `77 passed` (adapter + guide + audience)
- Plan gate: `uv run pytest tests/unit/test_article_draft_body_guide.py tests/unit/test_article_draft_body_audience.py tests/unit/test_deepseek_article_adapter.py -q` — included in the 77
- Wave gate: `1265 passed, 1 warning` (`uv run pytest tests/unit -q`)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: failing tests for guide section strip** - `7bf41ad` (test)
2. **Task 1 GREEN: strip Гайд section from every ArticleDraft body** - `ad7238e` (feat)
3. **Task 2: pin pass-1 templates omit Гайд** - `7d0a3a5` (test; characterization, no production edit)

**Plan metadata:** (docs commit after this file)

_Note: TDD Task 1 is test → feat. Task 2 is a characterization pin that was green on a clean tree by design._

## Files Created/Modified

- `data-collection/src/data_collection/dto/_body.py` — `_GUIDE_HEADING_RE`, `_GUIDE_PLACEHOLDER`, `strip_guide_section`
- `data-collection/src/data_collection/dto/article_draft.py` — `_strip_guide_scaffolding` validator after audience
- `tests/unit/test_article_draft_body_guide.py` — clone of audience case matrix plus D-10/D-11/D-12/A3 extras
- `tests/unit/test_deepseek_article_adapter.py` — parametrized `Гайд` absence pin over LECTURE/PODCAST

Unchanged: `lecture.md`, `podcast.md`, `tests/unit/test_article_draft_body_audience.py`.

## Decisions Made

- Clone the audience heading-until-next-h1/h2 walk rather than a fail-closed heading parser (D-09 / Phase 8 D-15).
- Second dedicated `field_validator("body_markdown")` after the audience strip so both run on every validate (D-11), including practical drafts.
- D-12 “exact” means do not match English/other how-to titles; `re.IGNORECASE` still folds Cyrillic `гайд` (A3).
- Task 2 does not rewrite templates; it pins the Phase 29 lock so Phase 32 is the first allowed home for a guide heading.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** No scope creep.

## Issues Encountered

None.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## TDD Gate Compliance

- Task 1 RED commit `7bf41ad` precedes GREEN `ad7238e`. RED failed because `## Гайд` remained in `body_markdown`.
- Task 2 has no RED production gap: the plan required a characterization pin that is green on a clean tree. Commit `7d0a3a5` is test-only.
- No `refactor(30-03)` commit — the audience-clone walk needed no cleanup.

## Next Phase Readiness

- KIND-03 body honesty is true in code. Persist still does not store `topic_kind` in Postgres — that is Plan 04 (KIND-01, migration 014).
- Do not start 30-04 from this executor. Do not revert 30-01 or 30-02.
- Phase 32 is the first allowed home for a guide heading in templates.

## Self-Check: PASSED

- FOUND: `data-collection/src/data_collection/dto/_body.py`
- FOUND: `data-collection/src/data_collection/dto/article_draft.py`
- FOUND: `tests/unit/test_article_draft_body_guide.py`
- FOUND: `tests/unit/test_deepseek_article_adapter.py`
- FOUND: `7bf41ad` `ad7238e` `7d0a3a5`

---
*Phase: 30-classifier-practical-conceptual*
*Completed: 2026-10-29*
