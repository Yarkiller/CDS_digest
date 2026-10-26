# Phase 3 — UI Review

**Audited:** 2026-09-20
**Baseline:** `03-UI-SPEC.md` (approved 2026-09-20)
**Screenshots:** captured to `.planning/ui-reviews/03-20260920-215439/` (mocks Vite `:5174` ballot; live `:5173` redirected to `/login` without session)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Contract CTAs/status/empty/closed strings present; extra non-contract prose + strip plural locked as «голосов» |
| 2. Visuals | 3/4 | Clear ballot hierarchy and muted leader strip; sticky footer competes with last rows on mobile |
| 3. Color | 2/4 | Voting orange CTA/progress correct, but empty-state link uses reserved violet `text-accent` |
| 4. Typography | 2/4 | Empty-state heading uses undeclared `text-2xl`; new `font-medium` on empty CTA |
| 5. Spacing | 3/4 | Mostly 4px-scale + declared `p-5`/`min-h-11`; undeclared 12px (`gap-3`/`mb-3`/`py-3`) cluster |
| 6. Experience Design | 3/4 | Strong state matrix (empty/closed/toast/409/ErrorPanel/splash); persistent «Выберите тему» + sticky occlusion |

**Overall: 16/24**

---

## Top 3 Priority Fixes

1. **Empty-state CTA uses reserved violet accent** — reads as primary brand action and breaks Color 60/30/10 accent reserve (UI-SPEC: violet only for selected radio) — In `VotingPage.jsx` `EmptyVotingCta`, replace `text-accent` with `text-ink` / `text-ink-2` + underline hover (keep `→` glyph).
2. **Empty heading `text-2xl` is outside the typography contract** — invents a fifth size role and weakens Display/Heading discipline — Change «Темы ещё не объявлены» to `text-lg font-display font-semibold` (Heading role) or reuse Display `text-3xl` only if it must compete with the page H1.
3. **Leader strip ignores RU plural helper** — «31 голосов» / «1 голосов» fights zero-one-many honesty already shipped in row meta via `voteCountLabel` — Update `leaderStripText` in `voting.js` to interpolate `voteCountLabel(votes)` (and adjust Playwright strip assertion accordingly).

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**WARNING — contract extras / plural strip**

Matches UI-SPEC Copywriting Contract (verified in source + mocks screenshots):

| Element | Spec | Implemented |
|---------|------|-------------|
| Page heading | «Голосование за тему разбора» | `VotingPage.jsx:256,264` |
| Never-voted status | «голос не отдан» | `voting.js:34`; visible in desktop/mobile ballot shots |
| Primary CTA | «Подтвердить голос» / «Изменить голос» / «Сохраняем…» | `voting.js:41–45` |
| Empty submit | «Выберите тему» | `VotingPage.jsx:180,358` (also shown whenever `!selectedId`) |
| Toasts | «Голос сохранён» / «Голос изменён» | `VotingPage.jsx:198` |
| Leader single/tie | D-40/D-42 templates | `voting.js:10–22` |
| Empty / no cycle | D-49/D-50 | `VotingPage.jsx:268,275` |
| Closed banner | «Цикл голосования закрыт» | `VotingPage.jsx:288` |
| Submit error title | «Ошибка сохранения» | `VotingPage.jsx:237` |
| GET splash body | ServiceUnavailable fixed copy | `ServiceUnavailable.jsx:34` |
| Materials / tallies | `materialCountLabel` / `voteCountLabel` incl. «0 материалов» | `TopicBallot.jsx:36`; `ruCount.js` |

Findings:

- **WARNING:** Empty CTA renders «К выпуску →» (`VotingPage.jsx:68`) vs locked «К выпуску». Glyph `→` is allowed by Design System, but the arrow is not in the copy table.
- **WARNING:** Non-contract body copy: «Когда редакция откроет темы…» (`VotingPage.jsx:276`), «Результаты цикла (только чтение).» (`:328`), pre-confirm «Выбор: «…» (нажмите «Подтвердить голос»)» (`voting.js:32`), multi-device conflict prose (`VotingPage.jsx:227–228`). Useful, but not in the contract — risk of drift.
- **WARNING:** `leaderStripText` hardcodes «голосов» / «голосов каждый» (`voting.js:14,22`) while UI Considerations require zero-one-many for голос*. Row meta already uses `voteCountLabel` correctly (screenshot: «31 голос», «24 голоса», «18 голосов»).
- **Pass:** No row «Лидирует» badge (`TopicBallot.jsx` has no leading tag). No generic English Submit/OK/Cancel on the ballot surface.

