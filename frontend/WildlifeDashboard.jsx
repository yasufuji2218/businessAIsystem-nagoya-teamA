/**
 * AI獣害対策SaaS「ケモノガード」フロントエンドモックアップ
 *
 * 単一ファイルで動作するSPA。サイドバーで3画面を切り替えます。
 *   ① 総合ダッシュボード
 *   ② リアルタイム検知履歴（検索・CSVエクスポート）
 *   ③ 獣害データ分析レポート（罠設置支援）
 *
 * バックエンドAPI開発中のため、全データはシード固定の擬似乱数で
 * 生成したリアルなダミーデータです（リロードしても同じ値になります）。
 *
 * 依存パッケージ: react / recharts / lucide-react / Tailwind CSS
 */

import { useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard,
  History,
  BarChart3,
  Camera,
  Clock,
  PawPrint,
  AlertTriangle,
  Bell,
  Download,
  Moon,
  Activity,
  TrendingUp,
  MapPin,
  Siren,
  Search,
  Leaf,
  Target,
  CircleDot,
  Wifi,
  WifiOff,
  Sparkles,
  Upload,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  fetchAppearance,
  fetchHabituation,
  fetchTrap,
  submitVideoAnalysisJob,
  fetchVideoAnalysisJob,
} from "./src/api";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  LabelList,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

/* ------------------------------------------------------------------ */
/* カラーパレット（CVD検証済み・コントラスト重視）                        */
/* ------------------------------------------------------------------ */

const COLORS = {
  // 動物種別（カテゴリカル・固定割り当て）
  サル: "#2a78d6",
  イノシシ: "#1baf7a",
  // 状態色（警戒レベルなど・系列色とは別枠）
  critical: "#d03b3b",
  warning: "#fab219",
  serious: "#ec835a",
  good: "#0ca30c",
  // チャートの地色
  grid: "#e1e0d9",
  axisText: "#52514e",
  muted: "#898781",
  // 単一系列（数量）用の青ランプ
  seqLight: "#9ec5f4",
  seqMid: "#3987e5",
  seqDark: "#1c5cab",
};

const ANIMALS = ["サル", "イノシシ"];
const CAMERAS = ["CAM-01", "CAM-02", "CAM-03", "CAM-04", "CAM-05", "CAM-06"];
const CAMERA_PLACES = {
  "CAM-01": "北側農道",
  "CAM-02": "果樹園 東",
  "CAM-03": "山際フェンス",
  "CAM-04": "水田 南",
  "CAM-05": "竹林入口",
  "CAM-06": "倉庫裏",
};
const ACTIONS = ["音声威嚇", "ライト点灯", "威嚇（音＋光）", "通知のみ"];

/* ------------------------------------------------------------------ */
/* ダミーデータ生成（シード固定でリロードしても同一）                     */
/* ------------------------------------------------------------------ */

function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function generateLog() {
  const rand = mulberry32(20260707);
  const records = [];
  const start = new Date(2026, 4, 1); // 2026-05-01
  const DAYS = 68; // 5/1 〜 7/7

  const pickAnimal = () => {
    const r = rand();
    if (r < 0.53) return "イノシシ";
    return "サル";
  };

  let id = 0;
  for (let d = 0; d < DAYS; d++) {
    const date = new Date(start);
    date.setDate(start.getDate() + d);
    const perDay = 1 + Math.floor(rand() * 4); // 1〜4件/日
    for (let i = 0; i < perDay; i++) {
      // 検知の約7割は夜間（18時〜翌4時）に集中させる
      const hour =
        rand() < 0.7
          ? [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4][Math.floor(rand() * 11)]
          : 5 + Math.floor(rand() * 13);
      const minute = Math.floor(rand() * 60);
      const second = 0;
      const animal = pickAnimal();
      const maxCount =
        animal === "サル"
          ? 1 + Math.floor(rand() * 11)
          : 1 + Math.floor(rand() * 5);
      id += 1;
      records.push({
        id: `DET-${String(id).padStart(4, "0")}`,
        year: date.getFullYear(),
        month: date.getMonth() + 1,
        day: date.getDate(),
        hour,
        minute,
        second,
        dateKey: `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`,
        datetimeLabel: `${date.getFullYear()}/${pad2(date.getMonth() + 1)}/${pad2(date.getDate())} ${pad2(hour)}:${pad2(minute)}:${pad2(second)}`,
        cameraId: CAMERAS[Math.floor(rand() * CAMERAS.length)],
        animal,
        maxCount,
        action: ACTIONS[Math.floor(rand() * ACTIONS.length)],
        staySec: 15 + Math.floor(rand() * 420),
      });
    }
  }
  records.sort((a, b) =>
    `${b.dateKey} ${pad2(b.hour)}:${pad2(b.minute)}` <
    `${a.dateKey} ${pad2(a.hour)}:${pad2(a.minute)}`
      ? -1
      : 1,
  );
  return records;
}

const FALLBACK_DETECTION_LOG = generateLog();
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/+$/, "");

function getAnimalColor(animal) {
  return COLORS[animal] || "#6b7280";
}

function getCameraPlace(cameraId) {
  return CAMERA_PLACES[cameraId] || "設置場所未登録";
}

function toFiniteNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function parseBackendTimestamp(timestamp) {
  if (!timestamp) return new Date(NaN);
  return new Date(String(timestamp).replace(" ", "T"));
}

function normalizeBackendDetection(row, index, receivedAtMs) {
  const timestamp = row.timestamp || "";
  const parsed = parseBackendTimestamp(timestamp);
  const hasValidDate = Number.isFinite(parsed.getTime());
  const year = hasValidDate ? parsed.getFullYear() : 0;
  const month = hasValidDate ? parsed.getMonth() + 1 : 0;
  const day = hasValidDate ? parsed.getDate() : 0;
  const hour = hasValidDate ? parsed.getHours() : 0;
  const minute = hasValidDate ? parsed.getMinutes() : 0;
  const second = hasValidDate ? parsed.getSeconds() : 0;
  const dateKey = hasValidDate
    ? `${year}-${pad2(month)}-${pad2(day)}`
    : "";
  const datetimeLabel = hasValidDate
    ? `${year}/${pad2(month)}/${pad2(day)} ${pad2(hour)}:${pad2(minute)}:${pad2(second)}`
    : String(timestamp || "timestamp unknown");

  return {
    id: `${timestamp}-${row.device_id || "camera"}-${index}`,
    year,
    month,
    day,
    hour,
    minute,
    second,
    dateKey,
    datetimeLabel,
    timestampMs: hasValidDate ? parsed.getTime() : 0,
    receivedAtMs,
    cameraId: row.device_id || "UNKNOWN",
    animal: row.animal_type || "不明",
    maxCount: 1,
    confidence: toFiniteNumber(row.confidence),
    action: row.action_triggered || "none",
    staySec: Math.round(toFiniteNumber(row.stay_duration)),
  };
}

