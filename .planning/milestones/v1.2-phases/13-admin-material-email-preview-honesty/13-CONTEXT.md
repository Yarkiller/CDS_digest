# Phase 13: Admin material & email preview honesty - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver ADUX-01…04: on `/admin/digest`, material preview shows a real body (not title+dek only), and «Превью письма» shows real email HTML (intro, per-material dek summaries + reader links, interstitial paragraph breaks) with no leaked `test-header` chrome. Draft→ready (ADUX-05) and score_factors honesty (ADUX-06) remain Phase 14. PIPE UI and live SMTP stay out of scope.

</domain>

<decisions>
## Implementation Decisions

### Material preview payload & layout (ADUX-01)
- **D-01:** Enrich `GET /admin/shortlist` — do **not** add fetch-on-open or a new `/admin/materials/<id>`. One endpoint, one DTO, one port path. — **Reversibility:** costly — SPA and tests will assume full item payloads on shortlist.
- **D-02:** Extend `AdminShortlistItem` / HTTP response with: `body_markdown`, `provenance_label`, `slug`, `reading_minutes`, `char_count`, `word_count`. Enrich via `ShortlistRepository.get_current_batch()` (and in-memory fake). Named proof: `test_admin_shortlist_returns_full_items`. — **Reversibility:** costly — `AdminShortlistResponse` stays `extra="forbid"`; additive fields need model + tests.
- **D-03:** Update Phase 12 lock artifact `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` so empty/non-empty **items** are full DTOs (not title-only). Empty-batch shapes from Phase 12 (D-04) stay; item schema grows. — **Reversibility:** costly — contract doc + FE mocks must stay aligned.
- **D-04:** Material modal renders **full markdown** with the same stack as the reader (`react-markdown` + sanitize), scrollable. Reader link is complementary, not a replacement for body. — **Reversibility:** reversible.
- **D-05:** Modal layout: **title → provenance → counts → body → reader link**. Counts row format: `~{char_count} символов · {word_count} слов · ~{reading_minutes} мин` (wording may be refined; both counts and minutes are required). — **Reversibility:** reversible.
- **D-06:** Empty/missing body is an **honest empty** state: muted «Текст материала недоступен»; no toast, no fail-closed. Other fields still shown. Empty counts may show `~0 символов · 0 слов · ~1 мин чтения` (or equivalent honest zeros). — **Reversibility:** reversible.

### Email HTML fidelity (ADUX-02)
- **D-07:** Backend owns email HTML via shared `render_email_html(...)` used by **preview and StubMailer send** (D-87 parity). FE must **not** construct email HTML. — **Reversibility:** costly — mail template becomes the send contract.
- **D-08:** FE renders with `<iframe srcDoc={html} sandbox="" />` (no JS/forms). Prefer iframe isolation over CSS-bleed risk from bare `dangerouslySetInnerHTML`. — **Reversibility:** reversible.
- **D-09:** Keep **`POST /admin/shortlist/preview`** with existing composition (`intro` + `blocks`) and D-86 fingerprint gate. Do not switch to GET-by-batch for composition. — **Reversibility:** costly if later changed — composition + fingerprint already wired to POST.
- **D-10:** Preview response is **additive**: keep plain `body` and add `html`. UI renders `html` only; plain `body` remains for StubMailer logs / text-only / debug. Include existing `subject` / `items` as needed; fingerprint may stay FE-side unless planner folds it into DTO. — **Reversibility:** reversible for optional fields; dropping `body` later would be a break.
- **D-11:** Per-material HTML block: **title + dek (omit dek if empty) +** `<a href="{site_url}/materials/{slug}">Читать →</a>`. No full body in email. No issue URL in preview (issue is created at send). `site_url` from settings (dev: `http://127.0.0.1:5173`). — **Reversibility:** costly — absolute URL shape becomes mailer contract.
- **D-12:** Parity proof: `test_preview_email_html_matches_send_html` (same composition → same `html`). Playwright: iframe present and contains a material title. — **Reversibility:** reversible.

