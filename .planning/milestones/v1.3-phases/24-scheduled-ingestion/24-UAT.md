---
status: complete
phase: 24-scheduled-ingestion
source: [24-VERIFICATION.md]
started: 2026-10-18T13:30:00.000Z
updated: 2026-10-18T20:55:00.000Z
---

## Current Test

[testing paused — 1 item outstanding]

## Tests

### 1. Live systemd timer

Установить юниты по §4k, заполнить `/etc/digest-cds/ingest.env`,
`sudo systemctl enable --now digest-ingest.timer`, дождаться двух тиков.

expected: `systemctl list-timers digest-ingest.timer` показывает следующее срабатывание ≤15 мин; journald содержит две строки сводки либо `not due: …`; юнит не в failed.
result: pass
note: Прогнано в WSL2 Ubuntu 24.04 (systemd 255) по раскладке §4k; таймер временно ускорен drop-in `OnCalendar=*:0/1`. 4 тика, каждый — `sources: read=0 unreadable=0` + `videos: new=0 ingested=0 already=0 failed=0 skipped_limit=0`; `Result=success`, `systemctl --failed` пуст. Постоянный `OnCalendar=*:0/15` в checked-in юните не менялся.

### 2. flock и конкурентный запуск

Во время активного прогона запустить второй `systemctl start digest-ingest.service`.

expected: Второй запуск завершается кодом 75, `systemctl status` не failed, `digest-ingest-alert.service` не поднимается.
result: pass
note: WSL2 Ubuntu 24.04, systemd 255. Лок держал `flock /run/digest-ingest/lock sleep 120` под `digestcds`; `systemctl start` → `ExecMainStatus=75`, `Result=success` (через `SuccessExitStatus=0 75`), `ActiveState=inactive`, `systemctl --failed` пуст, `InvocationID` alert-юнита не изменился (OnFailure не сработал).

### 3. RuntimeMaxSec и last_run_at

Дождаться/сымитировать прогон дольше 1800 с (или временно уменьшить лимит).

expected: Прогон убит по лимиту (`TimeoutStartSec=1800`); `last_run_at` не обновлён; следующий тик снова `due` и продолжает с того же курсора.
result: pass
note: Пере-проверено после закрытия G-24-3 (24-07). Живой host WSL2 Ubuntu 24.04 / systemd 255: `systemctl show digest-ingest.service -p Type -p TimeoutStartUSec -p RuntimeMaxUSec` → `Type=oneshot`, `TimeoutStartUSec=30min`, `RuntimeMaxUSec=infinity`; предупреждение «RuntimeMaxSec= has no effect … Ignoring.» больше не появляется. Live-проба T3 из 24-07-SUMMARY: `TimeoutStartSec=500ms` drop-in → `Result=timeout ExecMainStatus=15 elapsed 530 ms`, `last_run_at` остался `T_backdated2`; после `systemctl revert` следующий запуск заштамповал. Контракт: `uv run pytest tests/unit/test_phase24_systemd_units.py -q` → 15 passed.

### 4. OnFailure alert (exit 1 vs exit 2)

Форсировать exit 1 и отдельно exit 2, затем `journalctl -u digest-ingest-alert.service`.

expected: Разные сообщения «partial failure … (exit 1)» и «no source could be read … (exit 2)».
result: pass
note: Пере-проверено после закрытия G-24-4 (24-08). На хосте установлен исправленный юнит: `ExecStart` читает `${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}`. Live-проба T3 из 24-08-SUMMARY: exit 1 → «partial failure: a video failed or the run state could not be recorded (exit 1)», exit 2 → «no source could be read or the schedule was unreadable (exit 2)»; до фикса тот же exit-2 печатал «unexpected failure (exit exited)». Контракт: `uv run pytest tests/unit/test_phase24_systemd_units.py -q` → 15 passed.

### 5. EnvironmentFile 0600

`ls -l /etc/digest-cds/ingest.env` на VM.

