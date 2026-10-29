---
phase: 30-classifier-practical-conceptual
verified: 2026-10-29T18:10:34Z
status: passed
score: 24/24 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 30: Classifier practical | conceptual Verification Report

**Phase Goal:** Every ingest records a closed topic kind; extras never attach when the kind is missing, empty, unknown, or conceptual.
**Verified:** 2026-10-29T18:10:34Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Phase goal holds in the codebase. Every ingest path stamps a closed `topic_kind` (`practical` | `conceptual`) through classifier → `normalize_topic_kind` → `MaterialDraft` → `p_topic_kind`. Invalid / missing / empty / unknown classifier output is stored as `conceptual` and ingest continues. Pass-1 extras furniture (`## Гайд`, `ссылки скоро появятся`) is stripped in the DTO. Pass-2 extras (Tavily, enricher, cheat sheets) are absent from `ingest_pipeline.py`. Live `public.materials.topic_kind` exists and returns `conceptual` on existing rows.

SUMMARY.md claims were not treated as evidence. Named unit tests were re-run (70 passed). Live PostgREST `select id,topic_kind from materials limit 3` returned rows with `topic_kind=conceptual`. Three code-review warnings (first-match strip, furniture-only body, unfenced title/dek) are real edge cases; they do not falsify the phase goal or the roadmap success criteria for the specified contract.

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | After ingest, the draft stores `topic_kind` as `practical` or `conceptual` (KIND-01, SC-1) | ✓ VERIFIED | `test_fake_practical_persists_practical` (persist.calls[0].topic_kind == practical); `normalize_topic_kind` allowlist; live column `materials.topic_kind` |
| 2 | Missing, empty, or unknown `topic_kind` is stored as `conceptual` (KIND-02 mapping, SC-2) | ✓ VERIFIED | `test_normalize_topic_kind_garbage_is_conceptual` (None/"" /unsure/dict/list → conceptual); pipeline non-allowlist parametrize including `{"kind": "practical"}` |
| 3 | Conceptual / unknown does not attach guide extras, generated-code extras, Tavily reads, or a cheat sheet (KIND-02 extras, SC-2) | ✓ VERIFIED | `test_ingest_pipeline_does_not_wire_pass2_extras` — `ArticleEnricher` / `WebSearch` / `tavily` / `cheat_sheet` / `personal_kb` absent from `ingest_pipeline.py`; no matches under `ingestion-service/` |
| 4 | A conceptual material has no empty «Гайд» heading and no “ссылки скоро появятся” placeholder; no disabled CTA this phase (KIND-03, SC-3) | ✓ VERIFIED | `test_article_draft_body_guide.py` matrix via `model_validate`; templates omit `Гайд`; no cheat-sheet UI. Dual-heading leftover is a warning, not the specified contract |
| 5 | Pass-1 leaked `practical` is overwritten by the classifier stamp (Pitfall 4) | ✓ VERIFIED | `test_classifier_stamp_overwrites_leaked_pass1_topic_kind` — ArticleDraft practical + Fake conceptual → persist conceptual; pipeline always assigns `article_draft.topic_kind = normalize_topic_kind(raw)` |
| 6 | Classifier transport / generic Exception does not raise `IngestError`, does not set `stage=llm`, still persists `conceptual` (KIND-02, T-30-03) | ✓ VERIFIED | `test_classifier_runtime_error_persists_conceptual_without_ingest_error`; `except Exception: raw = None` in `ingest_pipeline.py` after the llm try/except |
| 7 | D-08 two-layer default: Python never maps invalid to `practical`; prompt unsure → practical; Fake practical on an ambiguous how-to is stored practical | ✓ VERIFIED | `normalize_topic_kind("unsure") == "conceptual"`; prompt literal `if you are not sure pick practical`; `test_ambiguous_howto_fake_practical_is_stored_practical` |
| 8 | `run_ingest_pipeline` requires `classifier=` with no None default; CollectDeps and unit call sites pass `FakeTopicKindClassifier` | ✓ VERIFIED | `test_run_ingest_pipeline_requires_classifier`; `CollectDeps.classifier: TopicKindClassifier`; every `CollectDeps(` in `test_collect_batch.py` passes the Fake |
| 9 | `data_collection.__all__` remains ten names; TopicKind names are in `NEGATIVE_ROOT_NAMES`; Stage remains seven values | ✓ VERIFIED | `test_public_all_is_exactly_ten_ingestion_names`; `TopicKindClassifier` not in `ports.__all__`; `test_stage_set_is_unchanged` |
| 10 | DeepSeek classifier issues one non-stream `json_object` create with `thinking.disabled`, `max_tokens=128`, and the word `json` plus `{"topic_kind": "conceptual"}` | ✓ VERIFIED | `test_create_kwargs_are_json_object_non_stream_with_max_tokens`; `test_messages_contain_json_word_and_topic_kind_example`; pass-1 pin still `stream=True` |
| 11 | Classifier system prompt encodes the practical bar (D-01…D-08) | ✓ VERIFIED | `test_system_prompt_encodes_d01_through_d08_literals` — named product, followable, without the video, Excel/SAP/Tableau/Power BI/Jira/Python/Kubernetes, job of the page, do vs understand, minutes not counted, unsure→practical |
| 12 | Adapter unwraps only `payload["topic_kind"]`; sibling key `kind` cannot launder `practical` (T-30-02) | ✓ VERIFIED | `test_sibling_kind_key_does_not_launder_practical`; `test_topic_kind_practical_payload_unwraps_to_practical` |
| 13 | Empty content, missing key, or transport exception is a KIND-02 miss; adapter never raises `ArticleError` | ✓ VERIFIED | `test_empty_content_maps_to_conceptual_without_article_error`; `test_transport_error_does_not_raise_article_error`; `test_adapter_source_does_not_import_article_errors` |
| 14 | Classifier input is title, dek, and transcript head 8000 + tail 4000 fenced as untrusted data; `body_markdown` is not sent | ✓ VERIFIED | `test_user_message_has_title_dek_fenced_transcript_not_body`; `test_long_transcript_is_head_8000_plus_tail_4000`; `BODY_SENTINEL` absent |
| 15 | `build_ingest_deps` / `build_collect_deps` pass `build_deepseek_topic_kind_classifier`; composition exports the factory | ✓ VERIFIED | factory in `clients.py` uses `build_async_deepseek_client`; wired in `cli.py` / `collect_cli.py`; in `composition.__all__` |
| 16 | Pass-1 `ARTICLE_SYSTEM_PROMPT` keys stay title/dek/body_markdown/roles — `topic_kind` absent (Pitfall 4) | ✓ VERIFIED | `test_pass1_article_system_prompt_has_no_topic_kind` |
| 17 | Guide strip never raises on a leaked heading; persist proceeds for the specified (content + furniture) cases (D-09) | ✓ VERIFIED | Guide tests use `model_validate` with no expected exception; remaining `## Тезис` bodies persist. Furniture-only body is a documented warning |
| 18 | In-prose `гайд` and D-12 titles (Guide, How-to, Как сделать, Tutorial, Шпаргалка) remain; lowercase ATX `гайд` is stripped; mid-body keeps the next h2 | ✓ VERIFIED | `test_d12_talk_headings_are_kept`; `test_body_mention_of_guide_mid_text_is_preserved`; `test_body_strips_lowercase_atx_guide_heading`; `test_body_keeps_a_later_section_that_follows_the_guide_block` |
| 19 | `lecture.md` / `podcast.md` still do not contain `Гайд`; `SHARED_PROMPT_HEADINGS` unchanged | ✓ VERIFIED | `test_assembled_user_message_omits_guide_heading`; `SHARED_PROMPT_HEADINGS == ("## Конкретика", "## Зачем это СВА", "## Аудитория")`; no `Гайд` under `data-collection/src` templates |
| 20 | Migration 014 ADDs `public.materials.topic_kind text NOT NULL DEFAULT conceptual` and DO-block CHECK `materials_topic_kind_check` | ✓ VERIFIED | `014_phase30_materials_topic_kind.sql`; `test_migration_014_adds_topic_kind_column`; `test_migration_014_check_constraint_via_do_block`; live PostgREST returns `topic_kind` |
| 21 | 014 DROP 12-arg `persist_draft_and_enqueue` then CREATE 13-arg with `p_topic_kind` (T-30-06) | ✓ VERIFIED | SQL DROP of exact 12 types then CREATE; `test_migration_014_drops_live_12_arg_then_creates_p_topic_kind`; 42P13 trailing `p_batch_size int default null` pinned |
| 22 | `ON CONFLICT (youtube_video_id) DO NOTHING` and already_saved branches survive; 007/008/009 unmodified | ✓ VERIFIED | `test_migration_014_keeps_already_saved_and_conflict_branches`; `test_applied_007_008_009_files_unchanged_relative_to_git_blob` |
| 23 | 13-arg signature is `security invoker`; revoke public/anon/authenticated; grant execute to `service_role` only (T-30-04) | ✓ VERIFIED | `test_migration_014_grants_13_arg_execute_only_to_service_role` |
| 24 | `SupabaseDraftPersister._rpc_params` sends `p_topic_kind` from `draft.topic_kind`; practical override forwards practical. 014 applied on shared VM | ✓ VERIFIED | `test_persist_forwards_practical_topic_kind`; live `materials.topic_kind=conceptual` on ids 2/3/4; runbook §4l Applied 2026-10-29 (`n=1`, `pronargs=13` operator screenshot) |

