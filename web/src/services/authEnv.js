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
