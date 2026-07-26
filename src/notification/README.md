# Notification System（通知システム担当）

## 概要

本ディレクトリは、チーム開発における**通知システム担当**の実装です。

ラズパイ担当が生成した解析結果（CSV）を利用し、

- Excelへのデータ反映
- 通知用データの生成
- Slack通知

までを担当しています。

本実装はバックエンドの解析処理を変更するものではなく、
**バックエンドが生成したCSVを利用して通知システムを構築すること**を目的としています。

---

# 担当範囲

通知システム担当として実装したファイル

```
notification/
│
├── notification_launcher.py
├── notification_database_updater.py
├── notification_calculator.py
├── notification_writer.py
├── notification_sender.py
│
└── result/
    └── notification_database.xlsx
```

---

# システム構成

```
ラズパイ担当
        │
        ▼
YOLO動画解析(Job API)
        │
        ▼
detections.csv生成
        │
        ▼
backend.batch
(daily/week/month/year)
        │
──────────────────────────
ここから通知担当
──────────────────────────

notification_launcher.py
        │
        ▼
notification_database_updater.py
        │
        ▼
notification_calculator.py
        │
        ▼
notification_writer.py
        │
        ▼
notification_sender.py
        │
        ▼
Slack通知
```

---

# 各プログラムの役割

## notification_launcher.py

通知システム全体の制御を行います。

### 主な役割

- detections.csvの更新監視
- backend.batchの実行
- 各通知処理の呼び出し
- 全体ログ管理

処理順

```
detections.csv更新待ち

↓

daily batch

↓

weekly batch

↓

monthly batch

↓

yearly batch

↓

notification_database_updater

↓

notification_calculator

↓

notification_writer

↓

notification_sender
```

---

## notification_database_updater.py

CSVファイルを読み込み、

notification_database.xlsx

のRawシートへ反映します。

対象CSV

- detections.csv
- daily_analysis.csv
- weekly_analysis.csv
- monthly_analysis.csv
- yearly_analysis.csv

処理内容

- CSV読込
- 入力検証
- Rawシート更新

---

## notification_calculator.py

Rawシートから通知用データを生成します。

主な処理

- 通知用データ生成
- 必要項目のみ抽出
- 通知文生成用データ作成

なお、

trap_score

rank

など、通知に不要な項目は利用しません。

---

## notification_writer.py

notification_calculator.pyで作成したデータを

notificationシート

へ書き込みます。

対象シート

- realtime_notification
- daily_notification
- weekly_notification
- monthly_notification
- yearly_notification

書式を保持したまま更新を行います。

---

## notification_sender.py

notificationシートを読み込み、

Slack Incoming Webhook

を利用して通知します。

送信後

通知確認列

を更新します。

.env

からWebhook URLを取得します。

---

# 通知システムで自動化した内容

本担当では、

CSV生成後の通知処理

を自動化しています。

自動化内容

```
detections.csv更新検知

↓

backend.batch実行

↓

analysis.csv生成

↓

Excel Rawシート更新

↓

通知シート生成

↓

Slack通知
```

---

# バックエンドとの関係

通知システムでは、

YOLO解析

動画解析

バックエンドAPI

batch処理

については

**一切変更していません。**

通知システムは、

バックエンドが生成したCSV

のみを利用します。

---

# YOLO動画解析バックエンドについて

本担当では、

以下については実装・変更を行っていません。

- YOLOモデル
- 動画解析
- Job API
- FastAPI
- backend.batch
- CSV生成ロジック

これらはバックエンド担当の実装です。

通知システムでは、

生成されたCSV

のみを入力データとして利用しています。

---

# 動画解析Job APIについて

通知システムでは

```
curl

↓

Job API

↓

動画解析

↓

detections.csv生成
```

までの処理には関与していません。

通知システムは、

detections.csv

が更新されたことを検知して処理を開始します。

---

# フロントエンドとの関係

通知システムは

**フロントエンドとは独立しています。**

通知システムは

```
CSV

↓

Excel

↓

Slack
```

までを担当しています。

フロントエンドとの通信は行っていません。

---

# 最終結合について

通知システムは

バックエンド

↓

通知システム

までを担当しています。

最終的な

画面表示

フロントエンドとの接続

UIとの連携

については、

**フロントエンド担当者が実施します。**

そのため、

本通知システム単体でも動作可能な構成となっています。

---

# 実行時に更新されるファイル

CSV

```
detections.csv

daily_analysis.csv

weekly_analysis.csv

monthly_analysis.csv

yearly_analysis.csv
```

Excel

