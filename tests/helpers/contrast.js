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
 *
 * `oklch()` is supported because a hard-coded colour in this codebase is usually written
 * that way (`text-[oklch(45%_0.14_25)]`), and a grammar that throws on the offending value
 * lets a failing ratio hide behind "unsupported colour" — the CR-01 failure mode.
 */

/** `oklch(L% C H[deg] [/ A|A%])` — the CSS Color 4 grammar, minus `none` keywords. */
const OKLCH_PATTERN =
  /^oklch\(\s*([0-9]*\.?[0-9]+)(%?)\s+([0-9]*\.?[0-9]+)(%?)\s+(-?[0-9]*\.?[0-9]+)(?:deg)?\s*(?:\/\s*([0-9]*\.?[0-9]+)(%?)\s*)?\)$/i

/**
 * CSS Color 4 oklch → oklab → linear sRGB → sRGB, clamped to the 0..255 cube.
 *
 * @param {number} lightness 0…1
 * @param {number} chroma 0…0.4 for in-gamut colours
 * @param {number} hue degrees
 * @returns {{ r: number, g: number, b: number }}
 */
function oklchToRgb(lightness, chroma, hue) {
  const radians = (hue * Math.PI) / 180
  const a = chroma * Math.cos(radians)
  const b = chroma * Math.sin(radians)

  // oklab → LMS, cubed back out of the perceptual cube.
  const l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
  const m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
  const s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3

  const toSrgb = (linear) => {
    const gamma = linear <= 0.0031308 ? 12.92 * linear : 1.055 * linear ** (1 / 2.4) - 0.055
    if (!Number.isFinite(gamma)) throw new Error(`oklch produced a non-finite channel: ${gamma}`)
    return Math.min(255, Math.max(0, Math.round(gamma * 255)))
  }

  return {
    r: toSrgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    g: toSrgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    b: toSrgb(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  }
}

/**
 * @param {string} text an `oklch(...)` literal
 * @returns {{ r: number, g: number, b: number, a: number }}
 */
function parseOklch(text) {
  const match = OKLCH_PATTERN.exec(text)
  if (!match) throw new Error(`unsupported colour: ${text}`)

  const [, lightness, lightnessUnit, chroma, chromaUnit, hue, alpha, alphaUnit] = match
  // Percent for L, and a bare number for L, are the only two legal spellings. `oklch(45 …)`
  // is neither 45% nor L=45, so guessing would silently mis-measure rather than fail.
  const lightnessValue = Number(lightness) / (lightnessUnit === '%' ? 100 : 1)
  if (!(lightnessValue >= 0 && lightnessValue <= 1)) throw new Error(`unsupported colour: ${text}`)

  // CSS Color 4: 100% chroma is 0.4.
  const chromaValue = Number(chroma) * (chromaUnit === '%' ? 0.004 : 1)
  if (!Number.isFinite(chromaValue) || chromaValue < 0) throw new Error(`unsupported colour: ${text}`)

  const alphaValue = alpha === undefined ? 1 : Number(alpha) / (alphaUnit === '%' ? 100 : 1)
  if (!(alphaValue >= 0 && alphaValue <= 1)) throw new Error(`unsupported colour: ${text}`)

  return { ...oklchToRgb(lightnessValue, chromaValue, Number(hue)), a: alphaValue }
}

/**
 * @param {string} value serialized colour — hex, rgb()/rgba(), oklch(), or `transparent`
 * @returns {{ r: number, g: number, b: number, a: number }}
 */
function parseColor(value) {
  const text = String(value).trim()

  if (text.toLowerCase() === 'transparent') return { r: 0, g: 0, b: 0, a: 0 }

  if (/^oklch\(/i.test(text)) return parseOklch(text)

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
