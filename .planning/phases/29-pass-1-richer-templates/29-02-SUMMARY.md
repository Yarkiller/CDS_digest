---
phase: 29-pass-1-richer-templates
plan: 02
subsystem: ingestion-prompts
tags: [deepseek, podcast-template, article-prompt, tdd, pass-1, audience-strip]

requires:
  - phase: 29-pass-1-richer-templates
    provides: lecture.md talk-shaped frame, ARTICLE_SYSTEM_PROMPT voice/dek/length, LEGACY_PODCAST_HEADINGS forward declaration
provides:
  - podcast.md as a dialogue/topic-shaped СВА longread frame with the same ## Конкретика and ## Зачем это СВА clauses as lecture.md
  - inverted podcast heading pins plus cross-kind sentinel isolation at file and assembled-message level
  - audience-strip exact-remainder pin on a pass-1-shaped body
affects: [29-03-live-ingest-proof]

actuals:
  tokens: 2493
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - kind discriminator is a multi-word sentinel unique to one file, never a shared section heading
    - ## in a template file is an output heading only — never an instruction label
    - strip_audience_section characterization via exact remainder plus a recorded mutation

key-files:
  created: []
  modified:
    - data-collection/src/data_collection/templates/podcast.md
    - tests/unit/test_article_templates.py
    - tests/unit/test_deepseek_article_adapter.py
    - tests/unit/test_article_draft_body_audience.py

key-decisions:
  - "podcast.md mirrors lecture.md with one kind-hint paragraph; shared voice/dek/length stay in ARTICLE_SYSTEM_PROMPT"
  - "Kind isolation pins unique sentinels (positions of its participants vs single speaker's argument), never ## Конкретика or ## Зачем это СВА"
  - "Audience-strip mutation: a pure top-placement among h2 sections does not redden equality; non-vacuity required demoting the first section out of h2 so it sat inside the audience span"

patterns-established:
  - "Pattern: the two templates differ by one multi-word kind hint and nothing else"
  - "Pattern: inverted absence pins for both kinds at file and stub-client message level"
  - "Pattern: strip_audience_section is proven against a body shaped like the new output, not by rewriting legacy fixtures"

requirements-completed: [ART-01, ART-02, ART-03]

coverage:
  - id: D1
    description: "podcast.md is a positive editorial frame whose only level-2 headings are ## Конкретика, ## Зачем это СВА, ## Аудитория (audience last, no H1, no instruction-only heading), with the dialogue kind hint"
    requirement: ART-01
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_has_only_the_intended_headings
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_keeps_the_audience_block_last
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_names_the_dialogue_frame
        status: pass
    human_judgment: false
  - id: D2
    description: "Legacy podcast scaffold headings are absent from podcast.md and from the assembled podcast user message; all six legacy literals are forbidden at message level; shared frame headings are present"
    requirement: ART-01
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_omits_legacy_scaffold
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_podcast_prompt_omits_every_legacy_heading
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_podcast_prompt_carries_the_shared_frame
        status: pass
    human_judgment: false
  - id: D3
    description: "podcast.md copies lecture.md's ## Конкретика and ## Зачем это СВА clauses verbatim (same heading strings, bullets-first, canonical-name, never-invent-a-version, analog bar, omit-when-empty)"
    requirement: ART-02
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_states_the_concretika_rules
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_podcast_md_states_the_sva_rules
        status: pass
    human_judgment: false
  - id: D4
    description: "Kind sentinels do not cross at file or assembled-message level: lecture has single speaker's argument, podcast has positions of its participants"
    requirement: ART-01
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_kind_sentinels_do_not_cross
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_podcast_prompt_keeps_the_kind_sentinel
        status: pass
    human_judgment: false
  - id: D5
    description: "A body shaped like the new pass-1 output keeps ## Конкретика and ## Зачем это СВА byte-identically while the trailing ## Аудитория scaffolding is stripped"
    requirement: ART-03
    verification:
      - kind: unit
        ref: tests/unit/test_article_draft_body_audience.py#test_body_strips_audience_section_after_the_concretika_and_sva_sections
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-26
status: complete
---

# Phase 29 Plan 02: Podcast frame and audience-strip Summary

