---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
reviewed: 2026-10-21T13:45:00Z
depth: standard
scope: "PIPEUI-01…04, THEME-01/02; tree at working copy, diff base 38f59c39d83919bb56ff7fdc814a1a59c569512e^"
files_reviewed: 17
files_reviewed_list:
  - playwright.config.js
  - tests/admin-chrome.spec.js
  - tests/admin.spec.js
  - tests/helpers/contrast.js
  - tests/unit/test_semantic_token_coverage.js
  - web/src/components/ActionButton.jsx
  - web/src/components/AdminLayout.jsx
  - web/src/components/AppShell.jsx
  - web/src/components/IngestSourcesSection.jsx
  - web/src/components/ServiceUnavailable.jsx
  - web/src/components/UnsavedChangesDialog.jsx
  - web/src/index.css
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/pages/KnowledgePage.jsx
  - web/src/pages/LoginPage.jsx
  - web/src/pages/RegisterPage.jsx
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Phase 25: Code Review Report (Настройка / readable surfaces / token repair)

**Reviewed:** 2026-10-21T13:45:00Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found
**Scope:** `38f59c39…^..worktree` — PIPEUI-01…04 (rename, chrome geometry, «Источники» heading) and THEME-01/02 (semantic token family, theme-independent fill labels, `--color-scrim`).

## Summary

The core of the phase is genuinely implemented, and I verified it against the artefact rather than the diff prose:

- `npm run test:js` → **61 passed, 0 failed**, including the eleven new `G-0…G-10` gates.
- `npm run build --prefix web` → built, and the emitted stylesheet really contains `.bg-paper{background-color:var(--color-paper)}`, `.bg-paper-2`, `.text-ink-2`, `.text-muted`, `.border-rule`, `.bg-scrim`, `.text-on-solid`, `.text-voting-ink`. The «tokens Tailwind will not generate» class of defect is closed for the new family — no finding there.
- Cascade check in `web/dist/assets/index-*.css`: `[data-theme=light]` is emitted inside `@layer base` (index 8468) *after* the `@layer theme` token block (index 3757), so the light overrides do win over `:root`, and the six themed tokens are all overridden with non-identical values.

The rename is honest too: the three surfaces (tab, sr-only h1, mobile `<option>`) are «Настройка», the route and every `data-testid` are untouched, and `tests/admin.spec.js` was updated rather than bypassed.

What the phase did **not** close is the second half of «readable surfaces». `IngestSourcesSection.jsx` still paints its destructive action and every add-error message with hard-coded `oklch()` values that the new token gate cannot see — measured **1.98:1** on the row surface in the default dark theme (CR-01). Around it, the legacy status tokens (`--color-danger`, `--color-success`, `--color-voting`) are still used as *text* on tints and on white, which fails 4.5:1 in light theme (WR-02, WR-05), and the new lint gates have blind spots that would let the exact regressions this phase fixed walk back in (WR-01).

## Critical Issues

### CR-01: The «Удалить» label and the add-error copy are hard-coded `oklch()` and measure ≈2:1 in the default dark theme

**File:** `web/src/components/IngestSourcesSection.jsx:237`, `:253`, `:336`, `:338`, `:346`, `:356`, `:362`
**Issue:** Every destructive/error colour in this file bypasses the token layer with arbitrary values:

