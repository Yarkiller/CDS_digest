const { expect, test } = require("@playwright/test");

const { contrastRatio, blendOver } = require("./helpers/contrast");

/**
 * Admin chrome acceptance spec (PIPEUI-01…04, THEME-01/02).
 *
 * One home for the criterion-by-criterion checks that need BOTH the role harness
 * (tests/admin.spec.js) and the pre-load theme fixture (tests/web-app.spec.js). Kept in a
 * separate file so the naming/contrast criteria stay readable and each one can be run by
 * `-g "<title prefix>"`.
 */

const THEME_KEY = "digest-cds-theme";

/**
 * Role + theme before first load (Shared Pattern 1 + 2).
 *
 * The theme must be written before the document runs, because ThemeToggle reads the key in
 * an effect. Dark is set explicitly with removeItem instead of trusting the default: a
 * previous test may have left the light key behind.
 */
async function gotoAdmin(page, path, theme) {
  await page.addInitScript(
    ({ themeKey, light }) => {
      window.__DIGEST_MOCK_ME_ROLE__ = "admin";
      if (light) localStorage.setItem(themeKey, "light");
      else localStorage.removeItem(themeKey);
    },
    { themeKey: THEME_KEY, light: theme === "light" },
  );
  await page.goto(path);
  // Reset module-level admin mocks between tests (Vite keeps singleton state).
  await page.waitForFunction(() => Boolean(window.__DIGEST_ADMIN_HARNESS__));
  await page.evaluate(() => window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness());
  await page.reload();
  // The ingest block owns a second store; without its reset the «Тип» control can arrive in
  // whatever state the previous case left behind.
  if (path.startsWith("/admin/pipeline")) await resetIngestSourcesMock(page);
  await page.evaluate(() => document.fonts.ready);
  // WR-04: `ThemeToggle` writes `data-theme` in an effect (`ThemeToggle.jsx:8-18`), so the
  // attribute lands one commit after the document. Without this wait every light-theme
  // assertion below can read a dark value and "pass" for the wrong reason. `?? 'dark'` is
  // load-bearing: the dark theme is the ABSENCE of the attribute, so a bare comparison with
  // 'dark' would never resolve and the test would hang until timeout.
  //
  // A page that mounts no toggle has no attribute to await — the auth shell is the only such
  // surface, and its cases apply the theme explicitly with `forceTheme`.
  await page.waitForFunction(() => document.getElementById("root")?.childElementCount > 0);
  const mountsToggle = await page.evaluate(
    () => document.querySelector('[data-testid="theme-toggle"]') !== null,
  );
  if (mountsToggle) {
    await page.waitForFunction(
      (expected) => (document.documentElement.dataset.theme ?? "dark") === expected,
      theme,
    );
  }
}

/**
 * Shared Pattern 1 — the ingest-sources harness reset, contract identical to
 * tests/admin.spec.js:1815-1824.
 */
async function resetIngestSourcesMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGEST_SOURCES_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesMockStore();
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingest-sources-section")).toBeVisible();
}

/**
 * Shared Pattern 3 — the computed pair crosses into the Node context as plain strings, so
 * the WCAG formula lives in exactly one place (tests/helpers/contrast.js) and is never
 * duplicated inside the browser.
 */
function stylePair(locator) {
  return locator.evaluate((el) => {
    const cs = getComputedStyle(el);
    return { color: cs.color, background: cs.backgroundColor, fontSize: cs.fontSize };
  });
}

/**
 * Shared Pattern 4 — token-exact class comparison. `bg-primary` is a substring of
 * `bg-primary-solid`, so a regex over the raw attribute would pass vacuously.
 */
async function classTokens(locator) {
  return (await locator.getAttribute("class")).split(/\s+/).filter(Boolean);
}

/**
 * The translucent tint's alpha, read from the pill's own class list. A status pill is
 * `bg-success/15 text-success-ink` or `bg-voting/20 text-voting-ink-on-tint`; the `/N` is
 * the composite strength `blendOver` needs. Reading it from the class — not a constant —
 * keeps the e2e measurement honest when the class drifts (GAP-25-6 / T-25-32).
 */
function pillAlpha(tokens, label) {
  const match = tokens
    .map((token) => /^(?:[\w-]+:)?bg-(success|voting|danger)\/(\d{1,3})$/.exec(token))
    .find((result) => result !== null);
  if (!match) {
    throw new Error(
      `${label} pill must carry a bg-(success|voting|danger)/<alpha> class, got: ${tokens.join(" ")}`,
    );
  }
  return Number(match[2]) / 100;
}

/**
 * A link's own label colour plus the first opaque surface behind it.
 *
 * A text link paints no fill, so `stylePair(link).background` is always `rgba(0, 0, 0, 0)`
 * and `contrastRatio` refuses it by design. Walking up to the first ancestor with an opaque
 * `background-color` is the surface the label actually sits on (the `bg-paper` card for the
 * retry actions, the `bg-bg-app` dialog for the preview link).
 */
