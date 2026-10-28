---
phase: 29
slug: pass-1-richer-templates
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-26
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `29-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.3.0` (Python 3.12.13), `testpaths = ["tests/unit"]` |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — no `pytest.ini` |
| **Quick run command** | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~1.4 s quick / ~13.5 s full (measured baseline: 54 passed in 1.37 s; 1156 passed in 13.42 s) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green, plus the live-proof evidence file (`stage=llm … response_chars=…`) and the criteria 1–3 UAT checklist
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD (template pins) | 01 | 1 | ART-01 | T-29-03 (invented facts) | `lecture.md` / `podcast.md` carry the free-`##` frame; all six legacy scaffold literals absent | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — pin **rewrite** | ⬜ pending |
| TBD (loaded templates) | 01 | 1 | ART-01 | — | Loaded lecture + podcast templates expose the new frame for both kinds | unit | `uv run pytest tests/unit/test_article_templates.py::test_load_article_templates_returns_both_kinds -x` | ✅ exists — **rewrite** | ⬜ pending |
| TBD (message assembly) | 02 | 2 | ART-01 | T-29-01 (prompt injection) | Assembled user messages contain no scaffold literal and do not cross-leak the other kind's hint | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — **rewrite** | ⬜ pending |
| TBD (facts layer prompt) | 02 | 2 | ART-02 | T-29-03 (invented facts) | Both templates instruct `## Конкретика`: transcript-only, bullets-first, canonical names, omit-when-empty | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — new assertions | ⬜ pending |
| TBD (facts passthrough) | 02 | 2 | ART-02 | — | A scripted draft with `## Конкретика` passes through the adapter untouched | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — no change | ⬜ pending |
| TBD (СВА prompt) | 02 | 2 | ART-03 | T-29-03 (invented facts) | Both templates instruct `## Зачем это СВА`: analog bar, no invented duty, editorial voice, omit rule | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — new assertions | ⬜ pending |
| TBD (system prompt) | 02 | 2 | ART-03 | T-29-01 | Shared voice/no-recap rules added without losing the ten pinned honesty/language substrings | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — extend | ⬜ pending |
| TBD (audience strip) | 02 | 2 | (regress) | T-29-06 (prompt text leaking) | `## Аудитория` strip still works when new headings precede it | unit | `uv run pytest tests/unit/test_article_draft_body_audience.py -x` | ✅ exists — add 1 case | ⬜ pending |
| TBD (call shape) | 02 | 2 | (regress) | — | `response_format`, `thinking`, `stream=True`, no `max_tokens` unchanged | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — no change | ⬜ pending |
| TBD (budget guard) | 02 | 2 | (regress) | — | Long template with short transcript still exempt from transcript budget | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — no change | ⬜ pending |
| TBD (error taxonomy) | 02 | 2 | (regress) | T-29-05 (secret leakage) | `LLM_REASONS`, `stage=llm` / `llm_truncation` fail-closed unchanged | unit | `uv run pytest tests/unit/test_article_error_mapping.py -x` | ✅ exists — no change | ⬜ pending |
| TBD (live proof) | 03 | 3 | ART-01, ART-02, ART-03 | — | Ingested draft's `##` follow the talk; facts are transcript-traceable; СВА takeaway present when an analog exists; `dek` stays a hook | manual/live | `uv run --env-file ./ingestion-service/.env ingest <new-url> --template lecture --debug` + digit audit | ❌ **Wave 0** — UAT checklist + evidence capture | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_article_templates.py` — rewrite `test_lecture_md_contains_russian_headings` and `test_podcast_md_contains_russian_headings` into "frame present + scaffold absent"; update `test_load_article_templates_returns_both_kinds` off `## Тезис` / `## О чём разговор` (RED first, before editing the `.md` files).
- [x] `tests/unit/test_deepseek_article_adapter.py` — rewrite `test_lecture_prompt_contains_lecture_headings_not_podcast` and `test_podcast_prompt_contains_podcast_headings_not_lecture` to assert all six scaffold literals are absent from both messages and the shared headings present in both.
- [x] `tests/unit/test_article_draft_body_audience.py` — one case with the real new headings before the trailing `## Аудитория` block.
- [x] Evidence/UAT artifact for the live proof (checklist + captured `--debug` lines + the transcript used for the digit audit). Not a pytest file.
- [x] No framework install needed — pytest is already configured and the baseline suite (1156 passed) is green.

*Existing infra covers framework/config; the gaps above are test-content rewrites and one evidence artifact.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A real ingested lecture/podcast draft has `##` shaped by the talk and none of the six legacy scaffolds | ART-01 | Requires a live DeepSeek call plus a real transcript; the default suite never calls the network | `uv run --env-file ./ingestion-service/.env ingest <new-url> --template lecture --debug`; open `/admin/materials/{id}`; record the `##` list and confirm no scaffold heading appears |
| Every name / number / tool in `## Конкретика` appears in the transcript; no invented versions | ART-02 | Semantic ghost-diff review cannot be automated without a false-positive-heavy regex | Capture the transcript used for the run; audit each fact bullet against it (digit + canonical-name audit); record pass/fail per bullet |
| `## Зачем это СВА` present when an analog exists, `dek` still a 1–2 sentence hook, and no invented СВА duty/policy | ART-03 | Editorial judgment; owner-overridden by D-11/D-16 | Read the preview; confirm the section is present for an analog-bearing talk, quotes are `>`, and no policy/standard is asserted that is absent from the transcript |
| `response_chars` stays under the ~16K truncation-risk band | ART-01 (quality guard) | Only observable on a live run; adapter does not read `finish_reason` | Record `response_chars=` from `--debug`; `≥ 16000` is a **one-way owner escalation** (a `max_tokens` change is a locked-surface exception) — do not silently re-run; record the figure in the phase summary / `29-UAT.md` |

*If none: "All phase behaviors have automated verification."* — Not applicable: 4 manual-only behaviors above.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
