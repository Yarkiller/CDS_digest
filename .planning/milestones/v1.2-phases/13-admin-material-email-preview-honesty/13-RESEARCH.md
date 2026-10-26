# Phase 13: Admin material & email preview honesty - Research

**Researched:** 2026-10-02
**Domain:** Admin shortlist DTO enrichment, shared email HTML render, sandboxed FE preview, seed-chrome cleanup
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- Admin draft→ready control (ADUX-05) — Phase 14
- score_factors / «Обоснование» honesty (ADUX-06) — Phase 14
- CLI `--debug` — Phase 15
- PIPE-01 config UI — Phase 16
- Live SMTP — v1.3
- Markdown toolbar / live preview for connecting text — later polish
- Reader/public ban-list asserts — only if UAT finds leaks outside admin
- Broader seed-chrome ban list (`lorem`, `TODO`, etc.) — rejected for this phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADUX-01 | Admin material preview shows `body_markdown`, `provenance_label`, char/word counts, link to `/materials/<slug>` | Enrich shortlist join + DTO; modal mirrors `MaterialPage` markdown stack; counts helpers |
| ADUX-02 | «Превью письма» shows real email HTML (intro, summaries, links) | Shared `render_email_html`; additive `html` on preview; sandboxed iframe; send parity |
| ADUX-03 | Interstitial `\n\n` → visible paragraphs | `render_interstitial_html` + plain-body whitespace contract; FE hint |
| ADUX-04 | No leaked `test-header` chrome on admin preview after cleanup | Ban-list helpers + migration/runbook + regression asserts (no runtime strip) |
</phase_requirements>

## Summary

Phase 13 closes the honesty gap documented in Phase 10 UAT: admin material preview is title+dek only, email preview is titles-only plain text, interstitial newlines are not treated as paragraphs, and seed/test chrome (`test-header`) must not reappear on admin surfaces. Locked decisions require a **single enriched shortlist payload** (no second fetch), a **backend-owned HTML email renderer** shared by preview and StubMailer send, FE display via **sandboxed `srcDoc` iframe**, and **data+assert cleanup** (not runtime filtering).

Current code confirms the gap: `AdminShortlistItemResponse` stops at `dek`; Supabase shortlist select is `materials(title,status,dek)`; `compose_digest_segments` emits `- {title}` only; `AdminItemPreview` / `AdminEmailPreview` render title+dek / plain `body`. No new npm packages are required — the reader already ships `react-markdown` + `remark-gfm` + `rehype-sanitize` + `rehype-slug`.

**Primary recommendation:** Extend `ShortlistItem` + repository join → enrich admin DTO → add pure `render_interstitial_html` / `render_email_html` used by preview and send → FE modal markdown + iframe; ship migration `010_*` + runbook § for live scrub; update FIX-01 lock item schema; TDD proofs named in CONTEXT.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Shortlist item enrichment (`body_markdown`, slug, counts, …) | API / Backend | Database / Storage | Domain/use-case DTO from repository join; DB holds material columns |
| Material modal markdown render | Browser / Client | — | Mirror reader stack; consume shortlist DTO only |
| Email HTML composition | API / Backend | — | Single renderer for preview+send (D-07/D-87); FE must not invent HTML |
| Email HTML display | Browser / Client | — | Sandboxed iframe `srcDoc` isolation (D-08) |
| Interstitial paragraph split | API / Backend | Browser / Client | Backend owns HTML/plain contract; FE only shows hint copy |
| D-86 preview fingerprint gate | Browser / Client | — | Already FE-side; keep unless planner adds API field |
| Ban-list regression helpers | API / Backend + Browser / Client | — | Synced Python↔TS; asserts only, no render-time strip |
| Live `test-header` purge | Database / Storage | — | Checked-in migration + operator apply on shared VM |

## Project Constraints (from CLAUDE.md / AGENTS.md)

No root `CLAUDE.md` present this session. Actionable directives from `AGENTS.md` + workspace rules:

