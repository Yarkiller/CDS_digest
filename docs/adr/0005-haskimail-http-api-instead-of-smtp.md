# Haskimail HTTP API вместо SMTP-реле

Дайджест доставляется через **HTTP API Haskimail** (`POST https://api.haskimail.ru/email`), а не через корпоративный SMTP-релей. Транспорт реализован официальным SDK `haskimail` (`ServerClient`) в адаптере `backend/src/backend/infrastructure/haskimail_mailer.py`; `MAILER=haskimail` выбирает его в composition root (`backend/src/backend/composition/mailer_factory.py`).

**Статус:** принято. Адаптер `SmtpMailer` остаётся рабочим (`MAILER=smtp`, ADR-0003 не отменяется) — смена транспорта не затрагивает domain, use case и HTTP-край. Порт `application.ports.mailer.Mailer` не менялся.

**Considered Options:**

- (A) **HTTP API Haskimail через официальный SDK** — выбрано.
- (B) Корпоративный SMTP-релей через `smtplib` (`MAILER=smtp`) — оставлено как альтернатива.
- (C) Прямые HTTP-запросы к API через `httpx`/`requests` без SDK.
- (D) Платные managed-рассылки (SendGrid/Postmark и аналоги) — недоступны в контуре.

**Почему не SMTP (B).** Живой smoke-тест Фазы 21 показал: дайджест публикуется корректно, но письмо не уходит — корпоративный релей в целевом окружении не настроен и недоступен для выдачи учётных данных. SMTP остаётся кодом-веткой, но дефолтным транспортом для поставки быть не может.

**Почему SDK (A), а не самописный HTTP-клиент (C).** SDK владеет конвертом запроса, заголовком авторизации `X-Haskimail-Server-Token` (не `Authorization: Bearer`) и типизированной иерархией ошибок (`InvalidAPIKeyError`, `RateLimitExceededError`, `InactiveRecipientsError`, `ServiceUnavailableError`, …). Это позволяет адаптеру маппить исходы на контракт порта, а не воспроизводить спецификацию API у себя. Транспортная библиотека импортируется **только** в `infrastructure`; в `domain`/`application` запрещена (проверяется тестом).

**Consequences.**

- Письма уходят только при настроенных `HASKIMAIL_API_KEY` и `HASKIMAIL_FROM` — иначе `ConfigurationError`, без тихого фолбэка на `StubMailer` (D-16). `HASKIMAIL_FROM` должен быть на домене, верифицированном в кабинете Haskimail.
- **Тестовый период:** API принимает обратный адрес только из списка подтверждённых либо на подтверждённом домене. Непроверенный отправитель даёт `422 / ErrorCode 400`, а адаптер честно возвращает `failed` — это не дефект доставки, а невыполненное DNS-условие (DKIM/SPF или подтверждение адреса).
- `HASKIMAIL_API_URL` — **базовый** адрес (`https://api.haskimail.ru`), SDK сам добавляет `/email`. Полный путь `.../v1/messages/send` в env — ошибка. Допускается только `https://` (токен не должен идти по plaintext).
- Контракт доставки сохранён: одно письмо на получателя с единственным `To` (D-05), честный статус `sent`/`partial`/`failed` (D-07), остановка после 3 подряд неудач со сбросом серии на успехе (D-08), ошибки SDK считаются по получателю и не превращают опубликованный дайджест в 500 (MAIL-04), токен не читается из окружения внутри адаптера и не попадает в логи (MAIL-05).
- Сетевые сбои `requests` приходят как `OSError` и трактуются как одна неудача получателя — цикл продолжается.
- Появляется внешняя зависимость `haskimail` (и транзитивно `requests`) в `backend`; вендорить её не требуется.
- Отправка синхронная, как и в SMTP-адаптере; таймаут запроса — 30 с, не конфигурируется из env, чтобы оператор не выставил значение, превышающее бюджет запроса публикации.

**Configuration.**

```dotenv
MAILER=haskimail
HASKIMAIL_API_KEY=<server token>
HASKIMAIL_API_URL=https://api.haskimail.ru
HASKIMAIL_FROM=digest@knowledge-db.ru
HASKIMAIL_FROM_NAME=Digest CDS
HASKIMAIL_MESSAGE_STREAM=            # пусто = стрим по умолчанию
```

**References:** [`docs/adr/0003-email-domain-restriction.md`](0003-email-domain-restriction.md), `backend/src/backend/infrastructure/haskimail_mailer.py`, `backend/src/backend/composition/mailer_factory.py`, `tests/unit/test_haskimail_mailer.py`, `.planning/phases/21-mail-01-live-smtp-digest-delivery/`.
