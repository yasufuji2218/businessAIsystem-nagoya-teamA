# businessAIsystem-nagoya-teamA
ビジネスAIシステム開発後半開発

## 開発ルール

<!-- TODO: ブランチ命名規則・コミットメッセージ規則などを記入してください -->

## 0. Git/GitHubの基本用語とイメージ（初心者向け）
Gitに初めて触れる方向けの簡単な用語解説です。ゲームのセーブ機能などに例えると分かりやすいです。

* **Git（ギット）**: コードの変更履歴を記録する「タイムマシン」のようなシステム。
* **GitHub（ギットハブ）**: Gitの記録をインターネット上に保存し、みんなで共有する「クラウドの保管庫」。
* **ブランチ（Branch）**: メインのコードを壊さずに作業するための「自分専用のコピー（作業机）」。作業が終わったらメインに合流させます。
* **コミット（Commit）**: 作業のキリが良いところで行う「セーブ（記録）」。セーブデータには「何を変えたか」のメモ（コミットメッセージ）を残します。
* **プッシュ（Push）**: 手元のPCで行ったセーブデータを、GitHubに「アップロード」すること。
* **プルリクエスト（PR）**: 自分の作業（ブランチ）をメインのコードに「合流させてもいいですか？」とチームに提案・レビューしてもらう機能。

**⚠️ エラーが起きたときのSOSルール**
Gitの操作中によくわからない英語のエラーが出たり、手順通りに進まなくなった場合は、**絶対に勘でコマンドを実行しないでください。**（誤ってチームのコードを消してしまう可能性があります）
エラーが出たら操作を止め、画面のスクリーンショットを撮ってすぐにチームメンバーに相談してください。

**💡 豆知識：もし黒い画面で文字が入力できなくなったら？（vimが開いた場合）**
コマンド入力中、突然画面が切り替わって操作を受け付けなくなった場合は、`vim` というテキストエディタが起動しています。慌てずに以下のキーボード操作を順番に押すと、元の画面に脱出できます。
1. `Esc` キーを押す
2. 半角で `:q!` と入力する（画面の一番下に入力されます）
3. `Enter` キーを押す

### 1.概要

チーム開発を円滑に進めるためのブランチ命名規則とコミットメッセージの規則を設定する。

前提として１つのタスクに対して１つのブランチを作成するものとする。

### 2.ブランチの命名規則

| プレフィックス |               意味・用途               |              例              |
|:--------------:|:--------------------------------------:|:----------------------------:|
| feature/       | 新機能の開発                           | feature/news-scoring-logic   |
| fix/           | バグの修正                             | fix/db-connection-error      |
| docs/          | ドキュメント（README等）の更新         | docs/update-roadmap          |
| refactor/      | リファクタリング（機能を変えない整理） | refactor/api-response-format |
| chore/         | ライブラリの導入や雑務的な変更         | chore/add-pydantic-v2        |

ブランチ名は上記の表に基づいて命名するものとする。以下にブランチ名の例を複数挙げる。

* 例１.タイムラインを作成するタスクの場合：feature/make-timeline

* 例２.タイムラインにバグが発生したため、改善するコードを作成する場合：fix/timeline-connection-error

## 3.具体的な手順

**①：新しいブランチを作る**
まず、手元のPCで `main` から新しい枝を作ります。

最新のmainにいることを確認

```bash
git checkout main
```

```bash
git pull origin main
```

新しいブランチを作って移動

```bash
git checkout -b feature/fix-logo
```

**②コードを書いて保存**

```bash
git add .
```

```bash
git commit -m "Add transparent logo and update README"
```

**③自分のブランチをGitHubへアップロード**

```bash
git push origin feature/fix-logo
```

**④プルリクエストを出す**

GitHubの画面に行くと「Compare & pull request」というボタンが出ています。
これを押して、「この変更を main に合流させてもいいですか？」というリクエストをチームに送ります。

![Compare & pull request](images/プルリクエスト.png)


### 4.コミット時のコメント規則

```bash
git commit -m "コメント"
```
コミット時のコメントとは、上記の`"コメント"`の部分のことである。
コメント形式には、「何を変えたか」を一目で伝えるため、Conventional Commits という世界標準の書き方を簡略化したものを採用する。

```bash
タイプ：変更内容
```
**タイプ一覧**

- **feat**: 新機能（FastAPIの新しいエンドポイント追加など）
- **fix**: バグ修正
- **docs**: ドキュメントのみの変更
- **style**: コードの動作に影響しない修正（インデント、セミコロン等）
- **refactor**: 機能追加もバグ修正も行わないコード変更
- **chore**: ビルドプロセスや補助ツールの変更

### 5. 日常開発でよく使う基本コマンド集
開発中に「現在の状態を確認したい」「過去の履歴を見たい」というときに使う重要なコマンドです。

