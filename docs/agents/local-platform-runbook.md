# Local platform runbook (Phase 1)

Step-by-step bring-up for **local Vite + local FastAPI** against the **existing remote** self-hosted Supabase VM (`knowledge-db.ru`). This is the Phase 1 success path (D-05 / PLAT-08).

**Not required for success:** a second local Docker Supabase (PLAT-01). Schema/RLS from [`supabase-integration/migrations/001_initial_schema.sql`](../../supabase-integration/migrations/001_initial_schema.sql) is already applied on the VM — do **not** re-provision or run destructive resets against the shared instance.

**Live E2E gating (RESOLVED RESEARCH Q3):** the checklist below (or optional local Playwright with live env) proves FE↔BE. Phase 1 is **not** blocked on CI live credentials.

---

## 1. Environment

1. Copy [`.env.example`](../../.env.example) → `.env` at the repo root (gitignored).
2. Fill **backend / Supabase** values (never commit real keys):
   - `SUPABASE_URL` — e.g. `https://knowledge-db.ru`
   - `SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_SECRET_KEY`
   - `SUPABASE_JWKS_URL` / `SUPABASE_JWT_ISSUER` (must match Auth JWT issuer used by the VM)
   - `API_CORS_ORIGINS` — include Vite origins, e.g.  
     `http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174`
   - `ALLOWED_EMAIL_DOMAINS=@sberbank.ru,@omega.sbrf.ru`
   - `APP_CONTAINER=live` for ping persistence (default `memory` keeps unit tests offline)
3. Fill **Vite publishable-only** vars (never put `SUPABASE_SECRET_KEY` behind a `VITE_` prefix):
   - `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY`
   - `VITE_API_BASE_URL=http://127.0.0.1:8000`
   - `VITE_USE_MOCKS=true` for Playwright / offline UI (default)
   - `VITE_USE_MOCKS=false` **only** for the live FE↔BE proof (D-09 / D-10)

4. Optional **YouTube ingestion** vars (Phase 7 captions/oEmbed — composition only, never adapters):
   - `YOUTUBE_PROXY_URL` — optional SOCKS/HTTP proxy for Cloud.ru and other blocked egress.
     Example (AdGuard Home SOCKS on LAN): `socks5://192.168.1.68:1080`
     Unset → direct YouTube access. Without a working proxy from Cloud.ru, expect
     `IpBlocked` / operator reason `youtube_blocked` — that is a **proxy/network** problem,
     never a Whisper/ASR trigger (ADR-0002 captions-only MVP).
   - Never put the full `YOUTUBE_PROXY_URL` (especially credentialed forms) into logs or
     `IngestError.context`.

5. Optional **DeepSeek LLM** vars (Phase 8 article generation — read by `ingestion-service` `Settings`, never by adapters):
   - `DEEPSEEK_API_KEY` — required only for a live LLM call. Unit tests leave this unset.
   - `DEEPSEEK_BASE_URL` — default `https://api.deepseek.com`.
   - `DEEPSEEK_MODEL` — default `deepseek-flash`.
   - `MAX_TRANSCRIPT_CHARS` — default `80000`; must be a positive integer if set.
   - Do not paste a real key into this runbook or any committed file. Do not place the key
     behind a `VITE_` prefix.

6. **Ingestion CLI env (CLI-05 / D-02):** copy
   [`ingestion-service/.env.example`](../../ingestion-service/.env.example) →
   `ingestion-service/.env` (gitignored). Do **not** point UAT at the root backend `.env`.
   Keys are process-scoped via `uv run --env-file` — the CLI never mutates a shared dotenv
   file on disk.

```bash
# from repo root — separate env file from backend FastAPI
uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast
```

Threat note (T-01-13): keep secrets in `.env` only — do not paste keys into markdown, commits, or screenshots.

---

## 2. Backend (FastAPI)

```bash
# from repo root
uv sync
# live adapters → profiles + activity_events (service_role only in composition/live.py)
# --env-file .env is REQUIRED: settings read os.environ and nothing auto-loads .env.
# Without it APP_CONTAINER defaults to `memory` and JWKS/CORS are empty (ping won't persist).
uv run --env-file .env uvicorn backend.interface.http.app:create_default_app --factory --host 127.0.0.1 --port 8000
```

Smoke: `GET http://127.0.0.1:8000/health` should return OK. Structured JSON logs on stdout include `request_id` on each request (PLAT-06).

Optional helper (prints this path + the uvicorn command, no secrets):

```bash
npm run platform:runbook
```

---

## 3. Frontend (Vite)

```bash
npm install
npm install --prefix web
npm run dev
```

Vite loads env from the **`web/`** dir (its config root), **not** the repo-root `.env`. For the live proof create **`web/.env.local`** (gitignored) with the publishable-only vars:

```dotenv
VITE_SUPABASE_URL=https://knowledge-db.ru
VITE_SUPABASE_PUBLISHABLE_KEY=<publishable key>
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_USE_MOCKS=false
```

Restart `npm run dev` after creating/editing it — Vite only reads env files at startup. With `VITE_USE_MOCKS` unset or `true`, `RequireAuth` renders through and `/login` is never shown (mock data). Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Playwright web project uses port **5174** under mocks — keep CORS allowlist covering both.

---

## 4. Auth users (amended D-08 / G-01-3)

**Primary path — self-service registration:** new operators use SPA `/register` with corporate email, password, and display nickname **«Логин»** (publishable-client `signUp` only — never `service_role` in the browser).

### 4.1 Auth mailer / autoconfirm (G-01-3b — required for `/register`)

On `knowledge-db.ru`, GoTrue had `mailer_autoconfirm=false` and a broken SMTP path. Signup then returned **500** `Error sending confirmation email` and **no Auth user was created**. Diagnosis closed: [`.planning/debug/g-01-3b-signup-mailer.md`](../../.planning/debug/g-01-3b-signup-mailer.md).

**Shipped end state this session (path B):** runtime keeps autoconfirm ON. SPA `/register` null-session copy is honest — «Регистрация завершена. Аккаунт активен — войдите.» — and never claims a confirmation letter was sent. Path **(A)** (working confirmation email through the corporate relay) remains the **target** end state once the procedure below is proven.

**Phase 1 / path (B) unblock (current):** enable autoconfirm so signup does not depend on email:

1. Open Supabase Studio → **Authentication** → **Providers** → **Email**.
2. Turn **Confirm email** **OFF** (equivalent env: `GOTRUE_MAILER_AUTOCONFIRM=true` + restart Auth/GoTrue on the VM).
3. Verify: `GET https://knowledge-db.ru/auth/v1/settings` shows `"mailer_autoconfirm":true`. Trust this live probe over file contents alone (GoTrue README: `true` means autoconfirm **without** sending mail).
4. Smoke: `POST /auth/v1/signup` with a new `@sberbank.ru` / `@omega.sbrf.ru` address returns **2xx** and the user appears under Authentication → Users.

