# Phase 24: Scheduled ingestion - Context

**Gathered:** 2026-10-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Новые видео собираются **по расписанию, без человека**, из списка источников, которым управляет админ (Phase 23). Планировщик перечисляет свежие записи канала/плейлиста через **key-free YouTube Atom-фид** (`feeds/videos.xml`) и прогоняет их через **существующий** пайплайн `ingest`, записывая **только** драфты и pending-строки шортлиста. Публикации и отправки в этом пути нет и быть не может.

Расписание — настраиваемое из UI: админ задаёт «включено/выключено», время ЧЧ:ММ и дни недели на вкладке «Пайплайн». `systemd` остаётся транспортом (частый опрос), а решение «пора или нет» принимает сама команда сбора по состоянию в БД.

**In scope (ING-02, ING-05, ING-06, ING-07):**
- Порт листинга + Atom-адаптер в `data-collection` (инжектированный httpx-клиент, stdlib XML, лимит размера ответа).
- `ingest-collect` — отдельная точка входа Typer; чтение включённых источников, фильтрация по high-water mark, лимит на источник, изоляция ошибок, человекочитаемая сводка.
- High-water mark per source в БД + миграция `013` (колонки курсора и singleton настроек сбора).
- Singleton `ingestion_schedule` (вкл/выкл, время, дни недели, `last_run_at`) и due-проверка в коде по `Europe/Moscow`.
- Тонкая admin-поверхность для настроек сбора + блок «Автоматический сбор» на `/admin/pipeline` между источниками и YAML-редактором.
- `deploy/systemd/`: `Type=oneshot` service + timer (опрос каждые 15 минут), alert-юнит на `OnFailure=`, `EnvironmentFile=` 0600, `flock -n`, `RuntimeMaxSec=`.
- Guard-тест: путь планировщика не достигает publish/send.
- Runbook: smoke-запуск, диагностика, ручной ретрай.

**Out of scope:**
- HTTP-триггер ингеста (`ING-01`) и любая кнопка «запустить сейчас» в UI.
- Авто-публикация и авто-отправка дайджеста.
- YouTube Data API v3, `google-api-python-client`, `yt-dlp`, разрешение `@handle`.
- Новые runtime-пакеты Python (Atom + stdlib; `defusedxml` не добавляем).
- История прогонов в БД, per-source расписание, per-source шаблон, вебхук-алерты.
- Изменение поведения `ingest <url>` и его stdout-контракта.

</domain>

<decisions>
## Implementation Decisions

### Точка входа и контракт вывода (CLI)
- **D-01:** Команда сбора — **отдельный Typer entry point** `ingest-collect` (новый модуль + запись в `[project.scripts]`), а не флаг и не подкоманда внутри существующего `app`. Причина техническая: `cli.py` — Typer-приложение из одной команды, поэтому `ingest <url>` работает без имени подкоманды; добавление второй команды в тот же `app` превращает его в группу и ломает вызов, который трипваер фиксирует байт-в-байт. `cli.py` не меняется ни на строку. — **Reversibility:** costly — слияние в один `app` позже требует переписать трипваер и форму вызова, которую операторы и systemd уже используют.
- **D-02:** Шаблон статьи для батча берётся из env **`INGEST_TEMPLATE`** (`Settings.from_env`, дефолт `lecture`, невалидное значение → `ConfigurationError` на старте, как `MAX_TRANSCRIPT_CHARS`). Per-source шаблон отклонён как расширение схемы Phase 23. — **Reversibility:** reversible.
- **D-03:** **stdout — человекочитаемая сводка прогона** (сколько источников прочитано, сколько новых обработано, сколько уже было, сколько упало, сколько пропущено лимитом); **stderr — per-video диагностика** (video_id + причина). Прогресс по видео **никогда** не печатается в stdout: батч переиспользует `run_ingest_pipeline`, но не его `on_stage`-печать (`✓ transcript` и т.п.), иначе прогресс утечёт в сводку. — **Reversibility:** costly — формат сводки станет тем, что читают оператор и (возможно) алерты.
- **D-04:** Лимит на каждый источник — env **`INGEST_MAX_VIDEOS_PER_SOURCE`**, дефолт **5** (совпадает с `SHORTLIST_BATCH_SIZE`). Не глобальный лимит на прогон: один шумный канал не должен съедать квоту остальных. — **Reversibility:** reversible.
- **D-05:** Порядок обработки — **старые → новые**; лимит отрезает хвост, поэтому необработанное остаётся в окне и подхватывается следующим прогоном без дыр в истории. — **Reversibility:** reversible.

