import { useEffect, useState } from 'react'
import { Link, matchPath, NavLink, Outlet, useLocation } from 'react-router-dom'
import SearchPill from './SearchPill.jsx'
import ThemeToggle from './ThemeToggle.jsx'
import { getAccessToken } from '../services/authApi.js'
import { isLoginRequired, isMocksEnabled } from '../services/authEnv.js'
import { fetchMe } from '../services/meApi.js'

const MOCK_SHELL_IDENTITY = 'Мария Сидорова'

const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-2.5 text-sm',
    isActive ? 'bg-primary-solid text-on-solid' : 'text-text-secondary hover:bg-bg-surface',
  ].join(' ')

/** Fallback identity for local mock browsing — never shown when login is required. */
function mockIdentity() {
  return isMocksEnabled() && !isLoginRequired() ? MOCK_SHELL_IDENTITY : ''
}

async function resolveShellSession(token) {
  if (!token) {
    const me = await fetchMe(null)
    return { identity: mockIdentity(), appRole: me.role ?? 'employee' }
  }
  const me = await fetchMe(token)
  const identity = me.display_name?.trim() || me.email || mockIdentity()
  return { identity, appRole: me.role ?? 'employee' }
}

export default function AppShell() {
  const [identity, setIdentity] = useState(() => mockIdentity())
  const [appRole, setAppRole] = useState(/** @type {string | null} */ (null))
  const { pathname, state } = useLocation()
  // D-09: «Админ» lights up on digest, pipeline, and the materials preview alike.
  // IN-04: the /admin/ prefix is the single source of truth — there is no /admin route
  // (D-04), and the catch-all redirects /admin to /, so an equality branch is dead code.
  const adminActive = pathname.startsWith('/admin/')

  // D-07: the origin marker is a closed list — 'archive' | 'base' | 'issue'. This is the
  // only place it is compared; an absent or unknown value lights nothing at all (D-10).
  // It is never rendered and never reaches a className, so a forged history.state can
  // only paint a pill — it decides nothing about data, routing or access.
  const section = state?.section

  // D-10: '/issues/:number' exists only inside the archive, so that prefix is the one
  // honest inference from the address; a material URL never is (it serves three origins).
  // CR-01: ask the router instead of comparing strings by hand — `matchPath` keeps the
  // trailing-slash and case normalisation `NavLink` had, so `/archive/` or `/Archive`
  // (both of which the router still matches) cannot leave every pill dark.
  const homeRoute = Boolean(matchPath({ path: '/', end: true }, pathname))
  const archiveRoute = Boolean(matchPath({ path: '/archive', end: true }, pathname))
  const issuesBranch = Boolean(matchPath({ path: '/issues/:number' }, pathname))
  const baseRoute = Boolean(matchPath({ path: '/knowledge', end: true }, pathname))

  const homeLit = homeRoute || section === 'issue'
  const archiveLit = archiveRoute || issuesBranch || section === 'archive'
  const baseLit = baseRoute || section === 'base'

  // D-11: 'page' only for a pill's own route; 'true' when the section is claimed by
  // navigation state or by the /issues/ prefix.
  const current = (ownRoute) => (ownRoute ? 'page' : 'true')

  useEffect(() => {
    let cancelled = false

    async function loadIdentity() {
      try {
        const session = await resolveShellSession(await getAccessToken())
        if (!cancelled) {
          setIdentity(session.identity)
          setAppRole(session.appRole)
        }
      } catch {
        if (!cancelled) {
          setIdentity(mockIdentity())
          setAppRole('employee')
        }
      }
    }

    loadIdentity()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-svh bg-bg-app text-text-primary">
      <header className="sticky top-0 z-40 border-b border-border bg-bg-app">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-1.5 px-4 py-3">
          <div className="mr-auto min-w-0">
            <p className="font-display text-sm font-semibold text-primary-text">Digest CDS</p>
            <p className="text-xs text-text-disabled">СВА · издание</p>
          </div>
          <nav
            className="order-last flex w-full flex-wrap gap-1 sm:order-none sm:w-auto"
            aria-label="Основная навигация"
          >
            {/* D-11: NavLink drops an explicit aria-current whenever its own `to` is
                inactive, so a state-claimed section could never be announced. These three
                compute the attribute and the fill themselves, exactly like «Админ». */}
            <Link
              to="/"
              aria-current={homeLit ? current(homeRoute) : undefined}
              className={linkClass({ isActive: homeLit })}
            >
              Выпуск
            </Link>
            <Link
              to="/archive"
              aria-current={archiveLit ? current(archiveRoute) : undefined}
              className={linkClass({ isActive: archiveLit })}
            >
              Архив
            </Link>
            <Link
              to="/knowledge"
              aria-current={baseLit ? current(baseRoute) : undefined}
              className={linkClass({ isActive: baseLit })}
            >
              База
            </Link>
            <NavLink to="/voting" className={linkClass}>
              Голосование
            </NavLink>
            <NavLink to="/razbory" className={linkClass}>
              Разборы
            </NavLink>
            {appRole === 'admin' ? (
              <Link
                to="/admin/digest"
                // WR-02: NavLink derives aria-current from `to="/admin/digest"`, so the pill
                // was announced as inactive on pipeline/preview while looking active. Set it
                // from the already-computed prefix instead — "true" (not "page") because the
                // href targets digest while the whole admin section is the current context.
                aria-current={adminActive ? 'true' : undefined}
                className={linkClass({ isActive: adminActive })}
              >
                Админ
              </Link>
            ) : null}
          </nav>
          <SearchPill />
          <div className="flex flex-wrap items-center gap-1.5">
            {/* Gamification (XP, streak, rank) is deferred to the next version by
                ADR-0009 and banned in this release by ADR-0007 — the slot keeps only
                the theme toggle, which is part of the canon contract. */}
            <ThemeToggle data-testid="theme-toggle" />
          </div>
          {identity ? (
            <Link
              to="/profile"
              className="max-w-[10rem] shrink-0 truncate text-sm text-text-secondary underline-offset-2 hover:text-primary-text hover:underline sm:max-w-[8rem]"
              data-testid="shell-identity"
              title={identity}
            >
              {identity}
            </Link>
          ) : null}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-10">
        <Outlet />
      </main>
    </div>
  )
}
