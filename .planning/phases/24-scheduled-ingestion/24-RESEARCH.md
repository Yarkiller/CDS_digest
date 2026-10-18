# Phase 24: Scheduled ingestion — Research

**Researched:** 2026-10-18
**Domain:** key-free YouTube Atom-листинг + per-source high-water mark + systemd oneshot + admin singleton настроек сбора + guard «путь не достигает publish/send»
**Confidence:** HIGH (интеграция с существующим кодом), MEDIUM (форма Atom-фида — сеть недоступна из среды исследования), HIGH (stdlib XML / httpx / Typer / flock — проверено эмпирически)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Точка входа и контракт вывода (CLI)**
- **D-01:** Команда сбора — **отдельный Typer entry point** `ingest-collect` (новый модуль + запись в `[project.scripts]`), а не флаг и не подкоманда внутри существующего `app`. Причина техническая: `cli.py` — Typer-приложение из одной команды, поэтому `ingest <url>` работает без имени подкоманды; добавление второй команды в тот же `app` превращает его в группу и ломает вызов, который трипваер фиксирует байт-в-байт. `cli.py` не меняется ни на строку. — **Reversibility:** costly — слияние в один `app` позже требует переписать трипваер и форму вызова, которую операторы и systemd уже используют.
- **D-02:** Шаблон статьи для батча берётся из env **`INGEST_TEMPLATE`** (`Settings.from_env`, дефолт `lecture`, невалидное значение → `ConfigurationError` на старте, как `MAX_TRANSCRIPT_CHARS`). Per-source шаблон отклонён как расширение схемы Phase 23. — **Reversibility:** reversible.
- **D-03:** **stdout — человекочитаемая сводка прогона** (сколько источников прочитано, сколько новых обработано, сколько уже было, сколько упало, сколько пропущено лимитом); **stderr — per-video диагностика** (video_id + причина). Прогресс по видео **никогда** не печатается в stdout: батч переиспользует `run_ingest_pipeline`, но не его `on_stage`-печать (`✓ transcript` и т.п.), иначе прогресс утечёт в сводку. — **Reversibility:** costly — формат сводки станет тем, что читают оператор и (возможно) алерты.
- **D-04:** Лимит на каждый источник — env **`INGEST_MAX_VIDEOS_PER_SOURCE`**, дефолт **5** (совпадает с `SHORTLIST_BATCH_SIZE`). Не глобальный лимит на прогон: один шумный канал не должен съедать квоту остальных. — **Reversibility:** reversible.
- **D-05:** Порядок обработки — **старые → новые**; лимит отрезает хвост, поэтому необработанное остаётся в окне и подхватывается следующим прогоном без дыр в истории. — **Reversibility:** reversible.

**High-water mark (ING-05)**
- **D-06:** Курсор живёт **колонками на `public.pipeline_ingest_sources`**: `last_seen_published_at timestamptz` + `last_seen_video_id text` (миграция `013`, идемпотентная, без destructive statements). Удаление источника уносит курсор автоматически, отдельная таблица курсоров и локальный файл отклонены. — **Reversibility:** one-way — колонки становятся частью схемы, которую оператор применяет на общей VM; откат требует новой миграции.
- **D-07:** «Новое видео» = `published` из Atom-записи **строго больше** `last_seen_published_at`; при равной секунде решает `video_id` как тай-брейк. Курсор двигается только вперёд. — **Reversibility:** reversible.
- **D-08:** Первый прогон источника (`last_seen_* is null`) обрабатывает **всё окно фида в пределах лимита** — включение источника должно приносить драфты, а не молча инициализировать курсор. — **Reversibility:** reversible.
- **D-09:** Упавшее видео **не блокирует курсор**: он сдвигается к самому новому успешно обработанному, видео пропускается. Цена — молчаливая потеря; компенсируется тем, что каждый пропуск печатается в stderr с `video_id` и причиной, попадает в счётчик `failed` сводки и имеет документированный ручной путь восстановления (D-13). — **Reversibility:** costly — переход к «ретраить завтра» меняет семантику курсора и ожидания оператора.

**Прогон, изоляция и отчёт (ING-06)**
- **D-10:** Итог прогона виден **только в journald** (`journalctl -u digest-ingest`) плюс `systemctl --failed` и alert-юнит. Отдельная таблица истории прогонов **не создаётся**: `ingestion_jobs` из `001` не подходит (FK на `ingestion_sources` — таблицу скачанных материалов, а не на подписки). — **Reversibility:** reversible — таблица истории может быть добавлена позже без ломки контракта.
- **D-11:** Изоляция на **обоих** уровнях: упавшее видео → строка в stderr и переход к следующему видео; нечитаемый источник (сеть/не-200/битый XML/превышенный размер) → строка в stderr и переход к следующему источнику. Прогон прерывается только `ConfigurationError` (нет env/ключей). — **Reversibility:** reversible.
- **D-12:** Градуированные exit codes: **0** — сбоев нет; **1** — упало хотя бы одно видео; **2** — не прочитан ни один источник. — **Reversibility:** costly — алерты и `systemctl --failed` будут привязаны к этой шкале.
- **D-13:** Ручной ретрай пропущенного видео — **существующий** `ingest <video_id> --template …` (`extract_video_id` уже принимает голый 11-символьный id). Нового флага нет; команда и ожидаемый результат описаны в runbook. — **Reversibility:** reversible.

**Настройка расписания в UI**
- **D-14:** Настройки сбора — новый **singleton** `public.ingestion_schedule(id integer primary key default 1 check (id = 1), enabled boolean not null default true, time_of_day time not null default '06:00', days_of_week …, last_run_at timestamptz)` в миграции `013`, по образцу `pipeline_config` из `011` (RLS enabled, ноль политик, доступ только service_role). Колонки в `pipeline_config` и per-source расписание отклонены. — **Reversibility:** one-way — новая таблица применяется на общей VM и становится источником истины для планировщика.
- **D-15:** Админ настраивает: **включён ли автоматический сбор**, **время ЧЧ:ММ**, **дни недели** (ежедневно = все семь). Частота не выбирается отдельно — её задают дни. Время трактуется как **`Europe/Moscow`** явно (см. D-22). — **Reversibility:** reversible.
- **D-16:** Сохранение — **сразу по изменению** (PATCH на каждое действие; время — на `change`/`blur`, не на каждую клавишу), рендер по ответу сервера. Нового dirty-сигнала и второй кнопки «Сохранить» не появляется: `dirty` остаётся `yamlDirty || sourcesDirty` (Phase 23 D-01/D-03). — **Reversibility:** costly — переход к явной кнопке добавит второй сохраняемый объект и второй блок в leave-диалог.
- **D-17:** Playwright-трипваер `"pipeline config no execution controls render"` (запрет «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание») сохраняется **байт-в-байт**. Копирайт блока строится вокруг слов «Автоматический сбор», «Дни недели», «Время», «включён/выключен» и не содержит запрещённых строк. — **Reversibility:** reversible.
- **D-18:** Блок «Автоматический сбор» стоит **между** списком источников и YAML-редактором: частота настройки источников остаётся первой, существующий порядок Phase 23 (D-02) не переворачивается. — **Reversibility:** reversible.

**Таймер и ops**
- **D-19:** Unit-файлы живут **в репозитории** — `deploy/systemd/` (service, timer, alert-service) — и защищены Python text-контракт-тестом (по образцу `test_phase16_migration_011.py`): падает, если пропали `Type=oneshot`, `EnvironmentFile=`, `OnFailure=`, `RuntimeMaxSec=`, `flock -n` или абсолютный путь к `ingest-collect`. Runbook-only вариант отклонён как незащищённый от дрейфа. — **Reversibility:** reversible.
- **D-20:** `OnFailure=digest-ingest-alert.service` (Type=oneshot) пишет alert в journald; внешнего канала уведомлений нет. — **Reversibility:** reversible — вебхук добавляется заменой одного юнита.
- **D-21:** Таймер **опрашивает каждые 15 минут** (`OnCalendar=*:0/15`), `Persistent=false`, `flock -n`. Причина: расписание живёт в БД (D-14), systemd не может читать её для `OnCalendar`; `Persistent` не нужен, потому что catch-up делает сама due-проверка по `last_run_at`. Каждый «не пора» прогон выходит после одного SELECT, без обращений к YouTube и LLM. — **Reversibility:** costly — смена на «таймер знает время» потребует привилегированного хелпера на хосте.
- **D-22:** Due-проверка считает «сегодня» и «сейчас» явно в **`Europe/Moscow`** (`zoneinfo`), независимо от TZ хоста; в UI под полем времени — подсказка про московское время. — **Reversibility:** reversible.
- **D-23:** `RuntimeMaxSec=1800`. Убитый прогон не обновляет `last_run_at`, поэтому следующая проверка снова увидит «пора» и продолжит с того же курсора; вечно зависающее видео закрывается лимитом D-04. — **Reversibility:** reversible.

**Atom-фид**
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

### Deferred Ideas (OUT OF SCOPE)
- **Кнопка «Запустить сейчас»** в UI — это HTTP-триггер ингеста (`ING-01`), явно вне scope v1.3; к тому же запрещённые слова на странице.
- **Флаг `--only-video`** для массового ретрая — ручного `ingest <video_id>` достаточно (D-13).
- **Таблица истории прогонов** (`ingestion_runs`) — journald выбран вместо новой схемы (D-10).
- **Шаблон на каждый источник** — env-шаблон покрывает текущую потребность (D-02).
- **Вебхук/чат как канал алерта** — требует выбранного канала и секрета; alert в journald пока достаточен (D-20).
- **Расписание на каждый источник** — singleton покрывает «когда собирать вообще» (D-14).
- **`defusedxml` явной зависимостью** — отклонено ради критерия «zero new runtime packages» (D-26).
- **`Persistent=true`** — catch-up уже даёт due-проверка (D-21).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ING-02 | Плановый прогон перечисляет новые видео по каждому **включённому** источнику и прогоняет их через существующий пайплайн, пишет **только** draft + pending shortlist | Atom-adapter + порт листинга (§1); точный seam `run_ingest_pipeline(..., on_stage=None)` (§3); состав зависимостей `build_collect_deps` (§4) |
| ING-05 | Per-source high-water mark не даёт переобрабатывать уже загруженное; повторный прогон безопасен и не переплачивает captions/LLM | Семантика курсора и `is_newer` (§2); миграция `013` — две колонки + monotonic UPDATE (§6); RED-тест «re-scan неизменённого фида = 0 вызовов LLM» (§Validation) |
| ING-06 | Расписание крутится из systemd-таймера без человека; итог прогона виден; одно плохое видео не валит батч | due-проверка + `Clock`-порт (§5); изоляция ошибок и exit codes (§3.4); unit-файлы `deploy/systemd/` и text-контракт (§9) |
| ING-07 | Путь планировщика доказуемо не достигает publish/send, а stdout-контракт `ingest <url>` остаётся байт-идентичным | Модульная граница `ingestion_service` ↛ `backend` (§3.1, §10); AST+runtime guard (§10); `test_cli_ingest_contract.py` PRESERVE (§Tripwires) |
</phase_requirements>

## Summary

Фаза собирается **почти целиком из уже существующих кирпичей**. `run_ingest_pipeline` — готовый async-пайплайн, который принимает **голый 11-символьный `video_id`** (`extract_video_id` в `ingestion-service/src/ingestion_service/url.py:8,84-92`), отдаёт `PersistResult` и **не печатает ничего, если `on_stage is None`** (три `if on_stage is not None:` в `ingest_pipeline.py:73,132,158`). `build_httpx_client` уже отдаёт **`httpx.AsyncClient`** с 30-секундным таймаутом и прокси (не sync `Client` — предпосылка вопроса была неточной, см. §1.4), `Settings.from_env` — готовый образец fail-loud чтения env, `pipeline_config` из `011` — готовый singleton-шаблон, `IngestSourceRepository` + `require_admin` + `_require_*`-хелперы из Phase 23 — готовый шаблон admin-поверхности.

