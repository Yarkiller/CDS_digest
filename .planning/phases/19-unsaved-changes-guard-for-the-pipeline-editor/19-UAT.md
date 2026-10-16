---
status: testing
phase: 19-unsaved-changes-guard-for-the-pipeline-editor
source: [19-VERIFICATION.md]
started: 2026-10-16T07:25:00Z
updated: 2026-10-16T07:25:00Z
---

## Current Test

number: 1
name: Flagged edge — idempotency + no double-prompt
expected: |
  SPA path shows only the in-app modal (never a native dialog for that leave); reload/close shows exactly one browser beforeunload prompt; after successful save neither path prompts
awaiting: user response

## Tests

### 1. Flagged edge: idempotency + no double-prompt (plan 19-02)
expected: On /admin/pipeline, edit YAML → shell «Архив» → «Остаться» → edit again → «Уйти без сохранения»; then dirty again and reload/close the tab. SPA shows only the in-app modal; reload/close shows exactly one beforeunload; after successful save neither path prompts. Listeners do not accumulate across dirty↔clean cycles.
result: [pending]

### 2. Judgment prohibitions
expected: Git history shows 19-01 (6240fe9) before 19-02 guard commits; unload handler source has no confirm/alert; Cancel/Escape keep the draft — no silent discard, no confirm-in-unload, migration and guard never combined in one plan.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
