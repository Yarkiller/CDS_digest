---
phase: 29-pass-1-richer-templates
reviewed: 2026-10-30T03:45:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - data-collection/src/data_collection/adapters/deepseek_article.py
  - data-collection/src/data_collection/templates/lecture.md
  - data-collection/src/data_collection/templates/podcast.md
  - tests/unit/test_article_draft_body_audience.py
  - tests/unit/test_article_templates.py
  - tests/unit/test_deepseek_article_adapter.py
  - tests/unit/test_markdown_sections.js
  - tests/web-app.spec.js
  - web/src/pages/MaterialPage.jsx
  - web/src/utils/markdownSections.js
findings:
  critical: 0
  warning: 6
  info: 5
  total: 11
status: issues_found
---

# Phase 29: Code Review Report

**Reviewed:** 2026-10-30T03:45:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Pass-1 templates and `ARTICLE_SYSTEM_PROMPT` drop the three-block scaffolds and keep optional `## Конкретика` / `## Зачем это СВА`. The reader paints one muted body frame with nested cards for those two headings. Markdown still goes through `rehype-sanitize`; roles still normalize; `## Аудитория` is stripped on `ArticleDraft`. No secrets, XSS, or ingest crash in this slice. The new line-based splitter and per-band `react-markdown` trees break contracts this same phase added (fenced `##`, reserved-heading chrome, TOC ids, footnotes), and `podcast.md` contradicts D-05.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `splitMaterialSections` splits on ATX headings inside fenced code

**File:** `web/src/utils/markdownSections.js:22-60`
**Issue:** `headingText` treats every line that starts with `## ` as a section boundary. It does not track ` ``` ` fences. `extractMarkdownHeadings` (`web/src/utils/markdownToc.js:54-59`) skips fenced lines, so TOC and the reader now disagree. A DS lecture that shows a markdown/shell sample containing `## Configuration` or `## Конкретика` will flush the current band at the fence line: the opening fence stays in one tree, the closing fence in another. `react-markdown` then treats the rest of that band as code, and a false `concretika` card can appear (or a real one disappear). Unit tests never feed a fenced `##`.
**Fix:** Mirror the TOC fence toggle:

```javascript
export function splitMaterialSections(markdown) {
  if (markdown == null) return []
  const lines = String(markdown).split('\n')
  const sections = []
  let heading = null
  let buf = []
  let inFence = false

  const flush = () => {
    const text = buf.join('\n')
    buf = []
    if (!heading && !text.trim()) return
    sections.push({ heading, kind: kindForHeading(heading), markdown: text })
  }

  for (const line of lines) {
    if (/^```/.test(line)) inFence = !inFence
    const next = inFence ? null : headingText(line)
    if (next !== null) {
      flush()
      heading = next
      buf = [line]
      continue
    }
    buf.push(line)
  }
  flush()
  return sections
}
```

Pin it in `tests/unit/test_markdown_sections.js` with `## Конкретика` inside a fence; the outer article must stay one `topic`/`body` band.

### WR-02: reserved-heading chrome matches only the exact heading string

**File:** `web/src/utils/markdownSections.js:11-16`
**Issue:** `kindForHeading` is `heading === 'Конкретика'` / `'Зачем это СВА'`. The same templates tell the model to mark theses in `**bold**` (`lecture.md:8`, `podcast.md:9`). A leaked `## **Конкретика**`, `## Конкретика.`, or `## Зачем это СВА?` becomes `kind: 'topic'`, merges into the body band, and never gets a card. Playwright only sees the canonical strings on the `rag-systems` fixture, so this chrome — the reason `MaterialPage` was rewritten — can fail on a live draft without redding the suite.
**Fix:** Normalize before the compare, and pin the decorated heading:

