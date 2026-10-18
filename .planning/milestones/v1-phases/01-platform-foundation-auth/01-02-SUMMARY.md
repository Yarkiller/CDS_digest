---
phase: 01-platform-foundation-auth
plan: 02
subsystem: auth
tags: [jwt, es256, jwks, fastapi, email-domain, profile-repository]

requires:
  - phase: 01-platform-foundation-auth
    provides: FastAPI create_app with /health, CORS, request_id, Settings
provides:
  - ES256 JWKS access-token verification (auth_jwt)
  - Corporate email domain helper (ADR-0003)
  - ProfileRepository port + InMemoryProfileRepository
  - Authenticated GET /me returning CurrentUser DTO
affects:
  - 01-03 /me/ping and FE wire-up
  - Phase 5 admin-route 403 (AUTH-03 remainder)

actuals:
  tokens: 6081
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - injectable signing_key_resolver on create_app for offline ES256 tests
    - AccessTokenClaims in domain; verify helpers only in infrastructure
    - get_principal Depends: HTTPBearer + verify + email domain gate

key-files:
  created:
    - backend/src/backend/domain/auth_email.py
    - backend/src/backend/domain/auth_claims.py
    - backend/src/backend/domain/current_user.py
    - backend/src/backend/infrastructure/auth_jwt.py
    - backend/src/backend/interface/http/deps.py
    - backend/src/backend/interface/http/routes/me.py
    - backend/src/backend/application/ports/profile_repository.py
    - backend/src/backend/application/use_cases/get_current_user.py
    - tests/unit/test_auth_email_domain.py
    - tests/unit/test_jwt_verify.py
    - tests/unit/test_http_me.py
  modified:
    - backend/src/backend/interface/http/app.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/tests_support/in_memory.py
    - tests/unit/test_composition_container.py

key-decisions:
  - "Exact domain match after @ (not endswith) to avoid subdomain spoofing"
  - "AccessTokenClaims lives in domain so use-cases never import infrastructure"
  - "create_app(..., signing_key_resolver=) for offline PyJWK injection; production uses PyJWKClient(jwks_url)"

patterns-established:
  - "JWT verify in infrastructure; HTTP 401/403 mapping only in deps"
  - "Profile upsert via ProfileRepository port wired on AppContainer"
  - "AUTH-03 admin 403 deferred — documented on GET /me OpenAPI description"

requirements-completed: [PLAT-03, AUTH-01, AUTH-03]

coverage:
  - id: D1
    description: "GET /me rejects missing/invalid Bearer with 401"
    requirement: AUTH-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_me.py#test_me_without_authorization_returns_401"
        status: pass
    human_judgment: false
  - id: D2
    description: "Valid ES256 JWT with allowed corporate email returns CurrentUser from GET /me"
    requirement: PLAT-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_me.py#test_me_with_valid_corporate_jwt_returns_current_user"
        status: pass
    human_judgment: false
  - id: D3
    description: "Valid JWT with disallowed email domain returns 403 domain_not_allowed"
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_me.py#test_me_with_disallowed_email_domain_returns_403"
        status: pass
    human_judgment: false
  - id: D4
    description: "Offline ES256 JWKS verify rejects HS256/expired/wrong aud"
    requirement: AUTH-03
    verification:
      - kind: unit
        ref: "tests/unit/test_jwt_verify.py"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 02: JWT Gate & GET /me Summary

**ES256 JWKS verification, corporate email allowlist, and authenticated GET /me with ProfileRepository upsert — offline unit suite green.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-19T15:12:12Z
- **Completed:** 2026-09-19T15:24:00Z
- **Tasks:** 2/2 (email domain + GET /me tracer)
- **Files modified:** 16

## Accomplishments

- Domain `is_allowed_corporate_email` for `@sberbank.ru` / `@omega.sbrf.ru` (ADR-0003 / D-04)
- `auth_jwt.verify_access_token` ES256-only with injectable JWKS resolver + PyJWKClient path
- `GET /me` via `get_principal` + `get_current_user` / `ProfileRepository.get_or_upsert`
- POST `/me/ping` intentionally absent (Plan 03); admin 403 deferred to Phase 5

