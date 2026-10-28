/**
 * Split material body markdown on ATX `## `. Nested `###` stay inside the parent section.
 * The reader wraps all lead/topic prose in one body frame and keeps `## Конкретика`
 * / `## Зачем это СВА` as their own cards.
 */

/**
 * @param {string | null | undefined} heading
 * @returns {'lead' | 'topic' | 'concretika' | 'sva'}
 */
function kindForHeading(heading) {
  if (!heading) return 'lead'
  if (heading === 'Зачем это СВА') return 'sva'
  if (heading === 'Конкретика') return 'concretika'
  return 'topic'
}

/**
 * @param {string} line
 * @returns {string | null}
 */
function headingText(line) {
  if (!line.startsWith('## ') || line.startsWith('###')) return null
  return line.slice(3).replace(/\s+#+\s*$/, '').trim()
}

/**
 * @param {string | null | undefined} markdown
 * @returns {{ heading: string | null, kind: 'lead' | 'topic' | 'concretika' | 'sva', markdown: string }[]}
 */
export function splitMaterialSections(markdown) {
  if (markdown == null) return []
  const lines = String(markdown).split('\n')
  const sections = []
  let heading = null
  let buf = []

  const flush = () => {
    const text = buf.join('\n')
    buf = []
    if (!heading && !text.trim()) return
    sections.push({
      heading,
      kind: kindForHeading(heading),
      markdown: text,
    })
  }

  for (const line of lines) {
    const next = headingText(line)
    if (next !== null) {
      flush()
      heading = next
      buf = [line]
      continue
    }
    buf.push(line)
  }
  flush()
  return sections
}

/**
 * @param {string} left
 * @param {string} right
 * @returns {string}
 */
function joinMarkdown(left, right) {
  if (!left) return right
  if (!right) return left
  const a = left.endsWith('\n') ? left : `${left}\n`
  return `${a}${right}`
}

/**
 * Merge consecutive lead/topic sections into `body` bands so the reader can
 * paint one shared frame; leave Конкретика and Зачем это СВА as own bands.
 *
 * @param {{ heading: string | null, kind: 'lead' | 'topic' | 'concretika' | 'sva', markdown: string }[]} sections
 * @returns {{ heading: string | null, kind: 'body' | 'concretika' | 'sva', markdown: string }[]}
 */
export function groupMaterialBands(sections) {
  const bands = []
  for (const section of sections) {
    if (section.kind === 'concretika' || section.kind === 'sva') {
      bands.push({
        kind: section.kind,
        heading: section.heading,
        markdown: section.markdown,
      })
      continue
    }
    const last = bands[bands.length - 1]
    if (last && last.kind === 'body') {
      last.markdown = joinMarkdown(last.markdown, section.markdown)
      continue
    }
    bands.push({
      kind: 'body',
      heading: null,
      markdown: section.markdown,
    })
  }
  return bands
}
