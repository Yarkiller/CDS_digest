# Phase 5 — UI Review

**Audited:** 2026-09-22
**Baseline:** `05-UI-SPEC.md` (approved 2026-09-21T16:13:00+03:00)
**Screenshots:** live pass on `http://127.0.0.1:5173/admin/digest` (admin session, Vite). Playwright MCP could not start (Chrome binary missing); measurements used the Cursor browser at 1280×800 and the embedded 377×371 pane.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Locked CTAs mostly match; mutation/send errors omit contract «Повторить» |
| 2. Visuals | 2/4 | Digest editors sit above shortlist, burying the rank-1 focal row |
| 3. Color | 2/4 | Success/draft hues hardcoded as arbitrary `oklch(...)`; `--color-success` absent from SPA `@theme` |
| 4. Typography | 2/4 | Widespread new `font-medium` (500) + extra `text-xl` beyond contract roles |
| 5. Spacing | 3/4 | Mostly rem-scale utilities; a few arbitrary sizes (`min-h-28`, `max-w-[12rem]`) |
| 6. Experience Design | 2/4 | Send gate/rest/403 solid; recovery CTAs and item-preview a11y incomplete |

**Overall: 13/24**

---

## Top 3 Priority Fixes

1. **Add «Повторить» to decision toast and send-failure banner** — Admins cannot recover via the contracted retry CTA after «Не сохранено» / «Рассылка не отправлена»; they must rediscover the failed action. — Wire toast/banner actions that re-call `applyDecision` / `confirmSend` (or reopen confirm) and match UI-SPEC §2.7 copy pairs.
2. **Stop hardcoding success/draft OKLCH; mirror semantic tokens into `web/src/index.css`** — Accent discipline looks OK, but success send CTA and badges invent colors outside `@theme`, so theme swaps and 60/30/10 audits cannot hold. — Add `--color-success` (and draft/voting tint) to `@theme`; replace `bg-[oklch(45%_0.13_155)]` / badge arbitrary classes with `bg-success` / token-backed badge utilities (or port `.status-badge--ready|draft`).
3. **Restore shortlist as the primary focal stack** — Two large editor cards render before ≤5 rows, so rank-1 + sticky send (UI-SPEC Focal Points) lose hierarchy on typical viewports. — Move «Контекст» / «Схема» below the shortlist (or collapse them), so toolbar → rows → editors → sticky footer matches the contracted focal order.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)

**What matches the contract (positive evidence):**
- Overline / H1: «Админ» / «Shortlist дайджеста» — `AdminDigestPage.jsx:412-413`
- Toolbar: «Выбрать все», «Оставить топ-3», «Одобрить выбранные», «Отклонить выбранные» — `:450-478`
- Send / preview: «Отправить дайджест →», «Предпросмотр письма» — `:682-690`
- Hints: «Сначала откройте превью письма.», draft/empty/ready hints — `:221-230`
- Empty D-80: «Кандидатов пока нет» / «Обновите список позже.» / «Обновить список» — no «пайплайн» — `:435-443`
- Rest G-05-2: «дайджест успешно выпущен» + countdown days — `:423-426`
- 403: ForbiddenPage «Недостаточно прав» / «На выпуск» — `ForbiddenPage.jsx:13-21`
- Confirm: «Подтвердите отправку» / «Не отправлять» / stub honesty body — `AdminDigestPage.jsx:809-832`
- Modal titles + close `aria-label="Закрыть"` — `:716-725`, `:745-754`, `:809-818`
- Factors honesty «обоснование недоступно» — `factorText()` `:68-71`
- Decision captions «одобрен» / «отклонён» — `:62-65`
- Email caption «только одобренные ready» — `:775`

**WARNING — missing «Повторить» on mutation failure:**
UI-SPEC Copywriting: Toast **«Не сохранено» + «Повторить»**. Implementation only sets toast text — no retry control (`:276`, toast render `:697-704`).

**WARNING — missing «Повторить» on send failure:**
Contract: Banner **«Рассылка не отправлена» + «Повторить»**. Banner string only (`:363`, `:661-672`); no retry button (unlike email preview error which correctly has «Повторить» at `:761-771`).

