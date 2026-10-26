# Phase 1 — UI Review

**Audited:** 2026-09-20
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md for this phase)
**Screenshots:** Captured — `.planning/ui-reviews/01-20260920-123150/` (`login` + `register` × desktop 1440×900 / mobile 375×812 / tablet 768×1024). Dev server on `localhost:5173`.

**Scope:** Phase 1 frontend = Auth UX + shell proof (`LoginPage`, `RegisterPage`, `RequireAuth`, `ErrorPanel`, `PlatformProofBanner`, `AppShell`, `authApi`/`meApi`). Pre-existing editorial mock pages (Issue / Material / Voting / Knowledge) are **out of primary scope** except where AppShell / auth gate touches them; those pages are noted only when they affect shell/auth experience scores.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Register reuses «Вход только…» domain copy; password min-length + mailer honesty still missing (UAT deferred) |
| 2. Visuals | 2/4 | Auth cards are clean, but no page task title, no shell «Выйти», identity hidden on mobile |
| 3. Color | 2/4 | Token surfaces OK; field/ErrorPanel danger colors are hardcoded OKLCH outside `@theme` |
| 4. Typography | 3/4 | Auth surface stays within ~4 sizes / 2 weights; brand as `h1` competes with missing task heading |
| 5. Spacing | 3/4 | Consistent `gap-5` / `p-8` / `min-h-11` rhythm; domain help duplicated vertically |
| 6. Experience Design | 2/4 | Loading/Retry/domain gates solid; no logout UI; password/mailer UX gaps; shell errors silent |

**Overall: 14/24**

---

## Top 3 Priority Fixes

1. **Add shell «Выйти» wired to `authApi.signOut`** — Authenticated users have no visible way to end a session (`signOut` exists only in the service; AppShell shows identity without an action). — Place a text button or menu next to `data-testid="shell-identity"` (also show identity or a compact account control on `<md` breakpoints).
2. **Surface GoTrue password min-length (6) on `/register`** — UAT already saw short passwords rejected with no placeholder/helper (`G-01-3-password-hint`). — Add helper/placeholder e.g. «Не менее 6 символов» under «Пароль» on `RegisterPage` (and optionally map CREDENTIALS errors to that hint).
3. **Stop lying about register domain + mailer failures** — `DOMAIN_MESSAGE` on register still says «Вход только с корпоративного домена СВА» (`RegisterPage.jsx:9`); 5xx mailer failures still map to generic NETWORK «Сервис входа временно недоступен» (`authApi.js` signUp path / UAT `G-01-3b-spa-copy`). — Use «Регистрация только…» (or shared «Доступ только…») and map known GoTrue mailer/`unexpected_failure` to honest Russian copy.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)

**WARNING** — Domain gate string is login-specific on the register form:

```9:9:web/src/pages/RegisterPage.jsx
const DOMAIN_MESSAGE = 'Вход только с корпоративного домена СВА'
```

Same constant on `LoginPage.jsx:12` is correct; on register it mislabels the task.

**WARNING** — Password field has no min-length guidance (`RegisterPage.jsx:180–202`). UAT deferred follow-up `G-01-3-password-hint`: rejection below 6 chars is a surprise.

**WARNING** — Deferred honest mailer copy (`G-01-3b-spa-copy`): live `signUp` 500s still become retryable NETWORK with «Сервис входа временно недоступен…» (`authApi.js:144–152`), which hid the real SMTP failure during G-01-3b.

**Positive:** CTAs are specific («Войти», «Зарегистрироваться», «Повторить»), not English generics. Логин helper («любое ненастоящее имя, не ФИО») is clear (`RegisterPage.jsx:134–136`). Empty-field alerts use «Заполните поле» with `role="alert"`. Confirm-without-session copy is honest (`CONFIRM_MESSAGE`, `RegisterPage.jsx:10–11`).

**Out of scope note:** Knowledge empty state «Ничего не нашли» and voting copy were not scored as Phase 1 deliverables.

### Pillar 2: Visuals (2/4)

**Positive (screenshots + code):** Single centered composition; brand «Digest CDS» is the hero signal (`text-3xl font-display text-accent`); primary CTA is full-width pill; mobile/tablet cards remain readable without horizontal overflow. ErrorPanel dismiss has `aria-label="Скрыть сообщение об ошибке"` (`ErrorPanel.jsx:17`).

**WARNING** — Login and register share an identical visual chrome (brand + eyebrow only). There is no page-level «Вход» / «Регистрация» heading, so task identity depends on fields/CTA alone (`LoginPage.jsx:67–70`, `RegisterPage.jsx:84–87`).

**WARNING / near-BLOCKER for shell UX** — No logout control in `AppShell` despite `signOut` in `authApi.js:85–90`. Plan 01-06 SUMMARY already flagged this as a known gap.

**WARNING** — Shell identity is `hidden … md:block` (`AppShell.jsx:71–78`), so mobile authenticated users never see who they are in the chrome (only PlatformProofBanner on Issue when mounted).

**WARNING** — Accent color on brand wordmark + primary buttons + active nav reduces focal contrast between brand and action (still legible, but hierarchy is soft).

### Pillar 3: Color (2/4)

**Positive:** Auth surfaces use design tokens (`bg-paper`, `bg-paper-2`, `border-rule`, `bg-accent`, `text-accent-ink`) from `index.css` `@theme`. Rough 60/30/10 on auth: paper field, ink/muted type, accent CTAs.

