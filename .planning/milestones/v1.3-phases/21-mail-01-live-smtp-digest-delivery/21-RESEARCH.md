# Phase 21: MAIL-01 live SMTP digest delivery - Research

**Researched:** 2026-10-16
**Domain:** Live digest SMTP (stdlib `smtplib`/`email`) + profiles audience honesty + post-publish mail containment
**Confidence:** HIGH for in-repo seams and locked CONTEXT decisions; MEDIUM for stdlib SMTP transport details (Context7 + docs.python.org)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Audience from `profiles`
- **D-01:** Digest recipients = **all** `profiles` rows that have a usable email — no role filter, no admin exclusion.
- **D-02:** Empty or malformed emails are **excluded** from the audience and **logged** (who/why); they do not count toward M.
- **D-03:** The send address is **`profiles.email` only** (no alternate address fields).
- **D-04:** If the filtered audience is empty (`M=0`): still **publish** the issue; mail is a no-op; `recipient_count=0` with an honest delivery status — do **not** block publish. — **Reversibility:** costly — changing this later would reintroduce a pre-publish audience gate and conflict with D-88 best-effort mail.

### Send shape & partial failure
- **D-05:** Send **one SMTP message per recipient** (not a single Bcc blast), so N of M is meaningful and addresses are not leaked across employees.
- **D-06:** Persist honesty via **option (i)**: batch/`claim_and_publish` keeps **planned** `recipient_count=M`; actual N and status details go to the **API response** and the `digest_send` **activity/`pings` payload**. No `DigestPublisher.update_delivery` in this phase. — **Reversibility:** reversible — option (ii) can be added later without rewriting the mailer.
- **D-07:** Live `delivery_status` values: `sent` (N=M, M>0), `partial` (0<N<M), `failed` (N=0, M>0); `stubbed` remains for `MAILER=stub`.
- **D-08:** On per-recipient failure: **continue**; **stop after three consecutive SMTP failures**; a successful send **resets** the consecutive counter; record the stop reason and counts in the activity/`pings` event. — **Reversibility:** reversible — threshold is a constant in the adapter/use-case policy.

### Admin response after send
- **D-09:** Response `message` is two honest sentences: publish confirmation + delivery line (e.g. «Выпуск опубликован. Доставлено N из M» / «… Письма не доставлены» on full mail fail). Never claim organisation-wide delivery.
- **D-10:** API exposes both counts: `recipient_count` = planned **M**, `delivered_count` = actual **N**; `message` is composed from them. — **Reversibility:** costly — additive field on `SendDigestResponse` / SPA `adminApi` contract once clients depend on it.
- **D-11:** HTTP status stays **200** when claim+publish succeeded, even if mail is `partial`/`failed` (D-88; tripwire PRESERVE).
- **D-12:** When `MAILER=stub`, message must say so explicitly, e.g. «Выпуск опубликован. Доставка писем: stub (0 из M)» — never look like a live SMTP failure.

