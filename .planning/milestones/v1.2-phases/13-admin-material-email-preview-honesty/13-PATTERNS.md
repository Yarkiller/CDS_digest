# Phase 13: Admin material & email preview honesty - Pattern Map

**Mapped:** 2026-10-02
**Files analyzed:** 24
**Analogs found:** 24 / 24

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/domain/shortlist.py` | model | transform | `backend/src/backend/domain/shortlist.py` (extend in place) | exact |
| `backend/src/backend/domain/email_chrome.py` | utility | transform | `backend/src/backend/domain/shortlist.py` (`honest_factor_labels`) | role-match |
| `backend/src/backend/application/use_cases/email_render.py` | service | transform | `backend/src/backend/application/use_cases/preview_digest_email.py` (`compose_digest_*`) | role-match |
| `backend/src/backend/application/use_cases/get_admin_shortlist.py` | service | request-response | same file (enrich mapping) | exact |
| `backend/src/backend/application/use_cases/preview_digest_email.py` | service | request-response | same file (+ call `render_email_html`) | exact |
| `backend/src/backend/application/use_cases/send_digest.py` | service | request-response | same file (+ shared HTML) | exact |
| `backend/src/backend/application/ports/mailer.py` | middleware | request-response | same file (additive `body_html`) | exact |
| `backend/src/backend/infrastructure/stub_mailer.py` | service | request-response | same file | exact |
| `backend/src/backend/composition/settings.py` | config | request-response | same file (`mailer` / `from_env`) | exact |
| `backend/src/backend/interface/http/routes/admin.py` | route | request-response | same file (DTO + thin handlers) | exact |
| `backend/src/backend/tests_support/in_memory.py` | test | CRUD | same file (`InMemoryShortlistRepository`) | exact |
| `supabase-integration/src/supabase_integration/shortlist_repository.py` | service | CRUD | same file (`_item_from_row` + select) | exact |
| `supabase-integration/migrations/010_phase13_scrub_test_header.sql` | migration | batch | `supabase-integration/migrations/007_phase9_persist_draft.sql` | role-match |
| `web/src/pages/AdminDigestPage.jsx` | component | request-response | same file + `web/src/pages/MaterialPage.jsx` (markdown) | exact / partial |
| `web/src/services/adminApi.js` | service | request-response | same file (typedefs + mocks + `previewEmail`) | exact |
| `web/src/utils/forbiddenChrome.js` | utility | transform | `web/src/utils/markdownToc.js` | role-match |
| `tests/unit/test_email_render.py` | test | transform | `tests/unit/test_preview_digest.py` | role-match |
| `tests/unit/test_http_admin.py` | test | request-response | same file (`test_admin_shortlist_*`) | exact |
| `tests/unit/test_preview_digest.py` | test | request-response | same file | exact |
| `tests/unit/test_send_digest.py` | test | request-response | same file (`test_send_body_includes_*`) | exact |
| `tests/admin.spec.js` | test | request-response | same file (`email-preview-body` → iframe) | exact |
| `docs/agents/local-platform-runbook.md` | config | batch | same file (`## 4e`) | exact |
| `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` | config | request-response | same file (item schema growth) | exact |
| `.env.example` | config | request-response | same file (`APP_CONTAINER` / `MAILER` style) | exact |

## Pattern Assignments

### `backend/src/backend/domain/shortlist.py` (model, transform)

**Analog:** same file — frozen dataclasses + pure helpers

**Core pattern** (lines 40–71): extend `ShortlistItem` / `AdminShortlistItem` additively (do not rename existing fields):
```python
@dataclass(frozen=True)
class ShortlistItem:
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None
    score_factors: Mapping[str, Any]
    decided_by: str | None = None
    decided_at: datetime | None = None
    dek: str | None = None
    # Phase 13 additions (D-02): body_markdown, provenance_label, slug,
    # reading_minutes — defaults keep existing call sites compiling.

@dataclass(frozen=True)
class AdminShortlistItem:
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None
    factor_labels: tuple[str, ...]
    dek: str | None = None
    # Phase 13: body_markdown, provenance_label, slug, reading_minutes,
    # char_count, word_count
```

**Field source of truth for material columns:** `backend/src/backend/domain/material.py` lines 15–25 (`slug`, `body_markdown`, `reading_minutes`, `provenance_label`).

---

### `backend/src/backend/domain/email_chrome.py` (utility, transform) — NEW

**Analog:** `backend/src/backend/domain/shortlist.py` (`honest_factor_labels` — pure domain helper, assert-only consumers)