- **TDD mandatory:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST (Red–Green–Refactor).
- **Ports & Adapters:** domain/application free of supabase/httpx/fastapi; adapters in `supabase-integration`; wiring only in `backend/.../composition/`.
- **Frontend API access** only via `web/src/services/`; UI must not deep-couple to Supabase.
- **Git `origin`:** push/pull/auth via WSL only (not planning-critical for this phase).
- **Project skills available:** `.agents/skills/hallmark` (design — preserve existing admin chrome; do not redesign digest page), `.agents/skills/supabase` / `supabase-postgres-best-practices` (migration hygiene for ADUX-04).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI / Pydantic | `fastapi==0.141.1` (workspace) | Admin HTTP DTOs `extra="forbid"` | Existing admin surface |
| Python `html` stdlib | 3.12+ (project `requires-python = ">=3.12"`) | `html.escape` for interstitial/email text | Official escape; no new dep `[VERIFIED: docs.python.org/3/library/html.html]` |
| `react-markdown` | `10.1.0` (web lock / npm view) | Material modal body | Already used on `MaterialPage.jsx` `[VERIFIED: web/package.json]` |
| `remark-gfm` | `4.0.1` | GFM tables/lists in modal | Same reader stack |
| `rehype-sanitize` | `6.0.0` | XSS safety net for markdown | Official react-markdown security guidance `[CITED: remarkjs/react-markdown readme]` |
| `rehype-slug` | `6.0.0` | Heading ids (reader parity) | Already in reader |
| Playwright | `@playwright/test` `^1.62.1` | Admin modal + iframe e2e | Existing `tests/admin.spec.js` |
| pytest | `>=8.3.0` (workspace dev) | Unit/HTTP proofs | `uv run pytest` / `npm run test:unit` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| StubMailer | in-repo | Log send body / optional html for parity | Always for D-87; no SMTP |
| Supabase JS/Python adapters | existing | Expand materials join on shortlist load | Live container only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Backend HTML + iframe | FE-built HTML from DTO | Forbidden by D-07 |
| `dangerouslySetInnerHTML` | Sandboxed iframe | Higher CSS/XSS bleed risk; rejected by D-08 |
| New `/admin/materials/:id` | Enrich shortlist | Extra round-trip; rejected by D-01 |
| Runtime ban-token strip | Data migration + asserts | Masks root cause; rejected by D-17 |

**Installation:**
```bash
# No new packages required — reuse existing web markdown stack and Python stdlib.
# If planner accidentally proposes new deps, stop and re-check this research.
```

**Version verification:** `npm view react-markdown version` → `10.1.0`; `rehype-sanitize` → `6.0.0`; `remark-gfm` → `4.0.1` (2026-10-02). Python `html.escape` confirmed via `help(html.escape)` and official docs.

## Package Legitimacy Audit

> No **new** external packages for this phase. Existing packages used by the phase were checked.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| react-markdown | npm | since ~2015 / pub 2025-03-07 | ~42M/wk | github.com/remarkjs/react-markdown | OK | Approved (already installed) |
| rehype-sanitize | npm | pub 2023-08-26 | ~14M/wk | github.com/rehypejs/rehype-sanitize | OK | Approved (already installed) |
| remark-gfm | npm | pub 2025-02-10 | ~49M/wk | github.com/remarkjs/remark-gfm | OK | Approved (already installed) |
| rehype-slug | npm | pub 2023-08-31 | ~4.9M/wk | github.com/rehypejs/rehype-slug | OK | Approved (already installed) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
Admin SPA (/admin/digest)
  │
  ├─ GET /admin/shortlist ──────────────────────────────┐
  │     ShortlistRepository.get_current_batch()         │
  │       materials(title,status,dek,body_markdown,     │
  │                slug,provenance_label,reading_minutes)│
  │     → AdminShortlistItem (+ char_count/word_count)  │
  │     → AdminItemPreview (react-markdown + sanitize)  │
  │                                                     │
  └─ POST /admin/shortlist/preview {intro, blocks} ─────┤
        compose_digest_segments (order + plain segs)    │
        render_email_html(site_url, intro, materials…)  │
        → { subject, body, html, items }                │
        → <iframe sandbox="" srcDoc={html} />           │
                                                        │
  POST /admin/shortlist/send (same composition) ────────┘
        claim_and_publish → issue_url header in plain body
        render_email_html(...)  # same html as preview (no issue URL in html per D-11)
        StubMailer.send_digest(body_text=…, body_html=…)
