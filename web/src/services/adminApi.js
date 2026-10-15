/**
 * Admin shortlist API — GET/decision/preview/send (ADMIN-01…07).
 * Mock/live cutover via isMocksEnabled(); never silent mock fallback after live failure.
 */

import { delay } from '../utils/delay.js'
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'
import {
  buildDefaultMaterialBlocks,
  composePreviewBody,
  composePreviewItems,
} from './adminPreviewComposition.js'
import {
  applyMockMarkReady,
  applyMockMarkReadyBatch,
  getMockDefaultItems,
} from './adminReadyMock.js'

export { buildDefaultMaterialBlocks, composePreviewBody, composePreviewItems }
export { applyMockMarkReady, applyMockMarkReadyBatch, getMockDefaultItems }

export class AdminApiError extends Error {
  constructor(message, { code = 'ADMIN_FAILED', retryable = true, detail = null } = {}) {
    super(message)
    this.name = 'AdminApiError'
    this.code = code
    this.retryable = retryable
    this.detail = detail
  }
}

/** @typedef {{ material_id: number, rank: number, title: string, material_status: 'ready'|'draft', decision: 'pending'|'approved'|'rejected', score: number|null, factor_labels: string[], dek?: string, body_markdown?: string, provenance_label?: string, slug?: string, reading_minutes?: number, char_count?: number, word_count?: number }} AdminShortlistItem */
/** @typedef {{ batch_id: number|null, sent_at: string|null, week_label: string|null, items: AdminShortlistItem[], digest_rest?: boolean, days_until_next_batch?: number|null }} AdminShortlistDto */
/** @typedef {{ material_id: number, status: 'ready' }} MarkReadyResult */

/** Locked product weekly cadence days (G-05-2 / PROJECT.md weekly digest). */
export const DIGEST_WEEKLY_CADENCE_DAYS = 7

const DEFAULT_ITEMS = getMockDefaultItems()

/** @type {AdminShortlistDto} */
let mockBatch = {
  batch_id: 1,
  sent_at: null,
  week_label: '18–24 марта 2026',
  items: DEFAULT_ITEMS.map((item) => ({ ...item, factor_labels: [...item.factor_labels] })),
}

let failNextFetch = false
let failNextDecision = false
let failNextPreview = false
let failNextSend = false
let alreadySentOnSend = false
let mockMarkReadyBatchCalls = 0

function useMocks() {
  return isMocksEnabled()
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

function stickyFlag(name) {
  return typeof window !== 'undefined' && Boolean(window[name])
}

function cloneBatch() {
  return {
    batch_id: mockBatch.batch_id,
    sent_at: mockBatch.sent_at,
    week_label: mockBatch.week_label,
    items: mockBatch.items.map((item) => ({
      ...item,
      factor_labels: [...(item.factor_labels ?? [])],
    })),
    digest_rest: false,
    days_until_next_batch: null,
  }
}

function restDto() {
  return {
    batch_id: null,
    sent_at: mockBatch.sent_at,
    week_label: null,
    items: [],
    digest_rest: true,
    days_until_next_batch: DIGEST_WEEKLY_CADENCE_DAYS,
  }
}

function emptyDto() {
  return {
    batch_id: null,
    sent_at: null,
    week_label: null,
    items: [],
    digest_rest: false,
    days_until_next_batch: null,
  }
}

/** Empty-unsent batch mock (D-04 #2 / D-12 / D-13 — ISO week_label, not human RU). */
function emptyUnsentDto() {
  return {
    batch_id: 7,
    sent_at: null,
    week_label: '2026-10-06',
    items: [],
    digest_rest: false,
    days_until_next_batch: null,
  }
}

function mapShortlistBody(body) {
  return {
    batch_id: body.batch_id ?? null,
    sent_at: body.sent_at ?? null,
    week_label: body.week_label ?? null,
    items: Array.isArray(body.items) ? body.items : [],
    digest_rest: Boolean(body.digest_rest),
    days_until_next_batch:
      body.days_until_next_batch == null ? null : Number(body.days_until_next_batch),
  }
}

function resetMockItems() {
  mockBatch = {
    batch_id: 1,
    sent_at: null,
    week_label: '18–24 марта 2026',
    items: DEFAULT_ITEMS.map((item) => ({ ...item, factor_labels: [...item.factor_labels] })),
  }
}

export function armFailNextShortlistFetch() {
  failNextFetch = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_FAIL_SHORTLIST__ = true
  }
}

