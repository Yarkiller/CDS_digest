/**

 * Voting ballot API — GET /voting/current + POST /voting/votes (D-52, D-56).

 * Mock/live cutover via isMocksEnabled(); never silent mock fallback after live failure.

 */

import { delay } from '../utils/delay.js'

import { votingCycle, votingTopics } from '../data/mock.js'

import { getAccessToken } from './authApi.js'

import { isMocksEnabled } from './authEnv.js'



export class VoteSubmitError extends Error {

  constructor(message, { code = 'SUBMIT_FAILED', retryable = true, ballot = null } = {}) {

    super(message)

    this.name = 'VoteSubmitError'

    this.code = code

    this.retryable = retryable

    this.ballot = ballot

  }

}



export class BallotFetchError extends Error {

  constructor(message, { code = 'BALLOT_FAILED', retryable = true } = {}) {

    super(message)

    this.name = 'BallotFetchError'

    this.code = code

    this.retryable = retryable

  }

}



/**

 * Mock vote API. Fail-once can be armed via:

 * - `armFailNextVoteSubmit()` (tests / demos)

 * - URL `?simulateError=1` (handled by VotingPage before first submit)

 *

 * Empty/closed harnesses (sticky window flags for Playwright reloads):

 * - `__DIGEST_VOTING_CLOSED__` — D-48 closed cycle with tallies/leaders

 * - `__DIGEST_VOTING_NO_TOPICS__` — D-49 open cycle, zero topics

 * - `__DIGEST_VOTING_NO_CYCLE__` — D-50 null cycle

 * - `__DIGEST_VOTING_CLOSE_ON_SUBMIT__` — D-51 close mid-submit race

 * - `__DIGEST_VOTING_CONFLICT_ON_SUBMIT__` — D-54 CAS conflict adopt-server

 * - `__DIGEST_FAIL_NEXT_BALLOT__` — D-55 GET splash (sticky until cleared)

 */

let failNextSubmit = false

let failNextBallot = false



/** @type {{ topic_id: string, updated_at: string } | null} */

let mockPersonalVote = null



/** @type {Array<{ id: string, title: string, description: string, materialsCount: number, votes: number }>} */

let mockTopicTallies = null



export function armFailNextVoteSubmit() {

  failNextSubmit = true

}



export function armFailNextBallotFetch() {

  failNextBallot = true

  if (typeof window !== 'undefined') {

    window.__DIGEST_FAIL_NEXT_BALLOT__ = true

  }

}



export function clearFailNextBallotFetch() {

  failNextBallot = false

  if (typeof window !== 'undefined') {

    window.__DIGEST_FAIL_NEXT_BALLOT__ = false

  }

}



export function resetVoteSubmitHarness() {

  failNextSubmit = false

  failNextBallot = false

  mockPersonalVote = null

  mockTopicTallies = null

  if (typeof window !== 'undefined') {

    window.__DIGEST_VOTING_CLOSED__ = false

    window.__DIGEST_VOTING_NO_TOPICS__ = false

    window.__DIGEST_VOTING_NO_CYCLE__ = false

    window.__DIGEST_VOTING_CLOSE_ON_SUBMIT__ = false

    window.__DIGEST_VOTING_CONFLICT_ON_SUBMIT__ = false

    window.__DIGEST_FAIL_NEXT_BALLOT__ = false

  }

}



function mockHarnessClosed() {

  return typeof window !== 'undefined' && window.__DIGEST_VOTING_CLOSED__ === true

}



function mockHarnessNoTopics() {

  return typeof window !== 'undefined' && window.__DIGEST_VOTING_NO_TOPICS__ === true

}



function mockHarnessNoCycle() {

  return typeof window !== 'undefined' && window.__DIGEST_VOTING_NO_CYCLE__ === true

}



function mockCloseOnSubmit() {

  return typeof window !== 'undefined' && window.__DIGEST_VOTING_CLOSE_ON_SUBMIT__ === true

}



function mockConflictOnSubmit() {

  return typeof window !== 'undefined' && window.__DIGEST_VOTING_CONFLICT_ON_SUBMIT__ === true

}



function shouldFailBallotFetch() {

  if (failNextBallot) {

    failNextBallot = false

    return true

  }

  return typeof window !== 'undefined' && window.__DIGEST_FAIL_NEXT_BALLOT__ === true

}



function apiBase() {

  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

}



