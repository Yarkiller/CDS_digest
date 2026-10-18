# Phase 3: Voting Cycle - Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 23
**Analogs found:** 22 / 23

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/.../domain/vote.py` | model | transform | `backend/.../domain/issue.py` + `voting_cycle.py` | exact |
| `backend/.../domain/errors.py` | model | request-response | `backend/.../domain/errors.py` (extend) | exact |
| `backend/.../ports/vote_repository.py` | service | CRUD | `backend/.../ports/profile_repository.py` | role-match |
| `backend/.../use_cases/get_ballot.py` | service | request-response | `backend/.../use_cases/get_current_issue.py` | exact |
| `backend/.../use_cases/cast_vote.py` | service | CRUD | `backend/.../use_cases/publish_material.py` + `update_display_name.py` | role-match |
| `backend/.../tests_support/in_memory.py` | utility | CRUD | `InMemoryVotingCycleReader` / `InMemoryProfileRepository` | exact |
| `backend/.../routes/voting.py` | route | request-response | `backend/.../routes/issues.py` + `me.py` | exact |
| `backend/.../composition/container.py` | config | — | same file (add `votes` port) | exact |
| `backend/.../composition/live.py` | config | — | same file (wire adapter) | exact |
| `backend/.../interface/http/app.py` | config | — | same file (`include_router`) | exact |
| `supabase-integration/.../vote_repository.py` | service | CRUD | `profile_repository.py` (upsert) + `voting_cycle_repository.py` (read) | exact |
| `supabase-integration/.../__init__.py` | config | — | same file (export) | exact |
| `migrations/003_phase3_voting_ballot.sql` | migration | file-I/O | `migrations/002_phase2_issue_seed.sql` | role-match |
| `web/src/services/votingApi.js` | service | request-response | `web/src/services/contentApi.js` + `meApi.js` | exact |
| `web/src/pages/VotingPage.jsx` | component | request-response | same + `IssuePage.jsx` (GET splash) + `ArchivePage.jsx` (empty) | exact |
| `web/src/components/TopicBallot.jsx` | component | transform | same file (evolve; drop `leading`) | exact |
| `web/src/utils/voting.js` | utility | transform | same file (copy + button labels) | exact |
| `web/src/utils/ruCount.js` | utility | transform | `IssuePage.jsx` / `ArchivePage.jsx` `materialCountLabel` | exact |
| `web/src/data/mock.js` | config | — | `votingTopics` / `votingCycle` block | exact |
| `tests/unit/test_cast_vote.py` | test | CRUD | `tests/unit/test_get_current_issue.py` | role-match |
| `tests/unit/test_get_ballot.py` | test | request-response | `tests/unit/test_get_current_issue.py` | exact |
| `tests/unit/test_http_voting.py` | test | request-response | `tests/unit/test_http_issues.py` + `test_http_me.py` | exact |
| `tests/web-app.spec.js` | test | request-response | same file (voting describe blocks) | exact |

## Pattern Assignments

### `backend/src/backend/domain/vote.py` (model, transform)

**Analog:** `backend/src/backend/domain/issue.py` + `voting_cycle.py`

**Imports / frozen dataclasses** (`issue.py` 1–27, `voting_cycle.py` 1–14):
```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssueItem:
    slug: str
    title: str
    # ...

@dataclass(frozen=True)
class VotingCycle:
    id: str
    status: str  # "open" | "closed"
    opens_at: datetime
    closes_at: datetime
```

**Copy for BallotSnapshot:** frozen dataclasses only — no FastAPI/Pydantic in domain. Put `BallotTopic`, `PersonalVote`, `BallotLeader`, `BallotSnapshot` here (or sibling module). Keep `VotingCycle` as-is; snapshot may wrap cycle fields + `progress_ratio` as a view DTO in use-case/HTTP, not mutate the domain cycle.

---

### `backend/src/backend/domain/errors.py` (model, request-response)

**Analog:** same file — extend `DomainError` tree

**Core pattern** (lines 1–19):
```python
class DomainError(Exception):
    """Base domain error."""


class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int | str) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id


class MaterialValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
```

**Add (RESEARCH):** `VotingCycleClosedError`, `VoteConflictError`, `InvalidVoteError` — same style; map to HTTP only in `routes/voting.py`.

---

### `backend/src/backend/application/ports/vote_repository.py` (service, CRUD)

**Analog:** `backend/src/backend/application/ports/profile_repository.py` + `voting_cycle_reader.py`

**Protocol pattern** (`profile_repository.py` 1–13, `voting_cycle_reader.py` 1–11):
```python
from __future__ import annotations

