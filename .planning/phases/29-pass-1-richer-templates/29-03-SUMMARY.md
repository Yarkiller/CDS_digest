---
phase: 29-pass-1-richer-templates
plan: 03
subsystem: ingestion-live-proof
tags: [deepseek, live-ingest, uat, pass-1, blocking-human]

requires:
  - phase: 29-pass-1-richer-templates
    provides: lecture.md / podcast.md talk-shaped frames, ARTICLE_SYSTEM_PROMPT, inverted scaffold pins
provides:
  - live ingest proof of ART-01/ART-02/ART-03 on a fresh youtube_video_id
  - 29-UAT.md with heading list, per-bullet facts audit, response_chars, owner resume-signal
  - evidence/ingest-run-2.log, transcript-2.txt, draft-2.json for the approved draft
affects: [30-classifier]

actuals:
  tokens: 0
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - live proof is a fresh youtube_video_id with already_saved false
    - digit audit rows carry a transcript fragment or the literal NOT FOUND
    - blocking-human resume-signal is approved or a named defect, never done

key-files:
  created:
    - .planning/phases/29-pass-1-richer-templates/evidence/ingest-run-2.log
    - .planning/phases/29-pass-1-richer-templates/evidence/transcript-2.txt
    - .planning/phases/29-pass-1-richer-templates/evidence/draft-2.json
    - .planning/phases/29-pass-1-richer-templates/29-03-SUMMARY.md
  modified:
    - .planning/phases/29-pass-1-richer-templates/29-UAT.md
    - .planning/phases/29-pass-1-richer-templates/29-VALIDATION.md
    - .planning/phases/29-pass-1-richer-templates/29-CONTEXT.md
    - data-collection/src/data_collection/templates/lecture.md
    - data-collection/src/data_collection/templates/podcast.md
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - web/src/pages/MaterialPage.jsx
    - web/src/utils/markdownSections.js
    - tests/unit/test_article_templates.py
    - tests/unit/test_deepseek_article_adapter.py
    - tests/unit/test_markdown_sections.js
    - tests/web-app.spec.js

key-decisions:
  - "Owner path 1,2,4 (2026-10-27) reopened templates and MaterialPage after Attempt 3 rejection: interesting Конкретика, definitions/footnotes/reference data, shared body frame with own cards for Конкретика and Зачем это СВА"
  - "D-18/D-19 owner override: pass-1 may add textbook definitions, footnotes and reference data; Tavily stays Phase 32; talk-stated names/numbers/versions are not invented"
  - "Attempt 3 material_id=26 is left as-is; proof of the rewritten prompts is Attempt 4 material_id=27"
  - "Live YouTube egress for this proof is direct (YOUTUBE_PROXY_URL cleared in-process); SOCKS dest-connect was refused on Attempts 1-2"

patterns-established:
  - "Pattern: owner rejection names a defect; a code rescue of the rejected row is forbidden; a new ingest observes the rewritten prompt"
  - "Pattern: resume-signal approved closes Task 3; done is operator/page acknowledgement, not editorial approval"
  - "Pattern: reader chrome frames the whole body once and keeps Конкретика / Зачем это СВА as nested cards"

requirements-completed: [ART-01, ART-02, ART-03]

coverage:
  - id: D1
    description: "A freshly ingested lecture draft has talk-shaped ## and none of the six legacy scaffold headings"
    requirement: ART-01
    verification:
      - kind: manual
        ref: .planning/phases/29-pass-1-richer-templates/29-UAT.md
        status: pass
    human_judgment: true
  - id: D2
    description: "Every ## Конкретика talk-fact is traced to the captured transcript; editorial definitions are labelled, not scored as NOT FOUND"
    requirement: ART-02
    verification:
      - kind: manual
        ref: .planning/phases/29-pass-1-richer-templates/29-UAT.md
        status: pass
    human_judgment: true
  - id: D3
    description: "One ## Зачем это СВА when an analog exists; dek stays a 1-2 sentence hook; no invented duty"
    requirement: ART-03
    verification:
      - kind: manual
        ref: .planning/phases/29-pass-1-richer-templates/29-UAT.md
        status: pass
    human_judgment: true
  - id: D4
    description: "response_chars is recorded against the 16000 band and does not trigger a re-run"
    requirement: ART-01
    verification:
      - kind: manual
        ref: .planning/phases/29-pass-1-richer-templates/evidence/ingest-run-2.log
        status: pass
    human_judgment: false

duration: 2d
completed: 2026-10-28
status: complete
---

# Phase 29 Plan 03: Live ingest proof Summary

**A fresh lecture ingest through the rewritten pass-1 templates lands a draft whose `##` follow the talk, whose `## Конкретика` traces to the transcript (plus labelled editorial definitions), and whose `## Зачем это СВА` is one honest analog — owner resume-signal `approved` on material 27**

## Performance

- **Started:** 2026-10-26T18:47:47Z
- **Completed:** 2026-10-28
- **Tasks:** 3 (pre-flight+ingest, digit audit, blocking-human)
- **Wave gate:** `uv run pytest` → **1197 passed, 1 warning in 19.17s** (before close-out)