async function fetchApiJson(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail || response.statusText);
  }

  return data;
}

async function fetchDetections(signal) {
  const data = await fetchApiJson("/detections?limit=10000", signal);
  const rows = Array.isArray(data?.detections) ? data.detections : [];
  const receivedAtMs = Date.now();

  return rows
    .map((row, index) => normalizeBackendDetection(row, index, receivedAtMs))
    .sort((a, b) => b.timestampMs - a.timestampMs);
}

function getTimelineContext(detectionLog) {
  const latest = detectionLog[0] || null;
  if (!latest) {
    return {
      latest: null,
      todayKey: "",
      todayLabel: "データなし",
    };
  }

  return {
    latest,
    todayKey: latest.dateKey,
    todayLabel: `${latest.year}年${latest.month}月${latest.day}日`,
  };
}

/* 時間帯別集計（夜間/日中を色分け） */
function buildHourlyData(detectionLog) {
  const bins = Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    label: `${h}時`,
    検知数: 0,
    isNight: h >= 18 || h <= 4,
  }));
  detectionLog.forEach((r) => {
    if (r.hour >= 0 && r.hour < 24) {
      bins[r.hour].検知数 += 1;
    }
  });
  return bins;
}

/* 曜日別集計 */
function buildWeekdayData(detectionLog) {
  const names = ["日", "月", "火", "水", "木", "金", "土"];
  const bins = names.map((n) => ({ label: n, 検知数: 0 }));
  detectionLog.forEach((r) => {
    if (!r.dateKey) return;
    const dow = new Date(r.year, r.month - 1, r.day).getDay();
    if (Number.isInteger(dow) && bins[dow]) {
      bins[dow].検知数 += 1;
    }
  });
  return bins;
}

