/** Runtime wiring for Yandex.Metrika: reads Vite env + browser globals (not node-testable). */

import {
  ANALYTICS_GOALS,
  initAnalytics as initAnalyticsImpl,
  trackGoal as trackGoalImpl,
  trackHit as trackHitImpl,
} from './analytics.js'

export function metrikaCounterId() {
  return import.meta.env.VITE_YM_COUNTER_ID ?? ''
}

export function initAnalytics() {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return false
  }
  return initAnalyticsImpl({ counterId: metrikaCounterId(), doc: document, win: window })
}

export function trackGoal(goal, params) {
  if (typeof window === 'undefined') {
    return false
  }
  return trackGoalImpl(window, metrikaCounterId(), goal, params)
}

export function trackPageView(url, title) {
  if (typeof window === 'undefined') {
    return false
  }
  return trackHitImpl(window, metrikaCounterId(), url, title)
}

export { ANALYTICS_GOALS }
