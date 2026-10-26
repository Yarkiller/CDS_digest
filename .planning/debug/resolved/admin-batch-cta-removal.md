---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Batch promote CTA + promoteApprovedDrafts handler + approved-drafts hint removed from web/src (no admin-mark-ready-batch); per-row ready stays"
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: unknown
---

# DEBUG — remove batch promote CTA + approved-drafts hint (G-14-2)

**Status:** root cause found (intentional product change, not a defect)
**Phase:** 14-draft-ready-justification-honesty
**Date:** 2026-10-03

## Cause

Deliberate UX decision by the operator: the single-operator workflow does not want a batch
«Сделать ready все одобренные черновики (N)» control or the «Уберите черновики из одобренных или
дождитесь ready.» hint. The per-row «Сделать ready» stays (and must be fixed — G-14-1).

## What exists today

- Batch CTA render: `web/src/pages/AdminDigestPage.jsx:837-847` (`data-testid="admin-mark-ready-batch"`).
- Batch handler: `promoteApprovedDrafts` — `web/src/pages/AdminDigestPage.jsx:374-...`.
- Hint copy: `sendHint` memo — `web/src/pages/AdminDigestPage.jsx:253-263` (branch `approvedDrafts.length > 0` → «Уберите черновики из одобренных или дождитесь ready.»).
- Confirm dialog copy «Сделать ready N одобренных черновиков?» is only reachable from the removed handler.
- FE API `markReadyBatch` — `web/src/services/adminApi.js` (only consumer is the removed handler).
- Tests asserting the batch control: `tests/admin.spec.js` (`batch Сделать ready … issues one markReadyBatch`, and `approved draft blocks send with draft hint` asserts the hint + footer `ul` count) and `tests/unit/test_admin_mark_ready.js` (batch single-call shape).
- Backend batch route `POST /admin/materials/ready` + `mark_materials_ready` become unused by the FE if the CTA is removed.

## Open design point for the plan

With the draft hint branch removed, the footer must render something coherent when
`approvedDrafts.length > 0` (leading candidate: fall through to the existing
`approvedReady.length === 0` branch → «Нет одобренных ready-материалов для отправки.»). Decide
whether the `sendUnlocked` gate keeps requiring `approvedDrafts.length === 0` (yes, to preserve
D-85) and whether the now-unused FE/backend batch path is deleted or merely unhooked.
