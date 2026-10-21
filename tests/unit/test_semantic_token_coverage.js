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
 * G-11/G-12 close the hole CR-01 walked through: G-9 only compared *named* tokens inside a
 * single string literal, so `text-[oklch(45%_0.14_25)]` (measured 1.98:1 on the dark
 * `paper-2` surface) was structurally invisible. Arbitrary-value colour utilities are now
 * parsed and measured, and then forbidden outright under `web/src`.
 *
 * Run: npm run test:js
 */
const assert = require('node:assert/strict')
const { readFileSync, readdirSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { contrastRatio, blendOver } = require('../helpers/contrast')

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
const THEMED = ['paper', 'paper-2', 'ink', 'ink-2', 'muted', 'rule', 'danger-ink']

/** Roles that are identical in both themes: declared once, no light override (D-08). */
const FLAT = [
  'primary-solid',
  'accent-solid',
  'success-solid',
  'danger-solid',
  'on-solid',
  'voting-ink',
  'scrim',
  'field-border',
]

const UTILITY_PREFIXES = ['bg', 'text', 'border', 'ring', 'outline', 'divide', 'fill', 'stroke']

/**
 * `<prefix>-(voting-ink-on-tint|success-ink|accent-text|field-border|danger-ink|paper-2|paper|
 * ink-2|ink|muted|rule)`, optionally with an opacity modifier (tolerated here so the hit is
 * attributed to the family, and separately forbidden for `bg-paper*` by G-6). Longest names
 * first so `text-success-ink` is not read as `text-success` and `text-ink-2` not as `text-ink`.
 */
const UTILITY_PATTERN = new RegExp(
  `(?<![\\w-])(?:${UTILITY_PREFIXES.join('|')})-(voting-ink-on-tint|success-ink|accent-text|field-border|danger-ink|paper-2|paper|ink-2|ink|muted|rule)(?:/[0-9.]+)?`,
  'g',
)

/**
 * Fills: a label painted on one of these must not read a theme-dependent token.
 *
 * The `-solid` family is listed separately from its base token because `tokenSet()` uses
 * exact token equality — `bg-primary-solid` is *not* a hit for `bg-primary`. Leaving the
 * suffixes out made `bg-primary-solid text-text-primary` (one suffix away from the defect
 * this phase fixed) pass silently (WR-01).
 */
const FILL_TOKENS = [
  'bg-primary',
  'bg-primary-solid',
  'bg-accent',
  'bg-accent-solid',
  'bg-success',
  'bg-success-solid',
  'bg-danger',
  'bg-danger-solid',
  'bg-voting',
]

/** Labels that flip with the theme — illegal on top of a fill (THEME-01). */
const THEME_DEPENDENT_LABELS = ['text-text-primary', 'text-accent-ink', 'text-bg-app']

/**
 * G-14: the surfaces a tint can sit on. `bg-app` is a base too — a status chip may be painted
 * straight onto the page shell, not only onto a card.
 */
const TINT_BASES = ['paper', 'paper-2', 'bg-app']

/**
 * G-14: the status label roles and the translucent tint each one sits on.
 *
 * The tint tokens (`success` / `voting` / `danger`) are fill/status colours and stay theme-flat
 * by design — G-3 pins the absence of a light override. The label on top of them is *not* flat:
 * `bg-success/15` over a light surface composites to a pale green that a green label cannot
 * survive, which is the 1.925:1 defect this gate exists to close.
 */
const STATUS_LABEL_TINTS = [
  { ink: 'success-ink', tint: 'success', alpha: 0.15 },
  { ink: 'voting-ink-on-tint', tint: 'voting', alpha: 0.2 },
  { ink: 'danger-ink', tint: 'danger', alpha: 0.1 },
]

/** G-14: label roles that also stand on a bare surface (a pill with no tint, a link). */
const LABELS_ON_SURFACE = ['accent-text', 'success-ink', 'danger-ink']

/**
 * Arbitrary-value colour utilities: `<prefix>-[<colour>]`, e.g. `text-[oklch(45%_0.14_25)]`.
 * Tailwind writes spaces inside brackets as `_`, so the captured value is un-slugged before
 * it reaches `parseColor()`.
 */
const ARBITRARY_UTILITY = new RegExp(
  `(?<![\\w-])(${UTILITY_PREFIXES.join('|')})-\\[([^\\]]+)\\]`,
  'g',
)

/** True when a bracketed arbitrary value denotes a colour and not a length/position. */
function isArbitraryColour(rawValue) {
  return /^(?:#|oklch\(|oklab\(|rgba?\(|hsla?\(|hwb\(|lab\(|lch\(|color\()/i.test(
    deslug(rawValue),
  )
}

/** `oklch(45%_0.14_25)` -> `oklch(45% 0.14 25)`: the literal form, back to CSS. */
function deslug(rawValue) {
  return rawValue.replace(/_/g, ' ').trim()
}

/** Every arbitrary colour utility of one string literal, as `{ prefix, raw, utility }`. */
function arbitraryColourUtilities(literal) {
  return [...literal.matchAll(ARBITRARY_UTILITY)]
    .filter((match) => isArbitraryColour(match[2]))
    .map((match) => ({ prefix: match[1], raw: match[2], utility: match[0] }))
}

/**
 * Theme-dependent veils: forbidden outright, with or without an alpha modifier.
 *
 * `bg-text-primary` used to be carved out of G-10 as "the known adjacent toast defect". The
 * toast is repaired in 25-06, so the carve-out is gone and the veil form is now as illegal
 * as `bg-ink` — a second allow-list path is exactly what let the 1.00:1 toast survive.
 */
const VEIL_TOKENS = ['bg-ink', 'bg-text-primary']

/**
 * Every string literal of a JS/JSX source, verbatim.
 *
 * A class list can only live in a string — a `className` attribute value or an element of
 * the `stateClass` / `variantClass` / `linkClass` arrays — so scanning literals is both
 * complete and immune to prose in comments and JSX text. The scan deliberately stops at a
 * newline for `'`/`"` literals: a stray apostrophe in prose must not swallow the file.
 */
function stringLiterals(source) {
  const literals = []
  let quote = null
  let start = 0
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index]
    if (quote === null) {
      if (char === "'" || char === '"' || char === '`') {
        quote = char
        start = index + 1
      }
      continue
    }
    if (char === '\\') {
      index += 1
      continue
    }
    if (char === quote) {
      literals.push(source.slice(start, index))
      quote = null
      continue
    }
    if (char === '\n' && quote !== '`') quote = null
  }
  return literals
}

