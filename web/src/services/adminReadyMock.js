/**
 * Pure admin mark-ready mock helpers (ADUX-05 / D-07, D-08).
 * No Vite/supabase/import.meta — safe under node --test.
 */

/** @typedef {{ material_id: number, rank: number, title: string, material_status: 'ready'|'draft', decision: 'pending'|'approved'|'rejected', score: number|null, factor_labels: string[], dek?: string, body_markdown?: string, provenance_label?: string, slug?: string, reading_minutes?: number, char_count?: number, word_count?: number }} AdminShortlistItem */

/** Default mock shortlist seed — material 104 has empty factor_labels (ADUX-06). */
const MOCK_DEFAULT_ITEMS = /** @type {AdminShortlistItem[]} */ ([
  {
    material_id: 101,
    rank: 1,
    title: 'Building Production RAG Systems',
    material_status: 'ready',
    decision: 'pending',
    score: 0.92,
    factor_labels: ['relevance', 'freshness', 'engagement'],
    dek: 'Как быстро находить фрагменты регламентов СВА.',
    body_markdown: '## RAG для СВА\n\nФрагменты регламентов находятся быстрее.',
    provenance_label: 'YouTube · lecture',
    slug: 'building-production-rag-systems',
    reading_minutes: 2,
    char_count: 128,
    word_count: 18,
  },
  {
    material_id: 102,
    rank: 2,
    title: 'Anomaly Detection in Audit Pipelines',
    material_status: 'ready',
    decision: 'pending',
    score: 0.87,
    factor_labels: ['relevance', 'freshness', 'engagement'],
    dek: 'Как замечать аномалии в аудиторских выборках.',
    body_markdown: 'Аномалии в выборках обнаруживаются раньше.',
    provenance_label: 'YouTube · podcast',
    slug: 'anomaly-detection-in-audit-pipelines',
    reading_minutes: 3,
    char_count: 96,
    word_count: 12,
  },
  {
    material_id: 103,
    rank: 3,
    title: 'Prompt Engineering Patterns 2026',
    material_status: 'ready',
    decision: 'pending',
    score: 0.81,
    factor_labels: ['relevance', 'freshness'],
    dek: 'Паттерны формулировок запросов к LLM для аудита.',
    body_markdown: 'Паттерны промптов для аудиторских запросов.',
    provenance_label: 'Internal note',
    slug: 'prompt-engineering-patterns-2026',
    reading_minutes: 2,
    char_count: 80,
    word_count: 10,
  },
  {
    material_id: 104,
    rank: 4,
    title: 'SQL Dashboards for Audit Reporting',
    material_status: 'draft',
    decision: 'pending',
    score: 0.74,
    factor_labels: [],
    dek: 'Черновик витрин для ежемесячной отчётности.',
    body_markdown: '',
    provenance_label: '',
    slug: 'sql-dashboards-for-audit-reporting',
    reading_minutes: 1,
    char_count: 0,
    word_count: 0,
  },
  {
    material_id: 105,
    rank: 5,
    title: 'Data Quality Checks for Regulated Domains',
    material_status: 'ready',
    decision: 'pending',
    score: 0.69,
    factor_labels: ['relevance'],
    dek: 'Один фактор — обоснование недоступно.',
    body_markdown: 'Проверки качества данных в регулируемых доменах.',
    provenance_label: '',
    slug: 'data-quality-checks-for-regulated-domains',
    reading_minutes: 1,
    char_count: 64,
    word_count: 8,
  },
])

/**
 * Deep-clone default mock items (ADUX-06 empty seed for material 104).
 * @returns {AdminShortlistItem[]}
 */
export function getMockDefaultItems() {
  return MOCK_DEFAULT_ITEMS.map((item) => ({
    ...item,
    factor_labels: [...item.factor_labels],
  }))
}

/**
 * Flip matching material_id to ready; leave others unchanged.
 * @param {Array<{ material_id: number, material_status: string }>} items
 * @param {number} materialId
 * @returns {boolean} true when found and updated
 */
export function applyMockMarkReady(items, materialId) {
  const item = (items ?? []).find((row) => row.material_id === materialId)
  if (!item) return false
  item.material_status = 'ready'
  return true
}

/**
 * Batch promote in one call — owns the loop (D-08); does not call markReady export.
 * @param {Array<{ material_id: number, material_status: string }>} items
 * @param {number[]} materialIds
 * @returns {{ results: Array<{ material_id: number, ok: boolean, status: string|null, error: string|null }> }}
 */
export function applyMockMarkReadyBatch(items, materialIds) {
  const results = []
  for (const materialId of materialIds ?? []) {
    const item = (items ?? []).find((row) => row.material_id === materialId)
    if (!item) {
      results.push({
        material_id: materialId,
        ok: false,
        status: null,
        error: 'material_not_found',
      })
      continue
    }
    item.material_status = 'ready'
    results.push({
      material_id: materialId,
      ok: true,
      status: 'ready',
      error: null,
    })
  }
  return { results }
}
