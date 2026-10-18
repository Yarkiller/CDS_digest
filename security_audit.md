# Отчёт по безопасности — Digest CDS

Аудит проведён для домашнего задания «Настройка CI/CD и интеграция сервисов».
Область: backend (FastAPI, Python 3.12), frontend (React/Vite), CI/CD (GitHub Actions),
контейнеризация (Docker), интеграции (Supabase Auth/OAuth2 Яндекс ID, Яндекс.Метрика).

## Методология и инструменты

| Инструмент | Назначение | Команда |
|---|---|---|
| `npm audit` | уязвимости npm-зависимостей (корень + `web/`) | `npm audit --audit-level=high` |
| `pip-audit` | уязвимости Python-зависимостей | `uv run --with pip-audit pip-audit` |
| `bandit` | SAST Python-кода (CWE) | `uv run --with bandit bandit -r backend/src supabase-integration/src data-collection/src ingestion-service/src` |
| AI security review | разбор диффа + структурная проверка OWASP Top 10 (2021) | Cursor `security-review` subagent + ручной разбор |

Все сканеры выполняются автоматически в CI (job `security` в `.github/workflows/ci.yml`),
поэтому регрессии по зависимостям и коду ловятся на каждом push.

## Сводка

| ID | Серьёзность | Область | Статус |
|---|---|---|---|
| SEC-01 | High | CI/CD (`deploy.yml`) | Исправлено |
| SEC-02 | Medium | Backend (`/health/ready`) | Исправлено |
| SEC-03 | Medium | Frontend (аналитика) | Исправлено |
| SEC-04 | Low | Docker (`.dockerignore`) | Исправлено |
| SEC-05 | Medium | Зависимости (`pyjwt`) | Исправлено |
| SEC-06 | Low | Backend (YAML) | Принято (false positive, `nosec`) |
| SEC-07 | Low | Тестовая поддержка | Принято (test-only, `nosec`) |
| SEC-08 | High | Зависимости (`source-map-js`) | Исправлено (найдено в CI) |
| SEC-09 | High | Зависимости (`multidict`) | Исправлено (найдено в CI) |
| SEC-10 | Medium | Заголовки безопасности (A05) | Исправлено (проверка OWASP Top 10) |

## Найденные и исправленные проблемы

### SEC-01 (High) — Запуск недоверенного кода с секретами в `workflow_run`

**Где:** `.github/workflows/deploy.yml`.
**Суть:** job деплоя, запускаемый по `workflow_run`, делал checkout `head_sha` и запускал
сборку репозитория (`vercel build`) с доступом к `VERCEL_TOKEN`. Условие опиралось только
на фильтр `branches: [main]`, который сопоставляется с именем head-ветки, — этого
недостаточно, чтобы гарантировать, что запуск пришёл именно от push в `main` этого
репозитория, а не из форка/PR с одноимённой веткой.
**Исправление:** добавлено строгое условие `if` для обоих job:

```yaml
github.event.workflow_run.event == 'push' &&
github.event.workflow_run.head_branch == 'main' &&
github.event.workflow_run.head_repository.full_name == github.repository
```

Теперь деплой выполняется только для push в `main` основного репозитория (либо вручную
через `workflow_dispatch`).

### SEC-02 (Medium) — Утечка деталей ошибок в `/health/ready`

**Где:** `backend/src/backend/interface/http/routes/health.py`.
**Суть:** публичный (без авторизации) endpoint возвращал `detail` пробы как есть —
в случае ошибки БД это могло раскрыть строку подключения, хост или текст SDK-ошибки.
**Исправление:** добавлен `ReadinessReport.to_public_dict()`: наружу отдаётся только
`healthy` и нормализованный `detail` (`ok` / `unhealthy`); полный текст остаётся в логах.
Покрыто тестом `test_ready_does_not_leak_probe_error_detail`.

### SEC-03 (Medium) — Передача пользовательских данных в Яндекс.Метрику

**Где:** `web/src/pages/KnowledgePage.jsx`, `web/src/components/AnalyticsPageViews.jsx`.
**Суть:** goal поиска отправлял сырой текст запроса (`{ q }`), а page-view — полный URL
вместе с query-строкой. Это могло отправлять во внешний сервис аналитики
пользовательский ввод и параметры (`returnUrl` и т.п.).
**Исправление:** search-goal отправляет только фильтр роли (`{ role }`); page-view
отправляет только `location.pathname` (без query-строки). Персональные данные не уходят.

