import "@testing-library/jest-dom/vitest";

// recharts の ResponsiveContainer が要求するが jsdom には実装がないためスタブを用意
if (typeof global.ResizeObserver === "undefined") {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