function cloneTopics() {

  if (!mockTopicTallies) {

    mockTopicTallies = votingTopics.map((topic) => ({

      id: topic.id,

      title: topic.title,

      description: topic.description ?? '',

      materialsCount: topic.materialsCount,

      votes: topic.votes,

    }))

  }

  return mockTopicTallies.map((topic) => ({ ...topic }))

}



/** Leaders from tallies only — no row-level leading badge (D-40, D-43). */

function computeLeaders(topics) {

  if (!topics.length) return []

  const maxVotes = Math.max(...topics.map((t) => t.votes))

  if (maxVotes <= 0) return []

  return topics

    .filter((t) => t.votes === maxVotes)

    .map((t) => ({ title: t.title, votes: t.votes }))

}



function buildMockSnapshot() {

  if (mockHarnessNoCycle()) {

    return {

      cycle: null,

      topics: [],

      personal_vote: null,

      leaders: [],

    }

  }



  if (mockHarnessNoTopics()) {

    return {

      cycle: {

        id: 'mock-cycle',

        status: 'open',

        opens_at: '2026-04-03T00:00:00Z',

        closes_at: '2026-04-16T23:59:59Z',

        progress_ratio: votingCycle.progressRatio,

        label: votingCycle.label,

        period: votingCycle.period,

        closesOn: votingCycle.closesOn,

      },

      topics: [],

      personal_vote: null,

      leaders: [],

    }

  }



  const topics = cloneTopics()

  const closed = mockHarnessClosed()

  return {

    cycle: {

      id: 'mock-cycle',

      status: closed ? 'closed' : 'open',

      opens_at: '2026-04-03T00:00:00Z',

      closes_at: '2026-04-16T23:59:59Z',

      progress_ratio: votingCycle.progressRatio,

      label: votingCycle.label,

      period: votingCycle.period,

      closesOn: votingCycle.closesOn,

    },

    topics,

    personal_vote: mockPersonalVote ? { ...mockPersonalVote } : null,

    leaders: computeLeaders(topics),

  }

}



/**

 * Normalize live BallotSnapshotResponse (snake_case) to SPA topic shape.

 * @param {object} raw

 */

function normalizeSnapshot(raw) {

  if (!raw || typeof raw !== 'object') return raw

  const topics = Array.isArray(raw.topics)

    ? raw.topics.map((t) => ({

        id: t.id,

        title: t.title,

        description: t.description ?? '',

        materialsCount: t.materials_count ?? t.materialsCount ?? 0,

        votes: t.votes ?? 0,

      }))

    : []

  return {

    ...raw,

    topics,

    leaders: Array.isArray(raw.leaders) ? raw.leaders : [],

    personal_vote: raw.personal_vote ?? null,

  }

}



/**

 * @returns {Promise<{

 *   cycle: object | null,

 *   topics: Array<{ id: string, title: string, description: string, materialsCount: number, votes: number }>,

 *   personal_vote: { topic_id: string, updated_at: string } | null,

 *   leaders: Array<{ title: string, votes: number }>,

 * }>}

 */

export async function fetchBallot(accessToken) {

  if (isMocksEnabled()) {

    await delay(80)

    if (shouldFailBallotFetch()) {

      throw new BallotFetchError('Не удалось загрузить голосование. Проверьте сеть.', {

        code: 'NETWORK',

        retryable: true,

      })

    }

    return buildMockSnapshot()

  }



  const token = accessToken ?? (await getAccessToken())

  if (!token) {

    throw new BallotFetchError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })

  }



  let response

  try {

    response = await fetch(`${apiBase()}/voting/current`, {

      headers: { Authorization: `Bearer ${token}` },

    })

  } catch {

    throw new BallotFetchError('Не удалось загрузить голосование. Проверьте сеть.', {

      code: 'NETWORK',

      retryable: true,

    })

  }



  if (response.status === 401) {

    throw new BallotFetchError('Сессия истекла. Войдите снова.', {

      code: 'UNAUTHORIZED',

      retryable: false,

    })

  }

  if (!response.ok) {

    throw new BallotFetchError('Не удалось загрузить голосование. Проверьте сеть.', {

      code: 'NETWORK',

      retryable: true,

    })

  }



  return normalizeSnapshot(await response.json())

}



/**

 * Cast/change vote. Returns full BallotSnapshot (D-52) — no mandatory follow-up GET.

 * @param {string} topicId

 * @param {string | null} [expectedUpdatedAt]

 * @param {string | null} [accessToken]

 */

