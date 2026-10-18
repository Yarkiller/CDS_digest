---
phase: 01
slug: platform-foundation-auth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-19
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Commands sourced from `01-RESEARCH.md` Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.3.0; Playwright @playwright/test ^1.62.1; Node built-in `node --test` (FE domain helper) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| **Quick run command** | `uv run pytest tests/unit/test_<focused>.py -x` |
| **Full suite command** | `npm run test:unit` && `npm run test:web` |
| **Estimated runtime** | ~30–90s focused; ~2–5m full |

---

## Sampling Rate

- **After every task commit:** Run the task’s `<automated>` command only (prefer focused pytest / `node --test`, not full Playwright)
- **After every plan wave:** `npm run test:unit`; if FE plan touched, also `npx playwright test --project=web tests/auth.spec.js`
- **Before `/gsd-verify-work`:** Full unit + web Playwright green; live `/me`+`/me/ping` proof documented
- **Max feedback latency:** Prefer &lt;60s per task; Playwright reserved for AUTH-02/03 flow contracts

---

## Requirement → Automated Command Map

| Req ID | Behavior | Test Type | Automated Command | Wave 0 File | Plans |
|--------|----------|-----------|-------------------|-------------|-------|
| PLAT-01 | Schema contract still holds; connectivity documented | unit + docs/human | `uv run pytest tests/unit/test_schema_migration_contract.py -x` | ✅ exists | 04, 06 |
| PLAT-02 | `GET /health` → 200 | API unit | `uv run pytest tests/unit/test_http_health.py -x` | ❌ | 01 |
| PLAT-03 | Authenticated `GET /me` (API + FE client) | API unit + Playwright mock | `uv run pytest tests/unit/test_http_me.py -x`; `npx playwright test --project=web tests/auth.spec.js` | ❌ | 02, 05, 06 |
| PLAT-04 | `POST /me/ping` via port; live adapter contract | use-case/API unit | `uv run pytest tests/unit/test_record_platform_ping.py tests/unit/test_supabase_ping_recorder_contract.py -x` | ❌ | 03, 04, 06 |
| PLAT-05 | `.env.example` present; not gitignored | file assert | `git check-ignore -v .env.example` must fail; `Test-Path .env.example` | ❌ | 01 |
| PLAT-06 | CORS allowlist reflects Origin | API unit | `uv run pytest tests/unit/test_cors.py -x` | ❌ | 01 |
| PLAT-07 | `X-Request-ID` + login network UX | API unit + Playwright | `uv run pytest tests/unit/test_request_id.py -x`; `npx playwright test --project=web tests/auth.spec.js` | ❌ | 01, 05 |
| PLAT-08 | Local + Cloud.ru deploy-path docs | path assert | `Test-Path docs/agents/local-platform-runbook.md, docs/agents/cloudru-app-deploy-path.md` | ❌ | 06 |
| AUTH-01 | Disallowed email → 403 API; UI inline reject | API unit + `node --test` + Playwright | `uv run pytest tests/unit/test_http_me.py tests/unit/test_auth_email_domain.py -x`; `node --test web/src/services/emailDomain.test.js`; Playwright domain case | ❌ | 02, 05 |
| AUTH-02 | Login → `/` or `returnUrl` | Playwright | `npx playwright test --project=web tests/auth.spec.js` | ❌ | 05 |
| AUTH-03 | JWT gate on `/me`; SPA RequireAuth → login | API unit + Playwright | `uv run pytest tests/unit/test_http_me.py -x`; Playwright guard case | ❌ | 02, 05 |

**AUTH-03 deferral (explicit):** Non-admin calls to admin APIs returning 403 are **out of Phase 1** (no admin routes until Phase 5). Phase 1 delivers JWT deps + SPA `RequireAuth` only.

