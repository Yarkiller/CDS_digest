/**
 * Semantic token coverage gate (criterion 3, THEME-02 + PIPEUI-02).
 *
 * The root cause of the unreadable «Тип» select is a missing CSS declaration, not a
 * missing class: the admin components already say `bg-paper` / `text-ink-2` /
 * `border-rule`, but until those names exist in `@theme` Tailwind v4 silently emits no
 * utility at all. This gate pins the declaration, the theme layer and the arithmetic
 * over the declared values.
 *
 * The other half of the proof — "the utility actually reached the DOM" — lives in
 * `tests/admin-chrome.spec.js`, because only a browser can compute a style. Neither
 * half replaces the other; the original defect was exactly the gap between them.
 *
 * Run: npm run test:js
 */
const assert = require('node:assert/strict')
const { readFileSync, readdirSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { contrastRatio } = require('../helpers/contrast')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')

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

const css = read('web/src/index.css')
const dark = parseBlock(css, '@theme(?:\\s+static)?')
const light = parseBlock(css, '\\[data-theme="light"\\]')

/** Values that depend on the theme: declared in @theme and overridden under light. */
const THEMED = ['paper', 'paper-2', 'ink', 'ink-2', 'muted', 'rule']

/** Roles that are identical in both themes: declared once, no light override (D-08). */
const FLAT = [
  'primary-solid',
  'accent-solid',
  'success-solid',
  'danger-solid',
  'on-solid',
  'voting-ink',
  'scrim',
]

const UTILITY_PREFIXES = ['bg', 'text', 'border', 'ring', 'outline', 'divide', 'fill', 'stroke']

/**
 * `<prefix>-(paper-2|paper|ink-2|ink|muted|rule)`, optionally with an opacity modifier
 * (tolerated here so the hit is attributed to the family, and separately forbidden for
 * `bg-paper*` by G-6). Longest names first so `text-ink-2` is not read as `text-ink`.
 */
const UTILITY_PATTERN = new RegExp(
  `(?<![\\w-])(?:${UTILITY_PREFIXES.join('|')})-(paper-2|paper|ink-2|ink|muted|rule)(?:/[0-9.]+)?`,
  'g',
)

/** Every .js/.jsx source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => entry.endsWith('.js') || entry.endsWith('.jsx'))
    .map((entry) => {
      const relative = path.join('web/src', entry).split(path.sep).join('/')
      return { relative, source: read(relative) }
    })
}

describe('semantic token coverage (criterion 3)', () => {
  it('G-0: keeps exactly one @theme block and one light override block', () => {
    const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
    const themeBlocks = withoutComments.match(/(^|\n)\s*@theme(\s+static)?\s*\{/g) ?? []
    const lightBlocks = withoutComments.match(/(^|\n)\s*\[data-theme="light"\]\s*\{/g) ?? []

    assert.equal(
      themeBlocks.length,
      1,
      `@theme must open exactly once — parseBlock reads only the first block, so a second one blinds both this gate and test_concept2_canon.js (found ${themeBlocks.length})`,
    )
    assert.equal(
      lightBlocks.length,
      1,
      `[data-theme="light"] must open exactly once — parseBlock reads only the first block, so a second one blinds this gate (found ${lightBlocks.length})`,
    )
  })

  it('G-1: declares every theme-dependent token in @theme', () => {
    const missing = THEMED.map((name) => `--color-${name}`).filter((token) => !dark.has(token))
    assert.deepEqual(
      missing,
      [],
      `undeclared theme-dependent tokens (Tailwind emits no utility for them): ${missing.join(', ')}`,
    )
  })

  it('G-2: overrides every theme-dependent token under [data-theme="light"]', () => {
    const offenders = THEMED.flatMap((name) => {
      const token = `--color-${name}`
      const darkValue = dark.get(token)
      const lightValue = light.get(token)
      if (lightValue === undefined) return [`${token} has no light override`]
      if (lightValue === darkValue) return [`${token} light value equals the dark value (${darkValue})`]
      return []
    })
    assert.deepEqual(offenders, [], `theme-dependent tokens need a real light override: ${offenders.join('; ')}`)
  })

  it('G-3: declares every theme-independent role once and never overrides it', () => {
    const offenders = FLAT.flatMap((name) => {
      const token = `--color-${name}`
      if (!dark.has(token)) return [`${token} is not declared in @theme`]
      if (light.has(token)) return [`${token} must not have a light override (identical value in both themes)`]
      return []
    })
    assert.deepEqual(
      offenders,
      [],
      `theme-independent roles are pinned as declared-and-not-overridden: ${offenders.join('; ')}`,
    )
  })

  it('G-4: every semantic utility used under web/src resolves to a declared token', () => {
    const found = new Set()
    const offenders = []

    for (const { relative, source } of sources()) {
      for (const match of source.matchAll(UTILITY_PATTERN)) {
        const name = match[1]
        found.add(name)
        if (!dark.has(`--color-${name}`)) {
          offenders.push(`${relative}: ${match[0]} -> --color-${name} is not declared`)
        }
      }
    }

    assert.deepEqual(
      offenders,
      [],
      `utilities are used but not backed by @theme, so Tailwind emits nothing: ${offenders.join('; ')}`,
    )

    const missing = THEMED.filter((name) => !found.has(name))
    assert.deepEqual(
      missing,
      [],
      `the scan found no use of ${missing.join(', ')} — the family cannot silently empty out`,
    )
  })

  it('G-5: no accent-ink token or utility survives', () => {
    const offenders = sources()
      .filter(({ source }) => source.includes('accent-ink'))
      .map(({ relative }) => relative)
    if (css.includes('accent-ink')) offenders.push('web/src/index.css')
    assert.deepEqual(
      offenders,
      [],
      `accent-ink has no consumers after the -solid migration (D-10), so declaring it would recreate the dead-token defect: ${offenders.join(', ')}`,
    )
  })

  it('G-6: forbids bg-ink and any opacity modifier on bg-paper / bg-paper-2', () => {
    const offenders = []
    for (const { relative, source } of sources()) {
      if (source.includes('bg-ink')) offenders.push(`${relative}: bg-ink`)
      for (const match of source.matchAll(/(?<![\w-])bg-(paper-2|paper)\/[0-9.]+/g)) {
        offenders.push(`${relative}: ${match[0]} (surfaces are opaque)`)
      }
    }
    assert.deepEqual(
      offenders,
      [],
      `a scrim must not ride a theme-dependent token and a nested surface must be opaque: ${offenders.join('; ')}`,
    )
  })

  it('G-7: the declared values clear 4.5:1 in both themes', () => {
    const failures = []

    for (const [themeLabel, block] of [
      ['dark', dark],
      ['light', light],
    ]) {
      for (const surface of ['paper', 'paper-2']) {
        for (const text of ['ink', 'ink-2', 'muted']) {
          const foreground = block.get(`--color-${text}`)
          const background = block.get(`--color-${surface}`)
          const ratio = contrastRatio(foreground, background)
          if (ratio < 4.5) {
            failures.push(`${text} on ${surface} (${themeLabel}): ${ratio.toFixed(3)} (${foreground} on ${background})`)
          }
        }
      }
    }

    for (const fill of ['primary-solid', 'accent-solid', 'success-solid', 'danger-solid']) {
      const ratio = contrastRatio(dark.get('--color-on-solid'), dark.get(`--color-${fill}`))
      if (ratio < 4.5) {
        failures.push(`on-solid on ${fill}: ${ratio.toFixed(3)} (${dark.get('--color-on-solid')} on ${dark.get(`--color-${fill}`)})`)
      }
    }

    const votingRatio = contrastRatio(dark.get('--color-voting-ink'), dark.get('--color-voting'))
    if (votingRatio < 4.5) {
      failures.push(`voting-ink on voting: ${votingRatio.toFixed(3)}`)
    }

    assert.deepEqual(failures, [], `contrast below the 4.5:1 threshold: ${failures.join('; ')}`)

    // The worst label-on-fill pair in the family. White on #DC2626 measures 4.8294, so a
    // `>= 4.83` floor would fail on its own rounding — 4.829 is the deliberate floor.
    const worst = contrastRatio(dark.get('--color-on-solid'), dark.get('--color-danger-solid'))
    assert.ok(
      worst >= 4.829,
      `on-solid on danger-solid must keep its margin: ${worst.toFixed(5)} < 4.829`,
    )
  })

  it('G-8: the aliases that must not drift stay byte-identical', () => {
    const shared = [
      ['paper', 'bg-surface'],
      ['paper-2', 'bg-elevated'],
      ['ink', 'text-primary'],
    ]
    const drift = []

    for (const [themeLabel, block] of [
      ['dark', dark],
      ['light', light],
    ]) {
      for (const [alias, canon] of shared) {
        const aliasValue = block.get(`--color-${alias}`)
        const canonValue = block.get(`--color-${canon}`)
        if (aliasValue !== canonValue) {
          drift.push(`${themeLabel}: --color-${alias} "${aliasValue}" != --color-${canon} "${canonValue}"`)
        }
      }
    }

    for (const [alias, canon] of [
      ['rule', 'border'],
      ['muted', 'text-secondary'],
    ]) {
      if (dark.get(`--color-${alias}`) !== dark.get(`--color-${canon}`)) {
        drift.push(
          `dark: --color-${alias} "${dark.get(`--color-${alias}`)}" != --color-${canon} "${dark.get(`--color-${canon}`)}"`,
        )
      }
    }

    assert.deepEqual(drift, [], `the alias contract drifted: ${drift.join('; ')}`)

    // The light deviations are deliberate (UI-SPEC § Boundary legibility / § Token
    // contract A: #64748B reaches only 4.34:1 on paper-2). Pinned as a fact so a later
    // cleanup cannot quietly snap them back to the failing canon value.
    assert.notEqual(
      light.get('--color-rule'),
      light.get('--color-border'),
      'light rule deviates from border by design; snapping it back drops the field edge to 1.23:1',
    )
    assert.notEqual(
      light.get('--color-muted'),
      light.get('--color-text-secondary'),
      'light muted deviates from text-secondary by design; #64748B only reaches 4.34:1 on paper-2',
    )
  })
})
