const { expect, test } = require("@playwright/test");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

/** @type {(text: string | null | undefined) => boolean} */
let containsForbiddenChrome;

/**
 * Admin Digest SPA honesty gate (ADMIN-01, ADMIN-04, ADMIN-06, ADMIN-07, ADMIN-08;
 * D-77, D-80, D-85, D-86, D-87, D-90).
 * Role harness: sticky window.__DIGEST_MOCK_ME_ROLE__ (employee default).
 */

test.beforeAll(async () => {
  const mod = await import(
    pathToFileURL(
      path.resolve(__dirname, "../web/src/utils/forbiddenChrome.js"),
    ).href,
  );
  containsForbiddenChrome = mod.containsForbiddenChrome;
});

async function gotoAsRole(page, role, path = "/", extraInit) {
  await page.addInitScript(
    ({ r, extra }) => {
      window.__DIGEST_MOCK_ME_ROLE__ = r;
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    },
    { r: role, extra: extraInit ?? null },
  );
  await page.goto(path);
  // Reset module-level admin mocks between tests (Vite keeps singleton state).
  if (path.startsWith("/admin")) {
    await page.waitForFunction(() => Boolean(window.__DIGEST_ADMIN_HARNESS__));
    await page.evaluate((extra) => {
      window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness();
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    }, extraInit ?? null);
    await page.reload();
  }
}

async function approveReadyRows(page, indices) {
  const rows = page.getByTestId("admin-shortlist-row");
  for (const i of indices) {
    await rows.nth(i).getByRole("checkbox").check();
  }
  await page.getByRole("button", { name: /одобрить выбранные/i }).click();
  await expect(rows.nth(indices[0]).getByText("одобрен")).toBeVisible();
}

test.describe("Admin Digest — role gate (D-75, D-76, D-77, ADMIN-01)", () => {
  test("employee never sees Админ nav link", async ({ page }) => {
    await gotoAsRole(page, "employee", "/");
    await expect(page.getByRole("navigation", { name: /основная навигация/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /^Админ$/ })).toHaveCount(0);
  });

  test("admin sees Админ nav linking to /admin/digest", async ({ page }) => {
    await gotoAsRole(page, "admin", "/");
    const adminLink = page.getByRole("link", { name: /^Админ$/ });
    await expect(adminLink).toBeVisible();
    await expect(adminLink).toHaveAttribute("href", "/admin/digest");
  });

  test("employee deep-link /admin/digest shows 403 Недостаточно прав", async ({
    page,
  }) => {
    // D-77 / AUTH-03 remainder — Playwright employee deep-link proof
    await gotoAsRole(page, "employee", "/admin/digest");
    await expect(
      page.getByRole("heading", { name: "Недостаточно прав", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText(/этот раздел доступен только администраторам digest cds/i),
    ).toBeVisible();
    const cta = page.getByRole("link", { name: /на выпуск/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/");
    await expect(page.getByText(/shortlist дайджеста/i)).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist")).toHaveCount(0);
  });

  test("/me network failure shows ServiceUnavailable not Forbidden", async ({
    page,
  }) => {
    // WR-03: transient /me outages must not look like 403
    await page.addInitScript(() => {
      window.__DIGEST_MOCK_ME_ROLE__ = "admin";
      window.__DIGEST_ME_FAIL_FETCH__ = true;
    });
    await page.goto("/admin/digest");
    await expect(page.getByTestId("service-unavailable")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Недостаточно прав", exact: true }),
    ).toHaveCount(0);
  });
});

test.describe("Admin nav grouping — in-page section switch (ADUX-12, D-01…D-12, D-16…D-19)", () => {
  function shellNav(page) {
    return page.getByRole("navigation", { name: /основная навигация/i });
  }

  function shellAdminLink(page) {
    return shellNav(page).getByRole("link", { name: /^Админ$/ });
  }

  /**
   * Layout probe for the geometry backstops: page-level and content-column widths plus the
   * `main` box. `main` owns the section switch and excludes the wrapping shell header, so
   * its scrollWidth is the tighter overflow signal; documentElement covers the page scroll.
   */
  async function layoutMetrics(page) {
    return page.evaluate(() => {
      const root = document.documentElement;
      const main = document.querySelector("main");
      const box = main.getBoundingClientRect();
      return {
        viewportWidth: window.innerWidth,
        documentScrollWidth: root.scrollWidth,
        documentClientWidth: root.clientWidth,
        mainScrollWidth: main.scrollWidth,
        mainClientWidth: main.clientWidth,
        mainLeft: box.left,
        mainRight: box.right,
      };
    });
  }

  test("admin-section nav lists Дайджест then Пайплайн and marks digest active", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const sectionNav = page.getByTestId("admin-section-nav");
    await expect(sectionNav).toBeVisible();
    await expect(sectionNav).toHaveAttribute("aria-label", "Разделы админки");

    // zero-one-many (resolved explicit): exactly two destinations, ordered digest → pipeline
    const sectionLinks = sectionNav.getByRole("link");
    await expect(sectionLinks).toHaveCount(2);
    await expect(sectionLinks.nth(0)).toHaveText("Дайджест");
    await expect(sectionLinks.nth(1)).toHaveText("Пайплайн");

    await expect(page.getByTestId("admin-tab-digest")).toHaveAttribute("href", "/admin/digest");
    await expect(page.getByTestId("admin-tab-pipeline")).toHaveAttribute(
      "href",
      "/admin/pipeline",
    );
    await expect(page.getByTestId("admin-tab-digest")).toHaveAttribute("aria-current", "page");
    await expect(page.getByTestId("admin-tab-pipeline")).not.toHaveAttribute(
      "aria-current",
      "page",
    );

    // Adjacency (resolved explicit): the shell landmark never owns a «Пайплайн» link
    await expect(shellNav(page).getByRole("link", { name: "Пайплайн", exact: true })).toHaveCount(
      0,
    );
  });

  test("admin-section pipeline tab navigates and keeps the shell Админ entry active", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await page.getByTestId("admin-tab-pipeline").click();

    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(page.getByTestId("admin-pipeline-page")).toBeVisible();
    await expect(page.getByTestId("admin-tab-pipeline")).toHaveAttribute("aria-current", "page");
    await expect(page.getByTestId("admin-tab-digest")).not.toHaveAttribute(
      "aria-current",
      "page",
    );

    const adminLink = shellAdminLink(page);
    await expect(adminLink).toHaveAttribute("href", "/admin/digest");
    await expect(adminLink).toHaveClass(/bg-accent/);
  });

  test("admin-section nav is absent from materials preview while shell Админ stays active", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/materials/sql-dashboards-for-audit-reporting");
    await expect(page.getByTestId("material-preview-banner")).toBeVisible();

    // D-03 / D-11: preview is a sibling route — no tab-bar, but the shell pill lights up
    await expect(page.getByTestId("admin-section-nav")).toHaveCount(0);
    await expect(page.getByTestId("admin-section-select")).toHaveCount(0);
    await expect(shellAdminLink(page)).toHaveClass(/bg-accent/);
  });

  test("narrow viewport swaps the section nav for the select backstop", async ({ page }) => {
    await page.setViewportSize({ width: 480, height: 800 });
    await gotoAsRole(page, "admin", "/admin/digest");

    await expect(page.getByTestId("admin-section-nav")).toHaveCount(1);
    await expect(page.getByTestId("admin-section-nav")).toBeHidden();

    const select = page.getByTestId("admin-section-select");
    await expect(select).toBeVisible();
    await expect(select).toHaveAttribute("aria-label", "Разделы админки");
    await expect(select).toHaveValue("/admin/digest");

    await select.selectOption("/admin/pipeline");
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(page.getByTestId("admin-section-select")).toHaveValue("/admin/pipeline");
    await expect(shellAdminLink(page)).toHaveClass(/bg-accent/);
  });

  test("dirty editor ignores a click on the already-active section tab (WR-01, D-13)", async ({
    page,
  }) => {
    // WR-01: NavLink navigates even to the current location, so useBlocker sees a
    // leave that is not a leave. Clicking the tab you are already on must be inert.
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    const pipelineTab = page.getByTestId("admin-tab-pipeline");
    await expect(pipelineTab).toHaveAttribute("aria-current", "page");
    await pipelineTab.click();

    // URL and draft are auto-waiting assertions, so the dialog count is read after the
    // (blocked) navigation settles instead of racing it.
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");
    await expect(page.getByRole("dialog")).toHaveCount(0);

    // D-13 no-carve-out guard: a genuine tab leave in the same state still prompts.
    await page.getByTestId("admin-tab-digest").click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");
    await expect(pipelineTab).toHaveAttribute("aria-current", "page");
  });

  test("admin surfaces expose exactly one visually hidden h1 (IN-01, D-06)", async ({
    page,
  }) => {
    // IN-01: the outline must not start at h2, but D-06 forbids restoring a visible title.
    await gotoAsRole(page, "admin", "/admin/digest");
    const digestHeading = page.getByRole("heading", {
      level: 1,
      name: "Дайджест",
      exact: true,
    });
    await expect(digestHeading).toHaveCount(1);
    // Playwright treats a 1x1 box as visible, so the class AND the geometry are what make
    // this case fail if `sr-only` is dropped and the title becomes sighted again.
    await expect(digestHeading).toHaveClass(/sr-only/);
    const digestBox = await digestHeading.boundingBox();
    expect(digestBox).not.toBeNull();
    expect(digestBox.width).toBeLessThanOrEqual(1);
    expect(digestBox.height).toBeLessThanOrEqual(1);

    await gotoAsRole(page, "admin", "/admin/pipeline");
    const pipelineHeading = page.getByRole("heading", {
      level: 1,
      name: "Пайплайн",
      exact: true,
    });
    await expect(pipelineHeading).toHaveCount(1);
    await expect(pipelineHeading).toHaveClass(/sr-only/);
    const pipelineBox = await pipelineHeading.boundingBox();
    expect(pipelineBox).not.toBeNull();
    expect(pipelineBox.width).toBeLessThanOrEqual(1);
    expect(pipelineBox.height).toBeLessThanOrEqual(1);

    // The removed page titles stay removed — this case only adds the section name.
    await expect(
      page.getByRole("heading", { name: "Конфиг пайплайна", exact: true }),
    ).toHaveCount(0);
  });

  test("shell Админ pill exposes aria-current on every admin path (WR-02, IN-04)", async ({
    page,
  }) => {
    // WR-02: the pill was visually active on every /admin/* path but announced nothing.
    await gotoAsRole(page, "admin", "/");
    const homeLink = shellAdminLink(page);
    await expect(homeLink).toHaveCount(1);
    await expect(homeLink).toHaveAttribute("href", "/admin/digest");
    expect(await homeLink.getAttribute("aria-current")).toBeNull();
    await expect(homeLink).not.toHaveClass(/bg-accent/);

    // "true", not "page": the href targets digest while the whole section is current.
    for (const target of [
      "/admin/digest",
      "/admin/pipeline",
      "/admin/materials/sql-dashboards-for-audit-reporting",
    ]) {
      await gotoAsRole(page, "admin", target);
      const adminLink = shellAdminLink(page);
      await expect(adminLink).toHaveCount(1);
      await expect(adminLink).toHaveAttribute("href", "/admin/digest");
      await expect(adminLink).toHaveAttribute("aria-current", "true");
      await expect(adminLink).toHaveClass(/bg-accent/);
    }
  });

  test("section tabs share one row with no overflow at 1280 and the 640px sm edge (GAP-BACKSTOP-1)", async ({
    page,
  }) => {
    for (const width of [1280, 640]) {
      for (const target of ["/admin/digest", "/admin/pipeline"]) {
        await page.setViewportSize({ width, height: 900 });
        await gotoAsRole(page, "admin", target);
        await page.evaluate(() => document.fonts.ready);

        const digestBox = await page.getByTestId("admin-tab-digest").boundingBox();
        const pipelineBox = await page.getByTestId("admin-tab-pipeline").boundingBox();
        expect(digestBox).not.toBeNull();
        expect(pipelineBox).not.toBeNull();
        // One row, no wrap: equal viewport-relative tops, digest ends before pipeline starts.
        expect(Math.abs(digestBox.y - pipelineBox.y)).toBeLessThanOrEqual(1);
        expect(digestBox.x + digestBox.width).toBeLessThanOrEqual(pipelineBox.x);

        // Both widths are asserted on purpose: documentElement = page scroll,
        // main = the content column that actually owns the switch.
        const metrics = await layoutMetrics(page);
        expect(metrics.documentScrollWidth).toBeLessThanOrEqual(metrics.documentClientWidth);
        expect(metrics.mainScrollWidth).toBeLessThanOrEqual(metrics.mainClientWidth);
      }
    }

    // Negative control: below `sm` the very same probe returns a hidden nav, so the
    // geometry assertions above are breakpoint-sensitive rather than vacuous.
    await page.setViewportSize({ width: 639, height: 900 });
    await gotoAsRole(page, "admin", "/admin/digest");
    await expect(page.getByTestId("admin-section-nav")).toBeHidden();
    await expect(page.getByTestId("admin-section-select")).toBeVisible();
  });

  test("narrow section select stays inside the content column without overflow (GAP-BACKSTOP-2)", async ({
    page,
  }) => {
    for (const width of [480, 400]) {
      await page.setViewportSize({ width, height: 900 });
      await gotoAsRole(page, "admin", "/admin/digest");
      await page.evaluate(() => document.fonts.ready);

      const select = page.getByTestId("admin-section-select");
      await expect(select).toBeVisible();
      const box = await select.boundingBox();
      expect(box).not.toBeNull();
      const metrics = await layoutMetrics(page);

      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(metrics.viewportWidth);
      // Content column = `main` minus its px-4 (16px) padding on each side, ±1px tolerance.
      expect(box.x).toBeGreaterThanOrEqual(metrics.mainLeft + 16 - 1);
      expect(box.x + box.width).toBeLessThanOrEqual(metrics.mainRight - 16 + 1);
      expect(box.width).toBeLessThanOrEqual(metrics.mainClientWidth - 32 + 1);
      expect(metrics.documentScrollWidth).toBeLessThanOrEqual(metrics.documentClientWidth);
      // The option→URL switch is already pinned at 480px by the select-backstop case.
    }
  });

  test("single shell Админ pill stays visible when the shell nav wraps (GAP-BACKSTOP-3)", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 480, height: 900 });
    await gotoAsRole(page, "admin", "/admin/digest");
    await page.evaluate(() => document.fonts.ready);

    const nav = shellNav(page);
    const navBox = await nav.boundingBox();
    // Measure the wrap instead of assuming it: the nav box beats one pill row.
    const firstPillBox = await nav
      .getByRole("link", { name: /^Выпуск$/ })
      .boundingBox();
    expect(navBox).not.toBeNull();
    expect(firstPillBox).not.toBeNull();
    expect(navBox.height).toBeGreaterThan(firstPillBox.height);

    const adminLink = shellAdminLink(page);
    await expect(adminLink).toBeVisible();
    const adminBox = await adminLink.boundingBox();
    expect(adminBox).not.toBeNull();
    expect(adminBox.x).toBeGreaterThanOrEqual(0);
    expect(adminBox.x + adminBox.width).toBeLessThanOrEqual(480);

    // The section switch never becomes a second row of pills.
    await expect(page.getByTestId("admin-section-nav")).toBeHidden();
    await expect(page.getByTestId("admin-section-select")).toBeVisible();
  });
});

