---
phase: 29-pass-1-richer-templates
verified: 2026-10-30T03:38:25Z
status: passed
score: 15/15 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 29: Pass-1 richer templates Verification Report

**Phase Goal:** A newly ingested material is a Russian longread shaped like the talk, with a transcript-only facts layer and an explicit СВА takeaway — not a three-block summary.
**Verified:** 2026-10-30T03:38:25Z
**Status:** passed
**Re-verification:** No — initial verification (missing VERIFICATION.md resume; SUMMARYs and 29-UAT.md already existed)

## Goal Achievement

The phase goal holds in the codebase and in the captured live draft. A newly ingested lecture (`youtube_video_id=JzEd26jQ1Ys`, `material_id=27`) is a Russian longread whose `##` name the talk's topics, whose `## Конкретика` traces talk-stated facts to the captured transcript (plus one labelled editorial definition under the D-18 owner override), and whose single `## Зачем это СВА` is an analog takeaway — not a three-block summary. Owner resume-signal `approved` on 2026-10-28 is recorded in `29-UAT.md` (`status: approved`). That human gate is treated as closed because the evidence files confirm the must-haves; they do not contradict them.

SUMMARY.md claims were not treated as evidence. Templates, system prompt, loader, stub-client round-trip, audience strip, and the Attempt 4 evidence bundle were re-read. Named unit tests were re-run (97 passed). Advisory `29-REVIEW.md` (0 critical / 6 warning) does not falsify a must-have.