/** One utility, without its variant prefixes: `hover:bg-primary` -> `bg-primary`. */
function baseToken(token) {
  return token.slice(token.lastIndexOf(':') + 1)
}

/** The token set of one class list. Token equality, never a substring match. */
function tokenSet(literal) {
  return new Set(literal.split(/\s+/).filter(Boolean).map(baseToken))
}

/** G-9 core: literals where a theme-dependent label is painted on a fill. */
function fillLabelOffences(relative, source) {
  const offenders = []
  for (const literal of stringLiterals(source)) {
    const tokens = tokenSet(literal)
    // Token equality is the whole point: `bg-primary-solid` must not read as
    // `bg-primary`, or the gate would be green on the very defect it forbids.
    const fills = FILL_TOKENS.filter((fill) => tokens.has(fill))
    if (fills.length === 0) continue
    const labels = THEME_DEPENDENT_LABELS.filter((label) => tokens.has(label))
    if (labels.length === 0) continue
    offenders.push(`${relative}: ${fills.join('+')} with ${labels.join('+')} — "${literal}"`)
  }
  return offenders
}

/**
 * G-11 core. A theme-flat `text-[<colour>]` cannot be followed to the surface it sits on —
 * the fill usually lives on a parent literal (`bg-paper-2` on the row, the label in the
 * button) — so the only honest floor is every paper surface in both themes at once. The
 * pre-fix delete label measures 1.98 on dark `paper-2` and 8.02 on light `paper`, so a
 * single-theme check would have called it readable.
 */
