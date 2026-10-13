/**
 * Concept 2 demo seed for gamification widgets (XP / streak / rank / leaderboard).
 *
 * Gamification is post-v1 (ADR-0001) and has no backend module yet, so the shell
 * renders explicitly-labelled demo data instead of fabricating live user stats.
 */

export const DEMO_ME_STATS = Object.freeze({
  level: 7,
  xp: 340,
  xpMax: 500,
  streakDays: 12,
  rank: 8,
})

export const DEMO_LEADERBOARD = Object.freeze([
  Object.freeze({ rank: 1, name: 'Anna K.', level: 12, xp: 840, streakDays: 21, isSelf: false }),
  Object.freeze({ rank: 2, name: 'Maria S.', level: 11, xp: 720, streakDays: 18, isSelf: false }),
  Object.freeze({ rank: 3, name: 'Alex K.', level: 10, xp: 610, streakDays: 15, isSelf: false }),
  Object.freeze({ rank: 4, name: 'Elena P.', level: 9, xp: 520, streakDays: 8, isSelf: false }),
  Object.freeze({ rank: 5, name: 'Oleg N.', level: 8, xp: 480, streakDays: 6, isSelf: false }),
  Object.freeze({ rank: 6, name: 'Pavel R.', level: 8, xp: 430, streakDays: 5, isSelf: false }),
  Object.freeze({ rank: 7, name: 'Sofia T.', level: 7, xp: 390, streakDays: 4, isSelf: false }),
  Object.freeze({ rank: 8, name: 'Вы', level: 7, xp: 340, streakDays: 12, isSelf: true }),
])

export const LEADERBOARD_NOTE = 'Демо-данные · рейтинг появится после v1 (ADR-0001)'