### High-water mark (ING-05)
- **D-06:** Курсор живёт **колонками на `public.pipeline_ingest_sources`**: `last_seen_published_at timestamptz` + `last_seen_video_id text` (миграция `013`, идемпотентная, без destructive statements). Удаление источника уносит курсор автоматически, отдельная таблица курсоров и локальный файл отклонены. — **Reversibility:** one-way — колонки становятся частью схемы, которую оператор применяет на общей VM; откат требует новой миграции.
- **D-07:** «Новое видео» = `published` из Atom-записи **строго больше** `last_seen_published_at`; при равной секунде решает `video_id` как тай-брейк. Курсор двигается только вперёд. — **Reversibility:** reversible.
- **D-08:** Первый прогон источника (`last_seen_* is null`) обрабатывает **всё окно фида в пределах лимита** — включение источника должно приносить драфты, а не молча инициализировать курсор. — **Reversibility:** reversible.
- **D-09:** Упавшее видео **не блокирует курсор**: он сдвигается к самому новому успешно обработанному, видео пропускается. Цена — молчаливая потеря; компенсируется тем, что каждый пропуск печатается в stderr с `video_id` и причиной, попадает в счётчик `failed` сводки и имеет документированный ручной путь восстановления (D-13). — **Reversibility:** costly — переход к «ретраить завтра» меняет семантику курсора и ожидания оператора.

### Прогон, изоляция и отчёт (ING-06)
- **D-10:** Итог прогона виден **только в journald** (`journalctl -u digest-ingest`) плюс `systemctl --failed` и alert-юнит. Отдельная таблица истории прогонов **не создаётся**: `ingestion_jobs` из `001` не подходит (FK на `ingestion_sources` — таблицу скачанных материалов, а не на подписки). — **Reversibility:** reversible — таблица истории может быть добавлена позже без ломки контракта.
- **D-11:** Изоляция на **обоих** уровнях: упавшее видео → строка в stderr и переход к следующему видео; нечитаемый источник (сеть/не-200/битый XML/превышенный размер) → строка в stderr и переход к следующему источнику. Прогон прерывается только `ConfigurationError` (нет env/ключей). — **Reversibility:** reversible.
- **D-12:** Градуированные exit codes: **0** — сбоев нет; **1** — упало хотя бы одно видео; **2** — не прочитан ни один источник. — **Reversibility:** costly — алерты и `systemctl --failed` будут привязаны к этой шкале.
- **D-13:** Ручной ретрай пропущенного видео — **существующий** `ingest <video_id> --template …` (`extract_video_id` уже принимает голый 11-символьный id). Нового флага нет; команда и ожидаемый результат описаны в runbook. — **Reversibility:** reversible.

