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

/**
 * NAV-02 / C-17 — the origin marker is a closed list read at exactly one point.
 *
 * These gates exist because C-17 cannot be pinned behaviourally without forging
 * `history.state` in the router's private shape, which would be a vacuous pin rather than
 * a proof. The UI-SPEC therefore classifies it as a backstop: the structural claim (one
 * read point, three literals, no second comparison, no storage) is proven statically and
 * written down in `26-03-SUMMARY.md`.
 *
 * Gate 2 is the anti-vacuum half: without it every other gate would pass on a deleted
 * `AppShell.jsx`, which is the failure mode that makes a static gate worthless.
 */
const SEVEN_MARKER_FILES = [
  'web/src/components/AppShell.jsx',
  'web/src/components/IssueToc.jsx',
  'web/src/components/MaterialListRow.jsx',
  'web/src/pages/ArchivePage.jsx',
  'web/src/pages/IssuePage.jsx',
  'web/src/pages/KnowledgePage.jsx',
  'web/src/pages/MaterialPage.jsx',
]

const COMPARES_A_SECTION_LITERAL = /===\s*'(archive|base|issue)'/

describe('NAV-02 marker is a closed list read at one point', () => {
  it('reads the marker once in the shell', () => {
    const shell = read('web/src/components/AppShell.jsx')
    assert.equal(
      count(shell, 'state?.section'),
      1,
      `C-17: AppShell must read state?.section exactly once, found ${count(shell, 'state?.section')}`,
    )
  })

  it('compares against all three literals in the shell (anti-vacuum)', () => {
    const shell = read('web/src/components/AppShell.jsx')

    // Anti-vacuum: the "exactly one comparison site" gate below would also pass on an
    // empty or truncated AppShell, so the literals and the attribute they feed are demanded
    // here by name. Dropping any literal from the closed list reddens this gate.
    for (const literal of ["'archive'", "'base'", "'issue'"]) {
      assert.ok(
        count(shell, literal) >= 1,
        `C-17: AppShell must compare the literal ${literal} — the closed list lost a value`,
      )
    }

    // Presence alone could be satisfied by the explanatory comment above the comparisons,
    // so the compared set is asserted explicitly: all three values must reach a `===`.
    const compared = [...new Set([...shell.matchAll(/===\s*'(archive|base|issue)'/g)].map((m) => m[1]))]
    assert.deepEqual(
      compared.sort(),
      ['archive', 'base', 'issue'],
      `C-17: AppShell must compare all three closed-list values, compared ${compared.join(', ') || 'none'}`,
    )

    assert.ok(
      count(shell, 'aria-current') >= 1,
      'C-17: AppShell must feed the marker into aria-current, not into className',
    )
    assert.ok(
      count(shell, 'linkClass') >= 1,
      'C-17: AppShell must reuse linkClass for the fill (a marker must never build a class string)',
    )
  })

  it('has exactly one comparison site for the closed list', () => {
    const sites = sources()
      .filter(({ source }) => COMPARES_A_SECTION_LITERAL.test(source))
      .map(({ relative }) => relative)

    assert.deepEqual(
      sites,
      ['web/src/components/AppShell.jsx'],
      `C-17: the three literals must be compared in AppShell only, found comparison sites in ${sites.join(', ')}`,
    )
  })

  it('forwards the marker from MaterialPage without comparing it', () => {
    const material = read('web/src/pages/MaterialPage.jsx')

    assert.equal(
      count(material, 'originState?.section'),
      1,
      'C-17: MaterialPage must read the origin marker once',
    )
    assert.equal(
      count(material, 'originSection ?'),
      1,
      'C-17: MaterialPage must forward the marker conditionally, not unconditionally',
    )
    assert.ok(
      !COMPARES_A_SECTION_LITERAL.test(material),
      'C-17: MaterialPage must blind-forward the marker — a comparison here would be a second read point',
    )
  })

  it('keeps the origin out of any storage', () => {
    for (const relative of SEVEN_MARKER_FILES) {
      const source = read(relative)
      for (const token of ['localStorage', 'sessionStorage', 'document.cookie']) {
        assert.equal(
          count(source, token),
          0,
          `C-17: ${relative} must not touch ${token} — the origin marker must not survive a fresh visit`,
        )
      }
    }
  })

  it('makes the forwarder props required and keeps the literal at the producer', () => {
    // No default value on either reusable forwarder: a default would light a false section
    // for any future caller (D-08) and would hide which page owns the literal.
    const forwarders = {
      'web/src/components/IssueToc.jsx': /function\s+IssueToc\s*\(\{[^}]*\bsection\b[^}]*\}\s*\)/,
      'web/src/components/MaterialListRow.jsx':
        /function\s+MaterialListRow\s*\(\{[^}]*\bsection\b[^}]*\}\s*\)/,
    }
    for (const [relative, receivesSection] of Object.entries(forwarders)) {
      const source = read(relative)
      assert.ok(
        receivesSection.test(source),
        `C-17: ${relative} must take \`section\` as a destructured prop`,
      )
      assert.ok(
        !/section\s*=\s*['"]/.test(source),
        `C-17: ${relative} must not default its \`section\` prop — the caller owns the literal`,
      )
    }

    // The literals live at the producers, each exactly once.
    for (const [relative, needle] of [
      ['web/src/pages/KnowledgePage.jsx', 'section="base"'],
      ['web/src/pages/ArchivePage.jsx', "section: 'archive'"],
    ]) {
      assert.equal(
        count(read(relative), needle),
        1,
        `C-17: ${relative} must own ${needle} exactly once`,
      )
    }
  })
})
