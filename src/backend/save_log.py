from __future__ import annotations

import csv
import os
from pathlib import Path
from uuid import uuid4

from filelock import FileLock


BASE_DIR = Path(__file__).resolve().parent
CSV_LOCK_TIMEOUT_SECONDS = 30

DAILY_ANALYSIS_CSV = BASE_DIR / "daily_analysis.csv"
WEEKLY_ANALYSIS_CSV = BASE_DIR / "weekly_analysis.csv"
MONTHLY_ANALYSIS_CSV = BASE_DIR / "monthly_analysis.csv"
YEARLY_ANALYSIS_CSV = BASE_DIR / "yearly_analysis.csv"


def _append_row(
    csv_path: Path,
    columns: list[str],
    row: list[object],
) -> None:
    """CSVをロックし、一時ファイルの原子的置換で1行追加する。"""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = csv_path.with_name(f".{csv_path.name}.lock")

    with FileLock(
        str(lock_path),
        timeout=CSV_LOCK_TIMEOUT_SECONDS,
    ):
        existing_rows: list[list[str]] = []

        if csv_path.is_file():
            with csv_path.open(
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:
                existing_rows = list(csv.reader(csv_file))

        if existing_rows:
            if existing_rows[0] != columns:
                raise ValueError(
                    f"CSVの列が想定と異なります: {csv_path}"
                )
        else:
            existing_rows = [columns]

        temporary_path = csv_path.with_name(
            f".{csv_path.name}.{uuid4().hex}.tmp"
        )

        try:
            with temporary_path.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(existing_rows)
                writer.writerow(row)

            os.replace(temporary_path, csv_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def save_daily_analysis(
    date,
    animal,
    total_count,
    average_stay_time,
    alert_level,
) -> None:
    _append_row(
        DAILY_ANALYSIS_CSV,
        [
            "date",
            "animal",
            "total_count",
            "average_stay_time",
            "alert_level",
        ],
        [
            date,
            animal,
            total_count,
            average_stay_time,
            alert_level,
        ],
    )


def save_weekly_analysis(
    week,
    animal,
    peak_hour,
    peak_day,
    familiarity_score,
    trap_score,
    level,
) -> None:
    _append_row(
        WEEKLY_ANALYSIS_CSV,
        [
            "week",
            "animal",
            "peak_hour",
            "peak_day",
            "familiarity_score",
            "trap_score",
            "level",
        ],
        [
            week,
            animal,
            peak_hour,
            peak_day,
            familiarity_score,
            trap_score,
            level,
        ],
    )


def save_monthly_analysis(
    month,
    device_id,
    total_count,
    monkey_count,
    boar_count,
    trap_score,
    rank,
) -> None:
    _append_row(
        MONTHLY_ANALYSIS_CSV,
        [
            "month",
            "device_id",
            "total_count",
            "monkey_count",
            "boar_count",
            "trap_score",
            "rank",
        ],
        [
            month,
            device_id,
            total_count,
            monkey_count,
            boar_count,
            trap_score,
            rank,
        ],
    )


def save_yearly_analysis(
    year,
    device_id,
    total_count,
    monkey_count,
    boar_count,
    trap_score,
    rank,
) -> None:
    _append_row(
        YEARLY_ANALYSIS_CSV,
        [
            "year",
            "device_id",
            "total_count",
            "monkey_count",
            "boar_count",
            "trap_score",
            "rank",
        ],
        [
            year,
            device_id,
            total_count,
            monkey_count,
            boar_count,
            trap_score,
            rank,
        ],
    )