- `text-[oklch(45%_0.14_25)]` resolves to `rgb(147, 43, 42)`. Against the row surface the phase just made opaque (`bg-paper-2` → `#1A2233`) that is **1.98:1**; against the section surface (`bg-paper` → `#131925`) it is **2.20:1**. The label of the delete button and the `role="alert"` row error are therefore effectively unreadable in dark, which is the default theme (`--color-bg-app: #0B0F17`).
- The diff made this slightly worse: `bg-paper-2/40 → bg-paper-2` (`:219`, `:263`) moved the row background from an over-`paper` blend toward the lighter elevated value, so the contrast of the hard-coded dark red dropped.
- The validation panel is a *light* surface in a dark theme: `bg-[oklch(96%_0.03_25)]` = `rgb(255, 235, 232)` with `border-[oklch(70%_0.12_25)]` = `rgb(223, 127, 120)`. It is legible (6.99:1) but it is exactly the "hard-coded colour that ignores the theme" pattern this phase exists to remove, and it is invisible to `G-4`/`G-6`/`G-9` because those gates only look for the six family names.
- `G-4` claims "every semantic utility used under web/src resolves to a declared token" — arbitrary-value utilities such as `text-[oklch(…)` and `bg-[oklch(…)` are not matched at all, so the suite stays green on all of this.

**Fix:** Add the missing themed ink/line roles and use them; also make the gate able to see arbitrary colour values.

```css
/* web/src/index.css — @theme (dark defaults) */
--color-danger-ink: #FCA5A5;   /* 8.38:1 on --color-paper-2 */
--color-danger-line: #7F1D1D;
--color-success-ink: #4ADE80;  /* 9.13:1 on --color-paper-2 */
--color-voting-ink-on-tint: #FDE68A;

/* [data-theme="light"] */
--color-danger-ink: #B91C1C;   /* 6.47:1 on #FFFFFF */
--color-danger-line: #FCA5A5;
--color-success-ink: #166534;  /* 6.02:1 on the success/15 tint */
--color-voting-ink-on-tint: #713F12; /* 7.33:1 on the voting/20 tint */
```

```jsx
// web/src/components/IngestSourcesSection.jsx
<button
  type="button"
  className="inline-flex min-h-11 items-center rounded-xl border border-danger-line px-3 text-sm font-normal text-danger-ink disabled:cursor-not-allowed disabled:opacity-45"
  disabled={rowBusy}
  onClick={() => onDelete(row)}
>
  Удалить
</button>
...
<p role="alert" className="mt-2 text-sm text-danger-ink">{rowErrors[id]}</p>
...
<div className="mt-4 rounded-2xl border border-danger-line bg-paper-2 p-4">
  <h3 className="font-sans text-2xl font-semibold text-danger-ink">Проверьте данные источника</h3>
```

Add the new names to `THEMED` in `tests/unit/test_semantic_token_coverage.js` so `G-1/G-2/G-7` cover them, and add a `G-11` that forbids colour-valued arbitrary utilities:

```js
const ARBITRARY_COLOR = /(?<![\w-])(?:bg|text|border|ring|outline|divide|fill|stroke)-\[[^\]]*(?:oklch|oklab|rgba?\(|color-mix|#[0-9a-f]{3,8})[^\]]*\]/gi
```

**Note:** this code predates the phase (the diff left these lines untouched), so it is not a regression *introduced* here — but it is in a file the phase rewrote, it is the surface the phase is named after, and the phase's own 4.5:1 gate is advertised as covering it while it structurally cannot.

## Warnings

### WR-01: `G-9` compares one string literal at a time, and its fill list omits every `-solid` token — the exact regression this phase fixed can return green

**File:** `tests/unit/test_semantic_token_coverage.js:70`, `:86-111`, `:332-352`
**Issue:** Two independent holes in the gate that is supposed to prevent `bg-primary text-text-primary` from coming back:

1. `FILL_TOKENS = ['bg-primary', 'bg-accent', 'bg-success', 'bg-danger', 'bg-voting']`. `tokenSet()` uses exact token equality, so `bg-primary-solid` is *not* a fill for this gate. A future `bg-primary-solid text-text-primary` (the most likely shape of the same mistake, one suffix away) passes silently.
2. The scan iterates `for (const literal of stringLiterals(source))` — one literal at a time. The dominant pattern in this codebase is a class list assembled from several literals (`ActionButton` joins `variantClass` + `stateClass`; `AdminDigestPage.jsx:696-699` and `:714-719` join arrays). A fill in one literal and a theme-dependent label in another are never compared, though the file comment asserts "a class list can only live in a string".

