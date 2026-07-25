from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DETECTIONS_CSV = BASE_DIR / "detections.csv"


def calc_peak(
    df: pd.DataFrame,
) -> tuple[int | None, int, pd.Series]:
    """有効なtimestampを時間帯別に集計する。入力DataFrameは変更しない。"""
    if "timestamp" not in df.columns:
        raise ValueError("timestamp列が必要です。")

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    ).dropna()

    hour_count = (
        timestamps.dt.hour.value_counts()
        .sort_index()
        .astype("int64")
    )

    if hour_count.empty:
        return None, 0, hour_count

    peak_hour = int(hour_count.idxmax())
    peak_count = int(hour_count.max())
    return peak_hour, peak_count, hour_count


if __name__ == "__main__":
    detections = pd.read_csv(DETECTIONS_CSV)
    peak_hour, peak_count, hour_count = calc_peak(
        detections
    )

    print(
        {
            "peak_hour": peak_hour,
            "peak_count": peak_count,
            "hour_count": hour_count.to_dict(),
        }
    )
