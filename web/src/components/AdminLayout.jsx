import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

const DIGEST_PATH = '/admin/digest'
const PIPELINE_PATH = '/admin/pipeline'

/**
 * Underline in-page section switch (D-05): no pill fill, no ARIA tab roles (D-12) —
 * these destinations are routes. The active tab carries the former page H1 weight
 * (D-08) so hierarchy survives the D-06 H1 removal.
 */
function tabClass({ isActive }) {
  return [
    'inline-flex min-h-11 items-end border-b-2 pb-2 text-3xl',
    isActive
      ? 'border-accent font-semibold text-ink'
      : 'border-transparent font-normal text-muted hover:text-ink',
  ].join(' ')
}

/**
 * Shared admin chrome for /admin/digest + /admin/pipeline only (D-01, D-03).
 * Rendered by a pathless route, so both URLs stay byte-identical (D-04).
 */
export default function AdminLayout() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  // Hard-coded whitelist (T-22-02): the select can never navigate to a free-form path.
  const section = pathname.startsWith(PIPELINE_PATH) ? PIPELINE_PATH : DIGEST_PATH

  /**
   * WR-01: a NavLink to the CURRENT location still runs navigate(), and the Phase 19
   * blocker reads that as a leave. Suppress only the already-active tab (D-13) — every
   * genuine leave still reaches useBlocker and the unchanged dialog (D-15).
   * Declared inside the component so it closes over the per-render `section`.
   */
  function handleSectionTabClick(event, target) {
    if (section === target) event.preventDefault()
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>

      {/*
        IN-01: the outline must not start at h2, but D-06 forbids a visible page title —
        so the section name lives in a visually hidden h1. The layout wraps every child
        branch (ready/loading/error/forbidden), so each one inherits this heading.
      */}
      <h1 className="sr-only">{section === PIPELINE_PATH ? 'Пайплайн' : 'Дайджест'}</h1>

      <nav
        className="mt-2 hidden gap-2 border-b border-rule sm:flex"
        aria-label="Разделы админки"
        data-testid="admin-section-nav"
      >
        <NavLink
          to={DIGEST_PATH}
          data-testid="admin-tab-digest"
          className={tabClass}
          onClick={(event) => handleSectionTabClick(event, DIGEST_PATH)}
        >
          Дайджест
        </NavLink>
        <NavLink
          to={PIPELINE_PATH}
          data-testid="admin-tab-pipeline"
          className={tabClass}
          onClick={(event) => handleSectionTabClick(event, PIPELINE_PATH)}
        >
          Пайплайн
        </NavLink>
      </nav>

      <select
        aria-label="Разделы админки"
        data-testid="admin-section-select"
        className="mt-2 min-h-11 w-full max-w-sm rounded-xl border border-rule bg-paper px-3 text-base text-ink focus-visible:outline-accent sm:hidden"
        value={section}
        // navigate() (not a document assignment) so useBlocker still fires on dirty leave (D-19).
        onChange={(event) => navigate(event.target.value)}
      >
        <option value={DIGEST_PATH}>Дайджест</option>
        <option value={PIPELINE_PATH}>Пайплайн</option>
      </select>

      <div className="mt-6">
        <Outlet />
      </div>
    </div>
  )
}