**WARNING — item preview incomplete copy chrome:**
Contract: status overline + title + dek. Modal shows title + dek fallback only (`:728-731`) — no ready/draft overline.

**Minor:** Editor extras («Добавить текст», «Удалить», interstitial placeholder) are gap-closure additions (05-07/08) not listed in the original copy table — tone is fine; not scored as failures.

**Live — missing page dek:** Contract copy «Неделя {week_label} · до 5 кандидатов» is absent. At 1280×800 the block under the H1 goes straight to the toolbar. `needs_human_review: true` only for whether a week label exists in this batch; the dek line itself is not rendered.

**Live — item preview:** Modal title «Превью материала», material title, fallback «Краткое описание недоступно.» No ready/draft overline. Close control is `✕` with `aria-label="Закрыть"`.

**Live — email preview copy matches:** Caption «только одобренные ready». Body lists only the two approved-ready titles (draft and unapproved rows excluded). After close, hint becomes «Превью просмотрено. Можно отправить.» Overline paints as «АДМИН» (uppercase). `needs_human_review: true` — whether all-caps is the locked overline style or a copy drift from «Админ».

### Pillar 2: Visuals (2/4)

**WARNING — focal hierarchy inverted vs Focal Points table:**
Contract primary focal for populated `/admin/digest`: **Shortlist rank-1 row + sticky send**. Implemented order is toolbar → **full digest editor grid** (`:482-580`) → shortlist (`:582-638`). On 1440×900 / mobile heights, rank-1 is pushed well below the first viewport.

**WARNING — design-system row chrome not reused:**
UI-SPEC asks to prefer `.admin-row`, `.status-badge`, `.sticky-footer`, `.btn--success` patterns from `design-frontend`. SPA reimplements with ad-hoc Tailwind grids and arbitrary badge pills (`:590-616`, `:684-686`) instead of shared badge/row classes — visual continuity with the prototype is weaker (no mini-thumb, no status-badge tint language).

**Positive:** Sticky footer stacks `flex-col` on narrow (`:647`); 44px `min-h-11` targets on toolbar/checkboxes/modals; glyph closes with accessible names; rest panel is calm and distinct from D-80 empty.

**Minor:** Reorder controls use `↑`/`↓` (outside the declared glyph set `→ ← ✕ ⌕`) but expose `aria-label` — acceptable a11y, slight convention drift.

**Live layout (1280×800):** H1 top 137px. «Контекст дайджеста» and «Схема дайджеста» share top 293px (side-by-side cards) and sit above the shortlist. Rank-1 row top is 625px, so it is inside an 800px viewport but below the editor band. Primary focal is still the editors, not rank-1 + sticky send.

**Live layout (377×371):** Rank-1 document top is 1209px against a 371px viewport (scroll height 3771px). On a short pane the contracted focal row is several viewports down. Sticky send is what remains on screen.

### Pillar 3: Color (2/4)

**Accent reservation (mostly OK):**
- Accent used for empty CTA, material preview link, email retry, 403 CTA, AppShell active nav + wordmark — matches reserved list.
- Toolbar stays ghost/secondary borders — matches prototype default.
- Disabled send uses `opacity-45` + `cursor-not-allowed` — matches contract.

**WARNING — success not in SPA theme; hardcoded everywhere:**
`web/src/index.css` `@theme` has paper/ink/accent/voting but **no `--color-success` / danger**. Admin page hardcodes success as `bg-[oklch(45%_0.13_155)]` and `text-[oklch(45%_0.13_155)]` (`:662`, `:686`, `:836`) — same hue as tokens.css success, but not token-backed. Grep of `web/src` finds **zero** `bg-success` / `--color-success` usages.

**WARNING — draft/ready badges invent non-token fills:**
Ready: `bg-[oklch(92%_0.04_155)] text-[oklch(35%_0.1_155)]`; draft: `bg-[oklch(93%_0.05_50)] text-[oklch(45%_0.12_38)]` (`:610-612`). Contract reserves `--color-voting` for `status-badge--draft` and success tint for ready — not these custom pairs.

**Count of arbitrary color utilities in AdminDigestPage:** 6 distinct `oklch(...)` class literals (badges ×4 channel pairs + banner + send/confirm fills).

