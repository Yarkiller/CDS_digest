const { expect, test } = require("@playwright/test");

test("opens the N13 search spotlight from the keyboard", async ({ page }) => {
  await page.goto("/design-frontend/pages/issue.html");

  const trigger = page.getByRole("button", { name: /поиск/i });
  await expect(trigger).toBeVisible();
  await expect(trigger.locator("kbd")).toHaveCount(2);

  await page.keyboard.press("Control+k");

  const dialog = page.getByRole("dialog", { name: /поиск digest cds/i });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("searchbox")).toBeFocused();
});

test("keeps search available as a compact mobile trigger", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/design-frontend/pages/issue.html");

  const trigger = page.getByRole("button", { name: /поиск/i });
  await expect(trigger).toBeVisible();
  await expect(trigger).toHaveCSS("width", "44px");

  await trigger.click();
  await expect(page.getByRole("dialog", { name: /поиск digest cds/i })).toBeVisible();
});

test("updates reading progress while scrolling a material", async ({ page }) => {
  await page.goto("/design-frontend/pages/material.html");

  const progress = page.locator(".reading-progress");
  await expect(progress).toBeAttached();
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expect(progress).not.toHaveCSS("transform", "none");
});

test("keeps metrics inside a responsive scroll region", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/design-frontend/pages/razbor.html");

  const region = page.getByRole("region", { name: /метрики качества/i });
  await expect(region).toBeVisible();
  await expect(region.locator("table")).toBeVisible();
  const dimensions = await region.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeGreaterThan(dimensions.clientWidth);
});

test("preserves the outlined secondary action", async ({ page }) => {
  await page.goto("/design-frontend/pages/admin-digest.html");

  const button = page.getByRole("button", { name: "Предпросмотр письма" });
  const borderColor = await button.evaluate((element) => getComputedStyle(element).borderTopColor);
  expect(borderColor).not.toBe("rgba(0, 0, 0, 0)");
});

test("keeps admin row spacing on the 4-point scale", async ({ page }) => {
  await page.goto("/design-frontend/pages/admin-digest.html");

  const rank = page.locator(".admin-row__rank").first();
  await expect(rank).toHaveCSS("padding-top", "8px");
});

test("reserves intrinsic space for cover images", async ({ page }) => {
  for (const path of [
    "/design-frontend/pages/knowledge.html",
    "/design-frontend/pages/material.html",
    "/design-frontend/pages/archive.html",
    "/design-frontend/pages/admin-digest.html",
  ]) {
    await page.goto(path);

    const images = page.locator('img[src*="/assets/covers/"]');
    await expect(images).not.toHaveCount(0);
    const dimensions = await images.evaluateAll((elements) =>
      elements.map((image) => ({
        width: image.getAttribute("width"),
        height: image.getAttribute("height"),
      }))
    );

    expect(dimensions).toEqual(
      dimensions.map(() => ({ width: "480", height: "270" }))
    );
  }
});
