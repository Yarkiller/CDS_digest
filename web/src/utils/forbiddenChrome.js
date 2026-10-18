/**
 * Assert-only email chrome ban list (ADUX-04, D-17/D-18).
 * Keep in sync with backend.domain.email_chrome.FORBIDDEN_LOWER.
 * Do not call from renderers to mutate output — tests and scrub tooling only.
 */

/** @type {readonly string[]} */
export const FORBIDDEN_LOWER = ['test-header', 'test_header', 'testheader']

/**
 * @param {string | null | undefined} text
 * @returns {boolean}
 */
export function containsForbiddenChrome(text) {
  const lowered = String(text ?? '').toLowerCase()
  return FORBIDDEN_LOWER.some((token) => lowered.includes(token))
}
