# Digest CDS — канонический дизайн и фронтенд

`design-frontend/` содержит единственный выбранный UI-прототип Digest CDS —
Editorial UI («Digest CDS: издание»). Директория является источником истины
для визуального языка и статического frontend-прототипа.

**Контентный контракт:** материал — только подготовленная агентом статья. Она
создаётся из транскрипции или импортированного текста, дополняется уточняющим
поиском и анализом; видео/аудио и необработанный транскрипт не являются
материалом и не показываются в интерфейсе. Сложные термины связываются
внутренними ссылками с отдельными поясняющими статьями; исходная ссылка
хранится отдельно как provenance.

**Backlog C3 (2026-08-23):** пункты C3-01…C3-18 закрыты в прототипе (см.
[`backlog_UI.md`](../docs/digest-cds/backlog_UI.md)).

## Как открыть

Из корня репозитория запустите статический сервер (Node, без Python):

```bash
npm run serve:design
```

Эквивалент: `npx --yes serve@14.2.4 . -l 8765 --no-port-switching`

Затем откройте
`http://127.0.0.1:8765/design-frontend/index.html`. Конкретные экраны
находятся в `pages/`; для интерактивных stubs нужен HTTP-сервер.

## Карта экранов

| Путь | Экран | Прототипная логика |
|------|-------|--------------------|
| `pages/issue.html` | Текущий выпуск | — |
| `pages/archive.html` | Архив выпусков | — |
| `pages/knowledge.html` | База знаний | фильтры, load more, empty state |
| `pages/material.html` | Подготовленная статья | — |
| `pages/voting.html` | Цикл голосования | выбор и подтверждение |
| `pages/razbory.html` | Список разборов | — |
| `pages/razbor.html` | Разбор longread | — |
| `pages/login.html` | Авторизация | — |
| `pages/admin-digest.html` | Shortlist дайджеста | approve/reject, email preview |

## Структура

```text
design-frontend/
├── index.html
├── README.md
├── UI-SPEC_3.md
├── design.md
├── scripts/app.js
├── styles/
├── assets/
│   ├── covers/
│   └── notebooks/hybrid-retrieval.ipynb
└── pages/
```

## Источники истины

- [`design.md`](design.md) — визуальная система, композиция и правила
  взаимодействия.
- [`styles/tokens.css`](styles/tokens.css) — фактические токены цветов,
  типографики, отступов, радиусов и z-index.
- [`UI-SPEC_3.md`](UI-SPEC_3.md) — самостоятельный контракт дизайна и
  frontend-архитектуры.