**Score:** 24/24 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `data-collection/src/data_collection/ports/topic_kind.py` | `TopicKindClassifier` Protocol | ✓ VERIFIED | Exists, substantive, imported by pipeline / CollectDeps / Fake; not in `ports.__all__` |
| `data-collection/src/data_collection/dto/topic_kind.py` | `TopicKind`, `VALID_TOPIC_KINDS`, `normalize_topic_kind` | ✓ VERIFIED | Two-member frozenset; dict/list/None → conceptual |
| `data-collection/src/data_collection/tests_support/fakes.py` | `FakeTopicKindClassifier` | ✓ VERIFIED | Scripted result + failures map; used at unit call sites |
| `tests/unit/test_topic_kind.py` | Allowlist + DTO garbage matrix | ✓ VERIFIED | Value-level assertions; 70-test spot-check included this file |
| `tests/unit/test_ingest_pipeline.py` | KIND-01/02 spine | ✓ VERIFIED | Practical persist, garbage, RuntimeError, Pitfall 4, extras-unwired |
| `data-collection/src/data_collection/adapters/deepseek_classifier.py` | Cheap DeepSeek adapter | ✓ VERIFIED | `stream=False`, `max_tokens=128`, fence, unwrap `topic_kind` only |
| `tests/unit/test_deepseek_classifier.py` | Stub-client pins | ✓ VERIFIED | Create-kwargs, D-01…D-08 literals, fail-soft |
| `ingestion-service/src/ingestion_service/composition/clients.py` | `build_deepseek_topic_kind_classifier` | ✓ VERIFIED | `build_async_deepseek_client`, same model, no new env var |
| `data-collection/src/data_collection/dto/_body.py` | `strip_guide_section` | ✓ VERIFIED | `_GUIDE_HEADING_RE` + reused `_NEXT_TOP_HEADING_RE`; first-match walk (warning) |
| `tests/unit/test_article_draft_body_guide.py` | Guide-strip matrix | ✓ VERIFIED | Empty/filled/lowercase/D-12/placeholder/practical/idempotent |
| `supabase-integration/migrations/014_phase30_materials_topic_kind.sql` | Additive column + 13-arg RPC | ✓ VERIFIED | ADD COLUMN, DO-block CHECK, DROP 12, CREATE 13, grants, `begin`/`commit` |
| `tests/unit/test_phase30_migration_014.py` | SQL contract | ✓ VERIFIED | Column, CHECK, DROP/CREATE, grants, no ENUM, 007–009 pin, SELECT omit |
| `docs/agents/local-platform-runbook.md` | §4l apply/verify | ✓ VERIFIED | Verify SQL for column + CHECK + `pronargs=13`; Applied 2026-10-29 |
| `ingestion-service/.../supabase_persist.py` | `p_topic_kind` | ✓ VERIFIED | `"p_topic_kind": draft.topic_kind` in `_rpc_params` |
| `data-collection/.../article_draft.py` / `material_draft.py` / `assemble.py` | `topic_kind` field + copy | ✓ VERIFIED | before-validator + `topic_kind=article.topic_kind` |

