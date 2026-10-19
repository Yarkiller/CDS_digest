# Digest CDS — UI-SPEC (Editorial UI)

**Status:** concept draft (2026-08-23)  
**Папка:** `design-frontend/`
**Источник визуальной системы:** [design.md](design.md) и [styles/tokens.css](styles/tokens.css)
**Domain glossary:** [CONTEXT.md](../CONTEXT.md)
**Language UI:** русский

Самостоятельный design contract для **внутреннего tech-издания** СВА. Digest CDS представлен как editorial product — еженедельный выпуск, подготовленные агентом статьи как материалы, архив как каталог номеров. Фокус — **комфортное чтение** для рядового сотрудника, Data Analyst и Data Scientist. Без геймификации. Визуальная реализация следует warm-paper bubble system из `design.md`, а не отдельной базовой концепции.

**Контентный контракт:** статья создаётся из транскрипции внешнего видео или импортированного текста, дополняется уточняющим поиском и анализом и проходит редакторскую подготовку. Она может быть гайдом по установке/использованию технологии или описанием нового подхода. Видео/аудио и необработанный транскрипт не являются материалом, не встраиваются и не сохраняются как материал; внешняя ссылка показывается только в provenance-блоке. Сложные термины и подходы связываются с существующими статьями внутренними ссылками при первом уместном упоминании, а связанные статьи — обратными ссылками или related-блоком.

---

## 0. Scope and source of truth

Concept 3 — единственный выбранный дизайн и статический frontend-прототип
Digest CDS. Этот документ описывает его standalone-контракт; сравнительные
концепты и унаследованные спецификации не являются частью проекта.

Канонические источники:

- `design.md` — жанр, макроструктуры, тема, типографика и правила
  взаимодействия;
- `styles/tokens.css` — фактические semantic tokens;
- HTML в `pages/`, `scripts/app.js` и `styles/` — рабочая static prototype
  реализация.

Прототип не является production React/FastAPI приложением. Он фиксирует
информационную архитектуру, визуальный язык, состояния интерфейса и
интерактивные stubs, которые должны быть перенесены в целевую frontend/backend
реализацию.

---

## 1. Принципы

| # | Принцип | Реализация |
|---|---------|------------|
| P1 | Читать — главное действие | Prose-first layout, колонка 680px, line-height 1.71+ |
| P2 | Выпуск — единица навигации | Home = обложка + оглавление текущего дайджеста |
| P3 | Тишина интерфейса | Минимум chrome: компактный header, без sidebar на reading pages |
| P4 | Серьёзная типографика | Serif для заголовков, sans для body и UI |
| P5 | Голосование — редакционная заметка | EditorialCallout на home; ballot на `/voting` |
| P6 | Domain language | Термины из CONTEXT.md: **дайджест**, **цикл голосования**, **материал**, **разбор** |

**Anti-patterns (запрещено):**

- Card grid как главный паттерн home
- Dark theme, glass/blur, glow effects
- XP, streak, лидерборд, квизы
- Gradient mesh heroes, emoji, mascots
- Play-button overlays (контент — подготовленные статьи, не видео)

---

## 2. Design tokens

### 2.1 Color — warm paper, light only

The implementation uses semantic OKLCH tokens from `styles/tokens.css`:

| Token group | Usage |
|-------------|-------|
| `--color-paper*`, `--color-bg-*` | Warm paper surfaces, prose, callouts and highlights |
| `--color-ink*`, `--color-text-*` | Primary copy, metadata and muted labels |
| `--color-rule`, `--color-border*` | Rules, dividers and focused controls |
| `--color-accent*` | Links, active states, tags and primary controls |
| `--color-voting*` | Voting callouts and cycle status |
| `--color-success`, `--color-danger`, `--color-info` | Semantic feedback |

No gradients, glass surfaces or decorative glow. Body text on prose surfaces
must maintain a contrast ratio of at least 4.5:1; secondary text at least 3:1.

### 2.2 Typography

**Font stacks**