**Fix:** Close hole 1 immediately (five tokens, no false positives):

```js
const FILL_TOKENS = [
  'bg-primary', 'bg-primary-solid',
  'bg-accent', 'bg-accent-solid',
  'bg-success', 'bg-success-solid',
  'bg-danger', 'bg-danger-solid',
  'bg-voting',
]
```

For hole 2, either scan the statically joined list (`className={\[...\].join(' ')}` arrays can be reduced by concatenating their literal elements inside the bracket expression), or state the limitation in the docstring and cover the composed components in Playwright (`classTokens()` already exists in `admin-chrome.spec.js`). Do not leave the comment claiming completeness that the code does not have.

### WR-02: Status tokens used as *text* on tints/white still fail 4.5:1 in light theme, and the new gate cannot see them

**File:** `web/src/pages/AdminDigestPage.jsx:717-718`; `web/src/pages/AdminPipelineConfigPage.jsx:333-335`, `:344`, `:354`, `:362-364`; `web/src/pages/LoginPage.jsx:160`, `:165`, `:190`; `web/src/pages/RegisterPage.jsx:141`, `:172`, `:177`, `:202`
**Issue:** The phase created a correct themed family for `paper/ink/muted/rule` but left the *semantic status* colours untouched and theme-blind. Measured with the phase's own helper:

| pair | light | dark |
|---|---|---|
| `text-success` on `bg-success/15` (`#22C55E` on `#D8F2E4`) | **1.92:1** | 6.71:1 |
| `text-voting` on `bg-voting/20` (`#EAB308` on `#F5ECCB`) | **1.62:1** | 6.84:1 |
| `text-danger` on `bg-danger/10` (`#EF4444` on `#F7E8EA`) | **3.17:1** | 4.71:1 |
| `text-danger` on `bg-bg-surface` (`#EF4444` on `#FFFFFF`, Login/Register field errors) | **3.76:1** | n/a |

The general rule the family encodes is missing for status colours: **a tint of a theme-flat token over a theme-dependent background produces a theme-dependent surface**, so the label on it must be themed as well. `G-7` only loops over `paper/paper-2 × ink/ink-2/muted`, so none of these pairs is gated.

