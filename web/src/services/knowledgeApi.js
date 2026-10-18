/**
 * Knowledge search API — GET /knowledge/search (KNOW-01 / D-57 / D-59 / D-61 / D-62).
 * role is analyst | ds or omitted («Все»). invalid_role → «Фильтр недоступен».
 * Mock/live cutover via isMocksEnabled(); never silent mock fallback after live failure.
 *
 * Auth/env imports are dynamic so pure mockSearchKnowledge stays node:test-friendly.
 */
import { delay } from '../utils/delay.js'
import { materials } from '../data/mock.js'

export const DEFAULT_SEARCH_LIMIT = 10

/** Max Unicode code points for q (matches backend / KNOW-01). */
export const MAX_QUERY_CODE_POINTS = 500

/**
 * Client-side blank/overlong guards before calling search (KNOW-01 / D-57).
 * @param {string} raw
 * @returns {{ ok: true, q: string } | { ok: false, code: string, message: string }}
 */
export function validateKnowledgeQuery(raw) {
  const trimmed = String(raw ?? '').trim()
  if (!trimmed) {
    return { ok: false, code: 'EMPTY_QUERY', message: 'Введите запрос' }
  }
  if ([...trimmed].length > MAX_QUERY_CODE_POINTS) {
    return { ok: false, code: 'QUERY_TOO_LONG', message: 'Сократите запрос' }
  }
  return { ok: true, q: trimmed }
}

export class KnowledgeApiError extends Error {
  constructor(message, { code = 'KNOWLEDGE_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'KnowledgeApiError'
    this.code = code
    this.retryable = retryable
  }
}

let failNextSearch = false

/** Playwright/unit harness: fail next searchKnowledge call once. */
export function armFailNextKnowledgeSearch() {
  failNextSearch = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ = true
  }
}

export function clearFailNextKnowledgeSearch() {
  failNextSearch = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ = false
  }
}

function consumeFailNext() {
  if (failNextSearch) {
    failNextSearch = false
    return true
  }
  return typeof window !== 'undefined' && window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ === true
}

/**
 * Pure mock hybrid-ish filter → HTTP DTO (no score). Testable without Vite env.
 * @param {{ q?: string, role?: string | null, limit?: number, offset?: number }} opts
 * @param {Array<object>} catalog
 */
export function mockSearchKnowledge(
  { q = '', role = null, limit = DEFAULT_SEARCH_LIMIT, offset = 0 } = {},
  catalog = materials,
) {
  const tokens = String(q)
    .toLowerCase()
    .split(/[\s,.#]+/)
    .filter(Boolean)

  const matched = catalog.filter((item) => {
    if (role && !(item.roles ?? []).includes(role)) return false
    if (!tokens.length) return true
    const haystack =
      `${item.title} ${item.keywords ?? ''} ${(item.tags ?? []).join(' ')} ${item.snippet ?? ''}`.toLowerCase()
    return tokens.some((token) => haystack.includes(token))
  })

  const page = matched.slice(offset, offset + limit)
  const has_more = matched.length > offset + limit

  return {
    items: page.map((item) => ({
      slug: item.id,
      title: item.title,
      snippet: item.snippet ?? '',
      tags: Array.isArray(item.tags) ? [...item.tags] : [],
      cover_url: item.cover == null || item.cover === '' ? null : item.cover,
      roles: Array.isArray(item.roles) ? [...item.roles] : [],
    })),
    has_more,
    limit,
    offset,
  }
}

/**
 * Authenticated knowledge search.
 * @param {{ q: string, role?: string | null, limit?: number, offset?: number }} opts
 * @param {string | null} [accessToken]
 */
export async function searchKnowledge(
  { q, role = null, limit = DEFAULT_SEARCH_LIMIT, offset = 0 } = {},
  accessToken = null,
) {
  if (consumeFailNext()) {
    throw new KnowledgeApiError('Не удалось выполнить поиск. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const { isMocksEnabled } = await import('./authEnv.js')
  if (isMocksEnabled()) {
    await delay(80)
    return mockSearchKnowledge({ q, role, limit, offset }, materials)
  }

  const { getAccessToken } = await import('./authApi.js')
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new KnowledgeApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
  const params = new URLSearchParams()
  params.set('q', q ?? '')
  if (role) params.set('role', role)
  params.set('limit', String(limit))
  params.set('offset', String(offset))

  let response
  try {
    response = await fetch(`${apiBase}/knowledge/search?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new KnowledgeApiError('Не удалось выполнить поиск. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (response.status === 401) {
    throw new KnowledgeApiError('Сессия истекла. Войдите снова.', {
      code: 'UNAUTHORIZED',
      retryable: false,
    })
  }

  if (response.status === 400) {
    let detail = 'empty_query'
    try {
      const body = await response.json()
      detail = body?.detail ?? detail
    } catch {
      /* keep default */
    }
    if (detail === 'invalid_role') {
      throw new KnowledgeApiError('Фильтр недоступен', {
        code: 'INVALID_ROLE',
        retryable: false,
      })
    }
    throw new KnowledgeApiError('Некорректный запрос.', {
      code: detail === 'query_too_long' ? 'QUERY_TOO_LONG' : 'EMPTY_QUERY',
      retryable: false,
    })
  }

  if (!response.ok) {
    throw new KnowledgeApiError('Не удалось выполнить поиск. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const body = await response.json()
  return {
    items: (body.items ?? []).map((hit) => ({
      slug: hit.slug,
      title: hit.title,
      snippet: hit.snippet ?? '',
      tags: hit.tags ?? [],
      cover_url: hit.cover_url ?? null,
      roles: hit.roles ?? [],
      // Intentionally omit score even if backend ever sends one (T-04-01 / D-59).
    })),
    has_more: Boolean(body.has_more),
    limit: body.limit ?? limit,
    offset: body.offset ?? offset,
  }
}
