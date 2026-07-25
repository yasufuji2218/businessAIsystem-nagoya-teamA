from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware

from backend.appearance import calc_peak
from backend.habituation import calc_familiarity_scores
from backend.trap import calc_trap_score
from scripts.analyze_video import MODEL_PATH, analyze_video
from scripts.merge_detections import (
    merge_detections,
    parse_start_timestamp,
    read_backend_csv,
)


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parent
DETECTIONS_CSV = BASE_DIR / "detections.csv"
JOB_INPUT_ROOT = SRC_DIR / "inputs" / "video_jobs"
JOB_OUTPUT_ROOT = SRC_DIR / "outputs" / "video_analysis" / "jobs"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
]

VIDEO_JOBS: dict[str, dict[str, object]] = {}
VIDEO_JOBS_LOCK = Lock()
VIDEO_ANALYSIS_LOCK = Lock()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _now_iso() -> str:
    """UTCの現在日時をAPI用文字列で返す。"""
    return datetime.now(timezone.utc).isoformat()


def _update_job(job_id: str, **changes: object) -> None:
    """共有ジョブ状態をスレッドセーフに更新する。"""
    with VIDEO_JOBS_LOCK:
        job = VIDEO_JOBS[job_id]
        job.update(changes)
        job["updated_at"] = _now_iso()


def _get_job(job_id: str) -> dict[str, object]:
    """外部変更を防ぐためジョブ状態のコピーを返す。"""
    with VIDEO_JOBS_LOCK:
        job = VIDEO_JOBS.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return dict(job)


def _run_video_analysis_job(
    job_id: str,
    source: Path,
    output_dir: Path,
    start_timestamp: datetime,
    device_id: str,
    action: str,
    confidence: float,
    image_size: int,
    device: str,
    tracker: str,
    gap_seconds: float,
) -> None:
    """バックグラウンドでYOLO解析とイベント反映を実行する。"""

    def report_progress(
        processed_frames: int,
        total_frames: int,
    ) -> None:
        progress = None
        if total_frames > 0:
            progress = round(
                processed_frames / total_frames * 100,
                1,
            )

        _update_job(
            job_id,
            processed_frames=processed_frames,
            total_frames=total_frames,
            progress_percent=progress,
        )

    try:
        # 同一プロセス内の複数YOLO推論によるメモリ競合を避ける。
        with VIDEO_ANALYSIS_LOCK:
            _update_job(
                job_id,
                status="running",
                started_at=_now_iso(),
            )

            raw_detection_csv = analyze_video(
                source=source,
                confidence=confidence,
                image_size=image_size,
                show=False,
                device=device,
                tracker=tracker,
                model_path=MODEL_PATH,
                output_dir=output_dir,
                progress_callback=report_progress,
            )

        events, added_count, total_count = merge_detections(
            source=raw_detection_csv,
            start_timestamp=start_timestamp,
            device_id=device_id,
            action=action,
            gap_seconds=gap_seconds,
            backend_csv=DETECTIONS_CSV,
            write=True,
        )

        _update_job(
            job_id,
            status="completed",
            completed_at=_now_iso(),
            event_count=len(events),
            added_event_count=added_count,
            backend_total_count=total_count,
            result={
                "annotated_video": str(output_dir / "annotated.mp4"),
                "raw_detections_csv": str(raw_detection_csv),
                "frame_summary_csv": str(
                    output_dir / "frame_summary.csv"
                ),
                "summary_json": str(output_dir / "summary.json"),
            },
        )
    except Exception as error:
        _update_job(
            job_id,
            status="failed",
            completed_at=_now_iso(),
            error=f"{type(error).__name__}: {error}",
        )


@app.get("/")
def root():
    return {"message": "Backend API"}


@app.get("/appearance")
def appearance():
    df = read_backend_csv(DETECTIONS_CSV)
    peak_hour, peak_count, hour_count = calc_peak(df)

    return {
        "peak_hour": peak_hour,
        "peak_count": peak_count,
        "hour_count": {
            int(hour): int(count)
            for hour, count in hour_count.items()
        },
    }


@app.get("/habituation")
def habituation():
    df = read_backend_csv(DETECTIONS_CSV)
    daily, weekly, monthly, yearly = calc_familiarity_scores(df)

    return {
        "familiarity_daily_score": daily,
        "familiarity_weekly_score": weekly,
        "familiarity_monthly_score": monthly,
        "familiarity_yearly_score": yearly,
    }


@app.get("/trap")
def trap():
    df = read_backend_csv(DETECTIONS_CSV)
    trap_score, level = calc_trap_score(df)

    return {
        "trap_score": trap_score,
        "level": level,
    }


@app.post(
    "/video-analysis/jobs",
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_video_analysis_job(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    start_timestamp: str = Form(...),
    device_id: str = Form("CAM001"),
    action: str = Form("なし"),
    confidence: float = Form(0.25, gt=0.0, le=1.0),
    image_size: int = Form(320, ge=1),
    device: str = Form("cpu"),
    tracker: str = Form("bytetrack.yaml"),
    gap_seconds: float = Form(1.0, gt=0.0),
):
    """MP4を保存し、解析ジョブをキューへ登録する。"""
    filename = Path(video.filename or "video.mp4").name
    if Path(filename).suffix.lower() != ".mp4":
        await video.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MP4動画を指定してください。",
        )

    try:
        parsed_start_timestamp = parse_start_timestamp(
            start_timestamp
        )
    except ValueError as error:
        await video.close()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    device_id = device_id.strip()
    action = action.strip()
    if not device_id or not action:
        await video.close()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="device_idとactionは空にできません。",
        )

    job_id = uuid4().hex
    input_dir = JOB_INPUT_ROOT / job_id
    output_dir = JOB_OUTPUT_ROOT / job_id
    input_dir.mkdir(parents=True, exist_ok=False)
    output_dir.mkdir(parents=True, exist_ok=False)
    source = input_dir / filename

    bytes_written = 0
    try:
        with source.open("xb") as destination:
            while chunk := await video.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="動画は2 GiB以下にしてください。",
                    )
                destination.write(chunk)
    except Exception:
        # このリクエストで作成した不完全な一時アップロードだけを除去する。
        source.unlink(missing_ok=True)
        raise
    finally:
        await video.close()

    created_at = _now_iso()
    with VIDEO_JOBS_LOCK:
        VIDEO_JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "filename": filename,
            "upload_bytes": bytes_written,
            "created_at": created_at,
            "updated_at": created_at,
            "processed_frames": 0,
            "total_frames": None,
            "progress_percent": None,
            "error": None,
        }

    background_tasks.add_task(
        _run_video_analysis_job,
        job_id,
        source,
        output_dir,
        parsed_start_timestamp,
        device_id,
        action,
        confidence,
        image_size,
        device,
        tracker,
        gap_seconds,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/video-analysis/jobs/{job_id}",
    }


@app.get("/video-analysis/jobs/{job_id}")
def get_video_analysis_job(job_id: str):
    """動画解析ジョブの状態と完了時の成果物を返す。"""
    try:
        return _get_job(job_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="動画解析ジョブが見つかりません。",
        ) from error
