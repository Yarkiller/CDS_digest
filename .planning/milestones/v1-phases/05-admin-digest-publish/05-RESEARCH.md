# Phase 5: Admin Digest Publish - Research

**Researched:** 2026-09-21
**Domain:** Admin shortlist triage → mandatory email preview → stub digest send → published `digest_issues` + returnUrl link integrity (FastAPI Ports & Adapters + React SPA)
**Confidence:** HIGH (schema + CONTEXT D-74…90 + brownfield auth/content patterns); MEDIUM (FastAPI/Supabase docs via Context7 — classify-confidence MEDIUM even with `--verified`); LOW (SMTP deferred; concurrent-send atomic claim is standard Postgres but not yet coded here)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Admin gate & AUTH-03
- **D-74:** Admin = **`profiles.role = admin` only** — no separate «delegate» flag/claim in v1. — **Reversibility:** reversible — enum already includes `admin`.
- **D-75:** Non-admins: **hide «Админ» nav**; deep-link to admin route shows **403 page** («Недостаточно прав») + CTA **«На выпуск»** — never an empty shortlist. Matches `error_handling.md` §2.7.
- **D-76:** SPA learns role from **`GET /me` profile DTO** (nav + client gate); **all admin APIs still enforce 403** server-side. — **Reversibility:** costly — couples `/me` shape to shell.
- **D-77:** AUTH-03 proof in Phase 5: **pytest** non-admin → 403 on all admin routes **and** Playwright employee deep-link → 403 page. Closes Phase 1 verify gap.

#### Shortlist source & scoring honesty
- **D-78:** v1 shortlist = **seeded/ops batch** in `digest_shortlist_batches` + `digest_shortlist_items` (≤5). **UI does not label** seed vs pipeline. **Runbook + docs** state: v1 batch from seed; live pipeline = PIPE-01+. **Seed file** comment: «demo batch для Phase 5». Future pipeline swap keeps the same UI contract. — **Reversibility:** costly — source swap is adapter-only if ports stay clean.
- **D-79:** Each row shows **numeric score + ≥2 readable factor labels** when `score_factors` provides them; otherwise **«обоснование недоступно»** (ADMIN-05).
- **D-80:** Empty shortlist copy: **«Кандидатов пока нет» + «Обновить»** — **no** «пайплайн не вернул» wording in UI (avoids implying a live job ran).
- **D-81:** **Current batch** = latest unsent (`sent_at IS NULL`, newest `week_start` / `created_at`). No week picker in v1.

#### Triage & batch selection
- **D-82:** Inclusion for send = **`shortlist_decision`**: `approved` in send pool; `rejected` out; `pending` not sendable. Persist Approve/Reject (ADMIN-02). — **Reversibility:** costly — decision enum is the send contract.
- **D-83:** Row **checkboxes are batch-action targets only** (Approve/Reject selected). Send pool = all **`approved` + ready** materials — not a separate «include» checkbox.
- **D-84:** **«Выбрать все»** / **«Оставить топ-N»** (e.g. топ-3) **only update checkboxes** in one operation; admin still must Approve/Reject. Manual uncheck of one row keeps other checks (ADMIN-06).
- **D-85:** Every row shows **draft vs ready** badge. **Approve allowed on drafts**; **Send blocked** if any `approved` item is still draft (list draft badges + error_handling copy).

#### Preview → send → email
- **D-86:** **Mandatory successful email preview this session** before Send unlocks (for current approved set). Failed preview never marks send verified (ADMIN-04). Aligns with prototype hint + §2.7 policy.
- **D-87:** **Mailer port** (Protocol/ABC). v1: **`StubMailer`** (`MAILER=stub`) — persist send + log email body; **no live SMTP**. **`SmtpMailer`** class exists but **`NotImplementedError`**; `MAILER=smtp` → **fail fast at startup** with clear «SMTP не настроен, используйте stub». Persist: `sent_at`, `recipient_count`, `issue_url`, `delivery_status='stubbed'` + **audit** `action='send'` (actor, batch_id, delivery_status). Success UI: **«Отправка записана»** — never «отправлено N подписчикам». Runbook §4e documents stub vs Phase 6+ SMTP. — **Reversibility:** costly — delivery_status + audit shape become the send contract.
- **D-88:** Successful send **publishes a new `digest_issues` row** (approved ready materials attached), sets batch **`sent_at`**, issue URL points at that issue (archive/current update for Phase 2 readers). — **Reversibility:** one-way — creates published issue rows.
- **D-89:** **Hard block** on repeat send for an already-sent batch: UI/API **«Уже отправлено»** — no second issue, no second stub send (ADMIN-07). Network/send failure → not marked sent; selection preserved (existing error patterns).
- **D-90:** Digest email (stub body) contains **link to the published issue**; unauthenticated open → login then **`returnUrl`** to that issue (ADMIN-08 / existing Phase 1 returnUrl).