## Accomplishments

- Attempt 4 ingested `https://www.youtube.com/watch?v=JzEd26jQ1Ys` with `--template lecture --debug` after clearing `YOUTUBE_PROXY_URL` in-process. `already_saved: false`, `material_id=27`, `slug=vektornaia-pamiat-na-svoem-servere-postgresql-pgve-JzEd26jQ1Ys`, `template=lecture`, `response_chars=10011` (below 16000), `transcript_chars=19801`.
- Digit audit: eight talk-fact bullets traced to `evidence/transcript-2.txt`; one editorial embedding definition labelled under the D-18 override. Zero `NOT FOUND` on a speaker-stated number, name, tool or version.
- Ten topic-shaped `##`; six legacy scaffolds absent; one `## Зачем это СВА`; `dek` is a two-sentence hook; `## Аудитория` stripped.
- Owner typed `approved` on 2026-10-28. Attempt 3 (`material_id=26`) stays the rejected row and was not patched.

## Task Commits

1. **Owner path 1/2/4 production** - `594452f` (feat)
2. **This SUMMARY + UAT + Attempt 4 evidence** - this commit
3. **STATE / ROADMAP / REQUIREMENTS** - following commit

## Observed ids (Attempt 4)

| Field | Value |
|-------|--------|
| youtube_video_id | `JzEd26jQ1Ys` |
| material_id | 27 |
| slug | `vektornaia-pamiat-na-svoem-servere-postgresql-pgve-JzEd26jQ1Ys` |
| batch_id / rank | 7 / 4 |
| already_saved | false |
| response_chars | 10011 |
| Owner resume-signal | `approved` (2026-10-28) |

## Deviations from Plan

### Auto-fixed Issues

None as plan-text auto-fixes.

### Owner-directed scope (recorded, not silent)

**1. Attempt 3 rejection → path 1, 2, 4**
- **Found during:** Task 3 (blocking-human) on `material_id=26`
- **Issue:** Owner named three defects: visual frames; Конкретика as inventory; transcript-only lock blocking definitions/footnotes.
- **Fix:** Explicit override of D-18/D-19 and ART-02 editorial quality; rewrite `lecture.md` / `podcast.md` / `ARTICLE_SYSTEM_PROMPT`; MaterialPage one body frame + nested cards for `## Конкретика` and `## Зачем это СВА`. Live row 26 not patched. Proof moved to Attempt 4.
- **Files modified:** templates, `deepseek_article.py`, `MaterialPage.jsx`, `markdownSections.js`, tests, CONTEXT/REQUIREMENTS
- **Verification:** unit pins + Playwright frame test + Attempt 4 digit audit + owner `approved`

**2. SOCKS captions-proxy precondition**
- **Found during:** Attempts 1–2
- **Issue:** httpx oEmbed through SOCKS dest-connect refused; TCP:1080 open is not sufficient.
- **Fix:** Operator-authorized direct YouTube egress (`.env` unchanged; proxy cleared in-process). Not a production adapter edit.
- **Verification:** Attempt 3 and 4 both `exit 0` with `stage=metadata` HTTP success on the direct path

**Total deviations:** 2 owner/operator (0 silent production rescues of a failed proof)
**Impact on plan:** Live proof observes the rewritten prompts on a new video. Pitfall 4 lifted for renderer CSS only.

## Authentication Gates

Admin preview of a `status=draft` row (`/admin/materials/{slug}`). Reader `/materials/{id}` 404s drafts.

## Issues Encountered

- Attempt 1: `stage=metadata` `ProxyError`
- Attempt 2: oEmbed probe ≠ HTTP 200; ingest not spent
- Preview URL is slug, not numeric `material_id`
- Resume-signal `done` is not `approved`

## User Setup Required

- `ingestion-service/.env`: `DEEPSEEK_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (and `YOUTUBE_PROXY_URL` present but cleared in-process for this host)
- Admin session on `VITE_USE_MOCKS=false` for `/admin/materials/{slug}`

## Next Phase Readiness

Ready for `/gsd-plan-phase 30` (classifier `practical | conceptual`). ART-01/ART-02/ART-03 are complete. Tavily, cheat sheets, and reader sources stay later phases.

No stubs. No new network endpoint, auth path, or schema change beyond the plan's `<threat_model>` plus the owner-directed renderer CSS.

## Self-Check: PASSED

- FOUND: `.planning/phases/29-pass-1-richer-templates/evidence/ingest-run-2.log`
- FOUND: `.planning/phases/29-pass-1-richer-templates/evidence/transcript-2.txt`
- FOUND: `.planning/phases/29-pass-1-richer-templates/evidence/draft-2.json`
- FOUND: `.planning/phases/29-pass-1-richer-templates/29-UAT.md`
- FOUND: `stage=llm … template=lecture response_chars=10011`
- FOUND: owner resume-signal `approved` 2026-10-28
- FOUND: `594452f` feat(29): rewrite Конкретика and frame article body

---
*Phase: 29-pass-1-richer-templates*
*Plan: 03*
