---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Global @layer base rule button:not(:disabled) { cursor: pointer } at web/src/index.css:38 covers the control"
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: unknown
---

# DEBUG — «Превью материала» has no pointer cursor (G-14-3)

**Status:** root cause found
**Phase:** 14-draft-ready-justification-honesty
**Date:** 2026-10-03

## Cause

The «Превью материала» button does not carry a `cursor-pointer` class, and the stylesheet has no
global rule making `<button>` show a pointer:

- `web/src/index.css` — no `cursor` rule (grep: no matches).
- `web/src/pages/AdminDigestPage.jsx:812-819` — the button's `className` list has no `cursor-pointer`,
  unlike sibling controls that do (e.g. the dialog «Закрыть» button asserted for
  `classList.contains("cursor-pointer")` in `tests/admin.spec.js`).

## Suggested fix direction (non-binding)

Add `cursor-pointer` to the «Превью материала» button; audit the other Phase 14 interactive
controls (per-row «Сделать ready», any remaining footer controls) for the same omission for
consistency. Regression-lock via Playwright asserting the class / computed `cursor: pointer`.

## Files involved

- `web/src/pages/AdminDigestPage.jsx` — «Превью материала» button className
- `web/src/index.css` — (no global cursor rule; consider whether a base rule is the better fix)