### Claude's Discretion
- Exact admin route path (e.g. `/admin` vs `/admin/digest`) — prefer prototype/`acceptance_criteria` (`admin-digest`) unless planner finds a clearer plural/section convention with AppShell.
- Email preview modal vs page layout — follow `design-frontend/pages/admin-digest.html` unless UI-SPEC overrides.
- Confirm-send dialog copy; item-preview modal behavior; exact top-N default (3 vs 5); audit_log table vs reuse existing activity if present.
- Carry forward: same `VITE_USE_MOCKS` gate; shortlist GET fail → ServiceUnavailable/banner+Retry; mutation fail → toast/banner, never fake success; composition `service_role` only; Ports & Adapters + TDD.

### Deferred Ideas (OUT OF SCOPE)
- Live ranking / YAML pipeline UI (PIPE-01 / REQ-US-30) — post-v1
- Real SMTP/API delivery (`MAILER=smtp` + credentials) — Phase 6+ / separate ops ticket
- Week picker for shortlist batches
- Explicit re-send / re-open sent batch
- Separate «delegate» role beyond `app_role=admin`
- Public leaderboard, quizzes — already post-v1

None folded from todos (none matched).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADMIN-01 | Admin sees ≤5 ranked candidates; non-admin HTTP 403; empty → refresh empty state | Shortlist GET + `require_admin` Depends; empty copy D-80; seed ≤5 |
| ADMIN-02 | Approve includes / Reject excludes and persists | `shortlist_decision` enum + PATCH/POST decision use-case |
| ADMIN-03 | draft vs ready badges; send blocked if approved draft | Join `materials.status`; D-85 send gate |
| ADMIN-04 | Email preview matches approved ready set; failed preview ≠ verified | Preview endpoint + session `emailPreviewed` flag; D-86 |
| ADMIN-05 | Score + ≥2 factor labels or «обоснование недоступно» | `score_factors` jsonb honesty parser |
| ADMIN-06 | Select-all / top-N checkboxes only; manual uncheck keeps others | Client-only checkbox ops (D-83/D-84); add missing «Оставить топ-3» control |
| ADMIN-07 | Confirm send → success + archive; repeat controlled; network fail not sent | Atomic `sent_at` claim + publish issue + StubMailer; 409 already-sent |
| ADMIN-08 | Stub email link → issue; unauth → login + returnUrl | Issue URL `/issues/{number}`; reuse `sanitizeReturnUrl` |
| AUTH-03 (remainder) | Non-admin admin APIs 403 + Playwright 403 page | D-77 closes Phase 1 verify gap |
</phase_requirements>

## Summary

Phase 5 closes the admin digest loop on **existing** shortlist + issue tables: triage ≤5 seeded candidates, persist Approve/Reject via `shortlist_decision`, require a successful email preview in-session, then atomically publish a new `digest_issues` row and record a **stub** mailer delivery — never live SMTP. Server-side admin gate uses **`profiles.role = admin`** (not JWT `role=authenticated`); SPA hides «Админ» and shows a dedicated 403 page for deep-links.

Brownfield gaps the planner must treat as Wave 0 / early plans: no admin React route, no shortlist/mailer ports, `IssueRepository` is **read-only**, `digest_shortlist_batches` currently stores only `sent_at` (D-87 needs delivery metadata + audit), and **`/me` + in-memory profiles currently expose JWT-shaped `role: "authenticated"`** instead of `app_role` — which blocks D-76 until fixed.