### Interstitial paragraph contract (ADUX-03)
- **D-13:** `render_interstitial_html(text)`: outer `.strip()`; if empty omit; `html.escape` then split `\n\n` → `<p>`, single `\n` → `<br>`. Apply to **intro** and **interstitial text blocks**. — **Reversibility:** reversible.
- **D-14:** Plain `body` must **preserve internal `\n\n`** after the same outer strip (stop collapsing interstitial text to a single stripped line). HTML and plain share one whitespace source. — **Reversibility:** costly if clients already assumed collapsed body.
- **D-15:** FE light hint under connecting-text textarea: «Пустая строка = новый абзац». No markdown toolbar in this phase. — **Reversibility:** reversible.
- **D-16:** Unit coverage for interstitial helper (empty, whitespace-only, single para, two paras, single-newline, leading-whitespace, escape). Playwright may assert hint presence. — **Reversibility:** reversible.

### test-header cleanup (ADUX-04)
- **D-17:** **No runtime strip/filter** of bad tokens in renderers. Fix data + lock with regression asserts. — **Reversibility:** reversible (policy).
- **D-18:** Closed ban list (case-insensitive via lowercase normalize): `test-header`, `test_header`, `testheader` (covers `testHeader` after lowercasing). Shared helper synced Python ↔ TS; document list in updated FIX-01 / phase lock notes. — **Reversibility:** reversible — list can grow later.
- **D-19:** Assert surfaces for this phase: `render_email_html` unit output; Playwright admin material modal text; Playwright email preview iframe content; mocks/fixtures must not contain tokens. **Not** required: reader/public page asserts (data cleanup covers them; add later if UAT finds leaks). — **Reversibility:** reversible.
- **D-20:** Live cleanup via **checked-in numbered migration/SQL + runbook §** (same pattern as §4e). Planner/researcher must root-cause (grep seeds, live materials, intro). Phase DoD includes SQL artifact + green asserts; operator applies migration on shared VM. — **Reversibility:** one-way — migration applied on shared VM.

### Carried forward (do not re-open)
- Phase 5 **D-86**: mandatory successful email preview this session before Send unlocks.
- Phase 5 **D-87**: StubMailer; preview/send body honesty; no live SMTP.
- Phase 12 empty-batch HTTP shapes (null batch vs empty unsent) and `extra="forbid"` — extend item fields, do not collapse empty taxonomy.
- Phase 12 D-11: preview honesty was deferred here — now in scope.

### Claude's Discretion
- Exact Russian copy micro-variants for counts row / empty body (keep meaning).
- Whether `fingerprint` is API field or remains FE-only.
- Exact migration number/name once root cause is known (user suggested 010-style).
- How `char_count` / `word_count` are computed (shared helper vs DB columns) as long as DTO fields exist and match modal.
- iframe sandbox attribute details as long as no script/forms and isolation holds.
- Whether `recipient_count` appears on preview DTO (mentioned once; not required for ADUX-02).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/ROADMAP.md` — Phase 13 goal, success criteria, ADUX-01…04
- `.planning/REQUIREMENTS.md` — ADUX-01…04 wording
- `.planning/PROJECT.md` — v1.2 focus; preview honesty cluster
- `.planning/STATE.md` — current position Phase 13

### Prior phase locks
- `.planning/milestones/v1-phases/05-admin-digest-publish/05-CONTEXT.md` — D-86, D-87, preview→send
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-CONTEXT.md` — empty shapes; deferred preview to Phase 13
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — **MUST update** for full shortlist item DTO while keeping empty-batch shapes
- `.planning/milestones/v1.1-phases/10-cli-composition-uat/10-UAT.md` — UAT observations 1–4 that define this phase’s honesty bar

