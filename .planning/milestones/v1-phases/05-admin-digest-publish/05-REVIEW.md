---
phase: 05-admin-digest-publish
reviewed: 2026-09-22T06:35:56Z
depth: standard
files_reviewed: 54
files_reviewed_list:
  - backend/src/backend/application/ports/digest_publisher.py
  - backend/src/backend/application/ports/issue_repository.py
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/application/ports/shortlist_repository.py
  - backend/src/backend/application/use_cases/get_admin_shortlist.py
  - backend/src/backend/application/use_cases/preview_digest_email.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/application/use_cases/set_shortlist_decision.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/domain/current_user.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/domain/shortlist.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/interface/http/app.py
  - backend/src/backend/interface/http/deps.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/interface/http/routes/me.py
  - backend/src/backend/tests_support/in_memory.py
  - docs/agents/local-platform-runbook.md
  - playwright.config.js
  - supabase-integration/migrations/005_phase5_admin_shortlist.sql
  - supabase-integration/src/supabase_integration/__init__.py
  - supabase-integration/src/supabase_integration/digest_publisher.py
  - supabase-integration/src/supabase_integration/issue_repository.py
  - supabase-integration/src/supabase_integration/shortlist_repository.py
  - tests/admin.spec.js
  - tests/auth.spec.js
  - tests/unit/test_admin_preview_composition.js
  - tests/unit/test_composition_container.py
  - tests/unit/test_get_admin_shortlist.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_http_knowledge_search.py
  - tests/unit/test_http_me.py
  - tests/unit/test_live_container_wiring.py
  - tests/unit/test_phase5_migration_005.py
  - tests/unit/test_preview_digest.py
  - tests/unit/test_score_factors.py
  - tests/unit/test_send_digest.py
  - tests/unit/test_set_shortlist_decision.py
  - tests/unit/test_stub_mailer.py
  - tests/unit/test_supabase_digest_publisher_contract.py
  - tests/unit/test_supabase_shortlist_repository_contract.py
  - tests/web-app.spec.js
  - web/src/App.jsx
  - web/src/components/AppShell.jsx
  - web/src/main.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/ForbiddenPage.jsx
  - web/src/pages/ProfilePage.jsx
  - web/src/services/adminApi.js
  - web/src/services/adminPreviewComposition.js
  - web/src/services/meApi.js
findings:
  critical: 2
  warning: 6
  info: 4
  total: 12
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-09-22T06:35:56Z
**Depth:** standard
**Files Reviewed:** 54
**Status:** issues_found

## Summary

Phase 05 admin digest publish has solid Ports & Adapters shape: `require_admin` gates on `profiles.role`, send goes through atomic `claim_and_publish_digest` on the happy path, and preview composition is covered in unit/Playwright tests. Live path still has two correctness holes — non-transactional rank rewrite before the RPC, and irreversible publish followed by a failing audit that surfaces as send failure — plus several SPA/API honesty gaps around the D-86 preview gate and response DTO fields.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Rank rewrite is outside the claim+publish transaction

**File:** `supabase-integration/src/supabase_integration/digest_publisher.py:56-93`
**Issue:** `_apply_publication_ranks` issues separate `UPDATE digest_shortlist_items` calls **before** `claim_and_publish_digest`. Those UPDATEs are not part of the RPC transaction. If the RPC then fails (`AlreadySentError`, `EmptySendPoolError`, `PersistenceError`), the unsent batch keeps mutated ranks (including possible mid-flight `temp_base + i` values if phase 2 fails). Concurrent admins / later default-rank sends can publish the wrong order. Schema has no `(batch_id, rank)` unique constraint, so collisions are silent.
**Fix:** Move ordering into the RPC (e.g. `p_material_ids bigint[]`) and assign `digest_issue_items.position` from that array inside the same PL/pgSQL transaction. Do not mutate shortlist ranks from the Python adapter, or wrap rewrite+RPC in a single DB transaction.

```sql
-- inside claim_and_publish_digest, after claim:
insert into public.digest_issue_items (issue_id, material_id, position)
select v_issue_id, mid, ord
from unnest(p_material_ids) with ordinality as t(mid, ord)
join public.digest_shortlist_items si
  on si.batch_id = p_batch_id and si.material_id = mid
join public.materials m on m.id = mid
where si.decision = 'approved' and m.status = 'ready';
```

### CR-02: Audit failure after successful publish returns send failure

**File:** `backend/src/backend/application/use_cases/send_digest.py:107-142`
**Issue:** `publisher.claim_and_publish` commits the issue + `sent_at` first. If `pings.record` (or a future non-stub mailer) then raises, `admin.post_shortlist_send` maps `PersistenceError` → 503 and the SPA shows «Рассылка не отправлена» (`AdminDigestPage.jsx` catch path) even though the digest is already published and the batch claimed. Retry correctly hits 409 «Уже отправлено», but the first response is a false failure and the CTA/issue link may never appear.
**Fix:** After a successful `claim_and_publish`, treat mail/audit as best-effort: catch and log audit failures, still return `SendDigestResult` success (optionally with an `audit_ok: false` field). Never convert post-publish infrastructure errors into a failed send response.

```python
publication = publisher.claim_and_publish(...)
mailer.send_digest(...)  # stub today
try:
    pings.record(...)
except PersistenceError:
    logger.exception("digest_send audit failed after publish batch_id=%s", publication.batch_id)
return SendDigestResult(...)  # always success after publish
```

## Warnings