### Настройка расписания в UI
- **D-14:** Настройки сбора — новый **singleton** `public.ingestion_schedule(id integer primary key default 1 check (id = 1), enabled boolean not null default true, time_of_day time not null default '06:00', days_of_week …, last_run_at timestamptz)` в миграции `013`, по образцу `pipeline_config` из `011` (RLS enabled, ноль политик, доступ только service_role). Колонки в `pipeline_config` и per-source расписание отклонены. — **Reversibility:** one-way — новая таблица применяется на общей VM и становится источником истины для планировщика.
- **D-15:** Админ настраивает: **включён ли автоматический сбор**, **время ЧЧ:ММ**, **дни недели** (ежедневно = все семь). Частота не выбирается отдельно — её задают дни. Время трактуется как **`Europe/Moscow`** явно (см. D-22). — **Reversibility:** reversible.
- **D-16:** Сохранение — **сразу по изменению** (PATCH на каждое действие; время — на `change`/`blur`, не на каждую клавишу), рендер по ответу сервера. Нового dirty-сигнала и второй кнопки «Сохранить» не появляется: `dirty` остаётся `yamlDirty || sourcesDirty` (Phase 23 D-01/D-03). — **Reversibility:** costly — переход к явной кнопке добавит второй сохраняемый объект и второй блок в leave-диалог.
- **D-17:** Playwright-трипваер `"pipeline config no execution controls render"` (запрет «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание») сохраняется **байт-в-байт**. Копирайт блока строится вокруг слов «Автоматический сбор», «Дни недели», «Время», «включён/выключен» и не содержит запрещённых строк. — **Reversibility:** reversible.
- **D-18:** Блок «Автоматический сбор» стоит **между** списком источников и YAML-редактором: частота настройки источников остаётся первой, существующий порядок Phase 23 (D-02) не переворачивается. — **Reversibility:** reversible.

### Таймер и ops
- **D-19:** Unit-файлы живут **в репозитории** — `deploy/systemd/` (service, timer, alert-service) — и защищены Python text-контракт-тестом (по образцу `test_phase16_migration_011.py`): падает, если пропали `Type=oneshot`, `EnvironmentFile=`, `OnFailure=`, `RuntimeMaxSec=`, `flock -n` или абсолютный путь к `ingest-collect`. Runbook-only вариант отклонён как незащищённый от дрейфа. — **Reversibility:** reversible.
- **D-20:** `OnFailure=digest-ingest-alert.service` (Type=oneshot) пишет alert в journald; внешнего канала уведомлений нет. — **Reversibility:** reversible — вебхук добавляется заменой одного юнита.
- **D-21:** Таймер **опрашивает каждые 15 минут** (`OnCalendar=*:0/15`), `Persistent=false`, `flock -n`. Причина: расписание живёт в БД (D-14), systemd не может читать её для `OnCalendar`; `Persistent` не нужен, потому что catch-up делает сама due-проверка по `last_run_at`. Каждый «не пора» прогон выходит после одного SELECT, без обращений к YouTube и LLM. — **Reversibility:** costly — смена на «таймер знает время» потребует привилегированного хелпера на хосте.
- **D-22:** Due-проверка считает «сегодня» и «сейчас» явно в **`Europe/Moscow`** (`zoneinfo`), независимо от TZ хоста; в UI под полем времени — подсказка про московское время. — **Reversibility:** reversible.
- **D-23:** `RuntimeMaxSec=1800`. Убитый прогон не обновляет `last_run_at`, поэтому следующая проверка снова увидит «пора» и продолжит с того же курсора; вечно зависающее видео закрывается лимитом D-04. — **Reversibility:** reversible.

### Atom-фид
- **D-24:** Парсер отдаёт **голый `video_id` + `published`**; батч передаёт id прямо в `run_ingest_pipeline` (`extract_video_id` принимает 11 символов). URL не склеивается — меньше преобразований и в диагностике остаётся только id. — **Reversibility:** reversible.
- **D-25:** Запись без `yt:videoId` или без валидного `published` **пропускается** с одной строкой в stderr; источник продолжает читаться. Битый XML / не-200 / превышенный размер — это ошибка источника (D-11). — **Reversibility:** reversible.
- **D-26:** Ответ фида ограничен **1 MiB** → `FeedError(reason="feed_too_large")` до разбора XML (реальный фид на 15 записей — десятки килобайт). Парсинг — stdlib `xml.etree.ElementTree`; `defusedxml` явной зависимостью **не добавляется** (success criterion 5: zero new runtime Python packages). — **Reversibility:** reversible — замена парсера локализована в одном адаптере.

