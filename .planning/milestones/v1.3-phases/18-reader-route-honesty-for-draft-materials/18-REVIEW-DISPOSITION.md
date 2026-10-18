---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "A stale `redirectToReader` survives the D-12 redirect — the reader route (and every later material navigation) renders nothing"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`forbidden` is never reset either — latent today, the same defect class as CR-01"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The D-12 redirect test asserts only the URL, so it cannot detect CR-01"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "`loadMaterial` is an unused prop — dead injection surface"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "`no-store` is set only on the success path"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`_SLUG_PATTERN` is imported across route modules while its sibling helper is duplicated"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "`mockSeatRole()` re-implements `meApi`'s role resolution"
  - id: IN-05
    severity: info
    disposition: deferred
    title: "An expired session on the preview endpoint is reported as a network failure"
open: 0
total: 8
recorded: 2026-10-15T12:41:00Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | tests/admin.spec.js:1289 RED + web/src/pages/MaterialPage.jsx:79-88 GREEN |
| WR-01 | warning | fixed | same fix — setForbidden(false) beside setRedirectToReader(false), web/src/pages/MaterialPage.jsx:86-88 |
| WR-02 | warning | fixed | tests/admin.spec.js:1289 new click-path test; the D-12 test carries a NOTE (WR-02) explaining why gotoAsRole's trailing page.reload() masks the handoff |
| IN-01 | info | deferred | removing an injected public prop is a public-surface change and the prop is inert; outside the phase files_modified — parked for a follow-up |
| IN-02 | info | deferred | no draft content can leak since the 200 is the only body-bearing response and it is no-store; hardening the 404 path is a separate concern |
| IN-03 | info | deferred | rectifying this needs a shared deps module touched by two route modules beyond the phase contract; parked as architecture tidy-up |
| IN-04 | info | deferred | test-mock duplication; consolidating requires editing meApi.js, outside the phase; parked |
| IN-05 | info | deferred | inherits mapHttpError behaviour; adding a 401 branch introduces a new error-code path that needs its own coverage; parked |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.

## Evidence for CR-01 / WR-02

`gotoAsRole` ends in `page.reload()`, and by then the client-side redirect has already moved the
document to `/materials/{slug}` — so the reload loads the *reader* URL in a fresh document and the
handoff under test is never observed. Measured (Chromium, `VITE_USE_MOCKS=true`, admin role):

| path | `material-not-found` | `<h1>` | verdict |
|---|---|---|---|
| direct load of the admin preview for a ready slug, then `reload()` (mirrors `gotoAsRole`) | 1 | Материал не найден | renders — but only because the reload discarded the handoff |
| direct load of the admin preview for a ready slug, no reload | 0 | none | blank — CR-01 |
| `/admin/digest` → «Превью материала» → «Открыть материал →» (the real user journey) | 0 | none | blank — CR-01 |
| control: draft preview `/admin/materials/sql-dashboards-for-audit-reporting` | 0 | SQL Dashboards for Audit Reporting | correct |

The new test drives the third row and fails `expect(locator).toBeVisible() — element(s) not found`
before the fix, and passes after it.