```

### Recommended Project Structure
```
backend/src/backend/
  domain/shortlist.py              # ShortlistItem + AdminShortlistItem fields
  domain/email_chrome.py           # FORBIDDEN_LOWER ban tokens (optional home)
  application/use_cases/
    get_admin_shortlist.py         # map enriched items + counts
    preview_digest_email.py        # DigestEmailPreview.html; call render_*
    send_digest.py                 # share render_email_html
    email_render.py                # NEW: render_interstitial_html, render_email_html, counts
  composition/settings.py          # SITE_URL / PUBLIC_SITE_URL
  interface/http/routes/admin.py   # additive DTO fields; pass site_url
  infrastructure/stub_mailer.py    # optional last_body_html
supabase-integration/
  shortlist_repository.py          # expand materials(...) select
  migrations/010_phase13_scrub_test_header.sql
web/src/
  pages/AdminDigestPage.jsx        # AdminItemPreview + AdminEmailPreview + hint
  services/adminApi.js             # typedefs + mocks + preview html
  utils/forbiddenChrome.js         # TS ban-list mirror
tests/unit/
  test_http_admin.py               # test_admin_shortlist_returns_full_items
  test_email_render.py             # interstitial matrix + html parity
  test_preview_digest.py           # html field
tests/admin.spec.js               # iframe + modal + hint + ban asserts
docs/agents/local-platform-runbook.md  # new § after 4e
.planning/phases/12-.../12-FIX-01-LOCK.md  # item schema growth
```

### Pattern 1: Enrich at repository boundary, count in use-case
**What:** Load material columns once in `get_current_batch` → map into `ShortlistItem` → `get_admin_shortlist` computes `char_count`/`word_count` for `AdminShortlistItem`.
**When to use:** ADUX-01 (D-01/D-02).
**Example:**
```python
# Current select (must widen) — [VERIFIED: supabase-integration/.../shortlist_repository.py:205-208]
# "decided_by,decided_at,materials(title,status,dek)"
# Target select:
# materials(title,status,dek,body_markdown,slug,provenance_label,reading_minutes)
```

### Pattern 2: Shared email HTML renderer (preview ≡ send composition)
**What:** Pure functions take intro + ordered materials (title/dek/slug) + text blocks + `site_url`; return HTML string. Preview and send call the same function before/without issue URL in HTML (D-11).
**When to use:** ADUX-02/03.
**Example:**
```python
# Source: docs.python.org/3/library/html.html — html.escape
import html

def render_interstitial_html(text: str) -> str:
    trimmed = text.strip()
    if not trimmed:
        return ""
    safe = html.escape(trimmed, quote=True)
    paragraphs = safe.split("\n\n")
    parts: list[str] = []
    for para in paragraphs:
        if not para:
            continue
        parts.append("<p>" + para.replace("\n", "<br>") + "</p>")
    return "".join(parts)
```

### Pattern 3: Sandboxed iframe for email HTML
**What:** FE displays backend `html` only via `<iframe sandbox="" srcDoc={html} title="…"/>`.
**When to use:** ADUX-02 (D-08).
**Example:**
```jsx
// Source: MDN iframe sandbox — empty sandbox applies all restrictions
<iframe
  data-testid="email-preview-frame"
  title="Превью письма HTML"
  sandbox=""
  srcDoc={emailModal.preview.html}
  className="mt-3 min-h-64 w-full rounded-xl border border-rule bg-white"
