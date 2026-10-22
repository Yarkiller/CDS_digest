/**
 * Single-call-site static gate (KNOW-05 / S3, UI-SPEC C-05 second half).
 *
 * Phase 27 counts requests with a counter inside `KnowledgePage.jsx`'s `runSearch`.
 * That counter only sees calls that go through `runSearch`, so the phase's "exactly
 * one search per submission" claim is only evidence while no second module can call
 * `searchKnowledge` behind the counter's back. This gate proves the structural half:
 * one importing module, one non-comment call site, and no counter or second limiter
 * inside the frozen adapter.
 *
 * Two traps this scanner has to survive, both measured on the clean tree:
 * - the identifier appears in prose (`KnowledgePage.jsx:131` says "do not call
 *   searchKnowledge") and in a JSDoc line of the adapter — comments are stripped
 *   before counting, but only line-leading `//`, so `https://` in a string survives;
 * - the adapter's own `export async function searchKnowledge(` is a declaration, not
 *   a call site, so declarations are excluded by shape rather than by whitelisting a
 *   file. The exclusion is itself pinned (`function searchKnowledge(` must still be
 *   found once), otherwise the filter could hide every hit and pass vacuously.
 *
 * Run: node --test tests/unit/test_knowledge_search_single_call_site.js
 */
const assert = require('node:assert/strict')
const { readdirSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')
const ADAPTER = 'web/src/services/knowledgeApi.js'
const PAGE = 'web/src/pages/KnowledgePage.jsx'
const COUNTER_KEY = '__DIGEST_KNOWLEDGE_SEARCH_COUNT__'

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')

/** Every .js/.jsx/.mjs source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => /\.(js|jsx|mjs)$/.test(entry))
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

/**
 * Blank out block-comment bodies and whole-line `//` runs, keeping every newline so
 * offsets stay readable. A blanket `//` strip would eat `https://` inside string
 * literals, which is why only line-leading runs are removed.
 */
function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, (block) => block.replace(/[^\n]/g, ' '))
    .replace(/^\s*\/\/.*$/gm, (line) => line.replace(/[^\n]/g, ' '))
}

/**
 * Offsets of the calls of `searchKnowledge(...)`, excluding the declaration
 * (`export async function searchKnowledge(`) that defines it.
 */
function callOffsets(source) {
  const offsets = []
  const pattern = /\bsearchKnowledge\s*\(/g
  let match = pattern.exec(source)
  while (match !== null) {
    const before = source.slice(Math.max(0, match.index - 32), match.index)
    if (!/(?:async\s+)?function\s+$/.test(before)) offsets.push(match.index)
    match = pattern.exec(source)
  }
  return offsets
}

const IMPORTS_SEARCH_KNOWLEDGE =
  /import\s*\{[^}]*\bsearchKnowledge\b[^}]*\}\s*from\s*['"][^'"]*knowledgeApi[^'"]*['"]/

/** A `DEFAULT_SEARCH_LIMIT` *definition*, not an import and not a default param. */
const DEFINES_SEARCH_LIMIT = /^\s*(?:export\s+)?const\s+DEFAULT_SEARCH_LIMIT\s*=/m

const files = sources()

describe('KNOW-05 single call site', () => {
  it('imports searchKnowledge in exactly one module', () => {
    assert.ok(files.length > 20, `walker found only ${files.length} files — the web/src path is wrong`)

    const importers = files
      .filter(({ source }) => IMPORTS_SEARCH_KNOWLEDGE.test(source))
      .map(({ relative }) => relative)

    assert.deepEqual(
      importers,
      [PAGE],
      `KNOW-05: searchKnowledge may be imported by ${PAGE} only, found ${importers.join(', ') || 'none'}`,
    )
  })

  it('calls searchKnowledge from exactly one non-comment site', () => {
    assert.ok(files.length > 20, `walker found only ${files.length} files — the web/src path is wrong`)

    const adapterSource = stripComments(read(ADAPTER))

    // Non-vacuity of the declaration filter: the declaration it skips must still be
    // there. Without this, a scanner that found nothing would pass for the wrong reason.
    assert.equal(
      count(adapterSource, 'function searchKnowledge('),
      1,
      `KNOW-05: ${ADAPTER} must still declare \`function searchKnowledge(\` exactly once — the declaration filter has nothing to skip`,
    )

    const calls = files
      .map(({ relative, source }) => ({ relative, offsets: callOffsets(stripComments(source)) }))
      .filter((entry) => entry.offsets.length > 0)
    const total = calls.reduce((sum, entry) => sum + entry.offsets.length, 0)

    assert.equal(
      total,
      1,
      `KNOW-05: a second call site means the X-1 counter under-reports and criterion 2 is no longer proven — found ${total} call(s) of searchKnowledge( in ${calls
        .map((entry) => `${entry.relative} (${entry.offsets.length})`)
        .join(', ') || 'no file'}`,
    )
    assert.deepEqual(
      calls.map((entry) => entry.relative),
      [PAGE],
      `KNOW-05: the single call site must live in ${PAGE}, found ${calls.map((entry) => entry.relative).join(', ')}`,
    )
  })

  it('keeps the request counter out of the frozen adapter', () => {
    const adapterSource = read(ADAPTER)

    assert.equal(
      count(adapterSource, COUNTER_KEY),
      0,
      `KNOW-05: ${COUNTER_KEY} must live in ${PAGE}, never in the frozen adapter (C-24)`,
    )

    // The limiter is matched by its declaration, not by the bare name: the page
    // imports `DEFAULT_SEARCH_LIMIT`, so a bare-token count reads 2 files on a clean tree.
    const definers = files
      .filter(({ source }) => DEFINES_SEARCH_LIMIT.test(source))
      .map(({ relative }) => relative)

    assert.deepEqual(
      definers,
      [ADAPTER],
      `KNOW-05: the search limit must be defined only in ${ADAPTER}, found ${definers.join(', ') || 'none'} — no page-level limiter may change the request shape`,
    )
  })
})
