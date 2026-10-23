# Digest CDS — web app

React-приложение Digest CDS (Vite + React Router + Tailwind CSS v4).

## Запуск

```bash
cd web
npm install
npm run dev
```

Откроется `http://localhost:5173` (hot reload включён).

## Scripts

| Команда | Назначение |
|---------|------------|
| `npm run dev` | Dev-сервер Vite |
| `npm run build` | Production-сборка в `dist/` |
| `npm run preview` | Превью сборки |
| `npm run lint` | Oxlint |

## Структура

```text
src/
├── components/     # AppShell, SearchPill, IssueToc, TopicBallot, ActionButton, …
├── data/mock.js    # mock-данные выпуска, KB, голосования
├── pages/          # issue / voting / knowledge / material
├── utils/
│   ├── filters.js  # фильтрация базы знаний
│   └── delay.js    # общая симуляция loading-latency
├── App.jsx         # роутинг
├── main.jsx
└── index.css       # Tailwind + design tokens
```

Маршруты: `/`, `/voting`, `/knowledge`, `/materials/:id`.

Эталон макетов остаётся в `../design-frontend/`.
