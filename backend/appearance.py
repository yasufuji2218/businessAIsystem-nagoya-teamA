import pandas as pd
import json

df = pd.read_csv("animal_log.csv")

# 日時型に変換
df["timestamp"] = pd.to_datetime(df["timestamp"])

# 時間だけ取り出す
df["hour"] = df["timestamp"].dt.hour

# 時間帯ごとの出現回数
hour_count = df["hour"].value_counts().sort_index()

# ピーク時間帯
peak_hour = hour_count.idxmax()
peak_count = hour_count.max()

# API用JSON
response = {
    "peak_hour": int(peak_hour),
    "peak_count": int(peak_count)
}

print(json.dumps(response, indent=2, ensure_ascii=False))