**Imports / helper pattern** (lines 10–37):
```python
def honest_factor_labels(score_factors: Mapping[str, Any] | None) -> list[str]:
    """Return readable factor labels only when ≥2 exist; else [] …"""
    if not score_factors:
        return []
    # … normalize → filter → return
```

**Copy for ban list (D-18):** same style — module-level `FORBIDDEN_LOWER` constant + `contains_forbidden_chrome(text: str) -> bool` with `.lower()` normalize. **Do not** call from renderers to mutate output (D-17).

---

### `backend/src/backend/application/use_cases/email_render.py` (service, transform) — NEW

**Analog:** `backend/src/backend/application/use_cases/preview_digest_email.py` — pure compose helpers co-located with use-cases, no FastAPI/Supabase

**Imports / compose pattern** (lines 52–96):
```python
def compose_digest_body(*, intro: str, segments: list[str]) -> str:
    parts: list[str] = []
    trimmed = intro.strip()
    if trimmed:
        parts.append(trimmed)
    parts.extend(segments)
    return "\n".join(parts) + ("\n" if parts else "")

def compose_digest_segments(*, pool: list[ShortlistItem], blocks: Sequence[PreviewBlock] | None) -> tuple[list[ShortlistItem], list[str]]:
    """Shared by preview and send so StubMailer/SMTP bodies match «Превью письма»."""
    …
```

**Word-count alignment** — `ingestion-service/src/ingestion_service/domain/material_completion.py` lines 14–15:
```python
def estimate_reading_minutes(body_markdown: str) -> int:
    return max(1, math.ceil(len(body_markdown.split()) / 200))
```
Use the same `.split()` for `word_count`; `char_count = len(body_markdown or "")`; pass stored `reading_minutes` from item.

**New API surface (from RESEARCH):** `render_interstitial_html`, `render_material_email_block`, `render_email_html`, optional `material_counts`. Use stdlib `html.escape`. Preview + send both call `render_email_html` (D-07/D-12).

**Plain-body whitespace (D-14):** when fixing interstitial plain segments, stop collapsing to a single stripped line — preserve internal `\n\n` after outer strip (today `PreviewTextBlock` path does `block.text.strip()` then appends one segment; HTML path applies `\n\n`→`<p>`).

---

### `backend/src/backend/application/use_cases/get_admin_shortlist.py` (service, request-response)

**Analog:** same file — map `ShortlistItem` → `AdminShortlistItem`

**Core mapping** (lines 37–49):
```python
items = tuple(
    AdminShortlistItem(
        material_id=item.material_id,
        rank=item.rank,
        title=item.title,
        material_status=item.material_status,
        decision=item.decision,
        score=float(item.score) if item.score is not None else None,
        factor_labels=tuple(honest_factor_labels(item.score_factors)),
        dek=item.dek,
        # Phase 13: pass body_markdown, provenance_label, slug, reading_minutes,
        # char_count/word_count from material_counts(item.body_markdown)
    )
    for item in ranked
)
```

Keep empty-batch / digest_rest branches unchanged (Phase 12 shapes).

---

### `backend/src/backend/application/use_cases/preview_digest_email.py` (service, request-response)

**Analog:** same file — extend `DigestEmailPreview` + return path

**DTO** (lines 33–38):
```python
@dataclass(frozen=True)
class DigestEmailPreview:
    batch_id: int
    subject: str
    body: str
    items: tuple[DigestPreviewItem, ...]
    # Phase 13: html: str
```

**Return construction** (lines 131–138): after `body = _compose_body(...)`, also `html = render_email_html(...)` with `site_url` + ordered materials (title/dek/slug) + intro/text blocks. Keep composition via existing `compose_digest_segments` (D-09).

---

### `backend/src/backend/application/use_cases/send_digest.py` (service, request-response)

**Analog:** same file — mail call after compose

**Mail call** (lines 155–170):
```python
composed = compose_digest_body(intro=intro, segments=body_segments)
subject = f"Digest CDS — выпуск {publication.issue_number}"
body_text = (
    f"Новый выпуск Digest CDS №{publication.issue_number}.\n"
    f"Читать: {issue_url}\n\n"
    f"{composed}"
)
mailer.send_digest(
    batch_id=publication.batch_id,
    issue_url=issue_url,
    subject=subject,
    body_text=body_text,
    recipient_count=publication.recipient_count,
    # Phase 13: body_html=render_email_html(...)  # no issue URL in HTML (D-11)
)
```

Parity proof compares preview `html` to send `html` for the same intro/blocks (issue URL only in plain send wrapper).