```css
--font-display: "Bricolage Grotesque", "Trebuchet MS", sans-serif;
--font-body: "IBM Plex Sans", "Segoe UI", sans-serif;
--font-outlier: "IBM Plex Mono", "Consolas", monospace;
--font-serif: var(--font-display);
--font-sans: var(--font-body);
--font-mono: var(--font-outlier);
```

Bricolage Grotesque is used for display/editorial headings; IBM Plex Sans for
body and UI; IBM Plex Mono for technical outliers and metadata.

**Scale**

| Token | Font | Size | Line height | Weight | Usage |
|-------|------|------|-------------|--------|-------|
| `--text-display` | display | fluid | 1.05 | 600 | H1 материала, обложка выпуска |
| `--text-h1` | display | fluid | 1.1 | 600 | Заголовок выпуска |
| `--text-h2` | display | fluid | 1.2 | 600 | Секции, rubric headers |
| `--text-h3` | sans | 18px | 1.4 | 600 | Подзаголовки, TOC items |
| `--text-body` | sans | 17px | 1.65 | 400 | Резюме, полный текст |
| `--text-body-sm` | sans | 15px | 1.5 | 400 | UI labels, nav |
| `--text-caption` | sans | 13px | 1.4 | 400 | Даты, bylines |
| `--text-overline` | sans | 12px | 1.4 | 600 | Rubric, issue metadata |
| `--text-pullquote` | display | 22px | 1.55 | 400 | Цитаты в статьях |

**Reading width:** prose — `max-width: 680px`; issue page — `max-width: 960px`.

### 2.3 Spacing

4px base grid.

| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |
| `--space-16` | 64px |

**Layout defaults**

| Element | Value |
|---------|-------|
| Page horizontal padding | `--space-6` (mobile), `--space-8` (≥768px) |
| Section vertical gap (prose) | `--space-10` |
| Major section gap (home) | `--space-16` |
| IssueTOC row padding | `--space-5` vertical |
| Prose column padding | `--space-12` horizontal |

### 2.4 Radius & elevation

| Token | Value |
|-------|-------|
| `--radius-sm` | 2px |
| `--radius-md` | 4px |
| `--radius-lg` | 6px |
| `--shadow-sm` | `0 1px 3px rgba(28, 25, 23, 0.06)` |

Cards и списки: **без box-shadow**; разделение через `1px solid var(--color-border)` rule lines. Исключение: sticky TOC при scroll — `--shadow-sm`.

### 2.5 Breakpoints

| Token | Min width | Layout |
|-------|-----------|--------|
| `--bp-sm` | 640px | Issue archive 1 → 2 col |
| `--bp-md` | 768px | Issue archive 2 col |
| `--bp-lg` | 1024px | Reading + sticky TOC |
| `--bp-xl` | 1280px | Full reading layout |

```css
--container-reading: 680px;
--container-issue: 960px;
--container-wide: 1200px;
--header-height: 48px;
--toc-width: 220px;
```

### 2.6 Motion

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-fast` | 100ms | Link hover, focus |
| `--duration-normal` | 180ms | Accordion, toast |
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | All transitions |

Respect `prefers-reduced-motion`: отключать transitions.

---

## 3. Global layout

### 3.1 App shell (authenticated)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER  h=48px  bg=surface  border-bottom 1px                            │
│ [Digest CDS]  [Выпуск] [Архив] [База] [Голосование] [Разборы]           │
│                                    [Search compact]  [User ▼]            │
├──────────────────────────────────────────────────────────────────────────┤
│ MAIN  bg=app  padding-x 24–32                                            │
│   {Outlet}                                                               │
└──────────────────────────────────────────────────────────────────────────┘
```

**Header nav items:**

| Label | Route | Roles |
|-------|-------|-------|
| Выпуск | `/` | all |
| Архив | `/archive` | all |
| База | `/knowledge` | all |
| Голосование | `/voting` | all |
| Разборы | `/razbory` | all |
| Админ | `/admin` | admin |

