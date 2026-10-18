const { expect, test } = require("@playwright/test");

test.describe("SPA auth contracts", () => {
  test("rejects disallowed email domain without creating a session", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel(/^email$/i).fill("user@gmail.com");
    await page.getByLabel(/^пароль$/i).fill("any-password");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(
      page.getByText(/вход только с корпоративного домена сва/i),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByTestId("auth-sign-in-calls")).toHaveAttribute(
      "data-count",
      "0",
    );
  });

  test("navigates to current issue after successful login without returnUrl", async ({
    page,
  }) => {
    await page.goto("/login");

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole("heading", { name: /новости ds для сва/i }),
    ).toBeVisible();
  });

  test("redirects protected route to login with returnUrl when auth gate is on", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.__DIGEST_FORCE_AUTH_GATE__ = true;
    });

    await page.goto("/voting");

    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fvoting/);
    await expect(page.getByRole("heading", { name: /digest cds/i })).toBeVisible();
  });

  test("returns to returnUrl path after successful login", async ({ page }) => {
    await page.goto("/login?returnUrl=/voting");

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page).toHaveURL(/\/voting$/);
    await expect(page.getByTestId("confirm-vote")).toBeVisible();
  });

  test("ADMIN-08 / D-90: returnUrl /issues/{n} lands on published issue after login", async ({
    page,
  }) => {
    // Stub email link path → login?returnUrl=/issues/{n} → same-origin issue (sanitizeReturnUrl)
    await page.goto("/login?returnUrl=/issues/13");

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page).toHaveURL(/\/issues\/13$/);
    await expect(
      page.getByRole("heading", { name: /прошлый выпуск/i }),
    ).toBeVisible();
  });

  test("sanitizeReturnUrl rejects protocol-relative open redirects", async ({ page }) => {
    // T-05-20 — only same-origin relative paths; // and :// fall back to /
    await page.goto("/login?returnUrl=//evil.example/phish");

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole("heading", { name: /новости ds для сва/i }),
    ).toBeVisible();
  });

  test("shows retryable network banner when sign-in fails", async ({ page }) => {
    await page.goto("/login");
    await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
    await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armFailNextSignIn());

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page.getByRole("alert")).toContainText(/сервис входа временно недоступен/i);
    await expect(page.getByRole("button", { name: /повторить/i })).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("shows welcome toast after login then dismisses; no ping button", async ({ page }) => {
    await page.clock.install();

    await page.goto("/login");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page).toHaveURL(/\/$/);
    const toast = page.getByTestId("welcome-toast");
    await expect(toast).toBeVisible();
    await expect(toast).toContainText(/analyst@sberbank\.ru/i);
    // Neater: no raw role paren like (employee)
    await expect(toast).not.toContainText(/\(employee\)/i);
    await expect(page.getByRole("button", { name: /проверить ping/i })).toHaveCount(0);
    await expect(page.getByTestId("platform-ping")).toHaveCount(0);
    // Overlay: must not participate in document flow (no layout shift on dismiss)
    await expect(toast).toHaveCSS("position", "fixed");

    await page.clock.fastForward(5500);
    await expect(toast).toHaveCount(0);

    // Once per auth session — revisiting Выпуск must not show the toast again
    await page.getByRole("link", { name: /^Архив$/i }).click();
    await expect(page).toHaveURL(/\/archive/);
    await page.getByRole("link", { name: /^Выпуск$/i }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByTestId("welcome-toast")).toHaveCount(0);
  });

  test("shows profile stub link with display name on mobile and desktop", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/login");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /войти/i }).click();
    await expect(page).toHaveURL(/\/$/);

    const profile = page.getByTestId("shell-identity");
    await expect(profile).toBeVisible();
    await expect(profile).toHaveAttribute("href", "/profile");
    await profile.click();
    await expect(page).toHaveURL(/\/profile$/);
    await expect(page.getByTestId("profile-stub")).toBeVisible();
    await expect(page.getByText(/профиль.*позже|скоро|в следующих фазах/i)).toBeVisible();
  });

  test("Регистрация on login navigates to /register", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: /регистрация/i }).click();
    await expect(page).toHaveURL(/\/register$/);
  });

  test("login form is email and password only", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/^email$/i)).toBeVisible();
    await expect(page.getByLabel(/^пароль$/i)).toBeVisible();
    await expect(page.getByLabel(/^имя$/i)).toHaveCount(0);
    await expect(page.getByLabel(/^логин$/i)).toHaveCount(0);
  });

  test("OAuth2: shows Yandex ID button when enabled", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByTestId("yandex-oauth")).toBeVisible();
    await expect(page.getByTestId("yandex-oauth")).toHaveText(/яндекс id/i);
  });

  test("OAuth2: Yandex ID with non-corporate email is rejected and session dropped", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
    await page.evaluate(() =>
      window.__DIGEST_AUTH_HARNESS__.armOAuthEmail("someone@yandex.ru"),
    );

    await page.getByTestId("yandex-oauth").click();

    await expect(
      page.getByText(/вход только с корпоративного домена сва/i),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("OAuth2: Yandex ID with corporate email signs in", async ({ page }) => {
    await page.goto("/login");
    await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
    await page.evaluate(() =>
      window.__DIGEST_AUTH_HARNESS__.armOAuthEmail("analyst@sberbank.ru"),
    );

    await page.getByTestId("yandex-oauth").click();

    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole("heading", { name: /новости ds для сва/i }),
    ).toBeVisible();
  });

  test("shows Логин as shell identity after register", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/login");
    await page.getByRole("link", { name: /регистрация/i }).click();
    await expect(page).toHaveURL(/\/register$/);

    await page.getByLabel(/^логин$/i).fill("Иван Петров");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByTestId("shell-identity")).toHaveText("Иван Петров");
    await expect(page.getByText("Мария Сидорова")).toHaveCount(0);
  });

  test("rejects disallowed email domain on register without signUp", async ({
    page,
  }) => {
    await page.goto("/register");

    await page.getByLabel(/^логин$/i).fill("Ник");
    await page.getByLabel(/^email$/i).fill("user@gmail.com");
    await page.getByLabel(/^пароль$/i).fill("any-password");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    await expect(
      page.getByText(/вход только с корпоративного домена сва/i),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByTestId("auth-sign-up-calls")).toHaveAttribute(
      "data-count",
      "0",
    );
  });

  test("blocks empty Логин on register without signUp", async ({ page }) => {
    await page.goto("/register");

    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    await expect(page.getByRole("alert")).toContainText(/заполните поле/i);
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByTestId("auth-sign-up-calls")).toHaveAttribute(
      "data-count",
      "0",
    );
  });

  test("returns to returnUrl path after successful register", async ({
    page,
  }) => {
    await page.goto("/register?returnUrl=/voting");

    await page.getByLabel(/^логин$/i).fill("Голосник");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    await expect(page).toHaveURL(/\/voting$/);
    await expect(page.getByTestId("confirm-vote")).toBeVisible();
  });

  test("shows retryable network banner when signUp fails", async ({ page }) => {
    await page.goto("/register");
    await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
    await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armFailNextSignUp());

    await page.getByLabel(/^логин$/i).fill("Ник");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    await expect(page.getByRole("alert")).toContainText(/сервис входа временно недоступен/i);
    await expect(page.getByRole("button", { name: /повторить/i })).toBeVisible();
    await expect(page).toHaveURL(/\/register/);
  });

  test("post-register copy never claims a confirmation letter", async ({ page }) => {
    await page.goto("/register");
    await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
    await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession());

    await page.getByLabel(/^логин$/i).fill("Ник");
    await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
    await page.getByLabel(/^пароль$/i).fill("correct-horse");
    await page.getByRole("button", { name: /зарегистрироваться/i }).click();

    const alert = page.getByRole("alert");
    await expect(alert).toContainText(
      /Регистрация завершена\. Аккаунт активен — войдите/i,
    );
    await expect(alert).not.toContainText(/письм/i);
    await expect(page).toHaveURL(/\/register/);
  });
});