**Primary recommendation:** Implement `ShortlistRepository` + `Mailer` + issue **publish** extension behind FastAPI `/admin/*` with `require_admin`, seed migration `005`, SPA `/admin/digest` from the HTML prototype **except** send-pool semantics follow D-83 (not prototype checkboxes-as-send-selection), and prove AUTH-03 with pytest + Playwright.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Admin role authorization (403) | API / Backend | Database / Storage | `profiles.role` is source of truth; JWT only authenticates |
| SPA nav hide + 403 page | Browser / Client | API / Backend | UX gate from `/me`; never trust client alone |
| Shortlist read / decisions | API / Backend | Database / Storage | Ports + service_role adapters; no browser Supabase |
| draft/ready + score honesty | API / Backend | Browser / Client | Status/factors from DB; UI renders badges/copy only |
| Checkbox select-all / top-N | Browser / Client | — | D-84: local checkbox state only |
| Email preview content | API / Backend | Browser / Client | Preview DTO from approved ready set; session flag client-side |
| Publish issue + mark sent | API / Backend | Database / Storage | Atomic claim + insert issue/items |
| Stub mailer + audit | API / Backend | Database / Storage | Mailer port in application; StubMailer + activity_events |
| returnUrl after email link | Browser / Client | Frontend Server (SSR) — N/A | Existing LoginPage + `sanitizeReturnUrl` |

## Project Constraints (from .cursor/rules/)

| Directive | Implication for Phase 5 |
|-----------|-------------------------|
| Ports & Adapters (`architecture.mdc`) | Mailer + ShortlistRepository are ports; Supabase adapters in `supabase-integration/`; wire only in `composition/` |
| No SDK in use-cases/domain | No `supabase`/`httpx`/`fastapi` in send/preview use-cases |
| Frontend only via `web/src/services/` | New `adminApi.js` (name flexible); pages never call Supabase |
| service_role only in composition | Live shortlist/send uses existing `create_service_role_client` pattern |
| TDD Red–Green–Refactor (`tdd.mdc` / `AGENTS.md`) | Failing pytest/Playwright before production code |
| Module boundaries | No deep-imports across `backend` / `supabase-integration` / `web` |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `0.141.1` `[VERIFIED: backend/pyproject.toml:6-14]` | Admin HTTP routes + Depends chain | Already pinned; `uv run` confirms import |
| uvicorn | `0.53.0` `[VERIFIED: backend/pyproject.toml:13]` | ASGI server | Existing |
| React + Vite | existing `web/` | Admin digest SPA | Brownfield |
| Playwright | `^1.62.1` `[VERIFIED: package.json:18]` | E2E 403 + admin honesty | Existing `tests/*.spec.js` |
| pytest | `>=8.3.0` `[VERIFIED: pyproject.toml dependency-groups]` | Unit/HTTP admin 403 + use-cases | `testpaths = tests/unit` |
| Supabase Python client (via `supabase-integration`) | existing workspace | Shortlist/issue persistence | service_role adapters |
| Postgres enums / tables | `001_initial_schema.sql` | `app_role`, `shortlist_decision`, shortlist + issues | Already migrated on VM |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| structlog | `26.1.0` | Correlate send/preview failures | Existing request logging |
| PyJWT + cryptography | pinned | Unchanged JWT verify | Admin Depends after `get_principal` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| StubMailer + Protocol | Direct SMTP in use-case | Violates ports; deferred by D-87 |
| New `audit_log` table | Reuse `activity_events` | Prefer reuse — already wired via PingRecorder pattern |
| Checkbox = send selection (prototype) | D-83 approved+ready pool | Prototype diverges; product locked to decisions |
| JWT claim admin | `profiles.role` | D-74 / Supabase skill: never authorize from editable user_metadata |

**Installation:** none — **do not add new PyPI/npm packages** for v1 stub mailer.

**Version verification:** FastAPI `0.141.1` confirmed via `uv run python -c "import fastapi; print(fastapi.__version__)"` (2026-09-21).

## Package Legitimacy Audit

> Phase 5 installs **no new** external packages. Existing FastAPI/uvicorn remain as previously approved Phase 1 pins.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| _(none new)_ | — | — | — | — | — | N/A |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none for this phase (legitimacy check on already-pinned fastapi/uvicorn returned SUS solely due to unknown-downloads/too-new heuristics — **do not reinstall**; not an install task)

## Architecture Patterns

### System Architecture Diagram

