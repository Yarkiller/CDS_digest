# Digest CDS — UI-SPEC v2 (Concept 2)

**Status:** concept draft (2026-08-23)  
**Папка:** `Homework_by_project/UI_concepts/Concept_2/`  
**Базовый spec:** [UI-SPEC v1](../../../docs/UI-SPEC.md)  
**Domain glossary:** [CONTEXT.md](../../../CONTEXT.md)  
**ADR:** [0001 — публичный лидерборд](../../../docs/adr/0001-public-leaderboard-gamification.md)  
**Language UI:** русский

Альтернативный design contract: **молодёжный tech-продукт** для DS-сообщества СВА с **встроенной геймификацией**. Стиль — энергичный, но **не казуальный**: без mascots, мультяшных иконок, «игровых» шрифтов и декоративного clutter. Ориентиры: Linear, Vercel Dashboard, GitHub Contributions, Strava (структура прогресса), Notion (читаемость).

---

## 0. Отличия от Concept 1 (UI-SPEC v1)

| Аспект | Concept 1 | Concept 2 |
|--------|-----------|-----------|
| Настроение | Корпоративный дайджест | Tech-community hub |
| Геймификация | Post-v1, скрыта | Встроена в shell и главную |
| Тема | Light-only | **Dark-first** + light toggle |
| Типографика | Inter | **Manrope** (геометричный grotesk) |
| Акценты | Синий + teal | **Violet + cyan** + lime для XP |
| Карточки | Flat shadow | Glass / subtle border glow |
| Прогресс | Только voting timer | XP, streak, weekly quest, лидерборд |
| Материалы | Статьи / презентации | То же + **карточки с вопросами** |

---

## 1. Принципы

| # | Принцип | Реализация |
|---|---------|------------|
| P1 | Прогресс виден сразу | XP-bar и streak — в header, не спрятаны в профиле |
| P2 | Соревнование без токсичности | Лидерборд показывает ранг и очки, без «позора» отстающих; opt-out в настройках |
| P3 | Молодёжно ≠ несерьёзно | Тёмная тема, чёткая сетка, monospace для метрик; никаких emoji-trophy |
| P4 | Контент остаётся главным | Gamification — полоски и компактные виджеты, не fullscreen overlays |
| P5 | Один CTA на блок | «Проголосовать», «Пройти тест», «+25 XP» — не более одного primary action |
| P6 | Дomain language | Термины из CONTEXT.md: **лидерборд**, **цикл голосования**, **карточка с вопросами** |

**Anti-patterns (запрещено):**

- Mascots, 3D-иллюстрации, comic badges
- Казуальные шрифты (Baloo, Fredoka, …)
- Confetti / particle effects на каждое действие
- Звуковые эффекты по умолчанию
- Детская цветовая палитра (bubblegum pink, candy yellow как primary)

---

## 2. Design tokens

### 2.1 Color — dark theme (default)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg-app` | `#0B0F17` | Фон приложения |
| `--color-bg-surface` | `#131925` | Карточки, panels |
| `--color-bg-elevated` | `#1A2233` | Hover cards, dropdowns |
| `--color-bg-muted` | `#242D3D` | Code blocks, progress track |
| `--color-bg-glass` | `rgba(19, 25, 37, 0.72)` | Header, sticky widgets (backdrop-blur 12px) |
| `--color-text-primary` | `#F1F5F9` | Основной текст |
| `--color-text-secondary` | `#94A3B8` | Meta, captions |
| `--color-text-disabled` | `#64748B` | Placeholders |
| `--color-border` | `#2A3548` | Dividers |
| `--color-border-glow` | `rgba(139, 92, 246, 0.35)` | Active card, focus |
| `--color-primary` | `#8B5CF6` | Primary CTA, nav active |
| `--color-primary-hover` | `#7C3AED` | Hover primary |
| `--color-accent` | `#06B6D4` | Links, search focus, DS-tags |
| `--color-accent-hover` | `#0891B2` | Hover accent |
| `--color-xp` | `#A3E635` | XP bar fill, level badge |
| `--color-xp-muted` | `#3F6212` | XP track background |
| `--color-streak` | `#F97316` | Streak flame (icon only, muted orange) |
| `--color-voting` | `#EAB308` | Voting CTA (sharp amber, not pastel) |
| `--color-success` | `#22C55E` | Quest complete, quiz pass |
| `--color-danger` | `#EF4444` | Errors |
| `--color-info` | `#38BDF8` | Info banners |