test.describe("Admin Digest — shortlist triage (ADMIN-01…03, ADMIN-05, D-79, D-80)", () => {
  test("populated shortlist shows ≤5 rows with badges and score factors", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    // D-06 / D-08: the active section tab replaces the former page H1 and carries its weight.
    await expect(
      page.getByRole("heading", { name: "Shortlist дайджеста", exact: true }),
    ).toHaveCount(0);
    await expect(page.getByTestId("admin-digest-page").getByText("Админ", { exact: true })).toHaveCount(0);
    const digestTab = page.getByTestId("admin-tab-digest");
    await expect(digestTab).toHaveAttribute("aria-current", "page");
    await expect(digestTab).toHaveClass(/text-3xl/);
    await expect(digestTab).toHaveClass(/font-semibold/);
    const list = page.getByTestId("admin-shortlist");
    await expect(list).toBeVisible();
    const rows = page.getByTestId("admin-shortlist-row");
    await expect(rows).toHaveCount(5);
    await expect(rows.first().getByText("готов", { exact: true })).toBeVisible();
    await expect(
      page.getByText("Обоснование недоступно — скоринг не запускался", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText(/relevance · freshness/i).first()).toBeVisible();
  });

  test("empty shortlist shows Кандидатов пока нет without пайплайн", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_EMPTY__: true,
    });
    await expect(
      page.getByRole("heading", { name: "Кандидатов пока нет", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /обновить список/i })).toBeVisible();
    // Scoped to the digest page content: «Пайплайн» lives only in the AdminLayout
    // section switch (ADUX-12), never in the digest page body.
    await expect(
      page.getByTestId("admin-digest-page").getByText(/пайплайн/i),
    ).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(0);
    // G-05-2: genuine empty (digest_rest=false) must not show post-send rest copy
    await expect(page.getByText(/дайджест успешно выпущен/i)).toHaveCount(0);
    await expect(page.getByTestId("admin-digest-rest")).toHaveCount(0);
  });

  // D-12 / D-13 / FIX-01: empty-unsent mock (batch_id present) must reuse D-80 empty UI, not digest_rest
  test("empty-unsent shortlist shows Кандидатов пока нет without пайплайн (EMPTY_UNSENT)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_EMPTY_UNSENT__: true,
    });
    await expect(
      page.getByRole("heading", { name: "Кандидатов пока нет", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /обновить список/i })).toBeVisible();
    // Scoped to the digest page content: «Пайплайн» lives only in the AdminLayout
    // section switch (ADUX-12), never in the digest page body.
    await expect(
      page.getByTestId("admin-digest-page").getByText(/пайплайн/i),
    ).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(0);
    await expect(page.getByText(/дайджест успешно выпущен/i)).toHaveCount(0);
    await expect(page.getByTestId("admin-digest-rest")).toHaveCount(0);
  });

  test("loading shortlist does not flash empty success", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    // After harness reset+reload, assert we never land on empty copy while rows exist.
    await expect(page.getByTestId("admin-digest-page")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Кандидатов пока нет", exact: true }),
    ).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(5);
  });

  test("Одобрить выбранные persists and shows одобрен caption", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(firstRow.getByText("одобрен")).toBeVisible();
  });

  test("Approve in-flight disables toolbar actions", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("checkbox").check();
    const approveBtn = page.getByRole("button", { name: /одобрить выбранные/i });
    await approveBtn.click();
    // While request is in flight (mock delay), primary decision actions stay disabled.
    await expect(approveBtn).toBeDisabled();
    await expect(firstRow.getByText("одобрен")).toBeVisible();
  });

  test("partial decision failure keeps failed selection and toasts ids (WR-06)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    await rows.nth(0).getByRole("checkbox").check();
    await rows.nth(1).getByRole("checkbox").check();
    await page.evaluate(() => window.__DIGEST_ADMIN_HARNESS__.armFailNextDecision());
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(page.getByText(/не сохранено/i)).toBeVisible();
    // First id fails (armed), second succeeds — failed row stays checked.
    await expect(rows.nth(0).getByRole("checkbox")).toBeChecked();
    await expect(rows.nth(1).getByText("одобрен")).toBeVisible();
  });
});