Scoring contract: ROADMAP success criterion 4 owner-overrides criterion 3. ART-02/ART-03 are scored against the owner-override reading in REQUIREMENTS.md and CONTEXT D-08/D-10/D-11/D-17/D-18 (definitions/footnotes/reference data allowed; one optional СВА section). PLAN 01 literals such as `do not add facts` / `Editorial inference is allowed only` were intentionally rewritten on owner path 1/2/4 (2026-10-27); current tests pin the post-override wording.

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Newly ingested lecture or podcast draft has talk-shaped `##`; six legacy scaffolds absent (ART-01, SC-1) | ✓ VERIFIED | Attempt 4 `draft-2.json` headings: 8 topic `##` + `## Конкретика` + `## Зачем это СВА`. All six legacy literals (`## Тезис`, `## Ход рассуждения`, `## Вывод`, `## О чём разговор`, `## Позиции`, `## Что запомнить`) absent from body. Section count 10, not a fixed three. File- and message-level inverted pins: `test_lecture_md_omits_legacy_scaffold`, `test_podcast_md_omits_legacy_scaffold`, `test_lecture_prompt_omits_every_legacy_heading`, `test_podcast_prompt_omits_every_legacy_heading` |
| 2 | Dedicated `## Конкретика` of interesting/explanatory facts; talk-stated names/numbers/tools/versions trace to the transcript; no invented speaker-stated facts; labelled editorial definitions allowed (ART-02, SC-2 via REQUIREMENTS/D-18 override) | ✓ VERIFIED | `draft-2.json` has `## Конкретика` with 8 talk-fact bullets + one `*Редакционное примечание:*`. All 9 UAT needles found in `transcript-2.txt` (`Postgress 16`, `ПГ вектор`, `векторQ`, `чан size я бы взял 500`, `лимит пять`, `модель именно Small`, `GPT 4 и1`, `mim type`, `2 руб. 40 коп`). Zero `NOT FOUND` on a speaker-stated number/name/version. Template pins: `test_lecture_md_states_the_concretika_rules`, `test_podcast_md_states_the_concretika_rules` (`interesting`, `explanatory`, `inventory`, `never invent a version`, `Omit the section entirely`) |
| 3 | Exactly one `## Зачем это СВА` when an analog exists; no second «Риски и ограничения»; `dek` stays a 1–2 sentence hook (ART-03, SC-4 owner-overrides SC-3) | ✓ VERIFIED | `draft-2.json`: SVA_COUNT=1; `## Риски и ограничения` / `## Что учесть СВА` absent. Analog is control over where data lives / snapshot-before-change. `dek` is two sentences about the talk, not an audit dump. Template + system-prompt pins: `test_lecture_md_states_the_sva_rules`, `test_system_prompt_carries_the_edition_voice_and_length_rules` (`1-2 sentence hook`, `Do not invent a duty`) |
| 4 | Lecture prompt frame is proven end-to-end on the real shipped file: package markdown → `load_article_templates` → `build_article_messages` → stub-client `DeepSeekArticleGenerator.process` (ART-01 tracer) | ✓ VERIFIED | `_template_text` and production loader both use `importlib.resources.files("data_collection.templates")`. `_user_content` / `_system_content` run `process` and read `calls[0]["messages"]`. Fixture `"some transcript text"` contains none of the frame literals, so absence/presence pins are decided by the template. 97 phase unit tests passed |
| 5 | `lecture.md` is a positive editorial frame: topic-shaped sections, `implicit editorial chapters`, `no fixed count`, kind sentinel `single speaker's argument`; only three level-2 output headings; `## Аудитория` last; no H1 | ✓ VERIFIED | File headings are exactly `## Конкретика`, `## Зачем это СВА`, `## Аудитория`. Last line `employee, analyst, ds.`. `test_lecture_md_has_only_the_intended_headings`, `test_lecture_md_keeps_the_audience_block_last`, `test_lecture_md_names_the_topics_frame`. No instruction-only `## Structure` |
| 6 | `lecture.md` / `podcast.md` carry the same `## Конкретика` and `## Зачем это СВА` clauses (analog bar, omit-when-empty, canonical PostgreSQL, never-invent-a-version) so Phase 32 can freeze one literal | ✓ VERIFIED | Both files share the three output heading strings. Concretika/SVA rule tests exist for both kinds. `test_kind_sentinels_do_not_cross` isolates kinds by sentinel, never by shared headings |
| 7 | `ARTICLE_SYSTEM_PROMPT` carries edition voice, recap-phrase examples, СВА inference boundary (plus D-18 definitions), `dek` as `1-2 sentence hook`, `1200-1800 words`; JSON-contract sentence is last; `json` and key list present | ✓ VERIFIED | `deepseek_article.py` lines 35–50. Last line: `Return one json object with keys title, dek, body_markdown, roles.` Tests: `test_system_prompt_carries_the_edition_voice_and_length_rules`, `test_system_prompt_contains_honesty_and_language_rules` (post-override honesty: `Do not invent names, numbers, tools or versions` + `definitions of hard terms`; `Use only the transcript` asserted absent) |
| 8 | No call-shape or contract drift: `response_format=json_object`, `thinking.disabled`, `stream=True`, no `max_tokens`; `stage=llm` / `llm_truncation` taxonomy and `data_collection.__all__` unchanged | ✓ VERIFIED | `_stream_content` create kwargs; `test_create_kwargs_include_json_object_and_disabled_thinking`; `test_create_is_called_with_stream_true`; grep finds no `max_tokens` in the article adapter. `ingest_pipeline.py` still emits `response_chars`; `article.py` still maps `llm_truncation`. `__all__` is the ten ingestion names |
| 9 | `podcast.md` carries the same topic-shaped frame with kind hint `positions of its participants`; none of the three legacy podcast headings in the file; none of the six in the assembled podcast user message | ✓ VERIFIED | `test_podcast_md_omits_legacy_scaffold`, `test_podcast_prompt_omits_every_legacy_heading`, `test_podcast_md_names_the_dialogue_frame`, `test_podcast_prompt_keeps_the_kind_sentinel`. Advisory WR-03 (dialogue vs topic bullets both present) does not restore the podcast trio |
| 10 | Kind discriminator is the multi-word sentinel alone; sentinels do not cross at file or assembled-message level; shared section headings appear in both | ✓ VERIFIED | `test_kind_sentinels_do_not_cross`; lecture/podcast prompt sentinel tests. `SHARED_PROMPT_HEADINGS` present in both assembled user messages |
| 11 | `strip_audience_section` still removes trailing `## Аудитория` scaffolding and preserves a body whose `## Конкретика` and `## Зачем это СВА` precede it byte-identically | ✓ VERIFIED | `test_body_strips_audience_section_after_the_concretika_and_sva_sections` exact-remainder assertion. `_AUDIENCE_HEADING_RE` / `_NEXT_TOP_HEADING_RE` in `dto/_body.py` unchanged. Attempt 4 body has no `## Аудитория` |
| 12 | A freshly ingested material is a new row: chosen `youtube_video_id` was absent; stdout `already_saved: false`; one `status=draft` material plus pending shortlist item | ✓ VERIFIED | `evidence/ingest-run-2.log`: `already_saved=False`, `material_id=27`, `slug=vektornaia-pamiat-na-svoem-servere-postgresql-pgve-JzEd26jQ1Ys`, `batch_id=7`, `rank=4`, `exit_code: 0`, `template=lecture`. UAT pre-flight: MCP `materials` filter `JzEd26jQ1Ys` was 0 rows. No `network_error` / `APIConnectionError` |
| 13 | `response_chars` from `--debug` `stage=llm` is recorded and compared against the 16000 band; crossing it does not trigger a re-run | ✓ VERIFIED | Log line `stage=llm elapsed_ms=19140 template=lecture response_chars=10011`. `len(body_markdown)=10011` in `draft-2.json`. 10011 < 16000. No `max_tokens` change. Attempt 3 measured 9847 (rejected row 26, not the approved proof) |
| 14 | Evidence is the run's own output: ingest log, transcript oracle, draft read-back, UAT per-criterion verdicts, runbook | ✓ VERIFIED | `ingest-run-2.log` (command, wall-clock, stderr, stdout ids); `transcript-2.txt` first two lines `JzEd26jQ1Ys` / `ru`, body length 19801 matches `transcript_chars`; `draft-2.json` keys `title`, `dek`, `body_markdown` only; `29-UAT.md` has pre-flight, heading list, per-bullet audit, verdicts, runbook. No `sk-` / `tvly-` / raw API keys in evidence |
| 15 | Owner editorial verdict on the live draft is recorded; blocking-human gate closed with resume-signal `approved` | ✓ VERIFIED | `29-UAT.md` frontmatter `status: approved`; body records `approved` on 2026-10-28 for `material_id=27`. Attempt 3 (`material_id=26`) remains the rejected row and was not patched. PLAN 03 `<human-check>` harvested and closed; not re-opened |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `data-collection/src/data_collection/templates/lecture.md` | Talk-shaped lecture frame + optional Конкретика/СВА | ✓ VERIFIED | 29 lines; three `##` only; audience last; D-18 definitions clause |
| `data-collection/src/data_collection/templates/podcast.md` | Same frame, dialogue kind hint | ✓ VERIFIED | Mirrors lecture; sentinel `positions of its participants` |
| `data-collection/src/data_collection/adapters/deepseek_article.py` | Shared `ARTICLE_SYSTEM_PROMPT` + message assembly | ✓ VERIFIED | Voice/`dek`/length additive; `build_article_messages` joins template + transcript; call shape locked |
| `data-collection/src/data_collection/templates/__init__.py` | `load_article_templates` | ✓ VERIFIED | Reads every `TemplateKind` from `importlib.resources` root |
| `tests/unit/test_article_templates.py` | Inverted scaffold pins + frame literals | ✓ VERIFIED | Lecture + podcast twins; `_template_text` uses package data |
| `tests/unit/test_deepseek_article_adapter.py` | Stub-client e2e + system-prompt pins | ✓ VERIFIED | `_user_content` / `_system_content`; legacy absence; stream/json_object |
| `tests/unit/test_article_draft_body_audience.py` | Strip regression on pass-1-shaped body | ✓ VERIFIED | Exact remainder after Конкретика/СВА |
| `web/src/pages/MaterialPage.jsx` | One body frame + nested Конкретика/СВА cards | ✓ VERIFIED | Owner path 1; `data-testid` `material-section-body` / `-concretika` / `-sva` |
| `web/src/utils/markdownSections.js` | Split/group bands | ✓ VERIFIED | `kindForHeading` exact `Конкретика` / `Зачем это СВА` |
| `.planning/phases/29-pass-1-richer-templates/evidence/ingest-run-2.log` | Approved live-proof log | ✓ VERIFIED | Attempt 4; PLAN 03 originally named `ingest-run-1.log` (Attempt 3, also present) |
| `.planning/phases/29-pass-1-richer-templates/evidence/transcript-2.txt` | Transcript oracle | ✓ VERIFIED | `JzEd26jQ1Ys` / `ru` / 19801 chars |
| `.planning/phases/29-pass-1-richer-templates/evidence/draft-2.json` | Read-only materials read-back | ✓ VERIFIED | `title`, `dek`, `body_markdown`; length 10011 |
| `.planning/phases/29-pass-1-richer-templates/29-UAT.md` | Per-criterion UAT + owner signal | ✓ VERIFIED | `status: approved`; audit table; runbook |