### SEC-04 (Low) — `.dockerignore` не исключал вложенные `.env`

**Где:** `.dockerignore`.
**Суть:** шаблоны `.env`/`.env.*` матчили только корень и могли оставить в образе
вложенные файлы (например `web/.env.local`) со значениями окружения.
**Исправление:** добавлены `**/.env` и `**/.env.*`.

### SEC-05 (Medium) — Уязвимая зависимость `pyjwt 2.14.0`

**Где:** `backend/pyproject.toml`.
**Суть:** `pip-audit` обнаружил `PYSEC-2026-4141` (исправлено в `2.15.0`).
**Исправление:** версия поднята до `pyjwt==2.15.0`, `uv.lock` обновлён; после этого
`pip-audit` — `No known vulnerabilities found`.

### SEC-08 (High) — Уязвимая транзитивная зависимость `source-map-js`

**Где:** `web/package-lock.json` (транзитивная зависимость Vite).
**Суть:** `npm audit` в CI обнаружил `GHSA-68fv-2mgg-jv7q` — DoS через offsets
indexed source-map в `source-map-js` `1.0.0–1.2.1`.
**Исправление:** `npm audit fix --prefix web` → `source-map-js 1.2.2`; `npm audit`
(root + web) — `found 0 vulnerabilities`. Сборка и тесты после обновления зелёные.

> Находка получена автоматически из CI-джоба `security` — подтверждает, что аудит
> зависимостей встроен в пайплайн и ловит новые advisories.

### SEC-09 (High) — Уязвимая транзитивная зависимость `multidict`

**Где:** `pyproject.toml` (`[tool.uv] constraint-dependencies`), `uv.lock`.
**Суть:** `pip-audit` в CI обнаружил `CVE-2026-104874` в `multidict 6.9.0`
(тянется через `yarl`).
**Исправление:** добавлен constraint `multidict>=6.9.1` (зафиксировано `7.0.0`);
`pip-audit` — `No known vulnerabilities found`. Тесты, ruff, bandit — зелёные.

### SEC-10 (Medium) — Отсутствовали заголовки безопасности (A05)