```
notification_database.xlsx
```

更新シート

```
realtime_sheet

daily_sheet

weekly_sheet

monthly_sheet

yearly_sheet

↓

realtime_notification

daily_notification

weekly_notification

monthly_notification

yearly_notification
```

---
notification/                                   # 通知システム
│
├── __init__.py
│
├── notification_launcher.py                    # 通知システム全体制御
│    ├── detections.csv更新監視
│    ├── backend.batch実行
│    ├── notification_database_updater呼び出し
│    ├── notification_calculator呼び出し
│    ├── notification_writer呼び出し
│    └── notification_sender呼び出し
│
├── notification_database_updater.py            # Excel Rawシート更新
│    ├── detections.csv読込
│    ├── daily_analysis.csv読込
│    ├── weekly_analysis.csv読込
│    ├── monthly_analysis.csv読込
│    ├── yearly_analysis.csv読込
│    ├── 入力検証
│    └── Rawシート更新
│
├── notification_calculator.py                  # 通知データ生成
│    ├── realtime_notification生成
│    ├── daily_notification生成
│    ├── weekly_notification生成
│    ├── monthly_notification生成
│    ├── yearly_notification生成
│    ├── 必要項目抽出
│    └── trap_score・rank除外
│
├── notification_writer.py                      # Notificationシート更新
│    ├── realtime_notification書込み
│    ├── daily_notification書込み
│    ├── weekly_notification書込み
│    ├── monthly_notification書込み
│    ├── yearly_notification書込み
│    └── 書式維持・Excel保存
│
├── notification_sender.py                      # Slack通知
│    ├── .env読込
│    ├── Slack Incoming Webhook取得
│    ├── Notificationシート読込
│    ├── Slack送信
│    └── 通知確認列（○／×）更新
│
├── result/
│   └── notification_database.xlsx              # 通知システム中間データベース
│
│       ├──────────────────────────────────────
│       │ Rawデータ格納シート
│       ├──────────────────────────────────────
│       │
│       ├── realtime_sheet
│       │      └── detections.csv
│       │          （YOLO解析結果）
│       │
│       ├── daily_sheet
│       │      └── daily_analysis.csv
│       │          （日次集計）
│       │
│       ├── weekly_sheet
│       │      └── weekly_analysis.csv
│       │          （週次集計）
│       │
│       ├── monthly_sheet
│       │      └── monthly_analysis.csv
│       │          （月次集計）
│       │
│       └── yearly_sheet
│              └── yearly_analysis.csv
│                  （年次集計）
│
│       ├──────────────────────────────────────
│       │ 通知データシート
│       ├──────────────────────────────────────
│       │
│       ├── realtime_notification
│       │      ├── realtime_sheetを元に生成
│       │      └── Slackリアルタイム通知用
│       │
│       ├── daily_notification
│       │      ├── daily_sheetを元に生成
│       │      └── 日次通知用
│       │
│       ├── weekly_notification
│       │      ├── weekly_sheetを元に生成
│       │      └── 週次通知用
│       │
│       ├── monthly_notification
│       │      ├── monthly_sheetを元に生成
│       │      └── 月次通知用
│       │
│       └── yearly_notification
│              ├── yearly_sheetを元に生成
│              └── 年次通知用
│
├── README.md                                   # 通知システム説明
│
└── .notification_launcher_state.json
       └── CSV監視状態保存（自動生成・Git管理しない）
---
### 通知システム内部のデータフロー
backend/

detections.csv
daily_analysis.csv
weekly_analysis.csv
monthly_analysis.csv
yearly_analysis.csv

        │
        ▼

notification_database_updater.py

        │

CSV読込

        │

入力検証

        │

notification_database.xlsx

Rawシート更新

        │
        ▼

notification_calculator.py

        │

通知文章生成用データ作成

        │

Realtime通知

Daily通知

Weekly通知

Monthly通知

Yearly通知

        │
        ▼

notification_writer.py

        │

Notificationシート更新

Excel保存

        │
        ▼

notification_sender.py

        │

Notificationシート読込

        │

Slack通知

        │

通知確認列更新
---

# 使用技術

- Python 3
- openpyxl
- pandas
- python-dotenv
- requests
- FastAPI（バックエンド利用）
- Slack Incoming Webhook

---

# 備考

本実装は、

通知システム担当

として開発した機能のみをまとめています。

バックエンドやYOLO解析の仕様変更は行っていません。

また、

フロントエンドとの結合も行っておらず、

通知システム単体で動作確認できる構成になっています。

最終的な画面との連携は、

フロントエンド担当者が実施します。