---

### `backend/src/backend/application/ports/mailer.py` + `stub_mailer.py` (port/adapter, request-response)

**Analog:** Protocol + StubMailer additive kwargs

**Port** (`mailer.py` lines 8–18):
```python
class Mailer(Protocol):
    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
    ) -> dict[str, object]:
        ...
```

**Stub pattern** (`stub_mailer.py` lines 10–45): store `last_*` fields; log body; return `{delivery_status: "stubbed", …}`. Add optional `body_html: str | None = None` + `last_body_html` without breaking existing callers (A4).

---

### `backend/src/backend/composition/settings.py` (config, request-response)

**Analog:** same file — additive field + `from_env`

**Pattern** (lines 13–55):
```python
@dataclass(frozen=True)
class Settings:
    …
    mailer: str = "stub"
    # Phase 13: site_url: str = "http://127.0.0.1:5173"

@classmethod
def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
    env = environ if environ is not None else os.environ
    …
    return cls(
        …
        mailer=mailer,
        # site_url=env.get("SITE_URL") or env.get("PUBLIC_SITE_URL") or default
    )
```

Wire `site_url` into preview/send from composition root (not client-supplied).

---

### `backend/src/backend/interface/http/routes/admin.py` (route, request-response)

**Analog:** same file — Pydantic `extra="forbid"` + thin handler

**DTO posture** (lines 35–83):
```python
class AdminShortlistItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None = None
    factor_labels: list[str] = []
    dek: str | None = None
    # Phase 13 additive: body_markdown, provenance_label, slug,
    # reading_minutes, char_count, word_count

class DigestPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch_id: int
    subject: str
    body: str
    items: list[DigestPreviewItemResponse] = []
    # Phase 13: html: str
```

**Auth / error pattern** (preview handler lines 250–301):
```python
def post_shortlist_preview(
    request: Request,
    body: DigestPreviewRequest | None = None,
    _admin: CurrentUser = Depends(require_admin),
) -> DigestPreviewResponse:
    …
    except EmptySendPoolError as exc:
        raise HTTPException(status_code=400, detail="empty_send_pool") from exc
    except InvalidPreviewCompositionError as exc:
        raise HTTPException(status_code=400, detail="invalid_preview_composition") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="shortlist_unavailable") from exc
    return DigestPreviewResponse(batch_id=…, subject=…, body=…, items=…, html=…)
```

Keep handler thin: map DTO only; HTML built in use-case/helper.

---

### `supabase-integration/src/supabase_integration/shortlist_repository.py` (service/adapter, CRUD)

**Analog:** same file — widen join + `_item_from_row`

**Row map** (lines 37–56):
```python
def _item_from_row(row: dict[str, Any]) -> ShortlistItem:
    material = row.get("materials")
    if not isinstance(material, dict):
        material = {}
    …
    return ShortlistItem(
        …
        dek=(str(material["dek"]) if material.get("dek") is not None else None),
        # Phase 13: body_markdown, slug, provenance_label, reading_minutes
        # from material dict with same None-safe casting
    )
```

**Select** (lines 205–208) — target:
```python
.select(
    "batch_id,material_id,rank,score,score_factors,decision,"
    "decided_by,decided_at,"
    "materials(title,status,dek,body_markdown,slug,provenance_label,reading_minutes)"
)
```

Map SDK errors to `PersistenceError` at boundary (existing try/except).

---

### `backend/src/backend/tests_support/in_memory.py` (test, CRUD)

**Analog:** same file — `set_decision` rebuilds `ShortlistItem` with all fields (lines 214–226). When adding fields to `ShortlistItem`, copy them through here and in all HTTP/unit seeds (`_seeded_shortlist` in `test_http_admin.py`).

---

### `supabase-integration/migrations/010_phase13_scrub_test_header.sql` (migration, batch) — NEW

**Analog:** `supabase-integration/migrations/007_phase9_persist_draft.sql` — idempotent `UPDATE public.materials … WHERE …`

**Header + update pattern** (lines 1–31):
```sql
-- Phase 9 persist+enqueue: …
-- Timestamped / phase-named header; idempotent; shared VM apply once — never reset.

update public.materials
set
  source_url = coalesce(nullif(source_url, ''), '…'),
  …
where slug = 'phase5-admin-draft';
```

**Phase 13 scrub shape:** UPDATE text columns (`title`, `dek`, `body_markdown`, `provenance_label`) where `lower(col) LIKE '%test-header%'` (and sibling tokens per D-18), or replace tokens; include verify `SELECT` comments for runbook. Prefer defensive no-op when 0 rows.

