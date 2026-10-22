# Phase 27 — UI Review

**Audited:** 2026-10-22
**Baseline:** `27-UI-SPEC.md` (approved, revision 2) — audited against the declared state model, spacing scale, typography table, color roles, and copywriting contract. `27-CONTEXT.md` D-01…D-10 treated as locked.
**Screenshots:** captured — dev server `127.0.0.1:5174` with `VITE_USE_MOCKS=true`, 1280 / 390 / 320, both themes
**Method:** computed-style measurement + live state polling (not eyeballing) at 320 / 390 / 1280; the screenshot set is retained for human review.

> Stance is adversarial against the contract, not against the changelog. Pre-existing defects that the phase did not introduce are marked **PRE-EXISTING** and are still scored, because the contract claims a closed inventory of accent, copy, and in-flight chrome for these exact surfaces.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Every declared string is byte-exact; but the overlong-on-mounted state prints «Сократите запрос» above stale rows and a live «Показано 2» that describe a different query. |
| 2. Visuals | 3/4 | Declared in-flight treatment does not render: «Найти» paints at 0.55 opacity with `not-allowed` (contract: `opacity-80` + `cursor-wait`); role chips go disabled with no visual change. |
| 3. Color | 3/4 | 60/30/10 holds and no hardcoded colors exist, but the "closed" accent list is factually exceeded (accent text on tags / «Сбросить фильтр» / «Повторить») and both search placeholders miss 4.5:1 (3.70 and 2.56 in light). |
| 4. Typography | 4/4 | Exactly the declared 4 sizes + 2 pins and 2 weights + 1 pin, measured in the DOM; no state changes size or weight. |
| 5. Spacing | 4/4 | Every spacing utility is on the 4px scale, zero arbitrary values, 44/48px targets intact, no horizontal overflow at 320/390/1280. |
| 6. Experience Design | 2/4 | Loading/error/empty states exist and are proven, but the overlong state violates the contract's "no rows" clause, empty submits stack history while non-empty ones replace, and no request generation guard exists. |

**Overall: 19/24**

---

## Top 3 Priority Fixes

