from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DETECTIONS_CSV = BASE_DIR / "detections.csv"


def _clamp_score(value: float) -> float:
    """スコア要素を0から1の範囲へ制限する。"""
    return max(0.0, min(float(value), 1.0))


def calc_trap_score(df: pd.DataFrame) -> tuple[float, str]:
    """出現頻度・増加傾向・滞在時間から罠推奨度を返す。"""
    required_columns = {
        "animal_type",
        "timestamp",
        "stay_duration",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"罠分析に必要な列がありません: {sorted(missing)}"
        )

    prepared = df.copy()
    prepared["animal_type"] = (
        prepared["animal_type"].astype("string").str.strip()
    )
    prepared = prepared[
        prepared["animal_type"].notna()
        & prepared["animal_type"].ne("")
    ]

    if prepared.empty:
        return 0.0, "LOW"

    animal_count = prepared["animal_type"].value_counts()
    animal_score = float(animal_count.max()) / len(prepared)

    prepared["timestamp"] = pd.to_datetime(
        prepared["timestamp"],
        errors="coerce",
    )
    timeline = (
        prepared.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .copy()
    )

    trend_score = 0.0
    familiarity_score = 0.0

    if not timeline.empty:
        start_time = timeline["timestamp"].min()
        end_time = timeline["timestamp"].max()

        if start_time < end_time:
            middle_time = start_time + (end_time - start_time) / 2
            first_half = int(
                (timeline["timestamp"] < middle_time).sum()
            )
            second_half = len(timeline) - first_half
            trend_score = _clamp_score(
                (second_half - first_half) / max(first_half, 1)
            )

        timeline["stay_duration"] = pd.to_numeric(
            timeline["stay_duration"],
            errors="coerce",
        )
        stay_timeline = timeline.dropna(
            subset=["stay_duration"]
        )
        stay_timeline = stay_timeline[
            stay_timeline["stay_duration"] >= 0
        ].copy()

        if not stay_timeline.empty:
            stay_timeline["date"] = (
                stay_timeline["timestamp"].dt.date
            )
            daily = (
                stay_timeline.groupby("date", sort=True)[
                    "stay_duration"
                ]
                .mean()
                .dropna()
            )

            if len(daily) >= 2:
                first_stay = float(daily.iloc[0])
                last_stay = float(daily.iloc[-1])

                if first_stay > 0:
                    familiarity_score = _clamp_score(
                        (last_stay - first_stay) / first_stay
                    )

    trap_score = _clamp_score(
        animal_score * 0.5
        + trend_score * 0.3
        + familiarity_score * 0.2
    )

    if trap_score >= 0.7:
        level = "HIGH"
    elif trap_score >= 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return float(trap_score), level


if __name__ == "__main__":
    detections = pd.read_csv(DETECTIONS_CSV)
    trap_score, level = calc_trap_score(detections)
    print("trap_score:", trap_score)
    print("level:", level)
