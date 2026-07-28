# 担当者：伊藤寛晋

## もくじ

- [自分の役割](#自分の役割)
- [技術スタック](#技術スタック)
- [環境構築の手順](#環境構築の手順)
- [実行手順](#実行手順)
- [やったこと](#やったこと)
- [まだ出来ていないこと](#まだ出来ていないこと)
- [関連PR・Issue](#関連pr・issue)

---

## 自分の役割

`docs/作業担当領域.md` の **「2. フロントエンド担当 (Frontend UI/UX Engineer)」** を担当。

農家・猟友会（エンドユーザー）向けのダッシュボードUI実装に加え、実際には以下の3つの担当領域をまたいだ**結合作業**を主に行った。

- フロントエンド（React/Vite）とバックエンドAPI（FastAPI）の結合
- フロントエンドと通知システム（Slack連携）の疎通確認・安全な運用方法の考案
- YOLO動画解析〜バックエンドCSV反映〜ダッシュボード表示までの一気通貫の動作検証

---

## 技術スタック

### フロントエンド
- React 18 / Vite
- Tailwind CSS
- recharts（グラフ描画）
- lucide-react（アイコン）

### フロントエンドのテスト
- Vitest + React Testing Library（単体テスト）
- Playwright（結合テスト・実ブラウザでの動作確認）

### 連携先（バックエンド／通知システム）
- FastAPI（Python）
- Pandas
- Ultralytics YOLO（動画解析）
- openpyxl / python-dotenv / filelock（通知システム側）
- Slack Incoming Webhook

### その他
- Git / GitHub（ブランチ運用・Pull Request）

---

## 環境構築の手順

### Python側（バックエンド・通知システム）

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windowsは .venv\Scripts\activate

pip install -r src/requirements.txt
pip install python-dotenv filelock openpyxl   # 通知システムに必要
```

### フロントエンド側

```bash
cd frontend
npm install
```

### Slack通知用の環境変数

プロジェクトルート直下に `.env` を作成する（**Gitには絶対にコミットしない**。`.gitignore` に登録済み）。

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
```

---

## 実行手順

### 1. バックエンドAPIを起動

```bash
PYTHONPATH=src uvicorn backend.api:app --app-dir src --host 0.0.0.0 --port 8000
```

### 2. フロントエンドを起動

```bash
cd frontend
npm run dev
```

表示されたURL（既定は `http://localhost:5173`）を開く。`vite.config.js` のプロキシ設定により、フロントエンドの `/api/...` へのリクエストは自動的に `http://127.0.0.1:8000/...` へ中継される。

### 3.（任意）通知Launcherを起動

Slack通知まで含めて確認したい場合、別ターミナルで:

```bash
PYTHONPATH=src python -m notification.notification_launcher --reset-baseline
```

### 4. 動画をアップロードして解析

フロントエンドの「分析レポート」画面上部にある「動画をアップロードして解析」カードから、MP4ファイルとカメラID・撮影開始日時などを指定して「解析ジョブを登録」を押すと、YOLOでの解析→`detections.csv`への反映→（Launcher起動中なら）Slack通知までが自動で流れる。

### テストの実行

```bash
cd frontend
npm run build       # ビルド確認
npm test             # Vitest（単体テスト）
npm run test:e2e     # Playwright（結合テスト、devサーバー自動起動）
```

---

## やったこと

### 1. フロントエンドUIモックアップの完成（[PR #11](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/pull/11)）

- `WildlifeDashboard.jsx`：総合ダッシュボード／検知履歴／分析レポートの3画面SPA
- React + Vite + Tailwind CSS + recharts + lucide-react の開発環境一式を構築
- CSVダウンロード機能に実バグ（Blobオブジェクトの参照が早期に失効しダウンロードに失敗する場合がある）を発見し修正
- Vitest単体テスト4件、Playwright結合テスト4件を追加
- デザイン違いの参考実装（`wildlife-saas-mockup/`）を追加

### 2. バックエンドAPIとの結合、動画アップロードUI、月次比較の実データ化（[PR #19](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/pull/19)）

- `/habituation`・`/trap` APIと結合し、「AI慣れ度分析」「総合罠設置推奨度」カードを追加
- 「動画をアップロードして解析」カードを新規実装。`POST /video-analysis/jobs` の登録から `GET /video-analysis/jobs/{job_id}` のポーリングまでをUIで完結させ、それまでcurlコマンドを手打ちしていたPowerShell手順をブラウザ操作に置き換えた
- 月次比較グラフを、ハードコードされたダミー配列から `/detections` の実データを集計する方式（`buildMonthlyData`）に変更
- フロントエンドのダミーデータに残っていた「シカ」「ハクビシン」（バックエンドが実際には検知できない動物種）を削除し、表示と実装の整合性を取った
- 同時期に別メンバーが実装していた「検知履歴・時間帯別・曜日別グラフを実データに接続する」変更（[PR #18](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/pull/18)）と自分の変更が重複していたため、そちらをベースに取り込み、被っていない差分だけを載せ直してコンフリクトなく統合した

### 3. YOLO動画解析の実行・検証

- `src/inputs/videos/test_video.mp4` を実際に `scripts/analyze_video.py` で解析し、イノシシ1頭・サル3頭の検出を確認
- `scripts/merge_detections.py` の役割（フレーム単位の検出をイベント単位に変換し、`src/backend/detections.csv` へロック付き・アトミックに追記する仕組み）を調査・検証
- フロントエンドの動画アップロードUI経由でも同じ解析パイプラインが動作することをPlaywrightで実ブラウザ確認

### 4. Slack通知システムとの疎通確認・安全な運用方法の考案

- `notification_sender.py` 等、通知システム一式のコードを読み込み、`.env`経由でのWebhook URL取得〜Slack送信〜ステータス更新までの流れを把握
- 実際にWebhookへテスト送信を行い、Slack側から `200 ok` が返ることを確認
- 動作確認用の大量サンプルデータ（740件）をそのまま通知パイプラインに流すと、初回にSlackへ大量送信されてしまう問題を発見
- データを削除せずに済む対処法として、`notification_status` を一括で `SKIPPED` にする手順を考案し、READMEに誰でも実行できる形で追記

### 5. ドキュメント整備

- プロジェクト共通の `README.md` に、フロントエンドからの動画解析実行手順、大量データの安全な既読化手順を追記

---

## まだ出来ていないこと

- カメラ別詳細分析（レーダーチャート）の実データ化：バックエンドにカメラ単位のスコアAPIが無いため、フロントエンド側はまだダミー表示のまま
- 通知パイプラインの本番相当の通しテスト（FastAPI・通知Launcher・動画アップロードを同時に動かし、新規検知が実際にSlackへ届くところまでの確認）
- 今回追加した機能（慣れ度・罠推奨度カード、動画アップロードUI）に対する自動テスト（Vitest/Playwright）の追加。現状は手動でのPlaywright確認のみ

---

## 関連PR・Issue

- [PR #11 ケモノガード フロントエンドUIモックアップ](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/pull/11)（マージ済み）
- [PR #19 AI慣れ度分析・総合罠設置推奨度API連携 + 動画アップロードUI](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/pull/19)（レビュー待ち）
- [Issue #5 feature/backendの.venv誤コミット](https://github.com/yasufuji2218/businessAIsystem-nagoya-teamA/issues/5)（未着手・担当者未アサイン）
