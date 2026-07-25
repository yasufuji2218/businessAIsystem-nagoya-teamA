from __future__ import annotations

import asyncio
from io import BytesIO
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import backend.api as api  # noqa: E402


class ApiRouteTests(unittest.TestCase):
    def test_existing_and_job_routes_are_registered(self) -> None:
        routes = {
            (route.path, method)
            for route in api.app.routes
            for method in (route.methods or set())
        }

        for route in (
            ("/", "GET"),
            ("/appearance", "GET"),
            ("/habituation", "GET"),
            ("/trap", "GET"),
            ("/video-analysis/jobs", "POST"),
            ("/video-analysis/jobs/{job_id}", "GET"),
        ):
            self.assertIn(route, routes)

        schema = api.app.openapi()
        self.assertIn("post", schema["paths"]["/video-analysis/jobs"])

    def test_cors_is_limited_to_local_origins(self) -> None:
        cors = next(
            middleware
            for middleware in api.app.user_middleware
            if middleware.cls is CORSMiddleware
        )
        origins = cors.kwargs["allow_origins"]

        self.assertNotIn("*", origins)
        self.assertTrue(origins)
        self.assertTrue(
            all(
                origin.startswith(
                    ("http://localhost:", "http://127.0.0.1:")
                )
                for origin in origins
            )
        )

    def test_non_mp4_upload_is_rejected(self) -> None:
        upload = UploadFile(
            filename="invalid.txt",
            file=BytesIO(b"not a video"),
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                api.create_video_analysis_job(
                    background_tasks=BackgroundTasks(),
                    video=upload,
                    start_timestamp="2026-07-21 10:00:00",
                    device_id="CAM001",
                    action="なし",
                    confidence=0.25,
                    image_size=320,
                    device="cpu",
                    tracker="bytetrack.yaml",
                    gap_seconds=1.0,
                )
            )

        self.assertEqual(context.exception.status_code, 400)

    def test_background_job_runs_analysis_then_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            backend_csv = temp_path / "backend" / "detections.csv"
            source = temp_path / "input.mp4"
            source.write_bytes(b"test")
            output_dir = temp_path / "output"
            output_dir.mkdir()
            job_id = "test-job"

            def fake_analyze_video(**kwargs) -> Path:
                raw_csv = Path(kwargs["output_dir"]) / "detections.csv"
                pd.DataFrame(
                    [
                        [0, 0.0, 7, "boar", 0.8],
                        [1, 0.1, 7, "boar", 0.9],
                    ],
                    columns=[
                        "frame",
                        "time_seconds",
                        "track_id",
                        "class_name",
                        "confidence",
                    ],
                ).to_csv(raw_csv, index=False)
                kwargs["progress_callback"](2, 2)
                return raw_csv

            created_at = api._now_iso()
            with api.VIDEO_JOBS_LOCK:
                api.VIDEO_JOBS[job_id] = {
                    "job_id": job_id,
                    "status": "queued",
                    "created_at": created_at,
                    "updated_at": created_at,
                }

            original_backend_csv = api.DETECTIONS_CSV
            api.DETECTIONS_CSV = backend_csv
            try:
                with patch.object(
                    api,
                    "analyze_video",
                    side_effect=fake_analyze_video,
                ):
                    api._run_video_analysis_job(
                        job_id=job_id,
                        source=source,
                        output_dir=output_dir,
                        start_timestamp=datetime(
                            2026, 7, 21, 10, 0, 0
                        ),
                        device_id="CAM001",
                        action="なし",
                        confidence=0.25,
                        image_size=320,
                        device="cpu",
                        tracker="bytetrack.yaml",
                        gap_seconds=1.0,
                    )

                job = api._get_job(job_id)
                stored = pd.read_csv(backend_csv)
                self.assertEqual(job["status"], "completed")
                self.assertEqual(job["event_count"], 1)
                self.assertEqual(job["added_event_count"], 1)
                self.assertEqual(job["progress_percent"], 100.0)
                self.assertEqual(len(stored), 1)
                self.assertEqual(stored.iloc[0]["animal_type"], "イノシシ")
            finally:
                api.DETECTIONS_CSV = original_backend_csv
                with api.VIDEO_JOBS_LOCK:
                    api.VIDEO_JOBS.pop(job_id, None)

    def test_background_job_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            job_id = "failed-job"
            created_at = api._now_iso()

            with api.VIDEO_JOBS_LOCK:
                api.VIDEO_JOBS[job_id] = {
                    "job_id": job_id,
                    "status": "queued",
                    "created_at": created_at,
                    "updated_at": created_at,
                }

            try:
                with patch.object(
                    api,
                    "analyze_video",
                    side_effect=RuntimeError("test failure"),
                ):
                    api._run_video_analysis_job(
                        job_id=job_id,
                        source=temp_path / "input.mp4",
                        output_dir=temp_path / "output",
                        start_timestamp=datetime(
                            2026, 7, 21, 10, 0, 0
                        ),
                        device_id="CAM001",
                        action="なし",
                        confidence=0.25,
                        image_size=320,
                        device="cpu",
                        tracker="bytetrack.yaml",
                        gap_seconds=1.0,
                    )

                job = api._get_job(job_id)
                self.assertEqual(job["status"], "failed")
                self.assertIn("RuntimeError", job["error"])
            finally:
                with api.VIDEO_JOBS_LOCK:
                    api.VIDEO_JOBS.pop(job_id, None)


if __name__ == "__main__":
    unittest.main()
