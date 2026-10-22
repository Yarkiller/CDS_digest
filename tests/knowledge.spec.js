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
    await expect(page.getByLabel(/^(теги|формат|тема)$/i)).toHaveCount(0);

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

/** X-1: the request counter installed at the `searchKnowledge` boundary (UI-SPEC X-1). */
const SEARCH_COUNT_KEY = "__DIGEST_KNOWLEDGE_SEARCH_COUNT__";

/**
 * Reset the counter on every new document, so «reload ⇒ 1 request» stays
 * distinguishable from «a cache survived F5» (27-03).
 */
async function installKnowledgeCounter(page) {
  await page.addInitScript((key) => {
    window[key] = 0;
  }, SEARCH_COUNT_KEY);
}

/** Anti-vacuum read: a missing instrument throws instead of reading 0 (T-27-05). */
async function readCount(page) {
  return page.evaluate((key) => {
    if (typeof window[key] !== "number") {
      throw new Error("knowledge search counter not installed");
    }
    return window[key];
  }, SEARCH_COUNT_KEY);
}

async function expectCount(page, n, label) {
  await expect.poll(() => readCount(page), { timeout: 4000, message: label }).toBe(n);
}

/** Hits are anchors rendered by MaterialListRow — there is no result-row testid. */
const hitLinks = (page) => page.locator('a[href^="/materials/"]');

/**
 * Settle gate for the knowledge surface itself.
 *
 * A URL assertion is necessary but not sufficient: the issue page (`/`) renders an
 * `IssueToc` whose `/materials/{id}` anchors carry the same accessible names as the
 * knowledge hits, and `navigate()` updates the URL one commit before React swaps the
 * route. Asserting a row right after `toHaveURL` can therefore pass against the OUTGOING
 * surface while the new page has not even started its request (observed: the counter read
 * 0 with the row «visible»). `kb-role-chips` and the live region exist only on the
 * knowledge page, so gating on them makes every later row assertion meaningful.
 */
const knowledgeSurface = (page) => page.getByTestId("kb-role-chips");

async function expectKnowledgeSettled(page, summary) {
  await expect(knowledgeSurface(page)).toBeVisible();
  await expect(page.locator('p[aria-live="polite"]')).toHaveText(summary);
}

/**
 * X-2 is a harness-side instrument (UI-SPEC: «тест-харнесс, page.evaluate»), never app code.
 * It samples the in-flight affordances the page exposes and keeps every label it has seen.
 */
const AFFORDANCE_LOG_KEY = "__KB_AFFORDANCE_LOG__";

async function installAffordanceCollector(page) {
  await page.evaluate((logKey) => {
    if (window.__KB_AFFORDANCE_OBSERVER__) return;
    window[logKey] = [];
    function sample() {
      const labels = [];
      if (document.querySelector('[data-state="loading"]')) labels.push("loading-state");
      if (document.querySelector("#kb-search[disabled]")) labels.push("field-disabled");
      if (document.querySelector('[aria-live="polite"]')?.textContent?.trim() === "Ищем…") {
        labels.push("live-searching");
      }
      for (const label of labels) {
        if (!window[logKey].includes(label)) window[logKey].push(label);
      }
    }
    sample();
    const observer = new MutationObserver(sample);
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["disabled", "data-state"],
    });
    window.__KB_AFFORDANCE_OBSERVER__ = observer;
  }, AFFORDANCE_LOG_KEY);
}

async function resetAffordanceLog(page) {
  await installAffordanceCollector(page);
  await page.evaluate((logKey) => {
    window[logKey].length = 0;
  }, AFFORDANCE_LOG_KEY);
}

async function affordanceLog(page) {
  return page.evaluate((logKey) => [...window[logKey]], AFFORDANCE_LOG_KEY);
}

