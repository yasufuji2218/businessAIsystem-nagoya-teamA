# businessAIsystem-nagoya-teamA

野生動物の出没動画をYOLOで解析し、検知イベントをCSV、FastAPI、Reactダッシュボード、通知処理へつなぐデモ成果物です。

現段階では、ローカルに配置済みの input 動画を使った分析まで確認済みです。任意の新規動画、長時間動画、本番カメラ映像、継続運用での精度や安定性は今後の検証対象です。

## 現在の成果物

- YOLOによるMP4動画解析
- 検出付き動画、フレーム集計CSV、生検出CSV、集計JSONの生成
- `boar` / `monkey` の検出結果をダッシュボード用イベントCSVへ変換
- FastAPIによる検知データ取得、動画解析ジョブ登録、ジョブ状態確認
- React + Vite の簡易フロントエンドダッシュボード
- 検知履歴、時間帯別・曜日別集計、リアルタイム速報の表示
- `detections.csv` 更新を起点にした日次・週次・月次・年次集計と通知処理

## 現段階の確認結果

確認に使った入力動画はローカルの次のファイルです。

```text
src/inputs/videos/test_video.mp4
```

確認時の主な結果は次のとおりです。

| 項目 | 値 |
|---|---:|
| 処理フレーム数 | 622 |
| 動画時間 | 約25.943秒 |
| 生検出数 | 63件 |
| ダッシュボード用イベント数 | 11件 |
| 生検出の平均信頼度 | 0.3810 |
| イベント平均信頼度 | 0.3622 |
| 検出ありフレーム率 | 10.13% |

学習済みモデルの検証指標は `src/outputs/training/animal_demo/results.csv` から確認しています。

| 指標 | 値 |
|---|---:|
| Precision | 0.8831 |
| Recall | 0.7699 |
| F1推定値 | 0.8226 |
| mAP50 | 0.8535 |
| mAP50-95 | 0.6060 |

`confidence` は各検出に対するYOLOの確信度です。モデル全体の評価を見る場合は、`Precision`、`Recall`、`mAP50`、`mAP50-95` を参照してください。

## ディレクトリ構成

```text
project-root/
├── frontend/                       # React + Vite フロントエンド
├── src/
│   ├── backend/                    # FastAPI、分析API、集計CSV出力
│   ├── inputs/                     # ローカル入力動画など。現状はGit管理対象外
│   ├── notification/               # 通知用Excel更新、Slack通知、Launcher
│   ├── outputs/
│   │   ├── training/animal_demo/   # 学習済みYOLOモデル。best.ptのみGit管理
│   │   └── video_analysis/         # 動画解析結果。Git管理対象外
│   └── scripts/                    # 動画解析、検出結果マージ、学習補助
├── tests/                          # Python側テスト
├── docs/                           # 担当範囲、設計メモ
└── README.md
```

## セットアップ

Anaconda環境を使う場合の例です。

```powershell
conda activate yolo-backend
python -m pip install -r .\src\requirements.txt
```

OpenMP関連の競合でバックエンドが落ちる場合があるため、YOLOを動かすPowerShellでは次を設定してください。

```powershell
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:OMP_NUM_THREADS = "1"
```

通常のvenvで実行する場合は次の形でも動かせます。

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
```

フロントエンドにはNode.jsとnpmが必要です。

```powershell
cd .\frontend
npm install
```

## 起動方法

PowerShellを2つ開いて実行します。

1つ目でバックエンドを起動します。

```powershell
conda activate yolo-backend
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:OMP_NUM_THREADS = "1"
python -m uvicorn backend.api:app --app-dir .\src --host 127.0.0.1 --port 8000 --workers 1
```

2つ目でフロントエンドを起動します。

```powershell
cd .\frontend
npm run dev
```

表示されたViteのURLをブラウザで開きます。通常は次のURLです。

```text
http://localhost:5173
```

バックエンドAPI仕様は次で確認できます。

```text
http://127.0.0.1:8000/docs
```

## デモ実行

フロントエンドの分析レポート画面からMP4をアップロードすると、動画解析ジョブを登録できます。現段階で確認済みの入力は次の動画です。

```text
src/inputs/videos/test_video.mp4
```

コマンドで実行する場合は、バックエンド起動中にプロジェクトルートで次を実行します。

```powershell
curl.exe -X POST "http://127.0.0.1:8000/video-analysis/jobs" -F "video=@src/inputs/videos/test_video.mp4;type=video/mp4" -F "start_timestamp=2026-07-28 10:00:00" -F "device_id=CAM001" -F "action=なし" -F "confidence=0.25" -F "image_size=320" -F "device=cpu" -F "gap_seconds=1.0"
```

返ってきた `job_id` で状態を確認します。

```powershell
curl.exe "http://127.0.0.1:8000/video-analysis/jobs/<job_id>"
```

状態は主に次の4つです。

```text
queued     ジョブ受付済み
running    動画解析中
completed  正常完了
failed     解析失敗
```

`completed` になると、ダッシュボード用の `src/backend/detections.csv` にイベントが追記され、フロントエンドの検知履歴やグラフへ反映されます。

## 生成されるファイル

動画解析ジョブごとの成果物は次へ生成されます。

```text
src/outputs/video_analysis/jobs/<job_id>/
├── annotated.mp4       # 検出枠付き動画
├── detections.csv      # フレーム単位の生検出結果
├── frame_summary.csv   # フレーム単位の集計
└── summary.json        # 解析条件と集計サマリー
```

ダッシュボード用イベントCSVは次です。

```text
src/backend/detections.csv
```

`detections.csv` は存在しない場合、初回読み込みまたは解析結果保存時にヘッダー付きで自動生成されます。動画解析だけで直接生成されるのは主に `detections.csv` と動画解析成果物です。

日次・週次・月次・年次の分析CSVは、`backend.batch` または通知Launcherを動かしたときに生成・更新されます。

```text
src/backend/daily_analysis.csv
src/backend/weekly_analysis.csv
src/backend/monthly_analysis.csv
src/backend/yearly_analysis.csv
```

手動で集計する場合は次のように実行します。

```powershell
$env:PYTHONPATH = ".\src"
python -m backend.batch daily
python -m backend.batch weekly
python -m backend.batch monthly
python -m backend.batch yearly
```

## 通知システム

通知まで含めて確認する場合は、バックエンドとは別のPowerShellでLauncherを起動します。

```powershell
conda activate yolo-backend
$env:PYTHONPATH = ".\src"
python -m notification.notification_launcher --reset-baseline
```

Launcherは `src/backend/detections.csv` の更新を監視し、更新を検知すると次の処理を行います。

```text
detections.csv更新
  -> daily / weekly / monthly / yearly 集計
  -> notification_database.xlsx のrawシート更新
  -> 通知用データ計算
  -> Slack通知
