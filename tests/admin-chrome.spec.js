const { expect, test } = require("@playwright/test");

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