**Live computed colors:**
- `:root` tokens match the contract for paper `oklch(97% 0.012 95)`, ink, accent `oklch(52% 0.13 278)`, voting `oklch(62% 0.14 38)`. `--color-success` computes empty.
- Ready badge: background `oklch(0.92 0.04 155)`, text `oklch(0.35 0.1 155)`, weight 500, 12px, padding 2px 8px, radius 6px.
- Draft badge: background `oklch(0.93 0.05 50)`, text `oklch(0.45 0.12 38)` — not `--color-voting`.
- Disabled send: fill `oklch(0.45 0.13 155)` (success hue as a literal), opacity `0.45`, `cursor: not-allowed`, min-height 44px. Opacity matches the disabled rule; the fill is not `var(--color-success)`.
- Active «Админ» nav: accent fill, paper text, min-height 44px, weight 400.

### Pillar 4: Typography (2/4)

**Contract roles present:**
| Role | Expected | Observed |
|------|----------|----------|
| Heading | `text-3xl` / 600 | H1 + empty/rest headings `:413`, `:423`, `:435` |
| Subhead | `text-2xl` / 600 | Editor + modal titles `:484`, `:716`, `:745`, `:809` |
| Body | `text-sm`–`text-base` / 400 | Banners, hints, confirm body |
| Label | `text-xs` / 600 | Overline «Админ» with `font-semibold` |

**WARNING — weight 500 proliferates in new markup:**
Contract: weights **400 + 600**; `font-medium` only as inherited badge/row-title exception. New admin UI applies `font-medium` to toolbar buttons, empty CTA, badges, row titles, send CTA, confirm primary, banner (`:439`, `:452`, `:605`, `:609`, `:686`, etc.) — introduces a third weight across most controls.

**WARNING — extra size `text-xl`:**
Email preview subject uses `font-display text-xl font-semibold` (`:776`) — outside the four primary roles (Heading/Subhead/Body/Label). Prefer `text-2xl` Subhead or body+display emphasis without a fifth size.

**Positive:** H1 uses `font-sans` (not Display) per contract; rank/score use `font-mono`.

**Live type metrics (1280×800):**
- H1: IBM Plex Sans, 30px / 600 / line-height 36px (1.2). Contract heading is `text-3xl` with clamp 2→3rem (32–48px) and line-height 1.1. Computed size is Tailwind’s default `text-3xl` (30px), not that clamp.
- Editor and modal H2: 24px / 600 / line-height 32px. Subhead floor (1.5rem) matches; line-height 1.33 vs contract 1.2.
- Email subject «Digest CDS — превью (2026-09-22)»: Bricolage Grotesque, 20px / 600. Display family matches the email-title exception; 20px is the extra `text-xl` size. `needs_human_review: true` for whether that display title feels on-brand.

### Pillar 5: Spacing (3/4)

**Aligned with declared scale (examples):**
- Overline→H1 `mt-2` (8px / `--space-2`)
- Toolbar `gap-2`, row `gap-3` / `p-4` (`--space-3` / `--space-4`)
- Editor cards `p-5` (`--space-5`), empty/rest `py-10` (`--space-10`)
- Modal panel `p-6` (`--space-6` / near `--space-8` on wide)
- Page `pb-32` clears sticky footer; container `max-w-6xl` matches `--container-wide` intent
- Modal `z-[400]` matches `--z-modal`

**WARNING — arbitrary values:**
- Factor column `max-w-[12rem]` (`:624`)
- Context textarea `min-h-28` (`:488`) — 7rem, not on spacing scale
- Text block `min-h-20` (`:529`)
- Toast `bottom-24` positioning

Not severe enough for a 2 — rhythm is generally consistent and touch targets meet 44px.

**Live spacing:**
- H1 margin-top 8px (`--space-2`). Main padding 40px 16px (`py-10` / `px-4`). Section `pb-32` (128px) clears the sticky footer.
- Email modal overlay `z-index: 400`, panel background paper, padding **24px** (`p-6` / `--space-6`), width 512px. Contract wide-viewport modal padding is `--space-8` (32px).
- Close control is 44×44. Toolbar and send min-heights are 44px.
- Desktop sticky footer is `flex-direction: row`. The narrow pane stacks the footer (screenshot), which matches the mobile column rule.

