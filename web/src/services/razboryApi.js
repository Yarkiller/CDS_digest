/**
 * Razbory list + detail API — GET /razbory, GET /razbory/{id}
 * (RAZB-01 / RAZB-02 / D-66 / D-67 / D-68).
 * Mock/live cutover via isMocksEnabled(); never silent mock fallback after live failure.
 * JWT via existing session headers (T-04-07).
 */
import { delay } from '../utils/delay.js'
import { getRazborById, getRazboryList } from '../data/mock.js'

export const RAZBOR_EDITOR_BYLINE = 'Редакция Digest CDS'

export class RazboryApiError extends Error {
  constructor(message, { code = 'RAZBORY_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'RazboryApiError'
    this.code = code
    this.retryable = retryable
  }
}

let failNextFetch = false
let emptyRazbory = false

/** Playwright/unit harness: fail next fetchRazbory once. */
export function armFailNextRazboryFetch() {
  failNextFetch = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_RAZBORY__ = true
  }
}

export function clearFailNextRazboryFetch() {
  failNextFetch = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_RAZBORY__ = false
  }
}

/** Playwright harness: force empty razbory list under mocks (D-69). */
export function armEmptyRazbory() {
  emptyRazbory = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_EMPTY_RAZBORY__ = true
  }
}

export function resetRazboryHarness() {
  failNextFetch = false
  emptyRazbory = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_RAZBORY__ = false
    window.__DIGEST_EMPTY_RAZBORY__ = false
  }
}

function consumeFailNext() {
  if (failNextFetch) {
    failNextFetch = false
    return true
  }
  return typeof window !== 'undefined' && window.__DIGEST_FAIL_NEXT_RAZBORY__ === true
}

function isEmptyArmed() {
  if (emptyRazbory) return true
  return typeof window !== 'undefined' && window.__DIGEST_EMPTY_RAZBORY__ === true
}

/**
 * Map announcement → «Анонс»; published has no extra overline label (D-68).
 * @param {string} status
 * @returns {string | null}
 */
export function razborStatusLabel(status) {
  if (status === 'announcement') return 'Анонс'
  return null
}

/**
 * Pure mock list → HTTP chronology DTO. Testable without Vite env.
 * @param {Array<{ id: number, title: string, meeting_at: string | null, status: string }>} catalog
 */
export function mockListRazbory(catalog) {
  return {
    items: (catalog ?? []).map((row) => ({
      id: row.id,
      title: row.title,
      meeting_at: row.meeting_at ?? null,
      status: row.status,
    })),
  }
}

/**
 * Pure mock detail → HTTP DTO. Announcement body always empty (D-68).
 * content_kind seeded or inferred (RAZB-04 / D-73).
 * @param {{ id: number, title: string, meeting_at?: string | null, status: string, body_markdown?: string, notebook_path?: string | null, content_kind?: string }} row
 */
export function mockRazborDetail(row) {
  const isAnnouncement = row.status === 'announcement'
  const body = isAnnouncement ? '' : (row.body_markdown ?? '')
  let contentKind = row.content_kind
  if (!contentKind) {
    const hasQualityHeading = /^##\s+(Качество|Оценка качества)\s*$/m.test(body)
    const hasNumericTable = /\|[^|\n]*\d/.test(body)
    contentKind = hasQualityHeading && hasNumericTable ? 'quality' : 'overview'
  }
  return {
    id: row.id,
    title: row.title,
    meeting_at: row.meeting_at ?? null,
    status: row.status,
    body_markdown: body,
    notebook_available: !isAnnouncement && Boolean(row.notebook_path),
    content_kind: isAnnouncement ? 'overview' : contentKind,
    editor: RAZBOR_EDITOR_BYLINE,
  }
}

/**
 * Authenticated razbory chronology list.
 * @param {string | null} [accessToken]
 */
