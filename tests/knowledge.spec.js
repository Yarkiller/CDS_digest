const { expect, test } = require("@playwright/test");

/**
 * Phase 4 knowledge honesty gate (KNOW-01…04) under VITE_USE_MOCKS.
 * No tag/format/topic selects — role chips only (D-62…D-65).
 */
test.describe("knowledge honesty (KNOW-01…04)", () => {
  test("Submit and Enter run search; whitespace shows Введите запрос without hits", async ({
    page,
  }) => {
    await page.goto("/knowledge");

    await expect(page.locator("select")).toHaveCount(0);
    await expect(page.getByLabel(/теги|формат|тема/i)).toHaveCount(0);

    const search = page.getByRole("searchbox", { name: /поиск по базе знаний/i });
    await search.fill("RAG");
    await page.getByRole("button", { name: "Найти", exact: true }).click();
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();
    // KNOW-01 / D-59: never render numeric score badges on hits.
    await expect(page.getByText(/\bscore\b|\bрейтинг\b|\d+\.\d{2,}/i)).toHaveCount(0);

    await page.goto("/knowledge");
    await search.fill("RAG");
    await search.press("Enter");
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();

    await page.goto("/knowledge");
    await search.fill("   ");
    await page.getByRole("button", { name: "Найти", exact: true }).click();
    await expect(page.getByTestId("kb-inline-error")).toHaveText(/Введите запрос/i);
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toHaveCount(0);
  });

  test("DS chip filters and opens a material by slug (KNOW-02/03)", async ({ page }) => {
    await page.goto("/knowledge");

    const search = page.getByRole("searchbox", { name: /поиск по базе знаний/i });
    await search.fill("RAG");
    // D-64: chip change re-runs search without «Найти».
    await page.getByRole("button", { name: "DS", exact: true }).click();
    const rag = page.getByRole("link", { name: /building production rag systems/i });
    await expect(rag).toBeVisible();
    await rag.click();
    await expect(page).toHaveURL(/\/materials\/rag-systems/);
  });

  test("Analyst zero-hit keeps query on Сбросить фильтр (KNOW-04)", async ({ page }) => {
    await page.goto("/knowledge");

    const search = page.getByRole("searchbox", { name: /поиск по базе знаний/i });
    await search.fill("RAG");
    await page.getByRole("button", { name: "Analyst", exact: true }).click();
    await expect(page.getByRole("heading", { name: /ничего не нашли/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toHaveCount(0);
    await expect(search).toHaveValue("RAG");

    await page.getByRole("button", { name: "Сбросить фильтр", exact: true }).click();
    await expect(search).toHaveValue("RAG");
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /ничего не нашли/i })).toHaveCount(0);
  });
});