**SPA authApi error-mapping honesty (still deferred):** map mailer/confirmation failures away from the generic «Сервис входа временно недоступен» NETWORK banner when path (A) is active — not required under path (B).

#### 4.1.1 Relay choice and env shape (path A — document only)

**Relay choice (D-03):** one corporate SMTP relay serving GoTrue signup confirmation and the future Phase 21 digest lane, under ADR-0002 contour isolation. Host, port, TLS mode, CA bundle, and credentials are **operator-supplied on the VM** — never committed to git.

**GoTrue lane** (Auth container env — placeholders only):

```dotenv
GOTRUE_SMTP_HOST="<corporate-relay-host>"
GOTRUE_SMTP_PORT="<587-or-ops-chosen>"
GOTRUE_SMTP_USER="<relay-user>"
GOTRUE_SMTP_PASS="<relay-pass>"
GOTRUE_SMTP_ADMIN_EMAIL="<from@corporate-domain>"
GOTRUE_SMTP_SENDER_NAME="Digest CDS"
```

**Phase 21 digest lane** (backend / composition env — separate process namespace, same relay host is fine):

```dotenv
MAILER="smtp"
SMTP_HOST="<corporate-relay-host>"
SMTP_PORT="<587-or-ops-chosen>"
SMTP_USER="<relay-user>"
SMTP_PASS="<relay-pass>"
SMTP_FROM="<digest-from@corporate-domain>"
SMTP_FROM_NAME="Digest CDS"
SMTP_TLS_MODE="starttls"
```

Posture (D-13/D-14): `SMTP_TLS_MODE` defaults to **starttls on port 587** (`ssl` = implicit TLS, `none` = no TLS). Connect (10s) and per-send (30s) timeouts are **fixed in `Settings`** — they are deliberately *not* env keys, so no env var can widen the hang window. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, and `SMTP_FROM` are all required: `MAILER=smtp` with any of them missing fails fast at startup with `ConfigurationError` (D-16) — there is no silent fallback to `StubMailer`.

Do **not** paste real secrets into this runbook or any tracked file. Do **not** route signup confirmation through the backend `Mailer` port (`send_digest`) — GoTrue owns confirmation mail.

#### 4.1.2 Path (A) enablement, smoke, and one-command rollback

**Operator blocker before flipping to (A) — Pitfall 16:** the SPA corporate-domain gate is bypassable via direct `POST /auth/v1/signup`. With healthy SMTP and confirm-email ON, open confirmation spam is possible. Treat a GoTrue-edge domain control (or equivalent) as a precondition before enabling path (A). Do not weaken ADR-0003 / `tests/unit/test_auth_email_domain.py`.

**Enablement (ops on VM only — not executed in Phase 20):**

1. Set `GOTRUE_SMTP_*` on the Auth/GoTrue container to the corporate relay (values from the operator vault).
2. Reload/restart Auth so SMTP is loaded.
3. Smoke relay **before** flipping autoconfirm: prove the relay accepts mail from the GoTrue sender (operator-chosen probe). Do **not** set `GOTRUE_MAILER_AUTOCONFIRM=false` until that smoke passes.
4. Only then set `GOTRUE_MAILER_AUTOCONFIRM=false` (Studio: Confirm email **ON**) and reload Auth.
5. Verify: `GET https://knowledge-db.ru/auth/v1/settings` shows `"mailer_autoconfirm":false`.
6. Signup smoke: `POST /auth/v1/signup` under confirm-email ON expects confirmation **delivery** (and a persisted unconfirmed user), **not** signup HTTP 500 `unexpected_failure` / «Error sending confirmation email».

**One-command rollback (D-05):** set `GOTRUE_MAILER_AUTOCONFIRM=true` and reload/restart Auth/GoTrue. Verify `GET /auth/v1/settings` → `"mailer_autoconfirm":true`. No DB change required.

#### 4.1.3 Criterion-4 gap → Phase 21 precondition (D-06)

**Acknowledged gap:** ROADMAP Phase 20 criterion 4 (live corporate-relay smoke-test proof on the GoTrue lane) is **not** completed this session. No speculative half-enabled `GOTRUE_SMTP_*` path was committed. Phase 21 (MAIL-01 live digest SMTP) **inherits** «relay chosen and proven on the GoTrue lane» as a precondition before live digest send. Until that proof exists, keep path (B) autoconfirm and do not claim confirmation mail is delivered.

**Ops fallback — shared VM dashboard seed:** if you need a pre-created test account without going through `/register`:

1. Open the Supabase Auth dashboard for the knowledge-db.ru project.
2. Create **1–2** users with corporate emails only (`@sberbank.ru` or `@omega.sbrf.ru`).
3. Set passwords you control locally; do not commit credentials.
4. Optional: if this self-host Auth build exposes a domain allowlist/hook, enable the two corporate domains. Otherwise defense-in-depth is UI + FastAPI claim checks (D-04 / AUTH-01).

Shared VM: **no automated seed script** against `knowledge-db.ru`. First successful `GET /me` upserts `profiles` via `ProfileRepository.get_or_upsert` (idempotent safety net if no Auth→profiles trigger is present).

Do **not** run DROP/TRUNCATE/reset SQL on the shared VM during proof (T-01-14). Ping is insert-only (`activity_events`, `kind=platform_ping`).

---

## 4b. Phase 2 content seed (D-25, D-27)

Checked-in idempotent SQL: `supabase-integration/migrations/002_phase2_issue_seed.sql`.

Creates / upserts:

- Two **published** `digest_issues` (№14 current from mock.js + №13 past for archive)
- Ready `materials` with Playwright slugs (`rag-systems`, …) + tags/relations
- `digest_issue_items` TOC positions
- One `voting_cycles` row (open window 3–16 Apr 2026) when missing

**Apply once on the shared VM** (`knowledge-db.ru`):

1. Prefer Supabase MCP / Studio SQL / `psql` — execute the file as **insert/upsert only**.
2. Or non-interactive CLI when `SUPABASE_ACCESS_TOKEN` is set: `supabase db push` (or Cloud.ru-documented remote equivalent) from repo root.
3. Re-running the file is safe (`ON CONFLICT` on `number` / `slug`; voting cycle uses `WHERE NOT EXISTS`).

**Do not** `TRUNCATE` / `DELETE` wipe / `db reset` on the shared VM. No `cover_url` / `is_current` columns (D-24/D-26).

**Verify after apply:**

