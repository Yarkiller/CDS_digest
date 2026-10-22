---
phase: 26-section-context-anchor-scrolling-and-header-active-state
plan: 02
subsystem: web-frontend (shell navigation + origin marker)
tags: [nav-02, aria-current, history-state, section-context, playwright, tdd]
requires:
  - phase: 26-01
    provides: "the global anchor offset, the extended fixtures and the section-context spec file the NAV-02 specs extend"
provides:
  - "web/src/components/AppShell.jsx: the three section pills are computed from route OR history.state.section"
  - "history.state.usr.section: one closed literal ('archive' | 'base' | 'issue') written by ArchivePage, IssuePage->IssueToc, KnowledgePage->MaterialListRow"
  - "web/src/pages/MaterialPage.jsx: originState?.section forwarded untouched to related materials (no literal comparison)"
  - "tests/web-app.spec.js: C-08, C-09, C-10, C-11, C-12, C-14, C-15, C-18, C-20 plus shared helpers"
affects:
  - 26-03 (C-13 honest degradation, C-16 admin untouched, C-17 closed-list gate all read this surface)
tech-stack:
  added: []
  patterns:
    - "<Link aria-current={lit ? (ownRoute ? 'page' : 'true') : undefined}> instead of NavLink, because NavLink drops an explicit aria-current when its own `to` is inactive"
    - "one read point: AppShell is the only place the three literals are compared (C-17); producers only write, MaterialPage only forwards"
    - "required props with no defaults (IssueToc, MaterialListRow) so a reusable component never guesses or hardcodes a section"
    - "blind forwarding: originState?.section passes through unchanged, so an out-of-enum value lights nothing downstream"
key-files:
  created: []
  modified:
    - web/src/components/AppShell.jsx
    - web/src/components/IssueToc.jsx
    - web/src/components/MaterialListRow.jsx
    - web/src/pages/ArchivePage.jsx
    - web/src/pages/IssuePage.jsx
    - web/src/pages/KnowledgePage.jsx
    - web/src/pages/MaterialPage.jsx
    - web/src/data/mock.js
    - tests/web-app.spec.js
decisions:
  - "Pills use <Link> + computed aria-current (D-11: 'page' only for a pill's own route, 'true' when the section is claimed by state)"
  - "The origin marker is one closed literal in history.state.usr.section — no { from: path }, no issue number, no storage (D-07)"
  - "Archive is the only section inferred from the URL (/issues/ prefix); /materials/:id never infers a section (D-10)"
  - "IssueToc and MaterialListRow take a required section prop — no default, so KnowledgePage owns the 'base' literal"
  - "C-12 uses the target h1 as its render barrier, not material-prose, because two material pages share that testid"
metrics:
  duration: 30min
  tasks_completed: 3
  files_touched: 9
  commits: 7
  completed: 2026-10-22
status: complete
actuals:
  tokens: 5722
  tasks: 3
  commits: 7
requirements-completed:
  - NAV-02
coverage:
  - id: D1
    description: "Every shell pill is announced correctly: own routes keep aria-current=page (C-15), a direct /issues/13 lights Архив (C-14), at most one pill is lit (C-20), and the paint differs only by the active pair (C-18)"
    requirement: "NAV-02"
    verification:
      - kind: e2e
        ref: "tests/web-app.spec.js#section pills: own routes keep aria-current=page (C-15)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section pills: archive -> issue lights Архив (C-08)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section pills: a direct /issues/13 lights Архив (C-14)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section pills: at most one lit pill (C-20)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section pills: the pill changes paint only, token-exact (C-18)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The origin marker survives four hops: archive -> issue -> material keeps Архив (C-09), current issue -> material lights Выпуск (C-10), knowledge -> material lights База (C-11), related materials keep the marker (C-12)"
    requirement: "NAV-02"
    verification:
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: archive -> issue -> material keeps Архив (C-09)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: current issue -> material lights Выпуск (C-10)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: knowledge -> material lights База (C-11)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: related materials keep the marker (C-12)"
        status: pass
    human_judgment: false
