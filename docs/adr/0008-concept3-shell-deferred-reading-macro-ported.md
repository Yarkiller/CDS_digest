# Shell-макроструктуры Concept 3 откладываются; reading-макро переносится

**Статус:** superseded — заменён [`ADR-0009 «Concept 2 — канон UI: тёмная и светлая тема, без геймификации»`](0009-concept2-canon-dark-light-no-gamification.md). Отсрочка shell-слоя отменена: канон Concept 2 переносит шапку вместе с остальным UI, а reading-макро Concept 3 в этом каноне отсутствует. Решение сохранено как история.

Digest CDS воспроизводит из `design-frontend/styles/layout.css` макроструктуру чтения — `.split-layout--reading`, `.toc*` и `.toc-mobile*`. Шапка приложения и футер остаются production-специфичными: это зафиксированное отклонение, а не незакрытый дрейф.

## Контекст

ADR-0006 требует воспроизводить макроструктуры прототипа, а не изобретать визуальный слой заново. К 2026-10-18 перенесены токены (99 из 99), типографика, editorial-компоненты (`.issue-cover`, `.editorial-box`, `.pull-quote`, `.reading-progress`, `.archive-grid`) и слой `.prose`.

Неперенесёнными оставались два блока `layout.css`:

- **reading-макро** (`layout.css:205-300`) — `.split-layout--reading`, `.toc`, `.toc__list`, `.toc__link`, `.toc-mobile`, `.toc-mobile__summary`, `.toc-mobile__list`;
- **shell** (`layout.css:6-174` и `349-372`) — `.app-shell`, `.header`, `.header__inner`, `.logo`, `.nav`, `.nav-toggle`, `.header__search`, `.header__user`, `.user-name`, `.site-footer`.

Reading-макро не конфликтует ни с одним принятым контрактом: `design.md` прямо разрешает «Reading pages may use a sticky TOC only when the viewport supports it», а production уже рисовал содержание как sticky-колонку на десктопе и `<details>` на мобиле — то есть ровно паттерн прототипа, но на Tailwind arbitrary-классах (`sticky top-24 hidden max-h-[70vh] w-56 … lg:block`).

Прямой перенос shell-слоя ломает три принятых контракта в `tests/web-app.spec.js:596-641`:

1. `.user-name { display: none }` до `60rem` против требования, чтобы `shell-identity` был виден на 390px и содержал «Мария Сидорова» (`tests/web-app.spec.js:611-612`).
2. `.nav { display: none }` с открытием через `.nav-toggle` (бургер) против требования, чтобы `navigation «Основная навигация»` была видима на 390px (`tests/web-app.spec.js:609`); production сейчас переносит навигацию во вторую строку, а не прячет её.
3. Прототипный поиск — кнопка `.search-pill`, открывающая `<dialog>`, против production-`SearchPill`, который даёт inline-`searchbox`; тесты требуют его видимым на 390px (`tests/web-app.spec.js:610`) и не шире 320px на узком телефоне (`tests/web-app.spec.js:632-635`).

`.site-footer` в production отсутствует вовсе, а его содержимое (`site-footer__statement` и meta-ссылки) продуктово не определено.

Оба теста пишут скриншоты в `docs/digest-cds/responsive-evidence/`, поэтому любое изменение шапки перезаписывает evidence-набор, требования к которому описаны в `docs/digest-cds/responsive-evidence/README.md`.

## Решение