**Artifacts:** 13/13 verified (gsd-tools `verify.artifacts` returned 0 because PLAN `artifacts` are path strings, not `{path, provides}` objects — checked manually)

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| package `lecture.md` / `podcast.md` | `DeepSeekArticleGenerator.process` | `load_article_templates(importlib.resources.files("data_collection.templates"))` → `templates[kind]` → `build_article_messages` user message | ✓ WIRED | `clients.py` `build_deepseek_article_generator`; CLI `cli.py` / `collect_cli.py` pass that factory. Stub-client tests inspect `messages[-1]["content"]` |
| `ARTICLE_SYSTEM_PROMPT` | `messages[0]` for both kinds | `build_article_messages` always sets system content from the shared literal | ✓ WIRED | `_system_content(LECTURE)` and podcast inherit the same string |
| `## Аудитория` last in both templates | `ArticleDraft.body_markdown` | `_AUDIENCE_HEADING_RE` / `_NEXT_TOP_HEADING_RE` in `dto/_body.py` | ✓ WIRED | Strip test exact remainder; live draft has no audience scaffolding |
| `ingest --template lecture --debug` | `materials` + `digest_shortlist_items` | `run_ingest_pipeline` → real generator → persist | ✓ WIRED | Attempt 4 log: `stage=llm template=lecture` then `stage=persist material_id=27 already_saved=False` |
| `stage=llm` diagnostic | evidence log truncation check | allowlisted `template`, `response_chars` | ✓ WIRED | `ingest_pipeline.py` `response_chars=len(article_draft.body_markdown)`; quoted 10011 |
| captured transcript | UAT per-bullet audit | `transcript-2.txt` oracle | ✓ WIRED | All nine Attempt 4 needles present in the oracle file |
| `body_markdown` | MaterialPage cards | `splitMaterialSections` → `groupMaterialBands` | ✓ WIRED | Playwright `frames the body once and keeps Конкретика and Зачем это СВА in their own cards` on `rag-systems` |