### Claude's Discretion
- Имена/размещение порта листинга, DTO и таксономии ошибок в `data-collection`; публичный `__all__` расширяется аддитивно (тесты с точным `__all__` — **AMEND**, прецедент Phase 23 D-24).
- Порты чтения источников/курсоров/настроек и их Supabase-адаптер в `ingestion-service` (service_role-клиент из composition, ошибки SDK маппятся на границе адаптера).
- Точная форма миграции `013` (обе части — курсор и singleton — в одном файле), представление `days_of_week`, дефолты и ограничения.
- Где живёт due-вычисление (чистая функция + `Clock`-порт, как в Phase 15) и как формулируются причины в stderr.
- Форма guard-теста ING-07 (статический скан импортов/строк против runtime-проверки).
- Порядок RED: pytest — для листинга, курсора, due, изоляции и guard; Playwright — интеграционное доказательство UI-блока.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Границы фазы и требования
- `.planning/ROADMAP.md` § Phase 24 — цель, `ING-02/05/06/07`, пять success criteria, tripwire (`test_cli_ingest_contract.py` → **PRESERVE**), Notes про снятый ADR-0002-гейт.
- `.planning/REQUIREMENTS.md` — `ING-02`, `ING-05`, `ING-06`, `ING-07`; Out-of-Scope: `ING-01` (HTTP API), авто-публикация/авто-отправка, разрешение `@handle`, Data API.
- `.planning/PROJECT.md` — v1.3 framing; риск «листинг канала требует Data API» и запись «`ingest` CLI уже идемпотентен» (важно: идемпотентность по строкам ≠ дешёвый повторный прогон).
- `.planning/STATE.md` — операционный блокер: Vite `127.0.0.1:5174` (убить stale listener до полного Playwright-прогона).

### Предыдущая фаза (источники и таблица)
- `.planning/phases/23-admin-managed-ingest-sources/23-CONTEXT.md` — D-16/D-17 (`pipeline_ingest_sources`, RLS deny-by-default, миграция `012`), D-01/D-03 (немедленное сохранение, один dirty-сигнал), D-22 (запрещённые слова на `/admin/pipeline`), D-24 (`__all__`-тесты → AMEND).
- `supabase-integration/migrations/012_phase23_ingest_sources.sql` — фактическая схема списка источников, к которой добавляется курсор.
- `supabase-integration/migrations/011_phase16_pipeline_config.sql` — шаблон singleton-таблицы с `check (id = 1)` и нулём политик для `ingestion_schedule`.

### Исследование (решения и подводные камни)
- `.planning/research/STACK.md` § (b) — Atom-фид `feeds/videos.xml` (channel_id/playlist_id, 15 записей, без ключа, без пагинации); § (c) — systemd `Type=oneshot` + timer, `EnvironmentFile=`, `flock`, `OnFailure=`, `Persistent`.
- `.planning/research/PITFALLS.md` — Pitfall 18 (перекрытие прогонов), 19 (пустое окружение cron), 20 (таймзона/DST и `Persistent`), 21 (переплата captions+LLM при неинкрементальном листинге), 23 (планировщик как publish/send), 25 (байт-идентичный stdout CLI).
- `.planning/research/SUMMARY.md` § Phase 22 — состав планировщика и требование «zero new runtime packages».