1. **The overlong state renders stale rows for a different query (WR-03) — BLOCKER.** `KnowledgePage.jsx:158-163` sets `setInlineError(validation.message)` and returns without clearing `items` / `hasMore` / `activeQuery`, so `/knowledge?q=RAG` → header overlong submit leaves 2 RAG rows and a live «Показано 2» under an assertive «Сократите запрос». `27-UI-SPEC.md` § state model defines `overlong` as «строк нет» and no `kb-search-error`; the screen it actually produces is a self-contradicting state. **Fix:** in that branch also `setItems([])`, `setHasMore(false)`, `setNextOffset(0)`, `setActiveQuery(null)` (keep `role` and the snapshot cache, matching the `qUrl === ''` branch's "view reset, not data reset" rule) — 4 lines, no new string.
2. **The two new in-flight affordances contradict the contract — WARNING (high).** Measured mid-flight (7 samples at 5 ms): «Найти» computed `opacity: 0.55` and `cursor: not-allowed`, because `disabled:opacity-55` + `disabled:cursor-not-allowed` (`ActionButton.jsx:57`) win over `stateChrome.loading`'s `opacity-80` / `cursor-wait` (`ActionButton.jsx:16-18`); and all three role chips are `disabled` with `opacity: 1` and `cursor: default` (`KnowledgePage.jsx:478`) although `27-UI-SPEC.md` § E3·loading states «У чипов нет спиннера/`disabled` во время поиска». Result: an undeclared dim on the CTA and three controls that look live but silently swallow clicks. **Fix:** drop `disabled={searching}` from the role chips (guard re-entry in `handleRoleChange` instead), and let the loading state carry a single opacity source (e.g. `disabled:opacity-80` on the loading variant, or move `stateChrome.loading` to `disabled:opacity-80 disabled:cursor-wait`).
3. **Placeholder copy — the only text on the phase's primary input — fails contrast in both themes — WARNING.** The header pill uses `placeholder:text-text-disabled` (`SearchPill.jsx:67`) = 3.70:1 dark / 2.56:1 light against `--color-bg-surface`; `#kb-search` (`KnowledgePage.jsx:446`) declares **no** placeholder utility and inherits the UA default 50 %-alpha colour (4.86:1 dark / 3.42:1 light). Two inputs, two different greys, one of them below WCAG AA at 14px. **Fix:** add `placeholder:text-text-disabled` to `#kb-search` for consistency and raise the placeholder token (or add a dedicated `--color-text-placeholder`) so both clear 4.5:1 — the light theme is the failing one in every case.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**Conformance (verified against the Copywriting Contract, string by string):**

| Contract element | Rendered | Location |
|---|---|---|
| Header sr-only / placeholder | `Поиск Digest CDS` / `Поиск по базе` | `SearchPill.jsx:58,66` |
| Page CTA | `Найти` | `KnowledgePage.jsx:455` |
| Landing heading + chips | `Попробуйте тему:` + `RAG` `SQL` `качество данных` `pgvector` | `KnowledgePage.jsx:17,525-537` |
| Zero-hit | `Ничего не нашли` / `По запросу нет материалов — уточните формулировку или смените роль.` / `Сбросить фильтр` | `KnowledgePage.jsx:561-569` |
| Error | `Не удалось найти материалы` + `Не удалось выполнить поиск. Проверьте сеть.` + `Повторить` | `KnowledgePage.jsx:543-547`, `ErrorPanel.jsx:8-11` |
| Validation | `Введите запрос` / `Сократите запрос` | `KnowledgePage.jsx:311-313,336` + validator `message` in the effect (`:161`) |
| Loading | `Ищем…` | `KnowledgePage.jsx:503` |
| Count | `Показано 2` / `Показано N+` / `Найдено 0 материалов` | measured live: `Показано 2`, `Найдено 0 материалов` |

Zero-new-strings invariant holds: the effect reuses `validation.message` (`:161`) and the two page literals stay at the pre-existing sites (`:313`, `:336`), exactly as § Copywriting Contract prescribes.

- **WARNING — copy contradicts the visible state (same defect as Priority 1).** Measured at 320 on a mounted result surface: `inline: "Сократите запрос"`, `statusText: "Показано 2"`, `hitCount: 2` (RAG rows). A rejection message and an affirmative count for two different queries are on screen simultaneously. The contract's `overlong` row requires «строк нет».
- **WARNING (PRE-EXISTING) — the contract's copy inventory omits the page field placeholder.** `Спросите своими словами: SQL, дашборды, RAG…` (`KnowledgePage.jsx:445`) is the landing's only visible instruction (the `<label>` is `sr-only`), yet it is absent from the Copywriting Contract table. Not a new string and not a phase regression, but the contract cannot be used as an exhaustive copy baseline while it is missing.
- **Info — no generic labels found.** The surfaces contain no `Submit` / `OK` / `Cancel` / `Save`; `Найти`, `Повторить`, `Показать ещё`, `Сбросить фильтр` are all specific verbs.

### Pillar 2: Visuals (3/4)

- **WARNING — the declared in-flight chrome is not what renders.** Sampled during a page-form search at 5 ms resolution: `{disabled: true, data-state: "loading", opacity: "0.55", cursor: "not-allowed"}` for 7 consecutive samples, then idle. `27-UI-SPEC.md` § Typography/Color pins the loading treatment to `opacity-80` (`stateChrome.loading`, `ActionButton.jsx:17`) and `27-UI-SPEC.md` § E10·loading says «без смены заливки, начертания и размера». The `disabled:` variants (`ActionButton.jsx:57`) override both the opacity and the cursor. The dimming is therefore 25 points deeper than contracted and the cursor reads as "unavailable" instead of "working".
- **WARNING — three role chips become dead controls with no visual signal.** `disabled={searching}` (`KnowledgePage.jsx:478`) sets `disabled = true` on all three chips while `opacity` stays `1` and `cursor` stays `default` (there is no `disabled:` utility on either chip class at `:482-483`). Users get a clickable-looking control that does nothing during the request; the contract explicitly forbids `disabled` here.
- **WARNING — the "first result row is the focal point" claim does not hold.** Measured in the populated state at 1280: `h1` 30px/600 (36px line box), row title 18px/600, status 12px/400. The only filled accent in the viewport is the «Найти» primary button, an action already completed. Visual weight ordering is h1 → form/CTA → rows, not rows → chrome. No chrome was allowed to change (correctly), but the contract's focal-point claim is aspirational rather than observable.
- **Warning (minor) — «Сбросить фильтр» is an accent-coloured button rendered as plain text** (`inline-flex min-h-11 text-sm text-primary-text`, `KnowledgePage.jsx:565-568`) with no underline or hover treatment, while every other text-link in the app (e.g. `IssuePage.jsx:55`) carries `hover:underline`. Affordance is ambiguous; 44px target is correct.
- **Conformance:** no icon-only buttons on any phase surface; result rows carry a hover surface (`MaterialListRow.jsx:19`) and a full-row link; the page has one H1 and the rows are `<h3>`, so heading order is h1 → h3 (browsers and AT tolerate this, but there is no `<h2>` in the results state — informational).

### Pillar 3: Color (3/4)

Measured on the dark theme at 1280 unless stated.

- **60/30/10 — passes.** `body` = `rgb(11,15,23)` (`--color-bg-app`); surfaces `rgb(19,25,37)` (`--color-bg-surface`) are limited to the field, chips, rows-on-hover, and cards; filled accent (`rgb(124,58,237)`) appears on exactly **2** elements in both landing and results states (the pressed role chip and «Найти»). No gradient or shadow was added by the phase.
- **No hardcoded colours.** `#[0-9a-fA-F]{3,8}` / `rgb(` scan over `web/src/**/*.jsx` returns nothing; every colour is a token.
- **WARNING — the accent "closed list" is exceeded, so the contract is not an accurate inventory.** The contract reserves accent for (1) the pressed role chip, (2) the primary «Найти», (3) the active nav pill, and explicitly forbids «акцент на строке выдачи». Measured accent **text** outside that list:
  - result-row tags `#RAG` — `text-primary-text` = `#A78BFA` on `#131925` (`MaterialListRow.jsx:43`), 7.05:1 — *directly inside the result row the contract forbids accent on*;
  - «Сбросить фильтр» — same token (`KnowledgePage.jsx:567`), 7.05:1;
  - «Повторить» — `ActionButton variant="secondary"` resolves to `text-primary-text` (`ActionButton.jsx:43`), 7.05:1.

  All three are PRE-EXISTING and readable, and the contract itself declares both components unchanged — but a reviewer comparing render against the contract will conclude the contract is wrong, not the code. The contract should either widen the accent list to "accent text on tags and secondary actions" or the tags should move to a neutral token.
- **WARNING — placeholder contrast.** Header pill `rgb(100,116,139)` on `rgb(19,25,37)` = **3.70:1** (dark), `rgb(148,163,184)` on `#FFFFFF` = **2.56:1** (light). Page field inherits the UA default 50 %-alpha placeholder → **4.86:1** dark, **3.42:1** light. Both are 14px normal text, so AA needs 4.5:1; three of the four combinations fail (see Priority 3).
- **Conformance (contrast measured, all ≥ AA):** status/snippet `#94A3B8` 7.48:1 dark and 4.55:1 light (light theme clears the floor by 1 % — brittle); zero-hit body 6.86:1; zero-hit heading 16.06:1; row title 17.06:1 light; tags 7.05:1 dark / 7.10:1 light; error copy `#F87171` on the danger tint ≥ 5:1.
- **Info:** the light theme flips `--color-primary-text` to `#6D28D9` (`index.css:205`), which is why tag/retry text stays readable there — the token pair is doing its job.

### Pillar 4: Typography (4/4)

Rendered sizes and weights, measured with `getComputedStyle` on the phase surfaces:

| Role | Measured | Contract |
|---|---|---|
| Page title | 30px / 600 / lh 36px | 30 / 600 / 1.20 ✓ |
| Result title (`MaterialListRow`) | 18px / 600 / lh 28px | 18 / 600 ✓ |
| Field, snippet, inline error, form labels | 14px / 400 / lh 20px | 14 / 400 ✓ |
| Status, landing caption, tags | 12px / 400 / lh 16px | 12 / 400 ✓ |
| Zero-hit heading | 24px / 600 | pin 24 ✓ |
| `ErrorPanel` heading | 16px / 600 | pin 16 ✓ |
| `ActionButton` label | 14px / 500 | pin 500 ✓ |

- **Finding (conformance):** exactly 6 sizes and 3 weights exist across the whole phase path — the declared 4 sizes + 2 pins and the declared 2 weights + 1 pin. No undeclared size appears in the landing, in-flight, populated, zero-hit, overlong, error, or restored frames.
- **Finding (conformance):** no state transition changes type. In-flight changes only the button's opacity and the live region's text (`Ищем…` keeps 12/400, measured); overlong keeps 14/400; error keeps 16/600 + 14/400. The contract's «Loading не "утолщает" и не "уменьшает" ни одной подписи» holds.

### Pillar 5: Spacing (4/4)

- **Every spacing utility on the phase surfaces is on the declared 4px scale.** Enumerated from source: `mb-6`(24), `mb-4`(16), `gap-3`(12), `px-4 py-3`(16/12), `mt-2`(8), `mb-6`/`gap-2`(8), `px-3`(12), `mb-8`(32), `mb-3`(12), `mt-4`(16), `p-8`(32), `mt-6`(24), `space-y-3`(12). That is the exact set the contract's Spacing Scale table declares; nothing outside it appears.
- **Zero arbitrary values.** `\[[^\]]*(px|rem|vh|vw)[^\]]*\]` over `KnowledgePage.jsx` → no matches. (The one bracketed value in the phase is `grid-cols-[4rem_minmax(0,1fr)]` in `MaterialListRow.jsx:19`, a grid track, not spacing, and explicitly pinned by the contract.)
- **Touch targets intact (measured at 320):** role chip 44px, hint chip 44px, «Повторить» 44px, header pill 48px (`min-h-12`). Nothing shrank below 44.
- **No horizontal overflow:** `documentElement.scrollWidth == clientWidth` at 1280 (1280/1280), 390 (375/375), 320 (305/305). Zero elements crossed the right edge at 320; the only `scrollWidth > clientWidth` hit is the `sr-only` label, which is correct.
- **Info (intentional, not a defect):** two card states use different geometry — zero-hit `rounded-2xl p-8` (16px radius / 32px padding) vs `ErrorPanel` `rounded-xl p-4` (12px / 16px). The contract explicitly forbids unifying them ("унификация — редизайн, запрещена").

### Pillar 6: Experience Design (2/4)

**State coverage (measured, not inferred):**

| State | Observed | Verdict |
|---|---|---|
| `landing` | form + 3 role chips + «Попробуйте тему:» + 4 chips, no status node, no rows | ✓ |
| `in-flight` | field `disabled`, button `data-state="loading"`, live «Ищем…», no `kb-hint-chips`, no skeleton (7/7 samples) | ✓ mechanism, ✗ chrome (see Pillar 2) |
| `populated` | 2 rows, live «Показано 2», hints 0 | ✓ |
| `zero-hit` | «Ничего не нашли» + body + «Сбросить фильтр» enabled, live «Найдено 0 материалов», rows 0 | ✓ |
| `error` | panel «Не удалось найти материалы» + «Повторить» enabled, hints 0, live region **absent**, rows 0, no alert in `<header>` | ✓ |
| `overlong` (from `/`) | «Сократите запрос», rows 0, hints 0, no panel | ✓ |
| `overlong` (on a mounted result surface) | «Сократите запрос» **plus** 2 rows and live «Показано 2» | ✗ **contract violation** |
| `restored` (Back from material) | rows instantly, counter Δ=0, X-2 log empty | ✓ (per `27-VERIFICATION.md`, not re-derived) |

- **BLOCKER — the `overlong` state is not self-consistent on a mounted surface.** `KnowledgePage.jsx:158-163` returns after `setInlineError` without touching `items`/`activeQuery`, so the newest state the phase introduces can render "this query is invalid" over "2 results for the previous query". The contract's state table says «строк нет». Reproduced live at 320 and captured in `mobile-320-overlong-stale-rows.png`. This is the single defect that can leave a user reading results they believe belong to the query in the URL — the exact class of confusion the URL-as-source-of-truth design (D-01) exists to prevent.
- **WARNING — empty submits push history while non-empty submits replace (WR-02).** Measured from `/knowledge?q=RAG`: empty header Enter → URL `/knowledge`, `history.length` **17 → 18**. The non-empty path is `navigate(..., { replace: true, state: {submitId} })` (`SearchPill.jsx:43-48`) and the page form/chip use `replace` (`writeQueryToUrl`, `:304-306`). Consequence: the same control (Enter in the header) has two different Back semantics, and Back from the empty landing resurrects the previous query. `27-SECURITY.md` T-27-16 records this as accepted residual risk (FU-27-01); from a UX standpoint it is an inconsistency in an otherwise uniform replace-only discipline.
- **WARNING — no request generation guard (WR-01).** `runSearch` (`:216-292`) applies every settled response unconditionally. Two header submissions inside one 80 ms mock window (trivially reachable on a slow network) can commit the older query's rows last, leaving rows that do not match the URL. The header pill is deliberately payload-only, so it cannot be disabled — the guard has to live in the page (a monotonically increasing request id, or `AbortController` in the adapter's caller).
- **WARNING — in-flight controls that look live but are dead** (role chips) and an over-dimmed CTA — see Priority 2; this is the pillar's second-largest gap because it affects the very state the phase adds.
- **Conformance:** error is never cached and retry costs exactly one request (seed→fail→revisit = 1→2→3, per `27-VERIFICATION.md`); zero-hit and error are mutually exclusive; the header never shows an error (measured `alertsInHeader: 0`); the first search renders no skeleton (append-only, structural); no destructive action exists, so confirmation is correctly absent; disabled states exist for the two submit controls.

