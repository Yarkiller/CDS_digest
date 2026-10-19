# Concept 3 Editorial UI — канон дизайн-системы

**Статус:** принято. Уточнён [`ADR-0008 «Shell-макроструктуры Concept 3 откладываются; reading-макро переносится»`](0008-concept3-shell-deferred-reading-macro-ported.md): токены, типографика, editorial-компоненты, `.prose` и reading-макро перенесены, а `.header`/`.nav`/`.header__search`/`.site-footer` отложены отдельным решением.

`design-frontend/` является единственным источником истины для пользовательского интерфейса Digest CDS. Production SPA (`web/`) обязан воспроизводить его токены, типографику, макроструктуры и состояния экранов, а не изобретать визуальный слой заново и не смешивать его с другими концептами.

Решение закрывает расхождение между двумя спецификациями прототипа и фиксирует механику, которая не даёт production снова разойтись с дизайном.

## Контекст

В прототипе два документа описывают типографику по-разному:

- `design-frontend/UI-SPEC_3.md` (принцип P4 и раздел 7) требует «Serif для заголовков»;
- `design-frontend/design.md` и `design-frontend/styles/tokens.css` задают `--font-serif: var(--font-display)`, то есть «serif» — это **Bricolage Grotesque**, гротеск; `styles/typography.css` реализует ровно это: `.text-serif { font-family: var(--font-display) }`.

На 2026-10-19 production содержал 12 токенов из 99 и четыре недостающих editorial-компонента, поэтому часть экрана рисовалась значениями, которых нет в дизайн-системе.

## Решение

1. **Канон — `design.md`.** Документ помечен как *locked design system*, тогда как `UI-SPEC_3.md` — *concept draft (2026-08-23)*. При расхождении приоритет у `design.md`, затем у фактических `styles/*.css`, и только затем у прозы `UI-SPEC_3.md`.
2. **«Serif» — это display-шрифт.** Заголовки набираются Bricolage Grotesque (`--font-display`); отдельный serif-шрифт в проект не вводится. Термин «serif» в `UI-SPEC_3.md` читается как «display-шрифт заголовков».
3. **Полный parity токенов.** Все 99 токенов `styles/tokens.css` переносятся в `@theme static` в `web/src/index.css` байт-в-байт, включая шкалы типографики, отступов, радиусов, теней, контейнеров, движения и z-index — не только цвета.
4. **`@theme static`, а не `@theme`.** Tailwind v4 по умолчанию исключает из вывода неиспользуемые переменные. Токены — контракт дизайн-системы, поэтому они обязаны присутствовать в `:root` в рантайме независимо от того, потребил ли их уже какой-нибудь utility-класс.
5. **Автоматический страж parity.** `tests/unit/test_design_tokens.js` парсит оба файла и падает, если токен отсутствует в production или его значение дрейфовало. Значение токена нельзя править в `web/` в обход прототипа.

## Considered Options

- (A) **`design.md` + фактические CSS-токены как канон, полный parity под тестом** — выбрано.
- (B) `UI-SPEC_3.md` как канон и введение настоящего serif-шрифта — отвергнуто: противоречит *locked design system* и удваивает шрифтовой набор.
- (C) Переносить только цвета и нужные по месту значения — отвергнуто: именно этот подход привёл к 12 из 99 токенов и к визуальному дрейфу.
- (D) Держать токены в отдельном CSS-файле вместо `@theme` — отвергнуто: лишает проект utility-классов Tailwind v4 и создаёт второй источник правды.

## Consequences

- Расхождение спецификаций больше не требует обсуждения в каждой задаче: приоритет документов зафиксирован.
- Правка токена в `web/src/index.css` без правки `design-frontend/styles/tokens.css` ломает тест — дрейф обнаруживается до ревью.
- Если прототип добавит или удалит токен, тест на количество (99) упадёт и потребует осознанного обновления контракта, а не тихого расхождения.
- Паттерны, которые плохо выражаются utility-классами (`mark`, `.rule`, `.prose p`), следует держать в `@layer base` как CSS, а не пытаться выразить токеном.
- Информационная архитектура меняться не должна: маршруты `UI-SPEC_3.md` §9 уже присутствуют в `web/src/App.jsx`. Переход на Concept 3 — это визуальный слой и состояния экранов, а не пересборка роутинга.

## Verification

```bash
node --test tests/unit/test_design_tokens.js   # parity токенов
npm run build --prefix web                     # Tailwind v4 принимает @theme static
npm run test:web                               # отсутствие регрессий
```

**References:** [`design-frontend/design.md`](../../design-frontend/design.md), [`design-frontend/UI-SPEC_3.md`](../../design-frontend/UI-SPEC_3.md), [`design-frontend/styles/tokens.css`](../../design-frontend/styles/tokens.css), [`web/src/index.css`](../../web/src/index.css), [`tests/unit/test_design_tokens.js`](../../tests/unit/test_design_tokens.js), [`docs/digest-cds/backlog_UI.md`](../digest-cds/backlog_UI.md).
