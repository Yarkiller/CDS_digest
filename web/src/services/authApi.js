import { supabase } from './supabaseClient.js'
import { oauthEnabled, yandexProviderId } from './oauthSession.js'

export class AuthApiError extends Error {
  constructor(message, { code = 'AUTH_FAILED', retryable = false } = {}) {
    super(message)
    this.name = 'AuthApiError'
    this.code = code
    this.retryable = retryable
  }
}

/** @type {{ access_token: string, user: { email: string } } | null} */
let mockSession = null
let signInInvocations = 0
let signUpInvocations = 0
let failNextSignIn = false
let failNextSignUp = false
let signUpWithoutSession = false
let mockOAuthEmail = null

export function armFailNextSignIn() {
  failNextSignIn = true
}

export function armFailNextSignUp() {
  failNextSignUp = true
}

export function armSignUpWithoutSession() {
  signUpWithoutSession = true
}

/** Test harness: set the email returned by the mocked Yandex ID OAuth flow. */
export function armOAuthEmail(email) {
  mockOAuthEmail = email
}

export function resetAuthHarness() {
  mockSession = null
  signInInvocations = 0
  signUpInvocations = 0
  failNextSignIn = false
  failNextSignUp = false
  signUpWithoutSession = false
  mockOAuthEmail = null
}

export function getSignInInvocationCount() {
  return signInInvocations
}

export function getSignUpInvocationCount() {
  return signUpInvocations
}

function liveAuthEnabled() {
  return import.meta.env.VITE_USE_MOCKS === 'false'
}

/**
 * @param {{ email: string, password: string }} credentials
 */
export async function signIn({ email, password }) {
  signInInvocations += 1

  if (failNextSignIn) {
    failNextSignIn = false
    throw new AuthApiError('Сервис входа временно недоступен. Проверьте соединение и повторите попытку.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!liveAuthEnabled()) {
    mockSession = {
      access_token: 'mock-access-token',
      user: { email },
    }
    return mockSession
  }

  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) {
    const retryable = (error.status != null && error.status >= 500) || error.name === 'AuthRetryableFetchError'
    throw new AuthApiError(
      retryable
        ? 'Сервис входа временно недоступен. Проверьте соединение и повторите попытку.'
        : 'Не удалось войти. Проверьте данные и повторите попытку.',
      {
        code: retryable ? 'NETWORK' : 'CREDENTIALS',
        retryable,
      },
    )
  }
  return data.session
}

export async function signOut() {
  mockSession = null
  if (liveAuthEnabled()) {
    await supabase.auth.signOut()
  }
}

/**
 * Start Yandex ID OAuth via Supabase.
 * Live mode: initiates the redirect and resolves with null (the SPA is navigating away).
 * Mock mode: resolves with a mock session carrying the harness-provided email.
 * @returns {Promise<{ access_token: string, user: { email: string } } | null>}
 */
export async function signInWithYandex() {
  if (!oauthEnabled(import.meta.env)) {
    throw new AuthApiError('Вход через Яндекс ID отключён.', { code: 'OAUTH_DISABLED' })
  }

  if (!liveAuthEnabled()) {
    const email = mockOAuthEmail ?? 'oauth.user@yandex.ru'
    mockOAuthEmail = null
    mockSession = {
      access_token: 'mock-oauth-token',
      user: { email, app_metadata: { provider: 'yandex' } },
    }
    return mockSession
  }

  const redirectTo = `${window.location.origin}/login?oauth=yandex`
  const { error } = await supabase.auth.signInWithOAuth({
    provider: yandexProviderId(import.meta.env),
    options: { redirectTo },
  })
  if (error) {
    throw new AuthApiError('Не удалось начать вход через Яндекс ID. Повторите попытку.', {
      code: 'OAUTH',
      retryable: true,
    })
  }
  return null
}

export async function getSession() {
  if (!liveAuthEnabled()) {
    return mockSession
  }
  const { data, error } = await supabase.auth.getSession()
  if (error) {
    throw new AuthApiError(error.message, { code: 'SESSION', retryable: true })
  }
  return data.session
}

export async function getAccessToken() {
  const session = await getSession()
  return session?.access_token ?? null
}

/**
 * Self-service registration via publishable supabase-js only (never service_role).
 * @param {{ email: string, password: string, displayName: string }} credentials
 */
export async function signUp({ email, password, displayName }) {
  signUpInvocations += 1

  if (failNextSignUp) {
    failNextSignUp = false
    throw new AuthApiError('Сервис входа временно недоступен. Проверьте соединение и повторите попытку.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (signUpWithoutSession) {
    signUpWithoutSession = false
    return null
  }

  const trimmedName = (displayName ?? '').trim()

  if (!liveAuthEnabled()) {
    mockSession = {
      access_token: 'mock-access-token',
      user: { email, user_metadata: { full_name: trimmedName, display_name: trimmedName } },
    }
    return mockSession
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: trimmedName,
        display_name: trimmedName,
      },
    },
  })
  if (error) {
    const retryable = (error.status != null && error.status >= 500) || error.name === 'AuthRetryableFetchError'
    throw new AuthApiError(
      retryable
        ? 'Сервис входа временно недоступен. Проверьте соединение и повторите попытку.'
        : 'Не удалось зарегистрироваться. Проверьте данные и повторите попытку.',
      {
        code: retryable ? 'NETWORK' : 'CREDENTIALS',
        retryable,
      },
    )
  }
  return data.session
}

/**
 * Sync Auth dashboard Display name via user_metadata (full_name + display_name).
 * @param {string} displayName
 */
export async function updateAuthDisplayName(displayName) {
  const trimmed = displayName.trim()
  if (!trimmed) {
    return
  }
  if (!liveAuthEnabled()) {
    return
  }
  const { error } = await supabase.auth.updateUser({
    data: { full_name: trimmed, display_name: trimmed },
  })
  if (error) {
    throw new AuthApiError('Не удалось обновить имя в Auth. Повторите попытку.', {
      code: 'METADATA',
      retryable: true,
    })
  }
}
