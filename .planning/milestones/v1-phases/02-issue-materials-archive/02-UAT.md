---
status: complete
phase: 02-issue-materials-archive
source:
  - 02-VERIFICATION.md
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
  - 02-05-SUMMARY.md
  - 02-06-SUMMARY.md
started: 2026-09-20T11:30:00Z
updated: 2026-09-20T15:14:00Z
---

## Current Test

[testing complete]

## Tests

### 1. UI-SPEC visual backstops (held-out)
expected: At 320 / 390 / 1280 — no broken overflow on IssueTOC/archive/material/callout/hero/nav; Russian plurals OK; usable hit targets; nav clear of wordmark
result: pass
notes: User confirmed no overflow; mid-UAT fixed welcome toast (once, fixed overlay fade) + shell profile stub link

### 2. Live FE↔BE smoke (VITE_USE_MOCKS=false)
expected: Authenticated `/` shows issue №14 typography hero + TOC; `/materials/rag-systems` shows Статья + prose + TOC; `/archive` lists №13 linking to `/issues/13` without voting callout
result: pass

### 3. Advisory — live tags + open-cycle clock (02-REVIEW WR-01, WR-03)
expected: Material tag chips show display labels (not raw slugs); voting callout open/closed matches editorial intent around closes_at
result: pass

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

## Deferred Follow-Ups
- test: 1
  idea: "Registration roles (Data Scientist, Data Analytics, Product Owner, Chief DS) — see .scratch/future-registration-roles.md"
  deferred_at: 2026-09-20
