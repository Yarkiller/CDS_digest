# Architecture Research

**Domain:** Digest CDS v1.3 — Live SMTP mail, scheduled ingestion & backlog debt (integration architecture on a shipped app)
**Researched:** 2026-10-14
**Confidence:** HIGH for integration points / NEW-vs-MODIFIED / build order (every boundary below was read from the live codebase and the mandatory `.cursor/rules/architecture.mdc` + `AGENTS.md`). MEDIUM for third-party particulars (SMTP relay API, YouTube Data API v3 listing semantics) — no vendor doc pass was run this session; verify in the phase's spike.

> **Scope note.** This is a *subsequent* milestone. The v1.1 architecture research (dual-hexagon, shared DB) is already shipped and is **not re-litigated** here. This document covers the **integration points, NEW components and data-flow changes** for the six v1.3 features, and flags anything that would violate the inward-dependency rule.

---

## Standard Architecture (existing — preserve, do not replace)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ web/ (Vite+React)  — UI only; all API calls via web/src/services/*            │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ HTTPS (Bearer JWT)
┌───────────────────────────────▼──────────────────────────────────────────────┐
│ backend/ (FastAPI)                                                            │
│   interface/http/routes/*      ← thin adapters (auth gate, DTO mapping)       │
│   application/use_cases/*      ← orchestration; depends only on ports+domain  │
│   application/ports/*          ← typing.Protocol contracts                    │
│   domain/*                     ← entities, errors; ZERO fastapi/httpx/supabase│
│   infrastructure/*             ← local adapters (stub_mailer, yaml validator) │
│   composition/{container,live}.py ← THE ONLY wiring root                      │
└───────────────┬───────────────────────────────────┬──────────────────────────┘
                │ ports                             │ ports
      ┌─────────▼─────────┐              ┌──────────▼───────────┐
      │ supabase-integration │            │ data-collection       │
      │ PostgREST/SQL adapters,│          │ external API ports +  │
      │ migrations, RLS        │          │ DTOs + adapters       │
      └─────────┬─────────────┘          └──────────┬───────────┘
                │                                     │
      ┌─────────▼─────────┐              ┌──────────▼───────────┐
      │ Supabase/Postgres │              │ ingestion-service/    │
      │ (shared DB)       │◄─────────────│ Typer CLI + own       │
      └───────────────────┘  service_role│ composition           │
                                         └──────────────────────┘
```

**Invariants that v1.3 must not break**

1. Dependencies point inward: Infrastructure → Application → Domain. `domain/` and `application/use_cases/` import **no** `fastapi`, `httpx`, `supabase`, `yaml`, `smtplib`, or SQL.
2. Ports are `typing.Protocol` (or `abc.ABC`) with explicit types — **no `Any`** at module boundaries.
3. Wiring happens **only** in `backend/composition/` (`container.py`, `live.py`) and, for the second deployable, in `ingestion-service/src/ingestion_service/composition/`.
4. SDK/HTTP/SQL errors are mapped to domain errors **at the adapter boundary** (`backend/domain/errors.py`, `data_collection/errors/*`, `ingestion_service/adapters/persist_errors.py`).
5. Frontend talks to the API only through `web/src/services/*`; UI never learns Supabase/backend internals.
6. TDD Red–Green–Refactor is mandatory: failing test first, minimal production code, full suite, then refactor.

### Composition root today (read from code)

- `backend/composition/container.py` — `AppContainer` dataclass + `build_in_memory_container`.
- `backend/composition/live.py` — `build_live_container(settings)`; the **only** place `create_service_role_client`, `resolve_mailer`, `YamlPipelineConfigValidator` and the Supabase adapters are constructed.
- `backend/composition/settings.py` — frozen `Settings.from_env()`; `mailer`, `site_url`, Supabase/JWT/email-domain config.
- Mailer wiring today: `mailer=resolve_mailer(settings.mailer)`; `MAILER=smtp` **fail-fast** at startup (`stub_mailer.SmtpMailer.send_digest` → `NotImplementedError`, `resolve_mailer` raises).

---

## Feature → layer map (integration summary)

| # | Feature | Layers touched | NEW | MODIFIED |
|---|---------|----------------|-----|----------|
| 999.7 | YAML merge-key acceptance | `backend/infrastructure`, `backend/tests` | — | `yaml_pipeline_config_validator._StrictSafeLoader` |
| 999.1 | Reader-route honesty for draft | `backend/application/use_cases`, `backend/interface/http/routes`, `web/src` | new preview use case + admin route + FE page/link | `AdminDigestPage` link, `App.jsx` routes |
| 999.6 | Unsaved-changes guard | `web/src` only | router guard hook/component | `AdminPipelineConfigPage.jsx` |
| MAIL-02 | Signup confirmation mail | **Supabase Auth (GoTrue) config + ops** (no app port) | runbook update; optional SPA error copy | `RegisterPage`/`authApi` error mapping (optional) |
| MAIL-01 | Live SMTP digest | `backend/application/ports`, `backend/infrastructure`, `backend/composition`, `supabase-integration` | `SmtpMailer` (real), `Recipient` DTO, recipients port method + adapter | `Mailer` port signature, `send_digest` use case, `SupabaseDigestPublisher`, `Settings`, `resolve_mailer` |
| Scheduled ingestion | cron/systemd timer + playlist listing | `data-collection` (new port/DTO/adapter), `ingestion-service` (use case + CLI subcommand), **ops** (systemd/cron) | playlist lister port/DTO/adapter, `run_playlist_ingest`, CLI subcommand, unit file | `ingestion-service` Settings + composition, CLI |

---

## (a) Real SMTP mailer adapter + MAIL-02 signup mail

### Where the SMTP adapter belongs

**`backend/src/backend/infrastructure/smtp_mailer.py`** — a *local* adapter owned by `backend`.

Rationale (from `architecture.mdc` module table):
- `data-collection` is for **external API adapters → domain DTOs** (YouTube, FoundryModels). An SMTP relay is not a content-collection API and produces no domain DTO.
- `supabase-integration` owns the DB adapter only. SMTP is not Supabase.
- The existing `SmtpMailer` placeholder already lives in `backend/infrastructure/stub_mailer.py`; replace/expand it there (or split into `smtp_mailer.py` and re-export from `stub_mailer.py` to keep current imports stable).

It is wired **only** in `composition/live.py` through `resolve_mailer(settings)`; `SMTP_*` config is parsed **only** in `composition/settings.py`. The adapter receives ready primitives (host/port/user/password/from/tls) — it must **not** read `os.environ` (same rule as the ingestion adapters, D-17).

### Port change needed

The current port is insufficient for real delivery — it carries `recipient_count` but **no recipient addresses**, so the adapter cannot know where to send.

```python
# backend/src/backend/application/ports/mailer.py  (MODIFIED)
class Mailer(Protocol):
    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipients: Sequence[str] | Sequence[Recipient],   # NEW
        recipient_count: int,                               # keep (planned audience size)
        body_html: str | None = None,
    ) -> dict[str, object]: ...   # {delivery_status, recipient_count, issue_url}
```

Notes:
- Keep `recipient_count` as keyword-only and additive-friendly so `StubMailer` callers don't silently change meaning; `StubMailer` keeps returning `delivery_status="stubbed"`.
- Prefer passing explicit `Recipient` objects (see (b)) rather than bare strings, so `display_name` is available for a future personalised greeting without a second port change. If bare emails are chosen, document it as a deliberate YAGNI.
- `delivery_status` gains a real value (`sent`); the existing `stubbed` value stays for `MAILER=stub`. `resolve_mailer` stops failing fast once SMTP config is present and instead raises a clear `ConfigurationError` when `MAILER=smtp` but `SMTP_*` is incomplete (keep fail-fast for misconfiguration — honesty over silent stub).

### MAIL-02: reuse the port, add a method, or a new port? → **None of the three**

The signup confirmation mail is **not sent by the application at all**. It is sent by **Supabase Auth (GoTrue)** during `supabase.auth.signUp(...)` from `web/src/services/authApi.js`. Evidence, already recorded in-repo:

- `.planning/debug/g-01-3b-signup-mailer.md`: `POST /auth/v1/signup` → `{"code":500,"error_code":"unexpected_failure","msg":"Error sending confirmation email"}`.
- `docs/agents/local-platform-runbook.md` §4.1: GoTrue had `mailer_autoconfirm=false` and a broken SMTP path; the Phase 1 unblock was enabling **autoconfirm**, with SMTP left as an **ops ticket**.

Architectural consequences:
1. **Do not** add `send_signup_confirmation` to `Mailer`. The `Mailer` port models *application-initiated digest broadcast*; adding an Auth-flow method would put GoTrue's concern into our domain and force a fake SMTP send in the backend that never happens.
2. **Do not** create a second port for it either. There is no application code path to put behind a port.
3. The fix is **deployment configuration**, not a domain/use-case change:
   - Configure the SMTP relay for **GoTrue** (`GOTRUE_SMTP_HOST/PORT/USER/PASS/SENDER_*`, TLS) on the self-hosted Supabase VM / Compose env, restart Auth.
   - Decide the product contract: keep `mailer_autoconfirm=true` (current state — registration works without email) **or** re-enable confirmation once the relay is healthy. This is an operator/ADR decision, not application code.
4. The only *application* work that can accompany MAIL-02 is **honesty in error mapping**: `authApi.signUp` currently maps the GoTrue 500 to the generic retryable «Сервис входа временно недоступен» NETWORK copy (see `authApi.js` / `RegisterPage.jsx`). If confirmation mail is re-enabled, map confirmation-mailer failures to explicit Russian copy. This is a `web/src/services` + page change, no backend port.

> **Future seam (not v1.3):** if the backend ever has to send its own *transactional* mail (e.g. password-reset initiated server-side), introduce a separate **`TransactionalMailer`** port. Do not overload `Mailer`. Flag it in the phase notes, ship nothing.

### How it stays out of domain/use-cases

- The use case depends on the `Mailer` **Protocol** only; `smtplib`/`email.message` imports live exclusively in the infrastructure adapter.
- `send_digest` continues to call `mailer.send_digest(...)` and treat failures as best-effort after publish (CR-02, existing behavior).
- Config is read in `Settings.from_env()`; the adapter is constructed in `composition`. No `os.environ` in use case or adapter.

---

## (b) Recipients from `profiles` + honest `recipient_count`

### Current state (read from code)

- Port: `backend/src/backend/application/ports/profile_repository.py` — `get_or_upsert`, `set_display_name` only.
- Adapter: `supabase-integration/src/supabase_integration/profile_repository.py` — reads/writes `public.profiles` (`id,email,role,display_name`) via an injected client.
- The digest send path never resolves recipients: `send_digest` passes no recipients, and `SupabaseDigestPublisher.claim_and_publish(...)` **omits** `p_recipient_count`, so migration 005/006's `p_recipient_count int default 0` stamps **0** and returns `recipient_count=0` (`digest_publisher.py` line ~69-71).
- `ShortlistItem`/`DigestPublication` carry the count through to `SendDigestResponse.recipient_count`.

### Which layer resolves recipients → **application use case, via a port**

Audience policy ("who receives the weekly digest") is a business rule, so it belongs in the **application** layer, expressed against a port. Two acceptable shapes:

**Option A (recommended) — extend `ProfileRepository`:**

```python
# backend/src/backend/application/ports/profile_repository.py  (MODIFIED)
class ProfileRepository(Protocol):
    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser: ...
    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser: ...
    def list_digest_recipients(self) -> tuple[Recipient, ...]: ...   # NEW
```

- `Recipient` = new frozen dataclass in `backend/domain/recipient.py` (`email: str`, `display_name: str | None = None`, `role: str | None = None`) — explicit type, no `Any`.
- Adapter addition in `supabase-integration/profile_repository.py`: `select("email,display_name,role")` on `profiles`, `.execute()`, map rows → `Recipient`; map SDK failure → `PersistenceError` at the boundary (already the file's pattern).
- Pros: `profiles` is already the source of truth and already wired in both `build_in_memory_container` and `build_live_container` — **no new wiring slot, no new fake**.
- Cons: `ProfileRepository` grows past its original "upsert on /me" charter.

**Option B — a dedicated `RecipientDirectory` port** (`application/ports/recipient_directory.py`) implemented by the same Supabase adapter (or a new one). Cleaner single-responsibility, but adds a new `AppContainer` field, a new in-memory fake, and new wiring in **both** composition roots.

**Recommendation: Option A** for v1.3 (least surface; the audience is literally the profiles table). If `ProfileRepository` later accumulates more audience concerns, split to Option B.

### Who owns the count → **the use case**, then persisted by the RPC

Two-layer honesty:

1. **Planned audience (use case).** `send_digest` calls `profiles.list_digest_recipients()` → `recipients`, `recipient_count = len(recipients)`. It passes `recipient_count` into `publisher.claim_and_publish(...)`; the adapter forwards `p_recipient_count` to the RPC (new param usage). The RPC already persists and returns it — **no migration required** for the count itself (the parameter exists in 005/006).
   - The RPC must **not** compute the count from `profiles`: doing so would put audience policy into SQL and couple the claim transaction to `profiles`, violating the inward rule and the "no SQL business logic" intent. The RPC is a **persistence** of a value the application decided.
2. **Actual delivery (mailer).** `Mailer.send_digest` returns `{delivery_status, recipient_count}`. For live SMTP, `delivery_status="sent"` and the adapter reports how many addresses it accepted. The use case should surface the **mailer's** returned count once the send attempt completes, so the API response reflects delivery rather than intent.
   - **Honesty tension to resolve in-phase:** today the RPC stamps `delivery_status`/`recipient_count` **at publish time, before mail** (CR-02: mail is best-effort and must not fail the send). After a real SMTP send this can leave a stored count that overstates delivery. Options:
     - **(i) Minimal (recommended for v1.3):** `recipient_count` = planned audience size; `delivery_status` = `stubbed`/`sent`/`failed`. Document that `recipient_count` is the **audience size targeted**, not a per-message delivery receipt; store any partial-failure detail in the `digest_send` activity event payload (`pings.record`) which the use case already writes.
     - **(ii) Fully honest delivery (defer unless partial failures matter):** add a port method `DigestPublisher.update_delivery(batch_id, *, delivery_status, recipient_count)` (new adapter method → `update digest_shortlist_batches`), called after mail. Costs a port change + adapter + test. Only worth it if ops needs per-run delivery truth beyond the activity event.
   - Do **not** invent a count. If recipients resolve to zero, that is a real `recipient_count=0` + `delivery_status` that says so — never silently stamp the audience as delivered.

### Data-flow change (MAIL-01)

```
Before (today):
  send_digest → claim_and_publish(no count) → RPC stamps recipient_count=0
              → mailer.send_digest(recipient_count=0, recipients=none) → StubMailer logs

After (v1.3):
  send_digest
    ├─ profiles.list_digest_recipients() ──► Recipient[]  (application decides audience)
    ├─ recipient_count = len(recipients)
    ├─ claim_and_publish(..., recipient_count=N) ──► RPC stamps N (unchanged SQL body)
    ├─ mailer.send_digest(recipients=Recipient[], recipient_count=N, ...) ──► SmtpMailer (live)
    │        └─ returns {delivery_status: "sent"|"failed", recipient_count: M}
    └─ pings.record(digest_send, {audience: N, delivered: M, delivery_status})  (audit honesty)
```

### Open decision for the phase

- **Who is a recipient?** All `profiles`, or only non-admin roles? There is **no `email_confirmed` column** in `profiles` (migration 001 has `id,email,role,display_name`, default role `employee`), so confirmation state cannot be filtered without a schema change. Recommend: define the predicate once in the domain (e.g. a `is_digest_recipient(role) -> bool`) so it is unit-testable and changeable in one place; ship "all profiles" for v1.3 unless product says otherwise.

---

## (c) Reader-route honesty for draft materials (999.1)

### Current state (read from code)

- `backend/interface/http/routes/materials.py` → `GET /materials/{slug}` requires Bearer JWT and calls `get_material_for_reader`.
- `backend/application/use_cases/get_material_for_reader.py` → `repo.get_by_slug(slug)`, and if `status != READY` raises `MaterialNotFoundError` → route returns **404 `material_not_found`**.
- The admin shortlist row links to `/materials/{slug}` unconditionally (`web/src/pages/AdminDigestPage.jsx` ~line 994 «Открыть материал →»), including for `status=draft` rows → the reader route 404s → the SPA renders «Материал не найден».
- Email preview links (`email_render.py`, `preview_digest_email.py`) also point at `/materials/{slug}`, but preview/send pools are **approved∩ready**, so those links are already correct.

### Recommended shape → **NEW admin-only route; keep the public route ready-only**

- **New** `GET /admin/materials/{slug}` in `backend/interface/http/routes/admin.py`, gated by `Depends(require_admin)` (existing dependency, authorization from `profiles.role` — D-74). Returns a **draft-or-ready** material for preview.
- **Keep** `GET /materials/{slug}` exactly as-is: ready-only, authenticated reader path, drafts never leak. This is the "keeping drafts out of the public reader path" half of the requirement and is the safer default.

Rejected alternatives:
- Making `GET /materials/{slug}` draft-aware for admins relies on a role branch inside a public route; a regression in that branch leaks unpublished content. Higher risk for no benefit.
- A `?preview=1` query flag on the reader route has the same leak risk and muddies the reader contract.

### Where the visibility decision belongs

| Decision | Layer | Why |
|----------|-------|-----|
| **Who** may preview (admin vs any authenticated user) | **Interface layer** (`require_admin` dependency) | Authentication/authorization wiring is an HTTP-edge concern; the use case should receive a resolved actor, not a token. |
| **What** is visible (ready for reader; draft+ready for preview) | **Application use case** | A visibility rule is business logic; it must be testable with fakes and free of FastAPI. |
| Does a `Material` *have* a publishable/visible state? | **Domain** (existing `MaterialStatus`) | No new domain rule needed; optionally add a tiny predicate, but the existing enum is sufficient. |

Concretely: add `backend/application/use_cases/get_material_for_preview.py`:

```python
def get_material_for_preview(repo: MaterialRepository, slug: str) -> Material:
    material = repo.get_by_slug(slug)
    if material is None:
        raise MaterialNotFoundError(slug)
    return material          # draft OR ready — no status filter
```

`get_material_for_reader` is unchanged (still ready-only). The two use cases read the same port, so no repository change is needed.

### Frontend integration (999.1)

- **NEW** admin preview page (or reuse `MaterialPage` with an `adminPreview` prop) routed at e.g. `/admin/materials/:slug` in `web/src/App.jsx`.
- **MODIFIED** `web/src/pages/AdminDigestPage.jsx` «Открыть материал →» → `/admin/materials/${slug}`; add a banner indicating draft state.
- **NEW/MODIFIED** transport in `web/src/services/adminApi.js` (`fetchAdminMaterial(slug)` → `GET /admin/materials/{slug}`), keeping the `services/` boundary — the page must not call `fetch` directly.
- Reader-facing links (`IssueToc`, `MaterialListRow`, knowledge results, email HTML) stay on `/materials/{slug}` — all point at ready materials.

---

## (d) Scheduler — where it belongs, and the testable seam

### The scheduler is **infrastructure outside the app**, not a module/port

cron / systemd timer on the VM invoking the `ingest` CLI is the right shape and needs **no application daemon and no new port for "the scheduler"**. Introducing an in-app scheduler (APScheduler/Celery/queue consumer) would add a runtime, a process supervisor, and new domain concepts for zero v1.3 value, and would contradict the shipped "ingestion-service is a thin one-shot CLI" boundary.

### But listing a channel/playlist *is* application work

The timer cannot run `ingest <url>` per video unless something **enumerates video ids** from a channel/playlist. That enumeration is a real capability and must be a first-class, testable artifact:

1. **`data-collection`** — new listing port + adapter + DTO (see (e)).
2. **`ingestion-service`** — new orchestration use case `run_playlist_ingest(source, template, *, lister, ...pipeline deps)` that lists ids then loops the **existing** `run_ingest_pipeline` per id; plus a new Typer subcommand (e.g. `ingest-playlist` / `ingest-source`) in `cli.py`, wired through `build_ingest_deps()`.
3. **Ops** — a systemd `.service` + `.timer` (or crontab entry) that calls the new subcommand with env from an EnvironmentFile; logs to journald; plus a runbook section.

### Testable seam (satisfies the TDD rule)

- **Unit seam:** `run_playlist_ingest` takes injected `lister` + the same ports `run_ingest_pipeline` already takes; test with fakes — assert it lists N ids, calls the pipeline N times, and surfaces per-video failures without aborting the batch (partial success) or with an explicit policy.
- **CLI seam:** the repo already monkeypatches `build_ingest_deps()` in `CliRunner` tests (see `cli.py` docstring). Add a test that `ingest-playlist` calls the fakes and prints a summary; keep stdout JSON/exit-code contracts.
- **Idempotency seam:** `persist_draft_and_enqueue` (migrations 007–009) returns `already_saved` for a re-scanned video; **lock it with a test** that a second playlist scan produces no duplicate `materials` rows and reports `already_saved`. This is a stated v1.3 risk.
- **Scheduler itself** is not unit-tested as Python; validate via a smoke runbook step (`systemd-analyze verify`, a manual `systemctl start` against a small test playlist) and, if desired, a tiny shell-level test invoking the CLI entrypoint.

### No code change required? — **No, not strictly**

- If the operator is willing to hardcode/rotate video URLs in the timer, the mechanism needs no code. But v1.3 explicitly scopes "YouTube channel/playlist source", so listing **is** required → the port + use case + subcommand above are the actual work; cron/systemd is the last, thin step.
- **New external dependency & ADR gate:** listing needs **YouTube Data API v3 + an API key** — a public external API. Per `.planning/PROJECT.md` and ADR-0002 (contour isolation), this must be settled in a **spike/ADR before the scheduler phase can pass**. Architecturally the key is: composition-only (`ingestion_service/composition/clients.py` builds the client; the adapter takes an injected client, mirroring `YouTubeOEmbedAdapter`), never `os.environ` inside the adapter, never in `web/`.

---

## (e) YouTube playlist listing in `data-collection` — yes, new port + adapter + DTO

**Yes.** It is an external-API adapter producing a domain DTO, exactly like the existing `TranscriptProvider` / `VideoMetadataProvider`. Keeping it in `data-collection` is what makes the eventual FoundryModels/other-source swap behind the same port.

### Port (NEW)

```python
# data-collection/src/data_collection/ports/video_lister.py
class VideoLister(Protocol):
    async def list_videos(self, source: str) -> tuple[VideoRef, ...]: ...
```

- `source: str` = a playlist URL/ID or channel URL/ID (parse/validate in the adapter, mapping bad input to a domain error).
- Return explicit `VideoRef` DTOs (not bare ids) so title/position can be logged without a second call; the pipeline only needs `video_id`.

### DTO (NEW)

```python
# data-collection/src/data_collection/dto/video_listing.py
@dataclass(frozen=True)
class VideoRef:
    video_id: str
    position: int
    title: str | None = None

@dataclass(frozen=True)
class VideoListing:
    source_id: str
    video_refs: tuple[VideoRef, ...]
    next_page_token: str | None = None   # None => fully enumerated
```

- Keep it minimal and immutable; the adapter **paginates internally and returns a complete listing** (or surfaces `next_page_token` and the use case loops — choose one and document it). Recommendation: adapter paginates to completion for a bounded playlist and caps/guard-rails runaway channels (max items, page limit) to avoid quota blowups.
- Only `video_id` feeds `run_ingest_pipeline` (which re-validates via `extract_video_id`), so the listing DTO never needs to become a `MaterialDraft`.

### Error taxonomy (NEW)

`data-collection/src/data_collection/errors/listing.py` — a `ListingError` base with closed `reason`s mapped at the adapter boundary, mirroring `errors/captions.py` / `errors/metadata.py`:
`quota_exceeded`, `key_invalid`, `not_found`, `network`, `invalid_response`. Never let `googleapiclient`/`httpx` exceptions escape the adapter.

### Public-surface decision (flag)

`data_collection.__all__` is deliberately a **controlled public set** (currently 7 names: `Transcript`, `VideoMetadata`, `MaterialDraft`, `TemplateKind`, `TranscriptProvider`, `ArticleGenerator`, `VideoMetadataProvider`; a prior decision kept it at seven and negative-rooted new symbols). Adding `VideoLister` + `VideoListing`/`VideoRef` is therefore a **deliberate public-surface expansion** — call it out as an explicit decision in the phase (and extend `error/` exports consistently).

### API key & composition

- `ingestion_service/composition/settings.py`: add `youtube_api_key: str | None` (repr-hidden, like `deepseek_api_key`).
- `ingestion_service/composition/clients.py`: `build_youtube_video_lister(settings)` constructs the HTTP client / API-key-bearing client with proxy support, and injects it into the adapter — same shape as `build_youtube_metadata_provider`.
- Adapter: `data_collection/adapters/youtube_data_api.py` (or `youtube_playlist.py`), takes the injected client only.

---

## Integration Points

### External services

| Service | Integration pattern | Notes |
|---------|---------------------|-------|
| SMTP relay (digest) | `SmtpMailer` in `backend/infrastructure`, wired in `composition/live.py`; `SMTP_*` in `Settings` | Relay not chosen yet (PROJECT.md). Adapter takes ready credentials; no `os.environ` in adapter. `MAILER=stub` remains the default and the honest fallback. |
| SMTP relay (GoTrue signup mail) | **Supabase Auth/GoTrue env** on the Supabase VM (`GOTRUE_SMTP_*`), not application code | MAIL-02. Currently `mailer_autoconfirm=true` (runbook §4.1). No app port. |
| YouTube Data API v3 (playlist/channel listing) | New `VideoLister` adapter in `data-collection`, key in `ingestion-service` composition | New public external dependency → **ADR/spike required** against ADR-0002 before the scheduler phase passes. |
| YouTube oEmbed / captions | Existing `data-collection` adapters (unchanged) | Reused by scheduled ingestion via the existing pipeline. |
| Supabase PostgREST | `create_service_role_client` (unchanged) | Recipients read + RPC count param; service_role bypasses RLS. |

### Internal boundaries

| Boundary | Communication | Considerations |
|----------|---------------|----------------|
| `web` ↔ `backend` | REST via `web/src/services/*` | New admin preview endpoint joins `adminApi.js`; UI unchanged for readers. |
| `backend` use case ↔ `Mailer` | Protocol only | Signature change is the single behavioural contract change; all callers are keyword-only. |
| `backend` use case ↔ `ProfileRepository` | Protocol only | New `list_digest_recipients` method; two fakes to update (in-memory + tests). |
| `backend` use case ↔ `DigestPublisher` | Protocol only | Pass `recipient_count`; optional `update_delivery` only under option (ii). |
| `ingestion-service` ↔ `data-collection` | Package public API | New `VideoLister` + listing DTOs; adapter holds the SDK. |
| `ingestion-service` ↔ Supabase | Existing `PersistPort`/RPC | Scheduled runs reuse `already_saved` idempotency (migration 009). |
| `ingestion-service` ↔ `backend` | **None** (locked) | Scheduler must not call the HTTP API. |
| cron/systemd ↔ CLI | Process invocation + env file | Ops, not code. Logs to journald; exit codes unchanged. |

---

## NEW vs MODIFIED (explicit master list)

### NEW artifacts

| Artifact | Module | Purpose |
|----------|--------|---------|
| `backend/src/backend/domain/recipient.py` | backend/domain | `Recipient` DTO (email, display_name, role) |
| `backend/src/backend/infrastructure/smtp_mailer.py` | backend/infrastructure | Real `SmtpMailer` (replaces the NotImplementedError placeholder) |
| `backend/src/backend/application/use_cases/get_material_for_preview.py` | backend/application | Draft-or-ready reader for admin preview |
| `GET /admin/materials/{slug}` route (in `routes/admin.py`) | backend/interface | Admin-only preview endpoint |
| `web/src/pages/admin/AdminMaterialPreviewPage.jsx` (or a `MaterialPage` preview mode) + `/admin/materials/:slug` route | web | Renders draft preview honestly |
| router guard hook/component (`web/src/components/`) for 999.6 | web | `useBlocker`-based in-app navigation guard |
| `data-collection/.../ports/video_lister.py` | data-collection | `VideoLister` Protocol |
| `data-collection/.../dto/video_listing.py` | data-collection | `VideoRef` / `VideoListing` |
| `data-collection/.../adapters/youtube_data_api.py` | data-collection | Listing adapter (injected client) |
| `data-collection/.../errors/listing.py` | data-collection | `ListingError` taxonomy |
| `ingestion_service/application/use_cases/ingest_playlist.py` | ingestion-service | List → loop existing pipeline |
| `ingest-playlist` subcommand in `cli.py` + `build_ingest_deps` wiring | ingestion-service | Scheduled entrypoint |
| systemd `.service`/`.timer` (or crontab) + runbook section | ops / docs | Timer driving the CLI |
| ADR for YouTube Data API v3 key (contour) | docs/adr | Gate for the scheduler phase |

### MODIFIED artifacts

| Artifact | Change |
|----------|--------|
| `backend/.../ports/mailer.py` | add `recipients` param; clarify `delivery_status` values |
| `backend/.../infrastructure/stub_mailer.py` | keep `StubMailer` honest; replace/route the placeholder; `resolve_mailer` validates `SMTP_*` |
| `backend/.../application/use_cases/send_digest.py` | resolve recipients → count → pass to publisher + mailer; surface mailer-reported count/status |
| `backend/.../application/ports/profile_repository.py` | add `list_digest_recipients()` |
| `supabase-integration/.../profile_repository.py` | implement `list_digest_recipients()`; boundary error mapping |
| `backend/.../application/ports/digest_publisher.py` (+ `supabase-integration/digest_publisher.py`) | accept and forward `recipient_count` → `p_recipient_count` (optional `update_delivery` under option ii) |
| `backend/.../composition/settings.py` | add `SMTP_*` fields |
| `backend/.../composition/live.py` + `container.py` + `tests_support/in_memory.py` | wire real mailer + recipients; update fakes |
| `backend/.../infrastructure/yaml_pipeline_config_validator.py` | 999.7: `flatten_mapping` (or pre-resolve merge keys) **before** duplicate-key detection |
| `web/src/pages/AdminDigestPage.jsx` | link to `/admin/materials/{slug}` for drafts |
| `web/src/pages/AdminPipelineConfigPage.jsx` | 999.6: fix `beforeunload` + add router guard |
| `web/src/services/adminApi.js` | add `fetchAdminMaterial(slug)` |
| `ingestion-service/.../composition/settings.py` + `clients.py` | `youtube_api_key` + `build_youtube_video_lister` |
| `data-collection/.../__init__.py` | deliberately extend `__all__` with listing port/DTO |
| `.planning/...` / `docs/agents/local-platform-runbook.md` | MAIL-02 SMTP/autoconfirm contract; timer runbook |

---

## Data-flow changes (summary)

1. **Digest send:** recipients now resolved from `profiles` (application) → planned count flows into the claim RPC (persistence) → mailer receives real addresses → delivery status/count reported back; audit event records audience vs delivered.
2. **Draft preview:** admin shortlist link → `GET /admin/materials/{slug}` (admin auth) → `get_material_for_preview` (no status filter) → SPA admin preview page. Public `/materials/{slug}` flow is untouched.
3. **Scheduled ingestion:** timer → `ingest-playlist <source>` → `VideoLister` (data-collection) enumerates ids → `run_ingest_pipeline` per id (existing) → `persist_draft_and_enqueue` (`already_saved` idempotency) → drafts + shortlist rows in the shared DB → admin triages in `/admin/digest`. No HTTP API, no auto-ready, no auto-send.
4. **Signup mail:** SPA `supabase.auth.signUp` → GoTrue → SMTP relay configured in Supabase env. No backend data flow; only SPA error copy may change.
5. **YAML validation:** PUT `/admin/pipeline/config` → validator (merge-key fixed) → persists behind `PipelineConfigRepository`. Unchanged flow, corrected parser behaviour.

---

## Suggested build order (dependency-aware)

**Track A — backlog debt (milestone scope says "backlog first")**

1. **999.7 YAML merge-key** — isolated to one infrastructure class + tests. No cross-module deps; do it first.
2. **999.1 reader-route honesty** — application use case → route → FE link/route. Depends on nothing new.
3. **999.6 unsaved-changes guard** — FE only. Independent; can run in parallel with 1–2.

**Track B — mail**

4. **Settle the SMTP relay + `SMTP_*` contract (ops)** — shared external dependency for both MAIL-02 and MAIL-01; unblocks everything else in this track.
5. **MAIL-02** — configure GoTrue SMTP / decide autoconfirm contract; optional SPA error-copy honesty. No ports.
6. **MAIL-01a recipients + honest count** — `Recipient` DTO → `list_digest_recipients` port + adapter + fake → `send_digest` passes count → adapter forwards `p_recipient_count`. Ship this **without** live SMTP first: it makes `recipient_count` honest with the stub, and is independently testable.
7. **MAIL-01b real `SmtpMailer`** — port signature change → adapter (red/green on the port) → `Settings`/`resolve_mailer`/composition → live smoke. Depends on 4 and 6.

**Track C — scheduled ingestion**

8. **Playlist listing contract** — `data-collection` DTO + port + error taxonomy (+ `__all__` decision). Tests with an injected fake client.
9. **Playlist adapter** — YouTube Data API v3 adapter against the port; error mapping; ADR/spike for the API key (gate).
10. **Playlist orchestration + CLI subcommand** — `run_playlist_ingest` + `ingest-playlist`; unit tests with fakes; **idempotency test** for re-scans (`already_saved`).
11. **Ops** — systemd timer + env file + runbook smoke; verify exit codes/logs.
12. **UAT** — unattended run produces drafts + shortlist rows only; no auto-ready/auto-send.

**Rationale:** debt first (cheap, unblocks nothing but burns down risk); mail ordered so *honesty* (recipients/count) lands before *delivery* (SMTP), which is testable with the stub; ingestion last because it carries the only new external dependency (YouTube API + ADR) and builds on the already-shipped pipeline.

**Research flags for phases:**
- MAIL-01: relay choice, TLS/port, batch vs per-recipient sends, partial-failure semantics (drives option i vs ii).
- Scheduled ingestion: YouTube Data API v3 quota/pagination limits; channel vs playlist source parsing; run-away listing guards.
- 999.1: whether any admin surface beyond the shortlist row links to drafts.

---

## Anti-patterns — and inward-dependency violations to avoid

1. **Adding signup mail to the `Mailer` port.** Wrong layer: confirmation mail is GoTrue-owned. Adding `send_signup_confirmation` puts a foreign concern in `application/ports` and implies an application send path that does not exist. → Configure GoTrue; reuse nothing.
2. **Computing `recipient_count` inside the RPC from `profiles`.** Puts audience policy in SQL inside the claim transaction and couples persistence to a business rule. → Use case owns the count; RPC only persists `p_recipient_count`.
3. **Resolving recipients in the HTTP route.** Business rule in the interface layer. → Resolve in the use case via a port.
4. **Making `GET /materials/{slug}` draft-aware.** Leaks unpublished content into the public reader path if the role branch ever regresses. → New admin-only route; keep the reader route ready-only.
5. **Putting the visibility decision only in the route.** The *what-is-visible* rule must be a testable use case, not an inline HTTP branch.
6. **Importing `smtplib`/`yaml`/`httpx`/`supabase` into `domain/` or `application/use_cases/`.** Adapters (including the new SMTP and listing adapters) hold the SDKs and map errors at their boundary.
7. **Reading `os.environ` inside adapters.** Config belongs in `composition/settings.py`; adapters take ready primitives/clients (existing D-17 / D-02 rule).
8. **Building an in-app scheduler / daemon module.** Adds runtime and domain concepts; the repo's boundary is a thin one-shot CLI. → cron/systemd invoking the CLI.
9. **Having the CLI/timer call the FastAPI admin API.** Breaks the locked "ingestion writes Supabase only" boundary and couples the timer to HTTP/auth. → service_role writers/RPC.
10. **Auto-ready or auto-send from scheduled ingestion.** Breaks editorial trust (content contract + ADMIN-03 send-pool rules). → drafts + `pending` shortlist only; a human triages.
11. **Putting the listing SDK in `ingestion-service`.** Makes the CLI a god-package and blocks the FoundryModels/source swap. → `data-collection` adapter behind a port.
12. **Passing bare emails vs `Recipient` inconsistently across the port.** Pick one explicit type; no `Any`/untyped dicts at the port boundary.
13. **Silent stub fallback when `MAILER=smtp`.** Honesty over convenience: fail fast on incomplete `SMTP_*`.

---

## Scaling Considerations

| Concern | v1.3 reality | Guidance |
|---------|--------------|----------|
| Digest recipients | Tens–low hundreds of profiles | One send loop in the adapter; batch/chunk only if the relay rate-limits. No queue needed. |
| Scheduled listing | A handful of videos per run | Adapter paginates with a max-items guard; reuse `already_saved` idempotency. |
| Concurrency | Single operator, single timer | Do not add a broker/worker; if concurrent runs become real, gate with a lock file/systemd `flock`. |
| Reader path | Already shipped | Untouched; the new admin preview route is the only read-path addition and is admin-gated. |

---

## Sources

- Live codebase (read this session): `backend/src/backend/{application/ports,application/use_cases,infrastructure,composition,interface/http,domain,tests_support}/*`, `supabase-integration/src/supabase_integration/*`, `supabase-integration/migrations/001,005,006,007,008,009`, `data-collection/src/data_collection/*`, `ingestion-service/src/ingestion_service/*`, `web/src/{pages,services,components,App.jsx}`, `tests/unit/test_stub_mailer.py` — **confidence HIGH**.
- `.cursor/rules/architecture.mdc`, `.cursor/rules/tdd.mdc`, `AGENTS.md`, `CONTEXT.md` — mandatory architecture/TDD invariants.
- `.planning/PROJECT.md` (v1.3 scope, risks), `.planning/ROADMAP.md` (backlog 999.1/999.6/999.7), `.planning/debug/g-01-3b-signup-mailer.md`, `docs/agents/local-platform-runbook.md` §4.1 — MAIL-02 root cause and current autoconfirm workaround.
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — contour isolation (tension for YouTube Data API v3 listing).
- Third-party API specifics (SMTP relay, YouTube Data API v3 listing) — **not verified against vendor docs this session**; confidence MEDIUM/LOW → settle in the phase spike/ADR.

---
*Architecture research for: Digest CDS v1.3 — live mail, scheduled ingestion & backlog debt (integration on shipped architecture)*
*Researched: 2026-10-14*
