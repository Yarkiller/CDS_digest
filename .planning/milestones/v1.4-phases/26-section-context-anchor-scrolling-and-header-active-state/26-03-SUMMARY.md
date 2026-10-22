---
phase: 26-section-context-anchor-scrolling-and-header-active-state
plan: 03
subsystem: web-frontend (navigation proofs + static gates)
tags: [nav-02, c-13, c-16, c-17, honest-degradation, playwright, static-gate, anti-vacuum]
requires:
  - phase: 26-01
    provides: "the global anchor offset, the extended fixtures and tests/unit/test_section_context_gates.js (C-19 gates + ROOT/read/count/sources helpers)"
  - phase: 26-02
    provides: "the three computed section pills, the origin marker in history.state.usr.section and the NAV-02 helpers (shellNav, sectionPill, classTokens, isLit)"
provides:
  - "tests/web-app.spec.js: C-13 (a direct material visit lights nothing) and the zero-heading pin"
  - "tests/admin.spec.js: C-16 (section pills stay dark on every admin path)"
  - "tests/unit/test_section_context_gates.js: describe NAV-02 marker is a closed list read at one point — six static gates for C-17"
  - "26-03-SUMMARY.md: the written C-17 static audit artefact the UI-SPEC demands"
affects:
  - 26 verification (criteria 5 ROADMAP, C-16, C-17 all closed by pins + one written artefact)
tech-stack:
  added: []
  patterns:
    - "a negative assertion is only honest when its node is proven visible first (toBeVisible before every aria-current === null)"
    - "token-exact class split, never a substring: bg-primary is a substring of bg-primary-solid"
    - "static gates assert the compared set, not literal presence — a comment can satisfy presence and hide a removed comparison"
    - "a pin that must not be vacuous proves the mechanism is alive on the same page (scrollPaddingTop > 0 on a zero-heading material)"
key-files:
  created: []
  modified:
    - tests/web-app.spec.js
    - tests/admin.spec.js
    - tests/unit/test_section_context_gates.js
decisions:
  - "C-13 asserts all five shell entries (Выпуск/Архив/База/Голосование/Разборы), each visible before the negative — an absent node must never produce the negative"
  - "The zero-heading pin additionally demands scrollPaddingTop >= measured header height + 1, so a page without anchors still proves the global offset is live"
  - "C-17 gate 2 asserts the set of values that reach a `===` in AppShell, because literal presence alone passed under mutation (the explanatory comment keeps all three strings)"
  - "The C-17 mutation proof was executed for real (three comparisons stripped, gates 2 and 3 reddened, file restored byte-identically) instead of only reasoned about"
metrics:
  duration: 12min
  tasks_completed: 3
  files_touched: 3
  commits: 3
  completed: 2026-10-22
status: complete
actuals:
  tokens: 2948
  tasks: 3
  commits: 3
requirements-completed:
  - NAV-02
coverage:
  - id: D1
    description: "Honest degradation: a fresh direct visit to /materials/rag-systems lights none of the five shell entries, and a heading-less material renders no «Содержание» while the global offset stays live"
    requirement: "NAV-02"
    verification:
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: a direct material visit lights nothing (C-13)"
        status: pass
      - kind: e2e
        ref: "tests/web-app.spec.js#section state: a heading-less material renders no Содержание (zero-heading case)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The admin route is untouched: on /admin/digest and the materials preview «Админ» stays aria-current=true + filled while the three sections are visible, unmarked and unfilled"
    requirement: "NAV-02"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#section pills stay dark on every admin path (C-16)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The origin marker is a closed list read at one point: one read in AppShell, all three literals compared there and only there, MaterialPage blind-forwards, and no file among the seven touches storage"
    requirement: "NAV-02"
    verification:
      - kind: unit
        ref: "tests/unit/test_section_context_gates.js#NAV-02 marker is a closed list read at one point (6 gates)"
        status: pass
      - kind: static-audit
        ref: "26-03-SUMMARY.md#C-17 static audit"
        status: pass
    human_judgment: false
