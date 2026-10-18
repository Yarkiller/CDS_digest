# Digest CDS — Spec v1

**Status:** accepted (grill-with-docs, 2026-08-23)  
**Инициатор:** CDS, СВА Сбербанка  
**Аудитория:** Data Analyst, Data Scientist и рядовые сотрудники СВА

## Problem

Сотрудники СВА тратят много времени на поиск и отбор релевантных материалов по новым технологиям. Нет единого источника знаний и механизма голосования за темы для совместного разбора.

## Solution

Веб-сервис на Cloud.ru для сбора ссылок на внешние видео и текстовые источники, получения исходного текста без публикации и хранения видео/аудио, подготовки агентом проверенных статей с дополнительным поиском и анализом, еженедельного email-дайджеста, голосования за темы разборов, базы знаний с векторным поиском и подготовки .ipynb по победившим темам.

## Users & Roles

| Роль | Приоритет | v1 capabilities |
|---|---|---|
| **Data Analyst** | 1 | Поиск по SQL/BI/DQ, голосование, база знаний |
| **Data Scientist** | 1 | Поиск по ML, голосование, создание .ipynb для разборов |
| **Рядовой сотрудник СВА** | 2 | Дайджест, голосование, поиск в базе знаний |
| **Админ** (CDS/делегат) | — | YAML-конфиги, утверждение дайджеста, модерация |

Регистрация: email + пароль. Разрешённые домены: `@sberbank.ru`, `@omega.sbrf.ru` (ADR-0003).

## Core Flows

### 1. Content ingestion

1. **YAML-источники** (каналы, плейлисты, ключевые слова) + **ручное добавление URL или текста** админом/экспертом.
2. **YouTube Data API v3** или другой адаптер — получение списка новых внешних источников и их метаданных; видео остаётся внешним ресурсом.
3. Получение субтитров/текста или транскрибация через FoundryModels (Cloud.ru) в рамках обработки; видео и аудио не сохраняются в системе как материал.
4. Агент анализирует исходный текст, выполняет дополнительный поиск, проверяет факты и готовит самостоятельную русскоязычную **статью-материал**: практический гайд или описание нового подхода.
5. Публикационный quality gate проверяет статью, provenance и ссылки на связанные статьи; затем создаётся **карточка знаний** (.md) из статьи, а не из необработанного транскрипта.

### Контентная модель и связи

- **Исходный текст** — промежуточный результат транскрибации внешнего видео либо импортированный текст.
- **Материал** — только самостоятельная статья, подготовленная агентом на основе исходного текста, дополнительного поиска и анализа. Допустимые основные формы: практический гайд по установке/использованию технологии или статья о новом подходе.
- **Источник** — внешняя ссылка и метаданные происхождения; источник не превращается в хранимый видео-/аудио-артефакт и не встраивается в страницу материала.
- **Карточка знаний** — Markdown-представление опубликованной статьи для поиска. Она не создаётся напрямую из транскрипта.
- **Связи** — первое уместное упоминание сложного термина, подхода или технологии, описанных отдельной статьёй, получает внутреннюю ссылку. Связанные статьи поддерживают обратную ссылку или список related materials.

### 2. Weekly digest

1. **Cron** (еженедельно) запускает CLI: сбор кандидатов за неделю → авто-ранжирование → **shortlist топ-5**.
2. Админ утверждает состав в **веб-UI** (галочки → «Отправить»).
3. Email-рассылка через **корпоративный SMTP Сбера**.
4. Копия дайджеста в архиве на сайте.

UI и статьи — на русском; исходный текст может быть на EN. В статье может быть указана ссылка на внешний источник и его происхождение, но видеоплеер, видеофайл и аудиофайл частью материала не являются.

### 3. Voting & разбор

1. **Непрерывное голосование**: один голос на пользователя за **цикл голосования** (2 недели).
2. Тема может объединять несколько материалов.
3. По закрытии окна — победившая **тема** идёт на **разбор** (встреча раз в 2 недели).
4. Data Scientist готовит **.ipynb**; на сайте — **HTML-рендер** (nbconvert), без исполнения кода.

### 4. Knowledge base search

- Self-hosted Supabase (PostgreSQL + **pgvector**) на отдельной VM (Docker Compose).
- Векторный + полнотекстовый поиск по карточкам знаний на сайте.

### 5. Activity tracking (silent in v1)

Собираем **события активности** без UI:

- Просмотры материалов
- Открытия дайджестов
- Участие в голосованиях
- Поисковые запросы
- Время на странице

Данные для **лидерборда** (ADR-0001) — после v1.

## Architecture

| Component | Choice |
|---|---|
| Hosting | VM Cloud.ru |
| Backend | FastAPI (Python) |
| Frontend | React SPA |
| Database | Self-hosted Supabase (PostgreSQL + pgvector) via Docker Compose on separate VM |
| ML pipeline | FoundryModels API (Cloud.ru) |
| External sources | YouTube Data API v3 / text import; source remains external |
| Scheduler | cron + CLI commands on VM |
| Email | Corporate Sber SMTP |
| .ipynb display | nbconvert → static HTML |
| Config | YAML/JSON in repository |

## MVP Scope

### In v1

- [ ] Content ingestion (YAML + manual URL)
- [ ] Transcription & enrichment via FoundryModels
- [ ] Knowledge cards + vector search
- [ ] Weekly digest (auto-rank top-5 + admin approval UI)
- [ ] Email delivery
- [ ] Web: auth, digest archive, voting, search
- [ ] Bi-weekly разбор workflow + .ipynb HTML render
- [ ] Four roles (employee, Data Analyst, Data Scientist, admin)
- [ ] Silent activity event collection

### After v1

- [ ] Quiz cards (FoundryModels + author review)
- [ ] Public leaderboard (gamification)
- [ ] Leaderboard opt-out
- [ ] Jupyter viewer with cell execution
- [ ] Corporate SSO
- [ ] Extended CDS analytics dashboard

## ADRs

| ID | Decision |
|---|---|
| ADR-0001 | Public leaderboard (implement post-v1) |
| ADR-0002 | Cloud.ru VM + FoundryModels for ML |
| ADR-0003 | Email domains: @sberbank.ru, @omega.sbrf.ru |
| ADR-0004 | Self-hosted Supabase (PostgreSQL + pgvector) via Docker Compose on separate VM |

## Domain glossary

See [`CONTEXT.md`](../../CONTEXT.md) at repo root.

## Open items (for implementation)

- Конкретные модели FoundryModels (transcription, embedding) — уточнить при интеграции.
- YouTube Data API credentials и квоты.
- Параметры SMTP (хост, порт, заявка в Сбер).
- Алгоритм авто-ранжирования (веса: свежесть, просмотры YouTube, теги, LLM-score).

## Success criteria (v1)

1. Новый внешний источник из YAML-конфигурации или ручного импорта проходит транскрибацию/извлечение текста, после чего агент готовит русскоязычную статью с анализом, дополнительными источниками, provenance и ссылками на связанные статьи; видео и аудио в базе не сохраняются как материал.
2. Админ утверждает и отправляет дайджест из топ-5 за < 10 минут.
3. Пользователь СВА находит материал через поиск за < 30 секунд.
4. Голосование за тему и публикация .ipynb разбора работают end-to-end.
