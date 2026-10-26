# Phase 2 — UI Review

**Audited:** 2026-09-20
**Baseline:** `02-UI-SPEC.md` (approved design contract)
**Screenshots:** not captured — Vite responds on `:5173`, but Playwright Chromium is not installed (`npx playwright install` required); MCP browser also lacks Chrome. Audit is **code + UI-SPEC** evidence.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Load-failure splash omits visible «Ошибочка вышла»; archive H1 is «Архив» not «Архив выпусков» |
| 2. Visuals | 2/4 | IssueToc always renders dek `<p>` (empty rows leave blank space); archive cards over-compose vs issue-cover contract |
| 3. Color | 2/4 | Accent leaks onto archive card borders; callout fill hardcoded; Retry uses filled `bg-accent` outside reserved text-CTA pattern |
| 4. Typography | 2/4 | IBM Plex Mono never loaded; widespread `font-medium` (500) vs locked 400/600; role size mismatches |
| 5. Spacing | 3/4 | Tailwind 4px scale mostly respected; empty-state lacks `--space-10` block padding; reading/TOC widths drift from tokens |
| 6. Experience Design | 3/4 | Strong loading / soft-404 / splash separation; Retry lacks spinner; archive loading is not a card-skeleton grid |

**Overall: 14/24**

---

## Top 3 Priority Fixes

1. **ServiceUnavailable missing contract heading + spinner** — Users see art + body only; UI-SPEC requires heading **«Ошибочка вышла»** and disabled+spinner on **«Повторить»**. — Add `<h1 class="font-display …">Ошибочка вышла</h1>` above the body; replace busy label `Загрузка…` with a visible spinner (keep `disabled` + `aria-busy`).
2. **IssueToc always paints dek line** — Empty dek still mounts `<p>` (`IssueToc.jsx:22`), violating D-36 / UI-SPEC “dek line below (hidden if empty)” and looking like broken meta. — Conditionally render `{item.dek?.trim() ? <p>…</p> : null}`.
3. **Archive title + accent border** — H1 reads **«Архив»** (should be **«Архив выпусков»**); cards use `hover:border-accent`, which is not on the accent reserved list. — Rename H1; change hover to `hover:bg-paper-2` / `border-rule` (or callout surface), matching issue-cover muted secondary.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)

**WARNING — Load-failure heading absent**
- UI-SPEC Copywriting: heading **«Ошибочка вышла»** + body «Не удалось загрузить…» + **«Повторить»**.
- `ServiceUnavailable.jsx:33-43` renders body + button only. The phrase exists only in image `alt` (`Котёнок: ошибочка вышла`), not as visible page copy. Art may contain “Упс”, but the contract heading is missing from the DOM.

**WARNING — Archive page title**
- Contract: H1 **«Архив выпусков»**.
- `ArchivePage.jsx:52` → `Архив`.

**WARNING — Material byline minutes copy**
- Contract: `~{N} мин`.
- `MaterialPage.jsx:169` → `~${…} мин чтения` (extra word; drifts from locked byline template).

**PASS — Core Russian editorial strings**
- Empty issue «Выпуск готовится» + «В архив →» — `IssuePage.jsx:141-148`
- Soft issue 404 «Выпуск не найден» + «К текущему выпуску →» — `IssuePage.jsx:118-128`
- Soft material 404 «Материал не найден» + back-nav — `MaterialPage.jsx:116-129`
- Empty archive «Архив пуст» + CTA — `ArchivePage.jsx:65-70`
- Callout open/closed copy + «Выбрать тему →» — `IssuePage.jsx:172-182`
- Archive backlink «← К текущему выпуску» — `ArchivePage.jsx:48`
- No HTTP codes / stacktraces in ServiceUnavailable (D-23) — PASS

**Minor:** Busy retry label `Загрузка…` (`ServiceUnavailable.jsx:43`) is not in the copy contract (contract expects spinner, not alternate CTA text).

---

### Pillar 2: Visuals (2/4)

**WARNING — IssueToc empty dek still occupies layout**
- Spec: dek line hidden when empty; populated rows: mono position · display title · meta · `→`.
- `IssueToc.jsx:8-22` always renders `<p className="…">{item.dek}</p>`. Empty string still creates vertical gap under every row without dek.

**WARNING — Archive card composition**
- Spec `issue-cover`: overline `Выпуск №{n}`, **H2 period**, caption `{N} материалов`.
- `ArchivePage.jsx:83-92` adds a third text block `{issue.title}` between period and count, and uses generic `rounded-xl border` cards rather than the locked cover rhythm. Hierarchy competes (period H2 vs title line).

