import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getSession } from '../services/authApi.js'
import { isMocksEnabled } from '../services/authEnv.js'

/**
 * Auth gate: when mocks enabled (default), render children immediately (D-09).
 * When mocks disabled (or test force-gate), require a session else redirect with returnUrl.
 */
export default function RequireAuth({ children }) {
  const location = useLocation()
  const mocksOn = isMocksEnabled()
  const [ready, setReady] = useState(mocksOn)
  const [authed, setAuthed] = useState(mocksOn)

  useEffect(() => {
    if (isMocksEnabled()) {
      setAuthed(true)
      setReady(true)
      return undefined
    }

    let cancelled = false

    async function check() {
      setReady(false)
      try {
        const session = await getSession()
        if (!cancelled) {
          setAuthed(Boolean(session?.access_token))
          setReady(true)
        }
      } catch {
        if (!cancelled) {
          setAuthed(false)
          setReady(true)
        }
      }
    }

    check()
    return () => {
      cancelled = true
    }
  }, [location.pathname, location.search])

  if (mocksOn) {
    return children
  }

  if (!ready) {
    return (
      <p className="text-sm text-muted" role="status">
        Проверка сессии…
      </p>
    )
  }

  if (!authed) {
    const returnUrl = `${location.pathname}${location.search}`
    const params = new URLSearchParams({ returnUrl })
    return <Navigate to={`/login?${params.toString()}`} replace />
  }

  return children
}
