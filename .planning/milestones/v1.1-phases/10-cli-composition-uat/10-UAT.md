---
status: complete
phase: 10-cli-composition-uat
requirement: CLI-03
decisions: [D-13, D-14, D-15, D-16]
source:
  - 10-01-SUMMARY.md
  - 10-02-SUMMARY.md
  - 10-03-SUMMARY.md
  - 10-04-PLAN.md
  - 10-05-SUMMARY.md
started: 2026-09-29
updated: 2026-10-02T09:17:00.000Z
approved: 2026-10-01
---

# Phase 10 — Manual UAT (CLI-03)

Four-video matrix (D-14). Operator picked live captioned URLs at UAT time (D-15). Evidence is this note only — **do not add a Playwright test** for `/admin/digest` live UAT (D-13). Do not modify `backend/` or `web/` so drafts appear. Do not paste `SUPABASE_SECRET_KEY` / `DEEPSEEK_API_KEY` into this file (T-10-11).

Operator approved 2026-10-01. Full watch URLs were not pasted in the approval note; rows are identified by `material_id`, rank, and the slug the operator recorded (middle ellipsized in that note — not expanded here).

## Command (CLI-05 / D-02)

```bash
# from repo root — ingestion-service/.env only (never root backend .env)
uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast
```

See also: `docs/agents/local-platform-runbook.md` §5d.

## Digest checks per row (D-16)

For each video, open `/admin/digest` and confirm:

- [x] Row is on an **unsent** shortlist batch — batch_id=3, ranks 1–4, overflow not triggered (4 < 5)
- [x] Material `status=draft` — badge `[draft]` on all four
- [x] Body is **Russian** — confirmed on reader `/materials/<slug>` (preview modal shows title+dek only; see Follow-ups)
- [x] English source: provenance label ends with ` · пер. с англ.` — rows 2 and 4
- [x] Lecture headings present: `## Тезис` / `## Ход рассуждения` / `## Вывод` — row 2 (EN lecture); row 1 is lecture+ru
- [x] Podcast headings present: `## О чём разговор` / `## Позиции` / `## Что запомнить` — row 4 (EN podcast)

D-16 body, provenance, and headings were confirmed via the reader URL. The admin email preview modal does not show them. That limitation is a Phase 11 follow-up, not a CLI-03 failure.

Optional idempotency (CLI-02): re-run material id 9 → `material_id=9`, slug unchanged, `batch_id=3`, `rank=1`, `already_saved=true`. No duplicate rows (migration 008 stored slug).

## Current Test

[testing complete]

## Matrix rows

### 1. lecture + ru

| Field | Value |
|-------|-------|
| URL | not pasted in approval (D-15); video id suffix `Ch-l6-66Uyc` |
| template | `lecture` |
| material_id | 9 |
| slug | `obviazka-vazhnee-modeli-...-Ch-l6-66Uyc` |
| rank | 1 |
| batch_id | 3 |
| already_saved (first run) | false |
| /admin/digest (D-16) | passed — visible, rank 1, badge `[draft]`; reader has no translation suffix |

result: passed

### 2. lecture + en

| Field | Value |
|-------|-------|
| URL | not pasted in approval (D-15); video id suffix `JpGtOfSgR-c` |
| template | `lecture` |
| material_id | 10 |
| slug | `vvedenie-v-strukturu-ai-gramotnosti-...-JpGtOfSgR-c` |
| rank | 2 |
| batch_id | 3 |
| already_saved (first run) | false |
| EN provenance ends with ` · пер. с англ.` | passed (reader) |
| Headings | `Тезис` / `Ход рассуждения` / `Вывод` |
| Body | Russian |
| /admin/digest (D-16) | passed — visible, rank 2, badge `[draft]` |

result: passed

### 3. podcast + ru

| Field | Value |
|-------|-------|
| URL | not pasted in approval (D-15); video id suffix `wp7izqZmiWM` |
| template | `podcast` |
| material_id | 11 |
| slug | `detsentralizovannyi-ai-bitkoin-...-wp7izqZmiWM` |
| rank | 3 |
| batch_id | 3 |
| already_saved (first run) | false |
| /admin/digest (D-16) | passed — visible, rank 3, badge `[draft]`; reader has no translation suffix |

result: passed

### 4. podcast + en

| Field | Value |
|-------|-------|
| URL | not pasted in approval (D-15); video id suffix `DB9mjd-65gw` |
| template | `podcast` |
| material_id | 12 |
| slug | `interviu-sema-altmana-stargate-agi-...-DB9mjd-65gw` |
| rank | 4 |
| batch_id | 3 |
| already_saved (first run) | false |
| EN provenance ends with ` · пер. с англ.` | passed (reader) |
| Headings | `О чём разговор` / `Позиции` / `Что запомнить` |
| Body | Russian |
| /admin/digest (D-16) | passed — visible, rank 4, badge `[draft]` |

result: passed

## Idempotency (CLI-02)

Re-run of material id 9: `material_id=9`, slug unchanged, `batch_id=3`, `rank=1`, `already_saved=true`. No duplicate rows. Stored slug comes from migration 008.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None for CLI-03. UI observations below are follow-ups for Phase 11. They were not implemented in this plan.

## Follow-ups (Phase 11 — not CLI-03 failures)

1. Admin email preview modal shows only title and dek. Body, provenance, and headings are not visible there. Proposed: full `body_markdown`, `provenance_label`, char/word count, and a link to `/materials/<slug>`.
2. "Превью письма" lists titles only, not intro, summaries, links, or HTML. Proposed: a real email HTML preview.
3. "test-header" leaked into the preview from seed/test data. Needs data cleanup.
4. Interstitial connecting text ignores `\n\n` (whitespace not preserved). Proposed: `white-space: pre-wrap` or split into `<p>`.
5. No UI to flip material status `draft` → `ready`; send is blocked by D-85. UAT workaround used SQL `UPDATE materials SET status='ready' WHERE id IN (9,10,11,12)`. Proposed: an admin button, auto-ready, or PIPE-01.
6. "Обоснование недоступно" — `score_factors` is not filled by ingestion (PIPE-01 deferred). Not a blocker.
