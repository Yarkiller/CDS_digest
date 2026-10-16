# Phase 21: MAIL-01 live SMTP digest delivery - Pattern Map

**Mapped:** 2026-10-16
**Files analyzed:** 22
**Analogs found:** 21 / 22

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/domain/recipient.py` | model | transform | `backend/src/backend/domain/current_user.py` | exact |
| `backend/src/backend/domain/errors.py` | model | request-response | `backend/src/backend/domain/errors.py` (`PersistenceError`) | exact |
| `backend/src/backend/domain/auth_email.py` (reuse for usable-email predicate) | utility | transform | `backend/src/backend/domain/auth_email.py` | exact |
| `backend/src/backend/application/ports/mailer.py` | port | request-response | `backend/src/backend/application/ports/mailer.py` | exact |
| `backend/src/backend/application/ports/profile_repository.py` | port | CRUD | `backend/src/backend/application/ports/profile_repository.py` | exact |
| `backend/src/backend/application/ports/digest_publisher.py` | port | CRUD | `backend/src/backend/application/ports/digest_publisher.py` | exact |
| `backend/src/backend/application/use_cases/send_digest.py` | service | request-response | `backend/src/backend/application/use_cases/send_digest.py` | exact |
| `backend/src/backend/infrastructure/stub_mailer.py` | service | request-response | `backend/src/backend/infrastructure/stub_mailer.py` | exact |
| `backend/src/backend/infrastructure/smtp_mailer.py` | service | request-response | `backend/src/backend/infrastructure/stub_mailer.py` + `local_notebook_storage.py` | role-match |
| `backend/src/backend/composition/settings.py` | config | request-response | `backend/src/backend/composition/settings.py` | exact |
| `backend/src/backend/composition/config_error.py` | config | request-response | `ingestion-service/src/ingestion_service/composition/config_error.py` | exact |
| `backend/src/backend/composition/live.py` | config | request-response | `backend/src/backend/composition/live.py` | exact |
| `backend/src/backend/composition/container.py` | config | request-response | `backend/src/backend/composition/container.py` | exact |
| `supabase-integration/.../profile_repository.py` | service | CRUD | `supabase-integration/.../profile_repository.py` | exact |
| `supabase-integration/.../digest_publisher.py` | service | CRUD | `supabase-integration/.../digest_publisher.py` | exact |
| `backend/.../interface/http/routes/admin.py` | route | request-response | `backend/.../interface/http/routes/admin.py` | exact |
| `web/src/services/adminApi.js` | service | request-response | `web/src/services/adminApi.js` | exact |
| `web/src/pages/AdminDigestPage.jsx` | component | request-response | `web/src/pages/AdminDigestPage.jsx` | exact |
| `docs/agents/local-platform-runbook.md` | config | — | `docs/agents/local-platform-runbook.md` | exact |
| `backend/tests_support/in_memory.py` | test | CRUD | `backend/tests_support/in_memory.py` | exact |
| `tests/unit/test_smtp_mailer.py` | test | request-response | `tests/unit/test_stub_mailer.py` | role-match |
| `tests/unit/test_send_digest.py` (amend + new) | test | request-response | `tests/unit/test_send_digest.py` | exact |

## Pattern Assignments

### `backend/src/backend/domain/recipient.py` (model, transform)

**Analog:** `backend/src/backend/domain/current_user.py`

**Imports + frozen DTO pattern** (lines 1-13):
```python
"""Current authenticated user DTO returned by profile port / GET /me."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str = "employee"
    display_name: str | None = None
```

**Copy for Recipient:** same `frozen=True` dataclass; fields `email: str` + optional `display_name: str | None` (CONTEXT discretion). No FastAPI/SDK imports.

**Usable-email predicate analog:** `backend/src/backend/domain/auth_email.py` lines 13-20 (`"@" not in email`, empty local/domain → False). Reuse the same shape for D-02 filtering (non-empty + `@`); do not re-apply ADR-0003 domain gate in list path (RESEARCH A1).

---

### `backend/src/backend/domain/errors.py` — add `MailDeliveryError` (model, request-response)

**Analog:** same file — `PersistenceError` (lines 55-59)

```python
class PersistenceError(DomainError):
    """Raised when an infrastructure adapter cannot complete a persistence operation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
