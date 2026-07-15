/**
 * ケモノガード フロントエンド 参考実装（デザイン違い）
 *
 * frontend/WildlifeDashboard.jsx とは別デザイン案の単一ファイルモックアップです。
 * ダークテーマ・上部タブ切り替えのレイアウトを採用しています。
 *
 * 参考用ファイルであり、App.jsx からは配線していません。
 * 依存パッケージ: react / recharts / lucide-react
 */

import { useState } from "react";
import {
  ShieldAlert,
  Gauge,
  Bell,
  BarChart2,
  Camera,
  PawPrint,
  Clock,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const THEME = {
  bg: "#0f172a",
  panel: "#1e293b",
  border: "#334155",
  text: "#e2e8f0",
  subtext: "#94a3b8",
  accent: "#22d3ee",
  danger: "#f87171",
  warning: "#fbbf24",
};

const KPI_STATS = [
  { label: "本日の検知数", value: 47, icon: Bell },
  { label: "稼働カメラ", value: 6, icon: Camera },
  { label: "要注意種別", value: 2, icon: PawPrint },
];

const HOURLY = [
  { hour: "0時", 件数: 4 },
  { hour: "6時", 件数: 2 },
  { hour: "12時", 件数: 5 },
  { hour: "18時", 件数: 21 },
  { hour: "22時", 件数: 15 },
];

const ALERTS = [
  { id: "A-1", time: "22:14", text: "CAM-03 でイノシシを検知（最大3頭）" },
  { id: "A-2", time: "21:02", text: "CAM-05 で滞在時間が急増（撃退慣れの兆候）" },
  { id: "A-3", time: "19:40", text: "CAM-01 でサルの群れを検知" },
];

const TABS = [
  { key: "overview", label: "概要", icon: Gauge },
  { key: "alerts", label: "アラート", icon: ShieldAlert },
  { key: "reports", label: "レポート", icon: BarChart2 },
];

function StatCard({ label, value, icon: Icon }) {
  return (
    <div
      style={{
        background: THEME.panel,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: 20,
        flex: 1,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, color: THEME.subtext }}>
        <Icon size={18} aria-hidden />
        <span>{label}</span>
      </div>
      <p style={{ marginTop: 8, fontSize: 32, fontWeight: 700, color: THEME.text }}>
        {value}
      </p>
    </div>
  );
}

function OverviewTab() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", gap: 16 }}>
        {KPI_STATS.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>
      <div
        style={{
          background: THEME.panel,
          border: `1px solid ${THEME.border}`,
          borderRadius: 12,
          padding: 20,
        }}
      >
        <h2 style={{ color: THEME.text, fontSize: 16, marginBottom: 12 }}>
          時間帯別 検知数
        </h2>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={HOURLY}>
              <CartesianGrid stroke={THEME.border} vertical={false} />
              <XAxis dataKey="hour" tick={{ fill: THEME.subtext, fontSize: 12 }} />
              <YAxis tick={{ fill: THEME.subtext, fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: THEME.panel, border: `1px solid ${THEME.border}` }}
                labelStyle={{ color: THEME.text }}
              />
              <Bar dataKey="件数" fill={THEME.accent} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function AlertsTab() {
  return (
    <ul style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {ALERTS.map((a) => (
        <li
          key={a.id}
          style={{
            background: THEME.panel,
            border: `1px solid ${THEME.border}`,
            borderRadius: 10,
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: 12,
            color: THEME.text,
          }}
        >
          <Clock size={16} color={THEME.subtext} aria-hidden />
          <span style={{ color: THEME.subtext, minWidth: 48 }}>{a.time}</span>
          <span>{a.text}</span>
        </li>
      ))}
    </ul>
  );
}

function ReportsTab() {
  return (
    <div
      style={{
        background: THEME.panel,
        border: `1px solid ${THEME.border}`,
        borderRadius: 12,
        padding: 32,
        textAlign: "center",
        color: THEME.subtext,
      }}
    >
      レポート機能は準備中です（バックエンドAPI連携後に対応予定）。
    </div>
  );
}

export default function WildlifeGuardApp() {
  const [tab, setTab] = useState("overview");

  return (
    <div
      style={{
        minHeight: "100vh",
        background: THEME.bg,
        color: THEME.text,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 24px",
          borderBottom: `1px solid ${THEME.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <ShieldAlert color={THEME.accent} aria-hidden />
          <span style={{ fontWeight: 700, fontSize: 18 }}>ケモノガード</span>
        </div>
        <nav style={{ display: "flex", gap: 6 }}>
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 14px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                background: tab === key ? THEME.accent : "transparent",
                color: tab === key ? "#0f172a" : THEME.subtext,
                fontWeight: 600,
              }}
            >
              <Icon size={16} aria-hidden />
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main style={{ padding: 24 }}>
        {tab === "overview" && <OverviewTab />}
        {tab === "alerts" && <AlertsTab />}
        {tab === "reports" && <ReportsTab />}
      </main>
    </div>
  );
}