## ① 状態・変更を確認する
```bash
# 現在どのブランチにいるか、どのファイルが変更されているかを確認する（最重要）
git status

# 具体的にどの行を書き換えたか（差分）を確認する
git diff
```
## ② 履歴を確認する
```bash
# これまでのコミット履歴（誰が・いつ・どんなメッセージでセーブしたか）を一覧表示する
git log

# 履歴を1行でコンパクトに表示する
git log --oneline
```
## ③ ブランチを管理する
```bash
# ローカルにあるブランチの一覧を表示する（現在いるブランチには * がつきます）
git branch

# リモート（GitHub）にあるブランチも含めてすべて表示する
git branch -a
```
## ④ リモートの最新状態を取り込む（git pull）
他のメンバーが main や共有ブランチを更新したとき、その最新コードを手元のPCに取り込むためのコマンドです。

```bash
# リモート（origin）の main ブランチの最新状態を、今いるローカルブランチに合流させる
git pull origin main
```

6. ディレクトリ構成（ファイル配置ルール）
本リポジトリでは、以下のディレクトリ構成に従ってファイルを配置してください。
（※各ディレクトリの役割以外の場所にファイルを勝手に作成しないこと）

```text
project-root/
├── .github/       # GitHub Actionsなどの設定ファイル
├── docs/          # 設計書、議事録、マニュアル等のドキュメント
├──imgaes/         # 画像ファイル(プログラムに使うものは"src/"に入れる)
├── src/           # アプリケーションのソースコード本体
├── tests/         # テストコード
├── .gitignore     # Gitの管理から除外するファイルの設定
└── README.md      # このファイル
```

## YOLO動画解析バックエンド

### セットアップと起動

プロジェクトルートで仮想環境を作成し、`src/requirements.txt` をインストールします。

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --app-dir .\src --host 127.0.0.1 --port 8000 --workers 1
```

起動後は `http://127.0.0.1:8000/docs` でAPI仕様を確認できます。既存APIは `/`、`/appearance`、`/habituation`、`/trap` です。

### 動画解析ジョブAPI

MP4、撮影開始日時、カメラIDなどをmultipart formで送信します。応答はHTTP 202で、解析ジョブIDと状態確認URLを返します。

```powershell
curl.exe -X POST "http://127.0.0.1:8000/video-analysis/jobs" `
  -F "video=@src/inputs/videos/test_video.mp4;type=video/mp4" `
  -F "start_timestamp=2026-07-21 10:00:00" `
  -F "device_id=CAM001" `
  -F "action=なし" `
  -F "confidence=0.25" `
  -F "image_size=320" `
  -F "device=cpu" `
  -F "gap_seconds=1.0"
```

返されたIDで `queued`、`running`、`completed`、`failed` の状態を確認します。

```powershell
curl.exe "http://127.0.0.1:8000/video-analysis/jobs/<job_id>"
```

完了すると、検出付き動画・フレーム集計CSV・追跡検出CSV・集計JSONを `src/outputs/video_analysis/jobs/<job_id>/` に保存します。`boar` と `monkey` の検出は `track_id` と連続検出区間ごとにイベント化し、既存6列の `src/backend/detections.csv` へ安全に追記します。

### CLIとPython関数

動画解析だけをCLIで実行できます。

```powershell
.\.venv\Scripts\python.exe .\src\scripts\analyze_video.py `
  --source .\src\inputs\videos\test_video.mp4 `
  --model .\src\outputs\training\animal_demo\weights\best.pt `
  --conf 0.25 --imgsz 320 --device cpu
```

解析CSVをバックエンドイベントへ変換・追記する場合は次を実行します。

```powershell
.\.venv\Scripts\python.exe .\src\scripts\merge_detections.py `
  --source .\src\outputs\video_analysis\test_video\detections.csv `
  --start-timestamp "2026-07-21 10:00:00" `
  --device-id CAM001 --action なし --gap-seconds 1.0
```

Pythonからは `scripts.analyze_video.analyze_video(...)` と `scripts.merge_detections.merge_detections(...)` を呼び出せます。`src` をPythonのモジュール検索パスに含めてください。

### 制限事項

- ジョブ状態はメモリ上に保持されるため、API再起動後は取得できません。複数worker間でも共有されないため、現在は必ず `--workers 1` で起動してください。
- 同一プロセス内のYOLO解析はメモリ競合を避けるため1件ずつ実行します。CPU実行では長い動画の処理に時間がかかります。
- アップロード上限は2 GiBです。アップロード動画と解析成果物は自動削除されません。運用時は認証、容量監視、保存期間管理を別途追加してください。
- 既定モデルは `src/outputs/training/animal_demo/weights/best.pt` です。イベント変換対象はクラス名が `boar` または `monkey` の検出に限られ、その他のクラスは解析成果物には残りますがバックエンドCSVへは追加されません。
- `track_id` は1本の動画内でのみ有効です。動画をまたぐ同一個体判定は行いません。
- CLIの既定出力先は入力動画のstem名で決まるため、同名動画を再解析すると同じ出力先を使用します。保存が必要な場合は `--output-dir` で別ディレクトリを指定してください。

