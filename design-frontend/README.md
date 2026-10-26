# Digest CDS — Concept 2 (Visual)

Dark-first канон по [UI-SPEC_2.md](./UI-SPEC_2.md). Зафиксирован в
[ADR-0009](../docs/adr/0009-concept2-canon-dark-light-no-gamification.md):
тёмная тема по умолчанию, светлая через `[data-theme="light"]`, геймификация
исключена из релиза ([ADR-0007](../docs/adr/0007-drop-gamification-supersedes-0001.md)).

## Открыть

`index.html` → галерея экранов релиза. Сборка не нужна.

## Экраны релиза

| Файл | Описание |
|------|----------|
| `pages/home.html` | Главная: выпуск, материалы, голосование |
| `pages/material.html` | Статья |
| `pages/voting.html` | Голосование |
| `pages/login.html` | Auth + theme toggle |

## Следующая версия (не входит в релиз)

Вариант UI для геймификации сохранён как референс. Эти страницы **не линкуются
из навигации**, не входят в `index.html` и не имеют production-маршрутов —
открывать напрямую по файлу.

| Файл | Описание |
|------|----------|
| `pages/home-gamified.html` | Геймифицированная главная целиком: квест, XP-профиль, мини-лидерборд |
| `pages/leaderboard.html` | Публичный лидерборд, top-3 glow |
| `pages/profile.html` | XP, достижения hex-badge, настройки opt-out |
| `pages/quiz.html` | Карточка с вопросами: progress dots, ScoreRing |

Токены отложенного варианта (`--color-xp`, `--color-stat`, `--color-rank-*`)
остаются в `styles/tokens.css`, чтобы следующая версия не изобретала палитру
заново. В production они не используются.

## Фичи канона

- Dark theme по умолчанию, toggle ☀/☽ (`localStorage`, ключ `digest-cds-theme`)
- Manrope + JetBrains Mono
- Обложки материалов в `assets/covers/` (5 PNG + SVG)

## Concept 1 / Concept 3

`Concept_1` и `Concept_3` не входят в текущий канон. Concept 3 (editorial) был
каноном между ADR-0006 и ADR-0009 и снят этим решением.
