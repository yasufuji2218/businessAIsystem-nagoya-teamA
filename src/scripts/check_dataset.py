from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml
from PIL import Image, UnidentifiedImageError


# scripts/check_dataset.pyから見て、1つ上をプロジェクトルートとする
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# データセットの配置場所
DATASET_DIR = PROJECT_ROOT / "datasets"
DATA_YAML = DATASET_DIR / "dataset.yaml"

# 確認するデータ区分
SPLITS = ("train", "valid", "test")

# 読み込む画像形式
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
# ラベル座標の微小な丸め誤差を許容する
EDGE_TOLERANCE = 1e-4


def load_class_names() -> dict[int, str]:
    """data.yamlからクラスIDとクラス名を読み込む。"""
    if not DATA_YAML.is_file():
        raise FileNotFoundError(
            f"data.yamlが見つかりません: {DATA_YAML}"
        )

    with DATA_YAML.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    names = data.get("names")

    # names:
    #   - Monkey
    #   - Wild_Boar
    # というリスト形式
    if isinstance(names, list):
        return {
            class_id: str(name)
            for class_id, name in enumerate(names)
        }

    # names:
    #   0: Monkey
    #   1: Wild_Boar
    # という辞書形式
    if isinstance(names, dict):
        return {
            int(class_id): str(name)
            for class_id, name in names.items()
        }

    raise ValueError(
        "data.yamlにnamesが定義されていません。"
    )


def collect_files(
    directory: Path,
    extensions: set[str],
) -> dict[str, Path]:
    """
    指定フォルダ内のファイルを収集する。

    キー:
        拡張子を除いたファイル名

    値:
        ファイルのPath
    """
    files: dict[str, Path] = {}

    for path in directory.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in extensions:
            continue

        # monkey_001.jpgとmonkey_001.pngなど、
        # 同じstemのファイルが重複していないか確認
        if path.stem in files:
            raise ValueError(
                "同じ名前のファイルがあります: "
                f"{files[path.stem]} / {path}"
            )

        files[path.stem] = path

    return files


def validate_image(image_path: Path) -> list[str]:
    """画像ファイルが破損していないか確認する。"""
    try:
        with Image.open(image_path) as image:
            image.verify()

        return []

    except (UnidentifiedImageError, OSError) as error:
        return [
            f"画像を開けません: {image_path} ({error})"
        ]


def validate_label(
    label_path: Path,
    class_names: dict[int, str],
) -> tuple[list[str], Counter[int]]:
    """
    1つのYOLOラベルファイルを確認する。

    確認内容:
    ・1行が5項目か
    ・数値として読み込めるか
    ・クラスIDが整数か
    ・クラスIDがdata.yamlに存在するか
    ・座標が0～1の範囲か
    ・width、heightが0より大きいか
    ・検出枠が画像範囲外にはみ出していないか
    """
    errors: list[str] = []
    class_counts: Counter[int] = Counter()

    try:
        lines = label_path.read_text(
            encoding="utf-8-sig"
        ).splitlines()

    except UnicodeError as error:
        return (
            [
                f"UTF-8で読み込めません: "
                f"{label_path} ({error})"
            ],
            class_counts,
        )

    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        line = raw_line.strip()

        # 空行は無視する
        if not line:
            continue

        parts = line.split()
        location = f"{label_path}:{line_number}"

        # YOLO物体検出形式は5項目
        if len(parts) != 5:
            errors.append(
                f"{location}: 項目数が{len(parts)}個です。"
                "必要形式は "
                "class x_center y_center width height "
                "の5項目です。"
            )
            continue

        try:
            class_value = float(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])

        except ValueError:
            errors.append(
                f"{location}: "
                "数値以外の値が含まれています。"
            )
            continue

        # 0.0や1.0は許容するが、0.5などは不正
        if not class_value.is_integer():
            errors.append(
                f"{location}: "
                f"クラスIDは整数にしてください: "
                f"{parts[0]}"
            )
            continue

        class_id = int(class_value)

        if class_id not in class_names:
            errors.append(
                f"{location}: "
                f"未定義のクラスID {class_id} です。"
                f"使用可能なID: {sorted(class_names)}"
            )

        coordinates = {
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height,
        }

        # 正規化座標が0～1に収まっているか確認
        for coordinate_name, value in coordinates.items():
            if not 0.0 <= value <= 1.0:
                errors.append(
                    f"{location}: "
                    f"{coordinate_name}={value} は"
                    "0～1の範囲外です。"
                )

        if width <= 0.0 or height <= 0.0:
            errors.append(
                f"{location}: "
                "widthとheightは0より大きくしてください。"
            )

        # 中心座標と幅・高さから四隅を計算
        x_min = x_center - width / 2
        x_max = x_center + width / 2
        y_min = y_center - height / 2
        y_max = y_center + height / 2

        if (
    x_min < -EDGE_TOLERANCE
    or x_max > 1.0 + EDGE_TOLERANCE
    or y_min < -EDGE_TOLERANCE
    or y_max > 1.0 + EDGE_TOLERANCE
        ):
            errors.append(
                f"{location}: "
                "検出枠が画像範囲外にはみ出しています。"
                f" xmin={x_min:.6f},"
                f" ymin={y_min:.6f},"
                f" xmax={x_max:.6f},"
                f" ymax={y_max:.6f}"
            )

        class_counts[class_id] += 1

    return errors, class_counts


