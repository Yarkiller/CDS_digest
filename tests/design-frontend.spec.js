const { expect, test } = require("@playwright/test");

test("loads the Concept 2 gallery from design-frontend root", async ({ page }) => {
  await page.goto("/design-frontend/index.html");

  await expect(page.getByRole("heading", { name: "Digest CDS — Gamified Dark UI" })).toBeVisible();
  await expect(page.locator('a[href="pages/home.html"]')).toBeVisible();
  await expect(page.locator('a[href="pages/leaderboard.html"]')).toBeVisible();
});

test("defaults to dark theme on the home page", async ({ page }) => {
  await page.goto("/design-frontend/pages/home.html");

  const html = page.locator("html");
  await expect(html).not.toHaveAttribute("data-theme", "light");

  const bodyBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  expect(bodyBg).toBe("rgb(11, 15, 23)");
});

test("shows XP bar, streak pill and rank chip in the header", async ({ page }) => {
  await page.goto("/design-frontend/pages/home.html");

  const gamification = page.locator(".header__gamification");
  await expect(gamification).toBeVisible();
  await expect(gamification.locator(".xp-widget")).toBeVisible();
  await expect(gamification.locator(".streak-pill")).toContainText("12");
  await expect(gamification.locator(".rank-chip")).toContainText("#8");
});

test("toggles light theme and persists the choice", async ({ page }) => {
  await page.goto("/design-frontend/pages/home.html");

  const toggle = page.locator("[data-theme-toggle]").first();
  await expect(toggle).toBeVisible();

  await expect(page.locator("html")).not.toHaveAttribute("data-theme", "light");

  await toggle.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("dismisses the quest banner and keeps it hidden after reload", async ({ page }) => {
  await page.goto("/design-frontend/pages/home.html");

  const banner = page.locator("#quest-banner");
  await expect(banner).toBeVisible();

  await page.locator("[data-quest-dismiss]").click();
  await expect(banner).toHaveClass(/hidden/);

  await page.reload();
  await expect(banner).toBeHidden();
});

test("renders the leaderboard page with public ranking", async ({ page }) => {
  await page.goto("/design-frontend/pages/leaderboard.html");

  await expect(page.getByRole("heading", { name: /лидерборд/i })).toBeVisible();
  await expect(page.locator(".leaderboard-table")).toBeVisible();
  await expect(page.locator(".leaderboard-row--self")).toContainText("Ivan P.");
  await expect(page.locator(".rank-num--1")).toBeVisible();
});

test("renders quiz card with progress dots and score ring", async ({ page }) => {
  await page.goto("/design-frontend/pages/quiz.html");

  await expect(page.locator(".progress-dots")).toBeVisible();
  await expect(page.locator(".progress-dot--current")).toBeVisible();
  await expect(page.locator(".score-ring")).toBeVisible();
  await expect(page.locator(".quiz-answer").filter({ hasText: "Комбинация векторного и полнотекстового поиска" })).toBeVisible();
});

test("renders material page with quiz prompt", async ({ page }) => {
  await page.goto("/design-frontend/pages/material.html");

  await expect(page.locator(".quiz-prompt")).toBeVisible();
  await expect(page.getByRole("link", { name: /начать/i })).toBeVisible();
  await expect(page.locator(".material-hero")).toBeVisible();
});

test("reserves intrinsic space for cover images", async ({ page }) => {
  for (const path of ["/design-frontend/pages/material.html", "/design-frontend/pages/home.html"]) {
    await page.goto(path);

    const images = page.locator('img[src*="/assets/covers/"]');
    await expect(images).not.toHaveCount(0);
    const dimensions = await images.evaluateAll((elements) =>
      elements.map((image) => ({
        width: image.getAttribute("width"),
        height: image.getAttribute("height"),
      }))
    );

    expect(dimensions).toEqual(dimensions.map(() => ({ width: "480", height: "270" })));
  }
});