**WARNING — Error splash hierarchy**
- Without a display/H1 «Ошибочка вышла», the failure state’s primary verbal focal point is absent; art + muted body alone under-signal the friendly error tone the contract designed around the splash caption.

**PASS**
- Typography-only issue hero (no cover image) — `IssuePage.jsx:160-168`
- EditorialCallout only when `isCurrent` + cycle present — `IssuePage.jsx:154-183`
- Material: «Статья» badge + format overline — `MaterialPage.jsx:145-155`
- Material section TOC: mobile `<details>` + desktop sticky `nav` — `MaterialPage.jsx:39-53`
- AppShell «Архив» between «Выпуск» and «База» — `AppShell.jsx:60-68`
- Touch targets `min-h-11` on most primary links/nav — generally present

---

### Pillar 3: Color (2/4)

**Accent reserved-list audit (UI-SPEC § Color)**

| Allowed use | Present? |
|-------------|----------|
| Prose/meta text links `text-accent` | Yes (material TOC, back-nav, CTAs) |
| Active nav + brand wordmark | Yes (`AppShell.jsx:13,53`) |
| Primary/ghost CTA **text** | Partial — text CTAs OK; Retry is **filled** `bg-accent` |
| IssueToc hover title + callout surface | Hardcoded oklch hover, not token |
| Tag-pill `text-accent` | Yes (`MaterialPage.jsx:199`) |
| EditorialCallout open = voting border | Yes (`border-voting`) |

**WARNING — Accent leakage**
- `ArchivePage.jsx:81` `hover:border-accent` — accent on decorative border; **not** in reserved list. Prefer secondary surface hover (`hover:bg-paper-2` / callout fill).

**WARNING — Hardcoded callout fill**
- Open callout: `bg-[oklch(94%_0.025_278)]` (`EditorialCallout.jsx:10`) — matches `--color-bg-callout` in `design-frontend/styles/tokens.css` but is **not** mirrored in SPA `@theme` (`web/src/index.css`), so the SPA cannot use a named utility.
- IssueToc hover uses the same raw oklch (`IssueToc.jsx:11`).

**WARNING — Retry as filled accent button**
- `ServiceUnavailable.jsx:38` `bg-accent text-accent-ink` — reserved list emphasizes **text** CTAs for primary actions; filled accent elevates accent share beyond 10% on the failure surface.

**PASS**
- Dominant paper / ink / muted / rule usage on reader pages.
- Closed callout muted via `border-rule bg-paper-2 text-ink-2` — aligns with closed-state assumption.
- Soft 404s use ink/display, not danger red panic UI.

---

### Pillar 4: Typography (2/4)

**WARNING — Mono family not loaded**
- UI-SPEC: `IBM Plex Mono` for IssueToc position numbers.
- `web/src/index.css:1` Google Fonts import loads Bricolage + IBM Plex Sans only. `--font-mono` names IBM Plex Mono (`index.css:17`) but the face never downloads → Consolas/system fallback for `font-mono` rows (`IssueToc.jsx:13`).

**WARNING — Weight contract (400 / 600 only)**
- Phase UI-SPEC: weights limited to **400** and **600**; 500 not primary.
- Widespread `font-medium` (500): empty/soft CTAs (`IssuePage.jsx:125,146`), EditorialCallout CTA area patterns, Material TOC summary (`MaterialPage.jsx:42`), Archive empty CTA (`ArchivePage.jsx:68`), PlatformProofBanner strong (`PlatformProofBanner.jsx:70`).

**WARNING — Role size mismatches**
| Role (spec) | Expected | Implemented |
|-------------|----------|-------------|
| Archive card title (H2) | `--text-h2` (~text-2xl clamp) | `text-xl` (`ArchivePage.jsx:86`) |
| Dek / body-sm | `--text-body-sm` (~15px / text-sm) | Material dek `text-lg` (`MaterialPage.jsx:160`) |
| Overline tracking | `letter-spacing: 0.08em` | `tracking-wide` (~0.025em) on issue/archive overlines |

**PASS**
- Display titles use `font-display` + large semibold sizes on issue/material heroes.
- Caption / overline uppercase muted pattern present.
- Body stack IBM Plex Sans is loaded.

---

### Pillar 5: Spacing (3/4)

**PASS — Scale alignment (common utilities)**
- `mt-3` / `gap-4` / `p-5` / `my-8` / `mb-6` / `py-10` map to 12 / 16 / 20 / 32 / 24 / 40px — consistent with locked 4px rem scale.

