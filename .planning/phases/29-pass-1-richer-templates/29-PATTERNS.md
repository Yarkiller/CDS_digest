# Phase 29: Pass-1 richer templates - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 7 (2 prompt files + 3 test modules + 1 prompt constant + 1 evidence artifact)
**Analogs found:** 6 / 7 exact-or-role matches (evidence artifact: partial)

> This phase has **no new module, port, adapter or wiring**. Every production file is a
> rewrite of an existing file, so the dominant analog is *the file itself* plus its sibling.
> The one genuinely new thing is **test prose**: six legacy heading literals move from
> "assert present" to "assert absent", and new frame strings get pinned. Patterns below are
> written so plan actions can copy an existing helper, an existing assertion shape, or an
> existing template tail verbatim.
>
> **Tracked-source gate:** all six code files below were verified git-tracked with
> `git ls-files -- <path>` (non-empty output). No gitignored mirror path is emitted.
>
> **No `conftest.py` exists anywhere in the repo** (glob for `conftest.py` under `tests/`
> returns nothing), so every test module declares its own helper functions and module-level
> constants. New assertions must follow that, not look for a fixture.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `data-collection/src/data_collection/templates/lecture.md` (REWRITE) | prompt template (package markdown data) | transform (instruction text consumed by `build_article_messages`) | itself + `templates/podcast.md` (shared tail, honesty line) | exact (self) |
| `data-collection/src/data_collection/templates/podcast.md` (REWRITE) | prompt template (package markdown data) | transform | itself + `templates/lecture.md` | exact (self) |
| `data-collection/src/data_collection/adapters/deepseek_article.py` (MODIFIED — `ARTICLE_SYSTEM_PROMPT` string only) | adapter / prompt constant | request-response (message assembly) | itself: `ARTICLE_SYSTEM_PROMPT` (35-43) | exact (self) |
| `tests/unit/test_article_templates.py` (MODIFIED — 3 pins inverted, +new frame/optional-clause pins) | test (unit, package data) | file-I/O → string assertions | itself: `:13-36`; `tmp_path` loader cases `:39-51` | exact (self) |
| `tests/unit/test_deepseek_article_adapter.py` (MODIFIED — 2 prompt-isolation tests rewritten, system-prompt pins extended) | test (unit, adapter contract) | request-response capture via stub client | itself: `_stub_client` `:24-44`, `_make_transcript` `:47-48`, `_make_generator` `:279-290` | exact (self) |
| `tests/unit/test_article_draft_body_audience.py` (MODIFIED — +1 case) | test (unit, DTO normalisation) | transform (regex strip) | itself: `_draft()` `:17-23`, strip case `:26-33` | exact (self) |
| `.planning/phases/29-pass-1-richer-templates/evidence/*` + UAT checklist (CREATED, not code) | evidence / manual UAT | batch (one live ingest + digit audit) | `.planning/milestones/v1.4-phases/28-live-proof-streamed-deepseek-ingest/evidence/ingest-run-1.log`, `28-UAT.md`, `28-01-SUMMARY.md:85-94` | partial (different phase dir, same shape) |

**Directory placement check:** all three test modules already exist in `tests/unit/`
(`testpaths = ["tests/unit"]`, `pythonpath = ["."]` — `pyproject.toml:35-40`). Do **not**
create new test files, do **not** add a `tests/unit/conftest.py`.

---

## Pattern Assignments

### `data-collection/src/data_collection/templates/lecture.md` (prompt template, transform)

**Analog:** itself. The current file is the whole surface — 16 lines, level-2 headings only,
English instruction lines under each heading, one trailing Russian scaffolding block.

Current content (the file being replaced — the *tail* is preserved, the three body blocks are not):

```1:16:data-collection/src/data_collection/templates/lecture.md
## Тезис

Summarize the core thesis of the transcript in one clear sentence.

## Ход рассуждения

Reconstruct the main argument, evidence, and reasoning from the transcript.
Do not invent facts, names, or numbers that are not in the transcript.

## Вывод

State the key takeaway for a СВА reader.

## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
```

**Structural invariants to preserve (mechanical, read by production code/tests):**