```sql
select count(*) from digest_issues where published_at is not null;  -- expect >= 2
select slug from materials where slug = 'rag-systems';             -- expect 1 row
select count(*) from voting_cycles;                                -- expect >= 1
```

Record the apply method in the operator resume signal (or append a one-line note below when confirmed).

**Applied (2026-09-20):** Supabase MCP PostgREST `insert` (service_role) — `raw_sql` unavailable without `POSTGRES_URL`. Verified: published issues=2 (№13, №14), materials=6 (incl. `rag-systems`), voting_cycles=1 (open).

---

## 4c. Phase 3 voting ballot seed + open-cycle trigger (VOTE-01/03/04)

Checked-in idempotent SQL: `supabase-integration/migrations/003_phase3_voting_ballot.sql`.

Creates / upserts (option-a — trigger + use-case):

- `BEFORE INSERT OR UPDATE` trigger `votes_enforce_open_and_topic` — rejects writes when `voting_cycles.status != 'open'` or `topics.cycle_id != votes.cycle_id`
- ≥3 `topics` on the open Phase 2 cycle (titles from `mock.js` votingTopics: LLM / RAG / AutoML) with audit-language `description`
- `topic_materials` links for LLM + RAG only — **AutoML has zero materials** (VOTE-04 «0 материалов»)
- Index `votes_cycle_id_topic_id_idx` for tallies

**Apply once on the shared VM** (`knowledge-db.ru`) **after** Phase 2 seed (open cycle must exist):

1. Prefer non-interactive CLI when `SUPABASE_ACCESS_TOKEN` is set: `supabase db push` (or Cloud.ru-documented remote equivalent) from repo root.
2. If CLI cannot reach the shared VM: apply the SQL file once via Supabase MCP / Studio SQL / `psql` — **insert/upsert + DDL for function/trigger only**; do not reset DB.
3. Re-running the file is safe (`CREATE OR REPLACE` / `DROP TRIGGER IF EXISTS` / `WHERE NOT EXISTS` on topic names / `ON CONFLICT DO NOTHING` for topic_materials).

**Do not** `TRUNCATE` / `DELETE` wipe / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`.

**Verify after apply:**

```sql
-- expect >= 3 topics on an open cycle
select t.name, count(tm.material_id) as materials_count
from topics t
join voting_cycles vc on vc.id = t.cycle_id and vc.status = 'open'
left join topic_materials tm on tm.topic_id = t.id
group by t.id, t.name
order by t.name;
-- expect AutoML row with materials_count = 0
-- expect RAG title present

select tg.tgname
from pg_trigger tg
join pg_class c on c.oid = tg.tgrelid
where c.relname = 'votes' and not tg.tgisinternal;
-- expect votes_enforce_open_and_topic
```

Record the apply method in the operator resume signal (or append a one-line note below when confirmed).

**Applied (2026-09-20):** Seed via Supabase MCP PostgREST `insert` (service_role) — 3 topics on `cycle_id=1` (LLM id=1 materials=3, RAG id=2 materials=5, AutoML id=3 materials=0). DDL (`votes_enforce_open_and_topic` function/trigger + `votes_cycle_id_topic_id_idx`) via Studio SQL — operator confirmed `Success. No rows returned`. `raw_sql`/CLI `db push` unavailable without `POSTGRES_URL` / access token path.

---

## 4d. Phase 4 knowledge chunks + razbory seed (KNOW-01…03, RAZB-01…04)

Checked-in idempotent SQL: `supabase-integration/migrations/004_phase4_knowledge_razbory.sql`.

Creates / upserts (apply **after** Phase 2 materials + Phase 3 topics):

- `search_knowledge_chunks(...)` RPC — hybrid vector (`<=>`) + FTS (`ts_rank_cd`), ready-only, optional `role_filter`, material dedupe; **SECURITY INVOKER**; execute granted to `service_role` only
- ≥4 `knowledge_chunks` rows (1024-d embeddings via deterministic `StubQueryEmbedder` algorithm) spanning **ds** (`pgvector`, `rag-systems`) and **analyst** (`anomaly-detection`, `sql-dashboards`) ready materials
- ≥1 **published** multi-section razbor with metrics table + `notebook_path = hybrid-retrieval.ipynb` (relative to `NOTEBOOK_ROOT`)
- ≥1 **announcement** stub (empty body)
- ≥1 **published overview** razbor without a metrics/quality table

**Apply once on the shared VM** (`knowledge-db.ru`) **after** Phase 2–3 seeds (ready materials + topics must exist):

1. Prefer non-interactive CLI when `SUPABASE_ACCESS_TOKEN` is set: `supabase db push` (or Cloud.ru-documented remote equivalent) from repo root.
2. If CLI cannot reach the shared VM: apply the SQL file once via Supabase MCP / Studio SQL / `psql` — **insert/upsert + CREATE OR REPLACE function only**; do not reset DB.
3. Re-running the file is safe (`ON CONFLICT` on `(material_id, chunk_index)`; razbor inserts use `WHERE NOT EXISTS` on `(topic_id, title)`).

**Notebook file on the API host:** copy `design-frontend/assets/notebooks/hybrid-retrieval.ipynb` into the directory pointed to by `NOTEBOOK_ROOT` (env for live FastAPI). Seeded `notebook_path` is the basename `hybrid-retrieval.ipynb` — resolved under that root by `LocalNotebookStorage`.

**Do not** `TRUNCATE` / `DELETE` wipe / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`. Live search must use this RPC/SQL path — not `list_all` + Python cosine.

**Verify after apply:**

```sql
select count(*) from knowledge_chunks;  -- expect >= 1 (seed targets >= 4)
select count(*) from razbors where status = 'published';  -- expect >= 2
select count(*) from razbors where status = 'announcement';  -- expect >= 1
select proname from pg_proc where proname = 'search_knowledge_chunks';  -- expect 1
```

Also confirm the notebook file exists at `$NOTEBOOK_ROOT/hybrid-retrieval.ipynb` on the API host.

Record the apply method in the operator resume signal (or append a one-line note below when confirmed).

**Applied:** 2026-09-21 — operator confirmed: SQL for `004_phase4_knowledge_razbory.sql` applied on shared VM (checkpoint steps 1, 2, 4); notebook copied to `NOTEBOOK_ROOT` (`hybrid-retrieval.ipynb` present); `NOTEBOOK_ROOT` set in `.env` for local API. Operator confirmed verify queries; exact row counts not logged in the resume signal.

---

## 4e. Phase 5 admin shortlist delivery + demo seed (ADMIN-01/02/07/08, D-78, D-87)

Checked-in idempotent SQL: `supabase-integration/migrations/005_phase5_admin_shortlist.sql`.

Creates / alters (apply **after** Phase 2 materials seed):

