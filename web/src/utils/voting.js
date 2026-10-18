/**
 * Pure helpers for voting UI copy and button labels (D-44, VOTE-02).
 */

/**
 * Leader strip copy from BallotSnapshot.leaders[] only (D-40, D-42, D-43).
 * @param {Array<{ title: string, votes: number }> | null | undefined} leaders
 * @returns {string | null}
 */
export function leaderStripText(leaders) {
  if (!Array.isArray(leaders) || leaders.length === 0) return null
  if (leaders.length === 1) {
    const { title, votes } = leaders[0]
    return `Сейчас лидирует: ${title} · ${votes} голосов`
  }
  const titles = leaders.map((item) => item.title)
  const names =
    titles.length === 2
      ? `${titles[0]} и ${titles[1]}`
      : `${titles.slice(0, -1).join(', ')} и ${titles[titles.length - 1]}`
  const votes = leaders[0].votes
  return `Сейчас лидируют: ${names} · ${votes} голосов каждый`
}

export function voteStatusText({ confirmedId, selectedId, topics }) {
  if (confirmedId) {
    const topic = topics.find((item) => item.id === confirmedId)
    return `Ваш голос: ${topic?.title ?? confirmedId}`
  }
  if (selectedId) {
    const topic = topics.find((item) => item.id === selectedId)
    return `Выбор: «${topic?.title ?? selectedId}» (нажмите «Подтвердить голос»)`
  }
  return 'голос не отдан'
}

/**
 * @param {string} state
 * @param {{ confirmedId?: string | null }} [opts]
 */
export function voteButtonLabel(state, { confirmedId } = {}) {
  if (state === 'loading') return 'Сохраняем…'
  if (state === 'error') return 'Повторить'
  if (confirmedId) return 'Изменить голос'
  return 'Подтвердить голос'
}