**Light theme overrides** (`[data-theme="light"]`):

| Token | Hex |
|-------|-----|
| `--color-bg-app` | `#F8FAFC` |
| `--color-bg-surface` | `#FFFFFF` |
| `--color-bg-elevated` | `#F1F5F9` |
| `--color-text-primary` | `#0F172A` |
| `--color-text-secondary` | `#64748B` |
| `--color-border` | `#E2E8F0` |
| `--color-border-glow` | `rgba(139, 92, 246, 0.2)` |

### 2.2 Typography

```css
--font-sans: "Manrope", "Segoe UI", system-ui, sans-serif;
--font-mono: "JetBrains Mono", "Consolas", monospace;
--font-display: "Manrope", sans-serif; /* weight 700 for hero */
```

Manrope: weights 400, 500, 600, **700** (display numbers, XP).

| Token | Size | LH | Weight | Usage |
|-------|------|-----|--------|-------|
| `--text-display` | 36px | 44px | 700 | Hero, лидерборд #1 |
| `--text-h1` | 28px | 36px | 700 | Page titles |
| `--text-h2` | 22px | 30px | 600 | Sections |
| `--text-h3` | 17px | 26px | 600 | Card titles |
| `--text-body` | 16px | 26px | 400 | Prose |
| `--text-body-sm` | 14px | 22px | 500 | UI, nav |
| `--text-caption` | 12px | 16px | 500 | Meta |
| `--text-stat` | 28px | 32px | 700 | XP count, rank (mono optional) |
| `--text-overline` | 11px | 14px | 600 | LABELS, uppercase, ls 0.06em |

### 2.3 Spacing & radius

8px grid — та же шкала, что в v1 (`--space-1` … `--space-16`).

| Token | Value | Notes |
|-------|-------|-------|
| `--radius-sm` | 6px | Badges |
| `--radius-md` | 10px | Buttons, inputs |
| `--radius-lg` | 14px | Cards |
| `--radius-xl` | 20px | Hero widgets |
| `--radius-full` | 9999px | XP bar, avatars |

**Shadows (dark theme):**

```css
--shadow-sm: 0 1px 0 rgba(255,255,255,0.04) inset;
--shadow-md: 0 0 0 1px var(--color-border), 0 4px 24px rgba(0,0,0,0.4);
--shadow-glow: 0 0 0 1px var(--color-border-glow), 0 0 24px rgba(139,92,246,0.12);
```

### 2.4 Layout

```css
--container-max: 1280px;
--header-height: 64px;
--sidebar-width: 260px;
--xp-bar-height: 6px;
--streak-size: 32px;
```

Breakpoints: те же, что v1 (`640 / 768 / 1024 / 1280`).

