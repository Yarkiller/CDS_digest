---
status: complete
phase: 21-mail-01-live-smtp-digest-delivery
source: [21-VERIFICATION.md]
started: 2026-10-16T15:30:02Z
updated: 2026-10-18T10:40:00+03:00
---

## Current Test

[testing complete]

## Tests

### 1. Подтверждение запретов: честный текст без заявления о доставке всей организации (сообщение / API / баннер SPA)
expected: Текст из двух предложений формируется на сервере: «Доставлено N из M» / «Письма не доставлены» / «Получателей нет (0 из 0)» / строка про stub; нигде нет формулировки вида «всей организации».
result: pass

### 2. Подтверждение запретов: локализация ошибки почты (D-88) + нет 5xx после публикации + сохранённый тест-ловушка
expected: Ошибка почты после публикации по-прежнему возвращает HTTP 200 (успех), а выпуск сохранён; тест `test_send_audit_failure_after_publish_still_returns_success` присутствует и зелёный; `test_send_mail_failure_after_publish_still_returns_success` зелёный.
result: pass

### 3. Подтверждение запретов: приватность — одно письмо на получателя, без массового Bcc, без утечки smtplib, без os.environ в адаптере
expected: `SmtpMailer` ставит один `To` на каждый `EmailMessage` и не использует Bcc; `smtplib` импортируется только в infrastructure; в `smtp_mailer.py` нет `os.environ`/`getenv`.
result: pass

### 4. Подтверждение запретов: fail-fast по D-16, без молчаливого отката на stub, без update_delivery, без регистрации через Mailer, StubMailer сохранён
expected: `resolve_mailer` бросает `ConfigurationError` при неполных или выходящих за диапазон `SMTP_*`; неверно настроенный режим smtp никогда не возвращает `StubMailer`; метода `DigestPublisher.update_delivery` нет; под `web/src` нет `Mailer`/`send_digest`; класс `StubMailer` цел.
result: pass

### 5. Подтверждение запрета: runbook не заявляет, что доказательство доставки через корпоративный relay (критерий 4 фазы 20) получено
expected: Разделы §4.1.3 и §4e runbook указывают, что живой smoke через корпоративный relay — унаследованный операционный пробел (D-15); линия `GOTRUE_SMTP_*` остаётся отдельной от `SMTP_*` дайджеста.
result: pass

### 6. Живой smoke доставки дайджеста через Haskimail HTTP API (ADR-0005)
expected: При MAILER=haskimail с валидным HASKIMAIL_API_KEY и верифицированным HASKIMAIL_FROM один реальный недельный дайджест уходит через https://api.haskimail.ru/email; API принимает каждое письмо (MessageID), recipient_count=M и delivered_count=N совпадают с фактически отправленным набором; при отказе API статус честно partial/failed.
result: pass
note: "2026-10-18: MAILER подтвердил учётку, рассылка работает — пользователь подтвердил pass."

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]

## Deferred Follow-Ups

[resolved 2026-10-18 — Test 6 passed after MAILER account verification]
