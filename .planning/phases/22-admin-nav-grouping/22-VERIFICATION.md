---
phase: 22-admin-nav-grouping
verified: 2026-10-17T11:06:00Z
status: human_needed
score: 11/14 must-haves verified
covered_files:
  - .planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md
  - .planning/phases/22-admin-nav-grouping/22-01-PLAN.md
  - .planning/phases/22-admin-nav-grouping/22-01-SUMMARY.md
  - .planning/phases/22-admin-nav-grouping/22-02-PLAN.md
  - .planning/phases/22-admin-nav-grouping/22-02-SUMMARY.md
  - tests/admin.spec.js
  - web/src/App.jsx
  - web/src/components/AdminLayout.jsx
  - web/src/components/AppShell.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
covered_digest: "v2:sha256:43ccd53e1aef73055c3525391fcf9a07cf8edc0d2c98f768572d3067602d4cdd"
behavior_unverified: 3
overrides_applied: 0
prohibitions:
  - statement: "MUST NOT add a second AppShell top-level item labelled Пайплайн (ADUX-12)."
    tier: judgment
    verdict: held
    evidence: "rg 'Пайплайн' в web/src/components/AppShell.jsx и web/src/App.jsx → 0 совпадений; shell содержит единственную admin-пилюлю «Админ» (AppShell.jsx:92-96)."
  - statement: "MUST NOT mark the section switch with ARIA tablist/tab/tabpanel roles (D-12)."
    tier: judgment
    verdict: held
    evidence: "AdminLayout.jsx использует nav aria-label + NavLink и native select; rg 'role=.?tab|tablist|tabpanel' по AdminLayout/AppShell → 0."
  - statement: "MUST NOT introduce an /admin index route or redirect (D-04)."
    tier: judgment
    verdict: held
    evidence: "App.jsx: pathless element <AdminLayout /> с детьми admin/digest и admin/pipeline; пути 'admin' или index нет, есть только catch-all '*' → '/'."
  - statement: "MUST NOT wrap admin/materials/:id under AdminLayout so preview gains the tab-bar (D-03, D-11)."
    tier: judgment
    verdict: held
    evidence: "App.jsx:44 — admin/materials/:id остаётся sibling-маршрутом; тест :167 подтверждает отсутствие admin-section-nav на preview при активной пилюле."
  - statement: "MUST NOT add a dirty-nav carve-out that lets tab or select leave skip UnsavedChangesDialog (D-13; Phase 19 D-04)."
    tier: judgment
    verdict: held
    evidence: "AdminLayout навигирует через NavLink и navigate(); тесты :1391 и :1430 проходят — диалог открывается на обоих путях ухода; carve-out в коде отсутствует."
  - statement: "MUST NOT rewrite Phase 19 modal copy or action labels (D-15)."
    tier: judgment
    verdict: held
    evidence: "Тесты сравнивают точную строку «Есть несохранённые изменения. Уйти без сохранения?» и testids unsaved-changes-stay/-leave; UnsavedChangesDialog не менялся в коммитах фазы."
  - statement: "MUST NOT expand 16-UI-SPEC rewrite into editor/toolbar contracts unrelated to A-2 / Route-nav."
    tier: judgment
    verdict: held
    evidence: "docs-коммит 202b72c: 16-UI-SPEC.md +9/−6; затронуты только шапка, строка A-2, строка Page H1 и блок Route/page/nav."
human_verification:
  - test: "Открыть /admin/digest и /admin/pipeline на ширине ~1280px, затем на границе sm (~640px)."
    expected: "Обе вкладки «Дайджест» / «Пайплайн» остаются на одной строке; горизонтального скролла страницы нет; активная вкладка подчёркнута accent-линией, inactive тише."
    why_human: "Автотест подтверждает только переключение брейкпоинта (nav vs select), но не однострочность и отсутствие overflow — это layout-суждение."
  - test: "Сузить окно ниже sm (<640px) на /admin/digest и /admin/pipeline."
    expected: "Native select «Разделы админки» полностью помещается в колонке контента, без горизонтального переполнения; смена опции переводит на соответствующий URL."
    why_human: "Проверка overflow/удобства контрола — визуальная; Playwright видит только видимость и value."
  - test: "На узкой ширине довести шапку AppShell до переноса строк и посмотреть на навигацию."
    expected: "Единственная пилюля «Админ» остаётся видимой; переключатель разделов читается как in-page underline-хром, а не как второй ряд пилюль."
    why_human: "Продуктово-визуальная оценка иерархии при wrap; автоматизация не различает «in-page» и «shell» визуально."
