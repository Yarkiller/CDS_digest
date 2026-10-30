---
phase: 29-pass-1-richer-templates
fixed_at: 2026-10-30T04:00:36.951Z
review_path: .planning/phases/29-pass-1-richer-templates/29-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 29: Code Review Fix Report

**Fixed at:** 2026-10-30T04:00:36.951Z
**Source review:** `.planning/phases/29-pass-1-richer-templates/29-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 11
- Fixed: 11
- Skipped: 0

## Verification

Gates ran in the **main checkout** (`workflow.use_worktrees=false`; no isolated worktree). Per-finding TDD: failing test first (or a pin of already-green behavior for Info coverage), then production, then focused re-run.

- JS unit: `node --test tests/unit/test_markdown_sections.js` and `tests/unit/test_markdown_toc.js`
- Python: `uv run pytest tests/unit/test_article_templates.py` and focused `test_deepseek_article_adapter.py` cases
- Playwright (IN-04 only): `npx playwright test --project=web tests/web-app.spec.js -g "omits Конкретика..."` — 1 passed

## Fixed Issues

### WR-01: `splitMaterialSections` splits on ATX headings inside fenced code

**Files modified:** `web/src/utils/markdownSections.js`, `tests/unit/test_markdown_sections.js`
**Commit:** `cddec23`
**Applied fix:** Fence toggle (`/^```/`) now matches TOC. Fenced `## Конкретика` stays in the parent `topic`/`body` band.

### WR-02: reserved-heading chrome matches only the exact heading string

**Files modified:** `web/src/utils/markdownSections.js`, `tests/unit/test_markdown_sections.js`
**Commit:** `0e8c3c0`
**Applied fix:** `kindForHeading` strips `*_`` and trailing `.:?!` before comparing. `## **Конкретика**` and `## Зачем это СВА?` map to cards.

### WR-03: `podcast.md` orders the model to cut by speaker and by topic at once

**Files modified:** `data-collection/src/data_collection/templates/podcast.md`, `tests/unit/test_article_templates.py`
**Commit:** `ea98c8f`
**Applied fix:** One discriminator bullet keeps «positions of its participants» inside the dialogue branch; the unconditional «Structure the conversation by positions of its participants» sentence is gone.

### WR-04: each band is its own Markdown tree — footnotes and TOC ids diverge

**Files modified:** `data-collection/src/data_collection/templates/lecture.md`, `data-collection/src/data_collection/templates/podcast.md`, `data-collection/src/data_collection/adapters/deepseek_article.py`, `tests/unit/test_article_templates.py`, `tests/unit/test_deepseek_article_adapter.py`, `tests/unit/test_markdown_toc.js`
**Commit:** `f1780a6`
**Status:** `fixed: requires human verification`
**Applied fix:** Prompts forbid `[^n]` endnotes in favor of parenthetical «Редакционное примечание». TOC helper pin: two `## Введение` around `## Конкретика` → second id is `user-content-введение-1`. MaterialPage still mounts one `ArticleMarkdown` per band — DOM footnote counters and per-tree `rehype-slug` ids can still diverge until parse is one tree.

### WR-05: system prompt skips the editorial label and pushes a invented speaker name

**Files modified:** `data-collection/src/data_collection/adapters/deepseek_article.py`, `tests/unit/test_deepseek_article_adapter.py`
**Commit:** `195b687`
**Applied fix:** `ARTICLE_SYSTEM_PROMPT` now requires «докладчик»/«ведущий» when the name is absent, and marks added definitions/notes as «Редакционное примечание».

### WR-06: empty `## Конкретика` / `## Зачем это СВА` still become cards

**Files modified:** `web/src/utils/markdownSections.js`, `tests/unit/test_markdown_sections.js`
**Commit:** `4437a8f`
**Applied fix:** `groupMaterialBands` skips reserved bands whose body after the heading line is blank. `## Конкретика\n\n## Оценка` yields only the trailing topic body.

### IN-01: `test_assembled_user_message_omits_guide_heading` asserts a test constant against itself

**Files modified:** `tests/unit/test_deepseek_article_adapter.py`
**Commit:** `f290be2`
**Applied fix:** Dropped the tautological tuple equality. The test now asserts each shared heading is in `_user_content(...)` and still pins «Гайд» absence.

### IN-02: Конкретика / СВА / Аудитория tails are copy-pasted with no equality pin

**Files modified:** `tests/unit/test_article_templates.py`
**Commit:** `f8d1757`
**Applied fix:** `test_shared_concretika_sva_audience_tails_are_identical` slices each template from `## Конкретика` and asserts `lecture_tail == podcast_tail`.

### IN-03: splitter unit tests cover only the happy path with both reserved headings

**Files modified:** `tests/unit/test_markdown_sections.js`
**Commit:** `63fd87e`
**Applied fix:** Added `null`/`undefined` → `[]` and an article with only `## Введение` / `## Оценка` (no reserved cards). Fenced `##` and heading-only omit were already pinned by WR-01 / WR-06.

### IN-04: Playwright only asserts that both cards exist on `rag-systems`

**Files modified:** `tests/unit/test_markdown_sections.js`, `tests/web-app.spec.js`
**Commit:** `fdb0319`
**Applied fix:** Unit pin on the `empty-dek-article` body (`groupMaterialBands` → no `concretika`/`sva`). Playwright: `/materials/empty-dek-article` expects those testids at count 0 while `material-section-body` stays visible (ran, 1 passed).

### IN-05: `headingText` has an unreachable `startsWith('###')` guard

**Files modified:** `web/src/utils/markdownSections.js`
**Commit:** `e57fd58`
**Applied fix:** Dropped `|| line.startsWith('###')`. Comment notes that `###`/`####` fail the `'## '` prefix and stay in `buf`. Existing nested-heading test stays green.

---

_Fixed: 2026-10-30T04:00:36.951Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
