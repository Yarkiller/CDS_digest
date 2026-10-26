# FIX-01 Lock — Admin shortlist empty-batch HTTP contract

**Phase:** 12-admin-shortlist-empty-batch-contract  
**Artifact:** `12-FIX-01-LOCK.md` (D-10)  
**Requirement:** FIX-01  
**Authority:** Downstream planners/executors/verifiers MUST read this before changing `GET /admin/shortlist` empty paths, HTTP units, FE mocks, or Playwright empty coverage.

**Proven by (12-01 / D-05):**
- `test_admin_shortlist_no_batches_returns_null_batch_id`
- `test_admin_shortlist_empty_unsent_batch_returns_batch_id`

**Full-item enrichment (Phase 13 / ADUX-01 / D-03):**
- `test_admin_shortlist_returns_full_items` — non-empty items carry additive material preview fields (required-key asserts; no full-body equality).

---

## Shape 1 — No batches (D-04 #1)

When `get_current_batch()` returns no current unsent batch (repository has no open batch):

| Field | Value | Notes |
|-------|-------|-------|
| `batch_id` | `null` | Distinguishes from empty-unsent |
| `items` | `[]` | Never schema/validation 500 |
| `week_label` | `null` | No batch → no week |
| `sent_at` | `null` | Not a sent/rest state |
| `digest_rest` | `false` | Not digest_rest (G-05-2) |
| `days_until_next_batch` | `null` | Empty default |

Plus any other already-declared `AdminShortlistResponse` fields at their empty defaults. Do **not** invent new API fields in this lock.

---

## Shape 2 — Empty unsent batch (D-04 #2)

When a current unsent batch exists (`sent_at IS NULL`) but `items` is empty:

| Field | Value | Notes |
|-------|-------|-------|
| `batch_id` | `<int>` | Present batch id (e.g. `7` in unit seed) |
| `items` | `[]` | Empty list, HTTP 200 |
| `week_label` | `week_start.isoformat()` | Same as non-empty path (D-06); e.g. `"2026-10-06"` |
| `sent_at` | `null` | Unsent |
| `digest_rest` | `false` | Not digest_rest (G-05-2) |
| `days_until_next_batch` | `null` | Empty default |

`batch_id` null-vs-int and `week_label` null-vs-isoformat MUST remain distinct from Shape 1. Do not collapse these into a single empty shape.

---

## Shape 3 — Non-empty items (full AdminShortlistItem DTO)

When `items` is non-empty, each element is an `AdminShortlistItemResponse` (`extra="forbid"`). Phase 13 (ADUX-01 / D-02 / D-03) grows the item schema **additively** — empty-batch shapes above stay `items=[]` and are unchanged.

| Item field | Source / notes |
|------------|----------------|
| `material_id`, `rank`, `title`, `material_status`, `decision`, `score`, `factor_labels`, `dek` | Pre-Phase-13 fields (unchanged) |
| `body_markdown` | From materials join; may be `null`/empty — never invent prose (D-06) |
| `provenance_label` | From materials join; may be `null` |
| `slug` | From materials join; may be `null` |
| `reading_minutes` | Stored estimate from materials join; may be `null` |
| `char_count` | `len(body_markdown or "")` (Python code-unit length) |
| `word_count` | `len((body_markdown or "").split())` — whitespace tokens aligned with `estimate_reading_minutes` |

Enrichment is via `ShortlistRepository.get_current_batch` join only — **no** second fetch / `/admin/materials/:id` (D-01).

**Named proof:** `tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items` — required-key asserts for the six additive fields plus critical seeded values; not full-body JSON equality (D-08 carry).

---

## Assert rules (D-08)

HTTP / unit proofs MUST assert **required keys + critical values only**:

- Status `200`
- Required keys present: `batch_id`, `items`, `week_label`, `sent_at`, `digest_rest`, `days_until_next_batch`
- Critical values per shape tables above (`items == []`, `batch_id` null-vs-int, `week_label` null-vs-`week_start.isoformat()`, `sent_at is null`, `digest_rest is false`, `days_until_next_batch is null`)
- For non-empty items: required keys include `body_markdown`, `provenance_label`, `slug`, `reading_minutes`, `char_count`, `word_count` (plus existing rank/title/dek/decision fields)

**Forbidden:** brittle full-body JSON equality such as `response.json() == {…}`. Additive *declared* fields must not force rewriting the whole blob.

---

## Response model posture (D-09)

Keep `AdminShortlistResponse` (and `AdminShortlistItemResponse`) with `extra="forbid"` (`ConfigDict(extra="forbid")`). Undeclared extras fail construction. Additive API fields require explicit model + test + PR — not silent accept. Phase 13 item growth is additive under this posture (D-03).

---

## Proof test names (D-05)

| Shape | pytest node id |
|-------|----------------|
| No batches (D-04 #1) | `tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id` |
| Empty unsent (D-04 #2) | `tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id` |
| Full items (ADUX-01) | `tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items` |

Surface: in-memory HTTP units only (`InMemoryShortlistRepository`) — D-07.

---

## Not empty — digest_rest (G-05-2)

After-send rest is a **third** distinct shape (`digest_rest=true`, typically null `batch_id` / null `week_label`, with `days_until_next_batch` set). It MUST NOT be confused with genuine empty (Shapes 1–2). Empty proofs assert `digest_rest is false`.

---

## Closed ban list — ADUX-04 / D-18 (Phase 13)

Assert-only helpers (D-17 — **do not** strip at render time). Closed tokens (lowercase normalize):

| Token | Notes |
|-------|-------|
| `test-header` | hyphen form |
| `test_header` | underscore form |
| `testheader` | concatenated (covers `testHeader` after `.lower()`) |

**Synced surfaces:**
- Python: `backend.domain.email_chrome.FORBIDDEN_LOWER` + `contains_forbidden_chrome`
- JS: `web/src/utils/forbiddenChrome.js` — `FORBIDDEN_LOWER` + `containsForbiddenChrome`
- Sync proof: `tests/unit/test_email_render.py::test_python_forbidden_lower_matches_js_mirror`
- Live scrub: `supabase-integration/migrations/010_phase13_scrub_test_header.sql` + runbook **§4g** (D-20)

Do **not** broaden this list without an explicit phase decision. Do **not** add an admin UI scrub control.

---

## Citations

D-04, D-05, D-08, D-09, D-10; FIX-01. Prior wave: `12-01-SUMMARY.md`.  
Phase 13 carry: D-01, D-02, D-03, D-06; ADUX-01 (`13-01-SUMMARY.md`).  
Phase 13 ban/scrub: D-17, D-18, D-20; ADUX-04 (`13-05`).

---

*Phase: 12-admin-shortlist-empty-batch-contract*  
*Lock authored for plan 12-02; item schema grown in plan 13-01 (D-03); ban list locked in plan 13-05 (D-18)*
