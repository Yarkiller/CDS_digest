/**
 * Yandex.Metrika analytics — pure, injectable (no import.meta.env, no globals).
 * Runtime wiring (window + VITE_YM_COUNTER_ID) lives in analyticsRuntime.js.
 */

export const ANALYTICS_GOALS = Object.freeze({
  login: 'login',
  login_oauth: 'login_oauth',
  vote: 'vote',
  search: 'search',
  material_open: 'material_open',
  digest_send: 'digest_send',
})

export const METRIKA_TAG_URL = 'https://mc.yandex.ru/metrika/tag.js'

/**
 * A counter is usable only when it is a non-empty numeric id.
 * @param {unknown} counterId
 * @returns {boolean}
 */
export function analyticsEnabled(counterId) {
  if (typeof counterId !== 'string') {
    return false
  }
  return /^\d+$/.test(counterId.trim())
}

/**
 * Send a Metrika goal (reachGoal). Returns true when the call was dispatched.
 * @param {{ ym?: (...args: unknown[]) => void } | null | undefined} win
 * @param {string} counterId
 * @param {string} goal
 * @param {Record<string, unknown>} [params]
 */
export function trackGoal(win, counterId, goal, params = {}) {
  if (!analyticsEnabled(counterId) || typeof win?.ym !== 'function') {
    return false
  }
  win.ym(String(counterId).trim(), 'reachGoal', goal, params)
  return true
}

/**
 * Send a page-view hit. Returns true when the call was dispatched.
 * @param {{ ym?: (...args: unknown[]) => void } | null | undefined} win
 * @param {string} counterId
 * @param {string} url
 * @param {string} [title]
 */
export function trackHit(win, counterId, url, title) {
  if (!analyticsEnabled(counterId) || typeof win?.ym !== 'function') {
    return false
  }
  win.ym(String(counterId).trim(), 'hit', url, title ? { title } : undefined)
  return true
}

/**
 * Inject the Metrika tag and initialise the counter. Idempotent.
 * @param {{ counterId?: string, doc?: Document, win?: Window }} [options]
 * @returns {boolean} whether the counter was initialised
 */
export function initAnalytics({ counterId, doc, win } = {}) {
  if (!analyticsEnabled(counterId) || !doc || !win) {
    return false
  }
  if (typeof win.ym !== 'function') {
    const queue = []
    const ym = (...args) => {
      queue.push(args)
    }
    ym.a = queue
    ym.l = Date.now()
    win.ym = ym

    const script = doc.createElement('script')
    script.async = true
    script.src = `${METRIKA_TAG_URL}?id=${String(counterId).trim()}`
    doc.head.appendChild(script)
  }
  win.ym(String(counterId).trim(), 'init', {
    ssr: true,
    webvisor: true,
    clickmap: true,
    ecommerce: 'dataLayer',
    trackLinks: true,
    accurateTrackBounce: true,
  })
  return true
}
