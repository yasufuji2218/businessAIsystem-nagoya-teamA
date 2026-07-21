from __future__ import annotations

from pathlib import Path

from ultralytics import YOLO


# animal_detectionフォルダ
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# データセット設定ファイル
DATA_YAML = PROJECT_ROOT / "datasets" / "dataset.yaml"

# 学習結果の保存先
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "training"

# ローカルに保存するYOLO11 Nanoの初期モデル
BASE_MODEL_PATH = PROJECT_ROOT / "yolo11n.pt"


def main() -> None:
    """CPU環境でデモ用の動物検出モデルを学習する。"""

    if not DATA_YAML.is_file():
        raise FileNotFoundError(
            f"data.yamlが見つかりません: {DATA_YAML}"
        )

    # 軽量なYOLO11 Nanoモデルを使用
    # ファイルがなければ初回実行時に自動取得される
    model = YOLO(str(BASE_MODEL_PATH))

    model.train(
        # データセット
        data=str(DATA_YAML),

        # CPUで学習
        device="cpu",

        # 軽量化設定
        imgsz=320,
        epochs=15,
        batch=8,
        workers=2,

        # 事前学習済みモデルの前半部分を固定
        freeze=10,

        # 検証結果が改善しない場合の早期終了
        patience=5,

        # 学習結果の保存先
        project=str(OUTPUT_DIR),
        name="animal_demo",

        # 同じ名前の出力先を再利用
        exist_ok=True,

        # 学習済みモデルを保存
        save=True,

        # 学習結果のグラフを作成
        plots=True,

        # 詳細な進捗を表示
        verbose=True,
    )


if __name__ == "__main__":
    main()
