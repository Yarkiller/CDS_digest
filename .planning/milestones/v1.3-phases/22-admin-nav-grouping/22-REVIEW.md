---
phase: 22-admin-nav-grouping
reviewed: 2026-10-17T11:12:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - web/src/components/AdminLayout.jsx
  - web/src/components/AppShell.jsx
  - web/src/App.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - tests/admin.spec.js
findings:
  critical: 0
  warning: 2
  info: 4
  total: 6
status: issues_found
---

# Phase 22: Code Review Report

**Reviewed:** 2026-10-17T11:12:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Проверен nav-группинг админки (ADUX-12): `AdminLayout` как pathless layout для `admin/digest` + `admin/pipeline`, единственная shell-пилюля «Админ», отсутствие `/admin` index, `admin/materials/:id` остаётся sibling, guard Phase 19 не получал carve-out, копия модалки не менялась. Все явные запреты плана соблюдены: второго shell-пункта «Пайплайн» нет, ARIA `tablist/tab/tabpanel` не используется (`nav aria-label="Разделы админки"` + `NavLink`), URL-ы не изменены, `UnsavedChangesDialog` переиспользован как есть.

Замечаний уровня BLOCKER не найдено: утечек данных, обхода авторизации и падений нет, черновик при любом сценарии сохраняется. Есть два дефекта поведения/доступности (WR-01, WR-02), подтверждённые прогоном в реальном браузере на dev-сервере с mock-ролью admin (не только чтением кода), и четыре замечания по качеству/покрытию.

Полный Playwright-suite в рамках ревью не перезапускался (в `test-results/.last-run.json` зафиксирован прошлый `passed`); для WR-01/WR-02 выполнены точечные браузерные пробы.

## Narrative Findings (AI reviewer)

### Warnings

#### WR-01: Повторный клик по уже активной вкладке раздела при dirty-редакторе вызывает ложный диалог ухода

**File:** `web/src/components/AdminLayout.jsx:39-44` (в связке с `web/src/pages/AdminPipelineConfigPage.jsx:108`)
**Issue:** `NavLink` на текущий маршрут всё равно вызывает `navigate()` (react-router `Link` не подавляет переход на тот же URL), а `useBlocker(Boolean(dirty))` не имеет исключения для same-location навигации: в `react-router` 7.18.3 `shouldBlockNavigation()` сравнивает только наличие blocker-функции, но не `currentLocation` с `nextLocation`. В результате на `/admin/pipeline` с несохранённым YAML клик по уже активной вкладке «Пайплайн» открывает Phase 19 диалог «Есть несохранённые изменения. Уйти без сохранения?», хотя уходить некуда. Проба в браузере: `dialogCount = 1`, URL остаётся `/admin/pipeline`; после «Уйти без сохранения» URL тот же, текст редактора `template: lecture\n` сохранён, статус «Есть несохранённые изменения» — то есть копия диалога противоречит фактическому результату (ничего не покидается и не теряется). Побочный эффект: клик по активной вкладке/shell-пилюле добавляет лишнюю запись в историю (Back визуально «не работает»).

**Fix:** подавить переход, когда целевой раздел уже активен. У `Link` пользовательский `onClick` выполняется до внутренней навигации и проверяется через `event.defaultPrevented`, поэтому достаточно:

```jsx
function sameSectionClick(event, path, section) {
  if (section === path) event.preventDefault()
}

<NavLink
  to={PIPELINE_PATH}
  data-testid="admin-tab-pipeline"
  className={tabClass}
  onClick={(event) => sameSectionClick(event, PIPELINE_PATH, section)}
>
```

Альтернатива — учесть same-location в самом guard (`currentLocation.pathname !== nextLocation.pathname`), но это меняет контракт Phase 19 глобально; локальная правка `AdminLayout` безопаснее. Добавить Playwright-кейс «dirty + клик по активной вкладке → диалога нет».

#### WR-02: Shell-пилюля «Админ» визуально активна на `/admin/pipeline` и `/admin/materials/:id`, но без `aria-current`

**File:** `web/src/components/AppShell.jsx:92-93`
**Issue:** класс активности считается вручную из `adminActive` (`pathname`-префикс), а `aria-current` вычисляет сам `NavLink` — только по совпадению с `to="/admin/digest"`. На `/admin/pipeline` и `/admin/materials/...` пилюля получает `bg-accent text-accent-ink`, но `aria-current` отсутствует (проба в браузере: `shellAriaCurrent: null` в обоих случаях). Требование D-09 «active on any `/admin/*`» выражено только визуально: скринридер не сообщает, что пользователь находится в админ-разделе, а зрячий и незрячий пользователи получают разную картину. Переопределить это пропом нельзя: `NavLink` деструктурирует `aria-current` и вычисляет его после `...rest` (`ariaCurrent = isActive ? ariaCurrentProp : undefined`).

