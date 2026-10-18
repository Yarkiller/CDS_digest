# Phase 12: Admin shortlist empty-batch contract - Pattern Map

**Mapped:** 2026-10-02
**Files analyzed:** 11
**Analogs found:** 10 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/unit/test_http_admin.py` | test | request-response | `tests/unit/test_http_admin.py` (no-batch + digest_rest cases) | exact |
| `web/src/services/adminApi.js` | service | request-response | `web/src/services/adminApi.js` (`emptyDto` / `restDto` / sticky flags) | exact |
| `tests/admin.spec.js` | test | request-response | `tests/admin.spec.js` (empty + digest_rest Playwright) | exact |
| `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` | config | — | *(none — new contract lock)*; shape tables from `12-CONTEXT.md` D-04 / RESEARCH Pattern 2 | none |
| `.planning/REQUIREMENTS.md` | config | — | `.planning/REQUIREMENTS.md` FIX-01 row | exact |
| `.planning/ROADMAP.md` | config | — | `.planning/ROADMAP.md` Phase 12 success criteria | exact |
| `.planning/PROJECT.md` | config | — | `.planning/PROJECT.md` checklist item | exact |
| `backend/.../use_cases/get_admin_shortlist.py` | service | CRUD | self (touch **only** if empty-unsent HTTP test fails) | exact |
| `backend/.../interface/http/routes/admin.py` | route | request-response | self (`AdminShortlistResponse` + `read_admin_shortlist`) | exact |
| `backend/.../tests_support/in_memory.py` | utility | CRUD | self (`InMemoryShortlistRepository`) | exact |
| `web/src/pages/AdminDigestPage.jsx` | component | request-response | self (empty vs rest flags; touch **only** if E2E forces) | exact |

Optional (not required for FIX-01 per D-07 / RESEARCH open Q1): `tests/unit/test_get_admin_shortlist.py` — role-match twin of HTTP empty-unsent seed.

## Pattern Assignments

### `tests/unit/test_http_admin.py` (test, request-response)

**Analog:** same file — `test_admin_shortlist_empty_batch_returns_200_empty_items` (rename target) + `test_admin_shortlist_after_send_returns_digest_rest` (required-key style to copy)

**Imports / harness pattern** (lines 1–21, 59–74):
```python
from backend.composition.container import AppContainer, build_in_memory_container
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import InMemoryShortlistRepository
from fastapi.testclient import TestClient
# _mint / _public_jwk / _client / _seed_profile — reuse; do not reimplement
```

**Core no-batch seed** (lines 187–205) — keep semantics; rename to `test_admin_shortlist_no_batches_returns_null_batch_id`:
```python
container = build_in_memory_container()
container.shortlist = InMemoryShortlistRepository(batch=None)
# … mint admin JWT …
response = client.get("/admin/shortlist", headers={"Authorization": f"Bearer {token}"})
assert response.status_code == 200
```

**Anti-pattern to replace** (lines 208–215) — brittle full-dict equality (D-08 forbids):
```python
assert response.json() == {
    "batch_id": None,
    "items": [],
    "digest_rest": False,
    "days_until_next_batch": None,
    "week_label": None,
    "sent_at": None,
}
```

**Required-key assert style to copy** from digest_rest test (lines 255–260):
```python
body = response.json()
assert body["batch_id"] is None
assert body["items"] == []
assert body["digest_rest"] is True
assert body["days_until_next_batch"] == 7
```

**Empty-unsent seed template** — mirror digest_rest ShortlistBatch construction (lines 223–239) but `sent_at=None`, `items=()`:
```python
container.shortlist = InMemoryShortlistRepository(
    batch=ShortlistBatch(
        id=7,
        week_start=date(2026, 10, 6),
        sent_at=None,
        items=(),
    )
)
# Assert D-04 #2: batch_id == 7, week_label == "2026-10-06", items == [],
# sent_at is None, digest_rest is False, days_until_next_batch is None
# Optional: for key in REQUIRED: assert key in body
```

**Auth pattern:** reuse `_seed_profile(..., role="admin")` + `_mint` Bearer — same as lines 193–200 / 241–249. Do not weaken `require_admin`.

---

### `web/src/services/adminApi.js` (service, request-response)

**Analog:** same file — `emptyDto` / `restDto` / `resetAdminHarness` / `fetchShortlist` sticky branches

**DTO factory pattern** (lines 126–146) — add sibling `emptyUnsentDto`:
```javascript
function restDto() {
  return {
    batch_id: null,
    sent_at: mockBatch.sent_at,
    week_label: null,
    items: [],
    digest_rest: true,
    days_until_next_batch: DIGEST_WEEKLY_CADENCE_DAYS,
  }
}