test.describe("KNOW-05 header submit runs the search", () => {
  test.beforeEach(async ({ page }) => {
    await installKnowledgeCounter(page);
  });

  test("header submit renders results from ?q", async ({ page }) => {
    await page.goto("/");

    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);
    await expectKnowledgeSettled(page, "Показано 2");
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");
    await expectCount(page, 1, "header submit");
  });

  test("changing ?q while mounted replaces the rows", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();

    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("SQL");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge\?q=SQL$/);
    await expectKnowledgeSettled(page, "Показано 5");
    await expect(page.getByRole("link", { name: /anomaly detection in audit pipelines/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toHaveCount(0);
    await expectCount(page, 2, "q change");
  });

  test("header submit issues exactly one search request", async ({ page }) => {
    await page.goto("/");

    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");
    // Settle first: a counter read before settle cannot distinguish 1 from 0.
    await expectKnowledgeSettled(page, "Показано 2");
    await expectCount(page, 1, "settled");

    await page.getByTestId("theme-toggle").click();
    await expectCount(page, 1, "theme toggle");

    await header.focus();
    await page.evaluate(() => document.activeElement?.blur());
    await expectCount(page, 1, "focus change");

    await header.fill("SQL");
    await expectCount(page, 1, "typing");

    // Covers timer-driven re-renders. The 4 s kb-filter-toast timer is unreachable here:
    // setToast('Фильтр недоступен') only fires on an INVALID_ROLE response, which the mock
    // adapter never produces — waiting 4 s for it would assert nothing.
    await page.waitForTimeout(1200);
    await expectCount(page, 1, "idle window");
  });

  test("the header path shows the in-flight live region", async ({ page }) => {
    await page.goto("/");
    // Installed before Enter so the seed sample sees the pre-search tree.
    await resetAffordanceLog(page);

    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);
    // Settle on the knowledge surface, not on a bare row: the collector exists precisely to
    // survive the transient in-flight state, so it is read after the request has landed (a
    // post-settle toHaveText("Ищем…") would be flaky — the mock answers in ~80 ms).
    await expectKnowledgeSettled(page, "Показано 2");

    // C-10 non-vacuity control: all three affordances must have been observed.
    const log = await affordanceLog(page);
    expect(log).toContain("live-searching");
    expect(log).toContain("field-disabled");
    expect(log).toContain("loading-state");

    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();
  });

  test("a role chip change issues exactly one new request", async ({ page }) => {
    await page.goto("/knowledge?q=SQL");
    await expectKnowledgeSettled(page, "Показано 5");
    await expect(hitLinks(page)).toHaveCount(5);
    await expectCount(page, 1, "deep link");

    // UI-SPEC reading of ROADMAP criterion 3: a chip change IS a deliberate action and
    // fires exactly once (+1). The «no extra request» clause covers re-renders and history.
    await page.getByRole("button", { name: "DS", exact: true }).click();

    await expect(page.getByRole("link", { name: /pgvector for enterprise search/i })).toBeVisible();
    await expect(hitLinks(page)).toHaveCount(1);
    await expectCount(page, 2, "chip change");
    await expect(page.getByRole("button", { name: "DS", exact: true })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  test("a zero-hit query renders the empty state and no rows", async ({ page }) => {
    await page.goto("/knowledge?q=zzzz");

    await expect(page.getByRole("heading", { name: /ничего не нашли/i })).toBeVisible();
    await expect(hitLinks(page)).toHaveCount(0);
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Сбросить фильтр" })).toBeEnabled();
    await expect(page.locator('p[aria-live="polite"]')).toHaveText("Найдено 0 материалов");
    // The control that keeps the RAG assertion honest: a static row list could satisfy
    // C-01 without any search happening.
    await expectCount(page, 1, "zero hit");
  });

  test("a hint chip click fills the field without a request", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(knowledgeSurface(page)).toBeVisible();
    await expect(page.getByTestId("kb-hint-chips")).toBeVisible();

    await page.getByTestId("kb-hint-chips").getByRole("button", { name: "RAG", exact: true }).click();

    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");
    await expect(hitLinks(page)).toHaveCount(0);
    await expectCount(page, 0, "hint chip");
  });

  test("returning from a material restores the rows with no request", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expect(hitLinks(page)).toHaveCount(2);
    await expectCount(page, 1, "first load");

    // Installed before the click so the restore's own window is observed.
    await resetAffordanceLog(page);
    await hitLinks(page).first().click();
    await expect(page).toHaveURL(/\/materials\//);

    await page.goBack();
    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);
    await expect(hitLinks(page)).toHaveCount(2);
    // KNOW-05 criterion 4: the same rows, and no second trip to the adapter. The counter
    // lives inside runSearch, so a cache restore is structurally unable to bump it.
    await expectCount(page, 1, "restore");
    // No label at all: no live-searching, no field-disabled, no loading-state. The restored
    // view must not pretend to be searching.
    expect(await affordanceLog(page)).toEqual([]);

    // E3 · loading, pinned structurally: a role chip that gains a spinner, a data-state or an
    // aria-busy is the only way this invariant can break (a settled toBeEnabled() is a tautology).
    await expect(page.getByTestId("kb-role-chips").locator("[data-state], [aria-busy]")).toHaveCount(0);
  });

  test("a reloaded URL re-queries because the cache is memory-only", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expectCount(page, 1, "pre-reload");

    await page.reload();
    await expect(hitLinks(page)).toHaveCount(2);
    // installKnowledgeCounter re-installs 0 on the new document: a cache persisted to storage
    // would read 0 here, a memory-only cache reads 1.
    await expectCount(page, 1, "post-reload");
  });

  test("a first search renders no skeleton", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    // E5 · loading: the skeleton belongs to the append path (loadingMore) only.
    await expect(page.locator('[data-testid="kb-skeleton"]')).toHaveCount(0);
  });

  test("re-submitting the same q issues exactly one new request", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expectCount(page, 1, "first");

    // A deliberate act, not a re-render: the marker has to beat the cache (D-06).
    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);
    await expect(hitLinks(page)).toHaveCount(2);
    await expectCount(page, 2, "re-submit");
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");
  });

  test("the submitId marker is stripped after it is consumed", async ({ page }) => {
    await page.goto("/knowledge");
    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");
    await expectKnowledgeSettled(page, "Показано 2");

    // C-24: the opaque marker must not survive the navigation that consumed it.
    const readSubmitId = () =>
      page.evaluate(
        () => window.history.state?.usr?.submitId ?? window.history.state?.submitId ?? null,
      );
    await expect.poll(readSubmitId, { timeout: 4000, message: "submitId stripped" }).toBeNull();
    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);

    // A strip that left a consumable marker would double-fire on the next load.
    await page.reload();
    await expect(hitLinks(page)).toHaveCount(2);
    await expectCount(page, 1, "after reload");
  });

  test("a header submit resets the role filter", async ({ page }) => {    await page.goto("/knowledge?q=SQL");
    await expectKnowledgeSettled(page, "Показано 5");
    await page.getByRole("button", { name: "DS", exact: true }).click();
    await expect(hitLinks(page)).toHaveCount(1);
    await expectCount(page, 2, "chip narrows");

    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("RAG");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge\?q=RAG$/);
    // D-07: a header submission searches from a clean slate, so a previously narrowed chip
    // cannot silently hide hits. RAG + DS would be one row, RAG + Все is two.
    await expect(hitLinks(page)).toHaveCount(2);
    await expect(page.getByRole("button", { name: "Все", exact: true })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByRole("button", { name: "DS", exact: true })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    await expectCount(page, 3, "header resets role");
  });

  test("removing ?q clears the rows", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expect(hitLinks(page)).toHaveCount(2);
    await expectCount(page, 1, "loaded");

    // An empty header submit is a landing navigation, not an error (C-16).
    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill("");
    await header.press("Enter");

    await expect(page).toHaveURL(/\/knowledge$/);
    // A bare `return` on the empty branch would leave the two RAG rows on the landing.
    await expect(hitLinks(page)).toHaveCount(0);
    await expect(page.getByTestId("kb-hint-chips")).toBeVisible();
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("");
    await expectCount(page, 1, "no extra request");
  });

  test("a blank page-form submit shows the inline error and issues no request", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(knowledgeSurface(page)).toBeVisible();

    await page.getByRole("button", { name: "Найти", exact: true }).click();

    const inline = page.getByTestId("kb-inline-error");
    await expect(inline).toHaveText("Введите запрос");
    await expect(inline).toHaveAttribute("role", "alert");
    await expect(inline).toHaveId("kb-search-inline-error");
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveAttribute(
      "aria-describedby",
      "kb-search-inline-error",
    );
    // C-17: the page form owns no URL write yet — the blank submit stays put.
    await expect(page).toHaveURL(/\/knowledge$/);
    await expectCount(page, 0, "blank submit");
  });

  test("an overlong header submit is rejected inline with no request", async ({ page }) => {
    // One code point over MAX_QUERY_CODE_POINTS (500); the validator's own unit pin owns the cap.
    const tooLong = "a".repeat(501);

    await page.goto("/");
    const header = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await header.fill(tooLong);
    await header.press("Enter");

    await expect(page).toHaveURL(new RegExp(`/knowledge\\?q=a{501}$`));
    await expect(page.getByTestId("kb-inline-error")).toHaveText("Сократите запрос");
    await expect(hitLinks(page)).toHaveCount(0);
    // The landing rule keeps hints off any non-empty ?q.
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);
    await expect(page.getByTestId("kb-search-error")).toHaveCount(0);
    await expectCount(page, 0, "overlong");

    // C-18: no truncation anywhere — the full text survives in both inputs, and neither
    // carries a maxlength that could silently clip it.
    const pageField = page.getByRole("searchbox", { name: /поиск по базе знаний/i });
    expect(await pageField.inputValue()).toHaveLength(501);
    expect(await pageField.getAttribute("maxlength")).toBeNull();
    expect(await header.getAttribute("maxlength")).toBeNull();
  });

  test("the landing never coexists with a query", async ({ page }) => {
    // Overlong: no request, so `activeQuery` stays null — the frame that used to leak hints.
    await page.goto(`/knowledge?q=${"a".repeat(501)}`);
    await expect(page.getByTestId("kb-inline-error")).toHaveText("Сократите запрос");
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);

    // Zero-hit.
    await page.goto("/knowledge?q=zzzz");
    await expect(page.getByRole("heading", { name: /ничего не нашли/i })).toBeVisible();
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);

    // Populated.
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    await expect(page.getByTestId("kb-hint-chips")).toHaveCount(0);
  });

  test("a whitespace-only q is the landing", async ({ page }) => {
    await page.goto("/knowledge?q=%20");

    await expect(page.getByTestId("kb-hint-chips")).toBeVisible();
    await expect(hitLinks(page)).toHaveCount(0);
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("");
    await expectCount(page, 0, "whitespace");
  });

  test("the hint set is four fixed labels", async ({ page }) => {
    await page.goto("/knowledge");
    const chips = page.getByTestId("kb-hint-chips");
    await expect(chips).toBeVisible();
    await expect(chips.getByRole("button")).toHaveCount(4);
    for (const label of ["RAG", "SQL", "качество данных", "pgvector"]) {
      await expect(chips.getByRole("button", { name: label, exact: true })).toBeVisible();
    }
  });

  test("the live region carries only the status copy", async ({ page }) => {
    await page.goto("/knowledge?q=RAG");
    await expectKnowledgeSettled(page, "Показано 2");
    // E6 · long-text: the status line never echoes the query (T-27-14).
    const live = page.locator('p[aria-live="polite"]');
    expect(await live.textContent()).not.toMatch(/RAG/);
  });
});