---

## Minor Recommendations (beyond the top 3)

1. `KnowledgePage.jsx:446` — add `placeholder:text-text-disabled` so the page field and the header pill share one placeholder token.
2. `index.css:15` / `:184` — `--color-text-disabled` is used for placeholder text; either raise it or introduce `--color-text-placeholder` so the token can satisfy AA without changing disabled *control* text.
3. `KnowledgePage.jsx:478` — remove `disabled={searching}` from the role chips (or add a real `disabled:opacity-55 disabled:cursor-not-allowed` treatment **and** update `27-UI-SPEC.md` § E3·loading, which currently says there is none).
4. `ActionButton.jsx:16-18,57` — make the loading opacity/cursor single-sourced so the render matches the documented `opacity-80` / `cursor-wait`.
5. `KnowledgePage.jsx:563` — results state has `<h1>` then `<h3>` rows with no `<h2>`; adding a visually-hidden `<h2>Результаты</h2>` (a copy addition — needs contract approval) would fix the heading outline.
6. `KnowledgePage.jsx:565-568` — give «Сбросить фильтр» a `hover:underline` or a real button chrome to match its affordance elsewhere in the app.
7. `27-UI-SPEC.md` § Color — widen or correct the "closed" accent list so it names tag text, «Сбросить фильтр», and secondary `ActionButton` labels; today the contract is contradicted by code it declares frozen.
8. Tests — no assertion covers chip `disabled` or the button's computed opacity, so neither in-flight regression above can redden the suite; the existing structural pin only forbids `data-state`/`aria-busy` on chips (`tests/knowledge.spec.js:313`).

