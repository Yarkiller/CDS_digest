/**
 * Ingest sources API — sole SPA transport for /admin/ingest-sources (SRC-01/SRC-03).
 *
 * Pages/components must not import Supabase/SQL. Mock/live via isMocksEnabled().
 *
 * @typedef {{
 *   id: number,
 *   kind: string,
 *   source_id: string,
 *   label: string | null,
 *   is_enabled: boolean,
 *   created_at?: string,
 *   updated_at?: string,
 * }} IngestSourceDto
 */

import { delay } from '../utils/delay.js'
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

export class IngestSourcesError extends Error {
  constructor(message, { code = 'INGEST_SOURCES_FAILED', retryable = true, errors = null } = {}) {
    super(message)
    this.name = 'IngestSourcesError'
    this.code = code
    this.retryable = retryable
    this.errors = errors
  }
}

const MOCK_STORAGE_KEY = 'digest:ingest-sources-mock'
const ARM_STORAGE_KEY = 'digest:ingest-sources-mock-arm'

function mocksEnabled() {
  return isMocksEnabled()
}

/** @returns {{ failLoad?: boolean, failAdd?: boolean, rejectAdd?: unknown[] }} */
function readArm() {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.sessionStorage.getItem(ARM_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

/** @param {Record<string, unknown>} arm */
function writeArm(arm) {
  if (typeof window === 'undefined') return
  if (!arm || Object.keys(arm).length === 0) {
    window.sessionStorage.removeItem(ARM_STORAGE_KEY)
    return
  }
  window.sessionStorage.setItem(ARM_STORAGE_KEY, JSON.stringify(arm))
}

/** Arm the next add to fail as a network/5xx error (mock). */
export function armFailNextAdd() {
  writeArm({ ...readArm(), failAdd: true })
}

/** Arm the next list load to fail (mock). */
export function armFailNextLoad() {
  writeArm({ ...readArm(), failLoad: true })
}

/** Arm the next add to be rejected as invalid (mock). Pass structured errors. */
export function armRejectNextAdd(errors = []) {
  writeArm({ ...readArm(), rejectAdd: Array.isArray(errors) ? errors : [] })
}

/** Arm the next setEnabled (PATCH) to fail as a network/5xx error (mock). */
export function armFailNextSetEnabled() {
  writeArm({ ...readArm(), failSetEnabled: true })
}

/** Arm the next delete to fail as a network/5xx error (mock). */
export function armFailNextDelete() {
  writeArm({ ...readArm(), failDelete: true })
}

/** Clear every armed mock control (Playwright reset); the saved mock list is kept. */
export function resetIngestSourcesHarness() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(ARM_STORAGE_KEY)
}

/** Clear mock list + arms (Playwright seed empty). */
export function resetIngestSourcesMockStore() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(MOCK_STORAGE_KEY)
  window.sessionStorage.removeItem(ARM_STORAGE_KEY)
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

/** @returns {IngestSourceDto[]} */
function readMockSources() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.sessionStorage.getItem(MOCK_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/** @param {IngestSourceDto[]} sources */
function writeMockSources(sources) {
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(sources))
  }
  return sources
}

