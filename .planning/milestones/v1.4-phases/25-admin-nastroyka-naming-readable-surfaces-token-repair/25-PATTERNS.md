# Phase 25: Admin «Настройка» — naming, readable surfaces, token repair - Pattern Map

**Mapped:** 2026-10-21
**Files analyzed:** 13 (9 modified production/config, 3 new test artifacts, 1 test-amendment file)
**Analogs found:** 13 / 13 (3 of them partial — new files whose *class* of test does not exist yet)

**Как читать этот файл.** Фаза — ремонт, не функциональность. Почти все «новые» файлы на самом деле
новые **только как имена**: их содержание уже дважды написано в репозитории. Для каждого файла ниже
указан ближайший существующий аналог, конвенции которого надо копировать (импорты, стиль кавычек,
структура JSX/теста, сигнатуры ассертов), и точные выдержки с `file:line`.

**Важно про стиль репозитория — две разные конвенции, не путать:**

| Слой | Кавычки | Точка с запятой | Пример |
|---|---|---|---|
| `web/src/**/*.{js,jsx}` | одинарные | нет | `AdminLayout.jsx`, `ActionButton.jsx`, все страницы |
| `tests/*.spec.js` (Playwright) | двойные | да | `admin.spec.js:1`, `web-app.spec.js:1` |
| `tests/unit/*.js` (node:test) | одинарные | нет | `test_concept2_canon.js:17-21` |
| `playwright.config.js` | двойные | да | `playwright.config.js:1-2` |
| `tests/unit/helpers/*.js` | одинарные | нет, JSDoc-типы | `cssRules.js:20-23` |

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/index.css` | config (design tokens) | transform (CSS cascade) | сам файл: `@theme static` 7-68 + `[data-theme="light"]` 106-121 | exact (self) |
| `web/src/components/AdminLayout.jsx` | component (chrome) | request-response (route links) | сам файл + `AppShell.jsx` `linkClass` | exact (self) |
| `web/src/components/IngestSourcesSection.jsx` | component (form + list) | CRUD | сам файл (заголовок :169-173, `<select>` :268-276, CTA :306-312) | exact (self) |
| `web/src/components/AppShell.jsx` | component (nav) | request-response | сам файл `linkClass` :11-15 + `ActionButton.jsx` массив строк | exact (self) |
| `web/src/components/ActionButton.jsx` | component (primitive) | event-driven (state) | сам файл `stateClass`/`variantClass` :1-24 | exact (self) |
| `web/src/components/UnsavedChangesDialog.jsx` | component (modal) | event-driven | сам файл :24-58 | exact (self) |
| `web/src/components/ServiceUnavailable.jsx` | component (error splash) | request-response | `AdminPipelineConfigPage.jsx:303-311` (тот же `bg-accent`) | role-match |
| `web/src/pages/{Login,Register,Knowledge,AdminDigest,AdminPipelineConfig}Page.jsx` | component (page CTA) | request-response | `IngestSourcesSection.jsx:308` (accent) / `ServiceUnavailable.jsx:38` (primary) | exact (одна строка класса) |
| `playwright.config.js` | config (test runner) | — | сам файл `projects[].testMatch` :65-79 | exact (self) |
| `tests/admin-chrome.spec.js` | test (e2e, computed style) | request-response + batch (двойной прогон тем) | `tests/admin.spec.js` (harness) + `tests/web-app.spec.js` (тема/voting) | role-match (нет спека с dual-theme циклом) |
| `tests/helpers/contrast.js` | utility (shared, CJS) | transform (WCAG) | `tests/unit/helpers/cssRules.js` | role-match (нет helper'а в `tests/helpers/`) |
| `tests/unit/test_semantic_token_coverage.js` | test (node:test, CSS-контракт) | batch (скан дерева) | `tests/unit/test_concept2_canon.js` (`parseBlock`) + `test_design_typography.js` | role-match (скан `web/src/**` — новый приём) |
| `tests/admin.spec.js` | test (amendment) | request-response | сам файл | exact (self) |

**TDD-роль каждого файла** (правило `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`):

| Файл | Роль в цикле |
|---|---|
| `playwright.config.js` | **Wave 0 — разрешённое исключение** (`tdd.mdc`: конфиги). Без него RED не существует физически. |
| `tests/helpers/contrast.js` | **RED-инфраструктура** (падает на `rgba(0,0,0,0)` по конструкции) |
| `tests/unit/test_semantic_token_coverage.js` | **RED** (G-1…G-8) |
| `tests/admin-chrome.spec.js` | **RED** (критерии 1, 2, 4, 5) |
| `tests/admin.spec.js` | **RED** (амендменты — часть RED-шага, не «после факта») |
| `web/src/index.css` | **GREEN** (первым, после RED) |
| `AdminLayout.jsx`, `IngestSourcesSection.jsx`, `AppShell.jsx`, `ActionButton.jsx`, `UnsavedChangesDialog.jsx`, `ServiceUnavailable.jsx`, страницы | **GREEN** (после `index.css`) |

---

## Pattern Assignments

### `web/src/index.css` (config, transform)

**Analog:** сам файл. Новое объявление обязано лечь **внутрь существующих** блоков — второго
`@theme`/`[data-theme="light"]` создавать нельзя (`parseBlock` в канон-тесте берёт только первое
вхождение, `test_concept2_canon.js:31-39`).

**Открытие `@theme static` и первые токены** (`web/src/index.css:4-8`):

```css
/* Concept 2 tokens — dark-first, light via [data-theme="light"] (ADR-0009).
   `static` keeps tokens that no utility happens to consume: they are a design-system
   contract that must exist in :root at runtime, not only when Tailwind finds a user. */