function arbitraryLabelMeasurements(relative, source) {
  const measured = []
  for (const literal of stringLiterals(source)) {
    for (const { prefix, raw, utility } of arbitraryColourUtilities(literal)) {
      if (prefix !== 'text') continue
      const colour = deslug(raw)
      for (const [themeLabel, block] of [
        ['dark', dark],
        ['light', light],
      ]) {
        for (const surface of ['paper', 'paper-2']) {
          const background = block.get(`--color-${surface}`)
          measured.push({
            label: `${relative}: ${utility} on ${themeLabel} ${surface} (${background})`,
            ratio: contrastRatio(colour, background),
          })
        }
      }
    }
  }
  return measured
}

/** Every .js/.jsx source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => entry.endsWith('.js') || entry.endsWith('.jsx'))
    .map((entry) => {
      const relative = path.join('web/src', entry).split(path.sep).join('/')
      return { relative, source: read(relative) }
    })
}

/** `label = ratio` lines, so a failure message prints the measurement instead of a guess. */
function summarise(measured) {
  return measured.map((entry) => `${entry.label} = ${entry.ratio.toFixed(3)}`).join('; ')
}

/**
 * G-18: the status tokens that are fills and are *never* labels.
 *
 * `--color-success` (#22C55E), `--color-voting` (#EAB308) and `--color-danger` (#EF4444)
 * fail 4.5:1 as text on every surface the tree paints them on — light theme 2.279 / 1.918 /
 * 3.763 on `paper`, and 1.925 / 1.62 / 3.17 on their own tint. There is no legal text use.
 * G-4 only proves the token is *declared*, so a regression `text-success-ink` ->
 * `text-success` would pass the whole suite without this usage-level scan (T-25-13).
 */
const FORBIDDEN_STATUS_LABELS = ['text-success', 'text-voting', 'text-danger']

/**
 * Every status token used as a text role in one source, as `file: token`.
 *
 * Exact token equality plus the opacity form (`text-danger/70`), never a substring match:
 * `text-success-ink`, `text-voting-ink-on-tint` and `text-voting-ink` are the legal label
 * roles, and `bg-success` / `bg-voting` / `bg-danger` stay legal fills.
 */
function statusLabelOffences(relative, source) {
  const offenders = []
  for (const literal of stringLiterals(source)) {
    for (const token of tokenSet(literal)) {
      const forbidden = FORBIDDEN_STATUS_LABELS.find(
        (label) => token === label || token.startsWith(`${label}/`),
      )
      if (forbidden) offenders.push(`${relative}: ${token}`)
    }
  }
  return offenders
}

/**
 * G-16: the status literals the tree really sets, and the assertion contract over them.
 *
 * `AdminDigestPage.jsx` renders «Выпуск опубликован» (:443), «Уже отправлено» (:454) and
 * «Рассылка не отправлена» (:463) in the send banner, and toasts «Не сохранено» (:316/:318)
 * or «Не удалось сделать ready» (:366). A single regex alternation covering two of these
 * proves "one of the outcomes renders", never "each outcome renders" (T-25-16), and the
 * toast's defect is its *colour*, so a text-only check cannot see it either.
 *
 * The refusal path «Рассылка не отправлена» has no harness arm, so R2 requires only the two
 * outcomes that can actually be driven — the literal is registered for R1, not invented as
 * a required assertion.
 */
const STATUS_LITERALS = [
  'Выпуск опубликован',
  'Рассылка не отправлена',
  'Уже отправлено',
  'Не сохранено',
  'Не удалось сделать ready',
]