from typing import Protocol

from backend.domain.current_user import CurrentUser


class ProfileRepository(Protocol):
    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser: ...

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser: ...


class VotingCycleReader(Protocol):
    def list_cycles(self) -> list[VotingCycle]: ...
```

**Copy for VoteRepository:** `typing.Protocol`, no `Any`, methods like `get_vote(cycle_id, user_id)`, `list_topics_with_counts(cycle_id)`, `upsert_vote(...)` / `cas_update(...)`. Do **not** add write methods to `VotingCycleReader` (D-discretion / RESEARCH anti-pattern).

---

### `backend/src/backend/application/use_cases/get_ballot.py` (service, request-response)

**Analog:** `backend/src/backend/application/use_cases/get_current_issue.py`

**Imports + cycle selection + view DTO** (lines 1–38):
```python
from __future__ import annotations

from dataclasses import dataclass

from backend.application.ports.issue_repository import IssueRepository
from backend.application.ports.voting_cycle_reader import VotingCycleReader
from backend.domain.issue import Issue
from backend.domain.voting_cycle import VotingCycle


@dataclass(frozen=True)
class CurrentIssueView:
    issue: Issue | None
    voting_cycle: VotingCycle | None = None


def select_active_voting_cycle(cycles: list[VotingCycle]) -> VotingCycle | None:
    """RESEARCH A2: prefer open by closes_at DESC; else latest closed by opens_at."""
    open_cycles = [c for c in cycles if c.status == "open"]
    if open_cycles:
        return max(open_cycles, key=lambda c: c.closes_at)
    closed = [c for c in cycles if c.status == "closed"]
    if closed:
        return max(closed, key=lambda c: c.opens_at)
    return None


def get_current_issue(
    issues: IssueRepository,
    voting_cycles: VotingCycleReader | None = None,
) -> CurrentIssueView:
    issue = issues.get_latest_published()
    cycle = None
    if voting_cycles is not None:
        cycle = select_active_voting_cycle(voting_cycles.list_cycles())
    return CurrentIssueView(issue=issue, voting_cycle=cycle)
```

**Copy:** **Reuse** `select_active_voting_cycle` (import from this module — do not duplicate). `get_ballot(votes, voting_cycles, user_id)` returns snapshot with `leaders[]` computed here (D-40…43), never in React. Status switch = `cycle.status`, not wall-clock vs `closes_at` (RESEARCH Pattern 3).

---

### `backend/src/backend/application/use_cases/cast_vote.py` (service, CRUD)

**Analog:** `publish_material.py` (domain error + save) + `update_display_name.py` (user-scoped write)

**Core write + domain error** (`publish_material.py` 1–16):
```python
def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
```

**User-id from claims, not body** (`update_display_name.py` 9–17 + `me.py` patch):
```python
def update_display_name(
    profiles: ProfileRepository,
    user_id: str,
    email: str,
    display_name: str,
) -> CurrentUser:
    profiles.get_or_upsert(user_id, email)
    return profiles.set_display_name(user_id, display_name.strip())
```

**Copy for cast_vote:** (1) resolve active cycle via `select_active_voting_cycle`; (2) if `status != "open"` → `VotingCycleClosedError` (still attach/return snapshot for D-51); (3) validate topic ∈ cycle → `InvalidVoteError`; (4) CAS/`upsert` via `VoteRepository`; (5) on mismatch → `VoteConflictError`; (6) return full `BallotSnapshot` (D-52). Same-topic repeat → success snapshot (idempotent).

---

### `backend/src/backend/tests_support/in_memory.py` (utility, CRUD)

**Analog:** `InMemoryVotingCycleReader` + `InMemoryProfileRepository` in same file

**Read fake** (lines 130–140):
```python
class InMemoryVotingCycleReader:
    def __init__(self, cycles: list[VotingCycle] | None = None) -> None:
        self._cycles: list[VotingCycle] = list(cycles or [])

    def seed(self, cycles: list[VotingCycle]) -> None:
        self._cycles = list(cycles)

    def list_cycles(self) -> list[VotingCycle]:
        return list(self._cycles)
