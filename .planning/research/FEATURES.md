# Feature Research

**Domain:** Editorial knowledge service for a corporate internal-audit department (Russian-language) — v1.3 backlog debt, live mail, scheduled ingestion
**Project:** Digest CDS
**Researched:** 2026-10-14
**Scope:** FEATURES dimension only — how the six v1.3 capabilities typically work, expected behaviour, and what is table stakes / differentiator / anti-feature.
**Confidence:** HIGH overall (HIGH on 999.1, 999.6, 999.7, MAIL-02; HIGH–MEDIUM on MAIL-01 and scheduled ingestion — see per-feature notes).

> **Note on the research seam.** The GSD `gsd_run query research-plan` / `classify-confidence` runtime was **not present** in this environment (no `gsd-tools.cjs` shim on disk or on `PATH`, `.claude/config.json` carries no `agent_skills` map), so the code-seam provider selection and cache were unavailable. This file was produced with direct Context7 + web research plus mandatory codebase grounding. Confidence tiers are assigned honestly per finding below.

## Orientation

This is a **subsequent milestone on a shipped app**. The existing features (auth + sessions, issue/materials/archive reader, voting, knowledge search, разборы, admin shortlist → preview → send → archive, YouTube→DeepSeek→Supabase ingestion CLI, and the validated-only YAML pipeline-config editor) are **consumers and constraints, not rebuild targets**. Everything below is scoped to the six new items: `999.1`, `999.6`, `999.7`, `MAIL-02`, `MAIL-01`, scheduled ingestion.

Two cross-cutting realities from the codebase shape almost every decision:

1. **The backend is a *reader* of Supabase; the CLI owns ingestion writes.** Mail and ingestion therefore sit at different seams: digest mail goes through the backend `Mailer` port (`backend/src/backend/application/ports/mailer.py`), while signup confirmation mail is owned by **Supabase Auth / GoTrue**, not by that port. Conflating the two is the single most likely v1.3 design mistake.
2. **Honesty is a first-class product rule in this codebase** (D-87/D-88, ADMIN-03, ADUX-06, PIPE-02). Every feature below must fail closed and must not claim more than it did. That rule is the strongest signal for deciding what is table stakes vs anti-feature.

---

## Feature Landscape

### Feature 999.1 — Reader-route honesty (admin preview of an unpublished draft)

**Problem (grounded):** `GET /materials/{slug}` is ready-only — `get_material_for_reader` raises `MaterialNotFoundError` unless `status == READY` (`backend/src/backend/application/use_cases/get_material_for_reader.py`). So the «Открыть материал →» link from the admin material preview points a draft at `/materials/<slug>`, where `MaterialPage` renders the «Материал не найден» state (`web/src/pages/MaterialPage.jsx`). The current backend is *correct* for readers; the admin needs an honest preview path.

**How comparable editorial/CMS tools do it:** unpublished content is served through a dedicated, authenticated, **non-cacheable and non-indexable** preview surface that renders with the *same* templates as production. Two credible shapes recur: (a) a separate preview route/endpoint gated by an authorized role, or (b) a "draft-mode" state signal (short-lived preview token or signed cookie) that flips the data layer to include drafts. The load-bearing invariant in every variant is that the **authorization decision is server-side**, not a client flag, and that preview responses never enter a shared cache. (Sources: Vercel Draft Mode; headless CMS preview/draft workflow pattern guides; Context7-shape precedents.) For a single-tenant internal SPA with JWT auth and role in `profiles`, shape (a) is the natural fit and avoids introducing token expiry/rotation machinery the product does not need.

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Admin can open any draft from the shortlist/preview and read it in the normal reader rendering | The link exists today and currently dead-ends; an admin must be able to verify a draft before promoting it | LOW–MEDIUM | Server-gated preview endpoint (e.g. `GET /admin/materials/{slug}` or an admin-only `?preview=1`), rendering the same `MaterialReaderResponse` shape |
| Ordinary readers still cannot read a draft | The ready-only rule is the content contract (D-CONTENT-01 / MAT-01) | LOW | Keep `get_material_for_reader` ready-only; add a **separate** admin use case — do not weaken the reader filter |
| Authorization is server-side (role from `profiles`, never a client flag) | Consistent with `require_admin` and the D-74 rule that admin comes from `profiles.role`, not a JWT claim | LOW | Reuse `require_admin` (`backend/src/backend/interface/http/deps.py`) |
| Non-admin hitting a draft slug gets the opaque not-found state, not a "forbidden" hint | Prevents disclosing that an unpublished document exists | LOW | Keep 404 `material_not_found` semantics for non-admins; preview only widens for admins |
| The preview is visually marked as a preview (draft badge / "черновик") | Visual honesty (G-04-2 lineage): an unpublished state must not look published | LOW | Reuse the draft badge vocabulary already used in `/admin/digest` |
| Preview responses are non-cacheable and not indexed | Drafts must never leak via a shared/proxy cache | LOW | `Cache-Control: no-store`; internal SPA so indexation risk is low but the contract is cheap |
| Reader-link from the admin preview resolves for a draft after this change | The literal defect (W-1) | LOW | Depends on the reader page accepting the preview route or a preview-mode parameter |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Preview renders through the *same* fetch/render path as the reader | Guarantees "what the admin sees is what the reader will see" (parity), so preview is trustworthy | LOW–MEDIUM | Share the response DTO and the `MaterialPage` renderer; only the data source differs |
| Explicit preview provenance banner with the material status | Removes the risk of an admin mistakenly believing a draft is live | LOW | Reuse the v1.2 preview-honesty pattern from `AdminDigestPage` |
| Deep-link preview from the shortlist row (no context switch) | Faster triage loop for the single-operator workflow | LOW | SPA routing only |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Loosen the global reader filter to include drafts (e.g. `include_drafts=true` accepted from the client) | "One route is simpler" | Leaks unpublished content to any authenticated reader; breaks the content contract | Admin-gated *separate* use case; reader filter untouched |
| Full preview-token system with expiry/rotation/share links | "Matches CMS vendors" | Over-engineering for a single-tenant internal SPA; a token lifecycle becomes a new secret to manage (ADR-0002 contour) | Server-side role check on the existing JWT session |
| Client-side-only role gate in the SPA | "Hide the link" | The API would still return the draft to a non-admin; UI is not an authz boundary | Server-side `require_admin` |
| Separate "draft viewer" component that drifts from the reader | "Don't touch the reader" | Preview stops predicting production; the dishonesty returns in a subtler form | One renderer, two data sources |
| Marking the material `ready` (or publishing) on preview | "Make the link work" | Silent status change; breaks the admin decision gate (D-85) | Pure read; no write side-effects |
| Returning `403` (rather than `404`) for a draft to a non-admin | "More honest error" | Discloses the existence of unpublished content | Opaque 404 |

