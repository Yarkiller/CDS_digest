/**
 * Role-only helper. Knowledge search is server-side (KNOW-02).
 * Tag / format / topic selects are out of Phase 4 (D-63) and are not applied.
 */
export function filterMaterials(items, { query = '', role = '' } = {}) {
  const tokens = query
    .toLowerCase()
    .split(/[\s,.#]+/)
    .filter(Boolean)

  return items.filter((item) => {
    if (role && !(item.roles ?? []).includes(role)) return false

    if (!tokens.length) return true
    const haystack = `${item.title} ${item.keywords ?? ''} ${(item.tags ?? []).join(' ')}`.toLowerCase()
    return tokens.some((token) => haystack.includes(token))
  })
}

export function padIssueNumber(position) {
  return String(position).padStart(2, '0')
}