**Wiring:** 7/7 connections verified (gsd-tools `verify.key-links` returned 0 — PLAN `key_links` are prose strings, not `{from, to, via}` objects)

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `lecture.md` / `podcast.md` | user-message template text | package markdown loaded at generator construction | Yes — shipped files, not a copy | ✓ FLOWING |
| `DeepSeekArticleGenerator` | `messages` | `build_article_messages(transcript, kind, templates)` | Yes — template + live transcript | ✓ FLOWING |
| Attempt 4 `draft-2.json` `body_markdown` | article body | live DeepSeek completion, `response_chars=10011` | Yes — not a fixture; matches persist diagnostic | ✓ FLOWING |
| `## Конкретика` bullets | names/numbers/tools | talk-stated values from `transcript-2.txt`; one labelled editorial definition | Yes — 8/8 talk-facts matched; editorial not scored as speaker speech | ✓ FLOWING |
| `MaterialPage` cards | `material.body_markdown` | API/material row → splitter | Yes — live row 27; mock `rag-systems` only for Playwright chrome | ✓ FLOWING |

No hollow props. Attempt 4 used the read-only Supabase fallback for the transcribed text (Vite down at persist); that is the same `title`/`dek`/`body_markdown` row, not a mock.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase unit pins (templates, adapter, audience strip) | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -q` | `97 passed in 3.07s` | ✓ PASS |
| Markdown section splitter | `node --test tests/unit/test_markdown_sections.js` | 4 passed, 0 skipped | ✓ PASS |
| Attempt 4 heading list + forbidden literals + transcript needles | in-repo Python extract of `draft-2.json` / `transcript-2.txt` | 10 headings; 6 scaffolds absent; 9/9 needles true; `BODY_LEN=10011` | ✓ PASS |
| Full workspace suite | not re-run (constraint: at most once; UAT already recorded `1197 passed` before Attempt 4 verdict) | — | ? SKIP |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | No `scripts/*/tests/probe-*.sh`; PLAN/SUMMARY do not declare probes | skipped | N/A |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ART-01 | 29-01, 29-02, 29-03 | Newly ingested material is a Russian longread whose `##` follow the source talk, not the lecture three-block or the podcast trio | ✓ SATISFIED | Live draft-2 headings + inverted absence pins at file and message level for both kinds |
| ART-02 | 29-01, 29-02, 29-03 | Dedicated `## Конкретика` of interesting/explanatory facts grounded in the talk; no invented speaker-stated numbers/names/versions; definitions/footnotes/reference data allowed (REQUIREMENTS owner override) | ✓ SATISFIED | Template clauses + Attempt 4 audit (8 traced talk-facts, 1 labelled editorial, 0 NOT FOUND) |
| ART-03 | 29-01, 29-02, 29-03 | One optional `## Зачем это СВА` (SC-4 overrides SC-3); `dek` remains the 1–2 sentence hook | ✓ SATISFIED | One SVA heading in draft-2; no risks heading; dek is a two-sentence hook |

**Coverage:** 3/3 requirements satisfied. No orphaned IDs: REQUIREMENTS.md maps only ART-01/ART-02/ART-03 to Phase 29; all three appear in every plan's `requirements:` frontmatter. ART-04 is Phase 31.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. (`honored=20`, `total=20`, `not_honored=[]`). Non-blocking gate.

D-18/D-19 owner override 2026-10-27 (definitions/footnotes in pass-1; Tavily remains Phase 32) is present in CONTEXT, REQUIREMENTS, templates, and `ARTICLE_SYSTEM_PROMPT`. ROADMAP locked-scope still says «Source-facts stay transcript-only» — documentation drift in ROADMAP, not a missing implementation. Verifier did not edit ROADMAP.md.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_article_templates.py` | ART-01/02/03 | yes | 0 | no | Value (literals, heading set, sentinel isolation) | OK |
| `tests/unit/test_deepseek_article_adapter.py` | ART-01/03 | yes | 0 | no | Behavioral (stub-client messages) + value (kwargs) | OK |
| `tests/unit/test_article_draft_body_audience.py` | ART-03 strip | yes | 0 | no | Value (exact remainder) | OK |
| `tests/unit/test_markdown_sections.js` | owner path 1 chrome | yes | 0 | no | Value (band kinds) | OK |
| `tests/web-app.spec.js` (frame test) | owner path 1 | yes (Playwright; not re-run here) | 0 | no | Behavioral (visible cards on fixture) | OK — fixture-only chrome; live ART-* proven by draft-2 |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 1 warning — `test_assembled_user_message_omits_guide_heading` second assert compares `SHARED_PROMPT_HEADINGS` to itself (REVIEW IN-01). First assert (`Гайд` not in user message) is live. Not a requirement gap.

Live ART-01/02/03 behavior is proven by the captured draft + transcript oracle, not only by prompt-literal pins.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `web/src/utils/markdownSections.js` | 22–60 | Fence-unaware `##` split (REVIEW WR-01) | ⚠️ Warning | Can mis-card a heading inside a fence. Does not restore the three-block scaffold |
| `web/src/utils/markdownSections.js` | 11–16 | Exact heading match only (WR-02) | ⚠️ Warning | `## **Конкретика**` would miss the card. Attempt 4 headings were canonical |
| `data-collection/.../templates/podcast.md` | 4–7 | Dialogue and topic bullets both unconditional (WR-03) | ⚠️ Warning | Unstable podcast chaptering possible. Legacy podcast trio still absent; live proof was lecture |
| `web/src/pages/MaterialPage.jsx` | 260–279 | Per-band `react-markdown` trees (WR-04) | ⚠️ Warning | GFM footnotes / TOC anchors can break. Phase goal is article shape, not footnote UX |
| `deepseek_article.py` | 35–50 | System prompt does not require `Редакционное примечание` label (WR-05) | ⚠️ Warning | Attempt 4 labelled the definition anyway. Honesty line still forbids presenting added context as speaker words |
| `MaterialPage.jsx` / splitter | 261–273 | Empty Конкретика/СВА heading still draws a card (WR-06) | ⚠️ Warning | Prompt says omit entirely; no runtime heading validator by Phase 8 D-15 design |
| — | — | `TBD` / `FIXME` / `XXX` in phase-modified production files | none | No debt-marker blocker |

Advisory review `status: issues_found` is not a phase-goal failure.

### Human Verification Required

None. PLAN 03 blocking-human checkpoint is closed: `29-UAT.md` `status: approved`, owner typed `approved` on 2026-10-28 for `material_id=27`. Evidence files confirm ART-01/ART-02/ART-03; they do not contradict them. Visual chrome was accepted by the owner on 2026-10-27 («Принято - то что нужно»).

### Gaps Summary

No actionable gaps. Later milestone phases (31–34) own persist-then-enrich, Tavily, cheat sheets, and reader sources — not missing Phase 29 must-haves.

---

_Verified: 2026-10-30T03:38:25Z_
_Verifier: Claude (gsd-verifier)_
