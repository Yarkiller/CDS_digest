/**
 * Unit tests for splitting material markdown into framed ## sections.
 * Run: node --test tests/unit/test_markdown_sections.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

describe('splitMaterialSections', () => {
  it('returns an empty list for empty markdown', async () => {
    const { splitMaterialSections } = await import('../../web/src/utils/markdownSections.js')
    assert.deepEqual(splitMaterialSections(''), [])
    assert.deepEqual(splitMaterialSections('   \n'), [])
    assert.deepEqual(splitMaterialSections(null), [])
    assert.deepEqual(splitMaterialSections(undefined), [])
  })

  it('keeps lead prose unframed when there is no heading', async () => {
    const { splitMaterialSections } = await import('../../web/src/utils/markdownSections.js')
    assert.deepEqual(splitMaterialSections('Just a paragraph.\n\nAnother line.'), [
      { heading: null, kind: 'lead', markdown: 'Just a paragraph.\n\nAnother line.' },
    ])
  })

  it('splits on ## and keeps ### inside the parent topic', async () => {
    const { splitMaterialSections } = await import('../../web/src/utils/markdownSections.js')
    const markdown = [
      'Lead sentence.',
      '',
      '## Введение',
      '',
      'Topic prose.',
      '',
      '### Вложенное',
      '',
      'Nested prose.',
      '',
      '## Конкретика',
      '',
      '- **784** — pixels on the side of MNIST.',
      '',
      '## Зачем это СВА',
      '',
      'Для СВА это значит контроль размерности входа.',
    ].join('\n')

    assert.deepEqual(splitMaterialSections(markdown), [
      { heading: null, kind: 'lead', markdown: 'Lead sentence.\n' },
      {
        heading: 'Введение',
        kind: 'topic',
        markdown: '## Введение\n\nTopic prose.\n\n### Вложенное\n\nNested prose.\n',
      },
      {
        heading: 'Конкретика',
        kind: 'concretika',
        markdown: '## Конкретика\n\n- **784** — pixels on the side of MNIST.\n',
      },
      {
        heading: 'Зачем это СВА',
        kind: 'sva',
        markdown: '## Зачем это СВА\n\nДля СВА это значит контроль размерности входа.',
      },
    ])
  })

  it('does not split on ## headings inside fenced code', async () => {
    const { splitMaterialSections, groupMaterialBands } = await import(
      '../../web/src/utils/markdownSections.js'
    )
    const markdown = [
      '## Введение',
      '',
      'Topic prose.',
      '',
      '```markdown',
      '## Конкретика',
      '- fake fact',
      '```',
      '',
      'Closing prose.',
    ].join('\n')

    const sections = splitMaterialSections(markdown)
    assert.equal(sections.length, 1)
    assert.equal(sections[0].kind, 'topic')
    assert.equal(sections[0].heading, 'Введение')
    assert.ok(sections[0].markdown.includes('```markdown\n## Конкретика'))
    assert.equal(sections.some((section) => section.kind === 'concretika'), false)

    const bands = groupMaterialBands(sections)
    assert.equal(bands.length, 1)
    assert.equal(bands[0].kind, 'body')
  })

  it('keeps an article without reserved headings as topic sections only', async () => {
    const { splitMaterialSections, groupMaterialBands } = await import(
      '../../web/src/utils/markdownSections.js'
    )
    const markdown = [
      '## Введение',
      '',
      'Topic prose.',
      '',
      '## Оценка',
      '',
      'Trailing topic.',
    ].join('\n')
    const sections = splitMaterialSections(markdown)
    assert.equal(sections.every((section) => section.kind === 'topic'), true)
    assert.equal(sections.some((section) => section.kind === 'concretika' || section.kind === 'sva'), false)

    const bands = groupMaterialBands(sections)
    assert.deepEqual(bands, [
      {
        kind: 'body',
        heading: null,
        markdown: '## Введение\n\nTopic prose.\n## Оценка\n\nTrailing topic.',
      },
    ])
  })

  it('recognises reserved headings wrapped in emphasis or trailing punctuation', async () => {
    const { splitMaterialSections } = await import('../../web/src/utils/markdownSections.js')
    const sections = splitMaterialSections('## **Конкретика**\n\n- **784** — pixels.')
    assert.equal(sections.length, 1)
    assert.equal(sections[0].kind, 'concretika')
    assert.equal(sections[0].heading, '**Конкретика**')

    const sva = splitMaterialSections('## Зачем это СВА?\n\nДля СВА это значит контроль.')
    assert.equal(sva[0].kind, 'sva')
  })
})

describe('groupMaterialBands', () => {
  it('merges lead and topic prose into one body band and keeps Конкретика / СВА apart', async () => {
    const { splitMaterialSections, groupMaterialBands } = await import(
      '../../web/src/utils/markdownSections.js'
    )
    const markdown = [
      'Lead sentence.',
      '',
      '## Введение',
      '',
      'Topic prose.',
      '',
      '## Конкретика',
      '',
      '- **784** — pixels.',
      '',
      '## Зачем это СВА',
      '',
      'Для СВА это значит контроль.',
      '',
      '## Оценка',
      '',
      'Trailing topic.',
    ].join('\n')

    assert.deepEqual(groupMaterialBands(splitMaterialSections(markdown)), [
      {
        kind: 'body',
        heading: null,
        markdown: 'Lead sentence.\n## Введение\n\nTopic prose.\n',
      },
      {
        kind: 'concretika',
        heading: 'Конкретика',
        markdown: '## Конкретика\n\n- **784** — pixels.\n',
      },
      {
        kind: 'sva',
        heading: 'Зачем это СВА',
        markdown: '## Зачем это СВА\n\nДля СВА это значит контроль.\n',
      },
      {
        kind: 'body',
        heading: null,
        markdown: '## Оценка\n\nTrailing topic.',
      },
    ])
  })

  it('omits empty Конкретика / СВА headings so they never become cards', async () => {
    const { splitMaterialSections, groupMaterialBands } = await import(
      '../../web/src/utils/markdownSections.js'
    )
    const markdown = ['## Конкретика', '', '## Оценка', '', 'Trailing topic.'].join('\n')
    const bands = groupMaterialBands(splitMaterialSections(markdown))
    assert.equal(
      bands.some((band) => band.kind === 'concretika' || band.kind === 'sva'),
      false,
    )
    assert.deepEqual(bands, [
      {
        kind: 'body',
        heading: null,
        markdown: '## Оценка\n\nTrailing topic.',
      },
    ])
  })
})
