const { expect, test } = require("@playwright/test");

/**
 * Phase 4 razbory honesty gate (RAZB-01…04) under VITE_USE_MOCKS.
 */
test.describe("razbory honesty (RAZB-01…04)", () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test("lists chronology with date/status and empty CTA to /voting (RAZB-01)", async ({ page }) => {
    await page.goto("/razbory");

    await expect(page.getByRole("heading", { name: "Разборы", exact: true })).toBeVisible();
    const list = page.getByTestId("razbory-list");
    await expect(list).toBeVisible();
    const items = list.getByTestId("chronology-item");
    await expect(items).toHaveCount(4);
    await expect(items.first()).toContainText(/Анонс/i);
    await expect(items.first()).toContainText(/RAG в корпоративной среде/i);
    // G-04-2: announcement rows must not expose a read CTA
    await expect(items.first().getByRole("link", { name: /Читать разбор/i })).toHaveCount(0);
    await expect(items.first()).toContainText(
      "Разбор этой темы ещё готовится — следите за обновлениями",
    );
    await expect(items.first().getByTestId("chronology-pending")).toBeVisible();

    const published = items.filter({ hasNot: page.getByText(/Анонс/i) }).first();
    await expect(published.getByRole("link", { name: /Читать разбор/i })).toBeVisible();

    await page.addInitScript(() => {
      window.__DIGEST_EMPTY_RAZBORY__ = true;
    });
    await page.goto("/razbory");
    await expect(page.getByTestId("razbory-empty")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Разборов пока нет/i })).toBeVisible();
    const cta = page.getByRole("link", { name: /К голосованию/i });
    await expect(cta).toHaveAttribute("href", "/voting");
    await cta.click();
    await expect(page).toHaveURL(/\/voting/);
  });

  test("sticky TOC jumps to a section on published longread (RAZB-02)", async ({ page }) => {
    await page.goto("/razbory/2");

    await expect(page.getByTestId("razbor-longread")).toBeVisible();
    const toc = page.getByTestId("razbor-toc");
    await expect(toc).toBeVisible();
    const qualityLink = toc.getByRole("link", { name: "Качество", exact: true });
    await expect(qualityLink).toBeVisible();
    await qualityLink.click();
    await expect
      .poll(async () => decodeURIComponent(new URL(page.url()).hash))
      .toBe("#user-content-качество");
    const heading = page.locator("#user-content-качество");
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText(/Качество/i);
  });

  test("dual notebook strip enabled when present and disabled when missing (RAZB-03)", async ({
    page,
  }) => {
    await page.goto("/razbory/2");
    await expect(page.getByTestId("razbor-notebook-strip-top")).toBeVisible();
    await expect(page.getByTestId("razbor-notebook-strip-bottom")).toBeVisible();
    await expect(page.getByTestId("razbor-notebook-download-top")).toBeEnabled();
    await expect(page.getByTestId("razbor-notebook-download-bottom")).toBeEnabled();
    await expect(page.getByTestId("razbor-notebook-pending")).toHaveCount(0);

    await page.goto("/razbory/3");
    await expect(page.getByTestId("razbor-notebook-strip-top")).toBeVisible();
    await expect(page.getByTestId("razbor-notebook-strip-bottom")).toBeVisible();
    await expect(page.getByTestId("razbor-notebook-download-top")).toBeDisabled();
    await expect(page.getByTestId("razbor-notebook-download-bottom")).toBeDisabled();
    await expect(page.getByTestId("razbor-notebook-pending").first()).toHaveText(
      /Notebook скоро будет/i,
    );
  });

  test("Качество vs Обзор labeling and soft 404 (RAZB-04)", async ({ page }) => {
    await page.goto("/razbory/2");
    await expect(page.getByTestId("razbor-quality-label")).toHaveText(/Качество/i);
    await expect(page.getByTestId("razbor-type-badge")).toHaveText(/Разбор/i);

    await page.goto("/razbory/3");
    await expect(page.getByTestId("razbor-quality-label")).toHaveCount(0);
    await expect(page.getByTestId("razbor-type-badge")).toHaveText(/Обзор/i);

    await page.goto("/razbory/99999");
    await expect(page.getByTestId("razbor-not-found")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Разбор не найден/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /К списку разборов/i })).toHaveAttribute(
      "href",
      "/razbory",
    );
  });
});