```text
[Admin SPA /admin/digest]
   |  Bearer JWT
   v
[FastAPI /admin/*]
   |-- require_admin: get_principal → ProfileRepository → profiles.role==admin else 403
   |-- GET shortlist → ShortlistRepository.get_current_batch()
   |-- POST/PATCH decision → ShortlistRepository.set_decision()
   |-- POST preview → build EmailPreviewDTO (approved∩ready)
   |-- POST send → SendDigest use-case:
         1. validate pool (non-empty, no drafts, not already sent)
         2. claim batch (UPDATE ... WHERE sent_at IS NULL)
         3. publish digest_issues + digest_issue_items
         4. Mailer.send (StubMailer) → delivery_status=stubbed
         5. persist delivery fields + activity_events audit
         on failure before claim commit → not sent; UI keeps selection
   v
[composition/live service_role Supabase client]
   v
[Postgres: shortlist_*, materials, digest_issues, activity_events]
```

### Recommended Project Structure

```text
backend/src/backend/
  application/ports/
    shortlist_repository.py      # NEW Protocol
    mailer.py                    # NEW Protocol
    issue_repository.py          # EXTEND: publish/create
  application/use_cases/
    get_admin_shortlist.py
    set_shortlist_decision.py
    preview_digest_email.py
    send_digest.py
  domain/
    shortlist.py                 # Batch/Item DTOs + errors
    errors.py                    # AlreadySentError, DraftInSendPoolError, …
  infrastructure/
    stub_mailer.py               # StubMailer + SmtpMailer(NotImplementedError)
  interface/http/
    deps.py                      # + require_admin
    routes/admin.py              # NEW
  composition/
    settings.py                  # + mailer=stub|smtp
    container.py / live.py       # wire shortlist + mailer

supabase-integration/
  migrations/005_phase5_admin_shortlist.sql   # columns + seed
  shortlist_repository.py
  # extend issue_repository.py publish

web/src/
  services/adminApi.js
  pages/AdminDigestPage.jsx
  pages/ForbiddenPage.jsx        # or inline 403 view
  components/AppShell.jsx        # role-gated «Админ»
  App.jsx                        # route /admin/digest
```

### Pattern 1: Chained admin Depends (AUTH-03)

**What:** After JWT+domain `get_principal`, resolve profile and require `role == "admin"`.  
**When to use:** Every `/admin/*` route.  
**Example:**