### Код, который переиспользуем или меняем
- `ingestion-service/src/ingestion_service/cli.py` — существующая команда, её `on_stage`-печать и полный stdout-контракт; **не редактируется** (D-01).
- `ingestion-service/pyproject.toml` — `[project.scripts] ingest = …`; сюда добавляется `ingest-collect`.
- `ingestion-service/src/ingestion_service/composition/settings.py` — образец `Settings.from_env` с `ConfigurationError` для `INGEST_TEMPLATE` / `INGEST_MAX_VIDEOS_PER_SOURCE`.
- `ingestion-service/src/ingestion_service/composition/clients.py` — готовый `build_httpx_client` (30s timeout + `YOUTUBE_PROXY_URL`), который получает адаптер фида.
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` — точка переиспользования; здесь видно, что `on_stage` печатает в stdout и что дедуп происходит только на persist.
- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — образец адаптера с инжектированным клиентом и маппингом ошибок SDK на доменные.
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError`/`Stage`; сюда добавляется стадия листинга/сбора (или отдельная ошибка сбора).
- `data-collection/src/data_collection/__init__.py` — публичный `__all__` из семи имён, расширяется аддитивно.
- `data-collection/src/data_collection/adapters/youtube_oembed.py` — образец HTTP-адаптера `data-collection`.
- `backend/src/backend/application/ports/ingest_sources.py`, `backend/src/backend/application/use_cases/ingest_sources.py` — стиль порта/use-case Phase 23 для новой admin-поверхности настроек.
- `backend/src/backend/interface/http/routes/admin.py` — admin-роутер, `require_admin`, конверт `{errors:[…]}`, стиль 503 для отсутствующего репозитория.
- `backend/src/backend/composition/container.py`, `backend/src/backend/composition/live.py` — два места wiring для новой port-поверхности.
- `supabase-integration/src/supabase_integration/ingest_source_repository.py` — шаблон Supabase-адаптера и его `__init__.py`-экспорт.
- `web/src/pages/AdminPipelineConfigPage.jsx` — страница, принимающая блок «Автоматический сбор» (D-18) и комбинированный `dirty`.
- `web/src/services/ingestSourcesApi.js` — ближайший шаблон сервиса (mock+live, harness, типизированная ошибка) для `ingestScheduleApi.js`.
- `tests/unit/test_cli_ingest_contract.py` — `EXPECTED_SUCCESS_LINES` и `stderr == ""`; **PRESERVE**.
- `tests/admin.spec.js` — `"pipeline config no execution controls render"` (~1804, **PRESERVE**), ингест-секция (~1826+), `resetIngestSourcesMock`-харнесс.
- `tests/unit/test_phase16_migration_011.py` — text-контракт-тест миграции; шаблон для `013` и для systemd-юнитов.
- `docs/agents/local-platform-runbook.md` — куда попадают smoke-запуск, диагностика и ручной ретрай.

### Правила
- `.cursor/rules/tdd.mdc`, `AGENTS.md` — RED-first, `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`.
- `.cursor/rules/architecture.mdc` — порты + wiring только в composition; домен/use-case без SDK; UI только через `web/src/services/`.
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — контурная изоляция (Atom-фид её не нарушает, гейт снят).
- `docs/adr/0004-self-hosted-supabase-on-vm.md` — схема и RLS принадлежат self-hosted Supabase.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`run_ingest_pipeline`** — весь путь captions → metadata → LLM → persist уже собран; батч вызывает его по видео, подменяя только `on_stage` (в stderr или `None`).
- **`build_httpx_client`** — инжектируемый клиент с таймаутом и прокси; адаптер фида не читает env сам.
- **`Settings.from_env`** — готовый образец чтения env с `ConfigurationError`; новые ключи встраиваются туда же.
- **`SupabaseDraftPersister`** — образец адаптера: клиент в конструкторе, `PersistenceError`-подобные ошибки на границе.
- **`pipeline_config` (011)** — рабочий singleton-шаблон с `check (id = 1)`; `ingestion_schedule` копирует форму.
- **`ingestSourcesApi.js`** — mock/live сервис с sessionStorage-сидом и Playwright-харнессом; `ingestScheduleApi.js` строится по нему.
- **`test_phase16_migration_011.py`** — text-only контракт-тест; тот же приём применим к `013` и к `deploy/systemd/*`.