function emptyDto() {
  return {
    batch_id: null,
    sent_at: null,
    week_label: null,
    items: [],
    digest_rest: false,
    days_until_next_batch: null,
  }
}
```

**New DTO (D-04 #2 / D-12 / D-13 — ISO week_label):**
```javascript
function emptyUnsentDto() {
  return {
    batch_id: 7,
    sent_at: null,
    week_label: '2026-10-06',
    items: [],
    digest_rest: false,
    days_until_next_batch: null,
  }
}
```

**Sticky flag helper** (lines 108–110) — reuse as-is:
```javascript
function stickyFlag(name) {
  return typeof window !== 'undefined' && Boolean(window[name])
}
```

**Harness reset** (lines 212–225) — clear the new flag:
```javascript
export function resetAdminHarness() {
  // … existing clears …
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_EMPTY__ = false
    window.__DIGEST_ADMIN_DIGEST_REST__ = false
    // ADD: window.__DIGEST_ADMIN_EMPTY_UNSENT__ = false
    window.__DIGEST_ADMIN_FAIL_SHORTLIST__ = false
    // …
  }
}
```

**Mock branch order** (lines 267–276) — insert EMPTY_UNSENT after DIGEST_REST, before EMPTY (RESEARCH flag precedence):
```javascript
if (stickyFlag('__DIGEST_ADMIN_DIGEST_REST__')) {
  return restDto()
}
// ADD: if (stickyFlag('__DIGEST_ADMIN_EMPTY_UNSENT__')) return emptyUnsentDto()
if (stickyFlag('__DIGEST_ADMIN_EMPTY__')) {
  return emptyDto()
}
```

---

### `tests/admin.spec.js` (test, request-response)

**Analog:** same file — `gotoAsRole` + empty shortlist test + digest_rest cold-load

**gotoAsRole harness** (lines 9–34) — already re-applies `extraInit` after `resetAdminHarness`; new flag rides this path:
```javascript
async function gotoAsRole(page, role, path = "/", extraInit) {
  await page.addInitScript(/* set role + extra */);
  await page.goto(path);
  if (path.startsWith("/admin")) {
    await page.waitForFunction(() => Boolean(window.__DIGEST_ADMIN_HARNESS__));
    await page.evaluate((extra) => {
      window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness();
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    }, extraInit ?? null);
    await page.reload();
  }
}
```

**Empty UI asserts to mirror** (lines 111–126) — same asserts for empty-unsent:
```javascript
test("empty shortlist shows Кандидатов пока нет without пайплайн", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/digest", {
    __DIGEST_ADMIN_EMPTY__: true,
  });
  await expect(
    page.getByRole("heading", { name: "Кандидатов пока нет", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /обновить список/i })).toBeVisible();
  await expect(page.getByText(/пайплайн/i)).toHaveCount(0);
  await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(0);
  await expect(page.getByText(/дайджест успешно выпущен/i)).toHaveCount(0);
  await expect(page.getByTestId("admin-digest-rest")).toHaveCount(0);
});
```

**New case:** swap flag to `__DIGEST_ADMIN_EMPTY_UNSENT__: true`; keep the same empty UI asserts (D-12). Do **not** assert `Неделя {week_label}` unless a failing test forces it (D-13 — `weekDek` gated by `showTriage`).

**Contrast with digest_rest** (lines 464–476) — empty-unsent must **not** match this path:
```javascript
await gotoAsRole(page, "admin", "/admin/digest", {
  __DIGEST_ADMIN_DIGEST_REST__: true,
});
await expect(page.getByText(/дайджест успешно выпущен/i)).toBeVisible();
await expect(page.getByText("Кандидатов пока нет", { exact: true })).toHaveCount(0);
```

---

### `12-FIX-01-LOCK.md` (config / docs)

**Analog:** none in-repo for a phase contract-lock file. Closest planning prose: `12-CONTEXT.md` D-04/D-08 tables + `12-RESEARCH.md` Pattern 2 required-key asserts.

**Structure to author (planner/executor):**
- Table: No-batches shape (D-04 #1)
- Table: Empty-unsent shape (D-04 #2)
- Assert rules: required keys + critical values; forbid full-dict `==`
- Explicit: keep `AdminShortlistResponse` `extra="forbid"` (D-09)
- Proof test names (D-05)

Do not invent a new markdown genre beyond that phase artifact.

---

### `.planning/REQUIREMENTS.md` / `.planning/ROADMAP.md` / `.planning/PROJECT.md` (config)

**Analog:** self — update FIX-01 / Phase 12 proof strings only.

**Current FIX-01 row** (`REQUIREMENTS.md` line 34):
```markdown
- [ ] **FIX-01**: `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` passes (schema extras / `sent_at` / `week_label` response contract aligned)
```

**Replace per D-05** with both new names + taxonomy wording (RESEARCH open Q2 recommendation):
```markdown
- [ ] **FIX-01**: no-batch + empty-unsent HTTP contracts (D-04) green under required-key asserts —
  `test_admin_shortlist_no_batches_returns_null_batch_id` and
  `test_admin_shortlist_empty_unsent_batch_returns_batch_id`
