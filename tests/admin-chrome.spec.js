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
  const tintAlpha = { success: 0.15, voting: 0.2 };

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
    // composite — the same arithmetic G-14 uses statically.
    const rowBackground = (await styleTriple(rows.first())).backgroundColor;
    const successTint = await cssToken(page, "--color-success");
    const votingTint = await cssToken(page, "--color-voting");

    expect(
      contrastRatio(readyPair.color, blendOver(successTint, rowBackground, tintAlpha.success)),
      `ready pill (${theme}) contrast on its tint`,
    ).toBeGreaterThanOrEqual(4.5);
    expect(
      contrastRatio(draftPair.color, blendOver(votingTint, rowBackground, tintAlpha.voting)),
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
