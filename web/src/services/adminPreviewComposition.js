/**
 * Pure digest email preview composition (G-05-1 / ADMIN-04).
 * No Vite/supabase imports — safe under node --test.
 */

/**
 * @typedef {{ kind: 'material', material_id: number }} PreviewMaterialBlock
 * @typedef {{ kind: 'text', text: string }} PreviewTextBlock
 * @typedef {PreviewMaterialBlock | PreviewTextBlock} PreviewBlock
 */

/**
 * Default material blocks from approved∩ready, ordered by rank.
 * @param {Array<{ material_id: number, rank: number }>} approvedReady
 * @returns {PreviewMaterialBlock[]}
 */
export function buildDefaultMaterialBlocks(approvedReady) {
  return [...(approvedReady ?? [])]
    .sort((a, b) => a.rank - b.rank)
    .map((item) => ({ kind: 'material', material_id: item.material_id }))
}

/**
 * Compose preview body: optional intro, then each block (title line or text).
 * Matches backend segment style (`- {title}` + trailing newline when non-empty).
 *
 * @param {{ intro?: string, blocks?: PreviewBlock[], titleById?: Map<number, string> }} opts
 * @returns {string}
 */
export function composePreviewBody({ intro = '', blocks = [], titleById = new Map() } = {}) {
  const parts = []
  const trimmedIntro = String(intro ?? '').trim()
  if (trimmedIntro) {
    parts.push(trimmedIntro)
  }
  for (const block of blocks ?? []) {
    if (!block || typeof block !== 'object') continue
    if (block.kind === 'text') {
      const text = String(block.text ?? '').trim()
      if (text) parts.push(text)
      continue
    }
    if (block.kind === 'material') {
      const title = titleById.get(block.material_id)
      if (title) parts.push(`- ${title}`)
    }
  }
  return parts.length ? `${parts.join('\n')}\n` : ''
}

/**
 * Material items for the preview DTO, positions reflecting composition order.
 * @param {PreviewBlock[]} blocks
 * @param {Map<number, { material_id: number, rank: number, title: string }>} itemById
 * @returns {Array<{ material_id: number, rank: number, title: string }>}
 */
export function composePreviewItems(blocks, itemById) {
  const items = []
  let position = 1
  for (const block of blocks ?? []) {
    if (!block || block.kind !== 'material') continue
    const item = itemById.get(block.material_id)
    if (!item) continue
    items.push({
      material_id: item.material_id,
      rank: position,
      title: item.title,
    })
    position += 1
  }
  return items
}

/**
 * Stable fingerprint of preview composition for D-86 / G-05-1 honesty gate.
 * Includes intro + ordered material ids + interstitial text (not just the approved set).
 *
 * @param {{ intro?: string, blocks?: PreviewBlock[] }} opts
 * @returns {string}
 */
export function compositionFingerprint({ intro = '', blocks = [] } = {}) {
  const normalizedBlocks = (blocks ?? []).map((block) => {
    if (!block || typeof block !== 'object') return null
    if (block.kind === 'text') {
      return { kind: 'text', text: String(block.text ?? '') }
    }
    if (block.kind === 'material') {
      return { kind: 'material', material_id: Number(block.material_id) }
    }
    return null
  }).filter(Boolean)
  return JSON.stringify({
    intro: String(intro ?? ''),
    blocks: normalizedBlocks,
  })
}