function paintedPair(locator) {
  return locator.evaluate((el) => {
    const color = getComputedStyle(el).color;
    let node = el;
    let background = "rgba(0, 0, 0, 0)";
    while (node && background === "rgba(0, 0, 0, 0)") {
      background = getComputedStyle(node).backgroundColor;
      node = node.parentElement;
    }
    return { color, background };
  });
}

/**
 * Shared Pattern 5 — wait for the theme the fixture asked for.
 *
 * The theme key is read by `ThemeToggle` in an effect, so `data-theme` lands one commit
 * after the document (WR-04). Each new case waits for the attribute instead of reading a
 * dark-theme style under a light-theme expectation; `gotoAdmin` itself is untouched.
 */
async function waitForTheme(page, theme) {
  await page.waitForFunction(
    (expected) => (document.documentElement.getAttribute("data-theme") ?? "dark") === expected,
    theme,
  );
}

/**
 * Shared Pattern 5b — apply the theme on a page that mounts no `ThemeToggle`.
 *
 * The auth shell (`web/src/pages/LoginPage.jsx`) renders no toggle, so the attribute
 * `ThemeToggle` writes in its effect never appears on `/login` and `waitForTheme` cannot
 * settle. Write the attribute exactly as `ThemeToggle` does (`ThemeToggle.jsx:12-15`) —
 * `index.css` overrides `[data-theme="light"]` for the whole document — and then wait for
 * it so the computed style is read after the cascade updated.
 */
async function forceTheme(page, theme) {
  await page.evaluate((expected) => {
    if (expected === "light") document.documentElement.setAttribute("data-theme", "light");
    else document.documentElement.removeAttribute("data-theme");
  }, theme);
  await waitForTheme(page, theme);
}

/** The three computed colours a surface can be judged by (colour, fill, top edge). */
function styleTriple(locator) {
  return locator.evaluate((el) => {
    const cs = getComputedStyle(el);
    return {
      color: cs.color,
      backgroundColor: cs.backgroundColor,
      borderTopColor: cs.borderTopColor,
    };
  });
}

/**
 * A token as the browser resolved it. Tailwind v4 compiles `bg-success/15` to
 * `color-mix(in oklab, …)`, and Chrome serializes that as `oklab(… / 0.15)` — a form
 * `parseColor` deliberately refuses. Reading the tint token plus the declared alpha keeps
 * the composite arithmetic in `blendOver` instead of duplicating an oklab parser.
 */
async function cssToken(page, name) {
  return page.evaluate(
    (token) => getComputedStyle(document.documentElement).getPropertyValue(token).trim(),
    name,
  );
}

test("naming: the section reads Настройка on all three surfaces and the URL is unchanged", async ({
  page,
}) => {
  await gotoAdmin(page, "/admin/pipeline", "dark");

  // 1. The in-page section tab is renamed.
  const pipelineTab = page.getByTestId("admin-tab-pipeline");
  await expect(pipelineTab).toHaveText("Настройка");

  // 2. Renamed, but not duplicated and not lost.
  await expect(pipelineTab).toHaveCount(1);

  // 3. The sr-only h1 is renamed, stays the only h1, and stays visually hidden (IN-01).
  const sectionHeading = page.getByRole("heading", { level: 1 });
  await expect(sectionHeading).toHaveCount(1);
  await expect(sectionHeading).toHaveText("Настройка");
  const headingBox = await sectionHeading.boundingBox();
  expect(headingBox).not.toBeNull();
  expect(headingBox.width).toBeLessThanOrEqual(1);

  // 4. The mobile select: option texts renamed, the selected value is still the route.
  const sectionSelect = page.getByTestId("admin-section-select");
  expect(await sectionSelect.locator("option").allTextContents()).toEqual([
    "Дайджест",
    "Настройка",
  ]);
  expect(await sectionSelect.inputValue()).toBe("/admin/pipeline");

  // 5. The route is untouched — only the label moved (T-25-01).
  expect(page.url().endsWith("/admin/pipeline")).toBe(true);

  // 6. The sibling surface still reads its own name.
  await expect(page.getByTestId("admin-tab-digest")).toHaveText("Дайджест");

  // 7-8. The navigation contract survives the rename: no aria-label was rewritten.
  await expect(page.getByTestId("admin-section-nav")).toHaveAttribute(
    "aria-label",
    "Разделы админки",
  );
  await expect(sectionSelect).toHaveAttribute("aria-label", "Разделы админки");
});

