import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { isAllowedCorporateEmail } from './emailDomain.js'

describe('isAllowedCorporateEmail', () => {
  it('allows @sberbank.ru case-insensitively', () => {
    assert.equal(isAllowedCorporateEmail('user@sberbank.ru'), true)
    assert.equal(isAllowedCorporateEmail('User@Sberbank.RU'), true)
  })

  it('allows @omega.sbrf.ru case-insensitively', () => {
    assert.equal(isAllowedCorporateEmail('analyst@omega.sbrf.ru'), true)
    assert.equal(isAllowedCorporateEmail('Analyst@Omega.Sbrf.RU'), true)
  })

  it('rejects other domains', () => {
    assert.equal(isAllowedCorporateEmail('user@gmail.com'), false)
    assert.equal(isAllowedCorporateEmail('user@sber.ru'), false)
    assert.equal(isAllowedCorporateEmail('user@evil-sberbank.ru'), false)
  })

  it('rejects empty and malformed input', () => {
    assert.equal(isAllowedCorporateEmail(''), false)
    assert.equal(isAllowedCorporateEmail(null), false)
    assert.equal(isAllowedCorporateEmail(undefined), false)
    assert.equal(isAllowedCorporateEmail('nodomain'), false)
    assert.equal(isAllowedCorporateEmail('@sberbank.ru'), false)
  })
})