```

**ROADMAP Phase 12 success #1** (lines 59–62): cite both proof names; keep HTTP 200 / empty `items` / schema alignment criteria.

---

### `backend/.../get_admin_shortlist.py` (service, CRUD) — touch only if TDD fails

**Analog:** self — already implements D-04 shapes.

**No-batch + digest_rest + unsent assembly** (lines 15–58):
```python
def get_admin_shortlist(shortlist: ShortlistRepository) -> AdminShortlist:
    batch = shortlist.get_current_batch()
    if batch is None:
        latest = shortlist.get_latest_batch()
        if latest is not None and latest.sent_at is not None:
            return AdminShortlist(
                batch_id=None, items=(), digest_rest=True,
                days_until_next_batch=DIGEST_WEEKLY_CADENCE_DAYS,
                week_label=latest.week_start.isoformat(), sent_at=latest.sent_at,
            )
        return AdminShortlist(
            batch_id=None, items=(), digest_rest=False,
            days_until_next_batch=None, week_label=None, sent_at=None,
        )
    # empty items=() still takes this branch → D-04 #2
    return AdminShortlist(
        batch_id=batch.id, items=items, digest_rest=False,
        days_until_next_batch=None,
        week_label=batch.week_start.isoformat(), sent_at=batch.sent_at,
    )
```

---

### `backend/.../interface/http/routes/admin.py` (route, request-response) — keep as-is unless TDD fails

**Analog:** self

**Response model** (lines 48–56) — do not drop `extra="forbid"` (D-09):
```python
class AdminShortlistResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = None
    items: list[AdminShortlistItemResponse] = []
    digest_rest: bool = False
    days_until_next_batch: int | None = None
    week_label: str | None = None
    sent_at: datetime | None = None
