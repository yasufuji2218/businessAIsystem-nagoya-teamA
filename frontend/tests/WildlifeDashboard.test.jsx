import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WildlifeDashboard from "../WildlifeDashboard";

describe("WildlifeDashboard", () => {
  beforeEach(() => {
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  it("総合ダッシュボード画面を初期表示する", () => {
    render(<WildlifeDashboard />);
    expect(
      screen.getByRole("heading", { name: "総合ダッシュボード" }),
    ).toBeInTheDocument();
    expect(screen.getByText("ライブステータス")).toBeInTheDocument();
  });

  it("サイドバーから検知履歴画面に切り替えられる", async () => {
    const user = userEvent.setup();
    render(<WildlifeDashboard />);

    await user.click(screen.getByRole("button", { name: /検知履歴/ }));

    expect(
      screen.getByRole("heading", { name: "検知履歴" }),
    ).toBeInTheDocument();
    expect(screen.getByText("検索・絞り込み")).toBeInTheDocument();
  });

  it("分析レポート画面でカメラを選択するとリスクスコアが切り替わる", async () => {
    const user = userEvent.setup();
    render(<WildlifeDashboard />);

    await user.click(screen.getByRole("button", { name: /分析レポート/ }));
    expect(
      screen.getByRole("heading", { name: "分析レポート" }),
    ).toBeInTheDocument();

    const camButton = screen.getByRole("button", { name: /CAM-01/ });
    await user.click(camButton);

    expect(screen.getByText(/罠の優先度は低めです/)).toBeInTheDocument();
  });

  it("CSVダウンロードボタンでBlobが生成されダウンロードが実行される", async () => {
    const user = userEvent.setup();
    render(<WildlifeDashboard />);

    await user.click(screen.getByRole("button", { name: /検知履歴/ }));
    await user.click(screen.getByRole("button", { name: "CSVダウンロード" }));

    expect(global.URL.createObjectURL).toHaveBeenCalledTimes(1);
    const blobArg = global.URL.createObjectURL.mock.calls[0][0];
    expect(blobArg).toBeInstanceOf(Blob);
    expect(blobArg.type).toContain("text/csv");
  });
});