---

# Phase 26 Plan 03: Доказательства — честная деградация, админ не задет, закрытый список письменно — Summary

Прямой заход на материал в свежем контексте не зажигает ни один из пяти пиллов шапки, материал без заголовков не рендерит «Содержание» при живом глобальном офсете, `/admin/*` не задевает ни один раздел, а закрытый список маркера доказан шестью статическими гейтами, которые реально краснеют под мутацией.

## What shipped

| Файл | Что появилось |
|---|---|
| `tests/web-app.spec.js` | Два пина в существующем describe `section context — header pills (NAV-02)`: `section state: a direct material visit lights nothing (C-13)` (пять пиллов, каждый сначала `toBeVisible`, затем `aria-current === null` и отсутствие заливки) и `section state: a heading-less material renders no Содержание (zero-heading case)` (`material-toc` count 0, `details` «Содержание» count 0, ноль `[id^="user-content-"]`, живой `scrollPaddingTop`). Хелперы `sectionPill` / `classTokens` / `isLit` переиспользованы — ни одного дубля, ни одной существующей строки не изменено. |
| `tests/admin.spec.js` | Один пин `section pills stay dark on every admin path (C-16)` **внутри** существующего describe `Admin nav grouping — in-page section switch` (после GAP-BACKSTOP-3), потому что `shellNav`/`shellAdminLink` определены именно там. Два пути: `/admin/digest` и `/admin/materials/sql-dashboards-for-audit-reporting`. «Админ» — положительная половина (`true` + `bg-primary-solid`), три раздела — отрицательная (видимы, без атрибута, без `bg-primary-solid`/`bg-primary`, сравнение по токенам). Нового `describe` нет. |
| `tests/unit/test_section_context_gates.js` | `describe('NAV-02 marker is a closed list read at one point')` с шестью гейтами C-17: одно чтение `state?.section`; все три литерала доходят до `===` в `AppShell` (anti-vacuum); ровно одна точка сравнения на всём `web/src`; blind-forward из `MaterialPage`; ноль `localStorage`/`sessionStorage`/`document.cookie` в семи файлах; обязательные пропы форвардеров и литералы у производителей. |

**`web/src` не тронут вообще** — `git diff --name-only 5fbb254..HEAD` возвращает ровно три тестовых файла. Это и есть доказательство, что 26-01/26-02 закрыли требование полностью.

## C-17 static audit

Обязательный письменный артефакт по UI-SPEC § C-17 (без него пункт выпадает из верификации).

1. **Где читается маркер.** `web/src/components/AppShell.jsx` — `const { pathname, state } = useLocation()`, затем `const section = state?.section` (строка 45). Это **единственная** точка чтения и единственная точка сравнения во всём `web/src`; гейт 1 требует `count(source, 'state?.section') === 1`, гейт 3 — что файлов, чей текст совпадает с `/===\s*'(archive|base|issue)'/`, ровно один, и это `AppShell.jsx`.
2. **Какие три литерала и что даёт сравнение.** Закрытый список — `'archive'`, `'base'`, `'issue'`. Сравнение даёт **булевы** `homeLit` / `archiveLit` / `baseLit` (`homeRoute || section === 'issue'`, `archiveRoute || issuesBranch || section === 'archive'`, `baseRoute || section === 'base'`), а не отрендеренное значение: маркер никогда не интерполируется в `className` или разметку, он только выбирает `aria-current` (`'page'` для собственного маршрута, `'true'` для заявленного) и `linkClass({ isActive })`. Гейт 2 требует, чтобы все три значения реально доходили до `===`, и чтобы `aria-current` и `linkClass` присутствовали.
3. **Вторая точка чтения только пересылает.** `web/src/pages/MaterialPage.jsx` — `const { state: originState } = useLocation()`, `const originSection = originState?.section`, далее `state={originSection ? { section: originSection } : undefined}` на связанных материалах. Ни одного сравнения: гейт 4 требует наличия `originState?.section` и `originSection ?` и отсутствия `/===\s*'(archive|base|issue)'/` — то есть blind forward, из-за которого значение вне закрытого списка деградирует в «ничего не зажжено», а не в ложный раздел.
4. **Происхождение не переживает прямой заход.** Ни в одном из семи затронутых файлов (`AppShell.jsx`, `IssueToc.jsx`, `MaterialListRow.jsx`, `ArchivePage.jsx`, `IssuePage.jsx`, `KnowledgePage.jsx`, `MaterialPage.jsx`) нет `localStorage`, `sessionStorage` или `document.cookie` — гейт 5 проверяет каждый из трёх токенов отдельно и в сообщении называет файл и токен. Поведенчески то же самое доказывает C-13: свежий контекст `page.goto('/materials/rag-systems')` не зажигает ничего.

