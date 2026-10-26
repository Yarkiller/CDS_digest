/**
 * Russian zero-one-many plural labels for ballot / issue meta (UI-SPEC).
 */

function ruPlural(count, one, few, many) {
  const n = Number(count) || 0
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} ${one}`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${n} ${few}`
  }
  return `${n} ${many}`
}

export function materialCountLabel(count) {
  return ruPlural(count, 'материал', 'материала', 'материалов')
}

export function voteCountLabel(count) {
  return ruPlural(count, 'голос', 'голоса', 'голосов')
}
