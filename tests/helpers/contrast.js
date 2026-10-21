/**
 * Shared WCAG 2.x contrast arithmetic for the token gate and the admin chrome spec.
 *
 * Two runners need the same formula: `node:test` reads hex literals straight out of
 * `web/src/index.css`, Playwright reads `rgb(...)` strings from `getComputedStyle`.
 * Keeping the arithmetic here means the ratio is computed in exactly one place, and a
 * wrong value cannot be "fixed" independently in one of the two proofs.
 *
 * `relativeLuminance` deliberately throws when the colour carries alpha: a ratio
 * against a translucent surface is undefined, so the "contrast on a transparent field"
 * defect is made impossible by construction instead of by discipline.
 */

/**
 * @param {string} value serialized colour — hex, rgb()/rgba(), or `transparent`
 * @returns {{ r: number, g: number, b: number, a: number }}
 */
function parseColor(value) {
  const text = String(value).trim()

  if (text.toLowerCase() === 'transparent') return { r: 0, g: 0, b: 0, a: 0 }

  const hex = /^#([0-9a-f]{3,8})$/i.exec(text)
  if (hex) {
    const digits = hex[1]
    if (digits.length === 3) {
      const [r, g, b] = digits.split('').map((digit) => parseInt(digit + digit, 16))
      return { r, g, b, a: 1 }
    }
    if (digits.length === 6) {
      return {
        r: parseInt(digits.slice(0, 2), 16),
        g: parseInt(digits.slice(2, 4), 16),
        b: parseInt(digits.slice(4, 6), 16),
        a: 1,
      }
    }
    if (digits.length === 8) {
      return {
        r: parseInt(digits.slice(0, 2), 16),
        g: parseInt(digits.slice(2, 4), 16),
        b: parseInt(digits.slice(4, 6), 16),
        a: parseInt(digits.slice(6, 8), 16) / 255,
      }
    }
    throw new Error(`unsupported colour: ${value}`)
  }

  const channel = '([0-9]*\\.?[0-9]+)'
  const rgb = new RegExp(
    `^rgba?\\(\\s*${channel}[,\\s]+${channel}[,\\s]+${channel}(?:\\s*[,/]\\s*${channel})?\\s*\\)$`,
    'i',
  ).exec(text)
  if (!rgb) throw new Error(`unsupported colour: ${value}`)

  return {
    r: Number(rgb[1]),
    g: Number(rgb[2]),
    b: Number(rgb[3]),
    a: rgb[4] === undefined ? 1 : Number(rgb[4]),
  }
}

/**
 * @param {number} c channel value 0…255
 * @returns {number}
 */
function channelLuminance(c) {
  const s = c / 255
  return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
}

/**
 * @param {string} value serialized colour
 * @returns {number}
 */
function relativeLuminance(value) {
  const { r, g, b, a } = parseColor(value)
  if (a < 1) throw new Error(`transparent surface has no contrast: ${value}`)
  return 0.2126 * channelLuminance(r) + 0.7152 * channelLuminance(g) + 0.0722 * channelLuminance(b)
}

/**
 * @param {string} foreground serialized colour
 * @param {string} background serialized colour
 * @returns {number}
 */
function contrastRatio(foreground, background) {
  const first = relativeLuminance(foreground)
  const second = relativeLuminance(background)
  const [high, low] = first >= second ? [first, second] : [second, first]
  return (high + 0.05) / (low + 0.05)
}

module.exports = { parseColor, channelLuminance, relativeLuminance, contrastRatio }
