# Concept 2 — канон UI: тёмная и светлая тема, без геймификации

**Статус:** принято. Заменяет [`ADR-0006 «Concept 3 Editorial UI — канон дизайн-системы»`](0006-concept3-editorial-ui-canon.md) и [`ADR-0008 «Shell-макроструктуры Concept 3 откладываются»`](0008-concept3-shell-deferred-reading-macro-ported.md) в части выбора визуального канона. [`ADR-0007 «Отказ от геймификации интерфейса»`](0007-drop-gamification-supersedes-0001.md) **остаётся в силе**.

Каноном пользовательского интерфейса Digest CDS становится **Concept 2** — [`design-frontend/UI-SPEC_2.md`](../../design-frontend/UI-SPEC_2.md) и соответствующие `design-frontend/styles/*.css`: тёмная тема по умолчанию, светлая через `[data-theme="light"]`, Manrope, violet + cyan. Шапка и оболочка приложения переносятся в production (в отличие от ADR-0008). Геймификация, лидерборд и игра в карточки знаний в текущий релиз не входят; их UI-вариант документируется для следующей версии.

## Контекст

После тега `v1.3` команда реализовала Concept 2: `497c613` (тёмные токены), `17323b9` (геймификация в shell и лидерборд), `0737115` (Concept 2 в `design-frontend/`), merge `46e9a02`, финал `d3ada20`. Объём — 43 файла и +1045/−367 в `web/src`; прототип получил `UI-SPEC_2.md`, а `UI-SPEC_3.md` и `design.md` были удалены.

Затем `706d885` откатил `main` на срез `v1.3`: Concept 2 ушёл из релиза вместе с `.github/workflows/ci.yml` и `deploy.yml`, но сохранился тегом `backup/main-concept2-mix-20261019` (= `d3ada20`, включая фикс пустого экрана). Решение о переходе на Concept 2 не было записано ни в один ADR — оно жило только в коммитах.

Дальше направление развернулось документально, а не продуктово: ADR-0006 объявил каноном Concept 3 и удалил Concept 2 из обсуждения, ADR-0007 запретил геймификацию, ADR-0008 отложил shell. В результате в `web/src` перенесли только токены, типографику, четыре editorial-компонента и reading-макро (7 файлов, +588/−60, почти всё в `index.css`), а экраны и шапка остались визуально на `v1.3`. Продукт так и не сменил дизайн, хотя работы было много.

Причина дрейфа одна и она процессная: **смена концепта была зафиксирована кодом, но не решением**, поэтому каждый следующий шаг мог честно следовать ADR и при этом уходить от продукта.

## Решение

1. **Канон — Concept 2.** Источник истины: `design-frontend/UI-SPEC_2.md` + `design-frontend/styles/{tokens,typography,components,layout}.css` + `design-frontend/pages/*`.
2. **Тема — контракт, а не оформление.** `:root` описывает тёмную тему, `[data-theme="light"]` — светлую. Переключатель ставит/снимает атрибут на `<html>` и хранит выбор в `localStorage` под ключом `digest-cds-theme`; тёмная тема — дефолт без сохранённого выбора.
3. **Shell переносится.** `.app-shell`, `.header`, `.header__inner`, `.nav`, `.nav__link`, `.header__search`, `.header__user`, `.theme-toggle` воспроизводятся из `layout.css` Concept 2 вместе с брейкпоинтами. Отклонение ADR-0008 снимается.
4. **Геймификация исключена из релиза.** XP-бар, streak-пилюля, rank-chip, лидерборд (страница и роут), геймификация профиля и квиз в production не переносятся. Это действие ADR-0007, а не его отмена: запрет остаётся в силе.
5. **Следующая версия документируется, а не теряется.** UI-вариант геймификации сохраняется в прототипе: `design-frontend/pages/leaderboard.html`, `design-frontend/pages/quiz.html`, `design-frontend/pages/profile.html`. Они остаются в `design-frontend/` как референс, **не линкуются из навигации** и не имеют production-маршрутов.
6. **Concept 3 не сливается.** Селекторы `.issue-cover`, `.editorial-box`, `.pull-quote`, `.reading-progress`, `.split-layout--reading`, `.toc*`, `.prose` в каноне Concept 2 отсутствуют, поэтому в production они удаляются, а не остаются мёртвым кодом.

## Considered Options

- (A) **Concept 2 целиком, без геймификации, с документированным UI-вариантом на следующую версию** — выбрано: возвращает продуктовое решение, не нарушает ADR-0007 и не теряет уже нарисованный слой.
- (B) Concept 2 как есть, вместе с геймификацией — отвергнуто: прямо противоречит ADR-0007, продуктового решения по XP/лидерборду нет.
- (C) Оставить Concept 3 и доделать его (снять ADR-0008) — отвергнуто: это не решение команды, а следствие документального разворота.
- (D) Взять из Concept 2 только тёмную тему — отвергнуто: тема без shell и типографики Concept 2 даёт тот же гибрид двух языков, который уже один раз привёл к пустому экрану.

## Consequences

- Визуальный слой production переезжает на Concept 2: меняются токены (64 переменные, две темы), типографика (Manrope), компоненты и shell всех экранов.
- Артефакты Concept 3 удаляются из `web/src` вместе с их тестами; parity-стражи переориентируются на `design-frontend/styles/tokens.css` Concept 2.
- Появляется новый автоматический контракт — **отсутствие геймификации** в production и **наличие** документированного варианта в прототипе.
- Responsive evidence обязан сниматься в двух темах: скриншот только тёмной темы больше не доказывает соответствие канону.
- `.github/workflows/ci.yml` и `deploy.yml`, снесённые откатом `706d885`, возвращаются вместе с каноном.
- Правка токена в `web/src/index.css` в обход `design-frontend/styles/tokens.css` снова ломает тест — дрейф обнаруживается до ревью.

## Verification

```bash
node --test tests/unit/*.js        # parity токенов/типографики/компонентов + запрет геймификации
uv run pytest -q tests/unit        # backend без регрессий
npm run build --prefix web         # Tailwind v4 принимает обе темы
npm run test:web                   # контракты экранов + responsive evidence
```

**References:** [`design-frontend/UI-SPEC_2.md`](../../design-frontend/UI-SPEC_2.md), [`design-frontend/styles/tokens.css`](../../design-frontend/styles/tokens.css), [`design-frontend/styles/layout.css`](../../design-frontend/styles/layout.css), [`design-frontend/pages/material.html`](../../design-frontend/pages/material.html), [`web/src/index.css`](../../web/src/index.css), [`web/src/components/ThemeToggle.jsx`](../../web/src/components/ThemeToggle.jsx), тег `backup/main-concept2-mix-20261019`, [`ADR-0006`](0006-concept3-editorial-ui-canon.md), [`ADR-0007`](0007-drop-gamification-supersedes-0001.md), [`ADR-0008`](0008-concept3-shell-deferred-reading-macro-ported.md).

