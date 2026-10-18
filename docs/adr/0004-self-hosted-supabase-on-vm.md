# Self-hosted Supabase на отдельной VM

База данных и работа с данными — **self-hosted (локальный) Supabase**, развёрнутый через Docker Compose на отдельном виртуальном сервере. Supabase предоставляет PostgreSQL с расширением **pgvector** (векторный + полнотекстовый поиск), а также встроенные Auth/Storage/REST. Managed Supabase Cloud и managed PostgreSQL Cloud.ru не используем.

Инстанс доступен по базовому адресу `https://knowledge-db.ru/`. Адрес и ключи — **конфигурируемые** (env/секреты, без хардкода в коде); в будущем адрес может измениться без правок бизнес-логики. Доступ к Supabase инкапсулирован в модуле-адаптере `supabase-integration` (см. `.cursor/rules/architecture.mdc`): domain/application работают только через порт репозитория, смена адреса или провайдера = замена одного адаптера.

**Considered Options:** (A) self-hosted Supabase на отдельной VM (Docker Compose); (B) чистый PostgreSQL + pgvector в Docker Compose на VM приложения; (C) managed PostgreSQL Cloud.ru; (D) managed Supabase Cloud.

**Consequences:** получаем PostgreSQL+pgvector плюс готовые Auth/Storage/REST в одном контуре и без внешних managed-сервисов; ответственность за бэкапы, обновления, безопасность и отказоустойчивость Supabase лежит на команде; БД живёт на отдельном сервере от приложения — нужен надёжный сетевой доступ и защита эндпоинта; базовый URL и сервисные ключи держим в конфиге/секретах, чтобы смена адреса не затрагивала код.

## Initial schema (applied)

Каноническая DDL: [`supabase-integration/migrations/001_initial_schema.sql`](../../supabase-integration/migrations/001_initial_schema.sql). Описание слоёв и таблиц: [`supabase-integration/README.md`](../../supabase-integration/README.md).

На инстансе `knowledge-db.ru` схема применена через Studio SQL Editor. **RLS включён на всех 18 таблицах** `public` из миграции; базовые policies для `authenticated` — в том же SQL-файле.

