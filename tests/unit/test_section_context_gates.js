/**
 * Section-context static gates (NAV-01 / D-01…D-03 / C-19).
 *
 * NAV-01 is one mechanism, declared once: `scroll-padding-top` on `:root` inside
 * `@layer base`, sized from the `--header-height` token. There is no second
 * offset (`scroll-mt-*`, `scroll-margin`), no smooth-behaviour window and no JS
 * measurement of the header — those are exactly the regressions that look
 * correct in a browser and drift silently.
 *
 * These gates read the raw file text on purpose. `helpers/cssRules.parseRules`
 * flattens `@layer`/`@media` wrappers into one selector map, so it cannot prove
 * that the declaration lives in the base layer or that the token stayed in
 * `@theme static`.
 *
 * Run: node --test tests/unit/test_section_context_gates.js
 */
const assert = require('node:assert/strict')
const { readdirSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')

/** Every .js/.jsx/.css source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => /\.(js|jsx|css)$/.test(entry))
    .map((entry) => {
      const relative = path.join('web/src', entry).split(path.sep).join('/')
      return { relative, source: read(relative) }
    })
}

/** Number of non-overlapping occurrences of `needle` in `text`. */
function count(text, needle) {
  let total = 0
  let index = text.indexOf(needle)
  while (index !== -1) {
    total += 1
    index = text.indexOf(needle, index + needle.length)
  }
  return total
}

describe('NAV-01 offset is one mechanism', () => {
  it('declares exactly one scroll offset in web/src', () => {
    const found = sources()
      .map(({ relative, source }) => ({ relative, hits: count(source, 'scroll-padding-top:') }))
      .filter((entry) => entry.hits > 0)
    const total = found.reduce((sum, entry) => sum + entry.hits, 0)

    assert.equal(
      total,
      1,
      `NAV-01: expected exactly one scroll-padding-top in web/src, found ${total} — объявите его в web/src/index.css`,
    )
    assert.deepEqual(
      found.map((entry) => entry.relative),
      ['web/src/index.css'],
      `NAV-01: the single offset must live in web/src/index.css, found in ${found.map((entry) => entry.relative).join(', ')}`,
    )
  })

  it('names the offset from the header token', () => {
    const css = read('web/src/index.css')
    const expression = 'calc(var(--header-height) + 1rem)'

    assert.equal(
      count(css, expression),
      1,
      `NAV-01: the offset must be sized from the header token once, found ${count(css, expression)} of ${expression}`,
    )
    assert.equal(
      count(css, 'scroll-padding-top: 80px'),
      0,
      'NAV-01: the offset must not be a literal 80px — it is calc(var(--header-height) + 1rem)',
    )
  })

  it('keeps the offset in the base layer and the token in the theme block', () => {
    const css = read('web/src/index.css')
    const baseAt = css.indexOf('@layer base {')
    const offsetAt = css.indexOf('scroll-padding-top:')
    const tokenAt = css.indexOf('--header-height: 64px;')

    assert.ok(baseAt !== -1, 'NAV-01: @layer base must exist in web/src/index.css')
    assert.ok(offsetAt > baseAt, 'NAV-01: scroll-padding-top must be declared inside @layer base, not @theme')
    assert.equal(count(css, '@layer base {'), 1, 'NAV-01: exactly one @layer base block')
    assert.equal(
      count(css, '--header-height: 64px;'),
      1,
      'NAV-01: --header-height: 64px must stay a single declaration in the @theme block',
    )
    assert.ok(tokenAt !== -1 && tokenAt < baseAt, 'NAV-01: the 64px token must stay in @theme static, above @layer base')
  })

  it('forbids a second offset mechanism anywhere in web/src', () => {
    for (const token of ['scroll-mt', 'scroll-margin', 'scroll-behavior']) {
      const offenders = sources().filter(({ source }) => count(source, token) > 0)
      assert.deepEqual(
        offenders.map((entry) => entry.relative),
        [],
        `NAV-01: "${token}" is a second offset mechanism; found in ${offenders.map((entry) => entry.relative).join(', ')}`,
      )
    }
  })

  it('scopes the mobile override to one media block', () => {
    const css = read('web/src/index.css')
    const block =
      /@media\s*\(max-width:\s*639\.98px\)\s*\{\s*:root\s*\{\s*--header-height:\s*200px;?\s*\}\s*\}/g
    const matches = css.match(block) ?? []

    assert.equal(
      matches.length,
      1,
      `NAV-01: expected exactly one @media (max-width: 639.98px) :root block, found ${matches.length}`,
    )
    assert.equal(
      count(css, '--header-height: 200px'),
      1,
      'NAV-01: the mobile value must be declared once, inside the media block',
    )
    assert.ok(
      css.indexOf('@media') > css.indexOf('@layer base {'),
      'NAV-01: the media override must live inside @layer base, above nothing that re-declares it',
    )
  })
})