Три вещи проверены эмпирически в этой сессии и меняют/укрепляют план: **(1)** добавление второй `@app.command()` в тот же Typer-app действительно превращает `ingest <url>` в группу и он падает с exit 2 `No such command 'dQw4w9WgXcQ'` — D-01 подтверждён экспериментом, не догмой; **(2)** stdlib `xml.etree.ElementTree` на CPython 3.12 **сам** отбивает и classic XXE (`undefined entity &xxe;`), и billion-laughs (`limit on input amplification factor (from DTD and entities) breached` за 0.086 с) — значит `defusedxml` не нужен не «вопреки риску», а потому что риск уже закрыт expat'ом, а 1 MiB cap (D-26) остаётся как основной контроль объёма; **(3)** `flock -n` без `-E` отдаёт **exit 1**, что намертво смешивается с D-12 «1 = упало видео» — нужен `flock -n -E 75` + `SuccessExitStatus=0 75`.

Отдельно найдены **два трипваера, которые сломаются от новой работы и требуют явного AMEND**: `test_data_collection_public_api.py::test_ingestion_service_has_no_typer_import` (пропускает ровно `cli.py`, поэтому `collect_cli.py` с `import typer` его уронит — `tests/unit/test_data_collection_public_api.py:124`) и `test_public_all_is_exactly_seven_ingestion_names` (`assert set(data_collection.__all__) == PUBLIC_NAMES`, `:52`), если `__all__` расширяется. И одна среда-ловушка: на Windows-машине разработчика `ZoneInfo("Europe/Moscow")` падает с `ZoneInfoNotFoundError` (нет `tzdata`), поэтому tz обязан быть **инъектируемым параметром** чистой функции, а не константою модуля.

**Primary recommendation:** `ingest-collect` — отдельный модуль `collect_cli.py` + отдельный `build_collect_deps()`; листинг — порт + адаптер в `data-collection` с **локальным** (не namespace-URI) разбором direct-children `<entry>`; курсор — монотонный UPDATE после каждого успешного видео; due-проверка — чистая функция с инъекцией `tzinfo`; schedule-репозиторий — **внутри `ingestion-service`**, а не в `supabase-integration` (иначе `backend` попадёт в граф импортов и ING-07 станет недоказуем).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Листинг записей Atom-фида | **data-collection** (адаптер) | — | Единственный модуль, которому разрешено знать про внешний HTTP (`.cursor/rules/architecture.mdc`); инжектированный клиент, никакого `os.environ` |
| Решение «пора/не пора» | **ingestion-service / domain** | — | Чистая функция над состоянием из БД; не знает ни про systemd, ни про HTTP |
| Чтение источников / курсоров / настроек | **ingestion-service / adapters** | — | `ingestion-service` **не имеет права** импортировать `backend` (иначе ING-07 недоказуем) и потому не может использовать `supabase-integration` (он импортирует `backend.domain.*`); прецедент — `ingestion_service/adapters/supabase_persist.py` |
| Запуск пайплайна по видео | **ingestion-service / use_cases** | — | `run_ingest_pipeline` уже здесь; батч — новый use-case рядом |
| Транспорт расписания (таймер) | **OS / systemd** | — | `deploy/systemd/`; приложение о таймере не знает, только читает `ingestion_schedule` |
| Настройки сбора (админ) | **backend** (порт + use-case + HTTP) | **supabase-integration** (адаптер), **web** (сервис + блок) | Ровно как Phase 23: порт в `application/ports`, адаптер в `supabase-integration`, wiring только в `composition/` |
| Запись драфтов/шортлиста | **Supabase RPC** (`persist_draft_and_enqueue`) | — | Существующий идемпотентный RPC; Python-слой не дедуплицирует (установленный паттерн) |
| Публикация/отправка | **backend** — и только он | — | Путь сбора обязан быть **недостижим** до этих символов (ING-07) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stdlib `xml.etree.ElementTree` | CPython 3.12 (`.venv` → cpython-3.12) | Разбор Atom | `defusedxml` запрещён (D-26); XXE и amplification-бомба отбиваются expat'ом — проверено (§1.5) |
| `httpx` | `0.28.1` (пин `data-collection/pyproject.toml`) | Стриминговое чтение фида с cap | Уже HTTP-стандарт `data-collection`; `AsyncClient.stream` + `aiter_bytes` — проверено (§1.4) |
| `zoneinfo` | stdlib | `Europe/Moscow` для due-проверки | D-22; на Linux резолвится из системного tzdata (проверено в WSL Ubuntu 24.04) |
| `typer` | `>=0.27.2` (уже в `ingestion-service`) | Второй entry point | `cli.py:30` — `typer.Typer(add_completion=False)`; тот же объект годится как console-script |
| `datetime` / `time` | stdlib | `published`, `time_of_day`, `last_run_at` | `time.fromisoformat("06:00:00")` → `06:00:00` — проверено |
| systemd + `flock` (util-linux) | systemd 249+ / util-linux 2.39.3 | Транспорт расписания | `flock -E` подтверждён на 2.39.3 (§9) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8.3.0` (dev-group корня) | RED-тесты | Все unit-слои |
| `typer.testing.CliRunner` | (в typer) | Контракт `ingest-collect` | `tests/unit/test_collect_cli*.py` |
| `httpx.MockTransport` | (в httpx) | Фикстуры фида без сети | Адаптер-тесты: 200/404/битый XML/oversize/chunked |
| Playwright `@playwright/test` | `^1.62.1` | Интеграция UI-блока | `tests/admin.spec.js` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `httpx.AsyncClient.stream` + cap | `httpx.get(...).content` | Ломает D-26: тело целиком в память до проверки размера. Отклонено. |
| `ZoneInfo` в константе модуля | `timezone(timedelta(hours=3))` | Фиксированный offset корректен сегодня (Москва без DST), но **противоречит D-22 буквально** и тихо разойдётся, если правила изменятся. Компромисс — `ZoneInfo` в composition + инъекция `tzinfo` в чистую функцию (§5.3) |
| Schedule-адаптер в `supabase-integration` | Локальный адаптер в `ingestion-service/adapters/` | `supabase-integration` импортирует `backend.domain.*` (19 файлов) → транзитивно `backend` в графе планировщика, ING-07 перестаёт быть доказуемым. Прецедент локального адаптера — `supabase_persist.py` |
| `days_of_week` как bitmask `int` | `smallint[]` | Bitmask нечитаем в Studio и требует магии в UI; массив ограничивается CHECK'ом и читается PostgREST'ом как JSON-массив |

**Installation:**
```bash
# Ничего. Zero new runtime Python packages (success criterion 5).
uv sync            # если менялся только pyproject [project.scripts] — переустановка entry point
cd web && npm install   # не требуется: новых frontend-зависимостей нет
```

**Version verification (эта сессия):** `httpx` → `0.28.1` (распечатано `httpx.__version__`); Python venv → `cpython-3.12-windows` (из traceback'а), `requires-python = ">=3.12"` (`ingestion-service/pyproject.toml:5`); `flock from util-linux 2.39.3` (WSL); `zoneinfo` + `/usr/share/zoneinfo/Europe/Moscow` на Ubuntu 24.04 (WSL). Внешний фид **не проверяем** — см. §1.1.

## Package Legitimacy Audit

> Фаза **не устанавливает ни одного нового пакета** (success criterion 5, D-26). Гейт применяется только к тому, что могло бы быть предложено, и к тому, что уже стоит.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `httpx` | PyPI | уже в `data-collection` | — | github.com/encode/httpx | OK (pre-existing) | Уже в зависимостях |
| `typer` | PyPI | уже в `ingestion-service` | — | github.com/fastapi/typer | OK (pre-existing) | Уже в зависимостях |
| `defusedxml` | PyPI | — | — | — | **Не предлагается** | Отклонён D-26; риск закрыт expat'ом (§1.5) |
| `feedparser` | PyPI | — | — | — | **Не предлагается** | Отклонён STACK.md и D-26 |
| `yt-dlp` / `google-api-python-client` | PyPI | — | — | — | **Не предлагается** | Отклонены ROADMAP Notes + PITFALLS |
| `APScheduler` | PyPI | — | — | — | **Не предлагается** | Отклонён STACK.md §(c); транспорт — systemd |
| `tzdata` | PyPI | — | — | — | **Не предлагается** | ⚠ см. §5.2: на Windows нужен только для тестов; решается инъекцией tz, а не пакетом |

**Packages removed due to [SLOP] verdict:** none — ни один новый пакет не предлагался, поэтому гейт `gsd_run query package-legitimacy check` для этой фазы не имеет входных данных.
**Packages flagged as suspicious [SUS]:** none.

## Codebase Grounding

Все цитаты ниже прочитаны `Read` **в этой сессии**; `[VERIFIED: path:lines]` стоит только там, где рядом приведён verbatim-фрагмент.

### G-1. `build_httpx_client` отдаёт async-клиент, а не sync

```20:38:ingestion-service/src/ingestion_service/composition/clients.py
_DEFAULT_TIMEOUT = 30.0
_DEEPSEEK_TIMEOUT = 120.0
...
def build_httpx_client(settings: Settings) -> httpx.AsyncClient:
    proxy = settings.youtube_proxy_url
    if proxy:
        return httpx.AsyncClient(proxy=proxy, timeout=_DEFAULT_TIMEOUT)
    return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
```

`[VERIFIED: ingestion-service/src/ingestion_service/composition/clients.py:33]` — сигнатура `-> httpx.AsyncClient`.

**Следствие:** порт листинга **обязан быть `async def`**, ровно как `YouTubeOEmbedAdapter.get` (`data-collection/src/data_collection/adapters/youtube_oembed.py:37` — `async def get`). Никакого sync-`httpx.Client` в проекте нет; предпосылка «`build_httpx_client` возвращает sync `Client`» из задания **неверна** и не должна попасть в план.

### G-2. `run_ingest_pipeline` — точный контракт

```32:42:ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
async def run_ingest_pipeline(
    url: str,
    template: TemplateKind,
    *,
    captions: TranscriptProvider,
    metadata_provider: VideoMetadataProvider,
    article: ArticleGenerator,
    persist: PersistPort,
    on_stage: OnStage | None = None,
    diagnostics: StageDiagnostics | None = None,
) -> PersistResult:
```

`[VERIFIED: ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py:32-42]`

- Возвращает `PersistResult(material_id, slug, batch_id, rank, already_saved)` — `[VERIFIED: ingestion-service/src/ingestion_service/application/ports/persist.py:10-16]`:
  ```10:16:ingestion-service/src/ingestion_service/application/ports/persist.py
