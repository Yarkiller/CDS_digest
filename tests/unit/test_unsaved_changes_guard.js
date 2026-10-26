/**
 * RED→GREEN: armBeforeUnload body contract (ADUX-09 / D-05, D-06).
 * Pure module — no Vite/React imports (node --test friendly).
 * Run: node --test tests/unit/test_unsaved_changes_guard.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

describe('armBeforeUnload', () => {
  it('is a function that calls preventDefault on the event', async () => {
    const { armBeforeUnload } = await import('../../web/src/utils/unsavedChangesGuard.js')
    assert.equal(typeof armBeforeUnload, 'function')
    let prevented = false
    const event = {
      returnValue: undefined,
      preventDefault() {
        prevented = true
      },
    }
    armBeforeUnload(event)
    assert.equal(prevented, true)
  })

  it('sets a truthy returnValue (boolean true)', async () => {
    const { armBeforeUnload } = await import('../../web/src/utils/unsavedChangesGuard.js')
    const event = {
      returnValue: undefined,
      preventDefault() {},
    }
    armBeforeUnload(event)
    assert.ok(event.returnValue)
    assert.equal(event.returnValue, true)
  })

  it('source contains neither confirm nor alert', async () => {
    const { armBeforeUnload } = await import('../../web/src/utils/unsavedChangesGuard.js')
    assert.equal(typeof armBeforeUnload, 'function')
    const source = String(armBeforeUnload)
    assert.equal(source.includes('confirm'), false)
    assert.equal(source.includes('alert'), false)
  })
})
