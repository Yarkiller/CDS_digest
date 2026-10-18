# Документация по интеграциям и CI/CD — Digest CDS

Документ описывает настройку CI/CD, интеграцию внешних сервисов (OAuth2 Яндекс ID,
Яндекс.Метрика), мониторинг, логирование и порядок получения ключей.

Связанные документы:

- Отчёт по безопасности: [`security_audit.md`](security_audit.md)
- AI-промпты для анализа логов: [`docs/agents/log-analysis-prompts.md`](docs/agents/log-analysis-prompts.md)
- Локальный запуск: [`README.md`](README.md), [`docs/agents/local-platform-runbook.md`](docs/agents/local-platform-runbook.md)

---

## 0. Быстрый старт: включить автодеплой (пошагово, для новичка)

Цель: чтобы после merge в `main` фронтенд сам развернулся на Vercel, а backend — на Railway.

> **Важно:** ключи Supabase уже есть — в локальном файле `.env` (строки `SUPABASE_URL`,
> `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_ISSUER`).
> Получать их не нужно, достаточно скопировать значения оттуда в панели хостингов.

### Часть A. Vercel (фронтенд)

1. Откройте <https://vercel.com> → **Sign Up** → **Continue with GitHub** → разрешите доступ.
2. Нажмите **Add New… → Project** → в списке найдите репозиторий **digest_cds** →
   **Import**. (Если репозитория нет — нажмите «Adjust GitHub App Permissions» и дайте доступ.)
3. Framework Preset определится как **Vite** (настройки берутся из `vercel.json`).
   **Root Directory** оставьте пустым (корень репозитория). Если Vercel подставил `web` —
   тоже допустимо: в `web/vercel.json` есть такой же SPA-роутинг как страховка.
   Ничего не меняйте → **Deploy**. Дождитесь сборки.
4. Создайте токен для CI: правый верхний угол → **Settings** (аккаунт) → **Tokens** →
   **Create Token** → имя `github-actions` → **Create** → **скопируйте строку** (показывается
   один раз). Это значение `VERCEL_TOKEN`.
5. Узнайте ID проекта и аккаунта: **Project → Settings → General**.
   - `Project ID` → это `VERCEL_PROJECT_ID`.
   - `Team ID` (или Org ID; у личного аккаунта — в **Account Settings → General**) → `VERCEL_ORG_ID`.
6. Переменные приложения: **Project → Settings → Environment Variables** → добавьте (Environment: Production):

   | Name | Value |
   |---|---|
   | `VITE_SUPABASE_URL` | скопируйте из `.env` (значение `SUPABASE_URL`) |
   | `VITE_SUPABASE_PUBLISHABLE_KEY` | скопируйте из `.env` (`SUPABASE_PUBLISHABLE_KEY`) |
   | `VITE_API_BASE_URL` | URL backend из Части B (получите на шаге B1) |
   | `VITE_USE_MOCKS` | `false` |
   | `VITE_ENABLE_YANDEX_OAUTH` | `true` |
   | `VITE_YANDEX_OAUTH_PROVIDER` | `custom:yandex` |
   | `VITE_YM_COUNTER_ID` | номер счётчика Метрики (см. Часть D) |

7. Добавьте секреты в GitHub: репозиторий → **Settings → Secrets and variables → Actions →
   New repository secret** — по одному: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.

### Часть B. Railway (backend)

1. Откройте <https://railway.app> → **Login with GitHub** → **New Project** →
   **Deploy from GitHub repo** → выберите **digest_cds**.
   Railway найдёт `Dockerfile` и `railway.json` сам.
2. **Settings → Networking → Generate Domain** → появится публичный URL (например
   `https://digest-cds-api.up.railway.app`). Это `VITE_API_BASE_URL` для Части A, шаг 6.
3. **Variables → New Variable** — добавьте:

   | Name | Value |
   |---|---|
   | `APP_CONTAINER` | `live` |
   | `SUPABASE_URL` | из `.env` |
   | `SUPABASE_SECRET_KEY` | из `.env` |
   | `SUPABASE_JWKS_URL` | из `.env` |
   | `SUPABASE_JWT_ISSUER` | из `.env` |
   | `ALLOWED_EMAIL_DOMAINS` | `@sberbank.ru,@omega.sbrf.ru` |
   | `API_CORS_ORIGINS` | URL Vercel, например `https://digest-cds.vercel.app` |
   | `SITE_URL` | то же, `https://digest-cds.vercel.app` |
   | `LOG_LEVEL` | `info` |