```

**Write fake keyed by id** (lines 52–81):
```python
class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CurrentUser] = {}

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser:
        existing = self._by_id.get(user_id)
        if existing is None:
            raise KeyError(f"profile not found: {user_id}")
        # ... replace and return
```

**Copy for InMemoryVoteRepository:** dict keyed by `(cycle_id, user_id)`; seed topics + tallies; implement CAS by comparing `updated_at`; raise same domain errors the use-case expects (or return None rows so use-case raises).

---

### `backend/src/backend/interface/http/routes/voting.py` (route, request-response)

**Analog:** `issues.py` (GET snapshot + Pydantic `extra="forbid"`) + `me.py` (POST/PATCH with `claims.sub`)

**Router + response models** (`issues.py` 1–54, 121–144):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/issues", tags=["issues"])


class CurrentIssueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: int | None = None
    # ...


@router.get("/current", response_model=CurrentIssueResponse, ...)
def read_current_issue(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentIssueResponse:
    del claims  # or use claims.sub for personal vote
    # PersistenceError → 503
```

**Authenticated mutation with principal** (`me.py` 81–98):
```python
@router.patch("/me", response_model=CurrentUserResponse, ...)
def patch_me(
    body: UpdateMeRequest,
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUserResponse:
    user = update_display_name(
        container.profiles,
        claims.sub,
        claims.email,
        body.display_name,
    )
    return _to_response(user)
```

**Copy for voting routes:**
- `APIRouter(prefix="/voting", tags=["voting"])`
- `GET /current` → ballot snapshot; use `claims.sub` for personal vote
- `POST /votes` body `{ topic_id, expected_updated_at }` with `ConfigDict(extra="forbid")`
- Container guard like `_require_issues` → `votes_not_configured` 503
- Domain → HTTP: closed/conflict → **409** with `detail={code, message, ballot}` (see Shared Patterns — no in-repo 409 yet)
- Wire in `app.py` via `app.include_router(voting.router)` next to `issues`/`me`

---

### `backend/src/backend/composition/container.py` + `live.py` + `app.py` (config)

**Analog:** same files

**Container field + in-memory build** (`container.py` 30–82):
```python
@dataclass
class AppContainer:
    materials: MaterialRepository
    # ...
    voting_cycles: VotingCycleReader
    # ADD: votes: VoteRepository


def build_in_memory_container(...) -> AppContainer:
    return AppContainer(
        # ...
        voting_cycles=InMemoryVotingCycleReader(voting_cycles),
        # ADD: votes=InMemoryVoteRepository(),
    )
```

**Live service_role wiring** (`live.py` 19–46):
```python
admin_client = create_service_role_client(...)
return AppContainer(
    # ...
    voting_cycles=SupabaseVotingCycleReader(admin_client),
    # ADD: votes=SupabaseVoteRepository(admin_client),
)
```

**Router registration** (`app.py` 48–53):
```python
app.include_router(health.router)
app.include_router(me.router)
app.include_router(issues.router)
app.include_router(issues.archive_router)
app.include_router(materials.router)
# ADD: app.include_router(voting.router)
```

---

### `supabase-integration/.../vote_repository.py` (service, CRUD)

**Analog:** `profile_repository.py` (upsert + PersistenceError boundary) + `voting_cycle_repository.py` (list/select)

**Client protocol + error mapping** (`voting_cycle_repository.py` 12–51):
```python
class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


class SupabaseVotingCycleReader:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_cycles(self) -> list[VotingCycle]:
        try:
            result = self._client.table("voting_cycles").select(...).execute()
        except PersistenceError:
            raise
        except Exception as exc:
            raise PersistenceError(f"voting_cycles list failed: {exc}") from exc
```

**Upsert pattern** (`profile_repository.py` 46–65):
```python
upserted = (
    self._client.table("profiles")
    .upsert({"id": user_id, "email": email, "role": _DEFAULT_APP_ROLE})
    .execute()
)
```

**Copy:** inject client only via composition; map SDK exceptions → `PersistenceError`; for CAS use `.update(...).eq("updated_at", expected)` and treat empty `data` as conflict (RESEARCH — upsert has no WHERE). Export from `__init__.py` like `SupabaseVotingCycleReader`.

---

### `supabase-integration/migrations/003_phase3_voting_ballot.sql` (migration, file-I/O)

