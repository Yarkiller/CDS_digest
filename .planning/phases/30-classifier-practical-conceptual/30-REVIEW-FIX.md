---
phase: 30-classifier-practical-conceptual
fixed_at: 2026-10-30T02:57:36Z
review_path: .planning/phases/30-classifier-practical-conceptual/30-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 30: Code Review Fix Report

**Fixed at:** 2026-10-30T02:57:36Z
**Source review:** `.planning/phases/30-classifier-practical-conceptual/30-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (WR-01, WR-02, WR-03; IN-01…IN-04 out of scope)
- Fixed: 3
- Skipped: 0

## Verification

Gates ran in the **main checkout** (`workflow.use_worktrees=false`). No isolated worktree, temp branch, or recovery sentinel was created. Per finding: failing unit test first, then production fix, then `uv run pytest` on the touched module and `python -c "import ast; ast.parse(...)"` (Tier 1 re-read + Tier 2).

## Fixed Issues

### WR-01: `strip_guide_section` strips only the first `## Гайд` and deletes through EOF when no later h1/h2 exists

**Files modified:** `data-collection/src/data_collection/dto/_body.py`, `tests/unit/test_article_draft_body_guide.py`
**Commit:** `ad021ca`
**Status:** fixed: requires human verification
**Applied fix:** Loop until no ATX `Гайд` heading remains (a later `## Гайд` is no longer treated as a terminator that keeps the second block). Do not restore the original body when the strip would empty it — that would re-persist `## Гайд`. After stripping, if the body is empty, keep the stub `"."` so `ArticleDraft` `min_length=1` still validates. Tests pin (a) two `## Гайд` sections both gone and (b) a guide-only body still `model_validate()`s with no `Гайд`.

### WR-02: Honest-absence placeholder wipe is case-sensitive

**Files modified:** `data-collection/src/data_collection/dto/_body.py`, `tests/unit/test_article_draft_body_guide.py`
**Commit:** `ddf764c`
**Status:** fixed
**Applied fix:** Delete «ссылки скоро появятся» with `re.IGNORECASE` (`_GUIDE_PLACEHOLDER_RE.sub`) instead of exact `str.replace`. Test pins the capital-С form `Ссылки скоро появятся`.

### WR-03: Classifier interpolates `title`/`dek` outside the untrusted fence

**Files modified:** `data-collection/src/data_collection/adapters/deepseek_classifier.py`, `tests/unit/test_deepseek_classifier.py`
**Commit:** `fb5548d`
**Status:** fixed
**Applied fix:** Fence title and dek as untrusted data (`<<<UNTRUSTED_TITLE_*>>>`, `<<<UNTRUSTED_DEK_*>>>`) like the transcript. Strip all fence marker tokens from title, dek, and transcript before wrapping so a forged closer cannot escape. Tests pin a jailbreak-like title and a transcript containing the END marker: payload appears only inside fences, markers stripped from the inner text.

---

_Fixed: 2026-10-30T02:57:36Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
