import { useBlocker } from 'react-router-dom'

/**
 * Block every in-app SPA navigation while `dirty` is true (ADUX-09, D-04).
 * Boolean form — no pathname carve-out. Reload/close arming lands in Task 2.
 *
 * @param {boolean} dirty  `yaml !== savedYaml` — the page's single source of truth (D-12)
 * @returns {import('react-router-dom').Blocker}
 */
export function useUnsavedChangesGuard(dirty) {
  return useBlocker(Boolean(dirty))
}
