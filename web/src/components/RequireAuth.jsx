import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getSession, signOut } from '../services/authApi.js'
import { isLoginRequired, isMocksEnabled } from '../services/authEnv.js'
import { corporateAllowedDomains, isCorporateSession } from '../services/oauthSession.js'

/**
 * Auth gate. Mocks mode renders children immediately (D-09 offline tests) UNLESS
 * VITE_REQUIRE_LOGIN=true, which enforces a real sign-in on the deployed app.
 */
export default function RequireAuth({ children }) {
  const location = useLocation()
  const gate = !isMocksEnabled() || isLoginRequired()
  const [ready, setReady] = useState(!gate)
  const [authed, setAuthed] = useState(!gate)

  useEffect(() => {
    if (!gate) {
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
          // OAuth sessions must still carry a corporate email (ADR-0003).
          if (
            session?.access_token &&
            !isCorporateSession(session, corporateAllowedDomains(import.meta.env))
          ) {
            await signOut()
            setAuthed(false)
            setReady(true)
            return
          }
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
  }, [location.pathname, location.search, gate])

  if (!gate) {
    return children
  }

  if (!ready) {
    return (
      <p className="text-sm text-text-disabled" role="status">
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