```python
# Source: FastAPI dependency chaining [CITED: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2]
# Adapted to Digest CDS: app_role from ProfileRepository, not JWT role.

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

### Pattern 2: Atomic already-sent claim (ADMIN-07)

**What:** Mark batch sent only if still unsent; zero updated rows → 409 «Уже отправлено».  
**When to use:** Inside `send_digest` before creating a second issue.  
**Example:**

```sql
-- [CITED: https://www.postgresql.org/docs/current/sql-update.html] RETURNING
UPDATE digest_shortlist_batches
SET sent_at = now(),
    delivery_status = 'stubbed',
    recipient_count = $1,
    published_issue_id = $2
WHERE id = $3 AND sent_at IS NULL
RETURNING id;
```

Prefer claiming **after** validations and **in the same transaction** as issue insert when the adapter can run SQL/RPC; if PostgREST-only, use a single SECURITY INVOKER RPC `claim_and_publish_digest(...)` rather than read-modify-write in Python. `[ASSUMED]` exact RPC vs multi-step PostgREST — planner should prefer one RPC if concurrent admins are realistic on shared VM.

### Pattern 3: Prototype UI with product overrides

**What:** Port layout/modals from `admin-digest.html`, but **override** send-pool and empty copy per D-80/D-83.  
**When to use:** SPA implementation.  
**Overrides vs prototype JS:**

| Prototype (`app.js`) | Phase 5 product (locked) |
|----------------------|--------------------------|
| Send pool = checked rows | Send pool = all `approved` + `ready` |
| Select-all clears exclusion + checks all | Checkboxes only; Approve/Reject persist decision |
| Empty copy mentions pipeline (error_handling §2.7) | UI: «Кандидатов пока нет» (D-80) |
| No «Оставить топ-3» control | Add «Оставить топ-3» (ADMIN-06 / acceptance) |

### Anti-Patterns to Avoid

- **Authorizing admin from JWT `role` or `user_metadata`:** JWT `role` is Supabase `"authenticated"` `[VERIFIED: backend/src/backend/infrastructure/auth_jwt.py — role != "authenticated" raises]`. Admin is `profiles.role` only (D-74). Supabase skill: never authorize from editable user_metadata.
- **Checkbox = inclusion for send:** Violates D-83; causes draft-in-selection confusion vs approved drafts.
- **SMTP or «отправлено N подписчикам» success copy:** Violates D-87 honesty.
- **Publishing issue before successful claim / marking sent on mailer failure incorrectly:** Leaves duplicates or false success (ADMIN-07).
- **Browser service_role / direct shortlist PostgREST:** Architecture forbids; shortlist has RLS enabled with **no** authenticated policies `[VERIFIED: 001_initial_schema.sql:250-251]` — only service_role can touch.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| AuthN JWT verify | Custom crypto | Existing `get_principal` / `verify_access_token` | Already proven Phase 1 |
| Role gate | Ad-hoc ifs in every handler | `require_admin` Depends | DRY + testable AUTH-03 |
| Live email SMTP | smtplib in use-case | `Mailer` Protocol + StubMailer | D-87; fail-fast if `MAILER=smtp` |
| Audit trail table | New `audit_log` | `activity_events` via recorder port | Schema exists; PingRecorder pattern |
| returnUrl open redirect | Custom parse | `sanitizeReturnUrl` | Phase 1 T-01-12 |
| Concurrent double-send | Check-then-act in Python only | Atomic `UPDATE … WHERE sent_at IS NULL RETURNING` | Race → duplicate issues |

**Key insight:** The hard parts are **authorization semantics** (`app_role` vs JWT), **send-pool semantics** (decisions ≠ checkboxes), and **idempotent publish** — not UI chrome.

## Common Pitfalls

### Pitfall 1: `/me.role` still means JWT `"authenticated"`
**What goes wrong:** AppShell never shows «Админ»; admin tests assert wrong role; live Supabase returns `employee`/`admin` while memory returns `authenticated`.  
**Why it happens:** `InMemoryProfileRepository` and `meApi` mocks hard-code `"authenticated"` `[VERIFIED: backend/.../in_memory.py:82]` `[VERIFIED: web/src/services/meApi.js:51]`; tests lock it `[VERIFIED: tests/unit/test_http_me.py:93-97]`. Live adapter already maps `profiles.role` `[VERIFIED: supabase-integration/.../profile_repository.py:10-24]` (`_DEFAULT_APP_ROLE = "employee"`).  
**How to avoid:** Wave 0 align memory + mocks + tests to **`app_role`** (`employee` default; seed/admin fixture `admin`).  
**Warning signs:** Playwright admin nav never appears under mocks; `/me` contract tests still expect `"authenticated"`.

### Pitfall 2: Treating prototype checkboxes as send selection
**What goes wrong:** Send includes pending/rejected or misses approved-but-unchecked ready rows.  
**Why it happens:** Static `app.js` `selectedRows()` drives preview/send.  
**How to avoid:** Implement D-82/D-83 literally; server re-validates approved∩ready on preview/send.  
**Warning signs:** Preview list differs from DB approved set.

### Pitfall 3: Marking sent before publish/mail succeeds
**What goes wrong:** Batch stuck sent with no issue, or issue without stub record.  
**Why it happens:** Ordering mistakes / partial PostgREST success.  
**How to avoid:** Single transactional RPC or ordered steps with compensating rules documented; never set `sent_at` on preview.  
**Warning signs:** `sent_at` set while `digest_issues` missing for that week.

### Pitfall 4: Empty-state / §2.7 copy drift
**What goes wrong:** UI says «пайплайн не вернул» while seed is manual (dishonest).  
**Why it happens:** error_handling.md §2.7 still has pipeline wording `[VERIFIED: docs/digest-cds/error_handling.md:144]`.  
**How to avoid:** D-80 wins for product UI; update runbook §4e; leave §2.7 note for PIPE-01.  
**Warning signs:** Copy review finds «пайплайн» on admin empty state.

### Pitfall 5: Schema missing D-87 delivery columns
**What goes wrong:** Nowhere durable for `delivery_status` / `recipient_count` / `issue_url`.  
**Why it happens:** Batches table only has `sent_at` today `[VERIFIED: 001_initial_schema.sql:141-146]`.  
**How to avoid:** Migration `005` adds nullable columns (recommended) **and** audit row in `activity_events`.  
**Warning signs:** Stub success only in process logs.

### Pitfall 6: Approve draft then send without server block
**What goes wrong:** Draft article published into issue.  
**Why it happens:** UI-only draft check.  
**How to avoid:** `send_digest` rejects if any approved material `status != ready`; 400 with draft badges list.  
**Warning signs:** Issue items reference draft materials.

## Code Examples

### Schema enums (verbatim)

```sql
-- Source: [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:8-26]
create type app_role as enum ('employee', 'analyst', 'ds', 'admin');
create type material_status as enum ('draft', 'ready');
create type shortlist_decision as enum ('pending', 'approved', 'rejected');
```

### Shortlist tables (verbatim)

```sql
-- Source: [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:141-158]
create table if not exists digest_shortlist_batches (
  id bigint generated always as identity primary key,
  week_start date not null,
  created_at timestamptz not null default now(),
  sent_at timestamptz
);

create table if not exists digest_shortlist_items (
  batch_id bigint not null references digest_shortlist_batches (id) on delete cascade,
  material_id bigint not null references materials (id) on delete restrict,
  rank int not null check (rank > 0),
  score numeric,
  score_factors jsonb not null default '{}'::jsonb,
  decision shortlist_decision not null default 'pending',
  decided_by uuid references profiles (id),
  decided_at timestamptz,
  primary key (batch_id, material_id)
);
```

### Mailer port (recommended)

```python
# Source: project architecture pattern (Protocol ports) [ASSUMED shape — planner may rename fields]
from typing import Protocol

class Mailer(Protocol):
    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
    ) -> dict:
        """Return {delivery_status, recipient_count, issue_url} — stub always 'stubbed'."""
        ...
