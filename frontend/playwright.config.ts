import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright e2e test config for Looma-Zervi frontend monorepo.
 *
 * Usage:
 *   pnpm exec playwright test          — run all e2e tests
 *   pnpm exec playwright test --ui     — interactive UI mode
 *   pnpm exec playwright test e2e/poetry — run only Poetry tests
 *
 * The SaaS dev server auto-starts on port 5174.
 * Backend API is mocked via Playwright route interception.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  timeout: 30_000,
  expect: { timeout: 5_000 },

  use: {
    baseURL: "http://localhost:5174",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "saas-chrome",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "saas-mobile",
      use: {
        browserName: "chromium",
        viewport: { width: 375, height: 812 },
        isMobile: true,
        hasTouch: true,
        userAgent:
          "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
      },
    },
  ],

  webServer: {
    command: "pnpm dev:saas",
    url: "http://localhost:5174",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