**Как проверено:** `node --test tests/unit/test_section_context_gates.js` → `11 pass / 0 fail` (5 гейтов NAV-01 из 26-01 + 6 новых C-17). Плюс исполненная мутация: три сравнения в `AppShell.jsx` заменены на `homeRoute` / `archiveRoute || issuesBranch` / `baseRoute`, после чего гейт 2 упал с `compared none` (ожидалось `['archive','base','issue']`), а гейт 3 — с пустым списком точек сравнения; файл восстановлен (`git checkout --`, `git status` чист по `web/src`), гейты снова 11/11. Лог мутации использован как доказательство non-vacuum, а не как «мысленный эксперимент».

## Verification

| Проверка | Результат |
|---|---|
| `npx playwright test tests/web-app.spec.js --project=web -g "C-13\|zero-heading"` | 2/2 passed |
| `npx playwright test tests/web-app.spec.js --project=web -g "section pills\|section state"` | 11/11 passed (9 из 26-02 + 2 новых; положительные C-09/C-10/C-11 и пины C-08/C-14/C-15/C-18/C-20 не тронуты) |
| `npx playwright test tests/admin.spec.js --project=web -g "C-16"` | 1/1 passed |
| `npx playwright test tests/admin.spec.js --project=web -g "WR-02\|C-16"` | 2/2 passed — существующий WR-02 не ослаблен |
| `node --test tests/unit/test_section_context_gates.js` | 11/11 passed |
| `npm run test:js` | 108/108 passed (было 102 в 26-02, +6 гейтов C-17) |
| `npm run test:web` (весь срез) | 180/180 passed (4.2m; было 177, +2 web-app +1 admin) |
| `npm run build` | green; только пре-существующие предупреждения (размер чанка, `INEFFECTIVE_DYNAMIC_IMPORT`) |

Порт `5174` проверялся `Get-NetTCPConnection -LocalPort 5174 -State Listen` перед каждым Playwright-прогоном: 0 записей.

## TDD Gate Compliance

План — по своей природе **пины и статические доказательства**, и он сам фиксирует это: «RED-эпоха C-13/C-16/zero-heading — это 26-02». Ни один production-файл не менялся, поэтому RED-шаг здесь не мог быть «тест падает, затем фикс»: фикса нет.

Вместо имитации RED выполнены две честные проверки non-vacuum:

- **C-13 / C-16 / zero-heading** стоят рядом с положительными ассертами в тех же файлах (C-09/C-10/C-11/C-12 и WR-02) и требуют `toBeVisible` у каждого проверяемого узла, поэтому файл не может позеленеть при мёртвой шапке.
- **C-17** проверен настоящей мутацией (см. `## C-17 static audit`): гейты краснеют под удалением сравнений и зеленеют после восстановления.

Ни один существующий ассерт не ослаблен, не удалён и не переписан: `git diff` по трём коммитам — только добавления (50 / 37 / 144 строк, ноль удалений).

## Deviations from Plan

