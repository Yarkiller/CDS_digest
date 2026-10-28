# Phase 30: Classifier practical | conceptual - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-28
**Phase:** 30-classifier-practical-conceptual
**Areas discussed:** Правило practical, Смешанные доклады, Честность тела conceptual

---

## Правило practical

### Что должно открывать гайд, код, Tavily и cheat sheet?

| Option | Description | Selected |
|--------|-------------|----------|
| Инструмент + повторяемые шаги | practical только если есть конкретный стек/тул и шаги, которые аналитик или DS может повторить. Методология и «как устроено» остаются conceptual. | ✓ |
| Любой how-to | practical, если доклад учит «как делать», даже без кода | |
| You decide | зафиксируй бар в CONTEXT | |

**User's choice:** Инструмент + повторяемые шаги
**Notes:** Recommended option. Quota-preserving Diátaxis doing-bar.

### Что считается «инструментом»?

| Option | Description | Selected |
|--------|-------------|----------|
| Runnable / copy-paste | код, CLI, SQL, API, конфиг. Excel/SAP/Tableau без исполняемого артефакта — conceptual | |
| Именованный продукт + шаги | Excel, SAP, Tableau, Power BI, Jira, Python, Kubernetes; чистое «как устроен Kubernetes» без шагов — нет | ✓ |
| You decide | любой именованный тул + шаги, без списка продуктов | |

**User's choice:** Именованный продукт + шаги
**Notes:** Office/enterprise products count; explanation-without-steps does not.

### Насколько конкретными должны быть шаги?

| Option | Description | Selected |
|--------|-------------|----------|
| Читатель может повторить без ролика | нумерованные или чеклистовые шаги в названном продукте | ✓ |
| Демо достаточно | клики по продукту / показ экрана уже practical | |
| You decide | без отдельного порога строгости | |

**User's choice:** Читатель может повторить без ролика
**Notes:** «Потом открываете SAP и смотрите» without a procedure is conceptual.

### Должны ли шаги быть про аудит/данные?

| Option | Description | Selected |
|--------|-------------|----------|
| Любой именованный продукт + шаги | Tavily идёт в доки продукта; аналог для СВА в «Зачем это СВА» | ✓ |
| Только аудит / данные / ИБ / аналитика | Unity/Photoshop с шагами остаются conceptual | |
| You decide | не сужай по домену | |

**User's choice:** Любой именованный продукт + повторяемые шаги
**Notes:** Classifier is not a domain filter.

---

## Смешанные доклады

### Теория + один demo: как классифицировать весь доклад?

| Option | Description | Selected |
|--------|-------------|----------|
| Practical только если doing доминирует | один demo внутри теории остаётся conceptual | ✓ |
| Любой followable demo → practical целиком | даже 3 минуты шагов в часовой лекции открывают extras | |
| Смешанное всегда conceptual | extras только на чисто практических туториалах | |

**User's choice:** Practical только если doing доминирует
**Notes:** Quota gate for mixed talks.

### Как классификатор понимает, что doing «доминирует»?

| Option | Description | Selected |
|--------|-------------|----------|
| По работе страницы | Diátaxis: делать или понимать; не считать минуты | ✓ |
| Большая часть хронометража | процедура явно больше половины транскрипта | |
| You decide | формулировка без метрики | |

**User's choice:** По работе страницы
**Notes:** No 50% / minute-counting rule.

### В лекции «как устроен X» есть полный copy-pasteable пример. Это practical?

| Option | Description | Selected |
|--------|-------------|----------|
| Работа страницы побеждает | иллюстративный код не открывает Tavily; пример остаётся в pass-1 | ✓ |
| Followable пример побеждает | полный повторяемый фрагмент делает доклад practical | |
| You decide | без отдельного правила про иллюстрации | |

**User's choice:** Работа страницы побеждает
**Notes:** Sample code in a conceptual lecture is not extras.

### Если классификатор не уверен — что писать?

| Option | Description | Selected |
|--------|-------------|----------|
| conceptual | то же fail-closed, что KIND-02 на пустой JSON | |
| practical | лучше дать гайд, чем недообогатить how-to | ✓ |
| You decide | KIND-02 покрывает invalid/empty | |

**User's choice:** practical
**Notes:** Prompt-level only. KIND-02 still maps missing/empty/unknown/malformed JSON to conceptual in code. Two layers, not a third enum.

---

## Честность тела conceptual

### Если conceptual-статья содержит «Гайд» или «ссылки скоро появятся» — что делать?

| Option | Description | Selected |
|--------|-------------|----------|
| Вырезать кодом | как ## Аудитория, до persist | ✓ |
| Только промпт | без стриппера; Phase 8 D-15 | |
| Вырезать только пустые «Гайд» и заглушки | заполненный гайд оставляем | |

**User's choice:** Вырезать кодом
**Notes:** Sanitizer, not fail-closed heading validation.

### Какой закрытый набор вырезаем?

| Option | Description | Selected |
|--------|-------------|----------|
| «Гайд» целиком + заглушка «ссылки скоро появятся» | заполненный гайд на conceptual тоже уходит | ✓ |
| Только пустой «Гайд» и текстовые заглушки | заполненные секции не трогаем | |
| Шире | Гайд, Cheat sheet, Шпаргалка, Код плюс заглушки | |

**User's choice:** «Гайд» целиком + заглушка
**Notes:** Extras belong in pass-2 only.

### Вырезать у всех pass-1 статей или только у conceptual?

| Option | Description | Selected |
|--------|-------------|----------|
| У всех pass-1 | гайд появляется только в pass-2 | ✓ |
| Только conceptual | practical pass-1 может оставить секцию | |
| You decide | момент стрипа планировщику | |

**User's choice:** У всех pass-1
**Notes:** Practical drafts must not carry an empty «Гайд» into persist-before-Tavily.

### Точный заголовок или семейство how-to?

| Option | Description | Selected |
|--------|-------------|----------|
| Точный `## Гайд` + литерал «ссылки скоро появятся» | не угадывать Как сделать / Guide / Tutorial | ✓ |
| Семейство | Гайд, Guide, How-to, Практическое руководство, Шпаргалка | |
| You decide | точный `## Гайд` плюс заглушка | |

**User's choice:** Точный `## Гайд` + литерал заглушки
**Notes:** Broader how-to headings can be real talk chapters.

---

## Claude's Discretion

- Classifier input (gray area presented, not selected): transcript vs title+dek vs pass-1 article.
- Exact classifier JSON shape; `TopicKindClassifier` port not added to `__all__`.
- How `topic_kind` is persisted (column + RPC is the research sketch).
- Unsure → practical as a prompt sentence, not a third enum.
- Strip helper placement next to `strip_audience_section`.

Gray area **not discussed:** «Вход классификатора».

## Deferred Ideas

None from discussion. Tavily / enricher / reader downloads / `--debug` remain later v1.5 phases.