### Git管理と実行時CSV

- バックエンド実行に必要な学習済みモデルは `src/outputs/training/animal_demo/weights/best.pt` だけをGit管理します。
- 入力動画、動画解析結果、学習グラフ、`last.pt`、`src/yolo11n.pt`、バックアップCSVはローカル生成物としてGit管理しません。
- `src/backend/detections.csv` と `*_analysis.csv` は実行時データのためGit管理しません。存在しない場合は、初回読み込みまたは保存時に必要なヘッダー付きで自動生成されます。
- 動作確認用データは `src/backend/detections_sample.csv` に分離し、実運用CSVへ自動混入しません。

## 通知システムを含む統合実行手順（PowerShell 3画面）

この手順では、FastAPI、通知Launcher、動画解析ジョブ投入を別々のPowerShellで実行します。
各処理のログを個別に確認できるため、結合動作の確認時はこちらを使用してください。

### 事前準備

プロジェクトルートで必要ライブラリをインストールします。

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\.venv\Scripts\python.exe -m pip install python-dotenv filelock openpyxl
```

プロジェクトルート直下に `.env` を配置します。

```text
project-root/
├── .env
├── .gitignore
├── .venv/
└── src/
```

`.env` にはSlack Incoming Webhook URLを設定します。

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
```

`.env` は秘密情報を含むため、Gitへ登録しません。`.gitignore` に次を追加してください。

```gitignore
.env
```

実行中は、以下のCSVとExcelをExcel・エディター・プレビュー機能で開かないでください。Windowsのファイルロックにより、CSVまたはExcelの置換保存に失敗することがあります。

```text
src/backend/daily_analysis.csv
src/backend/weekly_analysis.csv
src/backend/monthly_analysis.csv
src/backend/yearly_analysis.csv
src/notification/result/notification_database.xlsx
```

### 実行順序

```text
PowerShell 1：FastAPIを起動
        ↓
PowerShell 2：notification_launcher.pyを起動してCSV更新待機
        ↓
PowerShell 3：curlで動画解析ジョブを登録
        ↓
FastAPIが動画解析を実行
        ↓
src/backend/detections.csvを追加・更新
        ↓
Launcherが更新を検知
        ↓
daily / weekly / monthly / yearly バッチを実行
        ↓
notification_database.xlsxのrawシートを更新
        ↓
通知用データを計算
        ↓
notificationシートへ書き込み
        ↓
Slackへ通知
```

### PowerShell 1：FastAPIの起動

プロジェクトルートで実行します。

```powershell
$env:PYTHONPATH = ".\src"

.\.venv\Scripts\python.exe -m uvicorn backend.api:app `
  --app-dir .\src `
  --host 127.0.0.1 `
  --port 8000 `
  --workers 1
```

次の表示が出れば起動成功です。

```text
Uvicorn running on http://127.0.0.1:8000
```

このPowerShellは閉じず、そのまま待機させます。動画解析の進行状況もこの画面へ表示されます。

### PowerShell 2：通知Launcherの起動

別のPowerShellを開き、プロジェクトルートへ移動します。

```powershell
cd C:\Users\matsukiymato\businessAIsystem-nagoya-teamA
$env:PYTHONPATH = ".\src"

.\.venv\Scripts\python.exe `
  -m notification.notification_launcher `
  --reset-baseline
```

次の表示が出れば正常な待機状態です。

```text
実行環境の確認が完了しました。
現在のdetections.csvを監視開始時点の基準として登録しました。
動画解析ジョブによる次回のCSV追加・更新を待機します。
```

`--reset-baseline` は、Launcher起動時点の既存 `src/backend/detections.csv` を処理済みの基準として登録し、その後の追加・更新だけを検知するための指定です。

このPowerShellも閉じず、そのまま待機させます。

### PowerShell 3：動画解析ジョブの登録

3つ目のPowerShellを開き、プロジェクトルートへ移動します。

```powershell
cd C:\Users\matsukiymato\businessAIsystem-nagoya-teamA
```

次のコマンドで動画解析ジョブを登録します。

