---
phase: 22
review: 22-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Повторный клик по уже активной вкладке раздела при dirty-редакторе вызывает ложный диалог ухода"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Shell-пилюля «Админ» визуально активна на /admin/pipeline и /admin/materials/:id, но без aria-current"
  - id: IN-01
    severity: info
    disposition: open
    title: "На admin-страницах не осталось ни одного h1"
  - id: IN-02
    severity: info
    disposition: open
    title: "waitForTimeout вместо ожидания условия в G-14-2 тесте"
  - id: IN-03
    severity: info
    disposition: open
    title: "Пробелы в покрытии nav-контракта (не ловят WR-01/WR-02 и вакуумный ассерт)"
  - id: IN-04
    severity: info
    disposition: open
    title: "Недостижимая ветка pathname === '/admin' в AppShell"
open: 6
total: 6
recorded: 2026-10-17T11:20:00.000Z
---

# Phase 22: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.
