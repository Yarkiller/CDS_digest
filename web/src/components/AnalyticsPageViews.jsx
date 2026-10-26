import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { trackPageView } from '../services/analyticsRuntime.js'

/** Sends a Yandex.Metrika page-view on every route change (no-op without a counter). */
export default function AnalyticsPageViews() {
  const location = useLocation()

  useEffect(() => {
    trackPageView(`${location.pathname}${location.search}`)
  }, [location.pathname, location.search])

  return null
}