```

### score_factors honesty (recommended discretionary shape)

```python
# [ASSUMED] seed convention for ADMIN-05 — confirm in plan if UI-SPEC differs
# Prefer object map with ≥2 human labels as keys, or {"factors":[{"label":"..."}, ...]}
# Empty {} / <2 readable labels → UI «обоснование недоступно»

def factor_labels(score_factors: dict) -> list[str]:
    factors = score_factors.get("factors")
    if isinstance(factors, list):
        labels = [str(f.get("label", "")).strip() for f in factors if isinstance(f, dict)]
        return [x for x in labels if x]
    # flat map: keys are labels
    return [str(k) for k, v in score_factors.items() if str(k).strip() and k != "factors"]
```

### returnUrl (existing)

```javascript
// Source: [VERIFIED: web/src/services/authEnv.js:19-28]
export function sanitizeReturnUrl(raw) {
  if (!raw || typeof raw !== 'string') {
    return '/'
  }
  const trimmed = raw.trim()
  if (!trimmed.startsWith('/') || trimmed.startsWith('//') || trimmed.includes('://')) {
    return '/'
  }
  return trimmed
}
```

Stub email should link e.g. `/issues/{number}` so RequireAuth → `/login?returnUrl=/issues/{number}` → LoginPage navigates to sanitized path (ADMIN-08).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static `admin-digest.html` only | React `/admin/digest` + FastAPI `/admin` | Phase 5 | Closes CONCERNS admin gap |
| AUTH-03 admin 403 deferred | pytest + Playwright proofs | Phase 5 (D-77) | Closes Phase 1 verify gap |
| IssueRepository read-only | + publish on send | Phase 5 | Archive/current update for readers |
| No mailer | StubMailer + fail-fast smtp | Phase 5 / SMTP later | Honesty for delivery |

**Deprecated/outdated:**
- Prototype send-pool = checkbox selection — superseded by D-83.
- error_handling §2.7 empty copy mentioning pipeline — superseded in UI by D-80 until PIPE-01.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Prefer route `/admin/digest` (matches `admin-digest` acceptance) | Discretion | Nav/deep-link tests rewrite |
| A2 | Reuse `activity_events` (`kind=digest_send` or `action=send` in payload) instead of new audit table | Discretion / D-87 | Extra migration if product wants dedicated audit_log |
| A3 | Migration adds `delivery_status`, `recipient_count`, `published_issue_id` (or `issue_url`) on batches | Pitfall 5 | Persist only in activity_events payload (weaker queryability) |
| A4 | Concurrent send uses SQL/RPC atomic claim; PostgREST multi-step may race | Pattern 2 | Duplicate issues under dual-admin |
| A5 | `score_factors` seed as map/list with ≥2 labels | Code Examples | UI parser mismatch |
| A6 | Top-N default = 3 («Оставить топ-3») per acceptance US-27 | Discretion | Product may want 5 |
| A7 | Stub `recipient_count=0` (or fixed stub) — never imply real subscribers | D-87 | Misleading success metrics |

**If this table is empty:** N/A — several discretion items remain for planner/UI-SPEC.

## Open Questions (RESOLVED)

1. **Transactional publish vs PostgREST steps** — **RESOLVED** (plan-locked in 05-05)
   - What we know: service_role adapters today are table-oriented; Phase 3 used Studio SQL for triggers when raw_sql unavailable.
   - Resolution: Prefer SECURITY INVOKER RPC `claim_and_publish_digest` (service_role execute only) when concurrent admins are realistic; otherwise documented ordered adapter steps with atomic `UPDATE … WHERE sent_at IS NULL RETURNING` claim (RESEARCH A4 / 05-05 must_haves). Memory tests simulate single-winner claim; live path chooses RPC-or-UPDATE in migration 005.

2. **Where to store mailer delivery fields** — **RESOLVED** (plan-locked in 05-05, D-87 / A3)
   - What we know: D-87 requires persist; batches lack columns.
   - Resolution: Migration `005_phase5_admin_shortlist.sql` adds nullable `delivery_status`, `recipient_count`, and `published_issue_id` and/or `issue_url` on `digest_shortlist_batches`, plus `activity_events` audit on send — not payload-only.

3. **Admin user seed on shared VM** — **RESOLVED** (plan-locked in 05-05 runbook §4e)
   - What we know: profiles upsert defaults to `employee`.
   - Resolution: Runbook §4e documents ops promote (`update profiles set role='admin' where email=…`); unit tests use in-memory admin fixture. No seeded Auth user identity locked in-repo — operator promotes one profile after migration apply.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | backend tests | ✓ | 3.14.0 | — |
| uv | pytest / uvicorn | ✓ | 0.10.9 | — |
| Node | Playwright / Vite | ✓ | v22.13.0 | — |
| FastAPI (workspace) | admin API | ✓ | 0.141.1 via uv | — |
| Playwright browsers | E2E | ✓ (postinstall script) | @playwright/test ^1.62.1 | `npm run playwright:install` |
| Supabase VM (`knowledge-db.ru`) | live seed/send | ✓ (runbook) | remote | `APP_CONTAINER=memory` for unit |
| Live SMTP | real delivery | ✗ by design | — | StubMailer only (D-87) |

**Missing dependencies with no fallback:** none for v1 stub scope.  
**Missing dependencies with fallback:** SMTP → StubMailer + startup fail if `MAILER=smtp`.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (≥8.3) + Playwright (@playwright/test ^1.62.1) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`; Playwright via `package.json` scripts |
| Quick run command | `uv run pytest tests/unit/test_http_admin.py -x` (Wave 0 create) |
| Full suite command | `uv run pytest` && `npm run test:web` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIN-01 | Admin GET shortlist ≤5; empty honesty | unit HTTP + Playwright | `uv run pytest tests/unit/test_http_admin.py -k shortlist -x` | ❌ Wave 0 |
| ADMIN-01 / AUTH-03 | Non-admin → 403 API | unit HTTP | `uv run pytest tests/unit/test_http_admin.py -k forbidden -x` | ❌ Wave 0 |
| AUTH-03 | Employee deep-link → 403 page | e2e | `npx playwright test tests/admin.spec.js -g "403"` | ❌ Wave 0 |
| ADMIN-02 | Approve/Reject persists | unit use-case + HTTP | `uv run pytest tests/unit/test_set_shortlist_decision.py -x` | ❌ Wave 0 |
| ADMIN-03 | Send blocked on approved draft | unit use-case | `uv run pytest tests/unit/test_send_digest.py -k draft -x` | ❌ Wave 0 |
| ADMIN-04 | Preview match; fail ≠ verified | unit + Playwright | `uv run pytest tests/unit/test_preview_digest.py -x` | ❌ Wave 0 |
| ADMIN-05 | Factors ≥2 or недоступно | unit + Playwright | `uv run pytest tests/unit/test_score_factors.py -x` | ❌ Wave 0 |
| ADMIN-06 | Select-all / top-N checkboxes | Playwright | `npx playwright test tests/admin.spec.js -g "топ"` | ❌ Wave 0 |
| ADMIN-07 | Send success; repeat 409; fail not sent | unit use-case + HTTP | `uv run pytest tests/unit/test_send_digest.py -x` | ❌ Wave 0 |
| ADMIN-08 | Stub body contains `/issues/{n}`; returnUrl | unit mailer + existing auth e2e | `uv run pytest tests/unit/test_stub_mailer.py -x` | ❌ Wave 0 |
| D-76 | `/me.role` is app_role | unit HTTP (update existing) | `uv run pytest tests/unit/test_http_me.py -x` | ✅ exists (must change asserts) |

