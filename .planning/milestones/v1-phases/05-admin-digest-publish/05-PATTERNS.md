# Phase 5: Admin Digest Publish - Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 36
**Analogs found:** 34 / 36

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/.../ports/shortlist_repository.py` | service | CRUD | `backend/.../ports/vote_repository.py` | exact |
| `backend/.../ports/mailer.py` | service | request-response | `backend/.../ports/ping_recorder.py` | role-match |
| `backend/.../ports/issue_repository.py` | service | CRUD | same file (+ `publish` / create) | exact |
| `backend/.../use_cases/get_admin_shortlist.py` | service | request-response | `backend/.../use_cases/get_ballot.py` | exact |
| `backend/.../use_cases/set_shortlist_decision.py` | service | CRUD | `backend/.../use_cases/cast_vote.py` | exact |
| `backend/.../use_cases/preview_digest_email.py` | service | transform | `get_ballot.py` (read + assemble DTO) | role-match |
| `backend/.../use_cases/send_digest.py` | service | CRUD | `cast_vote.py` + `publish_material.py` | exact |
| `backend/.../domain/shortlist.py` | model | transform | `backend/.../domain/vote.py` | exact |
| `backend/.../domain/errors.py` | model | request-response | same file (`VoteConflictError`, `VotingCycleClosedError`) | exact |
| `backend/.../domain/current_user.py` | model | — | same file (default `role` → `employee`) | exact |
| `backend/.../infrastructure/stub_mailer.py` | service | request-response | `backend/.../ports/query_embedder.py` (`StubQueryEmbedder`) | role-match |
| `backend/.../interface/http/deps.py` | middleware | request-response | same file (`get_principal`) + RESEARCH `require_admin` | exact |
| `backend/.../routes/admin.py` | route | request-response | `backend/.../routes/voting.py` | exact |
| `backend/.../interface/http/app.py` | config | — | same file (`include_router`) | exact |
| `backend/.../composition/settings.py` | config | — | same file (`APP_CONTAINER` / `notebook_root`) | exact |
| `backend/.../composition/container.py` | config | — | same file (add shortlist + mailer ports) | exact |
| `backend/.../composition/live.py` | config | — | same file (`create_service_role_client` wiring) | exact |
| `backend/.../tests_support/in_memory.py` | utility | CRUD | `InMemoryVoteRepository` / `InMemoryProfileRepository` | exact |
| `supabase-integration/.../shortlist_repository.py` | service | CRUD | `supabase-integration/.../vote_repository.py` | exact |
| `supabase-integration/.../issue_repository.py` | service | CRUD | same file (+ publish insert) | exact |
| `supabase-integration/migrations/005_phase5_admin_shortlist.sql` | migration | batch | `migrations/003_phase3_voting_ballot.sql` | exact |
| `web/src/services/adminApi.js` | service | request-response | `web/src/services/votingApi.js` | exact |
| `web/src/services/meApi.js` | service | request-response | same file (`role` mock → `employee`/`admin`) | exact |
| `web/src/pages/AdminDigestPage.jsx` | component | request-response | `web/src/pages/VotingPage.jsx` + `design-frontend/pages/admin-digest.html` | exact |
| `web/src/pages/ForbiddenPage.jsx` | component | request-response | `VotingPage.jsx` `EmptyVotingCta` + `ServiceUnavailable.jsx` | partial |
| `web/src/components/AppShell.jsx` | component | — | same file (role-gated «Админ» nav) | exact |
| `web/src/App.jsx` | config | — | same file (add `/admin/digest` + 403 route) | exact |
| `tests/unit/test_http_admin.py` | test | request-response | `tests/unit/test_http_voting.py` | exact |
| `tests/unit/test_http_me.py` | test | request-response | same file (assert `app_role`) | exact |
| `tests/unit/test_send_digest.py` | test | CRUD | `tests/unit/test_cast_vote.py` (if present) / use-case style of `cast_vote` tests | role-match |
| `tests/unit/test_set_shortlist_decision.py` | test | CRUD | same as cast_vote unit pattern | role-match |
| `tests/unit/test_preview_digest.py` | test | transform | `get_ballot` unit style | role-match |
| `tests/unit/test_stub_mailer.py` | test | request-response | StubQueryEmbedder honesty tests / ping recorder unit | role-match |
| `tests/unit/test_score_factors.py` | test | transform | pure-function unit (domain helper) | partial |
| `tests/admin.spec.js` | test | request-response | `tests/auth.spec.js` + `tests/web-app.spec.js` harness flags | exact |
| `docs/agents/local-platform-runbook.md` | config | — | same file (§4e stub/seed honesty) | exact |

## Pattern Assignments

### `backend/.../ports/shortlist_repository.py` (service, CRUD)

**Analog:** `backend/src/backend/application/ports/vote_repository.py`

**Imports + Protocol pattern** (lines 1-23):
```python
"""VoteRepository port — ballot topics, personal vote, upsert (not VotingCycleReader)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.vote import BallotTopic, PersonalVote


class VoteRepository(Protocol):
    def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]: ...

    def get_vote(self, cycle_id: str, user_id: str) -> PersonalVote | None: ...

    def upsert_vote(
        self,
        *,
        cycle_id: str,
        user_id: str,
        topic_id: str,
        expected_updated_at: datetime | None,
    ) -> PersonalVote: ...
```

**Copy for Phase 5:** `ShortlistRepository(Protocol)` with `get_current_batch()`, `set_decision(...)`, `claim_sent(...)` / publish helpers — keyword-only args, domain DTOs from `domain/shortlist.py`, no SDK types.

---

### `backend/.../ports/mailer.py` (service, request-response)

**Analog:** `backend/src/backend/application/ports/ping_recorder.py`

**Side-effect Protocol** (lines 1-14):
```python
"""PingRecorder port — persist platform proof mutations (D-10 / PLAT-04)."""

from __future__ import annotations

from typing import Protocol


class PingRecorder(Protocol):
    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str: ...
```

**Copy for Phase 5:** `Mailer(Protocol).send_digest(*, batch_id, issue_url, subject, body_text, recipient_count) -> dict` returning `{delivery_status, recipient_count, issue_url}` — stub always `'stubbed'`. Audit via existing `PingRecorder` / `activity_events` (`kind=digest_send` or payload `action=send`), not a new audit table.

---

### `backend/.../ports/issue_repository.py` (service, CRUD — EXTEND)

**Analog:** same file (read-only today)

**Current surface** (lines 10-21):
```python
class IssueRepository(Protocol):
    def get_latest_published(self) -> Issue | None: ...
    def get_by_number(self, number: int) -> Issue | None: ...
    def list_past_published(self) -> list[Issue]: ...
```

**Copy for Phase 5:** Add `publish(...)` / `create_published_issue(...)` returning `Issue` with attached items — keep read methods unchanged for Phase 2 readers. Domain model remains `backend/domain/issue.py` frozen dataclasses.

---

### `backend/.../use_cases/get_admin_shortlist.py` (service, request-response)

**Analog:** `backend/src/backend/application/use_cases/get_ballot.py`

**Core read pattern** (lines 29-47):
```python
def get_ballot(
    votes: VoteRepository,
    voting_cycles: VotingCycleReader,
    user_id: str,
    *,
    now: datetime | None = None,
) -> BallotSnapshot:
    cycle = select_active_voting_cycle(voting_cycles.list_cycles())
    if cycle is None:
        return BallotSnapshot(cycle=None, topics=(), personal_vote=None, leaders=())

    clock = now or datetime.now(timezone.utc)
    topics = votes.list_topics_with_counts(cycle.id)
    personal = votes.get_vote(cycle.id, user_id)
    return BallotSnapshot(
        cycle=BallotCycleView.from_cycle(cycle, now=clock),
        topics=tuple(topics),
        personal_vote=personal,
        leaders=_compute_leaders(topics),
    )
```

**Copy for Phase 5:** Pure function over `ShortlistRepository`; empty batch → empty DTO (not an exception); score factor honesty (`≥2` labels or empty) computed in use-case/domain helper, not UI.

---

### `backend/.../use_cases/set_shortlist_decision.py` + `send_digest.py` (service, CRUD)

**Analog:** `backend/src/backend/application/use_cases/cast_vote.py`

**Imports + domain errors + port call** (lines 1-60):
```python
from backend.application.ports.vote_repository import VoteRepository
from backend.domain.errors import InvalidVoteError, VoteConflictError, VotingCycleClosedError

def cast_vote(...) -> BallotSnapshot:
    # validate → call port → map conflicts to domain errors → return snapshot
    try:
        votes.upsert_vote(...)
    except VoteConflictError as exc:
        snapshot = get_ballot(...)
        raise VoteConflictError(cycle.id, user_id, ballot=snapshot) from exc
    return get_ballot(...)
```

**Also for publish step:** `publish_material.py` — load → domain transform → `repo.save`:
```python
def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
```

**Copy for Phase 5 `send_digest`:**
1. Validate approved∩ready non-empty; reject drafts (`DraftInSendPoolError` → HTTP 400).
2. Reject already-sent (`AlreadySentError` → HTTP 409 «Уже отправлено»).
3. Claim batch + publish issue + `Mailer.send` — no FastAPI/Supabase in use-case.
4. On failure before durable claim → not sent (ADMIN-07).

---

### `backend/.../domain/shortlist.py` + `errors.py` (model)

**Analog DTOs:** `backend/src/backend/domain/vote.py` (lines 11-38):
```python
@dataclass(frozen=True)
class BallotTopic:
    id: str
    title: str
    description: str
    materials_count: int
    votes: int

@dataclass(frozen=True)
class BallotSnapshot:
    # assembled read-model for HTTP layer
    ...
```

**Analog errors:** `backend/src/backend/domain/errors.py` (lines 67-95) — `VotingCycleClosedError` / `VoteConflictError` / `InvalidVoteError` carrying optional payload for HTTP 409 detail.

**Copy for Phase 5:** Add `AlreadySentError`, `DraftInSendPoolError`, `EmptySendPoolError`, `ShortlistNotFoundError` as `DomainError` subclasses; shortlist batch/item frozen dataclasses with `decision`, `score`, `score_factors`, `material_status`.

**Wave 0 role fix:** `CurrentUser.role` default in `domain/current_user.py` line 12 is `"authenticated"` — change to `"employee"` to match live adapter `_DEFAULT_APP_ROLE`.

---

### `backend/.../infrastructure/stub_mailer.py` (service, request-response)

**Analog:** `StubQueryEmbedder` in `backend/.../ports/query_embedder.py` (lines 15-27):
```python
class StubQueryEmbedder:
    """Deterministic ... for Phase 4 ... No FoundryModels HTTP client this phase — honesty path..."""

    def embed(self, text: str) -> list[float]:
        ...
```

**Copy for Phase 5:**
- `StubMailer` implements `Mailer` — logs body, returns `delivery_status='stubbed'`, `recipient_count=0` (or fixed stub; never imply real subscribers).
- `SmtpMailer` class exists with `NotImplementedError`; composition fail-fast if `MAILER=smtp`.
- Prefer colocating stubs either under `infrastructure/` (new) or next to Protocol like embedder — planner picks one; wire only in composition.

---

### `backend/.../interface/http/deps.py` + `routes/admin.py` (middleware + route)

**Auth base:** `deps.py` `get_principal` (lines 19-48) — JWT verify → domain gate → `HTTPException` 401/403.

**Chained admin Depends (from RESEARCH, adapt to codebase):**
```python
def require_admin(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUser:
    container = request.app.state.container
    user = get_current_user(container.profiles, claims)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user
```

**CRITICAL:** Authorize from `profiles.role` / `CurrentUser.role` — **never** JWT `role` (`auth_jwt.py` requires JWT `role == "authenticated"`).

**HTTP route analog:** `backend/.../routes/voting.py`

**Router + Pydantic + Depends + error map** (lines 22-23, 111-118, 141-154, 169-223):
```python
router = APIRouter(prefix="/voting", tags=["voting"])

def _require_votes(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "votes", None) is None:
        raise HTTPException(status_code=503, detail="votes_not_configured")
    return container.votes

@router.get("/current", response_model=BallotSnapshotResponse)
def read_current_ballot(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> BallotSnapshotResponse:
    ...
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="voting_unavailable") from exc

@router.post("/votes", ...)
def post_vote(...):
    except InvalidVoteError → 400
    except VotingCycleClosedError / VoteConflictError → 409 + structured detail
    except PersistenceError → 503
```

**Copy for Phase 5 `admin.py`:**
- `APIRouter(prefix="/admin", tags=["admin"])`.
- Every handler: `Depends(require_admin)` (not bare `get_principal`).
- Map: PersistenceError → 503; AlreadySent → 409; draft-in-pool / empty pool → 400; non-admin → 403.
- `_require_shortlist` / `_require_mailer` same 503-if-missing pattern.
- Register in `app.py` next to `voting.router` (line 55).

**me.py note:** Comment at lines 3-4 / 57-58 explicitly defers AUTH-03 admin gate to Phase 5 — update when admin router lands.

---

### `backend/.../composition/*` (config)

**Settings** (`settings.py` lines 13-51): frozen dataclass + `from_env`; add `mailer: str = "stub"`; if `mailer == "smtp"` → fail at `build_live_container` / `resolve_container` with clear Russian message.

**Container** (`container.py`): `@dataclass AppContainer` holds ports; `build_in_memory_container()` seeds fakes — add `shortlist` + `mailer`.

**Live wiring** (`live.py` lines 23-54):
```python
admin_client = create_service_role_client(settings.supabase_url, settings.supabase_secret_key)
return AppContainer(
    ...
    votes=SupabaseVoteRepository(admin_client),
    ...
)
```
Add `shortlist=SupabaseShortlistRepository(admin_client)`, `mailer=StubMailer()`, extend issues adapter. Never construct clients in use-cases.

---

### `supabase-integration/.../shortlist_repository.py` (service, CRUD)

**Analog:** `supabase-integration/.../vote_repository.py`

**Adapter pattern** (lines 36-65):
```python
class SupabaseVoteRepository:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]:
        try:
            topics_result = self._client.table("topics").select(...).eq(...).execute()
            ...
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"votes list_topics failed: {exc}") from exc
```

**Audit analog:** `SupabasePingRecorder.record` → `activity_events.insert` (lines 20-43).

**Copy for Phase 5:**
- Current batch = `sent_at IS NULL` ordered by `week_start`/`created_at` desc (D-81).
- Join materials for `status` draft/ready.
- Atomic claim: prefer SQL/RPC `UPDATE … WHERE sent_at IS NULL RETURNING` (RESEARCH Pattern 2); map zero rows → domain `AlreadySentError`.
- Seed migration comment: «demo batch для Phase 5».

---

### `supabase-integration/migrations/005_phase5_admin_shortlist.sql` (migration, batch)

**Analog:** `003_phase3_voting_ballot.sql` header (lines 1-4):
```sql
-- Phase 3 voting ballot seed + open-cycle vote trigger (VOTE-01/03/04, option-a).
-- Idempotent: WHERE NOT EXISTS ...; insert-only (no table wipes).
-- Shared VM (knowledge-db.ru): apply once via MCP/psql or supabase db push — never reset.
```

**Copy for Phase 5:** ALTER batches add nullable `delivery_status`, `recipient_count`, `published_issue_id`/`issue_url`; idempotent seed ≤5 items with `score_factors` ≥2 labels; honesty comment; optional `claim_and_publish_digest` RPC if planner chooses A4.

---

### `web/src/services/adminApi.js` (service, request-response)

**Analog:** `web/src/services/votingApi.js`

**Error classes + mock gate** (lines 1-15, 19-33):
```javascript
/**
 * Voting ballot API — GET /voting/current + POST /voting/votes (D-52, D-56).
 * Mock/live cutover via isMocksEnabled(); never silent mock fallback after live failure.
 */
import { isMocksEnabled } from './authEnv.js'

export class VoteSubmitError extends Error {
  constructor(message, { code = 'SUBMIT_FAILED', retryable = true, ballot = null } = {}) {
    super(message)
    this.name = 'VoteSubmitError'
    this.code = code
    this.retryable = retryable
    this.ballot = ballot
  }
}
```

**Live fetch pattern** (approx lines 471-473, 695-701): `getAccessToken()` → `fetch(`${apiBase()}/...`, { headers: { Authorization: `Bearer ${token}` }})` → map 4xx/5xx to typed errors; mocks never after live failure.

**Copy for Phase 5:** `fetchShortlist`, `setDecision`, `previewEmail`, `sendDigest`; harness flags for empty/sent/draft/403 as needed (`__DIGEST_ADMIN_*__`); `VITE_USE_MOCKS` same as voting/me.

---

### `web/src/services/meApi.js` (service — Wave 0)

**Analog:** same file lines 46-53 — mock currently returns `role: 'authenticated'`.

**Copy for Phase 5:** Mock default `employee`; admin fixture/harness sets `admin`. Align with live `SupabaseProfileRepository` (`_DEFAULT_APP_ROLE = "employee"`).

---

### `web/src/pages/AdminDigestPage.jsx` (component, request-response)

**Analog:** `web/src/pages/VotingPage.jsx`

**Load / mutation UX** (lines 1-15, 61-72, 79-99):
```javascript
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import ErrorPanel from '../components/ErrorPanel.jsx'
import { fetchBallot, submitVote, BallotFetchError, VoteSubmitError } from '../services/votingApi.js'

// GET fail → loadState + ServiceUnavailable + Retry (loadKey)
// mutation fail → toast/ErrorPanel; never mark success; keep selection
function EmptyVotingCta() {
  return (
    <p className="mt-6">
      <Link to="/" className="...">К выпуску →</Link>
    </p>
  )
}
```

**UI chrome:** Port layout/modals from `design-frontend/pages/admin-digest.html`.

**Product overrides (locked — do not copy prototype JS):**
| Prototype | Phase 5 |
|-----------|---------|
| Send pool = checked rows | Send pool = all `approved` + `ready` (D-83) |
| Empty mentions pipeline | «Кандидатов пока нет» + «Обновить» (D-80) |
| No top-N | «Оставить топ-3» checkboxes only (D-84) |
| Success «отправлено N» | «Отправка записана» (D-87) |

Session flag `emailPreviewed` client-side after successful preview; Send stays disabled until then (D-86). Server still re-validates on preview/send.

---

### `web/src/pages/ForbiddenPage.jsx` (component, request-response)

**Closest partial analogs:** `VotingPage` empty CTA («К выпуску») + `ServiceUnavailable` splash structure.

**No dedicated 403 page exists.** Implement:
- Heading «Недостаточно прав»
- CTA «На выпуск» → `/`
- Never render empty shortlist for non-admin deep-link (D-75)
- Gate after `fetchMe` shows `role !== 'admin'`

---

### `web/src/components/AppShell.jsx` + `App.jsx` (component / config)

**AppShell** (lines 56-75): nav `NavLink` list — add conditional:
```jsx
{role === 'admin' ? (
  <NavLink to="/admin/digest" className={linkClass}>Админ</NavLink>
) : null}
```
Extend `fetchMe` effect (lines 19-46) to store `role` alongside identity.

**App.jsx** (lines 21-38): under `RequireAuth` + `AppShell`, add:
```jsx
<Route path="admin/digest" element={<AdminDigestPage />} />
```
Non-admin deep-link handled inside page or wrapper that renders `ForbiddenPage` (not `Navigate` to empty shortlist). Catch-all `*` stays last.

---

### Tests

**HTTP admin / AUTH-03:** Copy `tests/unit/test_http_voting.py` harness — ES256 mint, `Settings`, `create_app`, `build_in_memory_container`, seed profile `role=employee` vs `admin`, assert all `/admin/*` → 403 for employee.

**`/me` role:** Update `test_http_me.py` lines 93-98 — expect `"employee"` not `"authenticated"`.

**Use-case units:** Follow `cast_vote` / ballot tests — in-memory fakes only; assert AlreadySent / draft block / stub delivery_status.

**Playwright:** Copy `tests/auth.spec.js` returnUrl + harness initScript pattern; new `tests/admin.spec.js` for 403 page, empty honesty, select-all/top-N, preview gate (mocks). Design-frontend static tests already hit `admin-digest.html` — SPA tests must not rely on those alone.

**returnUrl (ADMIN-08):** Reuse `sanitizeReturnUrl` from `web/src/services/authEnv.js` (RESEARCH lines 399-408); stub body links `/issues/{number}`.

---

## Shared Patterns

### Authentication / Admin gate
**Source:** `backend/.../deps.py` `get_principal` + new `require_admin`; profile from `get_current_user` / `ProfileRepository`
**Apply to:** All `/admin/*` routes; SPA nav is non-authoritative
```python
# JWT authenticates; profiles.role authorizes (D-74)
claims = Depends(get_principal)  # role claim is "authenticated" only
user = get_current_user(profiles, claims)
if user.role != "admin":
    raise HTTPException(status_code=403, detail="forbidden")
```

### Error handling (HTTP)
**Source:** `routes/voting.py`
**Apply to:** `routes/admin.py`
| Domain | HTTP |
|--------|------|
| PersistenceError | 503 |
| Invalid / empty / draft-in-pool | 400 |
| AlreadySent | 409 |
| Non-admin | 403 |
| Missing JWT | 401 (via get_principal) |

### Error handling (SPA)
**Source:** `VotingPage.jsx` + `ServiceUnavailable.jsx`
**Apply to:** `AdminDigestPage.jsx`
- GET fail → splash + Retry
- Mutation fail → toast/banner; keep checkbox/decision UI state; never fake send success

### Validation
**Source:** Pydantic `BaseModel` + `ConfigDict(extra="forbid")` in `voting.py`
**Apply to:** Admin decision body (`decision` enum allowlist: pending/approved/rejected)

### Composition / service_role
**Source:** `composition/live.py`
**Apply to:** Shortlist + issue publish + ping audit adapters — inject client; never `VITE_` secrets

### Honesty / stub delivery
**Source:** Phase 4 `StubQueryEmbedder` + runbook honesty
**Apply to:** StubMailer + UI copy «Отправка записана»; seed comment; runbook §4e; UI silent on seed vs pipeline

### Ports & Adapters + TDD
**Source:** `.cursor/rules/architecture.mdc`, `tdd.mdc`
**Apply to:** Entire phase — failing pytest/Playwright before production; no SDK in use-cases

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `web/src/pages/ForbiddenPage.jsx` | component | request-response | No dedicated 403 page; compose from empty-CTA + splash patterns |
| Atomic claim RPC (optional) | migration | batch | Phase 4 has `search_knowledge_chunks` RPC analog for SECURITY INVOKER + service_role grant — use that as template if planner chooses RPC over multi-step PostgREST |

**RPC template if needed:** `004_phase4_knowledge_razbory.sql` lines 6-64 — `create or replace function` + `revoke all … from anon, authenticated` + `grant execute … to service_role`.

## Metadata

**Analog search scope:** `backend/src/backend/{application,domain,interface,composition,infrastructure,tests_support}`, `supabase-integration/`, `web/src/{pages,services,components}`, `tests/`, `supabase-integration/migrations/`, `design-frontend/pages/admin-digest.html` (UI chrome reference only)
**Files scanned:** ~55 primary + prior `04-PATTERNS.md` format
**Pattern extraction date:** 2026-09-21

## PATTERN MAPPING COMPLETE
