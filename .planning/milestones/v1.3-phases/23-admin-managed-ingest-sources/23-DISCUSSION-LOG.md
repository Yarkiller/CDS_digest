# Phase 23: Admin-managed ingest sources - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-17
**Phase:** 23-admin-managed-ingest-sources
**Areas discussed:** Сохранение источников и guard, Поля источника и тип, Жизненный цикл и пустое состояние

---

## Сохранение источников и guard

| Option | Description | Selected |
|--------|-------------|----------|
| Действия по строке сразу | add/enable-disable/delete сразу идут в API; отдельной кнопки сохранения нет; «несохранённое» — только недописанный id в форме добавления | ✓ |
| Одна кнопка «Сохранить источники» | все правки списка копятся локально и уходят одним PUT; dirty → guard Phase 19 с той же копией | |
| Гибрид | enable/disable и удаление мгновенно, новый источник — через явную форму; guard только на недописанном id | |

**User's choice:** Действия по строке сразу (per-row immediate).
**Notes:** Мотивация — не ставить второй Save-режим рядом с YAML-редактором.

| Option | Description | Selected |
|--------|-------------|----------|
| Ниже YAML-редактора | сначала текущий конфиг, ниже — данные для планировщика | |
| Выше YAML-редактора | источники — главное действие страницы; YAML уходит вниз | ✓ |
| Свёрнутая секция/аккордеон | по умолчанию закрыта, открывается по клику | |

**User's choice:** Выше YAML-редактора.
**Notes:** Источники — то, что будет читать Phase 24, поэтому они наверху.

| Option | Description | Selected |
|--------|-------------|----------|
| Тот же guard | тот же диалог и копия Phase 19; dirty = yamlDirty \|\| pendingSourceId; тормозятся уход со страницы и переключение таба | ✓ |
| Свой диалог/копия | отдельный текст про недобавленный id; второй диалог на странице | |
| Без guard | недописанный id теряется незаметно; ADUX-10 закрыт формально | |

**User's choice:** Тот же guard и то же диалог с копией Phase 19.

---

## Поля источника и тип

| Option | Description | Selected |
|--------|-------------|----------|
| Одно поле id, тип из префикса | UC… → канал, PL… → плейлист; меньше полей, нельзя сохранить несогласованную пару | |
| Явный селектор «Канал/Плейлист» + id | админ выбирает тип, сервер проверяет соответствие; яснее для новичка, новый класс ошибки | ✓ |
| Свободный тип (канал / плейлист / другое) | гибко на будущее, но расширяет scope валидации | |

**User's choice:** Явный селектор «Канал/Плейлист» + id, сервер проверяет соответствие префиксу.

| Option | Description | Selected |
|--------|-------------|----------|
| Необязательная подпись «Название» | nullable-колонка; пусто → в списке только id; авто-названий без Data API нет | ✓ |
| Без подписи | только id и тип; минимальная схема | |
| Обязательная подпись | каждый источник обязан иметь название; больше трения и ещё одна ошибка валидации | |

**User's choice:** Необязательная подпись «Название».

| Option | Description | Selected |
|--------|-------------|----------|
| id (моно) + тип + статус + переключатель + «Удалить» + «Открыть на YouTube» | админ проверяет id до включения; нулевая стоимость, без API | ✓ |
| Минимально | без внешней ссылки; проверка id — на совесть админа | |
| С метаданными | плюс дата добавления / кто добавил; больше колонок, малая ценность для single-operator | |

**User's choice:** Строка с внешней ссылкой на YouTube.

---

## Жизненный цикл и пустое состояние

| Option | Description | Selected |
|--------|-------------|----------|
| Флаг is_enabled + жёсткое удаление | выключенный источник остаётся в списке; удаление безвозвратное отдельной кнопкой | ✓ |
| Мягкое удаление/архив | запись остаётся с is_deleted, можно восстановить; усложняет API и запросы планировщика | |
| Удаление только выключенных | сначала выключи, потом удали; лишний обязательный шаг | |

**User's choice:** `is_enabled` + жёсткое удаление.

| Option | Description | Selected |
|--------|-------------|----------|
| Разрешено + видимая подсказка | можно остаться с нулём, но секция честно сообщает, что новые видео собираться не будут | ✓ |
| Разрешено молча | никаких предупреждений | |
| Блокировать последний включённый | нельзя остаться с нулём; мешает штатной паузе | |

**User's choice:** Ноль включённых разрешён с честной подсказкой.

| Option | Description | Selected |
|--------|-------------|----------|
| Подсказка у формы + раскрывающееся «Где взять id?» | шаги для канала (UC…: Studio → Настройки → Канал → Расширенные) и плейлиста (PL…: `?list=` в адресе) | ✓ |
| Всегда видимый полный текст | ничего не спрятано, но форма длинная и шумная | |
| Отдельный блок помощи внизу | страница компактнее, но инструкцию легко пропустить в момент ошибки | |

**User's choice:** Inline-подсказка + раскрывающийся блок «Где взять id?».

---

## Free-text input during the lifecycle area

**User:** «Планировщик должен мониторить канал по ID и если появилось новое видео запустить его обработку. Кроме этого должна быть возможность добавить одноразовую обработку конкретного видео без добавления в планировщик.»

**Handling:**
- Monitoring a channel by id and auto-processing new videos → **Phase 24** (`ING-02`/`ING-05`/`ING-06`/`ING-07`). Phase 23 only stores the enabled list.
- One-off ingest of a single video → recorded as a **deferred idea** (see below). It is a new capability and `ING-01` (ingestion HTTP API) is out of scope for v1.3.
- **User's follow-up decision:** «зафиксировать разовый ingest как deferred-идею».

---

## Claude's Discretion

The user did not select the "validation strictness and duplicates" area, so the following are Claude's calls, recorded as D-14/D-15/D-19 in CONTEXT.md:

- Strict canonical-id patterns: channel `^UC[A-Za-z0-9_-]{22}$`, playlist `^PL[A-Za-z0-9_-]{32}$`; anything else → structured 400, zero writes.
- Duplicate `(kind, source_id)` → same 400 envelope, `path: "source_id"`; use-case pre-check so the unique constraint never surfaces as a 503.
- Reject row keeps the `{path, message}` shape with no `line`.

Also Claude's discretion: row-level request format (D-18), whether to extract or duplicate the error-row helper (D-19), and the router module split.

## Deferred Ideas

- **One-off ingest of a single video from the admin UI** — new capability, needs an HTTP trigger; blocked by the v1.3 out-of-scope entry for `ING-01`. Candidate backlog item for its own phase.
- **Inline label editing** for a saved source — label ships creation-only this phase.
- **Soft delete / restore** of a source — hard delete ships instead.
- **Automatic source titles / channel metadata** — needs YouTube Data API v3, rejected (ADR-0002 contour isolation).
- **Per-source statistics** (last ingested, video count, last error) — belongs to the scheduler's run history in Phase 24 or later.

## Notable codebase finding raised during the discussion

`supabase-integration/migrations/001_initial_schema.sql` already defines a table named **`ingestion_sources`**, but it models *fetched content items* (`external_id`, `canonical_url`, `title`, `published_at`, `view_count`, `status`) and is the FK target of `materials.source_id`, `ingestion_jobs` and `source_texts`. It therefore cannot be reused for admin-managed subscriptions; the new table is `public.pipeline_ingest_sources` in migration `012` (CONTEXT D-16).