function rejectIfMockClosed() {
  if (!mockHarnessClosed()) return
  throw new VoteSubmitError('Цикл голосования закрыт', {
    code: 'CYCLE_CLOSED',
    retryable: false,
    ballot: buildMockSnapshot(),
  })
}

function rejectIfMockClosesOnSubmit() {
  if (!mockCloseOnSubmit()) return
  if (typeof window !== 'undefined') {
    window.__DIGEST_VOTING_CLOSED__ = true
    window.__DIGEST_VOTING_CLOSE_ON_SUBMIT__ = false
  }
  throw new VoteSubmitError('Цикл голосования закрыт', {
    code: 'CYCLE_CLOSED',
    retryable: false,
    ballot: buildMockSnapshot(),
  })
}

function rejectIfMockNetwork() {
  if (!failNextSubmit) return
  failNextSubmit = false
  throw new VoteSubmitError(
    'Сервер голосования временно недоступен. Проверьте соединение и повторите попытку.',
    { code: 'NETWORK', retryable: true },
  )
}

function rejectIfMockConflict(topicId) {
  if (!mockConflictOnSubmit() || !mockPersonalVote || mockPersonalVote.topic_id === topicId) return
  throw new VoteSubmitError('Голос уже изменён на другом устройстве', {
    code: 'VOTE_CONFLICT',
    retryable: false,
    ballot: buildMockSnapshot(),
  })
}

function recordMockVote(topicId) {
  const topics = cloneTopics()
  const prev = mockPersonalVote?.topic_id ?? null
  if (prev && prev !== topicId) {
    const oldTopic = topics.find((topic) => topic.id === prev)
    if (oldTopic && oldTopic.votes > 0) oldTopic.votes -= 1
  }
  const nextTopic = topics.find((topic) => topic.id === topicId)
  if (!nextTopic) {
    throw new VoteSubmitError('Выберите тему', { code: 'NO_TOPIC', retryable: false })
  }
  if (prev !== topicId) nextTopic.votes += 1
  mockTopicTallies = topics
  mockPersonalVote = {
    topic_id: topicId,
    updated_at: new Date().toISOString(),
  }
  return buildMockSnapshot()
}

async function submitMockVote(topicId) {
  await delay()
  rejectIfMockClosed()
  rejectIfMockClosesOnSubmit()
  rejectIfMockNetwork()
  rejectIfMockConflict(topicId)
  return recordMockVote(topicId)
}

export async function submitVote(topicId, expectedUpdatedAt = null, accessToken = null) {

  if (!topicId) {

    throw new VoteSubmitError('Выберите тему', {

      code: 'NO_TOPIC',

      retryable: false,

    })

  }



  if (isMocksEnabled()) {
    return submitMockVote(topicId)
  }



  const token = accessToken ?? (await getAccessToken())

  if (!token) {

    throw new VoteSubmitError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })

  }



  let response

  try {

    response = await fetch(`${apiBase()}/voting/votes`, {

      method: 'POST',

      headers: {

        Authorization: `Bearer ${token}`,

        'Content-Type': 'application/json',

      },

      body: JSON.stringify({

        topic_id: topicId,

        expected_updated_at: expectedUpdatedAt ?? null,

      }),

    })

  } catch {

    throw new VoteSubmitError(

      'Сервер голосования временно недоступен. Проверьте соединение и повторите попытку.',

      { code: 'NETWORK', retryable: true },

    )

  }



  if (response.status === 401) {

    throw new VoteSubmitError('Сессия истекла. Войдите снова.', {

      code: 'UNAUTHORIZED',

      retryable: false,

    })

  }



  if (response.status === 400) {

    throw new VoteSubmitError('Выберите тему', { code: 'NO_TOPIC', retryable: false })

  }



  if (response.status === 409) {

    let detail = {}

    try {

      const body = await response.json()

      detail = body?.detail ?? body ?? {}

    } catch {

      detail = {}

    }

    const code = detail.code ?? 'CONFLICT'

    const message =

      detail.message ??

      (code === 'CYCLE_CLOSED'

        ? 'Цикл голосования закрыт'

        : 'Голос уже изменён на другом устройстве')

    throw new VoteSubmitError(message, {

      code,

      retryable: false,

      ballot: detail.ballot ? normalizeSnapshot(detail.ballot) : null,

    })

  }



  if (!response.ok) {

    throw new VoteSubmitError(

      'Сервер голосования временно недоступен. Проверьте соединение и повторите попытку.',

      { code: 'NETWORK', retryable: true },

    )

  }



  return normalizeSnapshot(await response.json())

}