- Nullable delivery columns on `digest_shortlist_batches`: `delivery_status`, `recipient_count`, `published_issue_id`, `issue_url` (D-87)
- Optional SECURITY INVOKER RPC `claim_and_publish_digest(...)` — execute granted to **`service_role` only** (revoked from `anon` / `authenticated`)
- Idempotent **demo batch** (week_start `2026-09-15`, unsent) with ≤5 shortlist items: ready materials from Phase 2 seed + one draft (`phase5-admin-draft`) for ADMIN-03 demos; ≥1 item has ≥2 `score_factors` labels — honesty comment in SQL: «demo batch для Phase 5»
- Seed is **not** the PIPE-01 ranking pipeline — product UI stays silent on seed vs pipeline (D-78)

**Digest mailer: stub vs live SMTP (D-15/D-16):** Live `APP_CONTAINER=live` wires **`StubMailer`** while `MAILER=stub` (the default) — the stub reports `delivery_status=stubbed` with `delivered_count=0` and the honest copy «Выпуск опубликован. Доставка писем: stub (0 из M)»; it never implies real delivery. With `MAILER=smtp` **and** a complete `SMTP_*` set, `resolve_mailer` constructs the real `SmtpMailer` (one message per recipient, D-05) and the admin response carries honest `recipient_count` (planned M) + `delivered_count` (delivered N) with a two-sentence message (never an org-wide delivery claim, D-09/D-10/D-11/D-12). With `MAILER=smtp` and `SMTP_*` incomplete the app **fails fast at startup** with `ConfigurationError` (D-16) — never a silent stub fallback. Flipping to live SMTP stays an **ops** decision after the relay smoke below passes; it is not required to merge or run the code.

**MAIL-05 (config boundary):** the digest adapter receives ready primitives from `Settings` and **never reads the process environment** — only `Settings.from_env` reads `MAILER` / `SMTP_*`. `SMTP_TLS_MODE` defaults to `starttls` on port `587` (D-13); connect (10s) and per-send (30s) timeouts are fixed in `Settings`, not env keys (D-14). Env var **names** only are documented here — never commit `SMTP_PASS` or any relay credential (T-21-09).

**Digest SMTP lane smoke + one-command rollback (D-13/D-15, ops):**

1. Set `MAILER=smtp` plus the **complete** `SMTP_*` set from §4.1.1 (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, optional `SMTP_FROM_NAME`, `SMTP_TLS_MODE`) on the API host, then restart the API. A clean start proves the config loaded; an incomplete set fails fast with `ConfigurationError`.
2. As admin, POST `/admin/shortlist/send` and confirm the response `message` reports real «Доставлено N из M» (not the `stub` line) and `delivered_count` reflects N.
3. Confirm per-recipient privacy: one SMTP message per addressee with a single `To` and no cross-employee `Bcc` (D-05), and that the relay logs show the expected number of messages.
4. **Rollback:** set `MAILER=stub` (or unset `MAILER`) and restart the API — `StubMailer` resumes with no config change and no DB write. No migration or data change is involved either way.

The Phase 20 criterion-4 corporate-relay **proof on the GoTrue lane remains an inherited ops gap (D-15)** — this digest code merges and runs under the `MAILER=stub` default without it. Do **not** claim that relay proof is complete here.

**Promote admin profile** for live admin proof (profiles default to `employee`):

```sql
update profiles set role = 'admin' where email = 'your-corporate@example.com';
```

**Apply once on the shared VM** (`knowledge-db.ru`) **after** Phase 2 materials (and preferably Phase 3–4 seeds):

1. Prefer non-interactive CLI when `SUPABASE_ACCESS_TOKEN` is set: `supabase db push` from repo root.
2. If CLI cannot reach the shared VM: apply `005_phase5_admin_shortlist.sql` once via Supabase MCP / Studio SQL / `psql` — **ALTER + insert/WHERE NOT EXISTS only**; do not reset DB.
3. Re-running the file is safe (`ADD COLUMN IF NOT EXISTS`, draft material `ON CONFLICT`, batch/items `WHERE NOT EXISTS`).

**Do not** `TRUNCATE` / `DELETE` wipe / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`. Do not add authenticated RLS policies that let browsers mutate shortlist.

**Verify after apply:**

```sql
select column_name from information_schema.columns
where table_name = 'digest_shortlist_batches'
  and column_name in ('delivery_status', 'recipient_count', 'published_issue_id', 'issue_url');
-- expect 4 rows

select b.id, b.week_start, b.sent_at, count(si.material_id) as items
from digest_shortlist_batches b
left join digest_shortlist_items si on si.batch_id = b.id
where b.sent_at is null and b.week_start = date '2026-09-15'
group by b.id, b.week_start, b.sent_at;
-- expect 1 batch, items between 1 and 5

select proname from pg_proc where proname = 'claim_and_publish_digest';  -- expect 1
```

Record the apply method in the operator resume signal (or append a one-line note below when confirmed).

**Applied:** 2026-09-21 — operator confirmed applied for `005_phase5_admin_shortlist.sql` on shared VM (method not specified).

---

## 4f. Phase 5 follow-up — ordered send RPC (`006_claim_publish_material_ids.sql`)

Checked-in idempotent SQL: `supabase-integration/migrations/006_claim_publish_material_ids.sql`.

**Why:** Code on `experiment/gsd-framework` passes `p_material_ids` into `claim_and_publish_digest` (CR-01). Until this migration runs, live admin send can fail against the migration-005 function signature (6 args only).

**What it does (safe on shared VM):**

- `DROP FUNCTION` the old 6-argument `claim_and_publish_digest`
- `CREATE OR REPLACE` with optional `p_material_ids bigint[] default null` — issue item `position` is set inside the same RPC transaction
- Re-grant `EXECUTE` to **`service_role` only** (revoke from `anon` / `authenticated`)

**Apply once on the shared VM** (`knowledge-db.ru`) **after** `005_phase5_admin_shortlist.sql`:

1. Open Supabase Studio → **SQL Editor** → **New query**  
   URL (self-hosted): `https://knowledge-db.ru/project/default/sql/new`
2. Paste the **entire** file [`006_claim_publish_material_ids.sql`](../../supabase-integration/migrations/006_claim_publish_material_ids.sql) and **Run** once. Expect success / no rows returned.
3. **Supabase MCP (`supabase-self-hosted-mcp`):** `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` (in `.cursor/mcp.json`) are enough for PostgREST tools (`query`, `insert`, `rpc`, …). **`raw_sql` / `transaction` / introspection** need an **additional** `POSTGRES_URL` or `DATABASE_URL` in the same MCP `env` block (direct `pg` pool — see package `loadConfigFromEnv`). Without it, apply 006 via Studio or `psql`, not `raw_sql`.
4. Optional: add `POSTGRES_URL` to MCP env, restart MCP, then run the file via `raw_sql` or `transaction` (no `db reset`).

