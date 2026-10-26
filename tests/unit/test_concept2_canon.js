/**
 * Concept 2 canon contract (ADR-0009).
 *
 * `design-frontend/` is the source of truth again, but this time it is Concept 2:
 * dark-first tokens with a `[data-theme="light"]` override layer, the shell ported
 * from `layout.css`, and gamification deliberately left out of production while its
 * UI variant stays documented in the prototype for the next version.
 *
 * Each group below has already drifted once, so each gets a guard:
 *   1. token parity, in both themes;
 *   2. the theme contract (attribute + storage key), not just the colours;
 *   3. absence of gamification in production, presence of its variant in the prototype;
 *   4. shell declarations taken from the canon instead of being reinvented.
 *
 * Run: node --test tests/unit/test_concept2_canon.js
 */
const assert = require('node:assert/strict')
const { existsSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')
const exists = (relativePath) => existsSync(path.join(ROOT, relativePath))

/** Tokens of one CSS block, matched by the selector head that opens it. */
function parseBlock(css, headPattern) {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const match = new RegExp(`${headPattern}\\s*\\{([\\s\\S]*?)\\n\\}`, 'm').exec(withoutComments)
  const tokens = new Map()
  if (!match) return tokens
  for (const declaration of match[1].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    tokens.set(declaration[1], declaration[2].trim())
  }
  return tokens
}

const canonDark = parseBlock(read('design-frontend/styles/tokens.css'), ':root')
const canonLight = parseBlock(read('design-frontend/styles/tokens.css'), '\\[data-theme="light"\\]')

const productionCss = read('web/src/index.css')
const productionDark = parseBlock(productionCss, '@theme(?:\\s+static)?')
const productionLight = parseBlock(productionCss, '\\[data-theme="light"\\]')

describe('Concept 2 token canon', () => {
  it('reads the canon theme layers', () => {
    assert.equal(canonDark.size, 51, 'the Concept 2 :root token count changed; update this contract deliberately')
    assert.equal(canonLight.size, 13, 'the Concept 2 light-theme override count changed')
    assert.equal(canonDark.get('--color-bg-surface'), '#131925', 'dark surface drifted from the canon')
    assert.equal(canonLight.get('--color-bg-surface'), '#FFFFFF', 'light surface drifted from the canon')
    assert.equal(canonDark.get('--header-height'), '64px')
  })

  it('mirrors every dark token into the production @theme block', () => {
    const missing = [...canonDark.keys()].filter((name) => !productionDark.has(name))

    assert.deepEqual(missing, [], `${missing.length} Concept 2 tokens are missing from @theme: ${missing.join(', ')}`)
  })

  it('keeps every dark token byte-identical to the canon', () => {
    const drifted = [...canonDark.entries()]
      .filter(([name, value]) => productionDark.has(name) && productionDark.get(name) !== value)
      .map(([name, value]) => `${name}: canon "${value}" vs production "${productionDark.get(name)}"`)

    assert.deepEqual(drifted, [], `token values drifted from the canon:\n${drifted.join('\n')}`)
  })

  it('carries the light theme as a real override layer', () => {
    assert.ok(productionLight.size > 0, 'web/src/index.css must define [data-theme="light"], not only dark tokens')

    const missing = [...canonLight.keys()].filter((name) => !productionLight.has(name))
    assert.deepEqual(missing, [], `light theme is missing overrides: ${missing.join(', ')}`)

    const drifted = [...canonLight.entries()]
      .filter(([name, value]) => productionLight.get(name) !== value)
      .map(([name, value]) => `${name}: canon "${value}" vs production "${productionLight.get(name)}"`)
    assert.deepEqual(drifted, [], `light theme drifted from the canon:\n${drifted.join('\n')}`)
  })
})

describe('Concept 2 theme contract', () => {
  const togglePath = 'web/src/components/ThemeToggle.jsx'

  it('ships a theme toggle bound to the canon attribute and storage key', () => {
    assert.ok(exists(togglePath), 'ThemeToggle.jsx is required: the light theme must be reachable, not decorative')

    const source = read(togglePath)
    assert.match(source, /digest-cds-theme/, 'the toggle must persist the choice under `digest-cds-theme`')
    assert.match(source, /data-theme/, 'the toggle must drive the [data-theme] attribute on <html>')
  })

  it('defaults to the dark layer, which is :root in the canon', () => {
    const toggle = read(togglePath)
    assert.ok(
      /removeAttribute\(\s*['"]data-theme['"]\s*\)/.test(toggle),
      'dark is the absence of [data-theme], so the toggle must remove the attribute for dark',
    )
  })
})

describe('Concept 2 gamification boundary (ADR-0007 + ADR-0009)', () => {
  const FORBIDDEN_SOURCES = [
    'web/src/components/XpBar.jsx',
    'web/src/components/StreakPill.jsx',
    'web/src/components/RankChip.jsx',
    'web/src/data/gamification.js',
    'web/src/pages/LeaderboardPage.jsx',
  ]

  it('does not ship gamification modules in production', () => {
    const present = FORBIDDEN_SOURCES.filter((file) => exists(file))
    assert.deepEqual(present, [], `gamification is deferred to the next version, but found: ${present.join(', ')}`)
  })

  it('does not expose a leaderboard route', () => {
    assert.doesNotMatch(read('web/src/App.jsx'), /leaderboard/i, 'App.jsx must not route to a leaderboard')
  })

  it('does not render gamification widgets in the shell', () => {
    const shell = read('web/src/components/AppShell.jsx')
    const offenders = [/XpBar/, /StreakPill/, /RankChip/, /Ур\./, /xp-widget/i]
      .filter((pattern) => pattern.test(shell))
      .map(String)
    assert.deepEqual(offenders, [], 'AppShell must not carry XP/streak/rank widgets')
  })

  it('documents the deferred UI variant in the prototype', () => {
    const variantPages = [
      'design-frontend/pages/leaderboard.html',
      'design-frontend/pages/quiz.html',
      'design-frontend/pages/profile.html',
      'design-frontend/pages/home-gamified.html',
    ]
    const missing = variantPages.filter((page) => !exists(page))
    assert.deepEqual(missing, [], `the next-version UI variant must stay documented: ${missing.join(', ')}`)
  })

  it('keeps the deferred variant out of the prototype gallery navigation', () => {
    const gallery = read('design-frontend/index.html')
    const linked = ['leaderboard.html', 'quiz.html', 'profile.html', 'home-gamified.html'].filter((page) =>
      gallery.includes(`href="pages/${page}"`),
    )
    assert.deepEqual(linked, [], `deferred pages must not be linked from the gallery: ${linked.join(', ')}`)
  })
})

describe('Concept 2 shell is expressed through tokens', () => {
  const shell = read('web/src/components/AppShell.jsx')

  it('has no literal colours', () => {
    const literals = shell.match(/#[0-9a-fA-F]{3,8}\b/g) ?? []
    assert.deepEqual(literals, [], `shell must paint from tokens, not literals: ${literals.join(', ')}`)
  })

  it('paints the shell from canon token names', () => {
    for (const utility of ['bg-bg-app', 'text-text-primary', 'border-border']) {
      assert.ok(
        shell.includes(utility),
        `shell must paint from the canon token (${utility}) instead of an ad-hoc colour`,
      )
    }
  })

  it('keeps the header geometry token the shell depends on', () => {
    assert.ok(productionDark.has('--header-height'), 'shell geometry depends on --header-height')
  })
})