| Invariant | Why it is not optional |
|-----------|------------------------|
| No `# ` H1 anywhere | `MaterialPage` renders `material.title` as the page `h1` and `extractMarkdownHeadings` includes level 1 (`web/src/utils/markdownToc.js:47-76`) — an H1 duplicates the title and pollutes the TOC. |
| The **last heading** is exactly `## Аудитория` and the last line is the role instruction | `strip_audience_section` walks from that heading to the next h1/h2 (`dto/_body.py:17-41`); anything appended after it leaks the scaffolding into the reader body (research Pitfall 3). |
| The honesty line `Do not invent facts, names, or numbers that are not in the transcript.` stays in the file (it is currently line 8 of both templates) | ART-02/D-18: the facts layer is the most exposed surface to invented numbers. The same rule is *also* pinned in the system prompt, so this copy may be reworded but not dropped. |
| No URL/link instruction, no colour/HTML promise | Phase 32/33 own links; `rehype-sanitize` strips style attributes (research Anti-Patterns, Pitfall 4). |
| **None** of `## Тезис` / `## Ход рассуждения` / `## Вывод` may appear — not even inside a prohibition | `test_deepseek_article_adapter.py:150` asserts `"## Тезис" not in user_content`; a negation would make the pin unsatisfiable and raises emission probability (research Pitfall 1). |