test("chrome: tab scale, gap and top space; no eyebrow; Источники heading", async ({ page }) => {
  await gotoAdmin(page, "/admin/pipeline", "dark");

  // The five facts below are the criterion-5 baseline; `expect.soft` reports them together so a
  // single RED run names every measured regression instead of stopping at the first one. A soft
  // failure still fails the test — this changes reporting, not the gate.
  //
  // 1. PIPEUI-04 — the «Админ» eyebrow left the DOM. Assert the DOM string, not the rendered
  // uppercased glyphs: `uppercase` made the eyebrow *look* like «АДМИН».
  const adminNodes = page.getByText("Админ", { exact: true });
  await expect.soft(adminNodes).toHaveCount(1);
  const shellAdminLink = page
    .getByRole("navigation", { name: /основная навигация/i })
    .getByRole("link", { name: "Админ", exact: true });
  await expect(shellAdminLink).toHaveCount(1);
  const soleNodeIsShellLink = await adminNodes
    .first()
    .evaluate((el, shellEl) => el === shellEl, await shellAdminLink.elementHandle());
  expect.soft(soleNodeIsShellLink).toBe(true);

  // 2. PIPEUI-04 — the tab reads at the content h2 scale, not one step above it.
  const tabStyle = await stylePair(page.getByTestId("admin-tab-pipeline"));
  const headingStyle = await stylePair(page.getByTestId("ingest-sources-heading"));
  expect.soft(tabStyle.fontSize).toBe(headingStyle.fontSize);
  expect.soft(tabStyle.fontSize).toBe("24px");
  expect.soft(headingStyle.fontSize).toBe("24px");

  // 3. PIPEUI-04 — the tab gap widens from 8px to 16px.
  const navMetrics = await page.getByTestId("admin-section-nav").evaluate((el) => {
    const cs = getComputedStyle(el);
    return { columnGap: cs.columnGap, marginTop: cs.marginTop };
  });
  expect.soft(navMetrics.columnGap).toBe("16px");
  expect.soft(parseFloat(navMetrics.columnGap)).toBeGreaterThan(8);

  // 4. PIPEUI-04 — no eyebrow + no top margin: the strip sits directly under the shell's py-10.
  expect.soft(navMetrics.marginTop).toBe("0px");
  const mainBox = await page.locator("main").first().boundingBox();
  const navBox = await page.getByTestId("admin-section-nav").boundingBox();
  expect(mainBox).not.toBeNull();
  expect(navBox).not.toBeNull();
  expect.soft(navBox.y - mainBox.y).toBeLessThan(48);

  // 5. PIPEUI-03 — the block heading drops the word «ингеста».
  await expect.soft(page.getByTestId("ingest-sources-heading")).toHaveText("Источники");

  // 6. The navigation contract is not rewritten by the type/spacing move.
  await expect(page.getByTestId("admin-section-nav")).toHaveAttribute(
    "aria-label",
    "Разделы админки",
  );
  await expect(page.getByTestId("admin-tab-digest")).toHaveCount(1);
  await expect(page.getByTestId("admin-tab-pipeline")).toHaveCount(1);
});

test("select legible in both themes", async ({ page }) => {
  // Criterion 2 (PIPEUI-02): the values are the declaration from the UI-SPEC token
  // contract, asserted as *equality*. "Not white" would already pass on the pre-fix tree,
  // where the field is transparent and simply inherits its colour.
  const expected = {
    dark: { color: "rgb(203, 213, 225)", background: "rgb(19, 25, 37)" },
    light: { color: "rgb(51, 65, 85)", background: "rgb(255, 255, 255)" },
  };
  const fields = ["ingest-sources-kind", "ingest-sources-id", "ingest-sources-label"];

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/pipeline", theme);

    for (const testId of fields) {
      const pair = await stylePair(page.getByTestId(testId));

      // Asserted first: this is the measured pre-fix state and the clearest RED message.
      expect(pair.background, `${testId} (${theme}) must paint an opaque surface`).not.toBe(
        "rgba(0, 0, 0, 0)",
      );
      expect(pair.background, `${testId} (${theme}) background`).toBe(expected[theme].background);
      expect(pair.color, `${testId} (${theme}) color`).toBe(expected[theme].color);

      // All three controls carry the same pair — this is what forbids a select-only patch.
      expect(
        contrastRatio(pair.color, pair.background),
        `${testId} (${theme}) contrast`,
      ).toBeGreaterThanOrEqual(4.5);
    }

    // The token must resolve at runtime, not merely exist in the stylesheet text.
    const paperToken = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--color-paper").trim(),
    );
    expect(paperToken, `${theme}: --color-paper must resolve at runtime`).not.toBe("");

    // The option texts are part of criterion 2; the list is not a copy of the control.
    expect(
      await page.getByTestId("ingest-sources-kind").locator("option").allTextContents(),
      `${theme}: option texts`,
    ).toEqual(["Канал", "Плейлист"]);
  }
});

