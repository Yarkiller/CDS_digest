# Phase 28: Live proof — streamed DeepSeek ingest - Context

**Gathered:** 2026-10-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Доказать на живом длинном ролике, что закоммиченный стриминг-фикс `0dddc75` (`stream=True` + сборка delta в `DeepSeekArticleGenerator._stream_content`, `data-collection/src/data_collection/adapters/deepseek_article.py`) доводит пайплайн до конца: `materials.status='draft'` + `pending`-строка шортлиста, без `network_error` на стадии `llm`. Фаза закрывает `ING-09`.

**In scope (ROADMAP.md, не переобсуждается):**

- Ровно один живой прогон `ingest` на ролике **дольше 10 минут** по реальному DeepSeek-пути.
- Пасс = exit 0 + material id/slug/batch id на stdout + `draft` в БД + `pending` шортлист + отсутствие `APIConnectionError`.
- Записанные операторские предусловия, чтобы прогон повторил другой оператор.
- Инструментальные факты (команда, тайминги, id) — в summary с транскриптом.

**Out of scope:**

- Любая переделка адаптера, новый retry-слой, тюнинг таймаутов, новый клиент, «улучшение» стриминга.
- Правки `ingestion-service`/`data-collection` под фикс: `0dddc75` уже в дереве и не переоткрывается.
- Повторный прогон на том же `youtube_video_id` как «доказательство»: он вернёт `already_saved: true` и не создаст новую пару draft+pending.

</domain>

<decisions>
## Implementation Decisions

### Целевой ролик

- **D-01:** Ролик — `https://www.youtube.com/watch?v=HR7hD8TO4Z8` (`youtube_video_id=HR7hD8TO4Z8`), выбран оператором. Измерено до прогона: длительность **24.14 мин** (558 сниппетов, последний конец 1448.6 s), авто-субтитры `ru` и `en`, транскрипт **20 923 символа** при лимите `MAX_TRANSCRIPT_CHARS=80000`. Id отсутствовал в `materials` на момент проверки — прогон обязан создать новую строку, а не попасть в `already_saved`.
  — **Reversibility:** reversible — выбор ролика не меняет код; другой ролик потребует нового прогона и нового id в evidence.

### Где и как запускается

- **D-02:** Прогон выполняется **агентом в этом workspace** (Windows/PowerShell), командой `uv run --env-file ./ingestion-service/.env ingest <url> --template lecture`. Транскрипт, wall-clock и SQL-выборка попадают в summary без ручного копирования оператором.
  — **Reversibility:** reversible.

- **D-03:** **`--template` обязателен**, хотя буквальная команда в ROADMAP его не содержит: без него Typer завершает процесс кодом **2** (`Missing option '--template'`) ещё до всякой сети — это измерено. В evidence и в summary фиксируется фактическая команда с `--template lecture`, и ROADMAP-строка считается неточной, а не проваленной.
  — **Reversibility:** reversible — это уточнение документации, не изменение кода.

### Предусловие сети (и почему оно часть доказательства)

- **D-04:** **Прямой доступ к YouTube с этой машины заблокирован, и это измерено, а не предположено.** TCP:443 к `www.youtube.com` открывается, но TLS-хендшейк (`ssl.create_default_context().wrap_socket`) уходит в `TimeoutError` и на `www.youtube.com`, и на `www.youtube-nocookie.com`; `api.deepseek.com` при этом даёт TLSv1.3. Поэтому стадия `captions` проходит **только** через прокси из `YOUTUBE_PROXY_URL` (`socks5://adguard:***@192.168.1.68:1080` в `ingestion-service/.env`), а стадия `llm` идёт к DeepSeek напрямую.
  — **Reversibility:** reversible — прокси уже был в `.env`; выключенный прокси даёт `CaptionsNetworkError` на стадии `captions`, а не провал стриминга.

- **D-05:** Прокси — **операторское предусловие, а не часть кода**. Требование к повторному прогону: контейнер `adguard-vpn` жив и подключён (в этой сессии — локация `HANOI`), Windows-хост видит `192.168.1.68:1080`, `YOUTUBE_PROXY_URL` непустой. Секрет прокси в артефактах маскируется (`adguard:***`).
  — **Reversibility:** reversible.

### Форма доказательства

- **D-06:** Доказательство = (а) `--debug` (stderr-тайминги по стадиям, секретобезопасные) + wall-clock вокруг команды, (б) лог прогона, приложенный к фазе, (в) read-only SQL: `materials` по `youtube_video_id` + `digest_shortlist_items` по `material_id`.
  — **Reversibility:** reversible.

- **D-07:** Критерий 3 формулируется как **записанное** значение `stage=llm elapsed_ms` плюс отсутствие `APIConnectionError`/`network_error` во всём логе. Сравнение «до фикса» в этой сессии не измеряется: старый дефект — TCP-idle reset, который в логах проявлялся как `APIConnectionError`; доказательством улучшения считается успешный стриминговый прогон с записанным временем, а не искусственное воспроизведение старого отказа.
  — **Reversibility:** reversible.

### Rider-пункты Phase 27 (в этой же сессии)