**Artifacts:** 15/15 verified (gsd-tools `verify.artifacts` returned 0 because PLAN `artifacts` are path strings, not `{path, provides}` objects — checked manually)

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `TopicKindClassifier.classify` | `PersistPort.persist` | `normalize_topic_kind` → `article_draft.topic_kind` → `assemble_material_draft` | ✓ WIRED | `ingest_pipeline.py` 138–148 |
| `ArticleDraft.topic_kind` / `MaterialDraft.topic_kind` | closed Literal | `field_validator(mode="before")` → `normalize_topic_kind` | ✓ WIRED | Garbage never hits Pydantic `literal_error` |
| `build_deepseek_topic_kind_classifier` | pipeline `classifier=` | `build_ingest_deps` / `build_collect_deps` | ✓ WIRED | `cli.py:48`, `collect_cli.py:52` |
| `strip_guide_section` | persist body | `ArticleDraft._strip_guide_scaffolding` on every `model_validate` | ✓ WIRED | Second `body_markdown` validator after audience |
| `MaterialDraft.topic_kind` | Postgres `materials.topic_kind` | `_rpc_params["p_topic_kind"]` → `persist_draft_and_enqueue` INSERT | ✓ WIRED | Python key + SQL `topic_kind` / `p_topic_kind` |
| DROP 12-arg | CREATE 13-arg | exact type list then `p_topic_kind` | ✓ WIRED | T-30-06 sequence in 014; wrapped in one transaction |

