from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from backend.appearance import calc_peak  # noqa: E402
from backend.habituation import calc_familiarity_scores  # noqa: E402
from backend.save_log import _append_row  # noqa: E402
from backend.trap import calc_trap_score  # noqa: E402
from scripts.analyze_video import analyze_video  # noqa: E402
from scripts.merge_detections import (  # noqa: E402
    BACKEND_COLUMNS,
    append_to_backend,
    build_backend_events,
    merge_detections,
    read_backend_csv,
)


class VideoEventConversionTests(unittest.TestCase):
    def test_track_id_and_gap_create_separate_events(self) -> None:
        raw_df = pd.DataFrame(
            [
                [0, 0.0, 10, "boar", 0.8],
                [1, 0.1, 10, "boar", 0.9],
                [2, 0.2, 11, "boar", 0.7],
                [20, 2.0, 10, "boar", 0.6],
                [3, 0.3, 20, "monkey", 0.75],
                [4, 0.4, 20, "monkey", 0.85],
            ],
            columns=[
                "frame",
                "time_seconds",
                "track_id",
                "class_name",
                "confidence",
            ],
        )
        original = raw_df.copy(deep=True)

        events = build_backend_events(
            raw_df=raw_df,
            start_timestamp=datetime(2026, 7, 21, 10, 0, 0),
            device_id="CAM001",
            action="なし",
            gap_seconds=1.0,
        )

        self.assertEqual(list(events.columns), BACKEND_COLUMNS)
        self.assertEqual(len(events), 4)
        self.assertEqual(
            events["animal_type"].value_counts().to_dict(),
            {"イノシシ": 3, "サル": 1},
        )
        pd.testing.assert_frame_equal(raw_df, original)

    def test_merge_function_supports_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            raw_csv = temp_path / "raw.csv"
            backend_csv = temp_path / "backend" / "detections.csv"
            pd.DataFrame(
                [[0, 0.0, 1, "boar", 0.9]],
                columns=[
                    "frame",
                    "time_seconds",
                    "track_id",
                    "class_name",
                    "confidence",
                ],
            ).to_csv(raw_csv, index=False)

            events, added_count, total_count = merge_detections(
                source=raw_csv,
                start_timestamp="2026-07-21 10:00:00",
                backend_csv=backend_csv,
                write=False,
            )

            self.assertEqual(len(events), 1)
            self.assertEqual(added_count, 0)
            self.assertEqual(total_count, 0)
            self.assertFalse(backend_csv.exists())

    def test_analyzer_uses_tracking_api(self) -> None:
        source = inspect.getsource(analyze_video)
        self.assertIn("model.track(", source)
        self.assertIn("boxes.id", source)
        self.assertIn("persist=True", source)


class CsvConcurrencyTests(unittest.TestCase):
    def test_missing_backend_csv_is_created_with_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend_csv = Path(temp_dir) / "backend" / "detections.csv"

            stored = read_backend_csv(backend_csv)

            self.assertTrue(backend_csv.is_file())
            self.assertTrue(stored.empty)
            self.assertEqual(list(stored.columns), BACKEND_COLUMNS)
            self.assertEqual(
                backend_csv.read_text(
                    encoding="utf-8-sig"
                ).strip(),
                ",".join(BACKEND_COLUMNS),
            )

    def test_concurrent_writers_preserve_all_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend_csv = Path(temp_dir) / "detections.csv"

            def append_one(index: int) -> tuple[int, int]:
                event = pd.DataFrame(
                    [
                        {
                            "timestamp": (
                                f"2026-07-21 10:00:{index:02d}.000"
                            ),
                            "device_id": f"CAM{index:03d}",
                            "animal_type": "イノシシ",
                            "confidence": 0.9,
                            "action_triggered": "なし",
                            "stay_duration": 1.0,
                        }
                    ],
                    columns=BACKEND_COLUMNS,
                )
                return append_to_backend(event, backend_csv)

            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(append_one, range(20)))

            stored = read_backend_csv(backend_csv)
            self.assertEqual(len(stored), 20)
            self.assertEqual(stored["device_id"].nunique(), 20)
            self.assertTrue(all(added == 1 for added, _ in results))
            self.assertEqual(list(stored.columns), BACKEND_COLUMNS)

    def test_analysis_log_writers_preserve_all_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_csv = Path(temp_dir) / "daily.csv"
            columns = ["id", "value"]

            def append_one(index: int) -> None:
                _append_row(log_csv, columns, [index, f"value-{index}"])

            with ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(append_one, range(20)))

            stored = pd.read_csv(log_csv)
            self.assertEqual(list(stored.columns), columns)
            self.assertEqual(len(stored), 20)
            self.assertEqual(stored["id"].nunique(), 20)


class AnalysisRegressionTests(unittest.TestCase):
    def test_empty_data_is_handled_without_division_errors(self) -> None:
        empty = pd.DataFrame(
            columns=[
                "timestamp",
                "device_id",
                "animal_type",
                "confidence",
                "action_triggered",
                "stay_duration",
            ]
        )

        peak_hour, peak_count, hour_count = calc_peak(empty)
        self.assertIsNone(peak_hour)
        self.assertEqual(peak_count, 0)
        self.assertTrue(hour_count.empty)
        self.assertEqual(
            calc_familiarity_scores(empty),
            (0.0, 0.0, 0.0, 0.0),
        )
        self.assertEqual(calc_trap_score(empty), (0.0, "LOW"))

    def test_analysis_functions_do_not_mutate_input(self) -> None:
        source = pd.DataFrame(
            {
                "timestamp": [
                    "2026-07-20 10:00:00",
                    "2026-07-21 11:00:00",
                ],
                "animal_type": ["イノシシ", "イノシシ"],
                "stay_duration": [1.0, 2.0],
            }
        )
        original = source.copy(deep=True)

        calc_peak(source)
        calc_familiarity_scores(source)
        score, level = calc_trap_score(source)

        pd.testing.assert_frame_equal(source, original)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn(level, {"LOW", "MEDIUM", "HIGH"})


if __name__ == "__main__":
    unittest.main()
