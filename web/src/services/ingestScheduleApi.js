/**
 * Ingestion schedule API — sole SPA transport for /admin/ingestion-schedule (ING-06).
 *
 * Pages/components must not import Supabase/SQL. Mock/live via isMocksEnabled().
 *
 * @typedef {{
 *   enabled: boolean,
 *   time_of_day: string,
 *   days_of_week: number[],
 *   last_run_at: string | null,
 *   updated_at: string | null,
 * }} IngestionScheduleDto
 *
 * @typedef {{
 *   schedule: IngestionScheduleDto,
 *   patchCount: number,
 * }} IngestionScheduleMockStore
 */

import { delay } from '../utils/delay.js'
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

export class IngestScheduleError extends Error {
  constructor(message, { code = 'INGESTION_SCHEDULE_FAILED', retryable = true, errors = null } = {}) {
    super(message)
    this.name = 'IngestScheduleError'
    this.code = code
    this.retryable = retryable
    this.errors = errors
  }
}

const MOCK_STORAGE_KEY = 'digest:ingestion-schedule-mock'
const ARM_STORAGE_KEY = 'digest:ingestion-schedule-mock-arm'

/** @type {IngestionScheduleDto} */
export const DEFAULT_SCHEDULE = {
  enabled: true,
  time_of_day: '06:00',
  days_of_week: [1, 2, 3, 4, 5, 6, 7],
  last_run_at: null,
  updated_at: null,
}

function mocksEnabled() {
  return isMocksEnabled()
}

/** @returns {{ failLoad?: boolean, failSave?: boolean, rejectSave?: unknown }} */
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

/** Arm the next schedule load to fail (mock). */
export function armFailNextScheduleLoad() {
  writeArm({ ...readArm(), failLoad: true })
}

/**
 * Arm the next schedule PATCH to fail (mock).
 * Pass `{ errors: [...] }` for a 400-style reject body.
 * @param {{ errors?: unknown[] } | null} [payload]
 */
export function armFailNextScheduleSave(payload = null) {
  if (payload && Array.isArray(payload.errors)) {
    writeArm({ ...readArm(), rejectSave: payload })
  } else {
    writeArm({ ...readArm(), failSave: true })
  }
}

/** Clear every armed mock control (Playwright reset); the saved mock schedule is kept. */
export function resetIngestionScheduleHarness() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(ARM_STORAGE_KEY)
}

/** Clear mock schedule + arms (Playwright seed defaults). */
export function resetIngestionScheduleMockStore() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(MOCK_STORAGE_KEY)
  window.sessionStorage.removeItem(ARM_STORAGE_KEY)
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

/** @returns {IngestionScheduleMockStore} */
function readMockStore() {
  if (typeof window === 'undefined') {
    return { schedule: { ...DEFAULT_SCHEDULE }, patchCount: 0 }
  }
  try {
    const raw = window.sessionStorage.getItem(MOCK_STORAGE_KEY)
    if (!raw) return { schedule: { ...DEFAULT_SCHEDULE }, patchCount: 0 }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') {
      return { schedule: { ...DEFAULT_SCHEDULE }, patchCount: 0 }
    }
    const schedule =
      parsed.schedule && typeof parsed.schedule === 'object'
        ? { ...DEFAULT_SCHEDULE, ...parsed.schedule }
        : { ...DEFAULT_SCHEDULE }
    const patchCount = Number.isFinite(Number(parsed.patchCount)) ? Number(parsed.patchCount) : 0
    return { schedule, patchCount }
  } catch {
    return { schedule: { ...DEFAULT_SCHEDULE }, patchCount: 0 }
  }
}

/** @param {IngestionScheduleMockStore} store */
function writeMockStore(store) {
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(store))
  }
}

/** Read mock store (Playwright PATCH-count assertions). */
export function readIngestionScheduleMock() {
  return readMockStore()
}

function mapHttpError(response, fallbackMessage, body = null) {
  if (response.status === 401) {
    return new IngestScheduleError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (response.status === 403) {
    return new IngestScheduleError('Недостаточно прав.', {
      code: 'FORBIDDEN',
      retryable: false,
    })
  }
  if (response.status === 400) {
    const errors = Array.isArray(body?.errors) ? body.errors : null
    const first =
      errors && errors[0] && typeof errors[0].message === 'string' ? errors[0].message : null
    return new IngestScheduleError(first || fallbackMessage, {
      code: 'INVALID_SCHEDULE',
      retryable: false,
      errors,
    })
  }
  if (response.status === 422) {
    return new IngestScheduleError(fallbackMessage, {
      code: 'INVALID_SCHEDULE',
      retryable: false,
    })
  }
  return new IngestScheduleError(fallbackMessage, { code: 'NETWORK', retryable: true })
}

/**
 * @param {string} [accessToken]
 * @returns {Promise<IngestionScheduleDto>}
 */
export async function fetchIngestionSchedule(accessToken) {
  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if (arm.failLoad) {
      const next = { ...arm }
      delete next.failLoad
      writeArm(next)
      throw new IngestScheduleError('Не удалось загрузить настройки сбора', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    return { ...readMockStore().schedule }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestScheduleError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingestion-schedule`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new IngestScheduleError('Не удалось загрузить настройки сбора', {
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
    throw mapHttpError(response, 'Не удалось загрузить настройки сбора', body)
  }

  return response.json()
}

/**
 * @param {Partial<IngestionScheduleDto>} payload
 * @param {string} [accessToken]
 * @returns {Promise<IngestionScheduleDto>}
 */
export async function patchIngestionSchedule(payload, accessToken) {
  const patch = payload && typeof payload === 'object' ? payload : {}

  if (mocksEnabled()) {
    await delay(80)
    const arm = readArm()
    if ('rejectSave' in arm) {
      const reject = arm.rejectSave
      const next = { ...arm }
      delete next.rejectSave
      writeArm(next)
      const errors = Array.isArray(reject?.errors) ? reject.errors : null
      const first =
        errors && errors[0] && typeof errors[0].message === 'string' ? errors[0].message : null
      throw new IngestScheduleError(first || 'Не удалось сохранить настройки сбора', {
        code: 'INVALID_SCHEDULE',
        retryable: false,
        errors,
      })
    }
    if (arm.failSave) {
      const next = { ...arm }
      delete next.failSave
      writeArm(next)
      throw new IngestScheduleError('Не удалось сохранить настройки сбора. Повторите действие.', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    const store = readMockStore()
    const merged = {
      ...store.schedule,
      ...patch,
      updated_at: new Date().toISOString(),
    }
    if (Array.isArray(patch.days_of_week)) {
      merged.days_of_week = [...patch.days_of_week]
    }
    writeMockStore({ schedule: merged, patchCount: store.patchCount + 1 })
    return { ...merged }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new IngestScheduleError('Требуется вход.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/ingestion-schedule`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patch),
    })
  } catch {
    throw new IngestScheduleError('Не удалось сохранить настройки сбора. Повторите действие.', {
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
      'Не удалось сохранить настройки сбора. Повторите действие.',
      body,
    )
  }

  return response.json()
}
