const { expect, test } = require("@playwright/test");

/**
 * Concept 2 gamification shell: header widgets (XP / streak / rank / theme) and
 * the public leaderboard page (ADR-0001, UI-SPEC_2 §4.2 / §7.2).
 */
test.describe("Concept 2 gamification shell", () => {
  test("header shows XP, streak and rank widgets on authenticated pages", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("xp-bar")).toBeVisible();
    await expect(page.getByTestId("streak-pill")).toBeVisible();
    await expect(page.getByTestId("rank-chip")).toBeVisible();
  });

  test("rank chip navigates to the leaderboard page", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("rank-chip").click();

    await expect(page).toHaveURL(/\/leaderboard$/);
    await expect(page.getByRole("heading", { name: /лидерборд/i })).toBeVisible();
  });

  test("leaderboard page renders ranked rows with an honest demo caption", async ({ page }) => {
    await page.goto("/leaderboard");

    const rows = page.getByTestId("leaderboard-row");
    await expect(rows.first()).toBeVisible();
    expect(await rows.count()).toBeGreaterThanOrEqual(5);

    // Rank 1 row leads with the top contributor.
    await expect(rows.first()).toContainText("#1");
    // Data is demo seed (gamification is post-v1) — never presented as live.
    await expect(page.getByTestId("leaderboard-note")).toContainText(/демо/i);
  });

  test("theme toggle switches to light and persists across reload", async ({ page }) => {
    await page.goto("/");
    const html = page.locator("html");

    await expect(html).not.toHaveAttribute("data-theme", "light");
    await page.getByTestId("theme-toggle").click();
    await expect(html).toHaveAttribute("data-theme", "light");

    await page.reload();
    await expect(html).toHaveAttribute("data-theme", "light");

    // Back to dark (default) and persisted.
    await page.getByTestId("theme-toggle").click();
    await expect(html).not.toHaveAttribute("data-theme", "light");
  });

  test("profile page surfaces XP, streak and rank stats", async ({ page }) => {
    await page.goto("/profile");

    await expect(page.getByTestId("profile-stats")).toBeVisible();
    await expect(page.getByTestId("profile-stats").getByTestId("xp-bar")).toBeVisible();
    await expect(page.getByTestId("profile-stats").getByTestId("streak-pill")).toBeVisible();
    await expect(page.getByTestId("profile-stats").getByTestId("rank-chip")).toBeVisible();
  });
});