export function clearFailNextShortlistFetch() {
  failNextFetch = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_FAIL_SHORTLIST__ = false
  }
}

export function armFailNextDecision() {
  failNextDecision = true
}

export function armFailNextPreview() {
  failNextPreview = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_FAIL_PREVIEW__ = true
  }
}

export function clearFailNextPreview() {
  failNextPreview = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_FAIL_PREVIEW__ = false
  }
}

export function armFailNextSend() {
  failNextSend = true
}

export function armAlreadySentOnSend() {
  alreadySentOnSend = true
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_ALREADY_SENT__ = true
  }
}

export function resetAdminHarness() {
  failNextFetch = false
  failNextDecision = false
  failNextPreview = false
  failNextSend = false
  alreadySentOnSend = false
  mockMarkReadyBatchCalls = 0
  resetMockItems()
  if (typeof window !== 'undefined') {
    window.__DIGEST_ADMIN_EMPTY__ = false
    window.__DIGEST_ADMIN_EMPTY_UNSENT__ = false
    window.__DIGEST_ADMIN_DIGEST_REST__ = false
    window.__DIGEST_ADMIN_FAIL_SHORTLIST__ = false
    window.__DIGEST_ADMIN_FAIL_PREVIEW__ = false
    window.__DIGEST_ADMIN_ALREADY_SENT__ = false
    window.__DIGEST_ADMIN_MATERIAL_EMPTY_BODY__ = false
    window.__DIGEST_ADMIN_MATERIAL_LONG_BODY__ = false
    window.__DIGEST_ADMIN_STALE_READY__ = false
  }
}

/** Playwright: count of mock markReadyBatch invocations (D-08). */
export function getMockMarkReadyBatchCalls() {
  return mockMarkReadyBatchCalls
}

function shouldFailFetch() {
  if (failNextFetch || stickyFlag('__DIGEST_ADMIN_FAIL_SHORTLIST__')) {
    failNextFetch = false
    return true
  }
  return false
}

function mapHttpError(response, fallbackMessage) {
  if (response.status === 403) {
    return new AdminApiError('Недостаточно прав.', { code: 'FORBIDDEN', retryable: false })
  }
  if (response.status === 409) {
    return new AdminApiError('Уже отправлено', {
      code: 'ALREADY_SENT',
      retryable: false,
    })
  }
  if (response.status === 400) {
    return new AdminApiError(fallbackMessage, { code: 'BAD_REQUEST', retryable: false })
  }
  if (response.status === 404) {
    return new AdminApiError(fallbackMessage, { code: 'NOT_FOUND', retryable: false })
  }
  return new AdminApiError(fallbackMessage, { code: 'NETWORK', retryable: true })
}

/**
 * @returns {Promise<AdminShortlistDto>}
 */
export async function fetchShortlist(accessToken) {
  if (useMocks()) {
    await delay(80)
    if (shouldFailFetch()) {
      throw new AdminApiError('Не удалось загрузить shortlist. Проверьте сеть.', {
        code: 'NETWORK',
        retryable: true,
      })
    }
    if (stickyFlag('__DIGEST_ADMIN_DIGEST_REST__')) {
      return restDto()
    }
    if (stickyFlag('__DIGEST_ADMIN_EMPTY_UNSENT__')) {
      return emptyUnsentDto()
    }
    if (stickyFlag('__DIGEST_ADMIN_EMPTY__')) {
      return emptyDto()
    }
    if (mockBatch.sent_at) {
      return restDto()
    }
    const batch = cloneBatch()
    if (stickyFlag('__DIGEST_ADMIN_MATERIAL_EMPTY_BODY__') && batch.items[0]) {
      batch.items[0] = {
        ...batch.items[0],
        body_markdown: '',
        provenance_label: '',
        char_count: 0,
        word_count: 0,
        reading_minutes: 1,
      }
    }
    if (stickyFlag('__DIGEST_ADMIN_MATERIAL_LONG_BODY__') && batch.items[0]) {
      const sentence = 'Фрагменты регламентов находятся быстрее.'
      batch.items[0] = {
        ...batch.items[0],
        body_markdown: Array.from({ length: 40 }, () => sentence).join('\n\n'),
      }
    }
    return batch
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new AdminApiError('Не удалось загрузить shortlist. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не удалось загрузить shortlist. Проверьте сеть.')
  }

  const body = await response.json()
  return mapShortlistBody(body)
}

