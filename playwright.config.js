const path = require("path");
const { defineConfig } = require("@playwright/test");

// Stable project-local browser cache (avoids Cursor sandbox temp re-downloads).
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(__dirname, ".playwright-browsers");

/**
 * Playwright starts every webServer entry even with --project.
 * Filter servers so `npx playwright test --project=web` does not boot design-frontend.
 */
function selectedProjects() {
  const names = [];
  const args = process.argv;
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--project" || arg === "-p") {
      if (args[i + 1]) names.push(args[i + 1]);
      continue;
    }
    if (arg.startsWith("--project=")) names.push(arg.slice("--project=".length));
  }
  return names;
}

function wantsProject(name) {
  const selected = selectedProjects();
  return selected.length === 0 || selected.includes(name);
}

const webServers = [];

if (wantsProject("design-frontend")) {
  webServers.push({
    name: "design-frontend",
    // Node-based static server: works on macOS/Linux/Windows without `python`/`python3`.
    command: "npx --yes serve@14.2.4 . -l 8765 --no-port-switching",
    url: "http://127.0.0.1:8765/design-frontend/index.html",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  });
}

if (wantsProject("web")) {
  webServers.push({
    name: "web",
    command: "npm run dev --prefix web -- --host 127.0.0.1 --port 5174",
    url: "http://127.0.0.1:5174",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    // Highest priority over web/.env.local live-proof overrides (D-09 offline Playwright).
    env: {
      ...process.env,
      VITE_USE_MOCKS: "true",
    },
  });
}

module.exports = defineConfig({
  testDir: "./tests",
  use: {
    headless: true,
  },
  projects: [
    {
      name: "design-frontend",
      testMatch: /design-frontend\.spec\.js/,
      use: { baseURL: "http://127.0.0.1:8765" },
    },
    {
      name: "web",
      testMatch: /(web-app|auth|knowledge|razbory|admin)\.spec\.js/,
      use: { baseURL: "http://127.0.0.1:5174" },
    },
  ],
  webServer: webServers,
});