Active link: `--color-primary` + 2px bottom border. Logo wordmark — serif «Digest CDS», sans weight для «CDS».

**Search:** compact icon + expand on focus (max 360px), не доминирует над nav.

**User menu:** имя, `RoleBadge`, «Выйти».

### 3.2 Auth layout

Centered card `max-width: 400px`, serif h1 «Digest CDS», sans form labels. Routes: `/login`, `/register`.

---

## 4. Components

### 4.1 Button

| Variant | Background | Text | Height | Notes |
|---------|------------|------|--------|-------|
| `primary` | `--color-primary` | white | 40px | Flat, no gradient |
| `secondary` | transparent | `--color-primary` | 40px | 1px border |
| `ghost` | transparent | `--color-text-secondary` | 36px | Text links style |
| `voting` | `--color-voting` | white | 40px | Confirm vote |

Radius `--radius-md`. No scale bounce on hover.

### 4.2 IssueTOCRow

Numbered list item (не card):

```
01  Building Production RAG Systems     Статья · 8 мин    →
    Как быстро находить нужные фрагменты регламентов СВА…
```

| Part | Style |
|------|-------|
| Number | mono, `--text-caption`, `--color-text-muted`, width 32px |
| Title | `--text-h3`, serif optional for title only |
| Dek | `--text-body-sm`, `--color-text-secondary`, 1 предложение «зачем СВА»; **вне** `<a>` (X-01) |
| Meta | `--text-caption`, `--color-text-secondary` |
| Arrow | `→` on hover, `--color-primary` |

Row: border-bottom `--color-border`, padding `--space-5` 0. Hover: title color `--color-primary`.

### 4.3 IssueCover

Archive grid item:

- Overline: `ВЫПУСК №N`
- H2 serif: date range
- Caption: N материалов
- Thumb strip: 3 mini covers (48×27), overlapping -8px
- Border 1px, no shadow; hover underline on title

### 4.4 EditorialCallout

Full-width within issue container:

- bg `--color-bg-callout`
- left border 3px `--color-voting`
- padding `--space-5`
- Copy: «Голосование открыто до {date}» + ghost link «Выбрать тему →`

### 4.5 EditorialBox

Aside in material page:

- bg `--color-bg-muted`
- padding `--space-5`
- border-left 3px `--color-accent`
- Content: «В выпуске №14 · позиция 01», related topics

### 4.6 TopicBallot

Radio-style voting (не card grid):

| Element | Style |
|---------|-------|
| Row | padding `--space-5`, border-bottom |
| Radio | 20px circle, border 2px; selected fill `--color-primary` |
| Title | `--text-h3` |
| Meta | tags + vote count; лидер: «Лидирует · N» без путаницы с «ваш выбор» |
| Selected row | bg `--color-bg-callout` subtle |
| Default | **ни один** row не selected, пока пользователь не выбрал; статус «Ваш голос: не отдан» |

Confirm → toast «Голос сохранён (прототип)»; статус обновляется на выбранную тему.

### 4.7 TagPill

`--color-accent` text on `--color-bg-muted` background, radius
`--radius-sm`, without heavy saturation.

### 4.8 RoleBadge, SearchBar, VotingTimer, NotebookViewer, AdminShortlistRow

Используют общие editorial tokens: serif только там, где это указано;
admin-интерфейс остаётся sans-led.

**AdminShortlistRow (C3):** checkbox · rank · title · `draft`/`ready` badge · score + rationale caption · exclusion copy · preview button (modal, не переход на reader). Toolbar: Select all / Approve / Reject. Email preview modal (serif headlines) обязателен перед Send; Send disabled при draft в selection.

**NotebookViewer:** disclaimer + CTA «Скачать .ipynb»; секции metrics / refs / end-of-article.

### 4.9 MaterialListRow (knowledge search)

Alternative to MaterialCard for search results — horizontal row:

```
[thumb 80×45]  Title (serif h3)  ·  snippet…  ·  tags
```

Rule line separator, no card shadow.

**Filters:** Role (СВА / Data Analyst / Data Scientist) · Tag (SQL/BI/DQ/аудит + ML) · Format · Topic. Default search **empty** + hint chips «для аналитика» / «для DS». Load more: skeleton + «Показано N из M». Empty state без подмены ML-топом.

### 4.10 PullQuote

Serif italic `--text-pullquote`, left border 3px `--color-border-strong`, padding-left `--space-5`, margin `--space-8` vertical.

### 4.11 ReadingProgress

Thin bar 2px top of viewport on material/razbor pages; fill `--color-primary`; optional, non-intrusive.

---

## 5. Routes

Same as v1 (no gamification routes):

```
/                         IssuePage (current digest)
/archive                  DigestArchivePage
/archive/:issueId         IssuePage (specific issue)
/knowledge                KnowledgeSearchPage
/knowledge/:materialId    MaterialPage
/voting                   VotingPage
/razbory                  RazboryListPage
/razbory/:razborId        RazborPage
/login, /register         Auth
/admin/digest             AdminDigestShortlistPage
/admin/sources            AdminSourcesPage
/admin/moderation         AdminModerationPage
```

---

## 6. Wireframes (ключевые экраны)

### 6.1 `/` — Current issue (home)

```
┌─ container-issue 960px ────────────────────────────────────────────────┐
│ overline: ВЫПУСК №14 · 17–23 МАРТА 2026                                 │
│ h1 (serif): Новости DS для СВА                                          │
│ caption: Редакция Digest CDS · 5 материалов                             │
│ ───────────────────────── rule line ─────────────────────────────────── │
│                                                                         │
│ [EditorialCallout — if voting active]                                   │
│                                                                         │
│ h2 (serif): В этом выпуске                                              │
│ [IssueTOCRow × N]                                                       │
│                                                                         │
│ aside: «Предыдущий выпуск №13 →»                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

