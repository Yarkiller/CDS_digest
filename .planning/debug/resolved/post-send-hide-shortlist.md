---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Post-send triage rows/checkboxes hide behind the digest-released copy plus 7-day countdown; G-05-2 closed"
trigger: "G-05-2: After digest send recorded, material-selection list stays visible with inactive checkboxes; should hide until new materials, show success + countdown"
created: 2026-09-21T17:48:00Z
updated: 2026-09-21T17:55:00Z
symptoms_prefilled: true
goal: find_root_cause_only
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: diagnosed
---

## Current Focus

hypothesis: CONFIRMED — Phase 5 never specified post-send hide + «дайджест успешно выпущен» + countdown; AdminDigestPage keeps items after send and only locks send (D-87/D-89)
test: Spec vs confirmSend vs empty-state vs cycle-length sources
expecting: Spec match for leftover list; no countdown field anywhere
next_action: return ROOT CAUSE FOUND (diagnose-only)
bug_class: Bohrbug
known_pattern_candidate: none (no knowledge-base.md)

reasoning_checkpoint:
  hypothesis: "Leftover shortlist after stub send is not a phase-5 regression; it is absent post-send rest-state UX. confirmSend sets batchSent + «Отправка записана» but never clears items / never swaps to a success panel; UI-SPEC/CONTEXT only require that banner + «Уже отправлено» lock."
  confirming_evidence:

    - "05-UI-SPEC Send→success: banner «Отправка записана» + issue CTA; already-sent «Уже отправлено»; empty only D-80 «Кандидатов пока нет» — no hide-on-send, no «дайджест успешно выпущен», no countdown copy"
    - "AdminDigestPage confirmSend (L239–262) sets banner/batchSent/issueUrl but leaves items[] and the shortlist/toolbar/footer branch (!isEmpty) mounted"
    - "Playwright admin.spec.js asserts post-send «Отправка записана» + disabled send + «Уже отправлено» without expecting list hide"
    - "Grep: «успешно выпущен» / «подготовлены через» absent from phase-05 specs, design-frontend, SPA"
  falsification_test: "A locked Phase-5 decision or UI-SPEC row requiring hide-after-send or countdown copy would refute 'never implemented'"
  fix_rationale: "N/A diagnose-only — plan-phase must add rest-state contract + SPA branch; countdown needs a product source for X"
  blind_spots: "Did not re-run live UAT browser; inferred live leftover list from SPA state retention (confirmSend no refetch). Live GET after send returns empty via get_current_batch sent_at IS NULL — reload would show D-80 empty, still wrong copy."
  candidate_causes:

    - "code: confirmSend does not clear items or switch UI mode after success"
    - "config/spec: Phase 5 CONTEXT/UI-SPEC never defined post-send hide or countdown (product gap)"
  and_gate: "yes — leftover list is both (1) SPA not clearing after send AND (2) no specified rest-state; even a refetch to empty would still miss the user's success/countdown copy"

## Symptoms

expected: |
  After «Отправка записана», materials already used for the sent digest are hidden until new materials appear.
  Inactive checkboxes are not shown.
  The page shows «дайджест успешно выпущен» and «Следующие материалы будут подготовлены через X дней».
actual: |
  User reported (verbatim): "pass. Замечание - материалы для выбора после того как отправка записана необходимо скрывать до появления новыйх материалов. Материалы из которых уже были отобраны годные больше не нужно демонстрировать - непонтно зачем, чекбоксы неактивны, их нужно элегантно скрыть, оставив надипись - дайджест успешно выпущен. Следующие материалы будут подготовлены через X дней ."
  The send checkpoint itself passed: success copy «Отправка записана», archive issue appears, send locks as already-sent, approved draft blocks send. This gap is the leftover selection UI after that success.
errors: None reported
reproduction: Test 2 in UAT (.planning/phases/05-admin-digest-publish/05-UAT.md). Live admin sends the digest stub, then looks at the selection list.
started: Discovered during UAT of phase 05-admin-digest-publish

## Eliminated

- hypothesis: Regression against an already-specified Phase-5 post-send hide / countdown contract
  evidence: 05-UI-SPEC Copywriting + Send→success + state machine only lock send and show «Отправка записана»; D-80 empty is «Кандидатов пока нет»; no countdown strings in phase docs or SPA
  timestamp: 2026-09-21T17:52:00Z

- hypothesis: Backend keeps returning sent-batch items so SPA must show them
  evidence: Port/live get_current_batch filters sent_at IS NULL (WR-03); after claim, GET is empty. Leftover UI is client state after confirmSend, not live GET of used materials
  timestamp: 2026-09-21T17:53:00Z

## Evidence

- timestamp: 2026-09-21T17:49:00Z
  checked: 05-UAT.md G-05-2 + Test 2
  found: Send happy-path passed; gap is remark to hide selection UI after send and show new success/countdown copy
  implication: Symptom is post-success UX, not failed send

- timestamp: 2026-09-21T17:50:00Z
  checked: 05-UI-SPEC.md Send→success, Copywriting, Interaction State Machine; 05-CONTEXT D-80/D-87/D-89
  found: Success = «Отправка записана» + issue link; already-sent = «Уже отправлено»; empty = «Кандидатов пока нет». No hide-after-send. No «дайджест успешно выпущен». No «через X дней»
  implication: Requested UX was never a Phase-5 must-have — gap = missing feature / UAT-driven requirement

- timestamp: 2026-09-21T17:51:00Z
  checked: web/src/pages/AdminDigestPage.jsx confirmSend + render branches
  found: On success sets banner/message, issueUrl, batchSent=true; items unchanged; isEmpty=false keeps toolbar, digest editors, checkbox rows, sticky footer. Checkboxes have no disabled={batchSent}; send locks via !sendUnlocked
  implication: Mechanism of leftover list is intentional omission of post-send UI swap, not a failed hide flag

- timestamp: 2026-09-21T17:52:00Z
  checked: tests/admin.spec.js post-send assertions; adminApi mock sendDigest
  found: Spec expects list still present (send hint/disabled button); mock keeps items and only stamps sent_at
  implication: Automated tests encode keep-list-after-send as correct Phase-5 behavior

- timestamp: 2026-09-21T17:53:00Z
  checked: AdminShortlistResponse (admin.py); week_start / voting_cycles schema
  found: HTTP shortlist DTO has batch_id+items only (no sent_at/week_label on live — IN-02). No shortlist prep cadence field. voting_cycles opens_at/closes_at are voting windows, not material-prep ETA. week_start is batch label. PIPE-01 deferred
  implication: «X дней» has no existing API source; plan must choose product rule (e.g. fixed 7-day weekly cadence, next week_start−today, or new field)

- timestamp: 2026-09-21T17:54:00Z
  checked: knowledge-base.md
  found: file absent
  implication: no prior KB match

## Resolution

root_cause: |
  (b) Behavior Phase 5 never implemented — not a bug against the locked Phase-5 contract.
  Phase 5 success UX is only «Отправка записана» + send lock «Уже отправлено» + issue CTA (D-87/D-89 / 05-UI-SPEC).
  AdminDigestPage.confirmSend leaves items[] mounted, so the triage shortlist (checkboxes/toolbar) stays visible after a successful stub send.
  Desired copy «дайджест успешно выпущен» / «Следующие материалы будут подготовлены через X дней» and hide-until-new-batch were never specified; «X» has no shortlist cadence field (voting_cycles dates ≠ prep ETA; week_start is label only).
fix: 
verification: 
files_changed: []
oracle_type: derived
