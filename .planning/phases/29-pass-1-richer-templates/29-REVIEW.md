---
phase: 29-pass-1-richer-templates
reviewed: 2026-10-30T03:26:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - data-collection/src/data_collection/templates/lecture.md
  - data-collection/src/data_collection/adapters/deepseek_article.py
  - tests/unit/test_article_templates.py
  - tests/unit/test_deepseek_article_adapter.py
  - data-collection/src/data_collection/templates/podcast.md
  - tests/unit/test_article_draft_body_audience.py
  - web/src/pages/MaterialPage.jsx
  - web/src/utils/markdownSections.js
  - tests/unit/test_markdown_sections.js
  - tests/web-app.spec.js
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 29: Code Review Report

**Reviewed:** 2026-10-30T03:26:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Pass-1 шаблоны и `ARTICLE_SYSTEM_PROMPT` действительно убрали трёхблочный каркас и держат опциональные `## Конкретика` / `## Зачем это СВА`, а ридер рисует одну рамку тела с вложенными карточками. Критических дыр (секреты, XSS, потеря данных, падение ingest) нет: markdown идёт через `rehype-sanitize`, роли по-прежнему нормализуются, `## Аудитория` снимается в DTO. Но новый сплиттер секций и нарезка тела на несколько деревьев `react-markdown` ломают несколько контрактов, которые эта же фаза добавила (сноски, точные карточки, TOC), а `podcast.md` internally противоречит D-05.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `splitMaterialSections` режет ATX-заголовки внутри fenced-блоков

**File:** `web/src/utils/markdownSections.js:22-60`
**Issue:** `headingText` смотрит каждую строку, начинающуюся с `## `, без учёта ` ``` `. TOC (`markdownToc.js:54-59`) fenced-блоки пропускает. Статья с примером markdown/shell, где внутри fence есть `## Configuration` или случайно `## Конкретика`, будет разрезана: открывающий fence останется в одном band, закрывающий — в другом. `react-markdown` в первом band проглотит хвост как код; карточка «Конкретика» может появиться ложно или исчезнуть. Юнит-тесты этот случай не покрывают.
**Fix:** Скопировать fence-aware обход из `extractMarkdownHeadings`:

```javascript
export function splitMaterialSections(markdown) {
  if (markdown == null) return []
  const lines = String(markdown).split('\n')
  const sections = []
  let heading = null
  let buf = []
  let inFence = false

  const flush = () => { /* без изменений */ }

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

Добавить кейс в `tests/unit/test_markdown_sections.js` с `## Конкретика` внутри ` ``` `.

### WR-02: вид секции матчится только точной строкой заголовка

**File:** `web/src/utils/markdownSections.js:11-16`
**Issue:** `kindForHeading` сравнивает `heading === 'Конкретика'` / `'Зачем это СВА'`. Модель по инструкции «Mark key theses in **bold**» часто пишет `## **Конкретика**`, `## Конкретика.`, `## Зачем это СВА?`. Тогда секция уходит в `topic`, сливается в body-band и **не получает** карточку. Playwright на фикстуре `rag-systems` это не ловит: там заголовки уже канонические. Live Attempt 4 тоже совпал буквально — дефект латентный, но ломает именно chrome, ради которого переписывали `MaterialPage`.
**Fix:** Нормализовать текст заголовка перед сравнением:

```javascript
function kindForHeading(heading) {
  if (!heading) return 'lead'
  const normalized = heading.replace(/[*_`]/g, '').replace(/[.:?!]+$/g, '').trim()
  if (normalized === 'Зачем это СВА') return 'sva'
  if (normalized === 'Конкретика') return 'concretika'
  return 'topic'
}
```

И пин в `test_markdown_sections.js` на `## **Конкретика**`.

### WR-03: `podcast.md` одновременно требует секции «по спикерам» и «по темам»

**File:** `data-collection/src/data_collection/templates/podcast.md:4-7`
**Issue:** D-05: диалог → секции по позициям/спикерам; иначе → по темам. Файл говорит всё сразу:

- строка 4: диалог → по спикеру; не диалог → по темам (верно);
- строка 5: **каждую** `##` называть «after a real topic of the conversation»;
- строка 7: **всегда** «Structure the conversation by positions of its participants».

Для диалога строки 4 и 5 конфликтуют; для монолога — 4 и 7. Kind-sentinel `positions of its participants` закреплён тестами, поэтому строку 7 нельзя просто выкинуть как «случайную», но как абсолютная команда она отменяет ветку «when it is not a dialogue». Итог — нестабильная нарезка подкастов (ART-01).
**Fix:** Оставить дискриминатор в одном буллете, sentinel не трогать:

```markdown
- When the episode is a dialogue, name every level-2 section after a position or a speaker and let the section carry that participant's argument (structure the conversation by positions of its participants); when it is not a dialogue, follow the topics of the conversation.
- Name every level-2 section after a real topic or speaker turn, with no fixed count and no padding; do not merge unrelated topics.
```

Удалить отдельную строку 7. Добавить пин в `test_podcast_md_names_the_dialogue_frame`, что «when it is not a dialogue» и «positions of its participants» оба присутствуют, и нет безусловного «Structure the conversation by positions» без ветки.

### WR-04: каждый band — отдельное дерево Markdown: ломаются сноски и TOC-якоря

