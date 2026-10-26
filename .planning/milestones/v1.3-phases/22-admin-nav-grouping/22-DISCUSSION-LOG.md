# Phase 22: Admin nav grouping - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-17
**Phase:** 22-admin-nav-grouping
**Areas discussed:** tab-bar-host, tab-visual-style, nested-admin-routes, dirty-pipeline-guard, narrow-viewport

---

## Где живёт tab-bar

| Option | Description | Selected |
|--------|-------------|----------|
| Общий admin layout + Outlet | Один shell с tab-bar; digest/pipeline — children | ✓ |
| Дублировать tab-bar | На обеих страницах без рефакторинга роутера | |
| You decide | | |

**User's choice:** Общий AdminLayout + Outlet
**Notes:** Plus nest inside AppShell; only digest+pipeline under layout; materials preview sibling; no `/admin` redirect.

---

## Внешний вид табов

| Option | Description | Selected |
|--------|-------------|----------|
| Underline tabs | Текст + нижняя граница; не AppShell pills | ✓ |
| Segmented / pills | Как `linkClass` в shell | |
| You decide | | |

**Follow-ups locked:** tabs replace H1; labels «Дайджест \| Пайплайн»; active = display-size (`text-3xl font-semibold`).

---

## Вложенные admin-маршруты

| Option | Description | Selected |
|--------|-------------|----------|
| «Админ» active на любом `/admin/*` | | ✓ |
| Active только на digest | | |
| Click «Админ» → всегда `/admin/digest` | | ✓ |
| Click no-op если уже в `/admin/*` | | |
| Preview: ничего кроме подсветки | | ✓ |
| Preview: добавить «← К шортлисту» | | |
| Markup: `nav` + NavLink | | ✓ |
| Markup: `role="tablist"` | | |

**User's choice:** Active all `/admin/*`; click → digest; no preview back-link; nav+NavLink not ARIA tabs.

---

## Грязный пайплайн-редактор

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 19 guard на клик «Дайджест» | Tab = SPA nav, no carve-out | ✓ |
| Silent leave внутри layout | | |
| Новый Playwright journey dirty→tab→modal | | ✓ |
| Только amend shell-nav тестов | | |
| Copy/actions без изменений vs Phase 19 | | ✓ |
| Отдельная формулировка для вкладок | | |

---

## Узкий viewport

| Option | Description | Selected |
|--------|-------------|----------|
| Всегда в ряд | | |
| Горизонтальный scroll | | |
| Collapse | | ✓ |
| Collapse = native `<select>` | | ✓ |
| Breakpoint `sm` (640px) | | ✓ |
| select → `navigate()` (guard жив) | | ✓ |

**Notes:** User: phone admin is not a target use case — select is a backstop only.

---

## Claude's Discretion

None.

## Deferred Ideas

- Materials-preview «← К шортлисту» back-link
- Polished mobile-admin tab chrome
- `/admin` index redirect
- ADUX-10 ingest-sources (Phase 23)