expected: Режим `0600`, владелец root; секретов в git и в юнитах нет.
result: pass
note: `-rw------- 1 root root /etc/digest-cds/ingest.env`; systemd читает файл как root до сброса привилегий, сервис под `digestcds` стартует штатно. В юнитах нет `SUPABASE_*`/`DEEPSEEK_*` (text-контракт). Отдельно: `.env.example` заканчивается `\r\n` — при дописывании ключей без нормализации строк клеится к последней строке (наступил при установке, лечится `tr -d '\r'` + завершающий `\n`).

### 6. Живой прогон на реальном включённом источнике

YouTube Atom + Supabase, затем проверить БД.

expected: Новые видео появляются как `materials.status='draft'` и строки шортлиста `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор.
extra: D-27 — due-тик при нуле включённых источников не меняет `last_run_at`; включите источник в тот же день МСК и убедитесь, что следующий 15-минутный тик его собирает. Отдельно подтвердите пограничный случай: ≥1 включённый, но все источники нечитаемы — сейчас `last_run_at` штампуется (D-27 это явно не регламентирует).
result: skipped
reason: "Deferred follow-up: живой прогон на реальном включённом источнике отложен — в `pipeline_ingest_sources` нет ни одной строки, а запуск пишет `materials`/шортлист в общую БД и требует реального YouTube-фида. Требуется операторское решение."
blocked_by: third-party
note: Пере-проверка 2026-10-18T20:52Z — PostgREST `select * from pipeline_ingest_sources limit 20` → `[]` (источников нет вовсе); `ingestion_schedule` содержит singleton `{enabled:true, time_of_day:06:00:00, days_of_week:[1,3,6,7], last_run_at:null}`. D-27 подтверждён косвенно: после 4 due-тиков при нуле источников `last_run_at` не появился. Для разблокировки: добавить источник `platform='youtube'` (включённый), дождаться 15-минутного тика в МСК-день, проверить `materials.status='draft'` + шортлист `pending`, затем повторный прогон не должен двигать курсор.

### 7. Проверка миграции 013 на общей VM

Studio SQL / psql: колонки курсора, `ingestion_schedule`, RLS, seed.

expected: Колонки `last_seen_published_at`/`last_seen_video_id` есть; `ingestion_schedule` существует, RLS=true, политик 0, seed-строки нет.

note: Оператор подтвердил apply 2026-10-18; PostgREST-проба `select * from public.ingestion_schedule limit 5` → `[]`. Колонки `last_seen_published_at`/`last_seen_video_id` подтверждены PostgREST-пробой `select id,last_seen_published_at,last_seen_video_id from pipeline_ingest_sources` → `[]` (колонки существуют, таблица пуста). RLS/политики подтверждены оператором в Studio SQL 2026-10-18: RLS=true, политик 0, seed-строк 0.
result: pass

### 8. Визуальная проверка блока «Автоматический сбор»

`/admin/pipeline`, desktop и узкая ширина.

expected: Блок читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» визуально очевиден.
result: pass
note: Проверено в живом SPA (`127.0.0.1:5173`, `VITE_USE_MOCKS=false`, backend на актуальном коде). Заголовки идут в порядке «Источники ингеста» → «Автоматический сбор», YAML-редактор ниже блока сбора. Горизонтального переполнения нет ни на 1440 px (`docScrollW=1425` при `vw=1440`), ни на 390 px (`docScrollW=390`); секция сбора 358 px при вьюпорте 390 px, дни недели переносятся на вторую строку (`вс`), контролы 44 px. Единственный `192>160` — это `truncate` на имени пользователя в шапке (by design). Сначала страница показывала «Не удалось загрузить настройки сбора» — причина оказалась не в коде, а в устаревшем uvicorn-процессе: `GET /admin/ingestion-schedule` отдавал 404; после перезапуска бэкенда эндпоинт отвечает 200 и блок заполняется (Время 06:00, все дни включены).

## Summary

total: 8
passed: 7
issues: 0
pending: 0
skipped: 1
blocked: 0

## Deferred Follow-Ups

- test: 6
  idea: "Живой прогон на реальном включённом источнике (YouTube Atom + Supabase): новые видео как materials.status='draft' и строки шортлиста 'pending', без публикаций/captions/LLM, повторный прогон не двигает курсор; плюс переход из нуля источников (D-27)"
  deferred_at: 2026-10-18

## Gaps

- gap_id: G-24-3
  truth: "Зависший прогон убивается по лимиту 1800 с; `last_run_at` не штампуется, следующий тик снова due и продолжает с того же курсора"
  status: resolved
  resolved_by: 24-07-PLAN.md
  resolved_at: 2026-10-18
  reason: "Наблюдение в WSL2/systemd 255: `RuntimeMaxSec=` игнорируется для `Type=oneshot`, юнит не убивается. D-23 и T-24-32 не реализованы."
  severity: blocker
  test: 3
  root_cause: "`RuntimeMaxSec=` применим только к юнитам, которые переходят в состояние running; `Type=oneshot` всё время в activating, поэтому systemd пишет «RuntimeMaxSec= has no effect in combination with Type=oneshot. Ignoring.» и не применяет лимит. Для oneshot нужен `TimeoutStartSec=`."
  artifacts:
    - path: "deploy/systemd/digest-ingest.service"
      issue: "RuntimeMaxSec=1800 на Type=oneshot — systemd игнорирует; зависший прогон держит flock вечно, последующие тики выходят 75 и считаются успехом"
    - path: "tests/unit/test_phase24_systemd_units.py"
      issue: "text-контракт пинит токен RuntimeMaxSec=1800, то есть защищает сломанную конфигурацию"
    - path: "docs/agents/local-platform-runbook.md"
      issue: "§4k/§5e описывают RuntimeMaxSec как рабочий лимит"
    - path: ".planning/phases/24-scheduled-ingestion/24-SECURITY.md"
      issue: "T-24-32 митигация ссылается на неработающий RuntimeMaxSec"
  missing:
    - "Заменить RuntimeMaxSec=1800 на TimeoutStartSec=1800 в oneshot-юните"
    - "Первый RED-тест: text-контракт требует TimeoutStartSec=1800 и отсутствие RuntimeMaxSec"
    - "Обновить §4k/§5e и T-24-32 под фактический механизм"
  debug_session: .planning/debug/phase24-runtimemax-oneshot.md
- gap_id: G-24-4
  truth: "Alert различает exit 1 («partial failure») и exit 2 («no source could be read»)"
  status: resolved
  resolved_by: 24-08-PLAN.md
  resolved_at: 2026-10-18
  reason: "Наблюдение: оба кода дают «unexpected failure (exit exited)»; alert читает `MONITOR_EXIT_CODE=exited`, а числовой код лежит в `MONITOR_EXIT_STATUS`. T-24-34 не реализован."
  severity: major
  test: 4
  root_cause: "В systemd 255 `MONITOR_EXIT_CODE` — квалификатор (`exited`/`killed`), а число лежит в `MONITOR_EXIT_STATUS`; `EXIT_CODE`/`EXIT_STATUS` не выставляются. Юнит читает `${MONITOR_EXIT_CODE:-...}`, поэтому `case` всегда уходит в ветку `*)`."
  artifacts:
    - path: "deploy/systemd/digest-ingest-alert.service"
      issue: "читает MONITOR_EXIT_CODE вместо MONITOR_EXIT_STATUS"
    - path: "tests/unit/test_phase24_systemd_units.py"
      issue: "text-контракт пинит именно `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}`, закрепляя дефект"
    - path: ".planning/phases/24-scheduled-ingestion/24-SECURITY.md"
      issue: "T-24-34 заявлен как закрытый"
  missing:
    - "Читать числовой код из MONITOR_EXIT_STATUS (фолбэк EXIT_STATUS)"
    - "Первый RED-тест: контракт требует MONITOR_EXIT_STATUS и запрещает старую подстановку"
    - "Проверка на живом systemd: exit 1 и exit 2 дают разные строки"
  debug_session: .planning/debug/phase24-alert-exit-code.md
