const { expect, test } = require("@playwright/test");

test.describe("web app main flows", () => {
  test("opens material by stable slug /materials/rag-systems", async ({ page }) => {
    // Prefer slug URLs for MAT-* stability (phase gate)
    await page.goto("/materials/rag-systems");

    await expect(page).toHaveURL(/\/materials\/rag-systems/);
    await expect(page.getByRole("heading", { name: /building production rag systems/i })).toBeVisible();
    await expect(page.getByTestId("material-format-badge")).toHaveText(/статья/i);
    await expect(page.getByTestId("material-prose")).toBeVisible();
    const toc = page.getByRole("navigation", { name: /содержание/i });
    await expect(toc).toBeVisible();
    await expect(toc.getByRole("link").first()).toBeVisible();
  });

  test("opens a material from the issue table of contents", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /новости ds для сва/i })).toBeVisible();
    await page.getByRole("link", { name: /building production rag systems/i }).click();

    await expect(page).toHaveURL(/\/materials\/rag-systems/);
    await expect(page.getByRole("heading", { name: /building production rag systems/i })).toBeVisible();
    // MAT-01/03: Статья badge + markdown prose (not legacy «Резюме» stub)
    await expect(page.getByTestId("material-format-badge")).toHaveText(/статья/i);
    await expect(page.getByTestId("material-prose")).toBeVisible();
    await expect(page.getByTestId("material-prose")).toContainText(/регламент/i);
    // TOC present when body_markdown has headings
    const toc = page.getByRole("navigation", { name: /содержание/i });
    await expect(toc).toBeVisible();
    await expect(toc.getByRole("link").first()).toBeVisible();
  });

  test("hides material dek block when empty", async ({ page }) => {
    await page.goto("/materials/empty-dek-article");

    await expect(page.getByRole("heading", { name: /empty dek article/i })).toBeVisible();
    await expect(page.getByTestId("material-dek")).toHaveCount(0);
    await expect(page.getByText(/заглушк|stub|dek отсутствует|нет описания/i)).toHaveCount(0);
  });

  test("shows empty current issue «Выпуск готовится» with archive CTA", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_EMPTY_CURRENT_ISSUE__ = true;
    });
    await page.goto("/");

    await expect(page.getByTestId("issue-loading")).toHaveCount(0);
    const empty = page.getByTestId("issue-empty");
    await expect(empty).toBeVisible();
    await expect(page.getByRole("heading", { name: "Выпуск готовится" })).toBeVisible();
    await expect(page.getByText(/свежий выпуск скоро появится/i)).toBeVisible();
    const archiveCta = page.getByRole("link", { name: /в архив/i });
    await expect(archiveCta).toBeVisible();
    // Archive page lands in 02-03; catch-all would redirect — assert CTA target only (D-30).
    await expect(archiveCta).toHaveAttribute("href", "/archive");
  });

  test("shows open voting callout with Выбрать тему CTA on current issue", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("issue-ready")).toBeVisible();
    const callout = page.getByTestId("editorial-callout");
    await expect(callout).toBeVisible();
    await expect(callout.getByText(/голосование открыто до/i)).toBeVisible();
    const cta = callout.getByRole("link", { name: /выбрать тему →/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/voting");
  });

  test("shows closed voting callout without topic-select CTA", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_CYCLE_CLOSED__ = true;
    });
    await page.goto("/");

    await expect(page.getByTestId("issue-ready")).toBeVisible();
    const callout = page.getByTestId("editorial-callout");
    await expect(callout).toBeVisible();
    await expect(callout.getByText(/голосование закрыто/i)).toBeVisible();
    await expect(callout.getByRole("link", { name: /выбрать тему/i })).toHaveCount(0);
  });

  test("hides voting callout when cycle is absent", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_NO_VOTING_CYCLE__ = true;
    });
    await page.goto("/");

    await expect(page.getByTestId("issue-ready")).toBeVisible();
    await expect(page.getByTestId("editorial-callout")).toHaveCount(0);
    await expect(page.getByText(/голосование открыто|голосование закрыто/i)).toHaveCount(0);
  });

  test("navigates Архив nav to past issue without voting callout", async ({ page }) => {
    await page.goto("/");

    const nav = page.getByRole("navigation", { name: /основная навигация/i });
    const archiveNav = nav.getByRole("link", { name: /^Архив$/ });
    await expect(archiveNav).toBeVisible();

    // Архив sits between Выпуск and База (D-28)
    const labels = await nav.getByRole("link").allTextContents();
    const archiveIdx = labels.findIndex((t) => t.trim() === "Архив");
    const issueIdx = labels.findIndex((t) => t.trim() === "Выпуск");
    const knowledgeIdx = labels.findIndex((t) => t.trim() === "База");
    expect(archiveIdx).toBeGreaterThan(issueIdx);
    expect(knowledgeIdx).toBeGreaterThan(archiveIdx);

    await archiveNav.click();
    await expect(page).toHaveURL(/\/archive/);
    await expect(page.getByRole("link", { name: /← К текущему выпуску/ })).toBeVisible();
    await expect(page.getByText(/текущий/i)).toHaveCount(0);

    await page.getByRole("link", { name: /выпуск №13/i }).click();
    await expect(page).toHaveURL(/\/issues\/13/);
    await expect(page.getByRole("heading", { name: /прошлый выпуск/i })).toBeVisible();
    await expect(page.getByText(/голосование открыто/i)).toHaveCount(0);
    await expect(page.getByRole("link", { name: /выбрать тему/i })).toHaveCount(0);
  });

  test("shows empty archive «Архив пуст» with CTA to current", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_EMPTY_ARCHIVE__ = true;
    });
    await page.goto("/archive");

    await expect(page.getByRole("heading", { name: "Архив пуст" })).toBeVisible();
    await expect(page.getByText(/прошлых выпусков пока нет/i)).toBeVisible();
    await expect(page.getByRole("link", { name: /← К текущему выпуску/ })).toBeVisible();
    const cta = page.getByRole("link", { name: /к текущему выпуску →/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/");
    await cta.click();
    await expect(page).toHaveURL(/\/$/);
  });

  // VOTE-02/04 · D-40…43, D-41 — leader strip + audit dek + 0 материалов (03-06)
  test("shows leader strip and 0 материалов without row Лидирует", async ({ page }) => {
    await page.goto("/voting");

    const strip = page.getByTestId("leader-strip");
    await expect(strip).toBeVisible();
    await expect(strip).toContainText(/Сейчас лидирует:\s*RAG в корпоративной среде\s*·\s*31 голосов/i);
    // Row badge forbidden (D-40); strip may contain «лидирует» as phrase
    await expect(page.getByText("Лидирует", { exact: true })).toHaveCount(0);

    await expect(page.getByText("0 материалов")).toBeVisible();
    await expect(
      page.getByRole("radio", { name: /AutoML для прогнозирования рисков/i }),
    ).toContainText(/0 материалов/i);
    await expect(
      page.getByRole("radio", { name: /RAG в корпоративной среде/i }),
    ).toContainText(/Корпоративный RAG/i);
  });

  // VOTE-03 · D-48…50 — closed / empty topics / no cycle under mock harnesses
  test("shows closed banner Цикл голосования закрыт with disabled radios", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_CLOSED__ = true;
    });
    await page.goto("/voting");

    await expect(page.getByTestId("voting-closed-banner")).toContainText(/Цикл голосования закрыт/i);
    await expect(page.getByTestId("leader-strip")).toBeVisible();
    const radios = page.getByRole("radio");
    await expect(radios.first()).toBeDisabled();
    await expect(page.getByTestId("confirm-vote")).toHaveCount(0);
    await expect(page.getByText(/Темы ещё не объявлены/i)).toHaveCount(0);
    await expect(page.getByText(/Сейчас нет активного голосования/i)).toHaveCount(0);
  });

  test("shows Темы ещё не объявлены empty state with К выпуску", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_NO_TOPICS__ = true;
    });
    await page.goto("/voting");

    await expect(page.getByRole("heading", { name: /Темы ещё не объявлены/i })).toBeVisible();
    const cta = page.getByRole("link", { name: /К выпуску/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/");
    await expect(page.getByTestId("voting-closed-banner")).toHaveCount(0);
    await expect(page.getByRole("radio")).toHaveCount(0);
  });

  test("shows Сейчас нет активного голосования without closed banner", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_NO_CYCLE__ = true;
    });
    await page.goto("/voting");

    await expect(page.getByText(/Сейчас нет активного голосования/i)).toBeVisible();
    const cta = page.getByRole("link", { name: /К выпуску/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/");
    await expect(page.getByTestId("voting-closed-banner")).toHaveCount(0);
    await expect(page.getByText(/Темы ещё не объявлены/i)).toHaveCount(0);
  });

  // VOTE-01/02 · D-40, D-44, D-47, D-52, D-56 — honest never-voted + confirm under mocks
  test("lets a reader pick a voting topic and confirm", async ({ page }) => {
    await page.goto("/voting");

    await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
    await expect(page.getByRole("status")).toContainText(/голос не отдан/i);
    await expect(page.getByText("Лидирует", { exact: true })).toHaveCount(0);

    const confirm = page.getByTestId("confirm-vote");
    await expect(confirm).toBeDisabled();
    await expect(confirm).toHaveText(/подтвердить голос/i);

    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await expect(confirm).toBeEnabled();
    await confirm.click();

    await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);
    await expect(confirm).toHaveText(/изменить голос/i);
    await expect(confirm).not.toHaveText(/голос принят/i);
    // D-47: pointless POST guard while selection equals confirmed topic
    await expect(confirm).toBeDisabled();

    await page.getByRole("radio", { name: /LLM для анализа аудиторских данных/i }).click();
    await expect(confirm).toBeEnabled();
  });

});

