---
phase: 2
slug: issue-materials-archive
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-09-20
verified: 2026-09-20
register_authored_at_plan_time: true
---

# Phase 2 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> L1 ASVS grep-depth verification (workflow.security_asvs_level=1). Plan-time STRIDE registers from 02-01…02-06 PLAN.md.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| SPA → FastAPI content GETs | Bearer JWT on `/issues/*`, `/archive`, `/materials/{slug}` | access_token; untrusted path/query |
| FastAPI → use-case → port | Authn enforced; reader content is shared among authenticated users | Issue/Material DTOs |
| composition/live.py → Supabase | service_role bypasses RLS — server-only | digest_issues, materials, voting_cycles reads |
| Markdown → React tree | Editorial body rendered via react-markdown | body_markdown (sanitize boundary) |
| Live API failure → UI | Error UX must not leak internals or fake success | ContentApiError → ServiceUnavailable |
| Seed SQL → shared Postgres | Operator-applied; wipe risk if destructive | Insert/upsert seed rows |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | Information Disclosure | content GETs / draft materials | high | mitigate | `Depends(get_principal)` on all content routes; draft/missing material → `MaterialNotFoundError` → 404; unpublished issue → 404 | closed |
| T-02-02 | Spoofing | contentApi mock/live | high | mitigate | Live path throws `ContentApiError` on failure; never silent mock fallback (D-21); `armFailNextContentFetch` → ServiceUnavailable | closed |
| T-02-03 | Elevation of Privilege | service_role client | high | mitigate | `create_service_role_client` only in `composition/live.py`; never Vite-prefixed; SPA content via FastAPI only | closed |
| T-02-04 | Tampering | 002 seed SQL | medium | mitigate | Idempotent `ON CONFLICT` upserts; no `TRUNCATE`/`DELETE`/`DROP`; insert-only seed | closed |
| T-02-05 | Information Disclosure / Elevation | RLS gaps on tags/cycles | high | mitigate | Content reads only via service_role adapters in live container; no SPA PostgREST content reads | closed |
| T-02-06 | Tampering / XSS | react-markdown | high | mitigate | `rehype-sanitize` on MaterialPage; no `rehype-raw`; no `dangerouslySetInnerHTML`; versions in package.json + lockfile | closed |
| T-02-07 | Information Disclosure | ServiceUnavailable splash | medium | mitigate | Fixed friendly Russian copy only — no HTTP status codes or stacktraces in render (D-23) | closed |
| T-02-SC | Tampering | npm/pip installs | low | accept | No new packages in 02-01/02/03/05/06; 02-04 markdown pkgs Approved + version-declared — see Accepted Risks | closed |
| T-02-01-cycle | Information Disclosure | voting_cycle stub fields | low | accept | Authenticated readers only; no PII in cycle stub (D-33) — see Accepted Risks | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `block_on: high` count toward `threats_open`*
*Disposition: mitigate · accept · transfer*

### Evidence (L1)

- `backend/.../interface/http/routes/issues.py` — `get_principal` on `/current`, `/{number}`, `/archive`
- `backend/.../interface/http/routes/materials.py` — `get_principal`; draft → 404 `material_not_found`
- `backend/.../application/use_cases/get_material_for_reader.py` — non-READY → `MaterialNotFoundError`
- `backend/.../composition/live.py` — sole `create_service_role_client` wiring for issues/materials/cycles
- `web/src/services/contentApi.js` — live failures → `ContentApiError` / `throwNetwork`; mock only when `isMocksEnabled()`
- `web/src/components/ServiceUnavailable.jsx` — fixed copy; no status/stack props
- `web/src/pages/MaterialPage.jsx` — `rehypePlugins={[rehypeSlug, rehypeSanitize]}`; no rehype-raw
- `web/src/services/` — content path has zero supabase table/REST usage (auth-only supabase in authApi)
- `supabase-integration/migrations/002_phase2_issue_seed.sql` — `on conflict` upserts; no wipe statements
- `web/package.json` + `package-lock.json` — pinned markdown stack (`react-markdown`, `rehype-sanitize`, `remark-gfm`, `rehype-slug`)
- `.env.example` — no `VITE_SUPABASE_SECRET` (Phase 1 gate retained)

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-02-SC | T-02-SC | Plans 02-01/02/03/05/06 added no packages; 02-04 markdown stack Approved in RESEARCH legitimacy audit and declared in package.json/lockfile | plan disposition + secure-phase | 2026-09-20 |
| AR-02-01-cycle | T-02-01-cycle | Cycle stub (`status`, `closes_at`) is non-PII editorial metadata exposed only to authenticated readers (02-05 accept) | plan disposition + secure-phase | 2026-09-20 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-20 | 9 | 9 | 0 | gsd-security-auditor (L1 verify) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-20