**Live FE↔BE (PLAT-03/04):** Manual / local optional proof — see Manual-Only Verifications. Not gated on CI credentials.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|----------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | — (T-01-SC) | T-01-SC | Human confirms package legitimacy | checkpoint | — | n/a | ⬜ pending |
| 01-01-02 | 01 | 1 | PLAT-02/06/07 | T-01-03, T-01-04 | Public health; CORS allowlist; request_id echo | API unit | `uv run pytest tests/unit/test_http_health.py tests/unit/test_cors.py tests/unit/test_request_id.py -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PLAT-05 | T-01-06* | Env template commitable; secrets not in example | file assert | `git check-ignore -v .env.example` fails; `Test-Path .env.example` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | AUTH-01 | T-01-02 | Corporate email domain helper | unit | `uv run pytest tests/unit/test_auth_email_domain.py -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | AUTH-01/03, PLAT-03 | T-01-01, T-01-02 | ES256 JWT verify; `/me` 401/200/403 | API unit | `uv run pytest tests/unit/test_jwt_verify.py tests/unit/test_http_me.py -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | PLAT-04 | — | Ping use-case + in-memory recorder | unit | `uv run pytest tests/unit/test_record_platform_ping.py -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 3 | PLAT-04, AUTH-03 | T-01-01 | `POST /me/ping` JWT-gated; container wiring | API unit | `uv run pytest tests/unit/test_http_me.py tests/unit/test_composition_container.py -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 4 | PLAT-04 | T-01-06 | Adapter contract offline stubs | unit | `uv run pytest tests/unit/test_supabase_ping_recorder_contract.py -x` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 4 | PLAT-01/04 | T-01-06, T-01-08 | Live composition wiring (mocked factories) | unit | `uv run pytest tests/unit/test_live_container_wiring.py -x` | ❌ W0 | ⬜ pending |
| 01-04-03 | 04 | 4 | AUTH-01, D-08 | T-01-07 | Manual Auth users | human | — | n/a | ⬜ pending |
| 01-05-01 | 05 | 4 | AUTH-01 | T-01-11 | FE domain helper (fast) | node unit | `node --test web/src/services/emailDomain.test.js` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 4 | AUTH-01/02/03 | T-01-09–12 | Login + guard + redirect | Playwright | `npx playwright test --project=web tests/auth.spec.js` | ❌ W0 | ⬜ pending |
| 01-05-03 | 05 | 4 | PLAT-03/07 | T-01-10 | meApi mock path + error codes | Playwright | `npx playwright test --project=web tests/auth.spec.js` | ❌ W0 | ⬜ pending |
| 01-06-01 | 06 | 5 | PLAT-08 | T-01-13 | Local runbook linked | path | `Test-Path docs/agents/local-platform-runbook.md`; README link | ❌ W0 | ⬜ pending |
| 01-06-02 | 06 | 5 | PLAT-08 | T-01-13 | Cloud.ru path docs (no deploy) | path | `Test-Path docs/agents/cloudru-app-deploy-path.md` | ❌ W0 | ⬜ pending |
| 01-06-03 | 06 | 5 | PLAT-03/04 | T-01-14 | Live FE↔BE proof | human | — | n/a | ⬜ pending |

\*Related: secret key must not appear under `VITE_` (enforced in `.env.example` content review + Plan 05 threat model).

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_http_health.py` — PLAT-02
- [ ] `tests/unit/test_cors.py` — PLAT-06
- [ ] `tests/unit/test_request_id.py` — PLAT-07
- [ ] `tests/unit/test_auth_email_domain.py` — AUTH-01
- [ ] `tests/unit/test_jwt_verify.py` — ES256 / JWKS helpers
- [ ] `tests/unit/test_http_me.py` — AUTH-01/03, PLAT-03
- [ ] `tests/unit/test_record_platform_ping.py` — PLAT-04
- [ ] `tests/unit/test_composition_container.py` — extend existing
- [ ] `tests/unit/test_supabase_ping_recorder_contract.py` — PLAT-04 adapter
- [ ] `tests/unit/test_live_container_wiring.py` — live builder
- [ ] `web/src/services/emailDomain.test.js` — AUTH-01 FE (fast path)
- [ ] `tests/auth.spec.js` — AUTH-01/02/03 Playwright
- [ ] `.env.example` + `!.env.example` gitignore exception — PLAT-05
- [ ] `uv add` FastAPI stack to `backend`; `supabase` to `supabase-integration` (after legitimacy checkpoint)
- [ ] Optional: `tests/integration/` marker excluded from default `testpaths`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Remote Supabase connectivity + schema already applied | PLAT-01 | Shared VM; no re-provision | Follow README / Plan 04 notes; optional MCP ping |
| Manual corporate Auth users | AUTH-01 / D-08 | Shared VM — no automated seed | Plan 04 human-action checkpoint |
| Live login → GET /me → POST /me/ping → `activity_events` row | PLAT-03/04, D-10 | Credentials not in CI | Plan 06 human-verify + `docs/agents/local-platform-runbook.md` |
| Auth domain hook on GoTrue (optional) | AUTH-01 / D-04 | May be unavailable on self-host | Document UI+API gates if hook missing |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 / human checkpoint dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency targets met (focused pytest / `node --test` &lt;60s; Playwright for flows only)
- [ ] `nyquist_compliant: true` set in frontmatter after `/gsd-validate-phase` or executor Wave 0 complete

**Approval:** pending