**Wiring:** 6/6 connections verified (`verify.key-links` also returned 0 — PLAN `key_links` are strings, not `{from,to,via}` objects)

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Fake ingest spine | `persist.calls[0].topic_kind` | Fake classifier result → `normalize_topic_kind` | Yes (scripted token, not hardcoded empty) | ✓ FLOWING |
| Live persist | `p_topic_kind` | `draft.topic_kind` from pipeline stamp | Yes — RPC param, not a static `"conceptual"` | ✓ FLOWING |
| Live `materials.topic_kind` | column | ADD COLUMN DEFAULT + INSERT `p_topic_kind` | Yes — PostgREST returned `conceptual` on ids 2, 3, 4 | ✓ FLOWING |
| Guide strip | `body_markdown` | `_GUIDE_HEADING_RE` walk + substring replace | Yes — validator mutates real body | ✓ FLOWING |
| DeepSeek adapter | raw `topic_kind` | `chat.completions.create` → `payload["topic_kind"]` | Yes on stub client; live LLM not invoked this verification | ✓ FLOWING |

No hollow/static persist of kind. Default `conceptual` is the product rule (KIND-02), not a stub.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| KIND-01/02/03 named tests | `uv run pytest` (topic_kind, ingest spine, guide, classifier, migration 014, persister practical, public API, wiring) | `70 passed in 2.51s` | ✓ PASS |
| Dual `## Гайд` leftover (review WR-01) | `uv run python` `ArticleDraft.model_validate` on two Гайд sections | second `## Гайд` remains | ⚠️ documented warning, not a failed must-have |
| Furniture-only body (review WR-02) | same, body `## Гайд\n\nsteps only` then `assemble_material_draft` | ArticleDraft accepts `""`; assemble `ValidationError` `string_too_short` | ⚠️ documented warning |
| Live column | Supabase PostgREST `materials` `select=id,topic_kind` limit 3 | `[{id:2,topic_kind:conceptual}, …]` | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` in the repo. PLAN/SUMMARY do not declare probes. Step 7c skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| KIND-01 | 30-01, 30-02, 30-04 | Every ingest records `topic_kind` as `practical` or `conceptual` on the draft | ✓ SATISFIED | Pipeline stamp + RPC `p_topic_kind` + live column |
| KIND-02 | 30-01, 30-02 | Missing/empty/unknown stored as `conceptual`; extras not attached | ✓ SATISFIED | Allowlist + fail-soft classify + extras identifiers absent this phase |
| KIND-03 | 30-03 | Conceptual material has no empty «Гайд» and no “ссылки скоро появятся”; no disabled cheat-sheet control | ✓ SATISFIED | Body sanitizer + template pin; download CTAs are Phase 33 |

**Coverage:** 3/3 requirements satisfied. No orphaned IDs: REQUIREMENTS.md maps KIND-01/02/03 only to Phase 30; all three appear in PLAN frontmatter.

### Prohibitions

All PLAN `must_haves.prohibitions` were checked as negative code facts (not silently passed):

| Prohibition | Status | Evidence |
| ----------- | ------ | -------- |
| Must not expose `topic_kind` as a reader/admin badge or add it to backend Material SELECT lists | held | `material_repository.py` SELECT omits `topic_kind`; no `topic_kind` under `backend/` or `web/` |
| Must not persist a third kind or hide kind inside `provenance_label` | held | Two-member allowlist + DB CHECK; assemble copies `topic_kind` separately from `provenance_label` |
| Must not treat invalid/empty/unknown/malformed classifier output as `practical` in Python | held | Garbage matrix → conceptual; sibling key `kind` does not unwrap |
| Must not fail-close a finished pass-1 draft because classifier transport failed; must not map classifier errors onto `stage=llm` | held | `except Exception: raw = None`; RuntimeError test; adapter has no `ArticleError` import |
| Must not fold classify into the pass-1 honesty prompt or send `body_markdown` / web extract to the classifier | held | Separate adapter; `BODY_SENTINEL` absent; `ARTICLE_SYSTEM_PROMPT` has no `topic_kind` |
| Must not delete talk chapter titles whose ATX text is not exactly `Гайд` | held | D-12 test keeps Guide / How-to / Как сделать / Tutorial / Шпаргалка |
| Must not render a disabled cheat-sheet download or insert `ссылки скоро появятся` as honest-absence copy | held | Substring stripped; no download control in this phase |
| Must not fail ingest because a `Гайд` heading leaked — strip then persist | held for specified content+furniture cases | See WR-02 warning for furniture-only body |

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. **12/12 honored**, `not_honored: []`. Non-blocking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `tests/unit/test_topic_kind.py` | KIND-01, KIND-02 | all | 0 | no | value | PASS |
| `tests/unit/test_ingest_pipeline.py` (kind cases) | KIND-01, KIND-02 | all | 0 | no | behavioral | PASS |
| `tests/unit/test_deepseek_classifier.py` | KIND-01, KIND-02 | all | 0 | no | value | PASS |
| `tests/unit/test_article_draft_body_guide.py` | KIND-03 | all | 0 | no | value | PASS |
| `tests/unit/test_phase30_migration_014.py` | KIND-01 | all | 0 | no (SQL file is the oracle) | value | PASS |
| `tests/unit/test_supabase_draft_persister_contract.py` | KIND-01 | all | 0 | no | value | PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 2 (WARNING) — no test for two `## Гайд` blocks; no test that a furniture-only body still persists. Other active tests still cover KIND-03 for the specified matrix, so not a blocker.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `data-collection/src/data_collection/dto/_body.py` | 58–68 | First-match `_GUIDE_HEADING_RE.search` — second `## Гайд` survives | ⚠️ Warning | Confirmed empirically: body with two Гайд sections keeps the second. Clones `strip_audience_section` (Chesterton: planned). Typical pass-1 leak is one furniture heading |
| `data-collection/src/data_collection/dto/article_draft.py` | 14, 32–35 | After-validators can empty `body_markdown`; `Field(min_length=1)` is not re-checked | ⚠️ Warning | Furniture-only body → ArticleDraft `""` → `assemble_material_draft` `ValidationError`. Review WR-02 claimed ArticleDraft would raise; actual fail is later, uncaught, not `stage=llm`. Rare (body is only furniture) |
| `data-collection/src/data_collection/adapters/deepseek_classifier.py` | 50–58 | Title/dek interpolated outside the transcript fence | ⚠️ Warning | Matches PLAN 02 (“title, dek, and transcript fenced”). Review WR-03 is a spec-level hardening note for Phase 31 quota, not a failed must-have |
| `data-collection/src/data_collection/dto/_body.py` | 25, 68 | Placeholder replace is case-sensitive | ℹ️ Info | D-10 asks for the exact substring; `Ссылки скоро появятся` would survive |
| `supabase-integration/migrations/014_phase30_materials_topic_kind.sql` | 28–46 | `CREATE FUNCTION` without `OR REPLACE` is not re-runnable | ℹ️ Info | One-way arity change; already applied |
| `tests/unit/test_phase30_migration_014.py` | 154–169 | `git diff -- file` only sees the working tree | ℹ️ Info | Committed 007–009 edits would still pass; real T-30-06 guard is the 014 DROP/CREATE pin |
| Live `pg_proc` / CHECK | — | `POSTGRES_URL` unset; MCP `raw_sql` / `describe_table` unavailable | ℹ️ Info | Column independently confirmed via PostgREST. `pronargs=13` and CHECK rest on operator screenshot + SQL contract tests, not a second live `pg_proc` probe |