test.describe("Admin Digest — batch select + preview/send gate (ADMIN-04,06,07, D-85, D-86)", () => {
  test("Выбрать все and Оставить топ-3 update checkboxes", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    await expect(rows).toHaveCount(5);

    await page.getByRole("button", { name: /выбрать все/i }).click();
    for (let i = 0; i < 5; i += 1) {
      await expect(rows.nth(i).getByRole("checkbox")).toBeChecked();
    }

    await page.getByRole("button", { name: /оставить топ-3/i }).click();
    for (let i = 0; i < 3; i += 1) {
      await expect(rows.nth(i).getByRole("checkbox")).toBeChecked();
    }
    await expect(rows.nth(3).getByRole("checkbox")).not.toBeChecked();
    await expect(rows.nth(4).getByRole("checkbox")).not.toBeChecked();

    await rows.nth(1).getByRole("checkbox").uncheck();
    await expect(rows.nth(0).getByRole("checkbox")).toBeChecked();
    await expect(rows.nth(1).getByRole("checkbox")).not.toBeChecked();
    await expect(rows.nth(2).getByRole("checkbox")).toBeChecked();
  });

  test("preview failure keeps send locked", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_FAIL_PREVIEW__: true,
    });
    await approveReadyRows(page, [0, 1]);

    const sendBtn = page.getByRole("button", { name: /отправить дайджест/i });
    await expect(sendBtn).toBeDisabled();

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await expect(emailDialog.getByText("Превью недоступно", { exact: true })).toBeVisible();
    await expect(
      emailDialog.getByRole("button", { name: "Повторить превью", exact: true }),
    ).toBeVisible();
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
    await expect(emailDialog).toHaveCount(0);

    await expect(page.getByText(/сначала откройте превью письма/i)).toBeVisible();
    await expect(sendBtn).toBeDisabled();
  });

  test("approved draft blocks send with draft hint (ADMIN-03/07, D-85)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    // Rank 4 is draft in default mock batch
    await rows.nth(3).getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(rows.nth(3).getByText("одобрен")).toBeVisible();

    await expect(
      page.getByTestId("admin-send-hint"),
    ).toContainText("Нет одобренных ready-материалов для отправки.");
    await expect(page.getByTestId("admin-mark-ready-batch")).toHaveCount(0);
    await expect(rows.nth(3).getByText("черновик", { exact: true })).toBeVisible();
    await expect(page.getByTestId("admin-send-footer").locator("ul")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /отправить дайджест/i })).toBeDisabled();
    // Preview stays locked until there is ≥1 approved ready
    await expect(page.getByRole("button", { name: /предпросмотр письма/i })).toBeDisabled();
  });

  // ADUX-05 / D-01…D-05 / D-10 — per-row Сделать ready next to draft badge
  test("per-row Сделать ready promotes draft and clears draft hint (ADUX-05)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    const draftRow = rows.nth(3); // material 104 — draft, empty body
    await expect(draftRow.getByText("черновик", { exact: true })).toBeVisible();
    const readyBtn = draftRow.getByTestId("admin-mark-ready");
    await expect(readyBtn).toBeVisible();
    await expect(readyBtn).toHaveText("Сделать ready");

    // Soft-warn for empty body (D-04/D-10)
    page.once("dialog", async (dialog) => {
      expect(dialog.message()).toBe("Текст пуст. Сделать ready и продолжить?");
      await dialog.accept();
    });
    await readyBtn.click();

    await expect(draftRow.getByText("готов", { exact: true })).toBeVisible();
    await expect(draftRow.getByTestId("admin-mark-ready")).toHaveCount(0);

    // Approve after ready — send path unblocked (no approved∩draft)
    await draftRow.getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(draftRow.getByText("одобрен")).toBeVisible();
    await expect(
      page.getByTestId("admin-send-hint"),
    ).toContainText("Сначала откройте превью письма.");
    await expect(page.getByTestId("admin-mark-ready-batch")).toHaveCount(0);
  });

  // G-14-2 / ADUX-05 — a still-draft refetch must never silently revert a confirmed promote
  test("stale still-draft refetch does not revert a promoted row (G-14-2)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_STALE_READY__: true,
    });
    const rows = page.getByTestId("admin-shortlist-row");
    const draftRow = rows.nth(3); // material 104 — draft, empty body
    await draftRow.getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(draftRow.getByText("одобрен")).toBeVisible();
    await expect(draftRow.getByText("черновик", { exact: true })).toBeVisible();

    page.once("dialog", async (dialog) => {
      expect(dialog.message()).toBe("Текст пуст. Сделать ready и продолжить?");
      await dialog.accept();
    });
    await draftRow.getByTestId("admin-mark-ready").click();

    // Let the optimistic update + still-draft refetch settle before asserting the
    // promoted row was not silently reverted (mock delays: 60ms POST + 80ms GET).
    await page.waitForTimeout(500);

    // Backend acknowledged the POST but the refetch still reports draft —
    // the row must stay ready and the D-85 draft hint must clear.
    await expect(draftRow.getByText("готов", { exact: true })).toBeVisible();
    await expect(draftRow.getByTestId("admin-mark-ready")).toHaveCount(0);
    await expect(
      page.getByTestId("admin-send-hint"),
    ).toContainText("Сначала откройте превью письма.");
    await expect(page.getByTestId("admin-mark-ready-batch")).toHaveCount(0);
  });

  // G-14-2 — batch promote control removed (operator override of D-03/D-04)
  test("no batch promote CTA is rendered (G-14-2)", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    // Approve the draft (rank 4) — a batch CTA used to appear in the footer.
    await rows.nth(3).getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(rows.nth(3).getByText("одобрен")).toBeVisible();

    await expect(page.getByTestId("admin-mark-ready-batch")).toHaveCount(0);
    await expect(rows.nth(3).getByTestId("admin-mark-ready")).toBeVisible();
    await expect(page.getByTestId("admin-send-footer").locator("ul")).toHaveCount(0);
  });

  // G-14-3 / ADUX-05 — interactive controls show the pointer affordance
  test("interactive admin controls show a pointer cursor (G-14-3)", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");

    await expect(
      rows.first().getByRole("button", { name: "Превью материала" }),
    ).toHaveCSS("cursor", "pointer");
    await expect(rows.nth(3).getByTestId("admin-mark-ready")).toHaveCSS(
      "cursor",
      "pointer",
    );
    await expect(
      page.getByRole("button", { name: /выбрать все/i }),
    ).toHaveCSS("cursor", "pointer");

    // Disabled controls keep the non-pointer cursor (guards :not(:disabled))
    const sendBtn = page.getByRole("button", { name: /отправить дайджест/i });
    await expect(sendBtn).toBeDisabled();
    await expect(sendBtn).not.toHaveCSS("cursor", "pointer");
  });

  test("Approve does not auto-ready draft (D-02)", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const rows = page.getByTestId("admin-shortlist-row");
    await rows.nth(3).getByRole("checkbox").check();
    await page.getByRole("button", { name: /одобрить выбранные/i }).click();
    await expect(rows.nth(3).getByText("одобрен (в шортлист)", { exact: true })).toBeVisible();
    await expect(rows.nth(3).getByText("черновик", { exact: true })).toBeVisible();
    await expect(rows.nth(3).getByTestId("admin-mark-ready")).toBeVisible();
  });

  test("preview lists one approved-ready article (zero-one-many E4)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0]);

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await expect(emailDialog.getByText(/только одобренные ready/i)).toBeVisible();
    await expect(emailDialog.getByText(/Digest CDS/i)).toBeVisible();
    const iframe = emailDialog.getByTestId("email-preview-frame");
    await expect(iframe).toBeVisible();
    await expect(iframe).toHaveAttribute(
      "sandbox",
      "allow-popups allow-popups-to-escape-sandbox",
    );
    await expect(emailDialog.locator("ul")).toHaveCount(0);
    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    await expect(frame.getByRole("heading")).toContainText("Building Production RAG Systems");
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
  });

  test("Вводный текст appears in Превью письма (G-05-1 / ADMIN-04)", async ({
    page,
  }) => {
    const introPhrase = `Добрый день коллеги! G05-1-${Date.now()}`;
    await gotoAsRole(page, "admin", "/admin/digest");
    await page.getByLabel(/вводный текст/i).fill(introPhrase);
    await approveReadyRows(page, [0, 1]);

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    await expect(frame.locator("body")).toContainText(introPhrase);
    await expect(emailDialog.locator("ul")).toHaveCount(0);
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
  });

  test("Блоки выпуска: reorder + interstitial text drive preview (G-05-1)", async ({
    page,
  }) => {
    const bridge = `Связка G05-1-${Date.now()}`;
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0, 1]);

    const blocks = page.getByTestId("admin-issue-blocks");
    await expect(blocks).toBeVisible();
    // Primary control is reorderable blocks — schema free-text textarea is gone.
    await expect(page.getByLabel(/^блоки выпуска$/i)).toBeVisible();
    await expect(
      page.locator('section').filter({ hasText: 'Схема дайджеста' }).locator('textarea.font-mono'),
    ).toHaveCount(0);
    const materialBlocks = blocks.getByTestId("admin-issue-block-material");
    await expect(materialBlocks).toHaveCount(2);
    await expect(materialBlocks.nth(0)).toContainText(/Building Production RAG Systems/i);
    await expect(materialBlocks.nth(1)).toContainText(/Anomaly Detection in Audit Pipelines/i);

    await materialBlocks.nth(1).getByRole("button", { name: /выше|вверх|переместить вверх/i }).click();
    await expect(materialBlocks.nth(0)).toContainText(/Anomaly Detection in Audit Pipelines/i);
    await expect(materialBlocks.nth(1)).toContainText(/Building Production RAG Systems/i);

    await page.getByRole("button", { name: /добавить текст/i }).click();
    const textBlocks = blocks.getByTestId("admin-issue-block-text");
    await expect(textBlocks).toHaveCount(1);
    await textBlocks.first().getByRole("textbox").fill(bridge);

    // Place text between the two materials if it landed at the end: move up once.
    const textUp = textBlocks.first().getByRole("button", {
      name: /выше|вверх|переместить вверх/i,
    });
    if (await textUp.isEnabled()) {
      await textUp.click();
    }

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    const body = frame.locator("body");
    await expect(body).toContainText(bridge);
    const bodyText = await body.innerText();
    const anomalyAt = bodyText.indexOf("Anomaly Detection");
    const bridgeAt = bodyText.indexOf(bridge);
    const ragAt = bodyText.indexOf("Building Production");
    expect(anomalyAt).toBeGreaterThanOrEqual(0);
    expect(bridgeAt).toBeGreaterThan(anomalyAt);
    expect(ragAt).toBeGreaterThan(bridgeAt);
    await expect(emailDialog.locator("ul")).toHaveCount(0);

    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
  });

  test("G-05-1: intro + interstitial in Превью письма; send shows stub honesty banner", async ({
    page,
  }) => {
    const introPhrase = `Привет! G05-1-${Date.now()}`;
    const bridge = `Связка между статьями G05-1-${Date.now()}`;
    await gotoAsRole(page, "admin", "/admin/digest");
    await page.getByLabel(/вводный текст/i).fill(introPhrase);
    await approveReadyRows(page, [0, 1]);

    const blocks = page.getByTestId("admin-issue-blocks");
    const materialBlocks = blocks.getByTestId("admin-issue-block-material");
    await expect(materialBlocks).toHaveCount(2);
    await materialBlocks.nth(1).getByRole("button", { name: /выше|вверх|переместить вверх/i }).click();

    await page.getByRole("button", { name: /добавить текст/i }).click();
    const textBlocks = blocks.getByTestId("admin-issue-block-text");
    await textBlocks.first().getByRole("textbox").fill(bridge);
    const textUp = textBlocks.first().getByRole("button", {
      name: /выше|вверх|переместить вверх/i,
    });
    if (await textUp.isEnabled()) {
      await textUp.click();
    }

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    const body = frame.locator("body");
    await expect(body).toContainText(introPhrase);
    await expect(body).toContainText(bridge);
    const bodyText = await body.innerText();
    const introAt = bodyText.indexOf(introPhrase);
    const anomalyAt = bodyText.indexOf("Anomaly Detection");
    const bridgeAt = bodyText.indexOf(bridge);
    const ragAt = bodyText.indexOf("Building Production");
    expect(introAt).toBeGreaterThanOrEqual(0);
    expect(anomalyAt).toBeGreaterThan(introAt);
    expect(bridgeAt).toBeGreaterThan(anomalyAt);
    expect(ragAt).toBeGreaterThan(bridgeAt);
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();

    const sendBtn = page.getByRole("button", { name: /отправить дайджест/i });
    await expect(sendBtn).toBeEnabled();
    await sendBtn.click();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();
    await expect(
      page.getByText("Выпуск опубликован. Доставка писем: stub (0 из 0)", { exact: true }),
    ).toBeVisible();
    const issueLink = page.getByRole("link", { name: /к выпуску/i });
    await expect(issueLink).toBeVisible();
    await expect(issueLink).toHaveAttribute("href", "/issues/15");
  });

  test("превью unlocks send; confirm shows stub honesty banner + issue link (D-90)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0, 1]);

    const sendBtn = page.getByRole("button", { name: /отправить дайджест/i });
    await expect(sendBtn).toBeDisabled();
    await expect(page.getByText(/сначала откройте превью письма/i)).toBeVisible();

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await expect(emailDialog.getByText(/только одобренные ready/i)).toBeVisible();
    await expect(emailDialog.locator("ul")).toHaveCount(0);
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
    await expect(emailDialog).toHaveCount(0);

    await expect(page.getByText(/превью просмотрено\. можно отправить/i)).toBeVisible();
    await expect(sendBtn).toBeEnabled();

    await sendBtn.click();
    await expect(
      page.getByRole("heading", { name: "Подтвердите отправку", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();
    await expect(
      page.getByText("Выпуск опубликован. Доставка писем: stub (0 из 0)", { exact: true }),
    ).toBeVisible();
    // D-90 / ADMIN-08 — success surfaces same-origin issue path for returnUrl integrity
    const issueLink = page.getByRole("link", { name: /к выпуску/i });
    await expect(issueLink).toBeVisible();
    await expect(issueLink).toHaveAttribute("href", "/issues/15");

    // Second attempt locked — already sent
    await expect(page.getByTestId("admin-send-hint")).toContainText(/уже отправлено/i);
    await expect(sendBtn).toBeDisabled();
  });

  test("G-05-2: after stub honesty send shortlist hides; rest copy shown", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0, 1]);
    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();

    await page.getByRole("button", { name: /отправить дайджест/i }).click();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();

    await expect(
      page.getByText("Выпуск опубликован. Доставка писем: stub (0 из 0)", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText(/дайджест успешно выпущен/i)).toBeVisible();
    await expect(
      page.getByText(/Следующие материалы будут подготовлены через 7 дней/i),
    ).toBeVisible();
    await expect(page.getByTestId("admin-shortlist")).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(0);
    await expect(page.getByRole("checkbox")).toHaveCount(0);
    await expect(page.getByText("Кандидатов пока нет", { exact: true })).toHaveCount(0);
    await expect(page.getByTestId("admin-send-hint")).toContainText(/уже отправлено/i);
  });

  test("G-05-2: Уже отправлено enters rest hide without inactive checkboxes", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_ALREADY_SENT__: true,
    });
    await approveReadyRows(page, [0]);
    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
    await page.getByRole("button", { name: /отправить дайджест/i }).click();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();

    await expect(page.getByRole("status").filter({ hasText: "Уже отправлено" })).toBeVisible();
    await expect(page.getByText(/дайджест успешно выпущен/i)).toBeVisible();
    await expect(page.getByTestId("admin-shortlist")).toHaveCount(0);
    await expect(page.getByRole("checkbox")).toHaveCount(0);
  });

  test("G-05-2: cold load digest_rest shows rest instead of Кандидатов пока нет", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_DIGEST_REST__: true,
    });
    await expect(page.getByText(/дайджест успешно выпущен/i)).toBeVisible();
    await expect(
      page.getByText(/Следующие материалы будут подготовлены через 7 дней/i),
    ).toBeVisible();
    await expect(page.getByText("Кандидатов пока нет", { exact: true })).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist")).toHaveCount(0);
    await expect(page.getByRole("checkbox")).toHaveCount(0);
  });

  test("Уже отправлено when batch already sent", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_ALREADY_SENT__: true,
    });
    await approveReadyRows(page, [0]);
    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await expect(emailDialog.getByText(/только одобренные ready/i)).toBeVisible();
    await emailDialog.getByRole("button", { name: "Закрыть", exact: true }).click();
    await expect(emailDialog).toHaveCount(0);

    await page.getByRole("button", { name: /отправить дайджест/i }).click();
    await page.getByRole("button", { name: /подтвердить отправку/i }).click();
    await expect(page.getByRole("status").filter({ hasText: "Уже отправлено" })).toBeVisible();
  });
});