### Relay contract & proof gate
- **D-13:** Default TLS posture: **`starttls` on port 587**; operator may override via env (`SMTP_TLS_MODE` / port). Document in runbook.
- **D-14:** Bounded timeouts are **fixed in `Settings`** (not env): connect ≈ **10s**, per-send ≈ **30s**; injected into the adapter as ready primitives — no `os.environ` in the adapter (MAIL-05).
- **D-15:** Ship real `SmtpMailer` + recipients/honesty with **`MAILER=stub` as default**. Live `MAILER=smtp` is an ops flip after relay smoke. Phase 20 criterion-4 relay **proof is not a merge blocker** for this phase's code; keep the smoke/rollback procedure in the runbook.
- **D-16:** `MAILER=smtp` with incomplete `SMTP_*` → **fail-fast at startup** (`ConfigurationError`), never silent stub fallback. Required at minimum: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` (TLS mode defaults to starttls). Align From with ADR-0003 domains. — **Reversibility:** reversible — env completeness check only.

### Claude's Discretion
- Exact Russian wording of the two-sentence `message` variants (sent / partial / failed / stub / M=0), as long as D-09/D-12 hold.
- Whether consecutive-failure stop lives primarily in the SMTP adapter vs use-case orchestration, provided D-08 semantics and event payload are identical.
- `Recipient` DTO shape (email + optional display_name) vs bare emails on the port — prefer explicit DTO per research, as long as the port stays typed (no `Any`).
- Exact log fields for excluded emails (D-02) and redaction of SMTP credentials in logs.

### Deferred Ideas (OUT OF SCOPE)
- **Option (ii) `update_delivery`** — post-mail update of batch delivery columns; not in this phase (D-06).
- **Relay/contour formal ADR** — declined in Phase 20 (D-04 there); still optional if ops needs a formal record when values land.
- **GoTrue confirmation path (A)** / flipping autoconfirm — ops after relay smoke; not digest `Mailer` work.
- **SPA `authApi.js` confirmation-mailer error mapping** — deferred from Phase 20 (D-08 there).
- **Bcc single-message send** — rejected for v1.3 in favour of per-recipient (D-05).

None — discussion stayed within phase scope for product capabilities.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAIL-01 | Real SMTP mailer replaces stub for digests; audience from `profiles`; mail best-effort after publish (never 500 a published digest) | `SmtpMailer` in `backend/infrastructure`; `send_digest` catches mail domain error + `PersistenceError`; D-88 tripwire PRESERVE |
| MAIL-03 | Honest planned M + delivered N; response reports «N из M»; never claim whole organisation | `list_digest_recipients` → M; mailer returns N; `SendDigestResponse.delivered_count`; message variants D-09/D-12; option (i) for batch vs API |
| MAIL-04 | SMTP/`OSError`/timeout map to domain error caught with `PersistenceError`; bounded timeouts | New `MailDeliveryError` (or equivalent) at adapter boundary; Settings-fixed 10s/30s timeouts (D-14); no smtplib leakage into use case |
| MAIL-05 | `SMTP_*` only via settings/composition; no `os.environ` in adapters; no secrets in app code | Extend `Settings.from_env`; `resolve_mailer(settings)` injects primitives; fail-fast `ConfigurationError` (D-16) |
</phase_requirements>

## Project Constraints (from AGENTS.md / architecture rules)

No `./CLAUDE.md` or `./.claude/CLAUDE.md` in this repo. Enforce from `AGENTS.md` + `.cursor/rules`:

- **TDD:** Red–Green–Refactor mandatory — `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`.
- **Ports & Adapters:** `domain/` and `application/use_cases/` must not import `smtplib`, `supabase`, `httpx`, or FastAPI. SMTP adapter lives in `backend/infrastructure`. Wiring only in `composition/`.
- **Error mapping at adapter boundary** into domain errors.
- **No `Any` on ports**; explicit DTOs.
- Frontend API only through `web/src/services/*`.
- Project skills present (hallmark / supabase) — not primary for this backend mail phase; supabase skill applies only if migration work appears (none required for `p_recipient_count`).

## Summary

Phase 21 lands digest delivery honesty and a real stdlib SMTP adapter behind the existing `Mailer` port, without making live corporate-relay smoke a merge gate. The codebase already publishes atomically (`claim_and_publish`), then treats mail/audit as best-effort — but today it only catches `PersistenceError`, discards the mailer return value, never resolves recipients, and stamps `recipient_count=0` / `delivery_status=stubbed` via RPC defaults. Locked CONTEXT settles the product gaps: all usable `profiles.email` addresses, per-recipient SMTP, option (i) honesty (planned M on the batch; N + status on API/`pings`), consecutive-failure stop at three, and `MAILER=stub` default with fail-fast `ConfigurationError` when `MAILER=smtp` lacks `SMTP_*`.

**Primary recommendation:** Plan two behavioural waves — (1) audience + honesty with the stub (MAIL-01a), then (2) `SmtpMailer` + Settings/`resolve_mailer` + mail-error containment (MAIL-01b) — then thin HTTP/SPA contract for `delivered_count` and the two-sentence Russian `message`. Honor D-06 over a literal reading of roadmap criterion 4 for **batch columns**: post-send status/N are written into `SendDigestResult` / API / `pings`, not via `update_delivery`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Audience predicate (usable email → Recipient[]) | API / Backend (application use case + port) | Database / Storage (profiles rows via service_role) | Audience is a business rule; SQL must not invent the count |
| Planned M at publish (`p_recipient_count`) | API / Backend → Database | — | Use case computes M; RPC already accepts param (005/006) |
| SMTP transport (STARTTLS, login, send) | API / Backend (`backend/infrastructure`) | — | Local adapter; not data-collection / not GoTrue |
| Partial-failure / consecutive-stop policy | API / Backend (adapter or use-case; same semantics) | — | D-08; discretion on home |
| Post-publish mail containment (no 500) | API / Backend (use case) | — | Catch domain mail error + `PersistenceError` after claim |
| Admin honesty copy (N/M, stub wording) | API / Backend + Browser / Client | — | Backend composes `message`; SPA shows banner via `adminApi` |
| `SMTP_*` / `MAILER` configuration | API / Backend (composition/settings) | OS / VM env | MAIL-05; adapters get primitives only |
| Signup confirmation mail | Out of scope (GoTrue) | — | Phase 20; anti-feature to route through `Mailer` |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `smtplib` | stdlib (workspace `requires-python = ">=3.12"`) [VERIFIED: pyproject.toml:6] | SMTP client | Sync `Mailer` port; zero new deps [CITED: docs.python.org/3/library/smtplib.html] |
| Python stdlib `email.message.EmailMessage` | stdlib | multipart text+HTML | Matches existing `body_text`/`body_html` [CITED: docs.python.org/3/library/email.message.html] |
| Python stdlib `ssl` | stdlib | `create_default_context()` for STARTTLS | Official pattern with `SMTP.starttls(context=…)` [CITED: Context7 /python/cpython] |
| Existing FastAPI + ports | in-repo | HTTP + use case | Extend, do not replace |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 9.1.1 via `uv run pytest` [VERIFIED: uv run] | Unit tests | Red–green for ports/adapters/use case |
| In-memory fakes (`backend/tests_support/in_memory.py`) | in-repo | Profile/mailer/publisher doubles | Unit tests without network |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `smtplib` | `aiosmtplib` | Would force async port/`send_digest` rewrite — rejected by STACK research and sync port |
| Per-recipient send | Single Bcc blast | Rejected by D-05 (privacy + N/M meaning) |
| Option (ii) `update_delivery` | Option (i) API/`pings` honesty | Deferred by D-06 |

**Installation:** none — **zero new runtime packages**.

**Version verification:** No third-party installs this phase. Workspace Python constraint: `requires-python = ">=3.12"` [VERIFIED: pyproject.toml:6]. Host probe: Python 3.14.0, `uv` 0.10.9, `uv run pytest` → pytest 9.1.1.

## Package Legitimacy Audit

> Phase installs **no** external packages (stdlib only). Legitimacy gate N/A.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | No installs |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
Admin SPA (AdminDigestPage)
    │  POST /admin/shortlist/send  (Bearer admin JWT)
    ▼
HTTP route (admin.py) ──► send_digest use case
                            │
                            ├─1─ profiles.list_digest_recipients()
                            │       └─ SupabaseProfileRepository (service_role)
                            │            └─ SELECT profiles → filter usable email → Recipient[]
                            │                 M = len(recipients)  (excluded logged, not in M)
                            │
                            ├─2─ publisher.claim_and_publish(..., recipient_count=M)
                            │       └─ RPC claim_and_publish_digest
                            │            stamps planned M; p_delivery_status default/stub-era
                            │            [NO post-mail update_delivery — D-06]
                            │
                            ├─3─ mailer.send_digest(recipients=…, recipient_count=M, …)
                            │       ├─ StubMailer → status=stubbed, N=0
                            │       └─ SmtpMailer → per-recipient SMTP (starttls/ssl)
                            │            consecutive-fail stop @ 3
                            │            maps SMTPException|OSError|TimeoutError → MailDeliveryError
                            │
                            ├─4─ catch MailDeliveryError | PersistenceError → log; continue
                            │
                            ├─5─ pings.record(digest_send, {M, N, status, stop_reason?})
                            │
                            └─6─ SendDigestResult {delivery_status, recipient_count=M,
                                                   delivered_count=N, message}
                                    └─ SendDigestResponse (+ SPA banner)
```

### Recommended Project Structure

```text
backend/src/backend/
├── domain/
│   ├── recipient.py              # NEW: frozen Recipient DTO
│   └── errors.py                 # ADD: MailDeliveryError
├── application/
│   ├── ports/
│   │   ├── mailer.py             # ADD recipients (+ clarify return keys)
│   │   ├── profile_repository.py # ADD list_digest_recipients
│   │   └── digest_publisher.py   # ADD recipient_count kwarg to claim_and_publish
│   └── use_cases/
│       └── send_digest.py        # resolve → publish(M) → mail → audit → honest result
├── infrastructure/
│   ├── stub_mailer.py            # KEEP StubMailer; resolve_mailer → real SmtpMailer
│   └── smtp_mailer.py            # NEW: real SmtpMailer (or replace placeholder in stub_mailer)
├── composition/
│   ├── settings.py               # SMTP_* + fixed timeouts + TLS mode
│   ├── config_error.py           # NEW: ConfigurationError (backend has none today)
│   ├── live.py                   # resolve_mailer(settings) with full Settings
│   └── container.py              # already has profiles + mailer
supabase-integration/src/supabase_integration/
├── profile_repository.py         # ADD list_digest_recipients (service_role client)
└── digest_publisher.py           # forward p_recipient_count (and optional p_delivery_status)
web/src/
├── services/adminApi.js          # delivered_count + new message contract / mocks
└── pages/AdminDigestPage.jsx     # banner already shows result.message
docs/agents/local-platform-runbook.md  # SMTP_FROM + timeouts note; smoke stays ops
```

### Pattern 1: Honesty-before-live-SMTP (MAIL-01a → MAIL-01b)

**What:** Land recipients + planned M + API/`pings` honesty with `StubMailer` first; then replace the `NotImplementedError` placeholder with real SMTP.
**When to use:** Always for this phase (ARCHITECTURE build order + roadmap success criterion 1).
**Example flow:** failing unit test that `send_digest` passes `recipients` and returns `recipient_count=M` / stub message → green with stub → then red tests for `SmtpMailer` mapping exceptions.

### Pattern 2: Adapter-boundary error mapping (MAIL-04)

**What:** `SmtpMailer` catches `smtplib.SMTPException`, `OSError`, `TimeoutError` (and SSL errors as OSError subclasses) and raises a domain `MailDeliveryError`. `send_digest` catches `(MailDeliveryError, PersistenceError)` around mail **and** keeps the existing audit catch.
**When to use:** Any live transport. Do **not** map SMTP failures solely to `PersistenceError` if that would blur persistence vs delivery in logs — CONTEXT/MAIL-04 asks for a domain error **caught alongside** `PersistenceError`. STACK's "map to PersistenceError" is superseded by locked MAIL-04.

### Pattern 3: Composition-only SMTP config (MAIL-05 / D-16)

**What:** `Settings.from_env` reads `MAILER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, optional `SMTP_FROM_NAME`, `SMTP_TLS_MODE` (default `starttls`). Timeouts are **dataclass defaults** (10s connect / 30s per-send), not env (D-14). `resolve_mailer(settings)` constructs `SmtpMailer(...)` with primitives; incomplete SMTP when mode is `smtp` raises `ConfigurationError` at startup.
**When to use:** Always. Note: backend currently has **no** `ConfigurationError` [VERIFIED: grep backend → zero matches]; ingestion uses a plain `Exception` subclass in `composition/config_error.py`. Mirror that under `backend/composition/config_error.py` and amend tests that expect `RuntimeError` from `resolve_mailer` / `build_live_container`.

### Anti-Patterns to Avoid

- **Importing `smtplib` in use cases/domain** — violates architecture.mdc.
- **Silent stub fallback when `MAILER=smtp`** — violates D-16 honesty.
- **Bcc blast** — violates D-05.
- **`DigestPublisher.update_delivery` in this phase** — deferred (D-06).
- **Routing signup confirmation through `Mailer`** — Phase 20 anti-feature; fence test exists.
- **New RLS policy on `profiles` for enumeration** — use existing service_role client (`live.py` already wires `SupabaseProfileRepository(admin_client)`).
- **Blocking publish when M=0** — violates D-04 / D-88.
- **Claiming «всем сотрудникам»** in copy — violates MAIL-03 / D-09.
- **Reading STACK's `SMTP_SECURITY` / env timeouts as authoritative** — locked names are `SMTP_TLS_MODE` and Settings-fixed timeouts (D-13/D-14); runbook already uses `SMTP_TLS_MODE`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMTP protocol / MIME | Custom socket SMTP | stdlib `smtplib` + `EmailMessage` | Edge cases (STARTTLS EHLO reset, Bcc strip, timeouts) already handled |
| Async mail queue | Celery/RQ worker | Sync per-recipient loop in adapter | Audience is tens–low hundreds; port is sync; weekly admin action |
| Retry framework | Tenacity for every send | D-08 consecutive-stop policy only | Product policy is continue + stop@3, not exponential backoff |
| Audience SQL in RPC | `count(*)` inside claim RPC | Use-case `list_digest_recipients` | Audience policy must stay testable in domain/application |
| Secret management lib | Vault SDK in adapter | VM env → `Settings.from_env` | MAIL-05; runbook already documents names-only |

**Key insight:** The hard problems are **honesty contracts and exception containment**, not SMTP libraries. Reuse stdlib transport; invest tests in M/N, D-88, and fail-fast config.

## Common Pitfalls

### Pitfall 1: SMTP exception escapes `send_digest` → 500 after publish
**What goes wrong:** Published digest + admin sees 500 / retries → `AlreadySentError` 409 (CR-02/D-88).
**Why it happens:** Mail catch only handles `PersistenceError` today [VERIFIED: send_digest.py:176-189].
**How to avoid:** Introduce `MailDeliveryError`; catch with `PersistenceError`; add unit test that a raising mailer still returns success with stamped issue.
**Warning signs:** HTTP 500 on `/shortlist/send` after issue exists; tripwire `test_send_audit_failure_after_publish_still_returns_success` still green but SMTP path untested.

### Pitfall 2: Ignoring mailer return → still `stubbed`/0 in API
**What goes wrong:** Live SMTP sends mail but response/audit still report stub-era values.
**Why it happens:** Use case discards mailer return; publisher omits `p_recipient_count` [VERIFIED: digest_publisher.py:63-71; send_digest.py:210-216].
**How to avoid:** Pass planned M into claim; surface mailer status/N into result + pings; amend `"stubbed"` asserts deliberately (tripwire AMEND).
**Warning signs:** `pings` payload `recipient_count: 0` after real send.

### Pitfall 3: Additive `Mailer` / `ProfileRepository` / container ripples
**What goes wrong:** Required new kwargs break stub callers and composition tests.
**Why it happens:** Keyword-only protocols + explicit container construction (Pitfall 26 in research PITFALLS).
**How to avoid:** Add `recipients` with default empty sequence **or** update all call sites in the same red/green; keep `StubMailer` tests PRESERVE; amend `test_composition_container` / `test_live_container_wiring` / `test_resolve_mailer_smtp_fails_fast`.
**Warning signs:** Import/`TypeError` in unit suite after port change.

### Pitfall 4: TLS mode / port mismatch
**What goes wrong:** `starttls` against 465 or plaintext after TLS failure.
**Why it happens:** First live transport decisions.
**How to avoid:** Explicit `SMTP_TLS_MODE` ∈ {`starttls`,`ssl`,`none`}; default starttls+587 (D-13); never downgrade after TLS error; document pairing in runbook.
**Warning signs:** `SMTPNotSupportedError` in logs; hung admin request without timeout=.

### Pitfall 5: Misreading option (i) vs roadmap "write delivery_status from mailer"
**What goes wrong:** Planner adds `update_delivery` (out of scope) or leaves API stuck on publication fields.
**Why it happens:** Success criterion 4 wording vs locked D-06.
**How to avoid:** Batch row: planned **M** via `p_recipient_count`; API/`SendDigestResult`/`pings`: mailer's **status + N**. Do not implement option (ii).
**Warning signs:** New publisher method or migration for post-mail update.

### Pitfall 6: `ConfigurationError` name without introducing the type
**What goes wrong:** Tests/docs say `ConfigurationError` but backend only raises `RuntimeError` today [VERIFIED: stub_mailer.py:72-76; test_stub_mailer.py:51-56].
**How to avoid:** Add `backend.composition.config_error.ConfigurationError` (plain `Exception`, like ingestion); switch `resolve_mailer` + amend wiring tests.
**Warning signs:** `except RuntimeError` left as the public contract.

### Pitfall 7: Listing profiles under authenticated RLS
**What goes wrong:** Empty audience in live if a user-scoped client is used.
**Why it happens:** `profiles_select_own` only allows own row [VERIFIED: 001_initial_schema.sql:295-297].
**How to avoid:** Keep `SupabaseProfileRepository` on service_role/`admin_client` (already true in `live.py`).
**Warning signs:** M=0 in production despite many profiles.

## Code Examples

Verified patterns from official sources / live seams:

### EmailMessage + STARTTLS send (stdlib)

```python
# Source: Context7 /python/cpython (email.examples + ssl.rst + smtplib.starttls)
import ssl
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = from_addr
msg["To"] = recipient_email  # one address per message (D-05)
msg.set_content(body_text)
if body_html:
    msg.add_alternative(body_html, subtype="html")

context = ssl.create_default_context()
with smtplib.SMTP(host, port, timeout=connect_timeout) as smtp:
    smtp.starttls(context=context)
    smtp.login(user, password)
    smtp.send_message(msg)
```

### Mailer port extension (additive keyword)

```python
# Target shape — align with ARCHITECTURE §(a); recipients required for live honesty
class Mailer(Protocol):
    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,  # planned M
        recipients: Sequence[Recipient],
        body_html: str | None = None,
    ) -> dict[str, object]:
        """Return delivery_status, recipient_count (planned M echo), delivered_count (N), issue_url."""
        ...
```

Current port (no recipients yet) [VERIFIED: mailer.py:8-23]:

```text
def send_digest(self, *, batch_id: int, issue_url: str, subject: str, body_text: str,
                recipient_count: int, body_html: str | None = None) -> dict[str, object]:
```

### send_digest post-publish catch (extend)

Current catch [VERIFIED: send_digest.py:176-189]:

```text
try:
    mailer.send_digest(...)
except PersistenceError:
    logger.exception(...)
```

Target: also catch `MailDeliveryError`; assign mailer result into `SendDigestResult` / ping payload; compose D-09/D-12 `message`.

### Claim RPC already accepts planned count

Migration 006 signature includes [VERIFIED: 005_phase5_admin_shortlist.sql:28-29 — same defaults in 006]:

```text
p_delivery_status text default 'stubbed',
p_recipient_count int default 0,
```

Forward `p_recipient_count=M` from `SupabaseDigestPublisher` / in-memory publisher. **No new migration** for the count parameter.

### Stub banner (locked example)

```text
«Выпуск опубликован. Доставка писем: stub (0 из M)»
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `StubMailer` + `MAILER=smtp` RuntimeError fail-fast | Real `SmtpMailer` + `ConfigurationError` on incomplete config; stub remains default | Phase 21 | Ops flips `MAILER=smtp` after smoke |
| Discard mailer return; RPC defaults 0/stubbed | Planned M at claim; N/status on API/`pings` (option i) | Phase 21 | Honest admin banner without `update_delivery` |
| Catch only `PersistenceError` around mail | Catch mail domain error + `PersistenceError` | Phase 21 | D-88 holds for live SMTP |
| GoTrue owns signup mail | Unchanged | Phase 20 | Do not overload `Mailer` |

**Deprecated/outdated:**
- STACK suggestion to map all SMTP errors only to `PersistenceError` — superseded by MAIL-04 / dedicated domain error caught alongside.
- STACK env name `SMTP_SECURITY` / env-driven timeout — superseded by D-13/D-14 (`SMTP_TLS_MODE`, fixed Settings timeouts).
- ARCHITECTURE open question "role filter?" — locked D-01: all profiles with usable email.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "Usable email" = non-empty + basic RFC-ish parse (must contain `@` / non-whitespace); no second ADR-0003 filter in the list path because registration already gates domains | Audience | Too-loose filter could include junk rows; too-strict could under-count M |
| A2 | Consecutive-failure stop best lives in `SmtpMailer` (adapter owns SMTP exception taxonomy); use case only records returned `stop_reason` | D-08 discretion | If placed only in use case, adapter must re-raise per failure instead of aggregating |
| A3 | `MailDeliveryError` name/location under `backend.domain.errors` | MAIL-04 | Naming only — must remain a `DomainError` subclass catchable in the use case |
| A4 | Optional `SMTP_FROM_NAME` / `SMTP_CA_BUNDLE` are nice-to-have; not required for D-16 minimum set | Settings | Corporate CA may need bundle later — document as follow-up if smoke fails TLS verify |
| A5 | Phase 20 relay **proof gap** remains ops-only; code merges with `MAILER=stub` | D-15 | Live `MAILER=smtp` in prod without smoke still fails at runtime — runbook must stay clear |

## Open Questions (RESOLVED)

1. **Batch row `delivery_status` after live send (option i)** — RESOLVED
   - What we know: D-06 forbids `update_delivery`; claim can still pass `p_delivery_status` (default `stubbed`).
   - **Chosen answer:** At claim, pass `p_recipient_count=M` and leave `p_delivery_status` at default `stubbed` (or pass `stubbed` explicitly for stub mode). Batch `delivery_status` is **not** the post-send truth in v1.3; API/`pings`/`SendDigestResult` carry live status + N. Do not invent option (ii). Plans 01–03 follow this.

2. **Mailer return key for delivered N** — RESOLVED
   - What we know: Port docstring today returns `{delivery_status, recipient_count, issue_url}` with stub `recipient_count: 0` [VERIFIED: stub_mailer.py:44-48].
   - **Chosen answer:** Return both — `recipient_count` echoes planned M, `delivered_count` is N; API maps 1:1 (D-10). Amend stub to accept `recipients` and keep `delivered_count=0`, `delivery_status=stubbed`. Plans 01–03 follow this.

3. **M=0 delivery_status token** — RESOLVED
   - What we know: D-04/D-07 define sent/partial/failed for M>0; stub uses `stubbed`.
   - **Chosen answer (locked):** For `MAILER=smtp` and M=0, use `delivery_status=sent` with N=0 and non-alarming two-sentence copy (discretion under D-04/D-07/D-09), e.g. «Выпуск опубликован. Получателей нет (0 из 0)». Do **not** use `failed` or invent a `noop` token. Stub mode keeps `stubbed` only when `MAILER=stub`. Locked in Plan 01 acceptance.
## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | backend unit tests / SMTP stdlib | ✓ | 3.14.0 (constraint ≥3.12) | — |
| `uv` | `uv run pytest` | ✓ | 0.10.9 | — |
| `pytest` (via uv) | unit suite | ✓ | 9.1.1 | — |
| Corporate SMTP relay values | Live `MAILER=smtp` smoke | ✗ (ops-supplied; Phase 20 gap) | — | Keep `MAILER=stub` default; code merges without live smoke (D-15) |
| GoTrue `GOTRUE_SMTP_*` proof | Inherited precondition narrative | ✗ | — | Not a digest merge blocker; runbook smoke/rollback preserved |

**Missing dependencies with no fallback:**
- None for **code merge** (stub default).

**Missing dependencies with fallback:**
- Live relay credentials → stub default + runbook ops flip.

Step 2.6 note: Graphify disabled in `.planning/config.json` (`graphify.enabled` not set / status disabled). No graph context used.

## Validation Architecture

> `.planning/config.json` has no `workflow.nyquist_validation` key — treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (`uv run pytest`) |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| Quick run command | `uv run pytest tests/unit/test_send_digest.py tests/unit/test_stub_mailer.py -q` |
| Full suite command | `uv run pytest tests/unit -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAIL-01 / D-88 | Mailer raises domain/SMTP-mapped error after publish → success result, issue exists | unit | `uv run pytest tests/unit/test_send_digest.py::test_send_mail_failure_after_publish_still_returns_success -x` | ❌ Wave 0 (extend PRESERVE pattern from audit test) |
| MAIL-03 | Planned M from profiles; response `recipient_count=M`, `delivered_count=N`; stub message D-12 | unit | `uv run pytest tests/unit/test_send_digest.py -k "recipient or stub_message" -x` | ❌ Wave 0 |
| MAIL-03 | Empty usable audience M=0 still publishes | unit | `uv run pytest tests/unit/test_send_digest.py::test_send_with_empty_audience_still_publishes -x` | ❌ Wave 0 |
| MAIL-04 | Adapter maps `SMTPException`/`OSError`/`TimeoutError` → `MailDeliveryError` | unit | `uv run pytest tests/unit/test_smtp_mailer.py -x` | ❌ Wave 0 |
| MAIL-04 / D-08 | Three consecutive failures stop; success resets streak; payload records stop | unit | `uv run pytest tests/unit/test_smtp_mailer.py -k consecutive -x` | ❌ Wave 0 |
| MAIL-05 / D-16 | Incomplete `SMTP_*` with `MAILER=smtp` → `ConfigurationError` at resolve/build | unit | `uv run pytest tests/unit/test_stub_mailer.py tests/unit/test_live_container_wiring.py -x` | ✅ amend existing |
| MAIL-01 | Stub mailer still returns `stubbed` | unit | `uv run pytest tests/unit/test_stub_mailer.py -x` | ✅ PRESERVE |
| MAIL-01 | Audit failure after publish still success | unit | `uv run pytest tests/unit/test_send_digest.py::test_send_audit_failure_after_publish_still_returns_success -x` | ✅ PRESERVE (message assertion may need amend for new copy) |
| MAIL-03 | HTTP response includes `delivered_count` | unit | `uv run pytest tests/unit/test_http_admin.py -k send -x` | ✅ amend |
| MAIL-03 | SPA mock/`sendDigest` types include `delivered_count` | unit/e2e optional | mock return in `adminApi.js`; Playwright only if banner copy asserted | ❌ Wave 0 (JS mock) |

### Sampling Rate

- **Per task commit:** focused file(s) under `tests/unit/` via `uv run pytest … -x`
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** Full unit suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_smtp_mailer.py` — covers MAIL-04 / D-05 / D-08 / TLS mode branches (fake socket or injected SMTP factory)
- [ ] `tests/unit/test_send_digest.py` — amend `"stubbed"` / message asserts; add mail-failure containment, audience M, delivered_count, ping payload honesty
- [ ] `tests/unit/test_profile_repository_recipients.py` (or extend existing profile tests) — list + exclude empty/malformed
- [ ] `backend/tests_support/in_memory.py` — `InMemoryProfileRepository.list_digest_recipients`; publisher accepts `recipient_count=`
- [ ] Amend `test_stub_mailer.py` resolve path: `ConfigurationError` + successful resolve when SMTP_* complete
- [ ] Amend `test_live_container_wiring.py` / `test_composition_container.py` for new wiring
- [ ] Amend `web/src/services/adminApi.js` mock return for `delivered_count` + stub message
- [ ] Framework install: already present via `uv` — no new install

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (admin send) | Existing `require_admin` on `/shortlist/send` |
| V3 Session Management | no new surface | Existing JWT bearer |
| V4 Access Control | yes | Recipients listed only via service_role adapter; no new RLS widen |
| V5 Input Validation | yes | Exclude malformed emails (D-02); validate `SMTP_TLS_MODE` enum at settings |
| V6 Cryptography | yes (TLS to relay) | `ssl.create_default_context()`; no plaintext fallback after TLS failure |
| V14 Config | yes | Secrets only in VM env; `Settings` fields must not log password (`repr` discipline) |

### Known Threat Patterns for SMTP digest send

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SMTP credential leakage in logs | Information Disclosure | Never log `SMTP_PASS` / full Settings; redacted logger fields |
| Recipient list leakage via shared To/Bcc | Information Disclosure | One message per recipient (D-05); To: single address |
| Enumeration of all profiles via user JWT | Information Disclosure | service_role-only repository path; no authenticated list endpoint |
| Admin request hang / DoS via black-hole relay | Denial of Service | Fixed connect/per-send timeouts (D-14); consecutive-stop (D-08) |
| Silent downgrade to stub on misconfig | Spoofing / Tampering of honesty | `ConfigurationError` fail-fast (D-16) |
| Claiming organisation-wide delivery | Spoofing (integrity of message) | Locked copy rules D-09/D-12 |

## Sources

### Primary (HIGH confidence)

- Live code: `mailer.py`, `stub_mailer.py`, `send_digest.py`, `settings.py`, `digest_publisher.py` (supabase + port), `profile_repository.py`, `admin.py` `SendDigestResponse`, `in_memory.py`, migrations `001`/`005`/`006`, `test_send_digest.py`, `test_stub_mailer.py`, `test_live_container_wiring.py`
- `.planning/phases/21-mail-01-live-smtp-digest-delivery/21-CONTEXT.md` — locked decisions
- `.planning/research/ARCHITECTURE.md` §(a)/(b) — placement, option (i), build order
- `.planning/research/STACK.md` — stdlib SMTP (env naming partially superseded by CONTEXT)
- `.planning/research/PITFALLS.md` — Pitfalls 10–13, 26
- `docs/agents/local-platform-runbook.md` — `SMTP_*` / `GOTRUE_SMTP_*` lanes
- `docs/adr/0003-email-domain-restriction.md` — From/audience domain gate
- `pyproject.toml` — `requires-python = ">=3.12"`

### Secondary (MEDIUM confidence)

- Context7 `/python/cpython` — `SMTP.starttls`, `send_message`, `EmailMessage` multipart examples, timeout/`TimeoutError`/`ValueError` for timeout=0
- [docs.python.org/3/library/smtplib.html](https://docs.python.org/3/library/smtplib.html) — SMTP client contract

### Tertiary (LOW confidence)

- WebSearch synthesis for corporate relay operational practices (no vendor relay doc available this session)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib chosen and verified in STACK + Context7; zero new packages
- Architecture: HIGH — seams read this session; CONTEXT locks product choices
- Pitfalls: HIGH — reproduced from PITFALLS + live code confirmation

**Research date:** 2026-10-16
**Valid until:** 2026-11-15 (30 days; stdlib-stable domain)

### Planner build-order checklist (prescriptive)

1. **Wave 0 tests** for audience/honesty + mail containment (red).
2. **Domain `Recipient` + `MailDeliveryError` + `ConfigurationError`.**
3. **`ProfileRepository.list_digest_recipients` + in-memory + Supabase adapter** (service_role).
4. **`send_digest` orchestration** with stub: M → claim → mail → pings → message/D-12; amend stub-era asserts.
5. **Publisher forwards `p_recipient_count=M`.**
6. **`SmtpMailer` + Settings SMTP_* + `resolve_mailer`** (D-13–D-16, D-05, D-08).
7. **HTTP `delivered_count` + SPA `adminApi` mock/types + banner copy.**
8. **Runbook touch:** document `SMTP_FROM`, fixed timeouts, TLS default; keep Phase 20 smoke/rollback; do not claim GoTrue proof done.