/>
```

### Anti-Patterns to Avoid
- **FE-constructed email HTML from titles/deks:** breaks D-07/D-87 parity.
- **Second fetch for material body:** breaks D-01.
- **Runtime strip of `test-header` in renderers:** breaks D-17.
- **Collapsing interstitial to `.strip()` then single line:** breaks D-14.
- **`allow-scripts` + `allow-same-origin` on iframe:** sandbox escape risk `[CITED: MDN iframe sandbox]`.
- **Putting business HTML assembly in FastAPI router:** keep thin HTTP; render in application helpers.
- **Full-body JSON equality in empty-batch tests:** FIX-01 D-08 forbids brittle blob equality — use required-key asserts; extend item schema docs only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML entity escaping | Custom replace maps | `html.escape` | Missed entities / quote edge cases |
| Markdown rendering | Custom markdown parser | `react-markdown` + sanitize | XSS + GFM already solved in reader |
| Email HTML isolation | `dangerouslySetInnerHTML` | sandboxed iframe `srcDoc` | CSS/JS bleed; D-08 |
| Word/minute estimate reinvent | Ad-hoc FE math | Align with `estimate_reading_minutes` word split (`split()` / 200) for words; use stored `reading_minutes` for minutes | Ingest already defines minutes `[VERIFIED: ingestion-service/.../material_completion.py:14-15]` |
| Ban-list drift Python vs TS | Copy-paste ad hoc | Shared constant lists + unit asserting identical tokens | ADUX-04 D-18 |

**Key insight:** Honesty is a **shared composition contract** (shortlist enrich + one HTML renderer + data cleanup), not a UI polish layer.

## Runtime State Inventory

> Data cleanup / migration phase (ADUX-04).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Live `materials` rows on shared VM (`knowledge-db.ru`); UAT logged `test-header` leak. MCP `materials` sample (ids 2–12) showed **no** `test-header` in title/dek/provenance; title `ilike.%test%` returned `[]`. Checked-in seeds `002`/`005` contain **no** `test-header` string. | Idempotent scrub SQL still required (defensive + future re-seed); verify with SQL before/after apply. Possible root cause: transient UAT content, later overwritten ingest, or non-material field — migration should scrub `title`,`dek`,`body_markdown`,`provenance_label` where lower(text) matches ban tokens. |
| Live service config | None found for `test-header` string in n8n/etc. | none |
| OS-registered state | None | none |
| Secrets/env vars | New recommended `SITE_URL` / `PUBLIC_SITE_URL` (not secret); document in `.env.example` | code + env template edit; no secret rename |
| Build artifacts | None specific to rename | none |

**Nothing found in category** (OS / live service config / build artifacts): None — verified by repo grep of seeds + MCP materials sample + absence of OS registration concerns for this phase.

## Common Pitfalls

### Pitfall 1: Forgetting `extra="forbid"` model updates
**What goes wrong:** Response construction fails or FE fields silently drop.
**Why it happens:** `AdminShortlistItemResponse` / `DigestPreviewResponse` forbid undeclared keys `[VERIFIED: admin.py:35-46,77-83]`.
**How to avoid:** Add fields to Pydantic models + domain dataclasses + in-memory fake + mocks in one wave.
**Warning signs:** 500 on GET shortlist after enrich; Playwright missing body.

### Pitfall 2: Preview HTML ≠ send HTML
**What goes wrong:** Admin trusts preview; StubMailer logs diverge.
**Why it happens:** Separate string builders; send prepends issue URL to plain body only.
**How to avoid:** One `render_email_html`; parity unit `test_preview_email_html_matches_send_html`; issue URL stays out of HTML (D-11) and only in plain send wrapper.
**Warning signs:** Parity test fails when intro/blocks include `\n\n` or dek.

### Pitfall 3: Playwright still targets `email-preview-body`
**What goes wrong:** Suite red after iframe switch.
**Why it happens:** Existing tests use `getByTestId("email-preview-body")` plain text `[VERIFIED: tests/admin.spec.js usages]`.
**How to avoid:** Wave 0 update helpers to `frameLocator('[data-testid=email-preview-frame]')` (or keep plain body testid hidden for debug only).
**Warning signs:** Multiple ADMIN-04 e2e failures on body text.

### Pitfall 4: Joining segments with `\n` collapses visual paragraphs in HTML only
**What goes wrong:** Plain shows `\n\n` but HTML looks flat if interstitial helper not applied to intro/text.
**Why it happens:** `compose_digest_body` joins with `"\n".join(parts)` `[VERIFIED: preview_digest_email.py:52-58]`; HTML needs `<p>` split.
**How to avoid:** Apply `render_interstitial_html` to intro + text blocks; material blocks use title/dek/link template.
**Warning signs:** ADUX-03 unit matrix fails on two-para case.

### Pitfall 5: Payload / select omission of `body_markdown`
**What goes wrong:** Modal empty despite ready materials.
**Why it happens:** Current join omits body `[VERIFIED: shortlist_repository.py:205-208]`.
**How to avoid:** Widen select + `_item_from_row` + in-memory seeds used by HTTP tests.
**Warning signs:** `body_markdown` null/absent in GET JSON.

### Pitfall 6: Ban-list runtime filter creep
**What goes wrong:** Bugs hide behind silent strip.
**Why it happens:** Tempting quick fix for UAT chrome.
**How to avoid:** Assert-only helpers; scrub SQL; document D-17 in lock notes.
**Warning signs:** Renderer imports ban-list for mutate/filter.

## Code Examples

### Counts helper (discretion, recommended)
```python
# Align word split with ingestion estimate_reading_minutes:
# return max(1, math.ceil(len(body_markdown.split()) / 200))
# [VERIFIED: ingestion-service/src/ingestion_service/domain/material_completion.py:14-15]

