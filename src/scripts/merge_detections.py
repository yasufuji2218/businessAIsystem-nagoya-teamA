from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from filelock import FileLock
from pandas.errors import EmptyDataError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_CSV = PROJECT_ROOT / "backend" / "detections.csv"
CSV_LOCK_TIMEOUT_SECONDS = 30

RAW_COLUMNS = {
    "frame",
    "time_seconds",
    "track_id",
    "class_name",
    "confidence",
}

BACKEND_COLUMNS = [
    "timestamp",
    "device_id",
    "animal_type",
    "confidence",
    "action_triggered",
    "stay_duration",
]

ANIMAL_NAME_MAP = {
    "boar": "イノシシ",
    "monkey": "サル",
}


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を読み込む。"""
    parser = argparse.ArgumentParser(
        description=(
            "追跡付き動画解析のdetections.csvを、"
            "バックエンド用イベントへ変換して追記します。"
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="analyze_video.pyが生成したdetections.csv",
    )
    parser.add_argument(
        "--start-timestamp",
        required=True,
        help='動画の撮影開始日時。例: "2026-07-21 10:00:00"',
    )
    parser.add_argument(
        "--device-id",
        default="CAM001",
        help="カメラID。既定値: CAM001",
    )
    parser.add_argument(
        "--action",
        default="なし",
        help="撃退動作。既定値: なし",
    )
    parser.add_argument(
        "--gap-seconds",
        type=float,
        default=1.0,
        help=(
            "同一track_idの検出がこの秒数より長く途切れた場合、"
            "別イベントとして扱います。既定値: 1.0"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="追記せず、変換結果だけ表示します。",
    )
    return parser.parse_args()


def parse_start_timestamp(value: str | datetime) -> datetime:
    """撮影開始日時をISO形式からdatetimeへ変換する。"""
    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            "--start-timestampは"
            "YYYY-MM-DD HH:MM:SS形式で指定してください。"
        ) from error


def load_raw_detections(source: Path) -> pd.DataFrame:
    """動画解析CSVを読み込み、列と値を検証する。"""
    source = source.expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(
            f"動画解析結果が見つかりません: {source}"
        )

    try:
        df = pd.read_csv(source)
    except EmptyDataError as error:
        raise ValueError(
            f"動画解析CSVが空です: {source}"
        ) from error

    missing_columns = RAW_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "動画解析CSVに必要な列がありません: "
            f"{sorted(missing_columns)}"
        )

    df = df.copy()

    for column in (
        "frame",
        "time_seconds",
        "track_id",
        "confidence",
    ):
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["class_name"] = (
        df["class_name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df = df.dropna(
        subset=[
            "frame",
            "time_seconds",
            "confidence",
        ]
    )

    df = df[
        df["class_name"].isin(ANIMAL_NAME_MAP)
    ]

    df = df[
        (df["frame"] >= 0)
        & (df["time_seconds"] >= 0)
        & (df["confidence"].between(0, 1))
    ]

    valid_track_id = (
        df["track_id"].isna()
        | (
            (df["track_id"] >= 0)
            & (df["track_id"] % 1 == 0)
        )
    )
    df.loc[~valid_track_id, "track_id"] = pd.NA

    return (
        df.sort_values(
            [
                "class_name",
                "track_id",
                "time_seconds",
                "frame",
            ],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def estimate_frame_duration(df: pd.DataFrame) -> float:
    """frameとtime_secondsから1フレーム分の秒数を推定する。"""
    frame_times = (
        df[["frame", "time_seconds"]]
        .drop_duplicates(subset=["frame"])
        .sort_values("frame")
    )

    frame_difference = frame_times["frame"].diff()
    time_difference = frame_times["time_seconds"].diff()

    valid = (
        (frame_difference > 0)
        & (time_difference > 0)
    )

    if not valid.any():
        return 1.0 / 30.0

    fps_values = (
        frame_difference[valid]
        / time_difference[valid]
    )

    fps_values = fps_values[
        (fps_values >= 1.0)
        & (fps_values <= 240.0)
    ]

    if fps_values.empty:
        return 1.0 / 30.0

    return 1.0 / float(fps_values.median())


def add_event(
    events: list[dict[str, object]],
    event_df: pd.DataFrame,
    class_name: str,
    start_timestamp: datetime,
    device_id: str,
    action: str,
    frame_duration: float,
) -> None:
    """連続検出区間をバックエンド用の1イベントへ変換する。"""
    start_seconds = float(
        event_df["time_seconds"].min()
    )
    end_seconds = float(
        event_df["time_seconds"].max()
    )

    event_timestamp = (
        start_timestamp
        + timedelta(seconds=start_seconds)
    )

    stay_duration = max(
        end_seconds - start_seconds + frame_duration,
        frame_duration,
    )

    events.append(
        {
            "timestamp": event_timestamp.isoformat(
                sep=" ",
                timespec="milliseconds",
            ),
            "device_id": device_id,
            "animal_type": ANIMAL_NAME_MAP[class_name],
            "confidence": round(
                float(event_df["confidence"].mean()),
                4,
            ),
            "action_triggered": action,
            "stay_duration": round(
                stay_duration,
                3,
            ),
        }
    )


def add_timeline_events(
    events: list[dict[str, object]],
    timeline: pd.DataFrame,
    class_name: str,
    start_timestamp: datetime,
    device_id: str,
    action: str,
    frame_duration: float,
    gap_seconds: float,
) -> None:
    """時系列を検出間隔で分割し、イベント一覧へ追加する。"""
    timeline = (
        timeline.sort_values("time_seconds")
        .reset_index(drop=True)
        .copy()
    )

    timeline["event_id"] = (
        timeline["time_seconds"]
        .diff()
        .gt(gap_seconds)
        .cumsum()
    )

    for _, event_df in timeline.groupby(
        "event_id",
        sort=False,
    ):
        add_event(
            events=events,
            event_df=event_df,
            class_name=class_name,
            start_timestamp=start_timestamp,
            device_id=device_id,
            action=action,
            frame_duration=frame_duration,
        )


def build_backend_events(
    raw_df: pd.DataFrame,
    start_timestamp: datetime,
    device_id: str,
    action: str,
    gap_seconds: float,
) -> pd.DataFrame:
    """
    フレーム単位の検出を個体別・連続区間別のイベントへ変換する。

    track_idがある行はclass_nameとtrack_id単位で集約する。
    track_idが空の行はclass_nameと検出間隔で補助的に集約する。
    """
    if gap_seconds <= 0:
        raise ValueError(
            "--gap-secondsは0より大きくしてください。"
        )

    device_id = device_id.strip()
    action = action.strip()

    if not device_id:
        raise ValueError(
            "--device-idを空にすることはできません。"
        )

    if not action:
        raise ValueError(
            "--actionを空にすることはできません。"
        )

    frame_duration = estimate_frame_duration(raw_df)
    events: list[dict[str, object]] = []

    tracked_df = raw_df.dropna(
        subset=["track_id"]
    ).copy()

    if not tracked_df.empty:
        tracked_df["track_id"] = (
            tracked_df["track_id"]
            .astype("int64")
        )

        for (
            class_name,
            _track_id,
        ), track_df in tracked_df.groupby(
            ["class_name", "track_id"],
            sort=False,
        ):
            timeline = (
                track_df.groupby(
                    "time_seconds",
                    as_index=False,
                )
                .agg(
                    confidence=("confidence", "mean")
                )
            )

            add_timeline_events(
                events=events,
                timeline=timeline,
                class_name=class_name,
                start_timestamp=start_timestamp,
                device_id=device_id,
                action=action,
                frame_duration=frame_duration,
                gap_seconds=gap_seconds,
            )

    untracked_df = raw_df[
        raw_df["track_id"].isna()
    ].copy()

    if not untracked_df.empty:
        for class_name, class_df in untracked_df.groupby(
            "class_name",
            sort=False,
        ):
            timeline = (
                class_df.groupby(
                    "time_seconds",
                    as_index=False,
                )
                .agg(
                    confidence=("confidence", "mean")
                )
            )

            add_timeline_events(
                events=events,
                timeline=timeline,
                class_name=class_name,
                start_timestamp=start_timestamp,
                device_id=device_id,
                action=action,
                frame_duration=frame_duration,
                gap_seconds=gap_seconds,
            )

    result = pd.DataFrame(
        events,
        columns=BACKEND_COLUMNS,
    )

    return (
        result.sort_values("timestamp")
        .reset_index(drop=True)
    )


def get_lock_path(csv_path: Path) -> Path:
    """CSVと同じディレクトリに置くロックファイルを返す。"""
    return csv_path.with_name(f".{csv_path.name}.lock")


def _read_backend_csv_unlocked(
    backend_csv: Path,
    create_if_missing: bool = True,
) -> pd.DataFrame:
    """呼び出し元でロック済みのバックエンドCSVを読む。"""
    if not backend_csv.is_file():
        empty_df = pd.DataFrame(columns=BACKEND_COLUMNS)

        if create_if_missing:
            temporary_path = backend_csv.with_name(
                f".{backend_csv.name}.{uuid4().hex}.tmp"
            )
            try:
                empty_df.to_csv(
                    temporary_path,
                    index=False,
                    encoding="utf-8-sig",
                )
                os.replace(temporary_path, backend_csv)
            finally:
                if temporary_path.exists():
                    temporary_path.unlink()

        return empty_df

    try:
        backend_df = pd.read_csv(backend_csv)
    except EmptyDataError:
        backend_df = pd.DataFrame(
            columns=BACKEND_COLUMNS
        )

    if list(backend_df.columns) != BACKEND_COLUMNS:
        raise ValueError(
            "backend/detections.csvの列が"
            "想定と異なります。\n"
            f"想定: {BACKEND_COLUMNS}\n"
            f"実際: {list(backend_df.columns)}"
        )

    return backend_df


def read_backend_csv(
    backend_csv: Path | str = BACKEND_CSV,
    create_if_missing: bool = True,
) -> pd.DataFrame:
    """プロセス間ロック中にバックエンドCSVを読み込む。"""
    backend_csv = Path(backend_csv).expanduser().resolve()
    backend_csv.parent.mkdir(parents=True, exist_ok=True)

    with FileLock(
        str(get_lock_path(backend_csv)),
        timeout=CSV_LOCK_TIMEOUT_SECONDS,
    ):
        return _read_backend_csv_unlocked(
            backend_csv,
            create_if_missing=create_if_missing,
        )


def append_to_backend(
    events: pd.DataFrame,
    backend_csv: Path | str = BACKEND_CSV,
) -> tuple[int, int]:
    """プロセス間ロックと原子的置換でイベントを追記する。"""
    backend_csv = Path(backend_csv).expanduser().resolve()

    if list(events.columns) != BACKEND_COLUMNS:
        raise ValueError(
            "追記イベントの列が想定と異なります。\n"
            f"想定: {BACKEND_COLUMNS}\n"
            f"実際: {list(events.columns)}"
        )

    backend_csv.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with FileLock(
        str(get_lock_path(backend_csv)),
        timeout=CSV_LOCK_TIMEOUT_SECONDS,
    ):
        backend_df = _read_backend_csv_unlocked(
            backend_csv
        )
        before_count = len(backend_df)

        if events.empty:
            return 0, before_count

        if backend_df.empty:
            merged = events.copy()
        else:
            merged = pd.concat(
                [backend_df, events],
                ignore_index=True,
            )

        merged = (
            merged.drop_duplicates(
                subset=BACKEND_COLUMNS,
                keep="first",
            )
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        temporary_path = backend_csv.with_name(
            f".{backend_csv.name}.{uuid4().hex}.tmp"
        )

        try:
            merged.to_csv(
                temporary_path,
                index=False,
                encoding="utf-8-sig",
            )
            os.replace(
                temporary_path,
                backend_csv,
            )
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

        added_count = len(merged) - before_count
        return added_count, len(merged)


def merge_detections(
    source: Path | str,
    start_timestamp: str | datetime,
    device_id: str = "CAM001",
    action: str = "なし",
    gap_seconds: float = 1.0,
    backend_csv: Path | str = BACKEND_CSV,
    write: bool = True,
) -> tuple[pd.DataFrame, int, int]:
    """解析CSVをtrack_id単位のイベントへ変換し、必要なら追記する。"""
    parsed_timestamp = parse_start_timestamp(start_timestamp)
    raw_df = load_raw_detections(Path(source))
    events = build_backend_events(
        raw_df=raw_df,
        start_timestamp=parsed_timestamp,
        device_id=device_id,
        action=action,
        gap_seconds=gap_seconds,
    )

    if write:
        added_count, total_count = append_to_backend(
            events,
            backend_csv=backend_csv,
        )
    else:
        added_count = 0
        total_count = len(
            read_backend_csv(
                backend_csv,
                create_if_missing=False,
            )
        )

    return events, added_count, total_count


def main() -> None:
    """CLIから変換・追記処理を実行する。"""
    args = parse_args()

    events, added_count, total_count = merge_detections(
        source=args.source,
        start_timestamp=args.start_timestamp,
        device_id=args.device_id,
        action=args.action,
        gap_seconds=args.gap_seconds,
        write=not args.dry_run,
    )

    print("=" * 72)
    print("バックエンド形式への変換結果")
    print("=" * 72)
    print(events.to_string(index=False))
    print("-" * 72)
    print(f"変換イベント数: {len(events)}件")

    if args.dry_run:
        print(
            "dry-runのためdetections.csvには"
            "追記していません。"
        )
        return

    print(f"追記先        : {BACKEND_CSV}")
    print(f"新規追加件数  : {added_count}件")
    print(f"追記後の総件数: {total_count}件")


if __name__ == "__main__":
    main()
