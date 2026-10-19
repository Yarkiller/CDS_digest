import { useEffect, useState } from 'react'
import { getAccessToken } from '../services/authApi.js'
import { fetchMe } from '../services/meApi.js'
import { clearWelcomeToast, peekWelcomeToast } from '../services/welcomeSession.js'

const DISMISS_MS = 5000
const FADE_MS = 500

/**
 * Fixed overlay welcome toast — once after login/register, fades without layout shift.
 */
export default function PlatformProofBanner() {
  const [me, setMe] = useState(null)
  const [phase, setPhase] = useState('idle') // idle | shown | fading

  useEffect(() => {
    let cancelled = false
    let dismissTimer
    let fadeTimer

    async function maybeShow() {
      if (!peekWelcomeToast()) return
      try {
        const token = await getAccessToken()
        if (!token || cancelled) return
        const user = await fetchMe(token)
        if (cancelled || !user) return
        setMe(user)
        setPhase('shown')
        dismissTimer = window.setTimeout(() => {
          if (cancelled) return
          // Clear only once the toast has been on screen. IssuePage remounts
          // this banner when loading becomes ready; clearing on show dropped it.
          clearWelcomeToast()
          setPhase('fading')
          fadeTimer = window.setTimeout(() => {
            if (!cancelled) setPhase('idle')
          }, FADE_MS)
        }, DISMISS_MS)
      } catch {
        // Silent — content pages own load-failure UX.
      }
    }

    maybeShow()
    return () => {
      cancelled = true
      if (dismissTimer) window.clearTimeout(dismissTimer)
      if (fadeTimer) window.clearTimeout(fadeTimer)
    }
  }, [])

  if (phase === 'idle' || !me) return null

  const label = me.display_name?.trim()
    ? `${me.display_name.trim()} · ${me.email}`
    : me.email

  return (
    <aside
      data-testid="welcome-toast"
      role="status"
      aria-live="polite"
      className={[
        'pointer-events-none fixed left-1/2 top-20 z-50 w-[min(100%-2rem,28rem)] -translate-x-1/2',
        'rounded-lg border border-rule bg-paper-2 px-4 py-3 text-center text-sm text-ink shadow-md',
        'transition-opacity duration-500 ease-out',
        phase === 'fading' ? 'opacity-0' : 'opacity-100',
      ].join(' ')}
    >
      <p>
        Вы вошли как <strong className="font-medium">{label}</strong>
      </p>
    </aside>
  )
}
