---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "material_status pill localised (chernovik/gotov) and triage caption qualified as odobren (v shorlist) in v1.2 Phase 14"
trigger: "UX: admin shortlist row shows `[draft]` badge AND «одобрен» on the same row, reads as a contradiction. Discovered during UAT verification of Phase 14 (G-14-2a)."
created: 2026-10-03T16:07:00Z
updated: 2026-10-03T16:07:00Z
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: investigating
---

## Current Focus

<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: The row renders two INDEPENDENT status dimensions side by side with no
  disambiguation — a raw `material_status` pill (`{item.material_status}` → `draft`) and a
  `decision` caption (`decisionCaption` → «одобрен»). For an approved draft both render
  unconditionally, producing the contradictory `draft` + «одобрен» pair.
test: Read AdminDigestPage.jsx row render block (lines ~735–801), decisionCaption (~70),
  and the D-02 Playwright test that locks the coexistence.
expecting: Confirm both badges render from separate fields in the same flex container with
  no tooltip/legend explaining the two axes.
next_action: Record evidence + Resolution.root_cause; return ROOT CAUSE FOUND (diagnose only).

## Symptoms

<!-- Written during gathering, then IMMUTABLE -->

expected: The admin shortlist row's status indicators read unambiguously — a row should not
  simultaneously show a `[draft]` badge AND an approval state (одобрен) in a way that looks
  contradictory to the user.
actual: User reports the `[draft]` badge plus «одобрен» reads as a contradiction on the same row.
errors: None.
reproduction: Open Admin Digest page and look at an approved draft row's status badges/labels.
started: Discovered during UAT verification of Phase 14.

## Eliminated

<!-- APPEND only - prevents re-investigating -->

(none yet)

## Evidence

<!-- APPEND only - facts discovered -->

- timestamp: 2026-10-03T16:07:00Z
  checked: web/src/pages/AdminDigestPage.jsx decisionCaption (lines 70–74)
  found: `decisionCaption(decision)` returns 'одобрен' for 'approved', 'отклонён' for
    'rejected', else null. It maps ONLY the shortlist triage decision; it knows nothing
    about material_status.
  implication: «одобрен» is purely a `decision` label.

- timestamp: 2026-10-03T16:07:00Z
  checked: web/src/pages/AdminDigestPage.jsx shortlist row render (lines 735–801)
  found: Inside each `<li>` (data-testid "admin-shortlist-row") a single
    `<div className="mt-2 flex flex-wrap items-center gap-2">` renders, in order:
    (1) a `<span>` pill whose text is the RAW `{item.material_status}` (line 768) —
        so it prints `draft`/`ready` verbatim;
    (2) the «Сделать ready» button when `material_status === 'draft'` (lines 770–780);
    (3) `{caption ? <span className="text-xs text-muted">{caption}</span> : null}`
        (line 781) — printing «одобрен» when `decision === 'approved'`.
  implication: For `decision==='approved' && material_status==='draft'`, items (1) and (3)
    render in the SAME container on the SAME row with no separator/disambiguation —
    the `draft` pill sits directly next to the «одобрен» caption.

- timestamp: 2026-10-03T16:07:00Z
  checked: web/src/services/adminApi.js AdminShortlistItem typedef (line 33)
  found: `material_status: 'ready'|'draft'` and `decision: 'pending'|'approved'|'rejected'`
    are two SEPARATE, independent fields on the same DTO.
  implication: Two genuinely independent concepts coexist on one row by design; the UI
    conflates them visually because both are dropped into the same unlabelled badge row.

- timestamp: 2026-10-03T16:07:00Z
  checked: tests/admin.spec.js "Approve does not auto-ready draft (D-02)" (lines 341–348)
  found: Asserts, after approving a draft: `getByText("одобрен")` visible AND
    `getByText("draft", { exact: true })` visible AND the «Сделать ready» button visible —
    i.e. the test LOCKS the coexistence of `draft` + «одобрен» as intended behavior.
  implication: The contradiction is by design (D-02: approve ≠ ready). It is a UX/labeling
    bug, not a data/logic bug — no tooltip or copy explains that `draft` = publishing
    readiness while «одобрен» = shortlist triage decision.

## Resolution

<!-- OVERWRITE as understanding evolves -->

root_cause: "The shortlist row renders two independent status dimensions side by side with
  no disambiguation. In AdminDigestPage.jsx, one flex container (line 759) renders BOTH
  the raw material_status pill (`{item.material_status}` → `draft`, line 768) AND the
  decision caption (`decisionCaption(item.decision)` → «одобрен», line 781). Because
  `material_status` and `decision` are separate fields on AdminShortlistItem (adminApi.js
  line 33) and D-02 keeps them decoupled (approve ≠ ready), an approved draft
  (decision==='approved' && material_status==='draft') legitimately carries both states,
  so the row displays `draft` + «одобрен» together with no tooltip/legend clarifying that
  `draft` refers to publish-readiness while «одобрен» refers to the shortlist triage
  decision — which reads as a contradiction to the user (G-14-2a)."
fix: ""
verification: ""
files_changed: []