test.describe("Admin Digest — interstitial hint (ADUX-03, D-15)", () => {
  test("Пустая строка = новый абзац hint under intro and connecting text", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0, 1]);

    const introSection = page.locator("section").filter({ hasText: "Контекст дайджеста" });
    await expect(introSection.getByText("Пустая строка = новый абзац", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /добавить текст/i }).click();
    const textBlock = page.getByTestId("admin-issue-block-text").first();
    await expect(textBlock.getByRole("textbox")).toBeVisible();
    await expect(textBlock.getByText("Пустая строка = новый абзац", { exact: true })).toBeVisible();
    // Empty connecting text remains valid — hint stays visible without markdown toolbar.
    await expect(page.getByRole("toolbar")).toHaveCount(0);
  });
});

test.describe("Admin Digest — email preview honesty (ADUX-02, D-08/D-12)", () => {
  test("email-preview-frame shows sandboxed backend HTML with material title", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0]);

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const iframe = emailDialog.getByTestId("email-preview-frame");
    await expect(iframe).toBeVisible();
    await expect(iframe).toHaveAttribute("title", "Превью письма HTML");
    await expect(iframe).toHaveAttribute(
      "sandbox",
      "allow-popups allow-popups-to-escape-sandbox",
    );
    await expect(emailDialog.getByTestId("email-preview-body")).toHaveCount(0);

    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    await expect(frame.getByRole("heading", { level: 2 })).toContainText(
      "Building Production RAG Systems",
    );
    await expect(frame.getByRole("link", { name: "Читать →" })).toBeVisible();
  });

  test("превью письма: «Читать →» открывает новую вкладку из песочницы (D-11, T-18-05)", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0]);

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const iframe = emailDialog.getByTestId("email-preview-frame");
    await expect(iframe).toBeVisible();

    const frame = emailDialog.frameLocator("[data-testid=email-preview-frame]");
    const readLink = frame.getByRole("link", { name: "Читать →" });
    await expect(readLink).toBeVisible();

    // Behavioural proof (criterion 4): the CTA opens a NEW top-level browsing
    // context instead of silently doing nothing. The mock href host
    // (127.0.0.1:5173) is not served in this project, so only the popup event is
    // asserted — never the popup's URL or content.
    const popupPromise = page.waitForEvent("popup", { timeout: 15000 });
    await readLink.click();
    const popup = await popupPromise;
    expect(popup).toBeTruthy();
    await popup.close();

    // Shape proof (T-18-05): popups are allowed, script and same-origin powers
    // are deliberately withheld.
    await expect(iframe).toHaveAttribute(
      "sandbox",
      "allow-popups allow-popups-to-escape-sandbox",
    );
    const sandbox = await iframe.getAttribute("sandbox");
    expect(sandbox).not.toContain("allow-scripts");
    expect(sandbox).not.toContain("allow-same-origin");
    await expect(readLink).toHaveAttribute("target", "_blank");
    await expect(readLink).toHaveAttribute("rel", /noopener/);
  });

  test("email preview close stays visible while the preview scrolls", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 400 });
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0]);
    await page.getByRole("button", { name: /предпросмотр письма/i }).click();

    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    await expect(emailDialog).toBeVisible();
    const close = emailDialog.getByRole("button", { name: "Закрыть", exact: true });
    const frame = emailDialog.getByTestId("email-preview-frame");
    await expect(frame).toBeVisible();
    await expect(frame).toHaveAttribute(
      "sandbox",
      "allow-popups allow-popups-to-escape-sandbox",
    );
    await expect(emailDialog.locator("ul")).toHaveCount(0);

    const closeContract = await close.evaluate((button) => {
      let node = button.parentElement;
      let insideOverflow = false;
      while (node) {
        const overflowY = getComputedStyle(node).overflowY;
        if (overflowY === "auto" || overflowY === "scroll") {
          insideOverflow = true;
          break;
        }
        node = node.parentElement;
      }
      return {
        insideOverflow,
        hasPointer: button.classList.contains("cursor-pointer"),
      };
    });
    expect(closeContract.insideOverflow).toBe(false);
    expect(closeContract.hasPointer).toBe(true);

    const metrics = await frame.evaluate((el) => {
      let node = el.parentElement;
      while (node) {
        const overflowY = getComputedStyle(node).overflowY;
        if (overflowY === "auto" || overflowY === "scroll") {
          node.scrollTop = node.scrollHeight;
          return { scrollHeight: node.scrollHeight, clientHeight: node.clientHeight };
        }
        node = node.parentElement;
      }
      return null;
    });
    expect(metrics).not.toBeNull();
    expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight);
    await expect(close).toBeInViewport();
    await expect(
      emailDialog.getByRole("heading", { name: "Превью письма", exact: true }),
    ).toBeInViewport();
  });
});