```

**Thin route + auth** (lines 183–205):
```python
@router.get("/shortlist", response_model=AdminShortlistResponse, ...)
def read_admin_shortlist(
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> AdminShortlistResponse:
    shortlist = _require_shortlist(request)
    try:
        dto = get_admin_shortlist(shortlist)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return _to_response(dto)
```

---

### `backend/.../tests_support/in_memory.py` (utility, CRUD)

**Analog:** self — empty-unsent seed relies on current-batch semantics (lines 178–193):
```python
class InMemoryShortlistRepository:
    def get_current_batch(self) -> ShortlistBatch | None:
        # sent_at IS NULL contract — sent batch is not "current"
        if self._batch is None or self._batch.sent_at is not None:
            return None
        return self._batch

    def get_latest_batch(self) -> ShortlistBatch | None:
        return self._batch
```

**Pitfall:** empty-unsent = `sent_at=None, items=()`. Sent batch → `get_current_batch()` None → digest_rest path.

---

### `web/src/pages/AdminDigestPage.jsx` (component) — no chrome work unless E2E fails

**Analog:** self

**Empty vs rest flags** (lines 441–452, 518–524):
```javascript
const { restMode, isEmpty, showTriage, restDays, showFooter } = digestViewFlags({
  batchSent, digestRest, itemCount: items.length, daysUntilNextBatch,
})
// weekDek only when showTriage (itemCount > 0) — empty-unsent looks like no-batch UI today
<AdminDigestHeading weekDek={showTriage ? weekDek : null} />
{restMode ? <AdminDigestRest restDays={restDays} /> : null}
{isEmpty ? <AdminShortlistEmpty onReload={reloadShortlist} /> : null}
```

**Empty copy D-80** (lines 590–606) — do not redesign:
```javascript
function AdminShortlistEmpty({ onReload }) {
  return (
    <div data-testid="admin-shortlist-empty" …>
      <h2>Кандидатов пока нет</h2>
      <button …>Обновить список</button>
    </div>
  )
}
```

## Shared Patterns

### Admin JWT + in-memory HTTP client
**Source:** `tests/unit/test_http_admin.py` lines 27–74, 77–83  
**Apply to:** Both FIX-01 HTTP units  
```python
container = build_in_memory_container()
_seed_profile(container, user_id="admin-uuid-1", email="admin@sberbank.ru", role="admin")
client = _client(jwk, container)
token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
response = client.get("/admin/shortlist", headers={"Authorization": f"Bearer {token}"})
```

### Required-key (soft) asserts — D-08
**Source:** digest_rest body asserts in `test_http_admin.py` 255–260 + RESEARCH Pattern 2  
**Apply to:** renamed no-batch + new empty-unsent HTTP tests  
```python
assert response.status_code == 200
body = response.json()
for key in ("batch_id", "items", "week_label", "sent_at", "digest_rest", "days_until_next_batch"):
    assert key in body
assert body["items"] == []
assert body["sent_at"] is None
assert body["digest_rest"] is False
# then shape-specific batch_id / week_label
```

### Sticky mock flags + harness reset
**Source:** `adminApi.js` 108–110, 212–225, 258–276; `admin.spec.js` 9–34  
**Apply to:** `__DIGEST_ADMIN_EMPTY_UNSENT__`  
- Clear in `resetAdminHarness`
- Set via `gotoAsRole(..., { __DIGEST_ADMIN_EMPTY_UNSENT__: true })`
- Precedence: DIGEST_REST → EMPTY_UNSENT → EMPTY

### Thin HTTP + `extra="forbid"`
**Source:** `admin.py` 48–56, 160–205  
**Apply to:** any production touch — keep route thin; map PersistenceError → 503; never drop forbid

### Empty taxonomy (three shapes)
**Source:** `get_admin_shortlist.py` 15–58  
**Apply to:** tests + mocks + lock doc  
| Shape | `batch_id` | `week_label` | `digest_rest` | Seed |
|-------|------------|--------------|---------------|------|
| No batches | `null` | `null` | `false` | `batch=None` |
| Empty unsent | int | ISO | `false` | unsent + `items=()` |
| Digest rest | `null` | latest ISO | `true` | sent latest |

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `12-FIX-01-LOCK.md` | config | — | No prior phase `*-LOCK.md` contract artifact in tracked tree; author from CONTEXT D-04/D-08 + RESEARCH Pattern 2 |

## Metadata

**Analog search scope:** `tests/unit/`, `tests/admin.spec.js`, `backend/src/backend/{application,interface,domain,tests_support}/`, `web/src/{services,pages,main.jsx}`, `.planning/{REQUIREMENTS,ROADMAP,PROJECT}.md`, phase 10 deferred-items  
**Files scanned:** ~15 tracked sources (all analogs verified via `git ls-files`)  
**Pattern extraction date:** 2026-10-02  
**Tracked-source gate:** all named analogs are git-tracked (no `.gsd` mirror paths)