**Do not** `TRUNCATE` / wipe batches. Re-running 006 is safe (`CREATE OR REPLACE` + idempotent grants).

**Verify after apply** (Studio SQL):

```sql
select pg_get_function_identity_arguments(p.oid) as args
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.proname = 'claim_and_publish_digest';
-- expect args to include p_material_ids bigint[] (7-parameter signature)

select has_function_privilege('service_role', 'public.claim_and_publish_digest(bigint,timestamp with time zone,text,text,text,integer,bigint[])', 'EXECUTE') as service_role_can_execute;
-- expect true
```

Record apply method below when confirmed.

**Applied:** _pending — run Studio step 2 above, then set date/method here._

**CI / Playwright honesty gate (ADMIN-01…08, D-77, D-90):** with default `VITE_USE_MOCKS=true`, run:

```bash
npx playwright test tests/admin.spec.js --reporter=line
```

Covers employee 403 deep-link, empty shortlist, select-all/top-3, preview fail/success gate, draft-in-pool block, stub send «Выпуск опубликован. Доставка писем: stub (0 из 0)» + `/issues/{n}` CTA, already-sent lock. ADMIN-08 returnUrl path: `tests/auth.spec.js` (`returnUrl=/issues/13` + open-redirect rejection). Live SMTP remains out of scope — stub honesty only (§4e above).

---

## 4g. Phase 13 test-header scrub (ADUX-04)

Checked-in idempotent SQL: `supabase-integration/migrations/010_phase13_scrub_test_header.sql`.

**Why:** Phase 10 UAT observed leaked chrome (`test-header` / siblings) on admin preview surfaces. ADUX-04 / D-20 require a defensive one-way scrub of materials text columns plus regression asserts — **no** runtime strip in renderers (D-17).

**Closed ban tokens (D-18):** `test-header`, `test_header`, `testheader` (case-insensitive). Synced helpers: `backend.domain.email_chrome.FORBIDDEN_LOWER` ↔ `web/src/utils/forbiddenChrome.js`.

**What it does (safe on shared VM):**

- `UPDATE public.materials` — `regexp_replace` on `title`, `dek`, `body_markdown`, `provenance_label` where `lower(col)` matches any closed token
- Idempotent: re-run updates 0 rows when already clean
- Historical row may already be gone (0-row apply OK)

**Apply once on the shared VM** (`knowledge-db.ru`) **after** shipping `010_*.sql` (decision: `apply-after-sql`):

1. Open Supabase Studio → **SQL Editor** → **New query**  
   URL (self-hosted): `https://knowledge-db.ru/project/default/sql/new`
2. Paste the **entire** file [`010_phase13_scrub_test_header.sql`](../../supabase-integration/migrations/010_phase13_scrub_test_header.sql) and **Run** once as the **postgres** role (or equivalent DDL-capable role). Expect success; row count may be 0.
3. Optional: when `POSTGRES_URL` is configured for Supabase MCP, `raw_sql` may run the same UPDATE — **never** `db reset`.

**Do not** `TRUNCATE` / wipe materials / `db reset` on the shared VM.

**Verify after apply** (Studio SQL — expect `0`):

```sql
select count(*) as remaining_ban_hits
from public.materials
where lower(coalesce(title, '')) like '%test-header%'
   or lower(coalesce(title, '')) like '%test_header%'
   or lower(coalesce(title, '')) like '%testheader%'
   or lower(coalesce(dek, '')) like '%test-header%'
   or lower(coalesce(dek, '')) like '%test_header%'
   or lower(coalesce(dek, '')) like '%testheader%'
   or lower(coalesce(body_markdown, '')) like '%test-header%'
   or lower(coalesce(body_markdown, '')) like '%test_header%'
   or lower(coalesce(body_markdown, '')) like '%testheader%'
   or lower(coalesce(provenance_label, '')) like '%test-header%'
   or lower(coalesce(provenance_label, '')) like '%test_header%'
   or lower(coalesce(provenance_label, '')) like '%testheader%';
```

Record apply method below when confirmed.

**Applied:** 2026-10-03 — Studio SQL Editor (postgres role) on shared knowledge-db VM; file `010_phase13_scrub_test_header.sql`. Operator confirmed («готово»). Post-apply Supabase MCP PostgREST probe: materials `title ilike %test-header%` → `[]`. Full `remaining_ban_hits` SELECT not pasted by operator; accepted per prior-phase pattern (operator confirm + empty probe).

---

## 4h. Phase 16 pipeline config singleton (PIPE-01…03, D-08)

Checked-in idempotent SQL: `supabase-integration/migrations/011_phase16_pipeline_config.sql`.

**Why:** PIPE-03 requires the validated admin pipeline config to persist behind the
`PipelineConfigRepository` port and be readable on the next admin session. The MVP stores one
global row (`id = 1`) holding the raw YAML document + `updated_at` (D-08/D-11). The SPA never
touches storage — it reaches the config only through `web/src/services/pipelineConfigApi.js`
(PIPE-03 hard boundary).

**What it does (safe on shared VM):**

- `create table if not exists public.pipeline_config` — singleton `id integer primary key default 1 check (id = 1)`, `yaml text not null default ''`, `updated_at timestamptz not null default now()`
- `alter table public.pipeline_config enable row level security;` — deny-by-default with **no** permissive policy (only the service_role composition adapter reaches it; admin gating is backend `require_admin`, D-10)
- Idempotent: re-running creates nothing new and mutates no rows

There is **no `supabase/config.toml`** in this repo, so `supabase db push` is not configured
locally — use Supabase Studio SQL or `psql` (established 005–010 path).

**Apply once on the shared VM** (`knowledge-db.ru`):

1. Open Supabase Studio → **SQL Editor** → **New query**  
   URL (self-hosted): `https://knowledge-db.ru/project/default/sql/new`
2. Paste the **entire** file [`011_phase16_pipeline_config.sql`](../../supabase-integration/migrations/011_phase16_pipeline_config.sql) and **Run** once. Expect success / no rows returned.
3. Optional: when `POSTGRES_URL` is configured for Supabase MCP, `raw_sql` may run the same DDL — **never** `db reset`.