export async function fetchRazbory(accessToken = null) {
  if (consumeFailNext()) {
    throw new RazboryApiError('Не удалось загрузить разборы. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const { isMocksEnabled } = await import('./authEnv.js')
  if (isMocksEnabled()) {
    await delay(80)
    if (isEmptyArmed()) {
      return { items: [] }
    }
    return mockListRazbory(getRazboryList())
  }

  const { getAccessToken } = await import('./authApi.js')
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new RazboryApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

  let response
  try {
    response = await fetch(`${apiBase}/razbory`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new RazboryApiError('Не удалось загрузить разборы. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new RazboryApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  if (!response.ok) {
    throw new RazboryApiError('Не удалось загрузить разборы. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const body = await response.json()
  return {
    items: (body.items ?? []).map((row) => ({
      id: row.id,
      title: row.title,
      meeting_at: row.meeting_at ?? null,
      status: row.status,
    })),
  }
}

/**
 * Authenticated razbor detail by id (RAZB-02 / D-68).
 * @param {number | string} id
 * @param {string | null} [accessToken]
 */
export async function fetchRazbor(id, accessToken = null) {
  if (consumeFailNext()) {
    throw new RazboryApiError('Не удалось загрузить разбор. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const { isMocksEnabled } = await import('./authEnv.js')
  if (isMocksEnabled()) {
    await delay(80)
    const row = getRazborById(id)
    if (!row) {
      throw new RazboryApiError('Разбор не найден.', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    return mockRazborDetail(row)
  }

  const { getAccessToken } = await import('./authApi.js')
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new RazboryApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

  let response
  try {
    response = await fetch(`${apiBase}/razbory/${encodeURIComponent(String(id))}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new RazboryApiError('Не удалось загрузить разбор. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new RazboryApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  if (response.status === 404) {
    throw new RazboryApiError('Разбор не найден.', {
      code: 'NOT_FOUND',
      retryable: false,
    })
  }

  if (!response.ok) {
    throw new RazboryApiError('Не удалось загрузить разбор. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const body = await response.json()
  return {
    id: body.id,
    title: body.title,
    meeting_at: body.meeting_at ?? null,
    status: body.status,
    body_markdown: body.body_markdown ?? '',
    notebook_available: Boolean(body.notebook_available),
    content_kind: body.content_kind === 'quality' ? 'quality' : 'overview',
    editor: body.editor ?? RAZBOR_EDITOR_BYLINE,
  }
}

/**
 * Authenticated notebook download (RAZB-03 / D-70…72).
 * Returns a Blob for object-URL save; failures surface as RazboryApiError for toast.
 * @param {number | string} id
 * @param {string | null} [accessToken]
 * @returns {Promise<{ blob: Blob, filename: string }>}
 */
export async function downloadRazborNotebook(id, accessToken = null) {
  const { isMocksEnabled } = await import('./authEnv.js')
  if (isMocksEnabled()) {
    await delay(80)
    const row = getRazborById(id)
    if (!row || row.status === 'announcement' || !row.notebook_path) {
      throw new RazboryApiError('Не удалось скачать', {
        code: 'NOTEBOOK_NOT_AVAILABLE',
        retryable: false,
      })
    }
    const filename = String(row.notebook_path).split('/').pop() || 'notebook.ipynb'
    const payload = JSON.stringify({
      nbformat: 4,
      nbformat_minor: 5,
      metadata: { mock: true, title: row.title },
      cells: [],
    })
    return {
      blob: new Blob([payload], { type: 'application/x-ipynb+json' }),
      filename,
    }
  }

  const { getAccessToken } = await import('./authApi.js')
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new RazboryApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

  let response
  try {
    response = await fetch(`${apiBase}/razbory/${encodeURIComponent(String(id))}/notebook`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new RazboryApiError('Не удалось скачать', { code: 'NETWORK', retryable: true })
  }

  if (response.status === 401) {
    throw new RazboryApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  if (!response.ok) {
    throw new RazboryApiError('Не удалось скачать', {
      code: response.status === 404 ? 'NOTEBOOK_NOT_AVAILABLE' : 'NETWORK',
      retryable: response.status !== 404,
    })
  }

  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') ?? ''
  const match = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(disposition)
  const filename = match
    ? decodeURIComponent(match[1].replaceAll('"', '').trim())
    : `razbor-${id}.ipynb`
  return { blob, filename }
}