/* 月次比較（前月比増減率と季節バースト） */
function buildMonthlyData(detectionLog) {
  const counts = new Map();
  detectionLog.forEach((r) => {
    if (!r.year || !r.month) return;
    const key = `${r.year}-${pad2(r.month)}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  const sortedKeys = Array.from(counts.keys()).sort();
  if (sortedKeys.length === 0) return [];

  const latestKey = sortedKeys[sortedKeys.length - 1];
  const nowKey = `${new Date().getFullYear()}-${pad2(new Date().getMonth() + 1)}`;

  return sortedKeys.map((key, index) => {
    const [year, month] = key.split("-");
    const count = counts.get(key);
    const previousCount = index > 0 ? counts.get(sortedKeys[index - 1]) : null;
    const delta =
      previousCount == null || previousCount === 0
        ? null
        : Math.round(((count - previousCount) / previousCount) * 100);

    return {
      month: `${Number(month)}月`,
      検知数: count,
      delta,
      burst: delta != null && delta >= 40,
      partial: key === latestKey && key === nowKey,
    };
  });
}

function getAvailableValues(baseValues, detectionLog, key) {
  return Array.from(
    new Set([
      ...baseValues,
      ...detectionLog.map((row) => row[key]).filter(Boolean),
    ]),
  );
}

function formatClockTime(record) {
  return `${pad2(record.hour)}:${pad2(record.minute)}:${pad2(record.second || 0)}`;
}

function formatShortDateTime(record) {
  return `${record.month}/${record.day} ${formatClockTime(record)}`;
}

function formatElapsedSince(timeMs, nowMs) {
  if (!timeMs) return "未取得";
  const seconds = Math.max(0, Math.floor((nowMs - timeMs) / 1000));
  if (seconds < 5) return "たった今";
  if (seconds < 60) return `${seconds}秒前`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}分前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}時間前`;
  return `${Math.floor(hours / 24)}日前`;
}

function buildAlertSummary(detectionLog) {
  const latest = detectionLog[0];
  if (!latest) {
    return {
      level: "低",
      totalCount: 0,
      nightCount: 0,
      topAnimal: "なし",
      message: "検知履歴がないため、警戒レベルは低です。",
    };
  }

  const referenceMs = latest.timestampMs || Date.now();
  const threeDaysMs = 3 * 24 * 60 * 60 * 1000;
  const recentRecords = detectionLog.filter(
    (record) => record.timestampMs && record.timestampMs >= referenceMs - threeDaysMs,
  );
  const records = recentRecords.length > 0 ? recentRecords : detectionLog;
  const nightCount = records.filter((record) => record.hour >= 18 || record.hour <= 4).length;
  const animalCounts = records.reduce((counts, record) => {
    counts[record.animal] = (counts[record.animal] || 0) + 1;
    return counts;
  }, {});
  const topAnimal =
    Object.entries(animalCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "なし";
  const boarCount = animalCounts.イノシシ || 0;
  const avgStay =
    records.reduce((sum, record) => sum + toFiniteNumber(record.staySec), 0) /
    Math.max(records.length, 1);
  const score = records.length + nightCount * 2 + boarCount * 1.5 + avgStay / 30;
  const level = score >= 18 ? "高" : score >= 6 ? "中" : "低";
  const message =
    level === "高"
      ? "検知件数と夜間活動が多いため、重点監視が必要です。"
      : level === "中"
        ? "一定数の検知があります。推移を確認してください。"
        : "直近の検知は少なく、警戒レベルは低めです。";

  return {
    level,
    totalCount: records.length,
    nightCount,
    topAnimal,
    message,
  };
}

/* 滞在時間の週次推移（撃退慣れ検知付き）
   Warn=true の点は「滞在時間が3週連続で増加＝撃退慣れの兆候」 */
const WEEKLY_STAY_DATA = [
  { week: "4/27週", サル: 34, イノシシ: 52 },
  { week: "5/4週", サル: 31, イノシシ: 48 },
  { week: "5/11週", サル: 38, イノシシ: 55 },
  { week: "5/18週", サル: 36, イノシシ: 61 },
  { week: "5/25週", サル: 44, イノシシ: 58 },
  { week: "6/1週", サル: 52, イノシシ: 64 },
  { week: "6/8週", サル: 61, イノシシ: 60, サルWarn: true },
  { week: "6/15週", サル: 75, イノシシ: 72, サルWarn: true },
  { week: "6/22週", サル: 88, イノシシ: 79, サルWarn: true },
  { week: "6/29週", サル: 96, イノシシ: 91, サルWarn: true, イノシシWarn: true },
  { week: "7/6週", サル: 104, イノシシ: 98, サルWarn: true, イノシシWarn: true },
];

/* カメラ別分析（罠設置支援）: 各指標は0〜100のリスクスコア */
const CAMERA_ANALYSIS = {
  "CAM-01": { 検知頻度: 55, 増加傾向: 40, 慣れ度: 30, 夜間比率: 72, 滞在時間: 45 },
  "CAM-02": { 検知頻度: 68, 増加傾向: 58, 慣れ度: 47, 夜間比率: 60, 滞在時間: 55 },
  "CAM-03": { 検知頻度: 88, 増加傾向: 81, 慣れ度: 79, 夜間比率: 92, 滞在時間: 84 },
  "CAM-04": { 検知頻度: 34, 増加傾向: 22, 慣れ度: 18, 夜間比率: 48, 滞在時間: 26 },
  "CAM-05": { 検知頻度: 74, 増加傾向: 66, 慣れ度: 61, 夜間比率: 81, 滞在時間: 70 },
  "CAM-06": { 検知頻度: 42, 増加傾向: 35, 慣れ度: 24, 夜間比率: 55, 滞在時間: 38 },
};

/* ------------------------------------------------------------------ */
/* 共通UI部品                                                          */
/* ------------------------------------------------------------------ */

function Card({ children, className = "" }) {
  return (
    <div
      className={`rounded-xl border border-gray-200 bg-white shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

function CardHeader({ icon: Icon, title, sub, right }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
      <div className="flex items-center gap-2.5">
        {Icon && <Icon className="h-5 w-5 shrink-0 text-emerald-700" aria-hidden />}
        <div>
          <h2 className="text-lg font-bold text-gray-900">{title}</h2>
          {sub && <p className="mt-0.5 text-sm text-gray-500">{sub}</p>}
        </div>
      </div>
      {right}
    </div>
  );
}

/** 夜間警戒レベルバッジ（高=赤 / 中=黄 / 低=青） */
function AlertLevelBadge({ level, large = false }) {
  const conf = {
    高: { bg: "bg-red-600", label: "警戒レベル：高" },
    中: { bg: "bg-amber-500", label: "警戒レベル：中" },
    低: { bg: "bg-blue-600", label: "警戒レベル：低" },
  }[level];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full font-bold text-white ${conf.bg} ${
        large ? "px-5 py-2.5 text-xl" : "px-3.5 py-1.5 text-base"
      }`}
    >
      <Siren className={large ? "h-6 w-6" : "h-4 w-4"} aria-hidden />
      {conf.label}
    </span>
  );
}

function AnimalChip({ animal }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-base font-semibold text-gray-800">
      <span
        className="h-3 w-3 rounded-full"
        style={{ backgroundColor: getAnimalColor(animal) }}
        aria-hidden
      />
      {animal}
    </span>
  );
}

const CHART_TOOLTIP_STYLE = {
  backgroundColor: "#ffffff",
  border: "1px solid #e1e0d9",
  borderRadius: 8,
  fontSize: 14,
  color: "#0b0b0b",
};

/* ------------------------------------------------------------------ */
/* ① 総合ダッシュボード                                                */
/* ------------------------------------------------------------------ */

function DashboardScreen({
  detectionLog,
  todayKey,
  todayLabel,
  latest,
  alertSummary,
  lastFetchedAtMs,
  nowMs,
}) {
  const todayRecords = detectionLog.filter((r) => r.dateKey === todayKey);
  const todayByAnimal = ANIMALS.map((a) => ({
    animal: a,
    count: todayRecords.filter((r) => r.animal === a).length,
  }));
  const recent5 = detectionLog.slice(0, 5);

  if (!latest) {
    return (
      <Card>
        <CardHeader
          icon={Activity}
          title="ライブステータス"
          sub="検知履歴がまだありません"
        />
        <div className="p-5 text-base text-gray-600">
          バックエンドの detections.csv に検知履歴が追加されると表示されます。
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* ライブステータス + 警戒レベル */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            icon={Activity}
            title="ライブステータス"
            sub="最新の検知情報とシステム稼働状況"
            right={
              <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-base font-bold text-emerald-800">
                <span className="relative flex h-3 w-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-600" />
                </span>
                システム稼働中
              </span>
            }
          />
          <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-3">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-gray-500">
                <Camera className="h-4 w-4" aria-hidden />
                最新検知カメラ
              </p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {latest.cameraId}
              </p>
              <p className="mt-1 flex items-center gap-1 text-base text-gray-600">
                <MapPin className="h-4 w-4" aria-hidden />
                {getCameraPlace(latest.cameraId)}
              </p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-gray-500">
                <PawPrint className="h-4 w-4" aria-hidden />
                動物種別
              </p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {latest.animal}
              </p>
              <p className="mt-1 text-base text-gray-600">
                最大 {latest.maxCount} 頭を同時検知
              </p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-gray-500">
                <Clock className="h-4 w-4" aria-hidden />
                検知日時
              </p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {pad2(latest.hour)}:{pad2(latest.minute)}
              </p>
              <p className="mt-1 text-base text-gray-600">{latest.datetimeLabel}</p>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader icon={Moon} title="夜間警戒レベル" sub="今夜の出没リスク予測" />
          <div className="flex flex-col items-center gap-4 p-6">
            <AlertLevelBadge level={alertSummary.level} large />
            <p className="text-center text-base leading-relaxed text-gray-700">
              直近3日間に
              <span className="font-bold text-red-700"> {alertSummary.totalCount}件 </span>
              の検知、夜間（18時〜翌4時）は
              <span className="font-bold text-red-700"> {alertSummary.nightCount}件 </span>
              です。最多検知は{alertSummary.topAnimal}。{alertSummary.message}
            </p>
            <div className="flex w-full items-center justify-center gap-3 border-t border-gray-100 pt-3 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <span className="h-2.5 w-2.5 rounded-full bg-red-600" />高
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />中
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />低
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* 本日のクイック統計 */}
      <Card>
        <CardHeader
          icon={TrendingUp}
          title="本日のクイック統計"
          sub={`${todayLabel} の検知サマリー`}
        />
        <div className="grid grid-cols-2 gap-4 p-5 md:grid-cols-5">
          <div className="rounded-lg border-2 border-emerald-600 bg-emerald-50 p-4">
            <p className="text-sm font-semibold text-emerald-800">総検知数</p>
            <p className="mt-1 text-4xl font-bold tabular-nums text-emerald-900">
              {todayRecords.length}
              <span className="ml-1 text-lg font-semibold">件</span>
            </p>
          </div>
          {todayByAnimal.map(({ animal, count }) => (
            <div key={animal} className="rounded-lg border border-gray-200 p-4">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-gray-500">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: getAnimalColor(animal) }}
                  aria-hidden
                />
                {animal}
              </p>
              <p className="mt-1 text-4xl font-bold tabular-nums text-gray-900">
                {count}
                <span className="ml-1 text-lg font-semibold text-gray-500">件</span>
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* リアルタイム速報 */}
      <Card>
        <CardHeader
          icon={Bell}
          title="リアルタイム速報"
          sub={`最新5件の検知履歴 / 最終更新 ${formatElapsedSince(lastFetchedAtMs, nowMs)}`}
        />
        <ul className="divide-y divide-gray-100 p-2">
          {recent5.map((r) => (
            <li
              key={r.id}
              className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border-l-4 px-4 py-3.5 hover:bg-gray-50"
              style={{ borderLeftColor: getAnimalColor(r.animal) }}
            >
              <span className="min-w-[7.5rem] text-lg font-bold tabular-nums text-gray-900">
                {formatShortDateTime(r)}
              </span>
              <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-sm font-bold text-emerald-700">
                受信 {formatElapsedSince(r.receivedAtMs || lastFetchedAtMs, nowMs)}
              </span>
              <AnimalChip animal={r.animal} />
              <span className="inline-flex items-center gap-1 text-base text-gray-700">
                <Camera className="h-4 w-4 text-gray-400" aria-hidden />
                {r.cameraId}（{getCameraPlace(r.cameraId)}）
              </span>
              <span className="text-base text-gray-700">
                最大 <b className="tabular-nums">{r.maxCount}</b> 頭
              </span>
              <span className="inline-flex items-center gap-1 rounded bg-orange-50 px-2 py-0.5 text-base font-semibold text-orange-800">
                <Siren className="h-4 w-4" aria-hidden />
                {r.action}
              </span>
              <span className="ml-auto text-base text-gray-500">
                滞在 <b className="tabular-nums text-gray-700">{r.staySec}</b> 秒
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ② リアルタイム検知履歴                                               */
/* ------------------------------------------------------------------ */

function selectClass() {
  return "rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-base font-medium text-gray-900 focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-200";
}

function HistoryScreen({ detectionLog }) {
  const [cameraFilter, setCameraFilter] = useState("all");
  const [animalFilter, setAnimalFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [exportYear, setExportYear] = useState("2026");
  const [exportMonth, setExportMonth] = useState("6");
  const [exportAnimal, setExportAnimal] = useState("サル");
  const availableCameras = useMemo(
    () => getAvailableValues(CAMERAS, detectionLog, "cameraId"),
    [detectionLog],
  );
  const availableAnimals = useMemo(
    () => getAvailableValues(ANIMALS, detectionLog, "animal"),
    [detectionLog],
  );

  const filtered = useMemo(
    () =>
      detectionLog.filter((r) => {
        if (cameraFilter !== "all" && r.cameraId !== cameraFilter) return false;
        if (animalFilter !== "all" && r.animal !== animalFilter) return false;
        if (dateFrom && r.dateKey < dateFrom) return false;
        if (dateTo && r.dateKey > dateTo) return false;
        return true;
      }),
    [cameraFilter, animalFilter, dateFrom, dateTo, detectionLog],
  );

  const handleExport = () => {
    const rows = detectionLog.filter(
      (r) =>
        String(r.year) === exportYear &&
        String(r.month) === exportMonth &&
        (exportAnimal === "all" || r.animal === exportAnimal),
    );
    const header = "検知日時,カメラID,動物の種類,最大同時検知頭数,実行アクション,滞在時間秒";
    const body = rows
      .map((r) =>
        [r.datetimeLabel, r.cameraId, r.animal, r.maxCount, r.action, r.staySec].join(","),
      )
      .join("\n");
    // Excelで文字化けしないようBOM付きUTF-8で出力
    const blob = new Blob(["﻿" + header + "\n" + body], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `検知履歴_${exportYear}年${exportMonth}月_${exportAnimal === "all" ? "全種別" : exportAnimal}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    // click() が発行するダウンロードは非同期のため、即座にrevokeすると
    // 一部ブラウザでBlob参照が早期に失効しダウンロードが失敗する。
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <div className="space-y-6">
      {/* 検索・絞り込み */}
      <Card>
        <CardHeader icon={Search} title="検索・絞り込み" sub="条件を指定して検知ログを検索" />
        <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">カメラID</span>
            <select
              className={selectClass()}
              value={cameraFilter}
              onChange={(e) => setCameraFilter(e.target.value)}
            >
              <option value="all">すべてのカメラ</option>
              {availableCameras.map((c) => (
                <option key={c} value={c}>
                  {c}（{getCameraPlace(c)}）
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">動物種別</span>
            <select
              className={selectClass()}
              value={animalFilter}
              onChange={(e) => setAnimalFilter(e.target.value)}
            >
              <option value="all">すべての動物</option>
              {availableAnimals.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">開始日</span>
            <input
              type="date"
              className={selectClass()}
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">終了日</span>
            <input
              type="date"
              className={selectClass()}
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
        </div>
      </Card>

      {/* 履歴データテーブル */}
      <Card>
        <CardHeader
          icon={History}
          title="検知履歴一覧"
          sub={`該当 ${filtered.length} 件`}
        />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left">
            <thead>
              <tr className="border-b-2 border-gray-200 bg-gray-50 text-base text-gray-600">
                <th className="px-5 py-3 font-bold">検知日時</th>
                <th className="px-5 py-3 font-bold">カメラID</th>
                <th className="px-5 py-3 font-bold">動物の種類</th>
                <th className="px-5 py-3 text-right font-bold">最大同時検知頭数</th>
                <th className="px-5 py-3 font-bold">実行アクション</th>
                <th className="px-5 py-3 text-right font-bold">滞在時間（秒）</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 30).map((r, i) => (
                <tr
                  key={r.id}
                  className={`border-b border-gray-100 text-base text-gray-800 ${
                    i % 2 === 1 ? "bg-gray-50/60" : ""
                  } hover:bg-emerald-50/50`}
                >
                  <td className="px-5 py-3 font-medium tabular-nums">
                    {r.datetimeLabel}
                  </td>
                  <td className="px-5 py-3">
                    {r.cameraId}
                    <span className="ml-1 text-sm text-gray-500">
                      {getCameraPlace(r.cameraId)}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <AnimalChip animal={r.animal} />
                  </td>
                  <td className="px-5 py-3 text-right font-bold tabular-nums">
                    {r.maxCount}
                  </td>
                  <td className="px-5 py-3">{r.action}</td>
                  <td className="px-5 py-3 text-right tabular-nums">{r.staySec}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length > 30 && (
          <p className="border-t border-gray-100 px-5 py-3 text-base text-gray-500">
            最新30件を表示中（全 {filtered.length} 件）。全件はCSVエクスポートをご利用ください。
          </p>
        )}
      </Card>

      {/* 高機能エクスポート */}
      <Card>
        <CardHeader
          icon={Download}
          title="データエクスポート"
          sub="年月・動物種別を指定してCSVをダウンロード"
        />
        <div className="flex flex-wrap items-end gap-4 p-5">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">年</span>
            <select
              className={selectClass()}
              value={exportYear}
              onChange={(e) => setExportYear(e.target.value)}
            >
              <option value="2025">2025年</option>
              <option value="2026">2026年</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">月</span>
            <select
              className={selectClass()}
              value={exportMonth}
              onChange={(e) => setExportMonth(e.target.value)}
            >
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={String(i + 1)}>
                  {i + 1}月
                </option>
              ))}
            </select>
          </label>
          <fieldset className="flex flex-col gap-1.5">
            <legend className="text-sm font-bold text-gray-600">動物種別</legend>
            <div className="flex gap-2 rounded-lg border border-gray-300 bg-white p-1.5">
              {[...availableAnimals, "all"].map((a) => (
                <label
                  key={a}
                  className={`cursor-pointer rounded-md px-4 py-1.5 text-base font-bold ${
                    exportAnimal === a
                      ? "bg-emerald-700 text-white"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <input
                    type="radio"
                    name="exportAnimal"
                    value={a}
                    checked={exportAnimal === a}
                    onChange={() => setExportAnimal(a)}
                    className="sr-only"
                  />
                  {a === "all" ? "全種別" : a}
                </label>
              ))}
            </div>
          </fieldset>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-6 py-3 text-lg font-bold text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-300"
          >
            <Download className="h-5 w-5" aria-hidden />
            CSVダウンロード
          </button>
        </div>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ③ 獣害データ分析レポート                                             */
/* ------------------------------------------------------------------ */

/** 撃退慣れの警告ドット（3週連続で滞在時間が増加した点を赤く強調） */
function HabituationDot(props) {
  const { cx, cy, payload, dataKey, stroke, index } = props;
  if (cx == null || cy == null) return null;
  const warn = payload[`${dataKey}Warn`];
  if (warn) {
    return (
      <g key={`dot-${dataKey}-${index}`}>
        <circle cx={cx} cy={cy} r={8} fill={COLORS.critical} stroke="#ffffff" strokeWidth={2} />
        <circle cx={cx} cy={cy} r={3} fill="#ffffff" />
      </g>
    );
  }
  return (
    <circle
      key={`dot-${dataKey}-${index}`}
      cx={cx}
      cy={cy}
      r={3.5}
      fill={stroke}
      stroke="#ffffff"
      strokeWidth={1.5}
    />
  );
}

/** 前月比の増減率ラベル（増加=赤 / 減少=緑） */
function DeltaLabel(props) {
  const { x, y, width, index, monthlyData } = props;
  const d = monthlyData[index];
  if (d.delta == null) {
    return d.partial ? (
      <text
        x={x + width / 2}
        y={y - 8}
        textAnchor="middle"
        fontSize={13}
        fill={COLORS.muted}
      >
        集計中
      </text>
    ) : null;
  }
  const up = d.delta >= 0;
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      fontSize={14}
      fontWeight={700}
      fill={up ? COLORS.critical : "#006300"}
    >
      {up ? `+${d.delta}%` : `${d.delta}%`}
    </text>
  );
}

/* ------------------------------------------------------------------ */
/* バックエンドAPI連携（habituation / trap / 動画アップロード）           */
/* ------------------------------------------------------------------ */

/** マウント時にhabituation/trap APIを取得するフック。失敗時はnullのまま */
function useBackendData() {
  const [state, setState] = useState({
    status: "loading",
    habituation: null,
    trap: null,
  });

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([fetchHabituation(), fetchTrap()]).then(
      ([habituation, trap]) => {
        if (cancelled) return;
        setState({
          status: "done",
          habituation: habituation.status === "fulfilled" ? habituation.value : null,
          trap: trap.status === "fulfilled" ? trap.value : null,
        });
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

/** データがAPI由来かダミーかを示す小さなバッジ */
function DataSourceBadge({ live }) {
  return live ? (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-sm font-bold text-emerald-800">
      <Wifi className="h-3.5 w-3.5" aria-hidden />
      APIデータ
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-sm font-bold text-gray-600">
      <WifiOff className="h-3.5 w-3.5" aria-hidden />
      ダミーデータ（バックエンド未対応）
    </span>
  );
}

/** 動画アップロード→解析ジョブ登録→完了までポーリングするカード */
function VideoUploadCard() {
  const [videoFile, setVideoFile] = useState(null);
  const [deviceId, setDeviceId] = useState(CAMERAS[0]);
  const [action, setAction] = useState(ACTIONS[0]);
  const [startTimestamp, setStartTimestamp] = useState(() => {
    const now = new Date();
    now.setSeconds(0, 0);
    return now.toISOString().slice(0, 16);
  });
  const [submitting, setSubmitting] = useState(false);
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!job || !["queued", "running"].includes(job.status)) return;
    const timer = setInterval(async () => {
      try {
        const updated = await fetchVideoAnalysisJob(job.job_id);
        setJob(updated);
      } catch (e) {
        setError(e.message);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [job]);

  const handleSubmit = async () => {
    if (!videoFile) {
      setError("MP4動画ファイルを選択してください。");
      return;
    }
    setError(null);
    setSubmitting(true);
    setJob(null);
    try {
      const created = await submitVideoAnalysisJob(videoFile, {
        startTimestamp: startTimestamp.replace("T", " ") + ":00",
        deviceId,
        action,
      });
      setJob(created);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader
        icon={Upload}
        title="動画をアップロードして解析"
        sub="MP4をアップロードするとYOLOで解析し、検知イベントをバックエンドへ反映します"
        right={<DataSourceBadge live />}
      />
      <div className="flex flex-col gap-4 p-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex flex-col gap-1.5 lg:col-span-2">
            <span className="text-sm font-bold text-gray-600">動画ファイル（MP4）</span>
            <input
              type="file"
              accept="video/mp4"
              className={selectClass()}
              onChange={(e) => setVideoFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">カメラID</span>
            <select
              className={selectClass()}
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
            >
              {CAMERAS.map((c) => (
                <option key={c} value={c}>
                  {c}（{getCameraPlace(c)}）
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">実行アクション</span>
            <select
              className={selectClass()}
              value={action}
              onChange={(e) => setAction(e.target.value)}
            >
              {ACTIONS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-bold text-gray-600">撮影開始日時</span>
            <input
              type="datetime-local"
              className={selectClass()}
              value={startTimestamp}
              onChange={(e) => setStartTimestamp(e.target.value)}
            />
          </label>
        </div>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting}
          className="inline-flex w-fit items-center gap-2 rounded-lg bg-emerald-700 px-6 py-3 text-lg font-bold text-white shadow-sm transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
          ) : (
            <Upload className="h-5 w-5" aria-hidden />
          )}
          解析ジョブを登録
        </button>

        {error && (
          <p className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-base text-red-800">
            <XCircle className="h-5 w-5 shrink-0" aria-hidden />
            {error}
          </p>
        )}

        {job && (
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="flex items-center gap-2 text-base font-bold text-gray-800">
              {job.status === "completed" && (
                <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden />
              )}
              {job.status === "failed" && (
                <XCircle className="h-5 w-5 text-red-600" aria-hidden />
              )}
              {(job.status === "queued" || job.status === "running") && (
                <Loader2 className="h-5 w-5 animate-spin text-blue-600" aria-hidden />
              )}
              ジョブ状態: {job.status}
              {job.progress_percent != null && `（${job.progress_percent}%）`}
            </p>
            {job.status === "completed" && (
              <p className="mt-1 text-base text-gray-700">
                検知イベント {job.event_count}件（新規追加 {job.added_event_count}件）。
                バックエンド累計 {job.backend_total_count}件。
              </p>
            )}
            {job.status === "failed" && (
              <p className="mt-1 text-base text-red-700">{job.error}</p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

function RiskBar({ label, value }) {
  const color =
    value >= 70 ? COLORS.critical : value >= 45 ? COLORS.serious : COLORS.good;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-base">
        <span className="font-bold text-gray-700">{label}</span>
        <span className="font-bold tabular-nums" style={{ color }}>
          {value}
          <span className="text-sm font-semibold text-gray-500"> /100</span>
        </span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full"
          style={{ width: `${value}%`, backgroundColor: color }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        />
      </div>
    </div>
  );
}

function AnalysisScreen({ detectionLog }) {
  const [selectedCamera, setSelectedCamera] = useState("CAM-03");
  const backend = useBackendData();
  const apiTrapColor =
    backend.trap?.level === "HIGH"
      ? COLORS.critical
      : backend.trap?.level === "MEDIUM"
        ? COLORS.serious
        : COLORS.good;
  const apiTrapLevelLabel =
    { HIGH: "高", MEDIUM: "中", LOW: "低" }[backend.trap?.level] ?? "-";
  const hourlyData = useMemo(
    () => buildHourlyData(detectionLog),
    [detectionLog],
  );
  const weekdayData = useMemo(
    () => buildWeekdayData(detectionLog),
    [detectionLog],
  );
  const monthlyData = useMemo(
    () => buildMonthlyData(detectionLog),
    [detectionLog],
  );
  const metrics = CAMERA_ANALYSIS[selectedCamera];
  const radarData = Object.entries(metrics).map(([axis, value]) => ({
    axis,
    value,
  }));
  const trapScore = Math.round(
    (metrics.検知頻度 + metrics.増加傾向 + metrics.慣れ度) / 3,
  );
  const trapLevel = trapScore >= 70 ? "高" : trapScore >= 45 ? "中" : "低";
  const trapColor =
    trapScore >= 70 ? COLORS.critical : trapScore >= 45 ? COLORS.serious : COLORS.good;

  return (
    <div className="space-y-6">
      <VideoUploadCard />

      {/* 検知頻度グラフ（時間帯別・曜日別） */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader
            icon={Clock}
            title="時間帯別の検知頻度"
            sub="過去約2ヶ月・夜間（18時〜翌4時）を濃色で表示"
          />
          <div className="p-5">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke={COLORS.grid} vertical={false} />
                  <XAxis
                    dataKey="label"
                    interval={2}
                    tick={{ fontSize: 13, fill: COLORS.axisText }}
                    axisLine={{ stroke: COLORS.grid }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 13, fill: COLORS.axisText }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={CHART_TOOLTIP_STYLE}
                    cursor={{ fill: "rgba(0,0,0,0.04)" }}
                    formatter={(v) => [`${v} 件`, "検知数"]}
                  />
                  <Bar dataKey="検知数" radius={[4, 4, 0, 0]}>
                    {hourlyData.map((d) => (
                      <Cell
                        key={d.hour}
                        fill={d.isNight ? COLORS.seqDark : COLORS.seqLight}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 flex items-center gap-5 text-sm text-gray-600">
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: COLORS.seqDark }} />
                夜間（18〜4時）
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: COLORS.seqLight }} />
                日中（5〜17時）
              </span>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader icon={BarChart3} title="曜日別の検知頻度" sub="過去約2ヶ月の合計" />
          <div className="p-5">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekdayData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid stroke={COLORS.grid} vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 14, fill: COLORS.axisText }}
                    axisLine={{ stroke: COLORS.grid }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 13, fill: COLORS.axisText }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={CHART_TOOLTIP_STYLE}
                    cursor={{ fill: "rgba(0,0,0,0.04)" }}
                    formatter={(v) => [`${v} 件`, "検知数"]}
                  />
                  <Bar dataKey="検知数" fill={COLORS.seqMid} radius={[4, 4, 0, 0]} barSize={36} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-sm text-gray-500">
              棒にカーソルを合わせると件数を表示します
            </p>
          </div>
        </Card>
      </div>

      {/* 滞在時間の週次推移（撃退慣れ検知） */}
      <Card>
        <CardHeader
          icon={AlertTriangle}
          title="滞在時間の週次推移（撃退慣れ分析）"
          sub="平均滞在時間（秒）の推移。赤い点は撃退慣れの兆候"
          right={
            <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3.5 py-1.5 text-base font-bold text-red-700">
              <AlertTriangle className="h-4 w-4" aria-hidden />
              撃退慣れの兆候あり
            </span>
          }
        />
        <div className="p-5">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={WEEKLY_STAY_DATA}
                margin={{ top: 12, right: 16, left: -8, bottom: 0 }}
              >
                <CartesianGrid stroke={COLORS.grid} vertical={false} />
                <XAxis
                  dataKey="week"
                  tick={{ fontSize: 13, fill: COLORS.axisText }}
                  axisLine={{ stroke: COLORS.grid }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 13, fill: COLORS.axisText }}
                  axisLine={false}
                  tickLine={false}
                  unit="秒"
                />
                <Tooltip
                  contentStyle={CHART_TOOLTIP_STYLE}
                  formatter={(v, name) => [`${v} 秒`, name]}
                />
                <Legend
                  wrapperStyle={{ fontSize: 15, paddingTop: 8 }}
                  iconType="plainline"
                />
                <Line
                  type="monotone"
                  dataKey="サル"
                  stroke={COLORS.サル}
                  strokeWidth={2.5}
                  dot={<HabituationDot />}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="イノシシ"
                  stroke={COLORS.イノシシ}
                  strokeWidth={2.5}
                  dot={<HabituationDot />}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" aria-hidden />
            <p className="text-base leading-relaxed text-red-900">
              <b className="text-red-700">赤い点</b>
              は滞在時間が3週連続で増加した「撃退慣れ」の兆候です。
              サルは6月上旬から、イノシシは6月末から威嚇への反応が鈍化しています。
              威嚇パターンの変更、または罠の設置をご検討ください。
            </p>
          </div>
        </div>
      </Card>

      {/* 月次比較 */}
      <Card>
        <CardHeader
          icon={TrendingUp}
          title="月次比較（前月比・季節バースト）"
          sub="月間検知数と前月比増減率。オレンジは季節バースト（急増）月"
          right={<DataSourceBadge live={detectionLog !== FALLBACK_DETECTION_LOG} />}
        />
        <div className="p-5">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData} margin={{ top: 28, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid stroke={COLORS.grid} vertical={false} />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 14, fill: COLORS.axisText }}
                  axisLine={{ stroke: COLORS.grid }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 13, fill: COLORS.axisText }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={CHART_TOOLTIP_STYLE}
                  cursor={{ fill: "rgba(0,0,0,0.04)" }}
                  formatter={(v) => [`${v} 件`, "月間検知数"]}
                />
                <Bar dataKey="検知数" radius={[4, 4, 0, 0]} barSize={48}>
                  {monthlyData.map((d) => (
                    <Cell
                      key={d.month}
                      fill={
                        d.burst
                          ? "#eb6834"
                          : d.partial
                            ? COLORS.seqLight
                            : COLORS.seqMid
                      }
                    />
                  ))}
                  <LabelList content={<DeltaLabel monthlyData={monthlyData} />} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-5 text-sm text-gray-600">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: COLORS.seqMid }} />
              月間検知数
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: "#eb6834" }} />
              季節バースト（前月比+40%以上）
            </span>
            <span className="text-gray-500">
              ※ 数値ラベルは前月比増減率（<span className="font-bold text-red-700">赤=増加</span>／
              <span className="font-bold" style={{ color: "#006300" }}>緑=減少</span>）
            </span>
          </div>
        </div>
      </Card>

      {/* AI慣れ度分析（バックエンドAPI連携） */}
      <Card>
        <CardHeader
          icon={Sparkles}
          title="AI慣れ度分析"
          sub="バックエンドAPI（/habituation）による滞在時間ベースの慣れ度スコア"
          right={<DataSourceBadge live={Boolean(backend.habituation)} />}
        />
        <div className="p-5">
          {backend.habituation ? (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {[
                ["日次", backend.habituation.familiarity_daily_score],
                ["週次", backend.habituation.familiarity_weekly_score],
                ["月次", backend.habituation.familiarity_monthly_score],
                ["年次", backend.habituation.familiarity_yearly_score],
              ].map(([label, score]) => (
                <div key={label} className="rounded-lg border border-gray-200 p-4">
                  <p className="text-sm font-semibold text-gray-500">{label}慣れ度</p>
                  <p
                    className="mt-1 text-3xl font-bold tabular-nums"
                    style={{ color: score >= 0 ? COLORS.critical : COLORS.good }}
                  >
                    {score >= 0 ? "+" : ""}
                    {(score * 100).toFixed(1)}
                    <span className="ml-1 text-lg font-semibold text-gray-500">%</span>
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-base text-gray-500">
              バックエンドAPIに接続できないため表示できません（
              <code className="rounded bg-gray-100 px-1.5 py-0.5">uvicorn backend.api:app --app-dir src</code>
              の起動をご確認ください）。
            </p>
          )}
        </div>
      </Card>

      {/* バックエンドAPIによる総合罠設置推奨度 */}
      <Card>
        <CardHeader
          icon={CircleDot}
          title="総合罠設置推奨度（バックエンドAPI）"
          sub="/trap のスコアに基づく、カメラを問わない全体の推奨度"
          right={<DataSourceBadge live={Boolean(backend.trap)} />}
        />
        <div className="p-5">
          {backend.trap ? (
            <div
              className="flex items-center justify-between rounded-lg border-2 p-5"
              style={{ borderColor: apiTrapColor, backgroundColor: `${apiTrapColor}12` }}
            >
              <div>
                <p className="text-base font-bold text-gray-900">trap_score</p>
                <p className="text-3xl font-bold tabular-nums" style={{ color: apiTrapColor }}>
                  {(backend.trap.trap_score * 100).toFixed(1)}
                  <span className="ml-1 text-lg font-semibold text-gray-500">/100</span>
                </p>
              </div>
              <span
                className="rounded-full px-4 py-1.5 text-xl font-bold text-white"
                style={{ backgroundColor: apiTrapColor }}
              >
                {apiTrapLevelLabel}（{backend.trap.level}）
              </span>
            </div>
          ) : (
            <p className="text-base text-gray-500">
              バックエンドAPIに接続できないため表示できません。
            </p>
          )}
        </div>
      </Card>

      {/* カメラ詳細分析（罠設置支援） */}
      <Card>
        <CardHeader
          icon={Target}
          title="カメラ詳細分析（罠設置支援）"
          sub="カメラを選択して「頻度」「増加傾向」「慣れ」を確認"
          right={<DataSourceBadge live={false} />}
        />
        <div className="p-5">
          <div className="mb-5 flex flex-wrap gap-2">
            {CAMERAS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setSelectedCamera(c)}
                className={`rounded-lg border-2 px-4 py-2 text-base font-bold transition ${
                  selectedCamera === c
                    ? "border-emerald-700 bg-emerald-700 text-white"
                    : "border-gray-300 bg-white text-gray-700 hover:border-emerald-600 hover:text-emerald-700"
                }`}
              >
                {c}
                <span className="ml-1 hidden text-sm font-semibold sm:inline">
                  {getCameraPlace(c)}
                </span>
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="h-80 rounded-lg bg-gray-50 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} outerRadius="72%">
                  <PolarGrid stroke={COLORS.grid} />
                  <PolarAngleAxis
                    dataKey="axis"
                    tick={{ fontSize: 14, fill: COLORS.axisText, fontWeight: 700 }}
                  />
                  <PolarRadiusAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: COLORS.muted }}
                    axisLine={false}
                  />
                  <Radar
                    name={selectedCamera}
                    dataKey="value"
                    stroke={COLORS.seqMid}
                    strokeWidth={2}
                    fill={COLORS.seqMid}
                    fillOpacity={0.3}
                  />
                  <Tooltip
                    contentStyle={CHART_TOOLTIP_STYLE}
                    formatter={(v) => [`${v} /100`, "リスクスコア"]}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="flex flex-col gap-5">
              <div className="space-y-4">
                <RiskBar label="検知頻度" value={metrics.検知頻度} />
                <RiskBar label="増加傾向" value={metrics.増加傾向} />
                <RiskBar label="撃退慣れ度" value={metrics.慣れ度} />
              </div>

              <div
                className="rounded-lg border-2 p-5"
                style={{ borderColor: trapColor, backgroundColor: `${trapColor}12` }}
              >
                <div className="flex items-center justify-between">
                  <p className="flex items-center gap-2 text-lg font-bold text-gray-900">
                    <CircleDot className="h-5 w-5" style={{ color: trapColor }} aria-hidden />
                    罠設置推奨度
                  </p>
                  <span
                    className="rounded-full px-4 py-1.5 text-xl font-bold text-white"
                    style={{ backgroundColor: trapColor }}
                  >
                    {trapLevel}（{trapScore}点）
                  </span>
                </div>
                <p className="mt-3 text-base leading-relaxed text-gray-800">
                  {trapScore >= 70 ? (
                    <>
                      <b>{selectedCamera}（{getCameraPlace(selectedCamera)}）</b>
                      は検知頻度・撃退慣れともに高水準です。威嚇装置の効果が低下しているため、
                      獣道の交差点付近への<b className="text-red-700">箱罠・くくり罠の設置を強く推奨</b>します。
                    </>
                  ) : trapScore >= 45 ? (
                    <>
                      <b>{selectedCamera}（{getCameraPlace(selectedCamera)}）</b>
                      は増加傾向が見られます。今後2週間の推移を注視し、
                      慣れ度が70を超えた場合は罠の設置を検討してください。
                    </>
                  ) : (
                    <>
                      <b>{selectedCamera}（{getCameraPlace(selectedCamera)}）</b>
                      は現在のところ威嚇装置が有効に機能しています。罠の優先度は低めです。
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ルート：サイドバー + 画面切り替え                                     */
/* ------------------------------------------------------------------ */

const PAGES = [
  { key: "dashboard", label: "総合ダッシュボード", icon: LayoutDashboard },
  { key: "history", label: "検知履歴", icon: History },
  { key: "analysis", label: "分析レポート", icon: BarChart3 },
];

export default function WildlifeDashboard() {
  const [page, setPage] = useState("dashboard");
  const [detectionLog, setDetectionLog] = useState(FALLBACK_DETECTION_LOG);
  const [dataSource, setDataSource] = useState("fallback");
  const [lastFetchedAtMs, setLastFetchedAtMs] = useState(null);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const current = PAGES.find((p) => p.key === page);
  const { latest, todayKey, todayLabel } = useMemo(
    () => getTimelineContext(detectionLog),
    [detectionLog],
  );
  const alertSummary = useMemo(
    () => buildAlertSummary(detectionLog),
    [detectionLog],
  );
  const activeCameraCount = useMemo(
    () => getAvailableValues([], detectionLog, "cameraId").length || CAMERAS.length,
    [detectionLog],
  );
  const dataSourceLabel =
    dataSource === "api" ? "バックエンドCSV接続中" : "ダミーデータ表示中";

  useEffect(() => {
    let disposed = false;
    let activeController = null;

    const loadDetections = () => {
      activeController?.abort();
      activeController = new AbortController();

      fetchDetections(activeController.signal)
        .then((records) => {
          if (disposed) return;
          setDetectionLog(records);
          setDataSource("api");
          setLastFetchedAtMs(Date.now());
        })
        .catch((error) => {
          if (disposed || error.name === "AbortError") return;
          setDetectionLog(FALLBACK_DETECTION_LOG);
          setDataSource("fallback");
          setLastFetchedAtMs(null);
        });
    };

    loadDetections();
    const intervalId = window.setInterval(loadDetections, 5000);

    return () => {
      disposed = true;
      activeController?.abort();
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(intervalId);
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-100 text-gray-900 antialiased">
      {/* サイドバー */}
      <aside className="flex w-20 shrink-0 flex-col bg-emerald-950 text-white lg:w-72">
        <div className="flex items-center gap-3 border-b border-emerald-900 px-4 py-5 lg:px-6">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-600">
            <Leaf className="h-6 w-6" aria-hidden />
          </span>
          <div className="hidden lg:block">
            <p className="text-xl font-bold leading-tight">ケモノガード</p>
            <p className="text-sm text-emerald-300">AI獣害対策クラウド</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1.5 p-3">
          {PAGES.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setPage(key)}
              aria-current={page === key ? "page" : undefined}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-3.5 text-lg font-bold transition lg:px-4 ${
                page === key
                  ? "bg-emerald-700 text-white shadow"
                  : "text-emerald-100 hover:bg-emerald-900 hover:text-white"
              }`}
            >
              <Icon className="h-6 w-6 shrink-0" aria-hidden />
              <span className="hidden lg:inline">{label}</span>
            </button>
          ))}
        </nav>

        <div className="hidden border-t border-emerald-900 p-5 text-sm leading-relaxed text-emerald-300 lg:block">
          <p className="flex items-center gap-2 font-bold text-emerald-200">
            <Activity className="h-4 w-4" aria-hidden />
            カメラ{activeCameraCount}台 稼働中
          </p>
          <p className="mt-1">最終同期：{todayLabel}</p>
        </div>
      </aside>

      {/* メイン */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-gray-200 bg-white px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{current.label}</h1>
            <p className="text-base text-gray-500">{todayLabel}</p>
          </div>
          <div className="flex items-center gap-4">
            <AlertLevelBadge level={alertSummary.level} />
            <button
              type="button"
              className="relative rounded-full border border-gray-200 bg-white p-2.5 text-gray-600 hover:bg-gray-50"
              aria-label="通知"
            >
              <Bell className="h-6 w-6" aria-hidden />
              <span className="absolute -right-0.5 -top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-xs font-bold text-white">
                3
              </span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-6">
          {page === "dashboard" && (
            <DashboardScreen
              detectionLog={detectionLog}
              todayKey={todayKey}
              todayLabel={todayLabel}
              latest={latest}
              alertSummary={alertSummary}
              lastFetchedAtMs={lastFetchedAtMs}
              nowMs={nowMs}
            />
          )}
          {page === "history" && <HistoryScreen detectionLog={detectionLog} />}
          {page === "analysis" && <AnalysisScreen detectionLog={detectionLog} />}
        </main>

        <footer className="border-t border-gray-200 bg-white px-6 py-3 text-sm text-gray-400">
          ケモノガード — AI獣害対策SaaS（{dataSourceLabel}）
        </footer>
      </div>
    </div>
  );
}
