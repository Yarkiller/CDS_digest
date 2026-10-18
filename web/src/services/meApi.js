import { getAccessToken, getSession } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

export class MeApiError extends Error {
  constructor(message, { code = 'ME_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'MeApiError'
    this.code = code
    this.retryable = retryable
  }
}

let failNextFetch = false

/** @type {string} app_role for mock /me — default employee (D-76); harness may set admin */
let mockRole = 'employee'

export function armFailNextMeFetch() {
  failNextFetch = true
}

/** @param {'employee' | 'analyst' | 'ds' | 'admin'} role */
export function setMockMeRole(role) {
  mockRole = role
  if (typeof window !== 'undefined') {
    window.__DIGEST_MOCK_ME_ROLE__ = role
  }
}

export function resetMeHarness() {
  failNextFetch = false
  mockDisplayName = null
  mockRole = 'employee'
  if (typeof window !== 'undefined') {
    window.__DIGEST_MOCK_ME_ROLE__ = 'employee'
    window.__DIGEST_ME_FAIL_FETCH__ = false
  }
}

function stickyMeFail() {
  return typeof window !== 'undefined' && Boolean(window.__DIGEST_ME_FAIL_FETCH__)
}

function resolveMockRole() {
  if (typeof window !== 'undefined' && typeof window.__DIGEST_MOCK_ME_ROLE__ === 'string') {
    return window.__DIGEST_MOCK_ME_ROLE__
  }
  return mockRole
}

/** @type {string | null} */
let mockDisplayName = null

function useMocks() {
  return isMocksEnabled()
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

/**
 * @returns {Promise<{ id: string, email: string, role: string, display_name: string | null }>}
 */
export async function fetchMe(accessToken) {
  if (failNextFetch || stickyMeFail()) {
    // One-shot arm is module-local. The window flag is the init-script outage
    // and stays set until resetMeHarness, so a second caller (shell + page,
    // or StrictMode's second effect) still sees the failure.
    failNextFetch = false
    throw new MeApiError('Не удалось загрузить профиль. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (useMocks()) {
    const session = await getSession()
    return {
      id: 'mock-user-id',
      email: session?.user?.email ?? 'analyst@sberbank.ru',
      role: resolveMockRole(),
      display_name: mockDisplayName,
    }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new MeApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new MeApiError('Не удалось загрузить профиль. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new MeApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (!response.ok) {
    throw new MeApiError('Не удалось загрузить профиль. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }
  return response.json()
}

/**
 * Persist display name on profiles (+ optional Auth metadata sync is caller's job).
 * @param {string} displayName
 * @param {string | null | undefined} accessToken
 * @returns {Promise<{ id: string, email: string, role: string, display_name: string | null }>}
 */
export async function updateDisplayName(displayName, accessToken) {
  const trimmed = displayName.trim()
  if (!trimmed) {
    throw new MeApiError('Укажите имя.', { code: 'VALIDATION', retryable: false })
  }

  if (useMocks()) {
    mockDisplayName = trimmed
    const session = await getSession()
    return {
      id: 'mock-user-id',
      email: session?.user?.email ?? 'analyst@sberbank.ru',
      role: resolveMockRole(),
      display_name: mockDisplayName,
    }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new MeApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/me`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ display_name: trimmed }),
    })
  } catch {
    throw new MeApiError('Не удалось сохранить имя. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new MeApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (!response.ok) {
    throw new MeApiError('Не удалось сохранить имя. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }
  return response.json()
}

/**
 * @param {string | null | undefined} accessToken
 * @returns {Promise<{ ok: boolean, id: string }>}
 */
export async function postPing(accessToken) {
  if (failNextFetch) {
    failNextFetch = false
    throw new MeApiError('Не удалось выполнить ping. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (useMocks()) {
    return { ok: true, id: 'mock-ping-id' }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new MeApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/me/ping`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: '{}',
    })
  } catch {
    throw new MeApiError('Не удалось выполнить ping. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new MeApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }
  if (!response.ok) {
    throw new MeApiError('Не удалось выполнить ping. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }
  return response.json()
}