test("theme-independent labels in both themes", async ({ page }) => {
  // Criterion 4 (THEME-01): a label painted on a fill must not flip with the theme. The
  // pair is asserted as an exact value in BOTH themes — "different from before" would pass
  // on a different theme-dependent value.
  const pillFill = { color: "rgb(255, 255, 255)", background: "rgb(124, 58, 237)" };
  const addFill = { color: "rgb(255, 255, 255)", background: "rgb(14, 116, 144)" };
  const votingFill = { color: "rgb(15, 23, 42)", background: "rgb(234, 179, 8)" };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/pipeline", theme);

    // 1. The active shell pill — the surface whose label was grey-on-violet in light theme.
    const pill = page
      .getByRole("navigation", { name: /основная навигация/i })
      .getByRole("link", { name: "Админ", exact: true });
    const pillPair = await stylePair(pill);
    // Asserted first: a transparent fill would make `contrastRatio` meaningless.
    expect(pillPair.background, `pill (${theme}) must paint an opaque fill`).not.toBe(
      "rgba(0, 0, 0, 0)",
    );
    expect(pillPair.color, `pill (${theme}) color`).toBe(pillFill.color);
    expect(pillPair.background, `pill (${theme}) background`).toBe(pillFill.background);
    expect(contrastRatio(pillPair.color, pillPair.background), `pill (${theme}) contrast`)
      .toBeGreaterThanOrEqual(4.5);

    // 2. Token-exact class check: `bg-primary` is a substring of `bg-primary-solid`, so a
    // regex over the raw attribute would stay green with the bare base class left behind.
    const pillTokens = await classTokens(pill);
    expect(pillTokens, `pill (${theme}) tokens`).toContain("bg-primary-solid");
    expect(pillTokens, `pill (${theme}) must not keep the base fill`).not.toContain("bg-primary");

    // 3. The accent CTA (migrated in 25-03) — this row holds it from being reverted.
    const addPair = await stylePair(page.getByTestId("ingest-sources-add"));
    expect(addPair.background, `add CTA (${theme}) must paint an opaque fill`).not.toBe(
      "rgba(0, 0, 0, 0)",
    );
    expect(addPair.color, `add CTA (${theme}) color`).toBe(addFill.color);
    expect(addPair.background, `add CTA (${theme}) background`).toBe(addFill.background);
    expect(contrastRatio(addPair.color, addPair.background), `add CTA (${theme}) contrast`)
      .toBeGreaterThanOrEqual(4.5);

    // 4. `voting` is a POSITIVE assertion of the recorded ROADMAP exception, not a skip:
    // white on #EAB308 measures 1.92 and must fail here.
    await page.goto("/voting");
    const confirm = page.getByTestId("confirm-vote");
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await expect(confirm).toBeEnabled();
    const votingPair = await stylePair(confirm);
    expect(votingPair.background, `voting (${theme}) must paint an opaque fill`).not.toBe(
      "rgba(0, 0, 0, 0)",
    );
    expect(votingPair.color, `voting (${theme}) color`).toBe(votingFill.color);
    expect(votingPair.background, `voting (${theme}) background`).toBe(votingFill.background);
    expect(contrastRatio(votingPair.color, votingPair.background), `voting (${theme}) contrast`)
      .toBeGreaterThanOrEqual(4.5);
  }
});

