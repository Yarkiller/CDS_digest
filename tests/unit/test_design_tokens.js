/**
 * Design token parity between the Concept 3 prototype and the production SPA.
 *
 * `design-frontend/styles/tokens.css` is the canonical Concept 3 token set
 * (see design-frontend/README.md and design-frontend/design.md). The Tailwind v4
 * `@theme` block in `web/src/index.css` must carry every one of those tokens with
 * an identical value, otherwise production drifts away from the locked design
 * system one hard-coded colour at a time.
 *
 * Run: node --test tests/unit/test_design_tokens.js
 */
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')

function readCss(relativePath) {
  return readFileSync(path.join(ROOT, relativePath), 'utf8')
}

/**
 * Collects `--name: value;` declarations from every `:root` block of a CSS file.
 * Comments are stripped first so documentation cannot be mistaken for a token.
 */
function parseRootTokens(css) {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const tokens = new Map()

  const rootPattern = /:root\s*\{([\s\S]*?)\}/g
  let rootMatch
  while ((rootMatch = rootPattern.exec(withoutComments)) !== null) {
    const declarationPattern = /(--[a-z0-9-]+)\s*:\s*([^;]+);/g
    let declaration
    while ((declaration = declarationPattern.exec(rootMatch[1])) !== null) {
      tokens.set(declaration[1], declaration[2].trim())
    }
  }

  return tokens
}

/** Tailwind v4 declares design tokens inside `@theme { ... }` (optionally `@theme static`) instead of `:root`. */
function parseThemeTokens(css) {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const tokens = new Map()

  const themePattern = /@theme(?:\s+static)?\s*\{([\s\S]*?)\n\}/g
  let themeMatch
  while ((themeMatch = themePattern.exec(withoutComments)) !== null) {
    const declarationPattern = /(--[a-z0-9-]+)\s*:\s*([^;]+);/g
    let declaration
    while ((declaration = declarationPattern.exec(themeMatch[1])) !== null) {
      tokens.set(declaration[1], declaration[2].trim())
    }
  }

  return tokens
}

const prototypeTokens = parseRootTokens(readCss('design-frontend/styles/tokens.css'))
const productionTokens = parseThemeTokens(readCss('web/src/index.css'))

describe('Concept 3 design token parity', () => {
  it('reads the canonical prototype token set', () => {
    assert.equal(
      prototypeTokens.size,
      99,
      'the Concept 3 prototype token count changed; re-check parity and update this contract deliberately',
    )
    assert.equal(prototypeTokens.get('--color-paper'), 'oklch(97% 0.012 95)')
    assert.equal(prototypeTokens.get('--header-height'), '4.25rem')
  })

  it('mirrors every prototype token into the production @theme block', () => {
    const missing = [...prototypeTokens.keys()].filter((name) => !productionTokens.has(name))

    assert.deepEqual(
      missing,
      [],
      `${missing.length} Concept 3 tokens are missing from web/src/index.css @theme: ${missing.join(', ')}`,
    )
  })

  it('keeps every mirrored token value byte-identical to the prototype', () => {
    const drifted = [...prototypeTokens.entries()]
      .filter(([name, value]) => productionTokens.has(name) && productionTokens.get(name) !== value)
      .map(([name, value]) => `${name}: prototype "${value}" vs production "${productionTokens.get(name)}"`)

    assert.deepEqual(drifted, [], `token values drifted from the locked design system:\n${drifted.join('\n')}`)
  })

  it('carries the spacing, radius, motion and z-index scales, not only colours', () => {
    for (const required of [
      '--space-2xs',
      '--space-3xl',
      '--radius-pill',
      '--shadow-modal',
      '--container-reading',
      '--toc-width',
      '--duration-modal',
      '--ease-out',
      '--z-toast',
    ]) {
      assert.ok(
        productionTokens.has(required),
        `${required} is required by design.md but absent from the production @theme block`,
      )
    }
  })
})