4. Создайте deploy hook: **Settings → Deploy → Deploy Hook** → скопируйте URL →
   добавьте в GitHub Secrets как `RAILWAY_DEPLOY_HOOK`.

### Часть C. Запуск автодеплоя

> **Уже настроено:** push в `main` автоматически деплоит и фронтенд (Vercel Git), и backend
> (Railway deployment trigger на ветку `main`). Проверено эмпирически (см. Часть E).

1. Убедитесь, что секреты добавлены (шаги A7, B4) — только если хотите деплой через workflow
   `Deploy` в GitHub Actions. Нативные git-интеграции работают и без них.
2. Влейте изменения в `main` (merge или push) — `main` уже синхронизирован.
3. Вкладка **Actions** → workflow **Deploy** → запускается автоматически после зелёного **CI**.
4. Проверьте: URL Vercel (фронтенд) открывается; `https://<railway-domain>/health/ready`
   возвращает `{"status":"ready",...}`.

### Часть D. OAuth2 (Яндекс ID) и Метрика — кратко

Ещё не сделано? Не обязательно для деплоя. Когда будете готовы — инструкции в §3 (шаги 2–3)
и §5. Там же, как провести **успешный** Яндекс-вход (через `VITE_ALLOWED_EMAIL_DOMAINS`).

### Часть E. Статус деплоя (LIVE)