**Где:** `backend/.../interface/http/middleware.py`, `backend/.../interface/http/app.py`,
`vercel.json`.
**Суть:** API и SPA не отдавали базовых заголовков безопасности
(`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS) —
это позволяло MIME-sniffing и clickjacking при встраивании страницы в iframe.
**Исправление:** добавлен `SecurityHeadersMiddleware` (backend, покрыт
`tests/unit/test_security_headers.py`) и такой же набор заголовков для SPA в `vercel.json`
(контрактный тест `test_vercel_sets_spa_security_headers`).

## Проверка OWASP Top 10 (2021)

Структурная проверка по категориям с фактическими доказательствами в коде.

| Кат. | Название | Статус | Доказательство / меры |
|---|---|---|---|
| A01 | Broken Access Control | OK | Каждый маршрут за `Depends(get_principal)`; админ-маршруты — `require_admin` (роль из `profiles.role`, не из JWT-claim); path traversal отклоняется в `LocalNotebookStorage` (`..`, абсолютные пути, `relative_to`) + тест `test_http_razbory.py:../outside-secret.ipynb` |
| A02 | Cryptographic Failures | OK | HTTPS на хостингах; `SUPABASE_SECRET_KEY` только на сервере (никогда не `VITE_`); JWT проверяется по ES256 c `audience`/`issuer`/`exp`/`role` (`auth_jwt.py`); секреты не в репо; токены не логируются (SEC-02, middleware) |
| A03 | Injection | OK | Нет склейки SQL — Supabase SDK (параметризованно); XSS: `rehype-sanitize` + sandbox-iframe; YAML парсится `_StrictSafeLoader` (подкласс `SafeLoader`); shell-инъекций нет (нет `subprocess` в пути запроса) |
| A04 | Insecure Design | Частично | Логика голосования (один голос/цикл, запрет правок после закрытия) соблюдена; отсутствует собственный rate-limit на API — принято: аутентификация через Supabase (есть свои лимиты), сервис внутренний. Рекомендация: rate-limit на `/voting` при публичном доступе |
| A05 | Security Misconfiguration | Исправлено | SEC-10: добавлены заголовки безопасности (backend + Vercel); CORS ограничен allow-list `API_CORS_ORIGINS`; `/docs`/`/openapi.json` открыты — принято (внутренний API, риск низкий) |
| A06 | Vulnerable & Outdated Components | OK | `npm audit` + `pip-audit` в CI; исправлены SEC-05/08/09; lockfile'ы зафиксированы (`uv.lock`, `package-lock.json`) |
| A07 | Identification & Authentication Failures | OK | Supabase Auth; JWT-верификация; доменная policy на сервере (`403 domain_not_allowed`); OAuth `redirectTo` из `window.location.origin` (без open redirect); нет фиксации сессии |
| A08 | Software & Data Integrity Failures | OK | SEC-01: `workflow_run` больше не исполняет недоверенный код с секретами; `uv sync --frozen`; сборка/тесты как гейт. Рекомендация: Dependabot |
| A09 | Security Logging & Monitoring Failures | Частично | JSON-логи с `request_id`, уровни по статусу, без секретов; `/health` и `/health/ready` + UptimeRobot. Пробел: нет алерта на всплеск 401/403 — рекомендация |
| A10 | SSRF | OK | Серверные HTTP-вызовы только на фиксированные хосты: YouTube oEmbed (`youtube_oembed.py`, хост задан кодом, URL собирается из video id), DeepSeek/OpenAI `base_url` из env, Supabase URL из env; пользователь не управляет хостом |

**Вывод:** критичных и высоких проблем по OWASP Top 10 не выявлено; единственная новая
находка (A05, SEC-10) исправлена. Практические пробелы (A04 rate-limit, A09 алерты по 401/403)
задокументированы как рекомендации.

Проверено на живых деплоях: backend `…/health` и фронтенд `digest-cds.vercel.app` отдают
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`,
`Permissions-Policy` (backend также HSTS).

## Принятые риски (false positives)

### SEC-06 (Low) — `bandit B506: yaml_load`

`yaml.load(yaml_text, Loader=_StrictSafeLoader)` в
`backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` помечен `# nosec B506`.
`_StrictSafeLoader` — подкласс `yaml.SafeLoader`, добавляющий только отказ на дубликаты
ключей; конструирование произвольных объектов невозможно. Риск отсутствует.

### SEC-07 (Low) — `bandit B101: assert_used`

`assert` в `backend/src/backend/tests_support/in_memory.py` относится к тестовой поддержке,
не к production-коду; помечен `# nosec B101`.

## Проверенные и подтверждённые защиты

- **Секреты не в репозитории:** `.env*` в `.gitignore`; `.env.example` содержит только имена
  переменных. Секреты хостингов — в GitHub Secrets / дашбордах Vercel и Railway.
- **OAuth2 без open redirect:** `redirectTo` строится из `window.location.origin`
  (`web/src/services/authApi.js`), не из пользовательского ввода.
- **Доменная политика на сервере:** backend (`deps.get_principal`) отклоняет
  не-корпоративный email (`403 domain_not_allowed`), включая OAuth-сессии — фронтенд-проверка
  лишь дополняет серверную.
- **CSRF:** авторизация по `Authorization: Bearer` (без cookie-сессий), CORS ограничен
  allow-list `API_CORS_ORIGINS`.
- **XSS:** Markdown рендерится с `rehype-sanitize`; статья выводится в sandbox-iframe.
- **SQL-инъекции:** доступ к данным только через параметризованный Supabase SDK, без
  конкатенации SQL.
- **Логи:** middleware пишет только method/path/status/request_id; `Authorization` не логируется.
- **Readiness:** не раскрывает деталей зависимостей (см. SEC-02).

## Результаты сканеров (после исправлений)

```text
npm audit (root)  → found 0 vulnerabilities
npm audit (web)   → found 0 vulnerabilities
pip-audit         → No known vulnerabilities found
bandit            → Total issues: 0 (High 0, Medium 0, Low 0)
```

## Рекомендации

1. Включить GitHub Dependabot для `uv.lock` и `package-lock.json`, чтобы обновления
   безопасности приходили автоматически.
2. Включить branch protection для `main` с обязательным зелёным CI перед merge.
3. Добавить `gitleaks` в CI для обнаружения случайных секретов в истории.
4. Для продакшена вынести Яндекс.Метрику за согласие (consent) в соответствии с политикой
   обработки данных; при необходимости — ограничить `webvisor`/clickmap.
5. Периодически (раз в квартал) прогонять AI security review по крупным изменениям.
