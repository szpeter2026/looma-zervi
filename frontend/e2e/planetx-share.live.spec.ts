/**
 * PlanetX Web 分享 E2E — 注册 → 答题 → 生成 HR 画像链接（真实后端）
 */
import { test, expect } from "@playwright/test";
import { uniqueHrEmail, TEST_PASS, SAAS_BASE } from "./helpers/liveApi";

test.describe("planetx share @live", () => {
  test("completes quiz and shows HR share link with candidate/share path", async ({ page }) => {
    const email = uniqueHrEmail("planetx");

    await page.goto("/");
    await page.waitForTimeout(2500);

    const emailInput = page.getByPlaceholder("你的星际邮箱");
    if (await emailInput.isVisible().catch(() => false)) {
      await emailInput.fill(email);
      await page.getByPlaceholder("至少6位").fill(TEST_PASS);
      await page.getByRole("button", { name: "✨ 注册" }).click();
    } else {
      test.skip(true, "Auth screen not visible — session may already exist");
    }

    await expect(page.getByText("正在寻找新的职业星球")).toBeVisible({ timeout: 15_000 });
    await page.getByText("正在寻找新的职业星球").click();

    await expect(page.getByText("星际人格测试")).toBeVisible({ timeout: 10_000 });
    await page.getByText("星际人格测试").click();

    for (let i = 0; i < 8; i++) {
      await page.getByRole("button", { name: /^A\./ }).click();
    }

    await expect(page.getByRole("button", { name: /分享给 HR/i })).toBeVisible({
      timeout: 15_000,
    });
    await page.getByRole("button", { name: /分享给 HR/i }).click();

    await expect(page.getByText(/candidate\/share\//)).toBeVisible({ timeout: 15_000 });
    const linkText = await page.locator("text=/candidate\\/share\\//").first().textContent();
    expect(linkText).toContain(SAAS_BASE.replace("http://", "").split(":")[0]);
  });
});