behavior_unverified_items:
  - truth: "At sm+ the two tab labels stay on one row without horizontal page scroll at 1280px and at the sm edge (~640px)"
    test: "Открыть /admin/digest и /admin/pipeline на 1280px и на ~640px"
    expected: "Одна строка вкладок, без горизонтального скролла страницы"
    why_human: "backstop-проба UI-SPEC: наличие тестid и видимость не доказывают отсутствие переноса/overflow"
  - truth: "Below sm the select remains fully usable within the content column without horizontal overflow"
    test: "Открыть /admin/digest ниже 640px и взаимодействовать с select"
    expected: "Select вписан в колонку, без горизонтального переполнения, опции переключают раздел"
    why_human: "backstop-проба UI-SPEC: Playwright проверяет видимость/значение, не геометрию"
  - truth: "Single «Админ» pill remains visible in the wrapping shell nav when the header wraps on narrow widths"
    test: "Сузить окно до переноса шапки AppShell"
    expected: "Пилюля «Админ» видна; переключатель разделов остаётся underline-хромом"
    why_human: "backstop-проба UI-SPEC: визуальная иерархия при wrap"
---

# Phase 22: Admin nav grouping — Verification Report

**Phase Goal:** The pipeline config surface is reached from the admin area rather than a second top-level nav item.
**Verified:** 2026-10-17T11:06:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ровно один AppShell-пункт «Админ» для admin, всегда ведущий на `/admin/digest`; primary nav landmark не содержит ссылок «Пайплайн» (ROADMAP SC1) | ✓ VERIFIED | `AppShell.jsx:92-96` — единственный admin-gated `NavLink to="/admin/digest"`; `rg "Пайплайн"` по `AppShell.jsx`/`App.jsx` → 0; тест `:1545` (запущен) и `:117` (запущен) зелёные |
| 2 | На `/admin/digest` и `/admin/pipeline` есть in-page переключатель «Разделы админки» с упорядоченными «Дайджест» → «Пайплайн» (underline NavLink на sm+, native select ниже sm); URL не изменены; `/admin` index не добавлен (ROADMAP SC2) | ✓ VERIFIED | `AdminLayout.jsx:33-57`; `App.jsx:38-45` — pathless `<AdminLayout />` без index; тест `:117` (запущен) проверяет aria-label, порядок, href и активную вкладку |
| 3 | 16-UI-SPEC A-2 больше не требует второго top-level shell-пункта «Пайплайн» (ROADMAP SC3) | ✓ VERIFIED | `16-UI-SPEC.md:19` (шапка superseded), `:30` (A-2 strikethrough + ADUX-12), `:190-193` (Route/nav переписан); «no second navigation bar» сохранён с обоснованием in-page |
| 4 | Падающий Playwright-тест существовал до изменения production-chrome (ROADMAP SC4, TDD) | ✓ VERIFIED | Коммит `4b62669 test(22-01)` предшествует `fed7b0b feat(22-01)`; в дереве `4b62669` `AppShell.jsx` ещё содержит shell-`NavLink` «Пайплайн», а тесты уже требуют `admin-section-nav`/`admin-section-select` → детерминированно RED; SUMMARY фиксирует прогон «5 failed … 59 passed» |
| 5 | Shell «Админ» визуально активен на digest, pipeline и materials-preview путях `/admin/*` (D-09, D-11) | ✓ VERIFIED | `AppShell.jsx:37` (`pathname === '/admin' || startsWith('/admin/')`); тесты `:148` и `:167` (запущены) проверяют `bg-accent` на `/admin/pipeline` и на preview |
| 6 | Page-level H1 «Shortlist дайджеста» / «Конфиг пайплайна» и дублирующий eyebrow удалены под AdminLayout (D-06, D-08) | ✓ VERIFIED | `rg "<h1"` по `web/src` → в `AdminDigestPage.jsx` и `AdminPipelineConfigPage.jsx` ни одного; `rg "Shortlist дайджеста\|Конфиг пайплайна\|Админ"` по страницам → 0; тесты `:206`/`:1097` требуют отсутствия заголовков |
| 7 | Adjacency: shell-landmark и section-landmark не сливаются — «Пайплайн» живёт только в переключателе разделов | ✓ VERIFIED | Два раздельных элемента: `nav aria-label="Основная навигация"` (AppShell) и `nav aria-label="Разделы админки"` (AdminLayout, внутри `main`); тест `:145` — 0 ссылок «Пайплайн» в shell |
| 8 | Cardinality: переключатель всегда имеет ровно два пункта (Дайджест, Пайплайн) | ✓ VERIFIED | Два литеральных `NavLink` (`AdminLayout.jsx:39-43`) и две литеральных `<option>` (`:55-56`); тест `:127` — `toHaveCount(2)` |
| 9 | Ordering: «Дайджест» предшествует «Пайплайну» и в nav-ряду, и в option-списке | ✓ VERIFIED | Порядок объявления в `AdminLayout.jsx`; тест `:128-129` проверяет nth(0)/nth(1); select-путь проверен тестом `:179` |
| 10 | Dirty YAML → клик in-page «Дайджест» открывает Phase 19 `UnsavedChangesDialog` с неизменной копией; «Остаться» сохраняет draft и URL, «Уйти без сохранения» ведёт на digest (D-13…D-15) | ✓ VERIFIED | Тест `:1391` (запущен, passed) — диалог, точная копия, `editor.toHaveValue(...)`, URL `/admin/pipeline` → `/admin/digest`, активные вкладки |
| 11 | Select ниже sm идёт тем же SPA-путём (`navigate()`), guard срабатывает, `document.location` не используется (D-19) | ✓ VERIFIED | `AdminLayout.jsx:53` `onChange={(e) => navigate(e.target.value)}`; тест `:1430` (запущен, passed) — диалог, «Остаться» сохраняет draft, «Уйти» ведёт на digest |
| 12 | Backstop: две вкладки на одной строке без горизонтального скролла на 1280px и на краю sm (~640px) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Разметка и брейкпоинт присутствуют (`sm:flex`), но layout-инвариант не покрыт тестом — см. Human Verification #1 |
| 13 | Backstop: select ниже sm полностью удобен в колонке контента без горизонтального overflow | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `w-full max-w-sm` + `sm:hidden` присутствуют; геометрия не проверяется автоматикой — см. Human Verification #2 |
| 14 | Backstop: единственная пилюля «Админ» видна при переносе шапки на узкой ширине | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Пилюля одна и в flex-wrap nav; видимость при wrap не проверяется автоматикой — см. Human Verification #3 |