**Complexity note:** LOW–MEDIUM. **Dependencies:** `get_material_for_reader` (ready-only), `MaterialRepository.get_by_slug`, `require_admin`, `MaterialPage` / `contentApi`, and the v1.2 admin preview link. Note the SPA route param is named `:id` but carries the slug (`web/src/App.jsx`, `web/src/pages/MaterialPage.jsx`).

---

### Feature 999.6 — Unsaved-changes guard for the admin pipeline-config editor

**Problem (grounded):** `AdminPipelineConfigPage` registers a `beforeunload` handler that calls `window.confirm` inside the event (`web/src/pages/AdminPipelineConfigPage.jsx`). `window.confirm` in `beforeunload` is unreliable in real browsers, and there is **no router-level guard**, so in-app SPA navigation silently discards typed YAML. The DB is safe (no save → no write); only typed text is lost (WR-04/WR-05).

**How comparable admin tools do it:** two *complementary* mechanisms are the norm:
- **`beforeunload`** for browser-level navigation (reload, tab/window close, external navigation) — custom text is ignored by modern browsers, but `event.preventDefault()` + `event.returnValue` still triggers the native confirm. It must be registered **only when dirty** and removed on save/clean.
- **A router-level blocker** for in-app SPA navigation. React Router's `useBlocker` is the canonical API, but it **only works with a data router** (`createBrowserRouter` + `RouterProvider`); it explicitly does *not* cover hard reloads or cross-origin navigations. The docs also note that blocking navigation is an anti-pattern to use sparingly and suggest persisting the draft (e.g. `sessionStorage`) and restoring it as an alternative to blocking. (Sources: reactrouter.com `useBlocker` + Navigation Blocking guide; TanStack Router navigation-blocking guide.)

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Dirty-state tracking (`yaml !== savedYaml`), already present | The guard is only correct if "dirty" is accurate | LOW | Reuse existing `dirty` |
| In-app SPA navigation is blocked with a confirm while dirty | This is the actual defect: nav links/back silently drop the draft | MEDIUM | `useBlocker` requires a **router migration to a data router** — a real dependency, not a drop-in |
| Browser reload/close shows the native confirm while dirty | Classic `beforeunload` contract | LOW | Correct form: `event.preventDefault(); event.returnValue = ''` (drop the `window.confirm`) |
| No prompt when clean, and dirty clears after a successful save | False prompts are worse than the bug; a post-save prompt blocks the workflow | LOW | Reset on `status === 'saved'` and on reset-to-saved |
| Russian confirm copy matches the existing string | Product copy canon | LOW | Reuse `UNSAVED_LEAVE_CONFIRM` = «Есть несохранённые изменения. Уйти без сохранения?» |
| "Cancel" keeps the user on the page with the draft intact | Core of the confirm contract | LOW | `blocker.reset()` |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persist the in-progress YAML to `sessionStorage` and restore on return | React Router's own recommended alternative; zero data loss without nagging the user | LOW–MEDIUM | Must be scoped to this page so it never leaks into saved server state |
| "Сохранить и выйти" as a third option | Removes the most common reason an admin navigates away | MEDIUM | `blocker.proceed()` after a successful save |
| Persistent "есть несохранённые изменения" indicator outside the toolbar | Speeds recognition | LOW | Already have `pipeline-config-status` |
| Guard scoped to the pipeline page only | Avoids app-wide friction | LOW | Per-route blocker |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| `window.confirm` inside `beforeunload` (the current code) | "It looks like it works" | Suppressed/ignored by browsers; gives false confidence and still loses data | `event.preventDefault()` + `returnValue`; use a router guard for SPA nav |
| Silent auto-save on navigation | "Never lose anything" | Writes to a global singleton config on an accidental nav; hides what was saved; can flip an admin's view of a shared resource | Explicit save, or `sessionStorage` restore |
| App-wide (global) navigation blocking | "Simplest to wire" | Blocks unrelated flows; users learn to dismiss the dialog | Per-page guard |
| Flushing unsaved work in `unload`/`beforeunload` via network calls | "Save on close" | Unreliable and discouraged; requests are frequently dropped | Explicit save / local restore |
| Blocking only some navigations (e.g. links but not back/forward) | "Good enough" | Partial coverage = the silent-loss bug persists in the uncovered paths, which erodes trust | Cover in-app nav **and** browser nav explicitly |
| Force-migrating the whole router without tests | "Just enable `useBlocker`" | A router change touches every route in the SPA | TDD a failing Playwright test for the guard first; migrate deliberately |

