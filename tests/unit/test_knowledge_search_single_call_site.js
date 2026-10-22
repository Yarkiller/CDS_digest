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
 * Run: node --test tests/unit/test_knowledge_search_single_call_site.js
 */
const assert = require('node:assert/strict')
const { readdirSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')
const ADAPTER = 'web/src/services/knowledgeApi.js'
const PAGE = 'web/src/pages/KnowledgePage.jsx'

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

describe('KNOW-05 single call site', () => {
  it('calls searchKnowledge from exactly one non-comment site', () => {
    const found = sources()
      .map(({ relative, source }) => ({ relative, hits: count(source, 'searchKnowledge') }))
      .filter((entry) => entry.hits > 0)
    const total = found.reduce((sum, entry) => sum + entry.hits, 0)

    assert.equal(
      total,
      1,
      `KNOW-05: expected exactly one searchKnowledge in web/src, found ${total} — ${found
        .map((entry) => `${entry.relative} (${entry.hits})`)
        .join(', ')}`,
    )
    assert.deepEqual(
      found.map((entry) => entry.relative),
      [PAGE],
      `KNOW-05: the single call site must live in ${PAGE}`,
    )
  })

  it('keeps a single knowledge search limiter', () => {
    const found = sources()
      .map(({ relative, source }) => ({ relative, hits: count(source, 'DEFAULT_SEARCH_LIMIT') }))
      .filter((entry) => entry.hits > 0)

    assert.deepEqual(
      found.map((entry) => entry.relative),
      [ADAPTER],
      `KNOW-05: DEFAULT_SEARCH_LIMIT must be defined only in ${ADAPTER} — found ${found
        .map((entry) => `${entry.relative} (${entry.hits})`)
        .join(', ')}`,
    )
  })
})
