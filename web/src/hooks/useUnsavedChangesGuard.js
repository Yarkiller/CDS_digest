import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'
import { armBeforeUnload } from '../utils/unsavedChangesGuard.js'

/**
 * Block every in-app SPA navigation while `dirty` is true (ADUX-09, D-04),
 * and arm the browser `beforeunload` prompt only while dirty (D-05).
 *
 * @param {boolean} dirty  `yaml !== savedYaml` — the page's single source of truth (D-12)
 * @returns {import('react-router-dom').Blocker}
 */
export function useUnsavedChangesGuard(dirty) {
  const blocker = useBlocker(Boolean(dirty))

  useEffect(() => {
    if (!dirty) return undefined
    window.addEventListener('beforeunload', armBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', armBeforeUnload)
    }
  }, [dirty])

  return blocker
}
