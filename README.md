# businessAIsystem-nagoya-teamA

野生動物の出没動画をYOLOで解析し、検知イベントをFastAPI、Reactダッシュボード、集計・通知処理へつなぐ大学チーム開発の成果物です。

就職活動向けに、実装内容、担当範囲、動作検証結果、現時点の制限が分かるように整理しています。

## プロジェクト概要

野生動物による農作物被害などを想定し、カメラ映像から動物の出没を検知して、ダッシュボード上で確認できるシステムを構築しました。

主な流れは次のとおりです。

```text
MP4動画
  -> YOLOによる動物検出
  -> フレーム単位の検出CSV生成
  -> 検知イベント形式へ変換
  -> FastAPIでデータ提供
  -> Reactダッシュボードで可視化
  -> 集計CSV・通知処理へ連携
```

## 主な機能

- MP4動画を対象にしたYOLO推論
- 検出枠付き動画、検出CSV、フレーム集計CSV、解析JSONの生成
- `boar` / `monkey` の検出結果を `イノシシ` / `サル` の検知イベントへ変換
- `src/backend/detections.csv` を中心にしたデータ分析処理
- FastAPIによる検知履歴、出没ピーク、慣れ度、罠設置推奨スコアの提供
- React + Vite による簡易ダッシュボード
- 動画解析ジョブの登録、進行状況確認、結果反映
- `detections.csv` 更新を起点にした日次・週次・月次・年次集計
- 通知Launcherを経由したSlack通知処理

## 技術スタック

| 領域 | 使用技術 |
|---|---|
| AI / 動画解析 | Ultralytics YOLO, OpenCV |
| バックエンド | Python, FastAPI, pandas |
| フロントエンド | React, Vite, Recharts, Tailwind CSS |
| 通知 | Slack Incoming Webhook |
| データ保存 | CSV, Excel |
| テスト | pytest, Vitest |

## 開発体制と担当範囲

- 開発人数：4人
- 開発期間：2026年6月～7月
- 開発形式：大学でのチーム開発

### 安藤の担当

- YOLOモデルの学習と評価
- MP4動画を対象とした動物検出処理
- 検出結果CSVの生成
- フレーム単位の検出結果を検知イベント形式へ変換する処理
- FastAPIへの動画解析機能の統合
- ReactフロントエンドとFastAPIバックエンドの接続
- 動画解析結果を既存の集計・通知処理へ統合
- `detections.csv` 更新から通知Launcher、Slack送信へつながる流れの確認

## システム構成

```text
project-root/
├── frontend/                       # React + Vite フロントエンド
├── src/
│   ├── backend/                    # FastAPI、分析API、集計CSV出力
│   ├── inputs/                     # ローカル入力動画など。現状はGit管理対象外
│   ├── notification/               # 通知用Excel更新、Slack通知、Launcher
│   ├── outputs/
│   │   ├── training/animal_demo/   # YOLOモデル。best.ptのみGit管理
│   │   └── video_analysis/         # 動画解析結果。Git管理対象外
│   └── scripts/                    # 動画解析、検出結果マージ、学習補助
├── tests/                          # Python側テスト
├── assets/readme/                  # README掲載用画像
└── README.md
```

## YOLOモデル

実装コードでは、既定モデルとして次のファイルを参照します。

```text
src/outputs/training/animal_demo/weights/best.pt
```

参照元は次のPythonファイルです。

- `src/scripts/analyze_video.py`
- `src/backend/api.py`

`analyze_video.py` のCLIでは `--model` 引数でモデルパスを指定できます。ただし、FastAPIの通常実行では上記の `MODEL_PATH` を使用します。

今回、実装コードを変更せずにモデルを差し替えるため、ユーザー指定の新しいモデル `C:/Users/anmin/Desktop/yolo11n.pt` を既存パスの `best.pt` として配置しました。ファイル名と配置場所は維持しています。

| 項目 | 旧モデル | 新モデル |
|---|---:|---:|
| リポジトリ内パス | `src/outputs/training/animal_demo/weights/best.pt` | `src/outputs/training/animal_demo/weights/best.pt` |
| 提供元パス | 既存ファイル | `C:/Users/anmin/Desktop/yolo11n.pt` |
| ファイルサイズ | 5,423,450 bytes | 19,165,914 bytes |
| SHA-256 | `d578284d7f8cc8fca51833226a82e65fbcebd578023eea0693baaac301895102` | `c075647acb250e93324d203088d812bea807cb91dd0a14a4a42822f594c34517` |
| クラス数 | 2 | 2 |
| クラスID | `0: boar`, `1: monkey` | `0: boar`, `1: monkey` |