def material_counts(body_markdown: str) -> tuple[int, int]:
    text = body_markdown or ""
    return len(text), len(text.split())
# reading_minutes: use stored ShortlistItem.reading_minutes from materials row
```

### Email material block (D-11)
```python
def render_material_email_block(*, title: str, dek: str | None, slug: str, site_url: str) -> str:
    base = site_url.rstrip("/")
    href = html.escape(f"{base}/materials/{slug}", quote=True)
    parts = [f"<h2>{html.escape(title)}</h2>"]
    if dek and dek.strip():
        parts.append(f"<p>{html.escape(dek.strip())}</p>")
    parts.append(f'<p><a href="{href}">Читать →</a></p>')
    return "".join(parts)
```

### Settings site_url (discretion)
```python
# composition/settings.py — additive
# site_url: str = "http://127.0.0.1:5173"
# from_env: env.get("SITE_URL") or env.get("PUBLIC_SITE_URL") or default
```

### Ban list (D-18 verbatim)
```python
FORBIDDEN_LOWER = ["test-header", "test_header", "testheader"]

def contains_forbidden_chrome(text: str) -> bool:
    lowered = (text or "").lower()
    return any(token in lowered for token in FORBIDDEN_LOWER)
```

### Reader markdown stack to mirror (ADUX-01 D-04)
```jsx
// Source: web/src/pages/MaterialPage.jsx — existing production pattern
<Markdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeSlug, rehypeSanitize]}
>
  {material.body_markdown}
</Markdown>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Title+dek admin modal | Full body + provenance + counts + reader link | Phase 13 | ADUX-01 honesty |
| Titles-only plain email preview | Backend HTML + iframe | Phase 13 | ADUX-02 |
| Interstitial strip-only | strip + `\n\n`→`<p>` / plain keep `\n\n` | Phase 13 | ADUX-03 |
| Ignore seed chrome | Migration + ban asserts (no runtime strip) | Phase 13 | ADUX-04 |

**Deprecated/outdated:**
- Relying on FE `composePreviewBody` as the honesty surface for email — keep for mocks/plain fallback, but live UI must prefer backend `html`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `char_count = len(body_markdown)` (raw length including whitespace/newlines) | Counts helper | Modal numbers disagree with editorial expectation; adjust to NFC/stripped if user prefers |
| A2 | Keep fingerprint FE-only (no API field) | Discretion | None functional; only debug/telemetry |
| A3 | `test-header` UAT leak was transient / overwritten; scrub migration still ships | Runtime inventory | Migration may update 0 rows — still OK if asserts + fixtures green |
| A4 | StubMailer gains optional `body_html` kwarg without breaking Protocol callers immediately (additive) | Mailer | Need coordinated Protocol + all fakes update |
| A5 | Preview HTML omits issue URL; send plain body may still prepend issue URL while HTML stays composition-only | Email parity | Misread of D-11 vs send header — confirm in plan acceptance |