```

**Copy for MailDeliveryError:** subclass `DomainError` with a `message: str` constructor (same shape). Adapter maps `SMTPException` / `OSError` / `TimeoutError` → this type; use case catches `(MailDeliveryError, PersistenceError)` after publish (MAIL-04). Do **not** map SMTP solely to `PersistenceError`.

---

### `backend/src/backend/application/ports/mailer.py` (port, request-response)

**Analog:** itself (extend keyword-only Protocol)

**Current Protocol** (lines 8-23):
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
        body_html: str | None = None,
    ) -> dict[str, object]:
        """Return {delivery_status, recipient_count, issue_url} — stub always 'stubbed'.

        Optional ``body_html`` is additive (A4) so existing keyword callers stay valid.
        """
        ...
```

**Extend pattern:** add `recipients: Sequence[Recipient]` (default empty or required — update all call sites in same wave); docstring return keys become `{delivery_status, recipient_count (planned M), delivered_count (N), issue_url}` (+ optional `stop_reason`). Keep keyword-only; import `Recipient` from domain (no `Any`).

---

### `backend/src/backend/application/ports/profile_repository.py` (port, CRUD)

**Analog:** itself (lines 10-13)

```python
class ProfileRepository(Protocol):
    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser: ...

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser: ...
```

**Add:** `def list_digest_recipients(self) -> Sequence[Recipient]: ...` — typed return, no role filter in the port contract (D-01 filtering is adapter/use-case: all usable emails).

---

### `backend/src/backend/application/ports/digest_publisher.py` (port, CRUD)

**Analog:** itself — `claim_and_publish` (lines 26-47)

```python
class DigestPublisher(Protocol):
    def claim_and_publish(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
        period_label: str,
        title: str,
        material_ids: list[int] | None = None,
    ) -> DigestPublication:
```

**Extend pattern:** add keyword `recipient_count: int = 0` (planned M). Do **not** add `update_delivery` (D-06). `DigestPublication` already has `delivery_status` / `recipient_count` fields (lines 15-23) — leave batch post-send truth on API/`pings`, not publication DTO mutation after mail.

---

### `backend/src/backend/application/use_cases/send_digest.py` (service, request-response)

**Analog:** itself — orchestration + best-effort catch

**Result DTO** (lines 35-42) — extend with `delivered_count: int`:
```python
@dataclass(frozen=True)
class SendDigestResult:
    batch_id: int
    issue_number: int
    issue_url: str
    delivery_status: str
    recipient_count: int
    message: str
```

**Post-publish mail catch** (lines 176-189) — extend exception tuple + use mailer return:
```python
    try:
        mailer.send_digest(
            batch_id=publication.batch_id,
            issue_url=issue_url,
            subject=subject,
            body_text=body_text,
            recipient_count=publication.recipient_count,
            body_html=body_html,
        )
    except PersistenceError:
        logger.exception(
            "digest_send mail failed after publish batch_id=%s",
            publication.batch_id,
        )
```

**Target shape:** resolve `profiles.list_digest_recipients()` → `M` **before** claim; pass `recipient_count=M` into `claim_and_publish`; pass `recipients=` into mailer; `except (MailDeliveryError, PersistenceError)`; compose D-09/D-12 two-sentence `message`; expand `pings.record` payload with M/N/status/`stop_reason`.

**Inject profiles:** add `profiles: ProfileRepository` parameter (same style as existing ports — positional deps then keyword-only actor fields). Wiring already has `container.profiles` (`live.py` line 51 / `container.py` line 54).

**D-88 PRESERVE analog:** `tests/unit/test_send_digest.py` `test_send_audit_failure_after_publish_still_returns_success` (lines 369-390) — mirror for mail-raise after publish.

---

### `backend/src/backend/infrastructure/stub_mailer.py` (service, request-response)

**Analog:** itself

**Stub return** (lines 44-48) — amend to echo planned M + `delivered_count=0`:
```python
        return {
            "delivery_status": "stubbed",
            "recipient_count": 0,
            "issue_url": issue_url,
        }
```

**resolve_mailer fail-fast** (lines 67-77) — switch `RuntimeError` → `ConfigurationError`; accept full `Settings` (or SMTP primitives) when mode is `smtp`:
```python
def resolve_mailer(mailer_mode: str) -> StubMailer:
    mode = (mailer_mode or "stub").strip().lower() or "stub"
    if mode == "stub":
        return StubMailer()
    if mode == "smtp":
        raise RuntimeError(
            "SMTP не настроен, используйте stub (MAILER=stub). "
            "Live SMTP is deferred past Phase 5."
        )
    raise RuntimeError(f"Unknown MAILER={mode!r}; use stub")
```

