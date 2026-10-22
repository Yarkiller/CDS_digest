/**
 * Frozen knowledge adapter — sha256 pin (C-24 / S0).
 *
 * Phase 27 instruments the search path from the page, not from the service: the
 * request counter (X-1) lives in `KnowledgePage.jsx` and the adapter it counts
 * around must stay provably untouched. `27-CONTEXT.md` § Out of scope forbids any
 * edit to `web/src/services/knowledgeApi.js` — "not even formatting" — because a
 * single byte there would move the boundary X-1 counts at and invalidate every
 * "one request" assertion in the phase.
 *
 * The digest is measured on the `git status`-clean pre-edit file and is therefore
 * checkout-independent: it hashes the CRLF-normalised text, so a Windows/WSL CRLF
 * checkout cannot redden this gate for the wrong reason, while any real edit still
 * fails it.
 *
 * Run: node --test tests/unit/test_knowledge_api_snapshot.js
 */
const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')
const API_PATH = path.join(ROOT, 'web', 'src', 'services', 'knowledgeApi.js')

/** Measured on the clean, unmodified adapter before any Phase 27 edit. */
const FROZEN_SHA256 = 'TODO'

const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('hex')

describe('frozen knowledge adapter (C-24)', () => {
  it('knowledgeApi.js stays byte-identical to the frozen snapshot (C-24)', () => {
    const source = readFileSync(API_PATH, 'utf8')
    const digest = sha256(source.replace(/\r\n/g, '\n'))

    assert.equal(
      digest,
      FROZEN_SHA256,
      `C-24: web/src/services/knowledgeApi.js must stay byte-identical — 27-CONTEXT.md § Out of scope\n` +
        `  expected ${FROZEN_SHA256}\n` +
        `  measured ${digest}\n` +
        `  Phase 27 counts searches from KnowledgePage.jsx; editing the adapter moves the boundary the counter proves.`,
    )
  })
})