**Fix:** заменить `NavLink` на `Link` и выставлять состояние вручную (совпадение уже посчитано):

```jsx
import { Link } from 'react-router-dom'

<Link
  to="/admin/digest"
  aria-current={adminActive ? 'true' : undefined}
  className={linkClass({ isActive: adminActive })}
>
  Админ
</Link>
```

`aria-current="true"` (а не `"page"`) точнее: ссылка ведёт на digest, а «текущим» является весь admin-раздел. Добавить в тесты проверку `aria-current` на `/admin/pipeline` и на materials preview.

### Info

#### IN-01: На admin-страницах не осталось ни одного `h1`

**File:** `web/src/pages/AdminDigestPage.jsx:511`, `web/src/pages/AdminPipelineConfigPage.jsx:222`
**Issue:** D-06 убрал page-level H1, но активная вкладка раздела — это `<a>`, а не заголовок. В итоге outline страницы начинается с `h2` («Контекст дайджеста», «Кандидатов пока нет», …), а в части состояний (loading/error/rest) заголовков нет вовсе (проверено: `h1Count = 0`). Визуально это санкционировано UI-SPEC, но семантически страница потеряла заголовок — навигация по заголовкам в скринридере больше не идентифицирует раздел.
**Fix:** не менять визуал, добавить скрытый заголовок и связать его с контентом, например `<h1 className="sr-only">{section === PIPELINE_PATH ? 'Пайплайн' : 'Дайджест'}</h1>` в `AdminLayout` (до `<Outlet />`) либо `aria-labelledby` на контейнере, ссылающийся на `id` активной вкладки.

#### IN-02: `waitForTimeout` вместо ожидания условия в G-14-2 тесте

**File:** `tests/admin.spec.js:433`
**Issue:** `await page.waitForTimeout(500)` — время-зависимое ожидание завершения «устаревшего» refetch (60 ms POST + 80 ms GET в моке). Под нагрузкой 500 ms может не хватить и тест станет flaky; при обратном сценарии фиксированная пауза маскирует момент регрессии.
**Fix:** ждать наблюдаемое условие вместо таймера — `await expect.poll(() => ...)` по состоянию строки или `await page.waitForResponse(...)` для GET шортлиста, затем проверять, что строка осталась `готов`.

#### IN-03: Пробелы в покрытии nav-контракта (не ловят WR-01/WR-02 и вакуумный ассерт)

**File:** `tests/admin.spec.js:164`, `:176`, `:194`, `:1568`
**Issue:**
- Нет кейса «dirty-редактор + клик по уже активной вкладке» — именно он фиксирует WR-01.
- Активность shell-пилюли проверяется только классом `bg-accent` (`:164`, `:176`, `:194`); `aria-current` не проверяется, поэтому WR-02 проходит незамеченным.
- `pipeline config nav item hidden for employee` (`:1568`) проверяет отсутствие `admin-section-nav` на маршруте `/`, где `AdminLayout` не рендерится в принципе — ассерт не может упасть. Полезнее проверить сотрудника на `/admin/digest`: layout рендерится (это разрешено), но страница обязана показать `ForbiddenPage`, а ссылки раздела не должны давать доступа к данным.
- Backstop UI-SPEC по overflow (E1, край `sm` ≈ 640 px) не покрыт: есть только 480 px (select) и дефолтные 1280 px.
**Fix:** добавить перечисленные проверки в `Admin nav grouping` describe; проверять `aria-current` рядом с `bg-accent`.

#### IN-04: Недостижимая ветка `pathname === '/admin'` в AppShell

**File:** `web/src/components/AppShell.jsx:37`
**Issue:** маршрута `/admin` нет (D-04), а catch-all `{ path: '*', element: <Navigate to="/" replace /> }` (`web/src/App.jsx:48`) уводит с `/admin` на `/`, поэтому `AppShell` на этом пути никогда не рендерится — условие мёртвое.
**Fix:** убрать `pathname === '/admin' ||` либо оставить с комментарием, что это защита на случай появления `/admin` index в будущем.

---

_Reviewed: 2026-10-17T11:12:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
