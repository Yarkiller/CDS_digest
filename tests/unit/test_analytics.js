/**
 * Unit tests for the Yandex.Metrika analytics module (Step 4).
 * Run: node --test tests/unit/test_analytics.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

describe('analyticsEnabled', () => {
  it('accepts a non-empty numeric counter id', async () => {
    const { analyticsEnabled } = await import('../../web/src/services/analytics.js')
    assert.equal(analyticsEnabled('12345678'), true)
    assert.equal(analyticsEnabled(' 42 '), true)
    assert.equal(analyticsEnabled(''), false)
    assert.equal(analyticsEnabled(undefined), false)
    assert.equal(analyticsEnabled('abc'), false)
  })
})

describe('trackGoal', () => {
  it('calls window.ym with reachGoal when enabled', async () => {
    const { trackGoal } = await import('../../web/src/services/analytics.js')
    const calls = []
    const win = { ym: (...args) => calls.push(args) }
    assert.equal(trackGoal(win, '123', 'vote', { topic: 'RAG' }), true)
    assert.deepEqual(calls, [['123', 'reachGoal', 'vote', { topic: 'RAG' }]])
  })

  it('is a no-op without counter id or ym', async () => {
    const { trackGoal } = await import('../../web/src/services/analytics.js')
    const calls = []
    const win = { ym: (...args) => calls.push(args) }
    assert.equal(trackGoal(win, '', 'vote'), false)
    assert.equal(trackGoal({}, '123', 'vote'), false)
    assert.deepEqual(calls, [])
  })
})

describe('trackHit', () => {
  it('sends a hit for the given url', async () => {
    const { trackHit } = await import('../../web/src/services/analytics.js')
    const calls = []
    const win = { ym: (...args) => calls.push(args) }
    assert.equal(trackHit(win, '123', '/knowledge', 'База знаний'), true)
    assert.equal(calls[0][1], 'hit')
    assert.equal(calls[0][2], '/knowledge')
  })
})

describe('initAnalytics', () => {
  it('injects the Metrika script with the counter id and queues init when enabled', async () => {
    const { initAnalytics } = await import('../../web/src/services/analytics.js')
    const appended = []
    const doc = {
      head: { appendChild: (el) => appended.push(el) },
      createElement: (tag) => ({ tag }),
    }
    const win = {}
    assert.equal(initAnalytics({ counterId: '123', doc, win }), true)
    assert.equal(typeof win.ym, 'function')
    assert.equal(appended.length, 1)
    assert.equal(appended[0].src, 'https://mc.yandex.ru/metrika/tag.js?id=123')
    assert.equal(win.ym.a.length, 1)
    assert.equal(win.ym.a[0][0], '123')
    assert.equal(win.ym.a[0][1], 'init')
    const options = win.ym.a[0][2]
    assert.equal(options.webvisor, true)
    assert.equal(options.clickmap, true)
    assert.equal(options.trackLinks, true)
    assert.equal(options.accurateTrackBounce, true)
  })

  it('does nothing without a valid counter id', async () => {
    const { initAnalytics } = await import('../../web/src/services/analytics.js')
    assert.equal(initAnalytics({ counterId: '', doc: {}, win: {} }), false)
    assert.equal(initAnalytics({ counterId: 'abc', doc: {}, win: {} }), false)
  })

  it('does not re-inject when ym already exists', async () => {
    const { initAnalytics } = await import('../../web/src/services/analytics.js')
    const appended = []
    const doc = { head: { appendChild: (el) => appended.push(el) }, createElement: () => ({}) }
    const win = { ym: () => {} }
    assert.equal(initAnalytics({ counterId: '123', doc, win }), true)
    assert.equal(appended.length, 0)
  })
})

describe('ANALYTICS_GOALS', () => {
  it('exposes the tracked goal names', async () => {
    const { ANALYTICS_GOALS } = await import('../../web/src/services/analytics.js')
    for (const key of [
      'login',
      'login_oauth',
      'vote',
      'search',
      'material_open',
      'digest_send',
    ]) {
      assert.ok(key in ANALYTICS_GOALS, `missing goal ${key}`)
    }
  })
})