### WR-01: D-86 preview gate ignores composition (order / intro / text)

**File:** `web/src/pages/AdminDigestPage.jsx:74-80,212-218`
**Issue:** `approvedFingerprint` is only the sorted approved∩ready material id set. After a successful preview, the admin can reorder issue blocks, edit intro, or change interstitial text without clearing `emailPreviewed`. Send still uses the *current* `issueBlocks` / `contextText` for `material_ids` (and preview showed a different body). D-86 text scopes to “approved set”, but G-05-1 composition honesty is broken end-to-end.
**Fix:** Fingerprint intro + ordered blocks (material ids + text contents), e.g. `JSON.stringify({ intro, blocks })`, and reset `emailPreviewed` when that fingerprint drifts.

### WR-02: Stub/live send body ignores previewed intro and text blocks

**File:** `backend/src/backend/application/use_cases/send_digest.py:116-122`
**Issue:** Preview builds body from `intro` + ordered material/text blocks (`preview_digest_email.py`). `send_digest` always builds a fixed template of titles only — no intro, no interstitial text. What the admin confirms in «Превью письма» is not what StubMailer logs / what a future SMTP path would send.
**Fix:** Accept the same composition on send (or reuse last preview payload server-side for the session), and build `body_text` with the same `_compose_body` rules as preview (plus issue URL header as needed).

### WR-03: Admin role probe maps any `/me` failure to Forbidden

**File:** `web/src/pages/AdminDigestPage.jsx:127-138`
**Issue:** `fetchMe` network/5xx errors set `roleState = 'forbidden'`, rendering `ForbiddenPage` instead of `ServiceUnavailable` + retry. Operators and admins with transient API outages look unauthorized.
**Fix:** Distinguish `MeApiError` codes: `UNAUTHORIZED`/`FORBIDDEN` → forbidden; `NETWORK`/5xx → error + retry; only `role !== 'admin'` → ForbiddenPage.

### WR-04: Live shortlist DTO omits fields the SPA already consumes

**File:** `backend/src/backend/interface/http/routes/admin.py:45-51` (vs `web/src/pages/AdminDigestPage.jsx:82-93,618-731`)
**Issue:** `AdminShortlistResponse` has no `week_label`, `sent_at`, or per-item `dek`. Live `mapShortlistBody` therefore always leaves `weekDek` null and material preview always shows «Краткое описание недоступно.» Mocks populate these fields, so mock Playwright ≠ live admin UX.
**Fix:** Extend the response DTO (and `get_admin_shortlist` / repository mapping) with `week_label` (from `week_start`), `sent_at` when relevant, and `dek` from materials.

### WR-05: Display truncate (≤5) vs send pool (full batch) mismatch

**File:** `backend/src/backend/application/use_cases/get_admin_shortlist.py:34` vs `send_digest.py:100-105`
**Issue:** Admin GET returns `sorted(...)[:5]` while send validates against the full approved∩ready set. If a batch ever has >5 items with more than five approved∩ready, the SPA’s `material_ids` will fail `InvalidSendOrderError` (400) with no UI path to include the hidden rows. Product says ≤5, but the API does not enforce that invariant on write.
**Fix:** Enforce ≤5 in repository/seed/pipeline **or** apply the same top-5 filter consistently in preview/send **or** return all items and paginate in UI.

### WR-06: Partial batch decision apply leaves silent half-state

**File:** `web/src/pages/AdminDigestPage.jsx:262-279`
**Issue:** `applyDecision` awaits `setDecision` in a loop. If decision 2 of N fails, earlier rows are already persisted; UI toasts «Не сохранено» and may refresh from the last successful DTO only when `latest` is set — checkbox selection is cleared, making the partial apply easy to miss.
**Fix:** Prefer a bulk decision endpoint, or on failure reload shortlist from GET and toast which ids failed; do not clear selection until all succeed.

## Info

### IN-01: Stale adapter docstring — `release_claim` no longer called by send

**File:** `supabase-integration/src/supabase_integration/shortlist_repository.py:179-185`
**Issue:** Comment still says «Called by send_digest when IssueRepository.publish fails». Live send uses `DigestPublisher` RPC; compensation is in-RPC rollback / in-memory publisher only.
**Fix:** Update the docstring to reflect DigestPublisher / in-memory compensation only.

### IN-02: `claim_sent` / `release_claim` remain on the live shortlist port but unused by send

**File:** `backend/src/backend/application/ports/shortlist_repository.py:32-43`
**Issue:** Dead surface for the production send path (still used by `InMemoryDigestPublisher`). Increases port noise.
**Fix:** Narrow the live adapter docs or split a test-only claim helper if RPC remains the sole live write path.

### IN-03: Profile page stub ignores `PATCH /me` / `updateDisplayName`

**File:** `web/src/pages/ProfilePage.jsx:1-20`
**Issue:** Backend `me.patch_me` and `meApi.updateDisplayName` exist; Profile UI is a stub with no editor. Harmless for phase 05 scope; identity rename only works at registration / future UI.
**Fix:** Track as follow-up or wire a minimal display-name form when profile phase starts.

### IN-04: Migration header still describes split claim-then-publish

**File:** `supabase-integration/migrations/005_phase5_admin_shortlist.sql:4-5`
**Issue:** Comment says live Python path is «atomic UPDATE … then IssueRepository.publish»; composition now wires `SupabaseDigestPublisher` + RPC.
**Fix:** Update the header comment to match the RPC-only live path.

---

_Reviewed: 2026-09-22T06:35:56Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
