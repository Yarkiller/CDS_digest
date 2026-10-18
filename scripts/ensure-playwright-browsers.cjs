const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

/**
 * Keep browser binaries in the repo workspace so Cursor sandbox
 * temp caches (cursor-sandbox-cache) do not force a re-download.
 */
const browsersPath = path.join(__dirname, "..", ".playwright-browsers");
process.env.PLAYWRIGHT_BROWSERS_PATH = browsersPath;

function hasChromium() {
  if (!fs.existsSync(browsersPath)) return false;
  return fs.readdirSync(browsersPath).some((name) => name.startsWith("chromium"));
}

if (hasChromium()) {
  console.log(`Playwright browsers already installed at ${browsersPath}`);
  process.exit(0);
}

console.log(`Installing Playwright Chromium into ${browsersPath}`);
execSync("npx playwright install chromium", {
  stdio: "inherit",
  env: process.env,
  cwd: path.join(__dirname, ".."),
});