**Analog:** `002_phase2_issue_seed.sql` voting insert (lines 166–178)

```sql
-- ─── Voting cycle (ISSUE-02 stub source for 02-05) ───────────
insert into voting_cycles (opens_at, closes_at, status)
select
  timestamptz '2026-04-03 00:00:00+00',
  timestamptz '2026-04-16 23:59:59+00',
  'open'::voting_cycle_status
where not exists (
  select 1
  from voting_cycles vc
  where vc.opens_at = timestamptz '2026-04-03 00:00:00+00'
    and vc.closes_at = timestamptz '2026-04-16 23:59:59+00'
);
```

**Copy:** idempotent `WHERE NOT EXISTS` seeds for ≥2 topics (titles matching `mock.js`); one topic with zero `topic_materials`; `BEFORE INSERT OR UPDATE` trigger on `votes` for open cycle + topic∈cycle; optional tally index. Extend `test_schema_migration_contract.py` only if asserting new objects (optional).

---

### `web/src/services/votingApi.js` (service, request-response)

**Analog:** `contentApi.js` (GET + `isMocksEnabled` + fail harness) + `meApi.js` (POST/PATCH Bearer)

**Mock gate + live fetch** (`contentApi.js` 5–6, 108–110, 157–199):
```javascript
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

export async function fetchCurrentIssue(accessToken) {
  if (consumeFailNext()) throwNetwork()
  if (isMocksEnabled()) { /* mock DTO */ }
  const headers = await authHeaders(accessToken)
  response = await fetch(`${apiBase()}/issues/current`, { headers })
  // 401 → UNAUTHORIZED; !ok → NETWORK
}
```

**Mutation POST** (`meApi.js` 117–145):
```javascript
response = await fetch(`${apiBase()}/me`, {
  method: 'PATCH',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ display_name: trimmed }),
})
```

**Keep from current `votingApi.js`:** `VoteSubmitError`, `armFailNextVoteSubmit`, `?simulateError=1` fail-once.

**Evolve:** add `fetchBallot()`; `submitVote(topicId, expectedUpdatedAt)` returns full ballot snapshot; on 409 parse `detail.ballot` + `detail.code` (`CYCLE_CLOSED` / `VOTE_CONFLICT`); use `isMocksEnabled()` not raw `VITE_USE_MOCKS` (D-56 / RESEARCH pitfall 4).

---

### `web/src/pages/VotingPage.jsx` (component, request-response)

**Analog:** same file (ballot UX) + `IssuePage.jsx` (GET → ServiceUnavailable) + `ArchivePage.jsx` (empty + CTA) + `PlatformProofBanner.jsx` (timed fade toast)

**Existing ErrorPanel + toast + ActionButton** (`VotingPage.jsx` 38–138) — keep mutation path; do **not** swap POST failures for ServiceUnavailable (D-53).

**GET splash** (`IssuePage.jsx` 66–112):
```javascript
useEffect(() => {
  fetchCurrentIssue()
    .then((dto) => { setIssue(dto); setStatus('ready') })
    .catch(() => { setStatus('error') })
}, [loadKey])

if (status === 'error') {
  return (
    <section>
      <ServiceUnavailable onRetry={reload} />
    </section>
  )
}
```

**Empty + CTA** (`ArchivePage.jsx` 63–72):
```jsx
{status === 'ready' && issues.length === 0 ? (
  <div data-testid="archive-empty">
    <h2>...</h2>
    <Link to="/">К текущему выпуску →</Link>
  </div>
) : null}
```

**Timed fade toast** (`PlatformProofBanner.jsx` 6–7, 31–37):
```javascript
const DISMISS_MS = 5000
const FADE_MS = 500
dismissTimer = window.setTimeout(() => {
  setPhase('fading')
  fadeTimer = window.setTimeout(() => setPhase('idle'), FADE_MS)
}, DISMISS_MS)
```

**Copy for VotingPage evolution:**
- Load ballot on mount from `votingApi.fetchBallot`
- Leader strip above ballot from DTO `leaders` (not row badge)
- Closed: banner «Цикл голосования закрыт»; radios disabled; hide/disable confirm (D-48)
- Empty topics / no cycle: D-49 / D-50 copy + «К выпуску»
- On 409 closed: adopt `detail.ballot`, flip read-only (D-51)
- On 409 conflict: banner + adopt server vote (D-54)
- Button: disable when `selectedId === personalVote.topic_id` (D-47); labels via `voting.js` (D-44)
- Toast «Голос сохранён» / «Голос изменён» with fade (D-45)

