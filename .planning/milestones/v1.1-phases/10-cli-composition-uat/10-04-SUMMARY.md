---
phase: 10-cli-composition-uat
plan: 04
subsystem: infra
tags: [ingest-cli, composition, CLI-03, D-16, manual-uat]

requires:
  - phase: 10-cli-composition-uat
    provides: Typer ingest, migration 008 already_saved, ingestion-service/.env (10-01, 10-02, 10-05)
  - phase: 09-draft-persist-shortlist-enqueue
    provides: persist_draft_and_enqueue and /admin/digest reader path
provides:
  - Live build_ingest_deps wiring through composition factories
  - Operator-approved four-video CLI-03 evidence in 10-UAT.md
affects:
  - Phase 11 admin preview, email HTML, draft-to-ready, and score_factors follow-ups

actuals:
  tokens: 3507
  tasks: 3
  commits: 4

plan_head_before: 5c64fc4063023e68282c78d491484556be8bb535
plan_head_after: 7f43c04499ff90c66b4cf0858e44dd7c20343962

tech-stack:
  added: []
  patterns:
    - Live ingest deps come from Settings.from_env and composition factories
    - CLI-03 evidence is a manual 10-UAT.md note, not a Playwright spec

key-files:
  created:
    - .planning/phases/10-cli-composition-uat/10-UAT.md
    - tests/unit/test_build_ingest_deps_wiring.py
  modified:
    - ingestion-service/src/ingestion_service/cli.py
    - ingestion-service/src/ingestion_service/composition/clients.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "CLI-03 closed on the D-14 four-video matrix; D-16 body, provenance, and headings confirmed on /materials/<slug>"
  - "Admin preview and email-HTML gaps are Phase 11 follow-ups, not CLI-03 failures, and were not implemented here"
  - "Approval note omitted full watch URLs; 10-UAT.md keeps the operator's ellipsized slugs and material ids 9-12"

patterns-established:
  - "Pattern: UAT ingest uses uv run --env-file ingestion-service/.env only"
  - "Pattern: reader URL is the D-16 check while the admin preview modal stays title+dek"

requirements-completed: [CLI-03]

coverage:
  - id: D1
    description: Live build_ingest_deps wires captions, metadata, article, and persist through composition factories
    requirement: CLI-03
    verification:
      - kind: unit
        ref: "tests/unit/test_build_ingest_deps_wiring.py"
        status: pass
    human_judgment: false
  - id: D2
    description: Runbook UAT command uses ingestion-service/.env only
    requirement: CLI-03
    verification:
      - kind: unit
        ref: "uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingestion_env_example.py tests/unit/test_build_ingest_deps_wiring.py (24 passed with sibling phase-10 unit files)"
        status: pass
    human_judgment: false
  - id: D3
    description: Four real captioned videos are drafts on unsent batch 3 and pass D-16 on the reader
    requirement: CLI-03
    verification:
      - kind: manual_procedural
        ref: ".planning/phases/10-cli-composition-uat/10-UAT.md"
        status: pass
    human_judgment: true
    rationale: "Operator must confirm /admin/digest badges and Russian reader bodies; no Playwright coverage by D-13"

duration: 48h
completed: 2026-10-01
status: complete
---

# Phase 10 Plan 04: Live composition + four-video UAT Summary

**Live `ingest` wiring is in place, and the operator approved four captioned videos (materials 9–12, batch 3) as Russian drafts with D-16 checks on the reader.**

## Performance

- **Duration:** ~48h wall, including the human-verify wait (wiring commits 2026-09-29; evidence close-out 2026-10-01)
- **Started:** 2026-09-29T18:28:22Z
- **Completed:** 2026-10-01T19:20:00Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- `build_ingest_deps` wires YouTube captions, oEmbed metadata, DeepSeek, and `SupabaseDraftPersister` through composition factories; adapters still do not read `os.environ`
- Runbook documents `uv run --env-file ingestion-service/.env ingest`
- CLI-03: four drafts on unsent batch 3 (ranks 1–4, overflow not triggered). EN lecture and EN podcast are Russian on `/materials/<slug>` with ` · пер. с англ.` and the D-16 headings. RU rows have no translation suffix
- Re-run of material 9 returned the same id, slug, batch, and rank with `already_saved=true` and no duplicate row

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Live builder wiring tests** — `6a78750` (test)
2. **Task 1 GREEN: Wire live ingest deps** — `8124fd1` (feat)
3. **Task 2: Four-video UAT checklist template** — `ca29fb3` (docs)
4. **Task 3: Record approved UAT evidence** — `7f43c04` (docs)

**Plan metadata:** docs commit with this summary, STATE.md, ROADMAP.md, and REQUIREMENTS.md

## Files Created/Modified