@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    already_saved: bool = False
  ```
- `on_stage` — keyword-only, `None` по умолчанию; печать строго под guard'ом `if on_stage is not None:` на трёх точках (`:73`, `:132`, `:158`). **`on_stage=None` полностью подавляет `✓ transcript` / `✓ LLM` / `✓ saved`.**
- Бросает `IngestError` (домен) — единственный ожидаемый тип на уровне use-case; `InvalidYouTubeUrl` уже маппится внутрь (`map_url_error`), `CaptionsError`/`MetadataError`/`ArticleError`/`DraftPersistError` — тоже.
- **Не бросает** `ConfigurationError`/`TemplateLoadError` — они прилетают из composition-фабрик (`build_deepseek_article_generator` → `load_article_templates`), т.е. **до** первого видео.

### G-3. `extract_video_id` принимает голый id

```83:92:ingestion-service/src/ingestion_service/url.py
def extract_video_id(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise InvalidYouTubeUrl("invalid_video_id", value)
    if _ID_RE.fullmatch(raw):
        return raw

    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host not in _ALLOWED_HOSTS:
        raise InvalidYouTubeUrl("not_a_youtube_url", value)
```

`[VERIFIED: ingestion-service/src/ingestion_service/url.py:8,83-92]` — `_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")`. Значит D-24 (передавать `video_id` без склейки URL) работает без правок `url.py`.

### G-4. `Settings.from_env` — образец fail-loud env

```16:28:ingestion-service/src/ingestion_service/composition/settings.py
def _max_transcript_chars(env: dict[str, str]) -> int:
    raw = env.get("MAX_TRANSCRIPT_CHARS")
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_TRANSCRIPT_CHARS
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "MAX_TRANSCRIPT_CHARS must be a positive integer"
        ) from exc
    if value <= 0:
        raise ConfigurationError("MAX_TRANSCRIPT_CHARS must be a positive integer")
    return value
```

`[VERIFIED: ingestion-service/src/ingestion_service/composition/settings.py:16-28]` — ровно этот шаблон копируется для `INGEST_MAX_VIDEOS_PER_SOURCE` (positive int) и `INGEST_TEMPLATE` (`TemplateKind(raw)` → `ValueError` → `ConfigurationError`).

`TemplateKind` — `[VERIFIED: data-collection/src/data_collection/dto/template_kind.py:5-7]`:
```5:7:data-collection/src/data_collection/dto/template_kind.py
class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
```

### G-5. `Clock`-порт (прецедент Phase 15)

```16:21:ingestion-service/src/ingestion_service/application/ports/diagnostics.py
@runtime_checkable
class Clock(Protocol):
    def monotonic(self) -> float: ...

    def now(self) -> datetime: ...
```

`[VERIFIED: ingestion-service/src/ingestion_service/application/ports/diagnostics.py:16-21]`. Docstring порта прямо говорит: «The use-case depends only on these `typing.Protocol` ports; it never imports `time`, `sys`, `typer`, or `datetime`». Реализация — `SystemClock` в `ingestion_service/adapters/stderr_diagnostics.py:28-35`.

**Рекомендация:** переиспользовать этот `Clock` как есть (`now()` уже отдаёт `datetime`). Не заводить второй порт и не переносить файл — перенос это refactor без RED-теста.

### G-6. Admin-поверхность Phase 23 — точный шаблон

```10:14:backend/src/backend/application/ports/ingest_sources.py
from typing import Protocol

from backend.domain.ingest_source import IngestSource


class IngestSourceRepository(Protocol):
```

`[VERIFIED: backend/src/backend/application/ports/ingest_sources.py:10-14]`

503-стиль (`[VERIFIED: backend/src/backend/interface/http/routes/admin.py:274-281]`):
```274:281:backend/src/backend/interface/http/routes/admin.py
def _require_ingest_sources(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "ingest_sources", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest_sources_not_configured",
        )
    return container.ingest_sources
```

Контейнер (`[VERIFIED: backend/src/backend/composition/container.py:72]`):
```71:72:backend/src/backend/composition/container.py
    # D-21: ingest sources port — None until wired (503 ingest_sources_not_configured).
    ingest_sources: IngestSourceRepository | None = None
```

In-memory (`[VERIFIED: backend/src/backend/composition/container.py:140]`): `container.ingest_sources = InMemoryIngestSourceRepository()`.
Live (`[VERIFIED: backend/src/backend/composition/live.py:65]`): `ingest_sources=SupabaseIngestSourceRepository(admin_client),`.

### G-7. Фронтенд: точка вставки и dirty-сигнал

```112:114:web/src/pages/AdminPipelineConfigPage.jsx
  const yamlDirty = yaml !== savedYaml
  const sourceFormDirty = sourceId.trim() !== '' || sourceLabel.trim() !== ''
  const dirty = yamlDirty || sourceFormDirty
```

`[VERIFIED: web/src/pages/AdminPipelineConfigPage.jsx:112-114]` — D-16 требует, чтобы `dirty` **остался** таким; блок сбора не добавляет третьего слагаемого (он сохраняет немедленно).

Точка вставки — `<IngestSourcesSection ... />` начинается на `:234` и закрывается `/>` перед блоком `{!savedYaml ? (` (`:249`). `data-testid="pipeline-config-editor"` — `:338`.

### G-8. Байт-идентичный stdout-контракт

`[VERIFIED: tests/unit/test_cli_ingest_contract.py:20-29]` — восемь строк, включая три `✓`-строки и `already_saved: false`. Ассерты на `:83` и `:112` — `result.stdout.splitlines() == EXPECTED_SUCCESS_LINES` + `result.stderr == ""`.

**PRESERVE.** Любая строка, добавленная `ingest-collect` в stdout, обязана быть в **другом** процессе/другом app; `cli.py` не трогаем вообще.

## Architecture Patterns

### System Architecture Diagram

```
                       ┌──────────────────────── systemd (host) ────────────────────────┐
                       │ digest-ingest.timer   OnCalendar=*:0/15  Persistent=false       │
                       │        │                                                       │
                       │        ▼                                                       │
                       │ digest-ingest.service  Type=oneshot, RuntimeMaxSec=1800        │
                       │   EnvironmentFile=/etc/digest-cds/ingest.env (0600)            │
                       │   ExecStart=flock -n -E 75 /run/digest-ingest.lock \<venv>/ingest-collect │
                       └────────────┬───────────────────────────────────────────────────┘
                                    │ exec (stdout→journald, stderr→journald)
                                    ▼
                     ingest_collect.py  (Typer app, отдельный entry point)
                                    │
                                    ▼
              ┌──────────── build_collect_deps()  [composition] ────────────┐
              │ Settings.from_env → INGEST_TEMPLATE, MAX_VIDEOS, keys       │
              │ httpx.AsyncClient (30 s, proxy) → YouTubeFeedAdapter        │
              │ captions / metadata / article / persist → существующие      │
              │ ScheduleSourceReader (Supabase) → schedule + sources+cursor │
              │ ZoneInfo("Europe/Moscow")                                   │
              └────────────────────────────┬────────────────────────────────┘
                                           ▼
   ┌──────────────────────────────── 1 SELECT ────────────────────────────────┐
   │ ingestion_schedule(enabled, time_of_day, days_of_week, last_run_at)      │
   │ is_due(...)?  ── нет ──▶ echo "не пора" (stdout) · exit 0 · БЕЗ сети/LLM │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      │ да
                                      ▼
   ┌──────────── 1 SELECT: enabled sources + last_seen_* ─────────────────────┐
   │ для каждого source:                                                      │
   │   YouTubeFeedAdapter.list_recent(kind, source_id)                        │
   │     ├─ FeedError (сеть/не-200/oversize/битый XML) ─▶ stderr, next source │
   │     └─ ok ─▶ sorted(asc by published) ─▶ filter is_newer(cursor)         │
   │                              ─▶ [:INGEST_MAX_VIDEOS_PER_SOURCE]          │
   │   для каждого video (старые→новые):                                      │
   │     run_ingest_pipeline(video_id, template, on_stage=None, diag=None)    │
   │       ├─ ok ─▶ cursor = max(cursor, published, video_id) ─▶ UPDATE        │
   │       └─ IngestError/Exception ─▶ stderr «<id>: <stage>/<reason>»         │
   │                                    · failed += 1 · next video            │
   │   (счётчики: read/ingested/already/failed/skipped_limit)                  │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
   UPDATE ingestion_schedule SET last_run_at = now()   (даже при пустом прогоне)
                                      ▼
   stdout: человекочитаемая сводка · exit 0 / 1 (упало видео) / 2 (ни один source)
```

### Recommended Project Structure

```text
data-collection/src/data_collection/
├── dto/video_ref.py                     # НОВЫЙ: VideoRef(video_id, published) + FeedListing
├── ports/video_list_provider.py         # НОВЫЙ: async Protocol list_recent(...)
├── adapters/youtube_feed.py             # НОВЫЙ: YouTubeFeedAdapter (httpx stream + ET)
├── errors/feed.py                       # НОВЫЙ: FeedError(reason=…) + подклассы
└── __init__.py                          # AMEND: __all__ += VideoRef, VideoListProvider

ingestion-service/src/ingestion_service/
├── collect_cli.py                       # НОВЫЙ: typer app + build_collect_deps()
├── domain/schedule.py                    # НОВЫЙ: IngestionSchedule, SourceCursor, is_due, is_newer
├── application/ports/collect_sources.py  # НОВЫЙ: CollectSourceReader Protocol
├── application/use_cases/collect_batch.py# НОВЫЙ: прогон по источникам/видео, сводка, exit code
├── adapters/supabase_collect_sources.py  # НОВЫЙ: чтение sources+cursor, schedule, запись курсора
├── adapters/stderr_summary.py            # НОВЫЙ (опц.): рендер сводки/диагностики
└── composition/{settings,clients}.py     # AMEND: 2 env-ключа + build_youtube_feed/build_collect_deps

supabase-integration/migrations/013_phase24_scheduled_ingestion.sql   # НОВЫЙ

backend/src/backend/
├── domain/ingestion_schedule.py                     # НОВЫЙ
├── application/ports/ingestion_schedule.py          # НОВЫЙ
├── application/use_cases/ingestion_schedule.py      # НОВЫЙ
├── interface/http/routes/admin.py                   # AMEND: GET/PATCH
├── composition/{container,live}.py                  # AMEND: поле + два wiring
└── tests_support/in_memory.py                       # AMEND: InMemoryIngestionScheduleRepository

supabase-integration/src/supabase_integration/
├── ingestion_schedule_repository.py                 # НОВЫЙ
└── __init__.py                                      # AMEND: экспорт (только `in`, не exact — безопасно)

web/src/
├── services/ingestScheduleApi.js                    # НОВЫЙ (mock/live + arm)
├── components/IngestionScheduleSection.jsx          # НОВЫЙ
├── pages/AdminPipelineConfigPage.jsx                # AMEND: блок между sources и YAML
└── main.jsx                                         # AMEND: __DIGEST_INGESTION_SCHEDULE_HARNESS__

deploy/systemd/
├── digest-ingest.service
├── digest-ingest.timer
└── digest-ingest-alert.service
```

### Pattern 1: адаптер с инжектированным клиентом и модульной таксономией ошибок

**What:** класс принимает клиент в конструкторе, не читает env, маппит транспорт/SDK на локальные ошибки.
**When to use:** любой внешний HTTP — здесь `YouTubeFeedAdapter`.
**Example:** копия формы `YouTubeOEmbedAdapter` (§1.3).

### Pattern 2: чистая функция + инъекция `tzinfo` / `Clock`

**What:** решение принимается функцией без `datetime.now()` внутри и без импорта `zoneinfo` в домене.
**When to use:** `is_due`, `is_newer`, выбор окна лимита.
**Example:** §5.3, §2.2.

### Pattern 3: монотонный условный UPDATE курсора

**What:** `UPDATE ... WHERE (last_seen_published_at IS NULL OR last_seen_published_at < $new OR (last_seen_published_at = $new AND last_seen_video_id < $vid))`.
**When to use:** после каждого успешного видео (crash-safe при `RuntimeMaxSec`).
**Example:** §6.4.

### Anti-Patterns to Avoid

- **Импорт `supabase_integration` из `ingestion-service`** — транзитивно тянет `backend.domain.*` (19 файлов) и обнуляет ING-07.
- **`ZoneInfo("Europe/Moscow")` на уровне модуля** — падает на Windows-машине разработчика (`ZoneInfoNotFoundError`) и уносит весь импорт `collect_cli`.
- **`on_stage=_print_progress`** — утечка `✓ transcript` в stdout сводки (D-03, PITFALL 25).
- **Дедупликация в Python вместо курсора** — сохраняет корректность, но **не** экономит captions+LLM (PITFALL 21).
- **`flock -n` без `-E`** — exit 1 смешивается с «упало видео» (D-12).
- **`create policy` в миграции 013** — `011`/`012` запрещают; deny-by-default.
- **Вызов `ingest <url>` как subprocess на каждое видео** — новый процесс на видео, stdout-контракт чужой команды в сводке, и потеря `PersistResult`. Прямой вызов `run_ingest_pipeline` дешевле и точнее.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Разбор Atom | Свой regex/`split("<entry>")` парсер | `xml.etree.ElementTree` + обход direct children по local-name | Регистр, CDATA, экранирование, вложенный `media:group` — всё уже решено |
| Защита от XXE/бомб | `defusedxml`, свой санитайзер | Ничего: expat в CPython 3.12 отбивает и то, и то | Проверено: `undefined entity`, `limit on input amplification factor breached` (§1.5) |
| Ограничение размера ответа | `len(response.content)` после `get` | `client.stream(...)` + `content-length` + cap по чанкам | D-26 требует «до разбора»; проверено на `httpx.MockTransport` (§1.4) |
| Идемпотентность записи | Python-проверка «уже есть?» | Существующий RPC `persist_draft_and_enqueue` → `already_saved` | Установленный паттерн (AGENTS/архитектура) |
| Расписание | Парсер cron-выражений, `APScheduler` | `enabled` + `time_of_day` + `days_of_week` + рантайм `is_due` | D-14/D-21; systemd не читает БД |
| Таймзоны / DST | Своя таблица смещений | `zoneinfo.ZoneInfo` (в composition) | stdlib, обновляется с tzdata |
| Блокировка прогона | Свой lock-файл с PID | `flock -n -E 75` + `Type=oneshot` | PITFALL 18; ядро снимает lock при смерти процесса |
| Монотонность курсора | Сравнение в Python перед UPDATE | Условный `WHERE` в UPDATE | Гонка двух прогонов не откатит курсор |
| `[project.scripts]` | Обёртка-шелл-скрипт | Вторая запись в `[project.scripts]` | `uv`/`uv_build` уже ставят entry points |

**Key insight:** в этой фазе «не пиши сам» относится прежде всего к **XML и таймзонам** — оба места, где самодельное решение выглядит проще, а ломается на реальных данных и на DST.

## Runtime State Inventory

Фаза — миграция схемы на **общей VM**. Grep по репозиторию этого не находит.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | `public.pipeline_ingest_sources` (создана `012`, применена на VM 2026-10-17, 0 строк) получает две новые колонки. `public.ingestion_schedule` — новая таблица, **строки-синглтона ещё нет**. Курсоров в БД пока нет: `last_seen_*` будут `NULL` до первого прогона. | `add column if not exists` — **code edit**, не data migration. Строка `ingestion_schedule(id=1)` создаётся лениво: `get()` при отсутствии отдаёт дефолты, `save()` делает upsert. Не вставлять seed-строку в миграцию (иначе «админ ничего не настраивал» станет неотличимо от «настроен дефолт»). |
| **Live service config** | На VM сегодня **нет** ни одного systemd-юнита для ингеста (`deploy/` в репозитории отсутствует — проверено). Значит регистрация юнитов, `EnvironmentFile` 0600 и `systemctl enable --now digest-ingest.timer` — полностью новые операторские шаги. | Manual/ops: создать `/etc/digest-cds/ingest.env` (0600), скопировать 3 юнита, `daemon-reload`, `systemctl start digest-ingest.service` (smoke), затем `enable --now digest-ingest.timer`. Всё — в runbook. |
| **OS-registered state** | Нет. Ни `cron`, ни `timer`, ни `pm2`, ни `launchd` в репозитории и артефактах не упоминаются. | None — verified by `Test-Path deploy` → «NO deploy/ dir» и отсутствием cron-файлов в репозитории. |
| **Secrets/env vars** | Новые ключи: `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE`. Существующие для планировщика: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS`, `SHORTLIST_BATCH_SIZE` (полный список — `ingestion-service/.env.example`). Новые ключи **не секреты** → их место в `.env.example` и в комментарии unit-файла, но не в `EnvironmentFile` 0600 как обязательные. | Code edit: `ingestion-service/.env.example` + тест `test_ingestion_env_example.py` (`REQUIRED_INGESTION_KEYS` — **AMEND** добавить 2 имени, не удалять). Ops: `ingest.env` содержит секреты. |
| **Build artifacts** | `.venv/bin/ingest-collect` появляется только после `uv sync` (переустановка entry points). На VM абсолютный путь в `ExecStart=` не существует до `uv sync`. | Ops: `uv sync` на VM **до** `systemctl start`; порядок зафиксировать в runbook. Windows-venv получит `ingest-collect.exe`. |

**Canonical question — «после обновления всех файлов что ещё держит старое состояние?»** Три вещи: (1) отсутствующая строка-синглтон в `ingestion_schedule`; (2) `NULL`-курсоры у уже добавленных источников (это **корректно**, D-08); (3) неустановленный `ingest-collect` entry point на VM до `uv sync`.

## Common Pitfalls

> Расширение PITFALLS 18–21 и 23/25, не повторение. Нумерация — фазовая.

### Pitfall 24-1: `flock -n` без `-E` даёт exit 1 и сливается с «упало видео»

**What goes wrong:** два прогона столкнулись (ручной `ingest-collect` во время таймера) → `flock -n` выходит **1** → `OnFailure=` срабатывает, `systemctl --failed` краснеет, а сообщение неотличимо от D-12 «упало видео». Оператор идёт искать сломанное видео, которого нет.
**Why it happens:** `flock -n` по умолчанию возвращает 1 при конфликте; D-12 уже занял 1 под «частичный сбой».
**How to avoid:** `ExecStart=/usr/bin/flock -n -E 75 /run/digest-ingest.lock <abs>/ingest-collect` + `SuccessExitStatus=0 75`. 75 = «занято, пропущено» — не failure. `flock -E` подтверждён на util-linux 2.39.3.
**Warning signs:** в журнале `failed to get lock` рядом с unit-статусом `failed`; `systemctl --failed` показывает прогон, у которого в stdout нет сводки вообще.

### Pitfall 24-2: `import typer` в `collect_cli.py` ломает существующий тест чистоты

**What goes wrong:** `tests/unit/test_data_collection_public_api.py::test_ingestion_service_has_no_typer_import` обходит `src_root.rglob("*.py")` и пропускает **ровно** файл с именем `cli.py`:

```120:128:tests/unit/test_data_collection_public_api.py
def test_ingestion_service_has_no_typer_import() -> None:
    """Only cli.py may import typer; all other ingestion_service modules stay clean."""
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "ingestion-service" / "src" / "ingestion_service"
    for path in src_root.rglob("*.py"):
        if path.name == "cli.py":
            continue
        body = path.read_text(encoding="utf-8")
        assert "import typer" not in body, path.name
        assert "from typer" not in body, path.name
```

`[VERIFIED: tests/unit/test_data_collection_public_api.py:120-128]`. Новый `collect_cli.py` с `import typer` → **красный** существующий тест.
**Why it happens:** skip-условие написано по точному имени, а не по суффиксу.
**How to avoid:** **AMEND** (не удалять): `if path.name.endswith("cli.py"): continue`. Это часть плана, а не «неожиданность».
**Warning signs:** «чужой» тест падает на `collect_cli.py`, хотя ни строчки в нём не менялось.

### Pitfall 24-3: `ZoneInfo` на уровне модуля падает на Windows

**What goes wrong:** `zoneinfo.ZoneInfo("Europe/Moscow")` в модульном дефолте → на машине разработчика (Windows, без пакета `tzdata`) `ZoneInfoNotFoundError: No time zone found with key Europe/Moscow` — проверено. Импорт `collect_cli` падает целиком, все его тесты краснеют «не по той причине».
**Why it happens:** на Linux tz берётся из `/usr/share/zoneinfo` (проверено в WSL Ubuntu 24.04), на Windows — из пакета `tzdata`, которого нет и который **нельзя** добавить (zero new packages).
**How to avoid:** `is_due` принимает `tz: tzinfo` параметром; тесты инъектируют `timezone(timedelta(hours=3), "Europe/Moscow")`. `ZoneInfo` конструируется **только** в `build_collect_deps()` (вызывается в рантайме), и его недоступность превращается в явный `ConfigurationError` с инструкцией, а не в трейсбек импорта.
**Warning signs:** тесты `domain/schedule` падают в коллекции на Windows; на CI/Linux — зелёные.

### Pitfall 24-4: курсор «сдвигается к самому новому» прочитан как «сдвигается всегда»

**What goes wrong:** реализация двигает курсор и на упавшем видео → самое новое видео канала, у которого нет субтитров, **никогда** не ретраится, и потеря невидима (только строка в stderr в одном прогоне из N).
**Why it happens:** D-09 буквально говорит «сдвигается к самому новому успешно обработанному» и «видео пропускается» — два прочтения.
**How to avoid:** курсор = **max по успешным** (монотонный). Упавшее видео пропускается *в этом прогоне*, но остаётся выше курсора и потому ретраится следующим прогоном (естественный bounded retry). Ограничение сверху: это максимум **одно** видео на источник (самое новое), а `INGEST_MAX_VIDEOS_PER_SOURCE` (D-04) не даёт разгуляться. Ручной путь D-13 остаётся.
**Warning signs:** тест «упавшее самое новое видео → курсор не сдвинулся» проходит, а тест «упавшее среднее видео + успешное новее → курсор на успешном» падает.

### Pitfall 24-5: лимит отрезает не тот конец

**What goes wrong:** сортировка по убыванию + `[:limit]` отрезает **старые** записи; тогда первый прогон (D-08, курсор `NULL`) берёт 5 самых новых, курсор прыгает на самый новый, а 10 более старых навсегда выпадают из окна фида — дыра в истории.
**Why it happens:** фид приходит по убыванию, и «взять первые 5» выглядит естественно.
**How to avoid:** явно `sorted(videos, key=lambda v: (v.published, v.video_id))` **по возрастанию**, затем `[:limit]`. D-05 + D-08 требуют именно этого. RED-тест: фид из 15 записей, лимит 5, курсор `NULL` → обработаны 5 **самых старых**, курсор = 5-я по возрасту.
**Warning signs:** после трёх прогонов на канале с 15 видео в БД 15 драфтов, но самое старое видео отсутствует.

### Pitfall 24-6: `last_run_at` не пишется при пустом прогоне

**What goes wrong:** ноль новых видео → ранний `return` без записи `last_run_at` → следующий тик снова «пора» → каждые 15 минут полный SELECT + листинг всех источников (сеть!) вместо одного SELECT.
**Why it happens:** «нечего делать» ощущается как «нечего писать».
**How to avoid:** `UPDATE ingestion_schedule SET last_run_at = <now>` **всегда** после успешного прохождения due-гейта, включая пустой прогон и прогон с нулём включённых источников (CONTEXT specifics: «`last_run_at` пишется и при пустом прогоне»).
**Warning signs:** `journalctl` показывает полный прогон каждые 15 минут при отсутствии новых видео.

### Pitfall 24-7: `<entry>` обход рекурсивно ловит `media:group/media:title`

**What goes wrong:** `root.iter()` по всем потомкам находит `media:title`, `media:description`, `media:thumbnail` — и `title`/`published` начинают браться не оттуда. Проверено: direct children `<entry>` включают `{http://search.yahoo.com/mrss/}group`, внутри которого свои `title`.
**Why it happens:** `iter()` удобнее и кажется безопаснее.
**How to avoid:** обходить **только** `for child in entry` (direct children) и матчить по local-name (`tag.rsplit("}", 1)[-1]`). Проверено эмпирически: `videoId` и `published` находятся именно на этом уровне, `media:group` — тоже direct child, но у него local-name `group`.
**Warning signs:** у видео с пустым `media:title` парсер молча берёт не то поле; тест на «запись без `videoId`» не проходит.

### Pitfall 24-8: stdout сводки перетирает контракт `ingest`

**What goes wrong:** соблазн «переиспользовать `cli._on_stage`» или добавить `--collect` флаг в `cli.py` → `EXPECTED_SUCCESS_LINES` ломается, и трипваер PRESERVE падает.
**Why it happens:** «одна команда с флагом» выглядит чище, чем второй entry point.
**How to avoid:** D-01 (проверено: вторая команда в том же app → exit 2 `No such command 'dQw4w9WgXcQ'`); `cli.py` — **нулевой дифф**; отдельный контракт-тест `test_collect_cli_contract.py` со своими строками.
**Warning signs:** любой дифф в `ingestion-service/src/ingestion_service/cli.py`.

### Pitfall 24-9: `days_of_week` как массив без нормализации

**What goes wrong:** PATCH присылает `[7,1,1]` → в БД дубликаты и «ежедневно» превращается в три дня; UI рендерит набор чекбоксов и показывает два «Пн».
**Why it happens:** массив принимается «как есть».
**How to avoid:** в use-case нормализовать: `sorted(set(days))`, диапазон `1..7`, непусто; сохранять нормализованное; в ответе — нормализованное. CHECK-констрейнт — второй барьер, не первый.
**Warning signs:** PATCH `{days_of_week:[1,1,1]}` → в ответе 3 элемента.

### Pitfall 24-10: UI-копирайт ловит запрещённое слово

**What goes wrong:** подпись «Расписание сбора» или «Планировщик запускается каждые 15 минут» роняет `"pipeline config no execution controls render"` — и падает **весь** тест страницы, не только новый блок.
**Why it happens:** D-17/D-22 требуют объяснить московское время, и «расписание» само просится в текст.
**How to avoid:** точный бан-лист из теста — **`["Запустить", "Выполнить", "Запуск", "Планировщик", "Расписание"]`**, проверяется и по `innerText` всей `admin-pipeline-page`, и по accessible-name кнопок. Копирайт: «Автоматический сбор», «Дни недели», «Время», «включён/выключен», «Время указывается по московскому времени». Слово «сбор» — можно, «расписание» — нельзя.
**Warning signs:** падает существующий трипваер, а не новый тест.

### Pitfall 24-11: guard-тест ING-07 проверяет только прямые импорты

**What goes wrong:** `collect_cli.py` напрямую не импортирует `backend`, но через `data_collection` → … → `backend` цепочка всё равно достижима (или появится позже). Grep по `"import backend"` этого не видит.
**Why it happens:** статический grep не строит граф.
**How to avoid:** AST-обход **графа** импортов от `collect_cli` + изолированная runtime-проверка в subprocess (`import ingestion_service.collect_cli; assert 'backend' not in sys.modules`). Два независимых доказательства (§10).
**Warning signs:** guard зелёный, а `sys.modules` после импорта содержит `backend`.

## Code Examples

### 1.3. Порт и адаптер листинга (форма — копия `YouTubeOEmbedAdapter`)

```python
# data-collection/src/data_collection/ports/video_list_provider.py
from __future__ import annotations

from typing import Protocol

from data_collection.dto.video_ref import FeedListing


class VideoListProvider(Protocol):
    """Recent-window listing for one channel/playlist (ING-02, D-24)."""

    async def list_recent(self, *, kind: str, source_id: str) -> FeedListing: ...
```

```python
# data-collection/src/data_collection/dto/video_ref.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VideoRef:
    video_id: str
    published: datetime          # tz-aware, нормализован к UTC


@dataclass(frozen=True)
class FeedSkip:
    video_id: str | None
    reason: str                  # "missing_video_id" | "invalid_published" | ...


@dataclass(frozen=True)
class FeedListing:
    videos: tuple[VideoRef, ...]
    skipped: tuple[FeedSkip, ...]
```

> **Почему `skipped` возвращается, а не печатается:** `data-collection` — адаптер без побочных эффектов; D-25 требует строку в **stderr**, а stderr — территория `ingest-collect`. Иначе адаптер начнёт писать в stdout при неаккуратном `print`.

### 1.4. Потоковое чтение с cap 1 MiB (проверенная форма)

```python
# data-collection/src/data_collection/adapters/youtube_feed.py
_FEED_ENDPOINT = "https://www.youtube.com/feeds/videos.xml"
_MAX_FEED_BYTES = 1024 * 1024          # D-26
_PARAMS = {"channel": "channel_id", "playlist": "playlist_id"}

async def _read_capped(self, kind: str, source_id: str) -> bytes:
    if kind not in _PARAMS:
        raise FeedError(source_id, reason="unsupported_kind", kind=kind)
    params = {_PARAMS[kind]: source_id}
    try:
        # httpx.AsyncClient.stream — проверено на 0.28.1
        async with self._client.stream("GET", _FEED_ENDPOINT, params=params) as response:
            if response.status_code != 200:
                raise FeedError(source_id, reason="feed_status",
                                status_code=response.status_code)
            declared = response.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > _MAX_FEED_BYTES:
                raise FeedError(source_id, reason="feed_too_large", declared=int(declared))
            buffer = bytearray()
            async for chunk in response.aiter_bytes():
                buffer.extend(chunk)
                if len(buffer) > _MAX_FEED_BYTES:
                    raise FeedError(source_id, reason="feed_too_large",
                                    read=len(buffer))
            return bytes(buffer)
    except FeedError:
        raise
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise FeedError(source_id, reason="feed_network",
                        exception_class=type(exc).__name__) from exc
    except httpx.HTTPError as exc:
        raise FeedError(source_id, reason="feed_network",
                        exception_class=type(exc).__name__) from exc
```

Проверено этой сессией: `httpx 0.28.1`, `AsyncClient.stream(...)` как async-context-manager, `Response.aiter_bytes()`, `content-length` доступен до чтения, прерывание по cap работает.

### 1.5. Разбор: local-name + direct children + проверенный stdlib-барьер

```python
import xml.etree.ElementTree as ET

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")   # локальная копия инварианта
_DTD_MARKERS = (b"<!DOCTYPE", b"<!ENTITY")          # защита в глубину, см. ниже


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(raw: bytes, *, source_id: str) -> FeedListing:
    head = raw[:4096].upper()
    if any(marker in head for marker in _DTD_MARKERS):
        # YouTube-фид не содержит DTD. Явный отказ сужает поверхность до нуля
        # и делает намерение видимым в коде (defusedxml недоступен — D-26).
        raise FeedError(source_id, reason="feed_doctype")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FeedError(source_id, reason="feed_invalid_xml") from exc

    videos: list[VideoRef] = []
    skipped: list[FeedSkip] = []
    for entry in root:
        if _local(entry.tag) != "entry":
            continue
        raw_id = raw_published = None
        for child in entry:                       # ТОЛЬКО direct children
            name = _local(child.tag)
            if name == "videoId" and child.text:
                raw_id = child.text.strip()
            elif name == "published" and child.text:
                raw_published = child.text.strip()
        if not raw_id or not _VIDEO_ID_RE.fullmatch(raw_id):
            skipped.append(FeedSkip(raw_id, "missing_video_id"))
            continue
        published = _parse_rfc3339(raw_published)
        if published is None:
            skipped.append(FeedSkip(raw_id, "invalid_published"))
            continue
        videos.append(VideoRef(video_id=raw_id, published=published))
    return FeedListing(videos=tuple(videos), skipped=tuple(skipped))
```

`_parse_rfc3339`: `datetime.fromisoformat(text.replace("Z", "+00:00"))`, затем **требовать `tzinfo is not None`** — naive → `invalid_published` (D-25: «без валидного `published`»), и `.astimezone(timezone.utc)` для детерминизма записей в БД. Идиома `.replace("Z", "+00:00")` уже используется в репозитории (`supabase-integration/src/supabase_integration/ingest_source_repository.py:30-31`).

**Почему DOCTYPE-скан всё ещё нужен, хотя бомба отбита (проверено):**
- classic XXE (`<!ENTITY xxe SYSTEM "file:///…">`) → `ParseError: undefined entity &xxe;` — внешняя сущность **не** резолвится, файл не читается.
- billion laughs (6 уровней, 350 байт) → `ParseError: limit on input amplification factor (from DTD and entities) breached` за **0.086 с**.
- Значит `defusedxml` объективно не нужен, а DTD-скан — дешёвая защита в глубину + сигнал читателю, что вопрос продуман. Тест: `<feed><!DOCTYPE …>` → `FeedError(reason="feed_doctype")`.

### 2.2. Курсор: `is_newer` и монотонное продвижение

```python
# ingestion-service/src/ingestion_service/domain/schedule.py
def is_newer(
    published: datetime,
    video_id: str,
    *,
    last_published: datetime | None,
    last_video_id: str | None,
) -> bool:
    """D-07: strict '>' on published, video_id as the same-second tie-break."""
    if last_published is None:
        return True                              # D-08: первый прогон видит всё
    if published > last_published:
        return True
    if published < last_published:
        return False
    if last_video_id is None:
        return True                              # защитный: равная секунда без тай-брейка
    return video_id > last_video_id


def advance_cursor(
    current: tuple[datetime, str] | None,
    candidate: tuple[datetime, str],
) -> tuple[datetime, str]:
    """Монотонно: только вперёд (D-07). Одинаковые секунды разрешает video_id."""
    if current is None:
        return candidate
    if candidate > current:
        return candidate
    return current
```

`datetime` сравнивается по инстанту для tz-aware значений — поэтому `.astimezone(timezone.utc)` перед сравнением делает тесты тривиальными.

### 3.3. Батч: точный seam, без правки пайплайна

```python
# ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
result = await run_ingest_pipeline(
    video.video_id,          # голый id: extract_video_id принимает ^[A-Za-z0-9_-]{11}$
    template,                # Settings.ingest_template (TemplateKind)
    captions=deps.captions,
    metadata_provider=deps.metadata_provider,
    article=deps.article,
    persist=deps.persist,
    on_stage=None,           # D-03: ни одного '✓ …' в stdout сводки
    diagnostics=None,        # --debug сюда не пробрасывается
)
# result.already_saved → счётчик already; курсор всё равно двигается (видео уже в БД)
```

`run_ingest_pipeline` и `cli.py` — **нулевой дифф**. Seam — только значение аргумента `on_stage`.

### 5.3. Due-проверка: чистая функция с инъекцией tz

```python
# ingestion-service/src/ingestion_service/domain/schedule.py
@dataclass(frozen=True)
class IngestionSchedule:
    enabled: bool
    time_of_day: time
    days_of_week: tuple[int, ...]     # ISO 1=Mon … 7=Sun
    last_run_at: datetime | None


def is_due(schedule: IngestionSchedule, *, now_utc: datetime, tz: tzinfo) -> bool:
    """D-21/D-22: 'пора' если сегодня разрешённый день, время наступило,
    и с прошлого срабатывания мы ещё не проходили сегодняшнюю точку."""
    if not schedule.enabled:
        return False
    local_now = now_utc.astimezone(tz)
    if local_now.isoweekday() not in schedule.days_of_week:
        return False
    target = datetime.combine(local_now.date(), schedule.time_of_day, tzinfo=tz)
    if local_now < target:
        return False
    if schedule.last_run_at is None:
        return True
    return schedule.last_run_at.astimezone(tz) < target
```

Свойства, которые надо зафиксировать тестами:
- «не пора» до `time_of_day`; «пора» в ровно `time_of_day`; не «пора» на следующий день, если сегодняшнее срабатывание записало `last_run_at`.
- Пропущенный день (VM лежала) → на следующий разрешённый день «пора» **однократно** (catch-up; `Persistent=false` из D-21 компенсирован).
- `enabled=false` → никогда.
- `days_of_week` не содержит сегодня → никогда.
- Идемпотентность: два вызова подряд с одним `now_utc` дают одинаковый ответ; после записи `last_run_at = now` второй даёт `False`.
- **DST-рассуждение для Москвы:** `Europe/Moscow` — постоянный UTC+3 без переходов (с 2014), поэтому `datetime.combine(date, time, tzinfo=tz)` однозначен, `fold` не нужен. Это **не** верно для DST-зоны — если tz когда-нибудь сменят, `combine` даст неоднозначность в час перехода. Зафиксировать комментарием + тест, что `is_due` не использует `datetime.now()` внутри (инъекция `now_utc`).

### 6.4. Монотонный UPDATE курсора

```sql
-- параметры: $published, $video_id, $pk
update public.pipeline_ingest_sources
   set last_seen_published_at = $published,
       last_seen_video_id      = $video_id,
       updated_at              = now()
 where id = $pk
   and (
        last_seen_published_at is null
     or last_seen_published_at < $published
     or (last_seen_published_at = $published and coalesce(last_seen_video_id, '') < $video_id)
   );
```

Выполняется **после каждого успешного видео** (не одним UPDATE в конце): `RuntimeMaxSec` (D-23) может убить прогон, и тогда уже сделанная работа не переплачивается заново. Верхняя граница — `INGEST_MAX_VIDEOS_PER_SOURCE` (5) записей на источник за прогон.

### 9. Unit-файлы (скелет, соответствующий D-19…D-23)

```ini
# deploy/systemd/digest-ingest.service
[Unit]
Description=Digest CDS scheduled ingestion (drafts + pending shortlist rows only)
Wants=network-online.target
After=network-online.target
OnFailure=digest-ingest-alert.service

[Service]
Type=oneshot
User=digestcds
Group=digestcds
WorkingDirectory=/opt/digest-cds
EnvironmentFile=/etc/digest-cds/ingest.env
Environment=TZ=UTC
ExecStart=/usr/bin/flock -n -E 75 /run/digest-ingest.lock /opt/digest-cds/.venv/bin/ingest-collect
RuntimeMaxSec=1800
SuccessExitStatus=0 75
NoNewPrivileges=true
PrivateTmp=true
```

```ini
# deploy/systemd/digest-ingest.timer
[Unit]
Description=Poll whether scheduled ingestion is due (every 15 minutes)

[Timer]
OnCalendar=*:0/15
Persistent=false
Unit=digest-ingest.service

[Install]
WantedBy=timers.target
```

```ini
# deploy/systemd/digest-ingest-alert.service
[Unit]
Description=Digest CDS scheduled-ingestion failure alert (journald only)

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo "digest-ingest.service failed: journalctl -u digest-ingest.service" >&2'
```

Что проверяет text-контракт (`tests/unit/test_phase24_systemd_units.py`):
1. три файла существуют с точными именами;
2. service содержит `Type=oneshot`, `EnvironmentFile=`, `OnFailure=digest-ingest-alert.service`, `RuntimeMaxSec=1800`, `flock -n`, `-E 75`, `SuccessExitStatus=`;
3. `ExecStart=` содержит **абсолютный** путь, оканчивающийся на `/.venv/bin/ingest-collect` (никакого голого `ingest-collect`);
4. timer содержит `OnCalendar=*:0/15` и `Persistent=false`;
5. alert-юнит существует и `Type=oneshot`;
6. **ни в одном** юните нет `DEEPSEEK_API_KEY=`, `SUPABASE_SECRET_KEY=`, `SUPABASE_URL=`, `SMTP_PASSWORD=` (секреты — только в `EnvironmentFile`);
7. **ни в одном** юните нет `publish`, `/admin/shortlist/send`, `curl` — текстовый близнец ING-07.

> ⚠ Права 0600 на `EnvironmentFile` текстовым тестом **не проверяются** (это ФС на VM). Это операторский шаг runbook, и план должен назвать его явно, а не делать вид, что тест его покрывает.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| YouTube Data API v3 (`playlistItems.list` + key) | Atom `feeds/videos.xml`, ключ не нужен | решение фазы (STACK.md §(b)) | Снимает ADR-0002-гейт; окно 15 записей без пагинации |
| `defusedxml` как обязательная защита XML | expat в CPython ≥3.12 отбивает XXE + amplification | проверено этой сессией | `defusedxml` не нужен — но DTD-скан остаётся защитой в глубину |
| `cron` + ручной `flock`/redirect/MAILTO | systemd `Type=oneshot` + timer + journald + `OnFailure=` | — | Структурная несовместимость двух прогонов, env из `EnvironmentFile`, видимость через `journalctl` |
| Планировщик «знает время» в `OnCalendar` | Таймер опрашивает 15 мин, решение — в БД | D-21 | Расписание живёт в БД и меняется из UI без root |

**Deprecated/outdated:**
- `Persistent=true` для этой задачи — D-21: catch-up уже делает due-проверка по `last_run_at`.
- Хранение курса в локальном файле — D-06: удаление источника не уносит курсор, файл рассинхронизируется.
- `yt-dlp`/`feedparser`/`google-api-python-client` — STACK.md §What NOT to Add + D-26.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Реальный YouTube-фид содержит `yt:videoId` и `published` как **direct children** `<entry>`, ~15 записей | §1.2 | Парсер пропустит всё → все источники «читаются», но ноль видео. Митигация: local-name + direct-children + Wave-0 фикстура из живого фида |
| A2 | Точные namespace-URI: `atom`=`http://www.w3.org/2005/Atom`, `yt`=`http://www.youtube.com/xml/schemas/2015`, `media`=`http://search.yahoo.com/mrss/` | §1.5 | Не влияет: парсер матчит по local-name и **не** зависит от URI. Зафиксировано как осознанное решение |
| A3 | `published` приходит как RFC3339 с offset (обычно `+00:00`) | §1.5 | naive-дата отбрасывается как `invalid_published` → возможная потеря видео. Митигация: stderr-строка на каждую отбраковку (D-25) |
| A4 | Целевая VM — Linux с системным `tzdata` (WSL Ubuntu 24.04 подтверждает паттерн), `ZoneInfo("Europe/Moscow")` резолвится | §5.2 | Без tzdata due-проверка падает. Митигация: `ConfigurationError` с диагностикой + smoke в runbook |
| A5 | `Europe/Moscow` — постоянный UTC+3 без DST | §5.3 | Если правила изменятся, `combine` даст неоднозначность в час перехода. Митигация: комментарий + отсутствие `fold`-логики оправдано только для Москвы |
| A6 | `smallint[] <@ ARRAY[1,2,3,4,5,6,7]::smallint[]` — валидный CHECK на Postgres 15 (self-hosted Supabase) | §6.2 | Миграция упадёт на apply. Митигация: оператор применяет один раз; при ошибке — правка CHECK в новой миграции. **Не проверено локально** (нет `psql` в среде) |
| A7 | `OnFailure=` срабатывает на exit 1 (D-12 «упало видео») — это **намеренное** поведение, а не шум | §9, Open Q1 | Если это ошибка, каждый частичный сбой будет шуметь в алертах. D-12 помечен costly, т.е. шкала принята осознанно |
| A8 | `RuntimeMaxSec` применим к `Type=oneshot` на systemd целевой VM | §9 | Не применим → нужен `TimeoutStartSec`. Ubuntu 24.04 = systemd 255, где применим |
| A9 | Supabase/PostgREST отдаёт `timestamptz` как ISO-строку с `Z`, `time` как `"HH:MM:SS"`, `smallint[]` как JSON-массив | §7 | Парсер адаптера упадёт. Митигация: те же `_parse_dt`/`_iso` хелперы, что в `ingest_source_repository.py` |
| A10 | Порядок сортировки фида — по убыванию `published`, но возможны «пиннед»/отредактированные записи вне порядка | §2.1 | Без явной `sorted()` лимит отрежет не тот конец (Pitfall 24-5) |

**Если таблица не пуста** — A1/A6/A8 требуют подтверждения на этапе plan/discuss или Wave-0 разведки; A2/A3/A4/A5/A9/A10 закрыты конструктивно (парсер не зависит от URI, tz инъектируется, сортировка явная).

## Open Questions (RESOLVED)

Все пять вопросов закрыты до планирования; ответы ниже — обязательные входы для планов 24-01…24-06.

1. **Срабатывает ли `OnFailure=` на exit 1 намеренно?** — **RESOLVED: да, намеренно.**
   - What we know: D-12 задаёт 0/1/2 и помечает шкалу costly; D-10 говорит «плюс `systemctl --failed` и alert-юнит».
   - Resolution: exit 1 красит unit как failed и будит alert — это единственный способ сделать частичный сбой видимым (D-09/D-10). Alert-юнит обязан различать «exit 1 = частичный» и «exit 2 = ни один источник»: `ExecStart=/bin/sh -c` читает `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}` и печатает разные сообщения для веток `1)` и `2)`. Реализуется в 24-04 (`deploy/systemd/digest-ingest-alert.service`), проверяется text-контрактом и UAT §5e.

2. **Naive `published` — отбрасывать или считать UTC?** — **RESOLVED: отбрасывать.**
   - What we know: D-25 говорит «без валидного `published` → пропустить».
   - Resolution: naive-дата невалидна (`invalid_published`) — неверная дата тихо сдвинет курсор и потеряет видео навсегда; отбраковка видна в stderr. Реализуется в 24-01 (task 2, behavior «`published` без offset (naive) … `skipped`»); runbook §5e фиксирует причину.

3. **Где именно живёт schedule-репозиторий планировщика?** — **RESOLVED: локальный адаптер в `ingestion-service/adapters/`.**
   - What we know: `supabase-integration` импортирует `backend.domain.*` (19 файлов) → транзитивно `backend`.
   - Resolution: локальный адаптер — прецедент `ingestion_service/adapters/supabase_persist.py` уже существует, а ING-07 делает альтернативу недоказуемой (AST/runtime guard в 24-04 запрещает корень `backend`). `SupabaseCollectSourceReader` в 24-01/24-03 — локальный; backend-адаптер 24-05 живёт в `supabase-integration`, потому что он не входит в граф `collect_cli`.

4. **`/admin/ingestion-schedule` или `/admin/ingest-schedule`?** — **RESOLVED: `/admin/ingestion-schedule`.**
   - Resolution: singleton в единственном числе, по аналогии с `/admin/pipeline/config`; имя `ingest-sources` уже занято списком. Зафиксировано в 24-05.

5. **Нужен ли optimistic-lock/версия на PATCH?** — **RESOLVED: нет.**
   - What we know: один оператор, D-16 «сохранение сразу по изменению».
   - Resolution: last-write-wins, как `pipeline_config`. `updated_at` пишется на каждое сохранение (24-05) и отдаётся в ответе для наблюдаемости, но **не** используется как precondition.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (проект) | всё | ✓ | `.venv` = cpython-3.12 (Windows dev), 3.12.3 (WSL) | — |
| `uv` | entry point / sync | ✓ | 0.10.9 | — |
| `httpx` | фид | ✓ | 0.28.1 | — |
| `typer` | `ingest-collect` | ✓ | `>=0.27.2` | — |
| `zoneinfo` + `Europe/Moscow` | due-проверка | ✗ на Windows dev / ✓ на Linux | — / `/usr/share/zoneinfo/Europe/Moscow` | **Инъекция `tzinfo`** в тестах; на VM — системный tzdata (Ops) |
| `tzdata` (pip) | — | ✗ | — | **Не добавлять** (D-26); не требуется при инъекции tz |
| systemd | таймер | ✗ на dev (Windows) | — | Только text-контракт локально; реальный прогон — на VM |
| `flock` (util-linux) | lock | ✗ на dev / ✓ в WSL | 2.39.3 | Text-контракт; оба флага (`-n`, `-E`) подтверждены |
| `psql` | проверка CHECK-синтаксиса | ✗ | — | Миграция применяется оператором; см. A6 |
| Исходящий доступ к `youtube.com` | живой фид | ✗ (TLS reset, `WinError 10054`) | — | Фикстуры в тестах; живой smoke — на VM |
| `git` remote `origin` | коммит | ✓ | — | Только через WSL (AGENTS.md) |

**Missing dependencies with no fallback:**
- Нет. Всё, что нужно тестам, либо есть, либо обходится инъекцией/фикстурой.

**Missing dependencies with fallback:**
- `zoneinfo`/tzdata на Windows dev → инъекция `tzinfo`; на VM — системный tzdata (Ops-шаг).
- Исходящий YouTube из среды исследования → `httpx.MockTransport`-фикстуры; живой smoke на VM (runbook).
- systemd/`flock` локально → text-контракт; живой прогон на VM.
- `psql` локально → A6 в Assumptions Log + операторский apply.

## Validation Architecture

> `workflow.nyquist_validation` в `.planning/config.json` отсутствует → трактуем как **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest>=8.3.0` (unit) + `@playwright/test ^1.62.1` (web/proof) |
| Config file | `pyproject.toml` (`testpaths = ["tests/unit"]`, `pythonpath = ["."]`); `playwright.config.js` (`testDir: "./tests"`, project `web` на `http://127.0.0.1:5174`) |
| Quick run command | `uv run pytest tests/unit/test_youtube_feed_adapter.py tests/unit/test_schedule_due.py -q` |
| Full suite command | `uv run pytest` + `npm run test:web` (базовая линия — 110 passed, STATE.md §«Vite dev-server flakiness»; сначала убить stale listener на 5174) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command / File | Observable signal | File Exists? |
|--------|----------|-----------|--------------------------|-------------------|--------------|
| ING-02 | Atom-фид 200 → `VideoRef` с `video_id` + tz-aware `published` | unit (adapter) | `pytest tests/unit/test_youtube_feed_adapter.py::test_parses_channel_feed` | `FeedListing.videos` содержит ожидаемый id и ровно тот `published` | ❌ Wave 0 |
| ING-02 | URL-формы: `?channel_id=` для channel, `?playlist_id=` для playlist | unit (adapter) | `::test_channel_uses_channel_id_param` / `::test_playlist_uses_playlist_id_param` | `request.url.params` в `MockTransport`-хендлере | ❌ Wave 0 |
| ING-02 | Запись без `videoId` / с битым `published` → в `skipped`, остальные живы | unit (adapter) | `::test_skips_entry_without_video_id` | `len(videos)==N`, `skipped` содержит причину (D-25) | ❌ Wave 0 |
| ING-02 | не-200 / битый XML / oversize → `FeedError` с reason | unit (adapter) | `::test_non_200_maps_to_feed_status`, `::test_invalid_xml`, `::test_oversize_rejected_before_parse` | `FeedError.reason in {...}` (D-26 `feed_too_large`) | ❌ Wave 0 |
| ING-02 | только `is_enabled` источники попадают в прогон | unit (use-case) | `tests/unit/test_collect_batch.py::test_only_enabled_sources_listed` | fake reader вызван 1 раз, атомарный список = enabled | ❌ Wave 0 |
| ING-02 | только draft + pending shortlist, никакого publish | unit (use-case) + guard | `test_collect_batch.py::test_persist_called_once_per_video` + §ING-07 | `FakeDraftPersister.stored` растёт, никакой publisher-порт не запрашивается | ❌ Wave 0 |
| ING-05 | повторный прогон неизменённого фида = **0** вызовов LLM | unit (use-case) | `test_collect_batch.py::test_rescan_of_unchanged_feed_makes_zero_llm_calls` | `FakeArticleGenerator.calls == []` после второго прогона (PITFALL 21) | ❌ Wave 0 |
| ING-05 | strict `>` + тай-брейк по `video_id` | unit (domain) | `tests/unit/test_schedule_due.py::test_cursor_tie_break_by_video_id` | `is_newer` True/False на равной секунде | ❌ Wave 0 |
| ING-05 | первый прогон (`NULL`) берёт 5 **самых старых** | unit (use-case) | `test_collect_batch.py::test_first_run_takes_oldest_within_limit` | обработанные id = 5 старейших (Pitfall 24-5) | ❌ Wave 0 |
| ING-05 | курсор двигается только вперёд, условие UPDATE | unit (adapter contract) | `test_supabase_collect_sources_contract.py::test_cursor_update_is_monotonic` | захваченный `update`-payload + фильтры | ❌ Wave 0 |
| ING-06 | due: время/день/enabled/last_run_at | unit (domain) | `test_schedule_due.py` (5 тестов) | булев результат при фиксированном `now_utc` + `tz` | ❌ Wave 0 |
| ING-06 | изоляция: упавшее видео → stderr + `failed+=1`, батч продолжается | unit (use-case) | `test_collect_batch.py::test_failed_video_does_not_abort_batch` | второй видео persist'нут, exit code 1 | ❌ Wave 0 |
| ING-06 | изоляция: нечитаемый источник → stderr + next source | unit (use-case) | `::test_feed_error_skips_source_and_continues` | второй источник обработан | ❌ Wave 0 |
| ING-06 | exit codes 0/1/2 | unit (CLI) | `tests/unit/test_collect_cli_contract.py` (3 теста) | `CliRunner(...).exit_code` | ❌ Wave 0 |
| ING-06 | сводка в stdout, диагностика только в stderr, нет `✓ …` | unit (CLI) | `test_collect_cli_contract.py::test_summary_on_stdout_no_checkmarks` | `"✓" not in result.stdout`, `result.stderr` содержит `video_id` | ❌ Wave 0 |
| ING-06 | ноль включённых источников → честная строка, exit 0, `last_run_at` записан | unit (use-case) | `::test_zero_enabled_sources_exits_zero_and_stamps_last_run` | счётчики нулевые, stamp вызван | ❌ Wave 0 |
| ING-06 | «не пора» = один SELECT, ноль сетевых вызовов | unit (use-case) | `::test_not_due_makes_no_network_calls` | `FakeFeed.calls == []` | ❌ Wave 0 |
| ING-06 | text-контракт юнитов (7 проверок §9) | text-contract | `tests/unit/test_phase24_systemd_units.py` | наличие/отсутствие токенов в тексте файлов | ❌ Wave 0 |
| ING-07 | граф импортов `collect_cli` не достигает `backend` | static (AST) | `tests/unit/test_phase24_scheduler_guard.py::test_import_graph_has_no_backend` | обход `ast` по `src/` от корня модуля | ❌ Wave 0 |
| ING-07 | runtime: `import collect_cli` не грузит `backend` | runtime (subprocess) | `::test_import_does_not_load_backend` | `sys.modules` в чистом интерпретаторе | ❌ Wave 0 |
| ING-07 | юниты не содержат `publish`/`send` | text-contract | часть `test_phase24_systemd_units.py` | подстрочный скан | ❌ Wave 0 |
| ING-07 | `ingest <url>` stdout байт-идентичен | PRESERVE | `uv run pytest tests/unit/test_cli_ingest_contract.py` | `EXPECTED_SUCCESS_LINES` + `stderr == ""` | ✅ **существующий, не редактировать** |
| ING-02/06 | блок «Автоматический сбор» виден между источниками и YAML | Playwright | `tests/admin.spec.js` → новый describe | `boundingBox().y` источника < блока < редактора | ❌ Wave 0 |
| ING-06 | сохранение немедленно + рендер по ответу сервера | Playwright | тот же describe | toggle → mock-ответ → состояние контрола | ❌ Wave 0 |
| ING-06 | «не пора»-состояние не рисует ложных значений | Playwright | тот же describe | `last_run_at` из mock рендерится как текст | ❌ Wave 0 |
| D-17 | запрещённые слова не появились | PRESERVE | `tests/admin.spec.js::"pipeline config no execution controls render"` | бан-лист `["Запустить","Выполнить","Запуск","Планировщик","Расписание"]` | ✅ существующий |
| ING-02 | миграция 013 — колонки + singleton + RLS | text-contract | `tests/unit/test_phase24_migration_013.py` | подстроки SQL | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit -q` (полный unit-набор дешёвый; ~секунды) + новый тест-файл задачи.
- **Per wave merge:** `uv run pytest` **и** `npm run test:web` (после проверки/убийства stale listener на `127.0.0.1:5174` — STATE.md).
- **Phase gate:** полный unit + полный Playwright `web` зелёные до `/gsd-verify-work`; живой smoke на VM (`systemctl start digest-ingest.service`, `journalctl -u`) — операторский, не автоматизируется.

### Wave 0 Gaps

- [ ] `tests/unit/test_youtube_feed_adapter.py` — ING-02 листинг (фикстуры: валидный фид, запись без `videoId`, битый `published`, документ без namespace, HTML вместо XML, ответ >1 MiB, chunked без `content-length`).
- [ ] `tests/unit/test_schedule_due.py` — ING-05/06 курсор + due.
- [ ] `tests/unit/test_collect_batch.py` — ING-02/05/06 батч, изоляция, лимит, «0 LLM на повторном прогоне».
- [ ] `tests/unit/test_collect_cli_contract.py` — ING-06 сводка/exit codes (свой контракт; **не** трогать `test_cli_ingest_contract.py`).
- [ ] `tests/unit/test_supabase_collect_sources_contract.py` — чтение sources/schedule, монотонный UPDATE, маппинг SDK-ошибок.
- [ ] `tests/unit/test_phase24_migration_013.py` — text-контракт миграции.
- [ ] `tests/unit/test_phase24_systemd_units.py` — text-контракт юнитов.
- [ ] `tests/unit/test_phase24_scheduler_guard.py` — ING-07 (AST + subprocess).
- [ ] `tests/unit/test_http_ingestion_schedule.py` — GET/PATCH admin-поверхности (JWT-харнесс копируется из `test_http_ingest_sources.py`).
- [ ] `tests/unit/test_ingestion_schedule_use_cases.py` — нормализация `days_of_week`, валидация времени.
- [ ] `tests/admin.spec.js` — новый describe для блока сбора + `resetIngestionScheduleMock`.
- [ ] **AMEND** `tests/unit/test_data_collection_public_api.py:124` — `path.name.endswith("cli.py")`; и `:52` + `PUBLIC_NAMES` — расширить `__all__`.
- [ ] **AMEND** `tests/unit/test_ingestion_env_example.py` `REQUIRED_INGESTION_KEYS` — + `INGEST_TEMPLATE`, + `INGEST_MAX_VIDEOS_PER_SOURCE`.
- [ ] `ingestion-service/.env.example` — две новые строки.
- [ ] Framework install: не требуется.

## Security Domain

> `security_enforcement` в конфиге не выставлен → считаем enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Существующий `require_admin` + ES256 JWT-харнесс (`backend/interface/http/deps.py`) |
| V3 Session Management | no | Новых сессий не появляется |
| V4 Access Control | yes | `ingestion_schedule`: RLS enabled + **ноль политик**, доступ только `service_role` из `composition/live.py`; все роуты под `Depends(require_admin)` |
| V5 Input Validation | yes | Pydantic `extra="forbid"` + `pattern` на `time_of_day`; `days_of_week` нормализуется в use-case; `kind`/`source_id` уже валидируются Phase 23 — листинг **не** принимает id от пользователя, только из БД |
| V6 Cryptography | no | Никакой криптографии; TLS к `youtube.com` — через `httpx` (stdlib `ssl`) |
| V7 Error Handling / Logging | yes | Секреты не печатаются: `EnvironmentFile` вне репозитория, `Settings`-поля с `repr=False`, stderr несёт только `video_id` + reason |
| V12 Files & Resources | yes | 1 MiB cap (D-26) + `RuntimeMaxSec=1800` (D-23) — единственные контроли объёма/времени на этот путь |

### Known Threat Patterns for {Atom feed + systemd + Supabase}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XML external entity (file/SSRF через фид) | Information Disclosure | **Проверено:** `ET.fromstring` не резолвит внешние сущности (`undefined entity`). Плюс DTD-скан → `feed_doctype` |
| Billion laughs / amplification DoS | Denial of Service | **Проверено:** expat отбивает (`amplification factor breached`, 0.086 с). Плюс 1 MiB cap **до** парсинга |
| Подмена фида / MITM | Tampering | HTTPS + системные CA через `httpx`; прокси только из `EnvironmentFile` |
| Секреты в unit-файле или в git | Information Disclosure | Секреты только в `/etc/digest-cds/ingest.env` (0600); text-тест запрещает `*_KEY=`/`*_SECRET=` в `deploy/systemd/` |
| Неавторизованное изменение расписания (RLS-обход) | Elevation of Privilege | RLS enabled + ноль политик; `service_role` только в composition; SPA ходит через `web/src/services/ingestScheduleApi.js` |
| Планировщик как publish/send (PITFALL 23) | Elevation of Privilege | ING-07: AST-граф + subprocess `sys.modules` + текстовый скан юнитов |
| Подделка `source_id` в прогон (инъекция чужого канала) | Tampering | `ingest-collect` читает id **только** из `pipeline_ingest_sources` (валидированы Phase 23), не из argv |
| Утечка содержимого в journald | Information Disclosure | stderr — только `video_id` + reason; никакого текста транскрипта/статьи (совпадает с DBG-02) |
| Resource exhaustion через зависший прогон | DoS | `RuntimeMaxSec=1800` + `INGEST_MAX_VIDEOS_PER_SOURCE` + `flock` |

## Sources

### Primary (HIGH confidence — прочитано `Read` в этой сессии)
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py:32-160` — контракт `run_ingest_pipeline`, три `on_stage`-guard'а.
- `ingestion-service/src/ingestion_service/cli.py:30,72-122` — Typer app, `_on_stage`, exit codes, stdout-строки.
- `ingestion-service/src/ingestion_service/composition/clients.py:20-99` — `build_httpx_client` (**AsyncClient**), фабрики портов.
- `ingestion-service/src/ingestion_service/composition/settings.py:16-89` — `Settings.from_env` / `ConfigurationError`.
- `ingestion-service/src/ingestion_service/url.py:8,83-104` — `_ID_RE`, `extract_video_id`.
- `ingestion-service/src/ingestion_service/application/ports/{persist,diagnostics}.py` — `PersistResult`, `Clock`.
- `data-collection/src/data_collection/{__init__,adapters/youtube_oembed.py,errors/metadata.py,dto/template_kind.py}` — публичный API, форма адаптера/ошибок.
- `backend/src/backend/{application/ports/ingest_sources.py,application/use_cases/ingest_sources.py,interface/http/routes/admin.py,composition/{container,live}.py,domain/ingest_source.py,tests_support/in_memory.py,domain/errors.py}` — admin-поверхность Phase 23.
- `supabase-integration/{migrations/011,012.sql,src/supabase_integration/{__init__,ingest_source_repository}.py}` — идемпотентные миграции и адаптер.
- `web/src/{pages/AdminPipelineConfigPage.jsx,components/IngestSourcesSection.jsx,services/{pipelineConfigApi,ingestSourcesApi}.js,main.jsx,utils/forbiddenChrome.js}` — точка вставки, dirty, harness.
- `tests/unit/{test_cli_ingest_contract,test_data_collection_public_api,test_phase16_migration_011,test_phase23_migration_012,test_http_ingest_sources,test_supabase_ingest_source_repository_contract,test_ingestion_env_example,test_ingest_pipeline,test_persist_port}.py` + `tests/admin.spec.js:1804-1965` — трипваеры и стиль тестов.
- `.planning/{ROADMAP.md,REQUIREMENTS.md,STATE.md,research/STACK.md,research/PITFALLS.md}`, `.planning/phases/24-scheduled-ingestion/24-CONTEXT.md`.

### Empirically verified in this session (HIGH confidence)
- `typer` — вторая `@app.command()` превращает app в группу; `ingest <url>` → **exit 2** `No such command 'dQw4w9WgXcQ'`; одиночная команда → exit 0. (probe, удалён после прогона)
- `xml.etree.ElementTree` (CPython 3.12) — XXE `SYSTEM "file:///…"` → `ParseError: undefined entity &xxe;`; billion laughs (350 B) → `ParseError: limit on input amplification factor (from DTD and entities) breached`, 0.086 с; direct children `<entry>` включают `{…xml/schemas/2015}videoId`, `{…Atom}published`, `{…mrss/}group`.
- `httpx 0.28.1` — `AsyncClient.stream(...)` async-CM, `Response.aiter_bytes()`, `content-length` до чтения, cap-прерывание работает.
- `time.fromisoformat("06:00:00")` → `time(6, 0)`.
- `flock from util-linux 2.39.3` — `-E, --conflict-exit-code` присутствует.
- `zoneinfo.ZoneInfo("Europe/Moscow")` — **падает** на Windows dev (`ZoneInfoNotFoundError`, нет `tzdata`); **резолвится** на Ubuntu 24.04 (WSL, `/usr/share/zoneinfo/Europe/Moscow`, Python 3.12.3).
- Исходящий `https://www.youtube.com/...` — **недоступен** из среды (`httpcore.ConnectError: [WinError 10054]`).

### Secondary (MEDIUM confidence)
- Форма Atom-фида (endpoint, ~15 записей, набор полей) — `.planning/research/STACK.md` §(b) (исследование 2026-10-14, несколько независимых источников).
- `RuntimeMaxSec` на `Type=oneshot` — systemd.timer/service man-страницы через STACK.md §(c); целевая systemd 255 предполагается (Ubuntu 24.04).

### Tertiary (LOW confidence / требует подтверждения — см. Assumptions Log)
- A1/A3 — точный набор direct-children и формат `published` в живом фиде (сеть недоступна).
- A6 — валидность `smallint[] <@ ARRAY[…]::smallint[]` CHECK на Postgres целевой VM (нет `psql`).
- A4 — дистрибутив целевой VM (WSL Ubuntu 24.04 — прокси, не факт).

## Recommendations for Planning

### Маппинг задач на решения D-01…D-26

| Задача (черновик) | Реализует | Слой / файлы | RED-сигнал |
|---|---|---|---|
| **T1. Порт + DTO листинга** | D-24, discretion | `data-collection/{dto/video_ref.py,ports/video_list_provider.py,__init__.py}` | `test_youtube_feed_adapter` / `test_data_collection_public_api` (AMEND) |
| **T2. Atom-адаптер** | D-24, D-25, D-26 | `data-collection/adapters/youtube_feed.py`, `errors/feed.py` | 7 unit-тестов адаптера (200/404/XML/oversize/skip/params) |
| **T3. Домен: `is_newer` / `is_due` / `advance_cursor`** | D-07, D-08, D-15, D-22 | `ingestion-service/domain/schedule.py` | `test_schedule_due.py` (8 тестов) |
| **T4. Settings: 2 новых ключа** | D-02, D-04 | `composition/settings.py` + `.env.example` | `test_ingestion_settings.py` (расширить) + `test_ingestion_env_example` (AMEND) |
| **T5. Порт чтения sources/schedule + Supabase-адаптер** | D-06, D-14, discretion | `application/ports/collect_sources.py`, `adapters/supabase_collect_sources.py` | `test_supabase_collect_sources_contract.py` (монотонный UPDATE, маппинг ошибок) |
| **T6. Use-case батча** | D-03, D-05, D-09, D-11, D-12 | `application/use_cases/collect_batch.py` | `test_collect_batch.py` (8 тестов: enabled-only, oldest-first, limit, isolation, 0-LLM, cursor, zero-sources, not-due) |
| **T7. `ingest-collect` CLI** | D-01, D-03, D-12, D-13 | `collect_cli.py`, `pyproject.toml:[project.scripts]` | `test_collect_cli_contract.py` (summary/exit/exit-2) |
| **T8. Миграция 013** | D-06, D-14 | `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` | `test_phase24_migration_013.py` (text) |
| **T9. Backend: порт + use-case + HTTP** | D-14, D-15, D-16 | `backend/{domain/ingestion_schedule.py,application/ports/ingestion_schedule.py,application/use_cases/ingestion_schedule.py,interface/http/routes/admin.py}` | `test_http_ingestion_schedule.py` + `test_ingestion_schedule_use_cases.py` |
| **T10. Backend wiring** | D-14 | `composition/{container,live}.py`, `tests_support/in_memory.py`, `supabase_integration/{ingestion_schedule_repository.py,__init__.py}` | `test_http_ingestion_schedule.py::test_missing_repo_503` + live-wiring тест |
| **T11. SPA-сервис** | D-16 | `web/src/services/ingestScheduleApi.js`, `main.jsx` (harness) | Playwright describe (mock-арм) |
| **T12. SPA-блок** | D-15, D-16, D-17, D-18 | `web/src/components/IngestionScheduleSection.jsx`, `pages/AdminPipelineConfigPage.jsx` | Playwright: порядок блоков, немедленное сохранение, трипваер бан-слов |
| **T13. systemd-юниты** | D-19…D-23 | `deploy/systemd/*` | `test_phase24_systemd_units.py` (7 проверок) |
| **T14. Guard ING-07** | ING-07 | `tests/unit/test_phase24_scheduler_guard.py` | AST-граф + subprocess `sys.modules` |
| **T15. Runbook** | D-10, D-13, D-19, D-21, D-23 | `docs/agents/local-platform-runbook.md` (§4j + §5e) | text-тест на наличие команд (по образцу существующих runbook-тестов) |

### Предлагаемые волны

- **Wave 1 (tracer, вертикальный срез):** T1 → T2 → T3 (курсор) → T4 → T5 (только чтение sources+cursor) → T6 (`enabled`-only, oldest-first, persist) → T7 (сводка/exit 0). Даёт: «фид → драфты, лишнего нет».
- **Wave 2 (инкрементальность):** T3 (`is_due`) + T5 (`last_run_at` stamp) + T6 (курсор, D-08/D-09) + T8 (миграция). Даёт: ING-05 целиком.
- **Wave 3 (ops-защита):** T13 + T14 + T15. Даёт: ING-06 (юниты) и ING-07 (guard).
- **Wave 4 (admin-поверхность):** T9 + T10 + T11 + T12. Даёт: настройку расписания из UI (D-14…D-18). Не блокирует Wave 1–3, потому что due-проверка работает и на дефолтах (нет строки → `enabled=true`, `06:00`, все дни).

> **Порядок волн обоснован:** ING-02/05/06 живут в CLI/БД и не зависят от admin-поверхности; UI-настройка (ING-06-часть D-14) может приехать последней, не блокируя проверяемость ядра. Если планировщик захочет «UI-first», это допустимо, но тогда Wave 4 = tracer и придётся вводить временный seed-дефолт — лишняя работа.

### Трипваеры: PRESERVE / AMEND (обязательно в плане)

| Тест | Диспозиция | Почему |
|---|---|---|
| `tests/unit/test_cli_ingest_contract.py` (`EXPECTED_SUCCESS_LINES`, `stderr == ""`) | **PRESERVE** | ROADMAP tripwire, success criterion 4 |
| `tests/admin.spec.js::"pipeline config no execution controls render"` | **PRESERVE** | D-17 байт-в-байт |
| `tests/unit/test_data_collection_public_api.py::test_ingestion_service_has_no_typer_import` | **AMEND** (`path.name == "cli.py"` → `.endswith("cli.py")`) | `collect_cli.py` обязан импортировать typer |
| `tests/unit/test_data_collection_public_api.py::test_public_all_is_exactly_seven_ingestion_names` + `PUBLIC_NAMES` | **AMEND** | `__all__` расширяется аддитивно (D-24 precedent) |
| `tests/unit/test_data_collection_public_api.py::test_stage_set_is_unchanged` | **PRESERVE** | Не добавлять значений в `Stage`; путь сбора не бросает `IngestError`-стадии |
| `tests/unit/test_ingestion_env_example.py::REQUIRED_INGESTION_KEYS` | **AMEND** (только добавление) | 2 новых не секретных ключа |
| `tests/unit/test_build_ingest_deps_wiring.py` | **PRESERVE** | `build_ingest_deps` не меняется; новые зависимости — в `build_collect_deps` |
| `tests/unit/test_phase16_migration_011.py`, `test_phase23_migration_012.py` | **PRESERVE** | 013 — новый файл, старые миграции не правятся |
| `tests/unit/test_http_ingest_sources.py`, `test_supabase_ingest_source_repository_contract.py` | **PRESERVE** | Schedule-поверхность — отдельные файлы |

### Порядок RED для каждой задачи

1. Adapter (T2): фикстура-строка фида → `FeedListing`; сначала падает `ImportError`/`AttributeError`, затем ассерты.
2. Domain (T3): `is_due`/`is_newer` — чистые функции, RED по значению (не по импорту).
3. Use-case (T6): fakes в `ingestion_service/tests_support/` (по образцу `FakeDraftPersister`, `RecordingDiagnostics`).
4. CLI (T7): `CliRunner` + monkeypatch `build_collect_deps` (по образцу `test_cli_ingest_contract.py`).
5. Backend HTTP (T9): JWT-харнесс **копируется** из `test_http_ingest_sources.py` (он сам копировал `test_http_pipeline_config.py`, который PRESERVE и не редактируется).
6. Text-contracts (T8/T13): падают на `FileNotFoundError`/assert — это законный RED для конфигурационных артефактов (исключение из `tdd.mdc` «конфиги», согласовано прецедентом `test_phase16_migration_011.py`).
7. Guard (T14): RED на отсутствующем модуле `collect_cli`; после T7 — реальная проверка.
8. Playwright (T12): RED на отсутствующем `data-testid`.

### Что НЕ делать в этой фазе

- Не менять `cli.py`, `run_ingest_pipeline`, `url.py`, `persist.py`, `supabase_persist.py`.
- Не добавлять `Stage`-значение, `defusedxml`, `feedparser`, `APScheduler`, `tzdata`, `google-api-python-client`, `yt-dlp`.
- Не добавлять `create policy` в миграцию, не делать `Persistent=true`, не добавлять таблицу истории прогонов.
- Не добавлять кнопку/слово из бан-листа D-17 на `/admin/pipeline`.
- Не вставлять seed-строку `ingestion_schedule(id=1)` в миграцию — дефолт отдаётся кодом, строка появляется при первом `save()`.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — единственная новая вещь — stdlib `xml`/`zoneinfo`; версии `httpx`/`typer`/`flock` проверены в этой сессии; ни одного нового пакета.
- Architecture: **HIGH** — все точки расширения прочитаны (`run_ingest_pipeline`, `Settings`, admin-роутер, composition, `persist_draft_and_enqueue`), seam найден и он однострочный (`on_stage=None`).
- Pitfalls: **HIGH** для проверенных (Typer-группа, XML-барьер, `flock -E`, `ZoneInfo` на Windows, `<entry>` direct children); **MEDIUM** для формы живого фида и CHECK-синтаксиса массива.

**Research date:** 2026-10-18
**Valid until:** 2026-11-17 (30 дней; external feed shape и `smallint[]`-CHECK — единственные места, где возможен дрейф; перепроверить при первом живом smoke на VM)