**Do not** `TRUNCATE` / wipe `pipeline_config` / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`.

**Verify after apply** (Studio SQL):

```sql
select count(*) from public.pipeline_config;                            -- expect 0 or 1
select relrowsecurity from pg_class where relname = 'pipeline_config';  -- expect t
select count(*) from pg_policies where tablename = 'pipeline_config';   -- expect 0
```

Record apply method below when confirmed.

**Applied (2026-10-04):** operator applied `011_phase16_pipeline_config.sql` once on the shared knowledge-db VM (Studio SQL / psql path; no `supabase/config.toml` in repo). Operator confirmed the file applied. Post-apply read-only verification via the Supabase PostgREST client against the live project: `select id,yaml,updated_at from public.pipeline_config limit 5` → `[]` (table exists and is reachable; 0 visible rows under RLS deny-by-default with no permissive policy). RLS enabled with zero policies per the migration contract. No destructive statement was run against the shared DB.

---

## 4i. Phase 23 admin ingest sources (SRC-01/SRC-03, D-16/D-17)

Checked-in idempotent SQL: `supabase-integration/migrations/012_phase23_ingest_sources.sql`.

**Why:** SRC-01 requires the admin channel/playlist subscription list to persist behind the
`IngestSourceRepository` port and survive reload on the live DB. The table is
**`public.pipeline_ingest_sources`** — do **not** reuse or alter `public.ingestion_sources`
from migration 001 (that table models fetched content items and is the FK target of
`materials` / `ingestion_jobs` / `source_texts`) (D-16). The SPA never touches storage —
it reaches sources only through `web/src/services/ingestSourcesApi.js` (SRC-03).

**What it does (safe on shared VM):**

- `create table if not exists public.pipeline_ingest_sources` — `bigint generated always as identity` PK, `kind text not null check (kind in ('channel', 'playlist'))`, `source_id text not null`, `label text`, `is_enabled boolean not null default true`, `created_at`/`updated_at timestamptz not null default now()`, `unique (kind, source_id)`
- `alter table public.pipeline_ingest_sources enable row level security;` — deny-by-default with **no** permissive policy (only the service_role composition adapter reaches it; admin gating is backend `require_admin`, D-17)
- Idempotent: re-running creates nothing new and mutates no rows

There is **no `supabase/config.toml`** in this repo, so Studio SQL / `psql` is the established
path (same as §4h). Prefer non-interactive `supabase db push` with `SUPABASE_ACCESS_TOKEN`
when that path works for this project; otherwise use Studio / `psql` below.

**Apply once on the shared VM** (`knowledge-db.ru`):

1. Open Supabase Studio → **SQL Editor** → **New query**  
   URL (self-hosted): `https://knowledge-db.ru/project/default/sql/new`
2. Paste the **entire** file [`012_phase23_ingest_sources.sql`](../../supabase-integration/migrations/012_phase23_ingest_sources.sql) and **Run** once. Expect success / no rows returned.
3. Optional: when `POSTGRES_URL` is configured for Supabase MCP, `raw_sql` may run the same DDL — **never** `db reset`.

**Do not** `TRUNCATE` / wipe `pipeline_ingest_sources` / alter `ingestion_sources` / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`.

**Verify after apply** (Studio SQL):

```sql
select count(*) from public.pipeline_ingest_sources;                            -- expect 0+ (empty OK)
select relrowsecurity from pg_class where relname = 'pipeline_ingest_sources';  -- expect t
select count(*) from pg_policies where tablename = 'pipeline_ingest_sources';   -- expect 0
-- Confirm ingestion_sources was not altered (structure still present; no Phase-23 columns):
select count(*) from information_schema.columns
  where table_schema = 'public' and table_name = 'ingestion_sources';           -- expect > 0
```

Record apply method below when confirmed.

**Applied (2026-10-17):** operator applied `012_phase23_ingest_sources.sql` once on the shared knowledge-db VM (Studio SQL / psql path; no `supabase/config.toml` in repo). Operator confirmed resume-signal «applied» and verify `select count(*) from public.pipeline_ingest_sources` → `0` (empty OK). RLS enabled with zero policies per the migration contract (D-17); operator did not restate the `relrowsecurity` / `pg_policies` checklist lines — accepted per checkpoint resume-signal and prior-phase pattern (§4h). No destructive statement was run against the shared DB. `ingestion_sources` was not altered (D-16).

---

## 4j. Phase 24 scheduled ingestion (ING-05/ING-06, D-06/D-14)

Checked-in idempotent SQL: `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql`.

**Why:** ING-05 needs a durable high-water mark per enabled source; ING-06 needs a singleton
schedule (`enabled` / `time_of_day` / `days_of_week` / `last_run_at`) so `ingest-collect` can
decide «пора / не пора» in `Europe/Moscow` without Persistent=true on the systemd timer (D-21).
Cursor columns live on `public.pipeline_ingest_sources` so deleting a source removes its cursor
(D-06). Application code supplies schedule defaults when no row exists — the migration must
**not** seed `id = 1` (D-14).

**What it does (safe on shared VM):**

- `alter table public.pipeline_ingest_sources add column if not exists last_seen_published_at timestamptz`
- `alter table public.pipeline_ingest_sources add column if not exists last_seen_video_id text`
- `create table if not exists public.ingestion_schedule` — singleton `id integer primary key default 1 check (id = 1)`, `enabled boolean not null default true`, `time_of_day time not null default '06:00'`, `days_of_week smallint[]` with ISO-week CHECK, `last_run_at timestamptz`, `updated_at timestamptz not null default now()`
- `alter table public.ingestion_schedule enable row level security;` — deny-by-default with **no** permissive policy (only the service_role composition adapter reaches it; admin gating is backend `require_admin` in Phase 24-05) (T-24-10)
- Idempotent: re-running adds nothing new and mutates no rows; no `INSERT`, no `CREATE POLICY`, no destructive statements; does **not** touch `public.ingestion_sources`

There is **no `supabase/config.toml`** in this repo, so Studio SQL / `psql` is the established
path (same as §4h/§4i).

**Apply once on the shared VM** (`knowledge-db.ru`):

1. Open Supabase Studio → **SQL Editor** → **New query**
   URL (self-hosted): `https://knowledge-db.ru/project/default/sql/new`
2. Paste the **entire** file [`013_phase24_scheduled_ingestion.sql`](../../supabase-integration/migrations/013_phase24_scheduled_ingestion.sql) and **Run** once. Expect success / no rows returned.
3. Optional: when `POSTGRES_URL` is configured for Supabase MCP, `raw_sql` may run the same DDL — **never** `db reset`.

**Do not** `TRUNCATE` / wipe `pipeline_ingest_sources` / `ingestion_schedule` / alter `ingestion_sources` / `db reset` on the shared VM. Never expose `SUPABASE_SECRET_KEY` via `VITE_`. Never insert a seed row into `ingestion_schedule` — defaults come from code until the first stamp/save.

**Verify after apply** (Studio SQL):