Mobile: same stack, TOC full width.

### 6.2 `/archive` — Archive

```
h1 (serif): Архив выпусков
grid 1 col → 2 col ≥768

[IssueCover] [IssueCover]
[IssueCover] …
```

### 6.3 `/knowledge` — Search

```
h1 (serif): База знаний
[SearchBar full width max 560px]
TagPill filters

[MaterialListRow × N]
[Load more]
```

Search highlight: `<mark>` with `--color-bg-highlight`.

### 6.4 `/knowledge/:id` — Material (article)

```
┌─ ≥1280: 2-col ─────────────────────────────────────────────────────────┐
│ PROSE col max 680px bg=prose   │ TOC sticky 220px                       │
│ padding 48px                   │ · Резюме                               │
│                                │ · Полный текст                         │
│ overline: СТАТЬЯ · RAG         │ · Связанные                            │
│ h1 display serif               │                                        │
│ byline: date · provenance · N мин │                                      │
│ ─── rule ───                   │                                        │
│ [hero image 16:9]              │                                        │
│ h2 Резюме                      │                                        │
│ body prose                     │                                        │
│ TagPill row                    │                                        │
│ h2 Полный текст                │                                        │
│ body prose…                    │                                        │
│ [EditorialBox: в выпуске №14]  │                                        │
│ [Связанные статьи]             │                                        │
└────────────────────────────────┴────────────────────────────────────────┘
```

Format badge: overline «СТАТЬЯ» above h1, not play button. Внешний первоисточник и его ссылка не подменяют статью и отображаются отдельно от prose.

Mobile: TOC → accordion «Содержание ▼» above prose.

### 6.5 `/voting`

```
h1 (serif): Голосование за тему разбора
VotingTimer inline (text + rule progress)
body-sm: Один голос за цикл…

[TopicBallot × N]
[Подтвердить голос] primary
```

### 6.6 `/razbory` — List