@theme static {
  --color-bg-app: #0B0F17;
  --color-bg-surface: #131925;
```

**Commented-group idiom, который надо повторить** (`web/src/index.css:39-40` — образец комментария
над группой токенов):

```css
  /* Scales carried for parity with design-frontend/styles/tokens.css. Concept 2 pages
     use the Tailwind default scale directly, but the canon scale is still a contract. */
```

**Источник значения `primary-solid`** (`web/src/index.css:19`):

```css
  --color-primary-hover: #7C3AED;
```

**Rgba-токен — существующий прецедент для `--color-scrim`** (`web/src/index.css:12`):

```css
  --color-bg-glass: rgba(19, 25, 37, 0.72);
```

**Слой light-темы, куда дописываются шесть override'ов** (`web/src/index.css:106-121`):

```css
  [data-theme="light"] {
    --color-bg-app: #F8FAFC;
    --color-bg-surface: #FFFFFF;
    --color-bg-elevated: #F1F5F9;
    --color-bg-muted: #E2E8F0;
    --color-bg-glass: rgba(255, 255, 255, 0.85);
    --color-text-primary: #0F172A;
    --color-text-secondary: #64748B;
    --color-text-disabled: #94A3B8;
    --color-border: #E2E8F0;
    --color-border-glow: rgba(139, 92, 246, 0.2);
    --color-xp-text: #1A2E05;
    --shadow-md: 0 0 0 1px var(--color-border), 0 4px 24px rgba(15, 23, 42, 0.08);
    --shadow-glow: 0 0 0 1px var(--color-border-glow), 0 0 20px rgba(139, 92, 246, 0.08);
  }
```

**Ограничения, которые следуют из аналога:**
- Канон-тест проверяет **канон → продакшн** (`test_concept2_canon.js:57-69`), поэтому *добавление*
  новых токенов в `@theme` его не ломает; *удаление* или *изменение* существующих — ломает.
- `@theme` не поддерживает вложенность селекторов (Tailwind v4) — light-override обязан остаться
  правилом в `@layer base`, как сейчас.
- Значения берутся из `25-UI-SPEC.md` § Token contract A/B **дословно** (нормативны, не пере-выводить):
  dark `paper #131925`, `paper-2 #1A2233`, `ink #F1F5F9`, `ink-2 #CBD5E1`, `muted #94A3B8`, `rule #2A3548`;
  light `#FFFFFF`, `#F1F5F9`, `#0F172A`, `#334155`, `#475569`, `#CBD5E1`; плоские `primary-solid #7C3AED`,
  `accent-solid #0E7490`, `success-solid #15803D`, `danger-solid #DC2626`, `on-solid #FFFFFF`,
  `voting-ink #0F172A`, `scrim rgba(0, 0, 0, 0.6)`.

---

### `web/src/components/AdminLayout.jsx` (component, request-response)

**Analog:** сам файл. `tabClass` уже собран массивом строк + `.join(' ')` — миграция это замена одной
строки в массиве, **не** рефакторинг компонента (`web/src/components/AdminLayout.jsx:8-18`):

```jsx
/**
 * Underline in-page section switch (D-05): no pill fill, no ARIA tab roles (D-12) —
 * these destinations are routes. The active tab carries the former page H1 weight
 * (D-08) so hierarchy survives the D-06 H1 removal.
 */
function tabClass({ isActive }) {
  return [
    'inline-flex min-h-11 items-end border-b-2 pb-2 text-3xl',
    isActive
      ? 'border-accent font-semibold text-ink'
      : 'border-transparent font-normal text-muted hover:text-ink',
  ].join(' ')
}
```

**Удаляемый eyebrow + сохраняемый sr-only `h1`** (`:40-49`):

```jsx
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>

      {/*
        IN-01: the outline must not start at h2, but D-06 forbids a visible page title —
        so the section name lives in a visually hidden h1. The layout wraps every child
        branch (ready/loading/error/forbidden), so each one inherits this heading.
      */}
      <h1 className="sr-only">{section === PIPELINE_PATH ? 'Пайплайн' : 'Дайджест'}</h1>
```

**Nav + три литерала** (`:51-84`) — здесь меняются только текст, `gap`, `mt`, `text-2xl`,
`focus-visible:outline-primary`:

```jsx
      <nav
        className="mt-2 hidden gap-2 border-b border-rule sm:flex"
        aria-label="Разделы админки"
        data-testid="admin-section-nav"
      >
```

```jsx
      <select
        aria-label="Разделы админки"
        data-testid="admin-section-select"
        className="mt-2 min-h-11 w-full max-w-sm rounded-xl border border-rule bg-paper px-3 text-base text-ink focus-visible:outline-accent sm:hidden"
```

**Do-not-touch (байт-идентично):** `DIGEST_PATH`/`PIPELINE_PATH` (`:3-4`), `handleSectionTabClick`
(`:36-38`), `aria-label`, все `data-testid`, `onChange={(event) => navigate(event.target.value)}` (`:80`),
`<div className="mt-6"><Outlet /></div>` (`:86-88`).

**`focus-visible:outline-primary` — не новый идиом**, тот же класс уже стоит в
`web/src/pages/AdminPipelineConfigPage.jsx:387` (проверено грепом по `outline-primary`).

**Целевой `tabClass`** (UI-SPEC § Admin Chrome Contract, нормативно):

```jsx
function tabClass({ isActive }) {
  return [
    'inline-flex min-h-11 items-end border-b-2 pb-2 text-2xl focus-visible:outline-primary',
    isActive
      ? 'border-accent font-semibold text-ink'
      : 'border-transparent font-normal text-muted hover:text-ink',
  ].join(' ')
}
```

---

### `web/src/components/IngestSourcesSection.jsx` (component, CRUD)

**Analog:** сам файл. Три точки правки — заголовок, подложки рядов/формы, accent-CTA.

**Заголовок блока** (`:169-174`) — PIPEUI-03 меняет **только текст**:

```jsx
      <h2
        data-testid="ingest-sources-heading"
        className="font-sans text-2xl font-semibold text-ink"
      >
        Источники ингеста
      </h2>
```

**Row surface (первый `bg-paper-2/40`)** (`:216-220`):

```jsx
              <li
                key={row.id}
                data-testid="ingest-source-row"
                className="rounded-xl border border-rule bg-paper-2/40 p-3"
              >
```

**Form sub-panel + `<select>` «Тип»** (`:264-277`) — это **тот самый** нечитаемый контрол
(критерий 2):

```jsx
      <div className="mt-6 space-y-3 rounded-xl bg-paper-2/40 p-4">
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs font-semibold text-ink-2">
            Тип
            <select
              data-testid="ingest-sources-kind"
              className="min-h-11 rounded-xl border border-rule bg-paper px-3 text-base font-normal text-ink-2 focus-visible:outline-accent"
              value={kind || 'channel'}
              disabled={adding}
              onChange={(e) => onKindChange?.(e.target.value)}
            >
              <option value="channel">Канал</option>
              <option value="playlist">Плейлист</option>
            </select>
          </label>
```

**Accent CTA** (`:306-312`) — эталон для всех трёх `bg-accent`-миграций:

```jsx
          <button
            type="button"
            data-testid="ingest-sources-add"
            className="inline-flex min-h-11 items-center justify-center rounded-full bg-accent px-5 text-sm font-medium text-accent-ink disabled:cursor-not-allowed disabled:opacity-45"
            disabled={!canAdd}
            onClick={onAdd}
          >
            Добавить источник
          </button>
```

**Не трогать в этом файле:** `outline-accent` на полях (`:270`, `:286`, `:299` — known defect 3),
`text-[oklch(...)]`-ошибки (`:235`, `:251`, `:333-361`), `border border-rule` на кнопках рядов
(`:229`, `:247` — они станут нарисованными, это ожидаемо), все копирайт-строки.

---

### `web/src/components/AppShell.jsx` (component, request-response)

**Analog:** сам файл `linkClass` (`web/src/components/AppShell.jsx:11-15`) — правка ровно одной ветки:

```jsx
const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-2.5 text-sm',
    isActive ? 'bg-primary text-text-primary' : 'text-text-secondary hover:bg-bg-surface',
  ].join(' ')
```

**Единственный потребитель ветки `isActive`** (`:93-104`) — `Link`, не `NavLink`, потому что
`aria-current` вычисляется из префикса:

```jsx
            {appRole === 'admin' ? (
              <Link
                to="/admin/digest"
                // WR-02: NavLink derives aria-current from `to="/admin/digest"`, so the pill
                // was announced as inactive on pipeline/preview while looking active. Set it
                // from the already-computed prefix instead — "true" (not "page") because the
                // href targets digest while the whole admin section is the current context.
                aria-current={adminActive ? 'true' : undefined}
                className={linkClass({ isActive: adminActive })}
              >
                Админ
              </Link>
            ) : null}
```

**КРИТИЧНО (найдено чтением, отсутствует в RESEARCH):** `tests/unit/test_concept2_canon.js:154-169`
требует, чтобы в `AppShell.jsx` **оставались** литералы `bg-bg-app`, `text-text-primary`,
`border-border`. Они живут на корневом `<div>` (`:66`) и в `<main>`; миграция `linkClass` их не
задевает. **Если исполнитель «вычистит» `text-text-primary` из `AppShell` целиком — канон-тест
упадёт.** Менять только строку `isActive`-ветки.

```jsx
    <div className="min-h-svh bg-bg-app text-text-primary">
```

---

### `web/src/components/ActionButton.jsx` (component, event-driven)

**Analog:** сам файл — две таблицы строк (`:1-6`, `:16-22`) + сборка className (`:26-34`):

```jsx
const stateClass = {
  idle: '',
  loading: 'cursor-wait opacity-80',
  error: 'bg-danger text-text-primary',
  success: 'bg-success text-text-primary',
}
```

```jsx
  const variantClass =
    variant === 'voting'
      ? 'bg-voting text-bg-app'
      : variant === 'secondary'
        ? 'border border-border bg-transparent text-primary'
        : 'bg-primary text-text-primary'
```

```jsx
      className={[
        'inline-flex min-h-11 items-center justify-center rounded-full px-4 text-sm font-medium transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-55',
        variantClass,
        stateClass[state] ?? '',
        className,
      ].join(' ')}
```

**Правило:** `variant === 'secondary'` и `'border border-border bg-transparent text-primary'`
(`:20`) **не меняются** (D-05). Меняются ровно 4 строки: `error`, `success` (`:4-5`), `voting` (`:18`),
`else`-ветка (`:21`). `data-state`-контракт (`:27`) не трогается.

---

### `web/src/components/UnsavedChangesDialog.jsx` (component, modal)

**Analog:** сам файл. Скрайм и accent-кнопка — две отдельные строки (`:24-31`, `:49-57`):

```jsx
    <div
      className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="unsaved-changes-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-paper p-6">
```

```jsx
          <button
            type="button"
            data-testid="unsaved-changes-leave"
            className="inline-flex min-h-11 items-center justify-center rounded-full bg-accent px-4 text-sm font-medium text-accent-ink"
            onClick={onLeave}
          >
            Уйти без сохранения
          </button>
```

**Не трогать:** `UNSAVED_LEAVE_CONFIRM` (`:2`, `:39`), Esc-обработчик (`:11-21`), `data-testid`
`unsaved-changes-message`/`-stay`/`-leave`. Копирайт тела запинен `tests/admin.spec.js:242`.

---

### `web/src/components/ServiceUnavailable.jsx` (component, error splash)

**Analog:** `web/src/pages/AdminPipelineConfigPage.jsx:303-311` по форме класса; сама кнопка —
`ServiceUnavailable.jsx:36-42`:

```jsx
      <button
        type="button"
        className="mt-6 inline-flex min-h-11 items-center justify-center rounded-full bg-primary px-5 text-sm font-medium text-text-primary disabled:cursor-wait disabled:opacity-60"
        disabled={busy}
        aria-busy={busy}
        onClick={handleRetry}
      >
        {busy ? 'Загрузка…' : 'Повторить'}
      </button>
```

Меняется подстрока `bg-primary` → `bg-primary-solid` и `text-text-primary` → `text-on-solid`;
`disabled:cursor-wait` и `aria-busy` — часть контракта загрузки (UI-SPEC E6), не трогать.

---

### `web/src/pages/*.jsx` — миграции CTA (5 файлов, 8 строк)

Все восемь строк — один и тот же паттерн «одна строка класса в массиве/атрибуте». Точные места
(проверено грепом `bg-primary |bg-accent |bg-success |bg-danger |bg-voting`):

| Файл:line | Сегодня | Цель |
|---|---|---|
| `LoginPage.jsx:126` | `min-h-11 self-start rounded-full bg-primary px-4 text-sm text-text-primary` | `bg-primary-solid` + `text-on-solid` |
| `LoginPage.jsx:198` | `min-h-11 w-full rounded-full bg-primary px-4 text-sm font-medium text-text-primary disabled:opacity-60` | то же |
| `RegisterPage.jsx:107` | как `LoginPage.jsx:126` | то же |
| `RegisterPage.jsx:210` | как `LoginPage.jsx:198` | то же |
| `KnowledgePage.jsx:278` | `? 'min-h-11 rounded-full bg-primary px-3 text-sm text-text-primary'` | то же |
| `AdminDigestPage.jsx:794` | `... rounded-full bg-success px-4 text-sm font-medium text-text-primary disabled:cursor-not-allowed disabled:opacity-45 sm:w-auto` | `bg-success-solid` + `text-on-solid` |
| `AdminDigestPage.jsx:919` | `... rounded-full bg-success px-4 text-sm font-medium text-text-primary disabled:opacity-55` | то же |
| `AdminPipelineConfigPage.jsx:305` | `... rounded-full bg-accent px-5 text-sm font-medium text-accent-ink disabled:cursor-not-allowed disabled:opacity-45` | `bg-accent-solid` + `text-on-solid` |

**Скраймы (4 строки):** `UnsavedChangesDialog.jsx:26` (`bg-ink/40`), `AdminDigestPage.jsx:821`,
`:885`, `:948` (`bg-text-primary/40`) → `bg-scrim`. Идентичные строки, различаются только
`data-testid`-контекстом вокруг — замена подстроки, не структуры.

**Эталон строки** — `AdminDigestPage.jsx:792-797`:

```jsx
              <button
                type="button"
                className="inline-flex min-h-11 w-full items-center justify-center rounded-full bg-success px-4 text-sm font-medium text-text-primary disabled:cursor-not-allowed disabled:opacity-45 sm:w-auto"
                disabled={restMode || !sendUnlocked || sending}
                onClick={() => setConfirmOpen(true)}
              >
                Отправить дайджест →
```

**Не трогать:** `AdminDigestPage.jsx:808` (toast, known defect 1), `:717-718` (тинт-чипы, D-12),
`AdminPipelineConfigPage.jsx:333,362` (`border-danger`/`bg-danger/10`), `MaterialPage.jsx:187`
(читательский callout — станет нарисованным, это принято), `TopicBallot.jsx:26`, `VotingPage.jsx:448`
(`<div className="h-full bg-voting" />` — полоса прогресса без текста).

---

### `playwright.config.js` (config, test runner)

**Analog:** сам файл (`:60-79`). Правка — **одна регулярка**, разрешённое TDD-исключение:

```js
module.exports = defineConfig({
  testDir: "./tests",
  use: {
    headless: true,
  },
  projects: [
    {
      name: "design-frontend",
      testMatch: /design-frontend\.spec\.js/,
      use: { baseURL: "http://127.0.0.1:8765" },
    },
    {
      name: "web",
      testMatch: /(web-app|auth|knowledge|razbory|admin)\.spec\.js/,
      use: { baseURL: "http://127.0.0.1:5174" },
    },
  ],
  webServer: webServers,
});
```

**Конвенции, которые нельзя ломать:**
- `baseURL` для `web` = `http://127.0.0.1:5174`; `storageState` не используется нигде.
- `webServer.env` жёстко ставит `VITE_USE_MOCKS: "true"` (`:50-55`), но `reuseExistingServer:
  !process.env.CI` (`:47`) может подхватить живой Vite с `VITE_USE_MOCKS=false` из `web/.env.local`
  (Pitfall 8). Перед прогоном — проверить порт.
- Минимальная правка: `/(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/`.
  Проверка — `npx playwright test --list --project=web` **обязана** назвать `admin-chrome`.

---

### `tests/admin-chrome.spec.js` (test, e2e computed style) — NEW

Файла нет. Два аналога, оба обязательны:

**Аналог 1 — харнесс роли и сброс моков:** `tests/admin.spec.js:22-50`.

```js
async function gotoAsRole(page, role, path = "/", extraInit) {
  await page.addInitScript(
    ({ r, extra }) => {
      window.__DIGEST_MOCK_ME_ROLE__ = r;
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    },
    { r: role, extra: extraInit ?? null },
  );
  await page.goto(path);
  // Reset module-level admin mocks between tests (Vite keeps singleton state).
  if (path.startsWith("/admin")) {
    await page.waitForFunction(() => Boolean(window.__DIGEST_ADMIN_HARNESS__));
    await page.evaluate((extra) => {
      window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness();
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    }, extraInit ?? null);
    await page.reload();
  }
}
```

Заголовок файла и импорты — `tests/admin.spec.js:1-2`:

```js
const { expect, test } = require("@playwright/test");
const path = require("node:path");
```

**Аналог 2 — тема через `addInitScript` + чтение токена из DOM:**
`tests/web-app.spec.js:631-637` (это **единственное** место в репозитории, где тема ставится
до загрузки — RESEARCH ошибочно приписывает его `admin.spec.js:633-636`, там лежит обработчик
`page.once("dialog", …)`):

```js
  test("regenerates the same evidence in the light theme", async ({ page }) => {
    // ADR-0009: the light layer is a contract, so evidence in one theme proves nothing.
    await page.addInitScript(() => {
      try {
        localStorage.setItem("digest-cds-theme", "light");
      } catch {}
    });
```

и `tests/web-app.spec.js:49-53` — форма чтения кастомного свойства:

```js
    const bgToken = () =>
      page.evaluate(() =>
        getComputedStyle(document.documentElement).getPropertyValue("--color-bg-app").trim(),
      );
```

**Аналог 3 — `/voting` fixture** (`tests/web-app.spec.js:288-291`): `confirm-vote` — это
`ActionButton` (default `variant="voting"`), disabled до выбора радио:

```js
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await expect(confirm).toBeEnabled();
    await confirm.click();
```

**Аналог 4 — геометрия с ожиданием шрифтов** (`tests/admin.spec.js:379-394`):

```js
    await page.evaluate(() => document.fonts.ready);

    const nav = shellNav(page);
    const navBox = await nav.boundingBox();
```

**Скелет, который надо собрать из этих аналогов** (структура — новая, каждый приём скопирован):

```js
const { expect, test } = require("@playwright/test");

const ADMIN_PATHS = { digest: "/admin/digest", pipeline: "/admin/pipeline" };

/** Тема ставится ДО загрузки: ThemeToggle читает ключ в useEffect. */
async function gotoAdmin(page, path, theme) {
  await page.addInitScript((t) => {
    window.__DIGEST_MOCK_ME_ROLE__ = "admin";
    if (t === "light") localStorage.setItem("digest-cds-theme", "light");
    else localStorage.removeItem("digest-cds-theme");
  }, theme);
  await page.goto(path);
  await page.evaluate(() => document.fonts.ready);
}

/** Пара color/background уходит в Node-контекст — формула контраста одна. */
function stylePair(locator) {
  return locator.evaluate((el) => {
    const cs = getComputedStyle(el);
    return { color: cs.color, background: cs.backgroundColor, fontSize: cs.fontSize };
  });
}

/** Токен-точный ассерт: подстрока `bg-primary` совпадает внутри `bg-primary-solid`. */
async function classTokens(locator) {
  return (await locator.getAttribute("class")).split(/\s+/).filter(Boolean);
}
```

Требования к содержимому (из UI-SPEC § Proof Map):
- критерий 1 — три поверхности + `page.url()` + `data-testid` неизменны, оба темы не нужны;
- критерий 2 — `background-color` **равен** `rgb(19, 25, 37)` / `rgb(255, 255, 255)` (не «не белый»),
  `color` = `rgb(203, 213, 225)` / `rgb(51, 65, 85)`, три контрола, обе темы;
- критерий 4 — три пары, обе темы, `contrastRatio(...) >= 4.5`, `voting` — **положительный** ассерт;
- критерий 5 — `getByText('Админ', { exact: true })` count 1, `font-size` вкладки === `font-size`
  заголовка, `column-gap` 16px, `margin-top` 0, `nav.top − main.top < 48`, текст заголовка.

---

### `tests/helpers/contrast.js` (utility, shared CJS) — NEW

Ни `tests/helpers/`, ни файла нет. **Аналог по форме и стилю:** `tests/unit/helpers/cssRules.js`.
Копировать: docstring-шапку с объяснением «зачем», JSDoc-типы, `module.exports = { … }` в конце,
одинарные кавычки без точек с запятой.

**Аналог (шапка + JSDoc + экспорт)** (`tests/unit/helpers/cssRules.js:1-9`, `:20-24`, `:82`):

```js
/**
 * Shared CSS rule parser for the Concept 3 design-parity tests.
 *
 * Flattens a stylesheet into `selector -> sorted declaration list`. At-rules that
 * merely wrap rules (`@layer`, `@media`, `@supports`) are descended into, so a rule
 * declared inside `@layer base` or a media query is found by its selector. Repeated
 * selectors are merged, which is what the CSS cascade would resolve to.
 */
```

```js
/**
 * @param {string} css raw stylesheet text
 * @returns {Map<string, string[]>}
 */
function parseRules(css) {
```

```js
module.exports = { parseRules, declarationsOf }
```

**Почему `tests/helpers/` безопасен (проверено чтением, не предположением):**
`scripts/run-unit-js.cjs:13-17` делает **нерекурсивный** `readdirSync(tests/unit)`, поэтому
`tests/unit/helpers/` и `tests/helpers/` не исполняются как тесты; Playwright `testMatch`
(`playwright.config.js:71`) матчит только `*.spec.js`. Файл-helper не попадёт ни в один раннер.
Строка 72 рядом — это `use: { baseURL: "http://127.0.0.1:5174" }`, её править нельзя.

**Функциональное требование** (UI-SPEC/Validation): `relativeLuminance` **бросает** на `a < 1` —
это делает Pitfall 2 («контраст на прозрачном фоне») невозможным по конструкции.

---

### `tests/unit/test_semantic_token_coverage.js` (test, node:test CSS-контракт) — NEW

Файла нет. **Аналог 1 (структура и `parseBlock`):** `tests/unit/test_concept2_canon.js`.
Файл-аналог трогать запрещено — `parseBlock` не экспортируется, поэтому копируется локально.

**Импорты и константы** (`test_concept2_canon.js:17-25`):

```js
const assert = require('node:assert/strict')
const { existsSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')
const exists = (relativePath) => existsSync(path.join(ROOT, relativePath))
```

**`parseBlock` — копируется как есть** (`test_concept2_canon.js:30-39`):

```js
/** Tokens of one CSS block, matched by the selector head that opens it. */
function parseBlock(css, headPattern) {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, '')
  const match = new RegExp(`${headPattern}\\s*\\{([\\s\\S]*?)\\n\\}`, 'm').exec(withoutComments)
  const tokens = new Map()
  if (!match) return tokens
  for (const declaration of match[1].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    tokens.set(declaration[1], declaration[2].trim())
  }
  return tokens
}
```

**Wiring двух слоёв** (`test_concept2_canon.js:44-46`) — те же head-паттерны:

```js
const productionCss = read('web/src/index.css')
const productionDark = parseBlock(productionCss, '@theme(?:\\s+static)?')
const productionLight = parseBlock(productionCss, '\\[data-theme="light"\\]')
```

**Стиль ассертов `describe`/`it` + «offenders»-массив как формат ошибки**
(`test_concept2_canon.js:48-56`, `:117-127`):

```js
describe('Concept 2 token canon', () => {
  it('reads the canon theme layers', () => {
    assert.equal(canonDark.size, 51, 'the Concept 2 :root token count changed; update this contract deliberately')
    assert.equal(canonLight.size, 13, 'the Concept 2 light-theme override count changed')
```

```js
  it('does not render gamification widgets in the shell', () => {
    const shell = read('web/src/components/AppShell.jsx')
    const offenders = [/XpBar/, /StreakPill/, /RankChip/, /Ур\./, /xp-widget/i]
      .filter((pattern) => pattern.test(shell))
      .map(String)
    assert.deepEqual(offenders, [], 'AppShell must not carry XP/streak/rank widgets')
  })
```

**Аналог 2 (скан исходника по пути + `assert.match` с сообщением):**
`tests/unit/test_admin_mark_ready.js:124-135`:

```js
  it('promoteReady reconciles the refetch via preservePromotedReady; batch CTA is gone', () => {
    const pagePath = path.resolve(__dirname, '../../web/src/pages/AdminDigestPage.jsx')
    const source = fs.readFileSync(pagePath, 'utf8')
    assert.match(
      source,
      /import\s*\{[^}]*preservePromotedReady[^}]*\}\s*from\s*['"][^'"]*adminReadyReconcile\.js['"]/,
      'AdminDigestPage must import preservePromotedReady from adminReadyReconcile.js',
    )
```

**Чего аналога нет:** рекурсивного обхода `web/src/**/*.{js,jsx}` в репозитории ещё не писал никто
(все существующие node-тесты читают файлы по явному пути). Для G-4/G-5/G-6 нужен
`readdirSync(dir, { recursive: true })` (Node 24) либо локальный рекурсивный walk — это новый приём,
и он должен остаться в этом одном файле. Формат ошибки при этом копируется: собрать массив
`offenders` и `assert.deepEqual(offenders, [], '…: ' + offenders.join(', '))`.

**Структура гейта** (нормативна, из UI-SPEC § Token-coverage Gate):

```js
const THEMED = ['paper', 'paper-2', 'ink', 'ink-2', 'muted', 'rule']
const FLAT = [
  'primary-solid', 'accent-solid', 'success-solid', 'danger-solid',
  'on-solid', 'voting-ink', 'scrim',
]
const UTILITY_PREFIXES = ['bg', 'text', 'border', 'ring', 'outline', 'divide', 'fill', 'stroke']
```

| # | Проверка | Аналог формы |
|---|---|---|
| G-1 | каждый `THEMED` есть в `productionDark` | `test_concept2_canon.js:57-63` (`missing`-массив) |
| G-2 | каждый `THEMED` есть в `productionLight` и значение ≠ dark | `test_concept2_canon.js:71-81` |
| G-3 | каждый `FLAT` есть в `productionDark` **и отсутствует** в `productionLight` | новый (absence-ассерт) |
| G-4 | скан `web/src/**/*.{js,jsx}`: утилиты `THEMED` резолвятся, найдены все шесть (анти-вакуум) | offenders-паттерн `:117-127` |
| G-5 | `accent-ink` = 0 вхождений | offenders-паттерн |
| G-6 | `bg-ink` = 0; нет `bg-paper`/`bg-paper-2` с `/` | offenders-паттерн |
| G-7 | WCAG-арифметика, порог 4.5, floor `on-solid`/`danger-solid` `>= 4.829` | `require('../../tests/helpers/contrast')` — путь от `tests/unit/` |
| G-8 | алиасы: `paper==bg-surface`, `paper-2==bg-elevated`, `ink==text-primary` (обе темы); `rule==border`, `muted==text-secondary` — **только dark** | new + объясняющий комментарий |

**Ловушка стиля:** `test_concept2_canon.js` зелёный только пока в `@theme` **один** блок. Гейт
копирует тот же `parseBlock`, поэтому тоже слепнет на втором блоке — дописывать токены в
существующие 7-68 и 106-121.

---

### `tests/admin.spec.js` (test, amendment)

**Analog:** сам файл. Правки — только литералы и token-точные ассерты. Реальные строки (проверено):

**Позитивные текстовые ассерты (RED → «Настройка»)** — `:139`, `:151`, `:165`, `:274`, `:1759`,
`:1764`:

```js
  test("admin-section nav lists Дайджест then Пайплайн and marks digest active", async ({
    page,
  }) => {
```

```js
    await expect(sectionLinks.nth(1)).toHaveText("Пайплайн");
```

```js
    await expect(shellNav(page).getByRole("link", { name: "Пайплайн", exact: true })).toHaveCount(
      0,
    );
```

```js
    const pipelineHeading = page.getByRole("heading", {
      level: 1,
      name: "Пайплайн",
      exact: true,
    });
```

**Кегль вкладки** — `:416` и `:1307`: `await expect(digestTab).toHaveClass(/text-3xl/);`
→ `/text-2xl/`.

**Vacuous-match hazard (не входит в таблицу RESEARCH, обязательно к правке)** — `:186`, `:198`,
`:216`, `:299`, `:312` используют `toHaveClass(/bg-primary/)` на shell-пилле. `bg-primary-solid`
содержит подстроку `bg-primary`, поэтому позитивный ассерт останется зелёным при любом состоянии,
а `:299` (`not.toHaveClass(/bg-primary/)`) станет **лгать** после миграции. Заменять на пару,
как в UI-SPEC § Proof Map:

```js
    const tokens = (await adminLink.getAttribute("class")).split(/\s+/);
    expect(tokens).toContain("bg-primary-solid");
    expect(tokens).not.toContain("bg-primary");
```

**Заголовок «Источники ингеста»** — единственная строка PIPEUI-03, `:1834`:

```js
    await expect(page.getByTestId("ingest-sources-heading")).toHaveText("Источники ингеста");
```

**Уже совместимые ассерты (менять НЕ надо, проверить после правки):**
`:415` и `:1305` — `getByTestId("admin-digest-page"|"admin-pipeline-page").getByText("Админ", { exact: true })).toHaveCount(0)`
уже ожидают ноль и скоупятся на страницу, а не на layout; удаление eyebrow их не ломает.
`:1789-1801` — employee deep-link ожидает `h1` count 2 (`Дайджест` + `Недостаточно прав`);
sr-only `h1` сохраняется, счётчик не меняется.

**Открытый конфликт документов (решить в плане явно):** UI-SPEC § Proof Map предписывает заменить
негативные `/пайплайн/i` на `/настройк/i` в `:439-443` и `:461-465`; RESEARCH Pitfall 10 требует
**оставить** их. По коду: оба ассерта скоупятся на `admin-digest-page` и утверждают отсутствие строки
в теле страницы — после переименования они остаются истинными и продолжают ловить banned copy.
**Рекомендация: оставить как есть** (совпадает с RESEARCH; UI-SPEC здесь ослабляет проверку).

---

## Shared Patterns

### 1. Playwright-харнесс роли и моков
**Source:** `tests/admin.spec.js:22-50` (`gotoAsRole`), `:1815-1824` (`resetIngestSourcesMock`).
**Apply to:** `tests/admin-chrome.spec.js` (все админ-кейсы).

```js
async function resetIngestSourcesMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGEST_SOURCES_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesMockStore();
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingest-sources-section")).toBeVisible();
}
```

Без `resetIngestSourcesMock` `ingest-sources-kind` может прийти в состоянии после предыдущего теста —
критерий 2 измеряет именно этот контрол.

### 2. Тема как состояние до первой загрузки
**Source:** `tests/web-app.spec.js:631-637`, контракт — `web/src/components/ThemeToggle.jsx:3,8-19,24-31`.
**Apply to:** каждый кейс `admin-chrome.spec.js`, которому нужна светлая тема; **явно** снимать ключ
для тёмной (`localStorage.removeItem`), а не полагаться на дефолт.

```js
const THEME_KEY = 'digest-cds-theme'
// ThemeToggle: dark = removeAttribute('data-theme'), light = setAttribute('data-theme','light')
```

### 3. Computed-style пара → контраст в Node-контексте
**Source:** `tests/web-app.spec.js:49-53` (чтение свойства), `tests/admin.spec.js:1079`
(`getComputedStyle(node).overflowY` — единственный существующий computed-style ассерт).
**Apply to:** критерии 2 и 4. `page.evaluate` возвращает только строки, формула WCAG считается в
Node один раз (`tests/helpers/contrast.js`) — не дублировать её внутри браузерного контекста.

### 4. Токен-точное сравнение классов
**Source:** антипаттерн-фикс из UI-SPEC § Proof Map; существующая слабая форма — `tests/admin.spec.js:186`.
**Apply to:** все ассерты `bg-primary-solid` / `bg-accent-solid` / `bg-success-solid` / `bg-danger-solid`.
`toHaveClass(/bg-primary/)` на подстроке — запрещённая форма в этой фазе.

### 5. Двухслойное объявление токенов
**Source:** `web/src/index.css:7-68` + `:106-121`.
**Apply to:** все 13 токенов фазы. Шесть темо-зависимых — в оба блока; семь плоских — только в
`@theme static` (`[data-theme="light"]`-override для них отсутствует, и это пинится G-3).

### 6. ClassName как массив строк + `.join(' ')`
**Source:** `web/src/components/ActionButton.jsx:26-34`, `AppShell.jsx:11-15`,
`AdminLayout.jsx:11-18`.
**Apply to:** все компонентные правки. Миграция подписи — замена **одного элемента массива**;
не разворачивать в конкатенацию и не вводить CSS-in-JS.

### 7. node:test авто-обнаружение
**Source:** `scripts/run-unit-js.cjs:12-17`.
**Apply to:** `tests/unit/test_semantic_token_coverage.js`. Файл кладётся **плоско** в `tests/unit/`,
имя оканчивается на `.js` — `npm run test:js` подхватит без правки раннера. В `tests/unit/` уже
лежат `.py`-файлы, они отфильтрованы по `endsWith('.js')`.

```js
const files = readdirSync(unitDir)
  .filter((name) => name.endsWith('.js'))
  .sort()
  .map((name) => join(unitDir, name))
```

### 8. Vite/5174 flake guard
**Source:** `playwright.config.js:44-55`, RESEARCH Pitfall 8, `.planning/STATE.md` blockers.
**Apply to:** каждый прогон `test:web`. Перед запуском — проверить, что на 5174 не висит вручную
поднятый Vite с `VITE_USE_MOCKS=false`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `tests/admin-chrome.spec.js` (частично) | test (e2e) | batch (обе темы в одном кейсе) | Ни один существующий спек не прогоняет одну и ту же проверку в двух темах и не считает контраст; приёмы взяты по отдельности из `admin.spec.js` / `web-app.spec.js`, но общая форма — новая. |
| `tests/helpers/contrast.js` (расположение) | utility | transform | В `tests/helpers/` ничего нет; ближайший по стилю — `tests/unit/helpers/cssRules.js`, но он живёт в другой папке и не шарится между раннерами. |
| G-4/G-5/G-6 сканер `web/src/**` | test-support | batch | Рекурсивного обхода исходников в `tests/unit/*.js` нет; все существующие тесты читают файлы по явному пути (`test_concept2_canon.js:85,106-110`, `test_admin_mark_ready.js:125`). |

---

## Расхождения «документ vs дерево», найденные при чтении

Планировщик должен учесть их явно — иначе исполнитель потратит цикл RED→GREEN впустую.

1. **Фикстура светлой темы лежит не там, где указывает RESEARCH.** `25-RESEARCH.md` § Test Harness
   ссылается на `tests/admin.spec.js:633-636`; по факту там `page.once("dialog", …)` внутри теста
   stale-draft refetch. Единственный `addInitScript` с `localStorage.setItem("digest-cds-theme","light")`
   — `tests/web-app.spec.js:631-637`. Копировать надо оттуда.
2. **`toHaveClass(/bg-primary/)` в `admin.spec.js` — 5 мест, а не «если такие есть».** `:186`, `:198`,
   `:216`, `:299`, `:312`. После миграции `:299` (`not.toHaveClass`) станет вакуумным в обратную
   сторону — обязательная правка, отсутствующая в таблице UI-SPEC (там перечислены только
   `:186/:198/:216`).
3. **Негативные `/пайплайн/i` (`:442`, `:464`)** — UI-SPEC и RESEARCH расходятся; рекомендация выше.
4. **Канон-тест держит `text-text-primary` в `AppShell.jsx`** (`test_concept2_canon.js:159-165`).
   Миграция `linkClass` безопасна только потому, что литерал остался на корневом `<div>`
   (`AppShell.jsx:66`). «Полная зачистка» файла сломает чужой тест.
5. **`--color-accent-ink` сегодня не объявлен** в `web/src/index.css` (проверено: 0 вхождений) —
   RESEARCH прав; миграция на `text-on-solid` действительно удаляет последних потребителей.
6. **Все миграционные точки совпали с RESEARCH построчно** (13 строк заливок + 4 скрайма +
   2 подложки `bg-paper-2/40` + 2 aria/geometry-строки в `AdminLayout`). Расхождений по номерам
   строк в production-файлах нет.

---

## Metadata

**Analog search scope:** `web/src/components/`, `web/src/pages/`, `web/src/index.css`,
`tests/` (root + `tests/unit/` + `tests/unit/helpers/`), `scripts/`, `playwright.config.js`.
**Files scanned:** 18 прочитанных файлов (7 production, 6 test-инфраструктуры, 5 конфигов/скриптов);
грепом проверены `web/src/**` (потребители семейства: 6 файлов, 65 вхождений),
`tests/**` (`getComputedStyle`, `digest-cds-theme`, `text-3xl`, `bg-*`-литералы).
**Pattern extraction date:** 2026-10-21

**Analog selection rationale:** приоритет — «тот же файл, та же строка» (repair-фаза), затем
«тот же роль + тот же data flow». Ни один аналог не выбран из `design-frontend/` для production-кода:
это прототип без Tailwind, его значение для фазы — только token canon, который уже читает
`test_concept2_canon.js`.