```sql
select column_name, data_type from information_schema.columns
  where table_schema = 'public' and table_name = 'pipeline_ingest_sources'
    and column_name in ('last_seen_published_at', 'last_seen_video_id');
  -- expect 2 rows: timestamptz / text (timestamp with time zone / text)
select enabled, time_of_day, days_of_week from public.ingestion_schedule;  -- expect 0 rows
select relrowsecurity from pg_class where relname = 'ingestion_schedule';  -- expect t
select count(*) from pg_policies where tablename = 'ingestion_schedule';   -- expect 0
-- Confirm ingestion_sources was not altered:
select count(*) from information_schema.columns
  where table_schema = 'public' and table_name = 'ingestion_sources';           -- expect > 0
```

Record apply method below when confirmed.

**Applied (2026-10-18):** operator applied `013_phase24_scheduled_ingestion.sql` once on the shared knowledge-db VM (Studio SQL / psql path; no `supabase/config.toml` in repo). Operator confirmed resume-signal «applied». Post-apply read-only verification via Supabase PostgREST against the live project: `select * from public.ingestion_schedule limit 5` → `[]` (table exists and is reachable; 0 seed rows — matches D-14; defaults come from application code). Unit text-contract `tests/unit/test_phase24_migration_013.py` remains green. No destructive statement was run against the shared DB.

---

## 4k. Phase 24 ingest timer (ING-06, D-19/D-20/D-21)

Checked-in units: `deploy/systemd/digest-ingest.service`, `deploy/systemd/digest-ingest.timer`, `deploy/systemd/digest-ingest-alert.service`.

**Run limit (D-23):** the service is `Type=oneshot`, so its **start phase** is bounded by `TimeoutStartSec=1800`. `RuntimeMaxSec=` has no effect on `Type=oneshot` — systemd 255 logs «RuntimeMaxSec= has no effect in combination with Type=oneshot. Ignoring.» and the run stays unbounded — so it must not be reintroduced. On expiry systemd SIGTERMs the unit cgroup and escalates to SIGKILL after `TimeoutStopSec` (default 90 s); the run never reaches its final summary, `last_run_at` is not stamped, and the next tick is due from the same cursor.

**Why the timer polls every 15 minutes:** the schedule lives in `public.ingestion_schedule` (`enabled` / `time_of_day` / `days_of_week` / `last_run_at`). systemd cannot read the DB for OnCalendar, so the timer only wakes `ingest-collect`; `due_decision` decides «пора / не пора». Persistent is false — catch-up after downtime is the due-check against `last_run_at`, not systemd (D-21).

**Prerequisites** (clean VM):

1. System account: `getent passwd digestcds || sudo useradd --system --home-dir /opt/digest-cds --shell /usr/sbin/nologin digestcds` — without it the unit User (digestcds) fails with «Failed to determine user credentials».
2. Install tree: `sudo install -d -o digestcds -g digestcds /opt/digest-cds`, then check out this repo into `/opt/digest-cds` (WorkingDirectory `/opt/digest-cds`).
3. Venv as the service user: `sudo -u digestcds bash -lc 'cd /opt/digest-cds && uv sync'` — `/opt/digest-cds/.venv/bin/ingest-collect` appears only after the entry point is installed and must be executable for `digestcds`.
4. Env file: `sudo mkdir -p /etc/digest-cds`, then `sudo install -m 600 -o root -g root ingestion-service/.env.example /etc/digest-cds/ingest.env`. systemd reads EnvironmentFile as root before dropping privileges, so mode 0600 owner root is fine for the service User digestcds. Fill **exactly the keys `Settings.from_env` reads** (mirror `ingestion-service/.env.example`):
   - required non-empty: `SUPABASE_URL=`, `SUPABASE_SECRET_KEY=`, `DEEPSEEK_API_KEY=`
   - defaults OK when blank: `DEEPSEEK_BASE_URL=`, `DEEPSEEK_MODEL=`, `SHORTLIST_BATCH_SIZE=`, `MAX_TRANSCRIPT_CHARS=`
   - optional: `YOUTUBE_PROXY_URL=`
   - Phase 24: `INGEST_TEMPLATE=lecture`, `INGEST_MAX_VIDEOS_PER_SOURCE=5`
   - Do **not** add keys from other modules (e.g. Foundry) — this service does not read them.

**Install:**

```bash
sudo install -m 644 deploy/systemd/digest-ingest.service \
  deploy/systemd/digest-ingest.timer \
  deploy/systemd/digest-ingest-alert.service \
  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start digest-ingest.service   # smoke once
sudo systemctl enable --now digest-ingest.timer
```

**Verify:**

```bash
systemctl list-timers digest-ingest.timer
journalctl -u digest-ingest.service -n 30 --no-pager
systemctl status digest-ingest-alert.service
```

**Do not:** run the unit as root; put secrets into the unit files; enable Persistent for missed runs; create `/run/digest-ingest` by hand, change its owner, or add tmpfiles.d rules — RuntimeDirectory recreates the directory (owner = service User digestcds) on every start, including the first after reboot.

**Permissions note:** mode 0600 on `/etc/digest-cds/ingest.env` is **not** covered by the text-contract test — verify with `ls -l /etc/digest-cds/ingest.env` on the VM.

Installed (дата):

---

## 5. Live FE↔BE proof checklist (D-10)

With API on `:8000`, Vite on `:5173`, `APP_CONTAINER=live`, and `VITE_USE_MOCKS=false`:

1. **Existing user:** open `/login` and sign in with corporate **email + password only** (no name/«Логин» field on login) → land on current issue `/` (or honor `returnUrl`). Header shows the stored display name (or email fallback), not the mock «Мария Сидорова».
2. **New user:** open `/register`, fill email, password, and **«Логин»** (display nickname) → after successful signUp, land on issue (or `returnUrl`). «Логин» is saved to `profiles.display_name` / Auth metadata at registration only.
3. Confirm **GET /me** succeeds — PlatformProofBanner shows name/email/role, or Network tab shows HTTP 200 with `display_name`.
4. Click **«Проверить ping»** (POST `/me/ping`) → banner shows `ok · id …`.
5. Confirm a new `activity_events` row with `kind = platform_ping` (Studio SQL / MCP `query` — **select/insert only**, no destructive DDL).
6. Attempt a **disallowed** domain on `/login` or `/register` — inline rejection; no usable session (AUTH-01).
7. In API stdout, confirm structured logs include `request_id` for the `/me` and `/me/ping` calls.

Phase 1 platform proof is this checklist. Issue/vote content may still be mock until later phases (D-12).

---

## 5b. Phase 4 optional live FE↔BE proof (KNOW-*/RAZB-*)

CI / Playwright honesty suites use **mocks** (`VITE_USE_MOCKS=true`). After **04-08** seed + `NOTEBOOK_ROOT` (see §4d), optional human proof against live API:

