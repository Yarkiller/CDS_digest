/**
 * Concept 3 editorial component parity.
 *
 * UI-SPEC_3 names four components that carry the editorial genre and are absent
 * from production: IssueCover (the Ecosystem Index entry point), EditorialBox (the
 * callout), PullQuote (the Long Document accent) and ReadingProgress (the scroll
 * affordance). Their styles live in design-frontend/styles/components.css and
 * layout.css; production must carry the same declarations, resolved through the
 * Concept 3 tokens.
 *
 * Run: node --test tests/unit/test_design_components.js
 */
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')

function readCss(relativePath) {
  return readFileSync(path.join(ROOT, relativePath), 'utf8')
}

/** Merges the prototype stylesheets into one selector -> declarations map. */
function prototypeRules() {
  const merged = new Map()
  for (const file of ['design-frontend/styles/components.css', 'design-frontend/styles/layout.css']) {
    for (const [selector, declarations] of parseRules(readCss(file))) {
      const existing = merged.get(selector)
      merged.set(selector, existing ? [...existing, ...declarations] : declarations)
    }
  }
  return merged
}

const prototype = prototypeRules()
const production = parseRules(readCss('web/src/index.css'))

/** The four components UI-SPEC_3 calls out as missing from production. */
const TARGET_SELECTORS = [
  '.editorial-box',
  '.editorial-box__title',
  '.issue-cover',
  '.issue-cover:hover',
  '.issue-cover:hover .issue-cover__title',
  '.issue-cover__title',
  '.issue-cover__thumbs',
  '.issue-cover__thumb',
  '.issue-cover__thumb:first-child',
  '.pull-quote',
  '.reading-progress',
]

describe('Concept 3 editorial component parity', () => {
  it('finds every target component in the prototype', () => {
    const absent = TARGET_SELECTORS.filter((selector) => !prototype.has(selector))

    assert.deepEqual(
      absent,
      [],
      `prototype selectors not parsed, fix the test fixture: ${absent.join(', ')}`,
    )
  })

  it('carries every editorial component selector into production', () => {
    const missing = TARGET_SELECTORS.filter((selector) => !production.has(selector))

    assert.deepEqual(
      missing,
      [],
      `${missing.length} Concept 3 editorial components are missing from web/src/index.css: ${missing.join(', ')}`,
    )
  })

  it('keeps the prototype declarations for each editorial component', () => {
    const drifted = TARGET_SELECTORS.filter((selector) => production.has(selector))
      .map((selector) => {
        const expected = prototype.get(selector)
        const actual = production.get(selector)
        const lost = expected.filter((declaration) => !actual.includes(declaration))
        return lost.length > 0 ? `${selector}: missing ${lost.join('; ')}` : null
      })
      .filter(Boolean)

    assert.deepEqual(
      drifted,
      [],
      `editorial component declarations drifted from the prototype:\n${drifted.join('\n')}`,
    )
  })

  it('expresses components through tokens rather than hard-coded values', () => {
    const offenders = TARGET_SELECTORS.filter((selector) => production.has(selector))
      .flatMap((selector) =>
        production
          .get(selector)
          .filter((declaration) => /#[0-9a-f]{3,8}\b|rgb\(|rgba\(|hsl\(/i.test(declaration))
          .map((declaration) => `${selector}: ${declaration}`),
      )

    assert.deepEqual(
      offenders,
      [],
      `components must reference Concept 3 tokens, not literal colours:\n${offenders.join('\n')}`,
    )
  })

  it('keeps the pull quote on the display face at the pull-quote size', () => {
    const pullQuote = production.get('.pull-quote') ?? []

    assert.ok(pullQuote.includes('font-family: var(--font-serif)'), '.pull-quote must use --font-serif')
    assert.ok(pullQuote.includes('font-size: var(--text-pullquote)'), '.pull-quote must use --text-pullquote')
    assert.ok(pullQuote.includes('font-style: italic'), '.pull-quote is italic per components.css')
  })

  it('keeps the reading progress anchored under the header', () => {
    const progress = production.get('.reading-progress') ?? []

    assert.ok(progress.includes('position: fixed'), '.reading-progress must be fixed')
    assert.ok(progress.includes('top: var(--header-height)'), '.reading-progress must sit under the header')
    assert.ok(progress.includes('transform: scaleX(0)'), '.reading-progress starts collapsed')
  })
})