### Pillar 2: Visuals (3/4)

**WARNING — sticky footer vs ballot focus**

- **Pass:** Page H1 is the clear title; cycle strip → instructional line → muted leader strip → radio list → sticky confirm forms a readable stack (desktop + mobile ballot screenshots).
- **Pass:** C3-02 honesty: leader lives on `bg-paper-2` (`VotingPage.jsx:334`), selected row uses violet tint + filled `border-accent bg-accent` radio (`TopicBallot.jsx:19,26`) — personal choice ≠ leader strip.
- **Pass:** Radios are full-row buttons with `role="radio"` / `radiogroup` aria-label «Темы для голосования» (`TopicBallot.jsx:5–14`). Error dismiss uses `aria-label` (`ErrorPanel.jsx:17`).
- **WARNING:** Sticky confirm bar (`VotingPage.jsx:355`) + always-visible «Выберите тему» sits on top of the last ballot rows on mobile (mobile screenshot) — weakens focal clarity the UI-SPEC checker already flagged as non-blocking.
- **WARNING:** Unselected radio visual is a small `size-5` circle; touch target relies on full-row `py-5` rather than explicit `min-h-11` on the control class list (likely ≥44px in practice, but not declared).

### Pillar 3: Color (2/4)

**WARNING — accent reserve leak on empty CTA**

60/30/10 against UI-SPEC Color:

| Role | Spec | Evidence |
|------|------|----------|
| Dominant paper | `bg-paper` | AppShell + page |
| Secondary | `bg-paper-2` / callout oklch(98.5% 0.009 95) | Closed/conflict/leader strips; cycle strip `VotingPage.jsx:302` |
| Accent violet | selected radio only | `TopicBallot.jsx:19,26` ✓; **also** `EmptyVotingCta` `text-accent` ✗ (`VotingPage.jsx:66`) |
| Voting orange | CTA + progress | `ActionButton` `bg-voting`; progress `bg-voting` (`VotingPage.jsx:309`) ✓ |

Findings:

- **WARNING / primary score driver:** `EmptyVotingCta` applies `text-accent` to «К выпуску →» — violet accent used for a navigation affordance outside the reserved selected-radio set.
- **WARNING:** GET-failure path reuses `ServiceUnavailable` retry with `bg-accent` (`ServiceUnavailable.jsx:38`) — violet primary on a voting surface where action accent should be voting orange. Inherited Phase 2 chrome, still a contract miss when shown from `/voting`.
- **Pass:** Leader strip never uses accent fill (honesty guard).
- **Pass:** Inline red/green oklch for validation/toast/ErrorPanel matches “existing literals” exception (`VotingPage.jsx:357,376`).
- Hardcoded callout / progress track / unselected border oklch values mirror UI-SPEC secondary notes — acceptable, but they are not tokenized (`bg-paper-2` / a named track token would be cleaner).

### Pillar 4: Typography (2/4)

**WARNING — undeclared size + weight**

Contract roles: Display `text-3xl` / Heading `text-lg` / Body `text-sm` / Label `text-xs` + weights 400/600 (ActionButton 500 inherited only).

| Usage | Classes | Verdict |
|-------|---------|---------|
| Page H1 | `text-3xl font-semibold font-display` | Pass |
| Topic titles | `text-lg font-semibold font-display` | Pass |
| Body / status | `text-sm` | Pass |
| Cycle labels | `text-xs uppercase tracking-wide` | Pass |
| Empty H2 | `text-2xl font-semibold font-display` (`VotingPage.jsx:275`) | **Fail — not in contract** |
| Empty CTA | `font-medium` (`VotingPage.jsx:66`) | **Fail — new 500 outside ActionButton** |
| ErrorPanel title | `text-base font-semibold` (`ErrorPanel.jsx:9`) | Inherited; still undeclared on voting error path |