test.describe("web app UI states", () => {
  test("confirms a vote with loading then Изменить голос state", async ({ page }) => {
    await page.goto("/voting");

    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    const confirm = page.getByTestId("confirm-vote");
    await confirm.click();

    await expect(confirm).toHaveAttribute("data-state", "loading");
    await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);
    await expect(confirm).toHaveText(/изменить голос/i);
    await expect(confirm).not.toHaveText(/голос принят/i);
    await expect(confirm).toBeDisabled();
  });

  // KNOW-* honesty cases live in tests/knowledge.spec.js (04-09).
  test("keeps header search as an enlarged inline field without a modal", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("dialog")).toHaveCount(0);
    const headerSearch = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await expect(headerSearch).toBeVisible();

    const box = await headerSearch.boundingBox();
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
    expect(box?.width ?? 0).toBeGreaterThanOrEqual(240);

    await page.keyboard.press("Control+k");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(headerSearch).toBeFocused();

    await headerSearch.fill("RAG");
    await headerSearch.press("Enter");
    await expect(page).toHaveURL(/\/knowledge/);
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");
  });
});

test.describe("web app edge and error cases", () => {
  test("shows not-found recovery for an unknown material id", async ({ page }) => {
    await page.goto("/materials/does-not-exist");

    await expect(page.getByRole("heading", { name: /материал не найден/i })).toBeVisible();
    await expect(page.getByText(/ссылка устарела|ещё готовится/i)).toBeVisible();
    await expect(page.locator('img[src*="bad_gateway"]')).toHaveCount(0);
    await expect(page.getByRole("link", { name: /в архив/i })).toBeVisible();
    await page.getByRole("link", { name: /к выпуску/i }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: /новости ds для сва/i })).toBeVisible();
  });

  test("shows soft empty «Выпуск не найден» for unknown issue number", async ({ page }) => {
    await page.goto("/issues/99999");

    await expect(page.getByRole("heading", { name: "Выпуск не найден" })).toBeVisible();
    await expect(page.getByText(/проверьте номер выпуска/i)).toBeVisible();
    await expect(page.locator('img[src*="bad_gateway"]')).toHaveCount(0);
    const cta = page.getByRole("link", { name: /к текущему выпуску →/i });
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/");
    await cta.click();
    await expect(page).toHaveURL(/\/$/);
  });

  // D-21…D-23: page load failure → ServiceUnavailable splash + Retry (never mock fallback)
  test("shows ошибочка splash with bad_gateway art and recovers on Повторить", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_FAIL_NEXT_CONTENT__ = true;
    });
    await page.goto("/");

    const splash = page.getByTestId("service-unavailable");
    await expect(splash).toBeVisible();
    // Title lives on the art — no duplicate heading under the image
    await expect(splash.getByRole("heading", { name: /ошибочка вышла/i })).toHaveCount(0);
    await expect(splash.getByText(/не удалось загрузить/i)).toBeVisible();
    const art = splash.locator('img[src="/bad_gateway.png"]');
    await expect(art).toBeVisible();
    await expect(art).toHaveAttribute("alt", /котёнок.*ошибочка/i);
    // D-23: no HTTP status codes or stacktraces on screen
    await expect(splash).not.toContainText(/\b(502|503|500|404)\b/);
    await expect(splash).not.toContainText(/stack|traceback|Error:/i);
    // Primary UX: splash only — no Phase-1 profile ErrorPanel crowding the failure
    await expect(page.getByRole("heading", { name: /ошибка профиля/i })).toHaveCount(0);
    await expect(page.getByTestId("welcome-toast")).toHaveCount(0);
    await expect(page.getByText(/платформенный контур/i)).toHaveCount(0);
    await expect(page.getByText(/не удалось загрузить выпуск\. проверьте сеть/i)).toHaveCount(0);
    // D-21: must not silently show mock issue content
    await expect(page.getByTestId("issue-ready")).toHaveCount(0);
    await expect(page.getByRole("heading", { name: /новости ds для сва/i })).toHaveCount(0);

    const retry = splash.getByRole("button", { name: /^Повторить$/ });
    await expect(retry).toBeVisible();
    await retry.click();

    await expect(page.getByTestId("service-unavailable")).toHaveCount(0);
    await expect(page.getByTestId("issue-ready")).toBeVisible();
    await expect(page.getByRole("heading", { name: /новости ds для сва/i })).toBeVisible();
  });

  test("keeps confirm vote disabled when no topic is selected", async ({ page }) => {
    await page.goto("/voting");

    const confirm = page.getByTestId("confirm-vote");
    await expect(confirm).toBeDisabled();
    await expect(page.getByRole("status")).toContainText(/голос не отдан/i);
    await expect(page.getByRole("radio", { checked: true })).toHaveCount(0);
  });

  // VOTE-01 / D-47 — empty submit blocked client-side; no POST
  test("blocks empty submit with Выберите тему and does not POST", async ({ page }) => {
    const posts = [];
    page.on("request", (req) => {
      if (req.method() === "POST" && /\/voting\//.test(req.url())) {
        posts.push(req.url());
      }
    });

    await page.goto("/voting");
    const confirm = page.getByTestId("confirm-vote");
    await expect(page.getByRole("status")).toContainText(/голос не отдан/i);
    await expect(confirm).toBeDisabled();
    await expect(page.getByText(/Выберите тему/i)).toBeVisible();

    // Disabled CTA must not fire a vote POST even if force-clicked (VOTE-01)
    await confirm.click({ force: true });
    await expect(page.getByRole("status")).toContainText(/голос не отдан/i);
    expect(posts).toHaveLength(0);
  });

  test("shows vote error state and recovers on retry", async ({ page }) => {
    await page.goto("/voting?simulateError=1");

    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    const confirm = page.getByTestId("confirm-vote");
    await confirm.click();

    await expect(confirm).toHaveAttribute("data-state", "loading");
    await expect(confirm).toHaveAttribute("data-state", "error");
    await expect(confirm).toHaveText(/повторить/i);

    const alert = page.getByRole("alert");
    await expect(alert).toBeVisible();
    await expect(alert.getByRole("heading", { name: /ошибка сохранения/i })).toBeVisible();
    await expect(alert).toContainText(/временно недоступен|соединен/i);
    await expect(alert).toContainText(/попытка 1/i);
    // D-53: selection kept; no full ServiceUnavailable splash for mutation failure
    await expect(page.getByTestId("service-unavailable")).toHaveCount(0);
    await expect(page.getByRole("radio", { name: /RAG в корпоративной среде/i })).toBeChecked();

    await confirm.click();
    await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);
    await expect(confirm).toHaveText(/изменить голос/i);
    await expect(confirm).not.toHaveText(/голос принят/i);
    await expect(page.getByRole("alert")).toHaveCount(0);
  });

  // VOTE-03 · D-45 — first save toast «Голос сохранён»; A→B status + «Голос изменён»
  test("shows Голос сохранён then changes vote A→B with Голос изменён", async ({ page }) => {
    await page.goto("/voting");

    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await page.getByTestId("confirm-vote").click();

    await expect(page.getByTestId("vote-toast")).toContainText(/Голос сохранён/i);
    await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);

    await page.getByRole("radio", { name: /LLM для анализа аудиторских данных/i }).click();
    await page.getByTestId("confirm-vote").click();

    await expect(page.getByTestId("vote-toast")).toContainText(/Голос изменён/i);
    await expect(page.getByRole("status")).toContainText(
      /ваш голос:\s*LLM для анализа аудиторских данных/i,
    );
  });

  // VOTE-03 · D-51 — close mid-submit flips to read-only closed UI (not toast-only)
  test("flips to closed banner when submit races cycle close", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_CLOSE_ON_SUBMIT__ = true;
    });
    await page.goto("/voting");

    await expect(page.getByTestId("voting-closed-banner")).toHaveCount(0);
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await page.getByTestId("confirm-vote").click();

    await expect(page.getByTestId("voting-closed-banner")).toContainText(/Цикл голосования закрыт/i);
    await expect(page.getByRole("radio").first()).toBeDisabled();
    await expect(page.getByTestId("confirm-vote")).toHaveCount(0);
  });

  // D-54 — CAS conflict adopts server vote into radios/status
  test("adopts server vote on VOTE_CONFLICT response", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_VOTING_CONFLICT_ON_SUBMIT__ = true;
    });
    await page.goto("/voting");

    // Seed a prior server vote via conflict harness setup: first confirm succeeds
    await page.getByRole("radio", { name: /RAG в корпоративной среде/i }).click();
    await page.getByTestId("confirm-vote").click();
    await expect(page.getByRole("status")).toContainText(/ваш голос:\s*RAG в корпоративной среде/i);

    // Change selection then conflict: server stays on RAG
    await page.getByRole("radio", { name: /LLM для анализа аудиторских данных/i }).click();
    await page.getByTestId("confirm-vote").click();

    await expect(page.getByTestId("vote-conflict-banner")).toBeVisible();
    await expect(page.getByTestId("vote-conflict-banner")).toContainText(/на сервере/i);
    await expect(page.locator('[role="status"][aria-live="polite"]')).toContainText(
      /ваш голос:\s*RAG в корпоративной среде/i,
    );
    await expect(page.getByRole("radio", { name: /RAG в корпоративной среде/i })).toBeChecked();
  });

  // D-55 — initial ballot GET failure → ServiceUnavailable splash + Повторить
  test("shows ServiceUnavailable splash on ballot GET failure with Повторить", async ({ page }) => {
    await page.addInitScript(() => {
      window.__DIGEST_FAIL_NEXT_BALLOT__ = true;
    });
    await page.goto("/voting");

    const splash = page.getByTestId("service-unavailable");
    await expect(splash).toBeVisible();
    await expect(splash.getByText(/не удалось загрузить/i)).toBeVisible();
    await expect(splash.getByRole("button", { name: /^Повторить$/ })).toBeVisible();
    // Mutation ErrorPanel must not replace the splash for GET failure
    await expect(page.getByRole("heading", { name: /ошибка сохранения/i })).toHaveCount(0);
    await expect(page.getByTestId("confirm-vote")).toHaveCount(0);

    await splash.getByRole("button", { name: /^Повторить$/ }).click();
    await expect(page.getByTestId("service-unavailable")).toHaveCount(0);
    await expect(page.getByTestId("voting-page")).toBeVisible();
    await expect(page.getByTestId("confirm-vote")).toBeVisible();
  });
});

