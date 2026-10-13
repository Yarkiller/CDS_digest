/**
 * Concept 2 theme contract: the React app must use the new token scheme only.
 * Run: node --test tests/unit/test_web_theme_tokens.js
 */
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const WEB_SRC = path.resolve(__dirname, '../../web/src')
const INDEX_CSS = path.join(WEB_SRC, 'index.css')

// Legacy (Concept 3 "editorial") color utilities that must no longer be used.
const LEGACY_CLASSES = [
  'bg-paper',
  'bg-paper-2',
  'text-ink',
  'text-ink-2',
  'text-muted',
  'bg-rule',
  'border-rule',
  'divide-rule',
  'bg-accent',
  'text-accent',
  'text-accent-ink',
  'border-accent',
  'outline-accent',
  'text-paper',
  'bg-ink',
]

// Concept 2 tokens that must be declared in @theme.
const REQUIRED_TOKENS = [
  '--color-bg-app',
  '--color-bg-surface',
  '--color-bg-elevated',
  '--color-text-primary',
  '--color-text-secondary',
  '--color-text-disabled',
  '--color-border',
  '--color-primary',
  '--color-accent',
  '--color-voting',
  '--color-xp',
  '--color-streak',
  '--color-success',
  '--color-danger',
]

function sourceFiles() {
  const out = []
  for (const entry of fs.readdirSync(WEB_SRC, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile()) continue
    if (!entry.name.endsWith('.jsx') && !entry.name.endsWith('.js')) continue
    out.push(path.join(entry.parentPath, entry.name))
  }
  return out
}

describe('Concept 2 token contract', () => {
  it('declares every required Concept 2 token', () => {
    const css = fs.readFileSync(INDEX_CSS, 'utf-8')
    for (const token of REQUIRED_TOKENS) {
      assert.ok(css.includes(token), `missing token ${token} in index.css`)
    }
  })

  it('uses no legacy Concept 3 color utilities in web/src', () => {
    const offenders = []
    for (const file of sourceFiles()) {
      const text = fs.readFileSync(file, 'utf-8')
      for (const legacy of LEGACY_CLASSES) {
        // word-boundary on both sides (allows `hover:`, `/opacity` suffixes)
        const re = new RegExp(`(?<![\\w-])${legacy}(?![\\w-])`)
        if (re.test(text)) {
          offenders.push(`${path.relative(WEB_SRC, file)} -> ${legacy}`)
        }
      }
    }
    assert.deepEqual(offenders, [], `legacy tokens still present:\n${offenders.join('\n')}`)
  })
})
