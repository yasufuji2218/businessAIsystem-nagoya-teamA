from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

import cv2
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = (
    ROOT
    / "outputs"
    / "training"
    / "animal_demo"
    / "weights"
    / "best.pt"
)
OUTPUT_ROOT = ROOT / "outputs" / "video_analysis"


def analyze_video(
    source: Path | str,
    confidence: float = 0.25,
    image_size: int = 320,
    show: bool = False,
    device: str = "cpu",
    tracker: str = "bytetrack.yaml",
    model_path: Path | str = MODEL_PATH,
    output_dir: Path | str | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    """
    MP4動画を追跡付きで解析する。

    Parameters
    ----------
    source:
        入力MP4動画のパス。
    confidence:
        検出に使用する最低信頼度。
    image_size:
        YOLOへ入力する画像サイズ。
    show:
        Trueの場合、処理中の映像を表示する。
    device:
        推論デバイス。CPUの場合は"cpu"。
    tracker:
        Ultralyticsのトラッカー設定。
    model_path:
        使用する学習済みモデルのパス。
    output_dir:
        出力先。省略時は動画名を使った既定ディレクトリ。
    progress_callback:
        処理済みフレーム数と総フレーム数を受け取る関数。

    Returns
    -------
    Path
        生成したdetections.csvのパス。
    """
    source = Path(source).expanduser().resolve()
    model_path = Path(model_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(
            f"動画が見つかりません: {source}"
        )

    if source.suffix.lower() != ".mp4":
        raise ValueError(
            f"MP4動画を指定してください: {source}"
        )

    if not model_path.is_file():
        raise FileNotFoundError(
            f"モデルが見つかりません: {model_path}"
        )

    if not 0.0 < confidence <= 1.0:
        raise ValueError(
            "confidenceは0より大きく1以下にしてください。"
        )

    if image_size <= 0:
        raise ValueError(
            "image_sizeは1以上にしてください。"
        )

    if output_dir is None:
        output_dir = OUTPUT_ROOT / source.stem
    else:
        output_dir = Path(output_dir).expanduser().resolve()

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    video_path = output_dir / "annotated.mp4"
    detection_path = output_dir / "detections.csv"
    frame_path = output_dir / "frame_summary.csv"
    summary_path = output_dir / "summary.json"

    model = YOLO(str(model_path))

    names = {
        int(class_id): str(class_name)
        for class_id, class_name in model.names.items()
    }

    class_ids = sorted(names)

    capture = cv2.VideoCapture(str(source))

    if not capture.isOpened():
        raise RuntimeError(
            f"動画を開けません: {source}"
        )

    fps = float(
        capture.get(cv2.CAP_PROP_FPS)
    )

    width = int(
        capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    total_frames = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    if fps <= 0:
        fps = 30.0

    if width <= 0 or height <= 0:
        capture.release()

        raise RuntimeError(
            "動画サイズを取得できません: "
            f"width={width}, height={height}"
        )

    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        capture.release()

        raise RuntimeError(
            f"出力動画を作成できません: {video_path}"
        )

    # フレーム単位の検出総数
    frame_detections: Counter[str] = Counter()

    # 1フレーム内で同時に検出された最大数
    max_simultaneous: Counter[str] = Counter()

    # クラスごとの追跡ID
    unique_tracks: dict[str, set[int]] = (
        defaultdict(set)
    )

    frames_with_detection = 0
    processed_frames = 0
    started_at = time.perf_counter()

    try:
        with (
            detection_path.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as detection_file,
            frame_path.open(
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as frame_file,
        ):
            detection_csv = csv.writer(
                detection_file
            )

            detection_csv.writerow(
                [
                    "frame",
                    "time_seconds",
                    "track_id",
                    "class_id",
                    "class_name",
                    "confidence",
                    "x1",
                    "y1",
                    "x2",
                    "y2",
                ]
            )

            frame_csv = csv.writer(frame_file)

            frame_csv.writerow(
                [
                    "frame",
                    "time_seconds",
                    "total",
                ]
                + [
                    f"count_{names[class_id]}"
                    for class_id in class_ids
                ]
            )

            while True:
                success, frame = capture.read()

                if not success:
                    break

                time_seconds = (
                    processed_frames / fps
                )

                # 連続フレーム間で追跡IDを維持する
                result = model.track(
                    frame,
                    imgsz=image_size,
                    conf=confidence,
                    device=device,
                    tracker=tracker,
                    persist=True,
                    verbose=False,
                )[0]

                counts: Counter[str] = Counter()
                boxes = result.boxes

                if (
                    boxes is not None
                    and len(boxes) > 0
                ):
                    class_id_list = (
                        boxes.cls
                        .int()
                        .cpu()
                        .tolist()
                    )

                    confidence_list = (
                        boxes.conf
                        .cpu()
                        .tolist()
                    )

                    coordinate_list = (
                        boxes.xyxy
                        .cpu()
                        .tolist()
                    )

                    if boxes.id is None:
                        track_id_list: list[
                            int | None
                        ] = [
                            None
                            for _ in class_id_list
                        ]

                    else:
                        track_id_list = (
                            boxes.id
                            .int()
                            .cpu()
                            .tolist()
                        )

                    for (
                        class_id,
                        confidence_value,
                        coordinates,
                        track_id,
                    ) in zip(
                        class_id_list,
                        confidence_list,
                        coordinate_list,
                        track_id_list,
                    ):
                        class_name = names[class_id]

                        x1, y1, x2, y2 = (
                            coordinates
                        )

                        counts[class_name] += 1
                        frame_detections[
                            class_name
                        ] += 1

                        if track_id is not None:
                            unique_tracks[
                                class_name
                            ].add(track_id)

                        detection_csv.writerow(
                            [
                                processed_frames,
                                round(
                                    time_seconds,
                                    3,
                                ),
                                track_id,
                                class_id,
                                class_name,
                                round(
                                    float(
                                        confidence_value
                                    ),
                                    6,
                                ),
                                round(
                                    float(x1),
                                    2,
                                ),
                                round(
                                    float(y1),
                                    2,
                                ),
                                round(
                                    float(x2),
                                    2,
                                ),
                                round(
                                    float(y2),
                                    2,
                                ),
                            ]
                        )

                total = sum(counts.values())

                if total > 0:
                    frames_with_detection += 1

                for (
                    class_name,
                    count,
                ) in counts.items():
                    max_simultaneous[
                        class_name
                    ] = max(
                        max_simultaneous[
                            class_name
                        ],
                        count,
                    )

                frame_csv.writerow(
                    [
                        processed_frames,
                        round(
                            time_seconds,
                            3,
                        ),
                        total,
                    ]
                    + [
                        counts[
                            names[class_id]
                        ]
                        for class_id in class_ids
                    ]
                )

                annotated = result.plot()
                writer.write(annotated)

                processed_frames += 1

                if (
                    progress_callback is not None
                    and (
                        processed_frames == 1
                        or processed_frames % 10 == 0
                        or processed_frames == total_frames
                    )
                ):
                    progress_callback(
                        processed_frames,
                        total_frames,
                    )

                if show:
                    cv2.imshow(
                        "Animal Detection",
                        annotated,
                    )

                    if (
                        cv2.waitKey(1) & 0xFF
                        == ord("q")
                    ):
                        break

                if processed_frames % 100 == 0:
                    if total_frames > 0:
                        print(
                            f"{processed_frames}/"
                            f"{total_frames}"
                            "フレーム処理済み"
                        )

                    else:
                        print(
                            f"{processed_frames}"
                            "フレーム処理済み"
                        )

    finally:
        capture.release()
        writer.release()
        cv2.destroyAllWindows()

    elapsed = (
        time.perf_counter() - started_at
    )

    summary = {
        "source": str(source),
        "model": str(model_path),
        "confidence_threshold": confidence,
        "image_size": image_size,
        "tracker": tracker,
        "fps": fps,
        "processed_frames": processed_frames,
        "video_duration_seconds": round(
            processed_frames / fps,
            3,
        ),
        "processing_time_seconds": round(
            elapsed,
            3,
        ),
        "frames_with_detection": (
            frames_with_detection
        ),
        "frame_detections_by_class": {
            name: frame_detections[name]
            for name in names.values()
        },
        "unique_tracks_by_class": {
            name: len(unique_tracks[name])
            for name in names.values()
        },
        "max_simultaneous_by_class": {
            name: max_simultaneous[name]
            for name in names.values()
        },
        "note": (
            "frame_detections_by_classは"
            "フレーム単位の検出総数です。"
            "unique_tracks_by_classは"
            "トラッカーが付与したID数です。"
        ),
    }

    summary_path.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 64)
    print("動画解析が完了しました")
    print(f"検出付き動画 : {video_path}")
    print(f"検出一覧CSV  : {detection_path}")
    print(f"フレーム集計 : {frame_path}")
    print(f"集計JSON     : {summary_path}")

    return detection_path


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を読み込む。"""
    parser = argparse.ArgumentParser(
        description="録画映像の動物検出・追跡"
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="入力MP4動画",
    )

    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="最低信頼度",
    )

    parser.add_argument(
        "--imgsz",
        type=int,
        default=320,
        help="推論画像サイズ",
    )

    parser.add_argument(
        "--device",
        default="cpu",
        help="推論デバイス",
    )

    parser.add_argument(
        "--tracker",
        default="bytetrack.yaml",
        help="Ultralyticsのトラッカー設定",
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=MODEL_PATH,
        help="学習済みモデル。既定値: outputs/training/.../best.pt",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="出力先ディレクトリ",
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="処理画面を表示",
    )

    return parser.parse_args()


def main() -> None:
    """コマンドラインから動画解析を実行する。"""
    args = parse_args()

    analyze_video(
        source=args.source,
        confidence=args.conf,
        image_size=args.imgsz,
        show=args.show,
        device=args.device,
        tracker=args.tracker,
        model_path=args.model,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
