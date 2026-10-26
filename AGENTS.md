## Agent skills

### Issue tracker

Issues live as markdown files under `.scratch/` in this repo. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Git remote (`origin`)

Default remote is **`origin`** (Cursor Origin). Push/pull/fetch and `origin auth` — **only via WSL** (`wsl.exe`), not PowerShell. See `docs/agents/git-origin.md`.

### Обязательный TDD

Разработка Digest CDS ведётся по циклу Red–Green–Refactor.

Для новых функций, исправлений, рефакторинга и изменений поведения обязательно:

1. Сначала написать минимальный автоматизированный тест.
2. Запустить его и убедиться, что он падает по ожидаемой причине.
3. Реализовать минимальный production-код для прохождения теста.
4. Запустить новый тест и весь существующий набор тестов.
5. Выполнить рефакторинг только при полностью успешных тестах.
6. Повторить цикл для следующего поведения.

Запрещено писать production-код до появления соответствующего падающего теста:

> NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST

Тесты должны проверять поведение системы, а не наличие mock-объектов. Моки применяются только при необходимости и после понимания реальных зависимостей.

Исключения допускаются только для конфигурационных, сгенерированных и одноразовых прототипных файлов либо с явным согласованием.
