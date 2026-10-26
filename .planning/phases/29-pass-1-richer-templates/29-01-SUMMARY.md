---
phase: 29-pass-1-richer-templates
plan: 01
subsystem: ingestion-prompts
tags: [deepseek, lecture-template, article-prompt, tdd, pass-1]

requires:
  - phase: 08-deepseek-article-templates
    provides: lecture.md package data, ARTICLE_SYSTEM_PROMPT, stub-client adapter tests
provides:
  - lecture.md as a topic-shaped СВА longread frame with optional ## Конкретика and ## Зачем это СВА
  - inverted lecture heading pins (legacy scaffold forbidden, shared frame present)
  - shared edition-voice, dek-hook, and 1200-1800 word rules in ARTICLE_SYSTEM_PROMPT
affects: [29-02-podcast-frame, 29-03-live-ingest-proof]

actuals:
  tokens: 3062
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - positive editorial frame in package markdown (no instruction-only ##)
    - inverted absence pins for legacy scaffold headings
    - shared voice/length rules live in ARTICLE_SYSTEM_PROMPT only

key-files:
  created: []
  modified:
    - data-collection/src/data_collection/templates/lecture.md
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - tests/unit/test_article_templates.py
    - tests/unit/test_deepseek_article_adapter.py

key-decisions:
  - "Instruction-only structure rules are a lead paragraph plus bullets with no ## heading, so lecture.md headings equal the headings the model is asked to emit"
  - "The 1200-1800 word band lives only in ARTICLE_SYSTEM_PROMPT, not in lecture.md"
  - "LEGACY_PODCAST_HEADINGS is a forward declaration for Plan 02; this plan does not invert the podcast pin"
  - "Edition-voice, recap-phrase examples, СВА inference boundary, dek hook, and length band are shared in ARTICLE_SYSTEM_PROMPT"

patterns-established:
  - "Pattern: ## in a template file is an output heading only — never an instruction label"
  - "Pattern: tests pin frame literals and absence, never a whole template sentence or a byte digest"
  - "Pattern: _user_content / _system_content helpers run the real stub-client round-trip so pins inspect the assembled messages"

requirements-completed: [ART-01, ART-02, ART-03]

coverage:
  - id: D1
    description: "lecture.md is a positive editorial frame whose only level-2 headings are ## Конкретика, ## Зачем это СВА, ## Аудитория (audience last, no H1, no instruction-only heading)"
    requirement: ART-01
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_has_only_the_intended_headings
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_keeps_the_audience_block_last
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_names_the_topics_frame
        status: pass
    human_judgment: false
  - id: D2
    description: "Legacy lecture scaffold headings are absent from lecture.md and from the assembled lecture user message; shared frame headings are present end-to-end through the package loader"
    requirement: ART-01
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_omits_legacy_scaffold
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_lecture_prompt_omits_every_legacy_heading
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_lecture_prompt_carries_the_shared_frame
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_load_article_templates_returns_both_kinds
        status: pass
    human_judgment: false
  - id: D3
    description: "lecture.md carries ## Конкретика with transcript-only, bullets-first, canonical-name, never-invent-a-version, table-only-for-grid, and omit-when-empty rules"
    requirement: ART-02
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_states_the_concretika_rules
        status: pass
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_names_the_topics_frame
        status: pass
    human_judgment: false
  - id: D4
    description: "lecture.md carries ## Зачем это СВА with the analog bar, no-invented-duty rule, and honest omit"
    requirement: ART-03
    verification:
      - kind: unit
        ref: tests/unit/test_article_templates.py#test_lecture_md_states_the_sva_rules
        status: pass
    human_judgment: false
  - id: D5
    description: "ARTICLE_SYSTEM_PROMPT carries edition voice, recap-phrase examples, СВА inference boundary, dek as a 1-2 sentence hook, and the 1200-1800 word band, with the ten honesty/language pins and trailing JSON-contract sentence intact"
    requirement: ART-03
    verification:
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_system_prompt_carries_the_edition_voice_and_length_rules
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_system_prompt_contains_honesty_and_language_rules
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-26
status: complete
---

# Phase 29 Plan 01: Lecture frame tracer Summary

**Lecture path is a Russian СВА longread whose `##` follow the talk: package markdown → `load_article_templates` → `build_article_messages` → stub-client `DeepSeekArticleGenerator.process`, with shared voice/`dek`/length rules in `ARTICLE_SYSTEM_PROMPT`**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-26T18:28:28Z
- **Completed:** 2026-10-26T18:32:30Z
- **Tasks:** 2
- **Files modified:** 4
- **Baseline (pre-RED trio):** 54 passed in 1.63s
- **Wave gate after Task 1 GREEN:** 1175 passed in 15.45s
- **Wave gate after Task 2 GREEN:** 1176 passed in 13.70s

## Accomplishments

- Rewrote `lecture.md` as a positive editorial frame: topic-shaped level-2 sections with no fixed count, optional `## Конкретика`, optional `## Зачем это СВА`, trailing `## Аудитория`. No instruction-only heading. No H1. No word-band copy (length lives in the system prompt).
- Inverted the lecture half of the heading pins from "scaffold is present" to "scaffold is forbidden and frame is present", via the real `importlib.resources.files("data_collection.templates")` path and a stub-client round-trip. `LEGACY_PODCAST_HEADINGS` is declared for Plan 02 and unused here on purpose.
- Extended `ARTICLE_SYSTEM_PROMPT` additively with edition voice, the three recap-phrase examples, the capitalised `Editorial inference is allowed only in the closing section about СВА;` boundary, `dek` as a `1-2 sentence hook`, and `1200-1800 words`. The seven prior lines and the trailing JSON-contract sentence are unchanged.

## Task Commits

Each task was committed atomically (TDD RED then GREEN):

1. **Task 1 RED: lecture longread pins** - `f3eaa95` (test)
2. **Task 1 GREEN: rewrite lecture.md** - `359b9eb` (feat)
3. **Task 2 RED: edition-voice system-prompt pins** - `4e7c3c2` (test)
4. **Task 2 GREEN: extend ARTICLE_SYSTEM_PROMPT** - `37f9916` (feat)

**Plan metadata:** pending `docs(29-01)` commit after this file.

_Note: TDD tasks produced two commits each (test → feat)._

## RED evidence (quoted)

**Task 1** (`uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py` before any production edit): **16 failed, 50 passed**.

Quoted assertion text:

- `AssertionError: assert '## Тезис' not in '## Тезис\n\...alyst, ds.\n'` (`test_lecture_md_omits_legacy_scaffold`)
- same shape for `## Ход рассуждения` and `## Вывод` (three parametrized failures)
- `AssertionError: assert '## Конкретика' in '## Тезис\n\nSummarize the core thesis...'` (`test_lecture_md_carries_the_shared_frame`; `## Зачем это СВА` twin; `## Аудитория` passed)
- `assert "single speaker's argument" in '## Тезис\n\nSummarize...'` (`test_lecture_md_names_the_topics_frame`)
- `assert '## Конкретика' in '## Тезис...'` (`test_lecture_md_states_the_concretika_rules`, `test_lecture_md_states_the_sva_rules`)
- `assert {'## Аудитория', '## Тезис', '## Ход рассуждения', '## Вывод'} == {'## Аудитория', '## Зачем это СВА', '## Конкретика'}` (`test_lecture_md_has_only_the_intended_headings`)
- `assert '## Конкретика' in templates[LECTURE]` (`test_load_article_templates_returns_both_kinds`)
- adapter: three of six `test_lecture_prompt_omits_every_legacy_heading` failures (`## Тезис` / `## Ход рассуждения` / `## Вывод` still in the assembled user message; the three podcast literals already absent)
- two of three `test_lecture_prompt_carries_the_shared_frame` failures (`## Конкретика`, `## Зачем это СВА`)
- `assert "single speaker's argument" in` assembled user message (`test_lecture_prompt_keeps_the_kind_sentinel`)

Untouched podcast cases stayed green (`test_podcast_md_contains_russian_headings`, `test_podcast_prompt_contains_podcast_headings_not_lecture`, `test_process_returns_article_draft_for_podcast`).

**Task 2** (`uv run pytest tests/unit/test_deepseek_article_adapter.py -k edition_voice -x` before the prompt edit):

```
AssertionError: assert 'voice of the edition' in 'You are an editorial assistant preparing articles for СВА (Служба внутреннего аудита).\nUse only the transcript below...Return one json object with keys title, dek, body_markdown, roles.'
```

## GREEN command output

- Task 1 after `lecture.md` rewrite: `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py -x` → **66 passed in 1.48s**; `uv run pytest` → **1175 passed in 15.45s**
- Task 2 after `ARTICLE_SYSTEM_PROMPT` extend: `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` → **49 passed in 0.87s**; `-k system_prompt` → **2 passed**; plan-level trio → **74 passed in 1.68s**; `uv run pytest` → **1176 passed in 13.70s**

## Files Created/Modified

- `data-collection/src/data_collection/templates/lecture.md` — topic-shaped longread frame + optional facts/СВА sections + audience tail
- `data-collection/src/data_collection/adapters/deepseek_article.py` — additive lines inside `ARTICLE_SYSTEM_PROMPT` only; `build_article_messages` / `process` / `_stream_content` / error mapping untouched
- `tests/unit/test_article_templates.py` — inverted lecture pins, shared-frame/concretika/SVA/heading-set/audience-last tests, `_template_text` helper, `LEGACY_PODCAST_HEADINGS` forward declaration
- `tests/unit/test_deepseek_article_adapter.py` — inverted lecture prompt pins, `_user_content` / `_system_content` helpers, edition-voice test

Untouched (empty `git diff --stat`): `podcast.md`, `dto/_body.py`, `pyproject.toml`, `uv.lock`. Call-shape kwargs (`response_format`, `thinking`, `stream=True`, no `max_tokens`) unchanged.

## Decisions Made

- Instruction-only structure rules carry no `##` heading. A `##` line in `lecture.md` is an output heading; `test_lecture_md_has_only_the_intended_headings` pins the set to exactly the three shared output headings. The PATTERNS example `## Structure` label was not copied (PLAN prohibition).
- Length band lives only in `ARTICLE_SYSTEM_PROMPT` (`1200-1800 words`, ASCII hyphen, no thousands separator). `lecture.md` does not repeat it.
- `LEGACY_PODCAST_HEADINGS` is declared in `test_article_templates.py` for Plan 02. No podcast heading assertion was added here, so this plan can go green without touching `podcast.md`.
- Shared voice/inference/`dek`/length rules were added to `ARTICLE_SYSTEM_PROMPT` rather than duplicated into the markdown file (RESEARCH Q2). Recap phrases are style prohibitions, not heading literals.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** none

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `29-02-PLAN.md` (podcast frame with kind-sentinel isolation and the audience-strip regression pin). ART-01/ART-02/ART-03 remain shared with 29-02 and 29-03, so they are not marked Complete until those summaries exist. Wave 2 must not start from this executor.

No stubs. No new network endpoint, auth path, file-access pattern, or schema change beyond the plan's `<threat_model>`.

## Self-Check: PASSED

- FOUND: `data-collection/src/data_collection/templates/lecture.md`
- FOUND: `data-collection/src/data_collection/adapters/deepseek_article.py`
- FOUND: `tests/unit/test_article_templates.py`
- FOUND: `tests/unit/test_deepseek_article_adapter.py`
- FOUND: `f3eaa95` test(29-01): add failing test for lecture talk-shaped longread
- FOUND: `359b9eb` feat(29-01): rewrite lecture template as talk-shaped longread
- FOUND: `4e7c3c2` test(29-01): add failing test for edition voice and length rules
- FOUND: `37f9916` feat(29-01): add edition voice, dek and length rules to system prompt

---
*Phase: 29-pass-1-richer-templates*
*Completed: 2026-10-26*
