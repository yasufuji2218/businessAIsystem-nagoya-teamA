import { test, expect } from "@playwright/test";

test.describe("ケモノガード ダッシュボード", () => {
  test("総合ダッシュボードが初期表示される", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: "総合ダッシュボード" }),
    ).toBeVisible();
    await expect(page.getByText("ライブステータス")).toBeVisible();
    await expect(page.getByText("夜間警戒レベル")).toBeVisible();
  });

  test("検知履歴画面で絞り込みができる", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "検知履歴" }).click();
    await expect(
      page.getByRole("heading", { name: "検知履歴", exact: true }),
    ).toBeVisible();

    const beforeCount = await page.locator("table tbody tr").count();

    await page
      .getByLabel("動物種別")
      .selectOption({ label: "イノシシ" });

    await expect(async () => {
      const afterCount = await page.locator("table tbody tr").count();
      expect(afterCount).toBeLessThanOrEqual(beforeCount);
      expect(afterCount).toBeGreaterThan(0);
    }).toPass();
  });

  test("分析レポート画面でカメラを切り替えると罠設置推奨度が変わる", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "分析レポート" }).click();
    await expect(
      page.getByRole("heading", { name: "分析レポート" }),
    ).toBeVisible();

    await expect(page.getByText("罠設置推奨度")).toBeVisible();
    await expect(page.getByText(/箱罠・くくり罠の設置を強く推奨/)).toBeVisible();

    await page.getByRole("button", { name: /CAM-01/ }).click();
    await expect(page.getByText(/罠の優先度は低めです/)).toBeVisible();
  });

  test("検知履歴のCSVダウンロードが実行される", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "検知履歴" }).click();

    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "CSVダウンロード" }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain("検知履歴_");
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
  });
});