**WARNING** — Field errors hardcode danger without a token:

```117:118:web/src/pages/LoginPage.jsx
              <p className="mt-1 text-sm text-[oklch(45%_0.14_25)]" role="alert">
```

Same pattern on Register (multiple lines). `ErrorPanel` likewise uses inline `oklch(...)` for border/bg/text/hover (`ErrorPanel.jsx:5–16`) instead of e.g. `--color-danger` / `--color-danger-bg`.

**WARNING** — Accent (~hue 278 purple) is the established editorial token, but on auth it paints both decorative brand title and every primary action — accent count on auth unique elements: brand title, primary submit, retry button, AppShell active nav ≈ 4 intentional uses (acceptable) plus brand-as-accent stretches the 10% accent budget.

No `components.json` / shadcn — no third-party registry color drift.

### Pillar 4: Typography (3/4)

**Auth-scope distribution:**

| Role | Classes |
|------|---------|
| Brand | `font-display text-3xl font-semibold` |
| Eyebrow / help | `text-xs` (+ uppercase tracking on eyebrow) |
| Labels / body / CTA | `text-sm` + `font-medium` on labels/CTA |
| Error titles | `font-display text-base font-semibold` |

Weights in auth: `font-medium`, `font-semibold` (2). Sizes: `xs` / `sm` / `base` / `3xl` (4). Font pairing `Bricolage Grotesque` + `IBM Plex Sans` via tokens — good restraint vs abstract “≤4 sizes / ≤2 weights”.

**WARNING** — Using brand as sole `h1` without a secondary task title weakens scannability for screen-reader/document outline (“Digest CDS” vs “Регистрация”). Prefer `h1` brand + visually quieter `h2` for the form task, or keep brand as logo-level and promote task heading.

**Out of scope:** Editorial pages use `text-4xl`/`text-5xl`/`text-2xl`/`text-lg` — more than 4 sizes app-wide; not charged against Phase 1 auth score.

### Pillar 5: Spacing (3/4)

**Auth pattern:** outer `px-4` + card `p-8` + header `mb-8` + form `gap-5` + footer `mt-6`/`mt-3` + control `min-h-11`. Tailwind scale is consistent; no arbitrary `[Npx]` spacing on Login/Register.

**WARNING** — Domain constraint is shown three times on each auth card (placeholder, field help, footer «Доступ:…»), adding vertical noise especially on register mobile (`register-mobile.png`). Consolidate to one persistent helper.

**WARNING** — `RequireAuth` pending state is a lone paragraph with no reserved layout (`RequireAuth.jsx:51–56`), so protected routes can jump when the session check resolves.

### Pillar 6: Experience Design (2/4)

**Positive:**
- Submit `disabled` + «Вход…» / «Регистрация…» loading labels
- Inline field + domain validation before Auth calls
- Retryable `ErrorPanel` + «Повторить» on login/register/network (`LoginPage.jsx:73–89`, `RegisterPage.jsx:90–110`)
- Session gate with returnUrl (`RequireAuth.jsx:59–62`)
- Register empty Логин blocked; confirm-email path stays on page
- `PlatformProofBanner` covers me load error + ping busy/disabled (`PlatformProofBanner.jsx:65–105`)

**WARNING (session lifecycle):** `signOut` has no UI — users cannot log out from the product chrome. Treat as high-priority Phase 1 residual even if UAT passed without it.

**WARNING:** Password policy and mailer failure honesty — see Pillar 1 / UAT Deferred Follow-Ups.

**WARNING:** `PlatformProofBanner` «Повторить» always calls `loadMe()` (`PlatformProofBanner.jsx:76–79`), even when the failed action was `postPing` — ping errors do not get a ping-specific retry.

**WARNING:** `AppShell` swallows `fetchMe` failures into mock identity or empty string (`AppShell.jsx:35–38`) with no user-visible error — identity can silently go blank/wrong after API blips.

**WARNING:** Auth inputs lack explicit `focus-visible` rings (unlike `SearchPill`); keyboard focus relies on browser defaults.

**BLOCKER?** Not scored as pillar-1: flows complete for login/register under autoconfirm. Missing logout is a **WARNING** that blocks clean session management, not first-time register success.

---

## Files Audited

**Planning / contract**
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md`
- `01-01` … `01-08-SUMMARY.md`
- `01-05-PLAN.md`, `01-07-PLAN.md`
- `01-UAT.md` (Deferred Follow-Ups)

**Implementation (Phase 1 FE)**
- `web/src/pages/LoginPage.jsx`
- `web/src/pages/RegisterPage.jsx`
- `web/src/components/RequireAuth.jsx`
- `web/src/components/ErrorPanel.jsx`
- `web/src/components/PlatformProofBanner.jsx`
- `web/src/components/AppShell.jsx`
- `web/src/services/authApi.js`
- `web/src/services/meApi.js`
- `web/src/index.css`
- `web/src/App.jsx`
- `web/src/main.jsx`

**Screenshots**
- `.planning/ui-reviews/01-20260920-123150/login-{desktop,mobile,tablet}.png`
- `.planning/ui-reviews/01-20260920-123150/register-{desktop,mobile,tablet}.png`

**Registry audit:** Skipped — no `components.json` / shadcn (NO_SHADCN).