**Debt-marker gate:** no `TBD` / `FIXME` / `XXX` in phase production files. `_GUIDE_PLACEHOLDER` is the product substring, not a stub.

**Anti-patterns:** 7 found (0 blockers, 3 warnings, 4 info)

### Human Verification Required

N/A — Infrastructure/foundation phase with no user-facing elements.
All acceptance criteria are verifiable programmatically.
Plan 04 `checkpoint:human-verify` already ran (operator Applied 2026-10-29); the live column is independently visible via PostgREST. That human-check sits on a blocking checkpoint, not on an `auto` task, so it is not re-harvested here.

### Gaps Summary

**No gaps found.** Phase goal achieved. Ready to proceed.

Roadmap success criteria 1–3 hold: closed kind on the draft, invalid kind → conceptual with extras unwired, Гайд furniture stripped from pass-1 bodies. Later phases 31–33 add Tavily, pass-2 extras, and download CTAs; they do not substitute for this floor.

### Confirmation-bias disconfirmation

1. **Partial requirement:** KIND-03 strip is first-match; a second `## Гайд` is not deleted. Specified PLAN cases still pass.
2. **Test that does not fully prove the claim:** `test_applied_007_008_009_files_unchanged_relative_to_git_blob` only diffs the working tree (IN-04). The DROP-then-CREATE pin is the real guard.
3. **Uncovered error path:** body that is only `## Гайд` / only the placeholder empties `ArticleDraft.body_markdown` and then fails at assemble with an uncaught `ValidationError`.

---

## Verification Metadata

**Verification approach:** Goal-backward from ROADMAP Phase 30 success criteria + PLAN 01–04 `must_haves` (plan adds detail, does not subtract SC-1…SC-3)
**Must-haves source:** ROADMAP.md success criteria merged with 30-01…30-04 PLAN.md frontmatter
**Automated checks:** 70 named tests passed; live PostgREST column probe passed; dual-heading and furniture-only spot-checks recorded as warnings
**Human checks required:** 0
**MVP mode:** dormant (goal is not a User Story)

---
_Verified: 2026-10-29T18:10:34Z_
_Verifier: Claude (gsd-verifier)_