def check_split(
    split: str,
    class_names: dict[int, str],
) -> tuple[
    list[str],
    list[str],
    Counter[int],
    int,
]:
    """
    train、valid、testのいずれか1区分を確認する。
    """
    image_dir = DATASET_DIR / split / "images"
    label_dir = DATASET_DIR / split / "labels"

    errors: list[str] = []
    warnings: list[str] = []
    class_counts: Counter[int] = Counter()

    if not image_dir.is_dir():
        errors.append(
            f"画像フォルダがありません: {image_dir}"
        )

    if not label_dir.is_dir():
        errors.append(
            f"ラベルフォルダがありません: {label_dir}"
        )

    if errors:
        return errors, warnings, class_counts, 0

    try:
        images = collect_files(
            image_dir,
            IMAGE_EXTENSIONS,
        )

        labels = collect_files(
            label_dir,
            {".txt"},
        )

    except ValueError as error:
        return (
            [str(error)],
            warnings,
            class_counts,
            0,
        )

    if not images:
        errors.append(
            f"画像が1枚もありません: {image_dir}"
        )

    image_names = set(images)
    label_names = set(labels)

    # ラベルのない画像
    # 対象物が写っていない画像では正常な場合があるため警告
    for stem in sorted(image_names - label_names):
        warnings.append(
            f"ラベルがない画像: {images[stem]}"
        )

    # 対応する画像がないラベルはエラー
    for stem in sorted(label_names - image_names):
        errors.append(
            f"対応画像がないラベル: {labels[stem]}"
        )

    # 画像破損確認
    for image_path in images.values():
        errors.extend(
            validate_image(image_path)
        )

    # ラベル内容確認
    for label_path in labels.values():
        label_errors, counts = validate_label(
            label_path,
            class_names,
        )

        errors.extend(label_errors)
        class_counts.update(counts)

    return (
        errors,
        warnings,
        class_counts,
        len(images),
    )


def main() -> int:
    """データセット全体を確認する。"""
    try:
        class_names = load_class_names()

    except (
        FileNotFoundError,
        ValueError,
        yaml.YAMLError,
    ) as error:
        print(f"[ERROR] {error}")
        return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    total_class_counts: Counter[int] = Counter()
    total_images = 0

    print("=" * 72)
    print("YOLOデータセット確認")
    print("=" * 72)
    print(f"データセット: {DATASET_DIR}")
    print(f"設定ファイル: {DATA_YAML}")
    print(f"クラス      : {class_names}")

    for split in SPLITS:
        (
            errors,
            warnings,
            class_counts,
            image_count,
        ) = check_split(
            split,
            class_names,
        )

        all_errors.extend(errors)
        all_warnings.extend(warnings)
        total_class_counts.update(class_counts)
        total_images += image_count

        print("-" * 72)
        print(
            f"{split:<5} | "
            f"画像 {image_count:>5}枚 | "
            f"物体 {sum(class_counts.values()):>6}個 | "
            f"エラー {len(errors):>4}件 | "
            f"警告 {len(warnings):>4}件"
        )

    print("-" * 72)
    print("クラス別物体数")

    for class_id, class_name in sorted(
        class_names.items()
    ):
        print(
            f"  {class_id}: "
            f"{class_name:<20} "
            f"{total_class_counts[class_id]:>6}個"
        )

    if all_warnings:
        print("-" * 72)
        print(
            f"[WARNING] {len(all_warnings)}件"
        )

        for message in all_warnings:
            print(f"  - {message}")

    if all_errors:
        print("-" * 72)
        print(
            f"[ERROR] {len(all_errors)}件"
        )

        for message in all_errors:
            print(f"  - {message}")

    print("-" * 72)
    print(f"合計画像数: {total_images}枚")

    if all_errors:
        print("判定: 修正が必要です。")
        return 1

    print("判定: 学習を開始できます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())