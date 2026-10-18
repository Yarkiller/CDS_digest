# Сдача домашнего задания — Digest CDS

Индекс артефактов домашнего задания «Настройка CI/CD и интеграция сервисов».
Все материалы доступны в репозитории и развёрнуты в интернете.

**Репозиторий:** https://github.com/Yarkiller/digest_cds (ветка `main`)
**Работающее приложение:** https://digest-cds.vercel.app
**API (backend):** https://digest-cds-api-production.up.railway.app
**CI/CD:** https://github.com/Yarkiller/digest_cds/actions

Пути ниже — относительно корня репозитория; ссылки ведут на ветку `main`.

---

## Обязательные артефакты сдачи

| Требование задания | Файл / ресурс | Путь в репозитории | Ссылка |
|---|---|---|---|
| Документация по интеграциям | `integration_documentation.md` | [`integration_documentation.md`](integration_documentation.md) | [открыть](https://github.com/Yarkiller/digest_cds/blob/main/integration_documentation.md) |
| Отчёт по безопасности | `security_audit.md` | [`security_audit.md`](security_audit.md) | [открыть](https://github.com/Yarkiller/digest_cds/blob/main/security_audit.md) |
| README (обновлён) | `README.md` | [`README.md`](README.md) | [открыть](https://github.com/Yarkiller/digest_cds/blob/main/README.md) |
| Конфигурация CI/CD | `ci.yml` + `deploy.yml` | [`.github/workflows/ci.yml`](.github/workflows/ci.yml), [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | [CI](https://github.com/Yarkiller/digest_cds/blob/main/.github/workflows/ci.yml) · [Deploy](https://github.com/Yarkiller/digest_cds/blob/main/.github/workflows/deploy.yml) |
| Код с интеграциями | OAuth2 + аналитика (frontend/backend) | см. «Шаг 3–4» ниже | — |
| Работающее приложение | Vercel + Railway | — | [digest-cds.vercel.app](https://digest-cds.vercel.app) |

---

## Артефакты по шагам задания

### Шаг 1. Настройка CI/CD пайплайна
- **CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — jobs `lint` (ruff + oxlint),
  `backend-tests` (pytest), `frontend-tests` (node:test + vite build), `security`
  (npm audit + pip-audit + bandit), `e2e` (Playwright), `docker` (сборка образа + health smoke).
- **CD (автодеплой при push в `main`):** [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) —
  Vercel (фронтенд) + Railway (бэкенд) + post-deploy smoke живых URL.
- **Конфиги деплоя:** [`Dockerfile`](Dockerfile), [`.dockerignore`](.dockerignore),
  [`railway.json`](railway.json), [`vercel.json`](vercel.json), [`web/vercel.json`](web/vercel.json),
  [`render.yaml`](render.yaml) (альтернатива Railway), [`.vercelignore`](.vercelignore).
- **Проверки качества кода:** ruff (Python) + oxlint (JS) в job `lint`.
- **Проверка пайплайна:** зелёные прогоны в [Actions](https://github.com/Yarkiller/digest_cds/actions).
- **Описание:** `integration_documentation.md` §2 (CI/CD) и §0 (быстрый старт).

### Шаг 2. Аудит безопасности
- **Отчёт:** [`security_audit.md`](security_audit.md) — находки SEC-01…SEC-10 со статусами,
  проверенные/подтверждённые защиты, принятые риски, **раздел «Проверка OWASP Top 10 (2021)»**,
  результаты сканеров, рекомендации.
- **Инструменты:** `npm audit`, `pip-audit`, `bandit`, AI security review (запускаются в CI).
- **Исправления в коде:** заголовки безопасности
  ([`middleware.py`](backend/src/backend/interface/http/middleware.py),
  [`vercel.json`](vercel.json)), обновления зависимостей (`pyjwt`, `source-map-js`, `multidict`),
  guard деплоя ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)),
  приватность аналитики.
- **Тесты:** [`tests/unit/test_security_headers.py`](tests/unit/test_security_headers.py).

### Шаг 3. Интеграция OAuth2 (Яндекс ID через Supabase)
- **Frontend:** [`web/src/services/oauthSession.js`](web/src/services/oauthSession.js),
  [`web/src/services/authApi.js`](web/src/services/authApi.js) (`signInWithYandex`),
  [`web/src/pages/LoginPage.jsx`](web/src/pages/LoginPage.jsx),
  [`web/src/components/RequireAuth.jsx`](web/src/components/RequireAuth.jsx).
- **Backend (проверка JWT + доменная политика):**
  [`backend/src/backend/interface/http/deps.py`](backend/src/backend/interface/http/deps.py),
  [`backend/src/backend/infrastructure/auth_jwt.py`](backend/src/backend/infrastructure/auth_jwt.py).
- **Тесты:** [`tests/unit/test_oauth_session.js`](tests/unit/test_oauth_session.js),
  [`tests/auth.spec.js`](tests/auth.spec.js) (Playwright: кнопка, отказ для не-корпоративного домена, успешный вход).
- **Инструкция:** `integration_documentation.md` §3 (шаг 2) и §4.

### Шаг 4. Интеграция аналитики (Яндекс.Метрика)
- **Модуль:** [`web/src/services/analytics.js`](web/src/services/analytics.js),
  [`web/src/services/analyticsRuntime.js`](web/src/services/analyticsRuntime.js),
  [`web/src/components/AnalyticsPageViews.jsx`](web/src/components/AnalyticsPageViews.jsx).
- **События:** `login`, `login_oauth`, `vote`, `search`, `material_open`, `digest_send`.
- **Счётчик:** `113475972` (`VITE_YM_COUNTER_ID` в Vercel).
- **Тесты:** [`tests/unit/test_analytics.js`](tests/unit/test_analytics.js).
- **Инструкция:** `integration_documentation.md` §3 (шаг 3) и §5.

### Шаг 5. Платежи (опционально)
- Не интегрированы: обязательный минимум (2 сервиса) закрыт OAuth2 + аналитикой.
  Обоснование — в `integration_documentation.md` (решения).

### Шаг 6. Мониторинг и Health Check
- **Эндпоинты:** `GET /health` (liveness) и `GET /health/ready` (проверка БД) —
  [`backend/src/backend/interface/http/routes/health.py`](backend/src/backend/interface/http/routes/health.py).
- **Порт + use-case:** [`health_probe.py`](backend/src/backend/application/ports/health_probe.py),
  [`check_readiness.py`](backend/src/backend/application/use_cases/check_readiness.py),
  [`supabase_integration/health_probe.py`](supabase-integration/src/supabase_integration/health_probe.py).
- **Тесты:** [`tests/unit/test_http_health_ready.py`](tests/unit/test_http_health_ready.py),
  [`tests/unit/test_supabase_health_probe_contract.py`](tests/unit/test_supabase_health_probe_contract.py).
- **Внешний мониторинг + алерты:** `integration_documentation.md` §6 (URL-ы мониторов UptimeRobot).

### Шаг 7. Логирование
- **JSON-логи + уровни:** [`backend/src/backend/interface/http/middleware.py`](backend/src/backend/interface/http/middleware.py)
  (structlog, `LOG_LEVEL`, уровни по статусу), [`backend/src/backend/composition/settings.py`](backend/src/backend/composition/settings.py).
- **Централизованное хранение:** логи Railway (backend) и Vercel (frontend).
- **AI-промпты для анализа логов:** [`docs/agents/log-analysis-prompts.md`](docs/agents/log-analysis-prompts.md).
- **Тесты:** [`tests/unit/test_logging_config.py`](tests/unit/test_logging_config.py).
- **Инструкция:** `integration_documentation.md` §7.

### Шаг 8. Тестирование и оптимизация
- **Тесты:** `uv run pytest` (795), `npm run test:js` (JS unit), `npx playwright test --project=web` (E2E).
- **Оптимизация:** immutable-кэш ассетов в [`vercel.json`](vercel.json) (Шаг 8); рекомендации по
  code-splitting — `integration_documentation.md` (оптимизация).
- **Доказательства:** `integration_documentation.md` §11.

### Шаг 9. Оформление результатов
- [`integration_documentation.md`](integration_documentation.md) — настройки CI/CD, инструкции по
  интеграциям, отчёт по безопасности, мониторинг/логирование, примеры конфигураций, порядок
  получения ключей.
- [`security_audit.md`](security_audit.md) — отчёт по безопасности.
- [`README.md`](README.md) — ссылки на деплой и документацию.
- **Использование AI** задокументировано в `integration_documentation.md` §9 и
  [`docs/digest-cds/ai_session_notes.md`](docs/digest-cds/ai_session_notes.md).

---

## Вспомогательная документация проекта

| Документ | Путь |
|---|---|
| Шаблон переменных окружения | [`.env.example`](.env.example) |
| Runbook локального запуска платформы | [`docs/agents/local-platform-runbook.md`](docs/agents/local-platform-runbook.md) |
| Отчёт о разработке | [`development_report.md`](development_report.md), [`docs/digest-cds/development_report.md`](docs/digest-cds/development_report.md) |
| Промпты для анализа логов | [`docs/agents/log-analysis-prompts.md`](docs/agents/log-analysis-prompts.md) |
| ADR (архитектурные решения) | [`docs/adr/`](docs/adr/) |
| ТЗ и критерии приёмки | [`docs/digest-cds/technical_specification.md`](docs/digest-cds/technical_specification.md), [`docs/digest-cds/acceptance_criteria.md`](docs/digest-cds/acceptance_criteria.md) |

---

## Соответствие критериям приёмки

| Критерий | Статус | Доказательство |
|---|---|---|
| CI/CD настроен и работает, включая проверки качества | Готово | `ci.yml`, зелёные [Actions](https://github.com/Yarkiller/digest_cds/actions) |
| Автодеплой при push в `main` | Готово | Vercel Git + Railway deployment trigger; `deploy.yml` + post-deploy smoke |
| Минимум 2 интеграции (OAuth2 + аналитика) | Готово | Шаг 3, Шаг 4 |
| Аудит безопасности с отчётом | Готово | `security_audit.md` (в т.ч. OWASP Top 10) |
| Мониторинг: Health Check endpoints | Готово | `/health`, `/health/ready` (живые) |
| Логирование (JSON, уровни) | Готово | `middleware.py`, `LOG_LEVEL` |
| Документация полная и понятная | Готово | `integration_documentation.md`, `security_audit.md`, `README.md` |
| Использование AI задокументировано | Готово | `integration_documentation.md` §9, `ai_session_notes.md` |

---

## Текущий статус деплоя

| Компонент | URL | Проверка |
|---|---|---|
| Frontend | https://digest-cds.vercel.app | HTTP 200; экран входа обязателен |
| Backend liveness | https://digest-cds-api-production.up.railway.app/health | `{"status":"ok"}` |
| Backend readiness | https://digest-cds-api-production.up.railway.app/health/ready | `{"status":"ready", … база healthy}` |
| Аналитика | счётчик 113475972 | работает на проде |
| Автодеплой frontend / backend | Vercel / Railway | подтверждён push-ом в `main` |

Ветки: рабочая `temp/homework-submission` синхронизирована с `main`.