**WARNING — Empty-state block padding**
- Spec: empty-state uses `--space-10` (40px) block padding.
- Empty issue / archive / soft-404 sections rely on margin only (`mt-3`/`mt-6`), no `p-10` / equivalent empty-state wrapper.

**WARNING — Container token drift**
- Material prose: `max-w-3xl` (48rem) vs `--container-reading` **42.5rem** (`MaterialPage.jsx:183`).
- Desktop TOC: `w-56` (14rem) vs `--toc-width` **15rem** (`MaterialPage.jsx:48`).
- Splash: `max-w-[360px]` / `sm:max-w-[420px]` — matches UI-SPEC image cap (acceptable arbitrary).

**WARNING — Touch target gap**
- Empty-issue CTA «В архив →» (`IssuePage.jsx:146`) lacks `min-h-11` (soft-404 and archive CTAs mostly include it).
- Material footer back-nav links (`MaterialPage.jsx:223-227`) are `text-sm` without `min-h-11`.

**Minor:** Archive loading skeleton is two pulse bars (`ArchivePage.jsx:55-58`), not a **card skeleton grid** (UI Considerations E2 loading).

---

### Pillar 6: Experience Design (3/4)

**PASS — State coverage (strong)**
| Surface | Loading | Empty | Soft 404 | Network error |
|---------|---------|-------|----------|---------------|
| Issue | skeleton `issue-loading` | «Выпуск готовится» | «Выпуск не найден» | `ServiceUnavailable` |
| Archive | skeleton | «Архив пуст» | n/a | `ServiceUnavailable` |
| Material | skeleton | n/a (dismissed) | «Материал не найден» (no splash) | `ServiceUnavailable` |
| Callout | arrives with issue; hidden if no cycle | — | — | page-level error |

- Soft NOT_FOUND never uses `bad_gateway.png` — PASS (D-22/D-39).
- Retry clears fail harness + remounts via `loadKey` — PASS (`IssuePage` / `ArchivePage` / `MaterialPage`).
- Material honesty: empty dek / tags / related omitted — PASS (`MaterialPage.jsx:158-220`).
- EditorialCallout gated to current issue — PASS (D-34).
- `role="alert"` on splash — PASS.

**WARNING — Retry busy affordance**
- Spec E5: disabled **+ spinner** during in-flight retry.
- Implementation: `disabled` + text swap to `Загрузка…` — no spinner (`ServiceUnavailable.jsx:36-43`).

**WARNING — IssueToc partial/empty dek**
- E1 partial: “Per-row dek hidden when empty” — not implemented (see Visuals / IssueToc).

**WARNING — Archive loading shape**
- E2 loading expects card skeleton grid distinct from empty; current bars can be confused with a thin content stub under the persistent backlink + H1 (H1 remains visible during load — good — but skeleton fidelity is low).

**Backstops (UI-SPEC 🧪) — not verified visually this audit**
- Long TOC overflow, Russian plural (code has `materialCountLabel` — property looks correct, visual backstop still open), long titles, nav mobile reflow. Flagged for `/gsd-verify-work`, not scored as PASS.

---

## Registry Safety

Registry audit: **skipped** — `components.json` absent; UI-SPEC declares `shadcn_initialized: false` / no third-party registries.

---

## Files Audited

- `.planning/phases/02-issue-materials-archive/02-UI-SPEC.md`
- `.planning/phases/02-issue-materials-archive/02-CONTEXT.md`
- `.planning/phases/02-issue-materials-archive/02-0{1-6}-SUMMARY.md` (plans skimmed via summaries)
- `web/src/pages/IssuePage.jsx`
- `web/src/pages/ArchivePage.jsx`
- `web/src/pages/MaterialPage.jsx`
- `web/src/pages/ProfilePage.jsx` (stub; out of phase shape)
- `web/src/components/AppShell.jsx`
- `web/src/components/EditorialCallout.jsx`
- `web/src/components/IssueToc.jsx`
- `web/src/components/ServiceUnavailable.jsx`
- `web/src/components/PlatformProofBanner.jsx`
- `web/src/components/ErrorPanel.jsx`
- `web/src/services/contentApi.js` (error code paths)
- `web/src/App.jsx`
- `web/src/index.css`
- `design-frontend/styles/tokens.css` (token cross-check)
- `web/public/bad_gateway.png` (asset present)

---

## Recommendation Count

- Priority fixes: **3**
- Additional WARNING findings: **11**
- Backstop / verify-held-out items: **10** (from UI-SPEC; not visually confirmed)
