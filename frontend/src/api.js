const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/+$/, "");

async function getJson(path) {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API request failed: ${path} (${res.status})`);
  }
  return res.json();
}

/** GET /appearance: 時間帯別の出没ピーク */
export function fetchAppearance() {
  return getJson("/appearance");
}

/** GET /habituation: 慣れ度スコア（日/週/月/年） */
export function fetchHabituation() {
  return getJson("/habituation");
}

/** GET /trap: 罠設置推奨スコア */
export function fetchTrap() {
  return getJson("/trap");
}

/**
 * POST /video-analysis/jobs: 動画解析ジョブを登録する
 * @param {File} videoFile
 * @param {{startTimestamp: string, deviceId: string, action: string}} options
 */
export async function submitVideoAnalysisJob(videoFile, options) {
  const formData = new FormData();
  formData.append("video", videoFile);
  formData.append("start_timestamp", options.startTimestamp);
  formData.append("device_id", options.deviceId);
  formData.append("action", options.action);
  formData.append("confidence", "0.25");
  formData.append("image_size", "320");
  formData.append("device", "cpu");
  formData.append("gap_seconds", "1.0");

  const res = await fetch(`${API_BASE_URL}/video-analysis/jobs`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`動画解析ジョブの登録に失敗しました (${res.status}): ${text}`);
  }
  return res.json();
}

/** GET /video-analysis/jobs/{jobId}: ジョブ状態を取得する */
export async function fetchVideoAnalysisJob(jobId) {
  return getJson(`/video-analysis/jobs/${jobId}`);
}