```javascript
function kindForHeading(heading) {
  if (!heading) return 'lead'
  const normalized = heading.replace(/[*_`]/g, '').replace(/[.:?!]+$/g, '').trim()
  if (normalized === 'Зачем это СВА') return 'sva'
  if (normalized === 'Конкретика') return 'concretika'
  return 'topic'
}
```

Add `splitMaterialSections('## **Конкретика**\n\n- **784** — pixels.')` → `kind: 'concretika'`.

### WR-03: `podcast.md` orders the model to cut by speaker and by topic at once

**File:** `data-collection/src/data_collection/templates/podcast.md:4-7`
**Issue:** D-05 is one discriminator: dialogue → sections by position/speaker; otherwise → by topic. The file states all three at once:

- line 4: dialogue → speaker; not a dialogue → topics (correct);
- line 5: **every** level-2 heading is named «after a real topic of the conversation»;
- line 7: **always** «Structure the conversation by positions of its participants».

For a dialogue, lines 4 and 5 conflict. For a monologue episode, lines 4 and 7 conflict. Tests pin the kind sentinel `positions of its participants`, so line 7 is not dead text — it is an unconditional command that cancels the «when it is not a dialogue» branch. Podcast ART-01 heading shape becomes lottery.
**Fix:** Keep the sentinel, fold the discriminator into one bullet, drop the absolute line 7:

```markdown
- When the episode is a dialogue, name every level-2 section after a position or a speaker and let the section carry that participant's argument (structure the conversation by positions of its participants); when it is not a dialogue, follow the topics of the conversation.
- Name every level-2 section after a real topic or speaker turn, with no fixed count and no padding; do not merge unrelated topics.
```

Extend `test_podcast_md_names_the_dialogue_frame` so both «when it is not a dialogue» and «positions of its participants» are present, and the bare sentence «Structure the conversation by positions of its participants» is not.

### WR-04: each band is its own Markdown tree — footnotes and TOC ids diverge

**File:** `web/src/pages/MaterialPage.jsx:20-26,260-279`
**Issue:** `bodyBands.map` mounts a fresh `<ArticleMarkdown>` per band. `remark-gfm` footnote counters and `rehype-slug` ids are **per tree**. This phase told the model it may add «short footnotes» (`lecture.md:2`, `podcast.md:2`, `ARTICLE_SYSTEM_PROMPT` lines 38 and 46). A typical `текст[^1]` in a topic and `[^1]: …` after `## Зачем это СВА` land in different trees — the reference never resolves. Duplicate heading text on either side of `## Конкретика` both get unsuffixed `user-content-…` in the DOM, while `extractMarkdownHeadings` suffixes globally (`введение-1`). The TOC link for the second heading goes nowhere (or to the first). Before this split, one tree kept those counters aligned.
**Fix:** Do not parse twice. Prefer one `ArticleMarkdown` on the full `body_markdown` and wrap already-rendered `h2` nodes with CSS, or rejoin bands with sanitizer-safe markers. Until parse is one tree, forbid GFM endnotes in the prompt:

```text
short parenthetical footnotes in the sentence («Редакционное примечание: …»), not [^n] endnotes
```

Pin TOC: two `## Введение` around `## Конкретика` → the second TOC `href` equals the second `h2` `id`.

### WR-05: system prompt skips the editorial label and pushes a invented speaker name

**File:** `data-collection/src/data_collection/adapters/deepseek_article.py:35-50`
**Issue:** D-18: added context must not be presented as the speaker's words; names must not be invented. The user templates require «mark it as editorial» (`lecture.md:17`, `podcast.md:18`). The stronger system prompt only says «never present it as the speaker's words» and «attribute a claim to the speaker by name instead («Элен считает…»)». If the transcript has no name, the «Элен» example is a direct invitation to invent one — against «Do not invent names». Definitions without a visible editorial label read as the speaker. Live Attempt 4 happened to emit `*Редакционное примечание:*`; that is luck, not a contract.
**Fix:** Append to `ARTICLE_SYSTEM_PROMPT` and pin in `test_system_prompt_carries_the_edition_voice_and_length_rules`:

```python
"If the speaker's name is absent from the transcript, attribute as «докладчик» or «ведущий» — never invent a name.\n"
"Mark every added definition, footnote or reference note as editorial («Редакционное примечание»), never as the speaker's words.\n"
```

### WR-06: empty `## Конкретика` / `## Зачем это СВА` still become cards