**If this table is empty:** N/A — several discretionary items remain.

## Open Questions (RESOLVED)

1. **Exact live root of `test-header`** — RESOLVED
   - What we know: not in checked-in seeds; not in current MCP title/dek/provenance sample; UAT recorded leak in Phase 10.
   - **Answer (Plans 13-05):** Ship idempotent migration `010_phase13_scrub_test_header.sql` scrubbing `materials` `title`/`dek`/`body_markdown`/`provenance_label` for the closed ban tokens + runbook `## 4f` verify/apply. Historical row may be gone (0-row apply OK); green asserts + SQL artifact satisfy local DoD; shared-VM apply via preferred gate `apply-after-sql` for live goal criterion 4 (D-20).

2. **`SITE_URL` env name** — RESOLVED
   - What we know: CONTEXT says settings, default `http://127.0.0.1:5173`; `.env.example` has no site URL today.
   - **Answer (Plan 13-02):** Primary env `SITE_URL`, fallback `PUBLIC_SITE_URL`, then default `http://127.0.0.1:5173` on `Settings.site_url`; document `SITE_URL` in `.env.example` (D-11).

3. **Plain-body material segment richness** — RESOLVED
   - What we know: HTML must be title+dek+link; plain `body` kept (D-10/D-14).
   - **Answer (Plans 13-02 / 13-06):** Preserve internal `\n\n` after outer strip on intro/interstitial plain segments (D-14; Plan 02). Enrich plain material segments to title + optional dek + absolute `{site_url}/materials/{slug}` for StubMailer log honesty (Plan 02 compose + Plan 06 send parity). FE continues to render `html` only (D-10); plain body is not the user-visible preview surface.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | unit tests / backend | ✓ | 3.14.0 (runtime); project `>=3.12` | — |
| Node / npm | Playwright / web | ✓ | node v22.13.0 / npm 11.18.0 | — |
| `uv` / pytest | `npm run test:unit` | ✓ | workspace pytest | — |
| Playwright | admin e2e | ✓ | @playwright/test ^1.62.1 | — |
| Supabase MCP query | ADUX-04 root-cause | ✓ (select) | — | raw_sql needs POSTGRES_URL (unavailable) — use select/filter + operator SQL |
| Shared VM apply | migration 010 | operator | — | runbook § apply via Studio/psql |

**Missing dependencies with no fallback:**
- None for local TDD. Operator apply of migration remains a human DoD step (same as §4e).

**Missing dependencies with fallback:**
- `raw_sql` MCP (no POSTGRES_URL): use table `query` + operator-run verify SQL in runbook.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (unit) + Playwright (e2e) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| Quick run command | `uv run pytest tests/unit/test_email_render.py tests/unit/test_http_admin.py -x` |
| Full suite command | `npm run test:unit && npm run test:web` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADUX-01 | Full shortlist item fields on GET | unit/http | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items -x` | ❌ Wave 0 |
| ADUX-01 | Modal shows body + provenance + counts + link | e2e | `npx playwright test tests/admin.spec.js -g "material preview"` | ❌ Wave 0 |
| ADUX-02 | Preview DTO includes `html` | unit | `uv run pytest tests/unit/test_preview_digest.py -k html -x` | ❌ Wave 0 |
| ADUX-02 | preview html == send html | unit | `uv run pytest -k test_preview_email_html_matches_send_html -x` | ❌ Wave 0 |
| ADUX-02 | iframe shows material title | e2e | Playwright frameLocator assert | ❌ Wave 0 (update existing preview tests) |
| ADUX-03 | interstitial helper matrix | unit | `uv run pytest tests/unit/test_email_render.py -x` | ❌ Wave 0 |
| ADUX-03 | hint copy under connecting text | e2e | Playwright text assert | ❌ Wave 0 |
| ADUX-04 | ban helper + render output clean | unit | pytest ban + html fixtures | ❌ Wave 0 |
| ADUX-04 | mocks/fixtures free of tokens | unit/e2e | grep/assert helpers | ❌ Wave 0 |
| FIX-01 carry | empty shapes still green | unit | existing empty-batch tests | ✅ |

### Sampling Rate
- **Per task commit:** focused pytest file(s) for the task
- **Per wave merge:** `npm run test:unit`
- **Phase gate:** `npm run test:unit && npm run test:web` green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_email_render.py` — interstitial matrix + `render_email_html` + ban asserts (ADUX-02/03/04)
- [ ] `tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items` — ADUX-01
- [ ] `tests/unit/test_preview_digest.py` / send tests — html field + parity
- [ ] Update `tests/admin.spec.js` email preview selectors for iframe
- [ ] Extend FE mocks in `web/src/services/adminApi.js` with full item fields + `html`
- [ ] Update `12-FIX-01-LOCK.md` item schema section (D-03)
- [ ] Migration `010_phase13_scrub_test_header.sql` + runbook §
- [ ] In-memory shortlist seeds must carry new `ShortlistItem` fields

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (existing) | `require_admin` on shortlist/preview/send |
| V3 Session Management | yes (existing) | Supabase JWT bearer |
| V4 Access Control | yes | Admin-only enrichment/preview; no new public leak of draft bodies beyond admin |
| V5 Input Validation | yes | Pydantic `extra="forbid"`; `html.escape` on interstitial/title/dek; markdown sanitize in modal |
| V6 Cryptography | no | — |

