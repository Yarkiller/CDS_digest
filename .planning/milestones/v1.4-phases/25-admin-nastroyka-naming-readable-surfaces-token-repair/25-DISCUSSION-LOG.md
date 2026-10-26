# Phase 25: Admin «Настройка» — naming, readable surfaces, token repair - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-21
**Phase:** 25-admin-nastroyka-naming-readable-surfaces-token-repair
**Areas discussed:** THEME-01 (белые подписи против арифметики контраста)

---

## Выбор зон для обсуждения

Перед обсуждением предъявлены четыре серые зоны; пользователь выбрал одну.

| Зона | Содержание | Выбрана |
|------|------------|---------|
| 1 | Значения токенов `paper`/`paper-2`/`ink`/`ink-2`/`muted`/`rule`/`accent-ink` + судьба инертных утилит (`bg-ink/40`, `bg-paper-2/40`) | |
| 2 | THEME-01: белые подписи против арифметики контраста | ✓ |
| 3 | Chrome 999.2: конкретные числа (кегль, gap, верхний отступ, sr-only h1) | |
| 4 | Гейт покрытия токенов: объём (7 имён vs любая `--color-*`) и место (node vs Playwright) | |

---

## THEME-01 — охват правила

Предъявленная картина: подписи на заливках заданы `text-text-primary`, который переворачивается вместе с темой; в тёмной теме проваливают 4.5:1 все пять заливок (primary 3.87, accent 2.22, voting 1.75, success 2.08, danger 3.44), в светлой — только primary (4.22). Белая подпись на текущих значениях невозможна нигде (лучший случай — primary 4.23).

| Option | Description | Selected |
|--------|-------------|----------|
| all_except_voting | Все пять, кроме voting: primary, accent, success, danger получают постоянную белую подпись и более тёмные значения; voting остаётся жёлтым с постоянной тёмной подписью | ✓ |
| literal_roadmap | Буквально по ROADMAP: только primary + accent + нав-пилл; success/danger остаются нечитаемыми в тёмной теме как известное расхождение | |
| only_visible | Только поверхности, видимые в админке в этой фазе | |

**User's choice:** `all_except_voting`
**Notes:** выбран вариант, закрывающий баг целиком; success/danger иначе остаются с контрастом 2.08 / 3.44 в тёмной теме.

---

## THEME-01 — форма токенов

Предъявленный замер радиуса поражения: `primary` как текст/бордер/тинт живёт в 24 файлах, включая читательские `MaterialPage` (11) и `RazborPage` (11); `accent` — только в 6, почти целиком админка.

| Option | Description | Selected |
|--------|-------------|----------|
| solid_tokens | Отдельные `--color-*-solid` + `--color-on-solid` + `--color-voting-ink`; базовые `primary`/`accent` не меняются, читательская поверхность не ре-темится | ✓ |
| darken_base | Потемнить сами `--color-primary`/`-accent`/`-success`/`-danger`: короткий дифф CSS, но меняет ссылки, focus-ринги и тинты в 24 файлах, включая читательские страницы | |
| hybrid | Потемнить только `--color-primary` глобально, остальные через `-solid` | |

**User's choice:** `solid_tokens`
**Notes:** побочный вывод, зафиксированный сразу — `--color-on-solid` обязан быть чистым `#FFFFFF`: `#F1F5F9` на `danger #DC2626` даёт 4.41 и проваливает порог.

---

## THEME-01 — значения

| Option | Description | Selected |
|--------|-------------|----------|
| minimal | `primary-solid #7C3AED` (5.70), `accent-solid #0E7490` (5.36), `success-solid #15803D` (5.02), `danger-solid #DC2626` (4.83); наименьший сдвиг, `primary-solid` совпадает с существующим `primary-hover` | ✓ |
| margin | С запасом: `#6D28D9` (7.10), `#155E75` (7.27), `#166534`, `#B91C1C` (6.47) — все ≥ 6.4, но кнопки заметно темнее | |
| reuse_hover | Только существующие hover-токены: `accent-hover #0891B2` даёт 3.68 и требует тёмной подписи — правило перестаёт быть единым | |

**User's choice:** `minimal`
**Notes:** худший случай набора — `danger-solid` 4.83; запас должен сохраняться при любых будущих правках.

---

## THEME-01 — судьба `accent-ink`

Предъявленное противоречие: ROADMAP утверждает, что объявление семейства «починит инертные `accent-ink`-подписи», но все три потребителя `accent-ink` — заливки `bg-accent`, которые по решению выше переезжают на `bg-accent-solid text-on-solid`. Дополнительно: семейства `paper`/`ink`/`rule` нет в каноне `design-frontend/styles/tokens.css` — оно пришло из `16-UI-SPEC`.

| Option | Description | Selected |
|--------|-------------|----------|
| drop | Не объявлять `accent-ink`, перевести три места на `bg-accent-solid text-on-solid`; в CONTEXT зафиксировать, что THEME-01 перекрывает соответствующую строку ROADMAP | ✓ |
| declare_tinted | Объявить `accent-ink = #0F172A` как подпись для тинтованных циановых подложек и держать без потребителей | |
| keep_accent_dark | Оставить акцентные кнопки на `bg-accent` с тёмной подписью (7.35) — противоречит критерию 4 ROADMAP | |

**User's choice:** `drop`

---

## Завершение

После четырёх вопросов пользователь выбрал «Готов писать CONTEXT» вместо продолжения по зонам 1, 3, 4 — они записаны в `Claude's Discretion` с констрейнтами из ROADMAP.

## Claude's Discretion

- Значения семейства `paper` / `paper-2` / `ink` / `ink-2` / `muted` / `rule` и судьба инертных утилит (`bg-ink/40` скрайм модалки, `bg-paper-2/40` подложки).
- Абсолютные числа chrome 999.2 (кегль вкладок, gap, верхний отступ, сохранение sr-only `h1`).
- Объём и форма гейта покрытия токенов (критерий 3).

## Deferred Ideas

- Контраст тинтованных чипов (`bg-success/15 text-success`, `bg-voting/20 text-voting`, `bg-primary/15`) — не покрыт критерием 4.
- Возможная отдельная фаза для скрайма модалки, если планировщик выберет светлый `ink`.
- Обновление устаревшей палитры `16-UI-SPEC` § Color под продакшн-значения.