test.describe("Admin Digest — ban-list surfaces (ADUX-04, D-19)", () => {
  test("material modal text has no forbidden chrome tokens", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("button", { name: "Превью материала" }).click();

    const dialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью материала", exact: true }),
    });
    await expect(dialog).toBeVisible();
    const sampled = await dialog.innerText();
    expect(containsForbiddenChrome(sampled)).toBe(false);
  });

  test("email-preview-frame content has no forbidden chrome tokens", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");
    await approveReadyRows(page, [0]);

    await page.getByRole("button", { name: /предпросмотр письма/i }).click();
    const emailDialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью письма", exact: true }),
    });
    const iframe = emailDialog.getByTestId("email-preview-frame");
    await expect(iframe).toBeVisible();

    const srcDoc = await iframe.getAttribute("srcdoc");
    expect(containsForbiddenChrome(srcDoc ?? "")).toBe(false);

    const frame = emailDialog.frameLocator('[data-testid=email-preview-frame]');
    const frameText = await frame.locator("body").innerText();
    expect(containsForbiddenChrome(frameText)).toBe(false);
  });
});

test.describe("Admin Digest — material preview honesty (ADUX-01, D-04…D-06)", () => {
  test("material preview shows body_markdown provenance counts and reader link", async ({
    page,
  }) => {
    const materialByIdHits = [];
    page.on("request", (req) => {
      const url = req.url();
      if (/\/admin\/materials\//i.test(url) || /\/materials\/\d+/i.test(url)) {
        materialByIdHits.push(url);
      }
    });

    await gotoAsRole(page, "admin", "/admin/digest");
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("button", { name: "Превью материала" }).click();

    const dialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью материала", exact: true }),
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Building Production RAG Systems")).toBeVisible();
    await expect(dialog.getByText("YouTube · lecture")).toBeVisible();
    await expect(dialog.getByText("~128 символов · 18 слов · ~2 мин")).toBeVisible();
    await expect(dialog.getByText("Фрагменты регламентов находятся быстрее.")).toBeVisible();
    const readerLink = dialog.getByRole("link", { name: "Открыть материал →" });
    await expect(readerLink).toBeVisible();
    await expect(readerLink).toHaveAttribute(
      "href",
      "/admin/materials/building-production-rag-systems",
    );
    await expect(dialog.getByRole("button", { name: "Закрыть", exact: true })).toBeVisible();
    expect(materialByIdHits).toEqual([]);
  });

  test("черновик: «Открыть материал →» ведёт на админ-предпросмотр, а не на читательский 404", async ({
    page,
  }) => {
    // Backlog 999.1: this is the row whose «Открыть материал →» used to land on the
    // reader route's «Материал не найден». Row 104 is the draft seed — deliberately
    // NOT `.first()`, which is the ready row 101.
    await gotoAsRole(page, "admin", "/admin/digest");

    const draftRow = page
      .getByTestId("admin-shortlist-row")
      .filter({ hasText: "SQL Dashboards for Audit Reporting" });
    await expect(draftRow).toHaveCount(1);
    await draftRow.getByRole("button", { name: "Превью материала" }).click();

    const dialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью материала", exact: true }),
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("SQL Dashboards for Audit Reporting")).toBeVisible();

    const previewLink = dialog.getByRole("link", { name: "Открыть материал →" });
    await expect(previewLink).toHaveAttribute(
      "href",
      "/admin/materials/sql-dashboards-for-audit-reporting",
    );
    await previewLink.click();

    await expect(page).toHaveURL(
      /\/admin\/materials\/sql-dashboards-for-audit-reporting$/,
    );
    await expect(page.getByTestId("material-preview-banner")).toBeVisible();
    await expect(page.getByText("Материал не найден")).toHaveCount(0);
  });

  test("material preview empty body shows Текст материала недоступен without toast", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_MATERIAL_EMPTY_BODY__: true,
    });
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("button", { name: "Превью материала" }).click();

    const dialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью материала", exact: true }),
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Building Production RAG Systems")).toBeVisible();
    await expect(dialog.getByText("Текст материала недоступен")).toBeVisible();
    await expect(dialog.getByText("~0 символов · 0 слов · ~1 мин")).toBeVisible();
    await expect(dialog.getByText("YouTube · lecture")).toHaveCount(0);
    await expect(dialog.getByRole("button", { name: "Закрыть", exact: true })).toBeVisible();
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test("material preview close stays visible while the body scrolls", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await gotoAsRole(page, "admin", "/admin/digest", {
      __DIGEST_ADMIN_MATERIAL_LONG_BODY__: true,
    });
    const firstRow = page.getByTestId("admin-shortlist-row").first();
    await firstRow.getByRole("button", { name: "Превью материала" }).click();

    const dialog = page.getByRole("dialog").filter({
      has: page.getByRole("heading", { name: "Превью материала", exact: true }),
    });
    await expect(dialog).toBeVisible();
    const close = dialog.getByRole("button", { name: "Закрыть", exact: true });
    const body = dialog.getByTestId("admin-material-preview-body");
    await expect(body).toBeVisible();

    const closeContract = await close.evaluate((button) => {
      let node = button.parentElement;
      let insideOverflow = false;
      while (node) {
        const overflowY = getComputedStyle(node).overflowY;
        if (overflowY === "auto" || overflowY === "scroll") {
          insideOverflow = true;
          break;
        }
        node = node.parentElement;
      }
      return {
        insideOverflow,
        hasPointer: button.classList.contains("cursor-pointer"),
      };
    });
    expect(closeContract.insideOverflow).toBe(false);
    expect(closeContract.hasPointer).toBe(true);

    const metrics = await body.evaluate((el) => {
      let node = el.parentElement;
      while (node) {
        const overflowY = getComputedStyle(node).overflowY;
        if (overflowY === "auto" || overflowY === "scroll") {
          node.scrollTop = node.scrollHeight;
          return { scrollHeight: node.scrollHeight, clientHeight: node.clientHeight };
        }
        node = node.parentElement;
      }
      return null;
    });
    expect(metrics).not.toBeNull();
    expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight);
    await expect(close).toBeInViewport();
    await expect(
      dialog.getByRole("heading", { name: "Превью материала", exact: true }),
    ).toBeInViewport();
  });
});

test.describe("Admin pipeline config — view + save (PIPE-01/PIPE-03, D-11/D-13)", () => {
  test("pipeline config happy path", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await expect(page.getByTestId("admin-pipeline-page")).toBeVisible();
    // D-06 / D-08: the active section tab owns the hierarchy; the page keeps only the hint.
    await expect(
      page.getByRole("heading", { name: "Конфиг пайплайна", exact: true }),
    ).toHaveCount(0);
    await expect(page.getByTestId("admin-pipeline-page").getByText("Админ", { exact: true })).toHaveCount(0);
    const pipelineTab = page.getByTestId("admin-tab-pipeline");
    await expect(pipelineTab).toHaveAttribute("aria-current", "page");
    await expect(pipelineTab).toHaveClass(/text-3xl/);
    await expect(pipelineTab).toHaveClass(/font-semibold/);
    // No-execution honesty (PIPE-EXEC-* deferred): the surface states its scope.
    await expect(page.getByText("Просмотр и правка без запуска пайплайна", { exact: true })).toBeVisible();

    const editor = page.getByTestId("pipeline-config-editor");
    await expect(editor).toBeVisible();
    await expect(editor).toHaveValue("");

    const doc = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n";
    await editor.fill(doc);

    const save = page.getByTestId("pipeline-config-save");
    await expect(save).toBeEnabled();
    await save.click();
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Сохранено");
    await expect(save).toBeDisabled();

    // PIPE-03: a subsequent read returns the saved YAML.
    await page.reload();
    await expect(page.getByTestId("pipeline-config-editor")).toHaveValue(doc);
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Изменений нет");
  });
});

test.describe("Admin pipeline config — validation + save failure (PIPE-02, D-05/D-07)", () => {
  test("pipeline config validation renders every server error row and keeps the document dirty", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    const doc = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 0\n";
    await editor.fill(doc);

    await page.evaluate(() => {
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armRejectNextSave([
        { path: "max_chars", message: "Input should be greater than 0" },
        { path: "template", line: 1, message: "Input should be 'lecture' or 'podcast'" },
      ]);
    });
    await page.getByTestId("pipeline-config-save").click();

    const panel = page.getByTestId("pipeline-config-errors");
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute("role", "alert");
    await expect(
      panel.getByRole("heading", { name: "Проверьте конфиг перед сохранением" }),
    ).toBeVisible();

    const rows = panel.getByTestId("pipeline-config-error");
    await expect(rows).toHaveCount(2);
    // Row prefix is Строка {line}: when a line is present, else {path}: — message verbatim.
    await expect(rows.nth(0)).toContainText("max_chars: Input should be greater than 0");
    await expect(rows.nth(1)).toContainText("Строка 1: Input should be 'lecture' or 'podcast'");

    // The rejected document stays editable + dirty and is never discarded.
    await expect(editor).toHaveValue(doc);
    await expect(editor).toHaveAttribute("aria-invalid", "true");
    await expect(page.getByTestId("pipeline-config-save")).toBeEnabled();
  });

  test("pipeline config validation falls back to a single generic string when the reject has no structured errors", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
    await page.evaluate(() => {
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armRejectNextSave();
    });
    await page.getByTestId("pipeline-config-save").click();

    const panel = page.getByTestId("pipeline-config-errors");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("pipeline-config-error")).toHaveCount(0);
    await expect(panel.getByText("Конфиг не прошёл проверку", { exact: true })).toBeVisible();
  });

  test("pipeline config validation clears stale errors on edit", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");
    await page.evaluate(() => {
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armRejectNextSave([
        { path: "template", message: "bad template" },
      ]);
    });
    await page.getByTestId("pipeline-config-save").click();
    await expect(page.getByTestId("pipeline-config-errors")).toBeVisible();

    await editor.fill("template: podcast\n");
    await expect(page.getByTestId("pipeline-config-errors")).toHaveCount(0);
    await expect(editor).toHaveAttribute("aria-invalid", "false");
  });

  test("pipeline config save failure shows a retry control and can succeed", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");
    await page.evaluate(() => {
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armFailNextSave();
    });
    await page.getByTestId("pipeline-config-save").click();

    await expect(page.getByText("Конфиг не сохранён", { exact: true })).toBeVisible();
    const retry = page.getByTestId("pipeline-config-save-retry");
    await expect(retry).toBeVisible();
    await expect(retry).toHaveText("Повторить сохранение");

    await retry.click();
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Сохранено");
    await expect(page.getByText("Конфиг не сохранён", { exact: true })).toHaveCount(0);
  });
});

