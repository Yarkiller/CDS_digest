/** OAuth2 (Yandex ID via Supabase) helpers — pure, node-testable. */

import { DEFAULT_ALLOWED_EMAIL_DOMAINS, isAllowedCorporateEmail } from './emailDomain.js'

export { DEFAULT_ALLOWED_EMAIL_DOMAINS }

export const YANDEX_OAUTH_LABEL = 'Продолжить с Яндекс ID'

/** Supabase has no built-in Yandex provider — it must be a `custom:` OAuth2 provider. */
export const DEFAULT_YANDEX_PROVIDER = 'custom:yandex'

/**
 * Supabase provider identifier for Yandex (defaults to a custom OAuth2 provider).
 * @param {Record<string, unknown> | null | undefined} env
 * @returns {string}
 */
export function yandexProviderId(env) {
  const value = env?.VITE_YANDEX_OAUTH_PROVIDER
  return typeof value === 'string' && value.trim() ? value.trim() : DEFAULT_YANDEX_PROVIDER
}

/**
 * Whether the Yandex ID OAuth button should be offered.
 * @param {Record<string, unknown> | null | undefined} env
 * @returns {boolean}
 */
export function oauthEnabled(env) {
  return env?.VITE_ENABLE_YANDEX_OAUTH === 'true'
}

/**
 * Parse a comma-separated domain allow-list; each entry is normalized to `@domain`.
 * @param {unknown} value
 * @returns {string[] | null} null when no usable entries (caller keeps the default)
 */
export function parseAllowedDomains(value) {
  if (typeof value !== 'string') {
    return null
  }
  const parsed = value
    .split(',')
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean)
    .map((domain) => (domain.startsWith('@') ? domain : `@${domain}`))
  return parsed.length ? parsed : null
}

/**
 * Corporate allow-list for the SPA: VITE_ALLOWED_EMAIL_DOMAINS overrides the strict
 * default (mirrors backend ALLOWED_EMAIL_DOMAINS). Defaults stay strict.
 * @param {Record<string, unknown> | null | undefined} env
 * @returns {readonly string[]}
 */
export function corporateAllowedDomains(env) {
  return parseAllowedDomains(env?.VITE_ALLOWED_EMAIL_DOMAINS) ?? DEFAULT_ALLOWED_EMAIL_DOMAINS
}

/**
 * A signed-in session is usable only when its email is on the corporate allow-list.
 * Supabase OAuth (Yandex) returns the provider email, which must still be corporate.
 * @param {{ user?: { email?: string } } | null | undefined} session
 * @param {readonly string[]} [allowedDomains]
 * @returns {boolean}
 */
export function isCorporateSession(session, allowedDomains) {
  const email = session?.user?.email
  if (typeof email !== 'string' || !email) {
    return false
  }
  return isAllowedCorporateEmail(email, allowedDomains)
}
