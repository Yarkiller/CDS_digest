/**
 * Content API — current / archive / by-number (ISSUE-01 / ISSUE-04).
 * Mock/live cutover via VITE_USE_MOCKS (D-20). Never silent mock fallback (D-21).
 */
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'
import {
  currentIssue,
  getArchiveIssues,
  getIssueByNumber,
  getIssueMaterials,
  getMaterialById,
} from '../data/mock.js'

export class ContentApiError extends Error {
  constructor(message, { code = 'CONTENT_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'ContentApiError'
    this.code = code
    this.retryable = retryable
  }
}

let failNextFetch = false
let emptyCurrentIssue = false
let emptyArchive = false

export function armFailNextContentFetch() {
  failNextFetch = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_CONTENT__ = true
  }
}

/** Clear fail arm so Retry can succeed (window flag is sticky for StrictMode). */
export function clearFailNextContentFetch() {
  failNextFetch = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_CONTENT__ = false
  }
}

/** Playwright/unit harness: force empty current DTO under mocks (D-30). */
export function armEmptyCurrentIssue() {
  emptyCurrentIssue = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_EMPTY_CURRENT_ISSUE__ = true
  }
}

/** Playwright harness: force empty archive list under mocks (D-30). */
export function armEmptyArchive() {
  emptyArchive = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_EMPTY_ARCHIVE__ = true
  }
}

export function resetContentHarness() {
  failNextFetch = false
  emptyCurrentIssue = false
  emptyArchive = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_CONTENT__ = false
    window.__DIGEST_EMPTY_CURRENT_ISSUE__ = false
    window.__DIGEST_EMPTY_ARCHIVE__ = false
    window.__DIGEST_VOTING_CYCLE_CLOSED__ = false
    window.__DIGEST_NO_VOTING_CYCLE__ = false
  }
}

/**
 * Fail arm: module flag is one-shot; window.__DIGEST_FAIL_NEXT_CONTENT__ is sticky
 * (survives React StrictMode remount) until clearFailNextContentFetch / reset.
 */
function consumeFailNext() {
  if (failNextFetch) {
    failNextFetch = false
    return true
  }
  return typeof window !== 'undefined' && window.__DIGEST_FAIL_NEXT_CONTENT__ === true
}

function isEmptyCurrentArmed() {
  if (emptyCurrentIssue) return true
  return typeof window !== 'undefined' && window.__DIGEST_EMPTY_CURRENT_ISSUE__ === true
}

function isEmptyArchiveArmed() {
  if (emptyArchive) return true
  return typeof window !== 'undefined' && window.__DIGEST_EMPTY_ARCHIVE__ === true
}

/** Mock/live voting_cycle stub for current issue (D-33). */
function mockVotingCycle() {
  if (typeof window !== 'undefined' && window.__DIGEST_NO_VOTING_CYCLE__ === true) {
    return null
  }
  const closed =
    typeof window !== 'undefined' && window.__DIGEST_VOTING_CYCLE_CLOSED__ === true
  return {
    status: closed ? 'closed' : 'open',
    // Matches currentIssue.votingOpenUntil narrative (28 марта 2026 UTC).
    closes_at: '2026-03-28T21:00:00.000Z',
  }
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

/**
 * Map mock.js materials to API IssueItem DTO.
 * @param {ReturnType<typeof getIssueMaterials>} materials
 */
function mapMockItems(materials) {
  return materials.map((m) => ({
    slug: m.id,
    title: m.title,
    position: m.issuePosition,
    format: m.format,
    reading_minutes: m.readingMinutes,
    dek: m.dek ?? null,
  }))
}

async function authHeaders(accessToken) {
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new ContentApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }
  return { Authorization: `Bearer ${token}` }
}

function throwNetwork(message = 'Не удалось загрузить выпуск. Проверьте сеть.') {
  throw new ContentApiError(message, { code: 'NETWORK', retryable: true })
}

/**
 * @returns {Promise<{
 *   number: number | null,
 *   period_label: string | null,
 *   title: string | null,
 *   editor: string | null,
 *   items: Array<{
 *     slug: string,
 *     title: string,
 *     position: number,
 *     format: string,
 *     reading_minutes: number,
 *     dek: string | null,
 *   }>,
 *   voting_cycle: { status: string, closes_at: string } | null,
 * }>}
 */
