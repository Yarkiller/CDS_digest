/**
 * Frozen-adapter digest pin (KNOW-05 / C-24).
 *
 * Phase 27 proves "exactly one search per submission" with a counter that lives in
 * `KnowledgePage.jsx`, wrapped around the adapter. That proof is only evidence while
 * the adapter itself is untouchable: `27-CONTEXT.md § Out of scope` forbids changing
 * `knowledgeApi.js` at all — not even formatting — so a hook or a limiter cannot be
 * smuggled into the file the counter is supposed to measure.
 *
 * The digest is taken over LF-normalised text, never over raw bytes: a CRLF checkout
 * (`core.autocrlf` on Windows) would otherwise redden the gate for the wrong reason,
 * while any real edit of the content still fails it.
 *
 * Run: node --test tests/unit/test_knowledge_api_snapshot.js
 */
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { createHash } = require('node:crypto')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')
const API_PATH = path.join(ROOT, 'web', 'src', 'services', 'knowledgeApi.js')
const API_RELATIVE = 'web/src/services/knowledgeApi.js'

/** Measured on the clean, pre-edit adapter in Wave 0 (27-PATTERNS.md § 4). */
const FROZEN_SHA256 = 'bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f'

const normalisedSource = () => readFileSync(API_PATH, 'utf8').replace(/\r\n/g, '\n')

describe('KNOW-05 frozen adapter', () => {
  it('knowledgeApi.js stays byte-identical to the frozen snapshot (C-24)', () => {
    const digest = createHash('sha256').update(normalisedSource(), 'utf8').digest('hex')

    assert.equal(
      digest,
      FROZEN_SHA256,
      `C-24: ${API_RELATIVE} must stay byte-identical — 27-CONTEXT.md § Out of scope (measured sha256 ${digest})`,
    )
  })
})