function mapHttpError(response, fallbackMessage, body = null) {
  if (response.status === 401) {
    return new IngestSourcesError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (response.status === 403) {
    return new IngestSourcesError('Недостаточно прав.', {
      code: 'FORBIDDEN',
      retryable: false,
    })
  }
  if (response.status === 400) {
    const errors = Array.isArray(body?.errors) ? body.errors : null
    return new IngestSourcesError('Источник не добавлен', {
      code: 'INVALID_SOURCE',
      retryable: false,
      errors,
    })
  }
  if (response.status === 422) {
    return new IngestSourcesError('Источник не добавлен', {
      code: 'INVALID_SOURCE',
      retryable: false,
    })
  }
  return new IngestSourcesError(fallbackMessage, { code: 'NETWORK', retryable: true })
}

/**
 * @param {string} [accessToken]
 * @returns {Promise<IngestSourceDto[]>}
 */
export async function listIngestSources(accessToken) {
  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if (arm.failLoad) {
      throw new IngestSourcesError('Не удалось загрузить источники', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    return readMockSources()
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestSourcesError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingest-sources`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new IngestSourcesError('Не удалось загрузить источники', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не удалось загрузить источники')
  }

  const body = await response.json()
  return Array.isArray(body?.sources) ? body.sources : []
}

/**
 * @param {{ kind: string, source_id: string, label?: string | null }} payload
 * @param {string} [accessToken]
 * @returns {Promise<IngestSourceDto>}
 */
export async function addIngestSource(payload, accessToken) {
  const kind = String(payload?.kind ?? 'channel')
  const sourceId = String(payload?.source_id ?? '').trim()
  const labelRaw = payload?.label
  const label =
    labelRaw == null || String(labelRaw).trim() === '' ? null : String(labelRaw).trim()

  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if ('rejectAdd' in arm) {
      const errors = Array.isArray(arm.rejectAdd) ? arm.rejectAdd : []
      const next = { ...arm }
      delete next.rejectAdd
      writeArm(next)
      throw new IngestSourcesError('Источник не добавлен', {
        code: 'INVALID_SOURCE',
        retryable: false,
        errors: errors.length ? errors : null,
      })
    }
    if (arm.failAdd) {
      const next = { ...arm }
      delete next.failAdd
      writeArm(next)
      throw new IngestSourcesError('Не удалось добавить источник. Проверьте данные и повторите.', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    const now = new Date().toISOString()
    const existing = readMockSources()
    const row = {
      id: existing.reduce((max, s) => Math.max(max, Number(s.id) || 0), 0) + 1,
      kind,
      source_id: sourceId,
      label,
      is_enabled: true,
      created_at: now,
      updated_at: now,
    }
    writeMockSources([...existing, row])
    return row
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestSourcesError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingest-sources`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ kind, source_id: sourceId, label }),
    })
  } catch {
    throw new IngestSourcesError('Не удалось добавить источник. Проверьте данные и повторите.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    let body = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    throw mapHttpError(
      response,
      'Не удалось добавить источник. Проверьте данные и повторите.',
      body,
    )
  }

  return response.json()
}

/**
 * Enable or disable an ingest source (immediate persist, D-01/D-18).
 * @param {number} id
 * @param {boolean} isEnabled
 * @param {string} [accessToken]
 * @returns {Promise<IngestSourceDto>}
 */
export async function setIngestSourceEnabled(id, isEnabled, accessToken) {
  const sourceId = Number(id)
  const enabled = Boolean(isEnabled)

  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if (arm.failSetEnabled) {
      const next = { ...arm }
      delete next.failSetEnabled
      writeArm(next)
      throw new IngestSourcesError('Не удалось обновить источник. Повторите действие.', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    const existing = readMockSources()
    const index = existing.findIndex((row) => Number(row.id) === sourceId)
    if (index < 0) {
      throw new IngestSourcesError('Источник не найден', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    const updated = {
      ...existing[index],
      is_enabled: enabled,
      updated_at: new Date().toISOString(),
    }
    const next = [...existing]
    next[index] = updated
    writeMockSources(next)
    return updated
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestSourcesError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingest-sources/${sourceId}`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_enabled: enabled }),
    })
  } catch {
    throw new IngestSourcesError('Не удалось обновить источник. Повторите действие.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    let body = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    if (response.status === 404) {
      throw new IngestSourcesError('Источник не найден', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    throw mapHttpError(
      response,
      'Не удалось обновить источник. Повторите действие.',
      body,
    )
  }

  return response.json()
}

/**
 * Hard-delete an ingest source (D-10). Returns void on success.
 * @param {number} id
 * @param {string} [accessToken]
 * @returns {Promise<void>}
 */
export async function deleteIngestSource(id, accessToken) {
  const sourceId = Number(id)

  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if (arm.failDelete) {
      const next = { ...arm }
      delete next.failDelete
      writeArm(next)
      throw new IngestSourcesError('Не удалось обновить источник. Повторите действие.', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    const existing = readMockSources()
    const next = existing.filter((row) => Number(row.id) !== sourceId)
    if (next.length === existing.length) {
      throw new IngestSourcesError('Источник не найден', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    writeMockSources(next)
    return
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestSourcesError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingest-sources/${sourceId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new IngestSourcesError('Не удалось обновить источник. Повторите действие.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new IngestSourcesError('Источник не найден', {
        code: 'NOT_FOUND',
        retryable: false,
      })
    }
    let body = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    throw mapHttpError(
      response,
      'Не удалось обновить источник. Повторите действие.',
      body,
    )
  }
}