**Complexity note:** LOW for the `beforeunload` fix; **MEDIUM** if `useBlocker` requires migrating `BrowserRouter`/`Routes` to a data router (`createBrowserRouter`/`RouterProvider`). **Dependencies:** SPA router architecture (`web/src/App.jsx`), `AdminPipelineConfigPage`, and the existing Playwright coverage in `tests/admin.spec.js` (pipeline-config scenarios). **TDD hook:** a failing Playwright test that types YAML, clicks an in-app nav link, and asserts the confirm + cancel-keeps-draft behaviour.

---

### Feature 999.7 — YAML merge keys (`<<`) in the strict pipeline-config validator

**Problem (grounded):** `_StrictSafeLoader.construct_mapping` pre-constructs key nodes and checks for duplicates *before* calling `super().construct_mapping` (`backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`). PyYAML's `SafeConstructor.construct_mapping` calls `flatten_mapping(node)` **first**, which resolves `<<` merge entries (moving merge sources to the front and re-tagging the merge key). Because the strict subclass constructs the `<<` key node before flattening, a valid merge document hits an unresolvable `tag:yaml.org,2002:merge` node and fails with a cryptic internal-tag error. It fails closed — a structured 400 `{errors:[...]}` and zero writes — so it is debt, not a user-facing outage.

