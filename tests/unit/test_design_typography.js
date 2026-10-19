/**
 * Typography contract for the Concept 2 canon (ADR-0009).
 *
 * The split is deliberate, so the test encodes it instead of pretending otherwise:
 *
 * - the prototype keeps the class layer (`design-frontend/styles/typography.css`:
 *   `.text-h1`, `.text-overline`, `mark`, …) because static pages have no Tailwind;
 * - production carries the same *faces* through `@theme` tokens (Manrope, JetBrains
 *   Mono) and applies them in `@layer base`, while page-level sizes come from
 *   Tailwind utilities.
 *
 * So parity is asserted on the tokens and the applied face, not on class names that
 * production never had. A silent switch to a system font is what this guard catches.
 *
 * Run: node --test tests/unit/test_design_typography.js
 */
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')
const readCss = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')

const canonRules = parseRules(readCss('design-frontend/styles/typography.css'))
const productionCss = readCss('web/src/index.css')
const productionRules = parseRules(productionCss)

const tokenValue = (name) => {
  const match = new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(productionCss)
  return match ? match[1].trim() : ''
}

describe('Concept 2 typography contract', () => {
  it('keeps the class layer documented in the prototype', () => {
    assert.ok(canonRules.size >= 14, `canon type layer lost rules, parsed ${canonRules.size}`)
    for (const selector of ['body', '.text-h1', '.text-overline', '.text-mono']) {
      assert.ok(canonRules.has(selector), `canon typography is missing ${selector}`)
    }
  })

  it('carries the canon faces as tokens', () => {
    assert.match(tokenValue('--font-sans'), /Manrope/, '--font-sans must be Manrope per the canon')
    assert.match(tokenValue('--font-mono'), /JetBrains Mono/, '--font-mono must be JetBrains Mono per the canon')
  })

  it('applies the sans face in the production base layer', () => {
    const applied = [...productionRules.entries()].some(([, declarations]) =>
      declarations.includes('font-family: var(--font-sans)'),
    )
    assert.ok(applied, 'a base rule must apply font-family: var(--font-sans), otherwise text falls back silently')
  })
})
