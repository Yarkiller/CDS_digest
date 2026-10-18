---
phase: 13-admin-material-email-preview-honesty
reviewed: 2026-10-04T16:41:00Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - backend/src/backend/application/use_cases/email_render.py
  - backend/src/backend/application/use_cases/preview_digest_email.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/application/use_cases/get_admin_shortlist.py
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/domain/email_chrome.py
  - backend/src/backend/domain/shortlist.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/tests_support/in_memory.py
  - supabase-integration/src/supabase_integration/shortlist_repository.py
  - web/src/pages/AdminDigestPage.jsx
  - web/src/services/adminApi.js
  - web/src/utils/forbiddenChrome.js
  - tests/admin.spec.js
  - tests/unit/test_email_render.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_preview_digest.py
  - tests/unit/test_send_digest.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-10-04T16:41:00Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

This re-run reviews the source actually on disk (later phases 14/16 touched `AdminDigestPage.jsx`, `adminApi.js`, `admin.py`, `test_http_admin.py`). The Phase 13 contracts hold: backend owns email HTML via one `render_email_html` shared by preview (`preview_digest_email.py:191`) and send (`send_digest.py:171`); the parity proof `test_preview_email_html_matches_send_html` is present and green; the FE renders preview HTML only through `<iframe sandbox="" srcDoc={...}>` (`AdminDigestPage.jsx:870-875`) with no `dangerouslySetInnerHTML` anywhere in `web/`; the ban helper is assert-only (renderers never import `email_chrome`); and scratch migration `010_phase13_scrub_test_header.sql` exists. I ran the four backend unit suites: **76 passed**.

No BLOCKERs. The findings below are robustness/honesty gaps: a dead reader link when `slug` is empty (the mock hides it), a one-minute read invented when `reading_minutes` is missing, a send-unlock path that never shows the preview, and an over-narrow catch that can turn a published digest into a 5xx.

## Warnings

### WR-01: Empty slug produces a dead `/materials/` link in mail — and the mock hides it

**File:** `backend/src/backend/application/use_cases/email_render.py:39-43` (and `preview_digest_email.py:73-74`)
**Issue:** Both the HTML renderer and the plain-body segment interpolate `slug` directly and always emit a link. With `slug is None`/empty, the recipient gets `href="{site}/materials/"`, which is a 404 link. Verified directly:

```
render_material_email_block(title='T', dek=None, slug='', site_url='https://x.test')
# => '<h2>T</h2><p><a href="https://x.test/materials/">Читать →</a></p>'
```

`materials.slug` is `not null unique` in `001_initial_schema.sql:91`, so live risk is low — but the domain type (`ShortlistItem.slug: str | None`) and `_item_from_row` (`shortlist_repository.py:67`) explicitly permit `None`, and `render_email_html` accepts `slug: str = ""`. The FE mock instead falls back to `item.slug || String(item.material_id)` (`adminApi.js:492`), so the Playwright "iframe shows Читать → link" assertion can never observe the broken-URL shape the live renderer can produce.

**Fix:** Make the renderer omit the anchor (or use an absolute-by-id fallback) when `slug` is blank, and mirror the same rule in the mock so tests exercise the live behavior:

```python
parts = [f"<h2>{html.escape(title, quote=True)}</h2>"]
if dek and dek.strip():
    parts.append(f"<p>{html.escape(dek.strip(), quote=True)}</p>")
if slug.strip():
    href = html.escape(f"{base}/materials/{slug}", quote=True)
    parts.append(f'<p><a href="{href}">Читать →</a></p>')
```

### WR-02: Material preview invents «~1 мин» when `reading_minutes` is missing

**File:** `web/src/pages/AdminDigestPage.jsx:947`
**Issue:** `Number.isFinite(item.reading_minutes) ? item.reading_minutes : 1` renders «~1 мин» whenever the shortlist omits `reading_minutes` / sends `null`, while the adjacent counts fall back to `0`. For a non-empty body with no duration, the row reads e.g. «~8500 символов · 1200 слов · ~1 мин» — an understated, invented read time. D-06 explicitly permits `~1 мин` only for the *empty* body case; the live-DTO path does not guarantee `reading_minutes`.

**Fix:** Fall back to `0` (honest unknown), consistent with `charCount`/`wordCount`:

```javascript
const readingMinutes = Number.isFinite(item.reading_minutes) ? item.reading_minutes : 0
```

### WR-03: Send unlocks even if the preview was closed before it rendered