新モデルはUltralytics YOLOの `DetectionModel` として読み込み確認済みです。FastAPI側の `MODEL_PATH` からも同じモデルを読み込めることを確認しています。

## 動作検証

利用条件を確認できる公開動画を使って、差し替え後モデルの推論を検証しました。

| 用途 | 動画 | 配布元 | ライセンス |
|---|---|---|---|
| イノシシ確認 | [Wild Boars Foraging in Natural Habitat Outdoors](https://www.pexels.com/video/wild-boars-foraging-in-natural-habitat-outdoors-28583161/) | Pexels | [Pexels License](https://www.pexels.com/license/) |
| サル確認 | [Barbary Macaque, Monkey, Barbary](https://pixabay.com/videos/barbary-macaque-monkey-barbary-2262/) | Pixabay / InspiredImages | [Pixabay Content License](https://pixabay.com/service/terms/#license) |

サル動画に映っている動物はバーバリーマカクです。汎用的な `monkey` クラスの動作確認に使用しており、ニホンザルや日本国内の実環境で検証した結果ではありません。

推論条件は次のとおりです。実装コード内の既定値は変更していません。

| 項目 | 値 |
|---|---:|
| confidence | 0.25 |
| image_size | 320 |
| device | cpu |
| tracker | bytetrack.yaml |

### 推論結果

| 検証動画 | 処理フレーム | 検出ありフレーム | 生検出数 | 主な結果 |
|---|---:|---:|---:|---|
| イノシシ動画 | 957 | 15 | 16 | 検出失敗。`boar` は0件で、`monkey` として16件誤検出された |
| サル動画 | 406 | 406 | 1,710 | `monkey` として検出。平均信頼度0.6613、最大信頼度0.8798 |

検出結果は手作業で修正していません。イノシシ動画では `boar` 検出に失敗し、`monkey` として誤検出されたため、今後の追加学習・データセット見直しが必要です。

### 検出結果画像

イノシシ動画での実推論結果です。実際にはイノシシが映っていますが、差し替え後モデルでは `boar` 検出に失敗し、`monkey` として誤検出しています。

![イノシシ動画での推論結果](assets/readme/yolo-boar-video-result.jpg)

サル動画での実推論結果です。複数個体を `monkey` として検出しています。

![サル動画での推論結果](assets/readme/yolo-monkey-video-result.jpg)

### 使用した推論コマンド

```powershell
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:OMP_NUM_THREADS = "1"

python .\src\scripts\analyze_video.py `
  --source "C:\Users\anmin\Downloads\12426691_2160_3840_60fps.mp4" `
  --conf 0.25 `
  --imgsz 320 `
  --device cpu `
  --output-dir "$env:TEMP\codex_yolo_validation_20260730_0400\boar"

python .\src\scripts\analyze_video.py `
  --source "C:\Users\anmin\Downloads\2262-157140556_medium.mp4" `
  --conf 0.25 `
  --imgsz 320 `
  --device cpu `
  --output-dir "$env:TEMP\codex_yolo_validation_20260730_0400\monkey"
```

既存のイベント変換処理も `--dry-run` で確認しました。実運用CSVへは追記していません。

```powershell
python .\src\scripts\merge_detections.py `
  --source "$env:TEMP\codex_yolo_validation_20260730_0400\boar\detections.csv" `
  --start-timestamp "2026-07-30 10:00:00" `
  --device-id PEXELS_BOAR `
  --action なし `
  --gap-seconds 1.0 `
  --dry-run

python .\src\scripts\merge_detections.py `
  --source "$env:TEMP\codex_yolo_validation_20260730_0400\monkey\detections.csv" `
  --start-timestamp "2026-07-30 11:00:00" `
  --device-id PIXABAY_MONKEY `
  --action なし `
  --gap-seconds 1.0 `
  --dry-run
```

## 起動方法

Anaconda環境での実行例です。

```powershell
conda activate yolo-backend
python -m pip install -r .\src\requirements.txt
```

OpenMP関連の競合でバックエンドが落ちる場合があるため、YOLOを動かすPowerShellでは次を設定してください。

```powershell
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:OMP_NUM_THREADS = "1"
```

バックエンドを起動します。

```powershell
python -m uvicorn backend.api:app --app-dir .\src --host 127.0.0.1 --port 8000 --workers 1
```

別のPowerShellでフロントエンドを起動します。

```powershell
cd .\frontend
npm install
npm run dev
```

表示されたViteのURLをブラウザで開きます。通常は次のURLです。

```text
http://localhost:5173
```

API仕様は次で確認できます。

```text
http://127.0.0.1:8000/docs
```

## API一覧

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/` | API疎通確認 |
| GET | `/detections` | ダッシュボード用検知イベント取得 |
| GET | `/appearance` | 時間帯別の出没ピーク取得 |
| GET | `/habituation` | 慣れ度スコア取得 |
| GET | `/trap` | 罠設置推奨スコア取得 |
| POST | `/video-analysis/jobs` | MP4動画解析ジョブ登録 |
| GET | `/video-analysis/jobs/{job_id}` | 動画解析ジョブ状態確認 |

## 生成されるファイル

動画解析ジョブごとの成果物は次へ生成されます。

```text
src/outputs/video_analysis/jobs/<job_id>/
├── annotated.mp4
├── detections.csv
├── frame_summary.csv
└── summary.json
```

ダッシュボード用イベントCSVは次です。

```text
src/backend/detections.csv
```

`detections.csv` は存在しない場合、初回読み込みまたは解析結果保存時にヘッダー付きで自動生成されます。

日次・週次・月次・年次の分析CSVは、`backend.batch` または通知Launcherを動かしたときに生成・更新されます。

```text
src/backend/daily_analysis.csv
src/backend/weekly_analysis.csv
src/backend/monthly_analysis.csv
src/backend/yearly_analysis.csv
```

通知まで含めて確認する場合は、バックエンドとは別のPowerShellでLauncherを起動します。

```powershell
$env:PYTHONPATH = ".\src"
python -m notification.notification_launcher --reset-baseline
```

Slack通知を使う場合は、プロジェクトルート直下の `.env` にIncoming Webhook URLを設定します。

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
```

`.env` は秘密情報のためGit管理しません。

## Git管理方針

次のファイルは実行時生成物または容量が大きいファイルのため、Git管理しません。

- `src/inputs/`
- `src/inputs/video_jobs/`
- `*.mp4`
- `src/outputs/video_analysis/`
- `src/backend/detections.csv`
- `src/backend/*_analysis.csv`
- `src/backend/*_backup.csv`
- `frontend/dist/`
- `node_modules/`
- `.env`

学習済みモデルは、バックエンド実行に必要な次のファイルだけをGit管理します。

```text
src/outputs/training/animal_demo/weights/best.pt
```

現時点では `src/inputs/` 配下に公開すべき軽量ファイルがなく、動画ファイルだけが確認対象のため、inputディレクトリ全体をGit管理対象外にしています。

将来、動画以外の軽量な入力定義、サンプルメタデータ、設定ファイルを公開する必要が出た場合は、`.gitignore` の `src/inputs/` を外し、動画とジョブ投入ファイルだけを除外する形へ変更してください。

```gitignore
src/inputs/videos/
src/inputs/video_jobs/
src/inputs/**/*.mp4
src/inputs/**/*.mov
src/inputs/**/*.avi
```

## 既知の制限

- 現段階で確認できているのは、ローカルにある検証動画を用いたデモ実行です。
- 任意の新規動画や本番映像に対する検出精度、処理時間、安定性は未検証です。
- 差し替え後モデルでは、イノシシ動画の `boar` 検出に失敗し、`monkey` として誤検出されました。
- ジョブ状態はメモリ上に保持されるため、バックエンドを再起動すると過去の `job_id` は取得できません。
- 複数worker間でジョブ状態を共有しないため、FastAPIは `--workers 1` で起動してください。
- アップロード動画と解析成果物は自動削除されません。
- 現在のイベント変換対象は `boar` と `monkey` です。
- フロントエンドの警戒レベルや一部表示はデモ向けの簡易ロジックです。

## テスト

バックエンド側のテストは次で実行します。

```powershell
conda activate yolo-backend
python -m pytest tests
```

フロントエンドのビルド確認は次で実行します。

```powershell
cd .\frontend
npm run build
```
