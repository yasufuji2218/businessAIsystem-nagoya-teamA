from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DETECTIONS_CSV = BASE_DIR / "detections.csv"


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """慣れ分析に必要な列を検証・正規化する。"""
    required_columns = {"timestamp", "stay_duration"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"慣れ分析に必要な列がありません: {sorted(missing)}"
        )

    prepared = df.copy()
    prepared["timestamp"] = pd.to_datetime(
        prepared["timestamp"],
        errors="coerce",
    )
    prepared["stay_duration"] = pd.to_numeric(
        prepared["stay_duration"],
        errors="coerce",
    )
    prepared = prepared.dropna(
        subset=["timestamp", "stay_duration"]
    )
    prepared = prepared[prepared["stay_duration"] >= 0]

    prepared["date"] = prepared["timestamp"].dt.date
    prepared["week"] = prepared["timestamp"].dt.to_period("W")
    prepared["month"] = prepared["timestamp"].dt.to_period("M")
    prepared["year"] = prepared["timestamp"].dt.year
    return prepared


def load_data(
    path: Path | str = DETECTIONS_CSV,
) -> pd.DataFrame:
    """__file__基準の既定CSVまたは指定CSVを読み込む。"""
    return prepare_data(pd.read_csv(Path(path)))


def calc_stay(df: pd.DataFrame, unit: str) -> pd.Series:
    """指定期間ごとの平均滞在時間を返す。"""
    if unit not in {"date", "week", "month", "year"}:
        raise ValueError(f"未対応の集計単位です: {unit}")

    return (
        df.groupby(unit, sort=True)["stay_duration"]
        .mean()
        .dropna()
    )


def calc_familiarity(series: pd.Series) -> float:
    """最初と最後の平均滞在時間の増加率を返す。"""
    clean_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(clean_series) < 2:
        return 0.0

    first_value = float(clean_series.iloc[0])
    last_value = float(clean_series.iloc[-1])

    if first_value == 0:
        return 0.0

    score = (last_value - first_value) / first_value
    return float(score) if math.isfinite(score) else 0.0


def calc_familiarity_scores(
    df: pd.DataFrame,
) -> tuple[float, float, float, float]:
    """日・週・月・年単位の慣れ度を計算する。"""
    prepared = prepare_data(df)

    return (
        calc_familiarity(calc_stay(prepared, "date")),
        calc_familiarity(calc_stay(prepared, "week")),
        calc_familiarity(calc_stay(prepared, "month")),
        calc_familiarity(calc_stay(prepared, "year")),
    )


if __name__ == "__main__":
    detections = load_data(DETECTIONS_CSV)
    daily, weekly, monthly, yearly = (
        calc_familiarity_scores(detections)
    )

    print("慣れ度（日）:", daily)
    print("慣れ度（週）:", weekly)
    print("慣れ度（月）:", monthly)
    print("慣れ度（年）:", yearly)