### Pillar 6: Experience Design (2/4)

**Covered (matches Interaction State Machine):**
- Role gate → Forbidden vs triage (`:372-382`)
- Loading without empty flash (`:394-401`)
- GET fail → `ServiceUnavailable` + «Повторить» (`:384-390`)
- Checkbox ops local; Approve/Reject persist; disabled when none checked (`:233-234`, `:262-279`)
- Email preview fingerprint invalidation (`:184-188`, `:212-219`)
- Send unlock conditions; confirm dialog; ALREADY_SENT / success → `restMode` hides triage (`:404-406`, `:335-369`, `:418-427`)
- Preview fail keeps send locked + «Повторить» (`:759-771`)
- Draft-in-pool hint lists draft titles (`:652-659`)

**WARNING — recovery incomplete (UI Considerations error E2/E3):**
Decision fail: toast only, no «Повторить». Send fail: banner only, no «Повторить». Selection is preserved on send fail (good), but contract explicitly pairs copy with retry.

**WARNING — item preview interaction gaps:**
- No status overline (partial E6 content).
- Close does not restore focus to the triggering row (Page & Component Contracts: «closing returns focus to the row») — `setPreviewItem(null)` only (`:723`).

**Minor:** No focus trap / Escape documented as required; sticky footer remains in rest with disabled CTAs (acceptable for locked «Уже отправлено» hint).

**Live interaction (populated triage only):**
- «Админ» is in the shell and `current` for this admin session.
- Five rows render. Approve/Reject stay disabled until a checkbox is checked.
- «Предпросмотр письма» opens a modal, lists the approved∩ready pair, and unlocks send. Hint switches to «Превью просмотрено. Можно отправить.» Send drops `disabled`.
- Item preview opens over the list. While it was open, the triggering «Превью материала» stayed `focused`. Closing-returns-focus was not rechecked after dismiss.
- Not exercised live: 403, empty D-80, post-send rest, confirm dialog, «Не сохранено» / «Рассылка не отправлена» retry. Those stay code-only.
- Email body shows the same two titles as a dash list and again as a numbered list. `needs_human_review: true` — schema blocks vs article list, or a duplicate.

---

## Files Audited

- `.planning/phases/05-admin-digest-publish/05-UI-SPEC.md` (baseline)
- `.planning/phases/05-admin-digest-publish/05-CONTEXT.md`
- `.planning/phases/05-admin-digest-publish/05-0{1..9}-SUMMARY.md` + corresponding PLAN headers
- `web/src/pages/AdminDigestPage.jsx`
- `web/src/pages/ForbiddenPage.jsx`
- `web/src/components/AppShell.jsx`
- `web/src/components/ServiceUnavailable.jsx`
- `web/src/App.jsx` (route `/admin/digest`)
- `web/src/index.css` (`@theme` tokens)
- `design-frontend/pages/admin-digest.html` + `design-frontend/styles/components.css` (prototype chrome comparison)
- `components.json` — absent (`NO_SHADCN`); Registry Safety gate skipped (UI-SPEC Registry Safety: not applicable)

---

## Automated visual pass

Cursor browser against the running Vite app. Scores above are unchanged: live checks confirm the code findings and add the dek gap, the 30px H1, and 24px modal padding.

| Surface | Result |
|---------|--------|
| `/admin/digest` populated, 1280×800 | Editors above shortlist; rank-1 at y=625 (in view, not the focal band) |
| Same page, 377×371 | Rank-1 at y=1209; sticky send occupies the pane |
| Email preview modal | z-index 400, paper panel, 24px padding, approved-ready list only, 44px close |
| Item preview modal | Title + fallback dek; no status overline |
| Disabled send | opacity 0.45, `not-allowed`, success hue as a literal |
| Enabled send after preview | `disabled` cleared; hint «Превью просмотрено. Можно отправить.» |

**needs_human_review:**
- Uppercase overline «АДМИН» vs contract «Админ»
- Email subject in Bricolage Grotesque at 20px
- Repeated titles inside the email preview (schema vs body)