**File:** `web/src/pages/MaterialPage.jsx:20-26,260-279`
**Issue:** `bodyBands.map` рендерит отдельный `<Markdown>` на band. `remark-gfm` сноски и `rehype-slug` считают счётчики **внутри дерева**. Эта фаза явно разрешила «short footnotes» (`lecture.md:2`, `ARTICLE_SYSTEM_PROMPT:38,46`). Типичный `текст[^1]` в топике и `[^1]: …` в конце статьи (после `## Зачем это СВА`) попадают в разные деревья — ссылка не резолвится. Дубли заголовков по разные стороны `## Конкретика` получают одинаковый `user-content-…` в DOM, тогда как `extractMarkdownHeadings` нумерует глобально (`введение-1`) — пункт TOC ведёт в никуда.
**Fix:** Не резать parse. Один `ArticleMarkdown` на весь `body_markdown`, а карточки вешать CSS-ом (обёртка вокруг уже распарсенных `h2`), либо склеивать bands обратно в один markdown с HTML-маркерами, которые sanitizer сохранит. Минимум — не обещать GFM-footnotes в промпте, пока parse один:

```text
# в lecture.md / podcast.md / ARTICLE_SYSTEM_PROMPT
short parenthetical footnotes in the sentence (Редакционное примечание: …), not [^n] endnotes
```

И пин TOC: два одинаковых `## Введение` вокруг `## Конкретика` → `href` второго линка совпадает с `id` второго `h2`.

### WR-05: system prompt не требует маркировки редактуры и провоцирует выдуманное имя спикера

**File:** `data-collection/src/data_collection/adapters/deepseek_article.py:35-50`
**Issue:** D-18: добавленный контекст нельзя выдавать за слова спикера; имена не выдумывать. User-шаблон просит «mark it as editorial» (`lecture.md:17`, `podcast.md:18`). System prompt — более сильный сигнал — говорит только «never present it as the speaker's words» и «attribute a claim to the speaker by name instead («Элен считает…»)». Если в транскрипте нет имени, пример «Элен» толкает модель выдумать его (прямо против «Do not invent names»). Редакционные определения без ярлыка читаются как речь спикера. Live Attempt 4 как раз пометил `*Редакционное примечание:*` — это удача модели, не контракт промпта.
**Fix:** Добавить в `ARTICLE_SYSTEM_PROMPT` и закрепить `test_system_prompt_carries_the_edition_voice_and_length_rules`:

```python
"If the speaker's name is absent from the transcript, attribute as «докладчик» or «ведущий» — never invent a name.\n"
"Mark every added definition, footnote or reference note as editorial («Редакционное примечание»), never as the speaker's words.\n"
```

### WR-06: пустые `## Конкретика` / `## Зачем это СВА` всё равно рисуются карточками

**File:** `web/src/pages/MaterialPage.jsx:261-273` · `web/src/utils/markdownSections.js:38-46`
**Issue:** D-08 / ART-02: пустого заголовка-заглушки быть не должно; шаблон говорит «Omit the section entirely». Сплиттер пушит секцию, если есть heading, даже когда тело — только строка `## Конкретика`. Ридер безусловно оборачивает `kind === 'concretika'|'sva'` в карточку. Промпт это не сторожит на клиенте: одна галлюцинация заголовка без фактов даёт пустую рамку, которую владелец уже отверг на Attempt 3.
**Fix:** Не выпускать band, у которого после heading-строки нет текста:

```javascript
function bandHasBody(section) {
  const lines = section.markdown.split('\n')
  return lines.slice(1).some((l) => l.trim())
}
```

В `groupMaterialBands` пропускать `concretika`/`sva` без тела (или схлопывать в соседний body, если так проще для TOC). Пин: `## Конкретика\n\n## Оценка` → нет band `concretika`.

## Info

### IN-01: второй assert в `test_assembled_user_message_omits_guide_heading` проверяет константу теста, не промпт

**File:** `tests/unit/test_deepseek_article_adapter.py:163-172`
**Issue:** `assert SHARED_PROMPT_HEADINGS == ("## Конкретика", …)` сравнивает литерал с самим собой. Регрессия содержимого user-message от этого не покраснеет.
**Fix:** Убрать равенство константы; оставить `"Гайд" not in _user_content(...)` и при необходимости `assert heading in _user_content(kind, language)` по каждому SHARED heading.

### IN-02: блоки Конкретика/СВА скопированы в двух файлах без общего фрагмента

**File:** `data-collection/src/data_collection/templates/lecture.md:11-25` · `podcast.md:12-26`
**Issue:** Plan 02 требует verbatim copy. Тесты пинят отдельные фразы, не равенство блоков. Расхождение промпта lecture vs podcast тесты не поймают.
**Fix:** В `test_kind_sentinels_do_not_cross` (или рядом) вырезать текст от `## Конкретика` до `## Аудитория` из обоих файлов и `assert lecture_tail == podcast_tail`.

### IN-03: юнит-тесты сплиттера не покрывают null, fence, omit, пустую карточку

**File:** `tests/unit/test_markdown_sections.js:8-113`
**Issue:** Есть happy-path с обоими спецзаголовками. Нет `splitMaterialSections(null)`, статьи без Конкретика/СВА, пустого `## Конкретика`, заголовка в fence. WR-01/WR-02/WR-06 из-за этого зелёные.
**Fix:** Добавить четыре кейса рядом с существующими `describe`.

### IN-04: Playwright всегда требует обе карточки на `rag-systems`

**File:** `tests/web-app.spec.js:43-87`
**Issue:** Тест фиксирует «есть Конкретика и СВА». Обратный контракт фазы (обе секции опциональны, карточек нет) на фикстуре без этих `##` не проверяется. Регрессия «всегда рисуем пустые карточки» на rag-systems не всплывёт.
**Fix:** Отдельный mock/материал без этих заголовков и `expect(concretika).toHaveCount(0)` / `expect(sva).toHaveCount(0)` при видимом `material-section-body`.

---

_Reviewed: 2026-10-30T03:26:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
