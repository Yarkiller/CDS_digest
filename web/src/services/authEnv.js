/**
 * Auth env helpers. Default VITE_USE_MOCKS=true keeps offline Playwright unblocked (D-09).
 * Tests may set window.__DIGEST_FORCE_AUTH_GATE__ = true to exercise RequireAuth.
 */

export function isMocksEnabled() {
  if (typeof window !== 'undefined' && window.__DIGEST_FORCE_AUTH_GATE__ === true) {
    return false
  }
  const value = import.meta.env.VITE_USE_MOCKS
  return value === undefined || value === '' || value === 'true'
}

/**
 * Whether the login gate must be enforced even when mocks are enabled.
 * Production sets VITE_REQUIRE_LOGIN=true so visitors must sign in.
 * Pure form takes the env object so it is unit-testable.
 * @param {Record<string, unknown> | null | undefined} env
 * @returns {boolean}
 */
export function loginRequired(env) {
  return Boolean(env) && env.VITE_REQUIRE_LOGIN === 'true'
}

export function isLoginRequired() {
  return loginRequired(import.meta.env)
}

/**
 * Allow only same-origin relative paths (T-01-12).
 * @param {string | null | undefined} raw
 * @returns {string}
 */
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
