---
status: complete
phase: 03-voting-cycle
source: [03-VERIFICATION.md]
started: 2026-09-20T17:05:00Z
updated: 2026-09-20T18:46:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Live FE↔BE ballot smoke
expected: Authenticated /voting loads seeded topics with audit deks; confirm stores one vote; A→B updates status; closed reject shows «Цикл голосования закрыт»
result: pass

### 2. UI-SPEC visual backstops
expected: Leader strip, topic rows, and status reflow at 320/390/1280 without clipping or false empty/closed flash
result: pass

### 3. Reconfirm live DDL trigger on shared VM
expected: pg_trigger lists votes_enforce_open_and_topic; closed-cycle write rejected at DB as well as app layer
result: pass
notes: |
  pg_trigger: votes_enforce_open_and_topic present;
  Direct SQL INSERT with closed cycle → ERROR 23514 «votes: cycle 1 is not open»;
  Function enforce_votes_open_cycle_and_topic confirmed in CONTEXT (line 7 at RAISE);
  Cycle restored: id=1, status=open, closes_at=2026-09-27

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