**File:** `web/src/pages/MaterialPage.jsx:261-273` · `web/src/utils/markdownSections.js:38-46`
**Issue:** D-08 / ART-02: no empty placeholder heading. Templates say «Omit the section entirely». `flush` still pushes a section whenever `heading` is set, even when the only line is `## Конкретика`. `MaterialPage` then wraps every `concretika`/`sva` band in a card. One hallucinated heading with no facts produces the empty frame the owner already rejected. The splitter has no «heading with no body» path; Playwright never asserts the omit case.
**Fix:** Drop reserved bands whose body after the heading line is blank:

```javascript
function bandHasBody(section) {
  return section.markdown.split('\n').slice(1).some((l) => l.trim())
}

export function groupMaterialBands(sections) {
  const bands = []
  for (const section of sections) {
    if (section.kind === 'concretika' || section.kind === 'sva') {
      if (!bandHasBody(section)) continue
      bands.push({ kind: section.kind, heading: section.heading, markdown: section.markdown })
      continue
    }
    // ...existing body merge...
  }
  return bands
}
```

Pin: `## Конкретика\n\n## Оценка` → no `concretika` band; trailing topic still renders.

## Info

### IN-01: `test_assembled_user_message_omits_guide_heading` asserts a test constant against itself

**File:** `tests/unit/test_deepseek_article_adapter.py:163-172`
**Issue:** `assert SHARED_PROMPT_HEADINGS == ("## Конкретика", "## Зачем это СВА", "## Аудитория")` compares the module literal to the same tuple. A user-message regression that drops one of those headings still passes this second assert. Only `"Гайд" not in _user_content(...)` is live.
**Fix:** Delete the constant equality. Keep the Гайд absence pin; if the shared frame must be locked here, `assert heading in _user_content(kind, language)` for each shared heading.

### IN-02: Конкретика / СВА / Аудитория tails are copy-pasted with no equality pin

**File:** `data-collection/src/data_collection/templates/lecture.md:11-30` · `podcast.md:12-30`
**Issue:** Plan 02 wants those blocks verbatim. Phrase-level tests on each file will stay green if one file drifts (an extra «always include» sentence, a renamed analog). Kind sentinels are tested for isolation; the shared tail is not tested for identity.
**Fix:** In `test_kind_sentinels_do_not_cross` (or a sibling), slice each file from `## Конкретика` through `## Аудитория` and `assert lecture_tail == podcast_tail`.

### IN-03: splitter unit tests cover only the happy path with both reserved headings

**File:** `tests/unit/test_markdown_sections.js:8-113`
**Issue:** No `splitMaterialSections(null)`, no article without Конкретика/СВА, no heading-only `## Конкретика`, no fenced `##`. WR-01 / WR-02 / WR-06 stay green on this file.
**Fix:** Add those four cases next to the existing `describe` blocks.

### IN-04: Playwright only asserts that both cards exist on `rag-systems`

**File:** `tests/web-app.spec.js:43-87`
**Issue:** The new test locks «Конкретика and Зачем это СВА are visible and nested». The phase contract is that both sections are optional. A fixture without those `##` never asserts `material-section-concretika` / `material-section-sva` count 0, so a regression that always paints empty cards would not fail on this spec. The `material-section` intro-card negative is also vacuous: that testid is gone, so a per-topic card under a new testid would still pass.
**Fix:** Drive a heading-only fixture (or `empty-dek-article` if its body has no reserved `##`) and `expect(concretika).toHaveCount(0)` / `expect(sva).toHaveCount(0)` while `material-section-body` stays visible.

### IN-05: `headingText` has an unreachable `startsWith('###')` guard

**File:** `web/src/utils/markdownSections.js:22-24`
**Issue:** `'### foo'.startsWith('## ')` is already false (`## ` is hash-hash-**space**). Nested `###` stay in the parent because they fail the `## ` prefix, not because of the `###` check. The extra clause cannot fire for any string that passed the first test. Nested headings still work; the guard is dead and suggests the author thought `###` matches `## `.
**Fix:** Drop `|| line.startsWith('###')`. Keep a comment that `###`/`####` do not start with `'## '`, so they remain in `buf`.

---

_Reviewed: 2026-10-30T03:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