**Prerequisites:** API on `:8000` with `APP_CONTAINER=live`, Vite on `:5173` with `VITE_USE_MOCKS=false`, corporate JWT session, migration `004` applied, notebook file under `NOTEBOOK_ROOT`.

1. **Knowledge:** `/knowledge` — Submit/Enter a real query; whitespace shows «Введите запрос» without a network search; Analyst/DS chips filter; Analyst empty never substitutes DS tops; «Сбросить фильтр» keeps `q`; DS hit opens `/materials/{slug}`; no score badges on rows.
2. **Razbory list:** `/razbory` shows chronology (date/status) or empty CTA → `/voting`.
3. **Razbor detail:** multi-section published longread — sticky TOC jumps; «Качество» vs «Обзор» labeling honest; soft 404 for unknown id.
4. **Notebook:** published with `notebook_path` — dual strip, download works; missing notebook — strip stays, download disabled, «Notebook скоро будет».

Record pass/fail in the verify-work session notes. This path is **not** required for CI green.

---

## 5c. Optional live YouTube captions / oEmbed (Phase 7, D-20)

Default `uv run pytest` collects **only** `tests/unit` (`testpaths`) — no network. Optional live stubs live under `tests/integration/` and skip unless the flag is set.

**Path-explicit command** (required — a bare `-m integration` collects zero tests because `testpaths` excludes `tests/integration`):

```bash
RUN_YOUTUBE_INTEGRATION=1 uv run pytest tests/integration -m integration
```

Use `YOUTUBE_PROXY_URL` from §1 when egress to YouTube is blocked (Cloud.ru → `youtube_blocked`). Pipeline order captions-then-metadata is Phase 10 policy (D-24) — these stubs do not implement the orchestrator.

---

## 5d. Phase 10 CLI UAT (`ingest` — CLI-03 / CLI-05 / D-02)

Manual four-video proof that live composition wires YouTube → DeepSeek → Supabase drafts into `/admin/digest`. Checklist: [`.planning/phases/10-cli-composition-uat/10-UAT.md`](../../.planning/phases/10-cli-composition-uat/10-UAT.md).

**Env (CLI-05 / D-02):** copy `ingestion-service/.env.example` → `ingestion-service/.env` with live `DEEPSEEK_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (service_role). Do not point UAT at the root backend `.env`. Optional: `YOUTUBE_PROXY_URL` when YouTube egress is blocked.

```bash
# from repo root — process-scoped secrets only via --env-file
uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast
```

Pick four captioned URLs at UAT time (lecture+ru, lecture+en, podcast+ru, podcast+en). Record `material_id` / `slug` / `already_saved` in `10-UAT.md`. Confirm each draft in `/admin/digest` (unsent shortlist, `status=draft`, Russian body, EN provenance suffix when applicable). Do not paste service_role or DeepSeek keys into UAT notes (T-10-11). No Playwright for this UAT; no backend/SPA edits required for drafts to appear.

---

## 5e. Phase 24 scheduled-ingestion UAT (ING-06, D-13/D-21/D-23)

Operator checklist after §4k install + §4j migration. Secrets stay in `/etc/digest-cds/ingest.env` (`ls -l` must show `0600` — text tests do not cover FS mode).

1. **Smoke:** `sudo systemctl start digest-ingest.service` then `journalctl -u digest-ingest.service -n 50 --no-pager` shows the two-line collect summary (or `not due: …`).
2. **Already ran:** within 15 minutes, `sudo systemctl start digest-ingest.service` again prints `not due: already_ran` and exits 0 (no YouTube/LLM).
3. **Forced due:** `sudo systemctl stop digest-ingest.timer`, shift `last_run_at` into the past with the SQL from §4j verify notes / Studio, then `sudo systemctl start digest-ingest.service` — a due run collects again.
4. **Manual retry (D-13):** retry a skipped video with the existing CLI — no new flag:
   `uv run --env-file ingestion-service/.env ingest <video_id> --template lecture`
5. **Run limit (TimeoutStartSec, D-23):** the service is `Type=oneshot`, so the bound is its **start phase** at 1800 s; a killed run does not reach its summary, `last_run_at` is **not** stamped, and the next tick is due again from the same cursor.
   - (i) `systemctl show digest-ingest.service -p TimeoutStartUSec` reports `TimeoutStartUSec=30min`.
   - (ii) a fresh `sudo systemctl start digest-ingest.service` produces no «has no effect in combination with Type=oneshot» warning: `journalctl -u digest-ingest.service --since "2 min ago" --no-pager` is clean of it.
   - (iii) prove the kill with a scratch unit: `/etc/systemd/system/uat-timeoutstart.service` with `[Unit]` → `Description=UAT: TimeoutStartSec bounds a Type=oneshot`, and `[Service]` → `Type=oneshot`, `TimeoutStartSec=3`, `ExecStart=/bin/sleep 10`; then `sudo systemctl daemon-reload`; `start=$(date +%s); sudo systemctl start uat-timeoutstart.service; rc=$?; end=$(date +%s)` (expect a non-zero `rc` and ≈3 s, not 10 s); `systemctl show uat-timeoutstart.service -p Result -p ExecMainStatus` (expect `Result=timeout`, `ExecMainStatus=15`); finally `sudo rm /etc/systemd/system/uat-timeoutstart.service` and `sudo systemctl daemon-reload`.
   - The discriminating real-unit round-trip (stamp-vs-kill) lives in `.planning/phases/24-scheduled-ingestion/24-07-PLAN.md`, checkpoint T3 step 5: seed the `ingestion_schedule` singleton and one enabled source, prove a **control** run stamps, apply the `TimeoutStartSec=2` runtime drop-in, confirm `Result=timeout` with `last_run_at` still at the seeded value, then `systemctl revert` and show the next start stamps. A bare `last_run_at` comparison without the control run is not acceptable — a zero-source run also skips the stamp (D-27), so it would not discriminate.
6. **flock busy (D-20):** while a run holds `/run/digest-ingest/lock`, a second start exits **75**; `systemctl status digest-ingest.service` does **not** go failed; `digest-ingest-alert.service` does **not** start (`SuccessExitStatus=0 75`).
7. **Live feed:** with outbound access to `youtube.com`, one enabled source, and an empty cursor, a due run yields at least one `VideoRef` with a non-empty `video_id` (proves `parse_feed` beyond the synthetic fixture).
8. **Alert codes:** forced exit 1 → journald line with «partial failure»; exit 2 → «no source could be read». Confirm via `journalctl -u digest-ingest-alert.service` after `OnFailure=`.

Record pass/fail in the verify-work session notes. This path is **not** required for CI green.