test.describe("web app responsive", () => {
  test("keeps mobile shell usable without horizontal overflow", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    // Include archive + material reader (ISSUE-04 / MAT-01 overflow sampling)
    for (const path of ["/", "/archive", "/materials/rag-systems", "/knowledge", "/voting"]) {
      await page.goto(path);

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(overflow.scrollWidth, `overflow on ${path}`).toBeLessThanOrEqual(overflow.clientWidth + 1);

      await expect(page.getByRole("navigation", { name: /основная навигация/i })).toBeVisible();
      await expect(page.getByRole("searchbox", { name: /поиск digest cds/i })).toBeVisible();
      await expect(page.getByTestId("shell-identity")).toBeVisible();
      await expect(page.getByTestId("shell-identity")).toHaveText("Мария Сидорова");
    }

    await page.goto("/");
    await page.screenshot({
      path: "docs/digest-cds/responsive-evidence/mobile-390-issue.png",
      fullPage: true,
    });
  });

  test("avoids horizontal overflow on a narrow 320px phone", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto("/");

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 1);

    const search = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await expect(search).toBeVisible();
    const box = await search.boundingBox();
    expect(box?.width ?? 0).toBeLessThanOrEqual(320);

    await page.screenshot({
      path: "docs/digest-cds/responsive-evidence/mobile-320-issue.png",
      fullPage: true,
    });
  });

  test("shows desktop identity and a wider header search", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    await expect(page.getByText("Мария Сидорова")).toBeVisible();

    const box = await page.getByRole("searchbox", { name: /поиск digest cds/i }).boundingBox();
    expect(box?.width ?? 0).toBeGreaterThanOrEqual(280);

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 1);

    await page.screenshot({
      path: "docs/digest-cds/responsive-evidence/desktop-1280-issue.png",
      fullPage: true,
    });
  });

  test("keeps voting confirm reachable on a phone viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/voting");

    const topic = page.getByRole("radio", { name: /RAG в корпоративной среде/i });
    await expect(topic).toBeVisible();
    await topic.click();
    const confirm = page.getByTestId("confirm-vote");
    await expect(confirm).toBeVisible();
    await expect(confirm).toBeInViewport();

    await page.screenshot({
      path: "docs/digest-cds/responsive-evidence/mobile-390-voting.png",
      fullPage: true,
    });
  });
});

/*
 * UI-SPEC backstops (02-UI-SPEC ## UI Considerations) — held for /gsd-verify-work.
 * Do NOT silent-pass: visual/held-out confirmation required.
 * - IssueToc: overflow / Russian plural (1/2/5+) / long title wrap
 * - Archive: grid overflow / 44px targets on mobile
 * - Material: prose overflow / sticky TOC / long title + deep headings
 * - EditorialCallout: long topic/date wrap
 * - Hero: long issue title reflow
 * - AppShell nav: mobile reflow without overlapping wordmark
 */
// Visual backstops stay a human gate at /gsd-verify-work.
// A skipped placeholder test is not an assertion Sonar can trust.
