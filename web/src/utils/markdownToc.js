/**
 * Extract ATX headings from markdown for section TOC.
 * Ids match rehype-slug + rehype-sanitize (github-slugger + user-content- clobber).
 */

/** hast-util-sanitize default clobberPrefix — must match rehypeSanitize after rehypeSlug. */
export const HEADING_ID_PREFIX = 'user-content-'

/**
 * @param {string} text
 * @returns {string}
 */
function headingFromLine(line) {
  let marks = 0
  while (marks < line.length && line[marks] === '#') marks += 1
  if (marks < 1 || marks > 6) return null
  if (line[marks] !== ' ' && line[marks] !== '\t') return null
  return { level: marks, text: stripClosingHashes(line.slice(marks + 1)) }
}

function stripClosingHashes(raw) {
  const text = raw.trim()
  let end = text.length
  while (end > 0 && text[end - 1] === '#') end -= 1
  if (end === text.length) return text
  let split = end
  while (split > 0 && (text[split - 1] === ' ' || text[split - 1] === '\t')) split -= 1
  if (split === end) return text
  return text.slice(0, split).trim()
}

function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    // \p{L}/\p{N}: Cyrillic headings must match rehype-slug (github-slugger).
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

/**
 * @param {string} markdown
 * @returns {{ id: string, text: string, level: number }[]}
 */
export function extractMarkdownHeadings(markdown) {
  if (!markdown) return []

  const headings = []
  const seen = new Map()
  let inFence = false

  for (const line of markdown.split(/\r?\n/)) {
    if (/^```/.test(line)) {
      inFence = !inFence
      continue
    }
    if (inFence) continue

    const heading = headingFromLine(line)
    if (!heading) continue

    const { level, text } = heading
    if (!text) continue

    let bare = slugify(text)
    const count = seen.get(bare) ?? 0
    seen.set(bare, count + 1)
    if (count > 0) {
      bare = `${bare}-${count}`
    }

    headings.push({ id: `${HEADING_ID_PREFIX}${bare}`, text, level })
  }

  return headings
}
