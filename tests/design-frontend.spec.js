const { expect, test } = require("@playwright/test");

/**
 * Concept 2 canon, release slice (ADR-0009).
 *
 * The prototype documents two things at once: the screens that ship, and the
 * gamification variant that ADR-0007 keeps out of this release. The tests below
 * assert both halves — release screens carry no XP/streak/leaderboard chrome, and
 * the deferred pages still render so the next version has a real reference.
 */

const GAMIFICATION = [
  ".header__gamification",
  ".xp-widget",
  ".streak-pill",
  ".rank-chip",
  ".quest-banner",
  ".profile-stats__xp",
  ".leaderboard-mini__row",
  ".quiz-prompt",
  ".xp-hint",
  ".text-xp",
];

test("gallery lists only release screens", async ({ page }) => {
  await page.goto("/design-frontend/index.html");

  await expect(page.getByRole("heading", { name: "Digest CDS — Concept 2" })).toBeVisible();

  for (const pageHref of ["home.html", "material.html", "voting.html", "login.html"]) {
    await expect(page.locator(`a[href="pages/${pageHref}"]`)).toBeVisible();
  }

  for (const deferred of ["leaderboard.html", "quiz.html", "profile.html", "home-gamified.html"]) {
    await expect(page.locator(`a[href="pages/${deferred}"]`)).toHaveCount(0);
  }
});

test("defaults to the dark theme and persists the light choice", async ({ page }) => {
  await page.goto("/design-frontend/pages/home.html");

  await expect(page.locator("html")).not.toHaveAttribute("data-theme", "light");
  expect(await page.evaluate(() => getComputedStyle(document.body).backgroundColor)).toBe("rgb(11, 15, 23)");

  await page.locator("[data-theme-toggle]").first().click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("release screens carry no gamification chrome", async ({ page }) => {
  for (const releasePage of ["home.html", "material.html", "voting.html"]) {
    await page.goto(`/design-frontend/pages/${releasePage}`);

    for (const selector of GAMIFICATION) {
      await expect(page.locator(selector), `${selector} must not appear on ${releasePage}`).toHaveCount(0);
    }
  }
});

test("material page keeps the hero without a quiz prompt", async ({ page }) => {
  await page.goto("/design-frontend/pages/material.html");

  await expect(page.locator(".material-hero")).toBeVisible();
  await expect(page.locator(".quiz-prompt")).toHaveCount(0);
});

test("keeps the deferred gamification variant renderable for the next version", async ({ page }) => {
  await page.goto("/design-frontend/pages/leaderboard.html");
  await expect(page.locator(".leaderboard-table")).toBeVisible();

  await page.goto("/design-frontend/pages/quiz.html");
  await expect(page.locator(".score-ring")).toBeVisible();

  // The gamified home keeps the quest banner, profile stats and the leaderboard rail.
  await page.goto("/design-frontend/pages/home-gamified.html");
  await expect(page.locator(".header__gamification")).toBeVisible();
  await expect(page.locator("#quest-banner")).toBeVisible();
  await expect(page.locator(".profile-stats__xp")).toBeVisible();
  await expect(page.locator(".leaderboard-mini__row").first()).toBeVisible();
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
      })),
    );

    expect(dimensions).toEqual(dimensions.map(() => ({ width: "480", height: "270" })));
  }
});

