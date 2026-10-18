/**
 * RED→GREEN: admin preview composition helpers (G-05-1 / ADMIN-04).
 * Pure module — no Vite/supabase imports (node --test friendly).
 * Run: node --test tests/unit/test_admin_preview_composition.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

const sampleReady = [
  { material_id: 102, rank: 2, title: 'Anomaly Detection in Audit Pipelines' },
  { material_id: 101, rank: 1, title: 'Building Production RAG Systems' },
]

describe('buildDefaultMaterialBlocks', () => {
  it('orders material blocks by rank ascending', async () => {
    const { buildDefaultMaterialBlocks } = await import(
      '../../web/src/services/adminPreviewComposition.js'
    )
    assert.deepEqual(buildDefaultMaterialBlocks(sampleReady), [
      { kind: 'material', material_id: 101 },
      { kind: 'material', material_id: 102 },
    ])
  })
})

describe('composePreviewBody', () => {
  it('places intro before material titles and interstitial text', async () => {
    const { composePreviewBody } = await import(
      '../../web/src/services/adminPreviewComposition.js'
    )
    const titleById = new Map(sampleReady.map((row) => [row.material_id, row.title]))
    const body = composePreviewBody({
      intro: 'Добрый день коллеги!',
      blocks: [
        { kind: 'material', material_id: 101 },
        { kind: 'text', text: 'связка' },
        { kind: 'material', material_id: 102 },
      ],
      titleById,
    })
    assert.match(body, /Добрый день коллеги!/)
    const introAt = body.indexOf('Добрый день коллеги!')
    const aAt = body.indexOf('Building Production RAG Systems')
    const bridgeAt = body.indexOf('связка')
    const bAt = body.indexOf('Anomaly Detection in Audit Pipelines')
    assert.ok(introAt >= 0 && aAt > introAt && bridgeAt > aAt && bAt > bridgeAt)
  })

  it('omits blank intro and blank text blocks', async () => {
    const { composePreviewBody } = await import(
      '../../web/src/services/adminPreviewComposition.js'
    )
    const titleById = new Map([[101, 'Building Production RAG Systems']])
    const body = composePreviewBody({
      intro: '   ',
      blocks: [
        { kind: 'text', text: '  ' },
        { kind: 'material', material_id: 101 },
      ],
      titleById,
    })
    assert.equal(body.includes('Добрый'), false)
    assert.match(body, /Building Production RAG Systems/)
  })
})

describe('compositionFingerprint', () => {
  it('changes when intro, order, or interstitial text drifts', async () => {
    const { compositionFingerprint } = await import(
      '../../web/src/services/adminPreviewComposition.js'
    )
    const base = compositionFingerprint({
      intro: 'Hello',
      blocks: [
        { kind: 'material', material_id: 101 },
        { kind: 'text', text: 'bridge' },
        { kind: 'material', material_id: 102 },
      ],
    })
    const introDrift = compositionFingerprint({
      intro: 'Hello changed',
      blocks: [
        { kind: 'material', material_id: 101 },
        { kind: 'text', text: 'bridge' },
        { kind: 'material', material_id: 102 },
      ],
    })
    const orderDrift = compositionFingerprint({
      intro: 'Hello',
      blocks: [
        { kind: 'material', material_id: 102 },
        { kind: 'text', text: 'bridge' },
        { kind: 'material', material_id: 101 },
      ],
    })
    const textDrift = compositionFingerprint({
      intro: 'Hello',
      blocks: [
        { kind: 'material', material_id: 101 },
        { kind: 'text', text: 'other' },
        { kind: 'material', material_id: 102 },
      ],
    })
    assert.notEqual(base, introDrift)
    assert.notEqual(base, orderDrift)
    assert.notEqual(base, textDrift)
    assert.equal(
      base,
      compositionFingerprint({
        intro: 'Hello',
        blocks: [
          { kind: 'material', material_id: 101 },
          { kind: 'text', text: 'bridge' },
          { kind: 'material', material_id: 102 },
        ],
      }),
    )
  })
})