/** @typedef {{ slug: string, title: string, dek: string, body_markdown: string, format: string, provenance: string, tags: string[], related: Array<{ slug: string, title: string }>, reading_minutes: number, published_at: string|null, editor: string }} MaterialPreviewDto */

/**
 * Sticky mock seat role — read directly from the window seat flag (the same
 * convention the /me mock uses) so the preview performs no extra round trip (D-03).
 * @returns {string}
 */
function mockSeatRole() {
  if (typeof window !== 'undefined' && typeof window.__DIGEST_MOCK_ME_ROLE__ === 'string') {
    return window.__DIGEST_MOCK_ME_ROLE__
  }
  return 'employee'
}

/**
 * Draft material preview by slug via the admin-gated endpoint (ADUX-07, ADUX-08).
 * 403 → FORBIDDEN; 404 → NOT_FOUND (the caller sends a non-draft to the reader route).
 * Mock branch resolves against the shortlist batch (its items carry
 * material_status) — never against web/src/data/mock.js (D-12, Pitfall 7).
 * @param {string} slug
 * @param {string} [accessToken]
 * @returns {Promise<MaterialPreviewDto>}
 */
export async function fetchMaterialPreview(slug, accessToken) {
  if (useMocks()) {
    await delay(80)
    // The seat-role gate runs BEFORE the slug lookup — the client mirror of
    // require_admin running before the repository read, so an employee cannot
    // distinguish an existing slug from a missing one (D-03).
    if (mockSeatRole() !== 'admin') {
      throw new AdminApiError('Недостаточно прав.', { code: 'FORBIDDEN', retryable: false })
    }
    const item = mockBatch.items.find((row) => row.slug === slug)
    if (!item || item.material_status !== 'draft') {
      throw new AdminApiError('Материал не найден.', { code: 'NOT_FOUND', retryable: false })
    }
    return {
      slug: item.slug,
      title: item.title,
      dek: item.dek ?? '',
      body_markdown: item.body_markdown ?? '',
      format: item.format ?? 'статья',
      provenance: item.provenance_label ?? '',
      tags: [],
      related: [],
      reading_minutes: item.reading_minutes ?? 1,
      published_at: null,
      editor: 'Редакция Digest CDS',
    }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/materials/${encodeURIComponent(slug)}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new AdminApiError('Не удалось загрузить материал. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Материал не найден.')
  }

  return response.json()
}

/**
 * @param {number} materialId
 * @param {'pending'|'approved'|'rejected'} decision
 * @returns {Promise<AdminShortlistDto>}
 */