### Known Threat Patterns for admin email preview

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via material title/dek/interstitial in email HTML | Tampering | `html.escape` before tags; no raw markdown in email HTML |
| XSS via `srcDoc` | Tampering | Empty `sandbox` (no scripts/forms); backend-escaped HTML only |
| XSS via admin material markdown modal | Tampering | `rehype-sanitize` (reader stack) |
| Over-exposure of draft body via shortlist | Information disclosure | Admin-only endpoint (existing); still enrich drafts for triage honesty |
| Open redirect / wrong site_url | Spoofing | Absolute URL from trusted settings, not client-supplied |
| Silent chrome filter masking bad data | Repudiation | D-17: no runtime strip; migration + asserts |

## Sources

### Primary (HIGH confidence)
- In-repo reads: `admin.py`, `preview_digest_email.py`, `send_digest.py`, `shortlist.py`, `shortlist_repository.py`, `AdminDigestPage.jsx`, `MaterialPage.jsx`, `adminApi.js`, `adminPreviewComposition.js`, `12-FIX-01-LOCK.md`, `10-UAT.md`, `material_completion.py`, `settings.py`, `stub_mailer.py`
- [docs.python.org/3/library/html.html](https://docs.python.org/3/library/html.html) — `html.escape`
- Context7 `/remarkjs/react-markdown` — sanitize + remark-gfm
- Context7 / MDN — iframe `sandbox` / `srcdoc`
- gsd package-legitimacy check — npm packages OK
- Supabase MCP `materials` sample — live root-cause probe

### Secondary (MEDIUM confidence)
- MDN/WebSearch synthesis on empty sandbox restrictions
- Phase 10 UAT observation of `test-header` (historical; may not be present now)

### Tertiary (LOW confidence)
- Exact historical row that contained `test-header` (raw_sql unavailable without POSTGRES_URL)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified; no new packages
- Architecture: HIGH — locked CONTEXT + verified code seams
- Pitfalls: HIGH — grounded in current tests/models/selects

**Research date:** 2026-10-02
**Valid until:** 2026-11-01 (stable admin stack; re-check if mailer Protocol changes)

## Discretion Recommendations (for planner)

1. **Fingerprint:** keep FE-only (`compositionFingerprint`) — already wired to D-86 gate.
2. **Counts:** compute `char_count`/`word_count` in `get_admin_shortlist` from `body_markdown`; pass through stored `reading_minutes`.
3. **Migration name:** `010_phase13_scrub_test_header.sql` + runbook `## 4f. Phase 13 test-header scrub (ADUX-04)`.
4. **iframe:** `sandbox=""` (empty string) + `data-testid="email-preview-frame"`; do not add allow-scripts.
5. **recipient_count on preview:** omit.
6. **Mailer:** add optional `body_html: str | None = None` to `Mailer.send_digest` / StubMailer for parity logging without requiring SMTP multipart yet.
