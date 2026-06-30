## バックエンド

使用技術：
Python・
Flask・
Pandas

OS：Ubuntu  
リポジトリ名：businessAIsystem-nagoya-teamA  
ブランチ名：feature/backend

## 現時点のAPI設計（確定変数）

| 変数名                       | 意味                       | 型             |
| ------------------------- | ------------------------ | ------------- |
| peak_hour                 | 最も出現が多い時間帯               | int           |
| peak_count                | ピーク時間の出現回数               | int           |
| hour_count                | 時間帯ごとの出現回数               | dict          |
| familiarity_daily_score   | 慣れ度（日単位）                 | float         |
| familiarity_weekly_score  | 慣れ度（週単位）                 | float         |
| familiarity_monthly_score | 慣れ度（月単位）                 | float         |
| familiarity_yearly_score  | 慣れ度（年単位）                 | float         |
| trap_score                | 罠設置推奨スコア                 | float         |
| level                     | 危険度（HIGH / MEDIUM / LOW） | string        |

＊最終出力の仕様


## ファイル名

出没ピーク算出\
ファイル名：appearance.py

慣れ分析\
ファイル名：habituation.py

罠設置推奨スコア\
ファイル名：trap.py

## できること
ダミーCSVにて、Pandasで読み\
動物ごとの出現回数\
撃退アクションの実行回数\
平均滞在時間\
時間帯分析\
出没ピーク算出\
慣れ分析\
罠設置推奨スコア



## 出没ピーク算出

| 変数名        | 意味         | 型      |
| ---------- | ---------- | ------ |
| hour_count | 時間帯ごとの出現回数 | Series |
| peak_hour  | 最も出現が多い時間帯 | int    |
| peak_count | ピーク時間の出現回数 | int    |


### フロントエンド用データ
時間帯分析グラフ用
```
{
  "hourly_detection_count": {
    "0": 2,
    "1": 1,
    "2": 5,
    "3": 3
  }
}
```


ピーク時間表示用
```
{
  "peak_hour": 2,
  "peak_count": 5
}
```


## 慣れ分析
| 変数名               | 意味           | 型      |
| ----------------- | ------------ | ------ |
| daily             | 日ごとの平均滞在時間   | Series |
| weekly            | 週ごとの平均滞在時間   | Series |
| monthly           | 月ごとの平均滞在時間   | Series |
| yearly            | 年ごとの平均滞在時間   | Series |
| first_day         | 最初の期間の平均滞在時間 | float  |
| last_day          | 最後の期間の平均滞在時間 | float  |
| familiarity_score | 慣れ度スコア（増加率）  | float  |




### フロントエンド用データ
慣れ度（デモ：日単位）
```
{
  "familiarity_daily_score": 0.65
}
```

慣れ度（週単位）
```
{
  "familiarity_weekly_score": 0.42
}
```

慣れ度（月単位）
```
{
  "familiarity_monthly_score": 0.58
}
```

慣れ度（年単位）
```
{
  "familiarity_yearly_score": 0.73
}
```


### 計算方法
familiarity_score
= (最後の平均滞在時間 - 最初の平均滞在時間)
  / 最初の平均滞在時間




## 罠設置推奨スコア

| 変数名               | 意味                      | 型         |
| ----------------- | ----------------------- | --------- |
| animal_count      | 動物ごとの出現回数               | Series    |
| animal_score      | 出現頻度スコア（正規化）            | float     |
| trend_score       | 出現増加トレンド                | float     |
| half              | 前半・後半の分割位置              | int       |
| first_half        | 前半データ件数                 | int       |
| second_half       | 後半データ件数                 | int       |
| df_sorted         | 時系列ソート済みデータ             | DataFrame |
| daily             | 日ごとの平均滞在時間              | Series    |
| familiarity_score | 慣れ度（滞在時間増加率）            | float     |
| trap_score        | 罠設置推奨スコア                | float     |
| level             | 危険度レベル（HIGH/MEDIUM/LOW） | string    |



### フロントエンド用データ
```
{
  "trap_score": 0.78,
  "level": "HIGH",
  "details": {
    "animal_score": 0.30,
    "trend_score": 1.00,
    "familiarity_score": 0.65
  }
}
```

### 計算方法
出現スコア  
animal_score = max(出現回数) / 全データ数

増加トレンド  
trend_score = (後半の件数 - 前半の件数) / 前半の件数

慣れ度  
familiarity_score =
(最後の平均滞在時間 - 最初の平均滞在時間)
/ 最初の平均滞在時間

最終数値  
```
trap_score =  
  0.5 × 出現スコア
+ 0.3 × 増加トレンド
+ 0.2 × 慣れ度
```

### レベル判別方法
```
if trap_score >= 0.7:
    level = "HIGH"
elif trap_score >= 0.4:
    level = "MEDIUM"
else:
    level = "LOW"
```