### Implementation surfaces
- `web/src/pages/AdminDigestPage.jsx` — `AdminItemPreview`, `AdminEmailPreview`, connecting text
- `web/src/pages/MaterialPage.jsx` — reader markdown + provenance pattern to mirror
- `web/src/services/adminApi.js` — shortlist + `previewEmail`
- `web/src/services/adminPreviewComposition.js` — composition fingerprint / body helpers
- `backend/src/backend/interface/http/routes/admin.py` — shortlist + preview DTOs (`extra="forbid"`)
- `backend/src/backend/application/use_cases/preview_digest_email.py` — compose/preview (extend with HTML)
- `backend/src/backend/application/use_cases/send_digest.py` — must share `render_email_html`
- `backend/src/backend/domain/shortlist.py` — `ShortlistItem` / `AdminShortlistItem` enrichment
- `backend/src/backend/domain/material.py` — `provenance_label`, `reading_minutes`
- `backend/src/backend/tests_support/in_memory.py` — enriched in-memory shortlist
- `docs/agents/local-platform-runbook.md` — §4e seed pattern; add ADUX-04 cleanup §
- `tests/admin.spec.js` — admin Playwright
- `tests/unit/test_http_admin.py` — shortlist/preview HTTP unit

### Architecture / TDD
- `.cursor/rules/architecture.mdc` — Ports & Adapters; thin HTTP; FE via `web/src/services/`
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — no production code without failing test first

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AdminItemPreview` / `AdminEmailPreview` modals in `AdminDigestPage.jsx` — extend in place.
- Reader markdown stack on `MaterialPage.jsx` (`react-markdown` + sanitize).
- `preview_digest_email` + `compose_digest_segments` — today title-bullet plain body; add shared HTML renderer used by send.
- `adminPreviewComposition.js` — fingerprint + mock composition; keep POST composition contract.
- Phase 12 sticky mock flags / empty DTO harness — extend mocks with full item fields + `html`.
- Domain `Material.provenance_label` / `reading_minutes` already exist; shortlist DTO currently omits them.

### Established Patterns
- Admin HTTP models: Pydantic `extra="forbid"`; additive fields require explicit model updates.
- StubMailer / preview parity (D-87): one composition path for preview and send.
- Honesty empty states (D-80 / Phase 4): never invent content; show explicit unavailable copy.
- Runbook + numbered SQL for shared-VM seeds/cleanups (§4e pattern).

### Integration Points
- `GET /admin/shortlist` → enriched items → material modal (no second fetch).
- `POST /admin/shortlist/preview` → `{ subject, body, html, items }` → sandboxed iframe.
- Send path must call the same `render_email_html` as preview.
- Migration + runbook for live `test-header` purge; asserts on admin preview surfaces.

</code_context>

<specifics>
## Specific Ideas

- Counts display example: `~8500 chars · 1200 words · ~6 min` (RU copy in UI).
- Empty body placeholder exactly: «Текст материала недоступен».
- Email CTA label: «Читать →».
- Hint copy: «Пустая строка = новый абзац».
- Ban-list helper: `FORBIDDEN_LOWER = ["test-header", "test_header", "testheader"]` with `.lower()` normalize.
- Suggested tests: `test_admin_shortlist_returns_full_items`, `test_preview_email_html_matches_send_html`, interstitial helper matrix, Playwright iframe + modal + hint + ban asserts.
- User noted payload size OK: ≤5 items × ~30KB admin-only.

</specifics>

<deferred>
## Deferred Ideas

- Admin draft→ready control (ADUX-05) — Phase 14
- score_factors / «Обоснование» honesty (ADUX-06) — Phase 14
- CLI `--debug` — Phase 15
- PIPE-01 config UI — Phase 16
- Live SMTP — v1.3
- Markdown toolbar / live preview for connecting text — later polish
- Reader/public ban-list asserts — only if UAT finds leaks outside admin
- Broader seed-chrome ban list (`lorem`, `TODO`, etc.) — rejected for this phase

</deferred>

---

*Phase: 13-Admin material & email preview honesty*
*Context gathered: 2026-10-02*
