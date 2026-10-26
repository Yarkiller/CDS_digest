---
status: complete
phase: 05-admin-digest-publish
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-05-SUMMARY.md, 05-06-SUMMARY.md, 05-07-SUMMARY.md, 05-08-SUMMARY.md, 05-09-SUMMARY.md]
started: 2026-09-21T19:28:42.510Z
updated: 2026-09-22T02:24:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: pass

### 2. Long titles and factor strings wrap
expected: Long titles/factor strings wrap without horizontal scroll; 44px targets usable. Rationale: Layout/backstop visual — deferred to SPA plan 05-04 / Playwright 05-06.
result: pass

### 3. Schema and demo seed applied on the shared VM
expected: Blocking schema/seed applied on shared VM before live-dependent verification. Rationale: Shared VM DDL/seed apply cannot be proven offline; operator resume signal required.
result: pass

### 4. Admin JWT + profiles.role=admin GET /admin/shortlist returns ≤5 ranked items with draft/ready, score, and factor_labels or honesty empty
expected: Admin JWT + profiles.role=admin GET /admin/shortlist returns ≤5 ranked items with draft/ready, score, and factor_labels or honesty empty
result: pass
source: automated
coverage_id: 05-01-D1

### 5. Non-admin authenticated caller gets HTTP 403 on GET /admin/shortlist — never empty shortlist JSON
expected: Non-admin authenticated caller gets HTTP 403 on GET /admin/shortlist — never empty shortlist JSON
result: pass
source: automated
coverage_id: 05-01-D2

### 6. ADMIN-05 score_factors honesty — ≥2 readable labels returned; 0 or 1 → empty factor_labels
expected: ADMIN-05 score_factors honesty — ≥2 readable labels returned; 0 or 1 → empty factor_labels
result: pass
source: automated
coverage_id: 05-01-D3

### 7. GET /me.role is app_role employee by default; seeded admin returns admin (D-76)
expected: GET /me.role is app_role employee by default; seeded admin returns admin (D-76)
result: pass
source: automated
coverage_id: 05-01-D4

### 8. Empty current batch returns 200 with items=[] for «Кандидатов пока нет»
expected: Empty current batch returns 200 with items=[] for «Кандидатов пока нет»
result: pass
source: automated
coverage_id: 05-01-D5

### 9. Approve persists shortlist_decision=approved and is visible on subsequent GET
expected: Approve persists shortlist_decision=approved and is visible on subsequent GET
result: pass
source: automated
coverage_id: 05-02-D1

### 10. Reject persists shortlist_decision=rejected and is reflected on subsequent GET
expected: Reject persists shortlist_decision=rejected and is reflected on subsequent GET
result: pass
source: automated
coverage_id: 05-02-D2

### 11. Every shortlist item exposes material_status draft|ready on GET and decision response
expected: Every shortlist item exposes material_status draft|ready on GET and decision response
result: pass
source: automated
coverage_id: 05-02-D3

### 12. Approve is allowed on draft materials (send-pool draft block is 05-03)
expected: Approve is allowed on draft materials (send-pool draft block is 05-03)
result: pass
source: automated
coverage_id: 05-02-D4

### 13. Non-admin cannot POST decision — HTTP 403
expected: Non-admin cannot POST decision — HTTP 403
result: pass
source: automated
coverage_id: 05-02-D5

### 14. Invalid decision → 400; unknown material → 404; PersistenceError → 503
expected: Invalid decision → 400; unknown material → 404; PersistenceError → 503
result: pass
source: automated
coverage_id: 05-02-D6

### 15. Email preview DTO lists exactly approved∩ready materials; empty pool errors; never sets sent_at
expected: Email preview DTO lists exactly approved∩ready materials; empty pool errors; never sets sent_at
result: pass
source: automated
coverage_id: 05-03-D1

### 16. StubMailer returns delivery_status=stubbed and recipient_count=0; SMTP fail-fast
expected: StubMailer returns delivery_status=stubbed and recipient_count=0; SMTP fail-fast
result: pass
source: automated
coverage_id: 05-03-D2

### 17. Successful send publishes one issue, claims sent_at, stubs mail with /issues/{n}, audits digest_send
expected: Successful send publishes one issue, claims sent_at, stubs mail with /issues/{n}, audits digest_send
result: pass
source: automated
coverage_id: 05-03-D3

### 18. Approved draft in pool blocks send with DraftInSendPoolError → HTTP 400
expected: Approved draft in pool blocks send with DraftInSendPoolError → HTTP 400
result: pass
source: automated
coverage_id: 05-03-D4

### 19. Repeat send → AlreadySentError / HTTP 409; no second issue or stub send
expected: Repeat send → AlreadySentError / HTTP 409; no second issue or stub send
result: pass
source: automated
coverage_id: 05-03-D5

### 20. Stub email body contains /issues/{number} for ADMIN-08 returnUrl after login
expected: Stub email body contains /issues/{number} for ADMIN-08 returnUrl after login
result: pass
source: automated
coverage_id: 05-03-D6

### 21. Non-admin cannot preview or send — HTTP 403
expected: Non-admin cannot preview or send — HTTP 403
result: pass
source: automated
coverage_id: 05-03-D7

### 22. Employee never sees Админ nav; admin NavLink → /admin/digest
expected: Employee never sees Админ nav; admin NavLink → /admin/digest
result: pass
source: automated
coverage_id: 05-04-D1

