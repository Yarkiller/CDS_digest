/** Corporate email domain policy for SPA login (ADR-0003 / D-04 / AUTH-01). */

export const DEFAULT_ALLOWED_EMAIL_DOMAINS = Object.freeze([
  '@sberbank.ru',
  '@omega.sbrf.ru',
])

/**
 * @param {string | null | undefined} email
 * @param {readonly string[]} [allowedDomains]
 * @returns {boolean}
 */
export function isAllowedCorporateEmail(
  email,
  allowedDomains = DEFAULT_ALLOWED_EMAIL_DOMAINS,
) {
  if (!email || typeof email !== 'string' || !email.includes('@')) {
    return false
  }
  const at = email.lastIndexOf('@')
  const local = email.slice(0, at)
  const domain = email.slice(at + 1)
  if (!local || !domain) {
    return false
  }
  const normalized = `@${domain.toLowerCase()}`
  const allowed = allowedDomains.map((d) => d.toLowerCase())
  return allowed.includes(normalized)
}