test.describe("Admin pipeline config — empty/dirty/reset/nav/no-execution (PIPE-01, D-10/D-12/D-13)", () => {
  test("pipeline config empty state shows the locked copy and a disabled Save", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const empty = page.getByTestId("pipeline-config-empty");
    await expect(empty).toBeVisible();
    await expect(
      empty.getByRole("heading", { name: "Конфиг ещё не задан", exact: true }),
    ).toBeVisible();
    await expect(
      empty.getByText(
        "Введите YAML и сохраните — конфиг будет доступен при следующих заходах.",
        { exact: true },
      ),
    ).toBeVisible();

    const editor = page.getByTestId("pipeline-config-editor");
    await expect(editor).toHaveAttribute("placeholder", "# YAML конфига пайплайна");
    await expect(editor).toHaveValue("");
    await expect(page.getByTestId("pipeline-config-save")).toBeDisabled();
  });

  test("pipeline config dirty gating enables Save and reset on edit", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const save = page.getByTestId("pipeline-config-save");
    const reload = page.getByTestId("pipeline-config-reload");
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Изменений нет");
    await expect(save).toBeDisabled();
    await expect(reload).toBeDisabled();

    await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
    await expect(save).toBeEnabled();
    await expect(reload).toBeEnabled();
  });

  test("pipeline config dirty gating arms the unsaved-leave guard", async ({ page }) => {
    // Listener-registry spy — must run before gotoAsRole so it wraps every mount.
    await page.addInitScript(() => {
      window.__DIGEST_BEFOREUNLOAD_REGISTRY__ = [];
      const origAdd = window.addEventListener.bind(window);
      const origRemove = window.removeEventListener.bind(window);
      window.addEventListener = (type, listener, options) => {
        if (type === "beforeunload") {
          window.__DIGEST_BEFOREUNLOAD_REGISTRY__.push(listener);
        }
        return origAdd(type, listener, options);
      };
      window.removeEventListener = (type, listener, options) => {
        if (type === "beforeunload") {
          window.__DIGEST_BEFOREUNLOAD_REGISTRY__ =
            window.__DIGEST_BEFOREUNLOAD_REGISTRY__.filter((l) => l !== listener);
        }
        return origRemove(type, listener, options);
      };
    });

    function appUnloadSources() {
      return page.evaluate(() =>
        (window.__DIGEST_BEFOREUNLOAD_REGISTRY__ || [])
          .map((fn) => String(fn))
          .filter(
            (s) =>
              s.includes("preventDefault") ||
              s.includes("returnValue") ||
              s.includes("confirm") ||
              s.includes("alert"),
          ),
      );
    }

    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");

    // Clean: sticky activation (click) then reload — must not raise beforeunload.
    const cleanTypes = [];
    const onCleanDialog = async (dialog) => {
      cleanTypes.push(dialog.type());
      await dialog.dismiss();
    };
    page.on("dialog", onCleanDialog);
    await editor.click();
    await page.reload({ waitUntil: "load" });
    page.off("dialog", onCleanDialog);
    expect(cleanTypes.filter((t) => t === "beforeunload")).toEqual([]);
    await expect(page.getByTestId("pipeline-config-editor")).toBeVisible();

    // Dirty: exactly one app-owned handler; source has no confirm/alert.
    // (Vite HMR may also register a willUnload stub — filtered out above.)
    await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
    await expect(page.getByTestId("pipeline-config-reload")).toBeEnabled();

    const appHandlers = await appUnloadSources();
    expect(appHandlers).toHaveLength(1);
    expect(appHandlers[0]).not.toMatch(/confirm/);
    expect(appHandlers[0]).not.toMatch(/alert/);

    // Successful save removes the app handler (page must stay alive for this).
    await page.getByTestId("pipeline-config-save").click();
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Сохранено");
    expect(await appUnloadSources()).toHaveLength(0);

    // Dirty unload prompt last: accept the beforeunload dialog so reload can
    // complete. (Dismiss-during-reload leaves an empty URL in this Chromium;
    // page.close({ runBeforeUnload: true }) did not surface a dialog here —
    // RESEARCH A2: assert only dialog.type(), never message text.)
    await page.getByTestId("pipeline-config-editor").fill("template: seminar\n");
    await expect(page.getByTestId("pipeline-config-reload")).toBeEnabled();
    const dirtyTypes = [];
    page.once("dialog", async (dialog) => {
      dirtyTypes.push(dialog.type());
      await dialog.accept();
    });
    await page.reload({ waitUntil: "load" });
    expect(dirtyTypes).toEqual(["beforeunload"]);
  });

  test("pipeline config dirty editor blocks in-app nav and Cancel keeps the draft", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    const archive = page
      .getByRole("navigation", { name: /основная навигация/i })
      .getByRole("link", { name: /^Архив$/ });
    await archive.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);

    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");

    await archive.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");
  });

  test("pipeline config dirty editor confirm navigates once without a second prompt", async ({
    page,
  }) => {
    const nativeTypes = [];
    page.on("dialog", async (dialog) => {
      nativeTypes.push(dialog.type());
      await dialog.dismiss();
    });

    await gotoAsRole(page, "admin", "/admin/pipeline");
    await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");

    await page
      .getByRole("navigation", { name: /основная навигация/i })
      .getByRole("link", { name: /^Архив$/ })
      .click();

    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByTestId("unsaved-changes-leave").click();

    await expect(page).toHaveURL(/\/archive$/);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(nativeTypes).toEqual([]);
  });

  test("pipeline config dirty editor blocks in-page section nav and Дайджест leave keeps the draft", async ({
    page,
  }) => {
    // D-13 / D-14 / D-15: the in-page section switch is ordinary SPA navigation, so the
    // Phase 19 guard must fire on a tab leave exactly as it does for the shell Архив link.
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    // Scope to the section landmark so the shell nav can never satisfy this click.
    const sectionNav = page.getByTestId("admin-section-nav");
    const digestTab = sectionNav.getByTestId("admin-tab-digest");
    await digestTab.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);

    // «Остаться» keeps both the draft and the URL, and the pipeline tab stays active.
    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");
    await expect(page.getByTestId("admin-tab-pipeline")).toHaveAttribute("aria-current", "page");

    // «Уйти без сохранения» lands on the digest section with the dialog closed.
    await digestTab.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByTestId("unsaved-changes-leave").click();

    await expect(page).toHaveURL(/\/admin\/digest$/);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByTestId("admin-digest-page")).toBeVisible();
    await expect(page.getByTestId("admin-tab-digest")).toHaveAttribute("aria-current", "page");
  });

  test("pipeline config dirty editor blocks the narrow section select leave", async ({ page }) => {
    // D-19: below sm the select navigates via navigate(), so the same guard fires.
    await page.setViewportSize({ width: 480, height: 800 });
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    const select = page.getByTestId("admin-section-select");
    await expect(select).toBeVisible();
    await select.selectOption("/admin/digest");

    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);

    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(editor).toHaveValue("template: lecture\n");
    await expect(select).toHaveValue("/admin/pipeline");

    await select.selectOption("/admin/digest");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByTestId("unsaved-changes-leave").click();

    await expect(page).toHaveURL(/\/admin\/digest$/);
    await expect(page.getByTestId("admin-section-select")).toHaveValue("/admin/digest");
  });

  test("pipeline config save disarms the guard and a reject keeps it armed", async ({ page }) => {
    const nativeTypes = [];
    page.on("dialog", async (dialog) => {
      nativeTypes.push(dialog.type());
      await dialog.dismiss();
    });

    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");
    await page.evaluate(() => {
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armRejectNextSave([
        { path: "template", message: "недопустимое значение" },
      ]);
    });

    await page.getByTestId("pipeline-config-save").click();
    await expect(page.getByTestId("pipeline-config-errors")).toBeVisible();

    const archive = page
      .getByRole("navigation", { name: /основная навигация/i })
      .getByRole("link", { name: /^Архив$/ });
    await archive.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);

    await page.getByTestId("pipeline-config-save").click();
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Сохранено");

    await archive.click();
    await expect(page).toHaveURL(/\/archive$/);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(nativeTypes).toEqual([]);
  });

  test("pipeline config reset confirm reverts to the last saved version", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    let message = null;
    page.once("dialog", async (dialog) => {
      message = dialog.message();
      await dialog.accept();
    });
    await page.getByTestId("pipeline-config-reload").click();

    await expect(editor).toHaveValue("");
    await expect(page.getByTestId("pipeline-config-status")).toHaveText("Изменений нет");
    await expect.poll(() => message).toBe(
      "Отменить изменения и вернуть последнюю сохранённую версию?",
    );
  });

  test("pipeline config reset confirm cancel keeps the edit", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const editor = page.getByTestId("pipeline-config-editor");
    await editor.fill("template: lecture\n");

    page.once("dialog", (dialog) => dialog.dismiss());
    await page.getByTestId("pipeline-config-reload").click();

    await expect(editor).toHaveValue("template: lecture\n");
  });

  test("pipeline config load error shows retry and recovers after reset", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await page.evaluate(() => window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armFailNextLoad());
    await page.reload();

    await expect(page.getByText("Не удалось загрузить конфиг", { exact: true })).toBeVisible();
    const retry = page.getByTestId("pipeline-config-retry");
    await expect(retry).toBeVisible();

    await page.evaluate(() =>
      window.__DIGEST_PIPELINE_CONFIG_HARNESS__.resetPipelineConfigHarness(),
    );
    await retry.click();

    await expect(page.getByTestId("pipeline-config-editor")).toBeVisible();
    await expect(page.getByText("Не удалось загрузить конфиг", { exact: true })).toHaveCount(0);
  });

  test("pipeline config nav item renders only in the in-page section switch", async ({ page }) => {
    await gotoAsRole(page, "admin", "/");
    const shell = page.getByRole("navigation", { name: /основная навигация/i });
    // ADUX-12 / D-10: the shell keeps exactly one admin entry and never a «Пайплайн» pill.
    await expect(shell.getByRole("link", { name: /^Админ$/ })).toHaveAttribute(
      "href",
      "/admin/digest",
    );
    await expect(shell.getByRole("link", { name: "Пайплайн", exact: true })).toHaveCount(0);

    await gotoAsRole(page, "admin", "/admin/digest");
    const pipelineTab = page
      .getByTestId("admin-section-nav")
      .getByRole("link", { name: "Пайплайн", exact: true });
    await expect(pipelineTab).toBeVisible();
    await expect(pipelineTab).toHaveAttribute("href", "/admin/pipeline");
  });

  test("employee deep-link renders Forbidden and no admin data at /admin/digest (IN-03)", async ({
    page,
  }) => {
    // IN-03: the retired case asserted on "/", where AdminLayout never renders — it could
    // not fail. Deep-link instead, where the layout really does mount for an employee.
    await gotoAsRole(page, "employee", "/admin/digest");

    const shell = page.getByRole("navigation", { name: /основная навигация/i });
    await expect(shell).toBeVisible();
    await expect(shell.getByRole("link", { name: /^Админ$/ })).toHaveCount(0);

    // Layout chrome renders by design (T-22-01)…
    await expect(page.getByTestId("admin-section-nav")).toBeVisible();
    await expect(page.getByTestId("forbidden-page")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Недостаточно прав", exact: true }),
    ).toBeVisible();

    // …but no admin data surface may.
    await expect(page.getByTestId("admin-digest-page")).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist")).toHaveCount(0);
    await expect(page.getByTestId("admin-shortlist-row")).toHaveCount(0);

    // Two level-1 headings is the intended structure on this branch: the layout's sr-only
    // section name plus ForbiddenPage's visible state name — pinned so the outline stays
    // unambiguous by design rather than by accident.
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(2);
    await expect(
      page.getByRole("heading", { level: 1, name: "Дайджест", exact: true }),
    ).toHaveCount(1);
    await expect(
      page.getByRole("heading", { level: 1, name: "Недостаточно прав", exact: true }),
    ).toHaveCount(1);
  });

  test("pipeline config no execution controls render", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const pageText = await page.getByTestId("admin-pipeline-page").innerText();
    for (const banned of ["Запустить", "Выполнить", "Запуск", "Планировщик", "Расписание"]) {
      expect(pageText).not.toContain(banned);
    }
    for (const banned of ["Запустить", "Выполнить", "Запуск", "Планировщик", "Расписание"]) {
      await expect(page.getByRole("button", { name: banned, exact: true })).toHaveCount(0);
    }
  });
});

