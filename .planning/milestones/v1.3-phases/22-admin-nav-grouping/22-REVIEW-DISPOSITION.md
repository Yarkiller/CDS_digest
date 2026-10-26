---
phase: 22
review: 22-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Повторный клик по уже активной вкладке раздела при dirty-редакторе вызывает ложный диалог ухода"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Shell-пилюля «Админ» визуально активна на /admin/pipeline и /admin/materials/:id, но без aria-current"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "На admin-страницах не осталось ни одного h1"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "waitForTimeout вместо ожидания условия в G-14-2 тесте"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "Пробелы в покрытии nav-контракта (не ловят WR-01/WR-02 и вакуумный ассерт)"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Недостижимая ветка pathname === '/admin' в AppShell"
open: 0
total: 6
recorded: 2026-10-17T11:20:00.000Z
updated: 2026-10-17T14:55:00.000Z
---

# Phase 22: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 22-03 (T1): `handleSectionTabClick` calls `preventDefault` only when `section === target`; test pins zero dialog + preserved draft on the active tab, and a genuine leave still prompts |
| WR-02 | warning | fixed | 22-03 (T2): shell pill is `Link` with `aria-current="true"` on every `/admin/*`, absent on `/` |
| IN-01 | info | fixed | 22-03 (T1): one `<h1 className="sr-only">` in `AdminLayout`; test fails if the `sr-only` class is dropped (class + box ≤ 1px) |
| IN-02 | info | deferred | Deferred in 22-03: the mocked refetch issues no network request, no observable busy transition, and the harness exposes no shortlist-fetch counter; recipe recorded in `22-03-PLAN.md` (add `getMockShortlistFetches()` + `expect.poll`) |
| IN-03 | info | fixed | 22-03 (T1/T2/T3): same-active-tab case, `aria-current` assertions, 640px sm edge, and the vacuous employee assertion at `/` replaced by a real deep-link case |
| IN-04 | info | fixed | 22-03 (T2): dead `pathname === '/admin'` disjunct removed; `startsWith('/admin/')` is the single source of truth |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.