### 2.5 Motion

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-fast` | 150ms | Hover |
| `--duration-normal` | 250ms | Panel open |
| `--duration-xp` | 600ms | XP bar fill (ease-out) |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Level-up badge (once) |

`prefers-reduced-motion`: XP animation → instant jump; no spring.

---

## 3. Gamification system (UI layer)

### 3.1 Метрики (отображение)

| Метрика | UI label | Источник (backend) |
|---------|----------|-------------------|
| **XP** | «Опыт» | События активности (просмотр, голос, тест, разбор) |
| **Уровень** | «Ур. N» | Пороги XP (лестница, конфиг YAML) |
| **Streak** | «Серия N дн.» | Последовательные дни с ≥1 событием |
| **Ранг** | «#12» | Позиция в **лидерборде** |
| **Weekly quest** | «Задание недели» | 3 материала + 1 голос = bonus XP |

**XP weights (UI hints, не финальные):**

| Действие | XP hint |
|----------|---------|
| Просмотр материала | +5 |
| Открытие дайджеста | +10 |
| Голосование в цикле | +25 |
| Карточка с вопросами ≥80% | +40 |
| Публикация .ipynb разбора | +100 |

### 3.2 Лидерборд (ADR-0001)

- Публичный, виден всем авторизованным.
- Колонки: **ранг** · **аватар + имя** · **уровень** · **XP (неделя)** · **streak**.
- Top-3: subtle gradient border (`--shadow-glow`), без золотых кубков.
- Текущий пользователь: строка highlighted `--color-bg-elevated` + «Вы».
- Opt-out: Settings → «Скрыть меня из лидерборда» → строка заменяется «Участник скрыт» для других; пользователь видит свой ранг privately.

### 3.3 Достижения (badges)

Минималистичные **hex-badge** (шестиугольник 40px), monochrome + один accent.

| Badge ID | Label | Условие |
|----------|-------|---------|
| `first-vote` | Первый голос | 1 голосование |
| `digest-reader` | Читатель дайджеста | 4 дайджеста подряд |
| `quiz-ace` | Тест сдан | 3 карточки с вопросами ≥80% |
| `razbor-author` | Автор разбора | 1 .ipynb опубликован |

Отображение: сетка в профиле; tooltip с описанием; locked = opacity 0.35.

### 3.4 Карточки с вопросами (в scope Concept 2)

- После материала или разбора: блок «Проверь понимание» → 5–10 вопросов.
- UI: один вопрос на экран, progress dots, timer optional (off by default).
- Result: score ring (SVG), XP grant animation в `--color-xp`.
- Термин: **карточка с вопросами** (не «квиз»).

---

## 4. Global layout

### 4.1 App shell

```
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER 64px  glass  border-bottom                                          │
│ [Logo] [Nav]  [SearchBar]     [Streak][XP bar + Lv][Rank#]  [Avatar ▼]   │
├────────────────────────────────────────────────────────────────────────────┤
│ MAIN  max-w=1280                                                           │
│  ┌─ optional QuestBanner (dismissible) ─────────────────────────────────┐  │
│  │ Задание недели: 2/3 материала · +50 XP          [Продолжить →]      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  {Outlet}                                                                  │
└────────────────────────────────────────────────────────────────────────────┘
```

**Nav items (расширенные):**

| Label | Route |
|-------|-------|
| Главная | `/` |
| Дайджест | `/digest` |
| База знаний | `/knowledge` |
| Голосование | `/voting` |
| Разборы | `/razbory` |
| **Лидерборд** | `/leaderboard` |
| Админ | `/admin` |

### 4.2 Header widgets

**XpBar** — width 120px (desktop), height 6px; fill `--color-xp`; label «Ур. 7» слева от бара.

**StreakPill** — icon flame 16px + «12» ; `--color-streak` icon only; bg `--color-bg-elevated`.

**RankChip** — «#8» mono caption; click → `/leaderboard`.

**ThemeToggle** — sun/moon icon in user dropdown.

---

## 5. Components (новые и изменённые)

### 5.1 Button (обновлённые варианты)

| Variant | BG | Height | Notes |
|---------|-----|--------|-------|
| `primary` | gradient `#8B5CF6 → #6D28D9` | 44px | Subtle gradient, not flat candy |
| `accent` | `#06B6D4` | 44px | Secondary actions |
| `xp` | `#A3E635` | 44px | Text `#1A2E05` — «Забрать +25 XP» |
| `ghost` | transparent | 40px | Border `--color-border` |
| `glass` | `--color-bg-glass` | 44px | Quest banner CTA |

Hover: brightness 1.08, не scale bounce.

### 5.2 MaterialCard v2

- Cover 128×72, radius `--radius-md`, border `1px solid var(--color-border)`.
- Hover: `--shadow-glow`, translateY -2px (150ms).
- Footer: tags + **«+5 XP»** hint (caption, `--color-xp`) если материал не прочитан.
- Format badge: «Статья» / «Презентация» (как v1).

### 5.3 TopicCard v2

- Voting card с **live pulse** on border (`--color-voting`, 2s, subtle — only active cycle).
- Selected: check in circle, не cartoon.
- Post-vote toast: «+25 XP · Голос учтён».

### 5.4 QuestBanner

- Full width, `--radius-xl`, bg `--color-bg-elevated`, left border 3px `--color-xp`.
- Progress bar inside; dismiss saves state localStorage.

### 5.5 LeaderboardRow

| Rank | User | Level | XP week | Streak |
|------|------|-------|---------|--------|
| mono stat | avatar 32 + name | badge «Ур.N» | mono `--color-xp` | StreakPill sm |

Top-3 rank: `#1` `#2` `#3` in `--text-stat`, colors `#A3E635` / `#94A3B8` / `#CD7F32` (muted bronze, not gold foil).

### 5.6 QuizCard (карточка с вопросами)

- Modal or route `/materials/:id/quiz`.
- **ProgressDots** — 5–10 dots, fill `--color-primary`.
- **ScoreRing** — 120px SVG, stroke `--color-xp`.
- Answer buttons: full width, letter prefix `A` `B` `C` in mono square.

### 5.7 ProfileStats (sidebar or `/profile`)

```
┌─ Profile ──────────────────┐
│ [Avatar 64]  Ivan P.       │
│ DS-эксперт                 │
│ Уровень 7  ████████░░ 340/500 XP │
│ Серия 12 дн.  ·  Ранг #8   │
│ ─────────────────────────  │
│ Достижения                 │
│ [hex][hex][hex][hex locked]│
└────────────────────────────┘
```

### 5.8 LevelUpModal

- Triggered once per level; dark overlay 60%.
- Content: «Уровень 8», new hex badge if unlocked.
- Single CTA «Продолжить»; no confetti — subtle radial glow 400ms.

---

## 6. Routes (дополнения к v1)

```
/leaderboard              LeaderboardPage
/profile                  ProfilePage
/profile/settings         SettingsPage (opt-out leaderboard, theme)
/materials/:id/quiz       QuizPage
```

---

## 7. Wireframes (ключевые экраны)

### 7.1 `/` — Home (gamified)

```
┌─ 3-col desktop ──────────────────────────────────────────────────────────┐
│ LEFT col (320)          │ CENTER (flex)              │ RIGHT (280)        │
│ ProfileStats compact    │ QuestBanner (if active)    │ LeaderboardTop5    │
│ Weekly quest ring       │ VotingBlock (enhanced)       │ «Топ недели»       │
│                         │ Latest digest              │ [Row][Row][Row]    │
│                         │ Material feed              │ [Весь лидерборд →] │
└─────────────────────────┴────────────────────────────┴────────────────────┘
```

Mobile: stack — QuestBanner → Voting → Materials → LeaderboardTop5 accordion.

### 7.2 `/leaderboard`

```
h1: Лидерборд
tabs: [Эта неделя] [Всё время]

┌ table ────────────────────────────────────────────────────────────────┐
│ #  │ Участник           │ Ур. │ XP    │ Серия │                     │
│ 1  │ ●● Anna K.         │ 12  │ 840   │ 🔥 21 │  ← glow border      │
│ 2  │ ●● …               │ …   │ …     │ …     │                     │
│ …  │ ▶ Вы — Ivan P.     │  7  │ 340   │ 🔥 12 │  ← highlighted      │
└───────────────────────────────────────────────────────────────────────┘

caption: Обновляется каждый час · N участников
link: Настройки приватности
```

*(flame только как SVG icon StreakPill, не emoji в production — в wireframe допустимо для схемы)*

### 7.3 Material + Quiz flow

```
[Cover hero]
[Format: Статья] [+5 XP если не прочитан]
Title · summary · tags

── after scroll 60% or explicit CTA ──
┌ QuizPrompt ──────────────────────────────────────┐
│ Проверь понимание · карточка с вопросами         │
│ 5 вопросов · ~3 мин · до +40 XP                  │
│ [Начать →]                                       │
└──────────────────────────────────────────────────┘
```

### 7.4 `/voting` — enhanced

- Header: countdown ** monospace ** + XP hint «+25 XP за участие».
- TopicCards in bento grid (2 large + 2 small on desktop).
- After vote: inline rank update «Вы поднялись на #8 → #7 в активности недели» (optional micro-copy).

---

## 8. Visual tone reference

| ✅ Допустимо | ❌ Казуальный стиль |
|-------------|---------------------|
| Dark UI, neon accents | Pastel gradients everywhere |
| Manrope 700 stats | Rounded comic fonts |
| Hex badges, mono ranks | Cartoon trophies, stars burst |
| Glass header | Skeuomorphic leather textures |
| Subtle glow on hover | Bouncy elastic buttons |
| XP as lime accent bar | Coin sprites, loot boxes |
| GitHub-style contribution grid (future) | Farmville mechanics |

**Mood:** «Discord meets Linear для аудиторов-аналитиков» — ночной режим, чувство community, но можно показать на совещании CDS.

---

## 9. Accessibility & ethics

- XP/лидерборд не показывают **чувствительные** детали активности (какие именно документы аудита смотрел).
- Opt-out лидерборда — prominent in settings, не buried.
- Animations respect `prefers-reduced-motion`.
- Contrast on dark: primary text ≥ 7:1 on `#131925`.
- Gamification copy на русском; избегать «achievement unlocked» — использовать «Достижение получено».
- Не использовать термин «рейтинг» вместо **лидерборд** (CONTEXT.md).

---

## 10. React structure delta

```
frontend/src/
├── components/
│   ├── gamification/
│   │   ├── XpBar.tsx
│   │   ├── StreakPill.tsx
│   │   ├── RankChip.tsx
│   │   ├── QuestBanner.tsx
│   │   ├── LeaderboardRow.tsx
│   │   ├── HexBadge.tsx
│   │   ├── ScoreRing.tsx
│   │   ├── LevelUpModal.tsx
│   │   └── QuizPrompt.tsx
│   └── … (остальное из v1)
├── pages/
│   ├── LeaderboardPage.tsx
│   ├── ProfilePage.tsx
│   └── QuizPage.tsx
├── hooks/
│   ├── useXpAnimation.ts
│   └── useTheme.ts
└── styles/
    ├── tokens-dark.css
    └── tokens-light.css
```

**Libraries add-on:** `framer-motion` только для XP bar и LevelUpModal; не для page transitions.

---

## 11. API (gamification endpoints)

```
GET  /me/stats              → xp, level, streak, rank, quests
GET  /leaderboard?period=week|all
POST /leaderboard/opt-out   → { hidden: boolean }
GET  /me/badges
GET  /materials/:id/quiz
POST /materials/:id/quiz    → answers → score, xp_grant
GET  /quests/current
```

---

## 12. Acceptance checklist (Concept 2)

- [ ] Dark theme default; light toggle works.
- [ ] XpBar + StreakPill visible in header on authenticated pages.
- [ ] `/leaderboard` matches ADR-0001 (public, opt-out documented).
- [ ] No casual mascots / comic visuals in component inventory.
- [ ] Карточка с вопросами flow complete (prompt → quiz → score → XP).
- [ ] Domain terms from CONTEXT.md used consistently.
- [ ] Material format = статья / презентация (cover image, no video).
- [ ] QuestBanner dismissible; progress persists.
- [ ] Level-up shown once, accessible, reducible motion.

---

## 13. References

- [UI-SPEC v1](../../../docs/UI-SPEC.md) — baseline
- [Spec v1](../../../.scratch/digest-cds/spec.md)
- [CONTEXT.md](../../../CONTEXT.md)
- [ADR-0001](../../../docs/adr/0001-public-leaderboard-gamification.md)
- Concept 1 prototype: [`../`](../) (Homework_by_project/UI_concepts)