1. **Reading-макро переносится.** Правила `layout.css:205-300` воспроизводятся в `web/src/index.css`; `MaterialPage.jsx` собирается как `.split-layout--reading` с `nav.toc` во втором треке и `details.toc-mobile` во главе колонки чтения. Брейкпоинт rail — `80rem`, как в прототипе.
2. **Ширина rail берётся из канонного токена.** `layout.css` сайзит rail через `var(--toc-width)` (`tokens.css`: `15rem`), который production уже несёт в `@theme static`. Новый токен не вводится.
3. **Shell-макроструктуры и `.site-footer` не переносятся** в рамках этой работы. `AppShell.jsx` остаётся на utility-классах Tailwind. Отклонение зафиксировано здесь, а не обнаруживается на ревью.
4. **Отклонение снимается только новым ADR**, который одновременно: (а) принимает бургер-навигацию и скрытие имени на мобиле либо явно сохраняет production-поведение; (б) выбирает модель поиска (inline-`searchbox` против `.search-pill` + `<dialog>`); (в) утверждает содержимое `.site-footer`; (г) обновляет `tests/web-app.spec.js:596-641` и перегенерирует responsive evidence.
5. **Частично «догонять» шапку запрещено.** Перенос половины shell-слоя даёт смешение двух визуальных языков в одном экране — ровно тот дрейф, против которого ADR-0006 ввёл автоматические стражи.

## Considered Options

- (A) **Перенести reading-макро, shell отложить отдельным ADR** — выбрано: закрывает требование `design.md` о sticky TOC, не ломая ни одного принятого контракта.
- (B) Перенести shell полностью по прототипу и переписать responsive-контракты — отложено: меняет три принятых UX-решения (видимость имени, всегда видимая навигация, inline-поиск) без продуктового решения и перезаписывает evidence.
- (C) Остановиться и не переносить ничего — отвергнуто: reading-макро бесконфликтно, а отказ от него оставил бы Long Document на arbitrary-классах вне канона.
- (D) Завести токен `--rail-toc` как alias `--toc-width` — отвергнуто: в каноне такого токена нет, `layout.css` обращается к `--toc-width` напрямую; изобретение токена нарушило бы пункт 3 ADR-0006 о полном parity.

## Consequences

- Содержание материала рисуется токенами дизайн-системы: ширина rail `--toc-width`, отступ rail от шапки `calc(var(--header-height) + var(--space-6))`, ссылка rail не ниже `--touch-target`, на мобиле вместо rail — disclosure.
- Дрейф reading-макро обнаруживается до ревью: `tests/unit/test_reading_layout.js` сравнивает объявления production с `layout.css` и падает на расхождении или на пропаже декларации.
- Поведение на 390px не изменилось: disclosure раскрывается по тапу на «Содержание», горизонтального переполнения нет.
- Контракты `tests/web-app.spec.js:4-33`, проверяющие видимость содержания на дефолтном вьюпорте 1280x720, остались зелёными: `80rem` = 1280px, то есть брейкпоинт прототипа совпадает с дефолтным вьюпортом Playwright впритык. Любое уменьшение `use.viewport` в `playwright.config.js` потребует явно задать ширину вьюпорта в этих тестах.
- Shell остаётся вне канона осознанно. Задачи «привести шапку к Concept 3» больше не должны открываться без ADR из пункта 4.
- Когда shell-ADR будет принят, `--toc-width` продолжит работать: rail сайзится токеном, а не шириной шапки, поэтому перенос `.header` не затронет reading-макро.

## Verification

```bash
node --test tests/unit/test_reading_layout.js   # parity reading-макро
npm run test:web                                # контракты reader + responsive evidence
npm run build --prefix web                      # Tailwind v4 принимает новые компоненты
```

**References:** [`design-frontend/styles/layout.css`](../../design-frontend/styles/layout.css), [`design-frontend/styles/tokens.css`](../../design-frontend/styles/tokens.css), [`design-frontend/pages/material.html`](../../design-frontend/pages/material.html), [`design-frontend/design.md`](../../design-frontend/design.md), [`web/src/index.css`](../../web/src/index.css), [`web/src/pages/MaterialPage.jsx`](../../web/src/pages/MaterialPage.jsx), [`tests/unit/test_reading_layout.js`](../../tests/unit/test_reading_layout.js), [`tests/web-app.spec.js`](../../tests/web-app.spec.js), [`docs/digest-cds/responsive-evidence/README.md`](../digest-cds/responsive-evidence/README.md), [`ADR-0006`](0006-concept3-editorial-ui-canon.md).
