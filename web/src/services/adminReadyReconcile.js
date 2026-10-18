/**
 * Pure post-promote refetch reconciliation (G-14-2 / ADUX-05).
 *
 * The single/batch ready POST response is the source of truth for a promoted
 * row's ready state; a follow-up shortlist refetch is display reconciliation
 * only. When a refetch still reports `draft` (live read-after-write lag, or a
 * backend that acknowledged the POST without persisting), the refetch must
 * never silently downgrade a confirmed promote back to draft.
 *
 * No Vite/supabase/import.meta — safe under node --test.
 */

/** @typedef {{ material_id: number, material_status: 'ready'|'draft' }} AdminReadyReconcileItem */

/**
 * Force promoted material ids back to `ready` over a refetched shortlist.
 *
 * For each item whose `material_id` is in `promotedIds` and whose
 * `material_status` is not already `'ready'`, returns a shallow-cloned item
 * with `material_status: 'ready'`. Every other item (and every already-ready
 * promoted item) is returned unchanged — including non-promoted still-draft
 * rows, which follow the refetch.
 *
 * @param {Array<AdminReadyReconcileItem>|null|undefined} refetchedItems
 * @param {Iterable<number>|null|undefined} promotedIds
 * @returns {Array<AdminReadyReconcileItem>} reconciled items (same reference when no change is needed)
 */
export function preservePromotedReady(refetchedItems, promotedIds) {
  const items = Array.isArray(refetchedItems) ? refetchedItems : []
  const promoted = promotedIds instanceof Set ? promotedIds : new Set(promotedIds ?? [])
  if (promoted.size === 0) return items

  let changed = false
  const next = items.map((item) => {
    if (!item || !promoted.has(item.material_id) || item.material_status === 'ready') {
      return item
    }
    changed = true
    return { ...item, material_status: 'ready' }
  })
  return changed ? next : items
}
