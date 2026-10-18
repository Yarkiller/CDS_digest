# supabase-integration

Postgres/Supabase-адаптер Digest CDS: миграции схемы и (далее) реализации портов из `backend`.

Инстанс: self-hosted Supabase ([ADR-0004](../docs/adr/0004-self-hosted-supabase-on-vm.md)), базовый URL конфигурируется (например `https://knowledge-db.ru/`).

## Применение миграций

В Supabase Studio → **SQL Editor** выполнить:

[`migrations/001_initial_schema.sql`](migrations/001_initial_schema.sql)

Unit-тесты схему на живой БД не применяют; контракт файла проверяется в `tests/unit/test_schema_migration_contract.py`.

## Схема `public` (применена на инстансе)

Extensions: `vector`, `pg_trgm`.  
Embedding: `knowledge_chunks.embedding vector(1024)` (+ generated `content_tsv` для FTS).

**RLS включён на всех 18 таблицах** (проверено в Studio после применения миграции).

| Слой | Таблицы |
|------|---------|
| Auth / профиль | `profiles` (FK → `auth.users`) |
| Ingestion | `ingestion_sources`, `ingestion_jobs`, `source_texts` |
| Publication | `materials`, `material_tags`, `material_relations` |
| Digest | `digest_issues`, `digest_issue_items`, `digest_shortlist_batches`, `digest_shortlist_items` |
| Knowledge | `knowledge_chunks` |
| Voting / разбор | `voting_cycles`, `topics`, `topic_materials`, `votes`, `razbors` |
| Activity | `activity_events` |

Базовые policies в миграции (для `authenticated`):

- `materials` / `knowledge_chunks` — SELECT только `ready`
- `digest_issues` / `digest_issue_items` — SELECT
- `votes` — SELECT/INSERT/UPDATE своих строк
- `profiles` — SELECT своего профиля

Запись pipeline (ingestion, embed, shortlist) — через `service_role` (обходит RLS). Остальные таблицы с RLS без открытых anon-политик по умолчанию закрыты для anon.

## Проверка live

После прогона SQL: Table Editor должен показать перечисленные таблицы; PostgREST OpenAPI (`/rest/v1/`) отдаёт их definitions. Старая тестовая `instruments` к схеме Digest CDS не относится.