Also mirror migration header style from `009_phase11_persist_sent_batch_already_saved.sql` (phase purpose + “Shared VM apply” note).

---

### `web/src/pages/AdminDigestPage.jsx` (component, request-response)

**Analog A (modal shell):** same file `AdminItemPreview` / `AdminEmailPreview` (lines 904–996)

**Current material modal** (lines 926–929) — replace with D-04/D-05 layout:
```jsx
<p className="mt-4 break-words font-medium text-ink">{item.title}</p>
<p className="mt-2 break-words text-sm text-ink-2">
  {item.dek || 'Краткое описание недоступно.'}
</p>
```

**Analog B (markdown stack):** `web/src/pages/MaterialPage.jsx` lines 1–9, 185–190:
```jsx
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
…
<Markdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeSlug, rehypeSanitize]}
>
  {material.body_markdown}
</Markdown>
```

Empty body (D-06): muted «Текст материала недоступен» — same honesty style as dek fallback / Phase 4 empty states.

**Email preview (D-08):** replace `data-testid="email-preview-body"` plain `<p>` (lines 976–982) with:
```jsx
<iframe
  data-testid="email-preview-frame"
  title="Превью письма HTML"
  sandbox=""
  srcDoc={emailModal.preview.html}
  className="mt-3 min-h-64 w-full rounded-xl border border-rule bg-white"
/>
```

**Connecting-text hint (D-15):** under interstitial textarea (~lines 706–714), add muted helper «Пустая строка = новый абзац» (intro textarea at 667–672 is also a candidate for the same hint if planner prefers both).

---

### `web/src/services/adminApi.js` (service, request-response)

**Analog:** same file

**Typedef + mock items** (lines 27–43): extend `AdminShortlistItem` with new fields; enrich `DEFAULT_ITEMS` (no ban tokens).

**Mock preview** (lines 400–406): add `html` string alongside `body` (mock may call a tiny shared HTML builder for Playwright, but live UI must prefer API `html` — D-07).

**Live preview** (lines 420–455): keep `POST …/admin/shortlist/preview` + JSON body `{ intro, blocks }`; return `response.json()` including `html`.

---

### `web/src/utils/forbiddenChrome.js` (utility, transform) — NEW

**Analog:** `web/src/utils/markdownToc.js` — small exported helpers, JSDoc, no React

**Structure** (lines 1–12 style):
```js
/**
 * Extract ATX headings from markdown for section TOC.
 */
export const HEADING_ID_PREFIX = 'user-content-'
```

**Phase 13:**
```js
export const FORBIDDEN_LOWER = ['test-header', 'test_header', 'testheader']
export function containsForbiddenChrome(text) {
  const lowered = String(text ?? '').toLowerCase()
  return FORBIDDEN_LOWER.some((token) => lowered.includes(token))
}
```
Keep list synced with Python `FORBIDDEN_LOWER` (unit assert identical tokens).

---

### `tests/unit/test_email_render.py` (test, transform) — NEW

**Analog:** `tests/unit/test_preview_digest.py` — pure use-case tests, in-memory repo optional

**Structure** (file header + focused cases lines 1–12, 126–161):
```python
"""preview_digest_email — approved∩ready preview DTO (ADMIN-04, D-86, G-05-1)."""
from backend.application.use_cases.preview_digest_email import (
    PreviewMaterialBlock,
    PreviewTextBlock,
    preview_digest_email,
)
```

For `test_email_render.py`: import `render_interstitial_html` / `render_email_html` / ban helper; matrix empty / whitespace / one para / two paras / `\n` / leading ws / escape; ban assert on fixture HTML; `test_preview_email_html_matches_send_html` may live here or in preview/send modules.

---

### `tests/unit/test_http_admin.py` (test, request-response)

**Analog:** same file — admin JWT + in-memory container

**Seed pattern** (lines 86–116) + assertion style (lines 167–184):
```python
response = client.get("/admin/shortlist", headers={"Authorization": f"Bearer {token}"})
assert response.status_code == 200
body = response.json()
assert first["rank"] == 1
# Phase 13 named proof:
# test_admin_shortlist_returns_full_items — assert body_markdown, provenance_label,
# slug, reading_minutes, char_count, word_count keys + values (required-key style, not blob eq)
```

Respect FIX-01 D-08: no full-body JSON equality.

---

### `tests/unit/test_preview_digest.py` + `tests/unit/test_send_digest.py` (test, request-response)

