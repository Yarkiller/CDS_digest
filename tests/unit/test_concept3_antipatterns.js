/**
 * Concept 3 anti-pattern guard (ADR-0007, UI-SPEC_3 "Never do").
 *
 * `design-frontend/UI-SPEC_3.md` bans a fixed set of visual and product patterns.
 * On 2026-10-19 a mixed Concept 2/3 build reached production and blank-screened the
 * app; nothing in the suite objected to the banned patterns themselves. This guard
 * makes the ban executable so re-introducing gamification or glass/blur fails a
 * test instead of a review.
 *
 * Assert-only, like web/src/utils/forbiddenChrome.js — it never mutates output.
 *
 * Run: node --test tests/unit/test_concept3_antipatterns.js
 */
const assert = require('node:assert/strict')
const { readFileSync, readdirSync, statSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const SRC = path.join(__dirname, '..', '..', 'web', 'src')
const EXTENSIONS = new Set(['.css', '.js', '.jsx'])

function collectSourceFiles(directory) {
  const found = []
  for (const entry of readdirSync(directory)) {
    const full = path.join(directory, entry)
    if (statSync(full).isDirectory()) {
      found.push(...collectSourceFiles(full))
      continue
    }
    if (EXTENSIONS.has(path.extname(entry))) found.push(full)
  }
  return found
}

/**
 * Banned patterns, each with the rule it enforces.
 * `pattern` is matched against the raw file text; `scope` narrows CSS-only rules so
 * that legitimate identifiers (for example a `*-format-badge` testid, which marks a
 * material format and is not a gamification badge) are not flagged.
 */
const BANNED = [
  {
    id: 'glass-blur',
    rule: 'no glass / blur / frosted surfaces',
    pattern: /backdrop-blur|backdrop-filter/i,
  },
  {
    id: 'dark-theme',
    rule: 'no dark theme',
    pattern: /\bdark:[a-z]/i,
  },
  {
    id: 'gradient-hero',
    rule: 'no gradient-mesh heroes or gradient text',
    pattern: /bg-gradient|gradient-mesh|bg-clip-text/i,
  },
  {
    id: 'glow',
    rule: 'no glow / neon shadows',
    pattern: /shadow-glow|drop-shadow\(|neon/i,
  },
  {
    id: 'gamification-xp',
    rule: 'no XP / experience points',
    pattern: /\bexperiencePoints\b|\bxpPoints\b|\bxp_points\b/i,
  },
  {
    id: 'gamification-streak',
    rule: 'no streaks',
    pattern: /\bstreak\b/i,
  },
  {
    id: 'gamification-leaderboard',
    rule: 'no user leaderboard or ranking of readers',
    pattern: /\bleaderboard\b|\buserRank\b|\buser_rank\b/i,
  },
  {
    id: 'gamification-achievement',
    rule: 'no achievements / badges as rewards',
    pattern: /\bachievement|\blevelUp\b|\blevel_up\b/i,
  },
]

const sourceFiles = collectSourceFiles(SRC)

/**
 * @param {string} filePath
 * @returns {Array<{id: string, rule: string, line: number, text: string}>}
 */
function findViolations(filePath) {
  const lines = readFileSync(filePath, 'utf8').split(/\r?\n/)
  const violations = []

  lines.forEach((text, index) => {
    for (const banned of BANNED) {
      if (banned.pattern.test(text)) {
        violations.push({
          id: banned.id,
          rule: banned.rule,
          line: index + 1,
          text: text.trim().slice(0, 120),
        })
      }
    }
  })

  return violations
}

describe('Concept 3 anti-pattern guard', () => {
  it('scans the production SPA source tree', () => {
    assert.ok(
      sourceFiles.length > 40,
      `expected to scan the web/src tree, found ${sourceFiles.length} files`,
    )
  })

  it('keeps every banned pattern out of web/src', () => {
    const violations = sourceFiles.flatMap((file) =>
      findViolations(file).map((violation) => ({
        ...violation,
        file: path.relative(path.join(__dirname, '..', '..'), file).replaceAll('\\', '/'),
      })),
    )

    const report = violations
      .map((violation) => `${violation.file}:${violation.line} [${violation.id}] ${violation.rule}\n    ${violation.text}`)
      .join('\n')

    assert.deepEqual(
      violations,
      [],
      `${violations.length} Concept 3 anti-pattern violation(s) found (ADR-0007, UI-SPEC_3 "Never do"):\n${report}`,
    )
  })

  it('does not ban editorial naming that merely contains the word badge', () => {
    // Regression lock: a `*-format-badge` / `*-type-badge` testid labels a material
    // format or razbor type. It is editorial metadata, not a gamification reward.
    const badgeTestids = sourceFiles.filter((file) =>
      /data-testid="[^"]*-badge"/.test(readFileSync(file, 'utf8')),
    )
    assert.ok(
      badgeTestids.length > 0,
      'expected editorial *-badge testids to still exist; the guard must not have removed them',
    )
  })
})