**Fix:** Introduce themed `-ink` variants (see CR-01's snippet) and use them wherever a status token is a *label* rather than a fill. For the digest pills:

```jsx
item.material_status === 'ready'
  ? 'bg-success/15 text-success-ink'
  : 'bg-voting/20 text-voting-ink-on-tint'
```

and for the error panels `text-danger-ink` with `border-danger-line`. Then extend `G-7` to iterate the tint pairs (`-ink` on the matching `/10`–`/20` composite over `paper`), not just the six-family matrix.

### WR-03: `ActionButton` emits two competing fills; the state fill is dead code today and a 1.92:1 hazard if the emission order ever changes

**File:** `web/src/components/ActionButton.jsx:1-5`, `:18-22`, `:28-34` (consumer: `web/src/pages/VotingPage.jsx:517-521`)
**Issue:** `variantClass` and `stateClass[state]` are both appended to the same `className`, so for `variant="voting"` + `state="success"|"error"` the element carries `bg-voting text-voting-ink` **and** `bg-success-solid text-on-solid` / `bg-danger-solid text-on-solid`. Which pair paints is decided by stylesheet order, not by class order. In the built stylesheet the order is:

```
.bg-danger-solid (16719) < .bg-paper (16958) < .bg-primary-solid (17104) < .bg-success-solid (17394) < .bg-voting (17737)
.text-on-solid  (21156) < .text-voting-ink (21479)
```

So today the variant wins and the success/error state paints nothing — voting feedback silently loses its green/red affordance (the copy still changes). If Tailwind's sort ever flips, the same markup becomes white-on-yellow (**1.92:1**), which `admin-chrome.spec.js` itself says "must fail here".

**Fix:** Make the state override the variant explicitly so exactly one fill is emitted:

```js
const stateFill = {
  error: 'bg-danger-solid text-on-solid',
  success: 'bg-success-solid text-on-solid',
}[state]
const stateExtra = state === 'loading' ? 'cursor-wait opacity-80' : ''
const fill = stateFill ?? variantClass

className={[base, 'disabled:cursor-not-allowed disabled:opacity-55', fill, stateExtra, className].join(' ')}
```

### WR-04: The light-theme assertions never wait for `data-theme` to land, so they can read the dark sheet

**File:** `tests/admin-chrome.spec.js:26-41`, `:176-235`, `:238-300`
**Issue:** `gotoAdmin()` sets the storage key before load, which is correct, but `ThemeToggle.jsx:6-18` applies `document.documentElement.setAttribute('data-theme', 'light')` in a `useEffect`, i.e. after mount, not before first paint. The helper then only awaits `document.fonts.ready` — it never asserts the attribute is present. The equality assertions (`rgb(51, 65, 85)` / `rgb(255, 255, 255)`) and the `--color-paper` probe are therefore racing the effect; on a slow first paint the spec reads the dark sheet and fails (or, worse, the `not.toBe('rgba(0, 0, 0, 0)')` guard gives a misleading "must paint an opaque surface" message for what is actually a theme race).

**Fix:** Await the attribute as part of `gotoAdmin`:

```js
if (theme === "light") {
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
} else {
  await expect(page.locator("html")).not.toHaveAttribute("data-theme", "light");
}
```

### WR-05: The admin toast paints `text-text-primary` on `bg-text-primary` — 1.00:1 in both themes

**File:** `web/src/pages/AdminDigestPage.jsx:808`
**Issue:** `className="… rounded-full bg-text-primary px-4 py-2 text-sm text-text-primary"`. Fill and label are the same token in both themes (dark `#F1F5F9` on `#F1F5F9`; light `#0F172A` on `#0F172A`) → **1.00:1**. The digest send confirmation ("Выпуск опубликован", "Не сохранено") is invisible.

`G-10` deliberately exempts this exact token (`if (token === 'bg-text-primary') continue`, `test_semantic_token_coverage.js:362-364`) as a "known adjacent defect", so the suite will stay green whether or not it is ever fixed. That exemption is also what makes it invisible to review tooling, so it is recorded here as a warning rather than silently accepted.

**Fix:** Use the alias family, which inverts correctly in both themes and passes `G-6` (no `bg-ink`) and `G-9` (no theme-dependent label on a fill):

```jsx
className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 rounded-full border border-rule bg-paper-2 px-4 py-2 text-sm text-ink"
```

and drop the `bg-text-primary` carve-out from `G-10` once this lands.

### WR-06: The light-theme field edge is 1.48:1 — the deviation is pinned as "by design" but still misses WCAG 1.4.11's 3:1

**File:** `web/src/index.css:149` (`--color-rule: #CBD5E1`), `tests/unit/test_semantic_token_coverage.js:318-329`
**Issue:** `G-8` pins the light `rule ≠ border` deviation as deliberate because `border` on paper would be **1.23:1**, but the chosen value only reaches **1.48:1** against `--color-paper` (`#CBD5E1` on `#FFFFFF`), and the fill difference is **1.06:1**. The `<select>`/`<input>`/`<textarea>` fields in light theme (e.g. `IngestSourcesSection` form, `AdminLayout` select) are therefore identified only by a boundary below the 3:1 required by WCAG 1.4.11 for user-interface components, while the test message reads as if the boundary question were settled.

**Fix:** Give fields their own boundary token instead of overloading the decorative rule:

```css
/* @theme */        --color-field-border: #4B5563;  /* dark */
/* [data-theme="light"] */ --color-field-border: #64748B; /* 4.76:1 on paper */
```

Use `border-field-border` on form controls only, keep `--color-rule` for card/divider decoration, and add the pair to `G-7` with a ≥3:1 floor for non-text contrast. At minimum, make `G-8`'s message state the achieved ratio (1.48) rather than implying conformance.

## Info

### IN-01: `THEME_DEPENDENT_LABELS` is half dead

**File:** `tests/unit/test_semantic_token_coverage.js:73`
**Issue:** `['text-text-primary', 'text-accent-ink', 'text-bg-app']` — `accent-ink` no longer exists anywhere (`G-5` forbids it) and `text-bg-app` has no consumers after the voting migration. Only `text-text-primary` is actually enforced, so the list advertises three bans and delivers one.
**Fix:** Prune the dead entries, or add a positive assertion that each forbidden label token exists somewhere in `web/src` (which would fail loudly when the token is retired).

### IN-02: `contrastRatio()` cannot measure the colours CR-01/WR-02 need

**File:** `tests/helpers/contrast.js:19-62`
**Issue:** `parseColor()` accepts only hex and `rgb()/rgba()` with numeric channels. The values these findings need are outside that grammar: the computed `color` of `text-[oklch(45%_0.14_25)]` is serialised in the `oklch()` colour space, and `bg-success/15` computes to an alpha-bearing `color-mix()` result — both throw `unsupported colour`. So the natural next test ("the delete label clears 4.5:1") throws instead of asserting, and an author may be tempted to skip it.
**Fix:** Resolve the colour through the browser instead of re-implementing colour science in Node:

```js
// in a Playwright helper
const resolved = await locator.evaluate((el) => {
  const c = document.createElement("canvas").getContext("2d")
  c.fillStyle = getComputedStyle(el).color
  return c.fillStyle // normalised to #rrggbb / rgba()
})
```

or extend `parseColor` with `oklch()/oklab()/color()` plus percentage channels.

### IN-03: `G-7`'s `worst >= 4.829` floor is a change-detector, not a contrast gate

**File:** `tests/unit/test_semantic_token_coverage.js:274-280`
**Issue:** The value is recomputed from the same declarations it is guarding, so it only trips on a token edit larger than the 0.001 margin; the loop above already enforces 4.5. It reads as an independent safety margin but cannot catch a drift to e.g. `#DC2625`.
**Fix:** Either drop it, or pin the fact it actually means — `assert.equal(dark.get('--color-danger-solid'), '#DC2626')` — so the intent ("this hex must not move") is explicit.

### IN-04: `issue_url` is rendered as a link without validating its scheme or origin

**File:** `web/src/pages/AdminDigestPage.jsx:444`, `:775`
**Issue:** `setIssueUrl(typeof result.issue_url === 'string' ? result.issue_url : '')` and `<Link to={issueUrl}>` accept any string the API returns. React Router prevents the default action for plain left clicks, but `ctrl`/middle-click would follow a `javascript:` URL (or an off-site URL presented as an internal «К выпуску →» link) if the response is ever attacker-influenced.
**Fix:** Reject anything that is not a same-origin path, like `sanitizeReturnUrl` already does for `returnUrl`:

```js
const nextUrl = result.issue_url
setIssueUrl(typeof nextUrl === 'string' && nextUrl.startsWith('/') ? nextUrl : '')
```

### IN-05: `.sr-only` is re-declared although Tailwind v4 already ships it

**File:** `web/src/index.css:93-105`
**Issue:** `@layer utilities .sr-only {…}` duplicates Tailwind's built-in `sr-only` with identical declarations. It is dead weight in the single-source token layer this phase is consolidating, and it makes the one behaviour the new `admin-chrome.spec.js:91-95` assertion depends on (a 1px-wide accessible h1) depend on a hand-written copy rather than the framework default.
**Fix:** Remove the local copy and re-run `-g "naming:"` to confirm `boundingBox().width <= 1` still holds; if it must stay, say in the comment why the framework utility is overridden.

---

_Reviewed: 2026-10-21T13:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