---

### `web/src/components/TopicBallot.jsx` (component, transform)

**Analog:** same file

**Current row meta** (lines 26–30) — **change**:
```jsx
<span className="mt-1 block text-xs text-ink-2">
  {topic.materialsCount} материалов
  {topic.leading ? ' · Лидирует' : ''} · {topic.votes} голосов
</span>
```

**Copy:** keep `role="radiogroup"` / `role="radio"` / `aria-checked`. Remove `topic.leading`. Show audit `description` (hide empty dek — VOTE-04 / US-13.2). Use `ruCount` for «N материалов» / «N голосов». Optional `disabled` prop when cycle closed. Do not compute leaders here.

---

### `web/src/utils/voting.js` (utility, transform)

**Analog:** same file

```javascript
export function voteStatusText({ confirmedId, selectedId, topics }) {
  if (confirmedId) {
    const topic = topics.find((item) => item.id === confirmedId)
    return `Ваш голос: ${topic?.title ?? confirmedId}`
  }
  if (selectedId) {
    const topic = topics.find((item) => item.id === selectedId)
    return `Выбор: «${topic?.title ?? selectedId}» (нажмите «Подтвердить голос»)`
  }
  return 'Ваш голос: не отдан'  // → change to honest «голос не отдан» (VOTE-02)
}

export function voteButtonLabel(state) {
  if (state === 'loading') return 'Сохраняем…'
  if (state === 'success') return 'Голос принят'  // → «Изменить голос» when confirmed (D-44)
  if (state === 'error') return 'Повторить'
  return 'Подтвердить голос'
}
```

**Copy:** pure helpers only — no leader math. Add helpers for leader-strip copy (singular/plural/tie) if not inlined in page.

---

### `web/src/utils/ruCount.js` (utility, transform)

**Analog:** `IssuePage.jsx` / `ArchivePage.jsx` lines 14–22 (duplicated today)

```javascript
function materialCountLabel(count) {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return `${count} материал`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} материала`
  }
  return `${count} материалов`
}
```

**Copy:** extract shared module; add `voteCountLabel` (`голос` / `голоса` / `голосов`); update IssuePage/ArchivePage imports in a follow-up task if planner wants one PR for DRY.

---

### `web/src/data/mock.js` (config)

**Analog:** `votingTopics` / `votingCycle` (lines 191–220)

```javascript
export const votingTopics = [
  {
    id: 'rag-corp',
    title: 'RAG в корпоративной среде',
    materialsCount: 5,
    votes: 31,
    leading: true,  // REMOVE — leaders come from ballot DTO / mock snapshot
  },
  // ...
]
```

**Copy:** add `description` audit strings; ensure one topic with `materialsCount: 0`; mock ballot snapshot builder in `votingApi` can derive `leaders` from tallies for Playwright without row badges.

---

### `tests/unit/test_cast_vote.py` + `test_get_ballot.py` (test)

**Analog:** `tests/unit/test_get_current_issue.py`

**Structure** (lines 1–50):
```python
"""get_current_issue use-case — D-24 ...; D-33 voting_cycle stub (A2)."""

from backend.application.use_cases.get_current_issue import get_current_issue
from backend.domain.voting_cycle import VotingCycle
from backend.tests_support.in_memory import InMemoryVotingCycleReader

def _cycle(*, cycle_id: str, status: str, opens_at, closes_at) -> VotingCycle:
    return VotingCycle(id=cycle_id, status=status, opens_at=opens_at, closes_at=closes_at)
```

**Copy:** pure use-case tests with in-memory fakes — no FastAPI. Cover: one vote, A→B, closed reject, bad topic, CAS conflict, leaders/ties/hide-when-zero, empty topics, no cycle.

---

### `tests/unit/test_http_voting.py` (test, request-response)

**Analog:** `test_http_issues.py` + `test_http_me.py` JWT harness

**JWT mint + TestClient** (`test_http_issues.py` 26–96, 99+):
```python
def _mint(private_key, *, email: str, role: str = "authenticated") -> str:
    return jwt.encode({... "sub": "user-uuid-1", "email": email ...}, ...)

