/**
 * RED→GREEN: knowledgeApi mock search DTO (KNOW-01 / D-59 / D-61).
 * Run: node --test tests/unit/test_knowledge_api.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

const sampleMaterials = [
  {
    id: 'rag-systems',
    title: 'Building Production RAG Systems',
    snippet: 'Гибридный поиск…',
    tags: ['RAG', 'LLM'],
    roles: ['ds'],
    cover: '/covers/rag-systems.png',
    keywords: 'rag llm корпоративн документ поиск',
  },
  {
    id: 'anomaly-detection',
    title: 'Anomaly Detection in Audit Pipelines',
    snippet: 'Шаблоны витрин…',
    tags: ['SQL', 'BI'],
    roles: ['analyst'],
    cover: null,
    keywords: 'sql bi аудит',
  },
  {
    id: 'pgvector-guide',
    title: 'pgvector Guide',
    snippet: 'PostgreSQL + pgvector…',
    tags: ['pgvector', 'RAG'],
    roles: ['ds'],
    cover: '/covers/pgvector.png',
    keywords: 'pgvector rag',
  },
]

describe('mockSearchKnowledge', () => {
  it('returns API-shaped hits without score and maps null cover_url (D-59 / Q2)', async () => {
    const { mockSearchKnowledge } = await import('../../web/src/services/knowledgeApi.js')
    const dto = mockSearchKnowledge({ q: 'RAG', limit: 10, offset: 0 }, sampleMaterials)

    assert.equal(Object.hasOwn(dto, 'items'), true)
    assert.equal(Object.hasOwn(dto, 'has_more'), true)
    assert.equal(dto.limit, 10)
    assert.equal(dto.offset, 0)
    assert.ok(dto.items.length >= 1)

    for (const hit of dto.items) {
      assert.equal(Object.hasOwn(hit, 'score'), false)
      assert.equal(typeof hit.slug, 'string')
      assert.equal(typeof hit.title, 'string')
      assert.equal(typeof hit.snippet, 'string')
      assert.ok(Array.isArray(hit.tags))
      assert.ok(Array.isArray(hit.roles))
      assert.ok(hit.cover_url === null || typeof hit.cover_url === 'string')
    }

    const anomaly = dto.items.find((h) => h.slug === 'anomaly-detection')
    // anomaly only matches if query hits it; for RAG query it should not appear
    assert.equal(anomaly, undefined)
    const rag = dto.items.find((h) => h.slug === 'rag-systems')
    assert.ok(rag)
    assert.equal(rag.cover_url, '/covers/rag-systems.png')
  })

  it('paginates with has_more when more materials exist (D-61)', async () => {
    const { mockSearchKnowledge } = await import('../../web/src/services/knowledgeApi.js')
    const dto = mockSearchKnowledge({ q: 'a', limit: 1, offset: 0 }, sampleMaterials)
    assert.equal(dto.items.length, 1)
    assert.equal(dto.has_more, true)

    const page1 = mockSearchKnowledge({ q: 'a', limit: 1, offset: 1 }, sampleMaterials)
    assert.equal(page1.items.length, 1)
    assert.notEqual(page1.items[0].slug, dto.items[0].slug)
  })

  it('maps null cover when material.cover is null', async () => {
    const { mockSearchKnowledge } = await import('../../web/src/services/knowledgeApi.js')
    const dto = mockSearchKnowledge({ q: 'SQL', limit: 10, offset: 0 }, sampleMaterials)
    const hit = dto.items.find((h) => h.slug === 'anomaly-detection')
    assert.ok(hit)
    assert.equal(hit.cover_url, null)
  })
})

describe('validateKnowledgeQuery', () => {
  it('rejects blank and whitespace-only with Введите запрос (KNOW-01)', async () => {
    const { validateKnowledgeQuery } = await import('../../web/src/services/knowledgeApi.js')
    for (const q of ['', '   ', '\t\n']) {
      const result = validateKnowledgeQuery(q)
      assert.equal(result.ok, false)
      assert.equal(result.code, 'EMPTY_QUERY')
      assert.equal(result.message, 'Введите запрос')
    }
  })

  it('rejects overlong queries with Сократите запрос (500 code points)', async () => {
    const { validateKnowledgeQuery, MAX_QUERY_CODE_POINTS } = await import(
      '../../web/src/services/knowledgeApi.js'
    )
    assert.equal(MAX_QUERY_CODE_POINTS, 500)
    const overlong = 'я'.repeat(501)
    const result = validateKnowledgeQuery(overlong)
    assert.equal(result.ok, false)
    assert.equal(result.code, 'QUERY_TOO_LONG')
    assert.equal(result.message, 'Сократите запрос')
  })

  it('accepts trimmed query within limit', async () => {
    const { validateKnowledgeQuery } = await import('../../web/src/services/knowledgeApi.js')
    const result = validateKnowledgeQuery('  RAG  ')
    assert.equal(result.ok, true)
    assert.equal(result.q, 'RAG')
  })
})