**Podcast path is the same talk-shaped СВА longread as lecture, differing by one multi-word kind hint (`positions of its participants`); inverted scaffold pins and the `## Аудитория` strip hold at file, message, and DTO level**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-26T18:37:39Z
- **Completed:** 2026-10-26T18:44:23Z
- **Tasks:** 2
- **Files modified:** 4
- **Task 1 RED:** 16 failed, 71 passed in 1.77s
- **Task 1 GREEN:** 87 passed in 1.47s; wave gate `uv run pytest` → **1196 passed in 13.52s**
- **Task 2 GREEN:** 8 passed in 0.21s; wave gate `uv run pytest` → **1197 passed in 14.63s**

## Accomplishments

- Rewrote `podcast.md` as a positive editorial frame mirroring `lecture.md`: dialogue-or-topic level-2 sections, optional `## Конкретика`, optional `## Зачем это СВА`, trailing `## Аудитория`. No instruction-only heading. No H1. No voice/dek/length copy (those live in `ARTICLE_SYSTEM_PROMPT` from Plan 01).
- Inverted the podcast half of the heading pins from "scaffold is present" to "scaffold is forbidden and frame is present", at both the package-markdown path and the stub-client assembled user message. Cross-kind isolation uses the unique sentinels, never the shared section headings.
- Swapped the `test_process_returns_article_draft_for_podcast` scripted body off `## О чём разговор` onto `## Как это устроено` so the module carries no positive legacy literal.
- Added `test_body_strips_audience_section_after_the_concretika_and_sva_sections`: a pass-1-shaped body keeps the three content sections byte-identically while the trailing audience scaffolding is stripped.

## Task Commits

Each task was committed atomically (TDD RED then GREEN for Task 1):

1. **Task 1 RED: podcast longread pins** - `ca0ced7` (test)
2. **Task 1 GREEN: rewrite podcast.md** - `fa82979` (feat)
3. **Task 2: audience-strip characterization pin** - `ce3f526` (test)

**Plan metadata:** pending `docs(29-02)` commit after this file.

_Note: Task 1 is TDD (test → feat). Task 2 is a characterization pin (passes on first run; RED is a recorded mutation)._

## RED evidence (quoted)

**Task 1** (`uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py` before any production edit): **16 failed, 71 passed**.

Quoted assertion text:

- `AssertionError: assert '## О чём разговор' not in '## О чём ра...alyst, ds.\n'` (`test_podcast_md_omits_legacy_scaffold`)
- same shape for `## Позиции` and `## Что запомнить` (three parametrized failures)
- `AssertionError: assert '## Конкретика' in '## О чём разговор\n\nSummarize the topic...'` (`test_podcast_md_carries_the_shared_frame`; `## Зачем это СВА` twin; `## Аудитория` passed)
- `assert "positions of its participants" in '## О чём разговор...'` (`test_podcast_md_names_the_dialogue_frame`)
- `assert '## Конкретика' in '## О чём разговор...'` (`test_podcast_md_states_the_concretika_rules`, `test_podcast_md_states_the_sva_rules`)
- `assert {'## Аудитория', '## О чём разговор', '## Позиции', '## Что запомнить'} == {'## Аудитория', '## Зачем это СВА', '## Конкретика'}` (`test_podcast_md_has_only_the_intended_headings`)
- `assert "positions of its participants" in podcast` (`test_kind_sentinels_do_not_cross`; lecture half already green)
- adapter: three of six `test_podcast_prompt_omits_every_legacy_heading` failures (`## О чём разговор` / `## Позиции` / `## Что запомнить` still in the assembled user message; the three lecture literals already absent)
- two of three `test_podcast_prompt_carries_the_shared_frame` failures (`## Конкретика`, `## Зачем это СВА`)
- `assert "positions of its participants" in` assembled user message (`test_podcast_prompt_keeps_the_kind_sentinel`)

PASS-THROUGH: `test_podcast_md_keeps_the_audience_block_last` stayed green on the old file (audience was already last) and after the rewrite.

**Task 2 mutation** (`uv run pytest tests/unit/test_article_draft_body_audience.py::test_body_strips_audience_section_after_the_concretika_and_sva_sections -x`):

- Pure top-placement of `## Аудитория` among intact h2 content sections: **1 passed** — `strip_audience_section` concatenates remaining h1/h2 sections, so the exact remainder still matched.
- Follow-up mutation (audience first, first content heading demoted out of h2 so that section sat inside the audience span): **1 failed**