/** Assertion forms that can carry a regex literal (R1). */
const REGEX_ASSERTION =
  /\b(toMatch|toContainText|toHaveText|getByText)\s*\(\s*\/((?:\\\/|[^/\n\\]|\\.)+)\/([a-z]*)/g

/** The subset of STATUS_LITERALS one regex alternation can match. */
function literalsCoveredBy(patternBody) {
  const alternatives = patternBody
    .split('|')
    .map((part) => part.trim())
    .filter(Boolean)
  return STATUS_LITERALS.filter((literal) =>
    alternatives.some((alternative) => {
      try {
        return new RegExp(alternative, 'i').test(literal)
      } catch {
        return false
      }
    }),
  )
}

/** A literal used in a statement, not only in a `test(...)` title. */
function literalIsAsserted(source, literal) {
  return source
    .split(/\r?\n/)
    .filter((line) => !/^\s*(test|it)\s*\(/.test(line))
    .some((line) => line.includes(literal))
}

/** The e2e specs that own the status contract. */
function specSources() {
  return readdirSync(path.join(ROOT, 'tests'))
    .filter((entry) => entry.endsWith('.spec.js'))
    .map((entry) => ({ relative: `tests/${entry}`, source: read(`tests/${entry}`) }))
}

/**
 * G-16 core — shared by the gate and by its proof so the detector cannot go green by
 * measuring a shape no spec can produce.
 *
 * R1: one assertion, one outcome (no alternation covering two registered literals).
 * R2: each driftable send outcome has its own assertion.
 * R3: `admin-toast` is checked at least once, by its computed colours.
 */
function statusContractOffences(specs) {
  const offenders = []

  for (const { relative, source } of specs) {
    for (const match of source.matchAll(REGEX_ASSERTION)) {
      const covered = literalsCoveredBy(match[2])
      if (covered.length >= 2) {
        offenders.push(
          `${relative}: one assertion matches ${covered.length} status literals (${covered.join(' | ')}) — /${match[2]}/`,
        )
      }
    }
  }

  for (const literal of ['Выпуск опубликован', 'Уже отправлено']) {
    if (!specs.some(({ source }) => literalIsAsserted(source, literal))) {
      offenders.push(`tests/*.spec.js: no assertion checks the send outcome «${literal}»`)
    }
  }
  for (const { relative, source } of specs) {
    for (const line of source.split(/\r?\n/)) {
      if (line.includes('Выпуск опубликован') && line.includes('Уже отправлено')) {
        offenders.push(`${relative}: one line asserts two send outcomes — ${line.trim()}`)
      }
    }
  }

  const toastReaders = specs.filter(({ source }) => source.includes('admin-toast'))
  if (toastReaders.length === 0) {
    offenders.push(
      'tests/*.spec.js: no spec checks admin-toast, so the 1.00:1 toast stays unproven',
    )
  }
  for (const { relative, source } of toastReaders) {
    const missing = ['backgroundColor', 'borderTopColor'].filter(
      (property) => !source.includes(property),
    )
    if (missing.length > 0) {
      offenders.push(
        `${relative}: reads admin-toast but never its computed ${missing.join(' / ')} — a text-only check cannot see a 1.00:1 toast`,
      )
    }
  }

  return offenders
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
        for (const text of ['ink', 'ink-2', 'muted', 'danger-ink']) {
          const foreground = block.get(`--color-${text}`)
          const background = block.get(`--color-${surface}`)
          if (foreground === undefined) {
            failures.push(`--color-${text} is not declared in the ${themeLabel} block`)
            continue
          }
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

  it('G-9: no theme-dependent label sits on a filled surface', () => {
    const offenders = sources().flatMap(({ relative, source }) => fillLabelOffences(relative, source))

    assert.deepEqual(
      offenders,
      [],
      `a label painted on a fill must not read the theme (THEME-01): ${offenders.join('; ')}`,
    )
  })

  it('G-9b: the fill list reaches the -solid family and keeps the base tokens', () => {
    // One suffix away from the defect this phase fixed. `bg-primary-solid` is not `bg-primary`
    // under token equality, so without the extension this literal passed silently (WR-01).
    const solid = fillLabelOffences(
      'synthetic.jsx',
      "<span className='bg-primary-solid text-on-solid text-text-primary' />",
    )
    assert.equal(solid.length, 1, `the -solid fill must count as a fill: ${solid.join('; ')}`)
    assert.match(solid[0], /bg-primary-solid with text-text-primary/)

    // The original family must stay caught — the extension may not replace it.
    assert.equal(
      fillLabelOffences('synthetic.jsx', "'bg-primary text-text-primary'").length,
      1,
      'the base fill family regressed',
    )

    // Every fill the migration created is in the list, or the gate is half dead.
    for (const fill of ['bg-accent-solid', 'bg-success-solid', 'bg-danger-solid', 'bg-voting']) {
      assert.ok(FILL_TOKENS.includes(fill), `${fill} is missing from FILL_TOKENS`)
    }
  })

  it('G-11: an arbitrary colour label clears 4.5:1 on every paper surface, both themes', () => {
    const measured = sources().flatMap(({ relative, source }) =>
      arbitraryLabelMeasurements(relative, source),
    )
    const failures = measured
      .filter((entry) => entry.ratio < 4.5)
      .map((entry) => `${entry.label} = ${entry.ratio.toFixed(3)}`)

    for (const entry of measured) console.log(`  ${entry.label} = ${entry.ratio.toFixed(3)}`)

    assert.deepEqual(
      failures,
      [],
      `a theme-flat arbitrary colour must survive every paper surface: ${failures.join('; ')}`,
    )
  })

  it('G-11 proof: the detector reproduces the recorded 1.98:1 offender', () => {
    // The pre-fix «Удалить» label. Pinned so the floor cannot be softened into vacuity once
    // G-12 makes the real tree empty of arbitrary colours.
    const measured = arbitraryLabelMeasurements(
      'synthetic.jsx',
      "className='inline-flex border-[oklch(70%_0.12_25)] text-[oklch(45%_0.14_25)]'",
    )
    for (const entry of measured) console.log(`  ${entry.label} = ${entry.ratio.toFixed(3)}`)

    assert.equal(measured.length, 4, 'the label must be measured against four surfaces')
    const dark = measured.filter((entry) => entry.label.includes('on dark '))
    const light = measured.filter((entry) => entry.label.includes('on light '))
    assert.equal(dark.filter((entry) => entry.ratio < 4.5).length, 2, summarise(measured))
    assert.equal(light.filter((entry) => entry.ratio < 4.5).length, 0, summarise(measured))

    const paper2Dark = measured.find((entry) => entry.label.includes('dark paper-2')).ratio
    assert.ok(
      paper2Dark > 1.9 && paper2Dark < 2.1,
      `expected the recorded 1.98 on dark paper-2, got ${paper2Dark.toFixed(3)}`,
    )
  })

  it('G-12: no arbitrary-value colour utility survives under web/src', () => {
    const offenders = []
    for (const { relative, source } of sources()) {
      for (const literal of stringLiterals(source)) {
        for (const { utility } of arbitraryColourUtilities(literal)) {
          offenders.push(`${relative}: ${utility}`)
        }
      }
    }

    assert.deepEqual(
      offenders,
      [],
      `a hard-coded colour bypasses the token layer; the allow-list is deliberately empty (CR-01): ${offenders.join('; ')}`,
    )
  })

  it('G-12 proof: every colour prefix is detected and non-colour brackets are not', () => {
    const sample =
      "'border-[oklch(70%_0.12_25)] bg-[#ff0000] text-[rgb(1,2,3)] ring-[oklab(0.5_0_0)] min-w-[12rem] text-[14px]'"
    assert.deepEqual(
      arbitraryColourUtilities(sample).map((entry) => entry.utility),
      ['border-[oklch(70%_0.12_25)]', 'bg-[#ff0000]', 'text-[rgb(1,2,3)]', 'ring-[oklab(0.5_0_0)]'],
      'the arbitrary colour scanner must see colours and ignore lengths',
    )
  })


  it('G-13: the destructive label role clears 4.5:1 on both surfaces, both themes', () => {
    // CR-01 closure. The pre-fix label was `text-[oklch(45%_0.14_25)]` = 1.98:1 on dark
    // paper-2; these are the ratios the replacement token actually measures.
    const rows = []
    for (const [themeLabel, block] of [
      ['dark', dark],
      ['light', light],
    ]) {
      for (const surface of ['paper', 'paper-2']) {
        const foreground = block.get('--color-danger-ink')
        const background = block.get(`--color-${surface}`)
        const ratio = contrastRatio(foreground, background)
        rows.push(`${themeLabel} ${surface}: ${ratio.toFixed(3)} (${foreground} on ${background})`)
        assert.ok(ratio >= 4.5, `danger-ink must clear 4.5:1 — ${rows[rows.length - 1]}`)
      }
    }
    console.log(`  danger-ink — ${rows.join(' | ')}`)
  })

  it('G-10: no theme-dependent veil survives under web/src', () => {
    const offenders = []

    for (const { relative, source } of sources()) {
      for (const literal of stringLiterals(source)) {
        for (const token of tokenSet(literal)) {
          if (!VEIL_TOKENS.some((veil) => token === veil || token.startsWith(`${veil}/`))) continue
          offenders.push(`${relative}: ${token}`)
        }
      }
    }

    assert.deepEqual(
      offenders,
      [],
      `a full-screen scrim must not ride a theme-dependent token (T-25-03): ${offenders.join('; ')}`,
    )
  })

  it('G-14: a status label clears 4.5:1 on its tint and on bare surfaces, both themes', () => {
    const failures = []
    const measured = []

    for (const [themeLabel, block] of [
      ['dark', dark],
      ['light', light],
    ]) {
      for (const { ink, tint, alpha } of STATUS_LABEL_TINTS) {
        const inkToken = `--color-${ink}`
        const inkValue = block.get(inkToken)
        if (inkValue === undefined) {
          const message = `${inkToken} is not declared in the ${themeLabel} block`
          if (!failures.includes(message)) failures.push(message)
          continue
        }
        if (themeLabel === 'light' && light.get(inkToken) === dark.get(inkToken)) {
          failures.push(`${inkToken} has no real light override (${dark.get(inkToken)} in both themes)`)
        }

        // The tint resolves by cascade, not from this theme's block alone: `success` / `voting`
        // / `danger` are theme-flat by design, and demanding a light override here would
        // contradict G-3 in the same run.
        const tintValue = light.get(`--color-${tint}`) ?? dark.get(`--color-${tint}`)
        if (tintValue === undefined) {
          failures.push(`--color-${tint} is not declared at all`)
          continue
        }

        for (const base of TINT_BASES) {
          const surface = block.get(`--color-${base}`)
          if (surface === undefined) {
            failures.push(`--color-${base} is not declared in the ${themeLabel} block`)
            continue
          }
          const composite = blendOver(tintValue, surface, alpha)
          measured.push({
            label: `${ink} on ${tint}/${alpha} over ${base} (${themeLabel}) (${inkValue} on ${composite})`,
            ratio: contrastRatio(inkValue, composite),
          })
        }
      }
    }

    // The same roles also stand on the bare surfaces — a status pill without a tint, a link on
    // the page — so the floor is measured there without the composite.
    for (const [themeLabel, block] of [
      ['dark', dark],
      ['light', light],
    ]) {
      for (const ink of LABELS_ON_SURFACE) {
        const inkValue = block.get(`--color-${ink}`)
        if (inkValue === undefined) {
          const message = `--color-${ink} is not declared in the ${themeLabel} block`
          if (!failures.includes(message)) failures.push(message)
          continue
        }
        for (const base of TINT_BASES) {
          const surface = block.get(`--color-${base}`)
          if (surface === undefined) continue
          measured.push({
            label: `${ink} on ${base} (${themeLabel}) (${inkValue} on ${surface})`,
            ratio: contrastRatio(inkValue, surface),
          })
        }
      }
    }

    for (const entry of measured) console.log(`  ${entry.label} = ${entry.ratio.toFixed(3)}`)
    for (const entry of measured) {
      if (entry.ratio < 4.5) failures.push(`${entry.label} = ${entry.ratio.toFixed(3)}`)
    }

    assert.deepEqual(
      failures,
      [],
      `a status label must survive its own tint in both themes: ${failures.join('; ')}`,
    )
  })

  it('G-14 proof: the detector reproduces the recorded 1.925:1 tint offender', () => {
    // The light-theme success pill exactly as it measures today. Pinned numerically so the
    // floor cannot be softened once the real tree is green (the CR-01 pattern).
    assert.equal(
      blendOver('#22C55E', '#F8FAFC', 0.15),
      'rgb(216, 242, 228)',
      'blendOver must return the opaque composite as normalized rgb()',
    )

    const successOnTint = contrastRatio('#22C55E', blendOver('#22C55E', '#F8FAFC', 0.15))
    assert.ok(
      successOnTint > 1.9 && successOnTint < 1.95,
      `expected the recorded 1.925 success-on-tint, got ${successOnTint.toFixed(3)}`,
    )

    const votingOnTint = contrastRatio('#EAB308', blendOver('#EAB308', '#F8FAFC', 0.2))
    assert.ok(
      votingOnTint < 4.5,
      `the recorded voting-on-tint offender must stay below the floor, got ${votingOnTint.toFixed(3)}`,
    )

    const whiteOnVoting = contrastRatio('#FFFFFF', '#EAB308')
    assert.ok(
      whiteOnVoting > 1.9 && whiteOnVoting < 1.95,
      `expected the recorded 1.918 white-on-voting, got ${whiteOnVoting.toFixed(3)}`,
    )
  })

  it('G-14 proof: blendOver always returns an opaque normalized rgb()', () => {
    // alpha 1 must normalize rather than echo the input: `getComputedStyle` hands back
    // `rgba(34, 197, 94, 0.15)`, and a verbatim return would reach `contrastRatio` and throw.
    assert.equal(blendOver('#22C55E', '#F8FAFC', 1), 'rgb(34, 197, 94)')
    assert.equal(blendOver('#22C55E', '#F8FAFC', 0), 'rgb(248, 250, 252)')

    // The tint's own alpha is never transferred — only the argument decides the strength.
    assert.equal(blendOver('rgba(34, 197, 94, 0.15)', '#F8FAFC', 0.15), 'rgb(216, 242, 228)')
    assert.equal(blendOver('rgba(34, 197, 94, 0.15)', '#F8FAFC', 1), 'rgb(34, 197, 94)')

    assert.throws(() => blendOver('#22C55E', 'rgba(0, 0, 0, 0)', 0.15), /opaque base/)
    assert.throws(() => blendOver('#22C55E', '#F8FAFC', 1.5), /0\.\.1/)
    assert.throws(() => blendOver('#22C55E', '#F8FAFC', -0.1), /0\.\.1/)
  })

  it('G-15: the field boundary clears the 3:1 non-text floor in both themes', () => {
    const failures = []
    const measured = []
    const token = '--color-field-border'

    if (!dark.has(token)) {
      failures.push(`${token} is not declared in @theme (WCAG 1.4.11 needs a boundary role of its own)`)
    }
    if (light.has(token)) {
      failures.push(`${token} must not have a light override — #64748B is the theme-independent boundary`)
    }

    const fieldBorder = dark.get(token)
    if (fieldBorder !== undefined) {
      for (const [themeLabel, block] of [
        ['dark', dark],
        ['light', light],
      ]) {
        for (const base of TINT_BASES) {
          const surface = block.get(`--color-${base}`)
          if (surface === undefined) {
            failures.push(`--color-${base} is not declared in the ${themeLabel} block`)
            continue
          }
          measured.push({
            label: `field-border on ${base} (${themeLabel}) (${fieldBorder} on ${surface})`,
            ratio: contrastRatio(fieldBorder, surface),
          })
        }
      }
    }

    for (const entry of measured) console.log(`  ${entry.label} = ${entry.ratio.toFixed(3)}`)
    for (const entry of measured) {
      if (entry.ratio < 3) failures.push(`${entry.label} = ${entry.ratio.toFixed(3)}`)
    }

    assert.deepEqual(
      failures,
      [],
      `a form boundary must clear WCAG 1.4.11's 3:1 (a decorative divider must not be reused as one): ${failures.join('; ')}`,
    )
  })

  it('G-15 proof: the same 3:1 floor rejects the decorative rule', () => {
    // The light field edge today, and its dark twin: both fail the non-text floor, so the gate
    // above is measuring a role and not simply waving every border through.
    const darkRule = contrastRatio('#2A3548', '#131925')
    const lightRule = contrastRatio('#CBD5E1', '#FFFFFF')

    assert.ok(
      darkRule > 1.4 && darkRule < 1.45,
      `expected the recorded 1.425 dark rule, got ${darkRule.toFixed(3)}`,
    )
    assert.ok(
      lightRule > 1.45 && lightRule < 1.5,
      `expected the recorded 1.485 light rule, got ${lightRule.toFixed(3)}`,
    )
    assert.ok(darkRule < 3 && lightRule < 3, 'the decorative rule must not clear the boundary floor')
  })

  it('G-18: a status token is a fill, never a label', () => {
    const offenders = sources().flatMap(({ relative, source }) =>
      statusLabelOffences(relative, source),
    )

    assert.deepEqual(
      offenders,
      [],
      `a status token is legal as a fill only — the label rides its -ink role (GAP-25-1): ${offenders.join('; ')}`,
    )
  })

  it('G-18 proof: the label scan rejects the base token and accepts the -ink roles', () => {
    assert.deepEqual(statusLabelOffences('synthetic.jsx', "'bg-success/15 text-success'"), [
      'synthetic.jsx: text-success',
    ])

    assert.deepEqual(
      statusLabelOffences('synthetic.jsx', "'bg-success/15 text-success-ink'"),
      [],
    )

    assert.deepEqual(statusLabelOffences('synthetic.jsx', "'text-danger/70'"), [
      'synthetic.jsx: text-danger/70',
    ])

    // The legal roles stay legal — the gate may not widen into `-ink` (a substring match would).
    assert.deepEqual(
      statusLabelOffences('synthetic.jsx', "'rounded-md bg-voting/20 text-voting-ink-on-tint'"),
      [],
    )
    assert.deepEqual(
      statusLabelOffences('synthetic.jsx', "'border-danger-ink/60 bg-danger/10 text-danger-ink'"),
      [],
    )
  })

  it('G-16: the status contract holds across the e2e specs', () => {
    const offenders = statusContractOffences(specSources())

    assert.deepEqual(
      offenders,
      [],
      `a status assertion must prove one real outcome, and the toast must be read by colour (T-25-16): ${offenders.join('; ')}`,
    )
  })

  it('G-16 proof: one assertion per outcome, and the toast is read by colour', () => {
    const good = `
      await expect(page.getByText('Выпуск опубликован. Доставка писем: stub (0 из 0)', { exact: true })).toBeVisible()
      await expect(page.getByRole('status').filter({ hasText: 'Уже отправлено' })).toBeVisible()
      const toast = await page.getByTestId('admin-toast').evaluate((el) => {
        const cs = getComputedStyle(el)
        return { background: cs.backgroundColor, border: cs.borderTopColor }
      })
    `
    const textOnly = `
      await expect(page.getByText('Выпуск опубликован. Доставка писем: stub (0 из 0)', { exact: true })).toBeVisible()
      await expect(page.getByRole('status').filter({ hasText: 'Уже отправлено' })).toBeVisible()
      await expect(page.getByTestId('admin-toast')).toHaveText('Не сохранено')
    `
    const bad = `${good}
      await expect(page.getByText(/Выпуск опубликован|Рассылка не отправлена/)).toBeVisible()
    `

    assert.deepEqual(
      statusContractOffences([{ relative: 'synthetic.spec.js', source: good }]),
      [],
      'two separate outcome assertions plus a colour-read toast must be accepted',
    )

    const textOffenders = statusContractOffences([
      { relative: 'synthetic.spec.js', source: textOnly },
    ])
    assert.equal(
      textOffenders.length,
      1,
      `a text-only toast check must be rejected: ${textOffenders.join('; ')}`,
    )
    assert.match(textOffenders[0], /backgroundColor/)

    const badOffenders = statusContractOffences([
      { relative: 'synthetic.spec.js', source: bad },
    ])
    assert.equal(
      badOffenders.length,
      1,
      `one alternation over two literals must be exactly one offender: ${badOffenders.join('; ')}`,
    )
    assert.match(
      badOffenders[0],
      /Выпуск опубликован \| Рассылка не отправлена|Рассылка не отправлена \| Выпуск опубликован/,
    )
  })
})