Fonts Bricolage / IBM Plex load via `web/src/index.css` — Pass.

### Pillar 5: Spacing (3/4)

**WARNING — undeclared 12px cluster**

- **Pass:** Declared rhythm appears: `mb-6`, `mb-8`, `mt-8`, `gap-4` (ballot grid), `p-5` on cycle/leader/closed surfaces (explicit UI-SPEC exception), `min-h-11` on ActionButton / empty CTA / ErrorPanel dismiss.
- **WARNING:** `mb-3`, `gap-3`, `mt-3`, sticky `py-3` introduce **12px** spacing not listed in the Spacing Scale table (xs4 / sm8 / md16 / lg24 / xl32 / …).
- **Pass:** No fixed-height clamps or `truncate` / `line-clamp` on topic titles, dek, leader strip, or status — long-text backstops look open (`TopicBallot.jsx`, `VotingPage.jsx`).
- Ballot row `py-5` reuses the 20px exception intended for card padding; visually fine, but it is the exception applied beyond the named surfaces.

### Pillar 6: Experience Design (3/4)

**WARNING — always-on validation + mobile sticky cover**

State coverage vs UI Considerations:

| State | Spec | Implementation |
|-------|------|----------------|
| Empty open 0 topics | D-49 | `noTopics` branch + «К выпуску» |
| No cycle | D-50 | `noCycle` branch; not fake closed |
| Closed | D-48 | Banner; radios `disabled`; confirm omitted |
| CTA loading | «Сохраняем…» disabled | `voteButtonLabel` + ActionButton |
| Initial GET pending | neutral | «Загрузка…» (`VotingPage.jsx:314,396–399`) |
| POST error | ErrorPanel + Retry | `VotingPage.jsx:361–371`; selection kept |
| GET failure | ServiceUnavailable splash | `VotingPage.jsx:253–259` |
| Toast fade ~3–5s | D-45 | `TOAST_DISMISS_MS = 4000` |
| Conflict adopt | D-54 | `role="alert"` banner + snapshot apply |
| Closed mid-submit | D-51 | `CYCLE_CLOSED` → apply ballot, flip read-only |
| D-47 disabled | selection === confirmed | `confirmDisabled` |
| Zero materials | VOTE-04 | «0 материалов» in screenshot + `ruCount` |

Findings:

- **WARNING:** «Выберите тему» is shown whenever ready && !selectedId (`VotingPage.jsx:356–359`), not only after a blocked submit — correct copy, noisy empty-idle chrome.
- **WARNING:** Sticky footer can cover the last radio row on short viewports (mobile screenshot) — overflow backstop partially unmet for “many topics” / last-row reach.
- **Pass:** No idle tally polling found in `VotingPage.jsx`.
- **Pass:** Destructive confirm dialog correctly absent (toast-only change).

---

## Files Audited

- `.planning/phases/03-voting-cycle/03-UI-SPEC.md` (baseline)
- `.planning/phases/03-voting-cycle/03-CONTEXT.md`
- `.planning/phases/03-voting-cycle/03-0{1..6}-SUMMARY.md`, `03-0{1..6}-PLAN.md`
- `web/src/pages/VotingPage.jsx`
- `web/src/components/TopicBallot.jsx`
- `web/src/utils/voting.js`
- `web/src/utils/ruCount.js`
- `web/src/components/ActionButton.jsx`
- `web/src/components/ErrorPanel.jsx`
- `web/src/components/ServiceUnavailable.jsx`
- `web/src/components/AppShell.jsx` (chrome / accent context)
- `web/src/services/votingApi.js` (error copy surfaces)
- `web/src/index.css` (tokens / fonts)
- `tests/web-app.spec.js` (copy assertions cross-check)
- Screenshots: `.planning/ui-reviews/03-20260920-215439/desktop-voting-ballot.png`, `mobile-voting-ballot.png`, `tablet-voting-ballot.png` (+ unauthenticated login captures from live `:5173`)

**Registry audit:** skipped — UI-SPEC `shadcn_initialized: false`; no `components.json`; Registry Safety table is `none / not applicable`.