export async function fetchCurrentIssue(accessToken) {
  if (consumeFailNext()) {
    throwNetwork()
  }

  if (isMocksEnabled()) {
    if (isEmptyCurrentArmed()) {
      return {
        number: null,
        period_label: null,
        title: null,
        editor: null,
        items: [],
        voting_cycle: null,
      }
    }
    return {
      number: currentIssue.number,
      period_label: currentIssue.period,
      title: currentIssue.title,
      editor: currentIssue.editor,
      items: mapMockItems(getIssueMaterials()),
      voting_cycle: mockVotingCycle(),
    }
  }

  const headers = await authHeaders(accessToken)
  let response
  try {
    response = await fetch(`${apiBase()}/issues/current`, { headers })
  } catch {
    throwNetwork()
  }

  if (response.status === 401) {
    throw new ContentApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (!response.ok) {
    throwNetwork()
  }
  return response.json()
}

/**
 * Past published issues excluding current (D-31).
 * @returns {Promise<{ issues: Array<{ number: number, period_label: string, title: string, material_count: number }> }>}
 */
export async function fetchArchive(accessToken) {
  if (consumeFailNext()) {
    throwNetwork('Не удалось загрузить архив. Проверьте сеть.')
  }

  if (isMocksEnabled()) {
    if (isEmptyArchiveArmed()) {
      return { issues: [] }
    }
    return { issues: getArchiveIssues() }
  }

  const headers = await authHeaders(accessToken)
  let response
  try {
    response = await fetch(`${apiBase()}/archive`, { headers })
  } catch {
    throwNetwork('Не удалось загрузить архив. Проверьте сеть.')
  }

  if (response.status === 401) {
    throw new ContentApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (!response.ok) {
    throwNetwork('Не удалось загрузить архив. Проверьте сеть.')
  }
  return response.json()
}

/**
 * Published issue by number — HTTP 404 → NOT_FOUND (not NETWORK).
 * @param {number|string} number
 */
export async function fetchIssueByNumber(number, accessToken) {
  if (consumeFailNext()) {
    throwNetwork()
  }

  const n = Number(number)

  if (isMocksEnabled()) {
    const dto = getIssueByNumber(n)
    if (!dto) {
      throw new ContentApiError('Выпуск не найден.', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    return dto
  }

  const headers = await authHeaders(accessToken)
  let response
  try {
    response = await fetch(`${apiBase()}/issues/${n}`, { headers })
  } catch {
    throwNetwork()
  }

  if (response.status === 401) {
    throw new ContentApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (response.status === 404) {
    throw new ContentApiError('Выпуск не найден.', {
      code: 'NOT_FOUND',
      retryable: false,
    })
  }
  if (!response.ok) {
    throwNetwork()
  }
  return response.json()
}

/**
 * Map mock.js material to API reader DTO (body[] → body_markdown).
 * @param {NonNullable<ReturnType<typeof getMaterialById>>} material
 */
function mapMockMaterial(material) {
  const bodyMarkdown =
    material.body_markdown ??
    (Array.isArray(material.body) ? material.body.join('\n\n') : String(material.body ?? ''))
  const format =
    typeof material.format === 'string' && material.format.toLowerCase() === 'статья'
      ? 'статья'
      : material.format
  return {
    slug: material.id,
    title: material.title,
    dek: material.dek ?? '',
    body_markdown: bodyMarkdown,
    format,
    provenance: material.provenance ?? '',
    tags: Array.isArray(material.tags) ? material.tags : [],
    related: Array.isArray(material.related) ? material.related : [],
    reading_minutes: material.readingMinutes,
    published_at: material.published_at ?? null,
    published_label: material.date ?? null,
    editor: 'Редакция Digest CDS',
  }
}

/**
 * Ready material by slug — HTTP 404 → NOT_FOUND (soft editorial empty).
 * @param {string} slug
 */
export async function fetchMaterial(slug, accessToken) {
  if (consumeFailNext()) {
    throwNetwork('Не удалось загрузить материал. Проверьте сеть.')
  }

  if (isMocksEnabled()) {
    const material = getMaterialById(slug)
    if (!material) {
      throw new ContentApiError('Материал не найден.', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    return mapMockMaterial(material)
  }

  const headers = await authHeaders(accessToken)
  let response
  try {
    response = await fetch(`${apiBase()}/materials/${encodeURIComponent(slug)}`, { headers })
  } catch {
    throwNetwork('Не удалось загрузить материал. Проверьте сеть.')
  }

  if (response.status === 401) {
    throw new ContentApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (response.status === 404) {
    throw new ContentApiError('Материал не найден.', {
      code: 'NOT_FOUND',
      retryable: false,
    })
  }
  if (!response.ok) {
    throwNetwork('Не удалось загрузить материал. Проверьте сеть.')
  }
  return response.json()
}