### Sampling Rate

- **Per task commit:** targeted unit file(s) for the behavior (`-x`)
- **Per wave merge:** `uv run pytest` + affected Playwright project
- **Phase gate:** Full `uv run pytest` + `npm run test:web` green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] Align `InMemoryProfileRepository` + `meApi` mocks + `test_http_me` to `app_role` (`employee` default)
- [ ] `tests/unit/test_http_admin.py` — 403 matrix for all admin routes
- [ ] `tests/unit/test_send_digest.py` / `test_preview_digest.py` / `test_set_shortlist_decision.py`
- [ ] `tests/admin.spec.js` — 403 page, empty state, draft block, preview gate, select-all/top-N (mocks)
- [ ] Migration `005_phase5_admin_shortlist.sql` — delivery columns + seed batch (comment «demo batch для Phase 5»)
- [ ] Runbook **§4e** stub mailer + seed honesty + promote admin profile
- [ ] `require_admin` dependency + empty `routes/admin.py` router registered in `app.py`
- [ ] In-memory `ShortlistRepository` + `StubMailer` fakes in `tests_support`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing Bearer JWT + corporate email gate |
| V3 Session Management | yes | Supabase session; returnUrl sanitized |
| V4 Access Control | yes | `require_admin` on all `/admin/*`; SPA hide is non-authoritative |
| V5 Input Validation | yes | Pydantic bodies; decision enum allowlist; material ids |
| V6 Cryptography | no new | No new crypto; do not hand-roll tokens |