---

# Phase 26 Plan 02: Маркер раздела в шапке и стрелки происхождения — Summary

Читатель, ушедший из «Архива» в выпуск и дальше в материал (в том числе по связанному материалу), видит в шапке подсвеченным именно «Архив», а не «Выпуск»; то же доказано для текущего выпуска и для «Базы», а прямой заход на собственный маршрут по-прежнему даёт `aria-current="page"` и ровно один подсвеченный пилл.

## What shipped

| Файл | Что появилось |
|---|---|
| `web/src/components/AppShell.jsx` | `const section = state?.section`; три производных (`homeLit`/`archiveLit`/`baseLit`) и `current(ownRoute) => ownRoute ? 'page' : 'true'`. «Выпуск», «Архив», «База» переведены с `NavLink` на `<Link>` с вычисленным `aria-current` и тем же `linkClass({ isActive })`. |
| `web/src/pages/ArchivePage.jsx` | Карточка выпуска несёт `state={{ section: 'archive' }}`. |
| `web/src/components/IssueToc.jsx` | Обязательный проп `section` (без дефолта) → `state={{ section }}` на каждой ссылке содержания. |
| `web/src/pages/IssuePage.jsx` | `section={isCurrent ? 'issue' : 'archive'}` — выпуск сам решает, какой маркер он передаёт. |
| `web/src/components/MaterialListRow.jsx` | Обязательный проп `section` (без дефолта) → `state={{ section }}`. |
| `web/src/pages/KnowledgePage.jsx` | `section="base"` — литерал живёт в странице, а не в переиспользуемой строке. |
| `web/src/pages/MaterialPage.jsx` | `useLocation()` → `originState?.section`; связанные материалы получают `state={originSection ? { section: originSection } : undefined}` — слепое прокидование, без сравнения литералов. |
| `web/src/data/mock.js` | `sql-dashboards` получил `related: [{ slug: 'rag-systems', … }]` — фикстура для второй стрелки C-12. |
| `tests/web-app.spec.js` | `test.describe("section context — header pills (NAV-02)")` и `("section state (NAV-02)")`: хелперы `shellNav`, `sectionPill`, `classTokens`, `isLit`, `litCount` и девять критериев. Ни одна существующая строка не изменена. |

Сравнение трёх литералов существует ровно в одном файле — `AppShell.jsx` (C-17 держится структурно); `MaterialPage` только читает `originState?.section` и передаёт дальше, поэтому значение вне закрытого списка не зажигает ничего.

## Verification

| Проверка | Результат |
|---|---|
| `npx playwright test tests/web-app.spec.js --project=web -g "section pills\|section state"` | 9/9 passed |
| `npx playwright test tests/knowledge.spec.js --project=web` | 3/3 passed |
| `npx playwright test --project=web` (весь срез) | 177/177 passed (4.2m) |
| `npm run test:js` (все статические гейты, включая гейты 26-01) | 102/102 passed |
| `npm run build` | green (только пре-существующие предупреждения о размере чанка и `INEFFECTIVE_DYNAMIC_IMPORT`) |

## TDD Gate Compliance

- RED: `b7be3cc` (C-15 падает с `aria-current null` у «Архива» на `/issues/13`, C-08/C-14/C-20 следом, C-18 — пины состояний), `4190793` (C-09/C-10 — маркер не переживает переход в материал), `aae2e10` (C-11/C-12 — у «Базы» и у связанного материала `aria-current` отсутствует).
- GREEN: `2ce15aa` (три пилла), `aa46f45` (`IssueToc`), `edf1aaf` (`MaterialListRow` + `MaterialPage`).
- Тестовая инфраструктура: `587b4fc` — фикстура `related` и честный барьер для C-12 (см. отклонение 1).
- Ни один существующий ассерт не ослаблен и не удалён.