**Target shape to copy (positive frame — field-tested wording is Claude's discretion per CONTEXT):**

```markdown
Write a Russian longread for СВА readers from the transcript below.
Use only what the transcript says; do not add facts, names, numbers, tools, or versions that are not in it.
Aim for 1 200-1 800 words; do not pad to fill space.

## Structure

- Name every level-2 section after a real topic of the talk. The number of sections is
  whatever the talk actually contains; do not pad and do not merge unrelated topics.
- When the talk has no named chapters, split it into the implicit editorial chapters an
  experienced editor would write, and name each by its topic in the speaker's own terms.
- Structure the article as a single speaker's argument: sections follow the topics of the talk.
- Mark key theses in **bold**. Give a memorable direct statement as a markdown blockquote.
- Do not open with a level-1 heading; the title is a separate field.

## Конкретика

Add this section only when the transcript carries concrete names, numbers, tools or caveats
worth keeping. Prefer bullets: `**item** — the caveat the speaker gave`. A table is allowed
only when the talk itself presents a grid of numbers. Spell tool names canonically
(PostgreSQL, not «постгрес»); never invent a version. Omit the section entirely when there is
nothing concrete — no placeholder, no apology.

## Зачем это СВА

Add this section only when the talk has a working analog for СВА — control, data, model,
vendor, information security, process quality — even if the speaker never said «аудит».
Write one editorial paragraph in the edition's voice («Для СВА это значит…»). Do not invent a
duty, an internal standard or a number, and do not present editorial inference as the
speaker's claim. Omit the section when there is no such analog.

## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
```

**Kind-hint discriminator (the only paragraph that differs between the two templates).**
The cross-kind test must be able to tell the templates apart, so the discriminator has to be a
**multi-word literal unique to one file**. Do not use single common words (`speaker`, `topic`,
`section`) — the shared frame above contains them, so an absence assertion would be
unsatisfiable:

- lecture sentinel (as in the block above): `single speaker's argument`
- podcast sentinel: `positions of its participants`

Pin exactly these two phrases (present in its own file / absent from the sibling), and pick
them **before** writing the templates so the paragraph wording and the test agree.

---

### `data-collection/src/data_collection/templates/podcast.md` (prompt template, transform)

**Analog:** itself + `lecture.md`. Same invariants, same tail, one different Structure paragraph.

Current content:

```1:16:data-collection/src/data_collection/templates/podcast.md
## О чём разговор

Summarize the topic and main discussion of the transcript in one clear sentence.

## Позиции

Outline the positions, arguments, or speakers' points from the transcript.
Do not invent facts, names, or numbers that are not in the transcript.

## Что запомнить

State the key takeaways for a СВА reader.

## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
```

**Shared tail — copy verbatim from the sibling** (the same four lines end both files today; the
strip contract depends on the heading spelling and on it being last):

```14:16:data-collection/src/data_collection/templates/lecture.md
## Аудитория

Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
```

**Kind hint (D-05):** dialogue → sections by positions/speakers; otherwise → by topic. Example
paragraph to use instead of the lecture's Structure bullet:

```markdown
## Structure

- When the episode is a dialogue, name every level-2 section after a position or a speaker
  and let the section carry that participant's argument; when it is not a dialogue, follow
  the topics of the conversation.
- Name every level-2 section after a real topic of the conversation. The number of sections
  is whatever the episode contains; do not pad and do not merge unrelated topics.
- Structure the conversation by positions of its participants.
- Mark key theses in **bold**. Give a memorable direct statement as a markdown blockquote.
- Do not open with a level-1 heading; the title is a separate field.
```

Retain the honesty line, the `## Конкретика` clause (with the *same heading string* as the
lecture so Phase 32 can freeze one literal — D-06), the `## Зачем это СВА` clause, and the
trailing `## Аудитория` block. Forbidden in this file: `## О чём разговор`, `## Позиции`,
`## Что запомнить`.

---

### `data-collection/src/data_collection/adapters/deepseek_article.py` (adapter, request-response)

**Analog:** itself, lines 35-43. The change is **additive wording inside one string literal**.
`build_article_messages` (46-62), `process` (91-122), `_stream_content` (124-184) and the
completion kwargs (131-138) must stay byte-identical — the call shape is a locked surface.

```35:43:data-collection/src/data_collection/adapters/deepseek_article.py
ARTICLE_SYSTEM_PROMPT = (
    "You are an editorial assistant preparing articles for СВА (Служба внутреннего аудита).\n"
    "Use only the transcript below. Do not invent facts, names, or numbers.\n"
    "Output is always Russian.\n"
    "If the transcript language is ru: format only; do not translate.\n"
    "If the transcript language is en: translate into Russian.\n"
    "Preserve technical terms, proper names, library names, numbers, and units as written.\n"
    "Return one json object with keys title, dek, body_markdown, roles."
)
```

**Invariants:** ten substrings in this literal are pinned by
`test_system_prompt_contains_honesty_and_language_rules` (`tests/unit/test_deepseek_article_adapter.py:171-180`):
`Use only the transcript`, `Do not invent facts, names, or numbers`, `Output is always Russian`,
both language lines, `Preserve technical terms…`, `json`, `title`, `dek`, `body_markdown`.
Add new lines; do not reflow or shorten the existing seven. Keep the word `json` and the key
list exactly where they are (DeepSeek returns HTTP 400 for `json_object` without an explicit
JSON instruction, and the JSON contract sentence is also the empty-content mitigation — research
Pitfalls 5).

**New shared rules to add here (D-03 / D-15 / D-16 — cross-cutting, so *not* duplicated in the
two templates):**

```python
ARTICLE_SYSTEM_PROMPT = (
    # ... the existing seven lines unchanged ...
    "Write in the voice of the edition: state the substance, do not report the container. "
    "Never write «в подкасте рассказывается», «монолог содержит» or «в ролике говорится»; "
    "attribute a claim to the speaker by name instead («Элен считает…»).\n"
    "Editorial inference is allowed only in the closing section about СВА. "
    "Never present it as the speaker's words and never invent a duty, a standard or a number.\n"
    # ... "Return one json object with keys ..." last, unchanged ...
)
```

Two consequences for the tests, both deliberate:

1. The Russian recap phrases are **style** prohibitions with examples — allowed in the shared
   prompt (research Pattern 1). They are *not* heading literals, so no absence pin conflicts.
2. If the output-length band ("1 200-1 800 words") lives here instead of in each template, pin
   it here; if it lives in the templates, pin it in `test_article_templates.py`. Pick one home
   and pin there — do not pin both (KISS, and the templates should differ by one paragraph only).

---

### `tests/unit/test_article_templates.py` (test, file-I/O → string assertions)

**Analog:** itself. Keep the module docstring convention (requirement IDs + decision IDs),
keep the two `load_article_templates` behaviours that already exist, and **reuse the negative
pin instead of deleting it**.

Existing pins that must flip:

```13:36:tests/unit/test_article_templates.py
def test_lecture_md_contains_russian_headings() -> None:
    root = importlib.resources.files("data_collection.templates")
    text = root.joinpath("lecture.md").read_text(encoding="utf-8")
    assert "## Тезис" in text
    assert "## Ход рассуждения" in text
    assert "## Вывод" in text


def test_podcast_md_contains_russian_headings() -> None:
    root = importlib.resources.files("data_collection.templates")
    text = root.joinpath("podcast.md").read_text(encoding="utf-8")
    assert "## О чём разговор" in text
    assert "## Позиции" in text
    assert "## Что запомнить" in text


def test_load_article_templates_returns_both_kinds() -> None:
    from data_collection.templates import load_article_templates

    root = importlib.resources.files("data_collection.templates")
    templates = load_article_templates(root)
    assert set(templates.keys()) == set(TemplateKind)
    assert "## Тезис" in templates[TemplateKind.LECTURE]
    assert "## О чём разговор" in templates[TemplateKind.PODCAST]
```

**Style rules to copy from this file:** one behaviour per test, `-> None` annotations,
`from __future__ import annotations`, production imports **inside** the test body (the module
top only imports `importlib.resources`, `pathlib.Path`, `pytest`, `TemplateKind`), plain
`assert`, and no fixtures beyond `tmp_path`. `pytest.mark.parametrize` is the house way to
express a set of strings (`tests/unit/test_data_collection_public_api.py:87`).

**Target test set (names and assertion shape — the executor copies this structure):**

```python
"""RED→GREEN: pass-1 templates carry the content-shaped frame (ART-01/ART-02/ART-03, D-01…D-18)."""

LEGACY_LECTURE_HEADINGS = ("## Тезис", "## Ход рассуждения", "## Вывод")
LEGACY_PODCAST_HEADINGS = ("## О чём разговор", "## Позиции", "## Что запомнить")
SHARED_HEADINGS = ("## Конкретика", "## Зачем это СВА", "## Аудитория")


def _template_text(kind: str) -> str:
    root = importlib.resources.files("data_collection.templates")
    return root.joinpath(f"{kind}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("heading", LEGACY_LECTURE_HEADINGS)
def test_lecture_md_omits_legacy_scaffold(heading: str) -> None:
    assert heading not in _template_text("lecture")


@pytest.mark.parametrize("heading", LEGACY_PODCAST_HEADINGS)
def test_podcast_md_omits_legacy_scaffold(heading: str) -> None:
    assert heading not in _template_text("podcast")


@pytest.mark.parametrize("heading", SHARED_HEADINGS)
def test_both_templates_carry_the_shared_frame(heading: str) -> None:
    assert heading in _template_text("lecture")
    assert heading in _template_text("podcast")


def test_lecture_md_names_the_topics_frame() -> None:
    text = _template_text("lecture")
    assert "single speaker's argument" in text          # kind sentinel, lecture only
    assert "implicit editorial chapters" in text        # D-02
    assert "do not add facts" in text                   # honesty (D-18)


def test_podcast_md_names_the_dialogue_frame() -> None:
    text = _template_text("podcast")
    assert "positions of its participants" in text      # kind sentinel, podcast only
    assert "implicit editorial chapters" in text


def test_kind_sentinels_do_not_cross() -> None:
    assert "positions of its participants" not in _template_text("lecture")
    assert "single speaker's argument" not in _template_text("podcast")


def test_concretika_clause_states_its_own_omission_rule() -> None:
    for kind in ("lecture", "podcast"):
        text = _template_text(kind)
        assert "Omit the section entirely" in text      # D-08, prompt-only rule


def test_sva_clause_states_the_analog_bar_and_the_omission_rule() -> None:
    for kind in ("lecture", "podcast"):
        text = _template_text(kind)
        assert "working analog for СВА" in text         # D-12
        assert "information security" in text           # D-12 analog family


def test_audience_block_is_the_last_heading_in_both_templates() -> None:
    for kind in ("lecture", "podcast"):
        text = _template_text(kind)
        headings = [line for line in text.splitlines() if line.startswith("#")]
        assert headings[-1] == "## Аудитория"
        assert text.rstrip().endswith("employee, analyst, ds.")


def test_neither_template_opens_an_h1() -> None:
    for kind in ("lecture", "podcast"):
        assert not any(line.startswith("# ") for line in _template_text(kind).splitlines())
```

`test_load_article_templates_returns_both_kinds` keeps its `TemplateKind` set assertion and
swaps its two content assertions to shared frame strings (`"## Конкретика" in
templates[TemplateKind.LECTURE]`, `"## Зачем это СВА" in templates[TemplateKind.PODCAST]`).

**Leave alone:** `test_missing_lecture_md_raises_template_load_error` /
`test_missing_podcast_md_raises_template_load_error` write throwaway content (`"## О чём
разговор"`, `"## Тезис"`) into `tmp_path` only to prove the loader raises; the assertion is
`pytest.raises(TemplateLoadError)`, so the literal is irrelevant. Replacing it with neutral
text is cosmetic — acceptable, not required.

---

### `tests/unit/test_deepseek_article_adapter.py` (test, adapter contract)

**Analog:** itself. Reuse the three module-level helpers instead of re-constructing the
generator inline (the two prompt tests currently duplicate 6 lines each):

```24:48:tests/unit/test_deepseek_article_adapter.py
def _stub_client(content: str) -> Any:
    class _Completions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def create(self, **kwargs: Any) -> Any:
            self.calls.append(kwargs)

            async def _gen():
                yield _delta_chunk(content)

            return _gen()

    class _Client:
        def __init__(self) -> None:
            self.chat = type("_Chat", (), {"completions": _Completions()})()

    return _Client()


def _make_transcript(language: str = "ru") -> Transcript:
    return Transcript(text="some transcript text", language=language, video_id="vid1")
```

```279:290:tests/unit/test_deepseek_article_adapter.py
def _make_generator(client: Any) -> Any:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    return DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )
```

**Important property of the fixture:** `_make_transcript` uses the literal text
`"some transcript text"`, which contains none of the headings or frame strings — that is what
makes `assert "## …" not in user_content` meaningful (the template sits in
`messages[-1]["content"]` joined with the transcript, `deepseek_article.py:46-62`). Do not
switch the fixture to a realistic transcript without re-checking every absence pin.

The two pins to rewrite (keep names recognisable, keep the `calls[0]["messages"]` capture
shape, `messages[0]` = system, `messages[-1]` = user):

```105:150:tests/unit/test_deepseek_article_adapter.py
def test_lecture_prompt_contains_lecture_headings_not_podcast() -> None:
    ...
    call = client.chat.completions.calls[0]
    messages = call["messages"]
    user_content = messages[-1]["content"]
    assert "## Тезис" in user_content
    assert "## Ход рассуждения" in user_content
    assert "## Вывод" in user_content
    assert "## О чём разговор" not in user_content


def test_podcast_prompt_contains_podcast_headings_not_lecture() -> None:
    ...
    user_content = messages[-1]["content"]
    assert "## О чём разговор" in user_content
    assert "## Позиции" in user_content
    assert "## Что запомнить" in user_content
    assert "## Тезис" not in user_content
```

**Target shape** (frame shared, all six legacy literals absent from *both* messages, kind
sentinels isolated):

```python
LEGACY_HEADINGS = (
    "## Тезис", "## Ход рассуждения", "## Вывод",
    "## О чём разговор", "## Позиции", "## Что запомнить",
)
SHARED_PROMPT_HEADINGS = ("## Конкретика", "## Зачем это СВА", "## Аудитория")


def _user_content(kind: TemplateKind, language: str) -> str:
    client = _stub_client(json.dumps({"title": "T", "dek": "D", "body_markdown": "B"}))
    asyncio.run(_make_generator(client).process(_make_transcript(language), kind))
    return client.chat.completions.calls[0]["messages"][-1]["content"]


@pytest.mark.parametrize("heading", LEGACY_HEADINGS)
def test_lecture_prompt_omits_every_legacy_heading(heading: str) -> None:
    assert heading not in _user_content(TemplateKind.LECTURE, "ru")


@pytest.mark.parametrize("heading", LEGACY_HEADINGS)
def test_podcast_prompt_omits_every_legacy_heading(heading: str) -> None:
    assert heading not in _user_content(TemplateKind.PODCAST, "en")


@pytest.mark.parametrize("heading", SHARED_PROMPT_HEADINGS)
def test_both_prompts_carry_the_shared_frame(heading: str) -> None:
    assert heading in _user_content(TemplateKind.LECTURE, "ru")
    assert heading in _user_content(TemplateKind.PODCAST, "en")


def test_lecture_prompt_keeps_the_kind_sentinel_out_of_the_podcast_prompt() -> None:
    assert "single speaker's argument" in _user_content(TemplateKind.LECTURE, "ru")
    assert "single speaker's argument" not in _user_content(TemplateKind.PODCAST, "en")


def test_podcast_prompt_keeps_the_kind_sentinel_out_of_the_lecture_prompt() -> None:
    assert "positions of its participants" in _user_content(TemplateKind.PODCAST, "en")
    assert "positions of its participants" not in _user_content(TemplateKind.LECTURE, "ru")
```

**System-prompt pins — extend, never replace.** The existing test is the ART-03 gate for shared
voice rules; add assertions at the end, leave the ten existing ones untouched:

```152:180:tests/unit/test_deepseek_article_adapter.py
def test_system_prompt_contains_honesty_and_language_rules() -> None:
    ...
    assert "Use only the transcript" in system_content
    assert "Do not invent facts, names, or numbers" in system_content
    assert "Output is always Russian" in system_content
    assert "If the transcript language is ru: format only; do not translate" in system_content
    assert "If the transcript language is en: translate into Russian" in system_content
    assert "Preserve technical terms, proper names, library names, numbers, and units as written" in system_content
    assert "json" in system_content
    assert "title" in system_content
    assert "dek" in system_content
    assert "body_markdown" in system_content
```

Add a separate test rather than growing this one further (one behaviour per test; this one is
already a ten-assertion "no rule was lost" gate):

```python
def test_system_prompt_carries_the_edition_voice_rules() -> None:
    ...
    assert "voice of the edition" in system_content
    assert "в подкасте рассказывается" in system_content      # D-03 example prohibition
    assert "attribute a claim to the speaker by name" in system_content
    assert "Editorial inference is allowed only" in system_content   # D-15/D-18
```

**Do not touch** `test_process_returns_article_draft_for_lecture/podcast`,
`test_create_kwargs_include_json_object_and_disabled_thinking`,
`test_create_is_called_with_stream_true`,
`test_long_template_with_short_transcript_does_not_raise_budget_error` (:533-548 — it is what
keeps a longer template safe w.r.t. `llm_truncation`), the error-mapping tests, or any
scripted-body assertion.

**Incidental fixture (optional cleanup):** `test_process_returns_article_draft_for_podcast`
(:89) passes `body_markdown: "## О чём разговор\n\nBody"` as a *scripted output* fixture. It
asserts pass-through, not the prompt, so it stays green — but after this phase the file would
still contain a legacy literal in a *positive* assertion context, which is confusing for anyone
grepping the six literals during verification. Swapping it to a content-shaped heading
(`"## Как это работает\n\nBody"`) is safe and one line.

---

### `tests/unit/test_article_draft_body_audience.py` (test, DTO transform)

**Analog:** itself. Reuse the `_draft()` helper and the "exact remainder" assertion style:

```17:33:tests/unit/test_article_draft_body_audience.py
def _draft(body_markdown: str, roles=None):
    from data_collection.dto.article_draft import ArticleDraft

    payload = {"title": "t", "dek": "d", "body_markdown": body_markdown}
    if roles is not None:
        payload["roles"] = roles
    return ArticleDraft.model_validate(payload)


def test_body_strips_trailing_audience_section_holding_role_json() -> None:
    body = '## Тезис\n\nМысль.\n\n## Аудитория\n\n["employee", "analyst", "ds"]'

    draft = _draft(body)

    assert "Аудитория" not in draft.body_markdown
    assert '["employee"' not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."
```

**New case (the Pitfall 3 regression guard).** Body ends with the two new sections, *then* the
audience block; assert the exact remainder, not just "absent":

```python
def test_body_strips_audience_section_after_concretika_and_sva_sections() -> None:
    body = (
        "## Как устроены языковые модели\n\nМысль.\n\n"
        "## Конкретика\n\n- **pgvector** — 1536 измерений.\n\n"
        "## Зачем это СВА\n\nДля СВА это значит, что модель надо проверять.\n\n"
        f"## Аудитория\n\n{PROMPT_LINE}"
    )

    draft = _draft(body)

    assert "Аудитория" not in draft.body_markdown
    assert "Кто целевая аудитория" not in draft.body_markdown
    assert draft.body_markdown == (
        "## Как устроены языковые модели\n\nМысль.\n\n"
        "## Конкретика\n\n- **pgvector** — 1536 измерений.\n\n"
        "## Зачем это СВА\n\nДля СВА это значит, что модель надо проверять."
    )
```

**Leave alone:** the existing `## Тезис` / `## Вывод` fixtures in this module. They exercise
the DTO strip, which is heading-agnostic; rewriting them adds churn without coverage. The new
case carries the new headings.

**Do not add:** any assertion of the form `"## Конкретика" in draft.body_markdown` sourced from
a stub draft. That tests the fixture and silently re-introduces the Phase 8 D-15 heading
validator (research Pitfall 6).

---

## Shared Patterns

### 1. Red-first sequencing (project mandate, `.cursor/rules/tdd.mdc` + `AGENTS.md`)

Every recent phase plan writes the failing assertion before the production edit, and the
summary records the observed failure. Copy this shape into the plan's `<behavior>` and
`<action>` blocks:

```119:133:.planning/milestones/v1.4-phases/27-header-search-runs-on-submit/27-02-PLAN.md
  <behavior>
    - RED: `header submit renders results from ?q` fails — `?q=RAG` renders the landing (`kb-hint-chips` visible), zero hit links, and the counter reads `0`.
    - GREEN: the same test passes with the counter at `1`, the row visible, `kb-hint-chips` at `0`, and the page field holding `RAG`.
    ...
  </behavior>
  <action>
    RED step. Append to the existing `tests/knowledge.spec.js` ...
    Run `npx playwright test ... -g "header submit renders results"` and record the failure (landing + counter `0`).

    GREEN step — `web/src/pages/KnowledgePage.jsx` only:
    ...
```

The summary records it as a two-line rider:

```85:94:.planning/milestones/v1.4-phases/28-live-proof-streamed-deepseek-ingest/28-01-SUMMARY.md
## Rider: FU-27-01 closed (TDD)
...
- **RED:** `an empty header submit replaces the history entry` failed on `history.length` 2 → 3.
- **GREEN:** `navigate('/knowledge', { replace: true })`; the case now pins the unchanged length and that
  Back leaves `/knowledge`.
- Commit `d77412f`. ...
```

**Phase 29 translation (this is the exact RED evidence to demand in the plan):**

1. Edit only the three test modules → `uv run pytest tests/unit/test_article_templates.py
   tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x`
   → RED with `AssertionError: assert '## Конкретика' in '## Тезис…'` (frame absent) and
   `AssertionError: assert '## Тезис' not in user_content` (scaffold still present).
2. Then rewrite the two `.md` files and add the system-prompt lines → same command GREEN.
3. Then `uv run pytest` (baseline 1156 passed) for the wave gate.
4. Record both commands and the RED assertion text in the task summary, as `28-01-SUMMARY.md` does.

### 2. Honesty line — two homes, one rule (ART-02 / D-18)

Transcript-only grounding is stated twice on purpose: in the shared system prompt
(`deepseek_article.py:37`, pinned at `test_deepseek_article_adapter.py:172`) and in each
template (line 8 today). The new templates keep a template-level line so the facts layer
(`## Конкретика`) is grounded at the point of use. Both stay; neither replaces the other.

### 3. Audience scaffolding tail (both templates; strip contract at `dto/_body.py:17-41`)

Always the final heading, always with the same instruction line, always with no content after
it. The role contract is the separate JSON `roles` key. Tests on this rule already exist
(`test_article_draft_body_audience.py`); the phase adds ordering coverage in
`test_article_templates.py` (`headings[-1] == "## Аудитория"`).

### 4. Package-data test idiom (`importlib.resources`, no conftest)

Read the real shipped files, never a copy:

```13:16:tests/unit/test_article_templates.py
def test_lecture_md_contains_russian_headings() -> None:
    root = importlib.resources.files("data_collection.templates")
    text = root.joinpath("lecture.md").read_text(encoding="utf-8")
```

Use `importlib.resources.files("data_collection.templates")` (not `Path(__file__)`) so the
assertion traverses the same path production uses (`load_article_templates`,
`templates/__init__.py:21-35`). `tmp_path` + a fake root is only for loader failure cases.

### 5. Two disjoint assertion surfaces (research Pattern 3)

| Surface | File | What it may assert |
|---------|------|--------------------|
| Prompt | `test_article_templates.py`, prompt tests in `test_deepseek_article_adapter.py` | frame strings present; legacy literals absent; kind sentinel isolated; audience block last |
| Pass-through | rest of `test_deepseek_article_adapter.py`, all of `test_article_draft_body_audience.py` | scripted JSON → `ArticleDraft` → `body_markdown` unchanged (except the audience strip) |

Never mix: a scripted `body_markdown` is fixture data, not evidence about the prompt.

### 6. Docstring / naming convention in `tests/unit/`

Module docstrings open with `"""RED→GREEN: <behaviour> (<REQ-ID>, <D-nn>)."""` (see
`test_article_templates.py:1`, `test_deepseek_article_adapter.py:1`,
`test_article_draft_body_audience.py:1`). Test names are full sentences describing the
behaviour (`test_body_keeps_a_later_section_that_follows_the_audience_block`). Helpers are
module-private `_snake_case` (`_draft`, `_stub_client`, `_make_transcript`, `_make_generator`,
`_template_text`). Keep all of it.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `## Конкретика` / `## Зачем это СВА` clause wording | prompt content | transform | New sections — no prior prompt text exists. Source of truth is `29-RESEARCH.md` Pattern 1 and the D-06…D-17 decisions, not an existing file. |
| Output-length band ("1 200-1 800 words") | prompt content | transform | Nothing in the repo bounds article length today; the only analog is the *risk* measurement in `.planning/milestones/v1.4-phases/28-…/evidence/ingest-run-1.log:5` (`response_chars=10314`). Research Pitfall 2 / Open Question Q1 govern it. |
| Phase 29 live-proof evidence + digit audit | evidence / manual UAT | batch | Nearest analog is Phase 28's `evidence/ingest-run-1.log` + `28-UAT.md` + the "Runbook" section of `28-01-SUMMARY.md:62-79`. Copy the shape (raw `--debug` lines, `EXIT=`, table of criteria with ✓/✗, explicit "still open"), not the content. |

---

## Guardrails for the Planner (each maps to a concrete failure seen in research)

1. **Never write the six legacy heading literals into any prompt string** — including as a
   prohibition. They belong in tests only. A plan action whose text contains `## Тезис` in the
   template-edit step is wrong (research Pitfall 1; breaks `test_deepseek_article_adapter.py:150`).
2. **`## Аудитория` stays last** in both `.md` files; nothing appended after it (Pitfall 3).
3. **No `max_tokens`, no `stream` change, no `response_format` change** in
   `deepseek_article.py:131-138` (locked scope; research Alternate/Open Question Q1).
4. **No heading validator, no new DTO field, no migration, no `pyproject.toml` / `uv.lock`
   diff** (Phase 8 D-15; research "Don't Hand-Roll").
5. **Do not pin long template sentences or a file digest** — pin frame strings, absence, and
   the kind sentinel; CONTEXT grants wording discretion, and prose pins turn every edit into a
   test edit (research Anti-Patterns).
6. **Kind sentinels must be multi-word and unique per file**, chosen before the prose is
   written (see lecture/podcast assignments above) — otherwise the cross-kind pin is
   unsatisfiable because the frame is shared by design.
7. **No SPA/CSS work.** Bold renders; `blockquote`/`table` are structurally correct but
   visually flat on `MaterialPage` (`[&_blockquote]` / `[&_table]` absent at
   `web/src/pages/MaterialPage.jsx:238`). Do not write a UAT criterion that depends on visual
   emphasis (Pitfall 4).
8. **Live proof needs a fresh `youtube_video_id`** (`youtube_video_id` is unique; a repeat run
   yields `already_saved` and proves nothing) and `--template lecture` (`28-01-SUMMARY.md:68-78`).

---

## Metadata

**Analog search scope:** `data-collection/src/data_collection/` (templates, adapters, dto),
`tests/unit/`, `ingestion-service/src/ingestion_service/composition/`, `web/src/pages/`,
`.planning/milestones/v1.3-phases/17-*`, `.planning/milestones/v1.4-phases/{27,28}-*`.
**Files read this session:** 14 (2 templates, `templates/__init__.py`, `deepseek_article.py`,
3 test modules, `pyproject.toml`, `web`/`dto` ranges via research, 17-PATTERNS.md, 27-02-PLAN.md,
28-01-SUMMARY.md).
**Baseline suite:** `uv run pytest` → 1156 passed (recorded in `29-RESEARCH.md`); targeted
trio → 54 passed in 1.44 s (re-measured at plan time, 2026-10-26; full suite 1156 passed in 13.70 s).
**Pattern extraction date:** 2026-10-26