**File:** `web/src/pages/AdminDigestPage.jsx:409-415`
**Issue:** `openEmailPreview()` sets `emailPreviewed(true)` and the fingerprint unconditionally once the request resolves, even when the user closed the modal while it was loading: `setEmailModal((current) => (current === null ? null : { preview }))` keeps the modal shut, but `previewOk` (line 242) then becomes true and `sendUnlocked` (line 244) turns the "Отправить дайджест →" button on. The user can therefore send without ever seeing the preview HTML or material body, which undercuts the Phase 13 goal ("Admin can inspect … before send") even though the inline comment cites the D-86 session flag. The comment suggests this is deliberate, so confirm with the product owner; if the intent is a *viewed* preview, only arm the flag when `{ preview }` is actually applied.

**Fix (if preview must be seen):** move the flag/fingerprint update into the reopen branch:

```javascript
setEmailModal((current) => {
  if (current === null) return null
  setEmailPreviewed(true)
  setPreviewFingerprint(fp)
  return { preview }
})
```

### WR-04: Post-publish mail/audit only tolerates `PersistenceError`

**File:** `backend/src/backend/application/use_cases/send_digest.py:176-208`
**Issue:** The docstring states "mail and audit are best-effort — failures are logged and must not convert an already-published digest into a failed send response" (CR-02), but both `try` blocks catch only `PersistenceError`. Any other exception raised by a mailer (e.g. `smtplib.SMTPException`, `NotImplementedError` from `SmtpMailer`, or an adapter bug) or by `pings.record` propagates *after* `claim_and_publish` has already published the issue and stamped `sent_at`, so the HTTP route returns 5xx for a digest that did ship. In practice adapters map boundary failures to `PersistenceError` and `SmtpMailer` cannot be wired (`resolve_mailer` fails fast), so impact today is low — but the code does not honor its own stated contract.

**Fix:** Widen the guard to `except Exception:` (log with `logger.exception`) for the mail and audit blocks, or document that adapters MUST only raise `PersistenceError`.

## Info

### IN-01: Mock email HTML re-implements the backend renderer (drift risk)

**File:** `web/src/services/adminApi.js:474-497`
**Issue:** `composeMockPreviewHtml` duplicates the backend template and hardcodes `http://127.0.0.1:5173/materials/...` instead of the settings-driven `site_url`. Playwright therefore asserts on mock-rendered HTML, not on backend output, so any divergence between the two renderers is invisible to the E2E suite — WR-01 is a concrete example. Consider sourcing the mock `html` from a shared fixture derived from the backend, or asserting the backend renderer directly in unit tests only and documenting the mock as a dev-only approximation.

### IN-02: Mock `escapeHtml` omits apostrophe escaping

**File:** `web/src/services/adminApi.js:444-450`
**Issue:** Escapes `&`, `<`, `>`, `"` only. Python `html.escape(..., quote=True)` also escapes `'` → `&#x27;`. Today's mock hrefs are double-quoted so nothing breaks, but text later placed in a single-quoted attribute would diverge from live mail.
**Fix:** Add `.replace(/'/g, '&#x27;')` to mirror CPython.

### IN-03: `render_interstitial_html` does not handle CRLF line endings

**File:** `backend/src/backend/application/use_cases/email_render.py:17-27`
**Issue:** Paragraphs are split on `"\n\n"` and single newlines become `<br>`. For CRLF input (`"a\r\n\r\nb"`) the split yields one paragraph with a literal `\r`, and `.replace("\n", "<br>")` leaves embedded `\r`. Browser textareas post `\n`, so this is latent, but the helper is the single whitespace source for both mail formats.
**Fix:** Normalize first: `trimmed = text.replace("\r\n", "\n").replace("\r", "\n").strip()`.

### IN-04: Numeric casts at the Supabase boundary can raise uncaught `ValueError`

**File:** `supabase-integration/src/supabase_integration/shortlist_repository.py:44-68`
**Issue:** `_item_from_row` does `int(row["material_id"])`, `int(row["rank"])`, `int(reading_raw)` with no `try/except`. A malformed DB value raises `ValueError`, which is not a `PersistenceError`, so the route returns 500 instead of the mapped 503 `shortlist_unavailable`. The `rank`/`material_id` columns are integers, but `reading_minutes` is read straight from the joined material row.
**Fix:** Wrap the per-row conversion and re-raise as `PersistenceError(f"shortlist item parse failed: {exc}")`, matching the rest of this adapter.

---

_Reviewed: 2026-10-04T16:41:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
