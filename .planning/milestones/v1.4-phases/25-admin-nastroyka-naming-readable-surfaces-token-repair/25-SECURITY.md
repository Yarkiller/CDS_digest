---
phase: 25
slug: admin-nastroyka-naming-readable-surfaces-token-repair
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-10-22
---

# Phase 25 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Ретроактивная проверка (`/gsd-secure-phase 25`) после завершения UAT.
> Реестр собран из `<threat_model>`-блоков всех десяти PLAN-файлов фазы
> (`register_authored_at_plan_time: true`); классификация выполнена на глубине **ASVS L1**
> (статическая проверка: гейты + дерево + конфиг), `block_on: high`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| route → guard (`RequireAuth` + role) | Переименование метки не должно ослабить доступ к админскому разделу | роль пользователя, путь маршрута |
| spec → runner (`testMatch`) | Непокрытый спек = отсутствующее доказательство, а не «зелёный» результат | имя файла теста |
| CSS-токены → computed style браузера | Токен существует, только если объявлен; значения не приходят из пользовательских данных | статические CSS-литералы |
| `[data-theme="light"]` → контраст | Светлая тема — override-слой; неверный слой делает подпись невидимой | атрибут темы (localStorage пользователя) |
| тинт → подпись | `bg-<status>/<alpha>` полупрозрачен; подпись обязана измеряться на композите | альфа из класса |
| заливка → подпись | Цвет подписи на заливке не должен зависеть от темы | — |
| оверлей → состояние модального окна | Скрайм от темо-зависимого токена маскирует модальное состояние | — |
| состояние отправки → обратная связь | Баннер/тост — единственный признак исхода; невидимый индикатор = молчаливый успех | текст исхода |
| admin chrome → a11y tree | Удаление eyebrow и смена кегля не должны лишить раздел заголовка или фокуса | — |
| статический сканер исходников → гейт CI | Гейт читает версионируемое дерево, а не рантайм | исходники `web/src`, `tests/` |
| Playwright → живой DOM | e2e читает вычисленный стиль реальной страницы | `data-testid`, computed style |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-25-01 | Elevation of Privilege | `AdminLayout.jsx` route wiring | high | mitigate | `PIPELINE_PATH = '/admin/pipeline'` (строки 4, 28, 63, 66, 81) и `data-testid` не редактировались; метка заменена на «Настройка» (стр. 47, 68, 81); тест employee deep-link в `admin.spec.js` не менялся | closed |
| T-25-02 | Tampering | `@theme` / `[data-theme="light"]` | medium | mitigate | Все токены внутри существующих блоков; второй `@theme`-блок запрещён гейтом **G-0**; только статические литералы, ни одного значения из пользовательских данных | closed |
| T-25-03 | Spoofing (UI redress) | `UnsavedChangesDialog` + три скрайма `AdminDigestPage` | high | mitigate | Тема-независимый `--color-scrim: rgba(0, 0, 0, 0.6)` в `web/src/index.css`; `bg-scrim` в 4 местах; `bg-ink` в `web/src` — **0** вхождений (G-10) | closed |
| T-25-04 | Repudiation | `playwright.config.js` `testMatch` / `tests/admin-chrome.spec.js` | high | mitigate | `testMatch: /(web-app\|auth\|knowledge\|razbory\|admin(-chrome)?)\.spec\.js/` (стр. 71) включает новый спек в проект `web`; UAT 12/12 пройден на этом спеке | closed |
| T-25-05 | Denial of Service (процесса) | прогон `--project=web` | medium | mitigate | Precondition «слушатель на 5174 отсутствует» проверен перед прогонами (одна из записей STATE.md § Blockers); финальный UAT-прогон выполнен на свободном порту | closed |
| T-25-06 | Tampering | `AdminLayout` `tabClass`/`nav` | medium | mitigate | Изменены только класс-строки: `text-2xl`, `gap-4`, `mt-0`, `border-rule`, `outline-primary`; `aria-label="Разделы админки"`, `data-testid` и `handleSectionTabClick` не тронуты | closed |
| T-25-07 | Repudiation | потеря программного заголовка раздела | medium | mitigate | `sr-only h1` сохранён (стр. 47) и читает «Настройка»/«Дайджест»; e2e-кейс `naming:` пинит `h1 count === 1` | closed |
| T-25-08 | Spoofing | focus-visible на вкладке | low | mitigate | Новый ринг — `focus-visible:outline-primary` (4.05:1 worst case), не `outline-accent` (2.43:1 на белом) | closed |
| T-25-09 | Information Disclosure | подписи на поверхностях | medium | mitigate | **G-7** пинит контраст ≥ 4.5 для `ink`/`ink-2`/`muted` на `paper` и `paper-2` в обеих темах; floor `danger-solid` = 4.829 | closed |
| T-25-10 | Information Disclosure | подписи на заливках | high | mitigate | **G-9** запрещает темо-зависимую подпись на заливке; e2e пинит три пары (pill / accent CTA / voting) в обеих темах, порог 4.5 | closed |
| T-25-11 | Tampering | `AppShell.jsx` канон-литералы | medium | mitigate | Правилась только `isActive`-ветка `linkClass` (`bg-primary-solid text-on-solid`); канон `bg-bg-app`/`text-text-primary`/`border-border` зелёный в прогоне 97/97 | closed |
| T-25-12 | Elevation of Privilege | `ActionButton` `voting`-вариант | low | mitigate | Менялась только пара цветов (`bg-voting text-voting-ink`); `data-state`-контракт и обработчики не тронуты; UAT 12 подтвердил подпись пилюли, e2e — `confirm-vote` | closed |
| T-25-13 | Information Disclosure | подписи статусов на тинтах (`AdminDigestPage`, `AdminPipelineConfigPage`, auth-формы) | high | mitigate | **G-14** измеряет `-ink` на композите `blendOver(tint, base, alpha)` для трёх баз и обеих тем (порог 4.5) + proof на записанного нарушителя 1.925; **G-18** ловит регресс по использованию | closed |
| T-25-14 | Tampering | `blendOver` как единственная точка композита | medium | mitigate | Композит в общем хелпере (`tests/helpers/contrast.js`), 14 вхождений в гейте; покрыт свойствами alpha 1 / alpha 0 / полупрозрачная база бросает | closed |
| T-25-15 | Spoofing | `--color-field-border` как единственный признак границы поля | medium | mitigate | `--color-field-border` объявлен (#64748B dark, светлый получает 3:1-пару); **G-15** держит 3:1 на трёх поверхностях в обеих темах и доказывает, что декоративный `rule` порог не держит | closed |
| T-25-16 | Spoofing | e2e-подтверждение отправки диджеста | high | mitigate | **G-16** + 4 proof-теста: R1 компилирует тело целиком (4 формы ассерта + grouped), R3 читает `backgroundColor`/`borderTopColor` тоста в окне ±15 строк; отдельная сверка на каждый реальный литерал баннера | closed |
| T-25-17 | Tampering | G-10 без исключений | medium | mitigate | Carve-out удалён; `bg-ink` = 0 и `bg-text-primary/<alpha>` в `web/src` отсутствуют, т.е. повторное исключение сразу краснит гейт | closed |
| T-25-18 | Repudiation | миграция без падающего теста | medium | mitigate | Порядок соблюдён (TDD): G-18/G-16 и снятие carve-out G-10 — до правок `web/src`; e2e RED зафиксирован, затем зелёный | closed |
| T-25-19 | Information Disclosure | ссылка «Повторить загрузку» (2.43:1 в светлой) | high | mitigate | `--color-accent-text` (#06B6D4 dark / #0E7490 light, 5.358/7.248); e2e считает `contrastRatio` на вычисленном цвете | closed |
| T-25-20 | Spoofing | граница поля как признак контрола | high | mitigate | `border-field-border` на контролах (4.759/3.698); **G-17** запрещает `rule`/`border` на контролах; e2e читает `border-top-color` | closed |
| T-25-21 | Tampering | `ActionButton` — две конкурирующие заливки | high | mitigate | Взаимоисключающий fill; **G-21** запрещает цветовую утилиту в записи `loading`; e2e проверяет единственный `bg-*` в обоих состояниях | closed |
| T-25-22 | Repudiation | гонка тем делает светлые ассерты недоказанными | medium | mitigate | `waitForFunction` на `dataset.theme` (7 вхождений в спеке); `waitForTimeout`/`page.clock` — **0** | closed |
| T-25-23 | Elevation of Privilege (перекраска чужого слоя) | декоративный `rule` | low | accept | Принятый риск: G-17 положительно требует `border-rule` на четырёх декоративных строках; риск визуальный, не доступностный. См. Accepted Risks Log | closed |
| T-25-24 | Tampering | `G-20` на `stringLiterals` | high | mitigate | Гейт скоупится литералами `className` (`stringLiterals`, 12 вхождений), а не сырым текстом файла; proof пинит обе стороны (нарушители ловятся, `bg-primary`/`border-primary` — нет) | closed |
| T-25-25 | Tampering | миграция 36 литералов | high | mitigate | `text-primary` standalone = **0**, `text-primary-text` = **36**; `--color-primary: #8B5CF6` не изменён (D-05); коррупции `text-text-primary-text`/`bg-primary-text` нет | closed |
| T-25-26 | Repudiation | e2e-числа в `must_haves` | medium | mitigate | Ожидания записаны точными парами `rgb(109, 40, 217)`/`rgb(167, 139, 250)` и порогом 4.5; при расхождении тест печатает фактическую пару | closed |
| T-25-27 | Elevation of Privilege | новый токен в `THEMED` + `UTILITY_PATTERN` | medium | mitigate | `THEMED` (4 вхождения) питает G-1/G-2, `UTILITY_PATTERN` (3 вхождения) — G-4: нельзя объявить без light-override и нельзя объявить «в стол» | closed |
| T-25-28 | Denial of Service | прогон Playwright на 5174 | low | accept | Принятый риск: занятый порт даёт `ERR_CONNECTION_REFUSED`, а не ложный зелёный; проверка названа как precondition | closed |
| T-25-29 | Tampering | `G-14` (источник альфы) | high | mitigate | `tintAlphaSites` (5 вхождений) читает `/N` из класса; неразобранная альфа — нарушитель; `STATUS_LABEL_TINTS`/`tintAlpha` удалены; proof `/15 → /60` краснеет | closed |
| T-25-30 | Tampering | `G-16` R1 | high | mitigate | `REGEX_LITERAL` (2 вхождения) привязан к слэшу; тело компилируется один раз целиком (4 формы ассерта, grouped) — групповая форма не обходит гейт | closed |
| T-25-31 | Repudiation | `G-16` R3 | high | mitigate | Чтение цветов ограничено окном ±15 строк вокруг `admin-toast`; удаление цветовых ассертов краснит гейт при сохранённых подстроках | closed |
| T-25-32 | Tampering | `tests/admin-chrome.spec.js` | medium | mitigate | Вторая копия константы удалена: `pillAlpha` (3 вхождения) берёт альфу из класса пилюли и падает, если тинт-токена нет | closed |
| T-25-33 | Denial of Service | прогон Playwright на 5174 | low | accept | Принятый риск: как T-25-28 | closed |
| T-25-34 | Tampering | `stateFill.loading` | high | mitigate | **G-21** запрещает любую цветовую утилиту в записи `loading`; proof краснеет на `text-text-primary`, e2e — на `rgb(241, 245, 249)` в тёмной теме | closed |
| T-25-35 | Repudiation | замер `opacity` / `cursor` | medium | mitigate | Ожидания запинены по факту (`0.55`, `not-allowed`) с объяснением специфичности `:disabled`-варианта | closed |
| T-25-36 | Tampering | гонка 600 мс | medium | mitigate | Только `toHaveAttribute`/`toHaveText`; `waitForTimeout` — 0 вхождений в спеке | closed |
| T-25-37 | Elevation of privilege | область плана | low | accept | Принятый риск: WR-11 и 12 backstop-пунктов явно вне скоупа (записаны в SUMMARY), «попутная» правка границы радио не проскочит как закрытие must_have | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-25-01 | T-25-23 | Декоративные границы `border-rule` остаются ниже 3:1 (1.36–1.48 в светлой): это не признак состояния, а визуальный разделитель; поле дополнительно несёт заливку и 44px-бокс, вкладка — `border-accent` + вес 600. WCAG 1.4.11 известен и принят в `25-UI-SPEC.md` § Boundary legibility | gsd-verify-work / secure-phase (L1) | 2026-10-22 |
| AR-25-02 | T-25-28 | Занятый порт 5174 даёт `ERR_CONNECTION_REFUSED`, а не ложный зелёный; проверка свободы порта включена в precondition каждого прогона | gsd-verify-work / secure-phase (L1) | 2026-10-22 |
| AR-25-03 | T-25-33 | То же, что AR-25-02 (повторная запись из плана 25-09 для своего прогона) | gsd-verify-work / secure-phase (L1) | 2026-10-22 |
| AR-25-04 | T-25-37 | WR-11 (граница радиокружка 1.178/1.554) и 12 backstop-пунктов явно отложены в будущую UI-фазу; их закрытие «заодно» запрещено скоупом фазы | gsd-verify-work / secure-phase (L1) | 2026-10-22 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-22 | 37 | 37 | 0 | gsd-verify-work → secure-phase (ASVS L1, block_on: high) |

### Метод (L1)

- Прочитаны `<threat_model>`-блоки всех десяти PLAN-файлов; реестр сведён в 37 уникальных ID
  (T-25-01…T-25-37; T-25-02/03/04/13 упоминаются в двух планах — дедуплицированы).
- `register_authored_at_plan_time: true` — каждый план фазы содержит разбор границ и STRIDE-реестр.
- Классификация по присутствию митигации в рабочем дереве (не в тексте SUMMARY): `web/src/index.css`
  (16 объявлений токенов, включая light-override), `web/src/**` (0 `text-primary`, 36 `text-primary-text`,
  0 `bg-ink`, 4 `bg-scrim`), `AdminLayout.jsx`, `AppShell.jsx`, `playwright.config.js`,
  `tests/unit/test_semantic_token_coverage.js` (G-0…G-21, все ID присутствуют), `tests/admin-chrome.spec.js`.
- Поведенческая проверка: `npm run test:js` → **97 pass / 0 fail** (все 22 гейта и их proof-тесты).
- UAT фазы: 12/12 pass (`25-UAT.md`, коммит `355ac38`) — включая тема-независимые подписи и 320px-геометрию.
- `threats_open: 0` при `register_authored_at_plan_time: true` и `asvs_level == 1` → короткое замыкание
  шага 3: аудитор L2/L3 не требуется, L1-глубины достаточно.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-22