```
h1 (serif): Разборы
caption: Встречи раз в две недели · материалы от Data Scientist

┌ chronology list ───────────────────────────────────────────────────────┐
│ [date overline]                                                         │
│ h3 serif: Topic title                                                   │
│ byline: Author · RoleBadge                                              │
│ [Читать разбор →]                                                       │
├ rule line ─────────────────────────────────────────────────────────────┤
│ …                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.7 `/razbory/:id` — Razbor

Same reading layout as MaterialPage + NotebookViewer in prose column. Header: «Разбор · {topic}» serif h1.

### 6.8 `/admin/digest`

Sans-only table layout (as C1). Email preview modal renders with **editorial typography** (serif headlines) to match sent digest.

---

## 7. Visual tone reference

| ✅ Допустимо | ❌ Избегать |
|-------------|------------|
| Warm paper backgrounds | Cold pure white `#FFFFFF` everywhere |
| Serif headlines | Sans-only longform |
| Rule lines, numbered TOC | Card grids on home |
| Compact 48px header | Tall dashboard headers |
| Reading time estimates | Video play buttons |
| Pull quotes, bylines | XP badges, streaks |
| Ink blue links | Neon / violet accents |

**Mood:** «Внутренний tech-журнал Сбербанк СВА» — можно читать 20 минут без усталости, уместно показать руководителю CDS.

---

## 8. Accessibility

- Prose line-height ≥ 1.7; paragraph spacing ≥ 1em
- Focus visible on all interactive elements (2px `--color-primary` outline)
- `prefers-reduced-motion` respected
- Reading progress bar optional; disable if reduced motion
- TOC: keyboard navigable, `aria-current` on active section
- Contrast on `--color-bg-prose`: primary text ≥ 4.5:1
- Terminology from CONTEXT.md: **дайджест**, **материал**, **цикл голосования**,
  **разбор**, **Data Analyst**, **Data Scientist**

---

## 9. Planned production frontend structure

`frontend/src/` ниже описывает целевую архитектуру, а не существующую
реализацию. Текущий runnable prototype остаётся в `design-frontend/`.

```
frontend/src/
├── components/
│   ├── editorial/
│   │   ├── IssueTOCRow.tsx
│   │   ├── IssueCover.tsx
│   │   ├── EditorialCallout.tsx
│   │   ├── EditorialBox.tsx
│   │   ├── TopicBallot.tsx
│   │   ├── MaterialListRow.tsx
│   │   ├── PullQuote.tsx
│   │   └── ReadingProgress.tsx
│   └── shared/
├── pages/
│   ├── IssuePage.tsx          # replaces HomePage as default /
│   └── …
└── styles/
    ├── tokens-editorial.css
    ├── typography-serif.css
    └── prose.css              # longform article styles
```

**Libraries:** Vite, React и TanStack Query. No framer-motion. Optional:
`reading-time` util for estimates.

### Static prototype to route map

| Static file | Target route |
|-------------|--------------|
| `pages/issue.html` | `/` |
| `pages/archive.html` | `/archive` |
| `pages/knowledge.html` | `/knowledge` |
| `pages/material.html` | `/materials/:id` |
| `pages/voting.html` | `/voting` |
| `pages/razbory.html` | `/razbory` |
| `pages/razbor.html` | `/razbory/:id` |
| `pages/admin-digest.html` | `/admin/digest` |

---

## 10. Static prototype scope (`design-frontend/`)

Pages for HTML/CSS mockup:

| File | Screen |
|------|--------|
| `index.html` | Gallery |
| `pages/issue.html` | Current issue (home) |
| `pages/archive.html` | Digest archive |
| `pages/knowledge.html` | Search |
| `pages/material.html` | Article reading |
| `pages/voting.html` | TopicBallot |
| `pages/razbory.html` | Razbory list |
| `pages/razbor.html` | Razbor longread |
| `pages/login.html` | Auth |
| `pages/admin-digest.html` | Admin shortlist |

The prototype uses only the local assets in `assets/covers/` and
`assets/notebooks/`.

---

## 11. References

- [design.md](design.md)
- [styles/tokens.css](styles/tokens.css)
- [CONTEXT.md](../CONTEXT.md)
- [spec v1](../.scratch/digest-cds/spec.md)