```
AssertionError: assert '## Конкретик...до проверять.' == '## Как устро...до проверять.'
- ## Как устроены языковые модели
-
- Мысль.
-
  ## Конкретика
```

Restored fixture: audience last, all three content headings intact. Suite green.

## GREEN command output

- Task 1 after `podcast.md` rewrite: `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py -x` → **87 passed in 1.47s**; `uv run pytest` → **1196 passed in 13.52s**
- Task 2 after the strip case: `uv run pytest tests/unit/test_article_draft_body_audience.py -x` → **8 passed in 0.21s**; `uv run pytest` → **1197 passed in 14.63s**

## Files Created/Modified

- `data-collection/src/data_collection/templates/podcast.md` — dialogue/topic-shaped longread frame + optional facts/СВА sections + audience tail
- `tests/unit/test_article_templates.py` — inverted podcast pins, shared-frame/concretika/SVA/heading-set/audience-last twins, bidirectional kind-sentinel isolation
- `tests/unit/test_deepseek_article_adapter.py` — inverted podcast prompt pins; pass-through fixture heading swapped to `## Как это устроено`
- `tests/unit/test_article_draft_body_audience.py` — exact-remainder strip case against a pass-1-shaped body

Untouched (empty `git diff --stat`): `lecture.md`, `deepseek_article.py`, `dto/_body.py`, `pyproject.toml`, `uv.lock`.

## Decisions Made

- `podcast.md` copies the lecture lead, `## Конкретика`, `## Зачем это СВА`, and `## Аудитория` clauses verbatim. The only structural difference is the kind-hint bullets (dialogue → positions/speakers; otherwise topics of the conversation; sentinel `positions of its participants`).
- Kind isolation never uses a shared section heading as the discriminator. `test_kind_sentinels_do_not_cross` and `test_podcast_prompt_keeps_the_kind_sentinel` pin the unique multi-word sentinels in both directions.
- No `## Structure` instruction label. Every `##` line is an output heading; `test_podcast_md_has_only_the_intended_headings` pins the set to exactly the three shared output headings.
- Voice/dek/length stay only in `ARTICLE_SYSTEM_PROMPT` (Plan 01). This plan does not restate them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Audience-strip mutation needed a demoted heading to redden equality**
- **Found during:** Task 2 (audience-strip characterization pin)
- **Issue:** Moving `## Аудитория` to the top of a body whose remaining sections are all h2 left the exact remainder unchanged, because `strip_audience_section` concatenates from the next h1/h2 to end-of-body. The planned mutation therefore could not prove the equality assertion was live.
- **Fix:** Recorded that pass, then demoted the first content heading out of h2 so that section sat inside the audience span. The strip truncated to `## Конкретика`. Restored the audience-last fixture with all three headings intact.
- **Files modified:** `tests/unit/test_article_draft_body_audience.py` (mutation only; restored before commit)
- **Verification:** mutation failed as quoted above; restored case and full suite green
- **Committed in:** `ce3f526` (Task 2 commit; restored fixture only)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Non-vacuity of the strip pin is proven; production `dto/_body.py` unchanged. No scope creep.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `29-03-PLAN.md` (live ingest proof: heading list, per-bullet facts audit against the transcript, `response_chars` band, owner read). ART-01/ART-02/ART-03 remain shared with 29-03, so they are not marked Complete until that summary exists. Wave 3 must not start from this executor.

No stubs. No new network endpoint, auth path, file-access pattern, or schema change beyond the plan's `<threat_model>`.

## Self-Check: PASSED

- FOUND: `data-collection/src/data_collection/templates/podcast.md`
- FOUND: `tests/unit/test_article_templates.py`
- FOUND: `tests/unit/test_deepseek_article_adapter.py`
- FOUND: `tests/unit/test_article_draft_body_audience.py`
- FOUND: `ca0ced7` test(29-02): add failing test for podcast talk-shaped longread
- FOUND: `fa82979` feat(29-02): rewrite podcast template as talk-shaped longread
- FOUND: `ce3f526` test(29-02): pin audience strip after concretika and sva sections

---
*Phase: 29-pass-1-richer-templates*
*Completed: 2026-10-26*