export async function setDecision(materialId, decision, accessToken) {
  if (useMocks()) {
    await delay(60)
    if (failNextDecision) {
      failNextDecision = false
      throw new AdminApiError('Не сохранено', { code: 'NETWORK', retryable: true })
    }
    const item = mockBatch.items.find((row) => row.material_id === materialId)
    if (!item) {
      throw new AdminApiError('Материал не найден.', { code: 'NOT_FOUND', retryable: false })
    }
    item.decision = decision
    return cloneBatch()
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist/items/${materialId}/decision`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ decision }),
    })
  } catch {
    throw new AdminApiError('Не сохранено', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не сохранено')
  }

  const body = await response.json()
  return mapShortlistBody(body)
}

/**
 * Promote a single material draft→ready (ADUX-05 / D-07).
 * The POST response is the source of truth for the promoted row — this is
 * decoupled from any shortlist refetch (G-14-2 #1).
 * @param {number} materialId
 * @param {string} [accessToken]
 * @returns {Promise<MarkReadyResult>} Authoritative promote result { material_id, status }.
 */
export async function markReady(materialId, accessToken) {
  if (useMocks()) {
    await delay(60)
    const exists = mockBatch.items.some((row) => row.material_id === materialId)
    if (!exists) {
      throw new AdminApiError('Материал не найден.', { code: 'NOT_FOUND', retryable: false })
    }
    // Stale-ready harness: simulate a backend that acknowledges the POST but does
    // not persist, so the silent-revert reconcile class is exercised under mocks (G-14-2).
    if (!stickyFlag('__DIGEST_ADMIN_STALE_READY__')) {
      applyMockMarkReady(mockBatch.items, materialId)
    }
    return { material_id: materialId, status: 'ready' }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/materials/${materialId}/ready`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
  } catch {
    throw new AdminApiError('Не удалось сделать ready', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не удалось сделать ready')
  }

  // Promote persisted; MarkReadyResponse is authoritative (G-14-2 — no refetch coupling).
  return response.json()
}

/**
 * Batch promote materials draft→ready in one POST (ADUX-05 / D-08).
 * Must not call markReady — single /admin/materials/ready request.
 * @param {number[]} materialIds
 * @param {string} [accessToken]
 * @returns {Promise<{ results: Array<{ material_id: number, ok: boolean, status: string|null, error: string|null }> }>}
 */
export async function markReadyBatch(materialIds, accessToken) {
  if (useMocks()) {
    mockMarkReadyBatchCalls += 1
    await delay(60)
    return applyMockMarkReadyBatch(mockBatch.items, materialIds ?? [])
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/materials/ready`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ material_ids: materialIds ?? [] }),
    })
  } catch {
    throw new AdminApiError('Не удалось сделать ready', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не удалось сделать ready')
  }

  return response.json()
}

/**
 * Escape text for mock email HTML (mirrors backend html.escape for Playwright honesty).
 * @param {string} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Interstitial/intro HTML for mocks — blank line → new paragraph (D-13/D-15).
 * @param {string} text
 * @returns {string}
 */
function composeMockInterstitialHtml(text) {
  const trimmed = String(text ?? '').trim()
  if (!trimmed) return ''
  const safe = escapeHtml(trimmed)
  return safe
    .split('\n\n')
    .filter(Boolean)
    .map((para) => `<p>${para.replace(/\n/g, '<br>')}</p>`)
    .join('')
}

/**
 * Mock preview HTML shaped like backend render_email_html (titles + Читать →).
 * Live path must prefer API `html` — this is mock-only.
 * @param {{ intro?: string, blocks?: Array<{ kind: string, material_id?: number, text?: string }>, itemById?: Map<number, AdminShortlistItem> }} opts
 * @returns {string}
 */
function composeMockPreviewHtml({ intro = '', blocks = [], itemById = new Map() } = {}) {
  const parts = []
  const introHtml = composeMockInterstitialHtml(intro)
  if (introHtml) parts.push(introHtml)
  for (const block of blocks ?? []) {
    if (!block || typeof block !== 'object') continue
    if (block.kind === 'text') {
      const textHtml = composeMockInterstitialHtml(block.text ?? '')
      if (textHtml) parts.push(textHtml)
      continue
    }
    if (block.kind === 'material') {
      const item = itemById.get(block.material_id)
      if (!item) continue
      parts.push(`<h2>${escapeHtml(item.title)}</h2>`)
      if (item.dek && String(item.dek).trim()) {
        parts.push(`<p>${escapeHtml(String(item.dek).trim())}</p>`)
      }
      const slug = item.slug || String(item.material_id)
      parts.push(
        `<p><a href="http://127.0.0.1:5173/materials/${escapeHtml(slug)}">Читать →</a></p>`,
      )
    }
  }
  return parts.join('')
}

/**
 * @typedef {{ intro?: string, blocks?: Array<{ kind: 'material', material_id: number } | { kind: 'text', text: string }> }} DigestPreviewComposition
 *
 * @param {string} [accessToken]
 * @param {DigestPreviewComposition} [composition]
 * @returns {Promise<{ batch_id: number, subject: string, body: string, html: string, items: Array<{ material_id: number, rank: number, title: string }> }>}
 */
export async function previewEmail(accessToken, composition = {}) {
  const intro = typeof composition?.intro === 'string' ? composition.intro : ''
  const requestedBlocks = Array.isArray(composition?.blocks) ? composition.blocks : null

  if (useMocks()) {
    await delay(80)
    if (failNextPreview || stickyFlag('__DIGEST_ADMIN_FAIL_PREVIEW__')) {
      failNextPreview = false
      throw new AdminApiError('Превью недоступно', { code: 'NETWORK', retryable: true })
    }
    const pool = mockBatch.items
      .filter((item) => item.decision === 'approved' && item.material_status === 'ready')
      .sort((a, b) => a.rank - b.rank)
    if (pool.length === 0) {
      throw new AdminApiError('Нет одобренных ready-материалов для отправки.', {
        code: 'EMPTY_SEND_POOL',
        retryable: false,
      })
    }
    const byId = new Map(pool.map((item) => [item.material_id, item]))
    const blocks =
      requestedBlocks && requestedBlocks.length > 0
        ? requestedBlocks
        : buildDefaultMaterialBlocks(pool)
    for (const block of blocks) {
      if (block?.kind === 'material' && !byId.has(block.material_id)) {
        throw new AdminApiError('Некорректная композиция превью.', {
          code: 'BAD_REQUEST',
          retryable: false,
        })
      }
    }
    const titleById = new Map(pool.map((item) => [item.material_id, item.title]))
    const items = composePreviewItems(blocks, byId)
    if (items.length === 0) {
      throw new AdminApiError('Нет одобренных ready-материалов для отправки.', {
        code: 'EMPTY_SEND_POOL',
        retryable: false,
      })
    }
    return {
      batch_id: mockBatch.batch_id ?? 1,
      subject: `Digest CDS · ${mockBatch.week_label ?? 'неделя'}`,
      body: composePreviewBody({ intro, blocks, titleById }),
      html: composeMockPreviewHtml({ intro, blocks, itemById: byId }),
      items,
    }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const payload = {
    intro,
    ...(requestedBlocks != null ? { blocks: requestedBlocks } : {}),
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist/preview`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new AdminApiError('Превью недоступно', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Превью недоступно')
  }
  return response.json()
}

/**
 * @param {string} [accessToken]
 * @param {{ material_ids?: number[], intro?: string, blocks?: Array<{ kind: 'material', material_id: number } | { kind: 'text', text: string }> }} [options]
 * @returns {Promise<{ batch_id: number, issue_number: number, issue_url: string, delivery_status: string, recipient_count: number, message: string }>}
 */
export async function sendDigest(accessToken, options = {}) {
  const materialIds = Array.isArray(options?.material_ids) ? options.material_ids : null
  const intro = typeof options?.intro === 'string' ? options.intro : ''
  const blocks = Array.isArray(options?.blocks) ? options.blocks : null

  if (useMocks()) {
    await delay(100)
    if (failNextSend) {
      failNextSend = false
      throw new AdminApiError('Рассылка не отправлена', { code: 'NETWORK', retryable: true })
    }
    if (alreadySentOnSend || stickyFlag('__DIGEST_ADMIN_ALREADY_SENT__') || mockBatch.sent_at) {
      alreadySentOnSend = false
      throw new AdminApiError('Уже отправлено', { code: 'ALREADY_SENT', retryable: false })
    }
    const drafts = mockBatch.items.filter(
      (item) => item.decision === 'approved' && item.material_status === 'draft',
    )
    if (drafts.length > 0) {
      throw new AdminApiError('Уберите черновики из одобренных или дождитесь ready.', {
        code: 'DRAFT_IN_SEND_POOL',
        retryable: false,
        detail: { draft_material_ids: drafts.map((d) => d.material_id) },
      })
    }
    const pool = mockBatch.items.filter(
      (item) => item.decision === 'approved' && item.material_status === 'ready',
    )
    if (pool.length === 0) {
      throw new AdminApiError('Нет одобренных ready-материалов для отправки.', {
        code: 'EMPTY_SEND_POOL',
        retryable: false,
      })
    }
    if (materialIds != null) {
      const poolIds = new Set(pool.map((item) => item.material_id))
      if (materialIds.length !== poolIds.size || materialIds.some((id) => !poolIds.has(id))) {
        throw new AdminApiError('Некорректный порядок материалов.', {
          code: 'BAD_REQUEST',
          retryable: false,
        })
      }
    }
    mockBatch.sent_at = new Date().toISOString()
    return {
      batch_id: mockBatch.batch_id ?? 1,
      issue_number: 15,
      issue_url: '/issues/15',
      delivery_status: 'stubbed',
      recipient_count: 0,
      message: 'Отправка записана',
    }
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  const payload = {}
  if (materialIds != null) payload.material_ids = materialIds
  if (intro) payload.intro = intro
  if (blocks != null) payload.blocks = blocks

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist/send`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new AdminApiError('Рассылка не отправлена', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Рассылка не отправлена')
  }
  return response.json()
}
