/**
 * Unit tests for auth env helpers (login-required flag).
 * Run: node --test tests/unit/test_auth_env.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')

describe('loginRequired', () => {
  it('is true only when VITE_REQUIRE_LOGIN is "true"', async () => {
    const { loginRequired } = await import('../../web/src/services/authEnv.js')
    assert.equal(loginRequired({ VITE_REQUIRE_LOGIN: 'true' }), true)
    assert.equal(loginRequired({ VITE_REQUIRE_LOGIN: 'false' }), false)
    assert.equal(loginRequired({}), false)
    assert.equal(loginRequired(null), false)
    assert.equal(loginRequired(undefined), false)
  })
})
