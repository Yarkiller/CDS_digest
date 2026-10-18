/**
 * RED→GREEN: admin mark-ready mock helpers + adminApi wiring (ADUX-05 / D-07, D-08).
 * Pure module — no Vite/supabase imports (node --test friendly).
 * Run: node --test tests/unit/test_admin_mark_ready.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')
const fs = require('node:fs')
const path = require('node:path')

function seedItems() {
  return [
    {
      material_id: 101,
      material_status: 'ready',
      decision: 'pending',
      factor_labels: ['relevance', 'freshness'],
    },
    {
      material_id: 104,
      material_status: 'draft',
      decision: 'pending',
      factor_labels: [],
      body_markdown: '',
    },
    {
      material_id: 105,
      material_status: 'draft',
      decision: 'approved',
      factor_labels: ['relevance'],
    },
  ]
}

describe('applyMockMarkReady', () => {
  it('flips matching material_id to ready and leaves others unchanged', async () => {
    const { applyMockMarkReady } = await import('../../web/src/services/adminReadyMock.js')
    const items = seedItems()
    applyMockMarkReady(items, 104)
    assert.equal(items.find((row) => row.material_id === 104).material_status, 'ready')
    assert.equal(items.find((row) => row.material_id === 105).material_status, 'draft')
    assert.equal(items.find((row) => row.material_id === 101).material_status, 'ready')
  })
})

describe('applyMockMarkReadyBatch', () => {
  it('returns order-preserving partial results in a single call (D-08)', async () => {
    const mod = await import('../../web/src/services/adminReadyMock.js')
    const { applyMockMarkReadyBatch, applyMockMarkReady } = mod
    const items = seedItems()
    const { results } = applyMockMarkReadyBatch(items, [104, 999, 105])
    assert.deepEqual(results, [
      { material_id: 104, ok: true, status: 'ready', error: null },
      { material_id: 999, ok: false, status: null, error: 'material_not_found' },
      { material_id: 105, ok: true, status: 'ready', error: null },
    ])
    assert.equal(items.find((row) => row.material_id === 104).material_status, 'ready')
    assert.equal(items.find((row) => row.material_id === 105).material_status, 'ready')
    // Batch owns the loop — applyMockMarkReady remains available but batch must not
    // require N separate HTTP-shaped markReady exports (assert via source below).
    assert.equal(typeof applyMockMarkReady, 'function')
  })
})

describe('getMockDefaultItems ADUX-06 empty seed', () => {
  it('includes material_id 104 with empty factor_labels', async () => {
    const { getMockDefaultItems } = await import('../../web/src/services/adminReadyMock.js')
    const items = getMockDefaultItems()
    const row = items.find((item) => item.material_id === 104)
    assert.ok(row, 'material 104 must exist in mock seed')
    assert.deepEqual(row.factor_labels, [])
    assert.equal(row.material_status, 'draft')
  })
})

describe('adminApi markReady / markReadyBatch exports', () => {
  it('exports markReady and markReadyBatch; batch body never calls markReady (D-08)', async () => {
    const apiPath = path.resolve(__dirname, '../../web/src/services/adminApi.js')
    const source = fs.readFileSync(apiPath, 'utf8')
    assert.match(source, /export async function markReady\b/)
    assert.match(source, /export async function markReadyBatch\b/)
    const batchMatch = source.match(
      /export async function markReadyBatch\([\s\S]*?(?=\nexport async function |\nexport function |\n$)/,
    )
    assert.ok(batchMatch, 'markReadyBatch function body must be present')
    assert.equal(
      /(?<!function )\bmarkReady\s*\(/.test(batchMatch[0].replace(/export async function markReadyBatch/, '')),
      false,
      'markReadyBatch must not call markReady (D-08 single batch POST)',
    )
  })
})

describe('decoupled markReady + reconciled promoteReady refetch (G-14-2 / ADUX-05)', () => {
  it('markReady is decoupled from fetchShortlist and returns a MarkReadyResult', () => {
    const apiPath = path.resolve(__dirname, '../../web/src/services/adminApi.js')
    const source = fs.readFileSync(apiPath, 'utf8')
    const markReadyMatch = source.match(
      /export async function markReady\([\s\S]*?(?=\nexport async function |\nexport function |\n$)/,
    )
    assert.ok(markReadyMatch, 'markReady function body must be present')
    const body = markReadyMatch[0]
    assert.equal(
      body.includes('fetchShortlist'),
      false,
      'G-14-2 #1: markReady must not couple promote success to fetchShortlist',
    )
    assert.match(
      source,
      /@returns \{Promise<MarkReadyResult>\}/,
      'markReady JSDoc must declare the MarkReadyResult return type',
    )
    assert.match(
      body,
      /status: 'ready'/,
      'mock markReady must return a MarkReadyResult-shaped object',
    )
    assert.match(
      body,
      /return response\.json\(\)/,
      'live markReady must return the parsed MarkReadyResponse',
    )
  })

  it('promoteReady reconciles the refetch via preservePromotedReady; batch CTA is gone', () => {
    const pagePath = path.resolve(__dirname, '../../web/src/pages/AdminDigestPage.jsx')
    const source = fs.readFileSync(pagePath, 'utf8')
    assert.match(
      source,
      /import\s*\{[^}]*preservePromotedReady[^}]*\}\s*from\s*['"][^'"]*adminReadyReconcile\.js['"]/,
      'AdminDigestPage must import preservePromotedReady from adminReadyReconcile.js',
    )
    const promoteMatch = source.match(
      /async function promoteReady\([\s\S]*?(?=\n  async function |\n  function )/,
    )
    assert.ok(promoteMatch, 'promoteReady function body must be present')
    assert.match(
      promoteMatch[0],
      /preservePromotedReady\(/,
      'G-14-2 #2: promoteReady must reconcile the refetch through preservePromotedReady',
    )
    // G-14-2 (operator override): the batch promote affordance + handler are removed.
    assert.equal(
      source.includes('markReadyBatch'),
      false,
      'AdminDigestPage must not import/call markReadyBatch (batch CTA removed)',
    )
    assert.equal(
      source.includes('promoteApprovedDrafts'),
      false,
      'AdminDigestPage must not define promoteApprovedDrafts (batch CTA removed)',
    )
    assert.equal(
      source.includes('admin-mark-ready-batch'),
      false,
      'AdminDigestPage must not render the admin-mark-ready-batch testid',
    )
  })
})

describe('preservePromotedReady refetch reconciliation (G-14-2 / ADUX-05)', () => {
  it('forces a still-draft promoted id to ready and leaves other rows untouched', async () => {
    const { preservePromotedReady } = await import(
      '../../web/src/services/adminReadyReconcile.js'
    )
    const refetched = [
      { material_id: 101, material_status: 'ready' },
      { material_id: 104, material_status: 'draft' },
      { material_id: 105, material_status: 'draft' },
    ]
    const result = preservePromotedReady(refetched, [104])
    assert.equal(result.find((row) => row.material_id === 104).material_status, 'ready')
    // Non-promoted rows keep their own status — including a still-draft one.
    assert.equal(result.find((row) => row.material_id === 105).material_status, 'draft')
    assert.equal(result.find((row) => row.material_id === 101).material_status, 'ready')
  })

  it('leaves an already-ready promoted row unchanged (identity preserved)', async () => {
    const { preservePromotedReady } = await import(
      '../../web/src/services/adminReadyReconcile.js'
    )
    const readyRow = { material_id: 101, material_status: 'ready' }
    const result = preservePromotedReady([readyRow], [101])
    assert.equal(result[0], readyRow)
  })

  it('forces every still-draft id in a multi-id promoted set', async () => {
    const { preservePromotedReady } = await import(
      '../../web/src/services/adminReadyReconcile.js'
    )
    const refetched = [
      { material_id: 104, material_status: 'draft' },
      { material_id: 105, material_status: 'draft' },
      { material_id: 106, material_status: 'draft' },
    ]
    const result = preservePromotedReady(refetched, [104, 105])
    assert.equal(result.find((row) => row.material_id === 104).material_status, 'ready')
    assert.equal(result.find((row) => row.material_id === 105).material_status, 'ready')
    assert.equal(result.find((row) => row.material_id === 106).material_status, 'draft')
  })

  it('treats null/undefined refetchedItems as [] and empty promotedIds as a no-op', async () => {
    const { preservePromotedReady } = await import(
      '../../web/src/services/adminReadyReconcile.js'
    )
    assert.deepEqual(preservePromotedReady(null, [104]), [])
    assert.deepEqual(preservePromotedReady(undefined, [104]), [])
    const refetched = [{ material_id: 104, material_status: 'draft' }]
    assert.equal(preservePromotedReady(refetched, []), refetched)
    assert.equal(preservePromotedReady(refetched, null), refetched)
  })
})