## Deviations from Plan

**1. [Rule 1 — bug] C-12 ждал не тот барьер отрисовки**
- **Found during:** task 3 (second hop)
- **Issue:** барьером стоял `expect(page.getByTestId("material-prose")).toBeVisible()`, но обе страницы материала имеют этот `data-testid`. Переход `sql-dashboards` → `rag-systems` удовлетворял барьер старой страницей, ассерт читал пилл ещё не перерисованной шапки и проходил ложно — на RED-стадии C-12 «зеленел» без производства.
- **Fix:** барьер заменён на уникальный заголовок целевой страницы — `getByRole("heading", { name: /building production rag systems/i, level: 1 })`. После этого C-12 упал по ожидаемой причине (`aria-current` = null) и позеленел только после слепого прокидования в `MaterialPage`.
- **Files modified:** `tests/web-app.spec.js`, `web/src/data/mock.js`
- **Verification:** C-12 red→green в общем прогоне 9/9; полный срез 177/177.
- **Committed in:** `587b4fc` (test), `edf1aaf` (production)

**2. [Rule 3 — blocking] `NavLink` не может объявить `aria-current` для неактивного маршрута**
- **Found during:** task 1
- **Issue:** план требует «Архив» с `aria-current` на `/issues/13`, но `NavLink` стирает явный `aria-current`, когда его собственный `to` неактивен, — состояние, пришедшее из `history.state`, объявить было нечем.
- **Fix:** три раздела переведены на `<Link>` с вычисленным `aria-current` (`page` только для собственного маршрута, `true` в остальных случаях); `linkClass({ isActive })` сохранён, поэтому краска не изменилась (C-18 держит токены).
- **Files modified:** `web/src/components/AppShell.jsx`
- **Verification:** C-08/C-14/C-15 зелёные, C-18 доказывает различие ровно парой активных токенов.
- **Committed in:** `2ce15aa`

---

**Total deviations:** 2 (1 bug, 1 blocking)
**Impact on plan:** Оба нужны для корректности: без первого C-12 давал ложный зелёный, без второго требование NAV-02 невыразимо средствами `NavLink`. Объём — те же файлы, что в `files_modified`.

## Issues Encountered

- Полный прогон `--project=web` запускался при свободном порту 5174 (проверка `Get-NetTCPConnection -LocalPort 5174 -State Listen` перед стартом) — 177/177 с первого раза.

## Accepted residuals (не чинятся в этой фазе)

| Полоса | Остаток | Причина |
|---|---|---|
| Прямой заход на `/materials/:id` | ни один пилл не подсвечен | честная деградация — C-13 и закрытый список (C-17) принадлежат 26-03 |
| Админ-раздел | пилл `adminActive` не затронут | C-16 принадлежит 26-03; правка `AppShell` его не касается |

## Known Stubs

Нет. Все производители передают реальный маркер, потребитель (`AppShell`) читает его из `history.state`; заглушек, пустых значений и TODO в изменённых файлах не появилось.

## Threat Flags

Нет. Новых сетевых путей, поверхностей аутентификации, доступа к файлам или изменений схемы не возникло: поверхность — атрибут `aria-current` и объект в `history.state`.

## Self-Check: PASSED

- `web/src/components/AppShell.jsx` — FOUND
- `web/src/components/IssueToc.jsx` — FOUND
- `web/src/components/MaterialListRow.jsx` — FOUND
- `web/src/pages/ArchivePage.jsx` — FOUND
- `web/src/pages/IssuePage.jsx` — FOUND
- `web/src/pages/KnowledgePage.jsx` — FOUND
- `web/src/pages/MaterialPage.jsx` — FOUND
- `web/src/data/mock.js` — FOUND
- `tests/web-app.spec.js` — FOUND
- Коммиты `b7be3cc`, `2ce15aa`, `4190793`, `aa46f45`, `aae2e10`, `587b4fc`, `edf1aaf` — FOUND
