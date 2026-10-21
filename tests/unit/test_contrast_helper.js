/**
 * `tests/helpers/contrast.js` — the shared WCAG arithmetic.
 *
 * The token gate and `admin-chrome.spec.js` both measure through this helper, so its
 * grammar is a contract: anything it cannot parse becomes a colour nobody can prove. CR-01
 * (25-REVIEW.md) shipped a 1.98:1 destructive label precisely because the offenders were
 * written as `oklch()` and the helper threw instead of asserting.
 *
 * The expected sRGB triples below are the CSS Color 4 conversion of those literals —
 * `oklch(45% 0.14 25)` is what the browser serialises for the pre-fix delete label
 * (`rgb(147, 43, 42)`), so the numbers are the ground truth, not a re-derivation of the
 * implementation under test.
 *
 * Run: npm run test:js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

const { contrastRatio, parseColor, relativeLuminance } = require('../helpers/contrast')

/** Channel-by-channel comparison with a ±tolerance window (rounding of a 3-dp matrix). */
function assertRgb(actual, expected, tolerance = 2) {
  assert.equal(actual.a, 1, `alpha: expected opaque, got ${actual.a}`)
  for (const channel of ['r', 'g', 'b']) {
    assert.ok(
      Math.abs(actual[channel] - expected[channel]) <= tolerance,
      `${channel}: expected ${expected[channel]} ±${tolerance}, got ${actual[channel]} (${JSON.stringify(actual)})`,
    )
  }
}

describe('contrast helper — oklch support (CR-01)', () => {
  it('parses an oklch() with a percentage lightness into sRGB', () => {
    // The exact value 25-REVIEW.md recorded for the pre-fix «Удалить» label.
    assertRgb(parseColor('oklch(45% 0.14 25)'), { r: 147, g: 43, b: 42 })
  })

  it('parses a light oklch() tint into sRGB', () => {
    // The pre-fix validation-panel fill: rgb(255, 235, 232).
    assertRgb(parseColor('oklch(96% 0.03 25)'), { r: 255, g: 235, b: 232 })
  })

  it('treats lightness as 0..1 when no percent sign is used', () => {
    assert.deepEqual(parseColor('oklch(0.45 0.14 25)'), parseColor('oklch(45% 0.14 25)'))
  })

  it('accepts an optional deg unit on the hue and a numeric or percent alpha', () => {
    const base = parseColor('oklch(45% 0.14 25)')
    assert.deepEqual(parseColor('oklch(45% 0.14 25deg)'), base)
    assert.equal(parseColor('oklch(45% 0.14 25 / 0.5)').a, 0.5)
    assert.equal(parseColor('oklch(45% 0.14 25 / 50%)').a, 0.5)
  })

  it('clamps an out-of-gamut oklch() to the sRGB cube instead of emitting NaN', () => {
    const wide = parseColor('oklch(100% 0.4 140)')
    for (const channel of ['r', 'g', 'b']) {
      assert.ok(Number.isFinite(wide[channel]), `${channel} is not finite: ${wide[channel]}`)
      assert.ok(wide[channel] >= 0 && wide[channel] <= 255, `${channel} left 0..255: ${wide[channel]}`)
    }
  })

  it('measures the recorded pre-fix label at ~1.98:1 on the dark paper-2 surface', () => {
    // G-11 in tests/unit/test_semantic_token_coverage.js asserts the floor; this pins the
    // arithmetic that makes the finding reproducible in Node rather than in a browser.
    const onPaper2 = contrastRatio('oklch(45% 0.14 25)', '#1A2233')
    const onPaper = contrastRatio('oklch(45% 0.14 25)', '#131925')
    assert.ok(onPaper2 > 1.9 && onPaper2 < 2.1, `expected ~1.98 on #1A2233, got ${onPaper2.toFixed(3)}`)
    assert.ok(onPaper > 2.1 && onPaper < 2.3, `expected ~2.20 on #131925, got ${onPaper.toFixed(3)}`)
  })

  it('rejects a lightness outside its own range and an unparseable grammar', () => {
    // 45 without a percent sign is neither 45% nor L=45 — guessing would silently
    // mis-measure, which is exactly how CR-01 passed review tooling in the first place.
    assert.throws(() => parseColor('oklch(45 0.14 25)'), /unsupported colour/)
    assert.throws(() => parseColor('var(--color-paper)'), /unsupported colour/)
    assert.throws(() => parseColor('color-mix(in oklab, red, blue)'), /unsupported colour/)
  })
})

describe('contrast helper — existing grammar stays byte-compatible', () => {
  it('keeps hex, rgb()/rgba(), transparent and the WCAG extremes unchanged', () => {
    assert.deepEqual(parseColor('#131925'), { r: 19, g: 25, b: 37, a: 1 })
    assert.deepEqual(parseColor('#fff'), { r: 255, g: 255, b: 255, a: 1 })
    assert.equal(parseColor('rgb(203, 213, 225)').r, 203)
    assert.equal(parseColor('rgba(19, 25, 37, 0.5)').a, 0.5)
    assert.deepEqual(parseColor('transparent'), { r: 0, g: 0, b: 0, a: 0 })
    assert.equal(contrastRatio('#FFFFFF', '#000000'), 21)
    assert.equal(relativeLuminance('#FFFFFF'), 1)
  })

  it('still refuses to measure a translucent surface', () => {
    assert.throws(() => relativeLuminance('oklch(45% 0.14 25 / 0.4)'), /transparent surface/)
  })
})