**Analog:** existing composition / body asserts

Preview: assert `preview.html` present and contains escaped title / interstitial `<p>`.
Send (`test_send_body_includes_intro_and_interstitial_text_blocks` region ~389+): extend with `mailer.last_body_html` parity vs preview for same intro/blocks.

---

### `tests/admin.spec.js` (test, request-response)

**Analog:** same file — dialog filter + testids

**Current email body assert** (lines 277–283):
```js
await expect(emailDialog.getByTestId("email-preview-body")).toContainText(introPhrase);
```

**Phase 13 update:** use frame locator, e.g. `emailDialog.frameLocator('[data-testid=email-preview-frame]')` and assert material title / intro text inside frame. Keep dialog heading filter pattern. Add material-modal body + ban-token absence + hint copy asserts.

---

### `docs/agents/local-platform-runbook.md` (config, batch)

**Analog:** `## 4e` block (lines 251–298)

**Structure to copy:**
1. Heading with phase + req IDs  
2. Checked-in SQL path  
3. What it does (bullet list)  
4. **Apply once on shared VM** steps (`supabase db push` / Studio / psql; never reset)  
5. **Verify after apply** SQL block  
6. Applied: date line  

New section: `## 4f. Phase 13 test-header scrub (ADUX-04)`.

---

### `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` (config)

**Analog:** same file — empty shapes stay; extend item schema docs

**Assert rules** (lines 48–56): keep required-key asserts; document additive item fields for non-empty items. Empty `items: []` shapes unchanged. Note ban-list + full DTO item schema per D-03/D-18.

---

### `.env.example` (config)

**Analog:** existing `APP_CONTAINER=memory` line style — add commented `SITE_URL=http://127.0.0.1:5173` (and optional `PUBLIC_SITE_URL` fallback note). No secrets.

## Shared Patterns

### Authentication (admin HTTP)
**Source:** `backend/src/backend/interface/http/routes/admin.py`  
**Apply to:** shortlist GET/preview/send (unchanged)  
```python
_admin: CurrentUser = Depends(require_admin)
```

### Error mapping (domain → HTTP)
**Source:** `admin.py` preview/send handlers  
**Apply to:** any new HTTP fields — map `EmptySendPoolError`→400, `InvalidPreviewCompositionError`→400, `PersistenceError`→503; never leak SDK traces.

### Pydantic `extra="forbid"`
**Source:** `AdminShortlistItemResponse` / `DigestPreviewResponse`  
**Apply to:** every additive field — declare on model + domain + in-memory + FE typedefs/mocks in one wave (Pitfall 1).

### Preview ≡ send composition
**Source:** `compose_digest_segments` shared import in `preview_digest_email.py` + `send_digest.py`  
**Apply to:** `render_email_html` — one function, both call sites; issue URL only in send plain wrapper (D-11).

### FE API boundary
**Source:** `web/src/services/adminApi.js`  
**Apply to:** all admin network I/O — UI imports services only; no Supabase in pages.

### Reader markdown stack
**Source:** `MaterialPage.jsx`  
**Apply to:** `AdminItemPreview` body only — same plugins; scrollable modal container already uses `max-h-[90vh] overflow-y-auto`.

### Honesty empty states
**Source:** dek fallback in `AdminItemPreview`; Phase 12 empty shortlist shapes  
**Apply to:** missing `body_markdown` → «Текст материала недоступен»; never invent body/HTML.

### Idempotent SQL + runbook
**Source:** runbook §4e + migration 007 UPDATE  
**Apply to:** `010_phase13_scrub_test_header.sql` + §4f.

### TDD
**Source:** workspace `tdd.mdc` / `AGENTS.md`  
**Apply to:** all production changes — named failing tests first (`test_admin_shortlist_returns_full_items`, interstitial matrix, `test_preview_email_html_matches_send_html`, Playwright iframe).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | All planned files have in-repo analogs |

*(Sandboxed iframe `srcDoc` is new to this SPA; closest structural analog is `AdminEmailPreview` modal shell + RESEARCH/MDN snippet — treat as role-match to existing modal, not a missing analog.)*

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application,interface/http,infrastructure,composition,tests_support}`, `supabase-integration/{src,migrations}`, `web/src/{pages,services,utils}`, `tests/{unit,admin.spec.js}`, `docs/agents`, `.planning/phases/12-*`, `ingestion-service/.../material_completion.py`, `.env.example`  
**Files scanned:** ~40 tracked paths (analogs verified via `git ls-files`)  
**Pattern extraction date:** 2026-10-02
)