---

## Files Audited

Implementation (read-only):

- `web/src/pages/KnowledgePage.jsx` — effect/state model (`:128-214`), `runSearch` (`:216-292`), `writeQueryToUrl` (`:304`), `handleSubmit` (`:307-330`), `handleRoleChange` (`:331-348`), `handleRetry` (`:352`), `preSearch`/`showZeroHit` (`:379-381`), `KnowledgeSearchForm` (`:416-498`), status node (`:551-555`), zero-hit card (`:556-572`), hit list (`:585-605`)
- `web/src/components/SearchPill.jsx` — empty/non-empty submit (`:34-48`), input (`:61-68`)
- `web/src/components/MaterialListRow.jsx` — row, title, snippet, tag (`:17-45`)
- `web/src/components/ActionButton.jsx` — `stateChrome` (`:16-18`), variant/state class assembly (`:30-60`)
- `web/src/components/ErrorPanel.jsx` — panel chrome and `role="alert"` (`:1-24`)
- `web/src/index.css` — spacing/radius/font tokens (`:95-117`), dark palette (`:8-87`), light palette (`:176-211`)
- `web/src/services/knowledgeApi.js` — **not read for change; frozen** (sha256 gate `tests/unit/test_knowledge_api_snapshot.js` green, `git diff` clean)