**1. [Rule 2 — correctness] Гейт 2 проверяет набор сравниваемых значений, а не только присутствие литералов**
- **Found during:** task 3 (мутационная проверка)
- **Issue:** план требует «текст `AppShell.jsx` содержит `'archive'`, `'base'`, `'issue'` (каждый ≥ 1 раз)». Это выполняется **объяснительным комментарием** над сравнениями (строки 41-44 перечисляют закрытый список), поэтому при удалении всех трёх сравнений проверка присутствия оставалась зелёной — гейт был бы вакуумным ровно в том сценарии, ради которого существует.
- **Fix:** добавлен ассерт на множество значений, реально доходящих до `===` (`matchAll(/===\s*'(archive|base|issue)'/g)`), — при мутации он падает с `compared none`. Проверка присутствия оставлена как документация закрытого списка.
- **Files modified:** `tests/unit/test_section_context_gates.js`
- **Verification:** мутация (три сравнения убраны) → гейт 2 `AssertionError: compared none`, гейт 3 → пустой список точек; восстановление → 11/11.
- **Committed in:** `5d4a76b`

**2. [Rule 2 — correctness] Zero-heading пин утверждает `scrollPaddingTop >= header.height + 1`, а не только `> 0`**
- **Found during:** task 1
- **Issue:** формулировка `toBeGreaterThan(0)` из `<action>` доказывает лишь «офсет не `auto`». Must-have truth плана требует «числом ≥ `header.height + 1`», иначе ноль якорей на странице мог бы «доказать» отсутствие офсета (T-26-09).
- **Fix:** обе претензии в тесте — `pad > 0` **и** `pad >= измеренная высота шапки + 1`; высота читается живым `getBoundingClientRect()`, литералов нет.
- **Files modified:** `tests/web-app.spec.js`
- **Verification:** на дефолтном viewport 1280×720 `pad = 80` при шапке ≈73 → обе претензии зелёные.
- **Committed in:** `83d601f`

**Total deviations:** 2 (обе — Rule 2, обе в тестах, ни одной production-правки).

## Issues Encountered

- Мутационная проверка гейтов выполнялась на живом `AppShell.jsx` с последующим `git checkout -- web/src/components/AppShell.jsx`; после восстановления `git status --short -- web/src` пуст, `node --test` снова 11/11. Никаких `git clean`/`git stash`/blanket-reset не применялось.
- Полный `--project=web` прогон запускался при свободном порту 5174 — 180/180 с первого раза, без перезапусков.

## Known Stubs

Нет. Изменения — только тесты и один статический гейт; ни одна новая поверхность не рендерит заглушку, ни одного `TODO`/`FIXME`/пустого значения в добавленных строках.

## Threat Flags

Нет. Никаких новых сетевых путей, поверхностей аутентификации, доступа к файлам или изменений схемы не появилось: поверхность — те же `aria-current`, `history.state` и `scroll-padding-top`. T-26-08 закрыт C-13 + гейтом 5, T-26-09 — симметрией негативных и положительных ассертов плюс живым офсетом на zero-heading странице, T-26-10 — гейтами 2-4 (литералы только сравниваются, единственная точка сравнения — `AppShell`), T-26-11 — проверкой порта перед каждым прогоном. T-26-SC неприменим: пакеты не устанавливались.

## Self-Check: PASSED

- `tests/web-app.spec.js` — FOUND (C-13 + zero-heading, 50 добавленных строк)
- `tests/admin.spec.js` — FOUND (C-16 внутри существующего describe, 37 добавленных строк)
- `tests/unit/test_section_context_gates.js` — FOUND (6 гейтов C-17, 144 добавленные строки)
- `web/src/**` — не изменён (`git diff --name-only 5fbb254..HEAD` = три тестовых файла)
- Коммиты `83d601f`, `a554b1c`, `5d4a76b` — FOUND
- `npm run test:js` 108/108, `npm run test:web` 180/180, `npm run build` green — CONFIRMED
