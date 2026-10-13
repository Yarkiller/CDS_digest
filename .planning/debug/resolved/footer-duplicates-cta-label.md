---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Sticky footer drops the duplicate title list for a count-only hint; batch CTA removed (v1.2 Phase 14)"
trigger: "UX: sticky send footer duplicates approved-draft titles already visible in the shortlist; batch CTA label «одобренные черновики» confusing. (Phase 14 UAT gap G-14-2b)"
created: 2026-10-03T16:08:00Z
updated: 2026-10-03T16:08:00Z
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: investigating
---

## Current Focus

hypothesis: The sticky send footer (`admin-send-footer`) re-renders the `approvedDrafts` subset as a title list, duplicating rows already rendered in `admin-shortlist`; the batch CTA label string «Сделать ready одобренные черновики» is a bare noun phrase without a count, making the action ambiguous.
test: Read AdminDigestPage.jsx completely; grep for label/approvedDrafts usage.
expecting: Footer `<ul>` maps `approvedDrafts.map(d => d.title)` (same items rendered in shortlist); CTA text is exactly «Сделать ready одобренные черновики».
next_action: Write root cause to Resolution and return ROOT CAUSE FOUND (diagnose-only mode).

## Symptoms

expected: The sticky send footer (when approved drafts exist) should NOT duplicate the approved-draft titles already visible in the shortlist, and the batch CTA label should be unambiguous about what it does.
actual: (1) the footer duplicates the approved-draft titles (repeating titles already shown in the list); (2) the batch CTA label «одобренные черновики» is confusing.
errors: None.
reproduction: Approve several drafts (N≥2) so the sticky send footer appears, then inspect it.
started: Discovered during UAT verification of Phase 14.

## Eliminated

<!-- none yet -->

## Evidence

- timestamp: 2026-10-03T16:08:00Z
  checked: web/src/pages/AdminDigestPage.jsx (read fully)
  found: `approvedDrafts = items.filter(item => item.decision === 'approved' && item.material_status === 'draft')` (lines 220–223). `items` is the full shortlist, all rendered as `<li data-testid="admin-shortlist-row">` with `{item.title}` at line 758.
  implication: Every approved draft is already displayed (with its title) in the shortlist list; `approvedDrafts` is a strict subset of rendered rows.

- timestamp: 2026-10-03T16:08:00Z
  checked: AdminDigestPage.jsx footer block (lines 806–834)
  found: When `!restMode && approvedDrafts.length > 0`, the footer renders `<ul>{approvedDrafts.map((d) => <li>{d.title} · draft</li>)}</ul>` (lines 818–823), re-listing each title.
  implication: The same titles appear twice on screen: once in `admin-shortlist` and again in the footer `<ul>`. This is the duplication reported.

- timestamp: 2026-10-03T16:08:00Z
  checked: AdminDigestPage.jsx line 832
  found: Batch CTA label literal is `Сделать ready одобренные черновики`.
  implication: The phrase «одобренные черновики» is a bare noun fragment; without a count or an explicit "all" it reads ambiguously (does it act on all drafts? which ones?). Contrast: the confirm dialog uses `Сделать ready ${n} одобренных черновиков?` (line 365) which includes a count and is clearer.

- timestamp: 2026-10-03T16:08:00Z
  checked: grep for `одобренные черновики|admin-mark-ready-batch|approvedDrafts` across web/
  found: Only occurrences are in AdminDigestPage.jsx (lines 220, 241, 248, 256, 363–367, 816–832). No other component renders this list or label.
  implication: Root cause is fully localized to the footer JSX in AdminDigestPage.jsx; no shared component or service is involved.

## Resolution

root_cause: "(a) Duplication — the sticky footer (`admin-send-footer`) renders an extra `<ul>` mapping `approvedDrafts` (`{d.title} · draft`, lines 818–823), but `approvedDrafts` is a subset of `items` that the shortlist `<ul>` (line 758) already renders with its titles; therefore approved-draft titles are shown twice. (b) Confusing CTA — the batch button's label string is the bare noun phrase «Сделать ready одобренные черновики» (line 832), which lacks a count/all-quantifier and reads ambiguously versus the confirm dialog's `Сделать ready ${n} одобренных черновиков?` (line 365)."
fix: "(Not applied — diagnose-only.) (a) Collapse the footer title list to a count-only summary (e.g. `Одобренных черновиков: {approvedDrafts.length}`) or remove the `<ul>` entirely, leaving only the hint + CTA. (b) Rename the CTA to an unambiguous action with a count, e.g. `Сделать ready все одобренные черновики ({approvedDrafts.length})`."
verification: "Code inspection confirmed exact strings and render paths; grep shows no other render site. (No runtime verification performed in diagnose-only mode.)"
files_changed: []
