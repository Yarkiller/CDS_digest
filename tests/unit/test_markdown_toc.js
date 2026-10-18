/**
 * Unit tests for markdown heading → TOC extraction (rehype-slug compatible ids).
 * Run: node --test tests/unit/test_markdown_toc.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

describe('extractMarkdownHeadings', () => {
  it('returns empty array when markdown has no headings', async () => {
    const { extractMarkdownHeadings } = await import('../../web/src/utils/markdownToc.js')
    assert.deepEqual(extractMarkdownHeadings('Just a paragraph.\n\nAnother line.'), [])
    assert.deepEqual(extractMarkdownHeadings(''), [])
  })

  it('extracts multi-level headings with rehype-slug compatible ids', async () => {
    const { extractMarkdownHeadings } = await import('../../web/src/utils/markdownToc.js')
    const markdown = [
      '# Building Production RAG Systems',
      '',
      'Intro prose.',
      '',
      '## Hello',
      '',
      'Section body.',
      '',
      '### Nested Detail',
      '',
      '## Retrieval Pipeline',
      '',
      'More prose.',
    ].join('\n')

    assert.deepEqual(extractMarkdownHeadings(markdown), [
      { id: 'user-content-building-production-rag-systems', text: 'Building Production RAG Systems', level: 1 },
      { id: 'user-content-hello', text: 'Hello', level: 2 },
      { id: 'user-content-nested-detail', text: 'Nested Detail', level: 3 },
      { id: 'user-content-retrieval-pipeline', text: 'Retrieval Pipeline', level: 2 },
    ])
  })

  it('skips fenced code blocks that look like headings', async () => {
    const { extractMarkdownHeadings } = await import('../../web/src/utils/markdownToc.js')
    const markdown = ['## Real Heading', '', '```', '## Not A Heading', '```', '', '## Another'].join(
      '\n',
    )
    assert.deepEqual(extractMarkdownHeadings(markdown), [
      { id: 'user-content-real-heading', text: 'Real Heading', level: 2 },
      { id: 'user-content-another', text: 'Another', level: 2 },
    ])
  })

  it('keeps Cyrillic heading ids aligned with rehype-slug + sanitize (RAZB-02)', async () => {
    const { extractMarkdownHeadings } = await import('../../web/src/utils/markdownToc.js')
    const markdown = ['## Введение', '', '## Качество', '', '## Качество'].join('\n')
    assert.deepEqual(extractMarkdownHeadings(markdown), [
      { id: 'user-content-введение', text: 'Введение', level: 2 },
      { id: 'user-content-качество', text: 'Качество', level: 2 },
      { id: 'user-content-качество-1', text: 'Качество', level: 2 },
    ])
  })
})