def _client(signing_jwk, container=None) -> TestClient:
    app = create_app(settings, container=container or build_in_memory_container(),
                     signing_key_resolver=lambda _token: signing_jwk)
    return TestClient(app)

def test_issues_current_without_authorization_returns_401() -> None:
    ...
    assert response.status_code == 401
```

**Copy:** 401 without Bearer; GET 200 snapshot; POST 200 returns ballot; POST 409 `CYCLE_CLOSED` includes `detail["ballot"]`; extra body fields → 422; seed `container.votes` + `voting_cycles` like issues tests seed `InMemoryIssueRepository`.

---

### `tests/web-app.spec.js` (test, request-response)

**Analog:** same file — voting tests ~139–175, 285–312

```javascript
test("lets a reader pick a voting topic and confirm", async ({ page }) => {
  await page.goto("/voting");
  const confirm = page.getByTestId("confirm-vote");
  await expect(confirm).toBeDisabled();
  await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
  await confirm.click();
  await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);
});

// OLD — rewrite first (TDD / RESEARCH pitfall 3):
await expect(confirm).toHaveText(/голос принят/i);
```

**Copy / rewrite (Wave 0):**
```javascript
await expect(page.getByRole('radio', { checked: true })).toHaveCount(0)
await expect(page.getByRole('status')).toContainText(/голос не отдан/i)
await expect(page.getByText('Лидирует')).toHaveCount(0)
// after confirm: button «Изменить голос»; empty submit «Выберите тему»
```

Keep fail-once `?simulateError=1` path; add GET fail → ServiceUnavailable if harnessed.

## Shared Patterns

### Authentication (JWT gate)
**Source:** `backend/src/backend/interface/http/deps.py` lines 19–48  
**Apply to:** All `/voting/*` handlers
```python
claims: AccessTokenClaims = Depends(get_principal)
# user_id = claims.sub — never from request body
```

### PersistenceError → 503
**Source:** `issues.py` 137–143  
**Apply to:** GET ballot / adapter failures on read path
```python
except PersistenceError as exc:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="issues_unavailable",  # → voting_unavailable
    ) from exc
```

### Pydantic `extra="forbid"`
**Source:** `issues.py` / `me.py` response + request models  
**Apply to:** Ballot response DTOs + `CastVoteRequest`

### Mock/live client gate
**Source:** `contentApi.js` `isMocksEnabled()` from `authEnv.js`  
**Apply to:** `votingApi.js` GET + POST (D-56)

### GET splash vs mutation ErrorPanel
**Source:** `IssuePage.jsx` ServiceUnavailable; `VotingPage.jsx` ErrorPanel  
**Apply to:** Initial ballot load failure (D-55) vs submit network/5xx (D-53)

### Empty state + «К выпуску»
**Source:** `ArchivePage.jsx` empty block with `Link to="/"`  
**Apply to:** D-49 / D-50 voting empties

### Timed toast fade
**Source:** `PlatformProofBanner.jsx` `DISMISS_MS=5000` + opacity fade  
**Apply to:** Vote saved/changed toast (D-45)

### Active cycle selection
**Source:** `get_current_issue.select_active_voting_cycle`  
**Apply to:** `get_ballot` / `cast_vote` — prefer `status=="open"`, ignore wall-clock alone

### Composition root only for Supabase clients
**Source:** `composition/live.py`  
**Apply to:** `SupabaseVoteRepository(admin_client)` — never in use-cases or Vite

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| HTTP 409 + `detail` dict with nested ballot | route | request-response | No in-repo `HTTP_409_CONFLICT` yet — use RESEARCH FastAPI pattern (`HTTPException(status_code=409, detail={code, message, ballot})`) |

Planner should treat RESEARCH.md Code Examples as the authority for 409 payload shape.

## Metadata

**Analog search scope:** `backend/src/backend/`, `supabase-integration/`, `web/src/`, `tests/unit/`, `tests/web-app.spec.js`, `supabase-integration/migrations/`  
**Files scanned:** ~90 (backend 52 + supabase adapters/migrations + web services/pages + unit/e2e tests)  
**Strong analogs used:** 8 primary (`get_current_issue`, `issues` routes, `me` routes, `profile_repository` upsert, `contentApi`/`meApi`, `VotingPage`/`TopicBallot`, `IssuePage`/`ArchivePage`, JWT test harness)  
**Pattern extraction date:** 2026-09-20
