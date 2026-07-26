from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook


RAW_HEADERS = {
    "realtime_sheet": [
        "timestamp", "device_id", "animal_type",
        "confidence", "action_triggered", "stay_duration",
    ],
    "daily_sheet": [
        "date", "animal", "total_count",
        "average_stay_time", "alert_level",
    ],
    "weekly_sheet": [
        "week", "animal", "peak_hour", "peak_day",
        "familiarity_score", "trap_score", "level",
    ],
    "monthly_sheet": [
        "month", "device_id", "total_count",
        "monkey_count", "boar_count", "trap_score", "rank",
    ],
    "yearly_sheet": [
        "year", "device_id", "total_count",
        "monkey_count", "boar_count", "trap_score", "rank",
    ],
}

NOTIFICATION_HEADERS = {
    "realtime_notification": [
        "timestamp", "device_id", "animal_type", "confidence",
        "action_triggered", "stay_duration", "notification_status",
    ],
    "daily_notification": [
        "date", "total_detection_count", "boar_count", "monkey_count",
        "average_stay_time", "night_alert_level", "notification_status",
    ],
    "weekly_notification": [
        "week", "animal", "peak_hour", "peak_day",
        "familiarity_score", "trap_score", "level", "notification_status",
    ],
    "monthly_notification": [
        "month", "device_id", "monthly_total_count",
        "boar_ratio", "monkey_ratio", "comparison_previous_month",
        "monthly_peak_hour", "action_effectiveness",
        "trap_score", "notification_status",
    ],
    "yearly_notification": [
        "year", "device_id", "total_count",
        "monkey_count", "boar_count", "trap_score", "notification_status",
    ],
}


@pytest.fixture
def sample_workbook_path(tmp_path: Path) -> Path:
    workbook_path = tmp_path / "notification_database.xlsx"
    workbook = Workbook()
    workbook.remove(workbook.active)

    for sheet_name, headers in {**RAW_HEADERS, **NOTIFICATION_HEADERS}.items():
        ws = workbook.create_sheet(sheet_name)
        ws.append(headers)

    realtime = workbook["realtime_sheet"]
    realtime.append([
        "2026-07-21 10:00:01.126", "CAM001", "サル",
        0.3667, "なし", 0.584,
    ])
    realtime.append([
        "2026-07-21 10:00:02.126", "CAM001", "サル",
        0.9000, "led_flash_buzzer", 0.300,
    ])
    realtime.append([
        "2026-07-21 10:00:03.126", "CAM001", "イノシシ",
        0.8000, "led_flash_buzzer", 1.630,
    ])

    daily = workbook["daily_sheet"]
    daily.append(["2026-07-21", "サル", 10, 0.34, "HIGH"])
    daily.append(["2026-07-21", "イノシシ", 1, 1.63, "LOW"])

    weekly = workbook["weekly_sheet"]
    weekly.append(["2026-07-21", "サル", 10, "火曜日", 0.25, 0.80, "HIGH"])
    weekly.append(["2026-07-21", "イノシシ", 10, "木曜日", 0.10, 0.50, "MEDIUM"])

    monthly = workbook["monthly_sheet"]
    monthly.append(["2026-06", "CAM001", 5, 4, 1, 0.4, 2])
    monthly.append(["2026-07", "CAM001", 11, 10, 1, 0.8, 1])

    yearly = workbook["yearly_sheet"]
    yearly.append([2026, "CAM001", 11, 10, 1, 0.8, 1])

    workbook.save(workbook_path)
    workbook.close()
    return workbook_path


@pytest.fixture
def backend_csv_dir(tmp_path: Path) -> Path:
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()

    (backend_dir / "detections.csv").write_text(
        "timestamp,device_id,animal_type,confidence,action_triggered,stay_duration\n"
        "2026-07-21 10:00:01,CAM001,サル,0.91,なし,0.5\n",
        encoding="utf-8",
    )
    (backend_dir / "daily_analysis.csv").write_text(
        "date,animal,total_count,average_stay_time,alert_level\n"
        "2026-07-21,サル,10,0.34,HIGH\n",
        encoding="utf-8",
    )
    (backend_dir / "weekly_analysis.csv").write_text(
        "week,animal,peak_hour,peak_day,familiarity_score,trap_score,level\n"
        "2026-07-21,サル,10,火曜日,0.25,0.8,HIGH\n",
        encoding="utf-8",
    )
    (backend_dir / "monthly_analysis.csv").write_text(
        "month,device_id,total_count,monkey_count,boar_count,trap_score,rank\n"
        "2026-07,CAM001,11,10,1,0.8,1\n",
        encoding="utf-8",
    )
    (backend_dir / "yearly_analysis.csv").write_text(
        "year,device_id,total_count,monkey_count,boar_count,trap_score,rank\n"
        "2026,CAM001,11,10,1,0.8,1\n",
        encoding="utf-8",
    )
    return backend_dir