Contract / evidence:

- `.planning/phases/27-header-search-runs-on-submit/27-UI-SPEC.md` (audit baseline)
- `27-CONTEXT.md`, `27-01…27-05-PLAN.md`, `27-01…27-05-SUMMARY.md`
- `27-VERIFICATION.md` (WR-01…WR-04, backstop items), `27-SECURITY.md` (T-27-16 / AR-27-03 / FU-27-01)
- `tests/knowledge.spec.js` (in-flight label collector `:120-145`, structural chip pin `:313`, error-panel assertions `:595`)

Screenshots (`.planning/ui-reviews/27-20261022-160628/`, git-ignored by `.planning/ui-reviews/.gitignore`):

- `desktop-1280-landing.png`, `desktop-1280-results.png`
- `mobile-390-landing.png`, `mobile-390-results-light.png`
- `mobile-320-results.png`, `mobile-320-zero-hit.png`, `mobile-320-error.png`, `mobile-320-overlong-stale-rows.png`

**Registry audit:** not applicable — `web/components.json` does not exist and `27-UI-SPEC.md` § Registry Safety declares no registries or blocks, so no third-party block was installed by this phase.

---

_Audited by gsd-ui-auditor · 2026-10-22 · measurements from a live `VITE_USE_MOCKS=true` build at 1280/390/320, dark + light_