**Score:** 11/14 truths verified (3 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/components/AdminLayout.jsx` | pathless layout: eyebrow «Админ», nav «Разделы админки» (testids `admin-section-nav`/`admin-tab-*`), select `admin-section-select`, `<Outlet />` | ✓ VERIFIED | 64 строки; всё перечисленное на месте; импортируется и используется в `App.jsx:40` |
| `web/src/components/AppShell.jsx` | один admin-gated «Админ» → `/admin/digest`, pathname-prefix active, shell-«Пайплайн» удалён | ✓ VERIFIED | `:37` adminActive, `:92-96` единственная ссылка; shell-«Пайплайн» отсутствует |
| `web/src/App.jsx` | pathless `AdminLayout` только для digest+pipeline; materials sibling; без `/admin` index | ✓ VERIFIED | `:38-45`; sibling `:44`; catch-all `:47` без admin-index |
| `web/src/pages/AdminDigestPage.jsx` | без page H1 / дубля eyebrow | ✓ VERIFIED | `<h1>` нет; `data-testid="admin-digest-page"` сохранён на всех ветках |
| `web/src/pages/AdminPipelineConfigPage.jsx` | без H1/eyebrow; hint и guard не тронуты | ✓ VERIFIED | `<h1>` нет; hint `:187/:198/:225`; `useUnsavedChangesGuard` `:107`; dialog `:331` |
| `tests/admin.spec.js` | shell-tripwires + section-nav/active-tab + H1-замены + dirty→tab journey | ✓ VERIFIED | `:108-196` (nav grouping), `:1391`/`:1430` (dirty), `:1545`/`:1563` (shell tripwires); 6 целевых тестов запущены и зелёные |
| `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` | A-2 + Route/nav superseded, указатель на 22-UI-SPEC | ✓ VERIFIED | `:19`, `:30`, `:140`, `:190-194`; посторонние editor/toolbar-контракты не тронуты |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `web/src/App.jsx` | `web/src/components/AdminLayout.jsx` | pathless `element: <AdminLayout />` с детьми digest+pipeline | WIRED | import `:3`, element `:40`, children `:42-43` |
| `web/src/components/AdminLayout.jsx` | `AdminDigestPage` / `AdminPipelineConfigPage` | `<Outlet />` | WIRED | `AdminLayout.jsx:60` |
| `web/src/components/AppShell.jsx` | `/admin/digest` | единственный `NavLink to="/admin/digest"` под `appRole === 'admin'` | WIRED | `:92-96`; тест `:67` и `:1545` |
| `tests/admin.spec.js` | `AdminLayout` / `AppShell` | landmark- и testid-scoped ассерты | WIRED | `admin-section-nav`, `admin-tab-*`, `admin-section-select`; «Пайплайн» в shell = 0 |
| `web/src/pages/AdminPipelineConfigPage.jsx` | `web/src/hooks/useUnsavedChangesGuard.js` | `useUnsavedChangesGuard(dirty)` + `UnsavedChangesDialog` | WIRED | `:107`, `:331`; поведение подтверждено тестами `:1391`, `:1430` |
| `16-UI-SPEC.md` | `22-UI-SPEC.md` | superseded-by указатель | WIRED | `16-UI-SPEC.md:19`, `:30`, `:190` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `AdminLayout.jsx` | `section` | `useLocation().pathname` (реальный router state) | Да — управляет `value` select и активной вкладкой | ✓ FLOWING |
| `AppShell.jsx` | `adminActive` | `useLocation().pathname` | Да — управляет `linkClass`/`bg-accent` | ✓ FLOWING |
| `AppShell.jsx` | `appRole` | `getAccessToken()` → `fetchMe()` (существующий session-флоу) | Да — гейтит единственный admin-пункт | ✓ FLOWING |
| `AdminLayout.jsx` | destinations (2 URL) | литеральные route-константы по контракту (D-10/D-17) | Н/Д — навигация, не данные; статичность здесь требование, не заглушка | ✓ VERIFIED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Section nav: aria-label, порядок, href, активная вкладка, shell без «Пайплайн» | `npx playwright test tests/admin.spec.js --project=web -g "admin-section nav lists"` | `ok 1 … (2.2s)` | ✓ PASS |
| Dirty → in-page «Дайджест»: диалог, «Остаться» (URL+draft), «Уйти» (digest) | `npx playwright test tests/admin.spec.js --project=web -g "dirty editor blocks in-page"` | `ok 2 … (2.3s)` | ✓ PASS |
| Клик по вкладке «Пайплайн» + активная shell-пилюля | `npx playwright test tests/admin.spec.js --project=web -g "admin-section pipeline tab navigates"` | `ok 1 … (2.0s)` | ✓ PASS |
| Materials preview: нет section switch, пилюля активна | `npx playwright test tests/admin.spec.js --project=web -g "materials preview while shell"` | `ok 2 … (2.0s)` | ✓ PASS |
| Ниже sm: nav скрыт, select виден и переключает раздел | `npx playwright test tests/admin.spec.js --project=web -g "narrow viewport swaps"` | `ok 3 … (1.8s)` | ✓ PASS |
| Dirty → narrow select: guard не обойдён | `npx playwright test tests/admin.spec.js --project=web -g "narrow section select leave"` | `ok 4 … (2.3s)` | ✓ PASS |

### Probe Execution

Не применимо: ни PLAN, ни SUMMARY фазы не объявляют probe-скриптов, и `scripts/*/tests/probe-*.sh` для этой фазы не задействованы (изменения — SPA-хром + Playwright + docs).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADUX-12 | 22-01, 22-02 | Один пункт «Админ» (→ `/admin/digest`) + in-page tab-bar «Дайджест \| Пайплайн»; `/admin/pipeline` без изменений; новый route не добавлен | ✓ SATISFIED | Truths #1–#2, #5–#11; `REQUIREMENTS.md:45` (описание совпадает), `:109` (Phase 22 = Complete) |

Осиротевших требований нет: `REQUIREMENTS.md` привязывает к Phase 22 только ADUX-12, и он заявлен в обоих PLAN-фронтматтерах.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web/src/components/AppShell.jsx` | 37 | `pathname === '/admin'` — недостижимая ветка (маршрута `/admin` нет, catch-all уводит на `/`) | ℹ️ Info | Мёртвое условие, поведение не ломает; IN-04 ревью |
| — | — | `TBD` / `FIXME` / `XXX` в изменённых файлах | — | Не найдено (`rg` по 5 изменённым файлам → 0) |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` / «coming soon» / «not implemented» | — | Не найдено. Совпадения `placeholder=` — это атрибуты `<textarea>`, а `return null` в `AdminDigestPage.jsx:78/266` — пре-существующие guard-хелперы, не render-заглушки |

### Классификация замечаний code review (WR-01 / WR-02)

Оба замечания **не нарушают ни один must_have** фазы и остаются качественной/accessibility-задолженностью вне зафиксированных решений.

| Finding | Что подтверждено независимо | Почему это не gap |
|---------|------------------------------|-------------------|
| **WR-01** повторный клик по уже активной вкладке при dirty-редакторе открывает диалог ухода | Код: `AdminLayout.jsx:39-44` — `NavLink` на текущий URL всё равно инициирует навигацию; `AdminPipelineConfigPage.jsx:107` — `useBlocker(Boolean(dirty))` без same-location исключения. Продуктовое поведение: лишний диалог, но draft/URL сохраняются | Ни один must_have не утверждает «диалога при клике по активной вкладке нет»; D-13/D-14 описывают уход, а запрет сформулирован в обратную сторону (MUST NOT ослаблять guard). Поведение ошибается в безопасную сторону — это UX-дефект, а не провал цели |
| **WR-02** shell-пилюля «Админ» на `/admin/pipeline` и `/admin/materials/:id` без `aria-current` | Код: `AppShell.jsx:92-93` — класс считается вручную из `adminActive`, а `aria-current` выставляет `NavLink` по совпадению с `to="/admin/digest"`; тесты проверяют только `bg-accent` | Must-have #5 и D-09/D-11 требуют **визуальной** активности на любом `/admin/*` — она есть (тесты `:148`, `:167` зелёные). Отсутствие `aria-current` — accessibility-долг, а не невыполненное требование |

Прочее из ревью: IN-01 (нет `h1` на admin-страницах) прямо санкционирован D-06/UI-SPEC; IN-02/IN-03 — качество тестов и покрытия; IN-04 — мёртвая ветка (Info). Все шесть записей остаются `open` в `22-REVIEW-DISPOSITION.md`, что соответствует их статусу «не блокирует verify».

### Суждение по ROADMAP criterion 4 (TDD)

Критерий удовлетворён Plan 22-01: тестовый коммит `4b62669` идёт до production-коммита `fed7b0b`, и в дереве `4b62669` shell всё ещё содержит `NavLink` «Пайплайн», тогда как тесты уже требуют `admin-section-nav`/`admin-section-select` — такой набор детерминированно падает. SUMMARY фиксирует наблюдённый RED (5 failed, ни одного `ERR_CONNECTION_REFUSED`/`0 passed`) и последующий GREEN.

Plan 22-02 дал GREEN-first (62/66 passed сразу): это **санкционированный планом characterization pin** — новый journey доказывает, что D-14/D-19 уже держатся после 22-01, и не требует искусственной production-правки. Критерий 4 говорит о падающем тесте «before the nav change»; nav change произошёл в 22-01 и был покрыт RED-first, поэтому 22-02 не ослабляет критерий.

### Human Verification Required

#### 1. Однострочность вкладок на 1280px и на краю sm (~640px)

**Test:** Открыть `/admin/digest` и `/admin/pipeline` на ширине ~1280px, затем на ~640px.
**Expected:** «Дайджест» и «Пайплайн» остаются на одной строке, горизонтального скролла страницы нет, активная вкладка подчёркнута accent-линией, inactive — тише.
**Why human:** Автотест ловит только переключение брейкпоинта; однострочность и отсутствие overflow — layout-суждение (backstop UI-SPEC E1).

#### 2. Usable select ниже sm без overflow

**Test:** Сузить окно ниже 640px на `/admin/digest`, открыть select «Разделы админки», переключить на «Пайплайн» и обратно.
**Expected:** Контрол полностью вписан в колонку контента, без горизонтального переполнения, переключение меняет раздел.
**Why human:** Playwright проверяет видимость и `value`, но не геометрию/удобство (backstop UI-SPEC E2).

#### 3. Одна пилюля «Админ» при переносе шапки

**Test:** На узкой ширине довести шапку AppShell до переноса строк.
**Expected:** Единственная пилюля «Админ» видна; переключатель разделов читается как in-page underline-хром, а не как второй ряд пилюль.
**Why human:** Визуально-продуктовая оценка иерархии при wrap (backstop UI-SPEC E3).

## Gaps Summary

Блокирующих пробелов нет: цель фазы достигнута в коде, все четыре ROADMAP success criteria подтверждены, ADUX-12 закрыт, запреты соблюдены. Три backstop-пробы UI-SPEC по определению требуют человеческого визуального подтверждения, поэтому статус — `human_needed`, а не `passed`. WR-01/WR-02 и info-находки ревью остаются открытым качественным долгом и не переводят фазу в `gaps_found`.

---

_Verified: 2026-10-17T11:06:00Z_
_Verifier: Claude (gsd-verifier)_
