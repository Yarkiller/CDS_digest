/**
 * Shared CSS rule parser for the Concept 3 design-parity tests.
 *
 * Flattens a stylesheet into `selector -> sorted declaration list`. At-rules that
 * merely wrap rules (`@layer`, `@media`, `@supports`) are descended into, so a rule
 * declared inside `@layer base` or a media query is found by its selector. Repeated
 * selectors are merged, which is what the CSS cascade would resolve to.
 */

/** Declarations of a rule body, ignoring nested blocks, whitespace-normalised and sorted. */
function declarationsOf(body) {
  return body
    .replace(/\{[\s\S]*?\}/g, '')
    .split(';')
    .map((declaration) => declaration.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .sort()
}

/**
 * @param {string} css raw stylesheet text
 * @returns {Map<string, string[]>}
 */
function parseRules(css) {
  const source = css.replace(/\/\*[\s\S]*?\*\//g, '')

  function walk(content) {
    const rules = new Map()
    let buffer = ''
    let index = 0

    while (index < content.length) {
      const char = content[index]

      if (char === '{') {
        // Collapse whitespace so a multi-line selector list matches its single-line form.
        const head = buffer.replace(/\s+/g, ' ').trim()
        buffer = ''

        let depth = 1
        let cursor = index + 1
        while (cursor < content.length && depth > 0) {
          if (content[cursor] === '{') depth += 1
          else if (content[cursor] === '}') depth -= 1
          cursor += 1
        }
        const body = content.slice(index + 1, cursor - 1)

        if (/^@(layer|media|supports)/.test(head)) {
          for (const [selector, declarations] of walk(body)) {
            const existing = rules.get(selector)
            rules.set(selector, existing ? [...existing, ...declarations] : declarations)
          }
        } else if (head && !head.startsWith('@')) {
          const declarations = declarationsOf(body)
          if (declarations.length > 0) {
            const existing = rules.get(head)
            rules.set(head, existing ? [...existing, ...declarations] : declarations)
          }
        }

        index = cursor
        continue
      }

      if (char === ';') {
        // Statement separator between top-level imports/rules: forget the pending head.
        buffer = ''
        index += 1
        continue
      }

      buffer += char
      index += 1
    }

    return rules
  }

  return walk(source)
}

module.exports = { parseRules, declarationsOf }