### Known Threat Patterns for admin digest / stub mailer

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Non-admin calls send/preview | Elevation of privilege | Server 403 via profiles.role |
| Client forges role in `/me` mock / localStorage | Spoofing | Server ignores client role; re-loads profile |
| service_role leaked to Vite | Information disclosure | Never `VITE_` secret; composition-only |
| Open redirect via email link | Spoofing | `sanitizeReturnUrl` same-origin paths only |
| Double-send race → duplicate issues | Tampering / DoS | Atomic `sent_at IS NULL` claim |
| Draft materials published | Tampering | Server reject approved∩draft |
| SMTP misconfig implies delivery | Repudiation / honesty | Fail-fast `MAILER=smtp`; stub copy only |

**security_enforcement:** enabled (config key absent).

## Sources

### Primary (HIGH confidence)
- `.planning/phases/05-admin-digest-publish/05-CONTEXT.md` — D-74…D-90
- `supabase-integration/migrations/001_initial_schema.sql` — enums + shortlist + issues
- `docs/digest-cds/acceptance_criteria.md` — US-06, US-22…27, US-31
- `docs/digest-cds/error_handling.md` §2.7
- `design-frontend/pages/admin-digest.html` + `design-frontend/scripts/app.js`
- Brownfield: `deps.py`, `me.py`, `profile_repository.py`, `issue_repository.py`, `AppShell.jsx`, `authEnv.js`

### Secondary (MEDIUM confidence)
- Context7 `/websites/fastapi_tiangolo` — Depends chaining / HTTPException
- Context7 `/supabase/supabase` — service_role bypasses RLS; never in browser
- PostgreSQL UPDATE … RETURNING docs — atomic claim pattern

### Tertiary (LOW confidence)
- Concurrent multi-step PostgREST without RPC — race residual `[ASSUMED]` until migration chooses RPC

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — reuse pinned FastAPI/React/Playwright; no new packages
- Architecture: HIGH — ports map clear; schema present; role gap explicitly identified
- Pitfalls: HIGH — `/me.role` mismatch and prototype checkbox divergence verified in-repo

**Research date:** 2026-09-21  
**Valid until:** 2026-10-21 (stable brownfield; re-check if UI-SPEC overrides route/modals)

## RESEARCH COMPLETE