```

Slack通知を使う場合は、プロジェクトルート直下の `.env` にIncoming Webhook URLを設定します。

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
```

`.env` は秘密情報のためGit管理しません。

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

将来、動画以外の軽量な入力定義、サンプルメタデータ、設定ファイルを公開する必要が出た場合は、`.gitignore` の `src/inputs/` を外し、動画とジョブ投入ファイルだけを除外する形へ変更してください。例は次のとおりです。

```gitignore
src/inputs/videos/
src/inputs/video_jobs/
src/inputs/**/*.mp4
src/inputs/**/*.mov
src/inputs/**/*.avi
```

この変更を行う場合も、データセット、学習済みモデル、動画、既存CSVを削除せず、公開対象だけを明示してGitへ追加してください。

## 既知の制限

- 現段階で実際に分析確認できているのは、ローカルにある `src/inputs/videos/test_video.mp4` です。
- 任意の新規動画や本番映像に対する検出精度、処理時間、安定性は未検証です。
- ジョブ状態はメモリ上に保持されるため、バックエンドを再起動すると過去の `job_id` は取得できません。
- 複数worker間でジョブ状態を共有しないため、FastAPIは `--workers 1` で起動してください。
- アップロード動画と解析成果物は自動削除されません。
- 現在のイベント変換対象は `boar` と `monkey` です。
- フロントエンドの警戒レベルや一部表示はデモ向けの簡易ロジックです。
- Anaconda環境ではOpenMP競合により落ちる場合があるため、必要に応じて `KMP_DUPLICATE_LIB_OK` と `OMP_NUM_THREADS` を設定してください。

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

## 個人が行ったこと

安藤担当領域

### 1. YOLOによる動画解析機能

YOLOを使って入力動画から野生動物を検出し、解析結果をファイルとして出力する部分を整備しました。

- 学習済みYOLOモデル `best.pt` を使ったMP4動画解析
- 検出枠付き動画 `annotated.mp4` の生成
- フレーム単位の生検出CSV `detections.csv` の生成
- フレーム集計CSV `frame_summary.csv` と解析サマリー `summary.json` の生成
- 検出信頼度 `confidence`、検出数、検出ありフレーム率などの確認

現段階では、ローカルにある `src/inputs/videos/test_video.mp4` を用いた解析まで確認済みです。

### 2. YOLO解析結果とデータ分析処理の結合

YOLOのフレーム単位の検出結果を、既存のデータ分析で扱えるイベント形式へ変換する処理を結合しました。

- YOLOの生検出結果を `timestamp`、`device_id`、`animal_type`、`confidence`、`action_triggered`、`stay_duration` の6列へ変換
- `boar` / `monkey` の検出を `イノシシ` / `サル` のイベントとして扱う処理
- `track_id` と連続検出区間をもとに、フレーム単位の検出を検知イベントへ集約
- `src/backend/detections.csv` への追記
- `daily_analysis.csv`、`weekly_analysis.csv`、`monthly_analysis.csv`、`yearly_analysis.csv` へつながる集計処理との接続確認

これにより、動画解析の結果を既存の分析・通知パイプラインで扱える形にしました。

### 3. バックエンドとフロントエンドの結合

FastAPIバックエンドとReactフロントエンドをつなぎ、画面上で検知データを確認できるようにしました。

- FastAPIに動画解析ジョブAPIを追加
- `/video-analysis/jobs` で動画解析ジョブを登録
- `/video-analysis/jobs/{job_id}` で解析状態と結果を確認
- `/detections` でダッシュボード用の検知履歴を取得
- Viteの `/api` プロキシ経由でフロントエンドからバックエンドへ接続
- フロントエンド上で検知履歴、速報、集計グラフを表示
- フロントエンドから動画解析を実行できる導線を追加

現在はデモ実行を優先した構成のため、ジョブ状態の永続化、本番用認証、アップロードファイルの保存期間管理などは今後の課題です。
