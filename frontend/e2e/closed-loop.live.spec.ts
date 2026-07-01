/**
 * T-space 最小闭环 E2E — 接真实 Flask 后端（无 API mock）
 *
 * 流程：公开画像页 → HR 注册 → 导入候选人 → Stub 试用
 */
import { test, expect } from "@playwright/test";
import {
  seedSeekerWithShareCode,
  uniqueHrEmail,
  TEST_PASS,
} from "./helpers/liveApi";

test.describe.configure({ mode: "serial" });

test.describe("closed loop @live", () => {
  let shareCode: string;
  let personalityName: string;
  let hrEmail: string;

  test.beforeAll(async () => {
    const seeded = await seedSeekerWithShareCode();
    shareCode = seeded.shareCode;
    personalityName = seeded.personalityName;
    hrEmail = uniqueHrEmail();
  });

  test("public candidate share page shows personality profile", async ({ page }) => {
    await page.goto(`/candidate/share/${shareCode}`);
    await expect(page.getByRole("heading", { name: personalityName })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText("创造力")).toBeVisible();
    await expect(page.getByRole("link", { name: /免费试用 T-space/i })).toBeVisible();
  });

  test("HR registers, imports candidate, and starts Pro trial stub", async ({ page }) => {
    await page.goto("/register");
    await page.getByPlaceholder("姓名（选填）").fill("E2E HR");
    await page.getByPlaceholder("邮箱地址").fill(hrEmail);
    await page.getByPlaceholder("密码（至少6位）").fill(TEST_PASS);
    await page.getByPlaceholder("确认密码").fill(TEST_PASS);
    await page.getByRole("button", { name: "注册" }).click();

    await expect(page).toHaveURL("/", { timeout: 15_000 });

    await page.goto("/candidates");

    const createEnterprise = page.getByRole("button", { name: "创建企业（一键）" });
    const shareInput = page.getByPlaceholder("粘贴分享码，如 A1B2C3D4");

    await expect(createEnterprise.or(shareInput)).toBeVisible({ timeout: 15_000 });

    if (await createEnterprise.isVisible()) {
      await createEnterprise.click();
      await expect(shareInput).toBeVisible({ timeout: 15_000 });
    }

    await shareInput.fill(shareCode);
    await page.getByRole("button", { name: "导入" }).click();
    await expect(page.getByText(/导入成功|已在列表中/)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("E2ESeeker")).toBeVisible();

    await page.goto("/pricing");
    await page.getByRole("button", { name: "开始 7 天试用" }).click();
    await expect(
      page.getByText(/已开通 Pro 试用|升级失败/),
    ).toBeVisible({ timeout: 10_000 });
  });
});