async function resetIngestSourcesMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGEST_SOURCES_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesMockStore();
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingest-sources-section")).toBeVisible();
}

test.describe("Admin pipeline — ingest sources (SRC-01, D-01/D-02)", () => {
  test("ingest sources section above YAML — empty then add channel row", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    await expect(page.getByTestId("admin-pipeline-page")).toBeVisible();
    const section = page.getByTestId("ingest-sources-section");
    await expect(section).toBeVisible();
    await expect(page.getByTestId("ingest-sources-heading")).toHaveText("Источники ингеста");

    const editor = page.getByTestId("pipeline-config-editor");
    await expect(editor).toBeVisible();
    const sectionBox = await section.boundingBox();
    const editorBox = await editor.boundingBox();
    expect(sectionBox).not.toBeNull();
    expect(editorBox).not.toBeNull();
    expect(sectionBox.y).toBeLessThan(editorBox.y);

    await expect(page.getByTestId("ingest-sources-empty")).toBeVisible();
    await expect(page.getByTestId("ingest-sources-empty")).toContainText("Пока нет источников");
    await expect(page.getByTestId("ingest-sources-add")).toBeVisible();
    await expect(page.getByTestId("ingest-sources-id")).toBeVisible();
    // D-11/D-12: zero-enabled hint only when rows exist and none are enabled.
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveCount(0);

    const channelId = "UC_x5XG1OV2P6uZZ5FSMdItQ";
    await page.getByTestId("ingest-sources-kind").selectOption("channel");
    await page.getByTestId("ingest-sources-id").fill(channelId);
    await page.getByTestId("ingest-sources-label").fill("Demo channel");
    await page.getByTestId("ingest-sources-add").click();

    const row = page.getByTestId("ingest-source-row").filter({ hasText: channelId });
    await expect(row).toBeVisible();
    await expect(row.locator(".font-mono")).toHaveText(channelId);
    await expect(page.getByTestId("ingest-sources-id")).toHaveValue("");
    await expect(page.getByTestId("ingest-sources-label")).toHaveValue("");
    await expect(page.getByTestId("ingest-sources-empty")).toHaveCount(0);
  });

  test("ingest source id-help disclosure shows channel and playlist recipes", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    await expect(page.getByTestId("ingest-sources-id-help")).toContainText(
      "Только канонический id: UC… для канала или PL… для плейлиста.",
    );
    const disclosure = page.getByTestId("ingest-sources-section").locator("details");
    await expect(disclosure.getByText("Где взять id?", { exact: true })).toBeVisible();
    await disclosure.locator("summary").click();
    await expect(disclosure).toContainText("Идентификатор канала");
    await expect(disclosure).toContainText("UC…");
    await expect(disclosure).toContainText("list=");
    await expect(disclosure).toContainText("PL…");
  });

  test("ingest source disable enable delete and zero-enabled hint", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    const channelId = "UC_x5XG1OV2P6uZZ5FSMdItQ";
    await page.getByTestId("ingest-sources-id").fill(channelId);
    await page.getByTestId("ingest-sources-add").click();

    const row = page.getByTestId("ingest-source-row").filter({ hasText: channelId });
    await expect(row).toContainText("включён");
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveCount(0);

    const yt = row.getByRole("link", { name: "Открыть на YouTube", exact: true });
    await expect(yt).toHaveAttribute("href", `https://www.youtube.com/channel/${channelId}`);
    await expect(yt).toHaveAttribute("target", "_blank");
    await expect(yt).toHaveAttribute("rel", "noopener noreferrer");

    await row.getByRole("button", { name: "Выключить", exact: true }).click();
    await expect(row).toContainText("выключен");
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toBeVisible();
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveText(
      "Нет включённых источников — новые видео собираться не будут",
    );

    await row.getByRole("button", { name: "Включить", exact: true }).click();
    await expect(row).toContainText("включён");
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveCount(0);

    let confirmMessage = null;
    page.once("dialog", async (dialog) => {
      confirmMessage = dialog.message();
      await dialog.accept();
    });
    await row.getByRole("button", { name: "Удалить", exact: true }).click();
    await expect.poll(() => confirmMessage).toBe(
      `Удалить источник ${channelId}? Это действие нельзя отменить.`,
    );
    await expect(page.getByTestId("ingest-source-row").filter({ hasText: channelId })).toHaveCount(0);
    await expect(page.getByTestId("ingest-sources-empty")).toBeVisible();
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveCount(0);
  });

  test("ingest source add reject keeps typed values and shows structured errors", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    await page.evaluate(() => {
      window.__DIGEST_INGEST_SOURCES_HARNESS__.armRejectNextAdd([
        { path: "source_id", message: "Этот источник уже добавлен" },
      ]);
    });

    const channelId = "UC_x5XG1OV2P6uZZ5FSMdItQ";
    await page.getByTestId("ingest-sources-id").fill(channelId);
    await page.getByTestId("ingest-sources-label").fill("Keep me");
    await page.getByTestId("ingest-sources-add").click();

    const errors = page.getByTestId("ingest-sources-errors");
    await expect(errors).toBeVisible();
    await expect(errors).toContainText("Проверьте данные источника");
    await expect(errors).toContainText("source_id:");
    await expect(errors).toContainText("Этот источник уже добавлен");
    await expect(page.getByTestId("ingest-sources-id")).toHaveValue(channelId);
    await expect(page.getByTestId("ingest-sources-label")).toHaveValue("Keep me");
    await expect(page.getByTestId("ingest-source-row")).toHaveCount(0);
  });

  test("ingest source toggle failure keeps prior state and shows inline error", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    const channelId = "UC_x5XG1OV2P6uZZ5FSMdItQ";
    await page.getByTestId("ingest-sources-id").fill(channelId);
    await page.getByTestId("ingest-sources-add").click();
    const row = page.getByTestId("ingest-source-row").filter({ hasText: channelId });
    await expect(row).toContainText("включён");

    await page.evaluate(() => {
      window.__DIGEST_INGEST_SOURCES_HARNESS__.armFailNextSetEnabled();
    });
    await row.getByRole("button", { name: "Выключить", exact: true }).click();

    await expect(row).toContainText("включён");
    await expect(row).toContainText("Не удалось обновить источник. Повторите действие.");
    await expect(page.getByTestId("ingest-sources-zero-enabled")).toHaveCount(0);
  });
});

test.describe("Admin pipeline — ingest sourceFormDirty (ADUX-10, D-03/D-04)", () => {
  test("sourceFormDirty id arms Phase 19 guard on Дайджест leave", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    await page.getByTestId("ingest-sources-id").fill("UC_x5XG1OV2P6uZZ5FSMdItQ");

    const digestTab = page.getByTestId("admin-section-nav").getByTestId("admin-tab-digest");
    await digestTab.click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(page.getByRole("dialog")).toHaveCount(1);

    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(page.getByTestId("ingest-sources-id")).toHaveValue("UC_x5XG1OV2P6uZZ5FSMdItQ");

    await digestTab.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByTestId("unsaved-changes-leave").click();
    await expect(page).toHaveURL(/\/admin\/digest$/);
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("sourceFormDirty label arms Phase 19 guard; kind-only does not", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    await page.getByTestId("ingest-sources-kind").selectOption("playlist");
    const digestTab = page.getByTestId("admin-section-nav").getByTestId("admin-tab-digest");
    await digestTab.click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/digest$/);

    await page.getByTestId("admin-section-nav").getByTestId("admin-tab-pipeline").click();
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await expect(page.getByTestId("ingest-sources-section")).toBeVisible();

    await page.getByTestId("ingest-sources-label").fill("Only label");
    await digestTab.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
      "Есть несохранённые изменения. Уйти без сохранения?",
    );
    await expect(page).toHaveURL(/\/admin\/pipeline$/);
    await page.getByTestId("unsaved-changes-stay").click();
    await expect(page.getByTestId("ingest-sources-label")).toHaveValue("Only label");
  });

  test("successful add clears sourceFormDirty so leave proceeds without dialog", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);

    const channelId = "UC_x5XG1OV2P6uZZ5FSMdItQ";
    await page.getByTestId("ingest-sources-id").fill(channelId);
    await page.getByTestId("ingest-sources-label").fill("Temp");
    await page.getByTestId("ingest-sources-add").click();
    await expect(page.getByTestId("ingest-source-row").filter({ hasText: channelId })).toBeVisible();
    await expect(page.getByTestId("ingest-sources-id")).toHaveValue("");
    await expect(page.getByTestId("ingest-sources-label")).toHaveValue("");

    const digestTab = page.getByTestId("admin-section-nav").getByTestId("admin-tab-digest");
    await digestTab.click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/digest$/);
  });
});