**How strict validators handle this:** accepting YAML conveniences (`<<` merge keys, anchors/aliases) is normal and desirable — merge keys are the documented, spec-backed mechanism for config reuse. The subtlety, verified against primary sources, is that **merge expansion must not be treated as duplication**: explicit keys legitimately override merged keys, and two merge sources may share keys (pyyaml issue #165; yaml.org merge spec; pyyaml PR #954). A duplicate check run over the *flattened* node therefore produces false positives and rejects valid configs. The correct split is: reject duplicate **explicitly-written** keys in each original mapping node (excluding `<<`), and allow inherited/merged keys to be overridden.

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| A valid `<<` merge document validates and saves | YAML merge keys are standard config ergonomics | LOW–MEDIUM | Run `flatten_mapping` before duplicate detection (or resolve merges first) |
| Duplicate **explicit** keys are still rejected with a structured 400 | PIPE-02 honesty: no silent last-wins | MEDIUM | Detect duplicates among explicit keys in each original mapping, excluding merge entries |
| Merge override is **not** reported as a duplicate | Explicit keys overriding merged keys is the spec, not an error | MEDIUM | This is the trap in the naive "flatten then check" fix |
| The fixed `extra="forbid"` 4-key schema still governs the result | PIPE-01/PIPE-02 contract (`PipelineConfigModel`) | LOW | Merged keys that aren't in `{template, roles, language, max_chars}` still fail schema validation |
| Rejected documents still return top-level `{errors:[...]}` with line/path, and write nothing | Existing contract (D-05, PIPE-02) | LOW | Preserve `PipelineConfigValidationError` mapping |
| Merge precedence follows YAML semantics (explicit > merged; earlier merge source > later) | Predictability | MEDIUM | PyYAML #954 territory; do not hand-roll precedence |
| Alias/merge DoS protections remain | The adapter caps `MAX_PIPELINE_CONFIG_CHARS` and maps `RecursionError` | LOW | Merge expansion must not bypass the cap or reintroduce exponential blow-up |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Clear Russian error text for genuinely invalid merges (scalar merge source, non-mapping merge) | Turns a cryptic failure into an actionable one | LOW–MEDIUM | Map `flatten_mapping` constructor errors to `PipelineConfigError` |
| Line numbers on merge-related errors | Operator can fix fast | LOW | `MarkedYAMLError.problem_mark` already available |
| Explicitly document which YAML conveniences are allowed | Removes ambiguity for the config author | LOW | Docs + a validator test matrix |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Dropping strict duplicate detection "so merge works" | "Fastest fix" | Reintroduces silent last-wins (the exact PIPE-02 regression) | Detect explicit keys, exclude merges |
| Running uniqueness over the flattened mapping | "Simplest implementation" | Rejects valid override configs as duplicates (false positive) | Check original mapping nodes before/around flatten |
| Switching to unsafe/arbitrary-tag loading | "Support all YAML" | Opens object-construction / SSRF-class risk on server-parsed input | Keep `SafeLoader` subclass |
| Accepting multi-document or empty documents | "Be permissive" | Violates the strict contract; ambiguous which doc is the config | Keep the existing single-document contract |
| Letting merge expansion bypass the size cap / alias-bomb guard | "Merges are small" | Reopens the DoS surface the cap exists for | Validate caps before/around expansion |
| Silently "helpfully" merging two explicit conflicting keys | "Be forgiving" | Hides an authoring bug; violates fail-closed | Reject explicit duplicates |

**Complexity note:** LOW–MEDIUM, but with a real correctness trap (merge-vs-duplicate). **Dependencies:** `_StrictSafeLoader`, `PipelineConfigModel` (`extra="forbid"`, four keys), `PipelineConfigValidationError`, the `PUT /admin/pipeline/config` route, and `tests/unit/test_pipeline_config_validator.py` (which currently asserts duplicate-key rejection and would gain merge-key cases). **Note:** because the schema is a fixed 4-key set, the practical value of `<<` is config-reuse ergonomics rather than enabling new keys.

---

### Feature MAIL-02 — Signup confirmation mail

**Problem (grounded):** the unresolved v1 debug file `.planning/debug/g-01-3b-signup-mailer.md` already established the root cause: self-hosted GoTrue on the VM had `mailer_autoconfirm=false` with a broken SMTP path, so `POST /auth/v1/signup` returned `500 unexpected_failure "Error sending confirmation email"` and **no Auth user was created**. The 2026-09-20 unblock simply enabled autoconfirm (`mailer_autoconfirm: true`), which is why registration completes today with **no email**. MAIL-02 is therefore mostly an *investigation-then-configuration* item, exactly as PROJECT.md frames it.

**Architecture insight that must drive design:** signup confirmation is sent by **Supabase Auth (GoTrue)**, using its own SMTP settings on the `auth` service (`GOTRUE_SMTP_HOST/PORT/USER/PASS/ADMIN_EMAIL`, `GOTRUE_MAILER_AUTOCONFIRM`, `GOTRUE_MAILER_URLPATHS_CONFIRMATION`, custom templates served over HTTP, `SITE_URL`/`API_EXTERNAL_URL`) — **not** by the backend `Mailer` port. Trying to send signup confirmation through `Mailer` would duplicate GoTrue's token/reset machinery and the SPA's `supabase.auth.signUp` path. (Sources: Supabase Auth self-hosting config; Supabase Auth README; Supabase self-hosting Docker guide; custom email templates guide.)

**Two honest end states exist, and the product must pick one explicitly:**
- **(A) Mail works:** GoTrue SMTP configured, `mailer_autoconfirm=false`, confirmation email delivered, link confirms the account.
- **(B) Autoconfirm intended:** `mailer_autoconfirm=true`, and the UI copy **must not** claim an email was sent. Today `RegisterPage` shows `CONFIRM_MESSAGE` («Подтвердите email по ссылке из письма…») whenever `signUp` returns no session — with autoconfirm on, that branch should generally not fire, but the copy/paths must be reconciled so the product never lies.

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Root cause identified and documented (investigation first) | PROJECT.md: MAIL-02 opens with investigation, not implementation | LOW | Start from `g-01-3b-signup-mailer.md` + `GET /auth/v1/settings` |
| Registered corporate users either receive a working confirmation email or signup is honestly autoconfirmed | The stated user complaint ("no email ever arrives") is a trust break | MEDIUM | Decide (A) vs (B) explicitly |
| Confirmation link resolves and the account becomes usable | Mail without a working link is worse than no mail | MEDIUM | Depends on `SITE_URL` / `API_EXTERNAL_URL` / `GOTRUE_MAILER_URLPATHS_CONFIRMATION` correctness |
| Mailer/confirmation failures surface honest Russian copy, never the generic «Сервис входа временно недоступен» banner | The deferred SPA follow-up from Phase 1 (never lie) | LOW–MEDIUM | RegisterPage error mapping |
| The confirmation flow respects ADR-0003 corporate-domain restriction | Only `@sberbank.ru` / `@omega.sbrf.ru` | LOW | Already enforced client-side; server/GoTrue alignment |
| Secrets live only in VM env, never in code/DB/YAML config | Security contract | LOW | GoTrue env on the Supabase VM |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Branded Russian confirmation template (sender name/identity aligned with the digest) | Recognizable, trustworthy internal mail | LOW–MEDIUM | Custom template served over HTTP (GoTrue does not read mounted volume templates) |
| SPF/DKIM/DMARC alignment on the sending domain | Deliverability into corporate inboxes | MEDIUM (ops) | Same concern as MAIL-01 |
| A resend-confirmation affordance for a lost mail | Reduces operator load | MEDIUM | GoTrue supports resend; verify against chosen config |
| A test-address smoke in the runbook | Proves the path end-to-end | LOW | Extend runbook §4.1 |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Build a bespoke backend confirmation-token + mail flow | "We already have a `Mailer` port" | Duplicates GoTrue's own token machinery; more surface, more failure modes; diverges from `supabase.auth.signUp` | Configure GoTrue SMTP |
| Route auth mail through the digest `Mailer` port | "One mailer" | Wrong layer; the SPA signs up directly against Supabase Auth | Keep GoTrue's mailer for auth |
| Leave autoconfirm ON while the UI claims "подтвердите email" | "It works today" | Dishonest copy; the user waits for a mail that is never sent | Reconcile copy with the chosen end state |
| Send confirmation synchronously from the signup request handler in our backend | "Visible control" | GoTrue already owns the request path; double-send / race | Configure at the auth service |
| Share a bulk/уведомления stream for auth mail | "One relay" | Auth mail must not be delayed by digest volume (transactional vs bulk separation) | Separate stream/lane, or at minimum separate sender identity and priority |
| Store SMTP credentials in the pipeline YAML config | "It's config" | PIPE-01 schema forbids secrets; a shared singleton row is the wrong secret store | VM env only |

**Complexity note:** MEDIUM (mostly ops/config + copy honesty + tests). **Dependencies:** self-hosted Supabase `auth` service on the VM; the corporate SMTP relay decision; ADR-0002 contour isolation; ADR-0003; `RegisterPage` copy/error mapping; runbook §4.1; the resolved-unblock state (`mailer_autoconfirm: true`) that must be deliberately re-evaluated.

---

### Feature MAIL-01 — Live SMTP digest delivery

**Problem (grounded):** `StubMailer` only logs and returns `delivery_status: "stubbed"`, `recipient_count: 0` (`backend/src/backend/infrastructure/stub_mailer.py`); `SmtpMailer` is an explicit placeholder that raises; `resolve_mailer("smtp")` fails fast at startup. `recipient_count` is hardcoded `0` by the `claim_and_publish_digest` RPC (`p_recipient_count int default 0`, migrations 005/006). `send_digest` calls the mailer **after** the atomic claim+publish and swallows mail failures (`except PersistenceError`, best-effort per CR-02) — so today a real SMTP failure would be invisible.

**How comparable tools do it:** transactional and bulk mail are treated as separate lanes; bulk/campaign sending is batched, paced (token-bucket / bounded concurrency / per-recipient-domain caps), retried with exponential backoff + jitter on transient 4xx/429, suppressed or dead-lettered on hard 5xx, and monitored (429 rate, bounce, queue age). Never batch transactional mail; keep critical lanes fast. (Sources: email sending-limit and queue-architecture guides; transactional rate-limiting guides.) For Digest CDS the audience is a modest internal list, so the pragmatic shape is **one message per recipient** (or a well-defined per-recipient loop) with bounded concurrency and honest per-recipient outcomes.

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| The send actually delivers to the audience (recipients sourced server-side from `profiles`) | The literal milestone goal | MEDIUM | Replaces `StubMailer`; keep the `Mailer` port |
| `recipient_count` reflects the real audience size, computed from `profiles` (not `0`) | Honest API/UI; PROJECT flags the hardcoded `0` | MEDIUM | RPC default must be replaced by a computed count; `ProfileRepository` has **no list-all method today** → new port method |
| The result honestly reports partial failure (e.g. «доставлено N из M») | Fail-closed honesty rule; silently "success" on partial delivery is the anti-pattern | MEDIUM | Needs a mail-error taxonomy and a per-recipient result summary |
| Mail is best-effort *after* publish, so a mail failure never corrupts the published issue | Existing CR-02 contract (claim+publish is the atomic step) | LOW | Keep the ordering; do not make the issue conditional on delivery |
| `MAILER=smtp` validates config at startup and fails fast only on *missing/invalid* config | Operability | LOW–MEDIUM | Distinguish "mode not ready" (today's fail-fast) from "configured but relay down" |
| SMTP secrets/config come only from VM env (`SMTP_*`), never DB or pipeline YAML | Security contract; ADR-0002 contour | LOW | Extend `Settings` (`backend/src/backend/composition/settings.py`) |
| Delivery outcome is auditable (`digest_send` ping already records `delivery_status`/`recipient_count`) | NFR-L1 audit | LOW | Populate with real values |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Per-recipient personalization (greeting by `profiles.display_name`) | Higher engagement; feels internal, not a blast | MEDIUM | One message per recipient makes this trivial |
| Per-recipient delivery summary persisted on the batch + audit ping | Operators can prove who got what | MEDIUM | Additional columns/JSON or `ingestion_jobs`-style run record |
| Bounded retry with backoff for transient 4xx/429; hard 5xx → recorded failure | Reliability without infinite retries | MEDIUM | Keep a bounded budget (≈3–5 attempts) |
| Per-recipient-domain pacing and bounded concurrency | Protects relay reputation and corporate anti-spam thresholds | MEDIUM | Token-bucket or fixed worker pool |
| Separate lanes for auth (MAIL-02) and digest (MAIL-01) | Auth mail never waits behind digest volume | MEDIUM (ops) | Aligns with the transactional/bulk separation norm |
| Operator-visible "recipient_count N, delivered X, failed Y" before/after send | Removes the biggest honesty gap left by the stub | LOW–MEDIUM | Extend `SendDigestResponse`/UI |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Put all recipients in one `To:`/`Bcc:` and call it success | "One send, fast" | Leaks the whole audience list; no per-recipient truth; `recipient_count` stays a guess | One message per recipient (or explicit, counted loop) |
| Synchronous send inline in the HTTP request with no bounds | "Simple" | Blocks the admin; risks request timeout and double-sends on retry | Bounded loop + timeouts, or queue the send |
| Make issue publish conditional on mail success | "All-or-nothing" | Contradicts D-88/CR-02 (archive + emailed link must match a real issue) and can strand a published batch | Keep publish atomic; mail best-effort + honest status |
| Infinite retries / tight retry loop on 429 | "Must deliver" | Worsens throttling; can get the relay reputation-blocked | Bounded retries with backoff + jitter |
| Store recipients or SMTP creds in the pipeline YAML config | "Central config" | PIPE schema forbids secrets; audience is derived from `profiles` | Env + `ProfileRepository` |
| Silently swallow SMTP failures (today's `except PersistenceError` path) | "Don't break the send response" | The admin believes the digest was delivered; this is the core dishonesty the milestone exists to remove | Classify + surface mail failures honestly |
| Auto-send / scheduled digest send | "Automation" | Explicitly OUT of scope; editorial trust requires a human send | Keep admin-triggered send |

**Complexity note:** MEDIUM–HIGH. **Dependencies:** `Mailer` port; `resolve_mailer`/`SmtpMailer`; `Settings` (`SMTP_*`); `Container.mailer` / `composition/live.py`; `send_digest` flow and its error handling; `DigestPublisher.claim_and_publish` + `DigestPublication.recipient_count`; migrations 005/006 (`p_recipient_count default 0`); **a new `ProfileRepository` list-all/audience method**; tests `test_send_digest.py`, `test_stub_mailer.py`, `test_live_container_wiring.py`. **Shared prerequisite with MAIL-02:** the SMTP relay choice.

---

### Feature — Scheduled ingestion (unattended YouTube channel/playlist collection)

**Problem (grounded):** today a human runs the `ingest` CLI one-shot. PROJECT.md wants a cron/systemd timer on the VM driving the existing CLI against a YouTube channel/playlist; results are **drafts + shortlist rows only**, never auto-publish or auto-send. The CLI is already idempotent (`already_saved`, unique `youtube_video_id`, RPC `persist_draft_and_enqueue`, migrations 007/009).

**How comparable scheduled ingestors do it:** systemd `timer` + `service` (or cron) with `Persistent=true` (catch-up after downtime), a single-flight lock / `Conflicts=` to prevent overlapping runs, **idempotent business logic**, a **durable per-source high-water mark** stored in the DB (not in memory), an **overlap window** for late-arriving records, structured per-run records (`run_id`, scheduled window, start/end, result, watermark), and **failure visibility** (Sentry check-ins, Prometheus job-last-status/missing alerts, or journald with `result=SUCCESS/FAIL/SKIP`). Listing is done with **YouTube Data API v3 `playlistItems.list`** on the channel's uploads playlist (1 quota unit/call, `maxResults=50`, `pageToken`); there is **no `publishedAfter` filter**, so poll newest-first and stop once an item is not newer than the stored watermark, keyed on `contentDetails.videoPublishedAt` (not `snippet.publishedAt`, which is playlist-add time). `search.list` costs 100 units and should not be used for routine polling. (Sources: YouTube Data API `playlistItems.list`; quota guides; systemd-timer/scheduled-job observability guides; feed-ingest idempotency patterns; Sentry cron check-ins.)

#### Table Stakes
| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Runs unattended on a schedule without a human | The literal goal | MEDIUM | systemd timer/cron on the VM |
| discovers only genuinely new videos | Re-ingesting old videos wastes LLM budget and pollutes the shortlist | MEDIUM–HIGH | High-water mark + newest-first stop condition; `unique (source_system, external_id)` and unique `youtube_video_id` are the durable backstops |
| Writes **drafts + pending shortlist rows only**; never `ready`, never a send | Editorial contract (D-CONTENT-01, D-85) | LOW | Reuse the unchanged CLI path |
| Re-running is safe (idempotent) even if the watermark is lost | PROJECT: "re-scanning a playlist must stay safe — lock it with a test" | MEDIUM | `already_saved` + unique `youtube_video_id` already enforce this; pin with a test |
| Durable high-water mark survives restarts | In-memory-only checkpointing is the classic restart-duplicate bug | MEDIUM | Store per-source bookmark in Supabase (`ingestion_sources.metadata` or a dedicated column/table) |
| Single-flight: no overlapping runs | Concurrent runs duplicate work and race the shortlist rank | LOW–MEDIUM | systemd `Conflicts=` / lock file |
| Each run's outcome is visible (success/fail/skip + counts) | Silent failures are the top scheduled-job pitfall | MEDIUM | Journald + `ingestion_jobs` run rows; alert on failure/missing |
| A bad video (no captions, quota, IP block) does not silently abort the whole batch | Partial failure is normal on YouTube | MEDIUM | Per-video error isolation with a run summary; reuse staged `IngestError.stage` reasons |
| Catch-up after downtime | Missed windows otherwise lose collection | LOW | systemd `Persistent=true` |
| Shortlist overflow (≤5/batch) creates a new unsent batch | Existing RPC behaviour | LOW | Already handled by `persist_draft_and_enqueue` |

#### Differentiators
| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `ingestion_jobs` run-history with new video ids/counts/errors | Operator can answer "what did the last run do?" | MEDIUM | `ingestion_jobs` table already exists |
| Per-run cap (`--max-new N`) to bound LLM cost | Predictable spend | LOW–MEDIUM | Scheduler-level guard |
| Dry-run / "list-only" mode | Safe rollout and diagnostics | LOW–MEDIUM | Reuses CLI diagnostics precedent (`--debug`) |
| Operator-visible "последний запуск" status (in admin or a runbook command) | Removes the "did it run?" question | MEDIUM | Read from run rows |
| Channel/playlist allowlist + configurable source | Prevents accidental broad scraping | LOW | Config-driven source id |
| Structured run result enum (SUCCESS/FAIL/SKIP_LOCKED/SKIP_DEADLINE) | Makes alerts and dashboards meaningful | LOW–MEDIUM | systemd/journald convention |

#### Anti-Features
| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Auto-publish / auto-`ready` / auto-send | "Fully automated digest" | Explicitly OUT; violates the editorial human gate and ADMIN-03 | Always draft + pending shortlist |
| Full playlist re-scan every run with no high-water mark | "Simplest correctness" | Quota and LLM-cost blow-up; slow runs; more partial failures | Watermark + newest-first stop |
| Scheduler wired inside the FastAPI backend request path | "Everything runs in the app" | PROJECT specifies a cron/systemd job on the VM; HTTP-triggered ingestion is out of scope | Standalone timer invoking the CLI |
| Poll via `search.list` for routine checks | "Search is easy" | 100 units/call vs 1 for `playlistItems.list`; burns the daily quota fast | `playlistItems.list` on the uploads playlist |
| Inferring "new" from titles/dates instead of video ids | "Avoid an API key" | Fragile, duplicates, misses renames | Video-id set + watermark |
| State living only in memory / a local file the app can't see | "Quick" | Lost on restart → duplicate ingests; invisible to ops | Durable watermark in Supabase |
| Alerting only to a log nobody reads (or no alerting) | "It usually works" | The failure mode is *silence*; nobody notices collection stopped | Journald + a failure/missing-run signal |
| Tight retry loop on quota exhaustion / IP block | "Retry until it works" | Worsens throttling and blocks | Backoff + skip + record + alert |
| Storing the YouTube API key in the pipeline YAML config | "Central config" | Secrets rule; wrong store | VM env |
| Treating the schedule as a send trigger | "End-to-end automation" | Conflates collection and delivery; breaks the trust contract | Collection only |

**Complexity note:** HIGH — this is the only v1.3 feature introducing a new external public dependency (YouTube Data API v3 + API key) and new VM ops. PROJECT.md explicitly requires this to be settled in a **spike/ADR against ADR-0002** before the scheduler phase can pass. **Dependencies:** the `ingest` CLI (already idempotent), `persist_draft_and_enqueue` (007/009), `ingestion_sources`/`ingestion_jobs` schema, `ingestion-service` composition/settings, YouTube captions + DeepSeek contour, and VM systemd/cron ops.

---

## Feature Dependencies

```
[999.1 admin draft preview]
    └──requires──> get_material_for_reader (ready-only, unchanged)
    └──requires──> require_admin (profiles.role)
    └──enhances──> [existing admin shortlist → preview → send]

[999.6 unsaved-changes guard]
    └──requires──> dirty-state tracking (exists)
    └──requires──> in-app router guard
                      └──may require──> migrate BrowserRouter → data router (useBlocker)

[999.7 YAML merge keys]
    └──requires──> _StrictSafeLoader + flatten_mapping ordering
    └──requires──> duplicate detection on explicit keys only
    └──enhances──> [existing strict validator / PUT pipeline config]

[MAIL-02 signup confirmation]  ──> GoTrue/Supabase Auth SMTP (NOT the Mailer port)
    └──requires──> corporate SMTP relay (SHARED with MAIL-01)
    └──requires──> SITE_URL/API_EXTERNAL_URL correctness
    └──conflicts──> bespoke backend confirmation flow

[MAIL-01 live digest delivery]
    └──requires──> Mailer port + SmtpMailer (replace StubMailer)
    └──requires──> corporate SMTP relay (SHARED with MAIL-02)
    └──requires──> audience source: NEW ProfileRepository list-all method
    └──requires──> recipient_count computed (replace RPC default 0)
    └──requires──> mail error taxonomy for honest partial-failure reporting

[Scheduled ingestion]
    └──requires──> existing idempotent `ingest` CLI
    └──requires──> YouTube Data API v3 key + spike/ADR vs ADR-0002
    └──requires──> durable per-source high-water mark
    └──requires──> systemd timer/cron + single-flight + failure visibility
    └──conflicts──> auto-publish / auto-send
```

### Dependency Notes

- **MAIL-01 and MAIL-02 share one prerequisite but two mechanisms.** Both need a corporate SMTP relay; auth mail uses GoTrue's config, digest mail uses the backend `Mailer` port. Decide the relay **once**, then implement each on its own lane. Sequencing MAIL-02 before MAIL-01 lets the same relay be proven on the simpler (auth) path first.
- **MAIL-01 requires a new `ProfileRepository` capability.** The current port only has `get_or_upsert` / `set_display_name`; there is no "list the audience". This is a genuine port change (and therefore an architecture-visible dependency), not just an adapter tweak.
- **`recipient_count` honesty is a two-part fix:** compute the real count from `profiles` *and* stop defaulting to `0` in the `claim_and_publish_digest` RPC (migrations 005/006), or pass the computed count through.
- **999.6 may force a router migration.** `useBlocker` requires a data router; the app is on declarative `<BrowserRouter>`/`<Routes>`. Treat the migration as an explicit, tested sub-task, not an incidental change.
- **999.7 has an internal ordering trap.** "Flatten then check duplicates" reintroduces false positives; the duplicate check must target explicit keys and exclude merge-injected keys.
- **Scheduled ingestion must not trigger mail.** It reuses the ingestion path only; the send path stays human-triggered.
- **Scheduled ingestion and the pipeline config are unrelated.** The scheduler's source/API-key config belongs in env, not the PIPE YAML singleton (which forbids secrets and does not execute).

---

## MVP Definition

### Launch With (v1.3)

Minimum honest, shippable increments — one per item.

- [ ] **999.7** — strict validator accepts `<<` merge keys, still rejects explicit duplicates, zero writes on reject (highest certainty, lowest blast radius; unblocks the "valid YAML rejected cryptically" complaint).
- [ ] **999.6** — correct `beforeunload` + an in-app navigation guard with the existing Russian copy (fix the actual silent-loss path).
- [ ] **999.1** — admin-gated draft preview returning the reader DTO; reader route stays ready-only; preview visibly marked and non-cacheable.
- [ ] **MAIL-02** — investigation closed: root cause restated, relay chosen, and either (A) working confirmation mail or (B) honestly-autoconfirmed copy. No silent "registered, no mail".
- [ ] **MAIL-01** — real SMTP send to `profiles`, honest `recipient_count`, honest partial-failure reporting; publish stays decoupled and best-effort.
- [ ] **Scheduled ingestion** — timer-driven CLI run against one channel/playlist, watermark-based dedup, drafts + pending shortlist only, per-run visibility.

### Add After Validation (v1.x)

- [ ] Per-recipient delivery summary persisted + surfaced in the admin UI (MAIL-01 polish).
- [ ] `sessionStorage` draft persistence for the pipeline editor (999.6 optional, non-blocking).
- [ ] Branded confirmation template + resend affordance (MAIL-02 polish).
- [ ] Per-run cap / dry-run for the scheduler; "последний запуск" surface.
- [ ] Retry/backoff + per-domain pacing for digest delivery.

### Future Consideration (v2+)

- [ ] Unsubscribe/preference management — only if the audience stops being a fixed internal `profiles` set.
- [ ] Multiple ingestion sources / source allowlist management UI.
- [ ] PIPE-01 full pipeline execution (still deferred beyond v1.3).
- [ ] Ingestion HTTP API (still deferred; collection stays CLI/timer-driven).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| 999.7 YAML merge keys | MEDIUM (config ergonomics; currently fails closed) | LOW–MEDIUM | P1 |
| 999.6 unsaved-changes guard | MEDIUM–HIGH (data-loss UX) | LOW (beforeunload) / MEDIUM (router) | P1 |
| 999.1 reader-route honesty | HIGH (broken admin link; trust) | LOW–MEDIUM | P1 |
| MAIL-02 signup confirmation | HIGH (registration trust) | MEDIUM | P1 |
| MAIL-01 live digest delivery | HIGH (core delivery value) | MEDIUM–HIGH | P1 |
| Scheduled ingestion | HIGH (removes human toil) | HIGH | P1/P2 (sequence last) |

**Priority key:**
- P1: must have for the v1.3 milestone
- P2: should have; sequence when its prerequisite (relay / API spike) lands
- P3: nice to have, future consideration

All six are in-scope for v1.3; the ordering axis is **dependency and risk**, not value. Backlog debt (999.x) is cheap and independent → first (matches PROJECT.md). Mail (MAIL-02 → MAIL-01) is gated on one shared relay decision. Scheduled ingestion is gated on a YouTube API spike/ADR and is sequenced last.

---

## Recommended Phase Sequencing (input to roadmap)

1. **999.7** — strict validator merge keys (isolated, test-locked, no UX dependency).
2. **999.6** — unsaved-changes guard (decide the router strategy up front; TDD a failing Playwright test).
3. **999.1** — admin draft preview (depends on the shipped v1.2 admin preview; keeps reader route honest).
4. **MAIL-02** — investigate + choose/validate the SMTP relay; prove it on the auth lane; reconcile copy.
5. **MAIL-01** — live digest to `profiles` on the same relay, separate lane; honest count + partial-failure reporting.
6. **Scheduled ingestion** — YouTube API spike/ADR vs ADR-0002 first, then timer + watermark + visibility, drafts only.

**Ordering rationale:** debt-first (explicit in PROJECT.md and low risk); one relay decision reused across mail; the only new external dependency (YouTube API) and the only new ops surface (systemd) are last, after the in-code seams are proven.

---

## Competitor / Analog Feature Analysis

| Feature | AI CMS (HITL) precedent | Email/queue precedent | Scheduled-ingest precedent | Digest CDS v1.3 approach |
|---------|-------------------------|-----------------------|----------------------------|--------------------------|
| Draft vs published | Draft-mode / preview token, server-gated, uncached | — | — | Admin-gated preview endpoint; reader stays ready-only |
| Unsaved work | Router blocker + `beforeunload`; or persist to storage | — | — | `beforeunload` fix + in-app guard (data router if needed) |
| Config validation | Strict schema, no silent accepts | — | — | Accept `<<`, reject explicit duplicates, structured 400 |
| Auth/confirmation mail | — | Transactional lane, separate from bulk | — | GoTrue SMTP (own lane) |
| Digest/bulk mail | — | Batched, paced, honest per-recipient outcomes | — | Per-recipient send from `profiles`, honest count |
| Unattended collection | — | — | Timer + watermark + run records + alerts | systemd timer → idempotent CLI → drafts only |

---

## Sources

Primary (HIGH confidence):
- Codebase (grounded): `backend/src/backend/application/use_cases/get_material_for_reader.py`; `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`; `backend/src/backend/infrastructure/stub_mailer.py`; `backend/src/backend/application/use_cases/send_digest.py`; `backend/src/backend/application/ports/{mailer,profile_repository,digest_publisher,pipeline_config}.py`; `backend/src/backend/composition/settings.py`; `web/src/pages/{MaterialPage,AdminPipelineConfigPage,RegisterPage}.jsx`; `web/src/App.jsx`; `web/src/services/authApi.js`; `ingestion-service/src/ingestion_service/{cli.py,adapters/supabase_persist.py,application/use_cases/ingest_pipeline.py}`; `supabase-integration/migrations/{001,005,006,007,009,011}*.sql`; `.planning/debug/g-01-3b-signup-mailer.md`; `docs/agents/local-platform-runbook.md §4.1`.
- React Router — `useBlocker`, Navigation Blocking, `useBeforeUnload` (reactrouter.com; Context7 `/remix-run/react-router`): `useBlocker` only blocks in-app navigation and requires a data router; `beforeunload` covers reload/close/external; persisting draft state is a recommended alternative. Confidence HIGH.
- PyYAML — `SafeConstructor.flatten_mapping` / `construct_mapping` ordering and merge-key semantics (Context7 `/yaml/pyyaml`); pyyaml issue #165 and PR #954; yaml.org `type/merge` spec: explicit keys override merged keys; sequence merges are first-wins; duplicate checks must exclude merge-injected keys. Confidence HIGH.
- Supabase Auth self-hosting — GoTrue `GOTRUE_SMTP_*`, `GOTRUE_MAILER_AUTOCONFIRM`, `GOTRUE_MAILER_URLPATHS_CONFIRMATION`, custom templates served over HTTP, `SITE_URL`/`API_EXTERNAL_URL` (supabase.com self-hosting docs; github.com/supabase/gotrue). Confidence HIGH.
- YouTube Data API v3 — `playlistItems.list` quota = 1 unit, `maxResults` ≤ 50, `pageToken`, uploads-playlist pattern, `contentDetails.videoPublishedAt` vs `snippet.publishedAt` (developers.google.com/youtube/v3). Confidence HIGH.

Secondary (MEDIUM confidence):
- CMS preview/draft workflow pattern guides (headless-cms-integration, orthacms, flowcms, Vercel Draft Mode): server-side state signal, two-token pattern, never shared-cache, never index. Confidence MEDIUM (vendor-authored, cross-checked).
- Email sending limits / queue architecture / transactional rate-limiting guides: transactional vs bulk separation, batching, backoff+jitter, DLQ, monitoring 429/bounce/queue-age. Confidence MEDIUM.
- Scheduled-job observability / systemd-timer / feed-ingest idempotency guides: `Persistent=true`, single-flight, durable watermark, overlap window, run records, check-ins. Confidence MEDIUM.
- One AI-authored blog (aident.ai) on PyYAML duplicate-vs-merge policy — used only as corroboration; the same claim is independently supported by pyyaml #165 / #954 (primary). Confidence LOW as a standalone source, MEDIUM when cross-checked.

---

*Feature research for: Digest CDS v1.3 — live mail, scheduled ingestion & backlog debt*
*Researched: 2026-10-14*
