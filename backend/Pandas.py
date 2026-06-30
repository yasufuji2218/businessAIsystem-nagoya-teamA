#Pandasテスト
import pandas as pd

df = pd.read_csv("animal_log.csv")


print(df)

print(df.columns)

print(df.info())


#動物ごとの出現回数
print(df["animal_type"].value_counts())


#撃退アクションの実行回数
print(df["action_triggered"].value_counts())



#平均滞在時間
print(df["stay_duration"].mean())


#時間帯分析
df["timestamp"] = pd.to_datetime(df["timestamp"])

df["hour"] = df["timestamp"].dt.hour

print(df["hour"].value_counts().sort_index())