test.describe("Admin Digest — предпросмотр черновика в читательском рендере (ADUX-07, ADUX-08)", () => {
  test("черновик открывается на предпросмотре с баннером", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/materials/sql-dashboards-for-audit-reporting");

    const banner = page.getByTestId("material-preview-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toContainText("Черновик — предпросмотр, не опубликовано");

    await expect(
      page.getByRole("heading", {
        level: 1,
        name: "SQL Dashboards for Audit Reporting",
        exact: true,
      }),
    ).toBeVisible();

    // D-02: the same reader container, proven attached — the draft seed's body is
    // empty, so the container is zero-height by construction (never toBeVisible()).
    await expect(page.getByTestId("material-prose")).toHaveCount(1);

    // D-08: empty payload arrays + the pre-existing length>0 gates hide both blocks.
    await expect(page.getByTestId("material-tags")).toHaveCount(0);
    await expect(page.getByTestId("material-related")).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Связанные материалы" }),
    ).toHaveCount(0);
  });

  test("ready-материал уходит на читательский маршрут без баннера", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/materials/building-production-rag-systems");

    // Host-anchored: /admin/materials/{slug} also *ends* with /materials/{slug},
    // so a bare trailing-path regex would pass without any redirect happening.
    await expect(page).toHaveURL(
      /^https?:\/\/[^/]+\/materials\/building-production-rag-systems$/,
    );
    await expect(page.getByTestId("material-preview-banner")).toHaveCount(0);
    // NOTE (WR-02): this test cannot observe whether the reader route actually *rendered*.
    // `gotoAsRole` ends in `page.reload()`, and by then the client-side redirect has already
    // moved the document to /materials/{slug} — the reload therefore loads the reader URL
    // directly in a fresh document, and the handoff under test is never asserted. The
    // rendered-surface proof lives in the click-path test below.
  });

  test("клик по «Открыть материал →» на готовой строке рендерит читательский маршрут, а не пустоту", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/digest");

    // D-10: the repointed shortlist link is the only in-app entry into the preview surface,
    // and it sits on ready rows as well as on the draft row.
    const readyRow = page
      .getByTestId("admin-shortlist-row")
      .filter({ hasText: "Building Production RAG Systems" });
    await readyRow.getByRole("button", { name: /Превью материала/ }).click();
    await page.getByRole("link", { name: /Открыть материал/ }).click();

    // Host-anchored: /admin/materials/{slug} also *ends* with /materials/{slug}.
    await expect(page).toHaveURL(
      /^https?:\/\/[^/]+\/materials\/building-production-rag-systems$/,
    );

    // CR-01: the URL is necessary but not sufficient — it also holds while the page renders
    // nothing at all. `redirectToReader` is never reset by the effect and is read by an early
    // return that is not guarded by `preview`, so the reused MaterialPage instance renders
    // <Navigate to={the URL we are already on}>, i.e. null. Pin the reader surface itself:
    // this slug is absent from the reader mock, so the honest reader surface is the reader 404.
    await expect(page.getByTestId("material-not-found")).toBeVisible();
  });

  test("сотрудник на предпросмотре черновика видит Forbidden, а не 404-заглушку", async ({
    page,
  }) => {
    await gotoAsRole(
      page,
      "employee",
      "/admin/materials/sql-dashboards-for-audit-reporting",
    );

    await expect(page.getByTestId("forbidden-page")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Недостаточно прав", exact: true }),
    ).toBeVisible();
    // The role gate owns the screen — no draft marker, no 404 splash.
    await expect(page.getByTestId("material-preview-banner")).toHaveCount(0);
    await expect(page.getByTestId("material-not-found")).toHaveCount(0);
    await expect(page.getByTestId("service-unavailable")).toHaveCount(0);
  });

  test("сотрудник на предпросмотре неизвестного slug видит тот же Forbidden", async ({
    page,
  }) => {
    await gotoAsRole(page, "employee", "/admin/materials/no-such-draft-slug");

    // D-03 / T-18-08: an existing slug and a missing slug are indistinguishable —
    // the seat-role gate fires before any slug lookup.
    await expect(page.getByTestId("forbidden-page")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Недостаточно прав", exact: true }),
    ).toBeVisible();
    await expect(page.getByTestId("material-not-found")).toHaveCount(0);
    await expect(page.getByTestId("material-preview-banner")).toHaveCount(0);
  });
});

async function resetIngestionScheduleMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGESTION_SCHEDULE_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleMockStore();
    window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingestion-schedule-section")).toBeVisible();
}

test.describe("Admin pipeline — automatic collection (ING-06, D-15/D-16/D-17)", () => {
  test("ingestion schedule sits between sources and YAML editor", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    const sources = page.getByTestId("ingest-sources-section");
    const schedule = page.getByTestId("ingestion-schedule-section");
    const editor = page.getByTestId("pipeline-config-editor");
    await expect(sources).toBeVisible();
    await expect(schedule).toBeVisible();
    await expect(page.getByTestId("ingestion-schedule-heading")).toHaveText("Автоматический сбор");
    await expect(editor).toBeVisible();

    const sourcesBox = await sources.boundingBox();
    const scheduleBox = await schedule.boundingBox();
    const editorBox = await editor.boundingBox();
    expect(sourcesBox).not.toBeNull();
    expect(scheduleBox).not.toBeNull();
    expect(editorBox).not.toBeNull();
    expect(sourcesBox.y).toBeLessThan(scheduleBox.y);
    expect(scheduleBox.y).toBeLessThan(editorBox.y);

    const harnessKeys = await page.evaluate(() => {
      const h = window.__DIGEST_INGESTION_SCHEDULE_HARNESS__;
      return h
        ? [
            typeof h.armFailNextLoad,
            typeof h.armFailNextSave,
            typeof h.resetIngestionScheduleHarness,
            typeof h.resetIngestionScheduleMockStore,
          ]
        : null;
    });
    expect(harnessKeys).toEqual(["function", "function", "function", "function"]);

    await expect(schedule.getByRole("button", { name: "Сохранить", exact: true })).toHaveCount(0);
  });

  test("ingestion schedule toggle patches immediately", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    const status = page.getByTestId("ingestion-schedule-status");
    const toggle = page.getByTestId("ingestion-schedule-enabled");
    await expect(status).toContainText("Включён");

    await toggle.click();
    await expect(status).toContainText("Выключен");
    await expect(status).toContainText("Сохранено");

    await toggle.click();
    await expect(status).toContainText("Включён");
    await expect(status).toContainText("Сохранено");
  });

  test("ingestion schedule time saves on blur, not on each keystroke", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    const before = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );

    const time = page.getByTestId("ingestion-schedule-time");
    await time.fill("07:30");

    const mid = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );
    expect(mid).toBe(before);

    await time.blur();
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Сохранено");
    await expect(time).toHaveValue("07:30");

    const after = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock(),
    );
    expect(after.patchCount).toBe(before + 1);
    expect(after.schedule.time_of_day).toBe("07:30");
  });

  test("ingestion schedule days normalize and refuse an empty week", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    for (const day of [2, 3, 4, 5, 6, 7]) {
      await page.getByTestId(`ingestion-schedule-day-${day}`).click();
      await expect(page.getByTestId(`ingestion-schedule-day-${day}`)).toHaveAttribute(
        "aria-pressed",
        "false",
      );
    }
    await expect(page.getByTestId("ingestion-schedule-day-1")).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    const beforeRefuse = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );
    await page.getByTestId("ingestion-schedule-day-1").click();
    await expect(page.getByTestId("ingestion-schedule-status")).toHaveText(
      "Выберите хотя бы один день недели.",
    );
    await expect(page.getByTestId("ingestion-schedule-day-1")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    const afterRefuse = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );
    expect(afterRefuse).toBe(beforeRefuse);

    await page.getByTestId("ingestion-schedule-day-6").click();
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Сохранено");
    const store = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock(),
    );
    expect(store.schedule.days_of_week).toEqual([1, 6]);
  });

  test("ingestion schedule save failure keeps the value and shows the message", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Включён");
    await page.evaluate(() => {
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.armFailNextSave();
    });
    await page.getByTestId("ingestion-schedule-enabled").click();

    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Включён");
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText(
      "Не удалось сохранить настройки сбора",
    );
    await expect(page.getByTestId("ingestion-schedule-section")).toBeVisible();
    await expect(page.getByTestId("ingestion-schedule-enabled")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  test("ingestion schedule load failure shows an error state without a fake success", async ({
    page,
  }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await page.waitForFunction(() => Boolean(window.__DIGEST_INGESTION_SCHEDULE_HARNESS__));
    await page.evaluate(() => {
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleMockStore();
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleHarness();
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.armFailNextLoad();
    });
    await page.reload();

    const section = page.getByTestId("ingestion-schedule-section");
    await expect(section).toBeVisible();
    await expect(page.getByTestId("ingestion-schedule-retry")).toBeVisible();
    await expect(page.getByTestId("ingestion-schedule-enabled")).toHaveCount(0);
    await expect(section).toContainText("Не удалось загрузить настройки сбора");

    await page.getByTestId("ingestion-schedule-retry").click();
    await expect(page.getByTestId("ingestion-schedule-enabled")).toBeVisible();
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Включён");
  });

  test("ingestion schedule changes do not mark the page dirty", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestionScheduleMock(page);

    await page.getByTestId("ingestion-schedule-enabled").click();
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Выключен");

    const digestTab = page.getByTestId("admin-section-nav").getByTestId("admin-tab-digest");
    await digestTab.click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(/\/admin\/digest$/);
  });
});