**PRESERVE:** `StubMailer` class + `tests/unit/test_stub_mailer.py` stub behaviour; **AMEND** smtp resolve tests to expect `ConfigurationError` and success path when `SMTP_*` complete.

**Move real implementation:** replace placeholder `SmtpMailer` (lines 51-64) by importing from `smtp_mailer.py` or relocating class — keep public import path stable for tests that import `SmtpMailer` from `stub_mailer` **or** update imports in the same wave.

---

### `backend/src/backend/infrastructure/smtp_mailer.py` (service, request-response)

**Primary analog:** `stub_mailer.py` `StubMailer.send_digest` signature (lines 21-48) — same keyword surface + return dict keys.

**Error-mapping analog:** `backend/src/backend/infrastructure/local_notebook_storage.py` (lines 16-34) — catch low-level failures, raise domain errors, no SDK leakage:
```python
        if not candidate.is_file():
            raise NotebookNotAvailableError(path=raw)
        return candidate
```

**SDK-boundary map analog (list/select):** `supabase-integration/.../profile_repository.py` lines 57-60:
```python
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"profiles get_or_upsert failed: {exc}") from exc
```

**SmtpMailer specifics (no in-repo SMTP yet):**
- Constructor takes ready primitives from Settings (host, port, user, password, from_addr, tls_mode, connect_timeout, send_timeout) — **no `os.environ`** (MAIL-05).
- Per-recipient loop (D-05); consecutive-failure stop @ 3 with reset on success (D-08) — prefer adapter ownership (RESEARCH A2).
- Map `smtplib.SMTPException | OSError | TimeoutError` → `MailDeliveryError`.
- Inject SMTP factory in tests (Wave 0) — do not hit real network.

**RESEARCH stdlib sketch** (for planner; not an in-repo analog): `EmailMessage` + `SMTP.starttls` + `ssl.create_default_context` + one `To` per message.

---

### `backend/src/backend/composition/settings.py` (config, request-response)

**Analog:** itself — `from_env` + frozen dataclass (lines 13-64)

```python
@dataclass(frozen=True)
class Settings:
    ...
    mailer: str = "stub"
    site_url: str = "http://127.0.0.1:5173"

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        ...
        mailer = (env.get("MAILER") or "stub").strip().lower() or "stub"
```

**Add fields:** `smtp_host`, `smtp_port`, `smtp_user`, `smtp_pass`, `smtp_from`, optional `smtp_from_name`, `smtp_tls_mode` (default `starttls`); **timeouts as dataclass defaults** `smtp_connect_timeout=10.0`, `smtp_send_timeout=30.0` — not read from env (D-14). Never log `smtp_pass` in `__repr__` (add exclusion if Settings is logged).

---

### `backend/src/backend/composition/config_error.py` (config, request-response)

**Analog:** `ingestion-service/src/ingestion_service/composition/config_error.py` (lines 1-7) — verified tracked

```python
"""Startup configuration errors — not an IngestError stage (D-17)."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Settings or client factory misconfiguration before any video is processed."""
```

**Copy:** plain `Exception` subclass (not `DomainError`); docstring for digest SMTP / composition fail-fast. Raise from `resolve_mailer` / `build_live_container` when `MAILER=smtp` and required `SMTP_*` missing (D-16).

---

### `backend/src/backend/composition/live.py` (config, request-response)

**Analog:** itself — mailer + profiles wiring (lines 48-66)

```python
    return AppContainer(
        ...
        profiles=SupabaseProfileRepository(admin_client),
        ...
        mailer=resolve_mailer(settings.mailer),
        publisher=SupabaseDigestPublisher(admin_client),
    )
```

**Change:** `resolve_mailer(settings)` (full Settings → SmtpMailer primitives); keep `SupabaseProfileRepository(admin_client)` on **service_role** (Pitfall 7 — do not switch to user JWT client).

---

### `supabase-integration/.../profile_repository.py` (service, CRUD)

**Analog:** itself — select + PersistenceError map (lines 34-65)

```python
            existing = (
                self._client.table("profiles")
                .select("id,email,role,display_name")
                .eq("id", user_id)
                .execute()
            )
```

**Add `list_digest_recipients`:** `.table("profiles").select("id,email,display_name").execute()` (or email+display_name only); filter usable emails in Python (D-02 log exclude); map to `Recipient`; wrap SDK errors as `PersistenceError`. No new RLS / no role filter (D-01).