- **Frontend LIVE:** [https://digest-cds.vercel.app](https://digest-cds.vercel.app) —
  Vercel-проект `digest-cds` (team `bender-s-park`). Проверено: HTTP 200, отдаётся наш бандл,
  deep-link `/voting` и `/knowledge` работают (SPA-rewrite). В сборку «запечены»
  OAuth-кнопка Яндекс ID, `custom:yandex` и адрес Railway API.
- **Backend LIVE:** [https://digest-cds-api-production.up.railway.app](https://digest-cds-api-production.up.railway.app) —
  Railway-сервис `digest-cds-api` (source `Yarkiller/digest_cds`, ветка `main`, Docker).
  Проверено: `GET /health` → `200 {"status":"ok"}`;
  `GET /health/ready` → `200 {"status":"ready","components":{"database":{"healthy":true,...}}}`;
  CORS preflight с origin `https://digest-cds.vercel.app` → `200`.
  Переменные окружения сервиса заданы (`APP_CONTAINER=live`, `SUPABASE_*`, `ALLOWED_EMAIL_DOMAINS`,
  `API_CORS_ORIGINS`, `SITE_URL`, `LOG_LEVEL`).
- **Аналитика live:** Яндекс.Метрика, счётчик **113475972** (`VITE_YM_COUNTER_ID` в Vercel).
  Проверено в продакшн-бандле: присутствуют `mc.yandex.ru`, `tag.js`, `?id=`, `webvisor`,
  `dataLayer`, `reachGoal`, `accurateTrackBounce`, число `113475972`. Page-view уходит на каждой
  смене маршрута; события — `login/login_oauth/vote/search/material_open/digest_send`.
- **Экран входа обязателен (`VITE_REQUIRE_LOGIN=true`):** открытие сайта переводит на `/login`
  (форма входа), а не показывает мок-пользователя. После входа в шапке отображается введённый
  email. Проверено headless-браузером на живом URL: `/` → `/login?returnUrl=%2F`, поле email
  видно, текста «Мария Сидорова» нет, после входа identity = `analyst@sberbank.ru`.
- **Боевой режим (`VITE_USE_MOCKS=false`):** приложение использует реальный Supabase Auth
  (`VITE_SUPABASE_URL=https://knowledge-db.ru`, `VITE_SUPABASE_PUBLISHABLE_KEY`) и живой backend
  на Railway (`APP_CONTAINER=live`). В БД Supabase есть данные: материалы (`ready`), разборы
  (published/announcement), профили. Тестовые учётные записи: `test@sberbank.ru` (роль admin),
  `yarkiller@sberbank.ru` (employee), `test2@omega.sbrf.ru`, `uat3.…@sberbank.ru` — все с
  подтверждённым корпоративным email.
- **Автодеплой frontend:** Vercel Git-интеграция подключена к `Yarkiller/digest_cds`,
  production branch `main` — push в `main` автоматически запускает сборку и деплой.
  Проверено эмпирически: push `609b41d` → Vercel-деплой `source=git`, `target=production`, `READY`.
- **Автодеплой backend:** включён (Railway deployment trigger на ветку `main`,
  `deploymentTriggerCreate` → id `d02db748-ca51-41d2-a4ec-969365558403`).
  Проверено эмпирически: push `3a7f4f1` → Railway **сам** создал деплой
  (id `c246e806-3dd6-4351-815a-63aa643a954e`, `createdAt 12:48:20Z`, `SUCCESS`) без ручного запуска.
- **Значения для GitHub Secrets (Vercel):** `VERCEL_ORG_ID` = `team_ZOvU4Mna7rW6Mcch7xZA5WJs`,
  `VERCEL_PROJECT_ID` = `prj_aPuyodDVW8W4V4slflvWcpDgFIwq`, `VERCEL_TOKEN` = ваш токен.
  (Фронтенд и backend уже деплоятся по push через нативные git-интеграции — секреты GitHub
  для деплоя не обязательны; workflow `Deploy` остаётся дополнительным каналом.)
- **Осталось для полного автодеплоя по push:** добавить GitHub Secrets (`VERCEL_TOKEN`,
  `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `RAILWAY_DEPLOY_HOOK`) — либо включить в дашбордах
  авто-деплой: Vercel → Git Integration, Railway → Settings → Auto Deploy.
  Deploy Hook URL: Railway → сервис `digest-cds-api` → Settings → Deploy → Deploy Hook.

---

## 1. Архитектура и потоки

```mermaid
flowchart LR
  Dev[Разработчик] -->|push/PR| GH[GitHub Actions]
  GH --> Lint[lint]
  GH --> Test[test: pytest + node:test]
  GH --> Build[build: vite]
  GH --> SecScan[security: npm audit + pip-audit + bandit]
  GH --> E2E[e2e: Playwright]
  GH -->|main, CI зелёный| Vercel
  GH -->|main, CI зелёный| Railway
  Vercel[Vercel: React SPA] -->|REST + JWT| Railway[Railway: FastAPI]
  Railway --> Supa[(Supabase: Postgres/Auth)]
  Browser[Браузер] --> Vercel
  Vercel --> Metrika[Yandex Metrika]
  Uptime[UptimeRobot] --> Vercel
  Uptime --> Railway
```

- **Frontend** — Vercel (статика Vite SPA).
- **Backend** — Railway (Docker, FastAPI + uv workspace).
- **Auth** — Supabase Auth (email/пароль + OAuth2 Яндекс ID).
- **Аналитика** — Яндекс.Метрика.
- **Мониторинг** — health-check endpoints + внешний мониторинг (UptimeRobot).
- **Логи** — структурированный JSON (`structlog`) → логи Railway/Vercel.

---

## 2. CI/CD (GitHub Actions)

### 2.1. Файлы

| Файл | Назначение |
|---|---|
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | lint, unit, build, security, e2e — на каждый `push`/PR |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | деплой на Vercel и Railway после успешного CI на `main` |

### 2.2. Стадии CI

| Job | Что делает |
|---|---|
| `lint` | `uv run ruff check .`, `npm run lint --prefix web` (oxlint) |
| `backend-tests` | `uv sync --frozen`, `uv run pytest -q` |
| `frontend-tests` | `npm ci`, `node --test`, `npm run build` |
| `security` | `npm audit` (root + web), `pip-audit`, `bandit` |
| `e2e` | Playwright (`--project=web`), отчёт выгружается в artifact |
| `docker` | сборка backend-образа по `Dockerfile` + запуск контейнера и smoke-проверка `/health` и `/health/ready` |

Контрактные тесты deploy-конфигов: [`tests/unit/test_deploy_configs.py`](tests/unit/test_deploy_configs.py)
(SPA-rewrite и immutable-кэш Vercel, health-чек Railway/Render, отсутствие секретов в
`render.yaml`, стадии CI, guard деплоя, корректный workspace-install в Dockerfile).

### Оптимизация (Шаг 8)

Рекомендации получены с помощью AI по итогам сборки и проверены:

- **Кэширование статики на Vercel** (применено): `Cache-Control: public, max-age=31536000, immutable`
  для `/assets/*` (хешированные бандлы Vite) и недельный кэш для `/covers/*` — повторные заходы
  не перекачивают бандлы.
- **Разбиение чанков** (рекомендация, не применена): сборка предупреждает о чанке > 500 kB
  (`index-*.js` ~760 kB). Безопасный следующий шаг — `build.rolldownOptions.output` code-splitting
  для vendor-зависимостей (`react`, `@supabase/supabase-js`); требует отдельной проверки
  Playwright, поэтому вынесено как рекомендация.
- **Docker-образ** (проверено): многоступенчатая установка (`--no-install-workspace` → `--no-install-project`)
  переиспользует кэш слоёв и не тянет dev-зависимости (`--no-dev`); образ собирается CI-job `docker`.

### 2.3. Автодеплой

`deploy.yml` запускается по `workflow_run` **только** когда CI на `main` завершился успешно
и запуск пришёл от push в основной репозиторий:

```yaml
github.event.workflow_run.event == 'push' &&
github.event.workflow_run.head_branch == 'main' &&
github.event.workflow_run.head_repository.full_name == github.repository
```

Это защищает секреты от выполнения недоверенного кода (см. SEC-01 в `security_audit.md`).

- Frontend → Vercel CLI (`vercel pull/build/deploy --prod`).
- Backend → POST на Railway Deploy Hook.
- **Post-deploy smoke** (`smoke`): после деплой-job автоматически проверяет живые URL —
  фронтенд отвечает `200`, а `/health/ready` возвращает `"status":"ready"`. Так пайплайн
  подтверждает, что развёрнутое приложение действительно работает.

Если тот или иной секрет не задан, соответствующий job печатает «skipped» и не падает —
пайплайн остаётся зелёным до момента, когда вы добавите ключи.

### 2.4. Как проверить пайплайн

1. Закоммитить и запушить в любую ветку → откроется run `CI`.
2. Открыть вкладку Actions → убедиться, что все job зелёные.
3. Для деплоя — merge/push в `main`; после успешного CI запустится `Deploy`.

---

## 3. Порядок получения ключей и переменные

Выполняйте шаги по порядку. Имена переменных указаны точно — под ними значения
добавляются в `.env` (локально) или в GitHub Secrets / дашборды хостингов.

### Шаг 1. Supabase (уже используется проектом)

Из Supabase Dashboard → Project Settings → API взять:

| Переменная | Где взять | Назначение |
|---|---|---|
| `SUPABASE_URL` | Project URL | backend |
| `SUPABASE_PUBLISHABLE_KEY` | `anon`/publishable key | frontend (публичный) |
| `SUPABASE_SECRET_KEY` | `service_role`/secret key | backend (только сервер!) |
| `SUPABASE_JWKS_URL` | `…/auth/v1/.well-known/jwks.json` | проверка JWT |
| `SUPABASE_JWT_ISSUER` | `https://<ref>.supabase.co/auth/v1` | проверка JWT |
| `VITE_SUPABASE_URL` | = `SUPABASE_URL` | frontend |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | = `SUPABASE_PUBLISHABLE_KEY` | frontend |

> `SUPABASE_SECRET_KEY` никогда не попадает в `VITE_`-переменные.

### Шаг 2. OAuth2 — Яндекс ID (через Supabase custom provider)

**Важно:** Яндекс не входит в список встроенных провайдеров Supabase. Его нужно
подключить как **custom OAuth2 provider** с идентификатором `custom:yandex`.

2.1. Создать приложение Яндекс ID:

1. Открыть <https://oauth.yandex.ru/client/new> → **«Для авторизации пользователей»**.
2. Платформа — **Веб-сервисы**. В поле **Redirect URI** указать:
   `https://<project-ref>.supabase.co/auth/v1/callback`
3. Доступы (scopes): `login:email`, `login:info`.
4. Сохранить. Получить **ClientID** (он же App ID) и **Client secret**.

2.2. Добавить провайдера в Supabase:

1. Dashboard → **Authentication → Providers → Add provider → Manual configuration**.
2. Identifier: `custom:yandex`.
3. Client ID / Client Secret — из шага 2.1.
4. Authorization URL: `https://oauth.yandex.ru/authorize`
5. Token URL: `https://oauth.yandex.ru/token`
6. UserInfo URL: `https://login.yandex.ru/info?format=json`
7. Scopes: `login:email login:info`.
8. Enable provider.
9. Authentication → URL Configuration → добавить Redirect URL вашего фронтенда
   (например `https://<app>.vercel.app/login`).

2.3. Переменные фронтенда:

| Переменная | Значение | Назначение |
|---|---|---|
| `VITE_ENABLE_YANDEX_OAUTH` | `true` | показать кнопку «Продолжить с Яндекс ID» |
| `VITE_YANDEX_OAUTH_PROVIDER` | `custom:yandex` | идентификатор провайдера в Supabase |
| `VITE_ALLOWED_EMAIL_DOMAINS` | пусто (строго) | allow-list доменов для SPA (см. ниже) |

> **Политика домена (ADR-0003).** По умолчанию вход разрешён только с `@sberbank.ru` /
> `@omega.sbrf.ru`. Яндекс отдаёт `@yandex.ru`, поэтому такой вход **по умолчанию** будет
> отклонён: фронтенд сбрасывает сессию и показывает сообщение, а backend отвечает
> `403 domain_not_allowed`. Это демонстрирует корректную обработку отказа.
>
> Чтобы **продемонстрировать успешный вход** (критерий ДЗ «проверить успешный вход»),
> добавьте домен аккаунта в allow-list через конфиг (без изменения кода):
> - фронтенд: `VITE_ALLOWED_EMAIL_DOMAINS=@sberbank.ru,@omega.sbrf.ru,@yandex.ru`
> - бэкенд: `ALLOWED_EMAIL_DOMAINS=@sberbank.ru,@omega.sbrf.ru,@yandex.ru`
>
> Значения по умолчанию остаются строгими; переопределение действует только там, где задано.
> Убедитесь также, что Supabase получает `email` из UserInfo Яндекса (поле `default_email`);
> при пустом email вход так же будет отклонён.

### Шаг 3. Аналитика — Яндекс.Метрика

1. Открыть <https://metrika.yandex.ru> → **Добавить счётчик**.
2. Указать имя и домен; включить нужные опции; создать счётчик.
3. Скопировать **номер счётчика** (число из URL/настроек).

| Переменная | Значение | Назначение |
|---|---|---|
| `VITE_YM_COUNTER_ID` | номер счётчика (только цифры) | включает счётчик и события |

Пустое значение = аналитика выключена (no-op), что используется в тестах и локальной разработке.

### Шаг 4. Vercel (фронтенд) — для автодеплоя из CI

1. <https://vercel.com> → **Add New… → Project** → импортировать GitHub-репозиторий.
2. Root Directory — корень репозитория (сборка задана в `vercel.json`).
3. Получить токен: Account Settings → **Tokens** → **Create** (scope — нужный аккаунт/команда).
4. Получить `orgId` и `projectId`: Project Settings → General (или из `.vercel/project.json`
   после `vercel link`).
5. Добавить в GitHub → Settings → Secrets and variables → Actions:

| Secret | Где взять |
|---|---|
| `VERCEL_TOKEN` | Account Settings → Tokens |
| `VERCEL_ORG_ID` | Project Settings → General → Team ID / Org ID |
| `VERCEL_PROJECT_ID` | Project Settings → General → Project ID |

6. В Vercel → Project → Settings → Environment Variables задать фронтенд-переменные:
   `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_BASE_URL`,
   `VITE_USE_MOCKS=false`, `VITE_ENABLE_YANDEX_OAUTH`, `VITE_YANDEX_OAUTH_PROVIDER`,
   `VITE_YM_COUNTER_ID`.

### Шаг 5. Railway (бэкенд) — для автодеплоя из CI

1. <https://railway.app> → **New Project → Deploy from GitHub repo**.
2. Railway найдёт `Dockerfile` и `railway.json` автоматически.
3. Settings → **Deploy → Deploy Hook** → скопировать URL.
4. GitHub → Settings → Secrets and variables → Actions:

| Secret | Значение |
|---|---|
| `RAILWAY_DEPLOY_HOOK` | URL Deploy Hook |

5. Railway → Variables (backend):

| Переменная | Пример |
|---|---|
| `APP_CONTAINER` | `live` |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_SECRET_KEY` | service_role key |
| `SUPABASE_JWKS_URL` | `…/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_ISSUER` | `…/auth/v1` |
| `ALLOWED_EMAIL_DOMAINS` | `@sberbank.ru,@omega.sbrf.ru` |
| `API_CORS_ORIGINS` | `https://<app>.vercel.app` |
| `SITE_URL` | `https://<app>.vercel.app` |
| `LOG_LEVEL` | `info` |

> Альтернатива Railway: Railway сам умеет автодеплой из GitHub по push в выбранную ветку —
> тогда `RAILWAY_DEPLOY_HOOK` можно не задавать. **Render** как альтернатива
> сконфигурирован в [`render.yaml`](render.yaml) (Render Blueprint: Docker, health check
> `/health`, секреты помечены `sync: false` и задаются в дашборде). Достаточно
> «New → Blueprint» и указать репозиторий.

### Шаг 6. UptimeRobot (внешний мониторинг)

1. <https://uptimerobot.com> → **Add New Monitor**.
2. HTTP(s)-монитор на фронтенд: `https://<app>.vercel.app`.
3. HTTP(s)-монитор на readiness: `https://<backend>.up.railway.app/health/ready`
   (ожидаемый статус — 200; 503 = зависимость недоступна).
4. Alert Contacts → email/Telegram; назначить контакты мониторам.

### Шаг 7. Прочие переменные

| Переменная | Назначение |
|---|---|
| `VITE_API_BASE_URL` | базовый URL backend для браузера |
| `VITE_USE_MOCKS` | `false` в продакшене (иначе фронт работает на mock-данных) |
| `VITE_REQUIRE_LOGIN` | `true` на проде — требовать форму входа (даже с mock-данными) |
| `LOG_LEVEL` | уровень логов backend: `debug/info/warning/error` |
| `API_CORS_ORIGINS` | origin-allow-list для CORS |
| `SITE_URL` | абсолютный origin для ссылок в письмах |

Шаблон: [`.env.example`](.env.example) (только имена, без значений).

---

## 4. Интеграция OAuth2 (детали)

- **Frontend:** кнопка «Продолжить с Яндекс ID» (`data-testid="yandex-oauth"`) на `/login`,
  видима при `VITE_ENABLE_YANDEX_OAUTH=true`. Клик → `supabase.auth.signInWithOAuth({ provider })`
  с `redirectTo = <origin>/login?oauth=yandex`.
- **Domain gate:** после входа сессия проверяется на корпоративный домен
  (`isCorporateSession`); не-корпоративный email → `signOut()` + сообщение.
  `RequireAuth` дополнительно не пускает такую сессию на защищённые маршруты.
- **Backend:** Supabase JWT проверяется (`verify_access_token`), затем email проходит
  доменную политику (`deps.get_principal` → `403 domain_not_allowed`).
- **Безопасность:** `redirectTo` строится из `window.location.origin` (нет open redirect).

Файлы: [`web/src/services/oauthSession.js`](web/src/services/oauthSession.js),
[`web/src/services/authApi.js`](web/src/services/authApi.js),
[`web/src/pages/LoginPage.jsx`](web/src/pages/LoginPage.jsx),
[`backend/src/backend/interface/http/deps.py`](backend/src/backend/interface/http/deps.py).

---

## 5. Интеграция аналитики (детали)

Модуль [`web/src/services/analytics.js`](web/src/services/analytics.js) (чистый, покрыт
unit-тестами) + [`web/src/services/analyticsRuntime.js`](web/src/services/analyticsRuntime.js)
(привязка к `window`/env). Счётчик инициализируется в `main.jsx`; page-view отправляется на
каждой смене маршрута (`AnalyticsPageViews`).

Счётчик: **113475972** (задан в Vercel как `VITE_YM_COUNTER_ID`). Инициализация соответствует
официальному сниппету Яндекс.Метрики: скрипт `https://mc.yandex.ru/metrika/tag.js?id=<id>`,
далее `ym(<id>, 'init', { ssr, webvisor, clickmap, ecommerce, trackLinks, accurateTrackBounce })`.

| Событие (goal) | Где | Параметры |
|---|---|---|
| `login` | успешный вход по email/паролю | — |
| `login_oauth` | успешный вход через Яндекс ID | — |
| `vote` | подтверждение голоса | `topic_id` |
| `search` | запуск поиска в базе знаний | `role` (без текста запроса) |
| `material_open` | открытие материала | `slug` |
| `digest_send` | отправка дайджеста админом | — |

Приватность: сырой поисковый запрос и query-строка URL в Метрику не передаются.

---

## 6. Мониторинг и Health Check

| Endpoint | Тип | Поведение |
|---|---|---|
| `GET /health` | liveness | `200 {"status":"ok"}` — процесс жив, зависимости не трогает |
| `GET /health/ready` | readiness | `200` если все пробы здоровы, иначе `503` |

- Проба БД (`SupabaseHealthProbe`) делает лёгкий `select … limit 1` через service_role.
- Наружу отдаётся только `healthy` и `detail = ok|unhealthy` (без деталей ошибок — SEC-02).
- Полные детали ошибок попадают в логи (`request_server_error`).

Реализация: [`check_readiness.py`](backend/src/backend/application/use_cases/check_readiness.py),
[`health_probe.py`](supabase-integration/src/supabase_integration/health_probe.py),
[`routes/health.py`](backend/src/backend/interface/http/routes/health.py).

Алерты: UptimeRobot (шаг 6). Railway автоматически перезапускает сервис по
`restartPolicyType: ON_FAILURE` (`railway.json`) и проверяет `/health`.

### Настроенные мониторы (UptimeRobot)

| Монитор | URL | Ожидание |
|---|---|---|
| Frontend | `https://digest-cds.vercel.app/` | HTTP 200 |
| Backend liveness | `https://digest-cds-api-production.up.railway.app/health` | HTTP 200, тело `{"status":"ok"}` |
| Backend readiness | `https://digest-cds-api-production.up.railway.app/health/ready` | HTTP 200 (503 = зависимость недоступна) |

Для readiness включите keyword-монитор по строке `"status":"ready"` — тогда алерт сработает
не только на 503, но и на деградацию БД. Интервал — 5 минут, Alert Contacts — email/Telegram.

---

## 7. Логирование

- Формат — JSON (по строке на событие), реализация — `structlog`
  ([`middleware.py`](backend/src/backend/interface/http/middleware.py)).
- Уровни: `debug | info | warning | error`, задаются `LOG_LEVEL`.
- Ответы 2xx/3xx → `request_finished` (info), 4xx → `request_client_error` (warning),
  5xx → `request_server_error` (error).
- Корреляция по `request_id` (заголовок `X-Request-ID`); `Authorization` не логируется.
- Централизованное хранение — встроенные логи Railway (backend) и Vercel (frontend).
- AI-разбор логов — промпты в [`docs/agents/log-analysis-prompts.md`](docs/agents/log-analysis-prompts.md).

---

## 8. Безопасность

Полный отчёт: [`security_audit.md`](security_audit.md). Кратко: проведён аудит
(`npm audit`, `pip-audit`, `bandit`, AI security review) и **структурная проверка OWASP
Top 10 (2021)** по всем категориям A01–A10 (см. раздел «Проверка OWASP Top 10» в отчёте).
Исправлены 7 находок (SEC-01…SEC-10), включая High-уязвимости зависимостей и заголовки
безопасности (A05); сканеры запускаются в CI. Подтверждены защиты от XSS, CSRF,
SQL-инъекций, path traversal, SSRF, утечек секретов и деталей ошибок.

---

## 9. Использование AI

| Этап | Как использован AI | Артефакт |
|---|---|---|
| CI/CD | генерация базовых workflow `ci.yml`/`deploy.yml`, разбор ошибок пайплайна | `.github/workflows/*` |
| Аудит безопасности | AI security review диффа + структурная проверка OWASP Top 10 (2021) | `security_audit.md` |
| Анализ логов | набор промптов для разбора JSON-логов и инцидентов | `docs/agents/log-analysis-prompts.md` |
| Интеграции | помощь в настройке OAuth2 (Supabase custom provider) и событий Метрики | `integration_documentation.md` |
| Разработка | Red–Green–Refactor для новых функций (health, OAuth, аналитика, логи) | unit + Playwright тесты |

Пример промпта для генерации CI (использован как основа `ci.yml`):

```text
Сгенерируй GitHub Actions workflow для монорепозитория: Python (uv workspace) + React/Vite.
Нужны отдельные jobs: lint (ruff, oxlint), backend tests (pytest), frontend tests
(node --test) и build (vite), security (npm audit, pip-audit, bandit), e2e (Playwright).
Кэшируй uv и npm. Не деплой здесь — вынеси деплой в отдельный workflow по workflow_run.
```

---

## 10. Примеры конфигураций

`vercel.json` (SPA-роутинг + сборка приложения из `web/`):

```json
{
  "framework": "vite",
  "installCommand": "npm ci --prefix web",
  "buildCommand": "npm run build --prefix web",
  "outputDirectory": "web/dist",
  "rewrites": [{ "source": "/((?!assets/|.*\\..*).*)", "destination": "/index.html" }]
}
```

`railway.json` (Docker + healthcheck):

```json
{
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "startCommand": "sh -c 'uv run --no-dev uvicorn backend.interface.http.app:create_default_app --factory --host 0.0.0.0 --port ${PORT:-8000}'",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Полные файлы: [`.github/workflows/ci.yml`](.github/workflows/ci.yml),
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml),
[`Dockerfile`](Dockerfile), [`.dockerignore`](.dockerignore),
[`railway.json`](railway.json), [`vercel.json`](vercel.json), [`render.yaml`](render.yaml).

---

## 11. Доказательства (локальная и CI-проверка)

| Проверка | Команда | Результат |
|---|---|---|
| Backend unit | `uv run pytest -q` | 782 passed |
| Frontend unit | `npm run test:js` | 53 passed |
| E2E | `npx playwright test --project=web` | 106 passed |
| Lint Python | `uv run ruff check .` | All checks passed |
| Lint JS | `npm run lint --prefix web` | без ошибок |
| Build | `npm run build` | успешно |
| Секреты зависимостей | `npm audit`, `pip-audit` | 0 уязвимостей |
| SAST | `bandit -r …` | 0 issues |
| Docker deploy-путь | `docker build` + `docker run` + `/health` | образ собран, 200/ready |

CI-прогон (все 6 job зелёные, включая сборку Docker-образа и health smoke):
[github.com/Yarkiller/digest_cds/actions/runs/37452697394](https://github.com/Yarkiller/digest_cds/actions/runs/37452697394).
Аудит зависимостей в CI обнаружил и подтвердил исправление двух реальных уязвимостей
(SEC-08, SEC-09 в `security_audit.md`); Docker-проверка в CI поймала и подтвердила
исправление дефекта сборки образа (см. `Dockerfile`: `--no-install-workspace`).

### Что нужно для запуска деплоя

`Deploy` регистрируется в Actions только после появления файла в ветке по умолчанию
(`main`), поэтому автодеплой выполняется при push в `main` после зелёного CI.
Workflow `Deploy` уже **проверен end-to-end** (коммит `9531a62`): CI успешен, `Deploy`
запустился автоматически, и smoke-job подтвердил живое приложение —

- `Deploy frontend (Vercel)` → success;
- `Deploy backend (Railway)` → success;
- `Post-deploy smoke (live endpoints)`:
  - `Frontend responds 200` → success;
  - `Backend readiness returns ready` → success.

Run: [github.com/Yarkiller/digest_cds/actions/runs/37463500346](https://github.com/Yarkiller/digest_cds/actions/runs/37463500346).

1. Для реального деплоя фронтенда/бэкенда из CI добавьте секреты (шаги 4–5 выше):
   `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `RAILWAY_DEPLOY_HOOK`.
   (Фронтенд уже деплоится автоматически через Vercel Git — секреты для него не обязательны.)
2. Перевести изменения в `main` (merge или push) — после этого `CI → Deploy` публикует
   приложение и проверяет живые URL.
3. Ссылка на деплой — в описании репозитория/README.