- **D-08:** **FU-27-01 закрывается здесь** (`SearchPill.jsx:36` — `{ replace: true }` на пустой отправке) по TDD: сначала падающий Playwright-тест на неизменность `history.length` и уход с `/knowledge` по Back, затем фикс. Это единственный кодовый пункт, перенесённый в фазу.
  — **Reversibility:** reversible — одна опция навигации.

- **D-09:** **Тост `INVALID_ROLE` (27-UAT тест 3) остаётся неснятым**: он требует живого фронтенда с `VITE_USE_MOCKS=false` и аутентифицированной сессии, а прогон `ingest` работает на сервисном ключе и браузера не касается. Фиксируется как всё ещё отложенный пункт, а не как пройденный.
  — **Reversibility:** reversible.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope и требования
- `.planning/ROADMAP.md` § Phase 28 — locked scope facts (proof only, >10 мин, что считается пассом, «при провале фиксируем и останавливаемся») и четыре критерия успеха.
- `.planning/REQUIREMENTS.md` § Ingestion proof — формулировка `ING-09`.
- `.planning/STATE.md` § Blockers/Concerns — операторские риски и засада с `5174`.

### Код, который читается, но не меняется
- `data-collection/src/data_collection/adapters/deepseek_article.py` — `_stream_content`: `stream=True`, сборка `delta.content`, маппинг `APIConnectionError`→`ArticleNetworkError`, `APIStatusError`→`ArticleUnknownError`.
- `ingestion-service/src/ingestion_service/composition/clients.py` — `build_async_deepseek_client` (`max_retries=0`, `DefaultAsyncHttpxClient(trust_env=False)`), `build_youtube_transcript_api` (прокси только здесь, D-17).
- `ingestion-service/src/ingestion_service/cli.py` — `main`: `--template` обязателен, на успехе печатает `material_id`/`slug`/`batch_id`/`rank`/`already_saved`.
- `ingestion-service/src/ingestion_service/composition/settings.py` — `Settings.from_env`, `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS` (дефолт 80 000).

### Код, который меняется (rider)
- `web/src/components/SearchPill.jsx:36` — пустая отправка получает `{ replace: true }` (FU-27-01 / T-27-16).
- `tests/knowledge.spec.js` — новый кейс рядом с `a header submit replaces the history entry`.

### Правила
- `.cursor/rules/tdd.mdc`, `AGENTS.md` — RED-first для rider-фикса.
- `.cursor/rules/architecture.mdc` — адаптеры не трогаются; прокси остаётся в composition.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`--debug` диагностика** (`StderrDiagnostics`) уже даёт постадийные `elapsed_ms`, `transcript_chars`, `response_chars`, `material_id`/`batch_id`/`rank` — готовый инструмент доказательства, новых метрик не требуется.
- **`digest_shortlist_items`** уже содержит `decision: 'pending'` для свежих ингестов (`material_id=24`, `batch=7`, `rank=1`) — форма запроса критерия 2 известна.
- **`uv run --env-file`** снимает обрамляющие кавычки из `.env` (проверено экспериментально: 19 символов вместо 21) — кавычки в `ingestion-service/.env` не ловушка.

### Established Patterns
- Прокси YouTube — только в composition (`build_youtube_transcript_api` / `build_httpx_client`), адаптеры его не видят (D-17).
- `already_saved: true` — идемпотентность по `youtube_video_id` (unique constraint), поэтому повторный прогон того же ролика не является доказательством.
- Шортлист-строка привязывается к материалу через `material_id`, а материал — к ролику через `youtube_video_id`; цепочка доказательства идёт по этим двум ключам.

### Hazards
- **Прямой TLS до YouTube заблокирован** — без прокси прогон падает на `captions`, и это ложно прочитается как проблема стриминга.
- **`--template` обязателен** — без него exit 2 до сети.
- **`youtube_video_id` уникален** — 12 роликов уже в БД, повтор даёт `already_saved`.
- **Прокси с учётными данными** — в артефактах маскировать.
- **Vite-флейк на `5174`** — полные Playwright-прогоны в этой сессии дважды дали массовые падения и зеленели на повторе; перед прогоном проверять слушателя и перезапускать при массовом падении.

</code_context>

<specifics>
## Specific Ideas

- Пасс доказывается **id из stdout**, совпадающими с id в БД, а не наличием строки «✓ saved» в выводе.
- `rank=2` в batch 7 — нормальное поведение (batch не отправлен, rank продолжается), а не аномалия.
- Wall-clock (21.91 s) и `stage=llm elapsed_ms=16578` фиксируются оба: первый — операторское время, второй — измерение самого LLM-стрима.
- Транскрипт прогона прикладывается файлом (`evidence/ingest-run-1.log`), а не пересказом.

</specifics>

<deferred>
## Deferred Ideas

- **Тост `INVALID_ROLE`** — требует живого фронтенда и аутентифицированной сессии; остаётся открытым пунктом 27-UAT теста 3.
- **Сравнительный замер «до/после» фикса** — воспроизведение старого TCP-idle отказа намеренно не делается (это была бы переделка адаптера/искусственный отказ), см. D-07.
- **Замер на нескольких роликах / выборке** — расширение доказательства, не требуется `ING-09`.
- **Автоматизация живого прогона в CI** — отдельная инфраструктурная задача (нужен прокси и реальные ключи).

</deferred>

---

*Phase: 28-live-proof-streamed-deepseek-ingest*
*Context gathered: 2026-10-22*