---

### `supabase-integration/.../digest_publisher.py` (service, CRUD)

**Analog:** itself — RPC params build (lines 54-71)

```python
        params: dict[str, Any] = {
            "p_batch_id": batch_id,
            "p_sent_at": _iso(sent_at),
            "p_period_label": period_label,
            "p_title": title,
        }
        if material_ids:
            params["p_material_ids"] = list(material_ids)
```

**Add:** when `recipient_count` kwarg provided, set `params["p_recipient_count"] = recipient_count`. Leave `p_delivery_status` default/`stubbed` (D-06 option i). No new migration.

---

### `backend/.../interface/http/routes/admin.py` (route, request-response)

**Analog:** itself — `SendDigestResponse` + handler (lines 136-144, 526-583)

```python
class SendDigestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    issue_number: int
    issue_url: str
    delivery_status: str
    recipient_count: int = 0
    message: str
```

**Add:** `delivered_count: int = 0`; map from `result.delivered_count`. Keep HTTP 200 on success path even when `delivery_status` is `partial`/`failed` (D-11) — do **not** map mail domain errors to 5xx here (use case already contains them). Pass `container.profiles` into `send_digest` when signature gains it. Auth stays `Depends(require_admin)`.

---

### `web/src/services/adminApi.js` (service, request-response)

**Analog:** itself — `sendDigest` JSDoc + mock (lines 665-721)

```javascript
 * @returns {Promise<{ batch_id: number, issue_number: number, issue_url: string, delivery_status: string, recipient_count: number, message: string }>}
 */
export async function sendDigest(accessToken, options = {}) {
  ...
      delivery_status: 'stubbed',
      recipient_count: 0,
      message: 'Отправка записана',
```

**Amend:** add `delivered_count` to typedef + mock; stub message example «Выпуск опубликован. Доставка писем: stub (0 из M)» when mock reports honesty (align with backend once message composition lands).

---

### `web/src/pages/AdminDigestPage.jsx` (component, request-response)

**Analog:** itself — banner from `result.message` (lines 437-442, 775-777)

```javascript
      const result = await sendDigest(undefined, { ... })
      setBanner(result.message || 'Отправка записана')
...
              {banner ? (
                <p className="mt-1 text-sm font-medium ..." role="status">
                  <span>{banner}</span>
```

**Minimal change:** banner already displays backend `message` — prefer composing honesty entirely on backend (D-09). Optional: show `delivered_count`/`recipient_count` only if product wants N/M outside `message`; default is message-only.

---

### `docs/agents/local-platform-runbook.md` (config)

**Analog:** itself — digest `SMTP_*` block (lines 138-144) + stub note (line 308)

```dotenv
SMTP_HOST="<corporate-relay-host>"
SMTP_PORT="<587-or-ops-chosen>"
SMTP_USER="<relay-user>"
SMTP_PASS="<relay-pass>"
SMTP_TLS_MODE="<starttls-or-ops-chosen>"
```

**Amend:** add `SMTP_FROM` (required for D-16); document Settings-fixed timeouts (10s/30s); default TLS `starttls`+587; keep GoTrue `GOTRUE_SMTP_*` lane separate; keep smoke/rollback; do not claim criterion-4 proof done.

---

### `backend/tests_support/in_memory.py` (test, CRUD)

**Analogs:** `InMemoryProfileRepository` (lines 299-328), `InMemoryDigestPublisher` (lines 519-598)

```python
class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CurrentUser] = {}
    ...
```

```python
    def __init__(..., *, delivery_status: str = "stubbed", recipient_count: int = 0) -> None:
        ...
        self._recipient_count = recipient_count

    def claim_and_publish(..., material_ids: list[int] | None = None) -> DigestPublication:
        ...
        return DigestPublication(
            ...
            recipient_count=self._recipient_count,
        )
```

**Add:** `list_digest_recipients` building `Recipient` from stored profiles (exclude empty/malformed); accept `recipient_count=` kwarg on `claim_and_publish` and stamp it into `DigestPublication` (override constructor default when caller passes planned M).

---

### `tests/unit/test_smtp_mailer.py` (test, request-response) — NEW

**Analog:** `tests/unit/test_stub_mailer.py` (structure: keyword `send_digest` calls, assert return dict, fail-fast resolve)