- `ingestion-service/src/ingestion_service/cli.py` — default path uses live `build_ingest_deps`
- `ingestion-service/src/ingestion_service/composition/clients.py` — composition factories for the four adapters
- `tests/unit/test_build_ingest_deps_wiring.py` — monkeypatched factory smoke for the live builder
- `docs/agents/local-platform-runbook.md` — UAT command uses `ingestion-service/.env` only
- `.planning/phases/10-cli-composition-uat/10-UAT.md` — four passed rows plus Phase 11 follow-ups

## UAT evidence (operator approved)

Batch 3, overflow not triggered (4 < 5). No secrets recorded.

| Row | material_id | rank | already_saved (first run) | slug (as approved) |
|-----|-------------|------|----------------------------|--------------------|
| lecture+ru | 9 | 1 | false | `obviazka-vazhnee-modeli-...-Ch-l6-66Uyc` |
| lecture+en | 10 | 2 | false | `vvedenie-v-strukturu-ai-gramotnosti-...-JpGtOfSgR-c` |
| podcast+ru | 11 | 3 | false | `detsentralizovannyi-ai-bitkoin-...-wp7izqZmiWM` |
| podcast+en | 12 | 4 | false | `interviu-sema-altmana-stargate-agi-...-DB9mjd-65gw` |

Idempotency: re-run id 9 → material_id 9, slug unchanged, batch_id 3, rank 1, `already_saved=true`.

`/admin/digest`: all four visible, ranks 1–4, badge `[draft]`.

Reader `/materials/<slug>`:

- #2 EN lecture: Russian body, ` · пер. с англ.`, headings Тезис / Ход рассуждения / Вывод
- #4 EN podcast: Russian body, suffix, headings О чём разговор / Позиции / Что запомнить
- #1 and #3 RU: no translation suffix

D-16 passed via the reader URL. Full watch URLs were not in the approval note.

## Decisions Made

- Treat the four-video matrix as satisfying CLI-03 “3–5” (D-14) without adding Playwright (D-13)
- Confirm headings, Russian body, and EN provenance on the reader, because the admin preview modal only shows title and dek
- Leave Phase 11 UI proposals unimplemented

## Deviations from Plan

### Auto-fixed Issues

None during this close-out. No `backend/` or `web/` edits.

Task 1 placed the wiring smoke in `tests/unit/test_build_ingest_deps_wiring.py` (plan `<files>` also named `tests/unit/test_ingestion_clients.py`). The new file is what the RED/GREEN commits shipped.

### Follow-ups for Phase 11 (not CLI-03 failures, not implemented)

1. Admin email preview modal shows only title and dek. Proposed: full `body_markdown`, `provenance_label`, char/word count, link to `/materials/<slug>`.
2. "Превью письма" lists titles only. Proposed: real email HTML preview.
3. "test-header" leaked into the preview from seed/test data. Needs data cleanup.
4. Interstitial connecting text ignores `\n\n`. Proposed: `white-space: pre-wrap` or split into `<p>`.
5. No UI to flip `draft` → `ready`; send blocked by D-85. UAT workaround was SQL `UPDATE materials SET status='ready' WHERE id IN (9,10,11,12)`. Proposed: admin button, auto-ready, or PIPE-01.
6. "Обоснование недоступно" — ingestion does not fill `score_factors` (PIPE-01 deferred). Not a blocker.

**Total deviations:** 0 auto-fixed. 6 operator observations deferred.
**Impact on plan:** CLI-03 stands as approved. No production UI fixes in this plan.

## Issues Encountered

None. Human-verify returned `approved`. Live ingest was not re-run during close-out.

## Verification

```text
uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_pipeline.py tests/unit/test_phase10_migration_008.py tests/unit/test_ingestion_env_example.py tests/unit/test_build_ingest_deps_wiring.py -q --tb=no
```

24 passed in 1.48s (2026-10-01).

## User Setup Required

None for this close-out. The approved UAT already used `ingestion-service/.env` (DeepSeek, Supabase service role, YouTube). Secrets are not copied here.

## Next Phase Readiness

Phase 10 plan 04 is complete. All five phase plans have summaries after this file lands. UI observations above are deferred and were not coded.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `.planning/phases/10-cli-composition-uat/10-04-SUMMARY.md`
- FOUND: `.planning/phases/10-cli-composition-uat/10-UAT.md`
- FOUND: `ingestion-service/src/ingestion_service/cli.py`
- FOUND: `tests/unit/test_build_ingest_deps_wiring.py`
- FOUND: `6a78750`, `8124fd1`, `ca29fb3`, `7f43c04`
- COMMITS_ACTUAL: 4 from plan_head_before `5c64fc4063023e68282c78d491484556be8bb535`
- Plan range touches no `backend/` or `web/` paths

---
*Phase: 10-cli-composition-uat*
*Completed: 2026-10-01*