## Task Commits

1. **Task 1 RED:** `2f02dc5` — `test(01-02): add failing test for corporate email domain`
2. **Task 1 GREEN:** `8039a57` — `feat(01-02): implement corporate email domain helper`
3. **Task 2 RED:** `fd28348` — `test(01-02): add failing tests for JWT verify and GET /me`
4. **Task 2 GREEN:** `909438c` — `feat(01-02): implement ES256 JWT gate and GET /me`

**Plan metadata:** (docs commit after state update)

## Files Created/Modified

- `backend/src/backend/domain/auth_email.py` — corporate domain helper
- `backend/src/backend/domain/auth_claims.py` / `current_user.py` — typed claims + DTO
- `backend/src/backend/infrastructure/auth_jwt.py` — ES256 JWKS verify
- `backend/src/backend/interface/http/deps.py` — Bearer + domain gate
- `backend/src/backend/interface/http/routes/me.py` — GET /me
- `backend/src/backend/application/ports/profile_repository.py` + `use_cases/get_current_user.py`
- `container.py` / `in_memory.py` — `profiles` on AppContainer
- Unit tests: email, jwt, /me, composition

## Decisions Made

- Exact `@domain` match (not `endswith`) to block `evil.sberbank.ru` / `sberbank.ru.com` spoofing
- Claims DTO in domain so use-cases stay free of infrastructure imports
- Test injects `signing_key_resolver`; live path uses `SUPABASE_JWKS_URL` via PyJWKClient

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HS256 rejection test key material raised KeyError**
- **Found during:** Task 2 (tracer GREEN)
- **Issue:** Stub oct JWK without `k` crashed outside `TokenVerificationError` before alg check.
- **Fix:** Mint HS256 token but resolve with ES256 public JWK so `algorithms=["ES256"]` rejects; wrap resolver failures as `TokenVerificationError`.
- **Files modified:** `tests/unit/test_jwt_verify.py`, `backend/src/backend/infrastructure/auth_jwt.py`
- **Verification:** 14 plan tests + full `npm run test:unit` (36 passed)
- **Committed in:** `909438c`

**2. [Rule 2 - Missing critical] Claims type placement for Ports & Adapters**
- **Found during:** Task 2 (GREEN)
- **Issue:** Putting `AccessTokenClaims` only in infrastructure would force use-case → infrastructure import (architecture.mdc violation).
- **Fix:** `AccessTokenClaims` in `domain/auth_claims.py`; infrastructure + use-case both depend inward.
- **Files modified:** `domain/auth_claims.py`, `use_cases/get_current_user.py`, `auth_jwt.py`
- **Verification:** import graph + unit suite green
- **Committed in:** `909438c`

**Total deviations:** 2 auto-fixed (Rule 1 × 1, Rule 2 × 1)
**Impact on plan:** Correctness/architecture only; no scope creep. `/me/ping` still deferred.

## Issues Encountered

None beyond the auto-fixes above.

## User Setup Required

None for this plan — live JWKS URL/issuer already named in `.env.example` from Plan 01.

## Next Phase Readiness

Ready for Plan 01-03 (`POST /me/ping`). JWT deps and GET /me are in place; do not register ping until Plan 03.

## TDD Gate Compliance

- RED commits: `2f02dc5`, `fd28348`
- GREEN commits: `8039a57`, `909438c`
- Gates satisfied for both tasks.

## Self-Check: PASSED

- FOUND: backend/src/backend/infrastructure/auth_jwt.py
- FOUND: backend/src/backend/interface/http/deps.py
- FOUND: backend/src/backend/interface/http/routes/me.py
- FOUND: backend/src/backend/application/ports/profile_repository.py
- FOUND: 2f02dc5, 8039a57, fd28348, 909438c

---
*Phase: 01-platform-foundation-auth*
*Completed: 2026-09-19*