```python
def test_stub_mailer_returns_stubbed_delivery_and_zero_recipients() -> None:
    mailer = StubMailer()
    result = mailer.send_digest(
        batch_id=42,
        issue_url=issue_url,
        subject="Digest CDS — выпуск 7",
        body_text=body,
        recipient_count=0,
    )
    assert result["delivery_status"] == "stubbed"
```

**Cover:** exception → `MailDeliveryError`; per-recipient N; consecutive stop @ 3; success resets streak; TLS mode branches via injected SMTP factory. **PRESERVE** stub tests; replace `test_smtp_mailer_send_raises_not_implemented` when real adapter lands.

---

### `tests/unit/test_send_digest.py` (test, request-response) — AMEND

**Analog:** itself — D-88 audit test (lines 369-390)

```python
def test_send_audit_failure_after_publish_still_returns_success() -> None:
    """CR-02: after claim_and_publish succeeds, audit/mail errors must not fail the send."""
    ...
    assert result.message == "Отправка записана"
    assert issues.get_by_number(result.issue_number) is not None
```

**Add/amend:** mailer raises `MailDeliveryError` → still success + issue exists; audience M from profiles; `delivered_count`; stub message D-12; empty audience M=0 still publishes (D-04); ping payload honesty. Tripwire: `"stubbed"` asserts **AMEND**; audit-failure success **PRESERVE** (message string may change).

---

## Shared Patterns

### Ports & Adapters / composition-only wiring
**Source:** `backend/src/backend/composition/live.py` lines 28-67; `.cursor/rules/architecture.mdc`
**Apply to:** `SmtpMailer`, Settings, `resolve_mailer`, profile/publisher adapters
- Domain/use cases never import `smtplib` / `supabase` / `os.environ` for SMTP.
- Clients and mailer constructed only in composition.

### Domain error at adapter boundary
**Source:** `PersistenceError` in `errors.py`; notebook storage; Supabase profile repo
**Apply to:** `SmtpMailer`, `list_digest_recipients` adapter
```python
# Map transport/SDK → DomainError subclass; use case catches DomainError types only
```

### Best-effort after publish (D-88 / CR-02)
**Source:** `send_digest.py` lines 176-208; `test_send_audit_failure_after_publish_still_returns_success`
**Apply to:** mail + audit only; claim+publish failures still raise to HTTP layer
```python
try:
    ...
except PersistenceError:
    logger.exception(...)
# extend: except (MailDeliveryError, PersistenceError)
```

### Keyword-only Protocol evolution
**Source:** `mailer.py` `body_html` additive comment; `digest_publisher` `material_ids`
**Apply to:** `recipients`, `recipient_count` on claim, `delivered_count` on result/response
- Prefer additive kwargs; update StubMailer + in-memory + all call sites in same red/green.

### Admin HTTP response mapping
**Source:** `admin.py` `post_shortlist_send` + `SendDigestResponse`
**Apply to:** `delivered_count` field only; keep `require_admin`; keep 200 after successful use-case return

### SPA service boundary
**Source:** `web/src/services/adminApi.js` → `AdminDigestPage.jsx`
**Apply to:** contract fields only through `adminApi`; UI shows `result.message`

### Fail-fast incomplete SMTP (D-16)
**Source today:** `resolve_mailer` RuntimeError in `stub_mailer.py`
**Target:** `ConfigurationError` from ingestion analog; amend `test_stub_mailer.py` / `test_live_container_wiring.py`

### TDD tripwires
**PRESERVE:** stub mailer honesty tests; audit-failure-after-publish success
**AMEND:** `"stubbed"` / message / `recipient_count: 0` asserts once honesty lands; resolve smtp fail-fast exception type

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none blocking)* | — | — | Real SMTP transport has no prior implementation; use `StubMailer` signature + `LocalNotebookStorage`/`PersistenceError` boundary mapping + RESEARCH stdlib sketch. Closest role-match listed above for `smtp_mailer.py`. |

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application,infrastructure,composition,interface,tests_support}`, `supabase-integration/src/supabase_integration`, `web/src/{services,pages}`, `tests/unit`, `ingestion-service/.../config_error.py`, `docs/agents`
**Files scanned:** ~188 tracked paths under backend/supabase/tests/web services (git ls-files sample); focused reads on 15 primary analogs
**Tracked-source gate:** all named analogs verified via `git ls-files` (non-empty)
**Pattern extraction date:** 2026-10-16