test("status labels legible in both themes", async ({ page }) => {
  // GAP-25-1 / WR-02: the status pills used the fill token as a label. Measured pre-fix in
  // the light theme: success #22C55E on its own 15% tint = 1.925, voting #EAB308 on 20% =
  // 1.62. The -ink roles are the only legal label and are asserted as exact values.
  const expected = {
    dark: { ready: "rgb(74, 222, 128)", draft: "rgb(253, 230, 138)" },
    light: { ready: "rgb(22, 101, 52)", draft: "rgb(113, 63, 18)" },
  };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/digest", theme);
    await waitForTheme(page, theme);

    const rows = page.getByTestId("admin-shortlist-row");
    // «готов» renders on four of the five mock rows and «черновик» on exactly one, so both
    // locators stay single without a strict-mode violation.
    const readyPill = rows.first().getByText("готов", { exact: true });
    const draftPill = rows
      .filter({ hasText: "черновик" })
      .getByText("черновик", { exact: true });

    await expect(readyPill).toHaveText("готов");
    await expect(draftPill).toHaveText("черновик");

    const readyPair = await styleTriple(readyPill);
    const draftPair = await styleTriple(draftPill);

    expect(readyPair.color, `ready pill (${theme}) color`).toBe(expected[theme].ready);
    expect(draftPair.color, `draft pill (${theme}) color`).toBe(expected[theme].draft);

    // The label sits on a translucent tint over the row, so the ratio is taken on the
    // composite — the same arithmetic G-14 uses statically. The alpha comes from the pill's
    // own class token, so any class drift changes what is measured.
    const rowBackground = (await styleTriple(rows.first())).backgroundColor;
    const successTint = await cssToken(page, "--color-success");
    const votingTint = await cssToken(page, "--color-voting");

    const readyAlpha = pillAlpha(await classTokens(readyPill), "ready");
    const draftAlpha = pillAlpha(await classTokens(draftPill), "draft");

    expect(
      contrastRatio(readyPair.color, blendOver(successTint, rowBackground, readyAlpha)),
      `ready pill (${theme}) contrast on its tint`,
    ).toBeGreaterThanOrEqual(4.5);
    expect(
      contrastRatio(draftPair.color, blendOver(votingTint, rowBackground, draftAlpha)),
      `draft pill (${theme}) contrast on its tint`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("auth field errors legible", async ({ page }) => {
  // GAP-25-1: the auth field errors were `text-danger` (#EF4444) on the white card = 3.763.
  const expected = {
    dark: "rgb(248, 113, 113)",
    light: "rgb(185, 28, 28)",
  };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/login", theme);
    await forceTheme(page, theme);

    await page.getByRole("button", { name: /^Войти$/ }).click();

    // An empty submit renders two alerts — the email field and the password field — so the
    // first one is taken; both share the same role and copy.
    const alert = page.getByRole("alert").first();
    await expect(alert).toHaveText("Заполните поле");

    // The white card is the form's parent; it paints `bg-bg-surface`.
    const cardBackground = await page
      .locator("form")
      .first()
      .evaluate((el) => getComputedStyle(el.parentElement).backgroundColor);

    const alertPair = await styleTriple(alert);
    expect(alertPair.color, `auth field error (${theme}) color`).toBe(expected[theme]);
    expect(
      contrastRatio(alertPair.color, cardBackground),
      `auth field error (${theme}) contrast on the card`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("send banner legible", async ({ page }) => {
  // GAP-25-2: the success banner is a `<p role="status">` inside `admin-send-footer`; its
  // pre-fix label was `text-success` = 2.279 on the light page shell.
  const expected = {
    dark: "rgb(74, 222, 128)",
    light: "rgb(22, 101, 52)",
  };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/digest", theme);
    await waitForTheme(page, theme);

    const rows = page.getByTestId("admin-shortlist-row");
    await rows.first().getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(rows.first().getByText("одобрен")).toBeVisible();

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
    await expect(emailDialog).toHaveCount(0);

    await page.getByRole("button", { name: /отправить дайджест/i }).click();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();

    const banner = page.getByTestId("admin-send-footer").getByRole("status");
    // The exact literal the tree sets (AdminDigestPage.jsx:443), one assertion, one outcome.
    await expect(banner).toContainText("Выпуск опубликован. Доставка писем: stub (0 из 0)");

    const bannerPair = await styleTriple(banner);
    expect(bannerPair.color, `send banner (${theme}) color`).toBe(expected[theme]);

    // The footer paints `bg-bg-app/95` over the page shell, and bg-app at 95% over bg-app is
    // bg-app — so the shell token is the composite the label actually sits on.
    const shell = await cssToken(page, "--color-bg-app");
    expect(
      contrastRatio(bannerPair.color, shell),
      `send banner (${theme}) contrast on the shell`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("failure toast legible", async ({ page }) => {
  // GAP-25-2 / WR-05: the toast painted `bg-text-primary` + `text-text-primary`, i.e. the
  // same themed value twice — 1.00:1 in both themes. It is the only surface that reports a
  // failed shortlist decision, so an invisible toast reads exactly like a silent success.
  const expected = {
    dark: {
      backgroundColor: "rgb(26, 34, 51)",
      color: "rgb(241, 245, 249)",
      borderTopColor: "rgb(42, 53, 72)",
    },
    light: {
      backgroundColor: "rgb(241, 245, 249)",
      color: "rgb(15, 23, 42)",
      borderTopColor: "rgb(203, 213, 225)",
    },
  };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/digest", theme);
    await waitForTheme(page, theme);

    const rows = page.getByTestId("admin-shortlist-row");
    await rows.nth(0).getByRole("checkbox").check();
    await rows.nth(1).getByRole("checkbox").check();
    await page.evaluate(() => window.__DIGEST_ADMIN_HARNESS__.armFailNextDecision());
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();

    const toast = page.getByTestId("admin-toast");
    // A partial failure renders «Не сохранено: <id>», so containment — never equality.
    await expect(toast).toContainText("Не сохранено");

    const toastPair = await styleTriple(toast);
    expect(toastPair.backgroundColor, `toast (${theme}) background`).toBe(
      expected[theme].backgroundColor,
    );
    expect(toastPair.color, `toast (${theme}) color`).toBe(expected[theme].color);
    expect(toastPair.borderTopColor, `toast (${theme}) border`).toBe(
      expected[theme].borderTopColor,
    );
    expect(
      contrastRatio(toastPair.color, toastPair.backgroundColor),
      `toast (${theme}) contrast`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("load-error actions and the preview link are legible in both themes", async ({ page }) => {
  // GAP-25-3 / 25-03 must_have #12: the retry action painted `text-accent` (#06B6D4) =
  // 2.43:1 on the light `paper`, while the message next to it was already `text-ink-2`
  // (10.35 light / 11.85 dark). The fix adds the `accent-text` label role and leaves both the
  // message and the base accent untouched.
  const accent = { dark: "rgb(6, 182, 212)", light: "rgb(14, 116, 144)" };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/pipeline", theme);

    // Only the injectors already in the tree: both blocks read an in-memory mock, so
    // `page.route` has nothing to intercept. `arms` are sessionStorage-backed, so they
    // survive the reload that triggers the load.
    await page.evaluate(() => window.__DIGEST_INGEST_SOURCES_HARNESS__.armFailNextLoad());
    await page.evaluate(() => window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.armFailNextLoad());
    await page.reload();
    await waitForTheme(page, theme);

    const sourcesRetry = page.getByTestId("ingest-sources-load-retry");
    await expect(sourcesRetry).toBeVisible();
    const sourcesPair = await paintedPair(sourcesRetry);
    expect(sourcesPair.color, `sources retry (${theme}) colour`).toBe(accent[theme]);
    expect(
      contrastRatio(sourcesPair.color, sourcesPair.background),
      `sources retry (${theme}) contrast on its card`,
    ).toBeGreaterThanOrEqual(4.5);

    // The sibling message was already legible and must not be traded away for the action.
    const sourcesMessage = sourcesRetry.locator("xpath=..").locator("p").first();
    const sourcesMessagePair = await paintedPair(sourcesMessage);
    expect(
      contrastRatio(sourcesMessagePair.color, sourcesMessagePair.background),
      `sources load error message (${theme}) contrast`,
    ).toBeGreaterThanOrEqual(4.5);

    const scheduleRetry = page.getByTestId("ingestion-schedule-retry");
    await expect(scheduleRetry).toBeVisible();
    const schedulePair = await paintedPair(scheduleRetry);
    expect(schedulePair.color, `schedule retry (${theme}) colour`).toBe(accent[theme]);
    expect(
      contrastRatio(schedulePair.color, schedulePair.background),
      `schedule retry (${theme}) contrast on its card`,
    ).toBeGreaterThanOrEqual(4.5);
  }

  // Third accent label: the preview panel's «Открыть материал →» (AdminDigestPage.jsx:993),
  // which sits on the dialog's `bg-bg-app` rather than on a `paper` card.
  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/digest", theme);

    const row = page
      .getByTestId("admin-shortlist-row")
      .filter({ hasText: "Building Production RAG Systems" });
    await row.getByRole("button", { name: /Превью материала/ }).click();

    const previewLink = page.getByRole("link", { name: /Открыть материал/ });
    await expect(previewLink).toBeVisible();
    const previewPair = await paintedPair(previewLink);
    expect(previewPair.color, `preview link (${theme}) colour`).toBe(accent[theme]);
    expect(
      contrastRatio(previewPair.color, previewPair.background),
      `preview link (${theme}) contrast in the dialog`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("control boundaries clear 3:1 in both themes while the decorative rule does not", async ({
  page,
}) => {
  // GAP-25-4 / 25-03 must_have #10: the field edge was `border-rule` = 1.485:1 on the light
  // `paper`, below WCAG 1.4.11's 3:1 for a UI boundary. The boundary role is #64748B; the
  // decorative rule keeps its own (deliberately lower) contrast and stays on panels.
  const FIELD_BORDER = "rgb(100, 116, 139)";
  const rule = { dark: "rgb(42, 53, 72)", light: "rgb(203, 213, 225)" };
  const fields = ["ingest-sources-kind", "ingest-sources-id", "ingest-sources-label"];

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/admin/pipeline", theme);

    for (const testId of fields) {
      const triplet = await styleTriple(page.getByTestId(testId));

      // Asserted first: a transparent field would make the ratio meaningless.
      expect(
        triplet.backgroundColor,
        `${testId} (${theme}) must paint an opaque field`,
      ).not.toBe("rgba(0, 0, 0, 0)");
      expect(triplet.borderTopColor, `${testId} (${theme}) edge`).toBe(FIELD_BORDER);
      expect(
        contrastRatio(triplet.borderTopColor, triplet.backgroundColor),
        `${testId} (${theme}) boundary contrast`,
      ).toBeGreaterThanOrEqual(3);
    }

    // Negative control inside the same case: the card is still a divider, not a boundary —
    // otherwise "every border became field-border" would pass unnoticed.
    const card = await styleTriple(page.getByTestId("ingest-sources-section"));
    expect(card.borderTopColor, `card edge (${theme}) stays the decorative rule`).toBe(
      rule[theme],
    );
    expect(card.borderTopColor, `card edge (${theme}) is not the field role`).not.toBe(
      FIELD_BORDER,
    );
    expect(
      contrastRatio(card.borderTopColor, card.backgroundColor),
      `card edge (${theme}) must stay below the boundary floor`,
    ).toBeLessThan(3);

    // `sm:hidden`: the select is not rendered at the default viewport, so the read has to
    // happen below the breakpoint — a style declaration is not a rendered edge.
    const viewport = page.viewportSize();
    await page.setViewportSize({ width: 480, height: 900 });
    const narrow = await styleTriple(page.getByTestId("admin-section-select"));
    await page.setViewportSize(viewport);

    expect(narrow.borderTopColor, `mobile section select (${theme}) edge`).toBe(FIELD_BORDER);
    expect(
      contrastRatio(narrow.borderTopColor, narrow.backgroundColor),
      `mobile section select (${theme}) boundary contrast`,
    ).toBeGreaterThanOrEqual(3);
  }
});

test("the vote button paints exactly one fill in every state", async ({ page }) => {
  // WR-03: `variantClass` and `stateClass[state]` were concatenated, so two `bg-*` shared one
  // class list and the state fill only "won" because of stylesheet order. A white label on
  // the yellow `voting` fill measures 1.918, so losing that race is not cosmetic.
  const fills = [
    "bg-voting",
    "bg-primary-solid",
    "bg-danger-solid",
    "bg-success-solid",
    "bg-transparent",
  ];
  const voting = "rgb(234, 179, 8)";
  const danger = "rgb(220, 38, 38)";

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/voting", theme);

    const confirm = page.getByTestId("confirm-vote");
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await expect(confirm).toBeEnabled();

    const idleFills = (await classTokens(confirm)).filter((token) => fills.includes(token));
    expect(idleFills, `idle (${theme}) must paint exactly one fill`).toEqual(["bg-voting"]);

    const idlePair = await styleTriple(confirm);
    expect(idlePair.backgroundColor, `idle (${theme}) fill`).toBe(voting);
    expect(
      contrastRatio(idlePair.color, idlePair.backgroundColor),
      `idle (${theme}) label on the voting fill`,
    ).toBeGreaterThanOrEqual(4.5);

    // The existing failure injector (VotingPage.jsx:132-136): the mock arms the next submit
    // from the query string, so no new mechanism is invented.
    await page.goto("/voting?simulateError=1");
    await waitForTheme(page, theme);

    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    const failing = page.getByTestId("confirm-vote");
    await expect(failing).toBeEnabled();
    await failing.click();
    await expect(failing).toHaveAttribute("data-state", "error");

    const errorFills = (await classTokens(failing)).filter((token) => fills.includes(token));
    expect(errorFills, `error (${theme}) must still paint exactly one fill`).toEqual([
      "bg-danger-solid",
    ]);

    const errorPair = await styleTriple(failing);
    expect(errorPair.backgroundColor, `error (${theme}) fill`).toBe(danger);
    expect(errorPair.backgroundColor, `error (${theme}) keeps the variant fill`).not.toBe(voting);
    expect(
      contrastRatio(errorPair.color, errorPair.backgroundColor),
      `error (${theme}) label on the danger fill`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("pipeline retry actions are legible in both themes", async ({ page }) => {
  // GAP-25-5 / WR-07: the pipeline retry links painted `text-primary` (#8B5CF6) — 4.047 on the
  // light `bg-app` for pipeline-config-retry and 3.566 / 4.186 on the save-retry's `bg-danger/10`
  // — below the 4.5:1 floor. The fix adds the `--color-primary-text` label role; both links are
  // asserted by their *computed* colour in both themes.
  //
  // The save-retry sits on `bg-danger/10`, which Tailwind compiles to a `color-mix` that Chrome
  // serializes as `oklab(… / 0.1)` — a form `parseColor` refuses. So the background is assembled
  // from tokens (`blendOver(--color-danger, --color-bg-app, 0.1)`) exactly as G-14 does, instead
  // of reading the DOM. The 600ms `UI_LATENCY_MS` window is not a race here: `toBeVisible()`
  // polls until the button mounts and it never unmounts, so no `data-state` wait is needed.
  for (const theme of ["dark", "light"]) {
    // Branch A — the load-error retry on the bare page shell.
    await gotoAdmin(page, "/admin/pipeline", theme);
    await page.evaluate(() => window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armFailNextLoad());
    await page.reload();
    await waitForTheme(page, theme);

    const retry = page.getByTestId("pipeline-config-retry");
    await expect(retry).toBeVisible();
    expect(await classTokens(retry)).toContain("text-primary-text");
    expect(await classTokens(retry)).not.toContain("text-primary");
    expect(await cssToken(page, "--color-primary-text")).toBe(
      theme === "light" ? "#6D28D9" : "#A78BFA",
    );
    const pair = await paintedPair(retry);
    expect(pair.color, `retry (${theme}) colour`).toBe(
      theme === "light" ? "rgb(109, 40, 217)" : "rgb(167, 139, 250)",
    );
    expect(
      contrastRatio(pair.color, pair.background),
      `retry (${theme}) contrast on the shell`,
    ).toBeGreaterThanOrEqual(4.5);

    // Branch B — the save-failure retry on the `bg-danger/10` panel. `armFailNextLoad` is
    // sticky (sessionStorage-backed, never cleared by the fetch), so reset it before the next
    // `gotoAdmin` or its internal reload lands on the same error state and the editor never
    // mounts (GAP-25-5 retry is one-shot, but the load arm is not).
    await page.evaluate(() => window.__DIGEST_PIPELINE_CONFIG_HARNESS__.resetPipelineConfigHarness());
    await gotoAdmin(page, "/admin/pipeline", theme);
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n");
    await page.evaluate(() => window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armFailNextSave());
    await page.getByTestId("pipeline-config-save").click();

    const saveRetry = page.getByTestId("pipeline-config-save-retry");
    await expect(saveRetry).toBeVisible();
    expect(await classTokens(saveRetry)).toContain("text-primary-text");
    expect(await classTokens(saveRetry)).not.toContain("text-primary");

    const savePair = await styleTriple(saveRetry);
    expect(savePair.color, `save retry (${theme}) colour`).toBe(
      theme === "light" ? "rgb(109, 40, 217)" : "rgb(167, 139, 250)",
    );
    const tintComposite = blendOver(
      await cssToken(page, "--color-danger"),
      await cssToken(page, "--color-bg-app"),
      0.1,
    );
    expect(
      contrastRatio(savePair.color, tintComposite),
      `save retry (${theme}) contrast on the danger tint`,
    ).toBeGreaterThanOrEqual(4.5);
  }
});

test("in-flight vote label keeps its colour and only dims", async ({ page }) => {
  // 25-VERIFICATION.md 25-04 #7: while a vote is in flight, the button label keeps its
  // theme-independent colour and only its opacity changes. ActionButton.jsx:1-7 documents the
  // contract — `stateFill.loading` is empty (so the variant fill survives) and `stateChrome.loading`
  // only adds `cursor-wait opacity-80`. The `:disabled` variant (ActionButton.jsx:54) wins over
  // `opacity-80` / `cursor-wait` by specificity (0-2-0 vs 0-1-0), so the actual opacity is 0.55
  // and the cursor is `not-allowed`, not 0.8 / `wait`.
  const voting = { color: "rgb(15, 23, 42)", background: "rgb(234, 179, 8)" };

  for (const theme of ["dark", "light"]) {
    await gotoAdmin(page, "/voting", theme);

    const confirm = page.getByTestId("confirm-vote");
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await expect(confirm).toBeEnabled();

    // Measure `idle` AFTER choosing a radio — before that the button is `disabled`, so the
    // `disabled:opacity-55` would read 0.55 in the idle sample too.
    const idle = await stylePair(confirm);
    const idleOpacity = await confirm.evaluate((el) => getComputedStyle(el).opacity);
    expect(idleOpacity, `idle opacity (${theme})`).toBe("1");
    expect(idle.color, `idle colour (${theme})`).toBe(voting.color);
    expect(idle.background, `idle background (${theme})`).toBe(voting.background);

    // Neutralize `transition-colors` (150ms) so the measured in-flight colour/fill are the
    // *settled* values, not a mid-transition sample — a re-painted loading state would
    // otherwise read as "unchanged" for the first frames and the mutation proof would be
    // vacuous (25-04 #7).
    await page.addStyleTag({ content: "*, *::before, *::after { transition: none !important; }" });

    await confirm.click();
    await expect(confirm).toHaveAttribute("data-state", "loading");
    await expect(confirm).toHaveText("Сохраняем…");

    const flying = await stylePair(confirm);
    const flyingOpacity = await confirm.evaluate((el) => getComputedStyle(el).opacity);

    // The must_have (25-04 #7): the label keeps its colour, only opacity dims.
    expect(flying.color, `loading colour (${theme})`).toBe(idle.color);
    expect(flying.background, `loading background (${theme})`).toBe(idle.background);
    expect(flying.fontSize, `loading font-size (${theme})`).toBe(idle.fontSize);
    expect(
      contrastRatio(flying.color, flying.background),
      `loading contrast (${theme})`,
    ).toBeGreaterThanOrEqual(4.5);

    // Actual opacity is 0.55, not 0.8: `data-state="loading"` sets `disabled`
    // (ActionButton.jsx:51), so `disabled:opacity-55` (0-2-0) beats `opacity-80` from
    // `stateChrome.loading` (0-1-0) regardless of stylesheet order.
    expect(flyingOpacity, `loading opacity (${theme})`).toBe("0.55");
    expect(
      await confirm.evaluate((el) => getComputedStyle(el).cursor),
      `loading cursor (${theme})`,
    ).toBe("not-allowed");

    await expect(page.getByTestId("vote-toast")).toHaveText("Голос сохранён");
    await expect(confirm).toHaveText("Изменить голос");
  }
});