### 23. Non-admin deep-link renders ForbiddenPage «Недостаточно прав» + «На выпуск»
expected: Non-admin deep-link renders ForbiddenPage «Недостаточно прав» + «На выпуск»
result: pass
source: automated
coverage_id: 05-04-D2

### 24. Populated shortlist ≤5 rows with badges, factors honesty, empty D-80 copy, Approve caption
expected: Populated shortlist ≤5 rows with badges, factors honesty, empty D-80 copy, Approve caption
result: pass
source: automated
coverage_id: 05-04-D3

### 25. Select-all / top-3 checkbox ops; preview unlocks send; success and already-sent copy
expected: Select-all / top-3 checkbox ops; preview unlocks send; success and already-sent copy
result: pass
source: automated
coverage_id: 05-04-D4

### 26. Migration 005 adds delivery columns + idempotent demo batch ≤5 items with score_factors honesty
expected: Migration 005 adds delivery columns + idempotent demo batch ≤5 items with score_factors honesty
result: pass
source: automated
coverage_id: 05-05-D1

### 27. SupabaseShortlistRepository + issue publish wired in live container with StubMailer
expected: SupabaseShortlistRepository + issue publish wired in live container with StubMailer
result: pass
source: automated
coverage_id: 05-05-D2

### 28. Atomic claim path (RPC and/or sent_at IS NULL) for ADMIN-07 concurrency
expected: Atomic claim path (RPC and/or sent_at IS NULL) for ADMIN-07 concurrency
result: pass
source: automated
coverage_id: 05-05-D3

### 29. Employee deep-link /admin/digest shows 403 Недостаточно прав + На выпуск (D-77)
expected: Employee deep-link /admin/digest shows 403 Недостаточно прав + На выпуск (D-77)
result: pass
source: automated
coverage_id: 05-06-D1

### 30. Empty shortlist honesty + no пайплайн; loading never flashes empty success
expected: Empty shortlist honesty + no пайплайн; loading never flashes empty success
result: pass
source: automated
coverage_id: 05-06-D2

### 31. Select-all / top-3 checkbox ops (ADMIN-06)
expected: Select-all / top-3 checkbox ops (ADMIN-06)
result: pass
source: automated
coverage_id: 05-06-D3

### 32. Preview fail keeps send locked; success unlocks; draft blocks; send success + already-sent
expected: Preview fail keeps send locked; success unlocks; draft blocks; send success + already-sent
result: pass
source: automated
coverage_id: 05-06-D4

### 33. ADMIN-08 returnUrl /issues/{n} after login; sanitize rejects // open redirects (D-90, T-05-20)
expected: ADMIN-08 returnUrl /issues/{n} after login; sanitize rejects // open redirects (D-90, T-05-20)
result: pass
source: automated
coverage_id: 05-06-D5

### 34. 05-VALIDATION.md Wave 0 complete; File Exists ✅ for phase test map
expected: 05-VALIDATION.md Wave 0 complete; File Exists ✅ for phase test map
result: pass
source: automated
coverage_id: 05-06-D6

### 35. preview_digest_email composes intro + ordered blocks into body; invalid material → 400
expected: preview_digest_email composes intro + ordered blocks into body; invalid material → 400
result: pass
source: automated
coverage_id: 05-07-D1

### 36. SPA posts intro/blocks and renders composed preview.body in «Превью письма»
expected: SPA posts intro/blocks and renders composed preview.body in «Превью письма»
result: pass
source: automated
coverage_id: 05-07-D2

### 37. Existing preview unlock / send / already-sent admin contracts remain green
expected: Existing preview unlock / send / already-sent admin contracts remain green
result: pass
source: automated
coverage_id: 05-07-D3

### 38. Reorderable issue blocks + optional interstitial drive preview order
expected: Reorderable issue blocks + optional interstitial drive preview order
result: pass
source: automated
coverage_id: 05-08-D1

### 39. send_digest material_ids permutation is publication/mail order; mismatch → 400
expected: send_digest material_ids permutation is publication/mail order; mismatch → 400
result: pass
source: automated
coverage_id: 05-08-D2

### 40. Intro + interstitial appear in «Превью письма»; send still «Отправка записана» + «К выпуску»
expected: Intro + interstitial appear in «Превью письма»; send still «Отправка записана» + «К выпуску»
result: pass
source: automated
coverage_id: 05-08-D3

### 41. Shortlist API returns digest_rest + days_until_next_batch=7 after send; genuine empty stays D-80-shaped
expected: Shortlist API returns digest_rest + days_until_next_batch=7 after send; genuine empty stays D-80-shaped
result: pass
source: automated
coverage_id: 05-09-D1

### 42. Post-send and ALREADY_SENT hide shortlist/checkboxes; show rest copy; keep Отправка записана / Уже отправлено
expected: Post-send and ALREADY_SENT hide shortlist/checkboxes; show rest copy; keep Отправка записана / Уже отправлено
result: pass
source: automated
coverage_id: 05-09-D2

### 43. Cold digest_rest load shows rest panel; D-80 empty does not
expected: Cold digest_rest load shows rest panel; D-80 empty does not
result: pass
source: automated
coverage_id: 05-09-D3

## Summary

total: 43
passed: 43
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