```powershell
curl.exe -X POST "http://127.0.0.1:8000/video-analysis/jobs" `
  -F "video=@src/inputs/videos/test_video.mp4;type=video/mp4" `
  -F "start_timestamp=2026-07-21 10:00:00" `
  -F "device_id=CAM001" `
  -F "action=なし" `
  -F "confidence=0.25" `
  -F "image_size=320" `
  -F "device=cpu" `
  -F "gap_seconds=1.0"
```

正常に受け付けられると、HTTP 202とジョブIDが返ります。

```json
{
  "job_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "queued",
  "status_url": "/video-analysis/jobs/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

`queued` は解析完了ではなく、解析ジョブの受付が完了した状態です。

### 動画解析ジョブの状態確認

PowerShell 3で、返された `job_id` を指定して確認します。

```powershell
curl.exe "http://127.0.0.1:8000/video-analysis/jobs/<job_id>"
```

主な状態は次のとおりです。

```text
queued     ジョブ受付済み
running    動画解析中
completed  正常完了
failed     解析失敗
```

正常完了時は、`status` に加えて `event_count`、`added_event_count`、`backend_total_count` も確認してください。

### 各PowerShellで確認するログ

#### PowerShell 1

FastAPIとYOLO動画解析のログを確認します。

```text
POST /video-analysis/jobs HTTP/1.1 202 Accepted
100/622フレーム処理済み
200/622フレーム処理済み
...
動画解析が完了しました
```

#### PowerShell 2

通知システム全体のログを確認します。

```text
detections.csvの新規作成・更新を検知しました。
バックエンドバッチを実行します: daily
dailyバッチが完了しました。
バックエンドバッチを実行します: weekly
weeklyバッチが完了しました。
バックエンドバッチを実行します: monthly
monthlyバッチが完了しました。
バックエンドバッチを実行します: yearly
yearlyバッチが完了しました。
日次・週次・月次・年次CSVの更新を確認しました。
Excelのrawシートを更新します。
通知用データを計算します。
notificationシートを更新します。
Slack通知を開始します。
```

Slack送信成功時は、次のように表示されます。

```text
Slack通知成功: realtime_notification 行2
Slack通知処理が完了しました
```

#### PowerShell 3

ジョブ登録結果とジョブ状態を確認します。

### 更新されるファイル

バックエンド側：

```text
src/backend/detections.csv
src/backend/daily_analysis.csv
src/backend/weekly_analysis.csv
src/backend/monthly_analysis.csv
src/backend/yearly_analysis.csv
```

通知システム側：

```text
src/notification/result/notification_database.xlsx
```

更新対象シート：

```text
realtime_sheet
daily_sheet
weekly_sheet
monthly_sheet
yearly_sheet
realtime_notification
daily_notification
weekly_notification
monthly_notification
yearly_notification
```

Slack送信結果は各notificationシートの `notification_status` に保存されます。

```text
PENDING  送信待ち
SUCCESS  送信成功
FAILED   送信失敗
SKIPPED  送信対象外
```

### Slack通知が届かない場合

`.env` が読み込まれていても、Webhook URLがIncoming Webhook形式でなければ送信されません。

正しい形式：

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
```

URL全体を表示せずに設定状態だけ確認する場合：

```powershell
Remove-Item Env:SLACK_WEBHOOK_URL -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe -c `
"from dotenv import load_dotenv; import os; load_dotenv('.env'); u=os.getenv('SLACK_WEBHOOK_URL','').strip(); print('設定あり:', bool(u)); print('Incoming Webhook形式:', u.startswith('https://hooks.slack.com/services/') or u.startswith('https://hooks.slack-gov.com/services/'))"
```

期待結果：

```text
設定あり: True
Incoming Webhook形式: True
```

通知用シートまで作成済みでSlack送信だけ失敗した場合は、動画解析からやり直さずSenderだけ実行できます。

```powershell
$env:PYTHONPATH = ".\src"
Remove-Item Env:SLACK_WEBHOOK_URL -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe `
  -m notification.notification_sender `
  .\src\notification\result\notification_database.xlsx
```

このコマンドは、`notification_status` が `PENDING` の行をすべて送信します。

### 終了方法

PowerShell 2のLauncherを停止します。

```text
Ctrl + C
```

PowerShell 1のFastAPIを停止します。

```text
Ctrl + C
```

PowerShell 3は、状態確認が終了したら閉じて問題ありません。

### 注意事項

- LauncherはSlack送信まで正常完了した後に、対象の `detections.csv` を処理済みとして記録します。
- Slack設定不備などで途中失敗すると、同じ `detections.csv` を再処理して分析CSVへ同じ期間の結果を追記する可能性があります。エラー発生時はLauncherを停止し、原因を修正してから再開してください。
- `notification_database.xlsx` をExcelで開いたまま実行すると、WriterまたはSenderの保存に失敗する可能性があります。
- `.env` と実行時CSV・ExcelはGitへ登録しないでください。