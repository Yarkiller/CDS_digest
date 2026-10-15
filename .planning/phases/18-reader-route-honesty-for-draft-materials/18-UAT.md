---
status: testing
phase: 18-reader-route-honesty-for-draft-materials
source: [18-VERIFICATION.md]
started: 2026-10-15T12:58:00Z
updated: 2026-10-15T12:58:00Z
---

## Current Test

number: 1
name: Sign off prohibition 1 — no unpublished material presented as published
expected: |
  A draft is reachable only behind `require_admin`, is 404 on `/materials/{slug}` for every token,
  never enters the email/send pool, and the preview carries the
  «Черновик — предпросмотр, не опубликовано» marker.
awaiting: user response

## Tests

### 1. Sign off prohibition 1 — no unpublished material presented as published
expected: A draft is reachable only behind `require_admin`, is 404 on `/materials/{slug}` for every token, never enters the email/send pool, and the preview carries the «Черновик — предпросмотр, не опубликовано» marker.
result: [pending]

### 2. Sign off prohibition 2 — no unpublished `related`/`tags` exposure
expected: The preview payload's `tags`/`related` are empty by design, and no other draft-facing surface projects unpublished taxonomy/neighbours.
result: [pending]

### 3. Sign off prohibition 3 — the preview surface is not a second copy of the reader contract
expected: `MaterialReaderResponse` has no `status`/`preview` field; `get_material_for_reader` is unchanged; 'draft ≡ missing' on the reader route remains the contract.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
