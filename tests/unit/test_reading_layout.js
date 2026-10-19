/**
 * Concept 3 Long Document reading-macro parity.
 *
 * UI-SPEC_3 gives reading pages "a comfortable reading measure, clear sections,
 * and a persistent reading rail on wide screens". design.md narrows that to
 * "Reading pages may use a sticky TOC only when the viewport supports it".
 * The macro lives in design-frontend/styles/layout.css: `.split-layout--reading`
 * puts the article beside the rail from 80rem up, `.toc*` is the rail itself and
 * `.toc-mobile*` is the disclosure that replaces it below that breakpoint.
 * Production must carry the same declarations.
 *
 * The rail width comes from the canonical `--toc-width` token that production
 * already carries from tokens.css, so the port introduces no new token.
 *
 * Run: node --test tests/unit/test_reading_layout.js
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

const prototype = parseRules(readCss('design-frontend/styles/layout.css'))
const productionCss = readCss('web/src/index.css')
const production = parseRules(productionCss)

/** The reading macro, exactly as layout.css spells each selector. */
const TARGET_SELECTORS = [
  '.split-layout--reading',
  '.toc',
  '.toc__list',
  '.toc__link',
  '.toc__link:hover, .toc__link:focus-visible, .toc__link--active',
  '.toc-mobile',
  '.toc-mobile__summary',
  '.toc-mobile__list',
  '.toc-mobile__list a',
]

describe('Concept 3 reading macro parity', () => {
  it('finds every target rule in the prototype', () => {
    const absent = TARGET_SELECTORS.filter((selector) => !prototype.has(selector))

    assert.deepEqual(
      absent,
      [],
      `prototype selectors not parsed, fix the test fixture: ${absent.join(', ')}`,
    )
  })

  it('carries every reading macro selector into production', () => {
    const missing = TARGET_SELECTORS.filter((selector) => !production.has(selector))

    assert.deepEqual(
      missing,
      [],
      `${missing.length} reading macro rules are missing from web/src/index.css: ${missing.join(', ')}`,
    )
  })

  it('keeps the prototype declarations for each reading macro rule', () => {
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
      `reading macro declarations drifted from the prototype:\n${drifted.join('\n')}`,
    )
  })

  it('sizes the reading rail through the canonical --toc-width token', () => {
    const reading = production.get('.split-layout--reading') ?? []

    // Production mirrors tokens.css into `@theme static`, which parseRules skips,
    // so the token itself is asserted on the raw stylesheet (test_design_tokens.js
    // owns the byte-for-byte value check).
    assert.ok(
      /--toc-width:\s*15rem\s*;/.test(productionCss),
      '--toc-width must stay the canonical rail width from tokens.css',
    )
    assert.ok(
      reading.includes('grid-template-columns: minmax(0, 1fr) var(--toc-width)'),
      '.split-layout--reading must size its rail through --toc-width, not a literal width',
    )
  })

  it('keeps the rail sticky below the header', () => {
    const toc = production.get('.toc') ?? []

    assert.ok(toc.includes('position: sticky'), '.toc must stick while the reader scrolls')
    assert.ok(
      toc.includes('top: calc(var(--header-height) + var(--space-6))'),
      '.toc must clear the sticky header by one --space-6 step',
    )
  })

  it('shows the rail only from 80rem and the disclosure below it', () => {
    const toc = production.get('.toc') ?? []
    const mobile = production.get('.toc-mobile') ?? []

    assert.ok(toc.includes('display: none'), '.toc starts hidden below the rail breakpoint')
    assert.ok(toc.includes('display: block'), '.toc becomes the rail from 80rem up')
    assert.ok(mobile.includes('display: block'), '.toc-mobile is the default below 80rem')
    assert.ok(mobile.includes('display: none'), '.toc-mobile steps aside from 80rem up')

    // Both states must live in a media query, not in the unconditional cascade.
    assert.ok(
      /@media \(min-width: 80rem\) \{[\s\S]*?\.toc \{/.test(productionCss),
      '.toc must be switched on inside a min-width: 80rem media query',
    )
    assert.ok(
      /@media \(min-width: 80rem\) \{[\s\S]*?\.toc-mobile \{[\s\S]*?display: none/.test(productionCss),
      '.toc-mobile must be switched off inside a min-width: 80rem media query',
    )
  })

  it('expresses the reading macro through tokens rather than hard-coded values', () => {
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
      `reading macro rules must reference Concept 3 tokens, not literal colours:\n${offenders.join('\n')}`,
    )
  })
})
