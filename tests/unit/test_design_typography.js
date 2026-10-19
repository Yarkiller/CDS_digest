/**
 * Typography parity between the Concept 3 prototype and the production SPA.
 *
 * `design-frontend/styles/typography.css` defines the shared type layer for all
 * three Concept 3 macros (Ecosystem Index, Long Document, Quiet form shell).
 * The production SPA must carry the same rules, otherwise headings fall back to
 * Tailwind defaults and prose loses its 65ch measure.
 *
 * Run: node --test tests/unit/test_design_typography.js
 */
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')

function readCss(relativePath) {
  return readFileSync(path.join(ROOT, relativePath), 'utf8')
}

const { parseRules } = require('./helpers/cssRules')

const prototypeRules = parseRules(readCss('design-frontend/styles/typography.css'))
const productionRules = parseRules(readCss('web/src/index.css'))

describe('Concept 3 typography parity', () => {
  it('reads the prototype type layer', () => {
    assert.ok(
      prototypeRules.size >= 18,
      `expected the prototype typography layer to define its rules, parsed ${prototypeRules.size}`,
    )
    assert.ok(prototypeRules.has('.prose p'), 'prototype .prose p rule is missing from the parse')
  })

  it('carries every prototype typography selector into production', () => {
    const missing = [...prototypeRules.keys()].filter((selector) => !productionRules.has(selector))

    assert.deepEqual(
      missing,
      [],
      `${missing.length} Concept 3 typography selectors are missing from web/src/index.css: ${missing.join(', ')}`,
    )
  })

  it('keeps the prototype declarations for each typography selector', () => {
    const drifted = [...prototypeRules.entries()]
      .filter(([selector, declarations]) => {
        const production = productionRules.get(selector)
        if (!production) return false
        return declarations.some((declaration) => !production.includes(declaration))
      })
      .map(([selector, declarations]) => {
        const production = productionRules.get(selector)
        const lost = declarations.filter((declaration) => !production.includes(declaration))
        return `${selector}: missing ${lost.join('; ')}`
      })

    assert.deepEqual(
      drifted,
      [],
      `typography declarations drifted from the locked design system:\n${drifted.join('\n')}`,
    )
  })

  it('sets the prose measure and the highlight treatment', () => {
    const proseParagraph = productionRules.get('.prose p') ?? []
    assert.ok(
      proseParagraph.includes('max-width: 65ch'),
      '.prose p must keep the 65ch reading measure from design.md',
    )

    const mark = productionRules.get('mark') ?? []
    assert.ok(
      mark.includes('background: var(--color-bg-highlight)'),
      'mark must use the --color-bg-highlight token, not a hard-coded colour',
    )
  })
})
