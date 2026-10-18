# Отчёт о разработке (Digest CDS — ДЗ)

## 1. Цель и результат

Инициализировано веб-приложение Digest CDS на **Vite + React + React Router + Tailwind CSS** по макетам Editorial (Concept 3). Реализованы минимум три пользовательские функции: **выпуск/материал**, **голосование**, **база знаний**. Покрытие — Playwright (основные сценарии, состояния UI, edge/error, адаптив).

Репозиторий GitHub: [https://github.com/Yarkiller/digest_cds](https://github.com/Yarkiller/digest_cds)  
Ветка работы: `feature/yarkiller/homework-react-app`

Демо: локальный запуск (см. README); деплой на Vercel/Netlify не обязателен для сдачи при наличии инструкций.

## 2. Процесс разработки

Работа велась пошагово с AI-агентом (Cursor), с явным согласованием каждого шага ДЗ.

| Шаг | Содержание | Артефакт |
|-----|------------|----------|
| 1 | Фиксация стека и ≥3 функций в ТЗ | `docs/digest-cds/technical_specification.md`, README |
| 2 | Scaffold Vite/React/Tailwind | `web/` |
| 3 | Компоненты + mock-данные | `web/src/{components,pages,data}` |
| 4 | Состояния loading / empty / error / success | `ActionButton`, Voting/Knowledge |
| 5 | Расширение тестов + AI-отладка | `tests/web-app.spec.js`, `ai_session_notes.md` |
| 6 | Адаптив + скриншоты | [`docs/digest-cds/responsive-evidence/`](docs/digest-cds/responsive-evidence/) |
| 7–8 | Рефактор, отчёт, инструкции запуска | этот файл, README |

Обязательный цикл: **Red → Green → Refactor** ([`AGENTS.md`](AGENTS.md), [`.cursor/rules/tdd.mdc`](.cursor/rules/tdd.mdc)). Production-код писался только после падающего теста (кроме конфигов/scaffold).

Эталон UX остаётся в `design-frontend/`; приложение ДЗ — в `web/`.

## 3. Взаимодействие с AI

### 3.1. Роли

- Генерация структуры Vite/React и маршрутов
- Перенос Editorial-токенов в Tailwind `@theme`
- Написание Playwright-сценариев по ТЗ и acceptance criteria
- Мультимодальный разбор скриншота (модалка поиска)
- Предложение media-query / breakpoint-стратегии
- Рефактор дублирующейся задержки UI (`delay.js`)

### 3.2. Примеры эффективных промптов / приёмов

1. «Сначала падающий Playwright-тест на поведение X, затем минимальный фикс» — удерживает TDD.
2. Скриншот модалки + «убери дубли header, оставь поле / убери модалку» — визуальная отладка без догадок.
3. «Проверь overflow на 320px» — выявил реальный баг `min-w-[240px]`.

### 3.3. Ограничения AI

- Context7 MCP в сессии был недоступен — документация Tailwind/Vite бралась с официальных источников.
- Слишком общие формулировки давали лишние «spotlight»-паттерны; точные UX-ограничения («без модалки») срабатывали лучше.

## 4. Проблемы и решения

| Проблема | Как обнаружена | Решение |
|----------|----------------|---------|
| Модалка поиска дублировала навигацию | Скриншот пользователя + AI-разбор | Inline-поиск в шапке |
| Поиск не передавал запрос в БЗ | Расширение теста шага 5 | `/knowledge?q=` + seed фильтров |
| Overflow на 320px | Playwright viewport-тест | `min-w-0 sm:min-w-[240px]` |
| Локатор кнопки голоса ломался при смене текста | Падение loading-assert | `data-testid="confirm-vote"` |
| Слишком короткая latency для loading | Флап тестов | Общий `UI_LATENCY_MS` (~600) |
| `python` в Playwright ломал Mac | Ревью ДЗ | Node `serve` + фильтр webServer по `--project` |
| Слабый error-state голоса | Ревью ДЗ | `votingApi` + `VoteSubmitError` + `ErrorPanel` |

## 5. Применённые техники и оценка

| Техника | Эффект |
|---------|--------|
| TDD (Playwright first) | Регрессии ловятся до ручной приёмки |
| Состояния UI (idle/loading/success/empty) | Соответствие Concept 3 и критериям ДЗ |
| Mobile-first Tailwind breakpoints | Адаптив без отдельного CSS-файла |
| Мультимодальный ревью скриншотов | Быстрый UX-фикс поиска и доказательная база шага 6 |
| Разделение design-frontend / web | Макеты не смешиваются с приложением ДЗ |

## 6. Тестирование

Команды: `npm test` / `npm run test:web` / `npm run test:design`.

Статический сервер макетов — Node (`serve`), без Python. При `--project=web` поднимается только Vite.

Web-приложение (`tests/web-app.spec.js`), группы:

- **Основные функции** — выпуск→материал, голосование, фильтр тега
- **Состояния** — loading/success/error, empty recovery, skeleton, header search
- **Edge/error** — неизвестный материал, disabled без выбора, сбой сохранения голоса + retry (`?simulateError=1`)
- **Адаптив** — 320/390/1280; скриншоты: [`docs/digest-cds/responsive-evidence/`](docs/digest-cds/responsive-evidence/)
  - [mobile-320-issue.png](docs/digest-cds/responsive-evidence/mobile-320-issue.png)
  - [mobile-390-issue.png](docs/digest-cds/responsive-evidence/mobile-390-issue.png)
  - [mobile-390-voting.png](docs/digest-cds/responsive-evidence/mobile-390-voting.png)
  - [desktop-1280-issue.png](docs/digest-cds/responsive-evidence/desktop-1280-issue.png)
  - оглавление: [`README.md`](docs/digest-cds/responsive-evidence/README.md)

Эталон макетов дополнительно покрыт `tests/design-frontend.spec.js`.

## 7. Структура кода после рефакторинга

```text
web/src/
├── components/     # shell, поиск, TOC, ballot, ErrorPanel, кнопки состояний
├── pages/          # маршруты экранов
├── services/       # mock API (votingApi с typed errors)
├── data/mock.js    # контент для UI
├── utils/
│   ├── filters.js  # фильтрация базы знаний
│   ├── voting.js   # статусы/лейблы голосования
│   └── delay.js    # общая симуляция latency
├── App.jsx
└── index.css       # Tailwind + токены Editorial
```

Удалены неиспользуемые scaffold-ассеты Vite. Общая задержка loading вынесена в `utils/delay.js`.

## 8. Выводы и рекомендации

1. Статический прототип ускорил согласование UX; перенос в React потребовал отдельного тестового контура (`web` project на порту 5174).
2. TDD окупается на UI-состояниях и адаптиве — баги 320px и hand-off поиска пойманы автотестами.
3. Дальше: бэкенд API вместо mock, деплой preview, a11y-аудит (фокус-ловушки, live regions).

Рабочие заметки сессии: [`docs/digest-cds/ai_session_notes.md`](docs/digest-cds/ai_session_notes.md).
