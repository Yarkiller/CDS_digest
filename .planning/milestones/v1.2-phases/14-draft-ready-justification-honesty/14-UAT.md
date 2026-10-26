---
status: complete
phase: 14-draft-ready-justification-honesty
source: [14-VERIFICATION.md]
started: 2026-10-03T19:10:00Z
updated: 2026-10-04T07:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Live per-row promote (G-14-1 live re-check)
expected: On live Supabase data (VITE_USE_MOCKS=false), promote a draft material with a non-empty body via per-row «Сделать ready»; `POST /admin/materials/{id}/ready` returns 200 (not 503) and the badge flips to «готов» after the silent refetch.
result: pass
evidence: "Live (VITE_USE_MOCKS=false, Supabase knowledge-db.ru). Demoted material 12 to draft in DB; row rendered «черновик Сделать ready одобрен (в шортлист)» and footer «Отправка недоступна.». Clicked «Сделать ready» → intercepted fetch recorded POST http://127.0.0.1:8000/admin/materials/12/ready → 200. Badge flipped to «готов», «Сделать ready» disappeared, footer hint became «Сначала откройте превью письма.». DB materials.id=12 → status=ready. Re-POST via authenticated session twice → both 200 {material_id:12,status:ready} (idempotent no-op). published_at stayed null throughout."

### 2. Long title + ready CTA layout (14-03 backstop)
expected: Open Admin Digest with a long draft title; the title wraps with `break-words` and the draft badge + «Сделать ready» stay usable in the meta flex wrap (clickable, no overflow clipping).
result: pass
evidence: "At a 390px viewport with an injected ~3x long title on the draft row: title element class `break-words font-medium text-ink`, computed `overflow-wrap: break-word`; wrapped to 1080px tall with right edge inside the viewport; badge «черновик» and «Сделать ready» both still usable (non-zero size, inside viewport); page and row horizontal overflow 0px."

### 3. Long factor caption / empty justification wrap (14-03 backstop)
expected: Render a row with a long populated factor caption and a row with the exact empty sentence; both wrap with `break-words` inside `max-w-[12rem]` without breaking the shortlist row grid.
result: pass
evidence: "Factor caption element class `mt-1 max-w-[12rem] break-words text-xs text-muted`, computed `max-width: 192px`, `overflow-wrap: break-word`. Empty state renders the exact D-15 copy «Обоснование недоступно — скоринг не запускался» on every row. With a long injected caption at 390px it wrapped (80px tall) at exactly 192px width with no overflow and the row grid stayed intact."

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

<!-- No goal-blocking gaps after re-verification (19/20). The prior round's gaps are closed: -->
<!-- G-14-1 / G-14-4 closed by 14-06 (FK-hinted `material_relations!material_relations_from_material_id_fkey(to_material_id)` embed + offline PGRST201 regression) -->
<!-- G-14-2 closed by 14-07 (batch promote CTA + «Уберите черновики…» hint + handler/import removed; sendHint reordered; per-row control + D-85 gate intact) -->
<!-- G-14-3 closed by 14-08 (global `button:not(:disabled){cursor:pointer}` base rule + computed-cursor Playwright lock) -->

## Previous Round (closed)

The 2026-10-03T17:25Z UAT round diagnosed 4 gaps (G-14-1 blocker, G-14-2 major, G-14-3 cosmetic, G-14-4 major) and 2 passes
(tests 3 and 4). Those gaps were planned as 14-06/14-07/14-08 and are closed, verified, and regression-locked —
see `14-VERIFICATION.md` (re-verification section). Tests 2, 5 and 6 from the prior round are obsolete (the batch promote
surface they exercised was removed by 14-07).

## Deferred Follow-Ups

- test: 1
  idea: "UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран»."
  deferred_at: 2026-10-03