### Established Patterns
- Один stdout-контракт на команду; диагностика — только stderr; опциональность — через флаг (прецедент `--debug`, Phase 15).
- Идемпотентность записи живёт в SQL-RPC (`persist_draft_and_enqueue`), не в Python-проверках.
- Миграции — идемпотентные текстовые файлы с `create table if not exists`, без destructive statements; RLS enabled + ноль политик; применяются оператором на общей VM.
- Admin-данные ходят только через `web/src/services/`; сервер — единственный авторитет валидации.
- Ошибки внешних SDK маппятся в доменные на границе адаптера; в domain/use-case нет httpx/supabase.

### Integration Points
- `ingest-collect` → чтение `pipeline_ingest_sources` (только `is_enabled`) + `ingestion_schedule` → листинг Atom по каждому источнику → фильтр по курсору → `run_ingest_pipeline` по видео → обновление курсора и `last_run_at`.
- `data-collection` → новый порт листинга + Atom-адаптер + `__all__`.
- `backend` → admin-роут настроек сбора (`GET`/`PATCH`), порт + in-memory fake + Supabase-адаптер, wiring в `container.py`/`live.py`.
- `web` → блок «Автоматический сбор» в `AdminPipelineConfigPage.jsx` + `ingestScheduleApi.js` (mock/live).
- `deploy/systemd/` → unit-файлы, читающие `EnvironmentFile` с теми же именами, что `ingest` (плюс `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE`).
- `docs/agents/local-platform-runbook.md` → smoke `systemctl start`, `journalctl -u`, ручной ретрай `ingest <video_id>`.

</code_context>

<specifics>
## Specific Ideas

- **Сводка прогона** — человекочитаемая, но с числами, пригодными для grep: источников прочитано, новых обработано, уже было, упало, пропущено лимитом.
- **Каждый пропуск виден** — строка в stderr с `video_id` и причиной; иначе D-09 делает потерю невидимой.
- **«Не пора» — дешёвый выход**: один SELECT и `exit 0`, без сети.
- **Ноль включённых источников** — честная строка, `exit 0` (иначе каждые 15 минут красный юнит).
- **`last_run_at` пишется и при пустом прогоне**, иначе due-проверка будет считать «пора» вечно.
- **Копирайт блока** не содержит «Расписание», «Планировщик», «Запуск», «Запустить», «Выполнить» — эти строки запрещены существующим тестом.
- **Время в UI — московское**, и об этом сказано рядом с полем.
- **Тестовые данные фида**: валидная запись (`yt:videoId` + `published` в ISO-8601 с `Z`), запись без `videoId`, запись с битым `published`, документ без namespace, HTML-страница вместо XML, ответ >1 MiB.

</specifics>

<deferred>
## Deferred Ideas

- **Кнопка «Запустить сейчас»** в UI — это HTTP-триггер ингеста (`ING-01`), явно вне scope v1.3; к тому же запрещённые слова на странице.
- **Флаг `--only-video`** для массового ретрая — ручного `ingest <video_id>` достаточно (D-13).
- **Таблица истории прогонов** (`ingestion_runs`) — journald выбран вместо новой схемы (D-10).
- **Шаблон на каждый источник** — env-шаблон покрывает текущую потребность (D-02).
- **Вебхук/чат как канал алерта** — требует выбранного канала и секрета; alert в journald пока достаточен (D-20).
- **Расписание на каждый источник** — singleton покрывает «когда собирать вообще» (D-14).
- **`defusedxml` явной зависимостью** — отклонено ради критерия «zero new runtime packages» (D-26).
- **`Persistent=true`** — catch-up уже даёт due-проверка (D-21).

### Reviewed Todos (not folded)
Совпадений с фазой не найдено (`todo.match-phase 24` вернул пустой список) — рассматривать было нечего.

</deferred>

---

*Phase: 24-scheduled-ingestion*
*Context gathered: 2026-10-18*
